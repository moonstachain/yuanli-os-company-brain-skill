# Changelog

All notable changes to this skill will be documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · [SemVer](https://semver.org/).

---

## [v0.5.0] — 2026-06-12

The "incorporate the flywheel" release. A first-principles self-audit (run with this
skill's own borrow-rubric) found the repo's biggest structural gap: the organs that
make the brain *live* in the author's production deployment — the prompt-time surface
hook, the write-back loop, the trust ladder — were not in the published repo. This
release closes that gap and fixes every trust defect the audit surfaced.

### Added · the production flywheel (7 scripts, field-run since 2026-06-06)

- `scripts/brain_surface_hook.py` — UserPromptSubmit hook: two-layer recall (OSA
  decision cards + concepts) on every non-trivial prompt, fail-silent, ~0.2s.
  Env-configured (`YUANLI_WIKI_ROOT`, `YUANLI_OSA_EXTRA_DIRS`) — machine-specific
  defaults removed during incorporation.
- `scripts/brain_writeback_hook.py` — Stop hook: auto-runs edge proposal for new
  OSA cards in a staging dir (env: `YUANLI_WRITEBACK_SRC/INBOX`).
- `scripts/brain_writeback.py` — fan-in engine: card JSON → concept scan → proposed
  edges → `.draft.json` for human review.
- `scripts/promote_card.py` — the human gate: reviewed draft → `decisions/osa/`,
  quality-gate checked, dry-run by default. AI proposes, human promotes.
- `scripts/embed_sources.py` — resumable batched vector indexer (DashScope, numpy).
- `scripts/cluster_decisions.py` — semantic clustering → "hot but unabsorbed topics".
- `scripts/retype_references.py` — flat `references` → 6 typed relations, dry-run.

### Changed · trust ladder through the core scripts

- `brain_surface.py`: CJK character-bigram retrieval (natural-language Chinese
  prompts now actually match), distinct-term precision signal, trust inference
  (`claude-auto < claude-unilateral < human-confirmed`), OSA-card scanning,
  optional semantic recall (graceful lexical fallback without numpy).
- `relationship_graph.py`: OSA-card JSON edges (`osa-card-json` source kind),
  high-value edges (`supersedes`/`blocks`) stay `candidate` until human-confirmed;
  stats now report active vs candidate.
- `metacognition_signals.py`: **weak-evidence signal shipped** (single-source OSA
  cards flagged — was a v0.2 roadmap item); supersedes-driven stale signals from
  decision cards.

### Fixed · every defect from the 2026-06-12 self-audit

- "pure stdlib, no deps" claim was false (schema_system.py imports PyYAML) →
  `requirements.txt` added (PyYAML + optional numpy), claims corrected in both
  READMEs and SKILL.md, import guarded with an actionable error.
- `schema_system.py` / `refresh_hot_static.py` hardcoded `~/Documents/your-wiki`
  default → now fail fast with usage when `WIKI_ROOT` is unset.
- SKILL.md said "7 scripts" (9 tracked), README trees said "5 methodologies /
  3 templates" (12 / 7) → all counts now generated-from-reality.
- Phase 2's `wiki_lint_l9.py (planned)` dangled since v0.1 → annotated (folded
  into L10; standalone L9 moved to v0.6 backlog).
- `examples/sample-runs/` snapshots were 42 days stale and disagreed with current
  output → re-captured against v0.5 scripts.
- One-off local distillation scripts and generated example artifacts now
  `.gitignore`d so `git status` stays honest.

### Added · CI

- `.github/workflows/ci.yml` — py_compile all scripts + run the three example-vault
  regressions on every push (the verified-level floor the audit found missing).

---

## [v0.4.0] — 2026-06-12

Distilled from a week of field discussions (2026-06-02 → 06-11) on running a
company brain across a real team: where different kinds of content should live,
how teammates get a slice of it, and how sandboxed Claude reads it.

### Added · tiered knowledge spine (the routing rubric)

#### `references/tiered-knowledge-spine.md`
3-tier content routing — **index spine** (local vault: concept network + pointers,
never bulk) / **capacity depth** (RAG notebook: large multimodal topic libraries) /
**hot pulse** (realtime hot-content capture: link → transcript → semantic recall).
Includes the 4-axis routing rubric (size / shelf-life / modality / recall frequency,
size wins conflicts), material-format priority (md > word/pdf/ppt > audio > video),
cost discipline, and field-tested pitfalls. Orthogonal to
`multiplatform-projection-protocol` (projection distributes the *same* content;
the spine homes *different kinds* of content).

### Added · team share slice (the distribution organ)

#### `references/team-share-slice.md` + `scripts/share_slice_export.py`
Tag-scoped (`share_group:` white-list, producer-decides), leak-guarded
(content-signature scan, **any hit aborts the whole export**), read-only private
GitHub slice that collaborators get by GitHub id and keep fresh with `git pull`.
Explicitly distinct from the v0.3 mirror: mirror = backup organ (whole vault, you
only); slice = distribution organ (tag scope, teammates). Script is stdlib-only,
dry-run by default, full-rebuild semantics so untagging a page takes it offline.
Field-tested guardrails baked in: patterns-not-literals in the guard file,
absolute paths only, scan scope limited to candidate files.

### Added · GitHub-connector bridge (read path for sandboxed Claude)

New section in `references/wiki-github-mirror-sync.md`: once the vault (mirror or
slice) is on GitHub, web Claude can read it through the built-in GitHub connector —
local vault → sync → connectors → authorize → topic-scoped context pull. Honest
labeling: the oft-quoted "2-3× better drafts" is classroom felt-sense, not a
benchmark. The bridge is a read path only; circles and leak-guard run before
anything reaches GitHub.

### Added · hot-layer intake adapter

#### `scripts/intake_getnote.py`
Renders agent-side semantic-recall results (JSON) into `sources/` stubs with
`circle: raw` + `truth_source` back-pointer, dry-run by default. Carries the
**large-integer note_id guardrail**: 19-digit ids passed as numbers get rounded
past 2^53 in float-coercing runtimes and the platform then reports "note not
found" — always recall semantically, always store ids as strings. Stubs are
volatile by contract: distill keepers into the index spine within 24h.

### Fixed
- Version drift: SKILL.md title said v0.1, README badge v0.2, frontmatter v0.3.0 — all aligned to v0.4.0
- SKILL.md references list was missing the three v0.2 references (5-layer / Karpathy / borrow-rubric) — restored

---

## [v0.3.0] — 2026-06-02

### Added · private GitHub mirror sync (the backup organ)

Answers the recurring question "does this skill auto-sync my Obsidian vault to
GitHub?" — previously *no*. Now there's an explicit, scoped backup capability,
kept carefully distinct from cross-circle promotion.

#### `scripts/wiki_git_mirror_sync.sh`
Scheduled, desensitized, whole-vault backup to a **private** GitHub mirror. Env-driven
(`WIKI_DIR / REPO_SLUG / EXPECTED_REMOTE_RE / PUSH_URL / BRANCH / LEAK_GUARD`).
Four safety gates enforced before every push:
- **Private-only** — `gh isPrivate` assertion + `origin` URL allowlist; aborts if the repo is/goes public
- **Leak guard** — runs an optional pre-push assertion (`LEAK_GUARD`); non-zero exit aborts
- **Never force** — `fetch` + `rebase` before push; history stays monotonic; rebase conflict ⇒ abort, ask a human
- **Single lock** — `mkdir` lock prevents overlapping scheduler runs
Headless-safe gh-credentialed https push (sidesteps the launchd-has-no-ssh-agent failure).

#### `references/wiki-github-mirror-sync.md`
The methodology: the **mirror ≠ promotion** boundary (backup is flat & whole-vault;
promotion stays human-gated per three-circles-protocol), the automation-rot 3-axis
model (cadence / transparency / recovery), the four gates, and launchd-vs-Actions
host choice (the writer is the laptop ⇒ launchd).

#### `templates/wiki-mirror.gitignore` + `templates/com.example.wiki-mirror-sync.plist.template`
Desensitization whitelist (blocklist default + strict-whitelist mode for public repos)
and a launchd timer template (2×/day, offset minutes, `RunAtLoad` off so the first big
commit happens under human eye).

### Fixed
- SKILL.md frontmatter `version` was stale at `v0.1` while CHANGELOG was at v0.2.0 — now aligned to v0.3.0.

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
