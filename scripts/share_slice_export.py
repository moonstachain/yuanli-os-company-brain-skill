#!/usr/bin/env python3
"""
share_slice_export.py — Team Share Slice 导出器（v0.1）

按 [[team-share-slice]] 协议把 vault 中一个 tag 作用域内的脱敏知识
导出成只读镜像目录（之后由人推到 GitHub **私有**仓邀请协作者）。

这是「分发器官」，不是「备份器官」（那是 wiki_git_mirror_sync.sh）。

链路（本脚本负责 ①-③）：
  ① 作用域筛选  frontmatter `share_group:` 含 --share-tag 且 circle ≥ shared
  ② leak-guard  对每个候选文件正文跑敏感签名扫描，任一命中 ⇒ 整次 abort
  ③ 导出        全量重建 out-dir（撤销 tag 即下线）+ README + _slice-manifest.json

安全门（与 mirror-sync 四门同款纪律）：
  - 默认 dry-run，--execute 才写盘
  - leak-guard 签名文件本身永不进切片
  - circle: individual 的页面即使打了 share tag 也拒绝（E1）
  - out-dir 全量重建：先清后写，保证「撤销 share_group 即从切片消失」

用法：
  share_slice_export.py --wiki-root /abs/vault --share-tag team-x \\
      --out-dir /abs/slice --leak-guard-file /abs/signatures.txt
  # 确认 dry-run 清单无误后加 --execute

实战护栏（field-tested 2026-06）：
  - 签名清单放「模式」不放明文（明文会自触发）
  - --wiki-root / --out-dir 一律绝对路径（launchd 下 cwd 不可预期）
  - 扫描 scope 只限候选文件集，不扫仓库根（防 .git/ 误报淹没真命中）
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SHAREABLE_CIRCLES = {"shared", "institutional"}

README_TEMPLATE = """# {tag} · share slice (read-only mirror)

This repository is a **one-way, read-only mirror** of a knowledge slice
exported from a private vault (the single source of truth lives elsewhere).

- Do **not** edit files here — changes will be overwritten by the next export.
- Pull requests are not accepted; corrections go through the source vault's
  human review, then re-export.
- `_slice-manifest.json` records what was exported and when, so you can
  check freshness.

Protocol: `team-share-slice.md` in
[yuanli-os-company-brain-skill](https://github.com/moonstachain/yuanli-os-company-brain-skill).
"""


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_str, body). Empty frontmatter if absent."""
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 4)
    if end == -1:
        return "", text
    return text[4:end], text[end + 4:]


def fm_get(fm: str, key: str) -> list[str]:
    """Extract scalar or YAML-list values for a top-level frontmatter key.

    Stdlib-only, tolerant of the two shapes used in this skill's templates:
      key: value
      key: [a, b]
      key:
        - a
        - b
    """
    values: list[str] = []
    lines = fm.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(rf"^{re.escape(key)}\s*:\s*(.*)$", line)
        if m:
            rest = m.group(1).strip()
            if rest.startswith("[") and rest.endswith("]"):
                values += [v.strip().strip("'\"") for v in rest[1:-1].split(",") if v.strip()]
            elif rest:
                values.append(rest.strip("'\""))
            else:
                j = i + 1
                while j < len(lines) and re.match(r"^\s+-\s+", lines[j]):
                    values.append(re.sub(r"^\s+-\s+", "", lines[j]).strip().strip("'\""))
                    j += 1
            break
        i += 1
    return values


def load_signatures(path: Path) -> list[re.Pattern]:
    pats = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            pats.append(re.compile(line))
        except re.error:
            pats.append(re.compile(re.escape(line)))
    return pats


def main() -> int:
    ap = argparse.ArgumentParser(description="Export a tag-scoped, leak-guarded share slice")
    ap.add_argument("--wiki-root", required=True, help="absolute path to the vault")
    ap.add_argument("--share-tag", required=True, help="share_group tag to export")
    ap.add_argument("--out-dir", required=True, help="absolute path to the slice mirror dir")
    ap.add_argument("--leak-guard-file", required=True,
                    help="absolute path to the sensitive-signature list (one pattern per line)")
    ap.add_argument("--execute", action="store_true", help="actually write (default: dry-run)")
    args = ap.parse_args()

    wiki_root = Path(args.wiki_root)
    out_dir = Path(args.out_dir)
    guard_file = Path(args.leak_guard_file)

    for p, name in ((wiki_root, "--wiki-root"), (out_dir, "--out-dir"), (guard_file, "--leak-guard-file")):
        if not p.is_absolute():
            print(f"ABORT: {name} must be an absolute path (got: {p})", file=sys.stderr)
            return 2
    if not wiki_root.is_dir():
        print(f"ABORT: wiki root not found: {wiki_root}", file=sys.stderr)
        return 2
    if not guard_file.is_file():
        print(f"ABORT: leak-guard file not found: {guard_file} "
              f"(a slice export without a guard is not allowed)", file=sys.stderr)
        return 2
    if out_dir == wiki_root or wiki_root in out_dir.parents:
        print("ABORT: --out-dir must live outside the vault", file=sys.stderr)
        return 2

    signatures = load_signatures(guard_file)
    if not signatures:
        print("ABORT: leak-guard file is empty — refuse to export unguarded", file=sys.stderr)
        return 2

    # ① scope selection
    candidates: list[tuple[Path, str]] = []
    rejected_individual: list[str] = []
    for md in sorted(wiki_root.rglob("*.md")):
        rel = md.relative_to(wiki_root)
        if any(part.startswith(".") or part.startswith("_extract") for part in rel.parts):
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        fm, _ = split_frontmatter(text)
        if not fm:
            continue
        if args.share_tag not in fm_get(fm, "share_group"):
            continue
        circles = fm_get(fm, "circle")
        circle = circles[0] if circles else "unknown"
        if circle not in SHAREABLE_CIRCLES:
            rejected_individual.append(str(rel))
            continue
        candidates.append((md, text))

    if rejected_individual:
        print(f"E1: {len(rejected_individual)} tagged page(s) below 'shared' circle — "
              f"promote them first or remove the tag:")
        for r in rejected_individual:
            print(f"  - {r}")

    if not candidates:
        print(f"Nothing to export: no page with share_group: {args.share_tag} at circle ≥ shared")
        return 1

    # ② leak guard — any hit aborts the WHOLE export
    hits: list[str] = []
    for md, text in candidates:
        for pat in signatures:
            m = pat.search(text)
            if m:
                hits.append(f"{md.relative_to(wiki_root)} :: /{pat.pattern}/")
                break
    if hits:
        print("ABORT: leak-guard hit — nothing exported. Review these pages:", file=sys.stderr)
        for h in hits:
            print(f"  ✗ {h}", file=sys.stderr)
        return 3

    # ③ export (full rebuild)
    print(f"Slice '{args.share_tag}': {len(candidates)} page(s) pass scope + leak-guard")
    for md, _ in candidates:
        print(f"  ✓ {md.relative_to(wiki_root)}")

    if not args.execute:
        print("\nDRY-RUN — re-run with --execute to write the slice.")
        return 0

    if out_dir.exists():
        for child in out_dir.iterdir():
            if child.name == ".git":
                continue  # keep repo history; never-force discipline lives in the push step
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "share_tag": args.share_tag,
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_vault": str(wiki_root),
        "pages": [],
    }
    for md, text in candidates:
        rel = md.relative_to(wiki_root)
        dest = out_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        manifest["pages"].append(str(rel))

    (out_dir / "README.md").write_text(README_TEMPLATE.format(tag=args.share_tag), encoding="utf-8")
    (out_dir / "_slice-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\nExported {len(candidates)} page(s) → {out_dir}")
    print("Next: create a PRIVATE repo, push, invite collaborators read-only "
          "(see team-share-slice.md §4-6).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
