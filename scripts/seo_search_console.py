"""Collect Search Console baselines and indexed-version samples, using read-only OAuth."""
import argparse
import json
import os
from datetime import date, timedelta
from pathlib import Path
import requests

from exchange_info.seo_reporting import SearchConsole, inspection_sample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token-env", default="UNIWAY_GOOGLE_ACCESS_TOKEN", help="Name of environment variable, never the token value")
    parser.add_argument("--site", default="https://app.uniway-tw.com/")
    parser.add_argument("--end", type=date.fromisoformat, default=date.today() - timedelta(days=3), help="Last complete date; default allows 3 days for reporting lag")
    parser.add_argument("--audit", type=Path, help="JSON produced by scripts/audit_seo.py")
    parser.add_argument("--max-inspections", type=int, default=30)
    parser.add_argument("--ga4-property", help="Optional numeric GA4 property ID; token also needs analytics.readonly")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 0 <= args.max_inspections <= 100:
        parser.error("max-inspections must be between 0 and 100")
    if args.end >= date.today():
        parser.error("end must be a completed past date")
    if args.site != "https://app.uniway-tw.com/":
        parser.error("This project collector targets the verified https://app.uniway-tw.com/ property")
    audit = json.loads(args.audit.read_text(encoding="utf-8")) if args.audit else {"pages": []}
    urls = inspection_sample(audit, args.site, args.max_inspections)
    try:
        client = SearchConsole(os.environ.get(args.token_env, ""), args.site)
        result = client.collect(args.end, urls)
        if args.ga4_property:
            result["ga4_organic_events"] = client.ga4_events(args.ga4_property, args.end - timedelta(days=27), args.end)
    except (ValueError, OSError, requests.RequestException) as error:
        parser.exit(1, str(error) + "\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved read-only Google data; {len(urls)} indexed-version inspections. No live test or indexing request was made.")


if __name__ == "__main__":
    main()
