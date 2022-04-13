from pyrogram import filters
from pyrogram.types import Message

from utils import administration


async def admin_filter(_, __, m: Message):
    return await administration.get_admins(m.from_user.id)


admin = filters.create(admin_filter)
""" Filter specified admins. """
