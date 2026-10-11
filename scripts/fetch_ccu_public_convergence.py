"""Acquire only the saved concrete child URLs for CCU's finite ninth pass."""
import json

from fetch_ccu_completion_sources import BUNDLE, fetch


def main():
    plan = json.loads((BUNDLE / "completion-ninth-acquisition-plan.json").read_text())
    for row in plan["sources"]:
        result = fetch(row["ccu_page"], row["label"], row["source_url"])
        print(result["source_id"], result.get("http_status"), result.get("error"))


if __name__ == "__main__":
    main()
