import asyncio as aio
import logging
import json

from httpx import AsyncClient
from marshmallow import ValidationError

from .config import MAX_REDIRECTS, TIMEOUT, STATUS_URL
from .request import process
from .utils import process_scope, read_body


logger = logging.getLogger('knocker.error')


class App:

    def __init__(self):
        """Initialize the application."""
        self.client = None

    async def startup(self, scope):
        self.client = AsyncClient(timeout=TIMEOUT, max_redirects=MAX_REDIRECTS)

    async def shutdown(self, scope):
        await self.client.aclose()

    async def __call__(self, scope, receive, send):
        """Init a http client."""
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
        try:
            assert scope['path'] != STATUS_URL

            method, url, headers, config = process_scope(scope)
            response = {'status': True, 'config': config}
            aio.create_task(process(
                self.client, config,  method, url, headers=headers, data=await read_body(receive)))

        except ValidationError as exc:
            response = {'status': False, 'errors': exc.messages}

        except AssertionError:
            response = {
                'status': True, 'tasks': len(aio.all_tasks()), 'client': id(self.client)
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
