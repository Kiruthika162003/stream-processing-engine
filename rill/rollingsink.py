"""Rolling file sink: rolling on size alone strands the quiet bucket's data.

A file sink groups records into buckets and writes each bucket to
an in-progress file that it rolls closed and commits once it is
full. Roll on size alone and the rule reads fine until a bucket
goes quiet: its half-full file never reaches the size cap, so it
never rolls, so its records stay in an in-progress file that
downstream readers cannot see, and the data is not lost but it is
invisible for as long as the bucket stays slow, which on a
low-traffic partition is forever. The fix is a second and third
trigger: roll on a maximum age so a file that has been open too
long commits regardless of size, and roll on inactivity so a
bucket that has stopped receiving flushes what it has. This
module tracks per-bucket open files and rolls on the first of
size, age, or idle to fire, so the visibility latency of the
quiet bucket is bounded by the age and idle timers rather than by
the arrival of traffic that may never come.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class OpenFile:
    opened_at: int
    last_write: int
    records: int


@dataclass
class RollingSink:
    max_records: int
    max_age: int
    idle_timeout: int
    _open: dict[str, OpenFile] = field(default_factory=dict)
    _rolled: list[tuple[str, int, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if min(self.max_records, self.max_age, self.idle_timeout) <= 0:
            raise Invalid("every roll trigger must be positive")

    def write(self, bucket: str, now: int) -> None:
        handle = self._open.get(bucket)
        if handle is None:
            self._open[bucket] = OpenFile(opened_at=now, last_write=now, records=1)
            return
        handle.records += 1
        handle.last_write = now
        if handle.records >= self.max_records:
            self._roll(bucket, "size")

    def tick(self, now: int) -> None:
        for bucket in list(self._open):
            handle = self._open[bucket]
            if now - handle.opened_at >= self.max_age:
                self._roll(bucket, "age")
            elif now - handle.last_write >= self.idle_timeout:
                self._roll(bucket, "idle")

    def _roll(self, bucket: str, reason: str) -> None:
        handle = self._open.pop(bucket)
        self._rolled.append((bucket, handle.records, reason))

    def open_buckets(self) -> list[str]:
        return sorted(self._open)

    def committed(self) -> list[tuple[str, int, str]]:
        return list(self._rolled)
