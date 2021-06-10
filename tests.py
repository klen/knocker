import asyncio as aio
import os

import pytest
import unittest.mock as mock
from asgi_tools.tests import ASGITestClient

from httpx import HTTPStatusError, Response, Request


@pytest.fixture(scope='session')
def aiolib():
    """Support asyncio only. Disable uvloop on tests."""
    return ('asyncio', {'use_uvloop': False})


@pytest.fixture
async def client():
    os.environ['TIMEOUT'] = '15.0'
    os.environ['DEBUG'] = 'true'
    os.environ['HOSTS_ONLY'] = '["test.com","test2.com"]'

    from knocker.app import app

    client = ASGITestClient(app)
    async with client.lifespan():
        yield client


@pytest.fixture
async def wait_for_other(client):
    """Await other tasks except the current one."""
    base_tasks = aio.all_tasks()

    async def wait_for_other():
        ignore = list(base_tasks) + [aio.current_task()]
        while len(tasks := [t for t in aio.all_tasks() if t not in ignore]):
            await aio.gather(*tasks, return_exceptions=True)

    return wait_for_other


async def test_config(client):
    from knocker import config

    assert config.TIMEOUT == 15.0
    assert config.HOSTS_ONLY == ['test.com', 'test2.com']


def test_request_scheme():
    from knocker.schemas import request_config_schema

    config = request_config_schema.load(dict((
        ('knocker-host', 'https://test.com'),
        ('knocker-timeout', '40'),
        ('knocker-retries', '5'),
        ('knocker-id', 'CUSTOM-ID'),
        ('knocker-backoff-factor', '10'),
    )))
    assert config['backoff_factor'] == 10.0
    assert config['id'] == 'CUSTOM-ID'
    assert config['retries'] == 5
    assert config['timeout'] == 40
    assert 'callback' in config


@mock.patch('knocker.request.request')
async def test_request(mocked, client, wait_for_other):
    """Test making requests."""

    # Status
    res = await client.get('/knocker/status')
    assert res.status_code == 200
    json = await res.json()
    assert json['worker']
    assert json['status']
    assert json['tasks']
    assert json['version']

    # Invalid requests
    res = await client.get('/')
    assert res.status_code == 400
    json = await res.json()
    assert json
    assert not json['status']

    res = await client.post('/test/me?q=1', headers={
        'knocker-host': 'google.com',
        'knocker-retries': '10',
        'knocker-scheme': 'http',
        'knocker-timeout': '10',
    })
    assert res.status_code == 400
    json = await res.json()
    assert json

    mocked.return_value = Response(200, request=Request('GET', 'https://test.com'))
    res = await client.post('/test/me?q=1', headers={
        'knocker-host': 'test.com',
        'knocker-retries': '10',
        'knocker-scheme': 'http',
        'knocker-timeout': '10',
    })
    assert res.status_code == 200
    json = await res.json()
    assert json
    assert json['config']
    assert json['config']['id']
    assert json['status']

    await wait_for_other()

    assert mocked.call_count == 1
    (_, method, url), kwargs = mocked.call_args
    assert method == 'POST'
    assert url == 'http://test.com/test/me?q=1'
    assert kwargs['headers']
    headers = dict(kwargs['headers'])
    assert headers['x-knocker']

    mocked.reset_mock()
    mocked.side_effect = HTTPStatusError('we have a problem', request=None, response=res)
    res = await client.post('/test/me?q=1', headers={
        'knocker-host': 'test.com',
        'knocker-retries': '1',
        'knocker-scheme': 'http',
        'knocker-timeout': '10',
        'knocker-id': 'custom-id',
    })
    assert res.status_code == 200
    json = await res.json()
    assert json
    assert json['config']['id'] == 'custom-id'

    await wait_for_other()
    assert mocked.call_count == 2


@mock.patch('knocker.request.request')
async def test_callbacks(mocked, client, wait_for_other):
    mocked.return_value = Response(200, request=Request('GET', 'https://test.com'))
    res = await client.post('/test/me?q=1', headers={
        'knocker-host': 'test.com',
        'knocker-scheme': 'http',
        'knocker-callback': 'https://callback.my',
    })
    assert res.status_code == 200
    json = await res.json()
    assert json

    await wait_for_other()
    assert mocked.call_count == 1
    (_, method, url), kwargs = mocked.call_args
    assert url == 'http://test.com/test/me?q=1'

    mocked.reset_mock()
    mocked.side_effect = HTTPStatusError('', request=None, response=res)
    res = await client.post('/test/me?q=1', headers={
        'knocker-host': 'test.com',
        'knocker-scheme': 'http',
        'knocker-callback': 'https://callback.my',
        'knocker-retries': '1',
        'knocker-backoff-factor': '.1',
        'knocker-custom': 'custom-knocker-header',
        'custom-header': 'custom-value',
    })
    assert res.status_code == 200
    json = await res.json()
    assert json

    rid = json['config']['id']

    await wait_for_other()
    assert mocked.call_count == 4
    (_, method, url), kwargs = mocked.call_args
    assert url == 'https://callback.my'
    json = kwargs['json']
    assert json['status_code']
    assert json['config']
    assert json['config']['id'] == rid
    assert 'knocker-custom' in json['config']

    from knocker import __version__

    assert kwargs['headers'] == [
        ('x-knocker', __version__), ('custom-header', 'custom-value'),
        ('remote-addr', '127.0.0.1'), ('user-agent', 'ASGI-Tools-Test-Client')
    ]

    # Ignore requests from Knocker itself (see for X-Knocker header)
    mocked.reset_mock()
    res = await client.post('/test/me?q=1', headers={
        'knocker-host': 'test.com',
        'x-knocker': '0.0.0',
    })
    assert res.status_code == 406
    assert not mocked.called


@mock.patch('knocker.request.request')
@mock.patch('knocker.request.sentry_sdk')
async def test_sentry(msentry, mrequest, client, wait_for_other):
    from knocker import config

    config.update(SENTRY_DSN='test', SENTRY_FAILED_REQUESTS=True)

    mrequest.return_value = Response(400, request=Request('GET', 'https://test.com'))
    res = await client.post('/test/me?q=1', headers={
        'knocker-host': 'test.com',
        'knocker-retries': '1',
        'knocker-backoff-factor': '.1',
    })
    assert res.status_code == 200

    await wait_for_other()
    assert msentry.capture_exception.called
