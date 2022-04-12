import logging

from decouple import config
from pyrogram import Client, filters

logging.basicConfig(level='INFO')

app = Client(
    'attacker',
    api_id=config('api_id', cast=int),
    api_hash=config('api_hash'),
    bot_token=config('bot_token'),
)


@app.on_message(filters.command('clean') & filters.group)
async def clean_accounts(client, message):
    """ Clean all logged-in accounts from the bot. """
    pass


@app.on_message(filters.command('del') & filters.group)
async def delete_account(client, message):
    """ Delete a logged-in account from the bot. """
    pass


@app.on_message(filters.command('check') & filters.group)
async def check_accounts(client, message):
    """ Check logged-in accounts status. """
    pass


def main():
    app.run()


if __name__ == '__main__':
    main()
