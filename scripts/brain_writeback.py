#!/usr/bin/env python3
"""
brain_writeback.py — 回写飞轮第②半（CONTRACT §4 步骤 6）。

输入一张（可能只填了 O/S/A/truth_source、还没连边的）OSA 决策卡 JSON，
自动扫概念层，把它**连回相关概念**（fan-in 自动化），产出 enriched `.draft.json`
到 writeback inbox 供人审 → promote。

核心价值 = "给一个新决策，自动把它的边接到已沉淀的知识层"。
这是把 Claude 干完的活收敛回大脑、让大脑越来越聪明的物理动作。

铁律：
  - 只提议**低风险 `derives-from`** 边（决策"借用/源于"某知识）。
  - **不**自动提议高价值边（supersedes/blocks/supports 由人在 review 时升级）。
  - 全部 trust=claude-auto + proposed=true，等 promote 时人审。

用法：
  brain_writeback.py --card draft.json --wiki-root <wiki> [--out-dir <inbox>]
                     [--top 5] [--min-distinct 3]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CJK_STOP = {
    "帮我", "我写", "写个", "我想", "想要", "帮忙", "一下", "一个", "怎么", "如何",
    "可以", "什么", "这个", "那个", "的话", "请帮", "给我", "需要", "是否", "以及",
    "或者", "然后", "目前", "现在", "关于", "对于", "麻烦", "一种", "一些", "最优",
    "解淘", "淘汰", "胜出", "原因", "备选",
}


def bigrams(text: str) -> set[str]:
    terms: set[str] = set()
    for tok in re.findall(r"[\w一-鿿]+", text.lower()):
        if re.search(r"[一-鿿]", tok):
            if len(tok) < 2:
                continue
            for i in range(len(tok) - 1):
                bg = tok[i:i + 2]
                if bg not in CJK_STOP:
                    terms.add(bg)
        elif len(tok) >= 2:
            terms.add(tok)
    return terms


def card_blob(card: dict) -> str:
    return " ".join(str(card.get(k, "")) for k in ("title", "o", "s", "a", "domain"))


def split_fm_body(text: str) -> tuple[dict, str]:
    fm: dict = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 4)
        if end != -1:
            for line in text[4:end].splitlines():
                m = re.match(r"^([\w_-]+):\s*(.+?)\s*$", line)
                if m:
                    fm[m.group(1)] = m.group(2).strip().strip("\"'")
            body = text[end + 4:]
    return fm, body


def propose_edges(card: dict, wiki_root: Path, top: int, min_distinct: int) -> list[dict]:
    card_terms = bigrams(card_blob(card))
    if not card_terms:
        return []
    existing = {(e.get("type"), str(e.get("to"))) for e in card.get("edges", []) or []}
    card_id = card.get("id", "")
    scored: list[tuple[int, str, str]] = []  # (distinct, concept-stem, title)
    for sub in ("concepts", "syntheses"):
        d = wiki_root / sub
        if not d.exists():
            continue
        for path in d.rglob("*.md"):
            if path.name.startswith("_"):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace").lower()
            except OSError:
                continue
            distinct = sum(1 for t in card_terms if t in text)
            if distinct >= min_distinct:
                fm, body = split_fm_body(text)
                title = fm.get("title", path.stem)
                scored.append((distinct, path.stem, title))
    scored.sort(key=lambda x: -x[0])
    proposed: list[dict] = []
    for distinct, stem, title in scored:
        if len(proposed) >= top:
            break
        if ("derives-from", stem) in existing:
            continue
        proposed.append({
            "from": card_id,
            "type": "derives-from",
            "to": stem,
            "cross": "decision->concept",
            "trust": "claude-auto",
            "proposed": True,
            "_note": f"auto-proposed by overlap (distinct={distinct} terms); 人审时确认/升级类型",
            "truth_source": [f"语义重叠 {distinct} 词 → {title}"],
        })
    return proposed


def main() -> int:
    p = argparse.ArgumentParser(description="回写飞轮：自动把决策卡连回概念层")
    p.add_argument("--card", type=Path, required=True)
    p.add_argument("--wiki-root", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, default=None,
                   help="writeback inbox（默认 <card 所在目录>/../writeback-inbox）")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--min-distinct", type=int, default=3)
    args = p.parse_args()

    if not args.card.exists() or not args.wiki_root.is_dir():
        print("error: --card 或 --wiki-root 无效", file=sys.stderr)
        return 2

    card = json.loads(args.card.read_text(encoding="utf-8"))
    if isinstance(card, list) or "nodes" in (card if isinstance(card, dict) else {}):
        print("error: brain_writeback 处理单卡，不接批量", file=sys.stderr)
        return 2

    new_edges = propose_edges(card, args.wiki_root, args.top, args.min_distinct)
    card.setdefault("edges", [])
    card["edges"].extend(new_edges)

    out_dir = args.out_dir or (args.card.parent.parent / "writeback-inbox")
    out_dir.mkdir(parents=True, exist_ok=True)
    cid = card.get("id", args.card.stem)
    out_path = out_dir / f"{cid}.draft.json"
    out_path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ 回写 draft → {out_path}")
    print(f"   自动提议 {len(new_edges)} 条 derives-from 边（连回概念层）：")
    for e in new_edges:
        print(f"     - derives-from → {e['to']}  ({e['_note']})")
    print(f"   下一步：人审 draft（升级高价值边类型）→ promote_card.py 晋升进 decisions/osa/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
