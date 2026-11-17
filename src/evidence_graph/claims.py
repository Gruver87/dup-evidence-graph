"""Fail-closed claim evaluation against packs for one product."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from evidence_graph.models import PackRecord

KNOWN_CLAIMS = (
    "unit",
    "verify_quick",
    "verify_full",
    "ops_ready",
    "short_soak",
    "soak_48h",
    "live_preflight",
    "protocol_status",
    "entries_unlocked",
    "skills_ci",
    "mesh_probe",
    "industrial_gate",
    "lab",
)


@dataclass(frozen=True)
class ClaimVerdict:
    product_id: str
    claim: str
    allowed: bool
    reason: str
    supporting_packs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "product_id": self.product_id,
            "claim": self.claim,
            "allowed": self.allowed,
            "reason": self.reason,
            "supporting_packs": list(self.supporting_packs),
        }


def _packs_for(product_id: str, packs: list[PackRecord]) -> list[PackRecord]:
    return [p for p in packs if p.product_id == product_id]


def evaluate_claim(product_id: str, claim: str, packs: list[PackRecord]) -> ClaimVerdict:
    claim = claim.strip().lower()
    mine = _packs_for(product_id, packs)

    if claim == "soak_48h":
        good = [
            p
            for p in mine
            if p.approx_48h_claim_ok is True and p.hard_fails == 0
        ]
        if good:
            return ClaimVerdict(
                product_id,
                claim,
                True,
                "approx_48h_claim_ok=true and hard_fails=0",
                tuple(p.path for p in good),
            )
        related = [
            p.path
            for p in mine
            if p.approx_48h_claim_ok is not None or p.hard_fails is not None
        ]
        return ClaimVerdict(
            product_id,
            claim,
            False,
            "no pack with approx_48h_claim_ok=true AND hard_fails=0",
            tuple(related[:5]),
        )

    if claim == "short_soak":
        # hard_fails=0 is enough for short soak; never upgrade to 48h here
        good = [p for p in mine if p.hard_fails == 0]
        if good:
            return ClaimVerdict(
                product_id,
                claim,
                True,
                "hard_fails=0 present (not a 48h claim)",
                tuple(p.path for p in good[:5]),
            )
        return ClaimVerdict(product_id, claim, False, "no pack with hard_fails=0")

    if claim == "ops_ready":
        good = [p for p in mine if p.ops_ready is True]
        if good:
            return ClaimVerdict(
                product_id,
                claim,
                True,
                "ops_ready=true",
                tuple(p.path for p in good),
            )
        return ClaimVerdict(product_id, claim, False, "no READY_OPS with ops_ready=true")

    if claim in {"verify_full", "verify_quick"}:
        needle = "verify-full" if claim == "verify_full" else "verify-quick"
        good = [
            p
            for p in mine
            if (p.run_id and needle in p.run_id.lower())
            or (p.path and needle in p.path.lower())
        ]
        if good:
            return ClaimVerdict(
                product_id,
                claim,
                True,
                f"run pack id contains {needle}",
                tuple(p.path for p in good[:5]),
            )
        return ClaimVerdict(
            product_id,
            claim,
            False,
            f"no run pack matching {needle}",
        )

    if claim == "entries_unlocked":
        status = [p for p in mine if p.pack_kind == "protocol_status"]
        if not status:
            return ClaimVerdict(product_id, claim, False, "PROTOCOL_STATUS.md missing")
        if any(p.status == "stopped" for p in status):
            return ClaimVerdict(
                product_id,
                claim,
                False,
                "protocol status indicates v1 stopped / entries off — refuse unlock",
                tuple(p.path for p in status),
            )
        return ClaimVerdict(
            product_id,
            claim,
            False,
            "entries unlock not evidenced (fail-closed)",
            tuple(p.path for p in status),
        )

    if claim == "protocol_status":
        status = [p for p in mine if p.pack_kind == "protocol_status"]
        if status:
            return ClaimVerdict(
                product_id,
                claim,
                True,
                f"protocol status present ({status[0].status})",
                tuple(p.path for p in status),
            )
        return ClaimVerdict(product_id, claim, False, "PROTOCOL_STATUS.md missing")

    if claim in {"unit", "skills_ci", "lab", "mesh_probe", "industrial_gate", "live_preflight"}:
        # Presence of any pack/doc for product is not enough to invent PASS —
        # report inventory only as refuse unless explicit status=ok run exists.
        ok_runs = [p for p in mine if (p.status or "").lower() in {"ok", "pass"}]
        if claim == "skills_ci" and any(
            p.path.endswith("plugin.json") for p in mine
        ):
            return ClaimVerdict(
                product_id,
                claim,
                True,
                "skills pack plugin.json present (CI claimed separately)",
                tuple(p.path for p in mine if p.path.endswith("plugin.json")),
            )
        if ok_runs and claim in {"unit", "lab", "mesh_probe", "industrial_gate", "live_preflight"}:
            return ClaimVerdict(
                product_id,
                claim,
                True,
                "status=ok run pack present — still not soak/mainnet",
                tuple(p.path for p in ok_runs[:5]),
            )
        return ClaimVerdict(
            product_id,
            claim,
            False,
            f"no fail-closed evidence for claim={claim}",
            tuple(p.path for p in mine[:3]),
        )

    return ClaimVerdict(product_id, claim, False, f"unknown claim={claim}")
