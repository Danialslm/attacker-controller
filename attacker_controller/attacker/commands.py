import asyncio
import os
import re
from typing import Union, Tuple

from decouple import config
from pyrogram import Client, filters
from pyrogram.errors import exceptions
from pyrogram.types import Message, SentCode

from attacker_controller import logger
from attacker_controller.attacker import Attacker
from attacker_controller.attacker.exceptions import AttackerNotFound
from attacker_controller.utils import (
    storage,
    auth,
    get_send_method_by_media_type,
    remove_attacker_session,
)
from attacker_controller.utils.custom_filters import admin

LOGGING_ATTACKER: Union[Client, None] = None


async def _web_login(phone: str) -> str:
    """Login to the web application by given phone."""
    global LOGGING_ATTACKER

    def _error(err_reason):
        return (
            'خطایی هنگام ورود به https://my.telegram.org به وجود آمد و اکانت لاگ اوت شد.\n'
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
        return _error(res[1])
    else:
        return 'فرایند به اتمام رسید و شماره ارسال شده به لیست اتکرها افزوده شد.'


async def _update_all_attackers(field: str, value: str) -> Tuple[int, list]:
    """
    Update all available attackers.

    Return number of successes and Unsuccessful phone numbers.
    """
    number_of_successes = 0
    unsuccessful_phones = []

    # get the phones that didn't update
    for atk_phone in await storage.get_attackers():
        try:
            succeed = await _update_attacker(atk_phone, field, value)
        except Exception as e:
            logger.error(f'Error on updating attacker {atk_phone}: {e}')
            unsuccessful_phones.append(atk_phone)
        else:
            if succeed:
                number_of_successes += 1
            else:
                unsuccessful_phones.append(atk_phone)
    return number_of_successes, unsuccessful_phones


async def _update_attacker(
    phone: str, field: str, value: str
) -> Union[bool, Tuple[bool, str]]:
    """
    Connect to attacker and update it by given field and value.

    Return True on success
    """
    async with await Attacker.init(phone) as attacker:
        if field in ['first_name', 'last_name', 'bio']:
            succeed = await attacker.update_profile(**{field: value})
        elif field == 'profile_photo':
            succeed = await attacker.set_profile_photo(photo=value)
        elif field == 'username':
            succeed = await attacker.update_username(value)
        else:
            succeed = False
    return succeed


@Client.on_message(
    filters.regex(r'^\/sendcode (\+\d+)$') & filters.group & ~filters.edited & admin
)
async def send_code(client: Client, message: Message):
    """Send Login code to given phone number."""
    global LOGGING_ATTACKER
    # if any connected attacker was left from previous login action, disconnect it
    if LOGGING_ATTACKER and LOGGING_ATTACKER.is_connected:
        await LOGGING_ATTACKER.disconnect()

    phone = message.matches[0].group(1)

    status_msg = await message.reply_text('درحال ارسال درخواست. لطفا صبر کنید...')

    LOGGING_ATTACKER = Client(
        f'attacker_controller/sessions/attackers/{phone}',
        api_id=config('api_id', cast=int),
        api_hash=config('api_hash'),
    )
    await LOGGING_ATTACKER.connect()
    code_sent = False
    try:
        sent_code: SentCode = await LOGGING_ATTACKER.send_code(phone)
        code_sent = True
    except exceptions.FloodWait as e:
        await status_msg.edit(
            'ارسال درخواست با محدودیت مواجه شده است. لطفا {} ثانیه دیگر امتحان کنید.'.format(
                e.x
            )
        )
    except exceptions.PhoneNumberInvalid:
        await status_msg.edit('شماره وارد شده نادرست است.')
    except Exception as e:
        exception_class = e.__class__.__name__
        await status_msg.edit(
            'خطای غیر منتظره‌ای هنگام ارسال کد رخ داده است. {} - {}'.format(
                exception_class, e
            )
        )
    else:
        if sent_code.type == 'app':
            type_text = 'پیام در پیوی تلگرام'
        elif sent_code.type == 'sms':
            type_text = 'اس ام اس'
        elif sent_code.type == 'call':
            type_text = 'تماس تلفنی'
        else:
            type_text = sent_code.type
        # store phone code hash for one minute
        await storage.redis.set(
            f'phone_code_hash:{phone}', sent_code.phone_code_hash, 60
        )
        await status_msg.edit('کد به صورت {} ارسال شد.'.format(type_text))
    finally:
        # only if the code didn't send, disconnect the client
        # because we need the client in next step which is login
        if not code_sent:
            await LOGGING_ATTACKER.disconnect()
            remove_attacker_session(phone)


@Client.on_message(
    filters.regex(r'^\/login (\+\d+) (.+)$') & filters.group & ~filters.edited & admin
)
async def login_attacker(client: Client, message: Message):
    """Login to account by provided credentials."""
    global LOGGING_ATTACKER

    phone = message.matches[0].group(1)
    # user must requested login code for the phone
    if LOGGING_ATTACKER is None or LOGGING_ATTACKER.phone != phone:
        await message.reply_text(
            'مطمئن باشید قبل از لاگین به اکانت درخواست ارسال کد برای این شماره را کرده اید.'
        )
        return

    phone_code_hash = await storage.redis.get(f'phone_code_hash:{phone}') or ''

    args = message.matches[0].group(2).split()
    code, password = args[0], None
    # set the password if the user provided it
    if len(args) == 2:
        password = args[1]

    status_msg = await message.reply_text('درحال لاگین با اطلاعات داده شده...')

    async def _check_password():
        if password is not None:
            try:
                await LOGGING_ATTACKER.check_password(password)
            except (exceptions.PasswordHashInvalid, exceptions.BadRequest):
                await status_msg.edit('پسورد اشتباه است!')
            else:
                await status_msg.edit(await _web_login(phone))
                await LOGGING_ATTACKER.disconnect()
        else:
            await status_msg.edit(
                'اکانت دارای پسورد می‌باشد. لطفا پسورد را بعد از کد با یک فاصله ارسال کنید.'
            )

    try:
        await LOGGING_ATTACKER.sign_in(phone, phone_code_hash, code)
    except (
        exceptions.PhoneCodeExpired,
        exceptions.PhoneCodeEmpty,
        exceptions.PhoneCodeInvalid,
    ):
        await status_msg.edit('کد منقضی یا اشتباه است.')
    except exceptions.PhoneNumberUnoccupied:
        await status_msg.edit('شماره تلفن هنوز استفاده نمی‌شود.')
    except exceptions.SignInFailed:
        await status_msg.edit('فرایند لاگین ناموفق بود.')
    except exceptions.SessionPasswordNeeded:
        await _check_password()
    except Exception as e:
        exception_class = e.__class__.__name__
        await status_msg.edit(
            'خطای غیر منتظره‌ای هنگام ارسال کد رخ داده است. {} - {}'.format(
                exception_class, e
            )
        )
    else:
        await status_msg.edit(await _web_login(phone))
        await LOGGING_ATTACKER.disconnect()


@Client.on_message(
    filters.command('setfirstnameall')
    & filters.group
    & ~filters.edited
    & filters.reply
    & admin
)
async def set_first_name_all(client: Client, message: Message):
    """Set a first name for all attackers."""
    provided_first_name = message.reply_to_message.text
    if not provided_first_name:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    status_msg = await message.reply_text(
        'درحال تغییر نام کوچک اتکر‌ها. لطفا صبر کنید...'
    )

    number_of_successes, unsuccessful_phones = await _update_all_attackers(
        'first_name', provided_first_name
    )

    text = '{} اتکر نام کوچک‌شان به **{}** تغییر یافت.'.format(
        number_of_successes, provided_first_name
    )
    if unsuccessful_phones:
        text += '\nمشکلی در تغییر نام کوچک اتکرهای زیر به وجود آمد.\n'
        text += '\n'.join(unsuccessful_phones)

    await status_msg.edit(text, parse_mode='markdown')


@Client.on_message(
    filters.command('setlastnameall')
    & filters.group
    & ~filters.edited
    & filters.reply
    & admin
)
async def set_last_name_all(client: Client, message: Message):
    """Set a last name for all attackers."""
    provided_last_name = message.reply_to_message.text
    if not provided_last_name:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    status_msg = await message.reply_text(
        'درحال تغییر نام خانوادگی اتکر‌ها. لطفا صبر کنید...'
    )

    number_of_successes, unsuccessful_phones = await _update_all_attackers(
        'last_name', provided_last_name
    )

    text = '{} اتکر نام خانوادگی‌شان به **{}** تغییر یافت.'.format(
        number_of_successes, provided_last_name
    )
    if unsuccessful_phones:
        text += '\nمشکلی در تغییر نام خانوادگی اتکرهای زیر به وجود آمد.\n'
        text += '\n'.join(unsuccessful_phones)

    await status_msg.edit(text, parse_mode='markdown')


@Client.on_message(
    filters.command('setbioall')
    & filters.group
    & ~filters.edited
    & filters.reply
    & admin
)
async def set_bio_all(client: Client, message: Message):
    """Set a bio for all attackers."""
    provided_bio = message.reply_to_message.text
    if not provided_bio:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    status_msg = await message.reply_text('درحال تغییر بیو اتکر‌ها. لطفا صبر کنید...')

    number_of_successes, unsuccessful_phones = await _update_all_attackers(
        'bio', provided_bio
    )

    text = '{} اتکر بیو‌شان به **{}** تغییر یافت.'.format(
        number_of_successes, provided_bio
    )
    if unsuccessful_phones:
        text += '\nمشکلی در تغییر بیو اتکرهای زیر به وجود آمد.\n'
        text += '\n'.join(unsuccessful_phones)

    await status_msg.edit(text, parse_mode='markdown')


@Client.on_message(
    filters.command('setprofileall')
    & filters.group
    & ~filters.edited
    & filters.reply
    & admin
)
async def set_profile_photo_all(client: Client, message: Message):
    """Set a profile photo for all attackers."""
    provided_photo = message.reply_to_message.photo
    if not provided_photo:
        await message.reply_text('لطفا روی یک عکس ریپلای بزنید و دستور را بفرستید.')
        return

    status_msg = await message.reply_text(
        'درحال تغییر عکس پروفایل اتکر‌ها. لطفا صبر کنید...'
    )

    # download the photo
    provided_photo = await client.download_media(
        provided_photo.file_id,
        file_name='media/profile_photo.jpg',
    )

    number_of_successes, unsuccessful_phones = await _update_all_attackers(
        'profile_photo', provided_photo
    )

    text = '{} اتکر عکس پروفایل‌شان تغییر یافت.'.format(number_of_successes)
    if unsuccessful_phones:
        text += '\nمشکلی در تغییر پروفایل اتکرهای زیر به وجود آمد.\n'
        text += '\n'.join(unsuccessful_phones)
    os.remove('media/profile_photo.jpg')

    await status_msg.edit(text, parse_mode='markdown')


@Client.on_message(
    filters.regex(r'^\/setfirstname (\+\d+)$') & filters.group & ~filters.edited & admin
)
async def set_first_name(client: Client, message: Message):
    """Start first name for a specific attacker."""
    phone = message.matches[0].group(1)

    provided_first_name = message.reply_to_message.text
    if not provided_first_name:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    status_msg = await message.reply_text(
        'درحال تغییر نام کوچک اتکر {}. لطفا صبر کنید...'.format(phone)
    )

    try:
        success = await _update_attacker(phone, 'first_name', provided_first_name)
    except AttackerNotFound as e:
        await status_msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await status_msg.edit(
            'سشن اتکر {} در ربات منسوخ شده است. لطفا اتکر را یک بار از ربات پاک و سپس اضافه کنید.'.format(
                phone
            )
        )
    else:
        if success:
            await status_msg.edit(
                'اتکر {} نام کوچکش به **{}** تغییر یافت.'.format(
                    phone, provided_first_name
                )
            )
        else:
            await status_msg.edit(
                'مشکلی در تغییر نام کوچک اتکر {} به وجود آمد.'.format(phone)
            )


@Client.on_message(
    filters.regex(r'^\/setlastname (\+\d+)$') & filters.group & ~filters.edited & admin
)
async def set_last_name(client: Client, message: Message):
    """Start last name for a specific attacker."""
    phone = message.matches[0].group(1)

    provided_last_name = message.reply_to_message.text
    if not provided_last_name:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    status_msg = await message.reply_text(
        'درحال تغییر نام خانوادگی اتکر {}. لطفا صبر کنید...'.format(phone)
    )

    try:
        success = await _update_attacker(phone, 'last_name', provided_last_name)
    except AttackerNotFound as e:
        await status_msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await status_msg.edit(
            'سشن اتکر {} در ربات منسوخ شده است. لطفا اتکر را یک بار از ربات پاک و سپس اضافه کنید.'.format(
                phone
            )
        )
    else:
        if success:
            await status_msg.edit(
                'اتکر {} نام خانوادگی اش به **{}** تغییر یافت.'.format(
                    phone, provided_last_name
                )
            )
        else:
            await status_msg.edit(
                'مشکلی در تغییر نام خانوادگی اتکر {} به وجود آمد.'.format(phone)
            )


@Client.on_message(
    filters.regex(r'^\/setbio (\+\d+)$') & filters.group & ~filters.edited & admin
)
async def set_bio(client: Client, message: Message):
    """Start bio for a specific attacker."""
    phone = message.matches[0].group(1)

    provided_bio = message.reply_to_message.text
    if not provided_bio:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    status_msg = await message.reply_text(
        'درحال تغییر بیو اتکر {}. لطفا صبر کنید...'.format(phone)
    )

    try:
        success = await _update_attacker(phone, 'bio', provided_bio)
    except AttackerNotFound as e:
        await status_msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await status_msg.edit(
            'سشن اتکر {} در ربات منسوخ شده است. لطفا اتکر را یک بار از ربات پاک و سپس اضافه کنید.'.format(
                phone
            )
        )
    else:
        if success:
            await status_msg.edit(
                'اتکر {} بیو اش به **{}** تغییر یافت.'.format(phone, provided_bio)
            )
        else:
            await status_msg.edit(
                'مشکلی در تغییر بیو اتکر {} به وجود آمد.'.format(phone)
            )


@Client.on_message(
    filters.regex(r'^\/setprofile (\+\d+)$') & filters.group & ~filters.edited & admin
)
async def set_profile_photo(client: Client, message: Message):
    """Start profile photo for a specific attacker."""
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

    status_msg = await message.reply_text(
        'درحال تغییر عکس پروفایل اتکر {}. لطفا صبر کنید...'.format(phone)
    )

    try:
        success = await _update_attacker(phone, 'profile_photo', provided_photo)
    except AttackerNotFound as e:
        await status_msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await status_msg.edit(
            'سشن اتکر {} در ربات منسوخ شده است. لطفا اتکر را یک بار از ربات پاک و سپس اضافه کنید.'.format(
                phone
            )
        )
    else:
        if success:
            await status_msg.edit(
                'اتکر {} عکس پروفایلش اش تغییر یافت.'.format(phone, provided_photo)
            )
        else:
            await status_msg.edit(
                'مشکلی در تغییر عکس پروفایل اتکر {} به وجود آمد.'.format(phone)
            )
    finally:
        os.remove('media/profile_photo.jpg')


@Client.on_message(
    filters.regex(r'^\/setusername (\+\d+)$') & filters.group & ~filters.edited & admin
)
async def set_username(client: Client, message: Message):
    """Start username for a specific attacker."""
    phone = message.matches[0].group(1)

    provided_username = message.reply_to_message.text
    if not provided_username:
        await message.reply_text('لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.')
        return

    status_msg = await message.reply_text(
        'درحال تغییر نام کاربری اتکر {}. لطفا صبر کنید...'.format(phone)
    )

    try:
        success = await _update_attacker(phone, 'username', provided_username)
    except AttackerNotFound as e:
        await status_msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await status_msg.edit(
            'سشن اتکر {} در ربات منسوخ شده است. لطفا اتکر را یک بار از ربات پاک و سپس اضافه کنید.'.format(
                phone
            )
        )
    else:
        if success:
            await status_msg.edit(
                'اتکر {} نام کاربری اش به **{}** تغییر یافت.'.format(
                    phone, provided_username
                )
            )
        else:
            await status_msg.edit(
                'مشکلی در تغییر نام کاربری اتکر {} به وجود آمد.\n'
                'ممکن است این نام کاربری از قبل رزرو شده باشد.\n'
                'همچنین توجه کنید که نام کاربری معتبر است.'.format(phone),
            )


@Client.on_message(
    filters.regex(r'^\/members (\+\d+) @?(.*) (\d+)$')
    & filters.group
    & ~filters.edited
    & admin
)
async def get_group_members(client: Client, message: Message):
    """Get list of group members."""
    phone = message.matches[0].group(1)
    group_id = message.matches[0].group(2)
    # if the link was not for a private group
    if 'joinchat' not in group_id:
        group_id = group_id.replace('https://t.me/', '')
        private_target = False
    else:
        private_target = True
    limit = int(message.matches[0].group(3))

    status_msg = await message.reply_text(
        'درحال گرفتن لیست ممبر های گروه. لطفا صبر کنید...'
    )

    # if the user entered the group chat id, convert it to int
    if group_id.lstrip('-').isdigit():
        group_id = int(group_id)

    if not private_target:
        # only can get groups member
        try:
            target_chat = await client.get_chat(group_id)
        except exceptions.PeerIdInvalid:
            await status_msg.edit('ایدی نامعتبر است.')
            return
        else:
            if target_chat.type not in ['group', 'supergroup']:
                await status_msg.edit('هدف گروه یا سوپرگروه نیست.')
                return

    member_counter = 0
    text = ''
    try:
        async with await Attacker.init(phone) as attacker:
            # for private chats, join if attacker wasn't already joined and get its chat id
            if private_target:
                try:
                    target_chat = await attacker.join_chat(group_id)
                except exceptions.UserAlreadyParticipant:
                    target_chat = await attacker.get_chat(group_id)
                group_id = target_chat.id

            async for member in attacker.iter_chat_members(group_id, limit=limit):
                # don't capture the bots and the users that doesn't have username
                if member.user.is_bot or not member.user.username:
                    continue

                member_counter += 1
                text += f'{member_counter} - {member.user.username if member.user.username else member.user.id}\n'

                # send members in lists of 50
                if member_counter % 50 == 0:
                    await message.reply_text(text)
                    text = ''
    except AttackerNotFound as e:
        await status_msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await status_msg.edit(
            'سشن اتکر {} در ربات منسوخ شده است. لطفا اتکر را یک بار از ربات پاک و سپس اضافه کنید.'.format(
                phone
            )
        )
    except Exception as e:
        exception_class = e.__class__.__name__
        await status_msg.edit(
            'خطای غیر منتظره ای هنگام انجام عملیات رخ داده است.\n {}  - {}'.format(
                exception_class, e
            )
        )
    else:
        # if any members still left
        if text:
            await message.reply_text(text)

        await message.reply_text(
            'فرایند گرفتن ممبرهای گروه {} تمام شد.'.format(group_id)
        )


async def start_attack(
    attacker: Attacker,
    message: Message,
    targets: list,
    method: str,
    banner: dict,
) -> Tuple[int, bool]:
    """
    Start attacking on given targets.

    If any FloodWait error occurred during attack, wait as long as flood wait time and
    get start where the flood occurred.

    :returns: (number of successes, is peer flooded)
    """
    succeed_attacks = 0
    peer_flood = False
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
            _succeed_attacks, _ = await start_attack(
                attacker, message, targets, method, banner
            )
            succeed_attacks += _succeed_attacks
            break
        except exceptions.PeerFlood:
            peer_flood = True
            break
    return succeed_attacks, peer_flood


@Client.on_message(
    filters.regex(r'^\/attack (\+\d+)$')
    & filters.group
    & ~filters.edited
    & filters.reply
    & admin
)
async def attack(client: Client, message: Message):
    """Attack to a list of users or groups."""
    phone = message.matches[0].group(1)

    # it is not possible to attack multiple places simultaneously
    if await storage.redis.sismember('attacking_attackers', phone):
        await message.reply_text('درحال حاضر این اتکر درحال اتک است.')
        return

    # check banner was set
    banner = await storage.redis.hgetall('banner')
    if not bool(banner):
        await message.reply('درحال حاظر بنری برای ربات تنظیم نشده است.')
        return

    # get usernames and ids from replied text
    targets = re.findall(r'(?<=@)\w{5,}|\d{6,}', message.reply_to_message.text)

    if not targets:
        return

    status_msg = await message.reply_text(
        'درحال اتک به لیست با شماره {}. لطفا صبر کنید...'.format(phone)
    )
    method = get_send_method_by_media_type(banner['media_type'])
    try:
        async with await Attacker.init(phone) as attacker:
            await storage.redis.sadd('attacking_attackers', phone)
            succeed_attacks, is_flooded = await start_attack(
                attacker, status_msg, targets, method, banner
            )
    except AttackerNotFound as e:
        await status_msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await status_msg.edit(
            'سشن اتکر {} در ربات منسوخ شده است. لطفا اتکر را یک بار از ربات پاک و سپس اضافه کنید.'.format(
                phone
            )
        )
    except Exception as e:
        exception_class = e.__class__.__name__
        await status_msg.edit(
            'خطای غیر منتظره ای هنگام انجام عملیات رخ داده است.\n {}  - {}'.format(
                exception_class, e
            )
        )
    else:
        if is_flooded:
            if succeed_attacks > 0:
                text = (
                    'اتکر در حین اتک به محدودیت خورد. تعداد اتک های موفق: {}.'.format(
                        succeed_attacks
                    )
                )
            else:
                text = 'اتکر به محدودیت خورده است.'
        else:
            text = 'اتک تمام شد. تعداد اتک های موفق: {}.'.format(succeed_attacks)
        await status_msg.edit(text)
    finally:
        await storage.redis.srem('attacking_attackers', phone)
