from typing import Literal, NotRequired, TypedDict


class TStatus(TypedDict):
    """Status of the server."""

    status: bool
    processed: int
    tasks: int
    version: str
    worker: int


class TRequestConfig(TypedDict, total=False):
    host: str
    scheme: Literal["http", "https"]
    callback: NotRequired[str | None]
    id: str
    timeout: float
    retries: int
    backoff_factor: float


TRequestAccepted = TypedDict(
    "TRequestAccepted",
    {
        "status": bool,
        "config": TRequestConfig,
        "url": str,
        "method": str,
        "headers": list[tuple[str, str]],
        "body-length": int,
    },
)
