"""The shuffle: every key to its owner, and the all-to-all that eats the network.

Between a keyed operation and the next, every event must move
from the node that produced it to the node that owns its key,
and in the worst case every producer sends to every consumer,
an all-to-all whose message count grows with the product of
the two, not their sum. The shuffle's cost is that product,
and the two levers against it are the local combiner, which
shrinks what each producer sends, and co-location, which
places producer and consumer on the same node so their
traffic never touches the wire. The planner prices a shuffle
by counting cross-node messages against same-node ones, and
the ratio is the diagnosis: a shuffle that is mostly
cross-node is a network bill, while one that is mostly
co-located has already been optimized, and knowing which
before adding hardware is the difference between buying
bandwidth and buying nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.content_hash import stable_bucket
from rill.errors import Invalid


@dataclass
class ShufflePlanner:
    consumer_nodes: int
    producer_of: dict[str, int] = field(default_factory=dict)
    cross_node: int = 0
    same_node: int = 0

    def __post_init__(self) -> None:
        if self.consumer_nodes < 1:
            raise Invalid("a shuffle needs consumers")

    def owner_node(self, key: str) -> int:
        return stable_bucket(key, self.consumer_nodes)

    def route(self, key: str, producer_node: int) -> str:
        if producer_node < 0:
            raise Invalid("producer nodes are nonnegative")
        self.producer_of[key] = producer_node
        owner = self.owner_node(key)
        if owner == producer_node:
            self.same_node += 1
            return f"{key}: co-located on node {owner}, no wire"
        self.cross_node += 1
        return (
            f"{key}: node {producer_node} -> node {owner}, "
            "crosses the wire"
        )

    def cost_report(self) -> str:
        total = self.cross_node + self.same_node
        if total == 0:
            raise Invalid("nothing shuffled")
        cross_share = 100 * self.cross_node // total
        if cross_share >= 70:
            diagnosis = (
                "a network bill: mostly cross-node, so "
                "bandwidth or a combiner will help"
            )
        elif cross_share <= 30:
            diagnosis = (
                "already co-located: buying bandwidth here "
                "buys nothing"
            )
        else:
            diagnosis = "mixed: measure the combiner before the hardware"
        return (
            f"{self.cross_node} cross-node, {self.same_node} "
            f"same-node ({cross_share}% on the wire); "
            f"{diagnosis}"
        )
