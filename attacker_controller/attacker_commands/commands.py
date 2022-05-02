import asyncio
import os
import re
from typing import Union

from decouple import config
from pyrogram import Client
from pyrogram.errors import exceptions
from pyrogram.types import Message, SentCode

from attacker_controller import logger
from attacker_controller.utils import storage, auth

LOGGING_ATTACKER: Union[Client, None] = None


class AttackerNotFound(Exception):
    """ Attacker with provided phone number doesn't exist. """

    def __init__(self):
        self.message = 'اتکری با این شماره یافت نشد.'
        super().__init__(self.message)


class Attacker:
    """
    Simple context manager which connect and disconnect to given attacker phone.
    """

    def __init__(self, phone):
        self.phone = phone

    async def __aenter__(self):
        attacker_info = await storage.get_attackers(self.phone)
        if not attacker_info:
            raise AttackerNotFound

        self.attacker = Client(
            f'attacker_controller/sessions/attackers/{self.phone}',
            api_id=attacker_info['api_id'],
            api_hash=attacker_info['api_hash'],
        )
        await self.attacker.connect()
        return self.attacker

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.attacker.disconnect()


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


async def _update_all_attackers(field: str, value: str) -> int:
    """
    Update all available attackers.
    Return the successes number.
    """
    updates = [
        asyncio.create_task(_update_attacker(atk_phone, field, value))
        for atk_phone in await storage.get_attackers()
    ]
    successes = sum(await asyncio.gather(*updates))
    return successes


async def _update_attacker(phone: str, field: str, value: str) -> bool:
    """
    Connect to attacker and update it by given field and value.
    Return True on success.
    """
    async with Attacker(phone) as attacker:
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

    return success


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
    except (exceptions.PhoneCodeExpired, exceptions.PhoneCodeEmpty, exceptions.PhoneCodeInvalid):
        await msg.edit('کد منقضی یا اشتباه است.')
    except exceptions.PhoneNumberUnoccupied:
        await msg.edit('شماره تلفن در تلگرام ثبت نشده است.')
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
    finally:
        await storage.redis.delete(f'phone_code_hash:{phone}')
        await LOGGING_ATTACKER.disconnect()
        LOGGING_ATTACKER = None


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
    phone = message.matches[0].group(1)
    await storage.remove_attacker(phone)
    _remove_attacker_session(phone)
    await message.reply_text('شماره داده شده از لیست اتکر‌ها حذف شد.')


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
            await msg.edit('مشکلی در تغییر نام کوچک اتکر {} به وجود آمد. لطفا دوباره امتحان کنید.'.format(phone))


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
            await msg.edit('مشکلی در تغییر نام خانوادگی اتکر {} به وجود آمد. لطفا دوباره امتحان کنید.'.format(phone))


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
            await msg.edit('مشکلی در تغییر بیو اتکر {} به وجود آمد. لطفا دوباره امتحان کنید.'.format(phone))


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
            await msg.edit('مشکلی در تغییر عکس پروفایل اتکر {} به وجود آمد. لطفا دوباره امتحان کنید.'.format(phone))
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

    group_username = message.matches[0].group(2)
    limit = int(message.matches[0].group(3))

    msg = await message.reply_text('درحال گرفتن لیست ممبر های گروه. لطفا صبر کنید...')

    member_counter = 0
    text = ''
    try:
        async with Attacker(phone) as attacker:
            async for member in attacker.iter_chat_members(group_username, limit=limit):
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
    except AttackerNotFound as e:
        await msg.edit(e.message)
    else:
        # if any members still left
        if text:
            await message.reply_text(text)

        await message.reply_text('فرایند گرفتن ممبرهای گروه {} تمام شد.'.format(group_username))


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
        if banner.media == 'photo':
            banner_media_ext = 'jpg'
        elif banner.media == 'video' or banner.media == 'animation':
            banner_media_ext = 'mp4'
        elif banner.media == 'voice':
            banner_media_ext = 'ogg'
        elif banner.media == 'sticker':
            banner_media_ext = 'webm'
            if banner.sticker.is_animated:
                banner_media_ext = 'tgs'

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


async def _attack(attacker: Client, target: str, method, banner: dict):
    """
    Send the banner to target.
    Return True on success.
    """
    # if the target chat type was group, join to it
    target_chat = await attacker.get_chat(target)
    if target_chat.type in ['supergroup', 'group']:
        await target_chat.join()

    send = getattr(attacker, method)

    try:
        if banner['media_type']:
            await send(target, f'media/banner/banner.{banner["media_ext"]}', banner['text'])
        else:
            await send(target, banner['text'])
        return True
    except Exception as e:
        logger.error(e.message)
        return False


async def attack(client: Client, message: Message):
    """
    Attack to a list of users or groups.
    """
    phone = message.matches[0].group(1)

    # get usernames and ids from replied text
    targets = re.findall(r'(?<=@)\w{5,}|\d{6,}', message.reply_to_message.text)

    if not targets:
        return

    msg = await message.reply_text('درحال اتک به لیست با شماره {}. لطفا صبر کنید...'.format(phone))

    banner = await storage.redis.hgetall('banner')
    # sending method based on banner media type
    if banner['media_type'] == 'photo':
        method = 'send_photo'
    elif banner['media_type'] == 'video':
        method = 'send_video'
    elif banner['media_type'] == 'animation':
        method = 'send_animation'
    elif banner['media_type'] == 'voice':
        method = 'send_voice'
    elif banner['media_type'] == 'sticker':
        method = 'send_sticker'
    else:
        method = 'send_message'

    try:
        async with Attacker(phone) as attacker:
            attacks = [
                asyncio.create_task(_attack(attacker, target, method, banner))
                for target in targets
            ]
            successes = sum(await asyncio.gather(*attacks))
    except AttackerNotFound as e:
        await msg.edit(e.message)
    else:
        await msg.edit('اتک تمام شد. تعداد موفقیت ها {}.'.format(successes))
