"""Setup ASGI application."""

from __future__ import annotations

from functools import partial

import sentry_sdk
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
    from sentry_sdk.integrations import asgi

    logger.info("Setup Sentry: %s", config.SENTRY_DSN)
    sentry_sdk.init(dsn=config.SENTRY_DSN, release=__version__)

    app.middleware(partial(asgi.SentryAsgiMiddleware, asgi_version=3))
