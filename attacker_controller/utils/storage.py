from typing import List, Optional, Union

import aioredis

from attacker_controller import REDIS_URL

redis = aioredis.from_url(REDIS_URL, decode_responses=True)


async def add_admin(*users_chat_id: List[int]) -> int:
    """
    Add the given `users_chat_id` to redis cache.

    Return number of added item.
    """
    return await redis.sadd('admins', *users_chat_id)


async def remove_admin(*users_chat_id: List[int]) -> int:
    """
    Remove the given `users_chat_id` from redis cache.

    Return number of removed item.
    """
    return await redis.srem('admins', *users_chat_id)


async def get_admins(user_chat_id: Union[str, int, None] = None) -> Union[bool, set]:
    """
    If `user_chat_id` was provided, return boolean that shows user is admin or not.
    otherwise Get current admins as `set`.

    Return empty set if there is no admin.
    """
    if user_chat_id:
        return await redis.sismember('admins', user_chat_id)
    return await redis.smembers('admins')


async def add_new_attacker(phone: str, api_id: str, api_hash: str) -> int:
    """Add a new attacker with provided credentials."""
    await redis.sadd('attackers', phone)
    return await redis.hmset(
        'attacker:' + phone, {'api_id': api_id, 'api_hash': api_hash}
    )


async def get_attackers(phone: Optional[str] = None) -> Union[dict, set]:
    """Return a `set` of attackers or a `dict` of attacker details."""
    if phone is not None:
        return await redis.hgetall('attacker:' + phone)
    return await redis.smembers('attackers')


async def remove_attacker(phone: str) -> int:
    """Remove the given phone from attackers."""
    await redis.srem('attackers', phone)
    return await redis.delete('attacker:' + phone)


async def set_phone_code_hash(
    phone: str, phone_code_hash: str, *args, **kwargs
) -> None:
    """Set phone_code_hash for given phone."""
    await redis.set(f'phone_code_hash:{phone}', phone_code_hash, *args, **kwargs)


async def get_phone_code_hash(phone: str) -> str:
    """Get given phone phone_code_hash."""
    return await redis.get(f'phone_code_hash:{phone}')


async def set_random_hash(phone: str, random_hash: str, *args, **kwargs) -> None:
    """Store random_hash for given phone."""
    await redis.set(f'random_hash:{phone}', random_hash, *args, **kwargs)


async def get_random_hash(phone: str) -> str:
    """Get given phone random hash."""
    return redis.get(f'random_hash:{phone}')


async def set_banner(text: str, media_ext: str, media_type: str) -> None:
    """Set banner with provided data."""
    await redis.hset(
        'banner',
        mapping={
            'text': text,
            'media_ext': media_ext,
            'media_type': media_type,
        },
    )


async def get_banner() -> dict:
    """Get banner data."""
    return await redis.hgetall('banner')


async def get_attacking_attackers(phone=Optional[str]) -> Union[bool, set]:
    """
    Get list of attacking attackers or a phone is attacking.

    If phone was provided, a boolean which shows attacker with the phone is attacking will return.
    """
    if phone:
        return await redis.sismember('attacking_attackers', phone)
    return await redis.smembers('attacking_attackers')


async def set_attacking_attacker(*phones):
    """Set one or many phones to attacking attackers."""
    await redis.sadd(*phones)


async def remove_attacking_attackers(*phones):
    """Remove one or many phones from attacking attackers"""
    await redis.srem(*phones)
