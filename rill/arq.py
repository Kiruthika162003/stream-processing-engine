"""ARQ retransmission: go-back-N resends the whole tail, selective repeat resends the loss.

Reliable delivery over a lossy channel retransmits what was lost,
and the two classic protocols make opposite trades on how much to
resend. Go-back-N keeps the receiver simple: it accepts packets
strictly in order and discards anything after a gap, so a single
lost packet forces the sender to go back and retransmit that
packet and every packet after it in the window, because the
receiver threw them all away. The receiver needs no buffer beyond
the next expected sequence, but a lone loss late in a large window
retransmits nearly the whole window. Selective repeat spends
receiver memory to save bandwidth: the receiver buffers the
out-of-order packets that arrived after the gap and acknowledges
them individually, so the sender retransmits only the packet that
was actually lost, one packet instead of a tail. The trade is
exactly buffer for bandwidth, a stateless receiver that wastes the
link on any loss against a buffering receiver that wastes nothing
but must hold and reorder. Which wins depends on whether the
channel's loss rate makes the retransmitted tail expensive enough
to justify the receiver complexity. This module computes the
retransmission count each protocol pays for a given loss in a
window, so the tail-versus-one difference is a measured number.
"""

from __future__ import annotations

from rill.errors import Invalid


def _validate(window: int, lost_index: int) -> None:
    if window < 1:
        raise Invalid("window must be positive")
    if not 0 <= lost_index < window:
        raise Invalid("lost index out of the window")


def go_back_n(window: int, lost_index: int) -> int:
    _validate(window, lost_index)
    return window - lost_index


def selective_repeat(window: int, lost_index: int) -> int:
    _validate(window, lost_index)
    return 1
