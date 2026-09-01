"""In-memory rate limiter."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict


class RateLimiter:
    def __init__(self, max_requests: int = 120, window_seconds: int = 60) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > self._window:
                q.popleft()
            if len(q) >= self._max:
                return False
            q.append(now)
            return True


rate_limiter = RateLimiter()
