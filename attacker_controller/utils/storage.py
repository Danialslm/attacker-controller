import json
from typing import List, Optional, Union

import aioredis

from attacker_controller import REDIS_URL

redis = aioredis.from_url(REDIS_URL, decode_responses=True)


async def add_admin(*users_chat_id: List[int]) -> int:
    """
    Add the given users chat id to redis cache.
    Return number of added item.
    """
    return await redis.sadd('admins', *users_chat_id)


async def remove_admin(*users_chat_id: List[int]) -> int:
    """
    Remove the given users chat id from redis cache.
    Return number of removed item.
    """
    return await redis.srem('admins', *users_chat_id)


async def get_admins(user_chat_id: Optional[str] = None) -> Union[bool, set]:
    """
    If `user_chat_id` was provided, return boolean that shows user is admin or not.

    Get a set of current admins.
    Return empty set if there is no admin.
    """
    if user_chat_id:
        return await redis.sismember('admins', user_chat_id)
    return await redis.smembers('admins')


async def add_new_attacker(phone: str, api_id: str, api_hash: str) -> int:
    """
    Add new attacker to attackers set in json format.
    Return number of added item.
    """
    data = json.dumps({'phone': phone, 'api_id': api_id, 'api_hash': api_hash})
    return await redis.sadd('attackers', data)
