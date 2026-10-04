"""Rebuild and validate offline school translations from reviewed span output."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exchange_info.public_translation import _valid_translation, cached_translation, needs_translation
from translate_school_foreign_spans import phrases, segments
from translate_school_content import save


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", type=Path)
    args = parser.parse_args()
    path = Path(__file__).resolve().parents[1] / "src/exchange_info/official_data/public_content_translations_zh.json"
    existing = json.loads(path.read_text("utf-8"))
    spans = json.loads((args.artifacts / "spans.json").read_text("utf-8"))
    whole_path = args.artifacts / "whole-spans.json"
    whole = json.loads(whole_path.read_text("utf-8")) if whole_path.exists() else {}
    manual_path = args.artifacts / "manual-spans.json"
    draft_path = args.artifacts / "whole-spans-drafts.json"
    if draft_path.exists():
        whole.update({source: target for source, target in json.loads(draft_path.read_text("utf-8")).items()
            if _valid_translation(source, target)})
    for extra in ("final-spans.json", "final-spans-drafts.json"):
        if (args.artifacts / extra).exists():
            whole.update({source: target for source, target in json.loads((args.artifacts / extra).read_text("utf-8")).items()
                if _valid_translation(source, target)})
    manual = json.loads(manual_path.read_text("utf-8")) if manual_path.exists() else {}
    whole.update(manual)
    # Short connectors and isolated month labels have complete, unambiguous meanings.
    spans.update({"on": "於", "On": "於", "in": "在", "of": "的", "to": "至", "or": "或",
        "and": "與", "at": "於", "from": "從", "one": "一", "two": "兩", "three": "三",
        "four": "四", "five": "五", "six": "六", "November": "十一月", "May, 2025": "2025 年五月",
        "Nov, 2022": "2022 年十一月", "View more": "查看更多", "dots": "點", "points": "分",
        "cc": "副本", "residence": "住所", "Residence": "住所", "by metro": "搭乘地鐵",
        "School of Business/Management": "商學院／管理學院"})
    rows = {(r["original"], r["url"]): r for r in existing if _valid_translation(r["original"], r["zh"])}
    by_text = {r["original"]: r["zh"] for r in rows.values()}
    pending = []
    for row in json.loads((args.artifacts / "translation-targets.json").read_text("utf-8")):
        original, url = row["text"], row.get("url", row.get("source_url", ""))
        if not needs_translation(original):
            continue
        complete = original
        for start, end, text in reversed(segments(original)):
            complete = complete[:start] + whole.get(text, spans.get(text, text)) + complete[end:]
        complete = manual.get(original, phrases(complete))
        value = complete if _valid_translation(original, complete) else by_text.get(original) or phrases(original)
        if original not in by_text and not _valid_translation(original, complete):
            for start, end, text in reversed(segments(value)):
                value = value[:start] + spans.get(text, text) + value[end:]
        if re.search(r"fact\s*sheet", original, re.I):
            value = value.replace("事實表", "交換資訊表")
        # Correct ambiguous fragment translations when the original gives the full meaning.
        if re.search(r"off-campus\s+housing", original, re.I):
            value = value.replace("關閉-校區 住宿", "校外住宿")
        if "Master Welcome Team" in original or "The Welcome Team Master" in original:
            value = value.replace("迎新團隊主管", "碩士班迎新團隊")
        if re.search(r"Twenty\s+Campus", original, re.I):
            value = re.sub(r"Twenty\s*校區|二十\s*校區", "Twenty Campus", value)
        if re.search(r"\bstudios\b", original, re.I):
            value = value.replace("工作室", "套房")
        if _valid_translation(original, value):
            rows[original, url] = {"original": original, "url": url, "zh": value,
                "status": "machine", "method": "validated_local_foreign_spans"}
            by_text[original] = value
        elif not cached_translation(original, url, Path("data")):
            pending.append({**row, "proposed": value})
    save(path, list(rows.values()))
    save(args.artifacts / "remaining-translations.json", pending)
    print(json.dumps({"bundled": len(rows), "remaining": len(pending)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
