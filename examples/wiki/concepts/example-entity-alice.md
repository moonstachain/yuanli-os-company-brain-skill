---
title: alice (example entity)
type: entity
domain: people
created: 2026-04-15
date: 2026-04-15
circle: shared
relationships:
  - type: owns
    target: "[[2026-05-02-example-skill-distillation]]"
    evidence:
      - "[[2026-05-02-example-skill-distillation]]"
    status: active
    note: "Alice owns the v0.1 build commitment."
---

# alice (example entity)

> An example entity page representing a fictional team member. Demonstrates `owns` relationship.

## Role

Backend engineer · methodology author · example data only.

## What alice owns

- The Company Brain skill v0.1 build (see `[[2026-05-02-example-skill-distillation]]`)
- The dual-axis rubric methodology

## Open commitments

1. Publish v0.1 of the public skill — due 2026-05-02 EOD
2. Schedule and run the 7-day re-audit — fire date 2026-05-09

These commitments derive from `decisions/2026-05-02-example-skill-distillation.md` and become typed edges via `relationship_graph.py`.

> This is an **example** entity. Use as a template for your own people / teams / projects.
