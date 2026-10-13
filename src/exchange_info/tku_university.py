"""TKU profile values consumed by the shared registry."""
import json
from pathlib import Path

_directory = json.loads((Path(__file__).parent / "official_data/tku/academic_units.json").read_text())
PROFILE = {
    "id": "tku", "school_name": "淡江大學", "short_name": "淡江",
    "english_name": "Tamkang University",
    "aliases": ("淡江大學", "淡江", "淡大", "TKU", "Tamkang University"),
    "hero_image": "/static/assets/tku-campus-placeholder.svg",
    "official_url": "https://oieie.tku.edu.tw/",
    "coverage_note": "部分支援：287校全量名錄／甄選機構聯集；2027–2028日語二甄4校7名已截止。新增第一梯25校50歷史名額，其他協議及一般原文列參考；新版、校區、期限與照片授權缺口逐校保存。",
    "support_level": "basic", "partner_count_hint": 287,
    "academic_score_minimum": 75,
    "student_card_signals": ("淡江大學", "TAMKANGUNIVERSITY", "TKU"),
    # This is a registration directory, not a list of eligible exchange units.
    "colleges": tuple(_directory["colleges"]),
}
