import json

from decouple import config
from pyrogram import Client, filters
from pyrogram.types import Message

from attacker_controller import MAIN_ADMINS
from attacker_controller.utils import storage
from attacker_controller.utils.auth import send_password, login
from attacker_controller.utils.custom_filters import admin

app = Client(
    'attacker_controller/sessions/attacker_controller',
    api_id=config('api_id', cast=int),
    api_hash=config('api_hash'),
    bot_token=config('bot_token'),
)


@app.on_message(
    filters.regex(r'^\/addadmin (\d+(?:\s+\d+)*)$') &
    filters.group &
    ~filters.edited &
    filters.user(MAIN_ADMINS)
)
async def add_admin(client: Client, message: Message):
    """ Add the given chat ids to the admin list. """
    users_chat_id = message.matches[0].group(1).split()
    await storage.add_admin(*users_chat_id)
    await message.reply_text('چت ایدی های داده شده به لیست ادمین‌ها اضافه شد.')


@app.on_message(
    filters.regex(r'^\/removeadmin (\d+(?:\s+\d+)*)$') &
    filters.group &
    ~filters.edited &
    filters.user(MAIN_ADMINS)
)
async def remove_admin(client: Client, message: Message):
    """ Remove the given chat ids from the admin list.  """
    users_chat_id = message.matches[0].group(1).split()
    await storage.remove_admin(*users_chat_id)
    await message.reply_text('چت ایدی های داده شده از لیست ادمین‌ها حذف شد.')


@app.on_message(
    filters.command('adminlist') &
    filters.group &
    ~filters.edited &
    filters.user(MAIN_ADMINS)
)
async def admin_list(client: Client, message: Message):
    """ Return list of current admins. """
    admins_chat_id = '\n'.join(await storage.get_admins())
    text = (
        'لیست چت ایدی ادمین‌های فعلی ربات:\n\n'
        f'{admins_chat_id}'
    )
    await message.reply_text(text)


@app.on_message(
    filters.regex(r'^\/sendpassword (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)
async def add_attacker(client: Client, message: Message):
    """ Add an attacker to bot. """
    phone = message.matches[0].group(1)
    res = await send_password(phone)

    # if the request was not success, send error message
    if not res[0]:
        await message.reply_text(res[1])
    else:
        await message.reply_text('کد ارسال شد. مهلت ارسال کد یک دقیقه می‌باشد.')


@app.on_message(
    filters.regex(r'^\/login (\+\d+) (.+)$') &
    filters.group &
    ~filters.edited &
    admin
)
async def login_attacker(client: Client, message: Message):
    """ Login to attacker. """
    match = message.matches[0]
    phone = match.group(1)
    password = match.group(2)

    res = await login(phone, password)
    await message.reply_text(res[1])


@app.on_message(
    filters.command('attackerlist') &
    filters.group &
    ~filters.edited &
    admin
)
async def attacker_list(client: Client, message: Message):
    """
    Get list of attackers phone.
    """
    text = 'لیست اتکرها : \n\n'
    attackers = await storage.get_attackers()
    for attacker in attackers:
        attacker = json.loads(attacker)
        text += f'`{attacker["phone"]}`\n\n'

    await message.reply_text(text)


@app.on_message(
    filters.command('^\/removeattacker (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)
async def remove_attacker(client: Client, message: Message):
    """
    Remove given phone from attacker list.
    """
    phone = message.matches[0].group(1)
    await storage.remove_attacker(phone)
    await message.reply_text('شماره داده شده از لیست اتکر‌ها حذف شد.')


app.run()
