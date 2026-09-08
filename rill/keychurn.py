"""Key churn: the state's future size is written in the keyspace's turnover.

Two streams with the same event rate can need wildly
different state: the one keyed by a stable million users
plateaus, the one keyed by session ids grows forever unless
swept, and the difference is churn, the share of each
window's keys never seen before. The census splits ar