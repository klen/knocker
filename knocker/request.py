"""Do requests."""

import asyncio
import typing as t
import http
from asgi_tools._compat import aio_sleep
from random import random

from httpx import (
    HTTPError, ConnectError, TimeoutException, NetworkError,
    AsyncClient, Response, HTTPStatusError)
import sentry_sdk

from . import config as global_config, logger, __version__


async def process(client: AsyncClient, config: dict, method: str, url: str, **kwargs):
    """Send requests."""
    attempts = 0
    error = None
    kwargs['timeout'] = config['timeout']
    kwargs['headers'] = kwargs.get('headers') or {}
    kwargs['headers'].append(('x-knocker', __version__))

    while True:
        try:
            attempts += 1
            res: Response = await request(client, method, url, **kwargs)
            res.raise_for_status()
            logger.info(
                'Request #%s done (%d): "%s %s" %d %s',
                config['id'], attempts, method, url, res.status_code,
                http.HTTPStatus(res.status_code).phrase)

            return

        except HTTPError as exc:
            error = exc_to_code(exc)

            if config['retries'] > (attempts - 1):
                retry = min(global_config.RETRIES_BACKOFF_FACTOR_MAX, (
                    config['backoff_factor'] * (2 ** (attempts - 1)) + random()
                ))
                logger.warning(
                    'Request #%s fail (%d), retry in %ss: "%s %s" %d',
                    config['id'], attempts, retry, method, url, error)

                await aio_sleep(retry)
                continue

            logger.warning(
                'Request #%s failed (%d): "%s %s" %d', config['id'], attempts, method, url, error)

            if global_config.SENTRY_DSN and global_config.SENTRY_FAILED_REQUESTS:
                sentry_sdk.capture_exception(exc)

        # An unhandled exception
        except Exception as exc:
            logger.error(
                'Request #%s raises an exception (%d): "%s %s"',
                config['id'], attempts, method, url)
            logger.exception(exc)

            if global_config.SENTRY_DSN:
                sentry_sdk.capture_exception(exc)

        break

    if config.get('callback'):
        # TODO: Remove dependency from asyncio (spawn nursery in worker)
        asyncio.create_task(process(
            client, config, 'POST', config.pop('callback'), json={
                'config': config,
                'method': method,
                'url': url,
                'status_code': error or 999,
            }, headers=kwargs.get('headers')
        ))


async def request(client: AsyncClient, method: str, url: str, **kwargs) -> Response:
    """Make a request."""
    # We don't need to read response body here
    async with client.stream(method, url, **kwargs) as response:
        return response


def exc_to_code(exc: HTTPError) -> int:
    """Convert an exception into a response code."""
    if isinstance(exc, HTTPStatusError):
        return exc.response and exc.response.status_code or 418

    if isinstance(exc, ConnectError):
        return 502

    if isinstance(exc, NetworkError):
        return 503

    if isinstance(exc, TimeoutException):
        return 504

    return 418
