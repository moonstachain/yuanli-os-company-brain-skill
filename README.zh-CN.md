# 原力OS 公司大脑 · Skill

> 在任意 Obsidian 类 wiki + Claude Code skills 之上，搭建一个 Sentra 式的「公司大脑（Company Brain）」。

[English version →](README.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status: experimental](https://img.shields.io/badge/status-experimental-orange.svg)]()
[![v0.2](https://img.shields.io/badge/version-v0.2-blue.svg)]()

## 这是什么

一个经过提炼、带有明确立场的 skill，能把那些「数据很多、但记忆很差」的个人 / 团队 wiki，变成一张**可查询的上下文关系图谱**。包含以下能力：

**v0.1 核心功能（2026-05-02）**：

- **适时浮现（Right-time surface）** —— 在你产出任何重要内容之前，自动召回相关的概念 / 任务 / 草稿（而不是等你回头去手动搜索）。
- **三圈边界（Three-circle boundaries）** —— 把知识明确分成 `个人 / 共享 / 机构`（individual / shared / institutional）三圈，并设置「晋升关卡（promotion gate）」。
- **带类型的关系（Typed relationships）** —— 6 种固定关系：`commits-to（承诺）/ owns（拥有）/ blocks（阻塞）/ derives-from（衍生自）/ supersedes（取代）/ supports（支撑）`。只有这 6 种枚举，没有反向关系，也没有「其他」这种万能兜底。
- **反幻觉四元组提取器（Anti-hallucination 4-tuple extractor）** —— 把会议逐字稿提取成 `承诺 / 分歧 / 反事实 / 决策理由`（commitments / disagreements / counterfactuals / decision_rationale）四类，每一条都**必须附带原文引用（source_quote）**，并用 grep 做验证。
- **双轴成熟度评分表（Dual-axis maturity rubric）** —— 把**骨架成熟度（满分 60 分）**和**使用成熟度（满分 10 分）**分开打分，专门用来戳穿那种「自我感觉良好」的乐观自评。
- **24 小时复评协议（24h re-score protocol）** —— 任何「我做完了」的宣称，都必须在 24 小时内用硬证据重新打一次分。

**v0.2 新增功能（2026-05-08）**：

- **五层架构（5-layer architecture）** —— L0 摄入 → L1 记忆（符号 / 向量 / 活跃）→ L2 晋升 → L3 召回 → L4 行动，配 4 处明确的跨层接缝（cross-layer seam）+ 一张「托管选型决策矩阵」（[详情](references/5-layer-architecture.md)）。
- **借鉴评分表 · 三档纪律（Borrow rubric · 3-tier discipline）** —— 把「文档级 / 可执行级 / 已验证级」（Doc-level / Executable-level / Verified-level）分开独立打分，专治「文档剧场」（documentation theater，即只有漂亮文档、没有真东西）（[详情](references/borrow-rubric-3-tier.md)）。
- **Karpathy LLM Wiki 模式** —— 用 `_ai-entry.md` + `_hot.md` 做一层「AI 入口压缩层」，在 1000+ 页的大型 wiki 上可实现约 20–30 倍的 token 压缩（[详情](references/karpathy-llm-wiki-pattern.md)）。
- **Schema 系统** —— `schema_infer / validate / diff` 三件套工具，借鉴自 basicmachines-co/basic-memory（[脚本](scripts/schema_system.py)）。
- **静态刷新（Static refresh）** —— 用不调用 LLM 的 `refresh_hot_static.py` 作为热缓存定时任务的默认策略（避免 LLM 自我递归的风险）。

本 skill 构建于 Sentra「公司大脑」心智模型（Ashwin Gopinath，2026-04）× 原力OS 治理内核 × 独立借鉴审计（2026-05-08）之上。

## 5 分钟快速上手

```bash
git clone https://github.com/moonstachain/yuanli-os-company-brain-skill.git
cd yuanli-os-company-brain-skill

# 在自带的 12 篇笔记示例库上试跑
python3 scripts/relationship_graph.py --wiki-root examples/wiki --stats
python3 scripts/wiki_lint_l10.py        --wiki-root examples/wiki
python3 scripts/metacognition_signals.py --wiki-root examples/wiki

# v0.2：在示例库上跑 schema 系统
WIKI_ROOT=examples/wiki python3 scripts/schema_system.py infer concepts/

# v0.2：刷新热缓存（不调用 LLM）
WIKI_ROOT=examples/wiki python3 scripts/refresh_hot_static.py

# 指向你自己的 Obsidian 库
python3 scripts/relationship_graph.py --wiki-root ~/path/to/your/vault --mermaid > my-brain.md
WIKI_ROOT=~/path/to/your/vault python3 scripts/refresh_hot_static.py
```

无任何依赖（纯 Python 标准库）。已在 Python 3.10+ 上测试通过。

## 你会得到什么

```
yuanli-os-company-brain-skill/
├── SKILL.md                       # Claude Code skill 清单（frontmatter + 调用方式）
├── README.md                      # 英文版说明
├── README.zh-CN.md                # 本文件（中文版）
├── LICENSE                        # MIT
├── references/                    # 5 套核心方法论
│   ├── sentra-three-layers.md     # Sentra 三层 × 四要素
│   ├── three-circles-protocol.md  # 个人 / 共享 / 机构 三圈协议
│   ├── typed-relationships-schema.md  # 6 种关系类型 + G2 闭合阈值
│   ├── dual-axis-rubric.md        # 骨架成熟度 + 使用成熟度
│   └── 24h-rescore-protocol.md    # 诚实自审纪律
├── scripts/                       # 5 个可参数化的运行时工具
│   ├── brain_surface.py           # 适时召回
│   ├── relationship_graph.py      # 带类型的边（显式 + 推导）
│   ├── wiki_lint_l10.py           # 关系 schema 校验器
│   ├── metacognition_signals.py   # 过期 / 孤立 / 新鲜度信号
│   └── extract_decision.py        # 逐字稿 → 四元组脚手架
├── templates/                     # 3 个 frontmatter 模板
│   ├── decision-page.md
│   ├── circle-frontmatter.md
│   └── relationship-frontmatter.md
└── examples/                      # 最小示例库 + 样例运行结果
    ├── wiki/                      # 12 篇笔记（概念 / 决策 / 综合 / 逐字稿）
    └── sample-runs/               # 捕获的命令输出
```

## 实战检验过

本 skill 于 **2026-05-02** 从一次真实的个人知识系统审计中提炼而来：

- 一个 1170 篇笔记的中英文混合 wiki；
- 3 份真实会议逐字稿 → 四元组提取，引用**经 grep 验证 100% 真实**；
- 从 2 个决策推导出 13 条带类型的边（5 条 commits-to / 2 条 derives-from / 6 条 supersedes）；
- 骨架成熟度：约 30 小时内达到 **A 级（54/60）**；
- 使用成熟度：提取时仅为 **D 级（4/10）** —— 这是设计使然，真正的「用起来」需要数周时间。

诚实的评估记录在 [`references/dual-axis-rubric.md`](references/dual-axis-rubric.md)。叙事版本见 [原力OS 橙皮书 第 8 部分](https://github.com/moonstachain/yuanli-os-orange-book/tree/main/part8-yuanli-os-company-brain)。

## 什么时候该用这个 skill

✅ **适合用**：你经常写笔记、会开会、会做一些值得记住的决策，并且你的知识存在 Markdown 友好的库里（Obsidian / Logseq / 一堆 `.md` 文件的普通文件夹）。

❌ **不适合用**：你的知识存在 Notion 数据库 / Confluence / Google Docs 里（请先导出）；或者你根本不开会；又或者你期待一个「自动帮我整理整个库」的魔法工具 —— 这个 skill 默认是**由你这个人**来决定什么内容值得一圈一圈往上晋升的。

## 诚实地说清适用范围

这是一款**有明确立场的软件**。它体现了一些具体的选择：

| 立场 | 含义 |
|---|---|
| 关系是一等公民级的记忆 | 我们不相信「对文件做 RAG」就够了；你需要带类型的边（typed edges） |
| 晋升是涌现，不是命令 | 由生产者决定一条笔记何时跨圈，而不是中央管理层下令 |
| 验证 > 印象 | 四元组里每一条引用都必须 grep 验证通过；每一次审计都必须展示命令输出 |
| 骨架 ≠ 使用 | 一个看起来很漂亮、却没有真实数据的系统，依然是 D 级 |
| 24 小时复评 | 「我做完了」只是一个假设，不是事实，要等到第二天验证后才算数 |

如果以上任何一条和你的世界观冲突，请 fork 这套方法论自行改造，而不要整套照搬。

## 路线图（v0.2 候选项）

- 在 `metacognition_signals.py` 中加入 `conflict（冲突）` 和 `weak-evidence（弱证据）` 信号；
- 一个把 3 个硬核脚本包起来的 TUI 仪表盘；
- `obsidian-cli` 适配器（直接在 Obsidian 内运行）；
- 与工单系统对接，用于 `commits-to` 的跨系统引用。

欢迎提交「有立场」的 PR（比如改进 typed-edges 的交互体验、增加更多元认知信号）。对于「无立场」的需求（比如「让它支持 Notion」），请先开一个 issue 讨论。

## 致谢

- **心智模型**：Ashwin Gopinath（Sentra.app CEO），《Company Brain 第 1 / 第 2 部分》X 文章，2026-04；
- **治理内核**：liming（moonstachain），原力OS 审计评分表 × 六判断；
- **首次实战检验**：2026-05-01 至 2026-05-02。

## 许可证

MIT —— 详见 [LICENSE](LICENSE)。
