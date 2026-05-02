---
title: "Example decision: distill Company Brain into a public skill"
type: decision
domain: company-brain
created: 2026-05-02
date: 2026-05-02
participants: ["alice", "bob"]
source_transcript: "sources/transcripts/2026-05-02-example-meeting-transcript.md"
source_minute_token: ""
decision_status: committed
circle: shared
relationships:
  - type: derives-from
    target: "[[2026-05-02-example-meeting-transcript]]"
    evidence:
      - "[[2026-05-02-example-skill-distillation]]"
    status: active
    note: "Decision was extracted from the meeting transcript on the same day."
---

# Example decision: distill Company Brain into a public skill

## 1. Decision Rationale

**Final decision**: Distill the Company Brain stack into a public skill (Option C — full skill including parameterized scripts and an anonymized example vault), publish to GitHub as v0.1 experimental, then re-score after a 7-day usage window.

**Key arguments**:

1. The methodology (Sentra × dual-axis × 24h re-score) is generalizable; not publishing means the IP stays trapped in one vault. *(quote: "the methodology is the asset, not the data" — alice — confidence: high)*
2. v0.1 experimental label is honest about usage maturity D; readers can calibrate. *(quote: "let's be explicit it's not production" — bob — confidence: high)*
3. Field-test evidence (54/60 scaffold + 100% grep-verified extractions) is enough to publish; we don't need full usage data first. *(quote: "we have the scaffold story, the usage story will come from adopters" — alice — confidence: medium)*

## 2. Commitments

| Owner | What | Due | Source quote | Confidence |
|---|---|---|---|---|
| alice | Write SKILL.md + 5 references + parameterize 5 scripts + bundle example vault | 2026-05-02 EOD | "I'll do the build today" | high |
| bob | Review the public-facing positioning before push | 2026-05-02 | "I'll read README before commit" | high |
| alice | Schedule a 7-day re-audit on 2026-05-09 to capture usage delta | armed at create time | "let's lock the re-score" | high |

## 3. Disagreements

- **Should v0.1 include the field-test scores?**
  - Supporter (alice): "We should publish 54/60 scaffold + 4/10 usage so readers calibrate"
  - Opposer (bob): "That risks looking unfinished and might scare off adopters"
  - Resolution: Include both; add a clear "honest constraints" section in README; bob agreed.
  - Confidence: high

## 4. Counterfactuals (rejected alternatives)

- **Wait 7 days for usage data before publishing**
  - Rejected reason: Loses the timing window; methodology value doesn't depend on usage data
  - Source quote: "the methodology is the asset"
  - Confidence: high

- **Publish methodology only (Option A — spec without scripts)**
  - Rejected reason: Methodology without runtime is hard to evaluate; readers can't kick the tires
  - Source quote: "let people clone and run on their own vault"
  - Confidence: high

## 5. Extraction meta

- Tool: extract_decision.py v0.1
- Extracted at: 2026-05-02T21:15:00+08:00
- Transcript word count: ~800
- Self-check notes: Dialogue-type (alice + bob, 2 voices). All quotes greppable in source transcript.

---

> This is an **example** decision page. The participants and content are fictional; the format is the real production format. Use it as a template for your own decisions and for testing the lint scripts.
