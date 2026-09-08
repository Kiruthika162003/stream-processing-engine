"""Critical path: the longest chain of dependencies sets the floor, and only it moves.

A pipeline of stages with dependencies finishes no sooner than
its longest chain of dependent work, the critical path, because
every stage on that chain must wait for the one before it, so
their durations add and nothing can overlap them away. Stages off
the critical path run in the slack beside it and finish early with
time to spare, which means the two ways people try to speed a
pipeline up divide sharply: shortening a stage on the critical
path lowers the whole makespan by that much, while shortening a
stage off it changes nothing at all, the effort absorbed by the
slack it already had. Finding the critical path is a longest-path
computation over the dependency graph, done by processing stages
in dependency order and tracking, for each, the earliest it can
finish given the latest of its predecessors, with the makespan the
largest of those finishes. The distinction the number draws is the
useful one for anyone optimizing a pipeline: measure the critical
path first, because the stage everyone complains about is often
sitting in slack while an unglamorous one on the path sets the
floor. This module computes the critical path length and the chain
that achieves it, so the makespan and where to spend effort are a
result rather than a guess.
"""

from __future__ import annotations

from rill.errors import Invalid


def critical_path(
    predecessors: dict[str, list[str]], duration: dict[str, int]
) -> tuple[int, list[str]]:
    if not duration:
        raise Invalid("no stages")
    finish: dict[str, int] = {}
    best_pred: dict[str, str | None] = {}

    def compute(node: str, visiting: set[str]) -> int:
        if node in finish:
            return finish[node]
        if node in visiting:
            raise Invalid(f"cycle through {node}")
        if node not in duration:
            raise Invalid(f"stage {node} has no duration")
        visiting.add(node)
        best = 0
        chosen = None
        for pred in predecessors.get(node, []):
            pred_finish = compute(pred, visiting)
            if pred_finish > best:
                best = pred_finish
                chosen = pred
        visiting.discard(node)
        finish[node] = best + duration[node]
        best_pred[node] = chosen
        return finish[node]

    for node in duration:
        compute(node, set())
    end = max(finish, key=lambda n: finish[n])
    path: list[str] = []
    cursor: str | None = end
    while cursor is not None:
        path.append(cursor)
        cursor = best_pred[cursor]
    path.reverse()
    return finish[end], path
