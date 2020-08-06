import asyncio as aio
import http

from httpx import HTTPError

from . import config as global_config, logger, __version__


async def process(client, config, method, url, **kwargs):
    """Send requests."""
    attempts = 0
    error = None
    kwargs['timeout'] = config['timeout']
    kwargs['headers'] = kwargs.get('headers') or {}
    kwargs['headers']['x-knocker'] = __version__

    while True:
        try:
            attempts += 1
            res = await request(client, method, url, **kwargs)
            res.raise_for_status()
            logger.info(
                'Request #%s done (%d): "%s %s" %d %s',
                config['id'], attempts, method, url, res.status_code,
                http.HTTPStatus(res.status_code).phrase)

        except HTTPError as exc:
            error = exc.response and exc.response.status_code or 999

            if config['retries'] > (attempts - 1):
                retry = min(global_config.RETRIES_BACKOFF_FACTOR_MAX, (
                    config['backoff_factor'] * (2 ** (attempts - 1))
                ))
                logger.warning(
                    'Request #%s fail (%d), retry in %ss: "%s %s" %d',
                    config['id'], attempts, retry, method, url, error)

                await aio.sleep(retry)
                continue

            logger.warning(
                'Request #%s failed (%d): "%s %s" %d', config['id'], attempts, method, url, error)

        # An unhandled exception
        except Exception as exc:
            logger.error(
                'Request #%s raises an exception (%d): "%s %s"',
                config['id'], attempts, method, url)
            logger.exception(exc)

        break

    if error and config.get('callback'):
        aio.create_task(process(
            client, config, 'POST', config.pop('callback'), json={
                'config': config,
                'method': method,
                'url': url,
                'status_code': error,
            }, headers=kwargs.get('headers')
        ))


async def request(client, method, url, **kwargs):
    """Make a request."""

    # We don't need to read response body here, but httpx>0.13 warns unclosed stream
    #  async with client.stream(method, url, **kwargs) as response:
    #      return response
    return await client.request(method, url, **kwargs)
