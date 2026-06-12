---
title: Team Share Slice Protocol
type: concept
domain: 原力OS
created: 2026-06-12
revision: v0.1
maturity: developing
audience: both
related:
  - "[[wiki-github-mirror-sync]]"
  - "[[three-circles-protocol]]"
  - "[[multiplatform-projection-protocol]]"
tags: [原力OS, company-brain, share-slice, team-memory, leak-guard, distribution]
---

# Team Share Slice Protocol · 团队共享切片协议

> **一句话定位**：把 vault 中**一个 tag 作用域内**的脱敏知识，导出成一个 GitHub **私有**仓的只读镜像，协作者提供 GitHub id 即可获取、自动同步更新——团队共享记忆，但真相层永远只有一个可写点。

## 0. 这不是 mirror-sync

| | [`wiki-github-mirror-sync`](wiki-github-mirror-sync.md)（备份器官） | 本协议（分发器官） |
|---|---|---|
| 目的 | 灾备：本机坏了 vault 不丢 | 共享：让同事/协作者拿到一片知识 |
| 范围 | 全 vault（gitignore 脱敏后） | **tag 作用域切片**（白名单为主） |
| 受众 | 只有你自己 | 提供 GitHub id 的协作者（只读） |
| 与三圈的关系 | 不跨圈（备份 ≠ promotion） | **是 promotion 的执行机**：内容先过人审进 shared/institutional 圈（打上 share tag 即人审动作），脚本只搬运已晋升内容 |

两个器官都终结于 GitHub 私有仓，但**永远是两个不同的仓**。备份仓里有你的 individual 圈；共享仓里绝不能有。

## 1. 五步链路

```
① 作用域筛选     frontmatter 含 share_group: <tag> 的页面（白名单，非排除法）
② 脱敏 leak-guard 内容签名扫描：敏感串字面命中 ⇒ 整次导出 abort
③ 导出           只读镜像目录（含 README 声明"单向镜像，勿在此修改"）
④ 私有仓 + 邀请   GitHub private repo；协作者按 GitHub id 邀请为 read-only collaborator
⑤ 定时单向同步    launchd 定时重跑 ①-③ + push；协作者 git pull 即拿到更新
```

每一步的执行机是 [`scripts/share_slice_export.py`](../scripts/share_slice_export.py)（①-③，默认 dry-run）+ 你已有的 mirror-sync 四安全门习惯（④-⑤：private-only 断言 / never-force / single lock / leak-guard）。

## 2. 作用域：tag 白名单，不是路径排除

**为什么用 frontmatter tag 而不是目录**：promotion 是按**页**发生的人审决定，不是按目录批发。一个 `share_group: team-x` 标签 = 一次显式的"这页可以给团队看"的判断，符合三圈协议的 producer-decides 原则。目录排除法（"除了 private/ 都共享"）是默认共享，方向反了。

```yaml
# 一个被纳入切片的页面 frontmatter
---
title: 某概念
circle: shared          # 必须 ≥ shared；individual 页即使打了 tag 也会被脚本拒绝
share_group: team-x     # 作用域标签；一页可属多个 group（YAML list）
---
```

## 3. 脱敏 leak-guard：内容签名扫描

导出前对**每个候选文件的正文**跑敏感签名扫描，任一命中 ⇒ abort（不是跳过该文件，是整次失败——强迫人来看）：

- 签名清单放独立文件（`--leak-guard-file`），一行一个字面串/正则：真实客户名、财务数字模式、手机号/证件号正则、API key 模式。
- **签名文件本身永不进切片**（脚本硬编码排除，且建议放 vault 外）。
- 实战教训（field-tested 2026-06，两例真实团队共享切片）：
  1. **guard 写字面密码会自触发**——签名清单若含真实密码明文，扫描自己时命中自己。解法：清单里放模式（正则）不放明文，或运行时拼接。
  2. **扫描 scope 必须限定知识目录**——对仓库根目录跑扫描会把 `.git/`、构建产物全扫一遍，误报淹没真命中；脚本只扫候选文件集。
  3. **路径参数拒 `.` 用绝对路径**——相对路径在 launchd 环境下 cwd 不可预期。

## 4. 接收端体验（这是协议存在的理由）

协作者侧的全部成本：

```bash
git clone git@github.com:<owner>/<slice-repo>.git   # 接受邀请后
# 之后只需要：
git pull                                             # 拿最新知识
```

切片仓自带（由导出脚本生成）：
- `README.md` — 声明这是单向只读镜像、真相层在别处、PR 不收（知识修正走源头人审）
- `_slice-manifest.json` — 本次导出的页面清单 + 源 vault 的 commit/时间戳，接收端可验新鲜度

如果切片里 vendor 了查询脚本（可选），同事 clone 即可本地 recall——参考投影协议平台分工卡中"团队共享 + 版本"角色的自包含原则。

## 5. 同步纪律（与投影协议三铁律对齐）

1. **切片仓永远只读**。任何人（包括你）不在切片仓里改内容——改源头，重跑导出。切片仓历史允许 force 吗？**不允许**，同 mirror 的 never-force：协作者的 pull 不应该断。
2. **下线即删除**。一页撤销 `share_group` 标签后，下次导出它会从切片消失（脚本做全量重建而非增量追加，保证撤销生效）。
3. **新协作者 = 新人审**。邀请一个 GitHub id 前问一次：这个作用域里**全部**页面都可以给这个人看吗？答案不是全称肯定，就拆新的 share_group。

## 6. Adoption checklist

1. 选一个最小作用域（5-10 页），加 `share_group` frontmatter
2. 写敏感签名清单（放 vault 外）
3. `python3 scripts/share_slice_export.py --wiki-root <vault> --share-tag <group> --out-dir <dir> --leak-guard-file <file>` —— 默认 dry-run，看清单
4. `--execute` 真导出 → 人眼过一遍导出目录 → `gh repo create <slice> --private` → push
5. 邀请协作者（read 权限）→ 对方 clone 验证
6. launchd 定时（复用 mirror 的 plist 模板，换脚本路径）；7 天后跑 [`dual-axis-rubric`](dual-axis-rubric.md)，usage 轴看协作者是否真的 pull 过（`gh api` 看 clone traffic）
