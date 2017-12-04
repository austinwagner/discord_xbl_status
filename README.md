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

`python discord_xbl_status.py --config=<config file>`
