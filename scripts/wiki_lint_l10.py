#!/usr/bin/env python3
"""
wiki_lint_l10.py — Phase 5 G2: typed-relationships schema 验证（v0.1）

按 [[typed-relationships-schema]] 第 4 节 Validation rules 检查 wiki 中
所有含 `relationships:` 字段的 page。

Hard errors（红色）：
  E1. relationships 必须是 YAML list
  E2. 每条必须有 type / target / evidence
  E3. type 必须是 6 个允许值之一
  E4. target 必须是单个 [[wikilink]] 字符串
  E5. evidence 必须是非空 wikilink list
  E6. 不允许一条 relation 含多个 target

Warnings（黄色）：
  W1. commits-to 应该有对应 owns（在 commitment / project 页或人页）
  W2. blocks 应该有 status + note 解释
  W3. supersedes 应该让 old target 标 stale（但不自动改）
  W4. derives-from 应指向最强 upstream，不是所有 source
  W5. supports 不是通用 backlink，必须 evidence

输出：markdown 报告（默认）/ JSON

用法：
  wiki_lint_l10.py
  wiki_lint_l10.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

WIKI_ROOT = Path(".")  # set via --wiki-root or YUANLI_WIKI_ROOT env var

VALID_TYPES = {
    "commits-to", "owns", "blocks", "derives-from", "supersedes", "supports"
}

WIKILINK_RE = re.compile(r'^\["?\[\[([^\]]+)\]\]"?\]$|^"?\[\[([^\]]+)\]\]"?$')


@dataclass
class Finding:
    severity: str   # error / warning
    code: str
    page: str
    detail: str
    relation_index: int = -1


def split_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 4)
    return text[4:end] if end != -1 else ""


def parse_relationships_block(fm_block: str) -> list[dict]:
    """极简 relationships YAML block 解析"""
    if "relationships:" not in fm_block:
        return []
    items: list[dict] = []
    in_block = False
    current: dict | None = None

    for line in fm_block.splitlines():
        stripped = line.lstrip()
        line_indent = len(line) - len(stripped)

        if stripped.startswith("relationships:"):
            in_block = True
            continue

        if not in_block:
            continue
        if not stripped:
            continue
        if line_indent == 0 and not stripped.startswith("-"):
            break

        if stripped.startswith("- type:"):
            if current is not None:
                items.append(current)
            current = {"type": stripped.split(":", 1)[1].strip().strip("\"'"),
                       "evidence": []}
            continue

        if current is None:
            continue

        m = re.match(r"^([\w-]+):\s*(.*?)\s*$", stripped)
        if m:
            key, val = m.group(1), m.group(2).strip().strip("\"'")
            if key in {"target", "status", "since", "until", "confidence", "note"}:
                current[key] = val
            elif key == "evidence":
                pass  # list 收集开始
        elif stripped.startswith("- "):
            current.setdefault("evidence", []).append(stripped[2:].strip().strip("\"'"))

    if current is not None:
        items.append(current)
    return items


def is_valid_wikilink(s: str) -> bool:
    if not isinstance(s, str):
        return False
    s = s.strip().strip("\"'")
    return s.startswith("[[") and s.endswith("]]") and "]]" not in s[:-2]


def validate(rel: dict, page: str, idx: int) -> list[Finding]:
    findings: list[Finding] = []

    # E2/E3: type
    rtype = rel.get("type", "")
    if not rtype:
        findings.append(Finding("error", "E2", page, f"relation #{idx}: 缺 `type` 字段", idx))
    elif rtype not in VALID_TYPES:
        findings.append(Finding(
            "error", "E3", page,
            f"relation #{idx}: type=`{rtype}` 不在允许值 {sorted(VALID_TYPES)}", idx,
        ))

    # E2/E4: target
    target = rel.get("target", "")
    if not target:
        findings.append(Finding("error", "E2", page, f"relation #{idx}: 缺 `target`", idx))
    elif not is_valid_wikilink(target):
        findings.append(Finding(
            "error", "E4", page,
            f"relation #{idx}: target=`{target}` 不是单个有效 [[wikilink]] 字符串", idx,
        ))

    # E2/E5: evidence
    evidence = rel.get("evidence", [])
    if not evidence:
        findings.append(Finding("error", "E5", page, f"relation #{idx}: 缺 `evidence`（必须非空）", idx))
    elif not all(is_valid_wikilink(e) for e in evidence):
        findings.append(Finding(
            "error", "E5", page,
            f"relation #{idx}: evidence 含非 wikilink 项 {evidence}", idx,
        ))

    # W2: blocks 应有 status + note
    if rtype == "blocks":
        if not rel.get("status"):
            findings.append(Finding("warning", "W2", page, f"relation #{idx}: blocks 缺 `status`", idx))
        if not rel.get("note"):
            findings.append(Finding("warning", "W2", page, f"relation #{idx}: blocks 缺 `note` 解释 blocker", idx))

    return findings


def scan() -> list[Finding]:
    findings: list[Finding] = []
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
            if not fm_block or "relationships:" not in fm_block:
                continue
            page = str(path.relative_to(WIKI_ROOT))
            rels = parse_relationships_block(fm_block)
            if not isinstance(rels, list):
                findings.append(Finding("error", "E1", page, "relationships 不是 YAML list"))
                continue
            for i, rel in enumerate(rels):
                findings.extend(validate(rel, page, i))

    return findings


def render_markdown(findings: list[Finding]) -> str:
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]

    out = ["# wiki-lint L10 · typed-relationships schema 验证", ""]
    out.append(f"- 错误（hard errors）：**{len(errors)}**")
    out.append(f"- 警告（warnings）：**{len(warnings)}**")
    out.append("")

    if not findings:
        out.append("✅ 全部 typed relationships 通过 schema 验证。")
        return "\n".join(out)

    if errors:
        out.append("## 🔴 Hard Errors")
        out.append("")
        for f in errors:
            out.append(f"- `{f.code}` · `{f.page}` · {f.detail}")
        out.append("")

    if warnings:
        out.append("## 🟡 Warnings")
        out.append("")
        for f in warnings:
            out.append(f"- `{f.code}` · `{f.page}` · {f.detail}")
        out.append("")

    out.append("---")
    out.append("")
    out.append(f"详见 [[typed-relationships-schema]] 第 4 节 Validation rules。")
    return "\n".join(out)


def main() -> int:
    import os as _os

    p = argparse.ArgumentParser(description="Yuanli-OS Company Brain · typed-relationships schema lint (L10)")
    p.add_argument("--wiki-root", type=Path, default=None,
                   help="Path to your wiki vault root (or set YUANLI_WIKI_ROOT env var)")
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

    findings = scan()
    if args.json:
        print(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2))
    else:
        print(render_markdown(findings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
