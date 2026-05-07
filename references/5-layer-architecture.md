# 5-Layer Company Brain Architecture · v0.1

> Hosting-aware, locality-first architecture for personal/team company brain.
> Distilled from real implementation 2026-05-07 → 2026-05-08.

---

## TL;DR

Don't pick "one platform". Pick **layers**, give each layer the host that's strongest at its job.

```
┌─────────────────────────────────────────────────────────────┐
│ L4 · ACTION LAYER     · Task system / IM bot / Calendar     │
└──────────────▲──────────────────────────────────────────────┘
               │ Seam #4: Action ← Recall (writeback)
┌──────────────┴──────────────────────────────────────────────┐
│ L3 · RECALL LAYER     · Right-time surface (hook + bot)     │
└──────────────▲──────────────────────────────────────────────┘
               │ Seam #3: Recall ← Memory (vector + symbol)
┌──────────────┴──────────────────────────────────────────────┐
│ L2 · PROMOTION LAYER  · L0→L4 distillation (cron + agents)  │
└──────────────▲──────────────────────────────────────────────┘
               │ Seam #2: Promotion → Memory (event log)
┌──────────────┴──────────────────────────────────────────────┐
│ L1 · MEMORY LAYER     · 3 sub-layers (symbol/vector/active) │
│  Symbol: GitHub-mirrored markdown + AI entry compression    │
│  Vector: local ChromaDB + agentdb (semantic recall)         │
│  Active: collaboration base (multi-user accessible)         │
└──────────────▲──────────────────────────────────────────────┘
               │ Seam #1: Memory ← Intake (frontmatter schema)
┌──────────────┴──────────────────────────────────────────────┐
│ L0 · INTAKE LAYER     · Multi-source adapters (5+ channels) │
│  Conversations / meeting transcripts / clipboard / mail /   │
│  domain dashboards / GitHub activity / etc.                 │
└─────────────────────────────────────────────────────────────┘
```

## Three Architecture Principles

### 1. Locality first

Place data **near its primary user**:

| Asset class | Primary user | Best host | Why |
|---|---|---|---|
| Markdown source-of-truth | You (deep reading + edit) | Local Obsidian + GitHub mirror | git history = audit, OB = edit surface |
| Vector store | LLM (semantic recall) | Local ChromaDB / agentdb | low latency, privacy |
| Tasks / commitments | You + team (multi-user) | Collaboration base (Feishu / Notion / Linear) | already where humans work |
| Cron · needs Mac resources | Local | launchd | credential-locality (keychain access) |
| Cron · pure cloud API | Cloud | GitHub Actions | free + secrets manager |
| Notifications | You (mobile) | IM bot (Lark / Slack) | already on phone |
| Static dashboard | Public/team | Vercel / GitHub Pages | zero-cost start |
| Large media | Anyone | S3-class object store | scale + cdn |

**Anti-pattern**: forcing everything into one platform "for simplicity". You'll pay for it in capability mismatch.

### 2. Credential adjacency

Any code path must be ≤1 hop from its required credentials:
- Mac local cron → keychain (≤1 hop)
- GitHub Actions → GitHub Secrets (0 hop)
- Local Claude Code → ~/.local/share keychain (1 hop)

If you find yourself shuttling credentials through 3+ layers, you're crossing a seam wrong.

### 3. Failure radius

Each layer must fail independently:
- L0 channel dies → other channels keep flowing data
- L1 vector store dies → symbol layer still readable
- L2 cron fails → manual catchup possible
- L3 hook fails → fall back to active query
- L4 IM bot dies → email/calendar fallback

**Test**: kill any one cron; rest of system should keep working. If not, your layers are too coupled.

---

## The 4 Seams (this is the hard part)

| Seam | Upstream → Downstream | Data shape | Owner | Example artifact |
|---|---|---|---|---|
| #1 Intake → Memory | L0 → L1 | Markdown + strict frontmatter schema | wiki-lint + schema_system | `wiki/sources/<channel>/<date>-<slug>.md` |
| #2 Memory → Promotion | L1 → L2 | jsonl event stream | bridge-log governance | `_bridge-log.jsonl` |
| #3 Memory → Recall | L1 → L3 | Vector + symbol dual query | brain-surface skill | `yuanli-brain-surface` (this skill v0.1) |
| #4 Recall → Action | L3 → L4 | Writeback to base + IM | feishu-bitable-bridge or equivalent | T01 task creation |

**First principle**: any cross-layer data flow goes through a seam **explicitly**. No direct cross-layer reads/writes.

This is what allows the deletion test (kill any layer, rest works).

---

## Anti-pattern: "the dashboard trap"

Don't build a dashboard before L0-L4 are connected.

Dashboards are visualization, not the system. A dashboard with no underlying flowing data is a museum exhibit.

Real ROI sequence:
1. L0 intake working
2. L2 promotion producing L4 entries
3. L3 recall actually invoked at decision time
4. L4 writeback closing the loop
5. **THEN** dashboard

If you skip to dashboard, you'll discover months later that no data is flowing and you've optimized a number that never moves.

---

## Real-world hosting matrix (what hosts what)

| Asset | Aliyun | GitHub | OB | Lark/Notion | Local | Vercel | **Best** |
|---|---|---|---|---|---|---|---|
| Markdown source-of-truth | ❌ | ✅ | ⚠️ edit surface | ❌ | ⚠️ | ❌ | **GitHub mirror + OB edit** |
| Vector store | ⚠️ ECS | ❌ | ❌ | ❌ | ✅ | ❌ | **Local** |
| Task ledger | ❌ | ⚠️ Issues | ❌ | ✅ | ❌ | ❌ | **Collab base** |
| Cron · Mac-resource | ❌ | ❌ | ❌ | ❌ | ✅ launchd | ❌ | **launchd** |
| Cron · cloud API | ✅ | ✅ Actions | ❌ | ❌ | ⚠️ | ❌ | **GitHub Actions** |
| Secrets | ✅ KMS | ✅ Secrets | ❌ | ⚠️ | ⚠️ keychain | ⚠️ env | **GitHub Secrets + keychain** |
| Large media | ✅ OSS | ⚠️ LFS | ⚠️ vault | ✅ Drive | ⚠️ | ❌ | **OSS-class** |
| Notifications | ❌ | ❌ | ❌ | ✅ IM bot | ❌ | ❌ | **IM bot** |
| Static dashboard | ✅ OSS+CDN | ✅ Pages | ⚠️ embed | ⚠️ mini-app | ⚠️ self | ✅ | **Pages → Vercel** |
| LLM inference | ✅ DashScope | ✅ Actions | ❌ | ❌ | ✅ Claude Code | ❌ | **Mix: interactive + batch** |
| Code/PR | ❌ | ✅ | ❌ | ⚠️ | ❌ | ❌ | **GitHub** |

One-liner:
> **GitHub = hub · base = action · local = compute · OSS = vault · OB = edit · Vercel = public face**

Each platform owns the ONE box it's strongest at. No platform tries to own everything.

---

## When to upgrade this architecture

Trigger lines (re-architect when crossed):

| Trigger | Re-eval |
|---|---|
| 3rd full-time collaborator joins | Team-grade tooling: Lark Suite, Linear, etc. |
| Local Mac CPU saturating on cron | Move LLM batch to cloud (Actions / DashScope batch) |
| ChromaDB > 5 GB | Pinecone / Qdrant cloud |
| Markdown > 10 GB | Git LFS + S3 sidecar |
| Multi-region team | Active-active base + cloud vector store |

Below these triggers, the locality-first design wins on cost + privacy + simplicity.
