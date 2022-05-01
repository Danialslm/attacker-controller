import os

from decouple import config
from pyrogram import Client, filters
from pyrogram.errors import exceptions
from pyrogram.types import Message, SentCode

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


def _remove_attacker_session(session_name: str) -> bool:
    """
    Remove a attacker session by given session name.
    Return boolean that shows the file removed or no.
    """
    try:
        os.remove(f'attacker_controller/sessions/attackers/{session_name}.session')
    except FileNotFoundError:
        return False

    return True


async def _get_api_id_and_api_hash(phone: str) -> str:
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
    # the web password can get by regex or pythonic way
    # web_password = re.match(r'.*This is your login code:\n(.*)\n', last_message[0].text).group(1)
    web_password = last_message[0].text.split('\n')[1]
    res = await auth.login(phone, web_password)

    if not res[0]:
        # logging to web was failed
        return await _error(res[1])
    else:
        return 'فرایند به اتمام رسید و {}'.format(res[1])


async def _update_all_attackers(field: str, value: str) -> int:
    """
    Update all available attackers.
    Return number of succeed update.
    """
    number_of_successes = 0

    for atk_phone in await storage.get_attackers():
        attacker = await storage.get_attackers(atk_phone)
        attacker_client = Client(
            f'attacker_controller/sessions/attackers/{atk_phone}',
            api_id=attacker['api_id'],
            api_hash=attacker['api_hash'],
        )
        success = await _update_attacker(attacker_client, field, value)
        if success:
            number_of_successes += 1

    return number_of_successes


async def _update_attacker(attacker: Client, field: str, value: str) -> bool:
    """
    Connect to attacker and update it by given field and value.
    Return True on success.
    """
    await attacker.connect()
    if field in ['first_name', 'last_name', 'bio']:
        success = await attacker.update_profile(**{field: value})
    elif field == 'profile_photo':
        success = await attacker.set_profile_photo(photo=value)
    elif field == 'username':
        try:
            success = await attacker.update_username(value)
        except (exceptions.UsernameInvalid, exceptions.UsernameOccupied):
            success = False
    else:
        success = False

    await attacker.disconnect()
    return success


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
    text = 'لیست چت ایدی ادمین‌های فعلی ربات:\n\n'
    admin_counter = 0
    for chat_id in await storage.get_admins():
        admin_counter += 1
        text += f'{admin_counter} - `{chat_id}`\n'

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
        sent_code: SentCode = await ATTACKERS[phone].send_code(phone)
        if sent_code.type == 'app':
            type_text = 'پیام در پیوی تلگرام'
        elif sent_code.type == 'sms':
            type_text = 'اس ام اس'
        elif sent_code.type == 'call':
            type_text = 'تماس تلفنی'
        else:
            type_text = sent_code.type

    except exceptions.FloodWait as e:
        await msg.edit('ارسال درخواست با محدودیت مواجه شده است. لطفا {} ثانیه دیگر امتحان کنید.'.format(e.x))
        await ATTACKERS[phone].disconnect()
        _remove_attacker_session(phone)
    except exceptions.PhoneNumberInvalid:
        await msg.edit('شماره وارد شده نادرست است.')
        await ATTACKERS[phone].disconnect()
        _remove_attacker_session(phone)
    else:
        # store phone code hash for one minute
        await storage.redis.set(f'phone_code_hash:{phone}', sent_code.phone_code_hash, 60)
        await msg.edit('کد به صورت {} ارسال شد.'.format(type_text))


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

    try:
        await ATTACKERS[phone].sign_in(phone, phone_code_hash, code)
    except (exceptions.PhoneCodeExpired, exceptions.PhoneCodeEmpty, exceptions.PhoneCodeInvalid):
        await msg.edit('کد منقضی یا اشتباه است.')
    except exceptions.PhoneNumberUnoccupied:
        await msg.edit('شماره تلفن در تلگرام ثبت نشده است.')
    except exceptions.SignInFailed:
        await msg.edit('فرایند لاگین به مشکل خورد! لطفا دوباره امتحان کنید.')
    except exceptions.SessionPasswordNeeded:
        if password is not None:
            try:
                await ATTACKERS[phone].check_password(password)
            except (exceptions.PasswordHashInvalid, exceptions.BadRequest):
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
    attacker_counter = 0
    for attacker in attackers:
        attacker_counter += 1
        text += f'{attacker_counter} - `{attacker}`\n'
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


# edit attacker profile commands
@app.on_message(
    filters.command('setfirstnameall') &
    filters.group &
    ~filters.edited &
    filters.reply &
    admin
)
async def set_first_name_all(client: Client, message: Message):
    """
    Set a first name for all attackers.
    """
    provided_first_name = message.reply_to_message.text
    if not provided_first_name:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر نام کوچک اتکر‌ها. لطفا صبر کنید...')

    number_of_successes = await _update_all_attackers('first_name', provided_first_name)

    await msg.edit(
        '{} اتکر نام کوچک‌شان به **{}** تغییر یافت.'.format(number_of_successes, provided_first_name),
        parse_mode='markdown',
    )


@app.on_message(
    filters.command('setlastnameall') &
    filters.group &
    ~filters.edited &
    filters.reply &
    admin
)
async def set_last_name_all(client: Client, message: Message):
    """
    Set a last name for all attackers.
    """
    provided_last_name = message.reply_to_message.text
    if not provided_last_name:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر نام خانوادگی اتکر‌ها. لطفا صبر کنید...')

    number_of_successes = await _update_all_attackers('last_name', provided_last_name)

    await msg.edit(
        '{} اتکر نام خانوادگی‌شان به **{}** تغییر یافت.'.format(number_of_successes, provided_last_name),
        parse_mode='markdown',
    )


@app.on_message(
    filters.command('setbioall') &
    filters.group &
    ~filters.edited &
    filters.reply &
    admin
)
async def set_bio_all(client: Client, message: Message):
    """
    Set a bio for all attackers.
    """
    provided_bio = message.reply_to_message.text
    if not provided_bio:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر بیو اتکر‌ها. لطفا صبر کنید...')

    number_of_successes = await _update_all_attackers('bio', provided_bio)

    await msg.edit(
        '{} اتکر بیو‌شان به **{}** تغییر یافت.'.format(number_of_successes, provided_bio),
        parse_mode='markdown',
    )


@app.on_message(
    filters.command('setprofileall') &
    filters.group &
    ~filters.edited &
    filters.reply &
    admin
)
async def set_profile_photo_all(client: Client, message: Message):
    """
    Set a profile photo for all attackers.
    """
    provided_photo = message.reply_to_message.photo
    if not provided_photo:
        await message.reply_text('لطفا روی یک عکس ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر عکس پروفایل اتکر‌ها. لطفا صبر کنید...')

    # download the photo
    provided_photo = await client.download_media(
        provided_photo.file_id,
        file_name='media/profile_photo.jpg',
    )

    number_of_successes = await _update_all_attackers('profile_photo', provided_photo)

    os.remove('media/profile_photo.jpg')
    await msg.edit(
        '{} اتکر عکس پروفایل‌شان تغییر یافت.'.format(number_of_successes),
        parse_mode='markdown',
    )


@app.on_message(
    filters.regex(r'^\/setfirstname (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)
async def set_first_name(client: Client, message: Message):
    """
    Start first name for a specific attacker.
    """
    phone = message.matches[0].group(1)
    attacker = await storage.get_attackers(phone)
    if not attacker:
        await message.reply_text('اتکری با این شماره موبایل وجود ندارد.')
        return

    provided_first_name = message.reply_to_message.text
    if not provided_first_name:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر نام کوچک اتکر {}. لطفا صبر کنید...'.format(phone))
    attacker_client = Client(
        f'attacker_controller/sessions/attackers/{phone}',
        api_id=attacker['api_id'],
        api_hash=attacker['api_hash'],
    )

    success = await _update_attacker(attacker_client, 'first_name', provided_first_name)
    if success:
        await msg.edit('اتکر {} نام کوچکش به **{}** تغییر یافت.'.format(phone, provided_first_name))
    else:
        await msg.edit('مشکلی در تغییر نام کوچک اتکر {} به وجود آمد. لطفا دوباره امتحان کنید.'.format(phone))


@app.on_message(
    filters.regex(r'^\/setlastname (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)
async def set_last_name(client: Client, message: Message):
    """
    Start last name for a specific attacker.
    """
    phone = message.matches[0].group(1)
    attacker = await storage.get_attackers(phone)
    if not attacker:
        await message.reply_text('اتکری با این شماره موبایل وجود ندارد.')
        return

    provided_last_name = message.reply_to_message.text
    if not provided_last_name:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر نام خانوادگی اتکر {}. لطفا صبر کنید...'.format(phone))
    attacker_client = Client(
        f'attacker_controller/sessions/attackers/{phone}',
        api_id=attacker['api_id'],
        api_hash=attacker['api_hash'],
    )

    success = await _update_attacker(attacker_client, 'last_name', provided_last_name)
    if success:
        await msg.edit('اتکر {} نام خانوادگی اش به **{}** تغییر یافت.'.format(phone, provided_last_name))
    else:
        await msg.edit('مشکلی در تغییر نام خانوادگی اتکر {} به وجود آمد. لطفا دوباره امتحان کنید.'.format(phone))


@app.on_message(
    filters.regex(r'^\/setbio (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)
async def set_bio(client: Client, message: Message):
    """
    Start bio for a specific attacker.
    """
    phone = message.matches[0].group(1)
    attacker = await storage.get_attackers(phone)
    if not attacker:
        await message.reply_text('اتکری با این شماره موبایل وجود ندارد.')
        return

    provided_bio = message.reply_to_message.text
    if not provided_bio:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر بیو اتکر {}. لطفا صبر کنید...'.format(phone))
    attacker_client = Client(
        f'attacker_controller/sessions/attackers/{phone}',
        api_id=attacker['api_id'],
        api_hash=attacker['api_hash'],
    )

    success = await _update_attacker(attacker_client, 'bio', provided_bio)
    if success:
        await msg.edit('اتکر {} بیو اش به **{}** تغییر یافت.'.format(phone, provided_bio))
    else:
        await msg.edit('مشکلی در تغییر بیو اتکر {} به وجود آمد. لطفا دوباره امتحان کنید.'.format(phone))


@app.on_message(
    filters.regex(r'^\/setprofile (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)
async def set_bio(client: Client, message: Message):
    """
    Start profile photo for a specific attacker.
    """
    phone = message.matches[0].group(1)
    attacker = await storage.get_attackers(phone)
    if not attacker:
        await message.reply_text('اتکری با این شماره موبایل وجود ندارد.')
        return

    provided_photo = message.reply_to_message.photo
    if not provided_photo:
        await message.reply_text('لطفا روی یک عکس ریپلای بزنید و دستور را بفرستید.')
        return

    # download the photo
    provided_photo = await client.download_media(
        provided_photo.file_id,
        file_name='media/profile_photo.jpg',
    )

    msg = await message.reply_text('درحال تغییر عکس پروفایل اتکر {}. لطفا صبر کنید...'.format(phone))
    attacker_client = Client(
        f'attacker_controller/sessions/attackers/{phone}',
        api_id=attacker['api_id'],
        api_hash=attacker['api_hash'],
    )

    success = await _update_attacker(attacker_client, 'profile_photo', provided_photo)
    if success:
        await msg.edit('اتکر {} عکس پروفایلش اش تغییر یافت.'.format(phone, provided_photo))
    else:
        await msg.edit('مشکلی در تغییر عکس پروفایل اتکر {} به وجود آمد. لطفا دوباره امتحان کنید.'.format(phone))

    os.remove('media/profile_photo.jpg')


@app.on_message(
    filters.regex(r'^\/setusername (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)
async def set_username(client: Client, message: Message):
    """
    Start username for a specific attacker.
    """
    phone = message.matches[0].group(1)
    attacker = await storage.get_attackers(phone)
    if not attacker:
        await message.reply_text('اتکری با این شماره موبایل وجود ندارد.')
        return

    provided_username = message.reply_to_message.text
    if not provided_username:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر نام کاربری اتکر {}. لطفا صبر کنید...'.format(phone))
    attacker_client = Client(
        f'attacker_controller/sessions/attackers/{phone}',
        api_id=attacker['api_id'],
        api_hash=attacker['api_hash'],
    )

    success = await _update_attacker(attacker_client, 'username', provided_username)
    if success:

        await msg.edit('اتکر {} نام کاربری اش به **{}** تغییر یافت.'.format(phone, provided_username))
    else:
        await msg.edit(
            'مشکلی در تغییر نام کاربری اتکر {} به وجود آمد.\n'
            'ممکن است این نام کاربری از قبل رزرو شده باشد.\n'
            'همچنین توجه کنید که نام کاربری معتبر است.'.format(phone),
        )


@app.on_message(
    filters.regex(r'^\/members (\+\d+) @?(.*) (\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)
async def get_group_members(client: Client, message: Message):
    """
    Get list of group members.
    """
    phone = message.matches[0].group(1)
    attacker = await storage.get_attackers(phone)
    if not attacker:
        await message.reply_text('اتکری با این شماره یافت نشد.')
        return

    await message.reply_text('درحال گرفتن لیست ممبر های گروه. لطفا صبر کنید...')
    attacker_client = Client(
        f'attacker_controller/sessions/attackers/{phone}',
        api_id=attacker['api_id'],
        api_hash=attacker['api_hash'],
    )
    await attacker_client.connect()

    group_username = message.matches[0].group(2)
    limit = int(message.matches[0].group(3))

    member_counter = 0
    text = ''
    async for member in attacker_client.iter_chat_members(group_username, limit=limit):
        # don't capture the bots
        if member.user.is_bot:
            continue

        member_counter += 1
        if not member.user.username:
            text += f'{member_counter} - {member.user.id}\n'
        else:
            text += f'{member_counter} - @{member.user.username}\n'

        if member_counter % 50 == 0:
            await message.reply_text(text)
            text = ''

    await attacker_client.disconnect()

    # if any members still left
    if text:
        await message.reply_text(text)

    await message.reply_text('فرایند گرفتن ممبرهای گروه {} تمام شد.'.format(group_username))


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
    ext = ''
    if media:
        # find file extension
        if banner.media == 'photo':
            ext = 'jpg'
        elif banner.media == 'video' or banner.media == 'animation':
            ext = 'mp4'
        elif banner.media == 'voice':
            ext = 'ogg'
        elif banner.media == 'sticker':
            ext = 'webm'
            if banner.sticker.is_animated:
                ext = 'tgs'

        await message.reply_to_message.download(file_name=f'media/banner/banner.{ext}')

    banner_text = message.reply_to_message.caption or message.reply_to_message.text or ''

    # store the banner in cache
    await storage.redis.hset('banner', mapping={'text': banner_text, 'media_ext': ext})
    await message.reply_text('بنر با موفقیت ذخیره شد.')


app.run()
