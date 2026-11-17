"""Parse evidence JSON / run manifests into PackRecord."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from evidence_graph.models import PackRecord

_JSON_NAME_HINT = re.compile(
    r"(?i)(LATEST_SOAK|LATEST|READY_OPS|soak_lab|smoke_live|manifest)"
)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _as_int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _as_bool(v: Any) -> bool | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        low = v.strip().lower()
        if low in {"true", "1", "yes"}:
            return True
        if low in {"false", "0", "no"}:
            return False
    return None


def parse_pack_json(product_id: str, path: Path, data: dict[str, Any] | None = None) -> PackRecord:
    body = data if data is not None else _read_json(path) or {}
    pack_kind = body.get("pack_kind")
    if pack_kind is None and path.name.upper().startswith("LATEST_SOAK"):
        pack_kind = "soak_lab"
    elif pack_kind is None and path.name.upper().startswith("READY_OPS"):
        pack_kind = "ops_ready"
    elif pack_kind is None and "smoke" in path.name.lower():
        pack_kind = "smoke_live"
    elif pack_kind is None and path.name == "manifest.json":
        pack_kind = "run_manifest"

    hard_fails = _as_int(body.get("hard_fails"))
    if hard_fails is None:
        hard_fails = _as_int(body.get("short_soak_hard_fails"))

    # Nested files[] on run manifests — prefer soak file if present
    approx = _as_bool(body.get("approx_48h_claim_ok"))
    if approx is None and isinstance(body.get("files"), list):
        for f in body["files"]:
            if not isinstance(f, dict):
                continue
            if f.get("approx_48h_claim_ok") is not None:
                approx = _as_bool(f.get("approx_48h_claim_ok"))
            if hard_fails is None and f.get("hard_fails") is not None:
                hard_fails = _as_int(f.get("hard_fails"))

    return PackRecord(
        product_id=product_id,
        path=str(path.resolve()),
        pack_kind=str(pack_kind) if pack_kind else None,
        hard_fails=hard_fails,
        approx_48h_claim_ok=approx,
        ops_ready=_as_bool(body.get("ops_ready")),
        status=str(body.get("status")) if body.get("status") is not None else None,
        run_id=str(body.get("run_id")) if body.get("run_id") is not None else path.parent.name,
        raw_keys=tuple(sorted(body.keys())),
    )


def parse_protocol_status_md(product_id: str, path: Path) -> PackRecord:
    text = path.read_text(encoding="utf-8", errors="replace")
    stopped = bool(
        re.search(r"(?i)\b(stopped|no-edge|SPOT_ENTRIES\s*(off|false|0))\b", text)
    )
    return PackRecord(
        product_id=product_id,
        path=str(path.resolve()),
        pack_kind="protocol_status",
        hard_fails=None,
        approx_48h_claim_ok=False,
        ops_ready=None,
        status="stopped" if stopped else "unknown",
        run_id=path.name,
        raw_keys=("markdown",),
    )


def load_pack_file(product_id: str, path: Path) -> PackRecord | None:
    if not path.is_file():
        return None
    if path.suffix.lower() == ".md" and path.name.upper().startswith("PROTOCOL"):
        return parse_protocol_status_md(product_id, path)
    if path.suffix.lower() == ".json":
        return parse_pack_json(product_id, path)
    if path.name.upper() == "EVIDENCE_MATRIX.MD":
        return PackRecord(
            product_id=product_id,
            path=str(path.resolve()),
            pack_kind="evidence_matrix",
            hard_fails=None,
            approx_48h_claim_ok=None,
            ops_ready=None,
            status="doc",
            run_id=path.name,
            raw_keys=("markdown",),
        )
    return None


def discover_run_packs(product_id: str, runs_root: Path) -> list[PackRecord]:
    if not runs_root.is_dir():
        return []
    out: list[PackRecord] = []
    for run_dir in sorted(p for p in runs_root.iterdir() if p.is_dir()):
        manifest = run_dir / "manifest.json"
        if manifest.is_file():
            rec = load_pack_file(product_id, manifest)
            if rec:
                out.append(rec)
            continue
        # Fallback: any LATEST*.json inside run
        for child in sorted(run_dir.glob("*.json")):
            if _JSON_NAME_HINT.search(child.name):
                rec = load_pack_file(product_id, child)
                if rec:
                    out.append(rec)
                    break
    return out
