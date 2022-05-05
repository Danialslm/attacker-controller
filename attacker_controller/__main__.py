from decouple import config
from pyrogram import Client, filters
from pyrogram.types import Message

from attacker_controller import MAIN_ADMINS
from attacker_controller.attacker_commands import handlers
from attacker_controller.utils import storage

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
    text = 'لیست چت ایدی ادمین‌های فعلی ربات:\n\n'
    admin_counter = 0
    for chat_id in await storage.get_admins():
        admin_counter += 1
        text += f'{admin_counter} - `{chat_id}`\n'

    await message.reply_text(text)


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
"""
    await message.reply_text(text)


# add handlers
app.add_handler(handlers.send_code_handler)
app.add_handler(handlers.login_attacker_handler)
app.add_handler(handlers.attacker_list_handler)
app.add_handler(handlers.remove_attacker_handler)
app.add_handler(handlers.clean_attacker_list_handler)
app.add_handler(handlers.set_first_name_all_handler)
app.add_handler(handlers.set_last_name_all_handler)
app.add_handler(handlers.set_bio_all_handler)
app.add_handler(handlers.set_profile_photo_all_handler)
app.add_handler(handlers.set_first_name_handler)
app.add_handler(handlers.set_last_name_handler)
app.add_handler(handlers.set_bio_handler)
app.add_handler(handlers.set_profile_photo_handler)
app.add_handler(handlers.set_username_handler)
app.add_handler(handlers.get_group_members_handler)
app.add_handler(handlers.set_banner_handler)
app.add_handler(handlers.get_current_banner_handler)
app.add_handler(handlers.set_attack_handler)

app.run()
