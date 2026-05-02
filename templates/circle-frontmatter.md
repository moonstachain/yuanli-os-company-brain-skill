# `circle:` frontmatter snippet

Add this field to any wiki page to make its three-circle membership explicit.

```yaml
---
title: <page title>
type: <concept | synthesis | decision | entity | etc.>
circle: institutional   # individual | shared | institutional | raw | tooling | unknown
---
```

## Six valid values

| Value | Meaning | Typical paths |
|---|---|---|
| `individual` | Personal / private. Drafts, notes, private commitments. | `insights/`, `drafts/` |
| `shared` | Team / project / customer common ground. Roadmap drafts, project workspaces. | `_factory/`, `artifacts/`, `articles/` |
| `institutional` | Company or ecosystem record. Concept definitions, decisions, synthesis. | `concepts/`, `syntheses/`, `decisions/`, `entities/`, `comparisons/` |
| `raw` | Unprocessed source material. Transcripts, raw notes. | `sources/transcripts/`, `sources/get-biji/` |
| `tooling` | Skills, scripts, configs (this very repo if you check it in) | `_skills/`, `_tools/` |
| `unknown` | Pre-classified. Use as a temporary state and resolve within 7 days. | (any path missing the field) |

## Auto-inference

If the field is missing, `brain_surface.py` infers from the path using the table above. Explicit field always wins over inference.

## Promotion gate

Promotion (individual → shared → institutional) is decided by **the producer**, not pushed by management. The promotion event is just an edit:

```yaml
# Before
circle: individual

# After
circle: shared
# (and optionally add a `promotion_note: "moved 2026-05-09 because team needs visibility"`)
```

Do NOT auto-promote based on view counts, edits, or any signal except the producer's explicit decision. See [`references/three-circles-protocol.md`](../references/three-circles-protocol.md).

## Visibility under role lens

| Role | Visible circles |
|---|---|
| `self` | individual + shared + institutional + raw + tooling + unknown |
| `student` | shared + institutional |
| `partner` | institutional |
| `agent` | institutional (capability-bounded) |

`brain_surface.py --role <role>` filters by this table.
