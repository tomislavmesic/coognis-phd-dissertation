from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import time


@dataclass
class RateLimitState:
    count: int
    reset_at: float


class AuthRateLimiter:
    def __init__(self) -> None:
        self._states: dict[str, RateLimitState] = {}
        self._lock = Lock()

    def check(self, key: str, *, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time()
        with self._lock:
            state = self._states.get(key)
            if state is None or state.reset_at <= now:
                self._states[key] = RateLimitState(count=1, reset_at=now + window_seconds)
                return True, limit - 1

            if state.count >= limit:
                return False, max(0, int(state.reset_at - now))

            state.count += 1
            return True, max(0, limit - state.count)

    def reset(self, key: str) -> None:
        with self._lock:
            self._states.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._states.clear()


auth_rate_limiter = AuthRateLimiter()
