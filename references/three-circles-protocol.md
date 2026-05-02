---
title: 三圈记忆协议（G1 显式化 v0.1）
type: concept
domain: 原力OS
sources:
  - sentra-company-brain-part-2-2049877146936786944
related:
  - "[[yuanli-os-company-brain-overview]]"
  - "[[yuanli-os-company-brain]]"
  - "[[memory-layer-contract]]"
  - "[[force-os]]"
created: 2026-05-02
updated: 2026-05-02
audience: both
maturity: developing
circle: institutional
tags: [原力OS, company-brain, three-circles, governance, promotion-gate, G1]
---

# 三圈记忆协议（G1 显式化）

> **一句话定位**：把"个人圈 ≠ 共享圈 ≠ 机构圈"这条铁律，从 [[yuanli-os-company-brain-overview]] 的隐式心智模型，落实到**可被工具识别 + 可被 lint 报告 + 可被 promote 工具流转**的工程协议（Phase 2 v0.1）。

## TL;DR

- **三圈定义**：individual / shared / institutional + 两个逃生标签 raw / tooling
- **推断优先级**：frontmatter `circle:` 字段（最权威）→ 路径规则推断（fallback）→ unknown
- **工程实现**：`circle_inference` Python 库（`~/.claude/skills/yuanli-brain-surface/scripts/lib/circle_inference.py`）
- **Phase 2 不强制 frontmatter 全填**：1078 wiki concepts 仍按目录推断，新建/编辑时才写 explicit 字段
- **晋升 gate**：用 `promote_artifact.py` CLI，人在中间审 — AI 不自动跨圈
- **可见性**：wiki-lint L9 扩展按目录扫圈分布（报告，不强制）

---

## 1. 三圈定义（精确版）

### Individual · 个人圈

**装什么**：

- LLM-Wiki `insights/` 目录（人类只读 / AI 永不写 — 铁边界）
- 个人 `Clippings/` `Research/` `qin-xiao-ming/`
- `~/.claude/projects/<cwd>/memory/`（个人 CLAUDE memory pointer）
- 个人 Get 笔记本地导出
- `~/.claude/CLAUDE.md`（个人全局配置）

**铁律**：

- AI 永不主动写 `insights/`（已在 wiki schema 硬约束）
- 跨圈晋升必须人在中间过滤，不能 AI 自动同步
- 内容可能含未成形判断 / 私密 / 错误，**不可外泄**

### Shared · 共享圈

**装什么**：

- LLM-Wiki `operations/`（运维状态 / clones / runs / digests）
- LLM-Wiki `dashboards/` `tasks/` `minutes/` `copilot/`
- 飞书 base T01-T03 / T07 / T12 / T13（task / digest / 协同 / 克隆 / 用户行为）
- zsxq 项目空间
- 合作方 lark space
- `claude-harness/research/`（工程研究产物）

**特征**：

- 跨人但不是"对外宣称的真相"
- team / 学员 / 合作方协作时共用
- 可被 modify（区别于 institutional 的"只增不改"）

### Institutional · 机构圈

**装什么**：

- LLM-Wiki `concepts/` `entities/` `syntheses/` `comparisons/`
- LLM-Wiki `decisions/`（**Phase 3 G3 v0.1 新增** · 4 元组结构化决策记录：commitment / disagreement / counterfactual / decision_rationale）
- 飞书 T04 决策提案 / T05 决策记录 / T06 治理成熟度 / T08 知识概念索引 / T15 治理审查
- 已发布的公众号文章 / 原力星球长文
- GitHub 公开仓（橙皮书等）

**特征**：

- 作为"原力生态对外的真相"
- 带 provenance / permissions / freshness / ownership
- 决策只增不改（V18 架构决策铁律）

### Raw · 不在三圈

**装什么**：LLM-Wiki `sources/`（6108 文件）+ `artifacts/`

**特征**：不可变原始素材。是 L1 Factual Memory 的"原料层"，本身不属于三圈，但可被三圈引用。

### Tooling · 不在三圈

**装什么**：`scripts/` / `exports/` / `~/.claude/skills/` / `~/.claude/hooks/`

**特征**：工具 / 配置 / 脚本，不算"记忆"。

---

## 2. 推断规则（落实在 circle_inference.py）

### 2.1 wiki 内部目录规则

| 目录 | circle |
|---|---|
| `concepts/` `entities/` `syntheses/` `comparisons/` `decisions/` | institutional |
| `operations/` `dashboards/` `tasks/` `minutes/` `copilot/` `_factory/` | shared |
| `insights/` `Clippings/` `Research/` `qin-xiao-ming/` | individual |
| `sources/` `artifacts/` | raw |
| `scripts/` `exports/` | tooling |

### 2.2 wiki 之外的路径规则

| 路径 substring | circle |
|---|---|
| `/.claude/projects/` | individual |
| `/Documents/Get笔记/` `/get-biji/` | individual |
| `/yuanli-os-orange-book` | institutional（GitHub 公开） |
| `/claude-harness/research/` | shared |
| `/.claude/skills/` `/.claude/hooks/` | tooling |
| `/.claude/CLAUDE.md` | individual |
| `/.claude/settings*` | tooling |

### 2.3 优先级

```
1. frontmatter `circle: <value>` 字段（explicit · 最高优先）
2. 路径规则推断（inferred）
3. unknown（默认 fallback，建议显式声明）
```

---

## 3. 晋升 gate（promote-artifact 协议）

### 3.1 什么时候应当晋升

- **个人 → 共享**：某个个人笔记 / Get 转写对学员或合作方有协作价值
- **共享 → 机构**：某个共享决策成熟到该写为 wiki concept / 决策记录
- **机构 → 共享 / 个人**：**不允许直接降级**（只能标 stale / superseded / deprecated）

### 3.2 promote-artifact CLI 工作流

```
人类决定"这个笔记该升级"
    ↓
promote_artifact.py --source <path> --to-circle <target> --target-path <new path>
    ↓
工具产出 draft（含 frontmatter `circle:` + sources + 提取段落）
    ↓
人类审 draft（保留 / 剔除 / 改写哪些段落）
    ↓
确认写入目标圈
    ↓
源文件末尾追加 `> 已晋升至 [[<target>]]` reference
```

### 3.3 铁律护栏

- ❌ AI 不自动跨圈（即使 surface 召回了某条 individual 内容，也不主动 promote）
- ❌ 不允许 institutional → shared / individual 降级（只能 stale 标记）
- ✅ promotion event 应留 audit trail（Phase 2.5 上飞书 T07）

---

## 4. wiki-lint L9 扩展

按 [LLM-Wiki schema](_schema.md) 的 lint 体系，**新增 L9 检查**：

| 检查 | 内容 | 严重度 |
|---|---|---|
| L9 | 圈分布扫描 — 报告每目录 frontmatter 显式 circle 比例、推断 circle 分布、unknown 文件清单 | 💡 Suggestion |

L9 **不强制**所有文件填 `circle:`（避免大批量改 1078 个 concepts）。但会列出"推断为 unknown"的孤儿文件，让人补 frontmatter 或调推断规则。

---

## 5. Phase 2 v0.1 的工程实物

| 文件 | 作用 |
|---|---|
| `~/.claude/skills/yuanli-brain-surface/scripts/lib/circle_inference.py` | 推断库 + CLI |
| `~/.claude/skills/yuanli-brain-surface/scripts/promote_artifact.py` | 半自动晋升 CLI |
| `~/.claude/skills/yuanli-brain-surface/scripts/wiki_lint_l9.py` | 圈分布扫描 |
| `concepts/three-circles-protocol.md`（**本页**） | 协议文档 |

集成：

- `yuanli-brain-surface` skill 已升级显示每条 surface 命中的 circle 标签（让用户在 surface 时立刻看到圈属性）

---

## 6. 升级路径

### Phase 2.5

- ✅ Phase 2.5 v0.1：`promote_artifact.py` 已先写本地 `operations/logs/promotion_events.jsonl`（append-only），字段对齐 T07 `promotion_event`；真实飞书 API 同步留 bridge 层
- promote-artifact 升级为 skill（AI 帮生成 draft）

### Phase 3+（依赖 G3 提取层）

- 自动检测"个人笔记里的 commitment 片段"建议晋升

### Phase 4 (G5)

- role lens 渲染时按 circle 字段过滤可见性

---

## 7. 与现有协议的关系

| 协议 | 关系 |
|---|---|
| [[memory-layer-contract]] | 五层记忆模型（L0-L5）是个人级别；三圈是生态级别。**正交，不冲突** |
| [[yuanli-os-company-brain-overview]] §8 | 三圈在 4 类载体的可见性映射 |
| [[yuanli-os-company-brain]] (synthesis) | spec 视角的 G1 升级 spec（与本协议互为镜像） |
| LLM-Wiki [[_schema|_schema.md]] | wiki Layer 1/2/3 划分 — 三圈是 wiki Layer 的**生态级扩展** |

---

## 8. 一句话收束

> **个人圈是产生地，共享圈是协作地，机构圈是真相地。三者不能混淆，但必须有显式的、人在中间过滤的晋升通道。**
>
> Phase 2 v0.1 把这条铁律落实到工具层 — `circle_inference` 看圈，`promote_artifact` 跨圈，wiki-lint L9 报圈，`/yuanli-brain-surface` 用圈。
