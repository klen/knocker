"""Do requests."""

from __future__ import annotations

import http
from random import random
from typing import TYPE_CHECKING

import sentry_sdk
from asgi_tools._compat import aio_sleep
from httpx import (
    AsyncClient,
    ConnectError,
    HTTPError,
    HTTPStatusError,
    NetworkError,
    Response,
    TimeoutException,
)

from knocker.tasks import create_task

if TYPE_CHECKING:
    import asyncio

    from knocker.types import TRequestConfig

from . import config as global_config
from . import logger


def run_process(
    client: AsyncClient,
    config: TRequestConfig,
    method: str,
    url: str,
    **kwargs,
) -> asyncio.Task:
    """Run process in the background."""
    return create_task(process(client, config, method, url, **kwargs))


async def process(
    client: AsyncClient,
    config: TRequestConfig,
    method: str,
    url: str,
    **kwargs,
) -> None:
    """Send requests."""
    error = None
    attempts = 0
    kwargs["timeout"] = config["timeout"]

    # Cycle requests
    while True:
        try:
            attempts += 1
            res: Response = await request(client, method, url, **kwargs)
            res.raise_for_status()
            logger.info(
                'Request #%s done (%d): "%s %s" %d %s',
                config["id"],
                attempts,
                method,
                url,
                res.status_code,
                http.HTTPStatus(res.status_code).phrase,
            )

        except HTTPError as exc:
            error = exc_to_code(exc)

            if config["retries"] > (attempts - 1):
                retry = min(
                    global_config.RETRIES_BACKOFF_FACTOR_MAX,
                    (config["backoff_factor"] * (2 ** (attempts - 1)) + random()),
                )
                logger.warning(
                    'Request #%s fail (%d), retry in %ss: "%s %s" %d',
                    config["id"],
                    attempts,
                    retry,
                    method,
                    url,
                    error,
                )

                await aio_sleep(retry)
                continue

            logger.warning(
                'Request #%s failed (%d): "%s %s" %d',
                config["id"],
                attempts,
                method,
                url,
                error,
            )

            if global_config.SENTRY_DSN and global_config.SENTRY_FAILED_REQUESTS:
                sentry_sdk.capture_exception(exc)

        # An unhandled exception
        except Exception as exc:  # noqa: BLE001
            logger.error(
                'Request #%s raises an exception (%d): "%s %s"',
                config["id"],
                attempts,
                method,
                url,
            )
            logger.exception(exc)

            if global_config.SENTRY_DSN:
                sentry_sdk.capture_exception(exc)

        else:
            return

        break

    callback_url = config.pop("callback", None)
    if callback_url:
        run_process(
            client,
            config,
            "POST",
            callback_url,
            json={
                "url": url,
                "method": method,
                "config": config,
                "status_code": error or 999,
            },
            headers=[("x-knocker-origin", "knocker"), *kwargs["headers"]],
        )


async def request(client: AsyncClient, method: str, url: str, **kwargs) -> Response:
    """Make a request."""
    # We don't need to read response body here
    async with client.stream(method, url, **kwargs) as response:
        return response


def exc_to_code(exc: HTTPError) -> int:
    """Convert an exception into a response code."""
    if isinstance(exc, HTTPStatusError):
        return (exc.response and exc.response.status_code) or 418

    if isinstance(exc, ConnectError):
        return 502

    if isinstance(exc, NetworkError):
        return 503

    if isinstance(exc, TimeoutException):
        return 504

    return 418
