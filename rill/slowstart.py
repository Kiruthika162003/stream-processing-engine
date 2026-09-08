"""Congestion control: probe fast until the threshold, then crawl, and halve on loss.

A sender ramping its in-flight window has two jobs that want
opposite behavior: find the available bandwidth quickly, and once
near it, approach gently so it does not overshoot into loss. TCP
splits them at a threshold. Below the slow-start threshold the
window doubles every round trip, an exponential ramp that reaches
a large window in a logarithmic number of rounds, so a fresh
connection finds its operating point fast rather than crawling up
from one. At or above the threshold it switches to congestion
avoidance and grows by one per round, the additive increase that
probes for a little more headroom without lurching past it. A
loss is the signal that the window was too big, and the response
is multiplicative: the threshold drops to half the window and the
ramp restarts, so the sender retreats hard and re-approaches
carefully, the same additive-increase multiplicative-decrease
shape that keeps many senders sharing a link from collapsing it.
This module runs the window through both phases and the loss
response, reporting the window and the phase, so the fast probe,
the gentle approach, and the hard retreat are a measured sequence.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid

SLOW_START = "slow_start"
CONGESTION_AVOIDANCE = "congestion_avoidance"


@dataclass
class CongestionControl:
    cwnd: int = 1
    ssthresh: int = 64

    def __post_init__(self) -> None:
        if self.cwnd < 1 or self.ssthresh < 1:
            raise Invalid("window and threshold must be positive")

    def phase(self) -> str:
        return SLOW_START if self.cwnd < self.ssthresh else CONGESTION_AVOIDANCE

    def on_ack(self) -> int:
        if self.cwnd < self.ssthresh:
            self.cwnd = min(self.ssthresh, self.cwnd * 2)
        else:
            self.cwnd += 1
        return self.cwnd

    def on_loss(self) -> int:
        self.ssthresh = max(1, self.cwnd // 2)
        self.cwnd = 1
        return self.cwnd
