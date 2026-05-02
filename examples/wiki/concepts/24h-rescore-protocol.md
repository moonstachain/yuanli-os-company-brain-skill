---
title: 24-hour re-score protocol
type: concept
domain: company-brain
created: 2026-05-02
date: 2026-05-02
circle: institutional
audience: both
related:
  - "[[dual-axis-rubric]]"
relationships:
  - type: derives-from
    target: "[[dual-axis-rubric]]"
    evidence:
      - "[[example-decision-2026-05-02-skill-distillation]]"
    status: active
    note: "The 24h discipline is what makes the dual-axis rubric resilient to optimistic self-reports."
---

# 24-hour re-score protocol

> Any "I'm done" claim must be re-scored within 24 hours, with hard evidence (command output, not memory).

## The bias this catches

Field observation (2026-05-02): a self-reported "Phase 5 done, ~40+/60" turned out to be **47/60** when re-scored with hard evidence one hour later. After 5 fixes, a second re-score gave **54/60**.

Without the protocol, the optimistic 40+ would have stuck. The gap came from:

1. Counting "I wrote the spec" as full credit when only the scaffold existed
2. Treating "lint passes on 0 data" as validation (it's not — it's a structural blind spot)
3. Conflating "the script works" with "the deduction is closed"

## The 3-step protocol

1. **Lock the timestamp** when you say "done". Record the artifact list and metric values claimed.
2. **Schedule the re-score within 24h** (memory of intent decays fast; command-cache stays warm).
3. **Re-score with command output** — paste actual `wc -l`, `grep`, script `--stats` outputs. Classify each deduction as closed / improved / unchanged / regressed.

## When to apply

Use it for **multi-checkpoint systemic claims**: audits, framework adoptions, multi-phase rollouts.

Skip it for: single-file fixes, one-shot scripts, tasks with intrinsic verification (test passes / build green).

See `references/24h-rescore-protocol.md` for full discipline + worked example.
