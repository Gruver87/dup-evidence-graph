"""Build and query the evidence graph."""

from __future__ import annotations

from typing import Any

from evidence_graph.claims import ClaimVerdict, evaluate_claim
from evidence_graph.models import Edge, EdgeKind, Node, NodeKind, PackRecord


class EvidenceGraph:
    def __init__(
        self,
        *,
        config: dict[str, Any],
        packs: list[PackRecord],
    ) -> None:
        self.config = config
        self.packs = packs
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self._build()

    def _add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def _add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)

    def _build(self) -> None:
        products = self.config.get("products") or []
        for product in products:
            pid = product["id"]
            self._add_node(
                Node(
                    id=f"product:{pid}",
                    kind=NodeKind.PRODUCT,
                    label=product.get("name") or pid,
                    attrs={
                        "repo": product.get("repo"),
                        "family": product.get("family"),
                        "root": product.get("_resolved_root"),
                        "root_exists": product.get("_root_exists"),
                    },
                )
            )
            for claim in product.get("claims") or []:
                cid = f"claim:{pid}:{claim}"
                self._add_node(
                    Node(
                        id=cid,
                        kind=NodeKind.CLAIM,
                        label=f"{pid}/{claim}",
                        attrs={"product_id": pid, "claim": claim},
                    )
                )

        for i, pack in enumerate(self.packs):
            nid = f"pack:{pack.product_id}:{i}:{pack.run_id or 'anon'}"
            self._add_node(
                Node(
                    id=nid,
                    kind=NodeKind.PACK,
                    label=pack.run_id or pack.pack_kind or pack.path,
                    attrs=pack.to_dict(),
                )
            )
            self._add_edge(
                Edge(
                    src=f"product:{pack.product_id}",
                    dst=nid,
                    kind=EdgeKind.HAS_PACK,
                )
            )

            # Wire claim support / refuse for key honesty claims
            for claim in ("ops_ready", "short_soak", "soak_48h", "verify_full", "entries_unlocked"):
                verdict = evaluate_claim(pack.product_id, claim, [pack])
                # Only attach if this single pack is decisive
                if claim == "ops_ready" and pack.ops_ready is True:
                    self._add_edge(
                        Edge(
                            src=nid,
                            dst=f"claim:{pack.product_id}:{claim}",
                            kind=EdgeKind.SUPPORTS,
                        )
                    )
                elif claim == "short_soak" and pack.hard_fails == 0:
                    self._add_edge(
                        Edge(
                            src=nid,
                            dst=f"claim:{pack.product_id}:{claim}",
                            kind=EdgeKind.SUPPORTS,
                            attrs={"note": "not 48h"},
                        )
                    )
                elif (
                    claim == "soak_48h"
                    and pack.approx_48h_claim_ok is True
                    and pack.hard_fails == 0
                ):
                    self._add_edge(
                        Edge(
                            src=nid,
                            dst=f"claim:{pack.product_id}:{claim}",
                            kind=EdgeKind.SUPPORTS,
                        )
                    )
                elif claim == "soak_48h" and pack.approx_48h_claim_ok is False:
                    self._add_edge(
                        Edge(
                            src=nid,
                            dst=f"claim:{pack.product_id}:{claim}",
                            kind=EdgeKind.REFUSES,
                            attrs={"reason": "approx_48h_claim_ok=false"},
                        )
                    )
                elif (
                    claim == "verify_full"
                    and pack.run_id
                    and "verify-full" in pack.run_id.lower()
                ):
                    self._add_edge(
                        Edge(
                            src=nid,
                            dst=f"claim:{pack.product_id}:{claim}",
                            kind=EdgeKind.SUPPORTS,
                        )
                    )
                elif claim == "entries_unlocked" and pack.status == "stopped":
                    self._add_edge(
                        Edge(
                            src=nid,
                            dst=f"claim:{pack.product_id}:{claim}",
                            kind=EdgeKind.REFUSES,
                            attrs={"reason": "protocol stopped"},
                        )
                    )
                _ = verdict  # keep import used for future expansion

        for b in self.config.get("boundaries") or []:
            src_f = b.get("from_family")
            dst_f = b.get("to_family")
            self._add_edge(
                Edge(
                    src=f"family:{src_f}",
                    dst=f"family:{dst_f}",
                    kind=EdgeKind.BOUNDARY,
                    attrs={"rule": b.get("rule")},
                )
            )
            self._add_node(
                Node(
                    id=f"family:{src_f}",
                    kind=NodeKind.PRODUCT,
                    label=f"family:{src_f}",
                    attrs={"synthetic": True},
                )
            )
            self._add_node(
                Node(
                    id=f"family:{dst_f}",
                    kind=NodeKind.PRODUCT,
                    label=f"family:{dst_f}",
                    attrs={"synthetic": True},
                )
            )

    def can_claim(self, product_id: str, claim: str) -> ClaimVerdict:
        return evaluate_claim(product_id, claim, self.packs)

    def packs_for(self, product_id: str) -> list[PackRecord]:
        return [p for p in self.packs if p.product_id == product_id]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "pack_count": len(self.packs),
            "product_count": sum(
                1
                for n in self.nodes.values()
                if n.kind is NodeKind.PRODUCT and not n.attrs.get("synthetic")
            ),
        }
