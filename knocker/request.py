import asyncio as aio
import logging

from httpx import HTTPError

from .config import RETRIES_BACKOFF_FACTOR_MAX
from .utils import get_id


logger = logging.getLogger('knocker')


async def process(client, config, method, url, **kwargs):
    """Send requests."""
    attempts = 0
    error = None
    ident = get_id()

    while True:
        try:
            attempts += 1
            res = await request(client, method, url, timeout=config['timeout'], **kwargs)
            logger.info('Request #%s done (%d): "%s" %d', ident, attempts, url, res.status_code)

        except HTTPError as exc:
            error = exc.response and exc.response.status_code or 999

            if config['retries'] > (attempts - 1):
                retry = min(RETRIES_BACKOFF_FACTOR_MAX, (
                    config['backoff_factor'] * (2 ** (attempts - 1))
                ))
                logger.warning(
                    'Request #%s fail (%d), retry in %ss: "%s" %d',
                    ident, attempts, retry, url, error)
                await aio.sleep(retry)
                continue

            logger.warning('Request #%s failed (%d): "%s" %d', ident, attempts, url, error)

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
        response.raise_for_status()

    return response
