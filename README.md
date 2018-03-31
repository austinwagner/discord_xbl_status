**THIS REPOSITORY IS NO LONGER MAINTAINED AND EXISTS ONLY FOR ARCHIVAL PURPOSES. It does not support 2FA and was meant to be superceded by (the incomplete) discord_console_status. That project was put to a halt for the same reason I suggest this project not be used: the Discord Terms of Service are phrased in a way where usage of this could be in violation. If you want this functionality, I suggest you reach out to the Hammer & Chisel as well as to Microsoft and Sony. Open-letters on social media or their forums would be the best way to draw attention to the desire to have these services play nice with Discord.** 

# Discord Xbox Live Status Monitor

This script polls the API provided by [xboxapi.com](https://xboxapi.com) at regular intervals to see if the account is currently playing a game. The game is set as the active game for a Discord user prefixed with either 'XB1' or '360' depending on the console being used.

## Setup

You will need a Discord account and an account on [xboxapi.com](https://xboxapi.com). The free account provides you with 120 requests per hour so the default update interval is set to 30 seconds.

This script expects all of your info to be in a JSON file (I suggest you make sure the permissions on the file are locked down since your Discord password is stored in here). 

This script uses newer Python features and thus requires Python 3.4+

### Example Configuration File
```javascript
{
  // JSON files do not allow comments, these are for documentation purposes only

  // Your discord login information
  "discord_username": "me@email.invalid",
  "discord_password": "password",

  // The API key provided by xboxapi.com
  "xbox_api_key": "0123456789abcdef",

  // Your Xbox Live ID, found near your API key
  "xbox_live_id": "1234567",

  // Time in seconds between user status checks
  // Optional, Default: 30
  "update_interval": 30,

  // Game/App specific settings
  // Names are case insensitive, but must otherwise match exactly
  // All titles are shown with full details by default (name + more specific per-game info)
  // To hide a title entirely, specify "ignore"
  // To hide only the more detailed into, specify "name-only"
  // Optional, Default: {}
  "title_settings": {
    "Blu-ray Player": "ignore",
    "Rock Band 4": "name-only"
  }
}
```

## Dependency Installation

I suggest using a [virtualenv](https://virtualenv.pypa.io/en/latest/) environment because this script uses a development version of [discord.py](https://github.com/Rapptz/discord.py).

Use the included requirements file to install the dependencies:

`pip3 install -r requirements.txt`

## Usage

`python discord_xbl_monitor.py --config=<config file>`
