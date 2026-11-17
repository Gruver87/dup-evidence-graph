"""CLI: scan / query / export."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from evidence_graph import __version__
from evidence_graph.export import render_markdown, write_dot, write_json, write_markdown
from evidence_graph.graph import EvidenceGraph
from evidence_graph.scan import scan_products


def _desktop_default() -> Path:
    return Path.home() / "Desktop"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dup-evidence-graph",
        description="Queryable evidence graph for DUP Labs packs (fail-closed).",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="products.json path (default: packaged configs/products.json)",
    )
    p.add_argument(
        "--desktop",
        type=Path,
        default=None,
        help="Desktop root for ../product paths (default: ~/Desktop)",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    scan = sub.add_parser("scan", help="Scan products and print summary")
    scan.add_argument("--out", type=Path, default=None, help="Write graph JSON")

    q = sub.add_parser("query", help="Query claim allowance")
    q.add_argument("product_id")
    q.add_argument("claim")

    packs = sub.add_parser("packs", help="List packs for a product")
    packs.add_argument("product_id")

    export = sub.add_parser("export", help="Export graph artifacts")
    export.add_argument(
        "--dir",
        type=Path,
        default=Path("out"),
        help="Output directory (default: ./out)",
    )
    export.add_argument(
        "--format",
        choices=("json", "md", "dot", "all"),
        default="all",
    )

    board = sub.add_parser("board", help="Print honesty board (markdown to stdout)")
    _ = board

    demo = sub.add_parser(
        "demo",
        help="Run against packaged fixtures (no Desktop / no live keys)",
    )
    demo.add_argument(
        "--out",
        type=Path,
        default=Path("out/demo"),
        help="Export dir (default: out/demo)",
    )

    return p


def _fixtures_config() -> Path:
    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "products.json"


def _load_graph(args: argparse.Namespace) -> EvidenceGraph:
    desktop = args.desktop or _desktop_default()
    cfg, packs = scan_products(config_path=args.config, desktop=desktop)
    return EvidenceGraph(config=cfg, packs=packs)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.cmd == "demo":
        cfg_path = _fixtures_config()
        if not cfg_path.is_file():
            print(f"FAIL: demo fixtures missing: {cfg_path}", file=sys.stderr)
            return 2
        cfg, packs = scan_products(config_path=cfg_path)
        graph = EvidenceGraph(config=cfg, packs=packs)
        print(
            f"evidence_graph DEMO packs={len(graph.packs)} "
            f"nodes={len(graph.nodes)} (fixtures — not live Desktop)"
        )
        for product in graph.config.get("products") or []:
            pid = product["id"]
            n = len(graph.packs_for(pid))
            print(f" - {pid}: packs={n} root_ok={product.get('_root_exists')}")
        v_ops = graph.can_claim("radar", "ops_ready")
        v_48 = graph.can_claim("radar", "soak_48h")
        print(f"query radar ops_ready → allowed={v_ops.allowed}")
        print(f"query radar soak_48h → allowed={v_48.allowed} (expect False)")
        write_json(graph, args.out / "graph.json")
        write_markdown(graph, args.out / "board.md")
        print(f"exported → {args.out.resolve()}")
        # Fail-closed demo succeeds when ops_ready true and soak refused
        return 0 if v_ops.allowed and not v_48.allowed else 1

    graph = _load_graph(args)

    if args.cmd == "scan":
        print(
            f"evidence_graph scan packs={len(graph.packs)} "
            f"nodes={len(graph.nodes)} edges={len(graph.edges)}"
        )
        for product in graph.config.get("products") or []:
            pid = product["id"]
            n = len(graph.packs_for(pid))
            flag = "OK" if product.get("_root_exists") else "MISSING"
            print(f" - {pid}: root={flag} packs={n}")
        if args.out:
            write_json(graph, args.out)
            print(f"wrote {args.out}")
        return 0

    if args.cmd == "query":
        v = graph.can_claim(args.product_id, args.claim)
        print(json.dumps(v.to_dict(), indent=2, ensure_ascii=False))
        return 0 if v.allowed else 1

    if args.cmd == "packs":
        rows = graph.packs_for(args.product_id)
        print(json.dumps([r.to_dict() for r in rows], indent=2, ensure_ascii=False))
        return 0 if rows else 1

    if args.cmd == "export":
        out = args.dir
        out.mkdir(parents=True, exist_ok=True)
        fmt = args.format
        if fmt in ("json", "all"):
            write_json(graph, out / "graph.json")
        if fmt in ("md", "all"):
            write_markdown(graph, out / "board.md")
        if fmt in ("dot", "all"):
            write_dot(graph, out / "graph.dot")
        print(f"exported → {out.resolve()}")
        return 0

    if args.cmd == "board":
        print(render_markdown(graph))
        return 0

    print("unknown command", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
