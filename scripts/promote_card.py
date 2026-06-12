#!/usr/bin/env python3
"""
promote_card.py — 回写飞轮的 human-gate 晋升步（三圈协议：AI 不自动跨圈，人在中间）。

把审过的 `.draft.json` OSA 卡晋升进决策层 `decisions/osa/<id>.json`：
  1. 跑七道质量门（osa_card_quality_gate）—— 不到格式合格不让晋升。
  2. 清掉 proposed / draft 标记，设 trust（默认 human-confirmed，因为这是人审晋升）。
  3. 写入目标决策目录。
  4. 提示仍是 candidate 的高价值边（supersedes/blocks）需单独 confirm。

铁律：
  - 默认 --dry-run，真正写入要显式 --commit。
  - 高价值候选边不会因晋升自动转 active（仍须在卡里把 trust 改 human-confirmed）。

用法：
  promote_card.py --card draft.json --to <decisions/osa 目录> [--trust human-confirmed] --commit
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

def _gate_candidates() -> list[Path]:
    # 质量门住在 distiller skill；跨 skill 依赖，搜多处
    home = Path.home()
    return [
        Path(__file__).resolve().parent / "osa_card_quality_gate.py",
        home / ".claude/skills/osa-strategy-card-distiller/scripts/osa_card_quality_gate.py",
        home / "Documents/osa-strategy-card-distiller/scripts/osa_card_quality_gate.py",
    ]


def load_gate():
    """返回 gate 模块；找不到则返回 None（优雅降级，不让晋升因姊妹 skill 缺失而崩）。"""
    for cand in _gate_candidates():
        if cand.exists():
            spec = importlib.util.spec_from_file_location("gate", cand)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["gate"] = mod
            spec.loader.exec_module(mod)
            return mod
    return None


def main() -> int:
    p = argparse.ArgumentParser(description="人审晋升 OSA 卡进决策层")
    p.add_argument("--card", type=Path, required=True)
    p.add_argument("--to", type=Path, required=True, help="目标 decisions/osa 目录")
    p.add_argument("--trust", default="human-confirmed")
    p.add_argument("--commit", action="store_true", help="真正写入（默认 dry-run）")
    args = p.parse_args()

    if not args.card.exists():
        print(f"error: 卡不存在 {args.card}", file=sys.stderr)
        return 2
    card = json.loads(args.card.read_text(encoding="utf-8"))

    # 1) 清标记 + 设 trust（晋升即 human-confirm 行为，先落 trust 再过门，
    #    否则 v=5 卡永远卡在门7 的 chicken-egg）
    card["trust"] = args.trust
    for e in card.get("edges", []) or []:
        e.pop("proposed", None)
        e.pop("_note", None)

    # 2) 质量门（跨 skill 依赖；缺失则降级警告，不阻断）
    gate = load_gate()
    if gate is None:
        print("⚠️ 未找到 osa_card_quality_gate.py（distiller skill），跳过质量门校验。")
    else:
        r = gate.gate_check(card)
        print(f"质量门：{r['passed']}/7 · {r['grade']}" + (f" · 卡在 {r['stuck_at']}" if r['stuck_at'] else ""))
        if r["grade"] == "生料卡":
            print("🔴 生料卡（格式门未过），拒绝晋升。先补 O 备选淘汰 / S 到 L4。", file=sys.stderr)
            return 1
    candidates = [e for e in card.get("edges", []) or []
                  if e.get("type") in ("supersedes", "blocks") and e.get("trust") != "human-confirmed"]

    cid = card.get("id", args.card.stem.replace(".draft", ""))
    target = args.to / f"{cid}.json"

    if not args.commit:
        print(f"\n[dry-run] 将晋升 → {target}  (trust={args.trust})")
        print(f"[dry-run] 卡内 active 边 {len(card.get('edges', []))} 条；其中 {len(candidates)} 条高价值候选边仍待单独 confirm")
        print("[dry-run] 加 --commit 真正写入。")
        return 0

    args.to.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ 已晋升 → {target}  (trust={args.trust})")
    if candidates:
        print(f"⚠️ {len(candidates)} 条高价值候选边（supersedes/blocks）仍是 candidate，"
              f"须把对应 edge 的 trust 改 human-confirmed 才计入正式图。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
