"""Patrol summaries must preserve currency amounts already in the local bundle."""
import hashlib
import json
from pathlib import Path


BUNDLE = Path(__file__).parents[1] / "src" / "exchange_info" / "official_data" / "cmu"


def test_cmu_patrol_summaries_preserve_existing_currency_amounts():
    info = json.loads((BUNDLE / "exchange_info.json").read_text(encoding="utf-8"))
    periods = "\n".join(info["application_period"])
    assert "NT$5,000" in periods
    for amount in ("45萬", "40萬", "35萬", "30萬", "50萬"):
        assert f"NT${amount}" in periods
    for filename in ("exchange_info.json", "student_dashboard.json", "pages.jsonl"):
        text = (BUNDLE / filename).read_text(encoding="utf-8")
        assert "NT,000" not in text, filename
        assert "最高 NT、" not in text, filename
    for line in (BUNDLE / "pages.jsonl").read_text(encoding="utf-8").splitlines():
        page = json.loads(line)
        if "NT$5,000" in page["text"]:
            assert page["content_hash"] == hashlib.sha256(page["text"].encode()).hexdigest()
