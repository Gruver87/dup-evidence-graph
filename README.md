# DUP Evidence Graph

[![ci](https://github.com/Gruver87/dup-evidence-graph/actions/workflows/ci.yml/badge.svg)](https://github.com/Gruver87/dup-evidence-graph/actions/workflows/ci.yml)

**Org:** [DUP Labs](https://github.com/Gruver87) · **Author:** Uladzimir Dabranski  
**Version:** `0.1.0` · Fail-closed queryable map of local evidence packs

Answers: *can this product claim X?* using packs on disk — never invents PASS.

| Product id | Default Desktop folder | Repo |
|------------|------------------------|------|
| `radar` | `dup-market-radar` | [`dup-market-radar`](https://github.com/Gruver87/dup-market-radar) |
| `bot` | `absolute-trading-bot-final` | [`absolute-trading-bot-final`](https://github.com/Gruver87/absolute-trading-bot-final) |
| `skills` | `dup-agent-skills` | [`dup-agent-skills`](https://github.com/Gruver87/dup-agent-skills) |
| `l1_pin` | `Absolute_Blockchain_Ultimate` | [`dup-protocol`](https://github.com/Gruver87/dup-protocol) |
| `l1_exp` | `Absolute_Blockchain_Experimental` | [`dup-protocol-experimental`](https://github.com/Gruver87/dup-protocol-experimental) |

## Install

```powershell
cd C:\Users\vovun\Desktop\dup-evidence-graph
python -m pip install -e ".[dev]"
.\scripts\test_all.ps1
.\scripts\scan_desktop.ps1
```

## Examples

```powershell
python -m evidence_graph query radar soak_48h
python -m evidence_graph query radar ops_ready
python -m evidence_graph query bot entries_unlocked
python -m evidence_graph board
python -m evidence_graph export --dir out
```

Exit code `1` on `query` when claim is **not** allowed (fail-closed).

## Related

- [`dup-skills-eval`](https://github.com/Gruver87/dup-skills-eval)
- [`dup-radar-news-mcp`](https://github.com/Gruver87/dup-radar-news-mcp)
- skill `l1-boundary` / `evidence-honesty`

## License

MIT — [`LICENSE`](LICENSE).
