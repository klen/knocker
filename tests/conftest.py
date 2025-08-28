from __future__ import annotations

import asyncio as aio
import os

import pytest
from asgi_tools.tests import ASGITestClient


@pytest.fixture(scope="session")
def aiolib():
    """Support asyncio only. Disable uvloop on tests."""
    return ("asyncio", {"use_uvloop": False})


@pytest.fixture()
async def client():
    os.environ["TIMEOUT"] = "15.0"
    os.environ["DEBUG"] = "true"
    os.environ["HOSTS_ONLY"] = '["test.com","test2.com"]'

    from knocker.app import app

    client = ASGITestClient(app)
    async with client.lifespan():
        yield client


@pytest.fixture()
async def wait_for_other():
    """Await other tasks except the current one."""
    base_tasks = aio.all_tasks()

    async def wait_for_other():
        ignore = [*list(base_tasks), aio.current_task()]
        while len(tasks := [t for t in aio.all_tasks() if t not in ignore]):
            await aio.gather(*tasks, return_exceptions=True)

    return wait_for_other
