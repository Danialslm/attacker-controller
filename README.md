# Attacker controller

### A telegram bot written in Python(pyrogram) for managing mtproto bots

## Installation (linux)

first copy the `.env.sample` to `.env` by running `cp .env.sample .env` and fill it

- `api_id`: your api id. you can get it from https://my.telegram.org
- `api_hash`: your api hash. you can get it from https://my.telegram.org
- `bot_token`: the telegram api bot token which can get it from @BotFather
- `redis_uri`: the redis server uri connection.
- `debug`: project debug mode. if `1` provided, the logs will be printed in terminal and if `0` provided, the logs will go to error.log file with ERROR level

### Create virtualenv

for creating a python virtual-environment with python3.8 (project python version) simply run `virtualenv -p python3.8 .venv`
and `.venv/bin/activate` to activate it

### Install dependencies

when the virtual-environment activated, install the project dependencies by running `pip install -r requirements.txt`

### Run
run `scripts/start.sh` to run the bot