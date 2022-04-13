import logging

from decouple import config
from pyrogram import Client, filters
from pyrogram.types import Message

from utils import administration

logging.basicConfig(level='INFO')

app = Client(
    'sessions/attacker_controller',
    api_id=config('api_id', cast=int),
    api_hash=config('api_hash'),
    bot_token=config('bot_token'),
)


@app.on_message(
    filters.regex(r'^\/addadmin (\d+(?:\s+\d+)*)$') &
    filters.group &
    ~filters.edited &
    filters.user(administration.MAIN_ADMINS)
)
async def add_admin(client: Client, message: Message):
    """ Add the given chat ids to the admin list. """
    users_chat_id = message.matches[0].group(1).split()
    await administration.add_admin(*users_chat_id)
    await message.reply_text('چت ایدی های داده شده به لیست ادمین‌ها اضافه شد.')


@app.on_message(
    filters.regex(r'^\/removeadmin (\d+(?:\s+\d+)*)$') &
    filters.group &
    ~filters.edited &
    filters.user(administration.MAIN_ADMINS)
)
async def add_admin(client: Client, message: Message):
    """ Remove the given chat ids from the admin list.  """
    users_chat_id = message.matches[0].group(1).split()
    await administration.remove_admin(*users_chat_id)
    await message.reply_text('چت ایدی های داده شده از لیست ادمین‌ها حذف شد.')


def main():
    app.run()


if __name__ == '__main__':
    main()
