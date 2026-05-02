---
title: Typed Relationships Schema
type: concept
domain: 原力OS
created: 2026-05-02
updated: 2026-05-02
revision: v0.1
maturity: developing
audience: both
related:
  - "[[yuanli-os-company-brain-overview]]"
  - "[[three-circles-protocol]]"
  - "[[_schema]]"
tags: [原力OS, company-brain, typed-relationships, schema, context-graph, G2]
---

# Typed Relationships Schema

> **一句话定位**：`relationships:` 是企业大脑 G2 的最小 typed edges 协议：在不做 mass migration 的前提下，让 wiki page 可以表达「谁承诺了什么、谁拥有它、什么阻塞什么、它从哪里来、它替代了什么、它支持什么」。

## 0. Scope

本 schema 只定义最小可用字段，不要求全库迁移。

- **写入范围**：优先用于 institutional / shared 层的 `concepts/`, `entities/`, `operations/` 页面。
- **不做**：不改脚本、不批量重写旧笔记、不要求每个 wikilink 都变成 typed edge。
- **关系方向**：每条 relation 都是从**当前文件**指向 `target` 的 outgoing edge。
- **初始 relation type 只允许 6 个**：`commits-to`, `owns`, `blocks`, `derives-from`, `supersedes`, `supports`。

## 1. Minimal YAML field

在任意 wiki page frontmatter 中添加：

```yaml
relationships:
  - type: supports
    target: "[[some-target-note]]"
    evidence:
      - "[[source-or-decision-note]]"
    status: active
    note: "为什么这条关系成立的一句话说明"
```

### Required fields

| Field | Type | Required | Rule |
|---|---|---:|---|
| `type` | enum | yes | Must be exactly one of the 6 initial relation types. |
| `target` | wikilink string | yes | A single Obsidian wikilink string, e.g. `"[[note-name]]"` or `"[[folder/note-name]]"`. |
| `evidence` | list of wikilink strings | yes | One or more provenance links: source, decision, meeting note, task, transcript, or current concept. |

### Optional fields

| Field | Type | Default | Rule |
|---|---|---|---|
| `status` | enum | `active` | `proposed`, `active`, `stale`, `archived`. |
| `since` | date | unset | First known date the relationship became true. |
| `until` | date | unset | End date when relationship is no longer true. |
| `confidence` | enum | unset | `low`, `medium`, `high`; use only when evidence is indirect. |
| `note` | string | unset | Short human-readable reason; keep under one sentence. |

## 2. Relation type semantics

| Type | Direction from current note | Use when | Example meaning |
|---|---|---|---|
| `commits-to` | current note -> commitment / task / outcome | A person, team, project, or decision creates an obligation to deliver or maintain something. | `[[partner-A]] commits-to [[joint-launch-commitment]]`. |
| `owns` | current note -> artifact / project / decision / commitment | Current note has accountable ownership of the target. | `[[liming]] owns [[yuanli-os-company-brain-overview]]`. |
| `blocks` | current note -> blocked target | Current note prevents target from progressing until resolved. | `[[missing-owner]] blocks [[right-time-surface-rollout]]`. |
| `derives-from` | current note -> upstream source / parent concept / prior decision | Current note is based on or extracted from the target. | `[[typed-relationships-schema]] derives-from [[yuanli-os-company-brain-overview]]`. |
| `supersedes` | current note -> older target | Current note replaces the target as the preferred reference. | `[[new-policy-v2]] supersedes [[old-policy-v1]]`. |
| `supports` | current note -> claim / project / decision / outcome | Current note strengthens, evidences, or enables the target without owning it. | `[[three-circles-protocol]] supports [[yuanli-os-company-brain-overview]]`. |

### Direction test

Read every relationship as:

```text
CURRENT_FILE --type--> TARGET
```

If that sentence sounds backwards, move the relationship to the other note or choose a different type.

## 3. Frontmatter examples

### 3.1 Concept supports a roadmap gap

```yaml
---
title: Typed Relationships Schema
type: concept
domain: 原力OS
relationships:
  - type: supports
    target: "[[yuanli-os-company-brain-overview]]"
    evidence:
      - "[[yuanli-os-company-brain-overview]]"
    status: active
    since: 2026-05-02
    note: "Provides the minimal G2 typed edges schema referenced by the company brain roadmap."
---
```

### 3.2 Decision commits to a task

```yaml
---
title: Right-time Surface v0.2 Decision
type: decision
relationships:
  - type: commits-to
    target: "[[operations/tasks/right-time-surface-poc]]"
    evidence:
      - "[[operations/decisions/right-time-surface-v0-2-decision]]"
    status: active
    since: 2026-05-02
    note: "Decision creates a delivery commitment for the PoC."
---
```

### 3.3 Person owns a project and blocks another item

```yaml
---
title: Example Operator
type: entity
relationships:
  - type: owns
    target: "[[entities/projects/company-brain-g2]]"
    evidence:
      - "[[operations/decisions/g2-owner-assignment]]"
    status: active
  - type: blocks
    target: "[[entities/projects/typed-edge-dashboard]]"
    evidence:
      - "[[operations/runs/2026-05-02-g2-planning]]"
    status: proposed
    note: "Dashboard should wait until the six relation types are stable."
---
```

### 3.4 New schema supersedes an older note

```yaml
---
title: Typed Relationships Schema v0.2
type: concept
relationships:
  - type: supersedes
    target: "[[typed-relationships-schema]]"
    evidence:
      - "[[operations/decisions/typed-relationships-v0-2-approval]]"
    status: active
    since: 2026-06-01
---
```

## 4. Validation rules

### Hard errors

1. `relationships` must be a YAML list when present.
2. Every item must have `type`, `target`, and `evidence`.
3. `type` must be exactly one of:
   - `commits-to`
   - `owns`
   - `blocks`
   - `derives-from`
   - `supersedes`
   - `supports`
4. `target` must be a single quoted wikilink string beginning with `[[` and ending with `]]`.
5. `evidence` must be a non-empty list of quoted wikilink strings.
6. Do not encode multiple targets in one relationship. Use one list item per target.
7. Do not invent inverse or catch-all relation types in this minimal version.

### Warnings

1. `commits-to` should usually have an `owns` relationship somewhere on the commitment, project, or accountable actor page.
2. `blocks` should include `status` and a short `note` explaining the blocker.
3. `supersedes` should normally imply the old target is stale, but do not auto-edit the old target unless explicitly asked.
4. `derives-from` should point to the strongest upstream source, not every source ever used.
5. `supports` is not a generic backlink. Use it only when the support claim is meaningful and evidenced.

### Review checklist before adding a relation

- Can I read it as `current file --type--> target`?
- Is there at least one evidence link?
- Is the relationship institutional/shared enough to deserve typed memory?
- Am I adding only the relation I need, not migrating nearby notes opportunistically?

## 5. Dataview snippets

### 5.1 All typed relationships

```dataview
TABLE file.link AS Source, r.type AS Type, r.target AS Target, r.status AS Status, r.evidence AS Evidence, r.note AS Note
FROM "concepts" OR "entities" OR "operations"
WHERE relationships
FLATTEN relationships AS r
SORT r.type ASC, file.name ASC
```

### 5.2 Invalid relation types

```dataview
TABLE file.link AS Source, r.type AS InvalidType, r.target AS Target
FROM "concepts" OR "entities" OR "operations"
WHERE relationships
FLATTEN relationships AS r
WHERE !contains(["commits-to", "owns", "blocks", "derives-from", "supersedes", "supports"], r.type)
SORT file.name ASC
```

### 5.3 Missing required fields

```dataview
TABLE file.link AS Source, r.type AS Type, r.target AS Target, r.evidence AS Evidence
FROM "concepts" OR "entities" OR "operations"
WHERE relationships
FLATTEN relationships AS r
WHERE !r.type OR !r.target OR !r.evidence
SORT file.name ASC
```

### 5.4 Active blockers

```dataview
TABLE file.link AS Blocker, r.target AS Blocked, r.evidence AS Evidence, r.note AS Why
FROM "concepts" OR "entities" OR "operations"
WHERE relationships
FLATTEN relationships AS r
WHERE r.type = "blocks" AND (r.status = "active" OR !r.status)
SORT file.mtime DESC
```

### 5.5 Commitments and owners review

```dataview
TABLE file.link AS Source, r.type AS Type, r.target AS Target, r.status AS Status, r.evidence AS Evidence
FROM "concepts" OR "entities" OR "operations"
WHERE relationships
FLATTEN relationships AS r
WHERE contains(["commits-to", "owns"], r.type)
SORT r.target ASC, r.type ASC
```

### 5.6 Superseded knowledge candidates

```dataview
TABLE file.link AS Newer, r.target AS Older, r.evidence AS Evidence, r.since AS Since
FROM "concepts" OR "entities" OR "operations"
WHERE relationships
FLATTEN relationships AS r
WHERE r.type = "supersedes"
SORT r.since DESC, file.name ASC
```

## 6. Adoption protocol

1. Start with new or actively edited institutional notes only.
2. Add 1-3 high-signal relationships per page; avoid relationship spam.
3. Prefer `evidence` over confidence theater: no evidence means no typed edge.
4. When unsure between a plain wikilink and a typed relationship, use a plain wikilink first.
5. Revisit the six-type enum only after repeated real examples prove a missing relation class.

## 7. Relationship to G2

This schema is the minimal version of G2 typed edges for the company brain. It makes the context graph queryable without forcing the whole vault into a database model. Later automation may add freshness, conflict, orphan detection, and visualization, but those are consumers of this field, not requirements for v0.1.

## 8. "真够" 阈值 (G2 closure threshold)

> 加入背景：2026-05-02 诚实成熟度审计扣"主题层 · 停止条件 = 1"（"什么算 G2 真的够了" 没定义）。本节回应。

G2 typed edges gap 视为 **真闭环**（不只是"骨架完成"）当且仅当**全部三条**满足：

| 维度 | 阈值 | 现状（2026-05-02） | 测量方法 |
|---|---|---|---|
| explicit relationships pages | **≥ 5** | 1（仅本 schema 自己作为 example） | `grep -rl "^relationships:" concepts/ syntheses/ entities/ decisions/` |
| decisions 文件数（非 draft 非 _example） | **≥ 5** | 2 | `ls decisions/*.md \| grep -v draft \| grep -v _example` |
| typed edges 总数（explicit + derived） | **≥ 20** | 7（全 derived） | `python3 ~/.claude/skills/yuanli-brain-surface/scripts/relationship_graph.py --stats` |

### Decision rule

- 三条**全部**通过 → G2 closure ✅，可宣布"真够"
- 任一未达 → G2 仍处 "scaffold complete" 阶段，**不要**对外宣布 G2 闭环

### Failure mode（如果 explicit 永远不增长）

如果 7 日 / 30 日观察期后 `explicit relationships pages` 仍 = 1：

1. 触发 root-cause 检查 — 是用户写作流没经过 typed edges 思考，还是 schema 太重 / 6 类不够？
2. 候选 fallback：
   - **A**：降低 schema 严格度（让简单 wikilink 也算半个 typed edge）
   - **B**：让 brain-surface skill 自动建议 1-2 条 typed edge 写入提示
   - **C**：放弃 explicit-only 的目标，正式承认派生层就够（重写本节阈值）

不要默认走 C — 派生层永远不能表达"未来承诺" / "正在 block" / "已被 supersede" 这类时态信息。

### 复测协议

`/schedule` 一个 7 日后的 closure-evolution agent，读本节阈值跑复测，把结果写入 `_log.md` "phase5-7day-recheck" 章节。
