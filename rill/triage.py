"""The triage table: from symptom to organ to first question, in one hop.

Streaming incidents present the same dozen symptoms over and
over, and the difference between a ten-minute diagnosis and a
two-hour one is usually knowing which organ owns which
symptom. The table encodes the map this repository's modules
already imply: rising lag belongs to the lag tracker and its
first question is whether drain outruns arrival; a stuck
watermark belongs to the multisource clock and its first
question is which partition went quiet; duplicate rows belong
to the epoch sink and its first question is whether the sink
counts; and so on through the dozen. The entry the table
refuses is the vague one, "it's slow", because slow is a
symptom of a symptom, and the triage forces the sharpening
question first: slow to arrive, slow to process, or slow to
seal, which are three different organs.
"""

from __future__ import annotations

from rill.errors import Invalid

TABLE: dict[str, tuple[str, str]] = {
    "lag-rising": (
        "lag tracker",
        "does drain outrun arrival, or is there no catch-up "
        "date at these rates",
    ),
    "watermark-stuck": (
        "multisource clock",
        "which partition went quiet, and is it idle or dead",
    ),
    "duplicate-rows": (
        "epoch sink",
        "does the sink count epochs, or is the outbox relay "
        "double-publishing",
    ),
    "missing-windows": (
        "gap filler",
        "did the pipeline count zero, or did it not speak",
    ),
    "answers-changed": (
        "trigger labels",
        "did someone paste an ESTIMATE where the ANSWER goes",
    ),
    "one-partition-hot": (
        "partitioner",
        "which key got famous, and is the fix split, salt, "
        "or accept",
    ),
    "state-growing": (
        "keyed state ttl",
        "what is the sweep reclaiming, and does anything "
        "expire at all",
    ),
    "balances-negative": (
        "order auditor",
        "is this the echo idempotence handles or the "
        "reordering it cannot",
    ),
}


def triage(symptom: str) -> str:
    if symptom == "its-slow":
        raise Invalid(
            "slow is a symptom of a symptom; sharpen first: "
            "slow to arrive, slow to process, or slow to "
            "seal, which are three different organs"
        )
    entry = TABLE.get(symptom)
    if entry is None:
        known = ", ".join(sorted(TABLE))
        raise Invalid(
            f"{symptom} is not in the table; the dozen known "
            f"symptoms are {known}"
        )
    organ, question = entry
    return (
        f"{symptom} -> {organ}; first question: {question}"
    )


def full_card() -> str:
    lines = [
        "the triage card, symptom to organ to first question:"
    ]
    for symptom in sorted(TABLE):
        organ, _ = TABLE[symptom]
        lines.append(f"  {symptom} -> {organ}")
    lines.append(
        "the ten-minute diagnosis is knowing which organ "
        "owns which symptom"
    )
    return "\n".join(lines)
