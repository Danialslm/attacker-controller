from pyrogram import Client
from pyrogram.types import Message

from attacker_controller import messages
from attacker_controller.utils import storage


def check_attacker_update_constraint(handler) -> str:
    """
    Check that admin can update attackers.

    If attackers was attacking, it can't be update.

    Returns:
        str: constraint error message, empty string if there is no problem.
    """

    async def wrapper(client: Client, message: Message):
        phone = message.matches[0].group(1) if message.matches else None

        attacking_attackers = await storage.get_attacking_attackers(phone)
        if attacking_attackers:
            if phone:
                await message.reply(messages.ATTACKING_ATTACKER_UPDATE_ERROR)
            else:
                await message.reply(
                    messages.ATTACKING_ATTACKERS_UPDATE_ERROR.format(
                        '\n'.join(attacking_attackers)
                    )
                )
        else:
            await handler(client, message)

    return wrapper
