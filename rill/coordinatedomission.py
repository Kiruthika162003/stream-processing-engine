"""Coordinated omission: the stall hides its own victims until you add them back.

A latency benchmark that sends a request, waits for the response,
then sends the next one measures a comforting lie whenever the
system stalls. During a long pause the harness is blocked waiting
too, so the requests it should have sent on schedule are never
sent and never timed, and the one slow sample it does record
stands in for a whole burst of requests that would each have seen
much of that stall. The measured distribution therefore omits
exactly the samples the stall hurt most, and its tail reads far
better than reality, the failure Gil Tene named coordinated
omission. The correction reconstructs the omitted requests from
the expected send interval: a response that took longer than the
interval implies requests that should have started at each
interval boundary during the wait, and each of those would have
observed the remaining stall, so they are backfilled with
latencies stepping down from the stall by the interval. Folding
those synthetic samples back in restores the tail the naive
measurement erased. This module backfills the omitted latencies
and reports a percentile, so the gap between the flattering naive
tail and the corrected one is a measured number.
"""

from __future__ import annotations

from rill.errors import Invalid


def correct(measured: list[int], expected_interval: int) -> list[int]:
    if expected_interval <= 0:
        raise Invalid("expected interval must be positive")
    if not measured:
        raise Invalid("no measurements")
    out: list[int] = []
    for latency in measured:
        if latency < 0:
            raise Invalid("latency cannot be negative")
        out.append(latency)
        backfill = latency - expected_interval
        while backfill > 0:
            out.append(backfill)
            backfill -= expected_interval
    return out


def percentile(latencies: list[int], quantile: float) -> int:
    if not latencies:
        raise Invalid("no latencies")
    if not 0.0 < quantile <= 1.0:
        raise Invalid("quantile in (0, 1]")
    ordered = sorted(latencies)
    index = max(0, min(len(ordered) - 1, round(quantile * len(ordered)) - 1))
    return ordered[index]
