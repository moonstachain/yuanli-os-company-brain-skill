# Reference · Wiki → GitHub Private Mirror Sync

**What it is**: an automated, scheduled, *desensitized* backup of an Obsidian-class
vault to a **private** GitHub repo, so a disk failure never loses your brain.

**What it is NOT**: cross-circle promotion. Promotion (INDIVIDUAL → SHARED →
INSTITUTIONAL) is human-gated by design — see
[three-circles-protocol.md](three-circles-protocol.md). The mirror is a flat,
whole-vault snapshot with the producer's circle boundaries already baked into the
files; it does not move anything between circles. **Two different concerns; never
conflate them.** A skill that "auto-syncs the whole vault to git" is a *backup*, and
a skill that "auto-promotes notes into the shared record" is a *governance
violation*. This reference is only about the first.

Runtime: [`../scripts/wiki_git_mirror_sync.sh`](../scripts/wiki_git_mirror_sync.sh).
Templates: [`wiki-mirror.gitignore`](../templates/wiki-mirror.gitignore),
[`com.example.wiki-mirror-sync.plist.template`](../templates/com.example.wiki-mirror-sync.plist.template).

---

## Why most "git-backup my vault" attempts rot

The repo gets created, a few manual `git push`es happen, then it silently stops —
weeks later you discover the last push was 10 days and 1000 commits ago. This is the
**automation-rot pattern**: the failure is never a crashed cron, it's one of three
axes going quiet —

| Axis | Failure | Fix in this design |
|---|---|---|
| **Cadence** | pushes are manual → they stop | launchd timer, 2×/day |
| **Transparency** | no log → you can't tell it stopped | timestamped `_log-git-mirror.log`, non-zero exit on failure |
| **Recovery** | no one-button manual run | the script is hand-runnable any time |

Before adding any of this, verify the *real* state first (don't assume the cron is
dead): `git -C <vault> status -sb`, `git log -1`, `gh repo view <slug> --json pushedAt`,
and `launchctl list | grep <label>`. The rot is usually "manual sync was never
automated," not "the job crashed."

---

## The four safety gates (all enforced before any push)

1. **PRIVATE-ONLY.** A vault holds PII / client / consulting data. The script
   asserts the target is private two independent ways: `gh repo view --json isPrivate`
   *and* an `origin` URL allowlist (`EXPECTED_REMOTE_RE`). If the repo ever flips to
   public, the next run aborts instead of leaking. **Choosing a private repo is what
   makes the whole-vault mirror safe** — it collapses the PII exposure question.

2. **Desensitization layer.** Two models in [`wiki-mirror.gitignore`](../templates/wiki-mirror.gitignore):
   - *Blocklist* (default for a private full-vault backup): mirror everything except
     secrets, volatile junk, and a **named sensitive sub-tree**.
   - *Strict whitelist*: ignore everything, un-ignore only allowed paths. Switch to
     this the moment the repo is or might become public.
   For a sub-tree that must **never** leave the machine (e.g. a pack of client PII),
   don't rely on `.gitignore` alone — back it with a **pre-push assertion** (see gate 3).

3. **Leak guard (defense in depth).** `.gitignore` is a filter; an assertion is a
   tripwire. Point `LEAK_GUARD` at a script that exits non-zero if any forbidden path
   is tracked or staged, and the sync aborts the push. A `.gitignore` line can be
   deleted by accident; an assertion that *also checks the `.gitignore` line is still
   present* cannot be silently defeated. Example shape:
   ```bash
   # abort if anything under the sensitive sub-tree is tracked/staged,
   # OR if the .gitignore exclusion line was removed
   git ls-files -- 'clients/' | grep -q . && { echo "LEAK: clients/ tracked"; exit 1; }
   grep -qE '^clients/' .gitignore || { echo "LEAK: .gitignore exclusion missing"; exit 1; }
   ```

4. **Never force; merge, don't overwrite.** A mirror must keep history monotonic.
   The script does `fetch` + `rebase` before push and **never** `--force`. If a rebase
   conflicts it aborts and asks for a human rather than clobbering the remote. (Single
   machine = single writer, so this is normally a no-op — but the guard is what saves
   you the one time a second device pushed.)

Plus: a `mkdir` lock so overlapping scheduler fires can't race.

---

## Host choice: launchd vs GitHub Actions

| | launchd (local) | GitHub Actions |
|---|---|---|
| **Use when** | the vault lives only on this Mac; push is *out* of the machine | the vault is already in git and you want cloud-side scheduled tasks |
| **Credentials** | gh token / ssh key on the machine (≤1 hop) | GitHub Secrets (0 hop) |
| **Limit** | Mac must be awake | can't *read* a local-only vault |

For a local Obsidian vault → private mirror, the writer is the laptop, so **launchd is
correct**. Actions can't see files that never left your disk. (This mirrors the
hosting decision matrix in [5-layer-architecture.md](5-layer-architecture.md): pick
the host adjacent to where the data and credentials already live.)

Headless reliability tip: pushing over **gh-credentialed https**
(`git -c credential.helper='!gh auth git-credential' push https://github.com/<slug>.git`)
avoids the "launchd has no ssh-agent" failure that bites ssh-remote pushes.

---

## Install (≈5 minutes)

```bash
# 1. desensitization layer
cp templates/wiki-mirror.gitignore  <vault>/.gitignore      # then customize the sub-tree block
# 2. (recommended) a leak-guard for your sensitive sub-tree
$EDITOR <vault>/scripts/assert-no-leak.sh && chmod +x <vault>/scripts/assert-no-leak.sh
# 3. FIRST run by hand — watch the initial commit
WIKI_DIR=<vault> REPO_SLUG=<owner/name> LEAK_GUARD=<vault>/scripts/assert-no-leak.sh \
  bash scripts/wiki_git_mirror_sync.sh
# 4. schedule it
cp templates/com.example.wiki-mirror-sync.plist.template \
   ~/Library/LaunchAgents/com.<you>.wiki-mirror-sync.plist   # fill in <…> placeholders
launchctl load ~/Library/LaunchAgents/com.<you>.wiki-mirror-sync.plist
launchctl list | grep wiki-mirror
```

Verify it's real (don't trust "it loaded"): run the script twice — the second run
should be a `CLEAN` / `Everything up-to-date` no-op — and confirm `gh repo view <slug>
--json pushedAt` moved. That's the verified-level check from
[borrow-rubric-3-tier.md](borrow-rubric-3-tier.md): "cron is loaded" ≠ "cron fired
with real data."

---

## Bridge: letting sandboxed Claude read the vault via GitHub connector

A side benefit of having the vault on GitHub (mirror or [share slice](team-share-slice.md)):
**web Claude (claude.ai), which runs in a managed sandbox and cannot see your disk,
can read it through the built-in GitHub connector.** Path:

```
local vault → mirror/slice sync to GitHub → claude.ai → Settings/customize
            → Connectors → GitHub → authorize → name a topic in chat
            → Claude pulls the relevant pages as context
```

When to use which surface:

| Surface | Strength | Reads your vault via |
|---|---|---|
| Claude Code (local) | scripts, lint, grep-verified quotes | filesystem directly |
| web Claude + GitHub connector | long-form drafting / polishing with your knowledge loaded | the GitHub mirror |

Field observation (teaching sessions, 2026-06): users report noticeably better
drafts when web Claude has the synced vault connected versus a bare chat —
anecdotally described as a 2-3× quality jump. **That figure is classroom felt-sense,
not a measured benchmark**; treat it as "clearly better", nothing more precise.

Boundaries:

- This bridge is a **read path** for an existing mirror — it does not change what
  may be mirrored. The three-circles rules and the leak-guard run *before* anything
  reaches GitHub; the connector only ever sees what already passed those gates.
- Syncing and connector reads both consume tokens/quota. Keep the sync scheduled
  (not per-edit), and connect the repo only when doing knowledge-heavy work.
- If collaborators should get this too, point them at a [share slice](team-share-slice.md)
  repo, not at your backup mirror (the mirror contains your individual circle).
