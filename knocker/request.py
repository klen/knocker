import asyncio as aio
import logging

from httpx import HTTPError

from .config import RETRIES_BACKOFF_FACTOR_MAX


logger = logging.getLogger('knocker')


async def process(client, config, method, url, **kwargs):
    """Send requests."""
    attempts = 0
    error = None

    while True:
        try:
            attempts += 1
            await request(client, method, url, timeout=config['timeout'], **kwargs)
            logger.info('Request processed: %s', url)

        except HTTPError as exc:

            if config['retries'] > (attempts - 1):
                await aio.sleep(min(RETRIES_BACKOFF_FACTOR_MAX, (
                    config['backoff_factor'] * (2 ** (attempts - 1))
                )))
                continue

            error = exc.response and exc.response.status_code or 999
            logger.info('Request failed [%s]: %s', attempts, url)

        break

    if error and config.get('callback'):
        aio.create_task(process(
            client, config, 'GET', config.pop('callback'), json={
                'config': config,
                'method': method,
                'status_code': error,
                'url': url,
            }
        ))


async def request(client, method, url, **kwargs):
    """Make a request."""
    async with client.stream(method, url, **kwargs) as response:
        logger.info('Response [%s]: %s', response.status_code, url)
        response.raise_for_status()

    return response
