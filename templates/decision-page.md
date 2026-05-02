---
title: "<one-sentence decision summary>"
type: decision
domain: <your-domain>
created: YYYY-MM-DD
date: YYYY-MM-DD
participants: ["alice", "bob"]
source_transcript: "sources/transcripts/YYYYMMDDhhmm-<topic>-transcript.md"
source_minute_token: ""
decision_status: draft   # draft | reviewed | committed | superseded
circle: shared           # individual | shared | institutional
relationships:
  - type: derives-from
    target: "[[<source-transcript-stem>]]"
    evidence:
      - "[[<this-decision-stem>]]"
    status: active
    note: "Decision is extracted from this transcript."
---

> **Draft (awaiting human review)** — Every quote in this draft must be greppable in the source transcript. Confidence values are calibrated by the extractor: a monologue-type transcript yields mostly low/medium disagreements; a dialogue-type yields high.

# <Decision title>

## 1. Decision Rationale

**Final decision**: <one sentence>

**Key arguments**:

1. <argument> — *(quote: "..." — speaker: alice — confidence: high)*
2. <argument> — *(quote: "..." — speaker: bob — confidence: medium)*
3. ...

## 2. Commitments

| Owner | What | Due | Source quote | Confidence |
|---|---|---|---|---|
| alice | <commitment> | YYYY-MM-DD | "..." | high |
| bob | <commitment> | YYYY-MM-DD | "..." | medium |

## 3. Disagreements (preserve dissent — don't smooth it over)

- **<topic 1>**
  - Supporter: <name> — *quote: "..."*
  - Opposer: <name> — *quote: "..."*
  - Resolution: <how it landed>
  - Confidence: high

## 4. Counterfactuals (what was rejected and why)

- **<alternative 1>**
  - Rejected reason: <one line>
  - Source quote: "..."
  - Confidence: high

## 5. Extraction meta

- Tool: extract_decision.py v0.1
- Extracted at: <ISO timestamp>
- Transcript word count: ~<n>
- Self-check notes: <transcript type? grep verification rate?>

---

## Review checklist (delete after promotion)

- [ ] All `source_quote` strings appear in the source transcript (grep-verify)
- [ ] At least one disagreement (or honest "(none — this was a monologue)")
- [ ] At least one counterfactual (or honest "(none — single-option decision)")
- [ ] `decision_status` updated from `draft` to `reviewed` or `committed`
- [ ] Frontmatter `circle:` is correct
- [ ] After approval: `mv <this>.md.draft.md <this>.md`
