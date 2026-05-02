#!/usr/bin/env python3
"""
brain_surface.py — Right-time recall (Phase 1 minimum).

Surfaces related concepts / open commitments / historical drafts before the user
drafts any non-trivial output. Reads only your wiki — no proprietary backends.

Datasources (all under --wiki-root):
  - concepts/      definitions
  - syntheses/     cross-source themes
  - decisions/     4-tuple meeting outcomes
  - sources/       transcripts and raw notes
  - _factory/ artifacts/ articles/   historical drafts (whichever you use)

Usage:
  python3 brain_surface.py --wiki-root ~/path/to/vault --topic "your topic here"
  python3 brain_surface.py --wiki-root ~/path/to/vault --topic "..." --role student
  python3 brain_surface.py --wiki-root ~/path/to/vault --topic "..." --json

Role lens:
  self      — see everything
  student   — see institutional + shared circles only
  partner   — see institutional only
  agent     — see institutional only (capability-bounded)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

WIKI_ROOT = Path(".")  # set via --wiki-root or YUANLI_WIKI_ROOT env var

PATH_TO_CIRCLE = {
    "concepts": "institutional",
    "syntheses": "institutional",
    "comparisons": "institutional",
    "operations": "institutional",
    "decisions": "institutional",
    "entities": "institutional",
    "_factory": "shared",
    "artifacts": "shared",
    "articles": "shared",
    "sources/transcripts": "raw",
    "sources/get-biji": "raw",
    "sources/meeting-notes": "raw",
    "insights": "individual",
    "drafts": "individual",
}

ROLE_VISIBLE_CIRCLES = {
    "self":     {"individual", "shared", "institutional", "raw", "tooling", "unknown"},
    "student":  {"shared", "institutional"},
    "partner":  {"institutional"},
    "agent":    {"institutional"},
}


@dataclass
class Hit:
    path: str
    title: str
    snippet: str
    circle: str
    date: str = ""
    score: int = 0
    category: str = ""


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 4)
    if end == -1:
        return "", text
    return text[4:end], text[end + 4:]


def parse_fm(fm_block: str) -> dict:
    fields: dict = {}
    for line in fm_block.splitlines():
        m = re.match(r"^([\w_-]+):\s*(.+?)\s*$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip().strip("\"'")
    return fields


def infer_circle(fm: dict, path: Path) -> str:
    explicit = fm.get("circle", "").strip().lower()
    if explicit:
        return explicit
    try:
        rel = path.relative_to(WIKI_ROOT)
    except ValueError:
        rel = path
    parts = rel.parts
    if len(parts) >= 2:
        prefix = "/".join(parts[:2])
        if prefix in PATH_TO_CIRCLE:
            return PATH_TO_CIRCLE[prefix]
    if parts and parts[0] in PATH_TO_CIRCLE:
        return PATH_TO_CIRCLE[parts[0]]
    return "unknown"


def first_title(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def first_snippet(text: str, query_terms: list[str], max_len: int = 120) -> str:
    body_lines = [l for l in text.splitlines()
                  if l.strip() and not l.startswith("#") and not l.startswith("---")]
    for line in body_lines:
        if any(t.lower() in line.lower() for t in query_terms if len(t) >= 2):
            return line.strip()[:max_len]
    return body_lines[0][:max_len] if body_lines else ""


def parse_topic(topic: str) -> list[str]:
    terms = re.findall(r"[\w一-鿿]+", topic.lower())
    return [t for t in terms if len(t) >= 2]


def score_hit(text: str, terms: list[str]) -> int:
    text_l = text.lower()
    return sum(text_l.count(t) for t in terms)


def scan_dir(subdir: Path, terms: list[str], visible_circles: set[str],
             category: str, limit: int = 5) -> list[Hit]:
    if not subdir.exists():
        return []
    hits: list[Hit] = []
    for path in subdir.rglob("*.md"):
        if path.name.startswith("_") or path.name.endswith(".draft.md"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        score = score_hit(text, terms)
        if score == 0:
            continue
        fm_block, body = split_frontmatter(text)
        fm = parse_fm(fm_block)
        circle = infer_circle(fm, path)
        if circle not in visible_circles:
            continue
        try:
            rel = str(path.relative_to(WIKI_ROOT))
        except ValueError:
            rel = str(path)
        hits.append(Hit(
            path=rel,
            title=first_title(body) or fm.get("title", path.stem),
            snippet=first_snippet(body, terms),
            circle=circle,
            date=fm.get("date", "") or fm.get("created", ""),
            score=score,
            category=category,
        ))
    hits.sort(key=lambda h: -h.score)
    return hits[:limit]


def render_markdown(topic: str, role: str, sections: dict[str, list[Hit]]) -> str:
    out = [
        f"## Brain Surface · topic: `{topic}` · role: `{role}`",
        "",
        f"_Visible circles: {sorted(ROLE_VISIBLE_CIRCLES[role])}_",
        "",
    ]
    total = sum(len(v) for v in sections.values())
    if total == 0:
        out.append("_(no hits - try a less specific topic, or widen role lens)_")
        return "\n".join(out)

    for cat, hits in sections.items():
        if not hits:
            continue
        out.append(f"### {cat} ({len(hits)})")
        out.append("")
        for h in hits:
            date_part = f" - {h.date}" if h.date else ""
            out.append(f"- `{h.path}` - {h.title}{date_part}")
            if h.snippet:
                out.append(f"  > {h.snippet}")
        out.append("")
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description="Yuanli-OS Company Brain - right-time surface (Phase 1)")
    p.add_argument("--wiki-root", type=Path, default=None,
                   help="Path to your wiki vault root (or set YUANLI_WIKI_ROOT env var)")
    p.add_argument("--topic", required=True, help="The topic you are about to draft about")
    p.add_argument("--role", choices=list(ROLE_VISIBLE_CIRCLES), default="self")
    p.add_argument("--limit", type=int, default=5, help="Max hits per category (default 5)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    global WIKI_ROOT
    root = args.wiki_root or Path(os.environ.get("YUANLI_WIKI_ROOT", "")).expanduser()
    if not root or str(root) == ".":
        print("error: --wiki-root <path> required (or set YUANLI_WIKI_ROOT env var)", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: wiki root does not exist: {root}", file=sys.stderr)
        return 2
    WIKI_ROOT = root

    visible = ROLE_VISIBLE_CIRCLES[args.role]
    terms = parse_topic(args.topic)
    if not terms:
        print("error: --topic must contain at least one >=2-char term", file=sys.stderr)
        return 2

    sections = {
        "Concepts (institutional)":   scan_dir(WIKI_ROOT / "concepts",   terms, visible, "concept",   args.limit),
        "Syntheses (institutional)":  scan_dir(WIKI_ROOT / "syntheses",  terms, visible, "synthesis", args.limit),
        "Decisions (institutional)":  scan_dir(WIKI_ROOT / "decisions",  terms, visible, "decision",  args.limit),
        "Transcripts / raw notes":    scan_dir(WIKI_ROOT / "sources",    terms, visible, "raw",       args.limit),
        "Drafts / artifacts":         scan_dir(WIKI_ROOT / "_factory",   terms, visible, "draft",     args.limit) +
                                      scan_dir(WIKI_ROOT / "artifacts",  terms, visible, "artifact",  args.limit) +
                                      scan_dir(WIKI_ROOT / "articles",   terms, visible, "article",   args.limit),
    }

    if args.json:
        flat = {k: [asdict(h) for h in v] for k, v in sections.items()}
        print(json.dumps({"topic": args.topic, "role": args.role, "sections": flat},
                         ensure_ascii=False, indent=2))
    else:
        print(render_markdown(args.topic, args.role, sections))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
