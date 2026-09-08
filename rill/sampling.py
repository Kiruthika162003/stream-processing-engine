"""Sampling a stream: a fair fraction, decided per event, forever.

Debugging a firehose needs a sample, and the two easy
mistakes are sampling the first N, which is a sample of the
morning, and sampling every Nth, which aliases against any
periodic pattern in the traffic. Hash sampling decides per
event from the event's own identity: hash the id, keep the
event if the hash lands under the rate, so the decision is
stateless, reproducible, and consistent across restarts and
machines, and the same event is always in or always out,
which makes the sample joinable: a sampled request stream and
a sampled error stream built on the same identity share
exactly their intersection. The meter tracks realized rate
against requested, because hash sampling is exact only in
expectation, and small streams wander, a truth better printed
than discovered during an incident extrapolation.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.content_hash import stable_bucket
from rill.errors import Invalid

RATE_BUCKETS = 1000


@dataclass
class HashSampler:
    rate_permille: int
    seen: int = 0
    kept: int = 0

    def __post_init__(self) -> None:
        if not 0 < self.rate_permille <= RATE_BUCKETS:
            raise Invalid(
                "the rate is per-mille, between 1 and 1000"
            )

    def admit(self, identity: str) -> bool:
        if not identity:
            raise Invalid("sampling needs the event's identity")
        self.seen += 1
        chosen = (
            stable_bucket(identity, RATE_BUCKETS)
            < self.rate_permille
        )
        if chosen:
            self.kept += 1
        return chosen

    def realized(self) -> str:
        if self.seen == 0:
            raise Invalid("no events seen; the rate is a wish")
        realized = 1000 * self.kept / self.seen
        drift = realized - self.rate_permille
        return (
            f"requested {self.rate_permille} per mille, "
            f"realized {realized:.0f} over {self.seen} "
            f"event(s) (drift {drift:+.0f}); exact only in "
            "expectation, and small streams wander"
        )


def joinability_drill(identities: list[str]) -> str:
    if not identities:
        raise Invalid("no identities to drill")
    requests = HashSampler(rate_permille=100)
    errors = HashSampler(rate_permille=100)
    in_requests = {
        identity
        for identity in identities
        if requests.admit(identity)
    }
    in_errors = {
        identity
        for identity in identities
        if errors.admit(identity)
    }
    if in_requests == in_errors:
        return (
            f"{len(in_requests)} sampled on both streams, "
            "identical membership: the same event is always "
            "in or always out, so the samples join"
        )
    return (
        "DIVERGED: the two samplers disagreed on the same "
        "identities, which breaks every joined investigation"
    )
