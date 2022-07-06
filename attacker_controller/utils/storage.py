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
