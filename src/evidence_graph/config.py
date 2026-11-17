"""Load products registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PACKAGE_ROOT / "configs" / "products.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or DEFAULT_CONFIG
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "products" not in data:
        raise ValueError(f"invalid products config: {cfg_path}")
    return data


def resolve_product_root(product: dict[str, Any], config_dir: Path, override: Path | None) -> Path:
    if override is not None:
        return override.resolve()
    raw = product.get("default_root") or "."
    p = Path(raw)
    if not p.is_absolute():
        p = (config_dir / p).resolve()
    return p
