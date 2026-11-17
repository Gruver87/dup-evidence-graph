"""DUP Evidence Graph — queryable honesty map over local packs."""

from __future__ import annotations

__version__ = "0.1.1"

from evidence_graph.graph import EvidenceGraph
from evidence_graph.scan import scan_products

__all__ = ["__version__", "EvidenceGraph", "scan_products"]
