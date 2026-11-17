"""Scan product trees into PackRecords."""

from __future__ import annotations

import glob
from pathlib import Path
from typing import Any

from evidence_graph.config import DEFAULT_CONFIG, load_config, resolve_product_root
from evidence_graph.models import PackRecord
from evidence_graph.packs import discover_run_packs, load_pack_file


def _expand_globs(root: Path, patterns: list[str]) -> list[Path]:
    out: list[Path] = []
    for pattern in patterns:
        matched = glob.glob(str(root / pattern), recursive=False)
        for m in matched:
            p = Path(m)
            if p.is_file():
                out.append(p)
    seen: set[Path] = set()
    uniq: list[Path] = []
    for p in sorted(out):
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        uniq.append(rp)
    return uniq


def scan_products(
    *,
    config_path: Path | None = None,
    root_overrides: dict[str, Path] | None = None,
    desktop: Path | None = None,
) -> tuple[dict[str, Any], list[PackRecord]]:
    """Return (config, packs).

    If ``desktop`` is set, resolve ``default_root`` values that start with ``../``
    against that Desktop folder instead of configs/.
    """
    cfg_path = config_path or DEFAULT_CONFIG
    cfg = load_config(cfg_path)
    config_dir = cfg_path.parent

    if desktop is not None:
        desktop = desktop.resolve()
        for product in cfg["products"]:
            raw = product.get("default_root") or ""
            if isinstance(raw, str) and raw.startswith("../"):
                product["default_root"] = str(desktop / raw[3:])

    overrides = root_overrides or {}
    packs: list[PackRecord] = []
    for product in cfg["products"]:
        pid = product["id"]
        root = resolve_product_root(product, config_dir, overrides.get(pid))
        product["_resolved_root"] = str(root)
        product["_root_exists"] = root.is_dir()
        if not root.is_dir():
            continue
        scan = product.get("scan") or {}
        for rel in scan.get("run_dirs") or []:
            packs.extend(discover_run_packs(pid, root / rel))
        for path in _expand_globs(root, list(scan.get("json_globs") or [])):
            rec = load_pack_file(pid, path)
            if rec:
                packs.append(rec)
    return cfg, packs
