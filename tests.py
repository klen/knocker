import asyncio as aio
import os

import pytest
import unittest.mock as mock

from httpx import AsyncClient, HTTPStatusError, Response, Request

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.fixture(scope='module')
def event_loop():
    """Bind Event Loop to module scope."""
    return aio.get_event_loop()


@pytest.fixture(scope='module')
async def client():
    """Generate the test client."""
    os.environ['TIMEOUT'] = '15.0'
    os.environ['HOSTS_ONLY'] = '["test.com","test2.com"]'

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
    assert config.HOSTS_ONLY == ['test.com', 'test2.com']


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
            (b'content-length', b'0'),
            (b'knocker-host', b'https://test.com'),
            (b'knocker-timeout', b'40'),
            (b'knocker-retries', b'5'),
            (b'knocker-id', b'CUSTOM-ID'),
            (b'knocker-backoff-factor', b'10'),
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
    assert url == 'https://test.com/test/me?q=1'
    assert config['backoff_factor'] == 10.0
    assert config['id'] == 'CUSTOM-ID'
    assert config['retries'] == 5
    assert config['timeout'] == 40
    assert 'callback' in config


@mock.patch('knocker.request.request')
async def test_request(mocked, client, event_loop):
    """Test making requests."""

    # Status
    res = await client.get('/knocker/status')
    assert res.status_code == 200
    json = res.json()
    assert json['worker']
    assert json['status']
    assert json['tasks']
    assert json['version']

    # Invalid requests
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
    assert res.status_code == 400
    json = res.json()
    assert json

    mocked.return_value = Response(200, request=Request('GET', 'https://test.com'))
    res = await client.post('/test/me?q=1', headers={
        'knocker-host': 'test.com',
        'knocker-retries': '10',
        'knocker-scheme': 'http',
        'knocker-timeout': '10',
    })
    assert res.status_code == 200
    json = res.json()
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
    assert kwargs['headers']['x-knocker']

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
    json = res.json()
    assert json
    assert json['config']['id'] == 'custom-id'

    await wait_for_other()
    assert mocked.call_count == 2


@mock.patch('knocker.request.request')
async def test_callbacks(mocked, client, event_loop):
    mocked.return_value = Response(200, request=Request('GET', 'https://test.com'))
    res = await client.post('/test/me?q=1', headers={
        'knocker-host': 'test.com',
        'knocker-scheme': 'http',
        'knocker-callback': 'https://callback.my',
    })
    assert res.status_code == 200
    json = res.json()
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
    json = res.json()
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
    assert kwargs['headers'].get('custom-header') == 'custom-value'

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
async def test_sentry(msentry, mrequest, client, event_loop):
    from knocker import config

    config.SENTRY_DSN = 'test'
    config.SENTRY_FAILED_REQUESTS = True
    mrequest.return_value = Response(400, request=Request('GET', 'https://test.com'))
    res = await client.post('/test/me?q=1', headers={
        'knocker-host': 'test.com',
        'knocker-retries': '1',
        'knocker-backoff-factor': '.1',
    })
    assert res.status_code == 200

    await wait_for_other()
    assert msentry.capture_exception.called
