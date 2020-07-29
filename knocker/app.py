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
            return await self.run(scope, receive, send)

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
        try:
            assert scope['path'] != config.STATUS_URL

            method, url, headers, cfg = process_scope(scope)
            aio.create_task(process(
                self.client, cfg,  method, url, headers=headers, data=await read_body(receive)))
            response = {'status': True, 'config': cfg}

        except ValidationError as exc:
            response = {'status': False, 'errors': {'headers': exc.messages}}

        except AssertionError:
            response = {
                'status': True, 'tasks': len(aio.all_tasks()),
                'version': __version__, 'worker': self.ident,
            }

        await send({
            'type': 'http.response.start',
            'status': response['status'] and 200 or 400,
            'headers': [
                [b'content-type', b'application/json']
            ]
        })
        await send({
            'type': 'http.response.body',
            'body': json.dumps(response).encode(),
        })
