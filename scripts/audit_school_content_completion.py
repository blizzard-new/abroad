"""Audit completed public school content without touching source or review data."""
from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exchange_info.public_translation import cached_translation, needs_translation, _valid_translation
from exchange_info.school_content import complete_destination_profile, SUPPLEMENTS
from exchange_info.storage import load_destination_profiles
from exchange_info.university_locations import load_university_locations

GAPS = re.compile(r"未公開|尚未|未取得|待補|未提供|未完成|無法.*核對")
LABELS = {"city": "城市", "housing_summary": "住宿", "cost_summary": "生活費",
    "transport_summary": "交通", "campus_life_summary": "校園生活"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", type=Path)
    args = parser.parse_args()
    profiles = load_destination_profiles(Path("data"), include_bundled_baseline=True)
    locations = load_university_locations(Path("data"))
    completed = [complete_destination_profile(p, Path("data"), locations=locations) for p in profiles]
    inventory = json.loads((args.artifacts / "inventory-input.json").read_text("utf-8"))
    by_school = {(p.home_university, p.school_name): p for p in completed}
    for row in inventory:
        if row["kind"] == "profile":
            if p := by_school.get((row["home"], row["data"]["school_name"])):
                row["data"] = p.model_dump(mode="json")
    current = args.artifacts / "completed-inventory.json"
    current.write_text(json.dumps(inventory, ensure_ascii=False), "utf-8")
    code = """const fs=require('fs'),zh=require('./src/exchange_info/static/public-content-zh.js');
const rows=JSON.parse(fs.readFileSync(process.argv[1],'utf8')),out=[];
for(const r of rows) for(const t of zh.collect(r.data))out.push({kind:r.kind,home:r.home,school:r.data.school_name||'',text:t.text,url:t.source_url});
process.stdout.write(JSON.stringify([...new Map(out.map(r=>[JSON.stringify([r.text,r.url]),r])).values()]));"""
    targets = json.loads(subprocess.check_output(["node", "-e", code, str(current)], encoding="utf-8"))
    pending = [r for r in targets if needs_translation(r["text"]) and not cached_translation(r["text"], r["url"], Path("data"))]
    bundled = json.loads(SUPPLEMENTS.with_name("public_content_translations_zh.json").read_text("utf-8"))
    assert all(_valid_translation(r["original"], r["zh"]) for r in bundled)
    supplements = json.loads(SUPPLEMENTS.read_text("utf-8"))
    research = json.loads((args.artifacts / "gap-research.json").read_text("utf-8"))
    gaps = []
    for p in completed:
        missing = [LABELS[f] for f in LABELS if not getattr(p, f) or GAPS.search(getattr(p, f))]
        if missing:
            gaps.append({"母校": p.home_university, "合作校": p.school_name, "國家": p.country,
                "仍須官方核對": "、".join(missing), "來源": " | ".join(s.source_url for s in p.sources)})
    docs = Path("docs")
    csv_path = docs / "school-content-unresolved-2026-10-01.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["母校", "合作校", "國家", "仍須官方核對", "來源"])
        writer.writeheader(); writer.writerows(gaps)
    save_pending = docs / "school-content-translation-gaps-2026-10-01.json"
    save_pending.write_text(json.dumps(pending, ensure_ascii=False, indent=2) + "\n", "utf-8")
    changed_cities = sum(not p.city and bool(c.city) for p, c in zip(profiles, completed))
    stats = {"schools": len(profiles), "bundled_translations": len(bundled), "translated_or_original_targets": len(targets)-len(pending),
        "pending_translations": len(pending), "supplemented_schools": len(supplements),
        "supplemented_fields": sum(len(r["fields"]) for r in supplements), "new_cities": changed_cities,
        "schools_with_unresolved_facts": len(gaps), "researched_schools": len(research),
        "researched_pages": sum(len(r["pages"]) for r in research)}
    urls = {s["url"] for r in supplements for f in r["fields"] for s in f["sources"]}
    lines = ["# 合作校中文內容與資料補查（2026-10-01）", "", "此紀錄區分翻譯、官方補查與尚待確認的事實，不能作為人工雙審或上線審核證明。", "", "## 實際覆蓋", ""]
    stat_labels = {"schools": "盤點學校", "bundled_translations": "附原文與來源的中文翻譯",
        "translated_or_original_targets": "已有中文或可保留原文的公開欄位", "pending_translations": "仍待處理的翻譯欄位",
        "supplemented_schools": "本輪新增官方資訊的學校", "supplemented_fields": "新增官方資訊欄位",
        "new_cities": "補入城市", "schools_with_unresolved_facts": "仍有城市、住宿、費用、交通或校園生活缺口的學校",
        "researched_schools": "補查學校", "researched_pages": "補查頁面"}
    lines.extend(f"- {stat_labels[key]}：{value}" for key, value in stats.items())
    lines += ["", "翻譯涵蓋公開合作校資料、學校詳情、申請流程、學生心得與既有生活情報。專有名稱、網址、測驗縮寫保留原文。機器翻譯保留原始來源；數字、幣別、日期與住宿否定條件經程式檢查，但不等同逐句人工審核。", "", "## 已補查內容", "", "| 母校 | 合作校 | 已補項目 |", "| --- | --- | --- |"]
    lines.extend(f"| {r['home_university']} | {r['school_name'].replace('|','／')} | {'、'.join(LABELS[f['field']] for f in r['fields'])} |" for r in supplements)
    lines += ["", "新增城市只採用現有已核對座標資料中的城市；未重新地理編碼。補查欄位只有在原內容仍與研究時的缺漏一致時才套用，不覆蓋後續人工更新。既有學校 profile 原始資料與審核核准事件未改寫。", "", "## 尚待確認", "", "[逐校事實缺口清單](school-content-unresolved-2026-10-01.csv)與[翻譯缺口清單](school-content-translation-gaps-2026-10-01.json)列出未能完成的項目。缺口數只涵蓋城市及四項生活摘要，不代表其他申請條件、期限、課程與生活情報均完整。研究只代表本輪取得的可核對頁面，不能據此聲稱學校未曾公開資訊。截止日、床位保證、簽證要求、課程適用性及補助金額均不可由推測補上。", "", "原文中亦發現截斷段落、網站模板、跨校內容混入，以及學位生學費混列生活費的情形。例如印尼伊斯蘭大學 UII 的原生活摘要出現 UIII 內容，武漢大學費用摘要混入其他合作校的學費待遇，部分第三方心得是高中交流或其他大學。翻譯只能處理文字，不能修復這些事實歸屬問題，仍須重新取得正確來源；不得將缺口改成已查核。", "", "俄斯特拉發大學的生活費頁標示更新於 2023 年，相關金額保留歷史參考提示。未標示年度的金額亦註明需核對當期；各校費用不作匯率換算。學生心得與第三方評論不升格為官方規定。本輪沒有驗證歷史『雙人審核』紀錄，翻譯不構成新的真人核准。", "", "## 補查來源", ""]
    lines.extend(f"- <{url}>" for url in sorted(urls))
    (docs / "school-content-completion-2026-10-01.md").write_text("\n".join(lines) + "\n", "utf-8")
    (args.artifacts / "completion-stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), "utf-8")
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
