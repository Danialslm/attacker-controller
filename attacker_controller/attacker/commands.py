import asyncio
import os
import re
from typing import Union, Tuple

from decouple import config
from pyrogram import Client, filters
from pyrogram.errors import exceptions
from pyrogram.types import Message, SentCode

from attacker_controller import logger, messages
from attacker_controller.attacker import Attacker
from attacker_controller.attacker.exceptions import AttackerNotFound
from attacker_controller.utils import (
    storage,
    auth,
    get_send_method_by_media_type,
    remove_attacker_session,
)
from attacker_controller.utils.custom_filters import admin

LOGGING_IN_ATTACKER: Union[Client, None] = None


async def _web_login(phone: str) -> Tuple[bool, str]:
    """
    Login to the web application.

    Returns:
        tuple: Contains a bool that shows the process was successful or not and
        a str that can be error message or success message.
    """
    global LOGGING_IN_ATTACKER

    def _error(err_reason):
        return False, (
            'خطایی هنگام ورود به https://my.telegram.org به وجود آمد.\n'
            'دلیل خطا:\n{}'.format(err_reason)
        )

    # now it's time to get account api id and api hash
    res = await auth.send_password(phone)
    if not res[0]:
        # sending password was failed
        return _error(res[1])

    # get password from official telegram bot chat history
    last_message = await LOGGING_IN_ATTACKER.get_history(777000, limit=1)
    web_password = last_message[0].text.split('\n')[1]
    res = await auth.login(phone, web_password)

    if not res[0]:
        # logging to web was failed
        return _error(res[1])
    else:
        return True, 'فرایند به اتمام رسید و شماره ارسال شده به لیست اتکرها افزوده شد.'


async def _update_all_attackers(field: str, value: str) -> Tuple[int, list]:
    """
    Update all attackers by given value.

    Args:
        field (str): Section that should be updated. Like first name or last name.
        value (str): New value for updating.

    Returns:
        tuple: Contains an int which is number of succeed updating and
        a list that contains phones that didn't update.
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


async def _update_attacker(phone: str, field: str, value: str) -> bool:
    """
    Connect to attacker and update it by given value.

    Args:
        phone (str): Account phone number.
        field (str): Section that should be updated. Like first name or last name.
        value (str): New value for updating.

    Returns:
        bool: True of successful, False otherwise.
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


@Client.on_message(filters.regex(r'^\/sendcode (\+\d+)$') & ~filters.edited & admin)
async def send_code(client: Client, message: Message):
    """Send Login code to given phone number."""
    global LOGGING_IN_ATTACKER
    # if any connected attacker was left from previous login action, disconnect it
    if LOGGING_IN_ATTACKER and LOGGING_IN_ATTACKER.is_connected:
        await LOGGING_IN_ATTACKER.disconnect()

    phone = message.matches[0].group(1)

    status_msg = await message.reply_text(messages.PLEASE_WAIT)

    LOGGING_IN_ATTACKER = Client(
        f'attacker_controller/sessions/attackers/{phone}',
        api_id=config('api_id', cast=int),
        api_hash=config('api_hash'),
    )
    await LOGGING_IN_ATTACKER.connect()
    code_sent = False
    try:
        sent_code: SentCode = await LOGGING_IN_ATTACKER.send_code(phone)
        code_sent = True
    except exceptions.FloodWait as e:
        await status_msg.edit(messages.SEND_CODE_FLOOD.format(e.x))
    except exceptions.PhoneNumberInvalid:
        await status_msg.edit(messages.PHONE_NUMBER_INVALID)
    except Exception as e:
        exception_class = e.__class__.__name__
        await status_msg.edit(messages.UNEXPECTED_ERROR.format(exception_class, e))
    else:
        if sent_code.type == 'app':
            type_text = messages.APP_CODE_SENT
        elif sent_code.type == 'sms':
            type_text = messages.SMS_CODE_SENT
        elif sent_code.type == 'call':
            type_text = messages.CALL_CODE_SENT
        else:
            type_text = sent_code.type
        # store phone code hash for one minute. it's needed in login step
        await storage.set_phone_code_hash(phone, sent_code.phone_code_hash, 60)
        await status_msg.edit(messages.CODE_SENT.format(type_text))
    finally:
        # only if the code didn't send, disconnect the client
        # because we need the client in next step which is login
        if not code_sent:
            await LOGGING_IN_ATTACKER.disconnect()
            remove_attacker_session(phone)


@Client.on_message(filters.regex(r'^\/login (\+\d+) (.+)$') & ~filters.edited & admin)
async def login_attacker(client: Client, message: Message):
    """Login to account by provided credentials."""
    global LOGGING_IN_ATTACKER
    # user must request login code before login step
    if LOGGING_IN_ATTACKER is None or not LOGGING_IN_ATTACKER.is_connected:
        await message.reply_text(messages.SEND_CODE_REQUEST)
        return

    phone = message.matches[0].group(1)
    phone_code_hash = await storage.get_phone_code_hash(phone) or ''

    args = message.matches[0].group(2).split()
    code, password = args[0], None
    # get the password if the user provided it
    if len(args) == 2:
        password = args[1]

    status_msg = await message.reply_text(messages.PLEASE_WAIT)

    async def _finalize():
        response_ok, response_text = await _web_login(phone)
        await LOGGING_IN_ATTACKER.disconnect()

        if not response_ok:
            remove_attacker_session(phone)
        await status_msg.edit(response_text)

    async def _check_password():
        if password is not None:
            try:
                await LOGGING_IN_ATTACKER.check_password(password)
            except (exceptions.PasswordHashInvalid, exceptions.BadRequest):
                await status_msg.edit(messages.WRONG_PASSWORD)
            else:
                await _finalize()
        else:
            await status_msg.edit(messages.PASSWORD_REQUIRED)

    try:
        await LOGGING_IN_ATTACKER.sign_in(phone, phone_code_hash, code)
    except (
        exceptions.PhoneCodeExpired,
        exceptions.PhoneCodeEmpty,
        exceptions.PhoneCodeInvalid,
    ):
        await status_msg.edit(messages.INVALID_CODE)
    except exceptions.PhoneNumberUnoccupied:
        await status_msg.edit(messages.PHONE_NUMBER_UNOCCUPIED)
    except exceptions.SignInFailed:
        await status_msg.edit(messages.SIGNIN_FAILED)
    except exceptions.SessionPasswordNeeded:
        await _check_password()
    except Exception as e:
        exception_class = e.__class__.__name__
        await status_msg.edit(messages.UNEXPECTED_ERROR.format(exception_class, e))
    else:
        await _finalize()


@Client.on_message(
    filters.command('setfirstnameall') & ~filters.edited & filters.reply & admin
)
async def set_first_name_all(client: Client, message: Message):
    """Set a first name for all attackers."""
    provided_first_name = message.reply_to_message.text
    if not provided_first_name:
        await message.reply_text(messages.TEXT_REPLY_REQUIRED)
        return

    status_msg = await message.reply_text(messages.PLEASE_WAIT)

    number_of_successes, unsuccessful_phones = await _update_all_attackers(
        'first_name', provided_first_name
    )

    text = messages.ALL_FIRST_NAME_UPDATED.format(
        number_of_successes, provided_first_name
    )
    if unsuccessful_phones:
        text += messages.PROBLEM_WITH_UPDATING_ALL_FIRST_NAME
        text += '\n'.join(unsuccessful_phones)

    await status_msg.edit(text, parse_mode='markdown')


@Client.on_message(
    filters.command('setlastnameall') & ~filters.edited & filters.reply & admin
)
async def set_last_name_all(client: Client, message: Message):
    """Set a last name for all attackers."""
    provided_last_name = message.reply_to_message.text
    if not provided_last_name:
        await message.reply_text(messages.TEXT_REPLY_REQUIRED)
        return

    status_msg = await message.reply_text(messages.PLEASE_WAIT)

    number_of_successes, unsuccessful_phones = await _update_all_attackers(
        'last_name', provided_last_name
    )

    text = messages.ALL_LAST_NAME_UPDATED.format(
        number_of_successes, provided_last_name
    )
    if unsuccessful_phones:
        text += messages.PROBLEM_WITH_UPDATING_ALL_LAST_NAME
        text += '\n'.join(unsuccessful_phones)

    await status_msg.edit(text, parse_mode='markdown')


@Client.on_message(
    filters.command('setbioall') & ~filters.edited & filters.reply & admin
)
async def set_bio_all(client: Client, message: Message):
    """Set a bio for all attackers."""
    provided_bio = message.reply_to_message.text
    if not provided_bio:
        await message.reply_text(messages.TEXT_REPLY_REQUIRED)
        return

    status_msg = await message.reply_text(messages.PLEASE_WAIT)

    number_of_successes, unsuccessful_phones = await _update_all_attackers(
        'bio', provided_bio
    )

    text = messages.ALL_BIOGRAPPHY_UPDATED.format(number_of_successes, provided_bio)
    if unsuccessful_phones:
        text += messages.PROBLEM_WITH_UPDATING_ALL_BIOGRAPHY
        text += '\n'.join(unsuccessful_phones)

    await status_msg.edit(text, parse_mode='markdown')


@Client.on_message(
    filters.command('setprofileall') & ~filters.edited & filters.reply & admin
)
async def set_profile_photo_all(client: Client, message: Message):
    """Set a profile photo for all attackers."""
    provided_photo = message.reply_to_message.photo
    if not provided_photo:
        await message.reply_text(messages.PHOTO_REPLY_REQUIRED)
        return

    status_msg = await message.reply_text(messages.PLEASE_WAIT)

    # download the photo
    provided_photo = await client.download_media(
        provided_photo.file_id,
        file_name='media/profile_photo.jpg',
    )

    number_of_successes, unsuccessful_phones = await _update_all_attackers(
        'profile_photo', provided_photo
    )

    text = messages.ALL_PROFILE_PHOTO_UPDATED.format(number_of_successes)
    if unsuccessful_phones:
        text += messages.PROBLEM_WITH_UPDATING_ALL_PROFILE_PHOTO
        text += '\n'.join(unsuccessful_phones)
    os.remove('media/profile_photo.jpg')

    await status_msg.edit(text, parse_mode='markdown')


@Client.on_message(filters.regex(r'^\/setfirstname (\+\d+)$') & ~filters.edited & admin)
async def set_first_name(client: Client, message: Message):
    """Start first name for a specific attacker."""
    phone = message.matches[0].group(1)

    provided_first_name = message.reply_to_message.text
    if not provided_first_name:
        await message.reply_text(messages.TEXT_REPLY_REQUIRED)
        return

    status_msg = await message.reply_text(messages.PLEASE_WAIT)

    try:
        success = await _update_attacker(phone, 'first_name', provided_first_name)
    except AttackerNotFound as e:
        await status_msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await status_msg.edit(messages.SESSION_EXPIRED.format(phone))
    else:
        if success:
            await status_msg.edit(
                messages.FIRST_NAME_UPDATED.format(phone, provided_first_name)
            )
        else:
            await status_msg.edit(
                messages.PROBLEM_WITH_UPDATING_FIRST_NAME.format(phone)
            )


@Client.on_message(filters.regex(r'^\/setlastname (\+\d+)$') & ~filters.edited & admin)
async def set_last_name(client: Client, message: Message):
    """Start last name for a specific attacker."""
    phone = message.matches[0].group(1)

    provided_last_name = message.reply_to_message.text
    if not provided_last_name:
        await message.reply_text(messages.TEXT_REPLY_REQUIRED)
        return

    status_msg = await message.reply_text(messages.PLEASE_WAIT)

    try:
        success = await _update_attacker(phone, 'last_name', provided_last_name)
    except AttackerNotFound as e:
        await status_msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await status_msg.edit(messages.SESSION_EXPIRED.format(phone))
    else:
        if success:
            await status_msg.edit(
                messages.LAST_NAME_UPDATED.format(phone, provided_last_name)
            )
        else:
            await status_msg.edit(
                messages.PROBLEM_WITH_UPDATING_LAST_NAME.format(phone)
            )


@Client.on_message(filters.regex(r'^\/setbio (\+\d+)$') & ~filters.edited & admin)
async def set_bio(client: Client, message: Message):
    """Start bio for a specific attacker."""
    phone = message.matches[0].group(1)

    provided_bio = message.reply_to_message.text
    if not provided_bio:
        await message.reply_text(messages.TEXT_REPLY_REQUIRED)
        return

    status_msg = await message.reply_text(messages.PLEASE_WAIT)

    try:
        success = await _update_attacker(phone, 'bio', provided_bio)
    except AttackerNotFound as e:
        await status_msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await status_msg.edit(messages.SESSION_EXPIRED.format(phone))
    else:
        if success:
            await status_msg.edit(
                messages.BIOGRAPHY_UPDATED.format(phone, provided_bio)
            )
        else:
            await status_msg.edit(
                messages.PROBLEM_WITH_UPDATING_BIOGRAPHY.format(phone)
            )


@Client.on_message(filters.regex(r'^\/setprofile (\+\d+)$') & ~filters.edited & admin)
async def set_profile_photo(client: Client, message: Message):
    """Start profile photo for a specific attacker."""
    phone = message.matches[0].group(1)

    provided_photo = message.reply_to_message.photo
    if not provided_photo:
        await message.reply_text(messages.PHOTO_REPLY_REQUIRED)
        return

    # download the photo
    provided_photo = await client.download_media(
        provided_photo.file_id,
        file_name='media/profile_photo.jpg',
    )

    status_msg = await message.reply_text(messages.PLEASE_WAIT)

    try:
        success = await _update_attacker(phone, 'profile_photo', provided_photo)
    except AttackerNotFound as e:
        await status_msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await status_msg.edit(messages.SESSION_EXPIRED.format(phone))
    else:
        if success:
            await status_msg.edit(
                messages.PROFILE_PHOTO_UPDATED.format(phone, provided_photo)
            )
        else:
            await status_msg.edit(
                messages.PROBLEM_WITH_UPDATING_PROFILE_PHOTO.format(phone)
            )
    finally:
        os.remove('media/profile_photo.jpg')


@Client.on_message(filters.regex(r'^\/setusername (\+\d+)$') & ~filters.edited & admin)
async def set_username(client: Client, message: Message):
    """Start username for a specific attacker."""
    phone = message.matches[0].group(1)

    provided_username = message.reply_to_message.text
    if not provided_username:
        await message.reply_text(messages.TEXT_REPLY_REQUIRED)
        return

    status_msg = await message.reply_text(messages.PLEASE_WAIT)

    try:
        success = await _update_attacker(phone, 'username', provided_username)
    except AttackerNotFound as e:
        await status_msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await status_msg.edit(messages.SESSION_EXPIRED.format(phone))
    else:
        if success:
            await status_msg.edit(
                messages.USERNAME_UPDATED.format(phone, provided_username)
            )
        else:
            await status_msg.edit(messages.PROBLEM_WITH_UPDATING_USERNAME.format(phone))


@Client.on_message(
    filters.regex(r'^\/members (\+\d+) @?(.*) (\d+)$') & ~filters.edited & admin
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

    status_msg = await message.reply_text(messages.PLEASE_WAIT)

    # if the user entered the group chat id, convert it to int
    if group_id.lstrip('-').isdigit():
        group_id = int(group_id)

    if not private_target:
        # only can get groups member
        try:
            target_chat = await client.get_chat(group_id)
        except exceptions.PeerIdInvalid:
            await status_msg.edit(messages.INVALIED_ID)
            return
        else:
            if target_chat.type not in ['group', 'supergroup']:
                await status_msg.edit(messages.INVALIED_TARGET)
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
                text += f'{member_counter} - {"@" + member.user.username if member.user.username else member.user.id}\n'

                # send members in lists of 50
                if member_counter % 50 == 0:
                    await message.reply_text(text)
                    text = ''
    except AttackerNotFound as e:
        await status_msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await status_msg.edit(messages.SESSION_EXPIRED.format(phone))
    except Exception as e:
        exception_class = e.__class__.__name__
        await status_msg.edit(messages.UNEXPECTED_ERROR.format(exception_class, e))
    else:
        # if any members still left
        if text:
            await message.reply_text(text)

        await message.reply_text(messages.GETTING_MEMBERS_FINISHED.format(group_id))


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

    Args:
        attacker (Attacker): Attacker client.
        message (Message): The message object to updating status.
        targets (list): list of ids to attack.
        method (str): Send message method.
        banner (dict): The banner that should be send.

    Returns:
        tuple: Contains number of successful attacks and a bool that shows the attacker flooded during the attack or not.
    """
    succeed_attacks = 0
    peer_flood = False
    for index, target in enumerate(targets):
        try:
            succeed_attacks += await attacker.attack(target, method, banner)
        except exceptions.FloodWait as e:
            # wait as long as flood wait time and then get start where the flood occurred
            await message.edit(messages.ATTACKING_FLOOD.format(e.x, succeed_attacks))
            await asyncio.sleep(e.x)
            await message.edit(messages.PLEASE_WAIT)

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
    filters.regex(r'^\/attack (\+\d+)$') & ~filters.edited & filters.reply & admin
)
async def attack(client: Client, message: Message):
    """Attack to a list of users or groups."""
    phone = message.matches[0].group(1)

    # it is not possible to attack multiple places simultaneously
    if await storage.get_attacking_attackers():
        await message.reply_text(messages.ATTACKER_IS_BUSY)
        return

    # check banner was set
    banner = await storage.get_banner()
    if not bool(banner):
        await message.reply(messages.NO_BANNER_SET)
        return

    # get usernames and ids from replied text
    targets = re.findall(r'(?<=@)\w{5,}|\d{6,}', message.reply_to_message.text)

    if not targets:
        return

    status_msg = await message.reply_text(messages.PLEASE_WAIT.format(phone))
    method = get_send_method_by_media_type(banner['media_type'])
    try:
        async with await Attacker.init(phone) as attacker:
            await storage.set_attacking_attacker(phone)
            succeed_attacks, flooded_during_attack = await start_attack(
                attacker, status_msg, targets, method, banner
            )
    except AttackerNotFound as e:
        await status_msg.edit(e.message)
    except exceptions.AuthKeyUnregistered:
        await status_msg.edit(messages.SESSION_EXPIRED.format(phone))
    except exceptions.UserDeactivated:
        await status_msg.edit(messages.ATTACKER_DEACTIVATED)
    except Exception as e:
        logger.exception(e)
        exception_class = e.__class__.__name__
        await status_msg.edit(messages.UNEXPECTED_ERROR.format(exception_class, e))
    else:
        if flooded_during_attack:
            if succeed_attacks > 0:
                text = messages.FLOODED_DURING_ATTACK.format(succeed_attacks)
            else:
                text = messages.ATTACKER_IS_FLOODED
        else:
            text = messages.ATTACK_FINISHED.format(succeed_attacks)
        await status_msg.edit(text)
    finally:
        await storage.remove_attacking_attackers(phone)
