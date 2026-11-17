"""Export graph to JSON / Markdown / DOT."""

from __future__ import annotations

import json
from pathlib import Path

from evidence_graph.claims import evaluate_claim
from evidence_graph.graph import EvidenceGraph
from evidence_graph.models import NodeKind


def write_json(graph: EvidenceGraph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(graph.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def render_markdown(graph: EvidenceGraph) -> str:
    lines = [
        "# DUP Evidence Graph",
        "",
        f"- packs: **{len(graph.packs)}**",
        f"- nodes: **{len(graph.nodes)}**",
        f"- edges: **{len(graph.edges)}**",
        "",
        "## Products",
        "",
    ]
    for product in graph.config.get("products") or []:
        pid = product["id"]
        exists = product.get("_root_exists")
        root = product.get("_resolved_root")
        lines.append(
            f"### `{pid}` — {product.get('name')} "
            f"({'on disk' if exists else 'MISSING'})"
        )
        lines.append("")
        lines.append(f"- repo: `{product.get('repo')}`")
        lines.append(f"- root: `{root}`")
        lines.append(f"- packs: {len(graph.packs_for(pid))}")
        lines.append("")
        lines.append("| Claim | Allowed | Reason |")
        lines.append("|-------|---------|--------|")
        for claim in product.get("claims") or []:
            v = evaluate_claim(pid, claim, graph.packs)
            lines.append(
                f"| `{claim}` | {'YES' if v.allowed else 'NO'} | {v.reason} |"
            )
        lines.append("")

    lines.append("## Boundaries")
    lines.append("")
    lines.append("Cross-family claim transfer is **forbidden** (l1-boundary).")
    lines.append("")
    for b in graph.config.get("boundaries") or []:
        lines.append(
            f"- `{b.get('from_family')}` → `{b.get('to_family')}`: {b.get('rule')}"
        )
    lines.append("")
    lines.append(
        "Honesty: 48h soak only when `approx_48h_claim_ok=true` AND `hard_fails=0`."
    )
    lines.append("")
    return "\n".join(lines)


def write_markdown(graph: EvidenceGraph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(graph), encoding="utf-8")


def render_dot(graph: EvidenceGraph) -> str:
    lines = ["digraph dup_evidence {", "  rankdir=LR;", "  node [shape=box];"]
    for n in graph.nodes.values():
        if n.attrs.get("synthetic") and n.kind is NodeKind.PRODUCT and n.id.startswith("family:"):
            shape = "diamond"
        elif n.kind is NodeKind.CLAIM:
            shape = "ellipse"
        elif n.kind is NodeKind.PACK:
            shape = "note"
        else:
            shape = "box"
        label = n.label.replace('"', "'")[:64]
        lines.append(f'  "{n.id}" [label="{label}", shape={shape}];')
    for e in graph.edges:
        lines.append(f'  "{e.src}" -> "{e.dst}" [label="{e.kind.value}"];')
    lines.append("}")
    return "\n".join(lines) + "\n"


def write_dot(graph: EvidenceGraph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_dot(graph), encoding="utf-8")
