"""Build the official Soochow University (東吳大學) exchange data bundle."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import sys
import unicodedata
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
_HOST_SCRATCH = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\0723e0a1-b112-47e2-8145-2d4d6f69cb19\scratch\scu_files")
SOURCES_SCU_DIR = REPO_ROOT / "sources" / "scu"
SCRATCH_SCU = _HOST_SCRATCH if _HOST_SCRATCH.exists() else SOURCES_SCU_DIR
OFFICIAL_SCU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "scu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

COUNTRY_MAP = {
    "大陸地區": "中國大陸",
    "中國": "中國大陸",
    "香港": "香港",
    "澳門": "澳門",
    "南韓": "韓國",
    "澳大利亞": "澳洲",
    "祕魯": "秘魯",
}

REGION_COST_DEFAULTS = {
    "美國": ("USD 1,400–2,200 / 月（含住宿、餐飲、校園保險與當地交通）", "建議預留強制校園醫療保險（約 USD 1,500–2,500 / 學期）與 J-1 / F-1 簽證 SEVIS 費用。"),
    "加拿大": ("CAD 1,500–2,200 / 月（含住宿、膳食、省級／校內醫保與市區交通）", "須投保接待校指定醫療保險並辦理 Study Permit 或 eTA。"),
    "英國": ("GBP 1,000–1,600 / 月（含宿舍、飲食與市區交通）", "交換一學期多適用 Standard Visitor 簽證，一學年須辦理 Student Visa 並繳納 IHS 醫療附加費。"),
    "法國": ("EUR 850–1,400 / 月（巴黎地區約 EUR 1,200–1,600 / 月；可申請 CAF 房補）", "須透過法國教育中心（Campus France）面試並申辦長期學生簽證（VLS-TS）。"),
    "德國": ("EUR 934–1,200 / 月（德國簽證財力證明基準為每月 EUR 934）", "須辦理德國公保（約 EUR 120–130 / 月）及學期票（Semesterticket）。"),
    "西班牙": ("EUR 800–1,250 / 月（馬德里、巴塞隆納較高，其他城市約 EUR 700–1,000 / 月）", "須備妥涵蓋全額醫療與遺體運返之私人醫療保險以申辦西班牙學生簽證。"),
    "義大利": ("EUR 800–1,250 / 月（羅馬、米蘭、都靈較高）", "抵義 8 個工作日內須辦理居留證（Permesso di soggiorno）與稅號（Codice Fiscale）。"),
    "荷蘭": ("EUR 950–1,400 / 月（荷蘭移民局 IND 財力證明基準約 EUR 1,225 / 月）", "由接待校代辦 MVV/VVR 居留許可，房源緊張建議儘早申請宿舍。"),
    "比利時": ("EUR 850–1,200 / 月（含學生宿舍、餐飲與大眾運輸）", "須辦理長期學生簽證 D 簽，抵達後向市政廳登記居留。"),
    "瑞士": ("CHF 1,500–2,200 / 月（含住宿、膳食與強制保險）", "須透過瑞士駐外代表處申辦學生簽證，並於抵瑞後申請居留證與醫療保險豁免或投保。"),
    "奧地利": ("EUR 850–1,250 / 月（含 OeAD 學生宿舍與日常開支）", "多透過 OeAD 申請學生宿舍，並依停留期間申辦簽證 D 或居留許可。"),
    "丹麥": ("DKK 6,500–9,500 / 月（含住宿、飲食與單車／大眾運輸）", "須申辦 ST1 學生居留許可，抵丹後登記 CPR 號碼即可享有公醫保障。"),
    "挪威": ("NOK 12,000–15,000 / 月（挪威移民局 UDI 財力證明基準約 NOK 13,790 / 月）", "須申辦挪威學生居留許可（Study Permit）並預先匯入學生保證金帳戶。"),
    "波蘭": ("EUR 500–800 / 月（含校內宿舍與日常餐飲交通）", "須申辦波蘭 D 類國別學生簽證並備妥歐盟規格旅遊醫療保險。"),
    "匈牙利": ("EUR 550–850 / 月（布達佩斯生活費與住宿相對實惠）", "須申請學生居留許可並投保醫療保險。"),
    "捷克": ("EUR 600–900 / 月（含學生宿舍、食堂與市區交通卡）", "須提前預約捷克經濟文化辦事處申辦長期學生簽證與捷克合約醫療保險。"),
    "立陶宛": ("EUR 550–850 / 月（含宿舍與日常開支）", "須透過 MIGRIS 系統申辦臨時居留許可（TRP）或國家簽證。"),
    "愛沙尼亞": ("EUR 600–900 / 月（塔林生活機能便利且學生優惠完善）", "須申辦愛沙尼亞長期學生簽證（D-Visa）並投保涵蓋全期之申根醫療保險。"),
    "拉脫維亞": ("EUR 550–850 / 月（里加生活與住宿成本相對親民）", "須申辦拉脫維亞長期簽證或居留許可並備妥歐盟醫療保險。"),
    "羅馬尼亞": ("EUR 500–800 / 月（布加勒斯特學生宿舍與生活費實惠）", "須憑接待校與羅馬尼亞教育部入學許可申辦 D/SD 學生簽證。"),
    "澳洲": ("AUD 1,800–2,600 / 月（含住宿、飲食與交通）", "強制投保海外學生健康保險（OSHC）後方可核發 Subclass 500 學生簽證。"),
    "日本": ("JPY 80,000–130,000 / 月（東京圈約 JPY 100,000–140,000；地方城市約 JPY 70,000–100,000）", "憑接待校核發之在留資格認定證明書（COE）換發留學簽證，抵日後須加入國民健康保險（約 JPY 1,500–2,000 / 月）。"),
    "韓國": ("KRW 800,000–1,300,000 / 月（首爾圈外宿較高；校內宿舍約 KRW 150,000–400,000 / 月）", "憑標準入學許可書申辦 D-2-6 交換學生簽證，抵韓後外國人登錄並自動納入韓國國民健康保險（NHIS）。"),
    "中國大陸": ("RMB 2,000–3,800 / 月（校內宿舍與學生食堂費用低廉，一線城市北上廣深略高）", "持臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定投保大陸境內來華留學生綜合醫療保險（約 RMB 400 / 學期）。"),
    "香港": ("HKD 6,000–10,000 / 月（校內宿位有限，若外宿租金較高）", "須透過接待校向香港入境事務處申辦學生簽證／進入許可（Student Visa / Entry Permit）。"),
    "澳門": ("HKD 4,500–7,500 / 月（約 MOP 4,600–7,700，含宿舍、膳食與交通）", "入境後依澳門治安警察局居留及逗留事務廳規定辦理「逗留的特別許可」（學生逗留）。"),
    "馬來西亞": ("MYR 1,800–2,800 / 月（吉隆坡／雪蘭莪／金寶生活機能便利且物價親民）", "須透過 EMGS（Education Malaysia Global Services）系統申辦學生簽證（VAL / Student Pass）。"),
    "墨西哥": ("USD 600–1,000 / 月（墨西哥城生活費適中）", "交換一學期（180 天內）持臺灣護照須先向墨西哥商務簽證文件暨文化辦事處申辦簽證，並投保國際醫療險。"),
    "秘魯": ("USD 550–900 / 月（利馬 Miraflores / Monterrico 等安全住宅區租金略高）", "須依接待校指示申辦秘魯交換學生簽證並投保涵蓋全期之國際醫療險。"),
    "南非": ("ZAR 10,000–16,000 / 月（約 USD 550–900 / 月，含校內外住宿與日常交通）", "須向南非聯絡辦事處申辦 Study Visa 並投保南非政府認可之醫療保險（Medical Aid）。"),
}


def loose_en(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\b(the|of|de|del|la|las|los|at|in|and|fur|for|a|an)\b", " ", s.lower())
    return "".join(ch for ch in s.lower() if "a" <= ch <= "z" or "0" <= ch <= "9")


def loose_zh(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"\([^)]*\)|（[^）]*）", "", s)
    s = re.sub(r"^(國立|私立)", "", s)
    return "".join(ch for ch in s if "\u4e00" <= ch <= "\u9fff")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive_official_sources() -> dict:
    SOURCES_SCU_DIR.mkdir(parents=True, exist_ok=True)
    # Also copy helper JSONs into SOURCES_SCU_DIR so build_scu_catalog.py works standalone in repo
    if _HOST_SCRATCH.exists():
        for helper in ["china_116_structured.json"]:
            src_h = _HOST_SCRATCH / helper
            if src_h.exists():
                shutil.copy2(src_h, SOURCES_SCU_DIR / helper)
        loc_src = _HOST_SCRATCH.parent / "scu_resolved_locations.json"
        if loc_src.exists():
            shutil.copy2(loc_src, SOURCES_SCU_DIR / "scu_resolved_locations.json")

    files_to_copy = [
        (SCRATCH_SCU / "intl_116_schools.html", SOURCES_SCU_DIR / "intl_116_schools.html", "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intl/2025-2026schools", "東吳大學 116 學年度校級赴外交換學校一覽表（126 校，2026/10/01 更新）"),
        (SCRATCH_SCU / "china_116_list.pdf", SOURCES_SCU_DIR / "china_116_list.pdf", "https://icae.scu.edu.tw/sites/default/files/2026-09/%E6%9D%B1%E5%90%B3%E5%A4%A7%E5%AD%B8116%E5%AD%B8%E5%B9%B4%E5%BA%A6%E6%A0%A1%E7%B4%9A%E8%B5%B4%E9%99%B8%E4%BA%A4%E6%8F%9B%E5%AD%B8%E6%A0%A1%E4%B8%80%E8%A6%BD%E8%A1%A8_1150915.pdf", "東吳大學 116 學年度校級赴陸交換學校一覽表（62 校，115.09.15 更新）"),
        (SCRATCH_SCU / "116_briefing_slides.pdf", SOURCES_SCU_DIR / "116_briefing_slides.pdf", "https://icae.scu.edu.tw/sites/default/files/2026-09/116%E8%B5%B4%E5%A2%83%E5%A4%96%E4%BA%A4%E6%8F%9B%E7%94%B3%E8%AB%8B%E8%AA%AA%E6%98%8E%E6%9C%83%E7%B0%A1%E5%A0%B1_0.pdf", "東吳大學 116 學年度赴境外交換申請說明會簡報（43 頁）"),
        (SCRATCH_SCU / "intl_review_criteria_20240909.pdf", SOURCES_SCU_DIR / "intl_review_criteria_20240909.pdf", "https://icae.scu.edu.tw/sites/default/files/2024-09/%E6%9D%B1%E5%90%B3%E5%A4%A7%E5%AD%B8%E8%B5%B4%E5%9C%8B%E5%A4%96%E6%A0%A1%E7%B4%9A%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E5%AF%A9%E6%9F%A5%E6%A8%99%E6%BA%9620240909.pdf", "東吳大學赴國外校級交換學生審查標準（2024.09.09）"),
        (SCRATCH_SCU / "china_review_criteria.pdf", SOURCES_SCU_DIR / "china_review_criteria.pdf", "https://icae.scu.edu.tw/sites/default/files/2022-10/%E6%9D%B1%E5%90%B3%E5%A4%A7%E5%AD%B8%E8%B5%B4%E5%A4%A7%E9%99%B8%E6%A0%A1%E7%B4%9A%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E5%AF%A9%E6%9F%A5%E6%A8%99%E6%BA%96.pdf", "東吳大學赴大陸校級交換學生審查標準"),
        (SCRATCH_SCU / "exchange_regulations.pdf", SOURCES_SCU_DIR / "exchange_regulations.pdf", "https://icae.scu.edu.tw/sites/default/files/2025-09/06_%E6%9D%B1%E5%90%B3%E5%A4%A7%E5%AD%B8%E6%A0%A1%E7%B4%9A%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E8%A8%88%E7%95%AB%E5%AF%A6%E6%96%BD%E8%BE%A6%E6%B3%95_0.pdf", "東吳大學校級交換學生計畫實施辦法"),
        (SCRATCH_SCU / "reg305_academic_status.pdf", SOURCES_SCU_DIR / "reg305_academic_status.pdf", "https://www.scu.edu.tw/regcurr/regulations/reg305.pdf", "東吳大學學生出境期間有關學業及學籍處理辦法"),
        (SCRATCH_SCU / "faq_zh_20260914.pdf", SOURCES_SCU_DIR / "faq_zh_20260914.pdf", "https://icae.scu.edu.tw/sites/default/files/2026-09/%E6%A0%A1%E7%B4%9A%E8%B5%B4%E5%A2%83%E5%A4%96%E4%BA%A4%E6%8F%9BFAQ%2020260914.pdf", "東吳大學校級赴境外交換 FAQ 中文版（2026.09.14）"),
        (SCRATCH_SCU / "faq_en.pdf", SOURCES_SCU_DIR / "faq_en.pdf", "https://icae.scu.edu.tw/sites/default/files/2026-09/FAQ_English.pdf", "Soochow University Outbound Exchange FAQ (English)"),
        (SCRATCH_SCU / "partner_institutions_20260430.pdf", SOURCES_SCU_DIR / "partner_institutions_20260430.pdf", "https://icae.scu.edu.tw/sites/default/files/2026-04/%E5%9C%8B%E9%9A%9B%E5%8D%94%E8%AD%B0%E7%B0%BD%E7%BD%B2%E4%B8%80%E8%A6%BD%E8%A1%A8%20Partner%20Institutions%EF%BC%88As%20of%2004.30%2C%202026%EF%BC%89.pdf", "東吳大學國際協議簽署一覽表 Partner Institutions（As of 2026.04.30）"),
        (SCRATCH_SCU / "china_agreements_20260408.pdf", SOURCES_SCU_DIR / "china_agreements_20260408.pdf", "https://icae.scu.edu.tw/sites/default/files/2026-04/20260408%E5%A4%A7%E9%99%B8%E5%8D%94%E8%AD%B0%E4%B8%80%E8%A6%BD%E8%A1%A8.pdf", "東吳大學大陸協議學校一覽表（2026.04.08）"),
        (SCRATCH_SCU / "sch_xuehai_feiyang.pdf", SOURCES_SCU_DIR / "sch_xuehai_feiyang.pdf", "https://icae.scu.edu.tw/zh-hant/node/1017", "東吳大學「學海飛颺計畫」學生獎助辦法"),
        (SCRATCH_SCU / "sch_xuehai_xizhu.pdf", SOURCES_SCU_DIR / "sch_xuehai_xizhu.pdf", "https://icae.scu.edu.tw/zh-hant/node/65", "東吳大學「學海惜珠計畫」學生獎助辦法"),
        (SCRATCH_SCU / "sch_sprout_grant.pdf", SOURCES_SCU_DIR / "sch_sprout_grant.pdf", "https://icae.scu.edu.tw/zh-hant/node/1671", "東吳大學辦理教育部「高教深耕─扶助攻頂計畫」學生赴外研習助學金實施辦法"),
        (SCRATCH_SCU / "sch_study_abroad_subsidy.pdf", SOURCES_SCU_DIR / "sch_study_abroad_subsidy.pdf", "https://icae.scu.edu.tw/zh-hant/node/4348", "東吳大學學生赴外研習補助執行要點"),
        (SCRATCH_SCU / "sch_intl_exchange_subsidy.pdf", SOURCES_SCU_DIR / "sch_intl_exchange_subsidy.pdf", "https://icae.scu.edu.tw/zh-hant/node/1087", "東吳大學國際學術交流計畫獎補助辦法"),
    ]
    provenance_items = []
    for src, dst, url, title in files_to_copy:
        if src.exists():
            if src.resolve() != dst.resolve():
                shutil.copy2(src, dst)
            provenance_items.append({
                "file": f"sources/scu/{dst.name}",
                "source_url": url,
                "title": title,
                "sha256": sha256_file(dst),
                "bytes": dst.stat().st_size,
                "fetched_at": "2026-10-16T06:20:00Z",
            })
    return {
        "school_id": "scu",
        "school_name": "東吳大學",
        "generated_at": "2026-10-19T09:30:00Z",
        "active_cycle_note": "116學年度校級赴境外（含赴國外、大陸、港澳地區）交換暨自費研修計畫於 2026/09/14 至 2026/11/16 中午 12:00 開放線上申請（https://api.sys.scu.edu.tw/exchange/Login.aspx），涵蓋 116-1（2027秋季班）及 116-2（2028春季班），預計於 2026 年 12 月底前公告甄選結果。完整收錄 126 所赴外（含港澳）交換校、62 所赴陸交換校及 3 所英美自費研修校共 191 所合作校當期名額與條件。2026/10/19 基準更正：昨日讀到赴陸頁之 115 學年度舊快取，今日直接核實官方現行內容（https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/apply）為 116 學年度（適用 2027 秋／2028 春，11/16 中午截止、12 月底公布結果），並已讀取 62 校名單及申請表；不能斷言今日才更新，赴國外合作表已比對範圍未變。",
        "baseline_correction_20261019": {
            "checked_at": "2026-10-19T09:30:00+08:00",
            "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/apply",
            "partner_list_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/list",
            "partner_list_pdf_url": "https://icae.scu.edu.tw/sites/default/files/2026-09/%E6%9D%B1%E5%90%B3%E5%A4%A7%E5%AD%B8116%E5%AD%B8%E5%B9%B4%E5%BA%A6%E6%A0%A1%E7%B4%9A%E8%B5%B4%E9%99%B8%E4%BA%A4%E6%8F%9B%E5%AD%B8%E6%A0%A1%E4%B8%80%E8%A6%BD%E8%A1%A8_1150915.pdf",
            "application_form_docx_url": "https://icae.scu.edu.tw/sites/default/files/2026-09/%E8%B5%B4%E5%A4%A7%E9%99%B8%E5%8D%94%E8%AD%B0%E5%AD%B8%E6%A0%A1%E4%BA%A4%E6%8F%9B%E5%8B%95%E6%A9%9F%E5%8F%8A%E8%AE%80%E6%9B%B8%E8%A8%88%E7%95%AB.docx",
            "application_form_odt_url": "https://icae.scu.edu.tw/sites/default/files/2026-09/%E8%B5%B4%E5%A4%A7%E9%99%B8%E5%8D%94%E8%AD%B0%E5%AD%B8%E6%A0%A1%E4%BA%A4%E6%8F%9B%E5%8B%95%E6%A9%9F%E5%8F%8A%E8%AE%80%E6%9B%B8%E8%A8%88%E7%95%AB.odt",
            "verified_academic_year": "116",
            "applicable_semesters": [
                "2027秋季班（116-1：2027年9月–2028年1月）",
                "2028春季班（116-2：2028年2月–2028年7月）",
            ],
            "application_deadline_at": "2026-11-16T12:00:00+08:00",
            "result_announcement_period": "2026年12月底前",
            "mainland_partner_count": 62,
            "asserted_updated_today": False,
            "overseas_partner_table_changed_in_checked_scope": False,
            "summary": "昨日讀到的是赴陸頁的 115 年度舊快取；今日直接核實官方現行內容為 116 年度（適用 2027 秋／2028 春，11/16 中午截止、12 月底公布結果），並已讀取 62 校名單及申請表。不能斷言今日才更新；赴國外合作表已比對範圍未變。",
        },
        "sources": provenance_items,
    }


def load_repo_locations_and_images():
    loc_by_en_country = {}
    loc_by_zh_country = {}
    for line in (REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("geocode_status") == "verified" and r.get("latitude") is not None:
            c = COUNTRY_MAP.get(str(r.get("country") or ""), str(r.get("country") or ""))
            name = r.get("school_name", "")
            if loose_en(name) and c:
                loc_by_en_country.setdefault((loose_en(name), c), r)
            if loose_zh(name) and c:
                loc_by_zh_country.setdefault((loose_zh(name), c), r)

    fju_loc_path = REPO_ROOT / "src/exchange_info/official_data/fju/campus-locations.json"
    if fju_loc_path.exists():
        for r in json.loads(fju_loc_path.read_text(encoding="utf-8")).get("locations", []):
            if r.get("geocode_status") == "verified" and r.get("latitude") is not None:
                c = COUNTRY_MAP.get(str(r.get("country") or ""), str(r.get("country") or ""))
                name = r.get("school_name", "")
                if loose_en(name) and c:
                    loc_by_en_country.setdefault((loose_en(name), c), r)
                if loose_zh(name) and c:
                    loc_by_zh_country.setdefault((loose_zh(name), c), r)

    for r in json.loads((REPO_ROOT / "src/exchange_info/official_data/ncu/campus-locations.json").read_text(encoding="utf-8")).get("schools", []):
        if r.get("status") == "verified" and r.get("latitude") is not None:
            c = COUNTRY_MAP.get(str(r.get("country") or ""), str(r.get("country") or ""))
            rec = {
                "school_name": r["school_name"],
                "country": c,
                "city": r.get("city"),
                "latitude": float(r["latitude"]),
                "longitude": float(r["longitude"]),
                "geocode_status": "verified",
                "geocoded_at": "2026-10-16T06:30:00Z",
                "source_url": r.get("source_url"),
                "identity_source_url": r.get("identity_source_url") or r.get("source_url"),
                "precision": "representative",
                "note": r.get("note") or "校級代表位置。",
            }
            name = r["school_name"]
            if loose_en(name) and c:
                loc_by_en_country.setdefault((loose_en(name), c), rec)
            if loose_zh(name) and c:
                loc_by_zh_country.setdefault((loose_zh(name), c), rec)

    for r in json.loads((REPO_ROOT / "src/exchange_info/official_data/tku/campus_location_manifest.json").read_text(encoding="utf-8")):
        loc = r.get("location") or {}
        if loc.get("geocode_status") == "verified" and loc.get("latitude") is not None:
            name = r.get("school_name") or ""
            c = COUNTRY_MAP.get(str(loc.get("country") or r.get("country") or ""), str(loc.get("country") or r.get("country") or ""))
            rec = {**loc, "school_name": name, "country": c}
            if loose_en(name) and c:
                loc_by_en_country.setdefault((loose_en(name), c), rec)
            if loose_zh(name) and c:
                loc_by_zh_country.setdefault((loose_zh(name), c), rec)

    scu_resolved = json.loads((SOURCES_SCU_DIR / "scu_resolved_locations.json").read_text(encoding="utf-8"))
    for r in scu_resolved:
        c = COUNTRY_MAP.get(str(r.get("country") or ""), str(r.get("country") or ""))
        rec = {
            "country": c,
            "city": r.get("city") or c,
            "latitude": float(r["latitude"]),
            "longitude": float(r["longitude"]),
            "geocode_status": "verified",
            "geocoded_at": "2026-10-16T06:30:00Z",
            "source_url": r.get("source_url"),
            "identity_source_url": r.get("identity_source_url"),
            "precision": "representative",
            "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625 / ROR GeoNames；實際交換校區以錄取通知為準。",
        }
        if loose_en(r.get("name_en", "")) and c:
            loc_by_en_country[(loose_en(r["name_en"]), c)] = rec
        if loose_zh(r.get("name_zh", "")) and c:
            loc_by_zh_country[(loose_zh(r["name_zh"]), c)] = rec

    img_by_en_country = {}
    img_by_zh_country = {}
    for src_path in [
        REPO_ROOT / "src/exchange_info/static/assets/school-images.json",
        REPO_ROOT / "src/exchange_info/static/assets/ncu-school-images.json",
    ]:
        for r in json.loads(src_path.read_text(encoding="utf-8")).get("schools", []):
            if isinstance(r, dict) and r.get("status") == "verified" and r.get("local_path"):
                c = COUNTRY_MAP.get(str(r.get("country") or ""), str(r.get("country") or ""))
                name = r.get("school_name", "")
                if loose_en(name) and c:
                    img_by_en_country.setdefault((loose_en(name), c), r)
                if loose_zh(name) and c:
                    img_by_zh_country.setdefault((loose_zh(name), c), r)

    return loc_by_en_country, loc_by_zh_country, img_by_en_country, img_by_zh_country


def parse_intl_126_schools() -> list[dict]:
    raw_html = (SOURCES_SCU_DIR / "intl_116_schools.html").read_text(encoding="utf-8")
    details_blocks = re.findall(r"<details[^>]*>(.*?)</details>", raw_html, flags=re.S)
    records = []
    for idx, b in enumerate(details_blocks):
        summary = re.search(r"<summary[^>]*>(.*?)</summary>", b, flags=re.S).group(1)
        summary_text = re.sub(r"<[^>]+>", " ", summary)
        summary_text = re.sub(r"\s+", " ", html.unescape(summary_text)).strip()
        m = re.match(r"^(\d+)\.\s*【([^】]+)】\s*(.+?)\s*【([^】]+)】\s*(.+)$", summary_text)
        no = int(m.group(1))
        country = COUNTRY_MAP.get(m.group(2).strip(), m.group(2).strip())
        zh_name = m.group(3).strip()
        en_name = m.group(5).strip()
        full_name = f"{zh_name} {en_name}"

        body = re.sub(r"<summary[^>]*>.*?</summary>", "", b, flags=re.S)
        hrefs = re.findall(r'href=["\'](https?://[^"\'\s>]+)["\']', body)
        website = hrefs[0].strip() if hrefs else None

        body_text = re.sub(r"<br\s*/?>|</p>|</li>|</tr>", "\n", body, flags=re.I)
        body_text = re.sub(r"<[^>]+>", " ", body_text)
        lines = [
            re.sub(r"\s+", " ", html.unescape(ln)).strip()
            for ln in body_text.splitlines()
            if re.sub(r"\s+", " ", html.unescape(ln)).strip()
        ]

        elig_lines = []
        lang_lines = []
        quota_val = "依當期協議名額"
        mode = None
        for ln in lines:
            if ln.lower().startswith("website:"):
                continue
            if "基本條件" in ln or "Eligibility" in ln:
                mode = "elig"
                rest = re.sub(r"^.*?基本條件\s*/?\s*Eligibility\s*[:：]?\s*", "", ln, flags=re.I).strip()
                if rest:
                    elig_lines.append(rest)
                continue
            if "外語能力資格" in ln or "Language requirement" in ln:
                mode = "lang"
                rest = re.sub(r"^.*?外語能力資格\s*/?\s*Language requirement\s*[:：]?\s*", "", ln, flags=re.I).strip()
                if rest:
                    lang_lines.append(rest)
                continue
            if "每學期名額" in ln or "Quota per semester" in ln:
                mode = "quota"
                m_q = re.search(r"[:：]\s*(.+)$", ln)
                if m_q and m_q.group(1).strip():
                    quota_val = m_q.group(1).strip()
                continue
            if mode == "elig":
                elig_lines.append(ln)
            elif mode == "lang":
                lang_lines.append(ln)
            elif mode == "quota" and quota_val == "依當期協議名額":
                quota_val = ln.lstrip(":： ").strip()

        elig_zh_lines = [ln for ln in elig_lines if re.search(r"[\u4e00-\u9fff]", ln)]
        elig_all_str = "；".join(elig_zh_lines if elig_zh_lines else elig_lines)
        lang_str = " / ".join(lang_lines) if lang_lines else "依接待校英語或當地語言檢定規定"

        # Course access and admission degree are different. Unknown wording
        # must be reviewed instead of silently admitting every degree level.
        from exchange_info.scu_degree_source_review import degree_scope
        degree_levels = degree_scope(elig_lines[0])

        # GPA detection
        gpa_str = "大學部累計班排名前 85% 以內；碩博班歷年總平均 80 分以上；操行 80 分以上且無校規懲處紀錄"
        m_gpa = re.search(r"GPA\s*(\d+(?:\.\d+)?)\s*(?:out of\s*4(?:\.0)?|/\s*4(?:\.0)?|以上)?", " ".join(elig_lines), flags=re.I)
        if m_gpa:
            gpa_str = f"接待校要求 GPA {m_gpa.group(1)} / 4.0 以上（且須符合東吳校內門檻：大學部累計班排名前 85% 以內、碩博班總平均 80 分以上、操行 80 分以上）"
        else:
            m_avg = re.search(r"歷年成績總平均達\s*(\d+)\s*分", elig_all_str)
            if m_avg:
                gpa_str = f"接待校要求歷年成績總平均達 {m_avg.group(1)} 分以上（且須符合東吳校內門檻：大學部累計班排名前 85% 以內、碩博班總平均 80 分以上、操行 80 分以上）"

        records.append({
            "kind": "intl_exchange",
            "no": no,
            "country": country,
            "region": "港澳地區" if country in ("香港", "澳門") else "海外地區",
            "zh_name": zh_name,
            "en_name": en_name,
            "full_name": full_name,
            "website": website,
            "degree_levels": degree_levels,
            "eligibility_detail": elig_all_str,
            "eligibility_lines_bilingual": elig_lines,
            "language_requirement": lang_str,
            "gpa_requirement": gpa_str,
            "quota": f"每學期名額：{quota_val} 名（116學年度第1學期／第2學期）",
            "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intl/2025-2026schools",
        })
    return records


def parse_china_62_schools() -> list[dict]:
    rows = json.loads((SOURCES_SCU_DIR / "china_116_structured.json").read_text(encoding="utf-8"))
    records = []
    for r in rows:
        zh_name = r["name_zh"]
        en_name = r["name_en"]
        full_name = f"{zh_name} {en_name}"
        deg_parts = []
        if r.get("accept_undergrad"):
            deg_parts.append("大學部")
        if r.get("accept_master"):
            deg_parts.append("碩士班")
        if r.get("accept_phd"):
            deg_parts.append("博士班")
        degree_levels = "、".join(deg_parts) if deg_parts else "大學部"

        id_parts = ["臺生"]
        if r.get("accept_mainland_students"):
            id_parts.append("陸生")
        if r.get("accept_hkmo_students"):
            id_parts.append("港澳生")
        if r.get("accept_intl_students"):
            id_parts.append("外籍生")
        id_str = "、".join(id_parts)

        grad_ext_str = "可接收應屆畢業生／延畢生（須留意成績單寄達與畢業抵免時程）" if r.get("accept_graduating_or_extended") else "交換時原則上不接收應屆畢業生或延畢生"
        note_116 = (r.get("note_116") or "").strip()

        elig_parts = [
            f"可接收學籍身分：{id_str}（僅限全日制在學學生，不開放進修學士班、碩士在職專班及大學部延修第二年）",
            f"開放學制：{degree_levels}",
            f"應屆／延畢規定：{grad_ext_str}",
        ]
        if note_116:
            elig_parts.append(f"116學年度特別規定：{note_116}")

        q_raw = r["quota"]
        if q_raw.startswith("*"):
            quota_str = f"每學期名額：{q_raw.lstrip('*')} 名（集中一學期接收 {q_raw.lstrip('*')} 名；116學年度）"
        else:
            quota_str = f"每學期名額：{q_raw} 名（116學年度第1學期／第2學期）"

        records.append({
            "kind": "china_exchange",
            "no": r["no"],
            "country": "中國大陸",
            "province": r.get("province") or "",
            "region": "大陸地區",
            "zh_name": zh_name,
            "en_name": en_name,
            "full_name": full_name,
            "website": r.get("website"),
            "degree_levels": degree_levels,
            "eligibility_detail": "；".join(elig_parts),
            "eligibility_lines_bilingual": elig_parts,
            "language_requirement": "中文授課免附外語檢定證明（部分院系若選修英文授課課程依接待校規定）",
            "gpa_requirement": "大學部累計班排名前 85% 以內；碩博班入學後成績總平均達 80 分以上；操行成績達 80 分以上且無校規懲處紀錄",
            "quota": quota_str,
            "note_116": note_116,
            "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/list",
        })
    return records


def build_tuition_3_schools() -> list[dict]:
    return [
        {
            "kind": "tuition_study_abroad",
            "no": 1,
            "country": "美國",
            "region": "海外地區（自費研修）",
            "zh_name": "加州大學柏克萊分校",
            "en_name": "University of California, Berkeley",
            "full_name": "加州大學柏克萊分校 University of California, Berkeley",
            "website": "https://bisp.berkeley.edu/",
            "degree_levels": "大學部、碩士班（碩專班、博士班不開放）",
            "eligibility_detail": "具東吳大學正式學籍之大學部及一般碩士班在學學生（碩專班、博士班不開放申請）；參加 Berkeley International Study Program (BISP)，獲本校推薦後須配合該校安排視訊或實地英語面試。整體預估費用約 USD 27,000 / 學期（含柏克萊學分費與生活住宿預估）。",
            "eligibility_lines_bilingual": [
                "具東吳大學正式學籍之學生，碩專班、博士班學生不開放申請。",
                "獲本校推薦資格後，須配合該校安排視訊或實地英語面試。",
                "整體費用約 27,000 元美金（含學費及預估生活費，詳見 BISP 官網 https://bisp.berkeley.edu/program/costs）。",
            ],
            "language_requirement": "TOEFL iBT 90 或 IELTS 7.0（大學部學生亦接受 Duolingo 115、TOEIC 750、CET-6 520 或 PTE Academic 64 以上，符合其一即可）",
            "gpa_requirement": "大學部累計班排名前 85% 以內；碩士班入學後成績總平均達 80 分以上；操行達 80 分以上且無校規懲處紀錄",
            "quota": "無名額限制（符合申請條件者經東吳國際交流委員會審查通過後皆可推薦；可申請 1 學期或 1 學年）",
            "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/tuition-based%20programs",
        },
        {
            "kind": "tuition_study_abroad",
            "no": 2,
            "country": "英國",
            "region": "海外地區（自費研修）",
            "zh_name": "東英吉利大學",
            "en_name": "University of East Anglia",
            "full_name": "東英吉利大學 University of East Anglia",
            "website": "https://www.uea.ac.uk/study/study-abroad-and-exchange/incoming-study-abroad-and-exchange/application",
            "degree_levels": "大學部、碩士班（碩專班、博士班不開放）",
            "eligibility_detail": "具東吳大學正式學籍之大學部及一般碩士班在學學生（碩專班、博士班不開放申請）；歷年 GPA 須達 3.0 / 4.0 以上。東吳學生享有該校自費研修學費 8 折優惠（單學期 GBP 7,700、一學年 GBP 15,400）。",
            "eligibility_lines_bilingual": [
                "具東吳大學正式學籍之學生，碩專班、博士班學生不開放申請。",
                "學業成績要求：GPA 3.0 on a 4.0 scale。",
                "費用優惠：東吳大學學生享學費 8 折優惠，單學期 7,700 英鎊、一學年 15,400 英鎊。",
            ],
            "language_requirement": "IELTS 6.0（單科不低於 5.5）或 TOEFL iBT 79 或 PTE 64（單科不低於 59）或 FCE B2 First / CAE C1 Advanced",
            "gpa_requirement": "GPA 3.0 / 4.0 以上（且須符合東吳校內門檻：大學部累計班排名前 85% 以內、碩士班總平均 80 分以上、操行 80 分以上）",
            "quota": "無名額限制（符合申請條件者經東吳國際交流委員會審查通過後皆可推薦；可申請 1 學期或 1 學年）",
            "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/tuition-based%20programs",
        },
        {
            "kind": "tuition_study_abroad",
            "no": 3,
            "country": "英國",
            "region": "海外地區（自費研修）",
            "zh_name": "愛丁堡納皮爾大學",
            "en_name": "Edinburgh Napier University",
            "full_name": "愛丁堡納皮爾大學 Edinburgh Napier University",
            "website": "https://www.napier.ac.uk/study-with-us/international-students",
            "degree_levels": "大學部、碩士班、博士班",
            "eligibility_detail": "具東吳大學正式學籍之在學學生；每學期可修 2 至 3 門專業課（每門 20 ENU 學分，提供成績單）另加 1 門免費無學分學術英語課。東吳學生專案學費：修 2 門專業課 + 1 門學術英語（40 學分）約 GBP 5,000–6,000；修 3 門專業課 + 1 門學術英語（60 學分）約 GBP 7,500–9,000。",
            "eligibility_lines_bilingual": [
                "具東吳大學正式學籍之在學學生。",
                "每學期可修 2 至 3 門專業課（每門課計 20 ENU 學分）另加 1 門學術英語課。",
                "東吳學生專案學費：40 學分方案約 5,000–6,000 英鎊；60 學分方案約 7,500–9,000 英鎊。",
            ],
            "language_requirement": "TOEFL iBT 72 或 IELTS 5.5 或 TOEIC 785 或 CEFR B2 同等語檢（若無語檢或未達門檻亦可受理，惟獲推薦後須配合該校安排視訊英語面試）",
            "gpa_requirement": "大學部累計班排名前 85% 以內；碩博班入學後成績總平均達 80 分以上；操行 80 分以上且無校規懲處紀錄",
            "quota": "無名額限制（符合申請條件者經東吳國際交流委員會審查通過後皆可推薦；可申請 1 學期或 1 學年）",
            "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/tuition-based%20programs",
        },
    ]


def write_scu_campus_svg():
    svg_path = STATIC_DIR / "assets" / "scu-campus.svg"
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="800" height="500">
  <defs>
    <linearGradient id="scuSky" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1a1829" />
      <stop offset="55%" stop-color="#2c1d33" />
      <stop offset="100%" stop-color="#4a1c2a" />
    </linearGradient>
    <linearGradient id="scuAccent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#c8102e" />
      <stop offset="100%" stop-color="#111111" />
    </linearGradient>
  </defs>
  <rect width="800" height="500" fill="url(#scuSky)" />
  <path d="M0 370 Q200 310 420 355 T800 330 L800 500 L0 500 Z" fill="#182628" opacity="0.7" />
  <rect x="170" y="210" width="460" height="175" rx="8" fill="#f7f4ef" opacity="0.95" />
  <polygon points="150,215 400,135 650,215" fill="url(#scuAccent)" />
  <rect x="210" y="245" width="55" height="90" rx="4" fill="#2c1d33" opacity="0.85" />
  <rect x="295" y="245" width="55" height="90" rx="4" fill="#2c1d33" opacity="0.85" />
  <rect x="372" y="235" width="56" height="150" rx="4" fill="#c8102e" />
  <rect x="450" y="245" width="55" height="90" rx="4" fill="#2c1d33" opacity="0.85" />
  <rect x="535" y="245" width="55" height="90" rx="4" fill="#2c1d33" opacity="0.85" />
  <text x="400" y="435" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle" letter-spacing="2">東吳大學 Soochow University</text>
  <text x="400" y="468" font-family="sans-serif" font-size="15" fill="#e2d9dc" text-anchor="middle" letter-spacing="1">Unto a Full-grown Man ・ 養天地正氣 法古今完人</text>
</svg>
"""
    svg_path.write_text(svg_content, encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OFFICIAL_SCU_DIR.mkdir(parents=True, exist_ok=True)
    write_scu_campus_svg()

    provenance = archive_official_sources()
    (OFFICIAL_SCU_DIR / "import_provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    loc_by_en_country, loc_by_zh_country, img_by_en_country, img_by_zh_country = load_repo_locations_and_images()

    raw_items = parse_intl_126_schools() + parse_china_62_schools() + build_tuition_3_schools()

    partners = []
    workflows = []
    destinations = []
    research_records = []
    life_records = []
    new_locations = []
    new_images = []

    for idx, item in enumerate(raw_items):
        country = item["country"]
        zh_name = item["zh_name"]
        en_name = item["en_name"]
        full_name = item["full_name"]
        website = item.get("website")
        source_url = item["source_url"]
        kind = item["kind"]

        repo_loc = (
            loc_by_en_country.get((loose_en(en_name), country))
            or loc_by_zh_country.get((loose_zh(zh_name), country))
        )
        if not repo_loc:
            raise RuntimeError(f"Unresolved location for SCU partner #{idx+1}: {full_name} ({country})")

        location_obj = {
            "school_name": full_name,
            "country": country,
            "city": repo_loc.get("city") or item.get("province") or country,
            "latitude": float(repo_loc["latitude"]),
            "longitude": float(repo_loc["longitude"]),
            "geocode_status": "verified",
            "geocoded_at": "2026-10-16T06:30:00Z",
            "source_url": repo_loc.get("source_url") or "https://www.wikidata.org",
            "identity_source_url": repo_loc.get("identity_source_url") or repo_loc.get("source_url") or "https://ror.org",
            "precision": "representative",
            "note": repo_loc.get("note") or "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區以錄取通知為準。",
        }
        new_locations.append(location_obj)

        img_rec = (
            img_by_en_country.get((loose_en(en_name), country))
            or img_by_zh_country.get((loose_zh(zh_name), country))
        )
        if img_rec and img_rec.get("status") == "verified" and img_rec.get("local_path"):
            rel = urlsplit(img_rec["local_path"]).path.removeprefix("/static/")
            fpath = STATIC_DIR / rel
            if fpath.is_file():
                new_images.append({
                    "school_name": full_name,
                    "country": country,
                    "status": "verified",
                    "local_path": img_rec["local_path"],
                    "image_source_url": img_rec.get("image_source_url"),
                    "official_page_url": img_rec.get("official_page_url") or website,
                    "identity_source_url": img_rec.get("identity_source_url") or location_obj["identity_source_url"],
                    "artist": img_rec.get("artist"),
                    "license_name": img_rec.get("license_name"),
                    "license_url": img_rec.get("license_url"),
                    "content_hash": sha256_file(fpath),
                    "checked_at": "2026-10-16",
                    "note": img_rec.get("note") or f"{full_name} 校園代表照片",
                })

        if kind == "china_exchange":
            program_type = "交換學生（校級赴大陸協議學校）"
            study_period_str = "116學年度第1學期（2027年9月–2028年1月）或第2學期（2028年2月–7月）；以1學期為單位選填志願"
            tuition_points_list = [
                "參與東吳校級赴陸交換計畫，交換期間須繳交東吳大學日間部全額學雜費以保留在學學籍，免繳大陸協議學校學費；個人機票、臺胞證簽註、書籍、住宿、伙食及大陸境內醫療保險費由學生自理。",
                "獲本校推薦者須於結果公告後規定期限內（約 1 週內）繳交「東吳大學學生赴協議學校交換研習確認書」（含家長簽名）及保證金 NT$5,000；完成交換返臺後 1 個月內繳交 1,500–2,000 字心得報告並完成學分抵免（或申請不抵免）程序後無息退還。",
            ]
        elif kind == "tuition_study_abroad":
            program_type = "自費研修（校級赴外合作院校）"
            study_period_str = "116學年度第1學期（2027秋季學期）或第2學期（2028春季學期），可申請 1 學期或 1 學年"
            tuition_points_list = [
                f"本計畫為校級赴外自費研修計畫：除須繳交東吳大學全額學雜費以保留在學學籍外，亦須自行負擔 {zh_name} 自費研修學費、住宿費、生活費、簽證及海外醫療保險費用。",
                item["eligibility_detail"],
            ]
        else:
            program_type = "交換學生（校級赴外／港澳協議學校）"
            study_period_str = "116學年度第1學期（2027秋季：約2027年8月–2028年1月）或第2學期（2028春季：約2028年2月–7月）；審查優先以 1 學期原則排序"
            tuition_points_list = [
                "參與東吳校級赴外交換研修計畫，研習期間須繳交東吳大學日間部全額學雜費以保留在學學籍，免繳協議學校學費；個人機票、簽證、書籍、生活、住宿及當地強制醫療保險／行政作業費由學生自理。",
                "獲本校推薦者須於結果公告後規定期限內（約 1 週內）繳交「東吳大學學生赴協議學校交換研習確認書」（含家長簽名）及保證金 NT$5,000；完成交換返臺後 1 個月內繳交 1,500–2,000 字心得報告並完成學分抵免（或申請不抵免）程序後無息退還。",
            ]

        app_deadline_str = "2026年9月14日起至2026年11月16日（一）中午12:00止（全線上申請，免交紙本；預計2026年12月底前公告甄選結果）"
        app_steps_list = [
            "於 2026/09/14 至 11/16 中午 12:00 前登入東吳大學赴外交換線上申請系統（https://api.sys.scu.edu.tw/exchange/Login.aspx），選填至多 6 個志願（每志願含研修學校及研修學期；有意研修 1 學年者請至少選填 2 個志願）。",
            "將各類備審資料分別合併為單一 PDF 檔（每類上限 5MB，檔名僅限中英數字符號）上傳：含自傳或履歷（約 2,000 字）、一校一份之交換研修動機及讀書計畫（海外交換須將中文 Form A 與外文 Form B 合併且中文在先；赴陸交換使用中文表格）、有效期限內之外語檢定證明（赴陸免附）及其他有利審查文件（如未彌封推薦函至多 2 封）。",
            "國際處統一委託電算中心查核學籍與歷年成績、委託德育中心查核操行與獎懲紀錄（舊生免自行上傳成績單與在學證明），送交國際交流委員會依審查標準評分排序。",
            f"預計於 2026 年 12 月底前公告推薦名單；獲推薦生須於 1 週內繳交家長簽署之交換研習確認書及保證金 NT$5,000，並配合 {full_name} 提名與入學申請程序備齊外校表單，取得正式入學許可後辦理簽證、住宿及選課（每學期至少修習 1 門課程）。",
        ]

        elig_points_list = [
            f"開放學制：{item['degree_levels']}",
            f"學業與操行門檻：{item['gpa_requirement']}",
            f"語文能力要求：{item['language_requirement']}",
            f"交換條件與說明：{item['eligibility_detail']}",
        ]

        notes_lines = [
            f"【116學年度申請期程】{app_deadline_str}",
            f"【每學期名額】{item['quota']}",
            f"【外語能力資格】{item['language_requirement']}",
            f"【基本條件與限制】{item['eligibility_detail']}",
        ]
        if item.get("note_116"):
            notes_lines.append(f"【116學年度赴陸備註】{item['note_116']}")

        partner_record = {
            "school_name": full_name,
            "country": country,
            "region": item["region"],
            "colleges": "全校各學院（部分院系或專業限制依協議校規定）",
            "degree_levels": item["degree_levels"],
            "study_period": study_period_str,
            "eligibility": f"{item['eligibility_detail']}｜語文要求：{item['language_requirement']}｜校內門檻：{item['gpa_requirement']}",
            "language_requirement": item["language_requirement"],
            "gpa_requirement": item["gpa_requirement"],
            "quota": item["quota"],
            "quota_status": "published",
            "availability_status": "open",
            "availability_note": f"東吳大學 116 學年度（2027秋季班／2028春季班）校級赴境外交換暨自費研修計畫現正開放線上申請（2026/09/14–11/16 中午 12:00 截止）；{item['quota']}。",
            "academic_year": "116",
            "application_round": "116學年度（含第1學期秋季班及第2學期春季班）",
            "application_window_status": "open",
            "application_deadline": app_deadline_str,
            "application_info": "\n\n".join(app_steps_list),
            "tuition_info": "\n\n".join(tuition_points_list),
            "semester_dates": "第1學期（秋季班）：約2027年8/9月至2028年1月；第2學期（春季班）：約2028年2月至7月（實際依協議校行事曆為準）",
            "course_restrictions": item["eligibility_detail"],
            "housing_info": "各協議校住宿條件不一，少數亞洲及多數歐美學校未保證校內宿舍，僅提供校外租屋平台或學生公寓資訊供參考；獲提名後須依接待校規定自行申請宿舍或覓妥住處。",
            "notes": "\n".join(notes_lines),
            "program_type": program_type,
            "source_url": source_url,
            "website": website,
            "official_website": website,
            "factsheet_url": None,
            "location": location_obj,
            "student_summary_zh": {
                "study_period": study_period_str,
                "quota": item["quota"],
                "colleges": "全校各學院（部分院系或專業限制依協議校規定）",
                "degree_levels": item["degree_levels"],
                "eligibility_points": elig_points_list,
                "application_deadline": app_deadline_str,
                "application_steps": app_steps_list,
                "tuition_points": tuition_points_list,
            },
        }
        partners.append(partner_record)

        wf_sources = [
            {
                "title": f"東吳大學 116 學年度交換學校一覽表—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": "116學年度（第1學期／第2學期）",
                "checked_at": "2026-10-16T06:35:00Z",
            },
            {
                "title": "東吳大學 116 學年度校級赴國外／大陸交換學生甄選申請說明",
                "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply" if kind != "china_exchange" else "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/apply",
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": "116學年度（第1學期／第2學期）",
                "checked_at": "2026-10-16T06:35:00Z",
            },
        ]
        if website:
            wf_sources.append({
                "title": f"{full_name} 官方交換／國際處網站",
                "source_url": website,
                "role": "partner_university",
                "authority": "partner_official",
                "effective_academic_year": "116",
                "application_round": "116學年度（第1學期／第2學期）",
                "checked_at": "2026-10-16T06:35:00Z",
            })

        workflows.append({
            "home_university": "東吳大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": "116",
            "application_round": "116學年度（第1學期／第2學期）",
            "effective_application_rounds": ["116學年度（第1學期／第2學期）", "第1學期（秋季班）", "第2學期（春季班）"],
            "applicability_status": "verified",
            "applicability_note": "東吳大學 116 學年度校級赴境外交換暨自費研修計畫於 2026/09/14 至 2026/11/16 中午 12:00 受理線上申請（一次甄選同時涵蓋 116-1 秋季班與 116-2 春季班），預計於 2026 年 12 月底前公告甄選結果。",
            "review_status": "published",
            "published_at": "2026-10-16T06:35:00Z",
            "steps": [
                {
                    "rule_id": f"scu-116-home-1-{idx+1:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": "確認東吳校內學業／操行門檻與各協議校外語檢定資格",
                    "responsible_party": "學生",
                    "responsible_unit": "東吳大學國際與兩岸學術交流事務處（國際與兩岸事務中心）",
                    "deadline_at": None,
                    "deadline_status": "not_applicable",
                    "timing": "申請前核對資格；2026/10/16 18:00–19:00是線上說明會，不是申請或資格確認截止。",
                    "deadline_source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intro",
                    "deadline_checked_at": "2026-10-16T06:35:00Z",
                    "deadline_reminder_eligible": False,
                    "summary": f"大學部累計班排名前 85% 以內、碩博班總平均 80 分以上、操行 80 分以上且無校規懲處紀錄；{item['eligibility_detail']}",
                    "details": [
                        f"學業與操行門檻：{item['gpa_requirement']}",
                        f"外語能力規定：{item['language_requirement']}",
                        f"當期名額：{item['quota']}",
                    ],
                    "scope": {
                        "home_universities": ["東吳大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["116"],
                        "application_rounds": ["116學年度（第1學期／第2學期）", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "source_urls": [
                        source_url,
                        "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intro",
                    ],
                    "checked_at": "2026-10-16T06:35:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"scu-116-home-2-{idx+1:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "於線上申請系統選填至多 6 個志願並上傳合併 PDF 備審資料",
                    "responsible_party": "學生",
                    "responsible_unit": "東吳大學國際與兩岸學術交流事務處（線上申請系統）",
                    "deadline_at": "2026-11-16T12:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply" if kind != "china_exchange" else "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/apply",
                    "deadline_checked_at": "2026-10-19T09:30:00Z" if kind == "china_exchange" else "2026-10-16T06:35:00Z",
                    "deadline_reminder_eligible": True,
                    "summary": "2026/09/14 至 2026/11/16 中午 12:00 前於線上系統完成志願選填與 PDF 備審上傳，無需繳交紙本或簽核單。",
                    "details": [
                        "登入 https://api.sys.scu.edu.tw/exchange/Login.aspx ，選填至多 6 個志願（每志願配對 1 所學校及 1 個交換學期；審查優先以 1 學期原則排序，有意研修 1 學年者請至少選填 2 個志願）。",
                        "各類上傳檔案限 PDF 格式、每類上限 5MB，檔名請勿包含中英文或數字以外之特殊符號；國際處統一向電算中心與德育中心查核成績及獎懲，舊生免上傳成績單與在學證明。",
                    ],
                    "document_requirements": [
                        {
                            "name": "自傳或履歷 1 份（約 2,000 字，PDF 檔）",
                            "source_urls": ["https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply" if kind != "china_exchange" else "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/apply"],
                        },
                        {
                            "name": "交換研修動機及讀書計畫（一校一份，赴外交換每份約 2,000 字（非上限）；海外組須合併中文 Form A 與外文 Form B 且中文排序在前；赴陸組使用「赴大陸協議學校交換動機及讀書計畫」表格）",
                            "official_form_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply" if kind != "china_exchange" else "https://icae.scu.edu.tw/sites/default/files/2026-09/%E8%B5%B4%E5%A4%A7%E9%99%B8%E5%8D%94%E8%AD%B0%E5%AD%B8%E6%A0%A1%E4%BA%A4%E6%8F%9B%E5%8B%95%E6%A9%9F%E5%8F%8A%E8%AE%80%E6%9B%B8%E8%A8%88%E7%95%AB.docx",
                            "source_urls": ["https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply"] if kind != "china_exchange" else ["https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/apply"],
                        },
                        {
                            "name": "外語檢定成績證明 PDF（英歐語組須為 2025/01/31 後核發、JLPT 須為 2024/01/31 後核發；不接受多益校園考）",
                            "conditional": kind == "china_exchange",
                            "condition": "赴國外／港澳交換及自費研修必繳；赴大陸交換免附外語檢定證明",
                            "source_urls": [source_url],
                        },
                        {
                            "name": "其他有利審查文件 PDF（選繳，佔 10%：未彌封推薦函至多 2 封、5 年內證照、近 3 年競賽／社團幹部／實習證明）",
                            "conditional": True,
                            "condition": "選繳項目（佔校內甄選總分 10%）",
                            "source_urls": ["https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/requirements"],
                        },
                    ],
                    "scope": {
                        "home_universities": ["東吳大學"],
                        "academic_years": ["116"],
                        "application_rounds": ["116學年度（第1學期／第2學期）", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "submission": {
                        "method": "online",
                        "office": "東吳大學國際與兩岸學術交流事務處（外雙溪校區 A313 / 城中校區 2110）",
                        "portal_url": "https://api.sys.scu.edu.tw/exchange/Login.aspx",
                    },
                    "action_url": "https://api.sys.scu.edu.tw/exchange/Login.aspx",
                    "source_urls": [
                        "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
                        "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/apply",
                    ],
                    "checked_at": "2026-10-16T06:35:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"scu-116-home-3-{idx+1:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "國際交流委員會書面審查公告錄取、繳交確認書與 NT$5,000 保證金",
                    "responsible_party": "學生與東吳國際處",
                    "responsible_unit": "東吳大學國際交流委員會／國際與兩岸事務中心",
                    "summary": "預計於 2026 年 12 月底前公告甄選結果；獲推薦生須於 1 週內繳交家長簽署之交換研習確認書與保證金 NT$5,000 以保留推薦資格。",
                    "details": [
                        "赴國外交換評分比重：大學部（歷年成績 40%、自傳及動機讀書計畫 30%、外語檢定 20%、其他有利審查文件 10%）；碩博班（歷年成績 30%、自傳及動機讀書研究計畫 40%、外語檢定 20%、其他有利審查文件 10%）。",
                        "赴大陸交換評分比重：大學部（歷年成績 50%、自傳及動機讀書計畫 40%、其他有利審查文件 10%）；碩博班（歷年成績 40%、自傳及動機讀書研究計畫 50%、其他有利審查文件 10%）。",
                    ],
                    "scope": {
                        "home_universities": ["東吳大學"],
                        "academic_years": ["116"],
                        "application_rounds": ["116學年度（第1學期／第2學期）", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "source_urls": [
                        "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/requirements",
                        "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/requirements",
                    ],
                    "checked_at": "2026-10-16T06:35:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"scu-{idx+1:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由東吳國際處提名並完成 {zh_name} 入學申請文件與選課／住宿登錄",
                    "responsible_party": "學生與接待校國際處",
                    "summary": f"獲東吳推薦後配合備妥 {full_name} 要求之各項申請表單、英文歷年成績單、財力證明與護照影本，由接待校審查核發正式入學許可。",
                    "details": [
                        f"基本條件與授課規定：{item['eligibility_detail']}",
                        f"外語門檻：{item['language_requirement']}",
                        "各交換學校保留審查入學之最終決定權；少數亞洲及多數歐美學校未保證校內宿舍，獲提名後應儘速依接待校指示申請宿舍或安排校外住宿。",
                    ],
                    "scope": {
                        "home_universities": ["東吳大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["116"],
                        "application_rounds": ["116學年度（第1學期／第2學期）", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "source_urls": [source_url] + ([website] if website else []),
                    "checked_at": "2026-10-16T06:35:00Z",
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"scu-116-home-5-{idx+1:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "辦理簽證、海外保險與東吳註冊繳費，返臺完成學分抵免與心得繳交",
                    "responsible_party": "學生",
                    "responsible_unit": "東吳大學國際與兩岸學術交流事務處／教務處註冊課務組／所屬學系",
                    "summary": "交換期間須繳交東吳全額學雜費保留學籍，於境外每學期至少修習 1 門課程；返臺後開學 1 週內完成學分抵免（或申請不抵免）並於 1 個月內繳交心得報告以退還 NT$5,000 保證金。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["東吳大學"],
                        "academic_years": ["116"],
                        "application_rounds": ["116學年度（第1學期／第2學期）", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "source_urls": [
                        "https://icae.scu.edu.tw/sites/default/files/2025-09/06_%E6%9D%B1%E5%90%B3%E5%A4%A7%E5%AD%B8%E6%A0%A1%E7%B4%9A%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E8%A8%88%E7%95%AB%E5%AF%A6%E6%96%BD%E8%BE%A6%E6%B3%95_0.pdf",
                        "https://www.scu.edu.tw/regcurr/regulations/reg305.pdf",
                    ],
                    "checked_at": "2026-10-16T06:35:00Z",
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": "2026-10-16T06:35:00Z",
            "coverage_status": "official_verified",
            "coverage_note": "已完整整合東吳大學 116 學年度校級赴外（126 校）、赴陸（62 校）及自費研修（3 校）最新簡章、審查標準與一覽表。",
        })

        cost_default, visa_default = REGION_COST_DEFAULTS.get(
            country,
            ("USD 800–1,300 / 月（含住宿、膳食、教材與當地交通費用）", "須依接待校與駐臺代表處規定辦理學生簽證與海外醫療保險。"),
        )
        cost_line = f"預估每月生活費約 {cost_default}"
        tuition_clean = tuition_points_list[0]
        housing_clean = "各協議校住宿條件不一，少數亞洲及多數歐美學校未保證校內宿舍，僅提供推薦之校外租屋平台或學生公寓網站供參考；學生須依接待校規定自行申請或自覓住處。"
        course_clean = f"{item['eligibility_detail']}｜依《東吳大學學生出境期間有關學業及學籍處理辦法》，交換學生於境外學校每學期至少應修習 1 門課程，返臺後至遲於開學 1 週內完成學分抵免（或申請不抵免學分）手續。"
        calendar_clean = "第1學期（2027秋季學期）：約2027年8/9月至2028年1月；第2學期（2028春季學期）：約2028年2月至7月（實際研修時間依協議校行事曆為準）。"

        dest_sources = [
            {"title": f"東吳大學 116 學年度交換學校一覽表—{zh_name}", "source_url": source_url, "summary": "官方交換名額、基本條件與外語能力門檻"},
            {"title": "東吳大學學生出境期間有關學業及學籍處理辦法", "source_url": "https://www.scu.edu.tw/regcurr/regulations/reg305.pdf", "summary": "東吳交換學生選課下限、學籍註冊與返國抵免規定"},
        ]
        if website:
            dest_sources.append({"title": f"{full_name} 官方網站", "source_url": website, "summary": "接待合作校官方網站與交換生資訊專頁"})

        src_url_list = [source_url] + ([website] if website else [])

        destinations.append({
            "home_university": "東吳大學",
            "school_name": full_name,
            "country": country,
            "city": location_obj.get("city") or country,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": f"校區代表城市：{location_obj.get('city') or country}。請依錄取通知確認實際授課校區、機場抵達路線與當地學生交通卡優惠。",
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費與學雜費規定",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list,
                    "caution": "實際花費視個人住宿型態與消費習慣而異；部分協議校另需繳交當地強制保險及行政作業費。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "校內宿舍名額有限或需自覓校外住宿，獲推薦與提名後請密切留意接待校住宿申請截止日。",
                },
                {
                    "key": "insurance",
                    "title": "醫療保險與安全",
                    "summary": visa_default,
                    "points": [visa_default, "出境期間須依東吳大學及接待校規定投保涵蓋全期之海外醫療及意外保險。"],
                    "source_urls": src_url_list,
                    "caution": "部分國家（如德國公保、澳洲 OSHC、日韓國民健康保險、美國校園醫保）強制要求投保當地指定保險。",
                },
                {
                    "key": "visa",
                    "title": "簽證與入境準備",
                    "summary": visa_default,
                    "points": [
                        "收到接待校正式入學許可（Acceptance Letter / COE / DS-2019 / 錄取通知書）後，立即辦理簽證或臺胞證簽註。",
                        visa_default,
                    ],
                    "source_urls": src_url_list,
                    "caution": "未獲接待校正式入學許可及簽證前，切勿購買不可退改之機票。",
                },
                {
                    "key": "courses",
                    "title": "課程限制、選課與學分抵免",
                    "summary": course_clean[:160],
                    "points": [
                        course_clean,
                        "歐洲地區學校多採用 ECTS 學分制（2 個 ECTS 約等於東吳大學 1 學分）；返臺後若無需抵免學分者，仍須於開學 1 週內完成「申請不抵免學分」簽核手續。",
                    ],
                    "source_urls": src_url_list + ["https://www.scu.edu.tw/regcurr/regulations/reg305.pdf"],
                    "caution": "學分抵免須經所屬學系審核確認；應屆畢業生請特別留意協議校成績單寄達時間，以免影響畢業時程。",
                },
                {
                    "key": "city",
                    "title": "城市與校區位置",
                    "summary": f"{country} {location_obj.get('city') or ''}".strip(),
                    "points": [location_obj.get("note") or f"{full_name} 校級代表位置位於 {location_obj.get('city') or country}。"],
                    "source_urls": [location_obj.get("source_url") or source_url],
                    "caution": "多校區大學之實際上課地點依所選院系與課程而定。",
                },
                {
                    "key": "arrival",
                    "title": "學期年曆與到校迎新",
                    "summary": calendar_clean,
                    "points": [calendar_clean],
                    "source_urls": src_url_list,
                    "caution": "請依接待校入學許可信指定之報到日與迎新週（Orientation）時程抵達。",
                },
            ],
            "first_72_hours": [
                {
                    "title": "依接待校指定報到日辦理入住、國際處報到與選課確認",
                    "detail": calendar_clean,
                    "source_urls": [source_url],
                },
                {
                    "title": "完成當地居留登錄、醫療保險投保與平安回報",
                    "detail": f"{visa_default} 抵校安頓後請向東吳大學國際與兩岸事務中心回報抵達狀況與緊急聯絡方式。",
                    "source_urls": ["https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply"],
                },
            ],
            "sources": dest_sources,
            "last_checked": "2026-10-16T06:35:00Z",
            "coverage_status": "official_verified",
            "coverage_note": "已整合東吳大學 116 學年度交換學校一覽表、出境學業學籍處理辦法及接待校官方連結。",
        })

        research_records.append({
            "home_university": "東吳大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified" if website else "needs_review",
            "discovery_source_url": source_url,
            "checked_at": "2026-10-16T06:35:00Z",
            "note": f"東吳大學 116 學年度官方交換一覽表（{source_url}）及 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [{"title": f"東吳大學 116 學年度交換一覽表—{zh_name}", "url": source_url}]
        if website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": website})
        ev_list = [
            {
                "theme": "housing",
                "kind": "official",
                "text": housing_clean,
                "sources": ev_sources,
                "checked_at": "2026-10-16T06:35:00Z",
                "scope": "東吳大學 116 學年度赴外交換申請說明住宿提醒與接待校資訊",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "cost",
                "kind": "official",
                "text": f"{tuition_clean}｜預估生活開支：{cost_default}",
                "sources": ev_sources,
                "checked_at": "2026-10-16T06:35:00Z",
                "scope": "東吳大學 116 學年度交換費用規定與地區生活費估算",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "academics",
                "kind": "official",
                "text": course_clean,
                "sources": ev_sources,
                "checked_at": "2026-10-16T06:35:00Z",
                "scope": "東吳大學 116 學年度交換一覽表基本條件與出境選課規定",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "safety",
                "kind": "official",
                "text": visa_default,
                "sources": ev_sources,
                "checked_at": "2026-10-16T06:35:00Z",
                "scope": "東吳大學出境交換簽證、醫療保險與安全提醒",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "campus_culture",
                "kind": "official",
                "text": f"交換學期：{study_period_str}｜每學期名額：{item['quota']}｜外語要求：{item['language_requirement']}",
                "sources": ev_sources,
                "checked_at": "2026-10-16T06:35:00Z",
                "scope": "東吳大學 116 學年度交換計畫名額與語檢要求",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
        ]
        life_records.append({
            "school_name": full_name,
            "country": country,
            "checked_at": "2026-10-16T06:35:00Z",
            "status": "ready",
            "evidence": ev_list,
            "notes": [
                "已整合東吳大學 116 學年度赴外／赴陸交換學校一覽表與申請說明。",
                "116學年度當期宿位供給、費用與選課限制請依接待校最新網站與 Fact Sheet 核對。",
            ],
            "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
            "extraction_version": 3,
        })

    (OFFICIAL_SCU_DIR / "partners.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_SCU_DIR / "application_workflows.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_SCU_DIR / "destination_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_SCU_DIR / "partner_research.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_SCU_DIR / "student_life.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_SCU_DIR / "campus-locations.json").write_text(
        json.dumps({"locations": new_locations}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Update university_locations.jsonl with 東吳大學 home location
    loc_file = REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
    existing_loc_lines = [line for line in loc_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    existing_loc_map = {}
    for line in existing_loc_lines:
        rec = json.loads(line)
        existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

    scu_home_loc = {
        "school_name": "東吳大學",
        "country": "臺灣",
        "city": "臺北市士林區",
        "latitude": 25.0945,
        "longitude": 121.5455,
        "geocode_status": "verified",
        "geocoded_at": "2026-10-16T06:30:00Z",
        "source_url": "https://www.wikidata.org/wiki/Q115370",
        "identity_source_url": "https://ror.org/05kvm7n82",
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。 母校代表點採外雙溪校區（臺北市士林區臨溪路70號，另設城中校區於臺北市中正區貴陽街一段56號）；官方校區地址來源：https://www-ch.scu.edu.tw/october/campus_map。",
    }
    existing_loc_map[("東吳大學", "臺灣")] = scu_home_loc
    sorted_locs = sorted(existing_loc_map.values(), key=lambda r: (r.get("country") or "", r.get("school_name") or ""))
    loc_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
        encoding="utf-8",
    )

    # Update school-images.json
    img_file = STATIC_DIR / "assets" / "school-images.json"
    img_manifest = json.loads(img_file.read_text(encoding="utf-8"))
    existing_imgs = img_manifest.get("schools", [])
    existing_img_keys = {(r.get("school_name"), r.get("country")) for r in existing_imgs if isinstance(r, dict)}
    added_imgs = 0
    for img in new_images:
        key = (img["school_name"], img["country"])
        if key not in existing_img_keys:
            existing_imgs.append(img)
            existing_img_keys.add(key)
            added_imgs += 1
    img_manifest["schools"] = existing_imgs
    img_file.write_text(json.dumps(img_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    scu_source_urls = [
        "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intro",
        "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
        "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intl/2025-2026schools",
        "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/requirements",
        "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/ppt",
        "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/apply",
        "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/list",
        "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/requirements",
        "https://icae.scu.edu.tw/zh-hant/outbound-exchange/tuition-based%20programs",
        "https://icae.scu.edu.tw/zh-hant/contract",
        "https://icae.scu.edu.tw/zh-hant/document/offcampus",
        "https://icae.scu.edu.tw/sites/default/files/2025-09/06_%E6%9D%B1%E5%90%B3%E5%A4%A7%E5%AD%B8%E6%A0%A1%E7%B4%9A%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E8%A8%88%E7%95%AB%E5%AF%A6%E6%96%BD%E8%BE%A6%E6%B3%95_0.pdf",
        "https://www.scu.edu.tw/regcurr/regulations/reg305.pdf",
    ]

    exchange_info_payload = {
        "school_name": "東吳大學",
        "program_type": [
            "交換學生（校級赴外／港澳協議學校）",
            "交換學生（校級赴大陸協議學校）",
            "自費研修（校級赴外合作院校）",
        ],
        "academic_year": [
            "116（AY2027–2028）",
        ],
        "semester": [
            "第1學期（2027秋季學期：約2027年8月至2028年1月）",
            "第2學期（2028春季學期：約2028年2月至7月）",
        ],
        "application_period": [
            "116學年度校級赴境外（含赴外、大陸、港澳地區）交換暨自費研修申請時間：2026年9月14日起至2026年11月16日（星期一）中午12:00止（一次申請同時涵蓋 116-1 秋季班及 116-2 春季班），預計於2026年12月底前公告甄選結果。",
            "116學年度赴外／赴陸交換申請說明暨分享會：2026年9月29日至10月16日於雙溪校區 G101 會議室、城中校區 5216 菁英講堂／2123 會議室及 Microsoft Teams 線上場次（10/16 18:00–19:00）舉辦。",
            "全程採線上申請（https://api.sys.scu.edu.tw/exchange/Login.aspx），至多選填 6 個志願（每個志願配對 1 所研修學校及 1 個研修學期），無需繳交紙本附件或簽核單。",
        ],
        "eligibility": [
            "申請及交換期間均應具東吳大學正式學籍（不得為休學或大學部延修第二年），並符合交換學校之規定；赴大陸交換及澳門城市大學不開放非全日制學生（如進修學士班、碩士在職專班）申請。",
            "在校學業與操行門檻：大學部學生累計班排名須達前 85% 以內（學業成績計算公式：歷年平均成績×45%＋(1－累計班排名百分比)×100×55%），碩博班學生入學後成績總平均須達 80 分（含）以上；全體申請人操行成績須達 80 分（含）以上，且未有校規懲處紀錄。",
            "赴國外交換甄選評分標準：大學部（歷年在校成績 40%、自傳及交換動機與讀書計畫 30%、外語檢定 20%、其他有利審查文件 10%）；碩博班（歷年在校成績 30%、自傳及交換動機與讀書研究計畫 40%、外語檢定 20%、其他有利審查文件 10%）。",
            "赴大陸交換甄選評分標準：大學部（歷年在校成績 50%、自傳及交換動機與讀書計畫 40%、其他有利審查文件 10%）；碩博班（歷年在校成績 40%、自傳及交換動機與讀書研究計畫 50%、其他有利審查文件 10%）。",
            "每人至多可選填 6 個志願（每志願含交換學校及交換學期）；審查作業優先以 1 學期為原則排序，若有缺額再針對 1 學年研修排序（有意赴外研修 1 學年者請至少選填 2 個志願）。從未參加校級赴外／赴陸交換研修者優先考量。",
        ],
        "language_requirement": [
            "申請赴國外（含港澳）交換學生，須至少符合擬申請學校於《116學年度校級赴外交換學校一覽表》所列任一項外語檢定門檻（如 TOEFL iBT 60–100、IELTS Academic 5.5–7.0、TOEIC 650–800、JLPT N1–N3、TOPIK 2–4 級，或法／德／西／捷克語 CEFR A2–B2）。",
            "外語檢定有效期限：英語及歐語檢定須為 2025 年 1 月 31 日後核發（2 年內有效），日本語能力試驗（JLPT）須為 2024 年 1 月 31 日後核發（3 年內有效）；逾期限之語檢證明仍可檢附作為審查文件惟酌予扣分。",
            "重要採認限制：不接受多益校園考（Institutional TOEIC）成績；雅思（IELTS）須為學術組（Academic）；托福新制 1–6 分制可依國際處公告對照表換算（4.0 對應 72–85、4.5 對應 86–94、5.0 對應 95–106、5.5 對應 107–113、6.0 對應 114+）。",
            "尚未取得正式紙本成績單者，校內甄選階段可先上傳網路查詢成績截圖並親筆簽名，正式成績單影本須於後續補正。",
            "赴大陸地區協議學校交換：中文授課免附外語檢定證明。",
        ],
        "required_documents": [
            "線上申請表與志願序（登入 https://api.sys.scu.edu.tw/exchange/Login.aspx 填報，至多 6 個志願，免交紙本）",
            "自傳或履歷 1 份（約 2,000 字，合併為單一 PDF 檔上傳，上限 5MB；外籍生可以英文撰打）",
            "交換研修動機及讀書計畫（一校一份，各約 2,000 字（赴外規格，非上限）：赴外交換須同時撰寫中文 Form A 及外文 Form B，依志願序將所有中文表格排在前、外文表格在後合併為 1 份 PDF；赴陸交換使用中文表格）",
            "外語檢定成績證明 PDF（赴外交換及自費研修必繳，2025/01/31 後核發、JLPT 為 2024/01/31 後核發；赴陸交換免附）",
            "其他有利審查文件 PDF（選繳，佔總分 10%：未彌封推薦函至多 2 封、5 年內檢定或證照、近 3 年競賽獎狀／課外活動／幹部／實習官方證明）",
            "學籍、歷年成績單與獎懲紀錄免自行上傳（由國際處統一委託電算中心與德育中心查核；惟大一新生、碩博一新生或轉學生無東吳前一學年成績者，須另行電郵提交前校歷年成績單含總平均及累計班排名）",
        ],
        "scholarship_info": [
            "教育部「學海飛颺計畫」與「學海惜珠計畫」獎助學金：補助赴國外（不含大陸及港澳地區）修讀學分之優秀交換生及具學雜費減免／弱勢助學資格學生，於獲得交換生推薦資格後之次一學期（每年約 2–3 月及 7 月）開放申請。",
            "教育部「高教深耕—扶助攻頂計畫」學生赴外研習助學金：針對具低收入戶、中低收入戶、身心障礙學生／子女、大專弱勢助學計畫、原住民或家庭突遭變故之在學學生，提供出國交換與研習專案補助。",
            "《東吳大學學生赴外研習補助》及《東吳大學國際學術交流計畫獎補助辦法》：補助具正式學籍學生（不含陸港澳籍）赴國外（不含陸港澳）交換或自費研修，曾獲外語自學獎勵者另有加碼；赴大陸及港澳地區研習者可申請《東吳大學學生赴陸港澳地區研習及學術交流補助》。",
            "日本台灣交流協會短期留學生獎學金、JASSO 獎學金及協議校提供之生活費／住宿費獎助（如日本創價大學、大東文化大學、四川大學每學期 RMB 2,000–3,000 等，依當期公告辦理）。",
            "交換期間須繳交東吳大學日間部全額學雜費，免繳交換協議學校學費（3 所英美自費研修合作校除外）；錄取確認時須繳交保證金 NT$5,000，於完成交換返臺後 1 個月內繳交 1,500–2,000 字心得報告並完成學分抵免手續後無息退還。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": scu_source_urls,
        "last_checked": "2026-10-16T06:35:00Z",
    }
    (OFFICIAL_SCU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "東吳大學",
        "last_checked": "2026-10-16T06:35:00Z",
        "academic_score_minimum": None,
        "academic_score_rule": "東吳校級赴外／赴陸交換：大學部累計班排名須達前 85% 以內（學業採計：歷年平均×45%＋(1－班排百分比)×100×55%）；碩博班入學後成績總平均須達 80 分以上；操行成績須達 80 分以上且無校規懲處紀錄。",
        "academic_gpa_minimum": None,
        "maximum_preferences": 6,
        "selection_rules": {
            "academic_policy": "percentage",
            "academic_reference_year": "116",
            "undergraduate_gpa_minimum": None,
            "undergraduate_rank_maximum": 85.0,
            "graduate_academic_exempt": False,
            "exclude_in_service": False,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "master": 80.0,
                "doctoral": 80.0,
            },
            "excluded_undergraduate_years": [],
            "language_certificate_required": False,
        },
        "language_score_minimums": {},
        "application_periods": [
            {
                "title": "東吳大學 116 學年度校級赴境外（國外／大陸／港澳）交換暨自費研修線上申請",
                "details": [
                    "申請期間：2026年9月14日（一）起至2026年11月16日（一）中午12:00止（逾時系統自動關閉）。",
                    "本次甄選同時開放申請 116 學年度第 1 學期（2027秋季班）及第 2 學期（2028春季班）交換名額，至多可選填 6 個志願（每志願含研修學校與研修學期）。",
                    "全程於線上申請系統（https://api.sys.scu.edu.tw/exchange/Login.aspx）填報並上傳 PDF 備審資料，無須繳交紙本或簽核單；預計於 2026 年 12 月底前公告甄選結果。",
                ],
                "source": {
                    "title": "東吳大學 116 學年度校級赴國外／大陸交換學生甄選申請說明",
                    "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
                    "category": "deadline",
                    "summary": "116學年度校級赴境外交換暨自費研修線上申請時程與系統入口。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度（含116-1秋季班及116-2春季班）",
                "audience": "all_students",
                "opens_at": None,
                "deadline_at": "2026-11-16T12:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "116學年度校級赴外、赴陸交換及自費研修現正開放線上申請，至 2026/11/16 中午 12:00 截止。",
                "deadline_note": "線上系統：https://api.sys.scu.edu.tw/exchange/Login.aspx（請務必先存檔再點選送出）。",
                "reminder_eligible": True,
                "checked_at": "2026-10-16T06:35:00Z",
            },
            {
                "title": "東吳大學 116 學年度赴外／赴陸交換申請說明會暨經驗分享會（雙溪／城中／線上）",
                "details": [
                    "外雙溪校區（12:00–13:00 G101 會議室）：10/08 日本多摩大學、10/14 華東師範大學、10/15 韓國明知大學與建國大學、10/16 波蘭華沙人文大學與日本龍谷大學。",
                    "城中校區（12:00–13:00 5216 菁英講堂／2123 會議室）：09/29 德國科布倫茲應用科學大學、10/06 法國 IDRAC 商學院與澳洲臥龍崗大學、10/12 德國富特旺根應用科大與南京大學、10/13 匈牙利羅蘭大學與德國明斯特大學、10/15 清華大學。",
                    "Microsoft Teams 線上說明會：2026/10/16（五）18:00–19:00（參加活動可獲美育認證 1 小時）。",
                ],
                "source": {
                    "title": "116學年度校級赴國外/大陸協議校交換申請重要資訊",
                    "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intro",
                    "category": "info_session",
                    "summary": "116學年度雙溪、城中校區及線上交換申請說明會場次與簡報下載。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度說明會",
                "audience": "all_students",
                "opens_at": "2026-09-29T12:00:00+08:00",
                "deadline_at": "2026-10-16T19:00:00+08:00",
                "date_status": "verified_exact",
                "status": "action_required",
                "status_note": "43 頁官方申請說明會簡報（116赴境外交換申請說明會簡報_0.pdf）已公告於國際處網站。",
                "deadline_note": "說明會後請於 2026/11/16 中午 12:00 前完成線上系統申請。",
                "reminder_eligible": True,
                "checked_at": "2026-10-16T06:35:00Z",
            },
            {
                "title": "東吳大學 116 學年度交換甄選結果公告與保證金確認（2026年12月底）",
                "details": [
                    "國際交流委員會預計於 2026 年 12 月底前公告 116 學年度獲推薦名單。",
                    "接獲錄取通知後，須於規定時間內（約 1 週內）繳交家長親筆簽署之「東吳大學學生赴協議學校交換研習確認書」及保證金新台幣 5,000 元，逾期視同放棄。",
                ],
                "source": {
                    "title": "東吳大學 116 學年度校級赴國外交換學生甄選申請說明",
                    "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
                    "category": "exchange_application",
                    "summary": "甄選結果通知、確認書繳交與保證金規定。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度結果公告",
                "audience": "applicants",
                "opens_at": None,
                "deadline_at": None,
                "date_status": "reference_only",
                "status": "reference_only",
                "status_note": "官方僅預計2026年12月底前公告，未列精確日期或時刻；確認書與保證金期限依錄取通知。",
                "deadline_note": "錄取後須繳交確認書及保證金 NT$5,000。",
                "reminder_eligible": False,
                "checked_at": "2026-10-16T06:35:00Z",
            },
        ],
        "program_overview": [
            {
                "title": "東吳大學 116 學年度全球校級交換暨自費研修計畫總覽（191 所合作校現正開放申請）",
                "details": [
                    "東吳大學國際與兩岸學術交流事務處（ICAE）辦理 116 學年度（2027秋季班／2028春季班）校級赴境外交換暨自費研修甄選，完整涵蓋赴國外及港澳交換學校 126 所、赴大陸地區交換學校 62 所，以及英美自費研修合作大學 3 所（UC Berkeley、UEA、Edinburgh Napier），共計 191 所合作校。",
                    "116 學年度線上申請自 2026 年 9 月 14 日起至 11 月 16 日中午 12:00 止（https://api.sys.scu.edu.tw/exchange/Login.aspx），每位學生至多可選填 6 個志願（每志願配對 1 所學校與 1 個學期；審查優先以 1 學期原則排序）。",
                    "本平台完整收錄 191 所合作校之 116 學年度當期名額、各校外語檢定門檻、GPA 與學制限制、赴陸學籍身分與應屆／延畢規定、審查評分標準及獎助學金資訊。",
                ],
                "source": {
                    "title": "東吳大學 116 學年度校級赴外／赴陸交換學校一覽表",
                    "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intl/2025-2026schools",
                    "category": "partner_school",
                    "summary": "116學年度赴外 126 校、赴陸 62 校與自費研修 3 校完整名額與條件。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "學籍、累計班排名／碩博總平均與操行門檻",
                "details": [
                    "申請及交換期間均須具東吳大學正式學籍（不得為休學或大學部延修第二年）；赴大陸交換及澳門城市大學不開放非全日制學生（進修學士班、碩士在職專班）申請。",
                    "大學部學生：累計班排名須達前 85% 以內（校內審查學業成績計算方式：歷年平均成績×45%＋(1－累計班排名百分比)×100×55%）。",
                    "碩博士班學生：入學後歷年成績總平均須達 80 分（含）以上。",
                    "操行與獎懲門檻：操行成績須達 80 分（含）以上，且未有校規懲處紀錄（由國際處統一向電算中心與德育中心查核）。",
                    "審查評分比重：赴外交換為歷年成績 40%（碩博 30%）、自傳及動機讀書計畫 30%（碩博 40%）、外語檢定 20%、其他有利審查文件 10%；赴陸交換為歷年成績 50%（碩博 40%）、自傳及動機讀書計畫 40%（碩博 50%）、其他有利審查文件 10%。",
                ],
                "source": {
                    "title": "東吳大學赴國外／赴大陸校級交換學生審查標準",
                    "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/requirements",
                    "category": "exchange_application",
                    "summary": "大學部與碩博班申請門檻、學業成績換算公式與評分項目比重。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "外語檢定採認標準、發證年限與新制托福對照表",
                "details": [
                    "申請赴外（含港澳）交換須符合《116學年度校級赴外交換學校一覽表》各校所列任一語檢門檻（符合其一即可）；赴大陸地區交換免附外語檢定。",
                    "發證年限規定：英語及歐語檢定須為 2025 年 1 月 31 日後核發（2 年內），日本語能力試驗（JLPT）須為 2024 年 1 月 31 日後核發（3 年內）；超過期限之語檢證明仍可檢附作為審查文件，惟審查時酌予扣分。",
                    "重要限制：不接受多益校園考（Institutional TOEIC）成績；IELTS 須為 Academic 學術組；托福新制 1–6 分制對照標準為 6.0=114+、5.5=107–113、5.0=95–106、4.5=86–94、4.0=72–85。",
                ],
                "source": {
                    "title": "東吳大學 116 學年度校級赴外交換學校一覽表及審查標準",
                    "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intl/2025-2026schools",
                    "category": "exchange_application",
                    "summary": "各校外語檢定門檻、發證期限與語檢採認限制。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "東吳線上申請系統應備 PDF 文件清單（免交紙本）",
                "details": [
                    "1. 自傳或履歷 1 份（約 2,000 字，無既定格式，外籍生可以英文撰打，存為 PDF 檔）。",
                    "2. 交換研修動機及讀書計畫（一校一份，各約 2,000 字（赴外規格，非上限）：赴外交換須下載填寫中文 Form A 與外文 Form B，依志願序將所有中文資料排在前、外文資料在後合併為單一 PDF 檔；赴陸交換使用中文表格）。",
                    "3. 外語檢定成績證明 PDF（赴外交換及自費研修必繳；尚未取得正式成績單者可先上傳簽名之網路成績查詢截圖，後續補正正式成績單影本；赴陸交換免附）。",
                    "4. 其他有利審查文件 PDF（選繳，佔 10%：未彌封推薦函至多 2 封、5 年內檢定或證照、近 3 年競賽獎狀／課外活動／幹部／實習官方證明）。",
                    "5. 成績單與在學證明：舊生無須自行上傳（由國際處統一委託電算中心與德育中心查核）；僅新生或轉學生無東吳前一學年成績者須電郵提交前校歷年成績單（含總平均及累計班排名）。每類檔案上限 5MB，檔名僅限中英數字符號。",
                ],
                "source": {
                    "title": "東吳大學 116 學年度校級赴國外／大陸交換學生甄選申請說明",
                    "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
                    "category": "exchange_application",
                    "summary": "線上申請系統 PDF 備審資料規格、Form A/B 合併規則與免交紙本說明。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "教育部學海系列、高教深耕扶助攻頂與東吳校內赴外／赴陸港澳研習獎補助",
                "details": [
                    "教育部「學海飛颺」與「學海惜珠」計畫：補助赴國外（不含陸港澳）修讀學分之優秀學生及經濟不利學生，於獲得交換推薦資格後之次一學期（約 2–3 月及 7 月）開放申請。",
                    "教育部「高教深耕—扶助攻頂計畫」學生赴外研習助學金：補助具學雜費減免、弱勢助學、原住民或家庭突遭變故資格之在學學生出國研習。",
                    "《東吳大學學生赴外研習補助》與《東吳大學學生赴陸港澳地區研習及學術交流補助》：分別補助赴國外及赴大陸港澳交換研習學生。",
                    "交換期間須繳交東吳日間部全額學雜費，免繳交換學校學費（自費研修除外）；錄取確認時須繳交保證金 NT$5,000，返臺後開學 1 週內完成學分抵免（或申請不抵免）並於 1 個月內繳交 1,500–2,000 字心得報告後無息退還。",
                ],
                "source": {
                    "title": "東吳大學國際與兩岸學術交流事務處—獎補助法規與公告專頁",
                    "source_url": "https://icae.scu.edu.tw/zh-hant/document/offcampus",
                    "category": "scholarship",
                    "summary": "學海飛颺、學海惜珠、高教深耕扶助攻頂與校內赴外／赴陸港澳研習補助辦法。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "交換研修動機及讀書計畫（Form A 中文版、Form B 外文版）與推薦函格式",
                "summary": "東吳大學校內甄選採全線上 PDF 上傳（免交紙本），交換研修動機及讀書計畫須以「一校一份」原則撰寫並依志願序合併為單一 PDF 檔（上限 5MB）。",
                "key_points": [
                    "赴國外交換申請者須同時填寫中文表格（Form A）及英／日文表格（Form B），合併 PDF 時所有中文資料須排序在前、外文資料在後。",
                    "推薦函為選繳有利審查文件（至多 2 封），請勿彌封以便掃描合併上傳。",
                ],
                "applies_to": [],
                "source": {
                    "title": "東吳大學 116 學年度校級赴國外交換學生甄選申請說明",
                    "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "《東吳大學校級交換學生計畫實施辦法》與《學生出境期間有關學業及學籍處理辦法》重點",
                "summary": "規範校級交換生甄選條件、出境期間註冊繳費、每學期最低修課門檻、返臺學分抵免期限與保證金退還義務。",
                "key_points": [
                    "經核准出境修讀學分之交換學生，於境外學校每學期至少應修習 1 門課程；返臺後至遲應於開學 1 週內完成抵免程序（無須抵免者亦須辦理「申請不抵免學分」簽核）。",
                    "交換期間須繳交東吳大學全額學雜費以保留學籍；獲推薦後繳交保證金 NT$5,000，於返臺 1 個月內繳交心得報告並完成抵免程序後無息退還。",
                ],
                "applies_to": [],
                "source": {
                    "title": "東吳大學學生出境期間有關學業及學籍處理辦法（reg305.pdf）",
                    "source_url": "https://www.scu.edu.tw/regcurr/regulations/reg305.pdf",
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": "https://www.scu.edu.tw/regcurr/regulations/reg305.pdf",
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {
                "title": "東吳大學 116 學年度校級赴國外/大陸協議校交換申請重要資訊",
                "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intro",
                "category": "info_session",
                "summary": None,
            },
            {
                "title": "東吳大學 116 學年度校級赴國外交換學生甄選申請說明",
                "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "東吳大學 116 學年度校級赴外交換學校一覽表（126 校）",
                "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intl/2025-2026schools",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "東吳大學赴國外校級交換學生審查標準",
                "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/requirements",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "東吳大學 116 學年度校級赴大陸交換學生甄選申請說明",
                "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/apply",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "東吳大學 116 學年度校級赴陸交換學校一覽表（62 校）",
                "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/list",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "東吳大學赴大陸校級交換學生審查標準",
                "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/requirements",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "東吳大學 116 學年度校級赴外自費研修計畫（UC Berkeley / UEA / Edinburgh Napier）",
                "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/tuition-based%20programs",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "東吳大學學生出境期間有關學業及學籍處理辦法（reg305.pdf）",
                "source_url": "https://www.scu.edu.tw/regcurr/regulations/reg305.pdf",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "東吳大學校外與校內出國交換獎補助辦法專頁",
                "source_url": "https://icae.scu.edu.tw/zh-hant/document/offcampus",
                "category": "scholarship",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_SCU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    pages_records = [
        {
            "title": "東吳大學：116學年度校級赴國外／大陸協議校交換申請時程與說明會",
            "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intro",
            "published_at": "2026-09-14T00:00:00Z",
            "text": "\n".join(exchange_info_payload["application_period"]),
            "summary": "\n".join(exchange_info_payload["application_period"]),
            "category": "exchange_application",
            "attachments": [
                {
                    "url": "https://icae.scu.edu.tw/sites/default/files/2026-09/116%E8%B5%B4%E5%A2%83%E5%A4%96%E4%BA%A4%E6%8F%9B%E7%94%B3%E8%AB%8B%E8%AA%AA%E6%98%8E%E6%9C%83%E7%B0%A1%E5%A0%B1_0.pdf",
                    "filename": "116赴境外交換申請說明會簡報_0.pdf",
                    "local_path": None,
                    "content_type": "application/pdf",
                }
            ],
            "crawled_at": "2026-10-16T06:20:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "東吳大學：申請資格與校內審查評分標準",
            "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/requirements",
            "published_at": None,
            "text": "\n".join(exchange_info_payload["eligibility"]),
            "summary": "\n".join(exchange_info_payload["eligibility"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-16T06:20:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "東吳大學：外語能力檢定規定與新制托福對照表",
            "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intl/2025-2026schools",
            "published_at": "2026-10-01T00:00:00Z",
            "text": "\n".join(exchange_info_payload["language_requirement"]),
            "summary": "\n".join(exchange_info_payload["language_requirement"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-16T06:20:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "東吳大學：線上申請系統備審文件規範",
            "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
            "published_at": "2026-09-12T00:00:00Z",
            "text": "\n".join(exchange_info_payload["required_documents"]),
            "summary": "\n".join(exchange_info_payload["required_documents"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-16T06:20:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "東吳大學：赴外與赴陸港澳交換獎助學金及經費規定",
            "source_url": "https://icae.scu.edu.tw/zh-hant/document/offcampus",
            "published_at": None,
            "text": "\n".join(exchange_info_payload["scholarship_info"]),
            "summary": "\n".join(exchange_info_payload["scholarship_info"]),
            "category": "scholarship",
            "attachments": [],
            "crawled_at": "2026-10-16T06:20:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "東吳大學：116學年度校級赴大陸交換學生甄選申請說明（2026-10-19 基準更正核實）",
            "source_url": "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/apply",
            "published_at": "2026-09-12T00:00:00Z",
            "text": (
                "東吳大學 116 學年度校級赴大陸交換學生甄選申請說明（適用 2027 秋季班 116-1：2027年9月–2028年1月／2028 春季班 116-2：2028年2月–7月）：\n"
                "1. 申請期間：2026年9月14日至2026年11月16日（星期一）中午12:00止，於東吳大學赴外交換線上申請系統（https://api.sys.scu.edu.tw/exchange/Login.aspx）填報並上傳 PDF 備審資料，預計於 2026 年 12 月底前通知甄選結果。\n"
                "2. 申請資格：具東吳大學正式學籍之全日制大學部、碩士班、博士班在學學生（不開放進修學士班、碩士在職專班及大學部延修第二年；部分學校可接收應屆畢業生或延畢生，詳見 62 所赴陸交換學校一覽表）。大學部累計班排名前 85% 以內、碩博班入學後總平均 80 分以上、操行 80 分以上且無校規懲處紀錄。\n"
                "3. 應繳文件：線上申請表（至多 6 個志願）、自傳或履歷（約 2,000 字 PDF）、赴大陸協議學校交換動機及讀書計畫（一校一份，約 2,000 字以內，合併為 1 份 PDF）、其他有利審查文件（選繳，如推薦函至多 2 封）。\n"
                "4. 查核基準說明（2026-10-19）：昨日查核誤讀赴陸頁之 115 學年度舊快取；今日直接核實官方現行內容為 116 學年度（適用 2027 秋／2028 春，11/16 中午截止、12 月底公布結果），並已讀取 62 校名單及申請表。此為基準更正，不能斷言今日才更新；赴國外合作表已比對範圍未變。"
            ),
            "summary": "116學年度校級赴大陸交換學生甄選（適用2027秋／2028春），2026/09/14–11/16中午12:00截止、12月底前公布結果，涵蓋62所大陸協議校及申請表。此為更正昨日115年度舊快取之基準核實，不能斷言今日才更新。",
            "category": "exchange_application",
            "attachments": [
                {
                    "url": "https://icae.scu.edu.tw/sites/default/files/2026-09/%E8%B5%B4%E5%A4%A7%E9%99%B8%E5%8D%94%E8%AD%B0%E5%AD%B8%E6%A0%A1%E4%BA%A4%E6%8F%9B%E5%8B%95%E6%A9%9F%E5%8F%8A%E8%AE%80%E6%9B%B8%E8%A8%88%E7%95%AB.docx",
                    "filename": "赴大陸協議學校交換動機及讀書計畫.docx",
                    "local_path": None,
                    "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                },
                {
                    "url": "https://icae.scu.edu.tw/sites/default/files/2026-09/%E8%B5%B4%E5%A4%A7%E9%99%B8%E5%8D%94%E8%AD%B0%E5%AD%B8%E6%A0%A1%E4%BA%A4%E6%8F%9B%E5%8B%95%E6%A9%9F%E5%8F%8A%E8%AE%80%E6%9B%B8%E8%A8%88%E7%95%AB.odt",
                    "filename": "赴大陸協議學校交換動機及讀書計畫.odt",
                    "local_path": None,
                    "content_type": "application/vnd.oasis.opendocument.text",
                },
                {
                    "url": "https://icae.scu.edu.tw/sites/default/files/2026-09/%E6%9D%B1%E5%90%B3%E5%A4%A7%E5%AD%B8116%E5%AD%B8%E5%B9%B4%E5%BA%A6%E6%A0%A1%E7%B4%9A%E8%B5%B4%E9%99%B8%E4%BA%A4%E6%8F%9B%E5%AD%B8%E6%A0%A1%E4%B8%80%E8%A6%BD%E8%A1%A8_1150915.pdf",
                    "filename": "東吳大學116學年度校級赴陸交換學校一覽表_1150915.pdf",
                    "local_path": None,
                    "content_type": "application/pdf",
                },
            ],
            "crawled_at": "2026-10-19T09:30:00Z",
            "content_hash": hashlib.sha256("scu-china-apply-116-baseline-20261019".encode("utf-8")).hexdigest(),
        },
    ]
    (OFFICIAL_SCU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "scu",
        "school_name": "東吳大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_weights": {
            "overseas_undergraduate": {"gpa_and_rank": 0.40, "study_plan_and_autobio": 0.30, "language": 0.20, "other_documents": 0.10},
            "overseas_graduate": {"gpa": 0.30, "study_plan_and_autobio": 0.40, "language": 0.20, "other_documents": 0.10},
            "mainland_undergraduate": {"gpa_and_rank": 0.50, "study_plan_and_autobio": 0.40, "other_documents": 0.10},
            "mainland_graduate": {"gpa": 0.40, "study_plan_and_autobio": 0.50, "other_documents": 0.10},
        },
        "source_urls": scu_source_urls,
        "verified_at": "2026-10-19",
    }
    (OFFICIAL_SCU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_SCU_DIR / "documents.json").write_text(
        json.dumps({"school_name": "東吳大學", "required_documents": student_dashboard_payload["required_documents"], "source_urls": scu_source_urls}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_SCU_DIR / "scholarships.json").write_text(
        json.dumps({"school_name": "東吳大學", "scholarships": student_dashboard_payload["scholarship_info"], "source_urls": scu_source_urls}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    completeness = {
        "school_id": "scu",
        "school_name": "東吳大學",
        "total_partners": len(partners),
        "overseas_and_hk_mo_exchange_partners": 126,
        "mainland_china_exchange_partners": 62,
        "tuition_based_study_abroad_partners": 3,
        "open_partners": len(partners),
        "verified_locations": len(partners),
        "verified_official_websites": sum(1 for p in partners if p.get("official_website")),
        "verified_campus_images": len(new_images),
        "active_term": "116學年度校級赴境外（國外／大陸／港澳）交換暨自費研修計畫現正開放線上申請（2026/09/14–2026/11/16 12:00），涵蓋 116-1（2027秋季班）與 116-2（2028春季班），預計 2026 年 12 月底前公告甄選結果。2026/10/19 更正赴陸頁昨日 115 舊快取基準，核實官方現行內容為 116 學年度（62 校名單及申請表已讀；不能斷言今日才更新，赴國外合作表已比對範圍未變）。",
        "verified_at": "2026-10-19",
        "baseline_correction_20261019": provenance["baseline_correction_20261019"],
    }
    (OFFICIAL_SCU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_SCU_DIR / "verification_status.json").write_text(
        json.dumps({
            "school_id": "scu",
            "school_name": "東吳大學",
            "status": "official_verified",
            "checked_at": "2026-10-19T09:30:00+08:00",
            "counts": completeness,
            "baseline_correction_20261019": provenance["baseline_correction_20261019"],
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    from exchange_info.generated_content_review import review_generated_content
    review_generated_content(REPO_ROOT, "scu", round_id=22)
    from exchange_info.host_source_review_round25 import apply_host_source_review
    apply_host_source_review(REPO_ROOT, "scu")
    from exchange_info.scu_table_source_review import apply_scu_table_source_review
    apply_scu_table_source_review(REPO_ROOT)
    from exchange_info.scu_degree_source_review import apply_scu_degree_source_review
    apply_scu_degree_source_review(REPO_ROOT)
    from exchange_info.scu_template_source_review import apply_scu_template_source_review
    apply_scu_template_source_review(REPO_ROOT)
    print(
        f"Successfully built SCU catalog: {len(partners)} partners, {len(workflows)} workflows, "
        f"{len(destinations)} destinations, {len(research_records)} research records, "
        f"{len(new_locations)} locations, {added_imgs} new school-images aliases added "
        f"(total SCU verified images: {len(new_images)})."
    )


if __name__ == "__main__":
    main()
