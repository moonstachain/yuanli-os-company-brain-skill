#!/usr/bin/env python3
"""brain_writeback_hook.py — Stop hook: auto edge-propose any new OSA card.

Fires when Claude finishes a turn. Scans the writeback-src staging dir for OSA
card JSONs whose edge-proposal draft in writeback-inbox is missing or stale, and
runs brain_writeback.py on each → lands a `.draft.json` for human review/promote.

The conversation→card distillation is done IN-SESSION by Claude (no LLM call in
this hook → no setup-token dependency). This hook only automates the fan-in:
edge proposal + staging, so insights captured during work are never lost.

fail-silent, fast, quiet. Consumes the Stop-hook JSON on stdin (content ignored).

Config (all via env, inline them in the hook command):
  YUANLI_WIKI_ROOT        vault absolute path            (required)
  YUANLI_WRITEBACK_SRC    staging dir with new OSA cards (required)
  YUANLI_WRITEBACK_INBOX  where .draft.json land         (required)
Any of the three missing → silent no-op exit 0.
"""
import os
import subprocess
import sys
from pathlib import Path


def _env_path(name: str) -> Path | None:
    v = os.environ.get(name, "").strip()
    return Path(v).expanduser() if v else None


SKILL = Path(__file__).resolve().parent
SRC = _env_path("YUANLI_WRITEBACK_SRC")
INBOX = _env_path("YUANLI_WRITEBACK_INBOX")
WIKI = _env_path("YUANLI_WIKI_ROOT")


def main() -> int:
    try:
        sys.stdin.read()
    except Exception:
        pass
    try:
        if SRC is None or INBOX is None or WIKI is None or not SRC.exists():
            return 0
        INBOX.mkdir(parents=True, exist_ok=True)
        for card in SRC.glob("*.json"):
            draft = INBOX / f"{card.stem}.draft.json"
            if draft.exists() and draft.stat().st_mtime >= card.stat().st_mtime:
                continue  # already processed, card unchanged
            subprocess.run(
                ["python3", str(SKILL / "brain_writeback.py"),
                 "--card", str(card), "--wiki-root", str(WIKI),
                 "--out-dir", str(INBOX)],
                capture_output=True, text=True, timeout=60,
            )
    except Exception:
        pass  # never break the session
    return 0


if __name__ == "__main__":
    sys.exit(main())
