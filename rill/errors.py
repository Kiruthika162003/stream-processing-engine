"""The error family: every refusal in this package speaks a full sentence.

Streams fail in ways batch jobs cannot: an event can be valid
and still arrive after its window closed, a source can be
healthy and still lie about time, and an operator can be
correct and still see its input out of order. The hierarchy
gives each failure its own name so callers can catch what they
mean: Invalid for requests that were never going to work, Missing
for things that should exist and do not, Late for events that
arrived behind the watermark they answer to, and Halted for
operations against a stream that has already been closed.
"""

from __future__ import annotations


class RillError(Exception):
    pass


class Invalid(RillError):
    pass


class Missing(RillError):
    pass


class Late(RillError):
    pass


class Halted(RillError):
    pass
