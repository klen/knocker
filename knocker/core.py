"""Create ASGI Knocker application."""

from __future__ import annotations

import asyncio as aio
import dataclasses as dc
import os
from typing import TYPE_CHECKING

from asgi_tools import Request, ResponseError
from asgi_tools._compat import json_dumps
from httpx import AsyncClient
from marshmallow import ValidationError

from . import __version__, config
from .request import run_process
from .schemas import request_config_schema

if TYPE_CHECKING:
    from .types import TRequestAccepted, TRequestConfig, TStatus


@dc.dataclass
class Knocker:
    """Process HTTP requests."""

    ident: int = os.getpid()
    processed: int = 0
    _client: AsyncClient | None = None

    async def start(self) -> None:
        """Initialize the client."""
        self._client = AsyncClient(
            timeout=config.TIMEOUT,
            max_redirects=config.MAX_REDIRECTS,
        )

    async def stop(self) -> None:
        """Stop the client."""
        await self.client.aclose()

    @property
    def client(self) -> AsyncClient:
        """Return client."""
        if self._client is None:
            msg = "Knocker is not started"
            raise RuntimeError(msg)

        return self._client

    async def status(self, _: Request) -> TStatus:
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
            msg = "Knocker is not started"
            raise ResponseError.LOCKED(msg)

        if request.headers.get("x-knocker"):
            msg = "Ignore requests from knocker"
            raise ResponseError.NOT_ACCEPTABLE(msg)

        config_data, headers = {}, [("x-knocker", __version__)]
        for header_name in request.headers:
            name = header_name.lower()
            if name in {"host", "content-length"}:
                continue

            if name.startswith("knocker-"):
                config_data[name] = request.headers[name]
                continue

            headers.extend([(name, val) for val in request.headers.getall(name)])

        try:
            config: TRequestConfig = request_config_schema.load(config_data)  # type: ignore[]
        except ValidationError as exc:
            raise ResponseError.BAD_REQUEST(
                json_dumps({"errors": exc.messages, "status": False}),
                content_type="application/json",
            ) from exc

        url = str(
            request.url.with_host(config["host"]).with_scheme(config["scheme"]).with_port(None),
        )
        body = await request.body()
        run_process(
            self.client,
            config,
            request.method,
            url,
            headers=headers,
            data=body,
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
