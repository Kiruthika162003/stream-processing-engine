"""Idle source ejection: a quiet input pins the minimum until a timeout evicts it.

The combined watermark over several sources is the minimum of
their per-source watermarks, so a source that goes quiet holds
its last watermark frozen and pins the whole combined watermark
there even while every other source races ahead. Watermark
alone cannot tell a quiet source from a slow one, so the fix is
an idleness timeout: a source that has not emitted for longer
than the timeout is marked idle and dropped out of the minimum
until it speaks again, letting the combined watermark climb to
the minimum of the sources still live. The trade the timeout
buys is not free. When the evicted source finally wakes, the
combined watermark has already advanced past it, so its first
events arrive behind the watermark that moved on without it, and
they are late by exactly the distance the watermark climbed
while the source slept. This module tracks per-source watermarks
and last-seen times, ejects the idle, and computes the combined
watermark from the survivors, so the choice of timeout is a
dial between a pinned pipeline and a source that returns late.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class IdleCoordinator:
    idle_timeout: int
    _watermark: dict[str, int] = field(default_factory=dict)
    _last_seen: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.idle_timeout <= 0:
            raise Invalid("idle timeout must be positive")

    def observe(self, source: str, watermark: int, now: int) -> None:
        prior = self._watermark.get(source)
        if prior is not None and watermark < prior:
            raise Invalid(f"{source} watermark went backward")
        self._watermark[source] = watermark
        self._last_seen[source] = now

    def _live(self, now: int) -> list[str]:
        return [
            s
            for s in self._watermark
            if now - self._last_seen[s] < self.idle_timeout
        ]

    def idle_sources(self, now: int) -> list[str]:
        return sorted(
            s
            for s in self._watermark
            if now - self._last_seen[s] >= self.idle_timeout
        )

    def combined(self, now: int) -> int:
        live = self._live(now)
        if not live:
            raise Invalid("every source is idle; no combined watermark")
        return min(self._watermark[s] for s in live)

    def lateness_on_return(self, source: str, now: int) -> int:
        if source not in self._watermark:
            raise Invalid(f"unknown source {source}")
        return max(0, self.combined(now) - self._watermark[source])
