import logging

from modconfig import Config


__version__ = "0.13.0"

config = Config(

    SCHEME='https',
    MAX_REDIRECTS=10,
    STATUS_URL='/knocker/status',
    HOSTS_ONLY=[],

    TIMEOUT=10.0,
    TIMEOUT_MAX=60.0,

    RETRIES=2,
    RETRIES_MAX=10,
    RETRIES_BACKOFF_FACTOR=0.5,
    RETRIES_BACKOFF_FACTOR_MAX=600,

    LOG_FILE='-',
    LOG_LEVEL='INFO',
    LOG_FORMAT='[%(asctime)s] %(process)s %(levelname)-8s %(message)s',

)

logger = logging.getLogger('knocker')
logger.setLevel(config.LOG_LEVEL)
logger.propagate = False
if config.LOG_FILE:
    handler = logging.StreamHandler()
    if config.LOG_FILE != '-':
        handler = logging.FileHandler(config.LOG_FILE)

    handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
    logger.addHandler(handler)


from .app import App  # noqa


app = App()
