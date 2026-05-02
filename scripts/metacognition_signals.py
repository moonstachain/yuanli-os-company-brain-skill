#!/usr/bin/env python3
"""
metacognition_signals.py — Phase 5 Metacognition 完整版 v0.1（minimum）

5 类信号：freshness / stale / conflict / weak-evidence / orphan

v0.1 minimum 实现：
  - **stale**：扫 frontmatter `freshness: stale` + `superseded_by:` + 含 supersedes 关系的反方
  - **orphan-commitment**：扫 wiki/decisions/ 中的 commitments[]，找
    - owner 缺失或为空
    - due 已过（早于今天）且 confidence != low
  - **freshness**（已在 brain-surface 输出 date，这里聚合统计）

留给 v0.2：
  - conflict 检测（两个 entity 关系互相矛盾）
  - weak-evidence 自动评分（基于 sources 数 + confidence）

用法：
  metacognition_signals.py            # 输出 markdown 报告
  metacognition_signals.py --json
  metacognition_signals.py --signal stale
  metacognition_signals.py --signal orphan
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path

WIKI_ROOT = Path(".")  # set via --wiki-root or YUANLI_WIKI_ROOT env var


@dataclass
class Signal:
    kind: str        # stale / orphan / conflict / weak-evidence / freshness
    severity: str    # info / warning / error
    page: str
    detail: str
    extra: dict | None = None


# ============================================================
# Frontmatter / 表格解析
# ============================================================


def split_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 4)
    return text[4:end] if end != -1 else ""


def parse_fm_simple(fm_block: str) -> dict:
    fields: dict = {}
    for line in fm_block.splitlines():
        m = re.match(r"^([\w_-]+):\s*(.+?)\s*$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip().strip("\"'")
    return fields


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
                "confidence": cols[4].strip("*"),
            })
    return rows


# ============================================================
# 信号扫描
# ============================================================


def scan_stale() -> list[Signal]:
    """识别 stale 信号：frontmatter freshness: stale OR superseded_by 字段"""
    out: list[Signal] = []
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
            fm_block = split_frontmatter(text)
            fm = parse_fm_simple(fm_block)
            page = str(path.relative_to(WIKI_ROOT))

            if fm.get("freshness", "").lower() == "stale":
                out.append(Signal(
                    kind="stale",
                    severity="warning",
                    page=page,
                    detail="frontmatter 显式标 freshness: stale",
                    extra={"freshness": "stale"},
                ))

            superseded_by = fm.get("superseded_by", "")
            if superseded_by:
                out.append(Signal(
                    kind="stale",
                    severity="info",
                    page=page,
                    detail=f"已被 superseded_by: {superseded_by}",
                    extra={"superseded_by": superseded_by},
                ))
    return out


def _due_is_overdue(due_str: str) -> bool:
    if not due_str or due_str in {"未明确", "持续每日", "已在执行", "(未明确)", "未提供"}:
        return False
    m = re.search(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})", due_str)
    if not m:
        return False
    try:
        d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return d < date.today()
    except ValueError:
        return False


def scan_orphan_commitments() -> list[Signal]:
    """识别 orphan commitment：owner 缺 / due 已过且 confidence != low"""
    out: list[Signal] = []
    d = WIKI_ROOT / "decisions"
    if not d.exists():
        return out
    for path in d.glob("*.md"):
        if path.name.startswith("_") or path.name.endswith(".draft.md"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        page = str(path.relative_to(WIKI_ROOT))
        commitments = parse_commitments_table(text)
        for i, c in enumerate(commitments):
            owner = c.get("owner", "").strip()
            due = c.get("due", "").strip()
            confidence = c.get("confidence", "").strip().lower()
            what = c.get("what", "")[:60]

            if not owner or owner in {"?", "—", "(未提供)"}:
                out.append(Signal(
                    kind="orphan",
                    severity="warning",
                    page=page,
                    detail=f"commitment #{i + 1} 缺 owner：{what}",
                    extra={"index": i, "what": what, "due": due},
                ))

            if _due_is_overdue(due) and confidence != "low":
                out.append(Signal(
                    kind="orphan",
                    severity="warning",
                    page=page,
                    detail=f"commitment #{i + 1} due {due} 已过但未标 low confidence：{what}",
                    extra={"index": i, "what": what, "owner": owner, "due": due, "confidence": confidence},
                ))
    return out


def scan_freshness_summary() -> list[Signal]:
    """聚合 freshness 统计（用 file mtime 兜底）"""
    out: list[Signal] = []
    today = date.today()
    targets = [WIKI_ROOT / "concepts", WIKI_ROOT / "syntheses", WIKI_ROOT / "decisions"]
    bins = {"fresh": 0, "aging": 0, "stale": 0}
    for d in targets:
        if not d.exists():
            continue
        for path in d.rglob("*.md"):
            if path.name.startswith("_"):
                continue
            try:
                mt = datetime.fromtimestamp(path.stat().st_mtime).date()
            except OSError:
                continue
            days = (today - mt).days
            if days < 30:
                bins["fresh"] += 1
            elif days < 180:
                bins["aging"] += 1
            else:
                bins["stale"] += 1

    out.append(Signal(
        kind="freshness",
        severity="info",
        page="(global)",
        detail=f"freshness 分布（按 mtime）：fresh={bins['fresh']} aging={bins['aging']} stale={bins['stale']}",
        extra=bins,
    ))
    return out


# ============================================================
# 渲染
# ============================================================


def render_markdown(signals: list[Signal]) -> str:
    out = ["# Metacognition Signals · Phase 5 v0.1", ""]
    out.append("> 5 信号实现：✅ stale / ✅ orphan / ✅ freshness · ⏳ conflict / ⏳ weak-evidence（v0.2）")
    out.append("")

    by_kind: dict[str, list[Signal]] = {}
    for s in signals:
        by_kind.setdefault(s.kind, []).append(s)

    for kind in ["freshness", "stale", "orphan"]:
        items = by_kind.get(kind, [])
        if not items:
            continue
        emoji = {"freshness": "🌱", "stale": "🍂", "orphan": "🚨"}.get(kind, "·")
        out.append(f"## {emoji} {kind} ({len(items)})")
        out.append("")
        for s in items:
            sev = {"info": "ℹ️", "warning": "⚠️", "error": "🔴"}.get(s.severity, "·")
            out.append(f"- {sev} `{s.page}` — {s.detail}")
        out.append("")

    return "\n".join(out)


# ============================================================
# CLI
# ============================================================


def main() -> int:
    import os as _os

    p = argparse.ArgumentParser(description="Yuanli-OS Company Brain · Metacognition Signals v0.1")
    p.add_argument("--wiki-root", type=Path, default=None,
                   help="Path to your wiki vault root (or set YUANLI_WIKI_ROOT env var)")
    p.add_argument("--signal", choices=["stale", "orphan", "freshness", "all"], default="all")
    p.add_argument("--json", action="store_true")
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

    signals: list[Signal] = []
    if args.signal in {"freshness", "all"}:
        signals.extend(scan_freshness_summary())
    if args.signal in {"stale", "all"}:
        signals.extend(scan_stale())
    if args.signal in {"orphan", "all"}:
        signals.extend(scan_orphan_commitments())

    if args.json:
        print(json.dumps([asdict(s) for s in signals], ensure_ascii=False, indent=2))
    else:
        print(render_markdown(signals))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
