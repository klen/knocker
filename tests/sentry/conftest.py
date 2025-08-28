from __future__ import annotations

import os
from functools import partial

import pytest
from asgi_tools.tests import ASGITestClient


@pytest.fixture
async def client():
    os.environ["TIMEOUT"] = "15.0"
    os.environ["DEBUG"] = "true"
    os.environ["HOSTS_ONLY"] = '["test.com","test2.com"]'

    from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

    from knocker.app import app

    app.middleware(partial(SentryAsgiMiddleware, asgi_version=3))

    client = ASGITestClient(app)
    async with client.lifespan():
        yield client
