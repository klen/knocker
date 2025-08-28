from __future__ import annotations

from unittest import mock

from httpx import Request, Response


@mock.patch("knocker.request.request")
@mock.patch("knocker.request.sentry_sdk")
async def test_sentry(msentry, mrequest, client, wait_for_other):
    from knocker import config

    config.update(SENTRY_DSN="test", SENTRY_FAILED_REQUESTS=True)

    mrequest.return_value = Response(400, request=Request("GET", "https://test.com"))
    res = await client.post(
        "/test/me?q=1",
        headers={
            "knocker-host": "test.com",
            "knocker-retries": "1",
            "knocker-backoff-factor": ".1",
        },
    )
    assert res.status_code == 200

    await wait_for_other()
    assert msentry.capture_exception.called
