# 24-hour re-score protocol

> Any "I'm done" claim must be re-scored within 24 hours with fresh hard evidence. Optimistic post-build estimates routinely overshoot real measurements by 5-10 points.

## The problem this solves

Field observation (2026-05-02 evening, immediately after Phase 5 closure):

- Self-reported estimate: "Phase 1-5 all done, scaffold maturity should be ~40+/60"
- 24-hour re-score with hard evidence: **47/60 actual**
- Then 5 fixes, second re-score: **54/60**

Without the discipline of "re-score with command output, not memory", the original 40+ estimate would have stuck. The gap between estimate and reality came from:

1. Counting "I wrote the spec" as full credit when only the scaffold existed
2. Forgetting that lint passing on **0 data** is a false positive, not validation
3. Conflating "the script works" with "the deduction is closed"

## Protocol (3 steps)

### Step 1 · Lock the timestamp

The moment you say "done" or "complete" or "ship-ready", record:

- ISO timestamp of the claim
- The artifact list claimed
- The metric values claimed

Without a locked timestamp, re-scoring drifts into "I think it improved" rather than "the number changed by N".

### Step 2 · Schedule the re-score (≤ 24h)

The re-score must happen within 24 hours of the claim. Two reasons:

1. **Memory of intent decays fast.** After 24h you forget which checkpoints you actually validated vs which you assumed.
2. **Cache of evidence is still warm.** Fresh re-runs of `grep`, `wc`, script outputs are easy because you remember the commands.

If your tooling supports scheduled tasks (Claude Code `/schedule`, cron, Linear automation), arm a one-shot agent for 23h later. If not, set a calendar reminder.

### Step 3 · Re-score with hard evidence (no memory shortcuts)

For each sub-axis, you must:

| Required | Forbidden |
|---|---|
| Run the actual command (e.g. `wc -l`, `grep -rl`, script `--stats`) | Cite from memory ("I think it's around 20") |
| Paste command output into the report | Paraphrase output |
| Note any "0-data clean" results explicitly | Treat empty result as success |
| Compare to the locked baseline numerically | Wave hands at "feels better" |

Each deduction line in the original audit must be classified:

- **closed** — checkpoint now full credit, evidence shown
- **improved** — partial credit moved up, but not full
- **unchanged** — same state, no progress
- **regressed** — worse than baseline (rare but possible after sloppy fixes)

## Worked example (2026-05-02)

**T0 claim**: "Phase 5 complete, all 5 gaps closed, total ≈ 40+/60"

**T0 + 1h re-score** (audit v0.2):

```
6-axis re-test:
  Theme: 9/10
  Strategy: 8/10
  Execution: 7/10  ← "closure clear" = 0 (skill registered nowhere)
  Recursion: 6/10  ← "writeback" = 1 (routing-bridges not updated)
  Global: 9/10
  Human-friendly: 8/10
Total: 47/60 (B grade)

Delta vs estimate: -7+ points. Estimate was optimistic.
```

**T0 + 30min fix** (5 nails to address the deductions):

- F1: register skill in routing-bridges → "writeback" 1→2
- F2: schedule 7-day re-score → "next-round" 1→2
- F3: define "really done" threshold → "stop condition" 1→2
- F4: mv draft decision to formal → "rework leak" 1→2
- F5: run extractor on a third transcript → "repeated errors falling" 1→2

**T0 + 1h re-score** (audit v0.3, with hard evidence):

```
Theme: 10/10  (+1 from §8 threshold)
Strategy: 9/10  (+1 from §8 fallback options)
Execution: 9/10  (+2 from F1+F2+F3 closing the deduction)
Recursion: 9/10  (+3 from F1+F2+F5)
Global: 9/10
Human-friendly: 8/10
Total: 54/60 (A grade)

Delta vs T0+1h: +7 points. Real progress, evidenced by command output.
```

## What the discipline catches

Three failure modes that the protocol catches:

### 1. "Spec ≠ implementation" credit

Writing a spec that says "use typed edges" is not the same as having typed edges. The re-score asks: how many actual typed edges does `relationship_graph.py --stats` show?

### 2. "Lint clean ≠ data validated"

A schema lint that passes on 0 data instances is a structural blind spot, not validation. The re-score requires explicit acknowledgment: "lint clean BUT 0-data, reduce credit".

### 3. "I described the change ≠ I made the change"

The re-score requires the file diff or command output, not the description.

## When NOT to use this protocol

- Single-file fixes (typo, formatting, dependency bump) — overhead exceeds value.
- One-shot scripts with no follow-on usage — there's nothing to re-score.
- Tasks where the "done" condition is intrinsically observable (test passes / build green / artifact deployed) — those have their own verification gate.

Use it when "done" depends on **multi-checkpoint systemic claims** — audits, framework adoptions, multi-phase rollouts, methodology installations.

## Promotion to protocol-level rule

This protocol started as an Evolution Note candidate during the v0.2 → v0.3 audit. After self-validating in the same session (the re-score correctly surfaced +7 points of real progress vs the +0 of zero-fix), it was promoted to a methodology reference. Treat it as a hard rule for any "system maturity" or "framework adoption" claim.

## Adoption checklist

When you adopt this skill, also adopt the discipline:

- [ ] Lock timestamps for every "done" claim
- [ ] Arm a re-score agent ≤ 24h later
- [ ] Re-score with command output, not memory
- [ ] Classify each deduction as closed / improved / unchanged / regressed
- [ ] Report the numerical delta, not just the new total
