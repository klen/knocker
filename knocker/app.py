"""Setup ASGI application."""

from asgi_tools import App

from . import __version__, config, logger
from .core import knocker

app: App = App(logger=logger, debug=config.DEBUG)

app.on_startup(knocker.start)
app.on_shutdown(knocker.stop)

app.route(config.STATUS_URL)(knocker.status)
app.route("/{path:path}")(knocker.process)


# Setup Sentry
if config.SENTRY_DSN:

    import sentry_sdk
    from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

    logger.info("Setup Sentry: %s", config.SENTRY_DSN)
    sentry_sdk.init(dsn=config.SENTRY_DSN, release=__version__)

    app.middleware(SentryAsgiMiddleware)
