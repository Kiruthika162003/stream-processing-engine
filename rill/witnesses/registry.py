"""Every witness, one call, one page."""

from __future__ import annotations

import importlib

from rill.witnesses.deposition import Deposition

WITNESSES: tuple[str, ...] = (
    "rill.witnesses.boundbet",
    "rill.witnesses.movebill",
    "rill.witnesses.crashdial",
    "rill.witnesses.idlefreeze",
    "rill.witnesses.herdjump",
    "rill.witnesses.exactlyonce",
    "rill.witnesses.storminvsbudget",
    "rill.witnesses.unionminimum",
    "rill.witnesses.cardinalitymerge",
    "rill.witnesses.slowhead",
    "rill.witnesses.arcsteal",
    "rill.witnesses.touchonce",
    "rill.witnesses.secondprobe",
    "rill.witnesses.cancellation",
    "rill.witnesses.maskedspike",
    "rill.witnesses.chatterband",
    "rill.witnesses.greedytrap",
    "rill.witnesses.hockeystick",
    "rill.witnesses.bottleneck",
    "rill.witnesses.fairdeal",
)


def all_depositions() -> list[Deposition]:
    depositions = []
    for dotted in WITNESSES:
        module = importlib.import_module(dotted)
        depositions.append(module.run())
    return depositions


def broken() -> list[str]:
    return [
        deposition.witness
        for deposition in all_depositions()
        if not deposition.holds
    ]


def report() -> str:
    depositions = all_depositions()
    lines = [deposition.line() for deposition in depositions]
    failing = sum(
        1 for deposition in depositions if not deposition.holds
    )
    lines.append("")
    lines.append(
        f"{len(depositions)} witnesses, {failing} broken"
    )
    return "\n".join(lines)
