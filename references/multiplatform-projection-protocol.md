---
title: Multiplatform Projection Protocol
type: concept
domain: 原力OS
created: 2026-06-11
revision: v0.1
maturity: developing
audience: both
related:
  - "[[5-layer-architecture]]"
  - "[[three-circles-protocol]]"
  - "[[dual-axis-rubric]]"
tags: [原力OS, company-brain, projection, multiplatform, sync-discipline, SSOT]
---

# Multiplatform Projection Protocol · 多平台投影协议

> **一句话定位**：当一个 Company Brain 需要同时活在 6+ 个平台上（本地 vault / git 仓 / RAG 问答服务 / 移动笔记 App / 协作表格 / 全局 wiki），本协议回答三件事：**每个平台扮演什么唯一角色、知识往哪个方向流、怎么保证永不失同步**。

## 0. 与姊妹文档的关系

| 文档 | 管什么 |
|---|---|
| [`5-layer-architecture.md`](5-layer-architecture.md) | **放哪跑**——资产/任务/cron 的托管位置（locality · credential · failure radius） |
| [`three-circles-protocol.md`](three-circles-protocol.md) | **什么能出圈**——individual / shared / institutional 的晋升 gate |
| 本文 | **出圈之后投到哪些消费面、怎么不失同步**——投影方向、平台分工、同步纪律 |

## 1. 第一性原则：单一真相源 + 单向投影

```
真相层 = 本地 vault（git 版本化 · typed edges · grep-verified quotes · circle 标注）
投影层 = git 远端 / RAG notebook / 移动笔记 / 协作表格（可过期、可重建、绝不反向手改）
回 写 = 任何入口产生的新知识 → 人审蒸馏 → 进真相层 → 再投影
```

**为什么**：多平台失同步的根因是「多处可写」。锁死单一可写点后，失同步的最坏后果只是「某个投影旧了」——重跑投影脚本即愈；真相永不分叉。这是把分布式系统的 SSOT（single source of truth）纪律搬到知识管理。

## 2. 六层投影栈

```
L0 原料层    原始档案 / 公众号后台 / 会议音视频          【raw · 只读不动 · 永不上云】
L1 提取层    _extract/（textutil / pdftotext / whisper） 【本地 · gitignore · reliability:raw】
L2 真相层★   company-brain vault（概念/实体/金句/决策）   【本地 Obsidian + git · 唯一可写点】
L3 共享层    私有 git 远端（gated sync：lint / secret 扫描 / 禁 raw）
L4 消费层    RAG 问答 · 移动快查 · 协作表格 · 语音转写    【单向投影 · 各司一职】
L5 本体层    全局 wiki（跨项目本体；敏感域只放脱敏指针）
```

L0→L1→L2 是蒸馏方向（见主 SKILL 六阶段）；L2→L3/L4/L5 是投影方向。**箭头永远单向**。

## 3. 平台分工卡（每平台一个唯一职责）

按「数据形态 × 使用场景」分工，不按平台名堆砌。下表的产品名是 2026-06 实测实例，可按生态替换（如 Notion 换 Feishu、Mem.ai 换 GET笔记）：

| 角色 | 实例 | 放什么 | 绝不放 | 选型依据（实测） |
|---|---|---|---|---|
| **真相层 / 治理** | 本地 Obsidian vault | 蒸馏卡 + typed edges + circle | — | 引擎可 lint、引文可 grep 验证 |
| **团队共享 + 版本** | GitHub **私有**仓 | 全蒸馏层 + vendored 引擎脚本（同事免装依赖） | L1 raw 提取层 | fresh clone 即可跑 recall，自包含 |
| **全文深问 + 引证 + 音频产物** | NotebookLM | 语料全文（脱敏合并 txt，≤50万字/源） | 成本/报价/PII | 跨年语料问询返回带引用答案；studio 出 audio overview |
| **移动 / 碎片语义快查** | GET笔记（得到） | 蒸馏卡（百条级） | 原始档案批量 | 语义 recall 准；**write 配额 ~100/天** 决定了只放卡不放料 |
| **结构化流水数据** | Feishu 多维表 | 内容清单/发文流水等表数据 | 知识正文 | 万行级流水的透视分析是表格的事，不是 vault 的事 |
| **语音→文字入口**（L0→L1） | Feishu 妙记 | 会议/讲座录音转写 | — | 转写数字默认存疑（reliability:raw） |
| **跨项目全局本体** | 全局 wiki（Obsidian 级） | 脱敏模式页 + 指针 | 客户域正文 | 多租户纪律：客户 IP 与个人本体隔离 |

记忆口诀：**真相在 vault，团队看 git，深问去 RAG，手机点笔记，流水进表格，录音走转写，全局查 wiki。**

## 4. 场景路由表

| 我现在要… | 入口 | 链路 |
|---|---|---|
| 写深度稿件 | agent CLI | 本地 recall 取金句 → RAG notebook 深问引证 → 写作 skill → 质检 |
| 手机上临时查个说法 | 移动笔记 App | 语义 recall |
| 给同事完整背景 | git 私有仓 | clone → 仓内自带引擎自查 → 经 source-index 指针回原档 |
| 通勤听资料 / 选题会前 | RAG notebook | audio overview / 脑图 |
| 分析发布规律 | 协作表格 | 数据透视 |
| 跨域借方法论 | agent CLI | 全局 wiki 检索 |
| 录音 / 会议要沉淀 | 语音转写服务 | 转写 → 人审 → 蒸馏回 vault → 投影 |

## 5. 三条同步铁律

1. **改只改真相层**。vault 改完 → gated sync 推 git（即时）；RAG/移动笔记按**里程碑**批量重投影（投影构建脚本化、可重跑）。不追实时，追可重建。
2. **三圈横切所有平台**。raw 永不出本地；敏感（财务/PII/成本/报价/名单）永不上任何云——上云前必过 secret 正则扫描（手机号/邮箱/证件号/API key）。
3. **回写走人审**。RAG 问询的好发现、移动端随手记、会议纪要 = **候选知识**，人确认后才进 vault。AI 不自动跨圈（三圈协议的 promotion gate 同款纪律）。

## 6. 实战坑速查（field-tested 2026-06）

| 坑 | 症状 | 修法 |
|---|---|---|
| RAG 服务并发上传限流 | 批量 add source 11 连发挂 5，**报错的调用可能已在服务端落库** | 串行 + wait 完成确认；失败重试后列表查重删除幽灵副本 |
| git 默认 quote 非 ASCII 路径 | **CJK 文件名在 `git diff --name-only \| xargs grep` 里被静默跳过 → secret 扫描门形同虚设** | `git -c core.quotepath=false diff --name-only -z \| while IFS= read -r -d '' f` 空分隔遍历 |
| 引擎脚本拒相对路径 | `--wiki-root .` 直接报错 | 一律传绝对路径 `"$PWD"` |
| macOS textutil 不吃 pptx | 批量提取静默漏掉 ppt 内容 | python stdlib 解 `ppt/slides/slideN.xml` 的 `<a:t>` 文本 |
| 竖排 CJK PDF 提取 | 封面/标题每字一行 | 正文 prose 行通常正常；标题层手工核对 |
| 移动笔记 write 配额 | 百条/天级硬顶 | 决定了它只能当「蒸馏卡投影」不能当「档案仓」 |
| 同名目录多 checkout 漂移 | 公开 skill 仓里混入未审改动 | 提交前 `git status`；**永远精确 `git add <file>`，公开仓禁 `add -A`** |

## 7. N+1 复制检查单（新领域大脑落地 7 步）

1. L0 圈定原料 + 敏感二分（🔴 只登记位置，正文不提取）
2. L1 提取（textutil / pdftotext / whisper → `_extract/`，标 raw）
3. L2 建 vault（company-brain 布局；**先读引擎 parser 源码再写**，对齐触发串，防"脚本读 0"）
4. L3 `git init` + gated sync（lint 0 错 / secret 扫描 / 禁 raw 三道门）+ 私有仓
5. L4 按需投影（移动笔记放蒸馏卡 / RAG notebook 放脱敏全文 / 表格放流水）
6. L5 全局 wiki 放脱敏模式指针
7. [`dual-axis-rubric`](dual-axis-rubric.md) 诚实双轴打分（scaffold ≠ usage），24h 复评

## 8. Field test（2026-06，两个匿名化案例）

- **案例 A**：一个 13 年 / 74.9G / 22,753 文件的机构档案（二进制 Word 为主，冷启动）→ 蒸馏 40+ 卡 + 全文 RAG 四库 + 移动笔记卡投影 + 私有 git 团队共享。typed edges 49 / lint 0 错 / 引文 grep 验证 100%。双轴：Scaffold B+ · Usage B。
- **案例 B**：一条文创品牌产品线（品牌书 PDF + 产品文案 + 经营 PPT）→ 脱敏白名单上 RAG（剔除成本/报价/经营数据 9 件），产品文案三段结构直接复用为内容生产素材。
- 跨年份语料问询实测：单一问题返回横跨 3 个年份的原文引用 + 出处，直接可用于内容生产。

## 9. Adoption notes

- 平台清单会过时，**角色分工不会**：真相层 / 版本共享 / 全文深问 / 移动快查 / 流水表格 / 语音入口 / 全局本体——七个角色先于任何产品存在。
- 起步最小集 = L2 vault + L3 私有 git。其余投影按真实使用频率逐个开，**别为了"完整"一次开满**（usage 轴会诚实揭穿）。
- 任何新平台接入前问三个问题：它的唯一职责是什么？它绝不放什么？它的投影脚本能否一键重建？三问有一答不上来，就不接。
