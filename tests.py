import asyncio as aio
import os

import pytest
import unittest.mock as mock

from httpx import AsyncClient, HTTPError

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.fixture(scope='module')
async def client():
    """Generate the test client."""
    os.environ['TIMEOUT'] = '15.0'

    from knocker import app

    async with AsyncClient(app=app, base_url='http://testserver') as client:
        await app.startup(None)
        yield client
        await app.shutdown(None)


async def wait_for_other():
    """Await other tasks except the current one."""
    while len(tasks := [t for t in aio.all_tasks() if t is not aio.current_task()]):
        await aio.gather(*tasks)


def test_config(client):
    from knocker import config

    assert config.TIMEOUT == 15.0


def test_process_scope():
    """Test scope deserialization."""
    from knocker.utils import process_scope

    method, url, headers, config = process_scope({
        'asgi': {'version': '3.0'},
        'client': ('127.0.0.1', 123),
        'headers': [
            (b'host', b'testserver'),
            (b'accept', b'*/*'),
            (b'accept-encoding', b'gzip, deflate'),
            (b'connection', b'keep-alive'),
            (b'knocker-host', b'google.com'),
            (b'knocker-timeout', b'40'),
            (b'knocker-retries', b'5'),
        ],
        'http_version': '1.1',
        'method': 'GET',
        'path': '/test/me?q=1',
        'query_string': b'',
        'root_path': '',
        'scheme': 'http',
        'server': 'testserver',
        'type': 'http'})

    assert method == 'GET'
    assert len(headers) == 3
    assert url == 'https://google.com/test/me?q=1'
    assert config['timeout'] == 40
    assert config['retries'] == 5
    assert config['backoff_factor'] == 0.5
    assert 'callback' in config


@mock.patch('knocker.request.request')
async def test_knocker(mocked, client, event_loop):
    """Test making requests."""

    # Status
    res = await client.get('/knocker/status')
    assert res.status_code == 200
    json = res.json()
    assert json['status']
    assert json['tasks']
    assert json['client']
    assert json['version']

    # Invalid request
    res = await client.get('/')
    assert res.status_code == 400
    json = res.json()
    assert json
    assert not json['status']

    res = await client.post('/test/me?q=1', headers={
        'knocker-host': 'google.com',
        'knocker-retries': '10',
        'knocker-scheme': 'http',
        'knocker-timeout': '10',
    })
    assert res.status_code == 200
    json = res.json()
    assert json
    assert json['status']

    await wait_for_other()
    assert mocked.call_count == 1
    (_, method, url), kwargs = mocked.call_args
    assert method == 'POST'
    assert url == 'http://google.com/test/me?q=1'
    assert kwargs['headers']

    mocked.reset_mock()
    mocked.side_effect = HTTPError(response=res)
    res = await client.post('/test/me?q=1', headers={
        'knocker-host': 'google.com',
        'knocker-retries': '1',
        'knocker-scheme': 'http',
        'knocker-timeout': '10',
    })
    assert res.status_code == 200

    await wait_for_other()
    assert mocked.call_count == 2

    mocked.reset_mock()
    res = await client.post('/test/me?q=1', headers={
        'knocker-host': 'google.com',
        'knocker-retries': '1',
        'knocker-backoff-factor': '1',
        'knocker-scheme': 'http',
        'knocker-callback': 'https://callback.my',
    })
    assert res.status_code == 200

    await wait_for_other()
    assert mocked.call_count == 4
    (_, method, url), kwargs = mocked.call_args
    assert url == 'https://callback.my'
    assert kwargs['json']['status_code']
