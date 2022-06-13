from pyrogram import Client
from pyrogram.errors.exceptions import UsernameNotOccupied, PeerIdInvalid
from attacker_controller.attacker.exceptions import AttackerNotFound
from attacker_controller.utils import storage


class Attacker(Client):
    """ Attacker Client. """

    def __init__(self, phone, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phone = phone

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    @classmethod
    async def init(cls, phone: str) -> Client:
        """
        Initiate a Attacker by with given phone.

        Raise `AttackerNotFound` if no attacker found with this phone.
        """
        attacker_info = await storage.get_attackers(phone)
        if not attacker_info:
            raise AttackerNotFound

        attacker = cls(
            phone=phone,
            session_name=f'attacker_controller/sessions/attackers/{phone}',
            api_id=attacker_info['api_id'],
            api_hash=attacker_info['api_hash'],
        )
        return attacker

    async def attack(self, target: str, method: str, banner: dict):
        """
        Send the banner to target.
        Return True on success.
        """
        # if the target chat type was group, join to it
        try:
            target_chat = await self.get_chat(target)
        except (
                UsernameNotOccupied,
                PeerIdInvalid,
        ):
            return False
        else:
            if target_chat.type in ['supergroup', 'group']:
                await target_chat.join()

        send_method = getattr(self, method)

        if banner['media_type']:
            await send_method(target, f'media/banner/banner.{banner["media_ext"]}', banner['text'])
        else:
            await send_method(target, banner['text'])
        return True
