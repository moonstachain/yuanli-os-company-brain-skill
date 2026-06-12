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

# Semantic recall (optional): shares the DashScope embed helper with the indexer.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import numpy as np  # noqa: E402
    from embed_sources import embed_texts, _load_key, prep_text, DIM  # noqa: E402
    _SEMANTIC_OK = True
except Exception:  # noqa: BLE001 - numpy / embed module absent → lexical only
    _SEMANTIC_OK = False

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
    score: int = 0         # 总命中次数（含重复）
    category: str = ""
    trust: str = ""        # OSA 决策卡专用：claude-auto / claude-unilateral / human-confirmed
    priority: int = 0      # OSA 决策卡专用：p = v×(6−m)
    distinct: int = 0      # 命中的不同 query 词数 —— 高精度信号（多词共现 >> 单词重复）


# 中文 filler/指令 bigram：不计入检索（"帮我写个..." 不是主题词）
CJK_STOP_BIGRAMS = {
    "帮我", "我写", "写个", "我想", "想要", "帮忙", "一下", "一个", "怎么", "如何",
    "可以", "什么", "这个", "那个", "的话", "请帮", "给我", "需要", "是否", "以及",
    "或者", "然后", "目前", "现在", "关于", "对于", "麻烦", "一种", "一些",
}


# 两层统一信任尺（CONTRACT §2）；高 = 更可信
TRUST_RANK = {"": 0, "claude-auto": 0, "claude-unilateral": 1, "human-confirmed": 2}


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


def infer_trust(fm: dict) -> str:
    """概念层 trust 读侧推断（不改 1116 个机构文件）。两层共享同一把信任尺。

    显式 frontmatter `trust:` 最高优先；否则从既有信号推断：
      - maturity: stable 或有 last_reviewed → human-confirmed（已沉淀/人审）
      - distilled_by 含 claude 且未达上述 → claude-unilateral（AI 蒸馏未人审）
      - 其余 → claude-auto
    """
    explicit = fm.get("trust", "").strip().lower()
    if explicit in TRUST_RANK and explicit:
        return explicit
    maturity = fm.get("maturity", "").strip().lower()
    if maturity == "stable" or fm.get("last_reviewed", "").strip():
        return "human-confirmed"
    if "claude" in fm.get("distilled_by", "").lower():
        return "claude-unilateral"
    return "claude-auto"


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
    """中文无词边界：CJK run 切字符 bigram，ASCII/数字保留整词。

    自然语言 prompt（无空格）若整段当一个 token，会匹配不到任何概念。
    bigram 是无分词器场景下的经典中文检索召回法。
    """
    terms: list[str] = []
    for tok in re.findall(r"[\w一-鿿]+", topic.lower()):
        if re.search(r"[一-鿿]", tok):          # 含 CJK → bigram
            if len(tok) < 2:
                continue
            terms.extend(tok[i:i + 2] for i in range(len(tok) - 1))
        elif len(tok) >= 2:                       # 纯 ASCII/数字 → 整词
            terms.append(tok)
    seen: set[str] = set()
    out: list[str] = []
    for t in terms:
        if t in seen or t in CJK_STOP_BIGRAMS:
            continue
        seen.add(t)
        out.append(t)
    return out


def score_terms(text: str, terms: list[str]) -> tuple[int, int]:
    """返回 (总命中次数, 不同命中词数)。distinct 是高精度信号。"""
    text_l = text.lower()
    counts = [text_l.count(t) for t in terms]
    return sum(counts), sum(1 for c in counts if c > 0)


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
        score, distinct = score_terms(text, terms)
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
            distinct=distinct,
            trust=infer_trust(fm) if category in ("concept", "synthesis") else "",
        ))
    hits.sort(key=lambda h: -h.score)
    return hits[:limit]


def scan_osa_cards(osa_dirs: list[Path], terms: list[str], min_trust: str,
                   limit: int = 5) -> tuple[list[Hit], int]:
    """扫 OSA 决策卡 JSON（两层大脑的决策层）。返回 (hits, filtered_by_trust 计数)。

    搜索面 = title + o + s + a + domain；按 trust 过滤（低于 min_trust 的剔除并计数）。
    """
    min_rank = TRUST_RANK.get(min_trust, 0)
    hits: list[Hit] = []
    filtered = 0
    seen: set[str] = set()
    for osa_dir in osa_dirs:
        if not osa_dir or not osa_dir.exists():
            continue
        for path in osa_dir.rglob("*.json"):
            if path.name.startswith("_") or str(path) in seen:
                continue
            seen.add(str(path))
            try:
                data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except (json.JSONDecodeError, OSError, ValueError):
                continue
            if isinstance(data, list):
                cards = data
            elif isinstance(data, dict) and isinstance(data.get("nodes"), list):
                cards = data["nodes"]
            elif isinstance(data, dict):
                cards = [data]
            else:
                continue
            for card in cards:
                if not isinstance(card, dict):
                    continue
                blob = " ".join(str(card.get(k, "")) for k in ("title", "o", "s", "a", "domain"))
                score, distinct = score_terms(blob, terms)
                if score == 0:
                    continue
                trust = str(card.get("trust", "")).strip()
                if TRUST_RANK.get(trust, 0) < min_rank:
                    filtered += 1
                    continue
                v, m = card.get("v"), card.get("m")
                prio = (v * (6 - m)) if isinstance(v, int) and isinstance(m, int) else 0
                hits.append(Hit(
                    path=str(card.get("id", path.stem)),
                    title=card.get("title", path.stem),
                    snippet=first_snippet(str(card.get("o", "")), terms, 140),
                    circle="institutional",
                    date=str(card.get("as_of", "")),
                    score=score,
                    category="osa-decision",
                    trust=trust or "claude-auto",
                    priority=prio,
                    distinct=distinct,
                ))
    hits.sort(key=lambda h: (-h.priority, -h.score))
    return hits[:limit], filtered


def scan_sources_semantic(wiki_root: Path, query: str, limit: int = 5,
                          min_sim: float = 0.35) -> list[Hit]:
    """Vector recall over <wiki-root>/.vector-index/sources.npz by MEANING.

    Cosine(query, all) → top-`limit` Hits with score=round(sim*100), above min_sim.
    Returns [] with a clear hint if the index or embedding stack is missing.
    """
    if not _SEMANTIC_OK:
        print("hint: semantic recall needs numpy + embed_sources.py (import failed)",
              file=sys.stderr)
        return []
    idx_dir = wiki_root / ".vector-index"
    npz = idx_dir / "sources.npz"
    paths_f = idx_dir / "paths.json"
    if not (npz.exists() and paths_f.exists()):
        print(f"hint: no vector index at {idx_dir}/sources.npz — "
              f"run embed_sources.py first", file=sys.stderr)
        return []
    try:
        vecs = np.load(npz)["vecs"].astype(np.float32)
        paths = json.loads(paths_f.read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"hint: could not load vector index ({e}) — re-run embed_sources.py",
              file=sys.stderr)
        return []
    if vecs.shape[0] == 0 or len(paths) != vecs.shape[0]:
        print("hint: vector index empty or inconsistent — re-run embed_sources.py",
              file=sys.stderr)
        return []

    key = _load_key()
    if not key:
        print("hint: DASHSCOPE_API_KEY not found (env or ~/.zshrc)", file=sys.stderr)
        return []
    try:
        qvec = np.asarray(embed_texts([query], key, dim=DIM)[0], dtype=np.float32)
    except Exception as e:  # noqa: BLE001
        print(f"hint: query embed failed ({e})", file=sys.stderr)
        return []

    qn = np.linalg.norm(qvec)
    vn = np.linalg.norm(vecs, axis=1)
    denom = vn * qn
    denom[denom == 0] = 1e-9
    sims = (vecs @ qvec) / denom

    order = np.argsort(-sims)[: max(limit * 4, limit)]
    hits: list[Hit] = []
    for i in order:
        sim = float(sims[i])
        if sim < min_sim:
            break
        rel = paths[i]
        snippet = ""
        try:
            raw = (wiki_root / rel).read_text(encoding="utf-8", errors="replace")
            snippet = prep_text(raw)[:140]
        except OSError:
            pass
        hits.append(Hit(
            path=rel,
            title=Path(rel).stem,
            snippet=snippet,
            circle="raw",
            score=round(sim * 100),
            category="raw-semantic",
        ))
        if len(hits) >= limit:
            break
    return hits


def render_markdown(topic: str, role: str, sections: dict[str, list[Hit]],
                    filtered_trust: int = 0) -> str:
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
            if h.category == "osa-decision":
                badge = "✅" if h.trust == "human-confirmed" else "⚠️"
                meta = f" {badge}trust={h.trust} · p={h.priority}"
                out.append(f"- `{h.path}`{date_part}{meta}")
                out.append(f"  - {h.title}")
            else:
                tb = ""
                if h.trust:
                    tb = " ✅" if h.trust == "human-confirmed" else f" ·{h.trust}"
                out.append(f"- `{h.path}` - {h.title}{date_part}{tb}")
            if h.snippet:
                out.append(f"  > {h.snippet}")
        out.append("")
    if filtered_trust:
        out.append(f"_filtered_out: {filtered_trust} 张决策卡因 trust 低于阈值被过滤_")
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description="Yuanli-OS Company Brain - right-time surface (Phase 1)")
    p.add_argument("--wiki-root", type=Path, default=None,
                   help="Path to your wiki vault root (or set YUANLI_WIKI_ROOT env var)")
    p.add_argument("--topic", required=True, help="The topic you are about to draft about")
    p.add_argument("--role", choices=list(ROLE_VISIBLE_CIRCLES), default="self")
    p.add_argument("--limit", type=int, default=5, help="Max hits per category (default 5)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-raw", action="store_true",
                   help="跳过 sources/ 原料层（hook 模式用：只两器官 concepts+决策卡，快）")
    p.add_argument("--osa-dir", type=Path, action="append", default=None,
                   help="OSA 决策卡 JSON 目录（默认 <wiki>/decisions/osa；可多次指定）")
    p.add_argument("--min-trust", choices=list(TRUST_RANK), default="claude-auto",
                   help="决策卡最低信任阈值（默认 claude-auto = 全显）")
    p.add_argument("--semantic", action="store_true",
                   help="加一段向量语义召回 sources（需先跑 embed_sources.py 建索引）")
    p.add_argument("--min-sim", type=float, default=0.35,
                   help="语义召回最低余弦相似度阈值（默认 0.35）")
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

    osa_dirs = args.osa_dir or [WIKI_ROOT / "decisions" / "osa"]
    osa_hits, filtered_trust = scan_osa_cards(osa_dirs, terms, args.min_trust, args.limit)

    # 🎯 决策层(OSA卡) 在前，🧠 语义层(概念) 在后 —— 两器官并列
    sections = {
        "🎯 决策卡 OSA (decision layer)": osa_hits,
        "🧠 Concepts (semantic layer)":   scan_dir(WIKI_ROOT / "concepts",   terms, visible, "concept",   args.limit),
        "Syntheses (institutional)":      scan_dir(WIKI_ROOT / "syntheses",  terms, visible, "synthesis", args.limit),
        "Decisions md (4-tuple)":         scan_dir(WIKI_ROOT / "decisions",  terms, visible, "decision",  args.limit),
    }
    if not args.no_raw:
        sections["Transcripts / raw notes"] = scan_dir(WIKI_ROOT / "sources", terms, visible, "raw", args.limit)
        sections["Drafts / artifacts"] = (
            scan_dir(WIKI_ROOT / "_factory",  terms, visible, "draft",    args.limit) +
            scan_dir(WIKI_ROOT / "artifacts", terms, visible, "artifact", args.limit) +
            scan_dir(WIKI_ROOT / "articles",  terms, visible, "article",  args.limit)
        )

    if args.semantic:
        sections["🔎 语义召回 sources (vector)"] = scan_sources_semantic(
            WIKI_ROOT, args.topic, args.limit, args.min_sim)

    if args.json:
        flat = {k: [asdict(h) for h in v] for k, v in sections.items()}
        print(json.dumps({"topic": args.topic, "role": args.role,
                          "filtered_trust": filtered_trust, "sections": flat},
                         ensure_ascii=False, indent=2))
    else:
        print(render_markdown(args.topic, args.role, sections, filtered_trust))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
