"""Bipartite matching: assigning tasks to workers so the most get done, past what greedy sees.

Assigning tasks to the workers able to do them, one worker per
task and one task per worker, to complete the most tasks is
maximum bipartite matching. A greedy pass, take each task and give
it to any free capable worker, can strand tasks: it may hand a
worker to a task that had other options, leaving a task with only
that worker unassignable, so greedy finishes with fewer matches
than possible. The augmenting-path method finds the true maximum.
For each unmatched task it searches for an augmenting path, a
chain that starts at the task, reaches a worker, and if that
worker is already taken, tries to re-home its current task to
another worker, cascading until it either frees a worker or fails.
Every augmenting path found increases the matching by one, and
when no more exist the matching is provably maximum. The key move
is the re-homing: greedy never revisits an assignment it made,
while the augmenting search will bump an earlier match aside if
doing so lets two tasks be served where one was, which is exactly
the case greedy loses. This module runs the augmenting-path search
and, for contrast, a greedy pass, so the extra tasks the augmenting
method assigns are a measured difference on a case greedy strands.
"""

from __future__ import annotations


def _augment(
    task: str,
    edges: dict[str, list[str]],
    match: dict[str, str],
    visited: set[str],
) -> bool:
    for worker in edges.get(task, []):
        if worker in visited:
            continue
        visited.add(worker)
        if worker not in match or _augment(match[worker], edges, match, visited):
            match[worker] = task
            return True
    return False


def max_matching(edges: dict[str, list[str]]) -> int:
    match: dict[str, str] = {}
    for task in edges:
        _augment(task, edges, match, set())
    return len(match)


def greedy_matching(edges: dict[str, list[str]]) -> int:
    taken: set[str] = set()
    matched = 0
    for workers in edges.values():
        for worker in workers:
            if worker not in taken:
                taken.add(worker)
                matched += 1
                break
    return matched
