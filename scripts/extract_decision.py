#!/usr/bin/env python3
"""
render_decision.py — 把 LLM 抽出的 4 元组 JSON 渲染成 wiki decisions/ 标准格式 draft

用法：
  当 Claude in-session 跑 interaction-memory-extractor skill 后，
  把抽到的 4 元组结构存为 JSON，调本脚本渲染成 markdown draft。

输入 JSON schema:
{
  "title": "一句话决策摘要",
  "scenario": "某次战略讨论会",
  "date": "2026-05-02",
  "participants": ["alice", "bob"],
  "source_transcript": "file:///path/to/transcript.md",
  "source_minute_token": "",
  "decision_rationale": {
    "final_decision": "采用方案 A",
    "key_arguments": [
      {"argument": "客户反馈强烈", "source_quote": "...", "speaker": "alice", "confidence": "high"},
      ...
    ]
  },
  "commitments": [
    {"owner": "bob", "what": "...", "due": "2026-05-09", "source_quote": "...", "confidence": "high"},
    ...
  ],
  "disagreements": [
    {"topic": "...", "supporter": "carol", "supporter_quote": "...", "opposer": "alice",
     "opposer_quote": "...", "resolution": "...", "confidence": "medium"},
    ...
  ],
  "counterfactuals": [
    {"alternative": "...", "rejected_reason": "...", "source_quote": "...", "confidence": "high"},
    ...
  ],
  "extraction_meta": {
    "tool": "interaction-memory-extractor v0.1",
    "extracted_at": "2026-05-02T14:30:00",
    "transcript_word_count": 12000,
    "self_check_notes": "..."
  }
}

输出：标准 wiki decisions/ markdown draft（带 frontmatter + 审核 checklist 顶部 box）
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def slug_from_title(title: str, max_len: int = 40) -> str:
    """从 title 生成 URL-safe slug"""
    s = re.sub(r"[^\w一-鿿-]+", "-", title.strip()).strip("-")
    return s[:max_len]


def render(data: dict) -> str:
    """JSON → markdown decision page"""
    title = data.get("title", "未命名决策")
    scenario = data.get("scenario", "")
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    participants = data.get("participants", [])
    source_transcript = data.get("source_transcript", "")
    source_minute_token = data.get("source_minute_token", "")

    rationale = data.get("decision_rationale", {})
    commitments = data.get("commitments", [])
    disagreements = data.get("disagreements", [])
    counterfactuals = data.get("counterfactuals", [])
    meta = data.get("extraction_meta", {})

    today = datetime.now().strftime("%Y-%m-%d")
    participants_yaml = "[" + ", ".join(f'"{p}"' for p in participants) + "]"

    out = []
    out.append("---")
    out.append(f"title: {title}")
    out.append("type: decision")
    out.append("circle: institutional")
    out.append(f"created: {today}")
    out.append(f"updated: {today}")
    out.append("audience: both")
    out.append("maturity: developing")
    out.append(f"source_transcript: {source_transcript}")
    if source_minute_token:
        out.append(f"source_minute_token: {source_minute_token}")
    out.append(f"participants: {participants_yaml}")
    out.append("decision_status: pending")
    out.append("related: []")
    out.append("tags: [decision, extracted-by-interaction-memory-extractor]")
    out.append("---")
    out.append("")
    out.append(f"# {title}")
    out.append("")

    # ── 顶部 Draft 提示框 ──
    out.append("> ⚠️ **Draft（待人审）— 抽取自 interaction-memory-extractor v0.1**")
    out.append(">")
    out.append("> **审核流程**：")
    out.append("> 1. 检查 frontmatter（participants / 日期 / source 是否准确）")
    out.append("> 2. 逐节核对原句引用 — 任意一句 grep 不到原 transcript = 标 ⚠️ 重抽")
    out.append("> 3. 看 confidence 分布 — 全 high 警惕（应有 mix）")
    out.append("> 4. 审完后：")
    out.append("> ```")
    out.append(f">    mv decisions/{slug_from_title(title)}.md.draft.md decisions/{slug_from_title(title)}.md")
    out.append("> ```")
    out.append("> 5. frontmatter `decision_status` 改为 `accepted` / `rejected` / `superseded`")
    out.append("")

    # ── 1. 摘要 ──
    out.append("## 摘要")
    out.append("")
    out.append(f"- **场景**: {scenario or '(未提供)'}")
    out.append(f"- **日期**: {date}")
    out.append(f"- **参与方**: {' · '.join(participants) if participants else '(未提供)'}")
    out.append(f"- **决策状态**: pending（待人审）")
    out.append(f"- **来源**: `{source_transcript}`")
    if source_minute_token:
        out.append(f"- **minute_token**: `{source_minute_token}`")
    out.append("")
    out.append("---")
    out.append("")

    # ── 2. Decision Rationale ──
    out.append("## 1. Decision Rationale · 为什么这样决定")
    out.append("")
    final = rationale.get("final_decision", "(未提取出最终决定)")
    out.append(f"**最终决定**: {final}")
    out.append("")
    args = rationale.get("key_arguments", [])
    if args:
        out.append("**关键论据链**:")
        out.append("")
        for i, a in enumerate(args, 1):
            arg_text = a.get("argument", "")
            quote = a.get("source_quote", "")
            speaker = a.get("speaker", "")
            conf = a.get("confidence", "?")
            out.append(f"{i}. {arg_text}")
            if quote:
                speaker_tag = f" — `{speaker}`" if speaker else ""
                out.append(f"   - 来源原句：\"{quote}\"{speaker_tag}")
            out.append(f"   - confidence: **{conf}**")
    else:
        out.append("_(无关键论据链 — 抽取阶段未识别)_")
    out.append("")
    out.append("---")
    out.append("")

    # ── 3. Commitments ──
    out.append("## 2. Commitments · 承诺")
    out.append("")
    if commitments:
        out.append("| Owner | Commitment | Due | 来源原句 | Confidence |")
        out.append("|---|---|---|---|---|")
        for c in commitments:
            owner = c.get("owner", "?")
            what = c.get("what", "")
            due = c.get("due", "(未明确)")
            quote = c.get("source_quote", "").replace("|", "\\|")
            conf = c.get("confidence", "?")
            out.append(f"| {owner} | {what} | {due} | \"{quote}\" | {conf} |")
    else:
        out.append("_(无 commitment 命中 — 此 transcript 未识别明确承诺信号)_")
    out.append("")
    out.append("---")
    out.append("")

    # ── 4. Disagreements ──
    out.append("## 3. Disagreements · 反对意见")
    out.append("")
    if disagreements:
        for i, d in enumerate(disagreements, 1):
            topic = d.get("topic", f"争议点 {i}")
            out.append(f"### 3.{i} {topic}")
            out.append("")
            sup = d.get("supporter", "?")
            sup_q = d.get("supporter_quote", "")
            opp = d.get("opposer", "?")
            opp_q = d.get("opposer_quote", "")
            res = d.get("resolution", "(未明确收敛)")
            conf = d.get("confidence", "?")
            out.append(f"- **支持方**: {sup} · 论点：\"{sup_q}\" · confidence: {conf}")
            out.append(f"- **反对方**: {opp} · 论点：\"{opp_q}\"")
            out.append(f"- **解决方式**: {res}")
            out.append("")
    else:
        out.append("_(无显著分歧 — 此 transcript 未识别反对意见)_")
    out.append("")
    out.append("---")
    out.append("")

    # ── 5. Counterfactuals ──
    out.append("## 4. Counterfactuals · 考虑过的替代方案")
    out.append("")
    if counterfactuals:
        for cf in counterfactuals:
            alt = cf.get("alternative", "?")
            reason = cf.get("rejected_reason", "")
            quote = cf.get("source_quote", "")
            conf = cf.get("confidence", "?")
            out.append(f"- **{alt}**")
            out.append(f"  - 否决原因：{reason}")
            if quote:
                out.append(f"  - 来源原句：\"{quote}\"")
            out.append(f"  - confidence: **{conf}**")
    else:
        out.append("_(无 counterfactual — 此 transcript 未识别被否决的替代方案)_")
    out.append("")
    out.append("---")
    out.append("")

    # ── 6. 抽取元数据 ──
    out.append("## 5. 抽取元数据")
    out.append("")
    out.append(f"- **抽取工具**: {meta.get('tool', 'interaction-memory-extractor v0.1')}")
    out.append(f"- **抽取时间**: {meta.get('extracted_at', datetime.now().isoformat(timespec='seconds'))}")
    if meta.get("transcript_word_count"):
        out.append(f"- **transcript 字数**: {meta['transcript_word_count']}")
    out.append("- **审核状态**: ⚠️ Draft（待人审）")
    out.append("- **审核 checklist**:")
    out.append('  - [ ] commitments 都准确（不是误识别「将来打算」为「承诺」）')
    out.append("  - [ ] 原句引用真实存在（grep 验证）")
    out.append("  - [ ] confidence 标注合理（不全 high）")
    out.append("  - [ ] decision_rationale 没漏关键论据")
    out.append("  - [ ] disagreements 双方论点都列出")
    out.append("  - [ ] counterfactuals 否决原因明确")
    if meta.get("self_check_notes"):
        out.append(f"- **抽取自检**: {meta['self_check_notes']}")
    out.append("")
    out.append("---")
    out.append("")
    out.append('_This draft was generated by extract_decision.py from a transcript. Review and delete this draft notice before promotion._')

    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Yuanli-OS Company Brain - render a 4-tuple JSON into a wiki decisions/ draft"
    )
    p.add_argument("--json-input", type=Path, required=True, help="Path to 4-tuple JSON file")
    p.add_argument("--wiki-root", type=Path, default=None,
                   help="Wiki root (default uses cwd; output goes to <wiki-root>/decisions/)")
    p.add_argument("--output", type=Path, help="Override output path (default = <wiki-root>/decisions/<date>-<slug>.md.draft.md)")
    p.add_argument("--title", help="Override the title from the JSON")
    args = p.parse_args()

    if not args.json_input.is_file():
        print(f"error: JSON file not found: {args.json_input}", file=sys.stderr)
        return 1

    try:
        data = json.loads(args.json_input.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"error: JSON decode failed: {e}", file=sys.stderr)
        return 2

    if args.title:
        data["title"] = args.title

    md = render(data)

    if args.output:
        out_path = args.output
    else:
        date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
        slug = slug_from_title(data.get("title", "decision"))
        out_path = Path(args.wiki_root or ".") / "decisions" / f"{date}-{slug}.md.draft.md"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    print(f"draft rendered: {out_path}", file=sys.stderr)
    print(f"  after review: mv {out_path} {str(out_path).replace('.md.draft.md', '.md')}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
