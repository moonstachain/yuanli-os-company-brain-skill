#!/bin/bash
# wiki_git_mirror_sync.sh — back up an Obsidian-class vault to a PRIVATE GitHub mirror
# ─────────────────────────────────────────────────────────────────────────────
# Part of the Yuanli-OS Company Brain skill. This is the *backup/mirror* organ —
# it is NOT cross-circle promotion. Promotion between INDIVIDUAL → SHARED →
# INSTITUTIONAL is human-gated by design (see references/three-circles-protocol.md).
# This script only snapshots the whole vault, as-is, to a private git remote so a
# disk failure never loses your brain. Two different concerns; do not conflate them.
#
# Safety contract (each enforced before any push):
#   1. PRIVATE-ONLY  — asserts the target repo is private (gh) AND the remote URL
#      matches an allowlist. A vault holds PII/consulting data; a public push leaks it.
#   2. LEAK GUARD    — runs an optional pre-push assertion script (e.g. to keep a
#      sensitive sub-tree out of the mirror). Non-zero exit aborts the push.
#   3. NEVER FORCE   — fetch + rebase before push; history stays monotonic. A mirror
#      backup must never rewrite remote history.
#   4. SINGLE LOCK   — mkdir lock prevents overlapping scheduler runs.
#   5. TIMESTAMPED LOG — every run is auditable; failure exits non-zero so the
#      scheduler records it (transparency axis — silent rot is the real failure mode).
#
# Configure via environment (or edit the defaults below):
#   WIKI_DIR        (required)  absolute path to the vault / git repo
#   REPO_SLUG       (optional)  "owner/name" for the gh isPrivate assertion
#   EXPECTED_REMOTE_RE (optional) ERE the `origin` URL must match (defaults from REPO_SLUG)
#   PUSH_URL        (optional)  explicit https push URL (defaults to origin)
#   BRANCH          (optional)  default: main
#   LEAK_GUARD      (optional)  path to a pre-push assertion script (exit≠0 ⇒ abort)
#   GH_HTTPS_PUSH   (optional)  "1" ⇒ push over https using gh credentials (headless-safe)
#
# Usage:  WIKI_DIR=~/vault REPO_SLUG=me/my-wiki LEAK_GUARD=~/vault/scripts/guard.sh \
#           bash wiki_git_mirror_sync.sh
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail   # deliberately not -e: control each step, log failures, don't die silently

WIKI_DIR="${WIKI_DIR:?set WIKI_DIR to the vault path}"
BRANCH="${BRANCH:-main}"
REPO_SLUG="${REPO_SLUG:-}"
PUSH_URL="${PUSH_URL:-}"
LEAK_GUARD="${LEAK_GUARD:-}"
GH_HTTPS_PUSH="${GH_HTTPS_PUSH:-1}"
LOG="${LOG:-$WIKI_DIR/_log-git-mirror.log}"     # add *.log to .gitignore so it never self-dirties
LOCK="${LOCK:-/tmp/wiki-git-mirror-$(echo "$WIKI_DIR" | md5sum 2>/dev/null | cut -c1-8 || echo x).lock}"
# Default the remote allowlist from the slug if not given.
if [ -z "${EXPECTED_REMOTE_RE:-}" ] && [ -n "$REPO_SLUG" ]; then
  EXPECTED_REMOTE_RE="github\.com[:/]${REPO_SLUG}(\.git)?$"
fi

log(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

if ! mkdir "$LOCK" 2>/dev/null; then
  log "SKIP: another instance is running ($LOCK)."; exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

cd "$WIKI_DIR" || { log "FATAL: cannot cd into $WIKI_DIR"; exit 1; }
log "──── run start ($WIKI_DIR) ────"

remote_url=$(git remote get-url origin 2>/dev/null || echo "")
[ -z "$PUSH_URL" ] && PUSH_URL="$remote_url"

# ── Assert 1: remote allowlist ──────────────────────────────────────────────
if [ -n "${EXPECTED_REMOTE_RE:-}" ]; then
  if ! echo "$remote_url" | grep -qE "$EXPECTED_REMOTE_RE"; then
    log "ABORT[1]: origin ($remote_url) is not on the allowlist. Refusing to push."; exit 1
  fi
fi

# ── Assert 2: repo must be PRIVATE (best-effort via gh) ─────────────────────
if [ -n "$REPO_SLUG" ] && command -v gh >/dev/null 2>&1; then
  vis=$(gh repo view "$REPO_SLUG" --json isPrivate -q .isPrivate 2>/dev/null || echo "")
  if [ "$vis" = "false" ]; then
    log "ABORT[2]: $REPO_SLUG is PUBLIC — a vault holds private data. Refusing to push."; exit 1
  elif [ "$vis" = "true" ]; then
    log "OK[2]: visibility PRIVATE verified."
  else
    log "WARN[2]: gh returned empty; falling back to URL allowlist only."
  fi
fi

# ── Assert 3: pre-push leak guard (optional but recommended) ────────────────
if [ -n "$LEAK_GUARD" ]; then
  if [ -x "$LEAK_GUARD" ] || [ -f "$LEAK_GUARD" ]; then
    if ! guard_out=$(bash "$LEAK_GUARD" 2>&1); then
      log "ABORT[3]: leak guard failed → $guard_out"; exit 1
    fi
    log "OK[3]: leak guard passed."
  else
    log "ABORT[3]: LEAK_GUARD set but not found ($LEAK_GUARD)."; exit 1
  fi
fi

# ── Stage + commit ──────────────────────────────────────────────────────────
git add -A 2>>"$LOG"
if git diff --cached --quiet; then
  log "CLEAN: no new changes."
else
  n=$(git diff --cached --name-only | wc -l | tr -d ' ')
  msg="chore(mirror): auto-sync $(date '+%Y-%m-%d %H:%M') (${n} files)"
  git commit -m "$msg" >>"$LOG" 2>&1 && log "COMMIT: $msg" || log "WARN: commit produced nothing."
fi

# ── Fetch + rebase (merge, never overwrite; never --force) ──────────────────
git fetch origin "$BRANCH" >>"$LOG" 2>&1 || log "WARN: fetch failed; still attempting push."
if git rev-parse "origin/$BRANCH" >/dev/null 2>&1; then
  if ! git rebase "origin/$BRANCH" >>"$LOG" 2>&1; then
    log "ABORT[4]: rebase conflict; needs a human. Auto rebase --abort."; git rebase --abort >>"$LOG" 2>&1; exit 1
  fi
fi

# ── Push (gh-credentialed https is headless-safe; never --force) ────────────
if [ "$GH_HTTPS_PUSH" = "1" ] && command -v gh >/dev/null 2>&1 && echo "$PUSH_URL" | grep -q '^https'; then
  push_cmd=(git -c credential.helper='!gh auth git-credential' push "$PUSH_URL" "$BRANCH")
else
  push_cmd=(git push origin "$BRANCH")
fi
if "${push_cmd[@]}" >>"$LOG" 2>&1; then
  log "PUSH OK: $BRANCH @ $(git rev-parse --short HEAD) → private mirror."; log "──── run ok ────"; exit 0
else
  log "ERROR: push failed (see git output above)."; exit 1
fi
