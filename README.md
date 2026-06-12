# Yuanli-OS Company Brain · Skill

> Build a Sentra-style "Company Brain" on top of any Obsidian-class wiki + Claude Code skills.

[中文版 →](README.zh-CN.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status: experimental](https://img.shields.io/badge/status-experimental-orange.svg)]()
[![v0.5](https://img.shields.io/badge/version-v0.5-blue.svg)]()

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

**v0.3 additions (2026-06-02)**:
- **Private GitHub mirror sync** — scheduled, desensitized whole-vault backup with 4 safety gates: private-only / leak-guard / never-force / single-lock ([details](references/wiki-github-mirror-sync.md))
- **Multiplatform projection protocol** — SSOT + one-way projection across 6+ platforms, role-per-platform card + 3 sync iron rules ([details](references/multiplatform-projection-protocol.md))

**v0.4 additions (2026-06-12)**:
- **Tiered knowledge spine** — 3-tier content routing (index spine / capacity depth / hot pulse) with a 4-axis rubric (size / shelf-life / modality / recall frequency), material-format priority and cost discipline ([details](references/tiered-knowledge-spine.md))
- **Team share slice** — the *distribution* organ (vs the mirror's *backup* organ): tag-scoped white-list export → content-signature leak-guard → read-only private GitHub slice teammates just `git pull` ([details](references/team-share-slice.md) · [script](scripts/share_slice_export.py))
- **GitHub-connector bridge** — let sandboxed web Claude read the synced vault through the built-in GitHub connector ([details](references/wiki-github-mirror-sync.md))
- **Hot-layer intake adapter** — semantic-recall results → `sources/` stubs with `circle: raw` + `truth_source` back-pointer, including the large-integer note-id precision guardrail ([script](scripts/intake_getnote.py))

**v0.5 additions (2026-06-12)** — the production flywheel, incorporated from the author's live deployment:
- **Right-time surface as a hook** — `brain_surface_hook.py` (UserPromptSubmit) auto-surfaces decision cards + concepts on every non-trivial prompt; `brain_writeback_hook.py` (Stop) auto-proposes edges for new decision cards. Both env-configured, fail-silent
- **Write-back fan-in + human gate** — `brain_writeback.py` proposes edges, `promote_card.py` promotes reviewed drafts through quality gates (AI proposes, human promotes — three-circles discipline, mechanized)
- **Trust ladder everywhere** — `claude-auto < claude-unilateral < human-confirmed`; high-value edges (`supersedes`/`blocks`) stay `candidate` until confirmed, across surface / graph / signals
- **Semantic recall (optional)** — `embed_sources.py` local vector index + CJK-bigram lexical fallback; `cluster_decisions.py` finds hot topics no concept has absorbed yet; `retype_references.py` proposes typed upgrades for flat reference edges
- **weak-evidence signal shipped** — single-source decision cards get flagged (was a v0.2 roadmap item)

Built on the Sentra "Company Brain" mental model (Ashwin Gopinath, 2026-04) × Yuanli-OS governance kernel × independent borrow audit (2026-05-08) × a week of real team field discussions (2026-06).

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

Pure Python stdlib, with one exception: `schema_system.py` needs PyYAML (`pip install -r requirements.txt`). Everything else runs dependency-free. Tested on Python 3.10+.

## What you get

```
yuanli-os-company-brain-skill/
├── SKILL.md                       # Claude Code skill manifest (frontmatter + invocation)
├── README.md                      # this file
├── LICENSE                        # MIT
├── requirements.txt               # PyYAML (schema_system.py only)
├── references/                    # The 12 core methodologies
│   ├── sentra-three-layers.md     # Sentra 3 layers × 4 elements
│   ├── three-circles-protocol.md  # individual / shared / institutional protocol
│   ├── typed-relationships-schema.md  # 6 relation types + G2 closure threshold
│   ├── dual-axis-rubric.md        # scaffold + usage maturity
│   ├── 24h-rescore-protocol.md    # honest self-audit discipline
│   ├── 5-layer-architecture.md    # hosting-aware locality model (v0.2)
│   ├── borrow-rubric-3-tier.md    # doc / executable / verified scoring (v0.2)
│   ├── karpathy-llm-wiki-pattern.md   # AI entry compression (v0.2)
│   ├── wiki-github-mirror-sync.md     # private mirror + connector bridge (v0.3/v0.4)
│   ├── multiplatform-projection-protocol.md  # SSOT one-way projection (v0.3)
│   ├── tiered-knowledge-spine.md      # 3-tier content routing (v0.4)
│   └── team-share-slice.md            # tag-scoped distribution organ (v0.4)
├── scripts/                       # 16 runtime tools + 1 ops script
│   ├── brain_surface.py           # right-time recall (lexical CJK-bigram + optional semantic)
│   ├── relationship_graph.py      # typed edges (explicit + derived + OSA-card JSON)
│   ├── wiki_lint_l10.py           # relationships schema validator
│   ├── metacognition_signals.py   # stale / orphan / freshness / weak-evidence
│   ├── extract_decision.py        # transcript → 4-tuple scaffolding
│   ├── schema_system.py           # infer / validate / diff (v0.2 · PyYAML)
│   ├── refresh_hot_static.py      # no-LLM _hot.md refresher (v0.2)
│   ├── share_slice_export.py      # team share slice exporter (v0.4)
│   ├── intake_getnote.py          # hot-layer intake stubs (v0.4)
│   ├── brain_surface_hook.py      # UserPromptSubmit hook (v0.5)
│   ├── brain_writeback_hook.py    # Stop hook (v0.5)
│   ├── brain_writeback.py         # edge-proposal fan-in engine (v0.5)
│   ├── promote_card.py            # human-gate promotion (v0.5)
│   ├── embed_sources.py           # vector indexer (v0.5 · numpy)
│   ├── cluster_decisions.py       # unabsorbed-topic clustering (v0.5)
│   ├── retype_references.py       # flat-edge retyping proposals (v0.5)
│   └── wiki_git_mirror_sync.sh    # private mirror backup (v0.3)
├── templates/                     # 7 templates
│   ├── decision-page.md
│   ├── circle-frontmatter.md
│   ├── relationship-frontmatter.md
│   ├── _ai-entry.md.template      # Karpathy master map (v0.2)
│   ├── _hot.md.template           # activity cache (v0.2)
│   ├── wiki-mirror.gitignore      # desensitization whitelist (v0.3)
│   └── com.example.wiki-mirror-sync.plist.template  # launchd timer (v0.3)
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

## Roadmap (v0.5 candidates)

- **Cold-start intake (Phase -1)**: raw dumps (PDF / Word / chat exports) → markdown → two-stage auto-organization — deliberately deferred from v0.4
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
