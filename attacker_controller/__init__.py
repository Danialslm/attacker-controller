import logging

from decouple import config, Csv

MAIN_ADMINS = config('main_admins', cast=Csv(cast=int))
""" Main admins are like normal admins but also can add and remove normal admins. """

REDIS_URL = config('redis_url')
""" Redis connection url. """

logging.basicConfig(
    level='INFO',
)
logger = logging.getLogger(__name__)
