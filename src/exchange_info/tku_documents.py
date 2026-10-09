"""TKU preparation notes; official application and declarations stay official files."""
from __future__ import annotations

from .models import ApplicationDocumentTemplate
from .tku_data import CHECKED_AT, load_tku_sources


def tku_application_templates() -> list[ApplicationDocumentTemplate]:
    source=next(s for s in load_tku_sources() if s["id"]=="jp-revision-attachment-1")
    result=[]
    for slug,title in [("autobiography","自傳"),("study-plan","研習計畫")]:
        result.append(ApplicationDocumentTemplate(id=f"tku-{slug}-preparation",title=f"淡江2027–2028日語二甄{title}準備稿",
            short_title=f"{title}準備稿",category="申請準備",stage="校內申請",
            description="本次校內已截止。依官方PDF p.4整理中日文準備稿；正式線上申請表與切結書仍使用官方文件，後續年度不能沿用。",
            fields=[{"id":"chinese_text","label":f"中文{title}","field_type":"textarea","required":True,"max_length":10000},
                    {"id":"japanese_text","label":f"日文{title}","field_type":"textarea","required":True,"max_length":10000}],
            destinations=["所屬系所"],program_types=["exchange"],official_layout=False,
            print_sides="single_sided",print_note="所有申請資料總共不得超過16頁，A4單面、不裝訂、L型套。",
            source_url=source["source_url"]+"#page=4",source_checked_at=CHECKED_AT,version="2027-2028-japanese-round-2"))
    return result
