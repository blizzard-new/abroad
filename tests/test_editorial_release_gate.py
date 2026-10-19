"""The release gate distinguishes model defaults from actual article changes."""
import importlib.util
import json
from pathlib import Path

from exchange_info.seo_articles import ARTICLES


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_editorial", ROOT / "scripts/check_editorial.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def test_unchanged_shipped_json_is_equivalent_to_validated_content():
    for slug, article in ARTICLES.items():
        raw = json.loads((ROOT / f"src/exchange_info/editorial/{slug}.json").read_text())
        assert gate.meaningful_content(raw) == gate.meaningful_content(article.model_dump(mode="json"))


def test_source_recheck_is_not_a_content_change_but_corrected_text_is():
    data = ARTICLES["exchange-budget"].model_dump(mode="json")
    previous = gate.meaningful_content(data)
    data["checked"] = "2026-10-20"
    assert gate.meaningful_content(data) == previous
    data["sections"][0]["paragraphs"][0] += "新增當期官方說明。"
    assert gate.meaningful_content(data) != previous
