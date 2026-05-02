---
title: Typed relationships schema (mini)
type: concept
domain: company-brain
created: 2026-04-25
date: 2026-04-25
circle: institutional
audience: both
related:
  - "[[right-time-surface]]"
  - "[[three-circles-protocol]]"
relationships:
  - type: supports
    target: "[[example-synthesis-company-brain-overview]]"
    evidence:
      - "[[example-synthesis-company-brain-overview]]"
    status: active
---

# Typed relationships schema (mini)

> The minimal version. The full normative spec is in `references/typed-relationships-schema.md`.

## The 6 enum

| Type | Direction | Use when |
|---|---|---|
| `commits-to` | current → commitment | An obligation is created |
| `owns` | current → artifact | Accountable ownership |
| `blocks` | current → blocked | Progress prevented |
| `derives-from` | current → upstream | Current was extracted from target |
| `supersedes` | current → older | Replacement |
| `supports` | current → claim | Strengthens without owning |

No inverse relation types. No catch-all `related-to`. Six is enough.

## Why typed edges

Plain wikilinks are platonic — they say "these two notes are connected" without saying *how*. A Company Brain needs the *how*, because:

- "Decision X commits-to Task Y" implies Y has a deadline owner from X
- "Note A supersedes Note B" implies B should be marked stale
- "Project P blocks Project Q" implies Q's roadmap depends on P

These are different relationships and must not collapse into a single line.

## Adoption protocol (don't migrate everything)

1. Start with new or actively edited institutional notes only.
2. Add 1-3 high-signal relationships per page; avoid spam.
3. Prefer `evidence` over confidence theater: no evidence, no typed edge.
4. When unsure, use a plain wikilink first.
5. Revisit the six-type enum only after repeated examples prove a missing class.
