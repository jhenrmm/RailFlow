"""Small in-process rate limiter for sensitive unauthenticated endpoints.

For multi-process deployments, replace this with a shared Redis-backed limiter.
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from config import RATE_LIMIT_ATTEMPTS, RATE_LIMIT_WINDOW_SECONDS

_attempts: dict[str, deque[float]] = defaultdict(deque)


def guard_auth_attempt(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    attempts = _attempts[client]
    while attempts and now - attempts[0] >= RATE_LIMIT_WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= RATE_LIMIT_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Try again later.",
        )
    attempts.append(now)
