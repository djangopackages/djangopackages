from __future__ import annotations

import random
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque

from rich import print


@dataclass
class RateLimiter:
    """Rate limiter for cron-style jobs.

    Goals:
    - Keep request pace smooth (avoid bursts).
    - Enforce hard caps (stop when a limit is reached).
    - Add small jitter to reduce synchronization with other workers.
    """

    min_interval: float = 0.0
    max_per_minute: int | None = None
    jitter: float = 0.0
    stop_on_limit: bool = True
    _last_ts: float = 0.0
    _window: Deque[float] = field(default_factory=deque)

    def wait(self) -> None:
        """Block or stop before issuing the next outbound request.

        - `min_interval` enforces a minimum gap between calls.
        - `max_per_minute` caps throughput using a sliding window.
        - `jitter` randomizes timing to avoid thundering herds.
        - `stop_on_limit=True` raises immediately instead of sleeping.
        """
        now = time.monotonic()

        if self.min_interval > 0 and self._last_ts:
            elapsed = now - self._last_ts
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                print(
                    f"[dim]RateLimiter: Sleeping {sleep_time:.2f}s (min_interval)[/dim]"
                )
                time.sleep(sleep_time)

        if self.max_per_minute:
            now = time.monotonic()
            cutoff = now - 60
            while self._window and self._window[0] < cutoff:
                self._window.popleft()

            if len(self._window) >= self.max_per_minute:
                if self.stop_on_limit:
                    raise RuntimeError("rate limit reached")
                sleep_for = self._window[0] + 60 - now
                if sleep_for > 0:
                    print(
                        f"[yellow]RateLimiter: Sleeping {sleep_for:.2f}s (max_per_minute)[/yellow]"
                    )
                    time.sleep(sleep_for)

        if self.jitter:
            time.sleep(random.uniform(0, self.jitter))

        now = time.monotonic()
        self._last_ts = now
        if self.max_per_minute:
            self._window.append(now)

    def stop_if_remaining_below(
        self, remaining: int | None, threshold: int, *, label: str
    ) -> None:
        """Stop when a provider reports remaining quota below a threshold.

        This is for APIs that expose quota counters (e.g. GitHub). For providers
        without counters, rely on HTTP 429 handling instead.
        """
        if remaining is None or remaining > threshold:
            return
        raise RuntimeError(f"{label} rate limit reached")
