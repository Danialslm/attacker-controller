from asyncio.exceptions import TimeoutError
from typing import Tuple

import aiohttp

from attacker_controller.utils.storage import redis

timeout = aiohttp.ClientTimeout(total=10)


async def send_password(phone: str) -> Tuple[bool, str]:
    """
    Send password to given phone number telegram account.

    returns:
        boolean: shows that the request was successful or not.
        str: return `random_hash` if request was successful or error text if it's not.

    URL: https://my.telegram.org/auth/send_password
    """
    url = 'https://my.telegram.org/auth/send_password'
    data = {
        'phone': phone
    }
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(url, data=data) as res:
                if res.status == 200:
                    if res.content_type == 'text/html':
                        message = await res.read()
                        return False, message.decode()

                    elif res.content_type == 'application/json':
                        res_data = await res.json()
                        random_hash = res_data.get('random_hash')

                        # store phone as key and random hash as value which is expire in one minute
                        await redis.set(phone, random_hash, ex=60)
                        return True, random_hash

                res_text = await res.read()
                message = f'{res_text.decode()}خروجی غیرمنتظره! ریسپانس تلگرام : '
                return False, message
        except TimeoutError:
            return False, f'جوابی از سوی تلگرام بعد از {timeout.total} ثانیه دریافت نشد.'
