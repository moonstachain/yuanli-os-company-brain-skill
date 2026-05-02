---
title: Company Brain overview (synthesis)
type: synthesis
domain: company-brain
created: 2026-04-30
date: 2026-04-30
circle: institutional
audience: both
sources:
  - "[[right-time-surface]]"
  - "[[three-circles-protocol]]"
  - "[[typed-relationships-schema]]"
relationships:
  - type: derives-from
    target: "[[right-time-surface]]"
    evidence:
      - "[[right-time-surface]]"
    status: active
  - type: derives-from
    target: "[[three-circles-protocol]]"
    evidence:
      - "[[three-circles-protocol]]"
    status: active
---

# Company Brain overview (synthesis)

> A synthesis page demonstrating how four pillars combine into one Company Brain. This is an **example** for the skill's bundled vault — adapt for your own ecosystem.

## The four-element formula

```
Factual memory + Human communication + Context graph + Governed action
                              = Company Brain
```

Miss any one and you only have:

- Missing factual memory → search and archives
- Missing communication → transcript + summarization
- Missing context graph → inference and guessing
- Missing governed action → fragile automation

A real Company Brain ties all four together.

## Three layers wired into your existing infra

| Sentra layer | This vault's home |
|---|---|
| L1 Factual memory | `concepts/`, `entities/`, `sources/` |
| L2 Context graph | `relationships:` frontmatter + `decisions/` 4-tuples (run `relationship_graph.py`) |
| L2 Metacognition | `metacognition_signals.py` (stale / orphan / freshness) |
| L3 Action coordination | (out of scope for v0.1; bridge to ticketing later) |

## How a new Company Brain matures (5 phases)

| Phase | Goal | Artifact |
|---|---|---|
| 0 | Read the spec, decide if it fits | `references/sentra-three-layers.md` |
| 1 | Right-time surface | `scripts/brain_surface.py` |
| 2 | Three-circle promotion gate | `circle:` frontmatter on 5-10 high-traffic notes |
| 3 | Interaction memory | First transcript → `extract_decision.py` |
| 4 | Role lens | `--role` flag in brain_surface |
| 5 | Typed edges + metacognition | `relationship_graph.py` + `metacognition_signals.py` + `wiki_lint_l10.py` |

Each phase is roughly 1 day if you have an existing 200+ note vault. Real **usage** maturity (not scaffold) takes weeks of natural use.

## Field test (2026-05-02)

A 30-hour build on a 1170-note vault scored:

- Scaffold maturity: **A (54/60)**
- Usage maturity: **D (4/10)**

This is the expected post-build state. The dual-axis rubric (`references/dual-axis-rubric.md`) prevents reporting just "54/60 = ready". See `references/24h-rescore-protocol.md` for the discipline that catches optimistic estimates.

## Roadmap (v0.2 candidates)

- `conflict` and `weak-evidence` signals in metacognition
- TUI dashboard
- Obsidian-cli adapter
- Bridge to ticket systems (Linear / Jira / Bitable)

PRs welcome — see the README on the source repo.
