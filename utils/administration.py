import aioredis
from decouple import config

redis = aioredis.from_url(config('redis_url'), decode_responses=True)


async def add_admin(*users_chat_id):
    """
    Add the given users chat id to redis cache.
    Return number of added item.
    """
    return await redis.sadd('admins', *users_chat_id)


async def remove_admin(*users_chat_id):
    """
    Remove the given users chat id from redis cache.
    Return number of removed item.
    """
    return await redis.srem('admins', *users_chat_id)


async def get_admins():
    """
    Get a set of current admins.
    Return empty set if there is no admin.
    """
    return await redis.smembers('admins')
