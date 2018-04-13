#!/usr/bin/env python3

import discord
import logging
import argparse
import requests
import asyncio
import json
import sys
from pathlib import Path
import logging.config
import inspect
import signal
import ctypes
from requests.structures import CaseInsensitiveDict

log = logging.getLogger(__name__)


class XblPresenceMonitorConfig(object):
    def __init__(self, discord_username, discord_password,
                 xbox_live_id, xbox_api_key, update_interval=30,
                 title_settings=None):
        self.discord_username = discord_username
        self.discord_password = discord_password
        self.xbox_live_id = xbox_live_id
        self.xbox_api_key = xbox_api_key
        self.update_interval = update_interval
        self.title_settings = {} if title_settings is None else CaseInsensitiveDict(title_settings)

    def __str__(self):
        return '{{ discord_username: {}, discord_password: [HIDDEN], xbox_live_id: {}, ' \
               'xbox_api_key: [HIDDEN], update_interval: {}, title_settings: {} }}'.format(self.discord_username,
                                                                                           self.xbox_live_id,
                                                                                           self.update_interval,
                                                                                           self.title_settings)


class XblPresenceMonitor(object):
    def __init__(self, config: XblPresenceMonitorConfig, event_loop=None):
        self._config = config
        self._api_url = 'https://xboxapi.com/v2/{}/presence'.format(self._config.xbox_live_id)
        self._request_header = {'X-AUTH': self._config.xbox_api_key}
        self._event_loop = asyncio.get_event_loop() if event_loop is None else event_loop
        self._last_status = None
        self._discord_client = discord.Client()

    @asyncio.coroutine
    def _update_loop(self):
        while True:
            try:
                yield from self._do_update()
            except Exception as e:
                log.error(e)

            yield from asyncio.sleep(self._config.update_interval)

    @asyncio.coroutine
    def _do_update(self):
        log.info('Requesting data from Xbox API')
        resp = requests.get(self._api_url, headers=self._request_header)
        presence = resp.json()

        log.debug('Xbox API response: %s', presence)

        success = presence.get('success', True)
        if not success:
            log.error('Xbox API error %d: %s', presence['error_code'], presence['error_message'])
            return

        new_status = None
        if presence['state'] == 'Online' and len(presence['devices']) > 0:
            device = presence['devices'][0]
            for title in device['titles']:
                if title['placement'] != 'Background' and title['state'] == 'Active':
                    new_status = self._make_status_string(device, title)

        if new_status == self._last_status:
            log.debug('Status unchanged')
        else:
            self._last_status = new_status
            if new_status is None:
                log.info('Clearing status')
            else:
                log.info('Updating status to "%s"', new_status)

            yield from self._discord_client.change_presence(game=discord.Game(name=new_status))

    def _make_status_string(self, device, title):
        title_name = title['name']
        title_setting = self._config.title_settings.get(title_name, '').lower()

        if title_setting == 'ignore':
            log.info('Skipping "%s" due to "ignore" setting', title_name)
            return None

        device_type = device['type']
        if device_type == 'XboxOne':
            device_type = 'XB1'
        elif device_type == 'Xbox360':
            device_type = '360'

        new_status = device_type + ': ' + title_name

        if 'activity' in title and 'richPresence' in title['activity'] and \
                title['activity']['richPresence'] != '':
            if title_setting == 'name-only':
                log.info('Skipping rich presence for "%s" due to "name-only" setting', title_name)
            else:
                new_status += ' (' + title['activity']['richPresence'] + ')'

        return new_status

    @asyncio.coroutine
    def _on_ready(self):
        yield from self._discord_client.wait_until_ready()
        log.info('Discord logged in as %s', self._discord_client.user.name)
        yield from self._update_loop()

    def run(self):
        def interrupt():
            raise KeyboardInterrupt

        # Register handlers to perform cleanup so we don't leave the user status stuck
        # This handles all graceful exit cases including clean OS shutdown
        if sys.platform == 'win32':
            @ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint)
            def ctrl_handler(ctrl_event):
                self._event_loop.call_soon(interrupt)
                return 1

            ctypes.windll.kernel32.SetConsoleCtrlHandler(ctrl_handler, 1)
        else:
            self._event_loop.add_signal_handler(signal.SIGTERM, interrupt)
            self._event_loop.add_signal_handler(signal.SIGINT, interrupt)

        tasks = asyncio.gather(self._discord_client.start(self._config.discord_username,
                                                          self._config.discord_password),
                               self._event_loop.create_task(self._on_ready()),
                               loop=self._event_loop)

        try:
            self._event_loop.run_until_complete(tasks)
        except KeyboardInterrupt:
            log.info('Event loop interrupted, resetting user status and cleaning up')
            tasks.cancel()
            self._event_loop.run_forever()
            tasks.exception()
            self._event_loop.run_until_complete(self._discord_client.change_status(None))
            self._event_loop.run_until_complete(self._discord_client.logout())
            sys.exit(0)
        finally:
            self._event_loop.close()


class ConfigLoadException(Exception):
    pass


def create_monitor_config(conf: dict):
    args = {}
    message = ''

    # Dynamically determine the configuration names and if they are required
    ctor_signature = inspect.signature(XblPresenceMonitorConfig)

    for parameter in ctor_signature.parameters.values():
        is_required = parameter.default == inspect.Parameter.empty
        entry_name = parameter.name

        entry_value = conf.get(entry_name)
        if entry_value is not None:
            # Copy over to args so we don't error on extra entries in the file
            args[entry_name] = conf[entry_name]
        elif is_required:
            if message == '':
                message = 'Configuration missing: ' + entry_name
            else:
                message += ', ' + entry_name

    if message != '':
        raise ConfigLoadException(message)

    return XblPresenceMonitorConfig(**args)


def main():
    parser = argparse.ArgumentParser(description='Show Xbox Live status in Discord')
    parser.add_argument('--config', dest='config', help='Configuration file path', required=True, type=Path)
    args = parser.parse_args()

    try:
        with args.config.open('r') as f:
            config = json.load(f)

        monitor_config = create_monitor_config(config)
    except Exception as e:
        print('Failed to load config: %s' % e)
        sys.exit(1)

    logging_config = config.get('logging')
    if logging_config is not None:
        logging_config['disable_existing_loggers'] = False
        logging.config.dictConfig(logging_config)
        log.info('Using logging config from file')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s [%(levelname)-5s] %(name)s  %(message)s')
        log.info('Using default logging config')

    log.debug('Using config %s', monitor_config)

    monitor = XblPresenceMonitor(monitor_config)
    monitor.run()

if __name__ == '__main__':
    main()
