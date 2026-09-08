"""Idempotency keys: a retry returns the first result instead of running the work again.

A client that retries a request after a timeout does not know
whether the first attempt succeeded, so it may resend a request
the server already processed, and if the server simply processes
it again the side effect happens twice, a second charge, a
duplicate order, a doubled increment. An idempotency key fixes
this at the server. The client stamps the request with a unique
key, the server remembers the result it produced for each key, and
a retry carrying a key it has already seen gets the stored result
back without the work being redone. The crucial property is that
the effectful work runs exactly once per key no matter how many
times the request arrives, because the second and later arrivals
are served from the cache before the work is reached, not merely
deduplicated after it. This is stronger than refusing a duplicate,
which stops the second write but does not give the retrying client
the answer it is waiting for; the idempotency store both prevents
the re-execution and returns the original result, so the retry
looks to the client exactly like the first call succeeded. This
module memoizes results by key and runs the work only on the
first occurrence, so the run-once guarantee is a counted fact.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class IdempotencyStore:
    _results: dict[str, str] = field(default_factory=dict)

    def execute(self, key: str, work: Callable[[], str]) -> str:
        if not key:
            raise Invalid("idempotency key cannot be empty")
        if key in self._results:
            return self._results[key]
        result = work()
        self._results[key] = result
        return result

    def was_seen(self, key: str) -> bool:
        return key in self._results
