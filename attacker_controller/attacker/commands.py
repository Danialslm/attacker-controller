import asyncio
import os
import re
from typing import Union, Tuple

from decouple import config
from pyrogram import Client
from pyrogram.errors import exceptions
from pyrogram.types import Message, SentCode

from attacker_controller import logger
from attacker_controller.attacker import Attacker
from attacker_controller.attacker.exceptions import AttackerNotFound
from attacker_controller.utils import (
    storage, auth,
    get_send_method_by_media_type,
    get_message_file_extension,
)

LOGGING_ATTACKER: Union[Client, None] = None


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


async def _web_login(phone: str) -> str:
    """
    Login to the web application by given phone.
    """
    global LOGGING_ATTACKER

    async def _error(err_reason):
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
    last_message = await LOGGING_ATTACKER.get_history(777000, limit=1)
    # the web password can get by regex or pythonic way
    # web_password = re.match(r'.*This is your login code:\n(.*)\n', last_message[0].text).group(1)
    web_password = last_message[0].text.split('\n')[1]
    res = await auth.login(phone, web_password)

    if not res[0]:
        # logging to web was failed
        return await _error(res[1])
    else:
        return 'فرایند به اتمام رسید و {}'.format(res[1])


async def _update_all_attackers(field: str, value: str) -> Tuple[int, list]:
    """
    Update all available attackers.
    Return the succeed number and Unsuccessful phone numbers.
    """
    updates = [
        asyncio.create_task(_update_attacker(atk_phone, field, value))
        for atk_phone in await storage.get_attackers()
    ]
    number_of_successes = 0
    unsuccessful_phones = []

    # get the phones that didn't update
    for succeed in await asyncio.gather(*updates):
        if succeed:
            number_of_successes += 1
        else:
            unsuccessful_phones.append(succeed[1])
    return number_of_successes, unsuccessful_phones


async def _update_attacker(phone: str, field: str, value: str) -> Union[bool, Tuple[bool, str]]:
    """
    Connect to attacker and update it by given field and value.
    Return True on success
    """
    async with await Attacker.init(phone) as attacker:
        try:
            if field in ['first_name', 'last_name', 'bio']:
                succeed = await attacker.update_profile(**{field: value})
            elif field == 'profile_photo':
                succeed = await attacker.set_profile_photo(photo=value)
            elif field == 'username':
                succeed = await attacker.update_username(value)
            else:
                return False, phone
        except Exception:
            logger.exception('An exception occurred when updating attacker.')
            return False, phone

    return succeed


async def send_code(client: Client, message: Message):
    """
    Send Login code to given phone number.
    """
    global LOGGING_ATTACKER
    # if any connected attacker was left from previous login action, disconnect it
    if LOGGING_ATTACKER and LOGGING_ATTACKER.is_connected:
        await LOGGING_ATTACKER.disconnect()

    phone = message.matches[0].group(1)

    msg = await message.reply_text('درحال ارسال درخواست. لطفا صبر کنید...')

    LOGGING_ATTACKER = Client(
        f'attacker_controller/sessions/attackers/{phone}',
        api_id=config('api_id', cast=int),
        api_hash=config('api_hash'),
    )
    await LOGGING_ATTACKER.connect()
    try:
        sent_code: SentCode = await LOGGING_ATTACKER.send_code(phone)
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
        await LOGGING_ATTACKER.disconnect()
        _remove_attacker_session(phone)
    except exceptions.PhoneNumberInvalid:
        await msg.edit('شماره وارد شده نادرست است.')
        await LOGGING_ATTACKER.disconnect()
        _remove_attacker_session(phone)
    else:
        # store phone code hash for one minute
        await storage.redis.set(f'phone_code_hash:{phone}', sent_code.phone_code_hash, 60)
        await msg.edit('کد به صورت {} ارسال شد.'.format(type_text))


async def login_attacker(client: Client, message: Message):
    """
    Login to account by provided credentials.
    """
    global LOGGING_ATTACKER
    # user should request for sending login code before logging
    if not LOGGING_ATTACKER:
        await message.reply_text('مطمئن باشید قبل از لاگین به اکانت درخواست ارسال کد را کرده اید.')
        return

    phone = message.matches[0].group(1)
    phone_code_hash = await storage.redis.get(f'phone_code_hash:{phone}') or ''

    args = message.matches[0].group(2).split()
    code, password = args[0], None
    if len(args) == 2:
        password = args[1]

    msg = await message.reply_text('درحال لاگین با اطلاعات داده شده...')

    try:
        await LOGGING_ATTACKER.sign_in(phone, phone_code_hash, code)
    except (
            exceptions.PhoneCodeExpired,
            exceptions.PhoneCodeEmpty,
            exceptions.PhoneCodeInvalid,
    ):
        await msg.edit('کد منقضی یا اشتباه است.')
    except exceptions.PhoneNumberUnoccupied:
        await msg.edit('شماره تلفن در تلگرام ثبت نشده است.')
        await LOGGING_ATTACKER.disconnect()
        _remove_attacker_session(phone)
        LOGGING_ATTACKER = None
    except exceptions.SignInFailed:
        await msg.edit('فرایند لاگین به مشکل خورد! لطفا دوباره امتحان کنید.')
    except exceptions.SessionPasswordNeeded:
        if password is not None:
            try:
                await LOGGING_ATTACKER.check_password(password)
            except (exceptions.PasswordHashInvalid, exceptions.BadRequest):
                await msg.edit('پسورد اشتباه است!')
            else:
                await msg.edit(await _web_login(phone))
        else:
            await msg.edit('اکانت دارای پسورد می‌باشد. لطفا پسورد را بعد از کد با یک فاصله ارسال کنید.')
    else:
        await msg.edit(await _web_login(phone))


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


async def remove_attacker(client: Client, message: Message):
    """
    Remove given phone from attacker list.
    """
    phones = message.matches[0].group(1).split()
    for phone in phones:
        await storage.remove_attacker(phone)
        _remove_attacker_session(phone)
    await message.reply_text('شماره(های) داده شده از لیست اتکر‌ها حذف شد.')


async def clean_attacker_list(client: Client, message: Message):
    """
    Remove all attackers.
    """
    for attacker_phone in await storage.get_attackers():
        await storage.remove_attacker(attacker_phone)

    for _, __, files in os.walk('attacker_controller/sessions/attackers/'):
        for file in files:
            _remove_attacker_session(file)

    await message.reply_text('تمام اتکرها از ربات پاک شدند.')


async def set_first_name_all(client: Client, message: Message):
    """
    Set a first name for all attackers.
    """
    provided_first_name = message.reply_to_message.text
    if not provided_first_name:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر نام کوچک اتکر‌ها. لطفا صبر کنید...')

    number_of_successes, unsuccessful_phones = await _update_all_attackers('first_name', provided_first_name)

    text = '{} اتکر نام کوچک‌شان به **{}** تغییر یافت.'.format(number_of_successes, provided_first_name)
    if unsuccessful_phones:
        text += (
            '\nمشکلی در تغییر نام کوچک اتکرهای زیر به وجود آمد.\n'
            '\n'.join(unsuccessful_phones)
        )

    await msg.edit(text, parse_mode='markdown')


async def set_last_name_all(client: Client, message: Message):
    """
    Set a last name for all attackers.
    """
    provided_last_name = message.reply_to_message.text
    if not provided_last_name:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر نام خانوادگی اتکر‌ها. لطفا صبر کنید...')

    number_of_successes, unsuccessful_phones = await _update_all_attackers('last_name', provided_last_name)

    text = '{} اتکر نام خانوادگی‌شان به **{}** تغییر یافت.'.format(number_of_successes, provided_last_name)
    if unsuccessful_phones:
        text += (
            '\nمشکلی در تغییر نام خانوادگی اتکرهای زیر به وجود آمد.\n'
            '\n'.join(unsuccessful_phones)
        )

    await msg.edit(text, parse_mode='markdown')


async def set_bio_all(client: Client, message: Message):
    """
    Set a bio for all attackers.
    """
    provided_bio = message.reply_to_message.text
    if not provided_bio:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر بیو اتکر‌ها. لطفا صبر کنید...')

    number_of_successes, unsuccessful_phones = await _update_all_attackers('bio', provided_bio)

    text = '{} اتکر بیو‌شان به **{}** تغییر یافت.'.format(number_of_successes, provided_bio)
    if unsuccessful_phones:
        text += (
            '\nمشکلی در تغییر بیو اتکرهای زیر به وجود آمد.\n'
            '\n'.join(unsuccessful_phones)
        )

    await msg.edit(text, parse_mode='markdown')


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

    number_of_successes, unsuccessful_phones = await _update_all_attackers('profile_photo', provided_photo)

    text = '{} اتکر عکس پروفایل‌شان تغییر یافت.'.format(number_of_successes)
    if unsuccessful_phones:
        text += (
            '\nمشکلی در تغییر پروفایل اتکرهای زیر به وجود آمد.\n'
            '\n'.join(unsuccessful_phones)
        )
    os.remove('media/profile_photo.jpg')

    await msg.edit(text, parse_mode='markdown')


async def set_first_name(client: Client, message: Message):
    """
    Start first name for a specific attacker.
    """
    phone = message.matches[0].group(1)

    provided_first_name = message.reply_to_message.text
    if not provided_first_name:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر نام کوچک اتکر {}. لطفا صبر کنید...'.format(phone))

    try:
        success = await _update_attacker(phone, 'first_name', provided_first_name)
    except AttackerNotFound as e:
        await msg.edit(e.message)
    else:
        if success:
            await msg.edit('اتکر {} نام کوچکش به **{}** تغییر یافت.'.format(phone, provided_first_name))
        else:
            await msg.edit('مشکلی در تغییر نام کوچک اتکر {} به وجود آمد.'.format(phone))


async def set_last_name(client: Client, message: Message):
    """
    Start last name for a specific attacker.
    """
    phone = message.matches[0].group(1)

    provided_last_name = message.reply_to_message.text
    if not provided_last_name:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر نام خانوادگی اتکر {}. لطفا صبر کنید...'.format(phone))

    try:
        success = await _update_attacker(phone, 'last_name', provided_last_name)
    except AttackerNotFound as e:
        await msg.edit(e.message)
    else:
        if success:
            await msg.edit('اتکر {} نام خانوادگی اش به **{}** تغییر یافت.'.format(phone, provided_last_name))
        else:
            await msg.edit('مشکلی در تغییر نام خانوادگی اتکر {} به وجود آمد.'.format(phone))


async def set_bio(client: Client, message: Message):
    """
    Start bio for a specific attacker.
    """
    phone = message.matches[0].group(1)

    provided_bio = message.reply_to_message.text
    if not provided_bio:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر بیو اتکر {}. لطفا صبر کنید...'.format(phone))

    try:
        success = await _update_attacker(phone, 'bio', provided_bio)
    except AttackerNotFound as e:
        await msg.edit(e.message)
    else:
        if success:
            await msg.edit('اتکر {} بیو اش به **{}** تغییر یافت.'.format(phone, provided_bio))
        else:
            await msg.edit('مشکلی در تغییر بیو اتکر {} به وجود آمد.'.format(phone))


async def set_profile_photo(client: Client, message: Message):
    """
    Start profile photo for a specific attacker.
    """
    phone = message.matches[0].group(1)

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

    try:
        success = await _update_attacker(phone, 'profile_photo', provided_photo)
    except AttackerNotFound as e:
        await msg.edit(e.message)
    else:
        if success:
            await msg.edit('اتکر {} عکس پروفایلش اش تغییر یافت.'.format(phone, provided_photo))
        else:
            await msg.edit('مشکلی در تغییر عکس پروفایل اتکر {} به وجود آمد.'.format(phone))
    finally:
        os.remove('media/profile_photo.jpg')


async def set_username(client: Client, message: Message):
    """
    Start username for a specific attacker.
    """
    phone = message.matches[0].group(1)

    provided_username = message.reply_to_message.text
    if not provided_username:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    msg = await message.reply_text('درحال تغییر نام کاربری اتکر {}. لطفا صبر کنید...'.format(phone))

    try:
        success = await _update_attacker(phone, 'username', provided_username)
    except AttackerNotFound as e:
        await msg.edit(e.message)
    else:
        if success:
            await msg.edit('اتکر {} نام کاربری اش به **{}** تغییر یافت.'.format(phone, provided_username))
        else:
            await msg.edit(
                'مشکلی در تغییر نام کاربری اتکر {} به وجود آمد.\n'
                'ممکن است این نام کاربری از قبل رزرو شده باشد.\n'
                'همچنین توجه کنید که نام کاربری معتبر است.'.format(phone),
            )


async def get_group_members(client: Client, message: Message):
    """
    Get list of group members.
    """
    phone = message.matches[0].group(1)
    group_id = message.matches[0].group(2).replace('https://t.me/', '')
    limit = int(message.matches[0].group(3))

    msg = await message.reply_text('درحال گرفتن لیست ممبر های گروه. لطفا صبر کنید...')

    # if the user entered the group chat id, convert it to int
    if group_id.lstrip('-').isdigit():
        group_id = int(group_id)

    # only can get groups member
    try:
        target_chat = await client.get_chat(group_id)
    except exceptions.PeerIdInvalid:
        await msg.edit('ایدی نامعتبر است.')
        return
    else:
        if target_chat.type not in ['group', 'supergroup']:
            await msg.edit('هدف گروه یا سوپرگروه نیست.')
            return

    member_counter = 0
    text = ''
    try:
        async with await Attacker.init(phone) as attacker:
            async for member in attacker.iter_chat_members(group_id, limit=limit):
                # don't capture the bots and the users that doesn't have username
                if member.user.is_bot or not member.user.username:
                    continue

                member_counter += 1
                if not member.user.username:
                    text += f'{member_counter} - {member.user.id}\n'
                else:
                    text += f'{member_counter} - @{member.user.username}\n'

                if member_counter % 50 == 0:
                    await message.reply_text(text)
                    text = ''
    except AttackerNotFound as e:
        await msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await msg.edit(
            'سشن اتکر {} در ربات منسوخ شده است. لطفا اتکر را یک بار از ربات پاک و سپس اضافه کنید.'.format(phone))
    except Exception as e:
        exception_class = e.__class__.__name__
        await msg.edit('خطای غیر منتظره ای هنگام انجام عملیات رخ داده است.\n {}  -{}'.format(exception_class, e))
    else:
        # if any members still left
        if text:
            await message.reply_text(text)

        await message.reply_text('فرایند گرفتن ممبرهای گروه {} تمام شد.'.format(group_id))


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


async def start_attack(attacker: Attacker, message: Message, targets: list, method: str, banner: dict) -> int:
    """
    Start attacking on given targets.

    If any FloodWait error occurred during attack, wait as long as flood wait time and
    get start where the flood occurred.

    Returns number of succeed attacks.
    """
    succeed_attacks = 0

    for index, target in enumerate(targets):
        try:
            succeed_attacks += await attacker.attack(target, method, banner)
        except exceptions.FloodWait as e:
            # wait as long as flood wait time and then get start where the flood occurred
            await message.edit(
                'اکانت به مدت {} ثانیه فلود خورد. '
                'بعد از اتمام فلود اتک دوباره شروع خواهد شد.\n'
                'تعداد اتک های زده شده تا به الان: {}.'.format(e.x, succeed_attacks)
            )
            await asyncio.sleep(e.x)
            targets = targets[index:]
            succeed_attacks += await start_attack(attacker, message, targets, method, banner)
            break
        except exceptions.PeerFlood:
            await message.edit('درحال حاظر این اتکر به محدود شده است.')
            break
    return succeed_attacks


async def attack(client: Client, message: Message):
    """
    Attack to a list of users or groups.
    """
    phone = message.matches[0].group(1)

    # it is not possible to attack multiple places simultaneously
    if await storage.redis.sismember('attacking_attackers', phone):
        await message.reply_text('درحال حاضر این اتکر درحال اتک است.')
        return

    # get usernames and ids from replied text
    targets = re.findall(r'(?<=@)\w{5,}|\d{6,}', message.reply_to_message.text)

    if not targets:
        return

    msg = await message.reply_text('درحال اتک به لیست با شماره {}. لطفا صبر کنید...'.format(phone))

    banner = await storage.redis.hgetall('banner')
    method = get_send_method_by_media_type(banner['media_type'])

    try:
        async with await Attacker.init(phone) as attacker:
            await storage.redis.sadd('attacking_attackers', attacker.phone)
            succeed_attacks = await start_attack(attacker, msg, targets, method, banner)
            await storage.redis.srem('attacking_attackers', attacker.phone)
    except AttackerNotFound as e:
        await msg.edit(e.message)
    else:
        await msg.edit('اتک تمام شد. تعداد اتک های موفق: {}.'.format(succeed_attacks))
