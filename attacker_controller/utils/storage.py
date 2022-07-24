from typing import List, Optional, Tuple, Union

import aioredis

from attacker_controller import REDIS_URL

redis = aioredis.from_url(REDIS_URL, decode_responses=True)


async def add_admin(*users_chat_id: Union[List[int], Tuple[int]]):
    """Store the given `users_chat_id` as admin."""
    await redis.sadd('admins', *users_chat_id)


async def remove_admin(*users_chat_id: Union[List[int], Tuple[int]]):
    """Remove the given `users_chat_id` from admin list."""
    await redis.srem('admins', *users_chat_id)


async def get_admins(
    user_chat_id: Optional[Union[int, str]] = None
) -> Union[bool, set]:
    """
    Get the admin list or show that a user is admin.

    Args:
        user_chat_id (int | str, optional): Determine user is admin or not. Defaults to None.

    Returns:
        bool | set: If the `user_chat_id` was provided, return bool that shows the user is admin or not,
        else a `set` of admins will return.
    """
    if user_chat_id:
        return await redis.sismember('admins', user_chat_id)
    return await redis.smembers('admins')


async def add_new_attacker(phone: str, api_id: str, api_hash: str):
    """
    Add a new attacker with provided credentials.

    Args:
        phone (str): Attacker account phone number.
        api_id (str): Attacker account `api_id`.
        api_hash (str): Attacker account `api_hash`.
    """
    await redis.sadd('attackers', phone)
    await redis.hmset('attacker:' + phone, {'api_id': api_id, 'api_hash': api_hash})


async def get_attackers(phone: Optional[str] = None) -> Union[dict, set]:
    """
    Get attacker list or return an attacker details

    Args:
        phone (str, optional): Attacker account phone number. Defaults to None.

    Returns:
        dict | set: If the `phone` was provided, the attacker details with given phone will return,
        else list of attackers will return.
    """
    if phone is not None:
        return await redis.hgetall('attacker:' + phone)
    return await redis.smembers('attackers')


async def remove_attacker(phone: str):
    """
    Remove the given phone from attackers.

    Args:
        phone (str): Attacker account phone number.
    """
    await redis.srem('attackers', phone)
    await redis.delete('attacker:' + phone)


async def set_phone_code_hash(
    phone: str, phone_code_hash: str, *args, **kwargs
) -> None:
    """
    Set phone_code_hash for given phone.

    Args:
        phone (str): Account phone number.
        phone_code_hash (str): Temporary code for login.
    """
    await redis.set(f'phone_code_hash:{phone}', phone_code_hash, *args, **kwargs)


async def get_phone_code_hash(phone: str) -> str:
    """
    Get given phone phone_code_hash.

    Args:
        phone (str): Account phone number.

    Returns:
        str: The login temporary `phone_code_hash`.
    """
    return await redis.get(f'phone_code_hash:{phone}')


async def set_random_hash(phone: str, random_hash: str, *args, **kwargs) -> None:
    """
    Store random_hash for given phone.

    Args:
        phone (str): Account phone number.
        random_hash (str): Web login `random_hash`.
    """
    await redis.set(f'random_hash:{phone}', random_hash, *args, **kwargs)


async def get_random_hash(phone: str) -> str:
    """
    Get given phone random hash.

    Args:
        phone (str): Account phone number.

    Returns:
        str: Web login `random_hash`.
    """
    return await redis.get(f'random_hash:{phone}')


async def set_banner(text: str, media_ext: str, media_type: str) -> None:
    """
    Set banner with provided data.

    Args:
        text (str): The banner text or caption.
        media_ext (str): The banner media extension.
        media_type (str): The banner media file type.
    """
    await redis.hset(
        'banner',
        mapping={
            'text': text,
            'media_ext': media_ext,
            'media_type': media_type,
        },
    )


async def get_banner() -> dict:
    """
    Get stored banner.

    Returns:
        dict: The banner data.
    """
    return await redis.hgetall('banner')


async def get_attacking_attackers(phone: Optional[str] = None) -> Union[bool, set]:
    """
    Get list of attacking attackers or show that a attacker is attacking.

    Args:
        phone (str, optional): Attacker account phone number. Defaults to None.

    Returns:
         bool | set: If the `phone` was provided,
         a bool that shows the attacker with given phone is attacking or
         not will return, else a list of attacking attacker will return
    """
    if phone:
        return await redis.sismember('attacking_attackers', phone)
    return await redis.smembers('attacking_attackers')


async def set_attacking_attacker(*phones):
    """Add the given phone as attacking attackers."""
    await redis.sadd('attacking_attackers', *phones)


async def remove_attacking_attackers(*phones):
    """Remove the given phones from attacking attackers."""
    await redis.srem('attacking_attackers', *phones)
