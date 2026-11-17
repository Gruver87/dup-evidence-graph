from __future__ import annotations

from pathlib import Path

from evidence_graph.claims import evaluate_claim
from evidence_graph.graph import EvidenceGraph
from evidence_graph.scan import scan_products

FIXTURES = Path(__file__).parent / "fixtures"


def _graph() -> EvidenceGraph:
    cfg, packs = scan_products(config_path=FIXTURES / "products.json")
    # fixture default_root is relative to configs dir (= fixtures/)
    return EvidenceGraph(config=cfg, packs=packs)


def test_radar_ops_ready_and_not_48h() -> None:
    g = _graph()
    assert g.can_claim("radar", "ops_ready").allowed is True
    assert g.can_claim("radar", "short_soak").allowed is True
    v48 = g.can_claim("radar", "soak_48h")
    assert v48.allowed is False
    assert "approx_48h_claim_ok" in v48.reason


def test_verify_full_from_run_id() -> None:
    g = _graph()
    assert g.can_claim("radar", "verify_full").allowed is True


def test_bot_entries_refused() -> None:
    g = _graph()
    assert g.can_claim("bot", "protocol_status").allowed is True
    v = g.can_claim("bot", "entries_unlocked")
    assert v.allowed is False
    assert "stopped" in v.reason.lower() or "refuse" in v.reason.lower()


def test_evaluate_claim_direct() -> None:
    g = _graph()
    v = evaluate_claim("radar", "soak_48h", g.packs)
    assert v.allowed is False
