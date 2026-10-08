"""TKU profile values consumed by the shared registry."""
PROFILE = {
    "id": "tku", "school_name": "淡江大學", "short_name": "淡江",
    "english_name": "Tamkang University",
    "aliases": ("淡江大學", "淡江", "淡大", "TKU", "Tamkang University"),
    "hero_image": "/static/assets/tku-campus-placeholder.svg",
    "official_url": "https://oieie.tku.edu.tw/",
    "coverage_note": "部分支援：2027–2028日語第二次甄選4校7名，已截止；英歐及中文組新版尚未核實，124筆舊期資料獨立保存。",
    "support_level": "basic", "partner_count_hint": 4,
    "academic_score_minimum": 75,
    "student_card_signals": ("淡江大學", "TAMKANGUNIVERSITY", "TKU"),
    # A verified college directory has not been captured; never reuse CGU/NTPU units.
    "colleges": (),
}
