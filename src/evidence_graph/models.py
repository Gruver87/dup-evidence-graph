"""Graph node/edge types."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class NodeKind(StrEnum):
    PRODUCT = "product"
    PACK = "pack"
    CLAIM = "claim"


class EdgeKind(StrEnum):
    HAS_PACK = "has_pack"
    SUPPORTS = "supports"
    REFUSES = "refuses"
    BOUNDARY = "boundary"


@dataclass(frozen=True)
class Node:
    id: str
    kind: NodeKind
    label: str
    attrs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    kind: EdgeKind
    attrs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d


@dataclass
class PackRecord:
    product_id: str
    path: str
    pack_kind: str | None
    hard_fails: int | None
    approx_48h_claim_ok: bool | None
    ops_ready: bool | None
    status: str | None
    run_id: str | None
    raw_keys: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
