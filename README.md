# roblox-item-sniper
Attempts to buy limited items as quickly as possible, as soon as they go below set threshold price. Don't even bother with free proxies.

# Requirements
- Python 3.6 or above /w `requests` module
- Roblox account with enough robux
- Proxies

# config.json
- `price_check_threads`: number of threads to use for checking limited prices
- `xsrf_refresh_interval`: number of seconds between each xsrf token refresh (the lower the better, 1-5 is enough)
- `targets`: list of `[asset_id, price_threshold]` values (the less targets, the better the performance)

# Python setup
1. Click `Download Python 3.X.X` at https://www.python.org/downloads/
2. While installing, make sure you check 'Add to PATH'
3. After installing Python, run the following command in cmd: `pip install requests`

# Usage
1. Place .ROBLOSECURITY cookie in `cookie.txt`
1. Place proxies in `proxies.txt`
1. Run `sniper.bat`

# Known bugs / To-Do
- The bot attempts to purchase glitched/'recoil' resellers (this is a bug on roblox's side that happens for a second after a limited is purchased)
- PriceCheckThread should have exception alerts
