---
name: yuanli-os-company-brain
description: Build a personal/team "Company Brain" on top of any Obsidian-class wiki + Claude Code skills. Distilled from the Yuanli-OS Company Brain v0.1 (Sentra × Yuanli-OS alignment). Use this skill when you want to (1) turn 1000+ scattered notes/transcripts/decisions into a queryable context graph, (2) get right-time memory surface before drafting articles/proposals/meetings, (3) extract commitments / disagreements / counterfactuals / decision rationale from any meeting transcript with anti-hallucination grep gate, (4) score the maturity of your own knowledge system on the dual-axis (scaffold + usage) rubric.
maturity: experimental
version: v0.3.0
license: MIT
sources:
  - "Sentra Company Brain Part 1 / Part 2 by Ashwin Gopinath"
  - "Yuanli-OS audit-rubric (6-axis × 30 checkpoints)"
  - "Field-tested 2026-05-01 to 2026-05-02 on a 1170-note real wiki"
related-skills:
  - "obsidian-cli (read/write your vault)"
  - "interaction-memory-extractor (transcript → 4-tuple)"
  - "skill-router / os-yuanli (governance gates)"
---

# Yuanli-OS Company Brain · v0.1

> **One-line positioning**: A skill that turns "data-rich but memory-poor" wikis into a Sentra-style company brain — explicit three-circle boundaries, typed relationships, right-time surface, role lens, metacognition signals.

## When to use this skill

Trigger this skill when **at least one** of these is true:

1. You have 500+ scattered notes / meeting transcripts / personal drafts and feel "I have data but no memory".
2. You're about to write an article / proposal / strategy doc and want **prior context surfaced automatically** (not via search).
3. You just had a meeting and want the transcript → 4-tuple (commitments / disagreements / counterfactuals / decision_rationale) extracted with **every quote grep-verified**.
4. You want to score the **maturity** of your own knowledge system honestly — not the "how full does it look" maturity, but the "is it actually being used" maturity.
5. You want a **24-hour re-score discipline** to catch your own optimistic post-build estimates.

Skip this skill if:

- Your wiki has fewer than 100 notes — you don't yet have the data density to benefit.
- You only need a single workflow step (extracting a transcript, querying a graph) — invoke that script directly, not the whole skill.
- You're looking for a search engine. This is a **proactive surface + structured extraction** skill, not search.

## Core mental model (3 layers × 4 elements × 3 circles)

The skill assumes the Sentra "Company Brain" mental model. If you haven't internalized it, read [references/sentra-three-layers.md](references/sentra-three-layers.md) first.

```
Factual memory + Human communication + Context graph & reasoning + Governed action
                              = Company Brain
```

Three-circle invariant (do not violate):

```
INSTITUTIONAL  (company / ecosystem record · provenance / permissions / freshness / ownership)
       ↑ promotion gate ↑
SHARED         (team docs / customer accounts / project context / open issues / decisions in progress)
       ↑ promotion gate ↑
INDIVIDUAL     (personal notes / drafts / meeting notes / private commitments)
```

The promotion gate is **decided by the producer**, not pushed by management — emergence, not command. See [references/three-circles-protocol.md](references/three-circles-protocol.md).

## What this skill gives you

### 6 phases (run in order on first install)

| Phase | Goal | Artifact |
|---|---|---|
| 0 · Concept | Read the spec, decide whether the Sentra mental model fits your context | `references/sentra-three-layers.md` |
| 1 · Right-time surface | Auto-surface related concepts/tasks/historical drafts before any non-trivial output | `scripts/brain_surface.py` (UserPromptSubmit hook style) |
| 2 · Three-circle protocol | Add `circle:` frontmatter (or auto-infer from path) + lint orphans | `scripts/wiki_lint_l9.py` (planned) |
| 3 · Interaction memory | Extract 4-tuples from any transcript with anti-hallucination grep gate | `templates/decision-page.md` + extractor prompt |
| 4 · Role lens | Filter same content for self / student / partner / agent roles | `--role` flag in `brain_surface.py` |
| 5 · Typed edges + Metacognition | Derive `commits-to / owns / blocks / derives-from / supersedes / supports` edges + freshness/orphan/stale signals | `scripts/relationship_graph.py` + `scripts/metacognition_signals.py` + `scripts/wiki_lint_l10.py` |

### References (the methodology)

- [`references/sentra-three-layers.md`](references/sentra-three-layers.md) — 3 layers + 4 elements + key oppositions
- [`references/three-circles-protocol.md`](references/three-circles-protocol.md) — explicit `circle:` field + path-rule inference + promotion gate
- [`references/typed-relationships-schema.md`](references/typed-relationships-schema.md) — 6 relation types + validation rules + adoption protocol + G2 closure threshold
- [`references/dual-axis-rubric.md`](references/dual-axis-rubric.md) — **scaffold maturity (60-pt) + usage maturity (10-pt)** evaluation, the methodology that catches optimistic self-reports
- [`references/24h-rescore-protocol.md`](references/24h-rescore-protocol.md) — any "I'm done" claim must be re-scored within 24h with hard evidence
- [`references/wiki-github-mirror-sync.md`](references/wiki-github-mirror-sync.md) — **automated private GitHub mirror** of the vault: 4 safety gates (private-only / desensitization / leak-guard / never-force) + launchd vs Actions + the mirror≠promotion boundary
- [`references/multiplatform-projection-protocol.md`](references/multiplatform-projection-protocol.md) — **SSOT + one-way projection** across 6+ platforms (local vault / private git / RAG notebook / mobile notes / collab tables / global wiki): role-per-platform card, scenario routing, 3 sync iron rules, field-tested pitfalls, N+1 checklist

### 5 scripts (the runtime · pure Python stdlib, no deps)

All scripts accept `--wiki-root <path>` so they work on any Obsidian vault.

- `scripts/brain_surface.py` — right-time recall: searches concepts / open commitments / historical drafts / personal CLAUDE memory by topic
- `scripts/relationship_graph.py` — typed edges scanner (explicit + derived from `decisions/` 4-tuples) → JSON / DOT / Mermaid / stats
- `scripts/wiki_lint_l10.py` — `relationships:` schema validator (E1-E6 hard errors + W1-W5 warnings)
- `scripts/metacognition_signals.py` — 5 signals: stale / orphan / freshness (v0.1 minimum); conflict / weak-evidence pending v0.2
- `scripts/extract_decision.py` — transcript → 4-tuple `.draft.md` scaffolding (LLM-driven; this script is the orchestrator template)

### 1 operations script (bash · the backup organ)

- `scripts/wiki_git_mirror_sync.sh` — scheduled, desensitized backup of the whole vault to a **private** GitHub mirror. Env-driven (`WIKI_DIR / REPO_SLUG / LEAK_GUARD / BRANCH`), enforces 4 safety gates (private-only assertion, leak guard, fetch+rebase never-force, single lock), headless-safe gh-credentialed https push. This is *backup*, not cross-circle promotion — see [`references/wiki-github-mirror-sync.md`](references/wiki-github-mirror-sync.md).

### 5 templates

- `templates/decision-page.md` — 4-tuple format with mandatory `source_quote` + `confidence(high/medium/low)` per item
- `templates/circle-frontmatter.md` — `circle: individual | shared | institutional | raw | tooling | unknown`
- `templates/relationship-frontmatter.md` — minimal `relationships:` YAML block
- `templates/wiki-mirror.gitignore` — desensitization whitelist for the private mirror (blocklist default + strict-whitelist mode)
- `templates/com.example.wiki-mirror-sync.plist.template` — launchd timer for the mirror sync (2×/day, offset minutes, RunAtLoad off)

### Sample run (examples/)

A 12-note minimal vault with 1 decision page, 1 transcript, 3 concepts, 1 synthesis, 1 entity. Run `python3 scripts/relationship_graph.py --wiki-root examples/wiki --stats` to see the typed edges derive in 0.2 seconds.

## How to invoke

**Quick start (5 minutes)**:

```bash
# 1. Clone and explore
git clone https://github.com/moonstachain/yuanli-os-company-brain-skill ~/yuanli-brain
cd ~/yuanli-brain

# 2. Run on the bundled example
python3 scripts/relationship_graph.py --wiki-root examples/wiki --stats
python3 scripts/wiki_lint_l10.py --wiki-root examples/wiki
python3 scripts/metacognition_signals.py --wiki-root examples/wiki

# 3. Point at your own vault
python3 scripts/relationship_graph.py --wiki-root ~/path/to/your/vault --mermaid > my-brain.md
```

**Full integration (60 minutes)**:

1. Read `references/sentra-three-layers.md` and decide if the model fits.
2. Add `circle:` to 5-10 of your most-used notes (not all 1000).
3. Run `scripts/brain_surface.py` once per day before drafting any major artifact.
4. Pick one recent meeting transcript, run the `extract_decision.py` template against it.
5. After 7 days, run `references/dual-axis-rubric.md` self-audit and check the **G2 closure threshold** in `references/typed-relationships-schema.md` §8.

## Honest constraints (read before adopting)

This skill embodies a **specific opinion** about how memory systems should work:

- ✅ It works when: you write notes regularly, you run meetings, you make decisions worth remembering, you have a Markdown-friendly vault.
- ❌ It does **not** work when: your knowledge lives in Notion databases / Confluence / Google Docs (you'd need to export to Markdown first); you don't actually run meetings or make decisions; you expect "auto-organize my whole vault" — this skill assumes you, the human, decide what's worth promoting circle by circle.

The author's field-test (2026-05-02) showed:
- Scaffold maturity reached **A grade (54/60)** in ~30 hours of focused build.
- Usage maturity stayed at **D grade (4/10)** because real data needs weeks/months to accumulate.
- This is normal. The skill is opinionated about distinguishing these two.

## Field-tested 2026-05-02

- 1170-note vault (Chinese + English mixed)
- 3 real-meeting transcripts → 4-tuple extraction with **100% grep-verified quotes**
- 13 typed edges derived from 2 decisions (`commits-to: 5 / derives-from: 2 / supersedes: 6`)
- `wiki_lint_l10` 0 errors / 0 warnings on 1170 pages
- `metacognition_signals` correctly reports 0 orphans (all commitments have owners) + freshness binning

See `examples/sample-runs/` for actual command outputs.

## Roadmap (v0.2 candidates)

- `conflict` signal (two relationships in opposition) and `weak-evidence` signal (relationships with single source) for `metacognition_signals.py`
- TUI dashboard wrapping the 3 hard-layer scripts
- `obsidian-cli` adapter so the scripts run inside Obsidian directly
- Bridge to ticket systems (Linear / Jira / Feishu Bitable) for `commits-to` cross-system references

Pull requests welcome on opinionated additions; please open an issue first for non-opinionated ones (e.g. "make it work with Notion") so we can discuss the alignment.

## License

MIT. Do whatever you want; if you build something on top, a link back is appreciated.

## Credits

- **Mental model**: Ashwin Gopinath (Sentra.app CEO), "Company Brain Part 1 / Part 2" X articles, 2026-04
- **Yuanli-OS governance kernel**: liming (moonstachain), audit-rubric / six-judgments / theme-strategy-execution gates
- **First field test**: 2026-05-01 to 2026-05-02 on the LLM-Wiki vault, see [yuanli-os-orange-book Part 8](https://github.com/moonstachain/yuanli-os-orange-book/tree/main/part8-yuanli-os-company-brain) for the narrative version
