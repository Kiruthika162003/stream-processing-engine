"""Queueing theory: waiting time does not rise with load, it explodes near full utilization.

The relationship between how busy a server is and how long
requests wait for it is not linear, and treating it as if it were
is how capacity plans go wrong. For a simple queue with random
arrivals and service, the mean number of requests waiting grows as
the utilization over one minus the utilization, so the wait scales
with one over one minus utilization, a curve that is nearly flat
while there is slack and then turns almost vertical as utilization
approaches one. At fifty percent busy a request waits about one
service time; at ninety percent it waits about nine; at
ninety-nine percent about ninety-nine. The last few percent of
utilization, the capacity a spreadsheet says is still available,
is where the latency lives, which is why running a server near a
hundred percent to save money produces a system that is fine on
average and catastrophic at the peak. The practical reading is
that headroom is not waste, it is the latency budget: the
difference between running at seventy and ninety percent is small
in throughput and enormous in tail latency. This module computes
the mean queue length and wait from the utilization, so the
explosion near full load is a number a capacity plan can see
rather than discover in an incident.
"""

from __future__ import annotations

from rill.errors import Invalid


def mean_queue_length(utilization: float) -> float:
    if not 0.0 <= utilization < 1.0:
        raise Invalid("utilization must be in [0, 1)")
    return utilization / (1 - utilization)


def mean_wait(utilization: float, service_time: float) -> float:
    if service_time <= 0:
        raise Invalid("service time must be positive")
    return service_time * mean_queue_length(utilization)
