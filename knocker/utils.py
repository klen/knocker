from httpx import Headers

from .schemas import request_config_schema


def process_scope(scope):
    """Get an URL and headers from the scope."""
    headers = Headers(scope['headers'])
    config = {
        name: headers.pop(name)
        for name in headers
        if name.startswith('knocker-')
    }

    # Clean Knocker HOST from headers
    headers.pop('host', None)

    # Clean Content-Length from headers
    headers.pop('content-length', None)

    config = request_config_schema.load(config)
    host = config.pop('host')

    url = "{scheme}://{host}{path}".format(
        host=host, scheme=config.pop('scheme'), path=scope['path'])
    if scope['query_string']:
        url += '?' + scope['query_string'].decode()

    return scope.get('method', 'GET'), url, headers, config


async def read_body(receive):
    """Loada a body from ASGI Server."""
    message = await receive()
    body = message.get('body', b'')
    while message.get('more_body'):
        message = await receive()
        body += message.get('body', b'')
    return body
