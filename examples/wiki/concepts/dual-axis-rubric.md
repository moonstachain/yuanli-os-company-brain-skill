---
title: Dual-axis maturity rubric
type: concept
domain: company-brain
created: 2026-05-02
date: 2026-05-02
circle: institutional
audience: both
related:
  - "[[24h-rescore-protocol]]"
relationships:
  - type: supports
    target: "[[example-synthesis-company-brain-overview]]"
    evidence:
      - "[[example-synthesis-company-brain-overview]]"
    status: active
---

# Dual-axis maturity rubric

> Reporting "system maturity = 54/60" hides the gap between **scaffold built** and **actually being used**. Split into two axes.

## Axis 1: Scaffold maturity (60-pt)

Six sub-axes × 5 checkpoints × {0/1/2}. Measures whether the system has been designed, scripted, documented.

Bands: A (54-60) / B+ (48-53) / B (42-47) / C+ (36-41) / C (30-35) / D (<30)

## Axis 2: Usage maturity (10-pt)

Five usage checkpoints × {0/1/2}. Measures whether real data is flowing through the system.

| Checkpoint | 2 pts | 1 pt | 0 |
|---|---|---|---|
| Explicit relationships growth | ≥ 5 pages | 1-4 | 0 |
| Decisions formal count | ≥ 5 | 1-4 | 0 |
| Typed edges total | ≥ 20 | 5-19 | 0-4 |
| Right-time surface frequency | ≥ 3 triggers/week | 1-2 | 0 |
| Cross-role real usage | ≥ 2 of {self/team/partner/agent} | 1 | 0 |

Bands: A (9-10) / B+ (7-8) / B (5-6) / C (3-4) / D (0-2)

## Why this matters

A new system can score **A on Scaffold** and **D on Usage** simultaneously — and reporting only one number hides this. The dual report makes the gap visible:

```
┌─────────────────────────────────────────────┐
│  Scaffold maturity:  54/60   A              │
│  Usage maturity:      4/10   D              │
└─────────────────────────────────────────────┘
```

This immediately surfaces "scaffold ready, real adoption hasn't started" — the most common state for newly-built knowledge systems. See `references/dual-axis-rubric.md` for full checkpoint tables.
