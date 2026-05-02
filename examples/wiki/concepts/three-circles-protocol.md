---
title: Three-circles protocol
type: concept
domain: company-brain
created: 2026-04-22
date: 2026-04-22
circle: institutional
audience: both
related:
  - "[[right-time-surface]]"
  - "[[typed-relationships-schema]]"
relationships:
  - type: supports
    target: "[[example-synthesis-company-brain-overview]]"
    evidence:
      - "[[example-synthesis-company-brain-overview]]"
    status: active
---

# Three-circles protocol

> `personal ≠ shared ≠ company record` — and the boundary between them must be **explicit**, not assumed.

## The three circles

```
INSTITUTIONAL  ← company / ecosystem record
       ↑
SHARED         ← team / project / customer common ground
       ↑
INDIVIDUAL     ← personal notes, drafts, private commitments
```

Iron rule: a piece of content lives in exactly one circle at a time. The circle field declares it.

## Six valid `circle:` values

- `individual` — private to the producer
- `shared` — visible to a defined group (team / project / customer relationship)
- `institutional` — visible to the whole company / ecosystem record
- `raw` — unprocessed source (transcript / get-biji)
- `tooling` — skills / scripts / configs
- `unknown` — pre-classified, must be resolved within 7 days

## Promotion

Crossing a circle is **emergence**, not command. The producer decides:

```yaml
# Before
circle: individual

# After (the producer makes a deliberate edit)
circle: shared
promotion_note: "Moved to shared because partner needs visibility for next call."
```

The system supports this with a one-line frontmatter edit. It does **not** auto-promote based on view counts, edit frequency, or any other signal.

## What this protects against

- **Premature institutionalization** — drafts being treated as company truth before the producer is ready
- **Boundary leakage** — partner-visible notes drifting into private commitments
- **Forced archive** — making people stop their natural workflow to feed a central repository

## Inference fallback

When `circle:` is missing, `brain_surface.py` infers from path:

| Path prefix | Inferred circle |
|---|---|
| `concepts/`, `syntheses/`, `decisions/`, `entities/` | institutional |
| `_factory/`, `artifacts/`, `articles/` | shared |
| `sources/transcripts/`, `sources/get-biji/` | raw |
| `insights/`, `drafts/` | individual |
| else | unknown |

Explicit field always overrides inference. If you disagree with the path-based default, write it down.
