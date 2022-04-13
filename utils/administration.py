import aioredis
from decouple import config, Csv

MAIN_ADMINS = config('main_admins', cast=Csv(cast=int))
""" Main admins are like normal admins but also can add and remove normal admins. """

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


async def get_admins(user_chat_id=None):
    """
    If `user_chat_id` was provided, return boolean that shows user is admin or not.

    Get a set of current admins.
    Return empty set if there is no admin.
    """
    if user_chat_id:
        return await redis.sismember('admins', user_chat_id)
    return await redis.smembers('admins')
