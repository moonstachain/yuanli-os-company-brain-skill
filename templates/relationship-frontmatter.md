# `relationships:` frontmatter snippet

Add typed edges to any wiki page. The field is a YAML list of relations from this page outward.

## Minimal example

```yaml
---
title: <your page>
relationships:
  - type: supports
    target: "[[some-target-note]]"
    evidence:
      - "[[evidence-source-note]]"
    status: active
    note: "One short sentence explaining why this relationship is real."
---
```

## Six allowed relation types (no others — see `references/typed-relationships-schema.md`)

| Type | Direction | Use when |
|---|---|---|
| `commits-to` | current → commitment / task / outcome | A person, team, or decision creates an obligation. |
| `owns` | current → artifact / project / decision | Current page has accountable ownership. |
| `blocks` | current → blocked target | Current page prevents target from progressing. Add `status` + `note`. |
| `derives-from` | current → upstream source / parent | Current is extracted from / based on the target. |
| `supersedes` | current → older target | Current replaces target as preferred reference. |
| `supports` | current → claim / decision | Current strengthens / evidences without owning. |

## Required fields per relation

- `type` — must be one of the six above
- `target` — single Obsidian wikilink string (`"[[note-name]]"`)
- `evidence` — non-empty list of wikilink strings (provenance)

## Optional fields

- `status` — `proposed | active | stale | archived` (default `active`)
- `since` / `until` — date strings
- `confidence` — `low | medium | high` (only when evidence is indirect)
- `note` — one short human sentence

## Direction test (read every relationship as)

```
CURRENT_FILE --type--> TARGET
```

If the sentence sounds backwards, move the relationship to the other note or pick a different type.

## Examples

### Decision commits to a task

```yaml
relationships:
  - type: commits-to
    target: "[[operations/tasks/q1-pricing-rollout]]"
    evidence:
      - "[[decisions/2026-05-02-pricing-decision]]"
    status: active
    since: 2026-05-02
    note: "Decision creates the rollout commitment."
```

### Person owns a project, blocks another

```yaml
relationships:
  - type: owns
    target: "[[entities/projects/customer-portal]]"
    evidence:
      - "[[decisions/2026-04-15-portal-owner-assignment]]"
    status: active
  - type: blocks
    target: "[[entities/projects/internal-dashboard]]"
    evidence:
      - "[[operations/runs/2026-05-01-roadmap-review]]"
    status: proposed
    note: "Dashboard work depends on portal data model stabilizing."
```

### New schema supersedes older

```yaml
relationships:
  - type: supersedes
    target: "[[concepts/typed-relationships-schema-v0-1]]"
    evidence:
      - "[[decisions/2026-06-01-schema-v0-2-approval]]"
    status: active
    since: 2026-06-01
```

## Validation

Run `python3 scripts/wiki_lint_l10.py --wiki-root <vault>` after editing to catch:

- E1-E6 hard errors (list shape, required fields, valid type, wikilink format, evidence non-empty, single target)
- W1-W5 warnings (commits-to without owns, blocks without status+note, etc.)

## Adoption protocol (don't migrate everything)

1. Start with new or actively edited institutional notes only.
2. Add 1-3 high-signal relationships per page; avoid spam.
3. Prefer `evidence` over confidence theater: no evidence means no typed edge.
4. When unsure between a plain wikilink and a typed relationship, use a plain wikilink first.
5. Revisit the six-type enum only after repeated real examples prove a missing class.
