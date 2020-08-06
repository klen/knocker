import asyncio as aio
import os
import json

from httpx import AsyncClient
from marshmallow import ValidationError

from . import __version__, config, logger

from .request import process
from .utils import process_scope, read_body


class App:

    def __init__(self):
        """Initialize the application."""
        self.client = None
        self.ident = os.getpid()

    async def startup(self, scope):
        """Init HTTP Client."""
        self.client = AsyncClient(timeout=config.TIMEOUT, max_redirects=config.MAX_REDIRECTS)
        logger.info('Knocker #%d started: %r', self.ident, vars(config))

    async def shutdown(self, scope):
        """Close HTTP Client."""
        await self.client.aclose()

    async def __call__(self, scope, receive, send):
        """Process ASGI request."""
        if scope['type'] == 'http':
            status, response = await self.run(scope, receive, send)
            await send({
                'status': status,
                'type': 'http.response.start',
                'headers': [
                    [b'content-type', b'application/json']
                ]
            })
            return await send({
                'type': 'http.response.body',
                'body': json.dumps(dict(response, status=bool(status < 400))).encode(),
            })

        if scope['type'] == 'lifespan':
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    await self.startup(scope)
                    await send({'type': 'lifespan.startup.complete'})

                elif message['type'] == 'lifespan.shutdown':
                    await self.shutdown(scope)
                    return await send({'type': 'lifespan.shutdown.complete'})

        raise ValueError('Unsupported Protocol: {type}'.format(**scope))

    async def run(self, scope, receive, send):
        """Process HTTP request."""

        if scope['path'] == config.STATUS_URL:
            return 200, dict(tasks=len(aio.all_tasks()), version=__version__, worker=self.ident)

        try:
            method, url, headers, cfg = process_scope(scope)
        except ValidationError as exc:
            return 400, {'errors': {'headers': exc.messages}}

        if headers.get('x-knocker'):
            return 406, {'errors': {'system': 'ignore requests from knocker'}}

        aio.create_task(process(
            self.client, cfg, method, url, headers=headers, data=await read_body(receive)))

        return 200, {'config': cfg}
