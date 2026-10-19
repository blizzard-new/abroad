"""Generate a local weekly SEO report from collected evidence; missing values stay null."""
import argparse
import json
from pathlib import Path

from exchange_info.seo_reporting import build_search_report, summarize_access_log


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search-console", type=Path, help="Collector JSON; omit when no connected Google evidence")
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--access-log", type=Path, help="Optional Caddy JSONL access log; output excludes IPs and raw URLs")
    parser.add_argument("--brand-pattern", default=r"uni\s*way|uniway-tw")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    read = lambda path: json.loads(path.read_text(encoding="utf-8")) if path else {}
    report = build_search_report(read(args.search_console), read(args.audit), args.brand_pattern)
    if args.access_log:
        with args.access_log.open(encoding="utf-8") as stream:
            report["server"] = summarize_access_log(stream)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    def fmt(value):
        return "尚無資料" if value is None else str(value)
    lines = ["# UniWay 每週 SEO 證據報告", "", f"範圍：{fmt(report['scope'])}", f"期間：{fmt(report['period'])}", "",
             "| 指標 | 本期 | 前期 |", "| --- | ---: | ---: |"]
    for key, label in (("clicks", "點擊"), ("impressions", "曝光"), ("ctr", "CTR（比例）"), ("position", "平均排名")):
        lines.append(f"| {label} | {fmt(report['current'][key])} | {fmt(report['previous'][key])} |")
    ga4 = report.get("ga4_organic_events")
    lines += ["", "## GA4 臺灣自然搜尋互動", ""]
    if ga4 is None:
        lines.append("尚無 GA4 資料；需建立資源、另外同意追蹤並接通唯讀 API。")
    else:
        lines += ["| 事件 | 次數 | 使用者數 |", "| --- | ---: | ---: |"]
        for row in ga4.get("rows", []):
            name = row["dimensionValues"][0]["value"].replace("|", "\\|")
            values = row["metricValues"]
            lines.append(f"| {name} | {values[0]['value']} | {values[1]['value']} |")
        lines.append("使用者可能觸發多種事件，不可將各列使用者數加總成不重複人數。")
    lines += ["", "非品牌查詢僅涵蓋 Google 回傳的明細；收錄檢查為代表樣本，不能當成全站收錄率。", "", report["scope_warning"], "",
              "詳細 canonical／noindex／抓取診斷及 sitemap 狀態見同名 JSON。未連線時不把未知填成零。"]
    args.output.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Saved JSON and Markdown report; missing Google data is explicitly unknown.")


if __name__ == "__main__":
    main()
