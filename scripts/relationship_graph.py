#!/usr/bin/env python3
"""
relationship_graph.py — Phase 5 G2 typed edges 图分析（v0.1 minimum）

按 [[typed-relationships-schema]] 6 关系类型（commits-to / owns / blocks /
derives-from / supersedes / supports），扫 wiki + decisions/ 抽 typed edges。

数据源：
  1. **显式 edges**: 任意 wiki page frontmatter 含 `relationships:` 字段
  2. **派生 edges**: decisions/ 4 元组自动派生
     - commitments[]    → owner -[commits-to]→ commitment_target
     - counterfactuals[] → final_decision -[supersedes]→ alternative
     - decision page 自身 -[derives-from]→ source_transcript

输出：
  - JSON: 标准 typed edges list（可编程消费）
  - DOT:  graphviz 可视化
  - Mermaid: markdown 嵌入

用法：
  relationship_graph.py --json     # 输出 JSON 到 stdout
  relationship_graph.py --dot --out /tmp/g2.dot
  relationship_graph.py --mermaid  # 输出 Mermaid 块（可贴 wiki/Obsidian）
  relationship_graph.py --stats    # 只看统计
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

WIKI_ROOT = Path(".")  # set via --wiki-root or YUANLI_WIKI_ROOT env var
VALID_RELATION_TYPES = (
    "commits-to", "owns", "blocks", "derives-from", "supersedes", "supports"
)


@dataclass
class Edge:
    source: str          # wikilink-style source (e.g. "[[李明]]")
    type: str            # one of VALID_RELATION_TYPES
    target: str          # wikilink-style target
    evidence: list[str] = field(default_factory=list)
    status: str = "active"          # active | candidate（高价值边待 human-confirm）
    confidence: str = ""
    note: str = ""
    source_kind: str = "explicit"  # explicit | derived-from-decision | osa-card-json
    trust: str = ""      # claude-auto | claude-unilateral | human-confirmed（两层统一信任尺）
    cross: str = ""      # decision->concept | decision->source | decision->decision | concept->concept


# 高价值边：未经 human-confirm 不计入正式图（CONTRACT §2）
HIGH_VALUE_TYPES = ("supersedes", "blocks")


# ============================================================
# Frontmatter parsing
# ============================================================


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 4)
    if end == -1:
        return "", text
    return text[4:end], text[end + 4:]


def parse_explicit_relationships(fm_block: str, source_label: str) -> list[Edge]:
    """从 frontmatter `relationships:` 字段（YAML list）解析显式 typed edges。

    极简 YAML 解析：仅识别 `- type:` 起手的 list item，逐字段填充。
    不引入 yaml lib（minimum dependency）。
    """
    if "relationships:" not in fm_block:
        return []

    edges: list[Edge] = []
    in_block = False
    current: dict | None = None
    indent = None

    for line in fm_block.splitlines():
        stripped = line.lstrip()
        line_indent = len(line) - len(stripped)

        if stripped.startswith("relationships:"):
            in_block = True
            indent = None
            continue

        if not in_block:
            continue

        # 退出 block：缩进回退到 0 且不是 list item
        if not stripped:
            continue
        if line_indent == 0 and not stripped.startswith("-"):
            break

        if stripped.startswith("- type:"):
            if current and current.get("type") and current.get("target"):
                edges.append(_dict_to_edge(current, source_label))
            current = {"type": stripped.split(":", 1)[1].strip().strip("\"'")}
            indent = line_indent
            continue

        if current is None:
            continue

        # field 行（缩进比 - 多 2）
        m = re.match(r"^([\w-]+):\s*(.*?)\s*$", stripped)
        if m:
            key, val = m.group(1), m.group(2).strip().strip("\"'")
            if key in {"target", "status", "since", "until", "confidence", "note"}:
                current[key] = val
            elif key == "evidence":
                current["evidence"] = []  # list 收集开始
        elif stripped.startswith("- "):
            # evidence 子列表项
            current.setdefault("evidence", []).append(stripped[2:].strip().strip("\"'"))

    if current and current.get("type") and current.get("target"):
        edges.append(_dict_to_edge(current, source_label))

    return edges


def _dict_to_edge(d: dict, source_label: str) -> Edge:
    return Edge(
        source=source_label,
        type=d.get("type", ""),
        target=d.get("target", ""),
        evidence=d.get("evidence", []),
        status=d.get("status", "active"),
        confidence=d.get("confidence", ""),
        note=d.get("note", ""),
        source_kind="explicit",
    )


# ============================================================
# Decision 4 元组 → 派生 edges
# ============================================================


def parse_commitments_table(text: str) -> list[dict]:
    m = re.search(r"## 2\. Commitments[\s\S]*?\n\n(\|[^\n]+\|.*?)\n\n", text, re.DOTALL)
    if not m:
        return []
    rows = []
    for line in m.group(1).splitlines():
        if not line.startswith("|") or "---" in line or "Owner" in line:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) >= 5:
            rows.append({
                "owner": cols[0],
                "what": cols[1],
                "due": cols[2],
                "source_quote": cols[3].strip('"'),
                "confidence": cols[4],
            })
    return rows


def parse_counterfactuals(text: str) -> list[dict]:
    """从 ## 4. Counterfactuals 抽 alternative + rejected_reason"""
    m = re.search(r"## 4\. Counterfactuals[\s\S]*?(?=^## |\Z)", text, re.MULTILINE)
    if not m:
        return []
    section = m.group(0)
    items = re.findall(r"^- \*\*(.+?)\*\*\s*\n\s*- 否决原因：(.+?)\n", section, re.MULTILINE)
    return [{"alternative": alt, "rejected_reason": reason} for alt, reason in items]


def parse_final_decision(text: str) -> str:
    m = re.search(r"\*\*最终决定\*\*:\s*(.+?)\n", text)
    return m.group(1).strip() if m else ""


def derive_edges_from_decision(decision_path: Path) -> list[Edge]:
    """从 decisions/<file>.md 派生 typed edges"""
    text = decision_path.read_text(encoding="utf-8", errors="replace")
    decision_label = f"[[{decision_path.stem}]]"
    edges: list[Edge] = []

    # 1) commitments → owner -[commits-to]→ decision (作为承诺承载)
    for c in parse_commitments_table(text):
        owner = c["owner"]
        what = c["what"]
        if owner and what:
            edges.append(Edge(
                source=f"[[{owner}]]",
                type="commits-to",
                target=decision_label,
                evidence=[decision_label],
                status="active",
                confidence=c.get("confidence", "").strip("*"),
                note=what[:80],
                source_kind="derived-from-decision",
            ))

    # 2) counterfactuals → final_decision -[supersedes]→ alternative
    final = parse_final_decision(text)
    if final:
        for cf in parse_counterfactuals(text):
            alt = cf["alternative"]
            if alt:
                edges.append(Edge(
                    source=decision_label,
                    type="supersedes",
                    target=f"[[{alt}]]",
                    evidence=[decision_label],
                    status="active",
                    note=cf.get("rejected_reason", "")[:80],
                    source_kind="derived-from-decision",
                ))

    # 3) decision 自身 -[derives-from]→ source_transcript
    fm_block, _ = split_frontmatter(text)
    m = re.search(r"^source_transcript:\s*(.+?)\s*$", fm_block, re.MULTILINE)
    if m:
        transcript = m.group(1).strip().strip("\"'")
        if transcript and transcript != "(本次对话)":
            edges.append(Edge(
                source=decision_label,
                type="derives-from",
                target=f"[[{Path(transcript).stem}]]",
                evidence=[decision_label],
                status="active",
                note=f"抽自 transcript: {Path(transcript).name}",
                source_kind="derived-from-decision",
            ))

    return edges


# ============================================================
# OSA 决策卡 JSON → 跨层 typed edges（两层大脑焊接层）
# ============================================================


def _normalize_target(to: str) -> str:
    """concept-name / card-id 原样；source 路径取 stem。统一成 wikilink。"""
    t = to.strip()
    if "/" in t or t.endswith(".md"):
        t = Path(t).stem
    return f"[[{t}]]"


def parse_osa_card_edges(card_path: Path) -> list[Edge]:
    """从一张/一批 OSA 卡 JSON 的 edges[] 抽跨层 typed edges。

    接受三种 JSON 形状：单卡(dict) / 批量(顶层 list) / {nodes:[...]}。
    高价值边(supersedes/blocks)若非 human-confirmed 或带 _flag → status=candidate。
    """
    try:
        data = json.loads(card_path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError, ValueError):
        return []

    if isinstance(data, list):
        cards = data
    elif isinstance(data, dict) and isinstance(data.get("nodes"), list):
        cards = data["nodes"]
    elif isinstance(data, dict):
        cards = [data]
    else:
        return []

    edges: list[Edge] = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        cid = card.get("id") or card.get("title") or card_path.stem
        src_label = f"[[{cid}]]"
        for e in card.get("edges", []) or []:
            if not isinstance(e, dict) or not e.get("type") or not e.get("to"):
                continue
            etype = str(e.get("type", "")).strip()
            trust = str(e.get("trust", "")).strip()
            flagged = bool(e.get("_flag"))
            ts = e.get("truth_source", [])
            if not isinstance(ts, list):
                ts = [str(ts)]
            status = "active"
            if flagged or (etype in HIGH_VALUE_TYPES and trust != "human-confirmed"):
                status = "candidate"
            edges.append(Edge(
                source=src_label,
                type=etype,
                target=_normalize_target(str(e.get("to", ""))),
                evidence=ts,
                status=status,
                confidence=trust,          # 向后兼容旧字段
                note=str(e.get("_flag", "") or "")[:120],
                source_kind="osa-card-json",
                trust=trust,
                cross=str(e.get("cross", "")).strip(),
            ))
    return edges


# ============================================================
# 扫描入口
# ============================================================


def scan_explicit() -> list[Edge]:
    """扫 wiki 中所有含 relationships 的 page"""
    edges: list[Edge] = []
    targets = ["concepts", "entities", "syntheses", "comparisons", "operations", "decisions"]
    for sub in targets:
        d = WIKI_ROOT / sub
        if not d.exists():
            continue
        for path in d.rglob("*.md"):
            if path.name.startswith("_"):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            fm_block, _ = split_frontmatter(text)
            if not fm_block or "relationships:" not in fm_block:
                continue
            label = f"[[{path.stem}]]"
            edges.extend(parse_explicit_relationships(fm_block, label))
    return edges


def scan_derived() -> list[Edge]:
    """从 decisions/ 派生 edges（不动源文件）"""
    edges: list[Edge] = []
    d = WIKI_ROOT / "decisions"
    if not d.exists():
        return edges
    for path in d.glob("*.md"):
        if path.name.startswith("_") or path.name.endswith(".draft.md"):
            continue
        edges.extend(derive_edges_from_decision(path))
    return edges


def scan_osa_cards(osa_dir: Path | None = None) -> list[Edge]:
    """扫 OSA 决策卡 JSON 的 edges[]（默认 decisions/osa/，可 --osa-dir 覆盖）"""
    edges: list[Edge] = []
    d = osa_dir if osa_dir is not None else (WIKI_ROOT / "decisions" / "osa")
    if not d.exists():
        return edges
    for path in d.rglob("*.json"):
        if path.name.startswith("_"):
            continue
        edges.extend(parse_osa_card_edges(path))
    return edges


# ============================================================
# 渲染
# ============================================================


def render_dot(edges: list[Edge]) -> str:
    out = ["digraph G2 {", '  rankdir=LR;', '  node [shape=box, style=rounded, fontname="Helvetica"];']
    for e in edges:
        s = e.source.strip("[]")
        t = e.target.strip("[]")
        kind = "solid" if e.source_kind == "explicit" else "dashed"
        out.append(f'  "{s}" -> "{t}" [label="{e.type}", style={kind}];')
    out.append("}")
    return "\n".join(out)


def render_mermaid(edges: list[Edge]) -> str:
    out = ["```mermaid", "graph LR"]
    seen = set()
    for i, e in enumerate(edges):
        s = _safe_id(e.source)
        t = _safe_id(e.target)
        if s not in seen:
            out.append(f'  {s}[{e.source.strip("[]")}]')
            seen.add(s)
        if t not in seen:
            out.append(f'  {t}[{e.target.strip("[]")}]')
            seen.add(t)
        edge_op = "-->" if e.source_kind == "explicit" else "-.->"
        out.append(f'  {s} {edge_op}|{e.type}| {t}')
    out.append("```")
    return "\n".join(out)


def _safe_id(label: str) -> str:
    raw = label.strip("[]")
    return "n" + str(abs(hash(raw)) % 10**8)


def render_stats(edges: list[Edge]) -> str:
    by_type: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    invalid = []
    for e in edges:
        by_type[e.type] = by_type.get(e.type, 0) + 1
        by_kind[e.source_kind] = by_kind.get(e.source_kind, 0) + 1
        if e.type not in VALID_RELATION_TYPES:
            invalid.append((e.source, e.type, e.target))

    nodes = set()
    for e in edges:
        nodes.add(e.source)
        nodes.add(e.target)

    candidates = [e for e in edges if e.status == "candidate"]
    active = len(edges) - len(candidates)

    lines = ["# G2 typed edges · 图统计", ""]
    lines.append(f"- 边数：{len(edges)}（active {active} · candidate {len(candidates)}）")
    lines.append(f"- 节点数：{len(nodes)}")
    lines.append("")
    lines.append("## 按类型分布")
    for t in VALID_RELATION_TYPES:
        if t in by_type:
            lines.append(f"- `{t}`: {by_type[t]}")
    lines.append("")
    lines.append("## 按来源分布")
    for k, v in by_kind.items():
        lines.append(f"- {k}: {v}")

    # 跨层边分布（仅 osa-card-json 携带 cross）
    by_cross: dict[str, int] = {}
    for e in edges:
        if e.cross:
            by_cross[e.cross] = by_cross.get(e.cross, 0) + 1
    if by_cross:
        lines.append("")
        lines.append("## 跨层分布（两层大脑焊接）")
        for k, v in sorted(by_cross.items()):
            lines.append(f"- {k}: {v}")

    if candidates:
        lines.append("")
        lines.append("## 🔶 candidate 边（高价值边待 human-confirm，未计入正式图）")
        for e in candidates:
            note = f" — {e.note}" if e.note else ""
            lines.append(f"- {e.source} -{e.type}-> {e.target} (trust={e.trust or '?'}){note}")

    if invalid:
        lines.append("")
        lines.append("## ⚠️ 无效 relation type")
        for s, t, tgt in invalid:
            lines.append(f"- {s} -{t}-> {tgt}")
    return "\n".join(lines)


# ============================================================
# CLI
# ============================================================


def main() -> int:
    import os as _os

    p = argparse.ArgumentParser(description="Yuanli-OS Company Brain · typed edges (explicit + derived)")
    p.add_argument("--wiki-root", type=Path, default=None,
                   help="Path to your wiki vault root (or set YUANLI_WIKI_ROOT env var)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--dot", action="store_true")
    p.add_argument("--mermaid", action="store_true")
    p.add_argument("--stats", action="store_true")
    p.add_argument("--out", type=Path)
    p.add_argument("--no-derived", action="store_true", help="explicit only, skip derivation from decisions/")
    p.add_argument("--no-osa", action="store_true", help="skip OSA decision-card JSON edges")
    p.add_argument("--osa-dir", type=Path, default=None,
                   help="OSA 卡 JSON 目录（默认 <wiki>/decisions/osa；可指向 dry-run 目录验证）")
    args = p.parse_args()

    global WIKI_ROOT
    root = args.wiki_root or Path(_os.environ.get("YUANLI_WIKI_ROOT", "")).expanduser()
    if not root or str(root) == ".":
        print("error: --wiki-root <path> required (or set YUANLI_WIKI_ROOT env var)", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: wiki root does not exist: {root}", file=sys.stderr)
        return 2
    WIKI_ROOT = root

    edges = scan_explicit()
    if not args.no_derived:
        edges.extend(scan_derived())
    if not args.no_osa:
        edges.extend(scan_osa_cards(args.osa_dir))

    if args.dot:
        out_text = render_dot(edges)
    elif args.mermaid:
        out_text = render_mermaid(edges)
    elif args.stats:
        out_text = render_stats(edges)
    else:
        # default JSON
        out_text = json.dumps([asdict(e) for e in edges], ensure_ascii=False, indent=2)

    if args.out:
        args.out.write_text(out_text, encoding="utf-8")
        print(f"✅ {len(edges)} edges 写入 {args.out}", file=sys.stderr)
    else:
        print(out_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
