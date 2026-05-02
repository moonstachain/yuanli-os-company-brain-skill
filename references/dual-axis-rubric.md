# Dual-axis maturity rubric

> Why two axes? Because "the system is built" and "the system is being used" are independent — and treating them as one number is the fastest way to fool yourself.

## The problem this solves

Field observation (2026-05-02): after 30 hours of focused build, a fresh Company Brain installation can score **A (54/60)** on a traditional 6-axis rubric while having essentially zero real usage data. Reporting "54/60 = A grade" feels honest but **is misleading**, because the score reflects scaffold quality, not actual context-graph density.

This rubric splits maturity into two independent axes so the gap is visible:

```
┌────────────────────────────────────────────┐
│  Scaffold maturity (60-pt)                 │  ← design / spec / scripts / docs in place
│  Usage maturity (10-pt)                    │  ← real data flowing through the system
└────────────────────────────────────────────┘
```

A healthy system trends toward **both** axes increasing. A sick one has Scaffold A and Usage D and stays that way.

## Axis 1 · Scaffold maturity (60-pt, B+ ≥ 48)

Six sub-axes × five checkpoints × {0 = absent, 1 = partial, 2 = formed} = 60.

### 1. Theme

| Checkpoint | 2 pts | 1 pt | 0 |
|---|---|---|---|
| Objective clarity | the audit object & objective are explicit | partial / fuzzy | absent |
| Priority defensible | clearly deserves entry now | maybe deserves entry | no case |
| Boundary clear | in/out of scope explicit | edges leak | mixed |
| Long-term value | compounds into capability | mixed | one-off |
| Stop condition | explicit & respected | exists but soft | none |

### 2. Strategy

| Checkpoint | 2 pts | 1 pt | 0 |
|---|---|---|---|
| Level named | explicit (insight / global) | strategy exists, level fuzzy | none |
| Core contradiction | explicit | tension visible, not distilled | only surface activity |
| Alternatives compared | meaningfully weighed | mentioned | none |
| Path coherent | matches objective + constraints | plausible | ad hoc |
| Risk boundary | failure modes explicit | partial | none |

### 3. Execution

| Checkpoint | 2 pts | 1 pt | 0 |
|---|---|---|---|
| Chain exists | explicit & stable | gaps | improvised |
| Ownership clear | named owners | blurred | none |
| Artifacts exist | full set | partial | mostly claims |
| Verification explicit | targets & evidence stated | partial | none |
| Closure clear | state & next step named | partial | ambiguous |

### 4. Recursion

| Checkpoint | 2 pts | 1 pt | 0 |
|---|---|---|---|
| Reflection captured | explicit & preserved | weak | none |
| Writeback to system | rules / skills / docs updated | partial | none |
| Repeated errors falling | visible reduction | unclear | gaps repeat |
| Upgrade destination | explicit | fuzzy | none |
| Next-round action | concrete | vague | none |

### 5. Global optimum

| Checkpoint | 2 pts | 1 pt | 0 |
|---|---|---|---|
| Alternatives considered | seriously weighed | lightly | first path wins |
| Reuse first | reuse > new build | some reuse | from-zero default |
| Layers distinct | theme / strategy / execution kept apart | some confusion | mixed |
| Resources proportionate | sharp | acceptable | wasteful |
| Cross-system leverage | across skills/runtimes | some | isolated |

### 6. Human-friendly

| Checkpoint | 2 pts | 1 pt | 0 |
|---|---|---|---|
| Few interruptions | minimal & meaningful | some avoidable | dragged into routine |
| Few rework cycles | structure prevents | some leaks | rework dominates |
| Few cycles burned | restrained | acceptable | obvious waste |
| Hidden complexity low | rollback / review easy | manageable | dominates |
| Output usable | directly | after cleanup | mostly noise |

### Bands (Scaffold)

| Score | Band |
|---|---|
| 54-60 | A |
| 48-53 | B+ |
| 42-47 | B |
| 36-41 | C+ |
| 30-35 | C |
| < 30 | D |

## Axis 2 · Usage maturity (10-pt, B+ ≥ 7)

Five usage checkpoints × {0 = absent, 1 = partial, 2 = formed} = 10.

| Checkpoint | 2 pts | 1 pt | 0 |
|---|---|---|---|
| Explicit relationships growth | ≥ 5 wiki pages with `relationships:` block (beyond example) | 1-4 | 0 |
| Decisions formal count | ≥ 5 formal decision pages | 1-4 | 0 |
| Typed edges total | ≥ 20 (explicit + derived) | 5-19 | 0-4 |
| Right-time surface frequency | ≥ 3 real triggers/week | 1-2 | 0 |
| Cross-role real usage | ≥ 2 of {self / team / partner / agent} actively used | 1 | 0 |

### Bands (Usage)

| Score | Band |
|---|---|
| 9-10 | A |
| 7-8 | B+ |
| 5-6 | B |
| 3-4 | C |
| 0-2 | D |

The numerical thresholds (5 / 5 / 20 / 3 / 2) come from [`typed-relationships-schema.md`](typed-relationships-schema.md) §8 G2 closure threshold + field-test calibration.

## How to report a dual-axis result

**Bad** — single number that hides the gap:

> "Maturity: 54/60, A grade."

**Good** — both axes side by side:

```
┌─────────────────────────────────────────────┐
│  Scaffold maturity:  54/60   A              │
│  Usage maturity:      4/10   D              │
└─────────────────────────────────────────────┘
```

The dual report immediately surfaces "design is done, real adoption hasn't started" — the most common state for newly-built knowledge systems.

## Field test (2026-05-02)

A 30-hour Company Brain build on a 1170-note vault scored:

- Scaffold: 54/60 (A) — all 6 sub-axes 8-10 / 10
- Usage: 4/10 (D) — explicit relationships 0/2, decisions 1/2, typed edges 1/2, surface freq 2/2 (validated via UserPromptSubmit hook), cross-role 0/2

The single-number version (54/60 alone) would have suggested "ready for production". The dual version correctly surfaced "ship as v0.1 experimental, expect 7-day usage observation before any v0.2 claim".

## Re-scoring discipline

A new score is **valid for 24 hours**. After 24 hours of further build, you must re-score with **fresh hard evidence** (not memory). Optimistic post-build estimates routinely overshoot real measurements by 5-10 points; the 24h re-score catches them. See [`24h-rescore-protocol.md`](24h-rescore-protocol.md).

## Adoption note

Use this rubric for any system that has both "spec/scripts" and "live data" — Company Brains, internal docs, design systems, governance frameworks, ML platforms. Don't use it for single-file projects or one-shot scripts (Scaffold-only is fine there).
