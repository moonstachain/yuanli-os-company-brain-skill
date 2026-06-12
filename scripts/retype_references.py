#!/usr/bin/env python3
"""
retype_references.py — Lever 1 dry-run：把概念层扁平 `type: references` 边
按 body 上下文重新分类成 6 类典型边（commits-to/owns/blocks/derives-from/
supersedes/supports）。**只提议、不写**（人审升级高价值边）。

第一轮诊断的核心债：5,261/5,277 边是 `references`（信息论 0 bit，等价裸 wikilink）。
本脚本找出其中真正承载推理关系的少数，提议升级；其余诚实保留为 references。

判据 = source 正文里提到 target 处的上下文措辞（cue 词）。无强 cue → 保留 references。

用法：
  retype_references.py --wiki-root <wiki> [--limit N] [--min-conf high] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

CANON = ("commits-to", "owns", "blocks", "derives-from", "supersedes", "supports")

# cue → (canonical type, confidence)。顺序即优先级。
# 注：supersedes 只用**强显式**标记（取代了/已被取代/废弃/前身/升级自），
# 不用裸"替代"——它在中文里多为"替代方案/不可替代/而非替代品"(否定/名词)，会反向误判。
CUES = [
    ("supersedes",   "high", r"取代了|已被取代|被.{0,4}取代|已(废弃|过时)|deprecat|的前身是|升级自|淘汰了"),
    ("derives-from", "high", r"源于|来自|脱胎(于|自)|衍生(自|于)|蒸馏自|提炼自|derive|根植于"),
    ("blocks",       "high", r"前置(条件|依赖)|必须先|依赖于(?!环境)|受制于|blocks|prerequisite"),
    ("derives-from", "med",  r"引用自|参考(了|自)|沿用自|借鉴自"),
    ("owns",         "med",  r"负责|归属于|owner|主理|主管"),
    ("commits-to",   "med",  r"承诺(于|给)|认领|交付给"),
    ("supports",     "med",  r"印证(了|该)|佐证(了|该)|实证(支持|了)|证据表明"),
]
# 否定/软idiom 守卫：cue 命中但上下文含这些 → 撤销（防 "而非替代品" 反向、"替代方案"名词误判）
NEG_GUARD = r"而非|并非|不是|不可替代|无法替代|替代方案|替代品|替代选择"
# 非典型6类但值得人审标注的（不升级，仅提示）
CONTRAST = r"对比|相对于|区别于|张力|矛盾|vs\b|与.*?不同"


def split_fm_body(text: str):
    if text.startswith("---"):
        end = text.find("\n---", 4)
        if end != -1:
            return text[4:end], text[end + 4:]
    return "", text


def parse_ref_edges(fm: str):
    """从 relationships 块抽 (type, target)。极简 YAML。"""
    edges = []
    if "relationships:" not in fm:
        return edges
    cur = None
    inb = False
    for line in fm.splitlines():
        s = line.strip()
        if s.startswith("relationships:"):
            inb = True
            continue
        if not inb:
            continue
        if s in ("...", "---", ""):   # 这些 vault 的 relationships 块里夹了 `...` YAML 标记，别误当块结束
            continue
        if line and not line[0].isspace() and not s.startswith("-"):
            break
        if s.startswith("- type:"):
            if cur and cur.get("type") and cur.get("target"):
                edges.append((cur["type"], cur["target"]))
            cur = {"type": s.split(":", 1)[1].strip().strip("\"'")}
        elif cur is not None:
            m = re.match(r"(target):\s*(.+)$", s)
            if m:
                cur["target"] = m.group(2).strip().strip("\"'")
    if cur and cur.get("type") and cur.get("target"):
        edges.append((cur["type"], cur["target"]))
    return edges


def classify(context: str):
    for typ, conf, pat in CUES:
        if re.search(pat, context, re.I):
            # 否定守卫只作用于 supersedes（替代idiom重灾区）
            if typ == "supersedes" and re.search(NEG_GUARD, context):
                continue
            return typ, conf
    return None, None


def context_of(body: str, target: str, width: int = 100) -> str:
    """在 body 里找 target（[[target]] 或裸 stem）的上下文窗口。"""
    stem = target.split("/")[-1]
    for pat in (re.escape(f"[[{stem}"), re.escape(stem)):
        m = re.search(pat, body)
        if m:
            a = max(0, m.start() - width)
            return body[a:m.end() + width]
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki-root", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--min-conf", choices=["high", "med"], default="med")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--show", type=int, default=15)
    args = ap.parse_args()

    cfiles = sorted((args.wiki_root / "concepts").glob("*.md"))
    # 排除 MoC/索引页：其 references 是成员导航链接，本就该是 references，不该升级
    is_moc = lambda n: n.startswith("moc-") or "知识地图" in n or n in ("原力战略.md",)
    moc_skipped = sum(1 for f in cfiles if is_moc(f.name))
    cfiles = [f for f in cfiles if not is_moc(f.name)]
    if args.limit:
        cfiles = cfiles[:args.limit]

    total_ref = 0
    proposals = []          # (conf, typ, src, target, cue_ctx)
    no_context = 0
    contrast_flag = 0
    rank = {"high": 2, "med": 1}

    for f in cfiles:
        fm, body = split_fm_body(f.read_text(encoding="utf-8", errors="replace"))
        for typ, target in parse_ref_edges(fm):
            if typ != "references":
                continue
            total_ref += 1
            ctx = context_of(body, target)
            if not ctx:
                no_context += 1
                continue
            ntyp, conf = classify(ctx)
            if ntyp and rank[conf] >= rank[args.min_conf]:
                snippet = re.sub(r"\s+", " ", ctx).strip()[:90]
                proposals.append((conf, ntyp, f.stem, target.split("/")[-1], snippet))
            elif re.search(CONTRAST, ctx):
                contrast_flag += 1

    by_type = Counter(p[1] for p in proposals)
    by_conf = Counter(p[0] for p in proposals)
    proposals.sort(key=lambda p: (rank[p[0]], p[1]), reverse=True)

    if args.json:
        print(json.dumps({
            "total_references": total_ref, "proposed_upgrades": len(proposals),
            "by_type": dict(by_type), "by_conf": dict(by_conf),
            "no_context": no_context, "contrast_candidates": contrast_flag,
            "samples": proposals[:50],
        }, ensure_ascii=False, indent=2))
        return 0

    print("# Lever 1 · concept 层 references 重分类 dry-run\n")
    print(f"- 扫描非MoC概念: {len(cfiles)} (已排除 {moc_skipped} 个 MoC/索引页=成员导航边,不该升级)")
    print(f"- 非MoC references 边: {total_ref}")
    print(f"- **可升级为典型边: {len(proposals)}** "
          f"({100*len(proposals)//max(total_ref,1)}%) · 其余保留 references")
    print(f"- 置信度: high={by_conf.get('high',0)} med={by_conf.get('med',0)}")
    print(f"- 无 body 上下文(无法判): {no_context} · contrast 候选(非6类,仅标注): {contrast_flag}\n")
    print("## 按提议类型分布")
    for t in CANON:
        if by_type.get(t):
            print(f"- `{t}`: {by_type[t]}")
    print(f"\n## 提议样例(前 {args.show}, 人审 gate)\n")
    for conf, typ, src, tgt, ctx in proposals[:args.show]:
        print(f"- [{conf}] `{src}` -**{typ}**-> `{tgt}`")
        print(f"    cue: …{ctx}…")
    print("\n> dry-run，未写任何文件。高价值边(supersedes/blocks)升级须 human-confirm。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
