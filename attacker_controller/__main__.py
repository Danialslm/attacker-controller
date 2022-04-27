import os

from decouple import config
from pyrogram import Client, filters
from pyrogram.errors.exceptions import (
    FloodWait, PhoneNumberInvalid,
)
from pyrogram.types import Message

from attacker_controller import MAIN_ADMINS
from attacker_controller.utils import storage, auth
from attacker_controller.utils.custom_filters import admin

ATTACKERS = {}

app = Client(
    'attacker_controller/sessions/attacker_controller',
    api_id=config('api_id', cast=int),
    api_hash=config('api_hash'),
    bot_token=config('bot_token'),
)


def _remove_session(session_name):
    """
    Remove a attacker session by given session name.
    Return boolean that shows the file removed or no.
    """
    try:
        os.remove(f'attacker_controller/sessions/attackers/{session_name}.session')
    except FileNotFoundError:
        return False

    return True


# admin setting commands
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


# attacker authentication
@app.on_message(
    filters.regex(r'^\/sendcode (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)
async def send_code(client: Client, message: Message):
    """
    Send Login code to given phone number.
    """
    phone = message.matches[0].group(1)
    msg = await message.reply_text('درحال ارسال درخواست. لطفا صبر کنید...')

    ATTACKERS[phone] = Client(
        f'attacker_controller/sessions/attackers/{phone}',
        api_id=config('api_id', cast=int),
        api_hash=config('api_hash'),
    )
    await ATTACKERS[phone].connect()
    try:
        sent_code = await ATTACKERS[phone].send_code(phone)
    except FloodWait as e:
        await msg.edit('ارسال درخواست با محدودیت مواجه شده است. لطفا {} ثانیه دیگر امتحان کنید.'.format(e.x))
        _remove_session(phone)
    except PhoneNumberInvalid:
        await msg.edit('شماره وارد شده نادرست است.')
        _remove_session(phone)
    else:
        # store phone code hash for one minute
        await storage.redis.set(f'phone_code_hash:{phone}', sent_code.phone_code_hash, 60)
        await msg.edit('کد ارسال شد.')


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

    res = await auth.login(phone, password)
    await message.reply_text(res[1])


# attacker setting commands
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
        text += '`{}`\n\n'.format(attacker)
    await message.reply_text(text)


@app.on_message(
    filters.regex(r'^\/removeattacker (\+\d+)$') &
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
