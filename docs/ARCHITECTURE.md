# Architecture — dup-evidence-graph

**Org:** DUP Labs · **Role:** queryable honesty map over local evidence packs

## Why

Agents and operators mix radar / bot / L1 claims. This tool builds a graph from
**on-disk** packs and answers fail-closed questions:

- Can product X claim `soak_48h`?
- Which packs support `ops_ready`?
- Are entries unlocked on the bot?

Cross-family edges are **boundaries** (see `l1-boundary` skill) — never transferable.

## Claims (radar)

| Claim | Rule |
|-------|------|
| `ops_ready` | `ops_ready=true` |
| `short_soak` | `hard_fails=0` (not 48h) |
| `soak_48h` | `approx_48h_claim_ok=true` **and** `hard_fails=0` |
| `verify_full` | run_id / path contains `verify-full` |

Missing pack → claim **refused** (never invent PASS).

## CLI

```text
dup-evidence-graph scan
dup-evidence-graph query radar soak_48h
dup-evidence-graph packs radar
dup-evidence-graph board
dup-evidence-graph export --dir out
```
