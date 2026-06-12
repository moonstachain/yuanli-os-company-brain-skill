#!/usr/bin/env python3
"""
brain_surface_hook.py — UserPromptSubmit hook：把"原力大脑两层检索契约"自动接进 Claude Code。

每次提交非平凡 prompt 时：
  1. 读 Claude Code 注入的 hook JSON（stdin，含 prompt）
  2. 跑 brain_surface 两层召回（决策卡 OSA + 概念，跳过 raw，~0.2s）
  3. 把紧凑的"相关历史上下文"块打到 stdout → Claude Code 注入进对话上下文
  4. append 到 _bridge-log.jsonl（量飞轮转速：把"一周 13 次手动"变成"每次自动"）

铁律：fail-silent —— 任何异常都 exit 0，永不阻断用户 prompt；无命中时静默。
治飞轮第①半（CONTRACT §4 / §5 步骤 5）。

配置（全走 env，hook command 里内联即可）：
  YUANLI_WIKI_ROOT       vault 绝对路径（必填；未设或不存在 → 静默退出）
  YUANLI_OSA_EXTRA_DIRS  额外 OSA 卡目录，冒号分隔（可选，如 promote 前的 staging 目录）

settings.json 接线示例：
  "command": "env YUANLI_WIKI_ROOT=$HOME/path/to/vault python3 <this-file>"

禁用：删掉 ~/.claude/settings.json 里 hooks.UserPromptSubmit 对应块即可。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

_wiki_env = os.environ.get("YUANLI_WIKI_ROOT", "").strip()
WIKI = Path(_wiki_env).expanduser() if _wiki_env else None
SKILL = Path(__file__).resolve().parent
SURFACE = SKILL / "brain_surface.py"

# OSA 决策卡：wiki 内生产位置 + env 指定的额外目录（如 promote 前的 dry-run staging）
OSA_DIRS = ([WIKI / "decisions" / "osa"] if WIKI else []) + [
    Path(p).expanduser()
    for p in os.environ.get("YUANLI_OSA_EXTRA_DIRS", "").split(":") if p.strip()
]
BRIDGE_LOG = (WIKI / "_bridge-log.jsonl") if WIKI else None

MIN_PROMPT_LEN = 8
MAX_CARDS = 2
MAX_CONCEPTS = 3
MIN_DISTINCT = 2     # 须命中 ≥2 个不同 query 词（多词共现）；滤掉"仅 1 个词重复"的词汇巧合
MIN_SCORE = 2
TIMEOUT_S = 4
TRIVIAL = re.compile(r"^\s*(/|y|n|yes|no|ok|okay|好|好的|是|对|嗯|继续|行|go|stop|done|谢谢|thanks?|thx)\b", re.I)


def read_prompt() -> str:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return ""
    return str(data.get("prompt", "")).strip()


def main() -> int:
    prompt = read_prompt()
    if len(prompt) < MIN_PROMPT_LEN or TRIVIAL.match(prompt):
        return 0
    if WIKI is None or not WIKI.is_dir() or not SURFACE.exists():
        return 0

    topic = prompt[:200]
    cmd = [sys.executable, str(SURFACE), "--wiki-root", str(WIKI),
           "--no-raw", "--json", "--limit", "4", "--topic", topic]
    for d in OSA_DIRS:
        cmd += ["--osa-dir", str(d)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S)
        data = json.loads(proc.stdout)
    except Exception:
        return 0

    sections = data.get("sections", {})

    def strong(hits):
        return [h for h in hits
                if h.get("distinct", 0) >= MIN_DISTINCT and h.get("score", 0) >= MIN_SCORE]

    cards = strong(next((v for k, v in sections.items() if "决策卡" in k or "OSA" in k), []))[:MAX_CARDS]
    concepts = strong(next((v for k, v in sections.items() if "Concepts" in k), []))[:MAX_CONCEPTS]
    if not cards and not concepts:
        return 0  # 静默：无强命中不打扰

    lines = ["<wiki-brain-surface>",
             f"原力大脑·自动召回相关历史上下文（topic≈「{topic[:40]}」）："]
    if cards:
        lines.append("🎯 在赌的决策（OSA 卡 · 快照，引用前看 trust）：")
        for h in cards:
            confirmed = h.get("trust") == "human-confirmed"
            badge = "✅已校准" if confirmed else "⚠️未校准草稿"
            lines.append(f"  - [{h.get('path')}] {h.get('title')} "
                         f"(trust={h.get('trust')} {badge}, p={h.get('priority')})")
    if concepts:
        lines.append("🧠 相关概念（慢沉淀知识）：")
        for h in concepts:
            tr = h.get("trust", "")
            badge = " ✅" if tr == "human-confirmed" else (f" ·{tr}" if tr else "")
            lines.append(f"  - {h.get('path')} — {h.get('title')}{badge}")
    ft = data.get("filtered_trust", 0)
    if ft:
        lines.append(f"  （{ft} 张低 trust 决策卡被过滤）")
    lines.append("说明：决策卡=快照可能未 human-confirm；概念=慢沉淀真相。若与决策相关，先读上述概念再下判断。")
    lines.append("</wiki-brain-surface>")
    print("\n".join(lines))

    try:
        with open(BRIDGE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "src": "auto-surface-hook",
                "topic": topic[:80],
                "cards": len(cards),
                "concepts": len(concepts),
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # 永不阻断 prompt
