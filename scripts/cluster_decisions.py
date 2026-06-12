#!/usr/bin/env python3
"""
cluster_decisions.py — 选择性聚类 fan-in（CONTRACT 步骤：把决策源按语义聚类，
找出"同主题 ≥N 篇但还没被任何概念吸收"的簇 = 该被萃取的真主题优先级清单）。

复用 embed_sources.py 建的向量索引（不重新嵌入）。只看决策源（get-biji + transcripts）。
这是 distiller L3 跨会议聚类的工程实现：不穷举萃取，只对"够热的真议题"做选择性收敛。

方法：
  1. 从 .vector-index 取决策源向量
  2. 归一化 → 余弦相似矩阵 → 阈值建图 → 连通分量聚类（union-find）
  3. 留 size ≥ --min-cluster 的簇
  4. 吸收判定：簇内成员被 concepts/syntheses/entities 引用的比例；ratio 低 = 未萃取
  5. 主题标签：medoid（簇内最中心成员）标题 + top 共享 bigram
  6. 输出按"未萃取 × 簇大小"排序的萃取优先级清单

用法：
  cluster_decisions.py --wiki-root <wiki> [--threshold 0.60] [--min-cluster 3]
                       [--subdir-filter sources/get-biji,sources/transcripts] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

CJK_STOP = {
    "我们", "这个", "那个", "什么", "怎么", "可以", "就是", "这样", "一个", "现在",
    "然后", "如果", "因为", "所以", "但是", "还是", "这种", "那种", "需要", "已经",
    "记录", "讨论", "沟通", "会议", "项目", "问题", "内容", "情况", "方面", "进行",
}


def bigrams(text: str) -> list[str]:
    out = []
    for tok in re.findall(r"[\w一-鿿]+", text.lower()):
        if re.search(r"[一-鿿]", tok):
            for i in range(len(tok) - 1):
                bg = tok[i:i + 2]
                if bg not in CJK_STOP:
                    out.append(bg)
        elif len(tok) >= 3:
            out.append(tok)
    return out


def load_index(wiki: Path):
    idx = wiki / ".vector-index"
    vecs = np.load(idx / "sources.npz")["vecs"].astype(np.float32)
    paths = json.loads((idx / "paths.json").read_text(encoding="utf-8"))
    return vecs, paths


def build_absorbed_set(wiki: Path) -> set[str]:
    """概念/综合/实体引用到的 source 标识集合（basename/stem）。"""
    ref: set[str] = set()
    for sub in ("concepts", "syntheses", "entities", "comparisons", "decisions"):
        d = wiki / sub
        if not d.exists():
            continue
        for f in d.rglob("*.md"):
            t = f.read_text(encoding="utf-8", errors="replace")
            for m in re.findall(r"([^\s\"'\]\)]+\.md)", t):
                ref.add(Path(m).name)
            for m in re.findall(r"\[\[([^\]|#]+)", t):
                ref.add(m.strip().split("/")[-1])
    return ref


def union_find_clusters(sim: np.ndarray, threshold: float) -> list[list[int]]:
    n = sim.shape[0]
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    iu = np.argwhere(np.triu(sim >= threshold, k=1))
    for a, b in iu:
        union(int(a), int(b))
    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def main() -> int:
    ap = argparse.ArgumentParser(description="决策源语义聚类 → 未萃取真主题优先级清单")
    ap.add_argument("--wiki-root", type=Path, required=True)
    ap.add_argument("--threshold", type=float, default=0.80,
                    help="同簇余弦阈值（get-biji 等带模板头的源 baseline 高，需 ~0.80 才分得开；低于会 chaining 成一坨）")
    ap.add_argument("--min-cluster", type=int, default=3)
    ap.add_argument("--subdir-filter", default="sources/get-biji,sources/transcripts")
    ap.add_argument("--top", type=int, default=25, help="输出前 N 个簇")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    wiki = args.wiki_root.expanduser()
    if not (wiki / ".vector-index" / "sources.npz").exists():
        print("error: 无向量索引，先跑 embed_sources.py", file=sys.stderr)
        return 2

    vecs, paths = load_index(wiki)
    prefixes = tuple(s.strip() for s in args.subdir_filter.split(","))
    sel = [i for i, p in enumerate(paths) if p.startswith(prefixes)]
    if len(sel) < args.min_cluster:
        print(f"决策源向量不足（索引里只有 {len(sel)} 条匹配 {prefixes}）。"
              f"先用 embed_sources.py 嵌入这些子目录。", file=sys.stderr)
        return 1

    sub_vecs = vecs[sel]
    sub_paths = [paths[i] for i in sel]
    norms = np.linalg.norm(sub_vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1e-9
    unit = sub_vecs / norms
    sim = unit @ unit.T

    clusters = [c for c in union_find_clusters(sim, args.threshold) if len(c) >= args.min_cluster]
    absorbed = build_absorbed_set(wiki)

    results = []
    for c in clusters:
        members = [sub_paths[i] for i in c]
        # 吸收率
        absorbed_n = sum(1 for m in members
                         if Path(m).name in absorbed or Path(m).stem in absorbed)
        absorb_ratio = absorbed_n / len(members)
        # medoid：簇内平均相似最高
        sub = sim[np.ix_(c, c)]
        medoid_local = int(np.argmax(sub.mean(axis=1)))
        medoid_path = members[medoid_local]
        medoid_title = Path(medoid_path).stem
        # 主题词：成员标题 bigram top
        term_counter: Counter = Counter()
        for m in members:
            term_counter.update(bigrams(Path(m).stem))
        top_terms = [t for t, _ in term_counter.most_common(6)]
        results.append({
            "size": len(members),
            "absorb_ratio": round(absorb_ratio, 2),
            "unextracted": absorb_ratio < 0.34,  # <1/3 成员被吸收 = 该簇基本没进概念
            "theme_terms": top_terms,
            "medoid": medoid_title,
            "members": members,
        })

    # 排序：未萃取优先，再按大小
    results.sort(key=lambda r: (not r["unextracted"], -r["size"]))
    worklist = [r for r in results if r["unextracted"]]

    if args.json:
        print(json.dumps({"clusters": results, "unextracted": worklist},
                         ensure_ascii=False, indent=2))
        return 0

    print(f"# 决策源聚类 · 未萃取真主题优先级清单\n")
    print(f"- 决策源向量：{len(sel)} · 阈值 cos≥{args.threshold} · 簇≥{args.min_cluster} 篇")
    print(f"- 形成簇：{len(clusters)} 个 · 其中**未萃取**（吸收率<1/3）：**{len(worklist)}** 个\n")
    print(f"## 🎯 该被萃取的簇（按未萃取×规模排序，前 {args.top}）\n")
    for i, r in enumerate(worklist[:args.top], 1):
        action = "→ OSA 决策卡" if any(k in r["medoid"] for k in ("讨论", "沟通", "规划", "决策", "对接")) else "→ concept/synthesis"
        print(f"### {i}. 【{r['size']} 篇 · 吸收{int(r['absorb_ratio']*100)}%】{' '.join(r['theme_terms'][:4])}")
        print(f"- 代表(medoid): `{r['medoid']}`")
        print(f"- 建议: **{action}**")
        print(f"- 成员样例: " + " · ".join(f"`{Path(m).stem[:28]}`" for m in r["members"][:4])
              + (f" …+{r['size']-4}" if r["size"] > 4 else ""))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
