from modconfig import Config


__version__ = "0.11.0"


config = Config(

    SCHEME='https',
    MAX_REDIRECTS=10,
    STATUS_URL='/knocker/status',

    #  Timeout
    #  -------

    TIMEOUT=10.0,
    TIMEOUT_MAX=60.0,

    #  Retries
    #  -------

    RETRIES=2,
    RETRIES_MAX=10,

    RETRIES_BACKOFF_FACTOR=0.5,
    RETRIES_BACKOFF_FACTOR_MAX=600,

)


from .app import App  # noqa


app = App()
