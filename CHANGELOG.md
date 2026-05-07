# Changelog

All notable changes to this skill will be documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · [SemVer](https://semver.org/).

---

## [v0.2.0] — 2026-05-08

### Added · 4 new patterns from real production borrow audit

#### `references/5-layer-architecture.md`
Hosting-aware, locality-first 5-layer model:
L0 Intake → L1 Memory (symbol/vector/active) → L2 Promotion → L3 Recall → L4 Action.
Includes:
- 4 explicit cross-layer **seams** with data shape contracts
- Hosting decision matrix (13 asset types × 6 platform candidates)
- Three architecture principles: Locality first / Credential adjacency / Failure radius
- Trigger lines for re-architecture (3rd FT collaborator, 5GB ChromaDB, etc.)

#### `references/borrow-rubric-3-tier.md`
Discipline for honest borrow completion tracking:
- **Doc-level / Executable-level / Verified-level** — each tier scored 0-100% independently
- Composite = average, **biased toward verified** (not max)
- Anti-pattern: documentation theater detection (docs:code ratio > 5:1)
- Sample bridge-log YAML for closing a borrow

#### `references/karpathy-llm-wiki-pattern.md`
AI Entry Compression Layer pattern:
- Two top-level files: `_ai-entry.md` (master map, ~800 words) + `_hot.md` (activity cache, ~500 words)
- Static script strategy (no LLM, robust) vs LLM-driven (smart but recursive-risky)
- Compression ratio measured: **~20-30× token reduction** on a 977-concept wiki
- Naming convention: underscore prefix to avoid clash with existing `_index.md`

#### `scripts/refresh_hot_static.py`
No-LLM static scanner that produces real `_hot.md` content:
- Walks `decisions/` `concepts/` `sources/` `operations/audits/`
- Reads frontmatter titles + mtimes
- Writes structured `_hot.md` in seconds, deterministic
- Recommended primary refresh strategy (over LLM-driven cron)

#### `scripts/schema_system.py`
Three-in-one frontmatter schema toolkit (borrowed from basicmachines-co/basic-memory):
- `infer <dir>` — walk markdown files, output union schema YAML with field present_pct + type distribution + tier (required/recommended/optional)
- `validate <file> <schema.yaml>` — check single file, return errors + warnings
- `diff <a.yaml> <b.yaml>` — added/removed/changed fields
- Surfaces hidden problems: e.g. "97% of concepts missing frontmatter"

#### `templates/_ai-entry.md.template` + `templates/_hot.md.template`
Fill-in-the-blank starting points for the Karpathy pattern.

### Changed

- README.md updated with v0.2 quickstart and new pattern table
- (no breaking changes from v0.1)

### Note · 3-tier discipline applied to v0.2 itself

This v0.2 release reached **verified-level** for all 4 new patterns:
- 5-layer architecture: real-world implementation passing 60-day audit
- 3-tier rubric: applied to 4 separate GitHub borrows on 2026-05-08
- Karpathy pattern: hot.md actually filled with real data via static script
- schema_system: ran `infer` against 968 concepts + 82 syntheses, produced real YAML

---

## [v0.1.0] — 2026-05-02

### Added · Initial distillation

- Sentra "Company Brain" three-layer architecture mapped to wiki structure
- Three-circle boundaries (individual / shared / institutional) with promotion gates
- Typed-relationships schema (6 enum: commits-to / owns / blocks / derives-from / supersedes / supports)
- Anti-hallucination 4-tuple extractor with mandatory `source_quote` + grep verification
- Dual-axis maturity rubric (60-pt scaffold + 10-pt usage)
- 24h re-score protocol for completion claims
- 5 references / 5 scripts / 3 templates / 12-note example vault

---

## [Unreleased] · v0.3 backlog

Candidate additions (not yet stage):
- `references/staging-execute-verify-pattern.md` (full L0-L4 rollout discipline)
- `references/multi-channel-redundancy.md` (4-channel reminder pattern)
- `references/ai-entry-compression.md` (deeper L1 sub-layer breakdown)
- `scripts/wiki_lint_l9.py` (Missing Cross-References as standalone)
- `examples/sample-runs/d0.5-borrow-closure/` (full audit trail of v0.2 borrow process as case study)
