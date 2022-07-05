from pyrogram import filters
from pyrogram.types import Message

from attacker_controller import MAIN_ADMINS
from attacker_controller.utils import storage


async def admin_filter(_, __, m: Message):
    return m.from_user.id in MAIN_ADMINS or await storage.get_admins(m.from_user.id)


admin = filters.create(admin_filter)
""" Filter specified admins. """
