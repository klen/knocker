import asyncio as aio
import logging

from httpx import HTTPError


logger = logging.getLogger('knocker.request')


async def process(client, config, method, url, **kwargs):
    """Send requests."""
    retries = config['retries']
    backof_factor = config['backof_factor']
    error = None

    while True:
        try:
            await request(client, method, url, timeout=config['timeout'], **kwargs)
            logger.info('Request processed: %s', url)

        except HTTPError as exc:

            if retries:
                await aio.sleep(backof_factor)
                retries -= 1
                backof_factor += backof_factor
                continue

            error = exc.response and exc.response.status_code or 999
            logger.info('Request failed [%s]: %s', config['retries'] + 1, url)

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
