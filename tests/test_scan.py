from __future__ import annotations

from pathlib import Path

from evidence_graph.scan import scan_products

FIXTURES = Path(__file__).parent / "fixtures"


def test_scan_fixture_packs() -> None:
    cfg, packs = scan_products(config_path=FIXTURES / "products.json")
    assert cfg["products"][0]["_root_exists"] is True
    kinds = {p.pack_kind for p in packs}
    assert "ops_ready" in kinds
    assert "soak_lab" in kinds or "run_manifest" in kinds
    assert any(p.product_id == "bot" for p in packs)
