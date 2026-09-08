"""One slow async call at the head, and the buffer that fills behind it.

The drill submits six events to an ordered async emitter, lets
the last five finish first in reverse, and holds the head open.
The guess going in was that ordered mode would keep maybe one or
two answers waiting, since the head is only one call. The
measurement says five: every one of the followers completed and
none could be released, because ordered emission will not ship an
answer until every earlier event has also shipped, so the buffer
peaked at five completed answers pinned behind a single dragging
call. When the head finally lands, all six leave at once and in
input order. The deposition keeps the low guess beside the
measured five because the surprise is the shape of the cost: an
ordered emitter's buffer tracks the latency tail, not the
throughput, so one slow call in a heavy tail is enough to hold
the whole batch.
"""

from __future__ import annotations

from rill.asyncorder import AsyncEmitter
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    emitter = AsyncEmitter(mode="ordered")
    head = emitter.submit("head")
    followers = [emitter.submit(f"e{n}") for n in range(5)]
    released_before_head = 0
    for token in reversed(followers):
        released_before_head += len(emitter.complete(token, f"a{token}"))
    peak = emitter.peak_buffer()
    final = emitter.complete(head, "HEAD")
    numbers = {
        "guessed_peak_buffer": 2,
        "measured_peak_buffer": peak,
        "released_before_head_landed": released_before_head,
        "released_when_head_landed": len(final),
        "head_first_in_output": final[0] == "HEAD",
    }
    holds = (
        peak == 5
        and released_before_head == 0
        and len(final) == 6
        and final[0] == "HEAD"
    )
    return Deposition(
        witness="slowhead",
        claim=(
            "ordered async emission held five finished answers "
            "behind one slow head, released nothing until the "
            "head landed, then shipped all six in input order, so "
            "the buffer tracks the latency tail and not the "
            "throughput"
        ),
        numbers=numbers,
        holds=holds,
    )
