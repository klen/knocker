"""Create ASGI Knocker application."""

import typing as t
import asyncio as aio
import os
import dataclasses as dc
from asgi_tools import Request

from httpx import AsyncClient
from marshmallow import ValidationError

from . import __version__, config

from .request import process
from .schemas import request_config_schema


@dc.dataclass
class Knocker:
    """Process HTTP requests."""

    ident: int = os.getpid()
    processed: int = 0
    client: t.Optional[AsyncClient] = dc.field(default=None, repr=None)  # type: ignore

    async def start(self):
        """Initialize the client."""
        self.client = AsyncClient(timeout=config.TIMEOUT, max_redirects=config.MAX_REDIRECTS)

    async def stop(self):
        """Stop the client."""
        await self.client.aclose()

    async def status(self, request: Request):
        """Returh status for the current worker."""
        return {
            'processed': self.processed,
            'status': True,
            'tasks': len(aio.all_tasks()),
            'version': __version__,
            'worker': self.ident,
        }

    async def process(self, request: Request):
        """Process a request."""
        if self.client is None:
            return 500, 'Service is broken'

        if request.headers.get('x-knocker'):
            return 406, {'status': False, 'errors': {'system': 'ignore requests from knocker'}}

        config, headers = {}, []
        for name in request.headers:
            name = name.lower()
            if name in {'host', 'content-length'}:
                continue

            if name.startswith('knocker-'):
                config[name] = request.headers[name]
                continue

            for val in request.headers.getall(name):
                headers.append((name, val))

        try:
            config = request_config_schema.load(config)
        except ValidationError as exc:
            return 400, {'status': False, 'errors': {'headers': exc.messages}}

        url = request.url.with_host(config.pop('host')).with_scheme(config.pop('scheme'))

        body = await request.body()
        aio.create_task(
            process(self.client, config, request.method, str(url), headers=headers, data=body))

        self.processed += 1
        return {'status': True, 'config': config}


knocker: Knocker = Knocker()
