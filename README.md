# Yuanli-OS Company Brain · Skill

> Build a Sentra-style "Company Brain" on top of any Obsidian-class wiki + Claude Code skills.

[中文版 →](README.zh-CN.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status: experimental](https://img.shields.io/badge/status-experimental-orange.svg)]()
[![v0.2](https://img.shields.io/badge/version-v0.2-blue.svg)]()

## What this is

A distilled, opinionated skill that turns "data-rich but memory-poor" personal/team wikis into a queryable context graph with:

**v0.1 core (2026-05-02)**:
- **Right-time surface** — auto-recall related concepts/tasks/drafts before any non-trivial output (vs reactive search)
- **Three-circle boundaries** — explicit `individual / shared / institutional` with promotion gates
- **Typed relationships** — `commits-to / owns / blocks / derives-from / supersedes / supports` (6 enum, no inverse, no catch-all)
- **Anti-hallucination 4-tuple extractor** — transcript → `commitments / disagreements / counterfactuals / decision_rationale` with mandatory `source_quote` + grep verification
- **Dual-axis maturity rubric** — separate **scaffold maturity (60-pt)** from **usage maturity (10-pt)** to catch optimistic self-reports
- **24h re-score protocol** — every "I'm done" claim must be re-scored within 24h with hard evidence

**v0.2 additions (2026-05-08)**:
- **5-layer architecture** — L0 Intake → L1 Memory (symbol/vector/active) → L2 Promotion → L3 Recall → L4 Action, with 4 explicit cross-layer seams + hosting decision matrix ([details](references/5-layer-architecture.md))
- **Borrow rubric · 3-tier discipline** — Doc-level / Executable-level / Verified-level scored independently to catch "documentation theater" ([details](references/borrow-rubric-3-tier.md))
- **Karpathy LLM Wiki pattern** — `_ai-entry.md` + `_hot.md` AI entry compression layer (~20-30× token reduction on 1000+ page wikis) ([details](references/karpathy-llm-wiki-pattern.md))
- **Schema system** — `schema_infer / validate / diff` three-piece toolkit borrowed from basicmachines-co/basic-memory ([scripts](scripts/schema_system.py))
- **Static refresh** — no-LLM `refresh_hot_static.py` as default hot-cache cron strategy (avoids LLM recursion risk)

Built on the Sentra "Company Brain" mental model (Ashwin Gopinath, 2026-04) × Yuanli-OS governance kernel × independent borrow audit (2026-05-08).

## 5-minute quickstart

```bash
git clone https://github.com/moonstachain/yuanli-os-company-brain-skill.git
cd yuanli-os-company-brain-skill

# Try on the bundled 12-note example vault
python3 scripts/relationship_graph.py --wiki-root examples/wiki --stats
python3 scripts/wiki_lint_l10.py        --wiki-root examples/wiki
python3 scripts/metacognition_signals.py --wiki-root examples/wiki

# v0.2: schema system on example vault
WIKI_ROOT=examples/wiki python3 scripts/schema_system.py infer concepts/

# v0.2: refresh hot cache (no LLM)
WIKI_ROOT=examples/wiki python3 scripts/refresh_hot_static.py

# Point at your own Obsidian vault
python3 scripts/relationship_graph.py --wiki-root ~/path/to/your/vault --mermaid > my-brain.md
WIKI_ROOT=~/path/to/your/vault python3 scripts/refresh_hot_static.py
```

No dependencies (pure Python stdlib). Tested on Python 3.10+.

## What you get

```
yuanli-os-company-brain-skill/
├── SKILL.md                       # Claude Code skill manifest (frontmatter + invocation)
├── README.md                      # this file
├── LICENSE                        # MIT
├── references/                    # The 5 core methodologies
│   ├── sentra-three-layers.md     # Sentra 3 layers × 4 elements
│   ├── three-circles-protocol.md  # individual / shared / institutional protocol
│   ├── typed-relationships-schema.md  # 6 relation types + G2 closure threshold
│   ├── dual-axis-rubric.md        # scaffold + usage maturity
│   └── 24h-rescore-protocol.md    # honest self-audit discipline
├── scripts/                       # 5 parameterized runtime tools
│   ├── brain_surface.py           # right-time recall
│   ├── relationship_graph.py      # typed edges (explicit + derived)
│   ├── wiki_lint_l10.py           # relationships schema validator
│   ├── metacognition_signals.py   # stale / orphan / freshness
│   └── extract_decision.py        # transcript → 4-tuple scaffolding
├── templates/                     # 3 frontmatter templates
│   ├── decision-page.md
│   ├── circle-frontmatter.md
│   └── relationship-frontmatter.md
└── examples/                      # Minimal vault + sample runs
    ├── wiki/                      # 12 notes (concepts / decisions / synthesis / transcript)
    └── sample-runs/               # Captured command outputs
```

## Field-tested

This skill was extracted on **2026-05-02** from a real personal-knowledge-system audit:

- 1170-note Chinese + English wiki
- 3 real meeting transcripts → 4-tuple extraction with **100% grep-verified quotes**
- 13 typed edges derived from 2 decisions (5 commits-to / 2 derives-from / 6 supersedes)
- Scaffold maturity: **A (54/60)** in ~30 hours
- Usage maturity: **D (4/10)** at extraction time — by design, real usage takes weeks

The honest assessment is captured in [`references/dual-axis-rubric.md`](references/dual-axis-rubric.md). The narrative version is in [yuanli-os-orange-book Part 8](https://github.com/moonstachain/yuanli-os-orange-book/tree/main/part8-yuanli-os-company-brain).

## When to adopt this skill

✅ **Adopt if**: you write notes regularly, run meetings, make decisions worth remembering, and your knowledge lives in a Markdown-friendly vault (Obsidian / Logseq / plain folder of `.md`).

❌ **Don't adopt if**: your knowledge lives in Notion DB / Confluence / Google Docs (export first), you don't run meetings, or you expect a "magic auto-organize my vault" tool — this skill assumes you, the human, decide what's worth promoting circle by circle.

## Honest scope

This is **opinionated software**. It embodies specific choices:

| Opinion | What it means |
|---|---|
| Relations are first-class memory | We don't believe RAG-over-files is enough; you need typed edges |
| Promotion is emergence, not command | The producer decides when a note crosses circles, not central management |
| Verification > impression | Every quote in a 4-tuple must grep-pass; every audit must show command output |
| Scaffold ≠ usage | A pretty-looking system with no real data is still D-grade |
| 24h re-score | "I'm done" is a hypothesis, not a fact, until verified the next day |

If any of these clash with your worldview, fork the methodology and adapt rather than adopting wholesale.

## Roadmap (v0.2 candidates)

- `conflict` and `weak-evidence` signals in `metacognition_signals.py`
- TUI dashboard wrapping the 3 hard-layer scripts
- `obsidian-cli` adapter (run inside Obsidian directly)
- Bridge to ticket systems for `commits-to` cross-system references

PRs welcome on opinionated additions (typed-edges UX improvements, more metacog signals). For non-opinionated ones (e.g. "make it work with Notion"), please open an issue first.

## Credits

- **Mental model**: Ashwin Gopinath (Sentra.app CEO), "Company Brain Part 1 / Part 2" X articles, 2026-04
- **Governance kernel**: liming (moonstachain), Yuanli-OS audit-rubric × six-judgments
- **First field-test**: 2026-05-01 to 2026-05-02

## License

MIT — see [LICENSE](LICENSE).
