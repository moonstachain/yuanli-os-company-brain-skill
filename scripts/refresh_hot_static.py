#!/usr/bin/env python3
"""
refresh_hot_static.py — 静态扫 wiki，刷新 _hot.md 真数据。

不调任何 LLM，纯 fs 扫描。可由 launchd 触发或人工跑。
作为 refresh_ai_entry.sh（LLM 路径）的兜底/补充。

源数据：
  - wiki/decisions/   最近 14 天
  - wiki/concepts/    mtime 14 天内 top 10
  - wiki/sources/     mtime 7 天内（中文文件名+大文件优先）top 5
  - wiki/operations/audits/  最近 30 天
"""

from __future__ import annotations
import os
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

_wiki_env = os.environ.get("WIKI_ROOT")
if not _wiki_env:
    sys.exit(
        "ERROR: WIKI_ROOT environment variable not set.\n"
        "  Usage: WIKI_ROOT=/abs/path/to/vault python3 refresh_hot_static.py"
    )
WIKI = Path(_wiki_env).expanduser()
HOT_PATH = WIKI / "_hot.md"
NOW = datetime.now()
DECISIONS_WINDOW_D = 60   # 决策稀疏，窗口拉大
CONCEPTS_WINDOW_D = 14
SOURCES_WINDOW_D = 7
AUDITS_WINDOW_D = 30
CALENDAR_PATH = WIKI / "operations" / "audits" / "_calendar.md"


def read_frontmatter_title(path: Path) -> Optional[str]:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            head = f.read(2000)
        m = re.search(r"^title:\s*[\"']?([^\"'\n]+)[\"']?\s*$", head, re.MULTILINE)
        if m:
            return m.group(1).strip()
    except Exception:
        return None
    return None


def fmt_size(n: int) -> str:
    if n < 1024: return f"{n}B"
    if n < 1024 * 1024: return f"{n/1024:.1f}K"
    return f"{n/(1024*1024):.1f}M"


def scan_decisions() -> list[str]:
    out = []
    cutoff = NOW - timedelta(days=DECISIONS_WINDOW_D)
    for p in (WIKI / "decisions").rglob("*.md"):
        if p.name.startswith("_"): continue
        try:
            mt = datetime.fromtimestamp(p.stat().st_mtime)
            if mt < cutoff: continue
            slug = p.stem
            title = read_frontmatter_title(p) or slug
            out.append((mt, slug, title, p.relative_to(WIKI)))
        except OSError:
            continue
    out.sort(reverse=True)
    return [
        f"- {mt.strftime('%Y-%m-%d')} · [[{slug}|{title}]]"
        for mt, slug, title, _ in out[:5]
    ] or ["- (近 60 天 decisions/ 无新增)"]


def scan_concepts_recent() -> list[str]:
    out = []
    cutoff = NOW - timedelta(days=CONCEPTS_WINDOW_D)
    for p in (WIKI / "concepts").glob("*.md"):
        if p.name.startswith("_"): continue
        try:
            mt = datetime.fromtimestamp(p.stat().st_mtime)
            if mt < cutoff: continue
            sz = p.stat().st_size
            slug = p.stem
            title = read_frontmatter_title(p) or slug
            out.append((mt, sz, slug, title))
        except OSError:
            continue
    # 排序：最近 mtime 优先 + 大于 1KB
    out.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [
        f"- {mt.strftime('%Y-%m-%d')} · [[{slug}|{title}]] ({fmt_size(sz)})"
        for mt, sz, slug, title in out[:10]
    ] or ["- (近 14 天 concepts/ 无更新)"]


def scan_sources_recent() -> list[str]:
    """近 7 天高密度 source（按大小+mtime 综合）"""
    out = []
    cutoff = NOW - timedelta(days=SOURCES_WINDOW_D)
    sources_root = WIKI / "sources"
    if not sources_root.exists(): return ["- (sources/ 不存在)"]
    for p in sources_root.rglob("*.md"):
        try:
            mt = datetime.fromtimestamp(p.stat().st_mtime)
            if mt < cutoff: continue
            sz = p.stat().st_size
            if sz < 2000: continue  # 小文件多是占位
            rel = p.relative_to(WIKI)
            title = read_frontmatter_title(p) or p.stem
            out.append((mt, sz, rel, title))
        except OSError:
            continue
    out.sort(key=lambda t: (t[1], t[0]), reverse=True)  # 大文件优先
    return [
        f"- {mt.strftime('%Y-%m-%d')} · [[{rel}|{title}]] ({fmt_size(sz)})"
        for mt, sz, rel, title in out[:5]
    ] or ["- (近 7 天高密度 source 无新增)"]


def scan_audits_recent() -> list[str]:
    out = []
    cutoff = NOW - timedelta(days=AUDITS_WINDOW_D)
    audits_root = WIKI / "operations" / "audits"
    if not audits_root.exists(): return []
    for p in audits_root.rglob("*.md"):
        if p.name.startswith("_"): continue
        try:
            mt = datetime.fromtimestamp(p.stat().st_mtime)
            if mt < cutoff: continue
            slug = p.stem
            title = read_frontmatter_title(p) or slug
            out.append((mt, slug, title))
        except OSError:
            continue
    out.sort(reverse=True)
    return [f"- {mt.strftime('%Y-%m-%d')} · {title}" for mt, _, title in out[:3]]


def scan_calendar_due() -> list[str]:
    """读 _calendar.md 找即将到期的 review item"""
    if not CALENDAR_PATH.exists(): return []
    out = []
    try:
        text = CALENDAR_PATH.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    for line in text.splitlines():
        m = re.match(r"\s*-\s*(\d{4}-\d{2}-\d{2})\s*·\s*(.+)", line)
        if m:
            try:
                d = datetime.strptime(m.group(1), "%Y-%m-%d")
                days_to = (d - NOW).days
                if -7 <= days_to <= 30:
                    flag = "⏰" if days_to <= 7 else "📅"
                    out.append(f"- {flag} {m.group(1)} (T+{days_to}d) · {m.group(2)}")
            except ValueError:
                continue
    return out


def count_total(dir_path: Path, pattern: str = "*.md") -> int:
    if not dir_path.exists(): return 0
    return sum(1 for _ in dir_path.glob(pattern))


def render_hot() -> str:
    lines = []
    lines.append("---")
    lines.append("title: Hot Cache · 本周热区")
    lines.append("type: hot-cache")
    lines.append(f"updated: {NOW.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"window_days: {CONCEPTS_WINDOW_D}")
    lines.append("origin: refresh_hot_static.py (no LLM)")
    lines.append("---")
    lines.append("")
    lines.append("# Hot Cache · 本周热区")
    lines.append("")
    lines.append(f"> **AI 契约**：每次回答前先读这份 + `_ai-entry.md`。这两份 ~1500 字足以定位 90% 答案。除非这两份明确指向，**不扫全 vault**。")
    lines.append("")
    lines.append(f"_最后刷新：{NOW.strftime('%Y-%m-%d %H:%M')} · 由 `scripts/refresh_hot_static.py` 静态扫产出（无 LLM 调用）_")
    lines.append("")

    # 决策
    lines.append(f"## 本周新决策（近 {DECISIONS_WINDOW_D} 天）")
    lines.append("")
    lines.extend(scan_decisions())
    lines.append("")

    # 概念
    lines.append(f"## 本周更新的概念（mtime ≤ {CONCEPTS_WINDOW_D} 天 · top 10）")
    lines.append("")
    lines.extend(scan_concepts_recent())
    lines.append("")

    # source
    lines.append(f"## 最近高密度 source（mtime ≤ {SOURCES_WINDOW_D} 天 · top 5）")
    lines.append("")
    lines.extend(scan_sources_recent())
    lines.append("")

    # audits
    audits = scan_audits_recent()
    if audits:
        lines.append(f"## 最近审计（近 {AUDITS_WINDOW_D} 天）")
        lines.append("")
        lines.extend(audits)
        lines.append("")

    # 即将到期的 review
    cal = scan_calendar_due()
    if cal:
        lines.append("## 即将到期的 review / commitment")
        lines.append("")
        lines.extend(cal)
        lines.append("")

    # stats
    lines.append("## 系统 stats")
    lines.append("")
    lines.append(f"- concepts/: {count_total(WIKI / 'concepts')} 篇")
    lines.append(f"- syntheses/: {count_total(WIKI / 'syntheses')} 篇")
    lines.append(f"- decisions/: {count_total(WIKI / 'decisions')} 篇")
    lines.append(f"- sources/transcripts/: {count_total(WIKI / 'sources' / 'transcripts')} 篇")
    lines.append("")

    # 使用提示
    lines.append("---")
    lines.append("")
    lines.append("> **使用提示**：如果你（AI）发现答案不在 hot cache 内，下一步是**问用户**，不是去扫 `concepts/`。问题：「我没找到，要我开放扫整 vault 吗？」")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Activity log")
    lines.append("")
    lines.append(f"- {NOW.strftime('%Y-%m-%d %H:%M')} — refreshed by `refresh_hot_static.py` (static, no LLM)")
    return "\n".join(lines)


def main() -> int:
    if not WIKI.exists():
        print(f"ERROR: {WIKI} not found", file=sys.stderr)
        return 1
    content = render_hot()
    HOT_PATH.write_text(content, encoding="utf-8")
    print(f"✓ {HOT_PATH} written ({len(content)} chars)")
    print(f"  decisions: {len(scan_decisions())} listed")
    print(f"  concepts:  {len(scan_concepts_recent())} listed")
    print(f"  sources:   {len(scan_sources_recent())} listed")
    print(f"  calendar:  {len(scan_calendar_due())} due-soon items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
