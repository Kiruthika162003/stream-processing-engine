"""The right to be forgotten: deletion across a system built to remember.

A stream platform is an apparatus for never losing anything,
and then a deletion request arrives with legal force, so
forgetting becomes an engineering project with a checklist:
the live state drops the keys, the compacted log tombstones
them, the read models purge, and the raw retention window is
the honest exception, immutable segments age out on schedule
and the certificate says so rather than pretending. The
eraser walks the checklist per subject, refuses to certify
while any station is unfinished, and the certificate names
the retention tail's expiry date, because "deleted everywhere
except the 30-day raw log, gone by March 3" is a sentence
legal can work with, while "deleted" delivered early is a
sentence that gets disproven in discovery.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

STATIONS = ("live-state", "compacted-log", "read-models")


@dataclass
class Eraser:
    retention_days: int
    progress: dict[str, set[str]] = field(default_factory=dict)
    certified: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.retention_days < 1:
            raise Invalid("retention is at least a day")

    def open_request(self, subject: str) -> str:
        if not subject:
            raise Invalid("forgetting needs a subject")
        if subject in self.progress:
            raise Invalid(f"{subject} already in progress")
        self.progress[subject] = set()
        return (
            f"{subject}: forgetting begins, "
            f"{len(STATIONS)} station(s) on the checklist"
        )

    def complete_station(
        self, subject: str, station: str
    ) -> str:
        if subject not in self.progress:
            raise Invalid(f"{subject} has no open request")
        if station not in STATIONS:
            raise Invalid(f"{station} is not on the checklist")
        self.progress[subject].add(station)
        remaining = len(STATIONS) - len(self.progress[subject])
        return f"{subject}: {station} purged, {remaining} to go"

    def certify(self, subject: str, today: str) -> str:
        done = self.progress.get(subject)
        if done is None:
            raise Invalid(f"{subject} has no open request")
        unfinished = sorted(set(STATIONS) - done)
        if unfinished:
            raise Invalid(
                f"cannot certify {subject}: "
                f"{', '.join(unfinished)} unfinished, and a "
                "deleted delivered early gets disproven in "
                "discovery"
            )
        del self.progress[subject]
        certificate = (
            f"{subject}: deleted everywhere except the "
            f"{self.retention_days}-day raw log, which ages "
            f"out on schedule from {today}; a sentence legal "
            "can work with"
        )
        self.certified.append(subject)
        return certificate
