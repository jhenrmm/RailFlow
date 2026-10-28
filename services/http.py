"""Shared synchronous HTTP transport for upstream API calls."""

import random
import time
from typing import Any

import httpx

from config import HTTP_MAX_CONNECTIONS, HTTP_RETRY_ATTEMPTS, HTTP_RETRY_BACKOFF_SECONDS

_client: httpx.Client | None = None


class UpstreamServiceError(RuntimeError):
    """An upstream dependency did not return a usable response."""


def _get_client() -> httpx.Client:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.Client(
            limits=httpx.Limits(
                max_connections=HTTP_MAX_CONNECTIONS,
                max_keepalive_connections=10,
            ),
        )
    return _client


def request_with_retries(
    method: str,
    url: str,
    *,
    timeout: float,
    attempts: int = HTTP_RETRY_ATTEMPTS,
    **kwargs: Any,
) -> httpx.Response:
    """Send a request with bounded exponential backoff and jitter."""
    last_error: httpx.HTTPError | None = None
    for attempt in range(attempts):
        try:
            response = _get_client().request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as exc:
            last_error = exc
            if attempt + 1 < attempts:
                delay = HTTP_RETRY_BACKOFF_SECONDS * (2**attempt)
                time.sleep(delay + random.uniform(0, delay / 4))
    raise UpstreamServiceError(f"Upstream request failed: {method} {url}") from last_error


def close_http_client() -> None:
    if _client is not None:
        _client.close()
