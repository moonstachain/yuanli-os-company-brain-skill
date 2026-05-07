# Borrow Rubric · 3-Tier Completion Discipline

> "GO ALL" doesn't mean "done". A borrow has 3 tiers, and you should track each separately.
> Distilled from D0.5 closure 2026-05-08 (4 GitHub borrows).

---

## The 3 tiers

| Tier | What "done" means | Common failure |
|---|---|---|
| **Doc-level** | SKILL.md / concept / reference page exists, structurally complete | "I added the section, ship it" |
| **Executable-level** | Tool / script / cron actually exists and runs without error | "L9 algorithm written" but never executed |
| **Verified-level** | End-to-end produced **real output with real data** | "Cron is loaded" but never fired with real data |

**Default delusion**: claiming doc-level = done.

**Reality**: only verified-level counts toward maturity.

---

## Use this when borrowing from any open-source project

For each candidate borrow, score each tier independently 0-100%:

| Tier | Score | Evidence |
|---|---|---|
| Doc-level | __% | file path + line count |
| Executable-level | __% | "ran command + exit code 0" |
| Verified-level | __% | output file size + content sanity check |

**Composite** = `(doc + exec + verified) / 3`. NOT max(), NOT average — bias toward verified.

---

## Why average lies

Suppose 4 borrows:
- ① doc=100% exec=60% verified=0% → 53%
- ② doc=100% exec=0%  verified=0% → 33%
- ③ doc=100% exec=0%  verified=0% → 33%
- ④ doc=100% exec=25% verified=0% → 42%

Average across borrows: 40%.

But if you only report doc-level:
- "All 4 done at 100% — 100% complete!"

This is the lie. Real status: nothing has been verified end-to-end. Production is in 50% state at best.

**Verified-level is the only honest KPI.**

---

## Discipline rules

1. **Stage-Execute-Verify** — every borrow must hit all 3 tiers before claiming done.
2. **No "GO ALL" without verified-level mandate** — set a deadline (e.g. within 1 hour of doc-level commit).
3. **Honest reporting** — when a stakeholder asks "is X borrowed?", report all 3 tiers separately.
4. **Bias toward verified** — when prioritizing, finish verified-level for one borrow before starting doc-level for another.

---

## Verified-level checklist

For a borrow to claim verified-level, you must have:

- [ ] Tool/script ran successfully (exit code 0)
- [ ] Output file produced (path + size)
- [ ] Output content sanity-checked (manual or automated)
- [ ] Result logged to bridge-log / commit history
- [ ] At least 1 downstream consumer can read the output

---

## When to skip verified-level (and admit it)

Some borrows are legitimately doc-only:
- Methodology references (no code to run)
- Long-term tracking entries (verification = waiting period)

For these, **explicitly mark `verified-level: not-applicable`** with reason. Don't pretend.

---

## Anti-pattern: documentation theater

Symptom: lots of beautiful new SKILL.md / README sections, no actual code change.

Detection:
```bash
git diff <commit> -- 'SKILL.md' '*.md' | wc -l   # docs lines
git diff <commit> -- 'scripts/' '*.py'   | wc -l  # code lines
```

If docs:code > 5:1, you're in documentation theater.

Healthy ratio is closer to 1:1 or 1:2 (slightly more code than docs).

---

## Sample template

When closing a borrow, append to your bridge-log / project log:

```yaml
borrow:
  source: <upstream repo>
  borrow_date: YYYY-MM-DD
  doc_level:
    score: 100
    artifact: SKILL.md L9 + L10 sections inserted
  exec_level:
    score: 100
    artifact: scripts/wiki_lint.py L9 algorithm + L10 prompt generator
    run_proof: "exit 0, _lint-report.md = 4543 lines"
  verified_level:
    score: 100
    artifact: _lint-report.md L9 surface = 50 pairs, L10 prompt file generated
    output_path: _lint-report.md, _lint-l10-prompt.md
    sanity_check: "manual review showed no false positives in top 5 L9 entries"
  composite: 100
```

Three numbers, three artifacts, one composite. That's the contract.
