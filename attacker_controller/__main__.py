import asyncio
import os

from decouple import config
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors.exceptions import UserDeactivated

from attacker_controller import MAIN_ADMINS
from attacker_controller.attacker import Attacker
from attacker_controller.utils import (
    remove_attacker_session,
    get_message_file_extension,
    get_send_method_by_media_type,
    storage,
)
from attacker_controller.utils.custom_filters import admin
from attacker_controller import messages

app = Client(
    'attacker_controller/sessions/attacker_controller',
    api_id=config('api_id', cast=int),
    api_hash=config('api_hash'),
    bot_token=config('bot_token'),
    plugins={'root': 'attacker_controller.attacker'},
)


@app.on_message(
    filters.regex(r'^\/addadmin (\d+(?:\s+\d+)*)$')
    & ~filters.edited
    & filters.user(MAIN_ADMINS)
)
async def add_admin(client: Client, message: Message):
    """Add the given chat id(s) to the admin list."""
    users_chat_id = message.matches[0].group(1).split()
    await storage.add_admin(*users_chat_id)
    await message.reply_text(messages.ADMIN_ADDED)


@app.on_message(
    filters.regex(r'^\/removeadmin (\d+(?:\s+\d+)*)$')
    & ~filters.edited
    & filters.user(MAIN_ADMINS)
)
async def remove_admin(client: Client, message: Message):
    """Remove the given chat id(s) from the admin list."""
    users_chat_id = message.matches[0].group(1).split()
    await storage.remove_admin(*users_chat_id)
    await message.reply_text(messages.ADMIN_REMOVED)


@app.on_message(
    filters.command('adminlist') & ~filters.edited & filters.user(MAIN_ADMINS)
)
async def admin_list(client: Client, message: Message):
    """Send admin chat id list."""
    admin_counter = 0
    text = messages.ADMIN_LIST
    for chat_id in await storage.get_admins():
        admin_counter += 1
        text += f'{admin_counter} - `{chat_id}`\n'

    await message.reply_text(text)


async def _check_attacker_status(attacker_phone: str):
    """
    Check the attacker status.

    Returns:
        str: 
            `attacking`: if attacker is currently attacking.
            `limited`: if attacker is reported and can't send message.
            `deleted/deactivated`: if the attacker account deleted or deactivated.
    """
    if await storage.get_attacking_attackers(attacker_phone):
        return 'attacking'

    async def _is_limited():
        async with await Attacker.init(attacker_phone) as attacker:
            await attacker.unblock_user('spambot')
            await attacker.send_message('spambot', '/start')

            # sleep for a while to get spambot reply
            await asyncio.sleep(1)
            spam_bot_reply = await attacker.get_history('spambot', limit=1)
            spam_bot_reply_text = spam_bot_reply[0].text
            if 'no limits' not in spam_bot_reply_text:
                return True

    try:
        if await _is_limited():
            return 'limited'
    except UserDeactivated:
        return 'deleted/deactivated'


@app.on_message(filters.command('attackerlist') & ~filters.edited & admin)
async def attacker_list(client: Client, message: Message):
    """Send list of copyable attackers phone number and their status."""
    text = messages.ATTACKER_LIST
    attackers = await storage.get_attackers()
    tasks = [
        asyncio.create_task(_check_attacker_status(attacker)) for attacker in attackers
    ]
    atks_status = await asyncio.gather(*tasks)

    attacker_counter = 0
    for attacker, status in zip(attackers, atks_status):
        attacker_counter += 1
        text += f'{attacker_counter} - `{attacker}`' + (
            f' ({status})\n' if status else '\n'
        )

    await message.reply(text)


async def _remove_attacker(phone):
    try:
        async with await Attacker.init(phone) as attacker:
            await attacker.log_out()
    except Exception:
        pass
    remove_attacker_session(phone)
    await storage.remove_attacker(phone)


@app.on_message(
    filters.regex(r'^\/removeattacker (\+\d+(?:\s+\+\d+)*)$') & ~filters.edited & admin
)
async def remove_attacker(client: Client, message: Message):
    """Remove attacker(s) by the given phone(s)."""
    phones = message.matches[0].group(1).split()
    await asyncio.gather(*[_remove_attacker(phone) for phone in phones])
    await message.reply_text('شماره(های) داده شده از لیست اتکر‌ها حذف شد.')


@app.on_message(
    filters.command('cleanattackers') & ~filters.edited & filters.user(MAIN_ADMINS)
)
async def clean_attacker_list(client: Client, message: Message):
    """Remove all attackers."""
    await asyncio.gather(
        *[_remove_attacker(phone) for phone in await storage.get_attackers()]
    )
    await message.reply_text('تمام اتکرها از ربات پاک شدند.')


@app.on_message(filters.command('setbanner') & ~filters.edited & filters.reply & admin)
async def set_banner(client: Client, message: Message):
    """Set a new banner."""
    # remove previous banner file
    for _, __, files in os.walk('media/banner'):
        for file in files:
            os.remove(f'media/banner/{file}')

    banner = message.reply_to_message
    # get and save message media if it has
    media = (
        banner.photo
        or banner.video
        or banner.animation
        or banner.voice
        or banner.sticker
    )
    banner_media_ext = ''
    if media:
        # download the media
        banner_media_ext = get_message_file_extension(banner)
        await message.reply_to_message.download(
            file_name=f'media/banner/banner.{banner_media_ext}'
        )

    banner_media_type = banner.media or ''
    banner_text = (
        message.reply_to_message.caption or message.reply_to_message.text or ''
    )

    await storage.set_banner(
        banner_text,
        banner_media_ext,
        banner_media_type,
    )
    await message.reply_text(messages.BANNER_SAVED)


@app.on_message(filters.command('banner') & ~filters.edited & admin)
async def get_current_banner(client: Client, message: Message):
    """Show the current banner."""
    banner = await storage.get_banner()

    if not banner:
        await message.reply_text(messages.NO_BANNER_SET)
        return

    method = get_send_method_by_media_type(banner['media_type'])

    send_method = getattr(client, method)
    if banner['media_type']:
        await send_method(
            message.chat.id,
            f'media/banner/banner.{banner["media_ext"]}',
            banner['text'],
        )
    else:
        await send_method(message.chat.id, banner['text'])


@app.on_message(filters.command('help') & ~filters.edited)
async def help_commands(client: Client, message: Message):
    """Return the list of bot commands."""
    await message.reply_text(messages.HELP)


app.run()
