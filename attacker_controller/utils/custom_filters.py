from pyrogram import filters
from pyrogram.types import Message

from attacker_controller.utils import administration


async def admin_filter(_, __, m: Message):
    return (
            m.from_user.id in administration.MAIN_ADMINS or
            await administration.get_admins(m.from_user.id)
    )


admin = filters.create(admin_filter)
""" Filter specified admins. """
