import logging

from decouple import config, Csv

DEBUG = config('debug', cast=bool)

MAIN_ADMINS = config('main_admins', cast=Csv(cast=int))
""" Main admins are like normal admins but also can add and remove normal admins. """

REDIS_URL = config('redis_uri')
""" Redis connection uri. """

logging.basicConfig(
    level='INFO' if DEBUG else 'ERROR',
    filename='error.log' if not DEBUG else None,
    format='%(asctime)s-%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)
