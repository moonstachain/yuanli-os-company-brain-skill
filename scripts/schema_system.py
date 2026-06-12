#!/usr/bin/env python3
"""
schema_system.py — yuanli_schema_infer / validate / diff 三件套（v0.1）

借鉴自 basicmachines-co/basic-memory 的 Schema System 设计哲学：
schema 不是预先写死，是从语料推断出来的；三件套互锁。

Usage:
    python3 schema_system.py infer concepts/ > _schemas/concepts.schema.yaml
    python3 schema_system.py validate concepts/some-page.md _schemas/concepts.schema.yaml
    python3 schema_system.py diff _schemas/v1.yaml _schemas/v2.yaml

外壳极简，先解决"能跑"，高级特性留 v0.3 backlog。
"""

from __future__ import annotations
import sys
import os

try:
    import yaml
except ModuleNotFoundError:
    sys.exit(
        "ERROR: schema_system.py needs PyYAML — the ONE non-stdlib dep in this skill.\n"
        "  pip install -r requirements.txt    # or: pip install PyYAML"
    )
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

_wiki_env = os.environ.get("WIKI_ROOT")
WIKI_ROOT = Path(_wiki_env).expanduser() if _wiki_env else None  # required for relative <dir>


def parse_frontmatter(filepath: Path) -> dict:
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    try:
        return yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        return {}


def detect_type(value) -> str:
    if value is None: return "null"
    if isinstance(value, bool): return "bool"
    if isinstance(value, int): return "int"
    if isinstance(value, float): return "float"
    if isinstance(value, list): return "list"
    if isinstance(value, dict): return "dict"
    if isinstance(value, str):
        # 进一步细分常见类型
        if len(value) == 10 and value[4] == "-" and value[7] == "-":
            try:
                datetime.strptime(value, "%Y-%m-%d")
                return "date"
            except ValueError:
                return "str"
        return "str"
    return "unknown"


def cmd_infer(target_dir: Path) -> dict:
    """扫所有 .md frontmatter，推断 schema。"""
    if not target_dir.is_absolute():
        if WIKI_ROOT is None:
            print("ERROR: relative <dir> requires WIKI_ROOT to be set.\n"
                  "Usage: WIKI_ROOT=/abs/path/to/vault python3 schema_system.py infer concepts/",
                  file=sys.stderr)
            return {}
        target_dir = WIKI_ROOT / target_dir
    if not target_dir.exists():
        print(f"ERROR: {target_dir} not found", file=sys.stderr)
        return {}

    files = list(target_dir.glob("*.md"))
    files = [f for f in files if not f.name.startswith("_")]  # 跳 _index/_log
    total = len(files)
    if total == 0:
        return {}

    field_present: Counter = Counter()
    field_types: dict[str, Counter] = defaultdict(Counter)
    field_examples: dict[str, list] = defaultdict(list)

    for f in files:
        fm = parse_frontmatter(f)
        if not fm:
            continue
        for k, v in fm.items():
            field_present[k] += 1
            field_types[k][detect_type(v)] += 1
            if len(field_examples[k]) < 3 and v not in field_examples[k]:
                # 仅记录可序列化样本
                if isinstance(v, (str, int, float, bool)):
                    field_examples[k].append(v)

    schema = {
        "schema_version": f"auto-{datetime.now().strftime('%Y%m%d-%H%M')}",
        "target": str(target_dir.relative_to(WIKI_ROOT))
                  if WIKI_ROOT and target_dir.is_relative_to(WIKI_ROOT) else str(target_dir),
        "total_files_scanned": total,
        "fields": {},
    }
    for field, count in field_present.most_common():
        present_pct = round(count / total * 100, 1)
        types = dict(field_types[field])
        primary_type = field_types[field].most_common(1)[0][0]
        schema["fields"][field] = {
            "present_pct": present_pct,
            "primary_type": primary_type,
            "type_distribution": types,
            "examples": field_examples[field][:3],
            "tier": "required" if present_pct >= 90 else
                    "recommended" if present_pct >= 50 else
                    "optional",
        }
    return schema


def cmd_validate(file: Path, schema_file: Path) -> dict:
    """校验单文件是否符合 schema 的 required + recommended tier。"""
    schema = yaml.safe_load(schema_file.read_text(encoding="utf-8"))
    fm = parse_frontmatter(file)
    errors = []
    warnings = []
    for field, spec in schema.get("fields", {}).items():
        tier = spec.get("tier", "optional")
        if field not in fm:
            if tier == "required":
                errors.append(f"missing required field '{field}' (schema present_pct={spec['present_pct']}%)")
            elif tier == "recommended":
                warnings.append(f"missing recommended field '{field}' (schema present_pct={spec['present_pct']}%)")
        else:
            actual_type = detect_type(fm[field])
            primary = spec.get("primary_type")
            if primary and actual_type != primary and actual_type not in spec.get("type_distribution", {}):
                warnings.append(f"field '{field}' type={actual_type} but schema primary={primary}")
    return {
        "file": str(file),
        "errors": errors,
        "warnings": warnings,
        "pass": len(errors) == 0,
    }


def cmd_diff(schema_a: Path, schema_b: Path) -> dict:
    """对比两份 schema yaml。"""
    a = yaml.safe_load(schema_a.read_text(encoding="utf-8"))
    b = yaml.safe_load(schema_b.read_text(encoding="utf-8"))
    fa = set(a.get("fields", {}).keys())
    fb = set(b.get("fields", {}).keys())
    added = sorted(fb - fa)
    removed = sorted(fa - fb)
    changed = []
    for f in fa & fb:
        ta = a["fields"][f].get("primary_type")
        tb = b["fields"][f].get("primary_type")
        ra = a["fields"][f].get("tier")
        rb = b["fields"][f].get("tier")
        if ta != tb or ra != rb:
            changed.append({
                "field": f,
                "type_change": f"{ta} → {tb}" if ta != tb else None,
                "tier_change": f"{ra} → {rb}" if ra != rb else None,
            })
    return {
        "schema_a": a.get("schema_version"),
        "schema_b": b.get("schema_version"),
        "added": added,
        "removed": removed,
        "changed": changed,
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd == "infer":
        if len(argv) < 3:
            print("Usage: schema_system.py infer <dir>", file=sys.stderr)
            return 1
        target = Path(argv[2])
        schema = cmd_infer(target)
        print(yaml.safe_dump(schema, allow_unicode=True, sort_keys=False))
        return 0
    elif cmd == "validate":
        if len(argv) < 4:
            print("Usage: schema_system.py validate <file.md> <schema.yaml>", file=sys.stderr)
            return 1
        result = cmd_validate(Path(argv[2]), Path(argv[3]))
        print(yaml.safe_dump(result, allow_unicode=True, sort_keys=False))
        return 0 if result["pass"] else 2
    elif cmd == "diff":
        if len(argv) < 4:
            print("Usage: schema_system.py diff <schema_a.yaml> <schema_b.yaml>", file=sys.stderr)
            return 1
        result = cmd_diff(Path(argv[2]), Path(argv[3]))
        print(yaml.safe_dump(result, allow_unicode=True, sort_keys=False))
        return 0
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
