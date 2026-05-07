# Karpathy LLM Wiki Pattern · AI Entry Compression Layer

> Pattern: pre-compile two ~500-word files so AI doesn't scan the full vault.
> Origin: Andrej Karpathy's `obsidian-as-personal-research-os`.
> Independent implementations: hirosichen/obsidian-ai-knowledge-base, mingrath/obsidian-ai-knowledge-agent.
> Distilled into this skill 2026-05-08.

---

## Problem

Once a wiki has > 500 pages, AI queries that "scan the whole vault" become:
- Slow (linear cost per query)
- Expensive (full-context every time)
- Noisy (low signal-to-token ratio)

You need an **AI-facing compressed entrance** that lets LLM jump to the right pages in O(1) instead of O(N).

---

## Solution

Two top-level files at the vault root:

### `_ai-entry.md` — the master map (~800 words)

Contents:
1. Top 5-10 domain MOCs (multi-page navigation hubs)
2. Top governance / contract pages (most-referenced)
3. Workflow shortcuts ("when writing → start with X")
4. Hard constraints (what NOT to do, e.g. "don't modify sources/")
5. Stats (total counts)

This file is **stable** — updated weekly or after major restructures.

### `_hot.md` — the activity cache (~500 words)

Contents:
1. New decisions (last 14-60 days)
2. Recently updated concepts (last 14 days, top 10)
3. High-density sources (last 7 days, top 5)
4. Open commitments / tasks (top 5 by age)
5. Anomalies / risks (from wiki-lint)

This file is **dynamic** — refreshed daily by cron.

---

## AI contract (in CLAUDE.md / equivalent)

> Any AI entering this wiki MUST first read `_ai-entry.md` + `_hot.md` (combined ~1500 words).
> These two files locate ~90% of answers. Only after reading them, decide which ≤5 specific pages to deep-read.
> **Forbidden**: directly scanning `concepts/` / `sources/` / `_index.md` (full).

---

## Two refresh strategies

### Strategy A: LLM-driven (smart but recursive-risky)

Cron triggers `claude -p` with prompt to rewrite `_hot.md`. LLM reads recent decisions / concepts / sources and produces a 500-word summary.

**Pros**: high-quality narrative, can prioritize semantically.

**Cons**: spawns child Claude process; risky if running during another Claude session. May fail silently.

### Strategy B: Static script (no LLM, robust)

Cron triggers a Python script that walks the file system, reads frontmatter titles + mtimes, produces a structured `_hot.md`.

**Pros**: zero LLM cost, no recursion risk, runs in seconds, deterministic.

**Cons**: less narrative; just a structured list.

### Recommended: B as primary, A as luxury

Use Strategy B as your default. Only upgrade to A when:
- You have 1000+ concepts and need semantic-prioritized hot list
- You can guarantee LLM context is isolated (separate API key, no concurrent session)

The static script ships in this skill: `scripts/refresh_hot_static.py`.

---

## Naming conventions (avoid clashes)

| Karpathy | hirosichen | This skill | Why |
|---|---|---|---|
| `Index.md` | `Index.md` | `_ai-entry.md` | underscore prefix avoids clash with existing `_index.md` (full directory) |
| `hot.md` | `hot.md` | `_hot.md` | same prefix convention |

If your wiki already has an `_index.md` for full directory listing, use the `_ai-entry.md` / `_hot.md` names. They're for **AI consumption**, not human navigation.

---

## Trigger options (multi-channel)

Don't lock yourself into one trigger:

| Trigger | When | Pros | Cons |
|---|---|---|---|
| Obsidian Shell Commands plugin | On file create | Real-time | Plugin dependency |
| launchd / cron daily | 06:00 every day | Predictable, no plugin | Up to 24h staleness |
| Manual `make refresh-hot` | Anytime | Full control | Easy to forget |

**Recommended**: launchd daily at 06:00 (so morning queries hit fresh `_hot.md`) + manual fallback command.

---

## Common failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| `_hot.md` shows old data | Cron not running | `launchctl list \| grep <label>` |
| `_hot.md` is empty | Script error | `tail ~/.gstack/<label>.log` |
| AI still scans full vault | CLAUDE.md contract not in place | Add `_ai-entry.md` + `_hot.md` to CLAUDE.md section 0 |
| Multiple AIs disagree on what to read | No shared CLAUDE.md | Write a single CLAUDE.md at vault root |

---

## ROI evidence

From real implementation 2026-05-08:
- Vault size: 977 concepts + 5713 sources + 82 syntheses
- Old AI query cost: ~50K-100K tokens (full vault scan)
- New AI query cost: ~3K tokens (`_ai-entry` + `_hot` + 3-5 deep pages)
- **Compression ratio: ~20-30×**

Ship-or-skip rule: if your wiki has < 200 pages, this pattern is overkill. Above 200, ROI is positive within a week.

---

## See also

- `templates/_ai-entry.md.template` — fill-in-the-blanks template
- `templates/_hot.md.template` — initial hot cache structure
- `scripts/refresh_hot_static.py` — Strategy B implementation (no LLM)
- `references/5-layer-architecture.md` — where this fits in L1 Memory layer
