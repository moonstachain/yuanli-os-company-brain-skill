---
title: Tiered Knowledge Spine
type: concept
domain: 原力OS
created: 2026-06-12
revision: v0.1
maturity: developing
audience: both
related:
  - "[[multiplatform-projection-protocol]]"
  - "[[5-layer-architecture]]"
  - "[[karpathy-llm-wiki-pattern]]"
tags: [原力OS, company-brain, tiered-storage, spine, routing, cost-discipline]
---

# Tiered Knowledge Spine · 分层知识脊柱

> **一句话定位**：当知识量超过单一工具的舒适区，本协议回答一件事：**一份内容按它的性质（容量 / 时效 / 模态 / 检索频率）应该落在哪一层**——索引层、容量层，还是热点层。

## 0. 与姊妹文档的关系

| 文档 | 管什么 |
|---|---|
| [`multiplatform-projection-protocol.md`](multiplatform-projection-protocol.md) | **同一份内容**出真相层之后投到哪些消费面、怎么不失同步（投影方向） |
| [`5-layer-architecture.md`](5-layer-architecture.md) | 资产/任务/cron 的**托管位置**（locality · credential · failure radius） |
| 本文 | **不同性质的内容**按四轴判据分层落位（路由方向）。投影协议管"分发"，本协议管"安家"——正交互补 |

## 1. 三层模型

```
索引层 SPINE   本地 vault（Obsidian 级）
               核心概念网络 + 全库目录索引 + 各容量库的位置指针
               只放根基知识，不存大容量内容 —— 保证检索效率
       │ 持有指针，按需调取 ↓
容量层 DEPTH   RAG notebook（NotebookLM 级）
               存量大容量多模态专题库（全文 PDF / 音视频 / 跨年语料）
               按专题分库；索引层知道每个专题库在哪
       │ 蒸馏沉淀，回流入脊柱 ↑
热点层 PULSE   实时抓取服务（GET笔记级）
               中文生态实时热点：链接 → 逐字稿 → 语义 recall
               天然带时效，过期即弃；值得留的蒸馏后进索引层
```

**为什么是三层而不是一层**：把全文塞进 vault，检索效率随体积坍塌（grep 一次扫几十 GB）；把概念网络放进 RAG notebook，typed edges / lint / grep 验证全部失效。每层只做自己最强的事，索引层持有其它层的**位置指针**——这是把操作系统的存储分级（cache / RAM / disk）搬到知识管理。

## 2. 四轴路由判据

新内容来了，按四轴打分决定落哪层：

| 轴 | 问题 | 索引层 | 容量层 | 热点层 |
|---|---|---|---|---|
| **容量** | 单件多大？ | 蒸馏卡级（KB） | 全文/音视频级（MB-GB） | 逐字稿级（KB-MB） |
| **时效** | 多久过期？ | 根基知识，年级 | 存量专题，月-年级 | 热点，天-周级 |
| **模态** | 什么形态？ | markdown only | 多模态（PDF/音视频/PPT） | 链接 + 转写文本 |
| **检索频率** | 多常用？ | 每次产出前都 surface | 专题深问时才进 | 选题/追热点时才进 |

**冲突裁决**：四轴指向不一致时，以**容量轴优先**——大体积内容进索引层是最不可逆的错误（拖垮全库检索），其余错位重路由即愈。

## 3. 物料适配优先级

入库前看物料形态，转换成本从低到高：

```
md  >  word / pdf / ppt  >  音频  >  视频
```

- **md**：直接进（索引层或容量层均可）。
- **word / pdf / ppt**：容量层 RAG notebook 原生可吃；要进索引层必须先蒸馏成 markdown 卡。
- **音频**：先转写（语音转写服务 → 逐字稿），逐字稿按 L0→L1 处理（reliability: raw）。
- **视频**：优先用**线上链接**喂容量层/热点层（墙内视频走热点层抓取，海外视频走 RAG notebook 链接源）；本地大视频切片 → 转写 → 逐字稿归档，原件留 NAS 级冷存储，**永不进任何一层**。

## 4. 成本纪律

分层的第二个理由是成本结构（2026-06 实测量级，会过时，结构不会）：

| 层 | 成本量级 | 纪律 |
|---|---|---|
| 索引层 | 本地免费 + git | 唯一可写真相层，成本在人审 |
| 容量层 | 免费额度可覆盖日常；pro 级 ~ 数百元/年 | 按专题分库，单库别超源数上限 |
| 热点层 | 推广期红利常见，按量计费 | 只当**入口**不当**仓库**——write 配额与召回额度决定它存卡不存料 |

**反模式**：为"统一"把三层合并到一个付费平台。单平台纵深再强，也同时丢掉本地 grep 验证（索引层的命根）和实时抓取（热点层的命根）。

## 5. 场景路由速查

| 我现在要… | 走哪层 | 链路 |
|---|---|---|
| 写稿前拉个人已有观点 | 索引层 | brain_surface recall |
| 对一个专题深问带引证 | 容量层 | 索引层指针 → RAG notebook 问询 |
| 追今天的行业热点 | 热点层 | 链接 → 逐字稿 → 语义 recall（见 [`scripts/intake_getnote.py`](../scripts/intake_getnote.py) 的 stub 约定） |
| 热点里有真知识想留下 | 热点层 → 索引层 | 人审蒸馏成卡，truth_source 指回原 note |
| 一批存量 PDF 资料 | 容量层 | 脱敏后按专题建库；索引层登记指针页 |

## 6. 实战坑速查（field discussion 2026-06）

| 坑 | 症状 | 修法 |
|---|---|---|
| 全文进索引层 | vault 膨胀，recall 变慢、噪声淹没根基概念 | 大容量内容迁容量层，索引层只留指针页 + 蒸馏卡 |
| 热点层当仓库 | 配额耗尽 / 平台政策变动即资产蒸发 | 热点层内容默认易失；值得留的 24h 内蒸馏进索引层 |
| 平台 API 取单条记录用大整数 ID | 19 位数字 ID 被运行时按浮点截断 → 稳报"记录不存在" | 一律走语义 recall 接口，不依赖按 ID 直取（见 intake_getnote.py 头注） |
| 指针页失修 | 索引层指针指向已删除/改名的容量库 | 指针页纳入 metacognition stale 信号扫描范围 |

## 7. Adoption notes

- 起步最小集 = 索引层（你已有的 vault 就是）。容量层在第一批超 50MB 的存量资料出现时再开；热点层在内容生产有追热点需求时再开。**别为了"完整"一次开满**（usage 轴会诚实揭穿）。
- 三层都接入后，跑一次 [`dual-axis-rubric`](dual-axis-rubric.md)：scaffold 看三层是否各有唯一职责，usage 看指针是否真的被 surface 调用过。
- 平台实例可整体替换（RAG notebook 换厂商、热点抓取换服务），**三层角色与四轴判据不变**——角色先于产品存在。
