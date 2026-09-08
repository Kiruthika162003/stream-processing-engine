"""Every witness, one call, one page."""

from __future__ import annotations

import importlib

from rill.witnesses.testimony import Testimony

WITNESSES: tuple[str, ...] = ()


def all_testimony() -> list[Testimony]:
    testimonies = []
    for dotted in WITNESSES:
        module = importlib.import_module(dotted)
        testimonies.append(module.run())
    return testimonies


def broken() -> list[str]:
    return [
        testimony.witness
        for testimony in all_testimony()
        if not testimony.holds
    ]


def report() -> str:
    testimonies = all_testimony()
    lines = [testimony.line() for testimony in testimonies]
    failing = sum(
        1 for testimony in testimonies if not testimony.holds
    )
    lines.append("")
    lines.append(
        f"{len(testimonies)} witnesses, {failing} broken"
    )
    return "\n".join(lines)
