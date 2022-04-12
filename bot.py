import logging

from decouple import config, Csv
from pyrogram import Client, filters

from utils import administration

logging.basicConfig(level='INFO')

app = Client(
    'attacker',
    api_id=config('api_id', cast=int),
    api_hash=config('api_hash'),
    bot_token=config('bot_token'),
)

MAIN_ADMINS = config('main_admins', cast=Csv(cast=int))
""" Main admins can do everything! like add and remove normal admins. """


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


@app.on_message(filters.regex(r'^\/add_admin (\d+(?:\s+\d+)*)$') & filters.group & filters.user(MAIN_ADMINS))
async def add_admin(client, message):
    """ Add the given chat ids to the admin list. """
    users_chat_id = message.matches[0].group(1).split()
    await administration.add_admin(*users_chat_id)
    await message.reply_text('چت ایدی های داده شده به لیست ادمین‌ها اضافه شد.')


@app.on_message(filters.regex(r'^\/remove_admin (\d+(?:\s+\d+)*)$') & filters.group & filters.user(MAIN_ADMINS))
async def add_admin(client, message):
    """ Remove the given chat ids from the admin list.  """
    users_chat_id = message.matches[0].group(1).split()
    await administration.remove_admin(*users_chat_id)
    await message.reply_text('چت ایدی های داده شده از لیست ادمین‌ها حذف شد.')


def main():
    app.run()


if __name__ == '__main__':
    main()
