#!/usr/bin/env python3
"""
embed_sources.py — Resumable, batched local embedding indexer over an Obsidian
wiki's sources/.

Builds a vector index at <wiki-root>/.vector-index/sources.npz (numpy) plus
parallel paths.json + meta.json so downstream semantic recall (brain_surface.py
--semantic) can do cosine search by MEANING, not just lexical bigrams.

Embedding backend: DashScope text-embedding-v3 (1024-dim) via urllib (stdlib
only). Batch limit = 10 texts/call. Results mapped back by text_index.

Usage:
  python3 embed_sources.py --wiki-root ~/LLM-Wiki
  python3 embed_sources.py --wiki-root ~/LLM-Wiki \
      --subdir sources/get-biji --subdir sources/transcripts
  python3 embed_sources.py --wiki-root ~/LLM-Wiki --rebuild --limit 50

Resumable: re-running WITHOUT --rebuild loads the existing index, skips files
whose (path, mtime) are unchanged, embeds only new/changed, and appends.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

EMBED_URL = ("https://dashscope.aliyuncs.com/api/v1/services/embeddings/"
             "text-embedding/text-embedding")
MODEL = "text-embedding-v3"
DIM = 1024
MAX_BATCH = 10
MAX_CHARS = 2000

_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
_WS_RE = re.compile(r"\s+")


def _load_key() -> str:
    """env DASHSCOPE_API_KEY first, else parse ~/.zshrc. NEVER print the key."""
    key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if key:
        return key
    zshrc = Path("~/.zshrc").expanduser()
    if zshrc.is_file():
        try:
            for line in zshrc.read_text(encoding="utf-8", errors="replace").splitlines():
                m = re.search(r'DASHSCOPE_API_KEY=["\']?([^"\'\s]+)', line)
                if m:
                    return m.group(1).strip()
        except OSError:
            pass
    return ""


def embed_texts(texts: list[str], key: str, dim: int = DIM,
                max_tries: int = 3) -> list[list[float]]:
    """Embed up to MAX_BATCH texts. Returns list[list[float]] aligned to `texts`
    order (remaps DashScope text_index). Retries transient errors with backoff.

    Raises on persistent failure; caller is responsible for catch/continue.
    """
    if not texts:
        return []
    if len(texts) > MAX_BATCH:
        raise ValueError(f"embed_texts batch > {MAX_BATCH}")
    body = json.dumps({
        "model": MODEL,
        "input": {"texts": texts},
        "parameters": {"dimension": dim},
    }).encode("utf-8")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    last_err: Exception | None = None
    for attempt in range(max_tries):
        try:
            req = urllib.request.Request(EMBED_URL, data=body, headers=headers)
            raw = urllib.request.urlopen(req, timeout=60).read()
            r = json.loads(raw)
            embs = r.get("output", {}).get("embeddings")
            if not embs:
                raise RuntimeError(f"no embeddings in response: {str(r)[:200]}")
            out: list[list[float] | None] = [None] * len(texts)
            for e in embs:
                out[e["text_index"]] = e["embedding"]
            if any(v is None for v in out):
                raise RuntimeError("response missing some text_index")
            return out  # type: ignore[return-value]
        except urllib.error.HTTPError as e:
            # 4xx (except 429) = don't retry
            if e.code != 429 and 400 <= e.code < 500:
                raise
            last_err = e
        except (urllib.error.URLError, TimeoutError, RuntimeError,
                json.JSONDecodeError, OSError) as e:
            last_err = e
        if attempt < max_tries - 1:
            time.sleep(2 ** (attempt + 1))  # 2s, 4s, 8s
    raise RuntimeError(f"embed_texts failed after {max_tries} tries: {last_err}")


def prep_text(raw: str) -> str:
    """Strip YAML frontmatter, collapse whitespace, truncate to MAX_CHARS."""
    body = _FRONTMATTER_RE.sub("", raw, count=1)
    body = _WS_RE.sub(" ", body).strip()
    return body[:MAX_CHARS]


def collect_files(wiki_root: Path, subdirs: list[str], limit: int | None) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for sub in subdirs:
        base = (wiki_root / sub)
        if not base.exists():
            print(f"  warn: subdir not found: {sub}", file=sys.stderr)
            continue
        for p in sorted(base.rglob("*.md")):
            if p.name.startswith("_"):
                continue
            rp = p.resolve()
            if rp in seen:
                continue
            seen.add(rp)
            files.append(p)
    if limit is not None:
        files = files[:limit]
    return files


def load_index(idx_dir: Path):
    """Returns (vecs Nx DIM float32, paths list[str], meta dict). Empty if absent."""
    npz = idx_dir / "sources.npz"
    paths_f = idx_dir / "paths.json"
    meta_f = idx_dir / "meta.json"
    if not (npz.exists() and paths_f.exists() and meta_f.exists()):
        return np.zeros((0, DIM), dtype=np.float32), [], {}
    try:
        vecs = np.load(npz)["vecs"].astype(np.float32)
        paths = json.loads(paths_f.read_text(encoding="utf-8"))
        meta = json.loads(meta_f.read_text(encoding="utf-8"))
        if len(paths) != vecs.shape[0]:
            print("  warn: index paths/vecs length mismatch; rebuilding", file=sys.stderr)
            return np.zeros((0, DIM), dtype=np.float32), [], {}
        return vecs, paths, meta
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"  warn: could not load existing index ({e}); rebuilding", file=sys.stderr)
        return np.zeros((0, DIM), dtype=np.float32), [], {}


def atomic_write_index(idx_dir: Path, vecs: np.ndarray, paths: list[str], meta: dict):
    idx_dir.mkdir(parents=True, exist_ok=True)
    tmp_npz = idx_dir / "sources.npz.tmp"
    np.savez(tmp_npz, vecs=vecs.astype(np.float32))
    # np.savez appends .npz to the filename if missing
    actual_tmp = tmp_npz if tmp_npz.exists() else Path(str(tmp_npz) + ".npz")
    os.replace(actual_tmp, idx_dir / "sources.npz")

    tmp_paths = idx_dir / "paths.json.tmp"
    tmp_paths.write_text(json.dumps(paths, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp_paths, idx_dir / "paths.json")

    tmp_meta = idx_dir / "meta.json.tmp"
    tmp_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp_meta, idx_dir / "meta.json")


def ensure_gitignore(wiki_root: Path):
    gi = wiki_root / ".gitignore"
    entry = ".vector-index/"
    try:
        existing = gi.read_text(encoding="utf-8") if gi.exists() else ""
        lines = {l.strip().rstrip("/") for l in existing.splitlines()}
        if entry.rstrip("/") in lines or ".vector-index" in lines:
            return
        with gi.open("a", encoding="utf-8") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write(f"{entry}\n")
        print(f"  added {entry} to .gitignore")
    except OSError as e:
        print(f"  warn: could not update .gitignore: {e}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="Resumable batched embedding indexer over wiki sources/")
    ap.add_argument("--wiki-root", type=Path, required=True)
    ap.add_argument("--subdir", action="append", default=None,
                    help="repeatable; default=['sources']")
    ap.add_argument("--file-list", type=Path, default=None,
                    help="只嵌此文件里列出的相对路径(每行一个),忽略 --subdir")
    ap.add_argument("--rebuild", action="store_true", help="ignore existing index")
    ap.add_argument("--limit", type=int, default=None, help="cap files (testing)")
    ap.add_argument("--batch", type=int, default=MAX_BATCH)
    args = ap.parse_args()

    wiki_root = args.wiki_root.expanduser()
    if not wiki_root.is_dir():
        print(f"error: wiki root not found: {wiki_root}", file=sys.stderr)
        return 2
    subdirs = args.subdir or ["sources"]
    batch_size = max(1, min(args.batch, MAX_BATCH))

    key = _load_key()
    if not key:
        print("error: DASHSCOPE_API_KEY not found (env or ~/.zshrc)", file=sys.stderr)
        return 2

    idx_dir = wiki_root / ".vector-index"
    ensure_gitignore(wiki_root)

    if args.rebuild:
        vecs, paths, meta = np.zeros((0, DIM), dtype=np.float32), [], {}
    else:
        vecs, paths, meta = load_index(idx_dir)
    mtimes: dict[str, float] = dict(meta.get("mtimes", {})) if not args.rebuild else {}

    if args.file_list:
        rels = [l.strip() for l in args.file_list.read_text(encoding="utf-8").splitlines() if l.strip()]
        files = [wiki_root / r for r in rels if (wiki_root / r).is_file()]
        if args.limit:
            files = files[:args.limit]
        print(f"file-list 模式: {len(files)} 篇 (来自 {args.file_list.name})")
    else:
        files = collect_files(wiki_root, subdirs, args.limit)
        print(f"scanning {len(files)} .md files under {subdirs} ...")

    # Determine which files need (re)embedding.
    to_embed: list[tuple[str, str, float]] = []  # (relpath, prepped_text, mtime)
    skipped = 0
    for p in files:
        rel = str(p.relative_to(wiki_root))
        try:
            mt = p.stat().st_mtime
        except OSError:
            continue
        if (not args.rebuild) and rel in mtimes and abs(mtimes[rel] - mt) < 1e-6 \
                and rel in paths:
            skipped += 1
            continue
        try:
            raw = p.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"  warn: read failed {rel}: {e}", file=sys.stderr)
            continue
        prepped = prep_text(raw)
        if not prepped:
            continue
        to_embed.append((rel, prepped, mt))

    print(f"  {skipped} unchanged (skipped), {len(to_embed)} to embed")

    # Build a path->row map for in-place update of changed files.
    path_to_row = {pth: i for i, pth in enumerate(paths)}
    vec_list = [vecs[i] for i in range(vecs.shape[0])]

    new_count = 0
    err_batches = 0
    est_tokens = 0
    start = time.time()
    total = len(to_embed)

    for bi in range(0, total, batch_size):
        chunk = to_embed[bi:bi + batch_size]
        texts = [c[1] for c in chunk]
        est_tokens += sum(len(t) for t in texts)  # rough char-as-token proxy
        try:
            embs = embed_texts(texts, key, dim=DIM)
        except Exception as e:  # noqa: BLE001 - one bad batch must not abort run
            err_batches += 1
            print(f"  ERROR batch {bi}-{bi+len(chunk)}: {e}", file=sys.stderr)
            continue
        for (rel, _txt, mt), emb in zip(chunk, embs):
            arr = np.asarray(emb, dtype=np.float32)
            if rel in path_to_row:
                vec_list[path_to_row[rel]] = arr
            else:
                path_to_row[rel] = len(vec_list)
                vec_list.append(arr)
                paths.append(rel)
                new_count += 1
            mtimes[rel] = mt
        done = min(bi + batch_size, total)
        print(f"  embedded {done}/{total} (new={new_count}, err_batches={err_batches})")
        # 周期性落盘：每 ~200 条 flush，长 run（如 backfill 6911）中断不丢进度
        if vec_list and done % 200 < batch_size:
            _vecs = np.vstack(vec_list).astype(np.float32)
            atomic_write_index(idx_dir, _vecs, paths, {
                "model": MODEL, "dim": DIM,
                "built": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "subdirs": subdirs, "mtimes": mtimes,
            })

    # Assemble final matrix and persist (always leave a valid index).
    final_vecs = (np.vstack(vec_list).astype(np.float32)
                  if vec_list else np.zeros((0, DIM), dtype=np.float32))
    meta_out = {
        "model": MODEL,
        "dim": DIM,
        "built": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "subdirs": subdirs,
        "mtimes": mtimes,
    }
    atomic_write_index(idx_dir, final_vecs, paths, meta_out)

    elapsed = time.time() - start
    npz_size = (idx_dir / "sources.npz").stat().st_size
    print("-" * 60)
    print(f"DONE: total vecs={final_vecs.shape[0]} dim={DIM}")
    print(f"  new this run={new_count}  skipped(unchanged)={skipped}  err_batches={err_batches}")
    print(f"  elapsed={elapsed:.1f}s  est_tokens~{est_tokens}  npz={npz_size/1024:.1f} KB")
    return 0


if __name__ == "__main__":
    # Tiny TDD smoke: cosine(related) > cosine(unrelated). Only runs with --smoke.
    if "--smoke" in sys.argv:
        k = _load_key()
        assert k, "no key for smoke"
        a, b, c = embed_texts(["财富传承与家族信托", "高净值客户的资产传承规划", "今天午饭吃什么"], k)
        va, vb, vc = (np.asarray(x, dtype=np.float32) for x in (a, b, c))
        cos = lambda u, v: float(u @ v / (np.linalg.norm(u) * np.linalg.norm(v)))
        rel, unrel = cos(va, vb), cos(va, vc)
        print(f"smoke: cos(related)={rel:.3f}  cos(unrelated)={unrel:.3f}")
        assert rel > unrel, "related pair should be more similar"
        print("smoke PASS")
        raise SystemExit(0)
    raise SystemExit(main())
