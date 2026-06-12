#!/usr/bin/env python3
"""
intake_getnote.py — 热点层 L0 intake stub 生成器（v0.1）

按 [[tiered-knowledge-spine]] 协议的热点层（PULSE）约定：实时抓取服务
（GET笔记级）的语义召回结果，落为 vault `sources/` 下带 frontmatter 的
markdown stub —— circle: raw，truth_source 指回原平台 note_id。

职责边界（保持本 skill 纯 stdlib、无网络依赖的原则）：
  - 本脚本【不】调用任何平台 API、不持任何密钥。
  - 实际召回由 agent 层完成（如 MCP 的 recall 工具），结果以 JSON 喂进来。
  - 本脚本只做：字段校验 → 渲染 stub → 写入 sources/（默认 dry-run）。

⚠️ 平台 API 护栏（field-tested 2026-06）：
  取单条记录【不要】用按 ID 直取接口传 19 位大整数 note_id —— 部分运行时
  把纯数字参数按 IEEE-754 浮点处理，超过 2^53 末位被四舍五入，服务端稳定
  报「记录不存在」（且加引号/前缀又报参数类型错误）。一律走【语义 recall】
  接口拿内容；note_id 只作为字符串存进 truth_source 供人工回溯。

输入 JSON 形状（单条或数组）：
  {
    "note_id":   "1912525785962185272",     # 字符串！永远当字符串
    "title":     "某次会议讨论",
    "created_at":"2026-06-11 17:58:17",
    "content":   "召回的摘要/逐字稿片段……",
    "query":     "当时用的召回 query（可选，利于复现）"
  }

用法：
  echo '<json>' | intake_getnote.py --wiki-root /abs/vault
  intake_getnote.py --wiki-root /abs/vault --input recall_result.json --execute

热点层纪律提醒（见 tiered-knowledge-spine §6）：stub 是易失候选知识——
值得留的应在 24h 内人审蒸馏成索引层的卡，stub 本身可被 stale 信号清理。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_FIELDS = ("note_id", "title", "content")

STUB_TEMPLATE = """---
title: "{title}"
type: source
circle: raw
reliability: raw
truth_source: "getnote:note_id:{note_id}"
captured_at: "{captured_at}"
source_created_at: "{created_at}"
recall_query: "{query}"
tags: [hot-layer, getnote-intake, pending-distill]
---

# {title}

> 热点层 intake stub —— 易失候选知识。值得留的请在 24h 内蒸馏成
> 索引层概念卡（truth_source 保留回溯链），本 stub 随后可删。

{content}
"""


def slugify(title: str, note_id: str) -> str:
    base = re.sub(r"[^\w一-鿿-]+", "-", title).strip("-")[:40]
    return f"{base or 'getnote'}-{note_id[-6:]}"


def validate(item: dict, idx: int) -> list[str]:
    errors = []
    for f in REQUIRED_FIELDS:
        if not str(item.get(f, "")).strip():
            errors.append(f"item[{idx}]: missing required field '{f}'")
    nid = item.get("note_id")
    if nid is not None and not isinstance(nid, str):
        errors.append(
            f"item[{idx}]: note_id must be a STRING (got {type(nid).__name__}) — "
            f"numeric note_ids lose precision past 2^53; see header guardrail")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Render hot-layer recall results as sources/ stubs")
    ap.add_argument("--wiki-root", required=True, help="absolute path to the vault")
    ap.add_argument("--input", help="JSON file (default: stdin)")
    ap.add_argument("--execute", action="store_true", help="actually write (default: dry-run)")
    args = ap.parse_args()

    wiki_root = Path(args.wiki_root)
    if not wiki_root.is_absolute() or not wiki_root.is_dir():
        print(f"ABORT: --wiki-root must be an existing absolute path (got: {wiki_root})",
              file=sys.stderr)
        return 2

    raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ABORT: input is not valid JSON: {e}", file=sys.stderr)
        return 2
    items = data if isinstance(data, list) else [data]

    errors = [e for i, item in enumerate(items) for e in validate(item, i)]
    if errors:
        for e in errors:
            print(f"✗ {e}", file=sys.stderr)
        return 3

    out_dir = wiki_root / "sources"
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    written = []
    for item in items:
        stub = STUB_TEMPLATE.format(
            title=str(item["title"]).replace('"', "'"),
            note_id=item["note_id"],
            captured_at=captured_at,
            created_at=str(item.get("created_at", "")),
            query=str(item.get("query", "")).replace('"', "'"),
            content=str(item["content"]).strip(),
        )
        dest = out_dir / f"{slugify(str(item['title']), str(item['note_id']))}.md"
        written.append((dest, stub))
        print(f"{'WRITE' if args.execute else 'DRY-RUN'}: {dest.relative_to(wiki_root)}")

    if args.execute:
        out_dir.mkdir(parents=True, exist_ok=True)
        for dest, stub in written:
            dest.write_text(stub, encoding="utf-8")
        print(f"\n{len(written)} stub(s) written. Distill keepers into concept cards within 24h.")
    else:
        print("\nDRY-RUN — re-run with --execute to write.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
