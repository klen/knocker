"""Create ASGI Knocker application."""

import asyncio as aio
import dataclasses as dc
import os

from asgi_tools import Request, ResponseError
from asgi_tools._compat import json_dumps
from httpx import AsyncClient
from marshmallow import ValidationError

from . import __version__, config
from .request import process
from .schemas import request_config_schema
from .types import TRequestAccepted, TRequestConfig, TStatus


@dc.dataclass
class Knocker:
    """Process HTTP requests."""

    ident: int = os.getpid()
    processed: int = 0
    _client: AsyncClient | None = None

    async def start(self):
        """Initialize the client."""
        self._client = AsyncClient(
            timeout=config.TIMEOUT, max_redirects=config.MAX_REDIRECTS
        )

    async def stop(self):
        """Stop the client."""
        await self.client.aclose()

    @property
    def client(self) -> AsyncClient:
        """Return client."""
        if self._client is None:
            raise RuntimeError("Knocker is not started")

        return self._client

    async def status(self, request: Request) -> TStatus:
        """Returh status for the current worker."""
        return {
            "processed": self.processed,
            "status": True,
            "tasks": len(aio.all_tasks()),
            "version": __version__,
            "worker": self.ident,
        }

    async def process(self, request: Request) -> TRequestAccepted:
        """Process a request."""
        if self._client is None:
            raise ResponseError.LOCKED("Service is not ready")

        if request.headers.get("x-knocker"):
            raise ResponseError.NOT_ACCEPTABLE("Ignore requests from knocker")

        config_data, headers = {}, [("x-knocker", __version__)]
        for name in request.headers:
            name = name.lower()
            if name in {"host", "content-length"}:
                continue

            if name.startswith("knocker-"):
                config_data[name] = request.headers[name]
                continue

            for val in request.headers.getall(name):
                headers.append((name, val))

        try:
            config: TRequestConfig = request_config_schema.load(config_data)
        except ValidationError as exc:
            raise ResponseError.BAD_REQUEST(
                json_dumps({"errors": exc.messages, "status": False}),
                content_type="application/json",
            )

        scheme = config.pop("scheme")
        url = str(
            request.url.with_host(config.pop("host"))
            .with_scheme(scheme)
            .with_port(None)
        )
        body = await request.body()
        aio.create_task(
            process(
                self.client, config, request.method, url, headers=headers, data=body
            )
        )

        self.processed += 1
        return {
            "status": True,
            "config": config,
            "url": url,
            "method": request.method,
            "headers": headers,
            "body-length": len(body),
        }


knocker: Knocker = Knocker()
