import os

from decouple import config
from pyrogram import Client, filters
from pyrogram.types import Message

from attacker_controller import MAIN_ADMINS
from attacker_controller.utils import (
    remove_attacker_session, get_message_file_extension,
    get_send_method_by_media_type, storage,
)
from attacker_controller.utils.custom_filters import admin

app = Client(
    'attacker_controller/sessions/attacker_controller',
    api_id=config('api_id', cast=int),
    api_hash=config('api_hash'),
    bot_token=config('bot_token'),
    plugins={'root': 'attacker_controller.attacker'}
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
    """ Send current admins list."""
    text = 'لیست چت ایدی ادمین‌های فعلی ربات:\n\n'
    admin_counter = 0
    for chat_id in await storage.get_admins():
        admin_counter += 1
        text += f'{admin_counter} - `{chat_id}`\n'

    await message.reply_text(text)


@app.on_message(
    filters.command('attackerlist') &
    filters.group &
    ~filters.edited &
    admin
)
async def attacker_list(client: Client, message: Message):
    """ Send list of attackers phone. """
    text = 'لیست اتکرها : \n\n'
    attackers = await storage.get_attackers()
    attacker_counter = 0
    for attacker in attackers:
        attacker_counter += 1
        text += f'{attacker_counter} - `{attacker}`\n'
    await message.reply_text(text)


@app.on_message(
    filters.regex(r'^\/removeattacker (\+\d+(?:\s+\+\d+)*)$') &
    filters.group &
    ~filters.edited &
    admin
)
async def remove_attacker(client: Client, message: Message):
    """ Remove given phone(s) from attacker list. """
    phones = message.matches[0].group(1).split()
    for phone in phones:
        await storage.remove_attacker(phone)
        remove_attacker_session(phone)
    await message.reply_text('شماره(های) داده شده از لیست اتکر‌ها حذف شد.')


@app.on_message(
    filters.command('cleanattackers') &
    filters.group &
    ~filters.edited &
    filters.user(MAIN_ADMINS)
)
async def clean_attacker_list(client: Client, message: Message):
    """ Remove all attackers. """
    for attacker_phone in await storage.get_attackers():
        await storage.remove_attacker(attacker_phone)

    for _, __, files in os.walk('attacker_controller/sessions/attackers/'):
        for file in files:
            remove_attacker_session(file)

    await message.reply_text('تمام اتکرها از ربات پاک شدند.')


@app.on_message(
    filters.command('setbanner') &
    filters.group &
    ~filters.edited &
    filters.reply &
    admin
)
async def set_banner(client: Client, message: Message):
    """
    Set a new banner.
    """
    # remove previous banner file
    for _, __, files in os.walk('media/banner'):
        for file in files:
            os.remove(f'media/banner/{file}')

    banner = message.reply_to_message
    # get and save media if message has
    media = (
            banner.photo or banner.video or
            banner.animation or banner.voice or
            banner.sticker
    )
    banner_media_ext = ''
    if media:
        # media file extension
        banner_media_ext = get_message_file_extension(banner)

        await message.reply_to_message.download(file_name=f'media/banner/banner.{banner_media_ext}')

    banner_media_type = banner.media or ''
    banner_text = message.reply_to_message.caption or message.reply_to_message.text or ''

    # store the banner in cache
    await storage.redis.hset('banner', mapping={
        'text': banner_text,
        'media_ext': banner_media_ext,
        'media_type': banner_media_type
    })
    await message.reply_text('بنر با موفقیت ذخیره شد.')


@app.on_message(
    filters.command('banner') &
    filters.group &
    ~filters.edited &
    admin
)
async def get_current_banner(client: Client, message: Message):
    """
    Show the current banner.
    """
    banner = await storage.redis.hgetall('banner')

    if not banner:
        await message.reply_text('بنری ست نشده است.')
        return

    method = get_send_method_by_media_type(banner['media_type'])

    send_method = getattr(client, method)
    if banner['media_type']:
        await send_method(message.chat.id, f'media/banner/banner.{banner["media_ext"]}', banner['text'])
    else:
        await send_method(message.chat.id, banner['text'])


@app.on_message(
    filters.command('help') &
    filters.group &
    ~filters.edited
)
async def help_commands(client: Client, message: Message):
    """
    Return the list of available bot commands.
    """
    text = """
`/adminlist` - لیست ادمین های معمولی
`/addadmin` - اضافه کردن ادمین جدید (جلوش یک چت ایدی یا چند چت ایدی باید باشه)
`/removeadmin` - حذف کردن ادمین جدید (جلوش یک چت ایدی یا چند چت ایدی باید باشه)

`/sendcode` - ارسال کد لاگین (جلوش شماره باید باشه)
`/login` - لاگین به اکانت (جلوش شماره و کد و پسورد اگه داشت باید باشه)

`/attackerlist` - لیست اتکر‌ها
`/removeattacker` - حذف کردن اتکر (جلوش یک یا چند شماره باید باشه)
`/cleanattackers` - حذف کردن تمام اتکرها

`/setfirstnameall` - ست کردن نام کوچک برای همه اتکرها
`/setlastnameall` - ست کردن نام خانوادگی برای همه اتکرها
`/setbioall` - ست کردن بیو برای همه اتکرها
`/setprofileall` - ست کردن عکس پروفایل برای همه اتکرها

`/setfirstname` - ست کردن نام کوچک برای یک اتکر (جلوش شماره باید باشه)
`/setlastname` - ست کردن نام خانوادگی برای یک اتکر (جلوش شماره باید باشه)
`/setbio` - ست کردن بیو برای یک اتکر (جلوش شماره باید باشه)
`/setprofile` - ست کردن عکس پروفایل برای یک اتکر (جلوش شماره باید باشه)
`/setusername` - ست کردن نام کاربری برای یک اتکر (جلوش شماره باید باشه)

`/members` - گرفتن ممبرا (جلوش شماره و ایدی گپ و تعداد ممبرای دریافتی باید باشه)
`/attack` - اتک (جلوش شماره باید باشه)

`/setbanner` - ست کردن بنر جدید
`/banner` - بنر فعلی
"""
    await message.reply_text(text)


app.run()
