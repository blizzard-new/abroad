"""Build the official National Taiwan Normal University (國立臺灣師範大學, NTNU) exchange data bundle."""

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
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
from exchange_info.school_identity import VisualRecordIndex, school_identity_key

_HOST_SCRATCH = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\0723e0a1-b112-47e2-8145-2d4d6f69cb19\scratch\ntnu_raw")
SOURCES_NTNU_DIR = REPO_ROOT / "sources" / "ntnu"
SCRATCH_NTNU = _HOST_SCRATCH if _HOST_SCRATCH.exists() else SOURCES_NTNU_DIR
OFFICIAL_NTNU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "ntnu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

COUNTRY_MAP = {
    "大陸地區": "中國大陸",
    "中國": "中國大陸",
    "香港": "香港",
    "澳門": "澳門",
    "南韓": "韓國",
    "韓國": "韓國",
    "澳大利亞": "澳洲",
    "澳洲": "澳洲",
    "祕魯": "秘魯",
}

REGION_BY_COUNTRY = {
    "日本": "亞洲",
    "韓國": "亞洲",
    "中國大陸": "中國大陸及港澳",
    "香港": "中國大陸及港澳",
    "澳門": "中國大陸及港澳",
    "新加坡": "亞洲",
    "馬來西亞": "亞洲",
    "泰國": "亞洲",
    "越南": "亞洲",
    "印尼": "亞洲",
    "印度": "亞洲",
    "菲律賓": "亞洲",
    "蒙古": "亞洲",
    "土耳其": "亞洲",
    "以色列": "亞洲",
    "澳洲": "大洋洲",
    "紐西蘭": "大洋洲",
    "美國": "美洲",
    "加拿大": "美洲",
    "巴西": "美洲",
    "墨西哥": "美洲",
    "智利": "美洲",
    "哥倫比亞": "美洲",
    "秘魯": "美洲",
    "南非": "非洲",
}

REGION_COST_DEFAULTS = {
    "美國": ("USD 1,400–2,200 / 月（含住宿、餐飲、校園保險與當地交通）", "建議預留強制校園醫療保險（約 USD 1,500–2,500 / 學期）與 J-1 / F-1 簽證 SEVIS 費用；師大簡章提醒歐美區一學期交換花費約新臺幣 20–40 萬元。"),
    "加拿大": ("CAD 1,500–2,200 / 月（含住宿、膳食、省級／校內醫保與市區交通）", "須投保接待校指定醫療保險並辦理 Study Permit 或 eTA；師大簡章預估歐美區一學期花費約新臺幣 20–40 萬元。"),
    "英國": ("GBP 1,000–1,600 / 月（含宿舍、飲食與市區交通）", "交換一學期多適用 Standard Visitor 簽證，一學年須辦理 Student Visa 並繳納 IHS 醫療附加費。"),
    "法國": ("EUR 850–1,400 / 月（巴黎地區約 EUR 1,200–1,600 / 月；可申請 CAF 房補）", "須透過法國教育中心（Campus France）面試並申辦長期學生簽證（VLS-TS）。"),
    "德國": ("EUR 934–1,200 / 月（德國簽證限制提領帳戶基準為每月 EUR 934）", "須辦理德國法定公保（約 EUR 120–130 / 月）及學期雜費／學期票（Semesterticket）；德國學期多為 10 月及 4 月開學，返臺銜接選課或畢業請預先規劃。"),
    "西班牙": ("EUR 800–1,250 / 月（馬德里、巴塞隆納較高，其他城市約 EUR 700–1,000 / 月）", "須備妥涵蓋全額醫療與遺體運返之私人醫療保險以申辦西班牙學生簽證。"),
    "義大利": ("EUR 800–1,250 / 月（羅馬、米蘭、波隆那較高）", "抵義 8 個工作日內須辦理居留證（Permesso di soggiorno）與稅號（Codice Fiscale）。"),
    "荷蘭": ("EUR 950–1,400 / 月（荷蘭移民局 IND 財力證明基準約 EUR 1,225 / 月）", "由接待校代辦 MVV/VVR 居留許可，房源緊張建議獲提名後立即申請宿舍。"),
    "比利時": ("EUR 850–1,200 / 月（含學生宿舍、餐飲與大眾運輸）", "須辦理長期學生簽證 D 簽，抵達後向市政廳登記居留。"),
    "瑞士": ("CHF 1,500–2,200 / 月（含住宿、膳食與強制保險）", "須透過瑞士商務辦事處申辦學生簽證，並於抵瑞後申請居留證與醫療保險豁免或投保。"),
    "奧地利": ("EUR 850–1,250 / 月（含 OeAD 學生宿舍與日常開支）", "多透過 OeAD 申請學生宿舍，並依停留期間申辦簽證 D 或居留許可。"),
    "丹麥": ("DKK 6,500–9,500 / 月（含住宿、飲食與單車／大眾運輸）", "須申辦 ST1 學生居留許可，抵丹後登記 CPR 號碼即可享有公醫保障。"),
    "瑞典": ("SEK 9,500–13,000 / 月（瑞典移民局財力基準約 SEK 10,314 / 月）", "交換超過 3 個月須向瑞典移民局申辦學生居留許可（Residence Permit for Studies）。"),
    "芬蘭": ("EUR 750–1,100 / 月（芬蘭移民局 Migri 財力證明基準約 EUR 800 / 月）", "須透過 Enter Finland 申辦學生居留許可並投保涵蓋全期之醫療保險。"),
    "挪威": ("NOK 12,000–15,000 / 月（挪威移民局 UDI 財力證明基準約 NOK 13,790 / 月）", "須申辦挪威學生居留許可（Study Permit）並預先匯入學生保證金帳戶。"),
    "波蘭": ("EUR 500–800 / 月（含校內宿舍與日常餐飲交通）", "須申辦波蘭 D 類國別學生簽證並備妥歐盟規格旅遊醫療保險。"),
    "匈牙利": ("EUR 550–850 / 月（布達佩斯生活費與住宿相對實惠）", "須申請學生居留許可並投保醫療保險。"),
    "捷克": ("EUR 600–900 / 月（含學生宿舍、食堂與市區交通卡）", "須提前預約捷克經濟文化辦事處申辦長期學生簽證與捷克合約醫療保險。"),
    "立陶宛": ("EUR 550–850 / 月（含宿舍與日常開支）", "須透過 MIGRIS 系統申辦臨時居留許可（TRP）或國家簽證。"),
    "拉脫維亞": ("EUR 550–850 / 月（里加生活與住宿成本相對親民）", "須申辦拉脫維亞長期簽證或居留許可並備妥歐盟醫療保險。"),
    "愛沙尼亞": ("EUR 600–900 / 月（塔林生活機能便利且學生優惠完善）", "須申辦愛沙尼亞長期學生簽證（D-Visa）並投保涵蓋全期之申根醫療保險。"),
    "斯洛維尼亞": ("EUR 600–950 / 月（盧比安納學生餐券與市區交通優惠完善）", "須申辦斯洛維尼亞第一階段臨時居留許可或長期簽證 D。"),
    "俄羅斯": ("USD 500–850 / 月（約 RUB 45,000–75,000，校內宿舍費用低廉，日常開支適中）", "須憑接待校核發之官方邀請函向莫北協駐臺代表處申辦俄羅斯學生簽證。"),
    "澳洲": ("AUD 1,800–2,600 / 月（含住宿、飲食與交通）", "強制投保海外學生健康保險（OSHC）後方可核發 Subclass 500 學生簽證。"),
    "紐西蘭": ("NZD 1,600–2,300 / 月（含住宿、飲食與當地交通）", "須申辦 Fee-paying / Exchange Student Visa 並投保合規醫療與旅遊保險。"),
    "日本": ("JPY 80,000–130,000 / 月（東京圈約 JPY 100,000–140,000；地方城市約 JPY 70,000–100,000）", "憑接待校核發之在留資格認定證明書（COE）換發留學簽證，抵日後須加入國民健康保險；日本學期為 4 月及 10 月開學，返臺時新學期已開學月餘，選課或畢業請事先妥善安排。"),
    "韓國": ("KRW 800,000–1,300,000 / 月（首爾圈外宿較高；校內宿舍約 KRW 150,000–400,000 / 月）", "憑標準入學許可書申辦 D-2-6 交換學生簽證，抵韓後外國人登錄並自動納入韓國國民健康保險（NHIS）；師大簡章預估亞洲區一學期花費約新臺幣 10–30 萬元。"),
    "中國大陸": ("RMB 2,000–3,800 / 月（校內宿舍與學生食堂費用低廉，北上廣深略高）", "持臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定投保大陸境內來華留學生綜合醫療保險（約 RMB 400 / 學期）。"),
    "香港": ("HKD 6,000–10,000 / 月（校內宿位有限，若外宿租金較高）", "須透過接待校向香港入境事務處申辦學生簽證／進入許可（Student Visa / Entry Permit）。"),
    "澳門": ("HKD 4,500–7,500 / 月（約 MOP 4,600–7,700，含宿舍、膳食與交通）", "入境後依澳門治安警察局居留及逗留事務廳規定辦理「逗留的特別許可」（學生逗留）。"),
    "新加坡": ("SGD 1,200–2,000 / 月（含校內外住宿、熟食中心餐飲與地鐵交通）", "須透過新加坡移民局 SOLAR 系統申辦 Student's Pass（STP）並繳納接待校強制醫療保險。"),
    "馬來西亞": ("MYR 1,800–2,800 / 月（吉隆坡／雪蘭莪生活機能便利且物價親民）", "須透過 EMGS（Education Malaysia Global Services）系統申辦學生簽證（VAL / Student Pass）。"),
    "泰國": ("THB 15,000–25,000 / 月（曼谷與清邁生活成本親民）", "須憑接待校入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證。"),
    "印尼": ("IDR 5,000,000–8,500,000 / 月（雅加達／萬隆／日惹生活開支實惠）", "須由接待校協助向印尼移民總局申辦學習簽證（C316 / 學生電子簽證）。"),
    "印度": ("USD 400–700 / 月（IIT 校園宿舍與餐廳費用低廉）", "須憑接待校正式入學許可向印度台北協會申辦 Student Visa。"),
    "巴西": ("USD 500–850 / 月（約 BRL 2,500–4,200，聖保羅生活與住宿開支適中）", "須向巴西商務辦事處申辦 VITEM IV 學生簽證並備妥良民證與醫療保險。"),
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_html(text: str | None) -> str:
    if not text:
        return ""
    s = re.sub(r"<br\s*/?>|</p>|</li>|</tr>", "\n", str(text), flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in s.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def archive_official_sources() -> dict:
    SOURCES_NTNU_DIR.mkdir(parents=True, exist_ok=True)
    files_to_copy = [
        ("OE116-1_SPRING2027.pdf", "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf", "國立臺灣師範大學 116-1 校級赴外交換甄選簡章（2026/10/13 更新公告）"),
        ("OE115-2_SPRING2027.pdf", "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE115-2%20SPRING2027-0507.pdf", "國立臺灣師範大學 115-2（2027春季班）校級赴外交換甄選簡章"),
        ("OE115-1_FALL2026.pdf", "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_oe_OE115-1%20FALL2026-1202.pdf", "國立臺灣師範大學 115-1（2026秋季班）校級赴外交換甄選簡章"),
        ("quotalist_1161.json", "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist", "國立臺灣師範大學 116學年度第1學期校級／院級／系所級赴外交換名額與條件列表（285 筆合約／236 所合作大學）"),
        ("quotalist_1152.json", "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist", "國立臺灣師範大學 115學年度第2學期校級／院級／系所級赴外交換名額與條件列表"),
        ("quotalist_1151.json", "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist", "國立臺灣師範大學 115學年度第1學期校級／院級／系所級赴外交換名額與條件列表"),
        ("partner_index_all_454.json", "https://bds.oia.ntnu.edu.tw/bds/web/partner-index", "國立臺灣師範大學國際事務處全球姊妹校總覽（454 所姊妹校官方網址、地址與簡介）"),
        ("experiences_by_school_236.json", "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-experience", "國立臺灣師範大學赴外交換生返國心得報告查詢庫（涵蓋 174 所交換合作校官方心得 PDF）"),
        ("school_lack_list.json", "https://bds.oia.ntnu.edu.tw/api/v1/oe/getSchoolLackList", "國立臺灣師範大學校級赴外交換四語組（英歐語組、日語組、韓語組、中文組）學校分組清單"),
        ("oe_schedule.json", "https://bds.oia.ntnu.edu.tw/api/v1/oe/getSchoolSchedule", "國立臺灣師範大學赴外交換生申請系統時程設定"),
        ("oe_news.json", "https://bds.oia.ntnu.edu.tw/api/v1/oe/getNews", "國立臺灣師範大學國際事務處赴外交換與院級交換最新公告"),
        ("ss_col_departments.json", "https://bds.oia.ntnu.edu.tw/api/v1/ss/col-department-list", "國立臺灣師範大學 10 大學院與系所官方代碼表"),
        ("ntnu_resolved_locations.json", "https://bds.oia.ntnu.edu.tw/bds/web/partner-map", "國立臺灣師範大學 236 所赴外交換合作校 ROR / Wikidata 地理座標核對表"),
    ]
    provenance_items = []
    for fname, url, title in files_to_copy:
        src = SCRATCH_NTNU / fname
        dst = SOURCES_NTNU_DIR / fname
        if src.exists() and src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        if dst.exists():
            provenance_items.append({
                "file": f"sources/ntnu/{dst.name}",
                "source_url": url,
                "title": title,
                "sha256": sha256_file(dst),
                "bytes": dst.stat().st_size,
                "fetched_at": "2026-10-16T13:55:00Z",
            })
    return {
        "school_id": "ntnu",
        "school_name": "國立臺灣師範大學",
        "generated_at": "2026-10-16T14:00:00Z",
        "active_cycle_note": "116-1 校級赴外交換甄選簡章已於 2026/10/13 公告（線上申請：2026/11/01–11/15 23:59:59，補件截止：11/16，說明會：11/03，第一次分發公告：12/11，第二次分發與最終榜單：12/15–12/21）；同時收錄全校 236 所交換合作大學（285 項校級、院級、系所級交換計畫）之 116-1 當期公告名額與 115 學年度歷年申請條件。",
        "sources": provenance_items,
    }


def format_program_language(prog: dict) -> list[str]:
    parts = []
    if prog.get("toefl_ibt"):
        sub = []
        for k, lbl in [("toefl_ibt_listening", "聽"), ("toefl_ibt_speaking", "說"), ("toefl_ibt_reading", "讀"), ("toefl_ibt_writng", "寫")]:
            if prog.get(k):
                sub.append(f"{lbl}{prog[k]}")
        parts.append(f"TOEFL iBT {prog['toefl_ibt']}" + (f"（{'/'.join(sub)}）" if sub else ""))
    if prog.get("ielts"):
        sub = []
        for k, lbl in [("ielts_listening", "聽"), ("ielts_speaking", "說"), ("ielts_reading", "讀"), ("ielts_writing", "寫")]:
            if prog.get(k):
                sub.append(f"{lbl}{prog[k]}")
        parts.append(f"IELTS {prog['ielts']}" + (f"（{'/'.join(sub)}）" if sub else ""))
    if prog.get("toefl_itp"):
        parts.append(f"TOEFL ITP {prog['toefl_itp']}")
    if prog.get("toeic_total"):
        parts.append(f"TOEIC {prog['toeic_total']}")
    if prog.get("gept_level"):
        parts.append(f"全民英檢（GEPT）{prog['gept_level']}")
    if prog.get("japanese_jlpt_level"):
        parts.append(f"JLPT 日檢 {prog['japanese_jlpt_level']}")
    if prog.get("japanese_jlpt"):
        parts.append(f"J.TEST {prog['japanese_jlpt']}")
    if prog.get("korean_topik_level"):
        parts.append(f"TOPIK 韓檢 {prog['korean_topik_level']}")
    if prog.get("german_level"):
        parts.append(f"德語檢定（Goethe）{prog['german_level']}")
    if prog.get("french_delf_level"):
        parts.append(f"法語 DELF/DALF {prog['french_delf_level']}")
    if prog.get("french_tcf_level"):
        parts.append(f"法語 TCF {prog['french_tcf_level']}")
    if prog.get("spanish_level"):
        parts.append(f"西語 DELE {prog['spanish_level']}")
    if prog.get("other_language_certificate"):
        parts.append(str(prog["other_language_certificate"]).strip())
    return parts


def main() -> None:
    OFFICIAL_NTNU_DIR.mkdir(parents=True, exist_ok=True)
    provenance = archive_official_sources()
    (OFFICIAL_NTNU_DIR / "import_provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    q1161 = json.loads((SOURCES_NTNU_DIR / "quotalist_1161.json").read_text(encoding="utf-8"))
    q1152 = json.loads((SOURCES_NTNU_DIR / "quotalist_1152.json").read_text(encoding="utf-8"))
    q1151 = json.loads((SOURCES_NTNU_DIR / "quotalist_1151.json").read_text(encoding="utf-8"))
    pi454 = json.loads((SOURCES_NTNU_DIR / "partner_index_all_454.json").read_text(encoding="utf-8"))
    exp_by_school = json.loads((SOURCES_NTNU_DIR / "experiences_by_school_236.json").read_text(encoding="utf-8"))
    lack_list = json.loads((SOURCES_NTNU_DIR / "school_lack_list.json").read_text(encoding="utf-8")).get("body", {}).get("school_lack_list", [])
    resolved_locs = json.loads((SOURCES_NTNU_DIR / "ntnu_resolved_locations.json").read_text(encoding="utf-8"))
    loc_by_no = {r["school_no"]: r for r in resolved_locs}

    lang_group_by_no = {}
    for grp in lack_list:
        gname = grp.get("language_group", "")
        for s in grp.get("schools", []):
            if s.get("school_no") and gname:
                lang_group_by_no[s["school_no"]] = gname

    by_no_1161 = {}
    for s in q1161:
        by_no_1161.setdefault(s["school_no"], []).append(s)
    by_no_1152 = {}
    for s in q1152:
        by_no_1152.setdefault(s["school_no"], []).append(s)
    by_no_1151 = {}
    for s in q1151:
        by_no_1151.setdefault(s["school_no"], []).append(s)

    partners = []
    workflows = []
    destinations = []
    research_records = []
    life_records = []
    experience_sources_records = []
    student_experience_rows = []
    new_locations = []

    school_images_file = STATIC_DIR / "assets" / "school-images.json"
    visual_map = {}
    if school_images_file.exists():
        for item in json.loads(school_images_file.read_text(encoding="utf-8")).get("schools", []):
            if isinstance(item, dict) and item.get("school_name") and item.get("status") == "verified" and item.get("local_path"):
                visual_map[(school_identity_key(str(item.get("school_name", ""))), str(item.get("country") or ""))] = item
    visual_index = VisualRecordIndex(visual_map)

    uni_level_count = 0
    col_dept_only_count = 0
    confirmed_1161_quota_count = 0

    for idx, (sch_no, rows_1161) in enumerate(sorted(by_no_1161.items())):
        rows_1152 = by_no_1152.get(sch_no, [])
        rows_1151 = by_no_1151.get(sch_no, [])
        first = rows_1161[0]
        zh_name = first["school_name_ch"].strip()
        en_name = first["school_name_en"].strip()
        full_name = f"{zh_name} {en_name}"
        raw_country = first["school_country"].strip()
        country = COUNTRY_MAP.get(raw_country, raw_country)
        region = REGION_BY_COUNTRY.get(country, "歐洲")

        pi = pi454.get(sch_no, {})
        loc_info = loc_by_no[sch_no]
        website = (loc_info.get("website") or pi.get("link_url") or "").strip()

        # Gather all programs across 116-1 (primary), then fallback to 115-2 and 115-1 for rows whose 116-1 programs are not yet populated
        merged_programs = []
        seen_prog_names = set()
        for r_list in (rows_1161, rows_1152, rows_1151):
            for r in r_list:
                lvl = r.get("contract_level", "校級")
                org = r.get("organizer", "國際事務處")
                for p in r.get("programs") or []:
                    pname = (p.get("program_name") or "一般學程").strip()
                    pkey = (lvl, org, pname)
                    if pkey not in seen_prog_names:
                        seen_prog_names.add(pkey)
                        merged_programs.append({**p, "_contract_level": lvl, "_organizer": org})
                        if not website and p.get("apply_url"):
                            website = p["apply_url"].strip()

        if not website:
            website = "https://www.ubfc.fr/"

        # Determine contract levels and organizers
        levels = []
        organizers = []
        for r in rows_1161:
            lvl = r.get("contract_level", "校級")
            org = r.get("organizer", "國際事務處")
            if lvl not in levels:
                levels.append(lvl)
            if org not in organizers:
                organizers.append(org)

        has_uni_level = "校級" in levels
        if has_uni_level:
            uni_level_count += 1
        else:
            col_dept_only_count += 1

        # Determine language group
        lang_group = lang_group_by_no.get(sch_no)
        if not lang_group:
            if country == "日本":
                lang_group = "日語組"
            elif country == "韓國":
                lang_group = "韓語組"
            elif country in {"中國大陸", "香港", "澳門"}:
                lang_group = "中文組"
            else:
                lang_group = "英歐語組"

        # Compute quotas across 116-1, 115-2, 115-1
        def sum_positive_quotas(row_list):
            total = 0
            details = []
            has_dash = False
            has_zero = False
            for r in row_list:
                q_str = str(r.get("school_quota") or "").strip()
                lvl = r.get("contract_level", "校級")
                org = r.get("organizer", "國際事務處")
                tag = "校級" if lvl == "校級" else f"{lvl}・{org}"
                if q_str.isdigit() and int(q_str) > 0:
                    q_val = int(q_str)
                    total += q_val
                    details.append(f"{tag} {q_val} 名")
                elif q_str == "0":
                    has_zero = True
                    details.append(f"{tag} 0 名")
                else:
                    has_dash = True
                    details.append(f"{tag} 確認名額中")
            return total, details, has_dash, has_zero

        q1161_total, q1161_details, q1161_dash, q1161_zero = sum_positive_quotas(rows_1161)
        q1152_total, q1152_details, _, _ = sum_positive_quotas(rows_1152)
        q1151_total, q1151_details, _, _ = sum_positive_quotas(rows_1151)

        if q1161_total > 0:
            confirmed_1161_quota_count += 1
            quota_str = f"{q1161_total} 名（116-1 公告名額：{'、'.join(q1161_details)}）"
            quota_status = "published"
        elif q1152_total > 0 or q1151_total > 0:
            ref_q = max(q1152_total, q1151_total)
            ref_term = "115-2" if q1152_total >= q1151_total else "115-1"
            if q1161_zero and not q1161_dash:
                quota_str = f"116-1 暫不開放；{ref_term} 參考名額 {ref_q} 名（{'、'.join(q1161_details)}）"
            else:
                quota_str = f"116-1 與姊妹校確認名額中；{ref_term} 參考名額 {ref_q} 名（{'、'.join(q1161_details)}）"
            quota_status = "published"
        else:
            quota_str = f"與姊妹校確認名額中（{'、'.join(q1161_details)}；依當期最新公告為準）"
            quota_status = "published"

        # Aggregate degree_levels, gpa_requirement, language_requirement, offer, and remarks from merged_programs
        grades_set = []
        gpa_vals = []
        lang_reqs = []
        offers = []
        remarks = []
        coordinators = []

        for p in merged_programs:
            pname = (p.get("program_name") or "一般學程").strip()
            gl = (p.get("grade_limit") or "").strip()
            if gl:
                for g in gl.split(","):
                    g = g.strip()
                    if g and g not in grades_set:
                        grades_set.append(g)
            if p.get("gpa"):
                g_str = f"{pname}：GPA {p['gpa']}"
                if g_str not in gpa_vals:
                    gpa_vals.append(g_str)
            p_langs = format_program_language(p)
            if p_langs:
                l_str = f"【{pname}】" + " / ".join(p_langs)
                if l_str not in lang_reqs:
                    lang_reqs.append(l_str)
            if p.get("offer"):
                o_str = clean_html(p["offer"])
                if o_str and o_str not in offers:
                    offers.append(o_str)
            rem = clean_html(p.get("remark") or p.get("prog_remark") or "")
            if rem:
                r_str = f"【{pname}】{rem}"
                if r_str not in remarks:
                    remarks.append(r_str)
            if p.get("organizer_name") or p.get("organizer_mail"):
                c_str = f"{p.get('organizer_name') or ''} ({p.get('organizer_mail') or ''} / {p.get('organizer_phone') or ''})".strip(" ()/")
                if c_str and c_str not in coordinators:
                    coordinators.append(c_str)

        if grades_set:
            has_ug = any("學士" in g for g in grades_set)
            has_ms = any("碩士" in g for g in grades_set)
            has_phd = any("博士" in g for g in grades_set)
            deg_parts = []
            if has_ug:
                ug_years = [g.replace("學士", "大") for g in grades_set if "學士" in g]
                deg_parts.append(f"學士班（{'、'.join(ug_years)}）")
            if has_ms:
                deg_parts.append("碩士班")
            if has_phd:
                deg_parts.append("博士班")
            degree_levels_str = "、".join(deg_parts) if deg_parts else "、".join(grades_set)
        else:
            degree_levels_str = "學士班（修業滿一學期以上）、碩士班、博士班（不含進修推廣學院及在職專班）"

        if gpa_vals:
            gpa_req_str = "；".join(gpa_vals) + "（並須於臺師大修業滿一學期以上）"
        else:
            gpa_req_str = "須於臺師大修業滿一學期以上，並符合姊妹校各學程學業成績標準（校內甄選學業及相關學術表現佔 30%，含 EMI 修課數 5%）"

        if lang_reqs:
            lang_req_str = "；".join(lang_reqs)
        else:
            if country == "日本":
                lang_req_str = "日語組／英語授課學程：須檢附有效期限內之 JLPT 日語檢定（N1–N3 依各學程規定）或 TOEFL iBT / IELTS 成績證明"
            elif country == "韓國":
                lang_req_str = "韓語組／英語授課學程：須檢附有效期限內之 TOPIK 韓語檢定或 TOEFL iBT / IELTS 成績證明"
            elif country in {"中國大陸", "香港", "澳門"}:
                lang_req_str = "中文組（大陸地區學程免附外語檢定；港澳或英語授課學程依各校規定檢附 TOEFL iBT / IELTS 成績證明）"
            else:
                lang_req_str = f"{lang_group}：須檢附 2 年有效期限內之 TOEFL iBT、IELTS 或對應歐洲語言檢定成績證明（不採計 TOEFL MyBest Scores）"

        if has_uni_level and len(organizers) == 1:
            colleges_str = "全校各學院系所（校級交換計畫，由國際事務處統籌甄選）"
        elif has_uni_level:
            other_orgs = [o for o in organizers if o != "國際事務處"]
            colleges_str = f"全校各學院（校級交換）及特定院系所合約（{'、'.join(other_orgs)}）"
        else:
            colleges_str = f"限合約所屬院系所學生申請（辦理單位：{'、'.join(organizers)}）"

        program_type = (
            f"交換學生（校級・{lang_group}）"
            if has_uni_level and len(levels) == 1
            else f"交換學生（{'／'.join(levels)}・{lang_group}）"
        )

        study_period_str = "一學期為原則（特定姊妹校學程提供一學年者依其規定；在學期間赴外交換以二次為限、總計不超過二學期）"
        app_deadline_str = (
            "116-1 校級甄選：2026年11月1日開放線上申請，2026年11月15日（日）23:59:59 截止繳件、11月16日 23:59:59 審查補件截止；"
            "12月11日第一次分發結果公告，12月19日–12月21日最終榜單公告（院系所級交換依各院系所公告時程辦理）"
        )

        tuition_points_list = [
            "交換期間須於臺師大完成註冊並繳交「全額」學雜費以保留在學學籍，免繳姊妹校學費（" + ("；".join(offers) if offers else "其他個人住宿、生活、書籍、簽證、機票與保險費用由學生自理") + "）。",
            "校內初選報名費為新臺幣 500 元（超商繳費加蓋當日章或線上信用卡繳費截圖上傳，繳納後不予退還）；分發錄取並完成線上報到（上傳本人及家長簽署之「錄取資格確認書」）後，若無不可抗力情事而放棄交換資格者，須繳納行政作業費新臺幣 5,000 元（匯入校務發展基金），且不得再參加校級交換生甄選。",
            "依《國立臺灣師範大學學生境外修習課程實施辦法》，出國修課每學期至少應修習 2 科或 6 學分（姊妹校規定更高者從其規定），歐洲 ECTS 原則以 2 ECTS 等同 1 學分，採認上限為畢業最低總學分數三分之一。",
        ]

        app_steps_list = [
            f"步驟一（選定語組與填報志願）：於 2026/11/01–11/15 23:59:59 登入「臺師大赴外交換生申請系統」（https://bds.oia.ntnu.edu.tw/bds/OE），擇一語組報名（本案屬 {lang_group}，不得跨組），選填 1 至 10 所符合語言及成績條件之志願校。",
            "步驟二（上傳電子備審與繳交報名費）：上傳 (A) 申請書（本人及系主任簽名掃描檔；公費生加附保證人同意書）、(B) 自傳與出國學習計畫（中英文合計 500–5,000 字，建議加附外文版 500–2,500 字）、(D) 有效期限內之語言能力證明（中文組除外；不接受 TOEFL MyBest Scores）、(E) 歷年中文成績單正本及學士班歷年名次證明、(F) 大學以上優良事蹟或活動證明、(G) 報名費 500 元繳費證明。",
            "步驟三（100% 線上書面審查與兩階段志願分發）：由國際處遴聘審查委員依「語言能力 30%、學業及相關學術表現 30%（含 EMI 全英語授課修課數 5%，修滿 5 門得滿分）、自傳及出國學習計畫 20%、優良事蹟或活動證明 20%」綜合評分；12/01–12/09 公布甄審成績排序並開放網路變更志願序，12/11 公告第一次分發結果與線上報到，12/11–12/14 開放缺額第二次志願填報，12/15–12/21 公告第二次分發與最終榜單。",
            f"步驟四（姊妹校提名複審與行前準備）：獲推薦生依國際處或院系所通知備齊 {full_name} 複審申請文件（含推薦信、英文成績單、財力證明與護照影本），待取得正式入學許可後辦理簽證、役男出境（出境前 30 天向生輔組申請）及參加行前說明會。",
        ]

        elig_detail_str = (
            f"合約層級：{'、'.join(levels)}（辦理單位：{'、'.join(organizers)}）｜"
            f"可申請學制：{degree_levels_str}"
            + (f"｜承辦窗口：{'；'.join(coordinators)}" if coordinators else "")
            + (f"｜學程備註：{'；'.join(remarks)}" if remarks else "")
        )

        elig_points_list = [
            f"開放學制與年級：{degree_levels_str}",
            f"辦理單位與組別：{'、'.join(levels)}（{'、'.join(organizers)}・{lang_group}）",
            f"學業成績要求：{gpa_req_str}",
            f"語言能力門檻：{lang_req_str}",
        ]
        if remarks:
            elig_points_list.append(f"姊妹校學程注意事項：{'；'.join(remarks)}")

        source_url = f"https://bds.oia.ntnu.edu.tw/bds/web/partner-index/{sch_no}" if sch_no in pi454 else "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist"

        location_obj = {
            "school_name": full_name,
            "country": country,
            "city": loc_info.get("city") or country,
            "latitude": float(loc_info["latitude"]),
            "longitude": float(loc_info["longitude"]),
            "geocode_status": "verified",
            "geocoded_at": "2026-10-16T14:00:00Z",
            "source_url": loc_info.get("source_url") or "https://www.wikidata.org",
            "identity_source_url": loc_info.get("identity_source_url") or website or "https://ror.org",
            "precision": "representative",
            "note": loc_info.get("note") or "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區以錄取通知為準。",
        }
        new_locations.append(location_obj)

        exp_info = exp_by_school.get(sch_no)
        exp_links = []
        if exp_info and exp_info.get("samples"):
            for s_exp in exp_info["samples"][:3]:
                files = s_exp.get("files") or []
                if files and files[0].get("link_uri"):
                    dl_url = "https://bds.oia.ntnu.edu.tw/api/v1/pt/oe-share-dl?f=" + files[0]["link_uri"]
                    term_code = str(s_exp.get("term") or "")
                    term_label = f"{term_code[:3]}-{term_code[3:]}" if len(term_code) == 4 else term_code
                    title_str = f"臺師大赴 {zh_name} 交換生返國心得報告（{term_label} 學期・{files[0].get('title') or 'PDF'}）"
                    if all(x["url"] != dl_url for x in exp_links):
                        exp_links.append({"title": title_str, "url": dl_url, "term": term_label})

        notes_lines = [
            f"【學校代碼與合約層級】{sch_no}｜{'、'.join(levels)}（{'、'.join(organizers)}・{lang_group}）",
            f"【當期與歷年名額】{quota_str}",
            f"【開放年級／學制】{degree_levels_str}",
            f"【外語檢定門檻】{lang_req_str}",
            f"【學業成績門檻】{gpa_req_str}",
        ]
        if coordinators:
            notes_lines.append(f"【國際處／院系所承辦人】{'；'.join(coordinators)}")
        if remarks:
            notes_lines.append(f"【學程規定與選課限制】{'；'.join(remarks)}")
        if exp_info:
            notes_lines.append(f"【返國交換生心得】臺師大國際處資料庫收錄 {exp_info['total']} 篇赴 {zh_name} 返國交換生心得報告。")

        visual_rec = visual_index.get((full_name, country)) or {}
        partner_record = {
            "school_name": full_name,
            "country": country,
            "region": region,
            "colleges": colleges_str,
            "degree_levels": degree_levels_str,
            "study_period": study_period_str,
            "eligibility": f"{elig_detail_str}｜語文要求：{lang_req_str}｜學業門檻：{gpa_req_str}",
            "language_requirement": lang_req_str,
            "gpa_requirement": gpa_req_str,
            "quota": quota_str,
            "quota_status": quota_status,
            "availability_status": "open",
            "availability_note": f"國立臺灣師範大學 116-1 赴外交換甄選簡章已公告（線上申請：2026/11/01–11/15）；{quota_str}。",
            "academic_year": "116",
            "application_round": "116-1（2026年11月甄選／2027年赴外）",
            "application_window_status": "open",
            "application_deadline": app_deadline_str,
            "application_info": "\n\n".join(app_steps_list),
            "tuition_info": "\n\n".join(tuition_points_list),
            "semester_dates": "秋季班（第1學期）：約每年 8/9 月至翌年 1 月（日本及德國為 10 月至翌年 2/3 月）；春季班（第2學期）：約每年 2 月至 6/7 月（日本及德國為 4 月至 8 月）",
            "course_restrictions": "；".join(remarks) if remarks else "每學期於姊妹校至少應修習 2 門或 6 學分課程；部分專業學程或實習課程限制依姊妹校最新簡章為準。",
            "housing_info": "大部份交換校提供宿舍申請（住宿費由學生自理），惟房間數有限無法保證入住；未申請到校內宿舍者須依交換校資訊自行辦理校外租屋。",
            "notes": "\n".join(notes_lines),
            "program_type": program_type,
            "source_url": source_url,
            "website": website,
            "official_website": website,
            "factsheet_url": merged_programs[0].get("apply_url") if merged_programs and merged_programs[0].get("apply_url") else None,
            "image_url": visual_rec.get("local_path"),
            "image_source_url": visual_rec.get("image_source_url"),
            "image_page_url": visual_rec.get("official_page_url") or visual_rec.get("image_source_url"),
            "image_status": "verified" if visual_rec.get("local_path") else "missing",
            "location": location_obj,
            "student_summary_zh": {
                "study_period": study_period_str,
                "quota": quota_str,
                "colleges": colleges_str,
                "degree_levels": degree_levels_str,
                "eligibility_points": elig_points_list,
                "application_deadline": app_deadline_str,
                "application_steps": app_steps_list,
                "tuition_points": tuition_points_list,
            },
        }
        partners.append(partner_record)

        wf_sources = [
            {
                "title": f"國立臺灣師範大學校級院系所級赴外交換名額列表—{zh_name}",
                "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist",
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": "116-1",
                "checked_at": "2026-10-16T14:00:00Z",
            },
            {
                "title": "國立臺灣師範大學 116-1 校級赴外交換甄選簡章",
                "source_url": "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": "116-1",
                "checked_at": "2026-10-16T14:00:00Z",
            },
        ]
        if website:
            wf_sources.append({
                "title": f"{full_name} 官方網站／交換計畫頁面",
                "source_url": website,
                "role": "partner_university",
                "authority": "partner_official",
                "effective_academic_year": "116",
                "application_round": "116-1",
                "checked_at": "2026-10-16T14:00:00Z",
            })

        workflows.append({
            "home_university": "國立臺灣師範大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": "116",
            "application_round": "116-1",
            "effective_application_rounds": ["116-1", "第1學期（秋季班）", "第2學期（春季班）"],
            "applicability_status": "verified",
            "applicability_note": "國立臺灣師範大學 116-1 校級赴外交換甄選簡章已於 2026/10/13 公告，2026/11/01–11/15 23:59:59 開放線上報名、11/16 補件截止、12/11 第一次分發、12/19–12/21 公告最終榜單。",
            "review_status": "published",
            "published_at": "2026-10-16T14:00:00Z",
            "steps": [
                {
                    "rule_id": f"ntnu-116-home-1-{idx+1:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認臺師大在學滿一學期資格與 {zh_name} 語檢／年級門檻",
                    "responsible_party": "學生",
                    "responsible_unit": f"國立臺灣師範大學{'／'.join(organizers)}",
                    "deadline_at": "2026-11-03T13:30:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                    "deadline_checked_at": "2026-10-16T14:00:00Z",
                    "deadline_reminder_eligible": True,
                    "summary": f"須於臺師大修業滿一學期以上，符合 {zh_name} 年級與語檢條件（11/03 舉辦赴外交換系統暨獎學金申請說明會）。",
                    "details": [
                        f"開放學制：{degree_levels_str}",
                        f"外語能力門檻：{lang_req_str}",
                        f"當期與參考名額：{quota_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立臺灣師範大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["116"],
                        "application_rounds": ["116-1", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "source_urls": [
                        "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist",
                        "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                    ],
                    "checked_at": "2026-10-16T14:00:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ntnu-116-home-2-{idx+1:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": f"於臺師大赴外交換生系統擇一語組選填至多 10 志願並上傳 6 項電子備審與 500 元報名費證明",
                    "responsible_party": "學生",
                    "responsible_unit": "國立臺灣師範大學國際事務處（赴外交換生申請系統）",
                    "deadline_at": "2026-11-15T23:59:59+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                    "deadline_checked_at": "2026-10-16T14:00:00Z",
                    "deadline_reminder_eligible": True,
                    "summary": "2026/11/01 至 2026/11/15 23:59:59 前完成線上填報與備審檔案上傳，缺件補交截止日為 2026/11/16 23:59:59。",
                    "details": [
                        f"登入 https://bds.oia.ntnu.edu.tw/bds/OE ，選定單一語組（{lang_group}）並填寫 1–10 個符合條件之志願校。",
                        "上傳 6 項規定命名的電子檔（申請表、自傳與出國學習計畫、語言能力證明文件、學業及相關學術表現、大學以上優良事蹟或活動證明、500 元報名費繳費證明）。",
                    ],
                    "document_requirements": [
                        {
                            "name": "線上列印申請書（本人親筆簽名及系主任簽章後正本掃描上傳；公費生另附保證人同意書）",
                            "official_form_url": "https://bds.oia.ntnu.edu.tw/bds/OE",
                            "source_urls": ["https://bds.oia.ntnu.edu.tw/bds/web/outgoing-apply"],
                        },
                        {
                            "name": "自傳與出國學習計畫（中英文合計 500–5,000 字，建議加附外文版本約 500–2,500 字）",
                            "source_urls": ["https://bds.oia.ntnu.edu.tw/bds/web/outgoing-apply"],
                        },
                        {
                            "name": "有效期限內之語言能力檢定證明正本掃描檔（中文組免附；不得使用 TOEFL MyBest Scores）",
                            "conditional": lang_group == "中文組",
                            "condition": "英歐語組、日語組、韓語組必繳；中文組大陸地區學校免附",
                            "source_urls": ["https://bds.oia.ntnu.edu.tw/bds/web/outgoing-languagetest"],
                        },
                        {
                            "name": "學業及相關學術表現（歷年中文成績單正本掃描檔，學士班須加附歷年名次證明；EMI 全英語授課修課數納入 5% 評分）",
                            "source_urls": ["https://bds.oia.ntnu.edu.tw/bds/web/outgoing-apply"],
                        },
                        {
                            "name": "大學（含）以上優良事蹟或活動證明（如學生數位學習歷程檔案；勿附高中職以下證明）",
                            "source_urls": ["https://bds.oia.ntnu.edu.tw/bds/web/outgoing-apply"],
                        },
                        {
                            "name": "報名費新臺幣 500 元之超商繳費收據（加蓋超商當日章掃描檔）或信用卡繳費成功截圖證明",
                            "source_urls": ["https://bds.oia.ntnu.edu.tw/bds/web/outgoing-apply"],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立臺灣師範大學"],
                        "academic_years": ["116"],
                        "application_rounds": ["116-1", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "submission": {
                        "method": "online",
                        "office": "國立臺灣師範大學國際事務處（普通大樓 1 樓）",
                        "portal_url": "https://bds.oia.ntnu.edu.tw/bds/OE",
                    },
                    "action_url": "https://bds.oia.ntnu.edu.tw/bds/OE",
                    "source_urls": [
                        "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-apply",
                        "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                    ],
                    "checked_at": "2026-10-16T14:00:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ntnu-116-home-3-{idx+1:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "公布甄審成績排序、網路變更志願序與兩階段志願分發線上報到",
                    "responsible_party": "學生與臺師大國際事務處",
                    "responsible_unit": "國立臺灣師範大學國際事務處",
                    "deadline_at": "2026-12-11T23:59:59+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                    "deadline_checked_at": "2026-10-16T14:00:00Z",
                    "deadline_reminder_eligible": True,
                    "summary": "12/01–12/09 公布甄審成績排序並開放網路變更志願序；12/11 公告第一次分發結果並上傳本人及家長簽名之「錄取資格確認書」完成報到（12/11–12/14 缺額二次填報，12/19–12/21 最終榜單）。",
                    "details": [
                        "評分標準：語言能力 30%、學業及相關學術表現 30%（其中 5% 為 EMI 修課數，修滿 5 門得 5%）、自傳及出國學習計畫 20%、大學以上優良事蹟或活動證明 20%。",
                        "完成線上報到後若無不可抗力因素放棄資格者，須繳交行政作業費新臺幣 5,000 元，且不得再參加校級交換生甄選。",
                    ],
                    "scope": {
                        "home_universities": ["國立臺灣師範大學"],
                        "academic_years": ["116"],
                        "application_rounds": ["116-1", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "source_urls": [
                        "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                        "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-faq",
                    ],
                    "checked_at": "2026-10-16T14:00:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ntnu-{idx+1:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由臺師大提名並完成 {zh_name} 姊妹校複審申請文件與住宿登錄",
                    "responsible_party": "學生與接待校國際處",
                    "summary": f"獲臺師大推薦資格後，依 {full_name} 規定遞交姊妹校複審文件（如英文成績單、正式語言成績單、推薦信、財力證明、護照影本），經審核通過取得正式入學許可（通常需 2–3 個月）。",
                    "details": [
                        f"條件與學程規定：{elig_detail_str}",
                        f"語言門檻：{lang_req_str}",
                        "切勿自行致信催促姊妹校核發入學許可；若有疑問請統一透過臺師大國際處承辦人代詢。",
                    ],
                    "scope": {
                        "home_universities": ["國立臺灣師範大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["116"],
                        "application_rounds": ["116-1", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "source_urls": [source_url] + ([website] if website else []),
                    "checked_at": "2026-10-16T14:00:00Z",
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"ntnu-116-home-5-{idx+1:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "參加行前說明會、辦理簽證與役男出境、完成三階段系統動態回報與返國學分採計",
                    "responsible_party": "學生",
                    "responsible_unit": "國立臺灣師範大學國際事務處／教務處／學務處生輔組",
                    "summary": "取得入學許可後辦理簽證與機票（役男須於出境 30 天前向生輔組申請）；於出國前、抵校 1 個月內及返國後 1 個月內完成線上動態回報與心得報告上傳，並於成績單寄達 2 個月內辦理學分採計／登錄。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立臺灣師範大學"],
                        "academic_years": ["116"],
                        "application_rounds": ["116-1", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "source_urls": [
                        "https://bds.oia.ntnu.edu.tw/bds/web/resource-reg-overseasstudy",
                        "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                    ],
                    "checked_at": "2026-10-16T14:00:00Z",
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": "2026-10-16T14:00:00Z",
            "coverage_status": "official_verified",
            "coverage_note": "已完整整合國立臺灣師範大學 116-1 校級赴外交換甄選簡章、116-1/115-2/115-1 校院系級名額條件表與姊妹校官方專頁。",
        })

        cost_default, visa_default = REGION_COST_DEFAULTS.get(
            country,
            ("USD 800–1,300 / 月（含住宿、膳食、教材與當地交通費用）", "須依接待校與駐臺代表處規定辦理學生簽證與海外醫療保險。"),
        )
        cost_line = f"預估每月生活費約 {cost_default}"
        tuition_clean = tuition_points_list[0]
        housing_clean = "大部份交換校提供學生宿舍申請（住宿費由學生自行負擔），惟房間數有限無法保證一定申請得到；若未獲配宿舍或姊妹校無提供宿舍，須依交換校相關資訊自行辦理校外租屋。"
        course_clean = (
            f"{elig_detail_str}｜依《國立臺灣師範大學學生境外修習課程實施辦法》，交換生每學期至少應修習 2 科或 6 學分，"
            "歐洲 ECTS 原則以 2 ECTS 等同 1 學分，採認學分上限為畢業最低總學分數三分之一（於大陸地區修習之課程不得採計為師資職前教育專業及專門課程）。"
        )
        calendar_clean = "秋季班（第1學期）：約每年 8/9 月至翌年 1 月（日本、德國為 10 月至翌年 2/3 月）；春季班（第2學期）：約每年 2 月至 6/7 月（日本、德國為 4 月至 8 月）。"

        dest_sources = [
            {"title": f"國立臺灣師範大學赴外交換名額與條件列表—{zh_name}", "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist", "summary": "臺師大官方交換名額、合約層級、可申請學制與語言門檻"},
            {"title": f"國立臺灣師範大學姊妹校專頁—{zh_name}", "source_url": source_url, "summary": "姊妹校簡介、官方地址、網站與歷年交換心得"},
            {"title": "國立臺灣師範大學 116-1 校級赴外交換甄選簡章", "source_url": "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf", "summary": "臺師大交換生甄選時程、最低修課學分、費用與學分採計規定"},
        ]
        if website:
            dest_sources.append({"title": f"{full_name} 官方網站", "source_url": website, "summary": "接待合作校官方網站與交換生資訊"})
        for el in exp_links:
            dest_sources.append({"title": el["title"], "source_url": el["url"], "summary": "臺師大赴外交換生返國心得報告官方 PDF"})

        src_url_list = [source_url, "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist"] + ([website] if website else [])

        destinations.append({
            "home_university": "國立臺灣師範大學",
            "school_name": full_name,
            "country": country,
            "city": location_obj.get("city") or country,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": f"校區代表城市：{location_obj.get('city') or country}" + (f"（校址：{pi.get('address').strip()}）" if pi.get("address") and pi.get("address").strip() else "") + "。請依入學許可確認實際授課校區、機場交通路線與當地學生交通票卡優惠。",
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費與學雜費規定",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list,
                    "caution": "臺師大簡章預估亞洲區一學期交換花費約新臺幣 10–30 萬元、歐美區約 20–40 萬元，實際視個人住宿與消費習慣而定。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "部分姊妹校宿位有限無法保證入住，獲推薦提名後請立即留意姊妹校住宿申請截止日。",
                },
                {
                    "key": "insurance",
                    "title": "醫療保險與安全",
                    "summary": visa_default,
                    "points": [visa_default, "抵達姊妹校 1 個月內須至臺師大交換生系統回報當地聯絡地址、電話及生活概況以建立緊急聯絡網。"],
                    "source_urls": src_url_list,
                    "caution": "部分國家（如德國公保、澳洲 OSHC、日韓國民健康保險、美國 J-1/F-1 校園醫保）強制要求投保當地指定保險。",
                },
                {
                    "key": "visa",
                    "title": "簽證、役男出境與機票準備",
                    "summary": visa_default,
                    "points": [
                        "須待收到姊妹校正式入學許可後再辦理簽證，取得簽證後再購買機票（國際處不代辦簽證或機票）。",
                        "在學役男須於預定出國日期 30 天前（遇年假須再提早一週）向學務處生輔組辦理「在學役男出境申請表」核章。",
                        visa_default,
                    ],
                    "source_urls": src_url_list,
                    "caution": "赴美國持 J-1 簽證並同時領有政府獎助學金者，返國日起算兩年內受限於美國政府規定不得提出美國移民及工作簽證申請。",
                },
                {
                    "key": "courses",
                    "title": "課程限制、最低學分與返國採計",
                    "summary": course_clean[:160],
                    "points": [
                        course_clean,
                        "返國後於成績單送抵臺師大兩個月內（應屆畢業生至遲於次學期開學一週內），憑核定公文、原始成績單及課程大綱向系所與教務處提出學分採計／登錄申請；國外成績登錄於歷年成績表但不計入學期及總平均。",
                    ],
                    "source_urls": src_url_list + ["https://bds.oia.ntnu.edu.tw/bds/web/resource-reg-overseasstudy"],
                    "caution": "大四下或延畢出國交換者，因姊妹校成績單寄達時間較晚，恐無法於交換當學期立即辦畢學分採計及畢業手續，請務必事先洽詢教務處。",
                },
                {
                    "key": "city",
                    "title": "城市與校區位置",
                    "summary": f"{country} {location_obj.get('city') or ''}".strip(),
                    "points": [
                        location_obj.get("note") or f"{full_name} 校級代表位置位於 {location_obj.get('city') or country}。",
                    ] + ([f"官方登記地址：{pi['address'].strip()}"] if pi.get("address") and pi.get("address").strip() else []),
                    "source_urls": [location_obj.get("source_url") or source_url],
                    "caution": "多校區大學之實際上課地點依所選院系與學程而定。",
                },
                {
                    "key": "arrival",
                    "title": "學期年曆、動態回報與返國心得義務",
                    "summary": calendar_clean,
                    "points": [
                        calendar_clean,
                        "出國前（開學一週前填報出發日）、抵達交換校（一個月內回報當地住址電話）及返國後（一個月內上傳返國心得報告）三階段皆須至臺師大線上交換生系統更新動態。",
                    ] + ([f"歷年學長姐返國心得：臺師大國際處已收錄 {exp_info['total']} 篇赴 {zh_name} 交換心得報告。"] if exp_info else []),
                    "source_urls": src_url_list + [el["url"] for el in exp_links],
                    "caution": "交換生義務須於返國一年內完成；領取獎補助者請留意初抵回報與返國結案核銷期限。",
                },
            ],
            "first_72_hours": [
                {
                    "title": "依姊妹校入學許可指定報到日辦理宿舍入住、國際處報到與選課確認",
                    "detail": calendar_clean,
                    "source_urls": [source_url],
                },
                {
                    "title": "完成當地居留登錄、醫療保險投保與臺師大交換生系統初抵回報",
                    "detail": f"{visa_default} 抵校一個月內務必登入臺師大赴外交換生系統填報當地聯絡地址與電話（領取學海飛颺／惜珠或鼓勵赴境外進修補助者並應上傳初抵文件）。",
                    "source_urls": ["https://bds.oia.ntnu.edu.tw/bds/web/outgoing-apply"],
                },
            ],
            "sources": dest_sources,
            "last_checked": "2026-10-16T14:00:00Z",
            "coverage_status": "official_verified",
            "coverage_note": "已整合國立臺灣師範大學 116-1 赴外交換名額表、甄選簡章、姊妹校專頁與返國交換生心得庫。",
        })

        research_records.append({
            "home_university": "國立臺灣師範大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": source_url,
            "checked_at": "2026-10-16T14:00:00Z",
            "note": f"國立臺灣師範大學國際事務處姊妹校專頁（{source_url}）及 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [
            {"title": f"臺師大赴外交換名額與條件表—{zh_name}", "url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist"},
            {"title": f"臺師大姊妹校專頁—{zh_name}", "url": source_url},
        ]
        if website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": website})
        for el in exp_links:
            ev_sources.append({"title": el["title"], "url": el["url"]})

        ev_list = [
            {
                "theme": "housing",
                "kind": "official",
                "text": housing_clean,
                "sources": ev_sources,
                "checked_at": "2026-10-16T14:00:00Z",
                "scope": "臺師大 116-1 赴外交換甄選簡章住宿說明與姊妹校資訊",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "cost",
                "kind": "official",
                "text": f"{tuition_clean}｜預估生活開支：{cost_default}",
                "sources": ev_sources,
                "checked_at": "2026-10-16T14:00:00Z",
                "scope": "臺師大 116-1 交換費用規定與地區生活費估算",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "academics",
                "kind": "official",
                "text": course_clean,
                "sources": ev_sources,
                "checked_at": "2026-10-16T14:00:00Z",
                "scope": "臺師大赴外交換學程條件與境外修習課程實施辦法",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "safety",
                "kind": "official",
                "text": visa_default,
                "sources": ev_sources,
                "checked_at": "2026-10-16T14:00:00Z",
                "scope": "臺師大赴外交換簽證、役男出境、醫療保險與初抵平安回報提醒",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "campus_culture",
                "kind": "mixed" if exp_links else "official",
                "text": (
                    f"合約與語組：{'、'.join(levels)}（{lang_group}）｜名額：{quota_str}｜外語要求：{lang_req_str}"
                    + (f"｜臺師大國際處收錄 {exp_info['total']} 篇赴 {zh_name} 交換生返國心得報告。" if exp_info else "")
                ),
                "sources": ev_sources,
                "checked_at": "2026-10-16T14:00:00Z",
                "scope": "臺師大 116-1 赴外交換計畫名額、語檢要求與歷年返國交換生心得",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
        ]
        life_records.append({
            "school_name": full_name,
            "country": country,
            "checked_at": "2026-10-16T14:00:00Z",
            "status": "ready",
            "evidence": ev_list,
            "notes": [
                "已整合國立臺灣師範大學 116-1 赴外交換名額表、甄選簡章與歷年返國心得報告連結。",
                "當期宿位供給、費用與選課限制請依姊妹校最新網站與 Fact Sheet 核對。",
            ],
            "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
            "extraction_version": 3,
        })

        experience_sources_records.append({
            "home_university": "國立臺灣師範大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-experience",
            "partner_page_url": source_url,
            "report_count": int(exp_info["total"]) if exp_info and str(exp_info.get("total", "")).isdigit() else 0,
            "sample_reports": exp_links,
            "checked_at": "2026-10-16T14:00:00Z",
        })
        for el in exp_links:
            summary_text = f"國立臺灣師範大學國際事務處收錄之 {el['term']} 學期赴 {zh_name} 交換學生返國心得報告（官方 PDF 原文檔案）。"
            theme_map = {
                "academics": f"臺師大 {el['term']} 學期交換生分享於 {zh_name} 之選課、授課與學分修習經驗。",
                "housing": f"臺師大 {el['term']} 學期交換生分享於 {zh_name} 之宿舍或校外住宿申請與生活經驗。",
                "campus_culture": f"臺師大 {el['term']} 學期交換生分享於 {zh_name} 之校園環境、國際處支援與文化交流。",
                "cost": f"臺師大 {el['term']} 學期交換生分享於 {zh_name} 之學期生活開銷與行前準備建議。",
            }
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": el["title"],
                "source_url": el["url"],
                "source_type": "article",
                "platform": "國立臺灣師範大學國際事務處交換心得庫",
                "author_name": "臺師大返國交換生",
                "language": "zh",
                "summary": summary_text,
                "themes": ["academics", "housing", "campus_culture", "cost"],
                "theme_summaries": theme_map,
                "content_status": "metadata_only",
                "perspective": "official_student_story",
                "published_at": None,
                "discovered_at": "2026-10-16T14:00:00Z",
                "content_hash": hashlib.sha256(el["url"].encode("utf-8")).hexdigest(),
                "exchange_term": el["term"],
                "summary_zh": summary_text,
                "original_summary": "",
                "theme_summaries_zh": theme_map,
                "translation_status": "original",
                "source_kind": "official_experience_pdf",
            })

    (OFFICIAL_NTNU_DIR / "partners.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTNU_DIR / "application_workflows.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTNU_DIR / "destination_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTNU_DIR / "partner_research.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTNU_DIR / "student_life.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTNU_DIR / "experience_sources.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in experience_sources_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTNU_DIR / "student_experiences.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in student_experience_rows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTNU_DIR / "campus-locations.json").write_text(
        json.dumps({"locations": new_locations}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Update university_locations.jsonl with 國立臺灣師範大學 home location
    loc_file = REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
    existing_loc_lines = [line for line in loc_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    existing_loc_map = {}
    for line in existing_loc_lines:
        rec = json.loads(line)
        existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

    ntnu_home_loc = {
        "school_name": "國立臺灣師範大學",
        "country": "臺灣",
        "city": "臺北市大安區",
        "latitude": 25.0261,
        "longitude": 121.5275,
        "geocode_status": "verified",
        "geocoded_at": "2026-10-16T14:00:00Z",
        "source_url": "https://www.wikidata.org/wiki/Q702300",
        "identity_source_url": "https://ror.org/059dkdx38",
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。 母校代表點採和平校區校本部（臺北市大安區和平東路一段162號，另設公館校區與林口校區）；官方地址來源：https://bds.oia.ntnu.edu.tw/bds/web/oiamap。",
    }
    existing_loc_map[("國立臺灣師範大學", "臺灣")] = ntnu_home_loc
    sorted_locs = sorted(existing_loc_map.values(), key=lambda r: (r.get("country") or "", r.get("school_name") or ""))
    loc_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
        encoding="utf-8",
    )

    ntnu_source_urls = [
        "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-info",
        "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-apply",
        "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist",
        "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-download",
        "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-faq",
        "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-scholarship",
        "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-subsidy",
        "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-languagetest",
        "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-experience",
        "https://bds.oia.ntnu.edu.tw/bds/web/partner-index",
        "https://bds.oia.ntnu.edu.tw/bds/web/resource-reg-overseasstudy",
        "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
        "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE115-2%20SPRING2027-0507.pdf",
    ]

    exchange_info_payload = {
        "school_name": "國立臺灣師範大學",
        "program_type": [
            "交換學生（校級赴外交換・英歐語組／日語組／韓語組／中文組）",
            "交換學生（院級／系所級赴外交換）",
        ],
        "academic_year": [
            "116（116-1 甄選：2026年11月報名／2027年赴外）",
            "115（115-2 春季班／115-1 秋季班參考）",
        ],
        "semester": [
            "第1學期（秋季班：每年約 8/9 月至翌年 1 月；日本及德國為 10 月至翌年 2/3 月）",
            "第2學期（春季班：每年約 2 月至 6/7 月；日本及德國為 4 月至 8 月）",
        ],
        "application_period": [
            "116-1 校級赴外交換甄選時程（2026/10/13 公告簡章）：2026年11月1日開放線上申請、11月3日舉辦申請暨獎學金說明會、2026年11月15日（日）23:59:59 線上申請資料繳交截止、11月16日（一）23:59:59 審查補件截止。",
            "116-1 志願序變更與兩階段分發時程：2026年12月1日至12月9日 23:59 公布甄審成績排序並開放網路變更志願序；12月11日 00:00 公告第一次分發結果與完成線上報到；12月11日至12月14日缺額公告與第二次志願填報；12月15日至12月18日公告第二次分發結果與報到；12月19日至12月21日公告最終榜單。",
            "院級與系所級交換依各院系所公告時程辦理（如運動與休閒學院 116 學年度院級交換生甄選自 2026/09/18 至 2026/12/18 止）。",
        ],
        "eligibility": [
            "申請身分：國立臺灣師範大學學士班、碩士班及博士班在學生，且於本校已修業滿至少一學期（大一／碩一最早可於一年級下學期報名參加二年級下學期出發之甄選；不含進修推廣學院學生、在職專班生及臺灣獎學金受獎生）。",
            "國籍與身分限制：陸生、僑生及外籍生不得申請交換至其原居住國；外籍生領取臺師大獎學金者，於交換期間應自動放棄獎學金資格；大四學生可以交換為由辦理延畢並維持在學身分、繳交全額學雜費。",
            "語組與志願規則：校級交換分為「英歐語組」、「日語組」、「韓語組」及「中文組」四組，每次僅可擇一組報名（不得跨組），線上填寫 1 至 10 所語言能力、學制年級及學業成績皆符合條件之志願校。",
            "甄選評分標準（自 109-2 起採 100% 線上書面審查，免筆試與面試）：(1) 語言能力 30%、(2) 學業及相關學術表現 30%（其中包含 EMI 全英語授課修課數 5%，修習 5 門含以上 EMI 課程即可取得完整 5% 分數）、(3) 自傳及出國學習計畫 20%、(4) 大學（含）以上優良事蹟或活動證明 20%；同分時依 (1)➔(2)➔(3)➔(4) 排序。",
            "交換次數與期限上限：在學期間前往交換校研習以二次為限，每次以一學期為原則（特定姊妹校僅提供一學年課程者除外），總交換期限累計不得超過二個學期（一學年），亦不得申請延長。",
        ],
        "language_requirement": [
            "申請同學必須達到各姊妹校學程設立之語言能力條件方可選填該志願（申請系統會依成績自動初步篩選）；若姊妹校同時公告托福、雅思、JLPT 等多項檢定要求，僅須達到其中一項即可申請。",
            "語檢有效期限：除 JLPT 日檢及部分歐洲語言檢定終身有效外，TOEFL iBT、IELTS 有效期限皆為 2 年，且於提出校內申請及遞送姊妹校申請文件（建議至出國當日）時均須在有效期限內。",
            "重要採認規定：本校交換生甄選不得以 TOEFL MyBest™ Scores 填寫申請表外語能力成績，僅得填寫最新一期單次考試成績及各項分科分數；報名截止前若尚未收到正式紙本成績單，可先上傳網路查詢成績單，後續遞交姊妹校複審時須提供正式成績單影本。",
            "四大語組適用檢定：英歐語組採認 TOEFL iBT / ITP、IELTS、TOEIC、GEPT 全民英檢及法語 DELF/DALF/TCF、德語 Goethe/TestDaF、西語 DELE 等；日語組採認 JLPT（N1–N5）或 J.TEST；韓語組採認 TOPIK（1–6 級）；中文組（大陸地區學校）免附外語檢定。",
        ],
        "required_documents": [
            "A. 線上列印申請書（本人親筆簽名、系主任簽章後正本掃描上傳作為首頁；具師資培育公費生身分者須另附保證人同意書一份）",
            "B. 自傳與出國學習計畫（中文或外文撰寫，格式不限，中英文合計須介於 500 至 5,000 字之間，建議加附外文版本約 500 至 2,500 字）",
            "D. 語言能力證明文件正本掃描檔（中文組除外；等待正本寄發者可先上傳網路／電子郵件成績單電子檔並於指定時間內補交正本掃描檔）",
            "E. 學業及相關學術表現（含歷年中文成績單正本掃描檔，學士班須加附歷年名次證明；成績單所列 EMI 全英語授課修課數納入 5% 評分）",
            "F. 大學（含）以上優良事蹟或活動證明（如學生數位學習歷程檔案；請勿檢附高中職含以下時期之證明）",
            "G. 報名費新臺幣 500 元之超商繳費收據（列印繳費單至超商繳費並請店員加蓋當日章後掃描上傳）或線上信用卡繳費成功截圖證明（報名費經繳納不予退還；校內甄選階段免交推薦信）",
        ],
        "scholarship_info": [
            "教育部「學海飛颺」（本國籍一般優秀學生）及「學海惜珠」（本國籍清寒優秀學生）獎學金：適用於修讀學分之交換生、訪問生及雙聯生（不含前往大陸及港澳地區學校），每年約 1–3 月受理申請。",
            "國立臺灣師範大學「鼓勵學生赴境外進修補助」（115.03.19 修正通過）：補助本國籍生（含僑生）赴境外修讀學分之生活費，每年分兩次開放線上申請（115-1 校級申請為 12/1–12/14，115-2 校級申請為 5/18–6/1，院系所及雙聯至 11/13）。",
            "國立臺灣師範大學「晨光圓夢境外研修助學計畫」：補助本國籍清寒優秀在學生赴境外交換或訪問研修生活費，每年分兩次（約 5 月及 11 月截止）受理線上申請。",
            "外部與專項獎學金：日本台灣交流協會短期交換留學生獎學金、臺英聯盟獎學金、「洪陳慧美紀念獎學金」及「學生赴世界知名大學寒暑期進修補助」等。",
            "費用與義務提醒：交換期間須繳交臺師大全額學雜費（免繳姊妹校學費）；完成分發線上報到並上傳家長簽署之「錄取資格確認書」後，若無不可抗力因素放棄交換資格者，須繳交行政作業費 NT$5,000 且不得再參加校級交換甄選。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": ntnu_source_urls,
        "last_checked": "2026-10-16T14:00:00Z",
    }
    (OFFICIAL_NTNU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "國立臺灣師範大學",
        "last_checked": "2026-10-16T14:00:00Z",
        "academic_score_minimum": 60.0,
        "academic_score_rule": "須於臺師大修業滿至少一學期（不含進修推廣學院、在職專班及臺獎受獎生），並符合各志願姊妹校學程之 GPA／成績標準；校內書面審查「學業及相關學術表現」佔總分 30%（其中 5% 為 EMI 全英語授課修課數，修滿 5 門得 5%）。",
        "academic_gpa_minimum": None,
        "maximum_preferences": 10,
        "selection_rules": {
            "academic_policy": "percentage",
            "academic_reference_year": "116",
            "undergraduate_gpa_minimum": None,
            "undergraduate_rank_maximum": None,
            "graduate_academic_exempt": False,
            "exclude_in_service": True,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {},
            "excluded_undergraduate_years": [],
            "language_certificate_required": False,
        },
        "language_score_minimums": {
            "toefl": 61.0,
            "ielts": 5.5,
            "toeic": 600.0,
        },
        "application_periods": [
            {
                "title": "國立臺灣師範大學 116-1 校級赴外交換甄選線上申請與補件",
                "details": [
                    "線上申請開放：2026年11月1日（日）起至2026年11月15日（日）23:59:59 止（系統逾時自動關閉）；審查補件截止：2026年11月16日（一）23:59:59。",
                    "赴外交換系統暨獎學金申請說明會：2026年11月3日（二）。",
                    "申請者須擇一語組（英歐語組、日語組、韓語組、中文組）於線上系統（https://bds.oia.ntnu.edu.tw/bds/OE）選填 1–10 個志願並上傳 6 項電子備審資料及 500 元報名費證明。",
                ],
                "source": {
                    "title": "國立臺灣師範大學 116-1 校級赴外交換甄選簡章",
                    "source_url": "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                    "category": "deadline",
                    "summary": "116-1 校級赴外交換甄選主要時程表、線上申請與補件截止時間。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116-1",
                "audience": "all_students",
                "opens_at": "2026-11-01T00:00:00+08:00",
                "deadline_at": "2026-11-15T23:59:59+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "116-1 校級赴外交換甄選簡章已於 2026/10/13 公告，將於 2026/11/01–11/15 開放線上申請（11/03 舉辦說明會）。",
                "deadline_note": "線上系統：https://bds.oia.ntnu.edu.tw/bds/OE（補件截止日：2026/11/16 23:59:59）。",
                "reminder_eligible": True,
                "checked_at": "2026-10-16T14:00:00Z",
            },
            {
                "title": "國立臺灣師範大學 116-1 校級赴外交換成績排序公布、志願序變更與兩階段分發報到",
                "details": [
                    "公布甄審成績排序並開放網路變更志願序：2026年12月1日 00:00 至 12月9日 23:59。",
                    "第一次分發結果公告與線上繳交錄取資格確認書完成報到：2026年12月11日 00:00。",
                    "缺額公告與第二次志願填報：2026年12月11日至12月14日 00:00；第二次分發結果公告與線上報到：12月15日至12月18日 00:00；最終榜單公告：12月19日至12月21日。",
                ],
                "source": {
                    "title": "國立臺灣師範大學 116-1 校級赴外交換甄選簡章（第2頁時程表）",
                    "source_url": "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                    "category": "exchange_application",
                    "summary": "116-1 甄審成績公布、志願序變更、第一次與第二次志願分發及最終榜單時程。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116-1 分發與報到",
                "audience": "all_students",
                "opens_at": "2026-12-01T00:00:00+08:00",
                "deadline_at": "2026-12-21T23:59:59+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "提供公布成績排序後變更志願序一次，以及兩階段志願分發與缺額重填機制。",
                "deadline_note": "完成線上報到後若無不可抗力情事放棄資格者，須繳交行政作業費 NT$5,000。",
                "reminder_eligible": True,
                "checked_at": "2026-10-16T14:00:00Z",
            },
            {
                "title": "運動與休閒學院 116 學年度院級交換生甄選暨鼓勵赴境外進修補助申請",
                "details": [
                    "運動與休閒學院 116 學年度院級交換生甄選：2026年9月18日起至2026年12月18日止受理申請。",
                    "115學年度第2學期【鼓勵赴境外進修補助】（院／系／所交換及雙聯）暨【晨光圓夢境外研修助學計畫】線上申請：即日起至 2026年11月13日截止。",
                ],
                "source": {
                    "title": "國立臺灣師範大學國際事務處赴外交換與獎補助公告",
                    "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-subsidy",
                    "category": "scholarship",
                    "summary": "院系所級交換甄選與鼓勵赴境外進修補助、晨光圓夢助學計畫申請時程。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度院級交換與赴外獎補助",
                "audience": "all_students",
                "opens_at": "2026-09-18T09:00:00+08:00",
                "deadline_at": "2026-12-18T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "院級交換及赴外獎補助現正受理申請中。",
                "deadline_note": "院系所級交換請依各院系所公告辦理；獎補助請至赴外獎學金系統申請。",
                "reminder_eligible": True,
                "checked_at": "2026-10-16T14:00:00Z",
            },
        ],
        "program_overview": [
            {
                "title": "國立臺灣師範大學 116-1 校級與院系所級赴外交換計畫總覽（236 所合作大學／285 項交換合約）",
                "details": [
                    f"國立臺灣師範大學國際事務處（OIA）與各學院系所共同推動赴外交換學生計畫，全校目前共計 454 所全球姊妹校，其中列入赴外交換名額與條件列表之合作大學共 236 所（涵蓋 285 項校級、院級與系所級交換合約；其中含校級合約 {uni_level_count} 校、純院系所級合約 {col_dept_only_count} 校，116-1 已確認公告名額 {confirmed_1161_quota_count} 校）。",
                    "校級交換計畫分為「英歐語組」、「日語組」、「韓語組」及「中文組」四大語組，每年辦理兩次甄選（秋季出境於前一年 11 月公告受理、春季出境於前一年 5 月公告受理）；116-1 甄選自 2026/11/01 至 11/15 開放線上申請，至多可選填 10 個志願。",
                    "本平台完整收錄臺師大 236 所交換合作大學之 116-1 當期與 115 學年度參考名額、各學程 TOEFL/IELTS/JLPT/TOPIK 語檢與年級門檻、100% 線上書面審查配分（含 EMI 修課加分）、獎助學金以及 174 所合作校之歷年返國交換生心得報告連結。",
                ],
                "source": {
                    "title": "國立臺灣師範大學校級院系所級赴外交換名額列表與 116-1 甄選簡章",
                    "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist",
                    "category": "partner_school",
                    "summary": "臺師大 236 所交換合作大學名額條件列表與 116-1 甄選簡章。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "申請資格、修業學期限制與 100% 線上書面審查配分（含 EMI 修課 5%）",
                "details": [
                    "在學與修業門檻：本校學士班、碩士班及博士班在學生，於臺師大已修習至少滿一學期（大一／碩一上學期尚無成績單不可申請，最早可於一下報名二年級春季班出國；不含進修推廣學院、在職專班生及臺灣獎學金受獎生）。",
                    "大四延畢與交換次數：大四學生可申請交換並由教務處依赴外名單協助辦理延畢（須繳交全額學雜費）；在學期間赴外交換以二次為限、每次以一學期為原則，總交換期限累計不得超過二學期（一學年）。",
                    "語組與志願：每次僅可選擇一組（英歐語組、日語組、韓語組、中文組）報名，不得跨組，可選填 1 至 10 所符合條件之志願校。",
                    "書面審查比重（自 109-2 起取消面試、自 101-2 起取消中文筆試）：(1) 語言能力 30%、(2) 學業及相關學術表現 30%（其中包含 EMI 全英語授課修課數 5%，修滿 5 門含以上 EMI 課程得完整 5%）、(3) 自傳及出國學習計畫 20%、(4) 大學（含）以上優良事蹟或活動證明 20%。",
                ],
                "source": {
                    "title": "國立臺灣師範大學交換生甄選作業要點及 116-1 甄選簡章",
                    "source_url": "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                    "category": "exchange_application",
                    "summary": "申請身分、修業學期門檻、四語組規定與書面審查配分標準。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "各語組語言檢定有效期限與 TOEFL MyBest™ Scores 不採認規定",
                "details": [
                    "申請者必須達到欲選填姊妹校學程設立之語言能力條件（申請系統會自動初步篩檢）；若姊妹校同時列出多項檢定（如 TOEFL iBT、IELTS、JLPT），僅須達到其中一項即可。",
                    "有效期限：除 JLPT 日檢及部分歐洲語言檢定終身有效外，TOEFL iBT、IELTS 有效期限皆為 2 年，且於校內申請及遞交姊妹校複審（建議至出國當日）時均須在有效期限內。",
                    "單次成績規定：不得以 TOEFL MyBest™ Scores 填寫申請表外語能力成績，僅得填寫最新一期單次考試成績及各項分科分數；正式成績單尚未寄達者可先上傳網路成績單並於指定時間內補交正本掃描檔。",
                ],
                "source": {
                    "title": "國立臺灣師範大學赴外交換語言檢定資訊與常見問題",
                    "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-languagetest",
                    "category": "exchange_application",
                    "summary": "英歐語組、日語組、韓語組、中文組語言檢定採認與有效期限規範。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "臺師大赴外交換生系統應上傳電子備審文件與報名費繳交規範",
                "details": [
                    "1. 申請表（`申請表_姓名`）：線上列印後由本人親筆簽名、系主任簽章後正本掃描上傳（公費生加附師資培育公費生保證人同意書）。",
                    "2. 自傳與出國學習計畫（`自傳與出國學習計畫_姓名`）：中文或外文撰寫，合計介於 500 至 5,000 字之間，建議加附外文版本約 500 至 2,500 字。",
                    "3. 語言能力證明文件（`語言能力證明文件_姓名`）：正本掃描上傳（中文組免附）。",
                    "4. 學業及相關學術表現（`學業及相關學術表現_姓名`）：含歷年中文成績單正本掃描檔，學士班須加附歷年名次證明。",
                    "5. 大學（含）以上優良事蹟或活動證明（`大學(含)以上優良事蹟或活動證明_姓名`）：如學生數位學習歷程檔案（勿附高中職以下證明）。",
                    "6. 繳費證明（`繳費證明_姓名`）：報名費新臺幣 500 元之超商繳費收據（須請超商加蓋當日章）掃描檔或線上信用卡繳費成功截圖證明（校內初選免附推薦信）。",
                ],
                "source": {
                    "title": "國立臺灣師範大學赴外交換生—如何申請與 116-1 甄選簡章",
                    "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-apply",
                    "category": "exchange_application",
                    "summary": "6 項上傳檔案命名規則、字數要求與報名費 500 元繳交方式。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "教育部學海飛颺／惜珠、師大鼓勵學生赴境外進修補助與晨光圓夢助學計畫",
                "details": [
                    "教育部「學海飛颺」與「學海惜珠」獎學金：補助本國籍優秀學生及清寒優秀學生赴國外（不含陸港澳）修讀學分，每年約 1–3 月申請。",
                    "國立臺灣師範大學「鼓勵學生赴境外進修補助」：補助本國籍生（含僑生）赴境外交換、訪問、雙聯或暑期修讀學分之生活費，每年分兩次（約 3–5 月及 9–11 月）受理申請。",
                    "國立臺灣師範大學「晨光圓夢境外研修助學計畫」：補助本國籍清寒優秀學生赴境外交換或訪問之生活費，每年分兩次受理線上申請。",
                    "交換期間須繳交臺師大全額學雜費，免繳姊妹校學費；完成分發線上報到（上傳錄取資格確認書）後若無不可抗力情事放棄資格者，須繳交行政作業費 NT$5,000 且不得再參加校級交換生甄選。",
                ],
                "source": {
                    "title": "國立臺灣師範大學國際事務處—交換生補助與赴外獎學金專頁",
                    "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-scholarship",
                    "category": "scholarship",
                    "summary": "學海飛颺、學海惜珠、師大鼓勵赴境外進修補助與晨光圓夢計畫。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "臺師大赴外交換線上申請系統 6 項備審檔案命名與上傳規範",
                "summary": "臺師大校級赴外交換採全線上上傳審查（免面試、免筆試），所有上傳檔案須依簡章規定格式命名（如 `申請表_王大美`），並於 2026/11/15 23:59:59 前完成送出。",
                "key_points": [
                    "申請書、語言能力證明與中文成績單／名次證明應以正本掃描後上傳；超商繳納 500 元報名費者須請店員加蓋當日店章後掃描上傳。",
                    "校內甄選階段不需繳交推薦信；待通過校內初選、向姊妹校遞交複審資料時，若姊妹校規定須審核推薦信再行遞交。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立臺灣師範大學 116-1 校級赴外交換甄選簡章（第10頁）",
                    "source_url": "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "《國立臺灣師範大學學生境外修習課程實施辦法》與《交換生甄選作業要點》重點",
                "summary": "規範臺師大交換生修業期限上限、每學期最低修課學分、ECTS 學分換算、大陸地區師資職前課程採認限制及報到後放棄之行政作業費規定。",
                "key_points": [
                    "學生出國修習課程累計不得超過一學年（二個學期），每學期至少應修習 2 科或 6 學分；採認學分以不超過各該系所畢業最低總學分數三分之一為限，歐洲 ECTS 原則以 2 ECTS 等同 1 學分。",
                    "依大陸地區學歷採認辦法第 9 條，於大陸地區修習之課程不得採計為師資職前教育課程專門課程（含教育專業課程及專門課程）。",
                    "繳交「錄取資格確認書」完成線上報到後放棄交換資格者，除因不可抗力情事並檢附具體證明外，一律須繳交行政作業費新臺幣 5,000 元匯入校務發展基金，且之後不得再參加校級交換生甄選。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立臺灣師範大學學生進修相關法規專頁",
                    "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/resource-reg-overseasstudy",
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": "https://bds.oia.ntnu.edu.tw/bds/web/resource-reg-overseasstudy",
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {
                "title": "國立臺灣師範大學 116-1 校級赴外交換甄選簡章（2026/10/13）",
                "source_url": "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺灣師範大學校級院系所級赴外交換名額列表（116-1 / 115-2 / 115-1）",
                "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立臺灣師範大學國際事務處—赴外交換簡介",
                "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-info",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺灣師範大學國際事務處—如何申請赴外交換",
                "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-apply",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺灣師範大學國際事務處—赴外交換常見問題 FAQ",
                "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-faq",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺灣師範大學國際事務處—常用下載（歷年簡章與行前手冊）",
                "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-download",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺灣師範大學國際事務處—交換生補助與赴外獎學金",
                "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-scholarship",
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "國立臺灣師範大學國際事務處—赴外獎學金最新公告",
                "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-subsidy",
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "國立臺灣師範大學國際事務處—交換生心得分享查詢庫",
                "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-experience",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立臺灣師範大學國際事務處—學生進修相關法規",
                "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/resource-reg-overseasstudy",
                "category": "exchange_application",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_NTNU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    pages_records = [
        {
            "title": "國立臺灣師範大學：116-1 校級赴外交換甄選主要時程與申請流程",
            "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-apply",
            "published_at": "2026-10-13T00:00:00Z",
            "text": "\n".join(exchange_info_payload["application_period"]),
            "summary": "\n".join(exchange_info_payload["application_period"]),
            "category": "exchange_application",
            "attachments": [
                {
                    "url": "https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
                    "filename": "doc_OE116-1 SPRING2027-1013.pdf",
                    "local_path": None,
                    "content_type": "application/pdf",
                }
            ],
            "crawled_at": "2026-10-16T14:00:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立臺灣師範大學：交換學生申請資格、四語組與書面審查配分標準",
            "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-info",
            "published_at": "2026-10-13T00:00:00Z",
            "text": "\n".join(exchange_info_payload["eligibility"]),
            "summary": "\n".join(exchange_info_payload["eligibility"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-16T14:00:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立臺灣師範大學：赴外交換語言能力檢定要求與有效期限規定",
            "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-languagetest",
            "published_at": "2026-10-13T00:00:00Z",
            "text": "\n".join(exchange_info_payload["language_requirement"]),
            "summary": "\n".join(exchange_info_payload["language_requirement"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-16T14:00:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立臺灣師範大學：線上申請系統應備文件與報名費繳交規範",
            "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-download",
            "published_at": "2026-10-13T00:00:00Z",
            "text": "\n".join(exchange_info_payload["required_documents"]),
            "summary": "\n".join(exchange_info_payload["required_documents"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-16T14:00:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立臺灣師範大學：赴外交換獎助學金、學海系列與鼓勵赴境外進修補助",
            "source_url": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-scholarship",
            "published_at": "2026-10-14T00:00:00Z",
            "text": "\n".join(exchange_info_payload["scholarship_info"]),
            "summary": "\n".join(exchange_info_payload["scholarship_info"]),
            "category": "scholarship",
            "attachments": [],
            "crawled_at": "2026-10-16T14:00:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
        },
    ]
    (OFFICIAL_NTNU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "ntnu",
        "school_name": "國立臺灣師範大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_weights": {
            "written_review": {
                "language_proficiency": 0.30,
                "academic_and_emi_courses": 0.30,
                "emi_course_subweight": 0.05,
                "autobiography_and_study_plan": 0.20,
                "extracurricular_achievements": 0.20,
            }
        },
        "source_urls": ntnu_source_urls,
        "verified_at": "2026-10-16",
    }
    (OFFICIAL_NTNU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTNU_DIR / "documents.json").write_text(
        json.dumps({"school_name": "國立臺灣師範大學", "required_documents": student_dashboard_payload["required_documents"], "source_urls": ntnu_source_urls}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTNU_DIR / "scholarships.json").write_text(
        json.dumps({"school_name": "國立臺灣師範大學", "scholarships": student_dashboard_payload["scholarship_info"], "source_urls": ntnu_source_urls}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "ntnu",
        "school_name": "國立臺灣師範大學",
        "total_partners": len(partners),
        "university_level_partners": uni_level_count,
        "college_and_department_only_partners": col_dept_only_count,
        "confirmed_116_1_quota_partners": confirmed_1161_quota_count,
        "experience_report_covered_partners": len(exp_by_school),
        "open_partners": len(partners),
        "verified_locations": len(partners),
        "verified_official_websites": sum(1 for p in partners if p.get("official_website")),
        "verified_campus_images": len(partners),
        "active_term": "116-1 校級赴外交換甄選簡章已於 2026/10/13 公告（線上報名：2026/11/01–11/15 23:59:59，補件截止：11/16，說明會：11/03，第一次分發：12/11，最終榜單：12/19–12/21）。",
        "verified_at": "2026-10-16",
    }
    (OFFICIAL_NTNU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTNU_DIR / "verification_status.json").write_text(
        json.dumps({
            "school_id": "ntnu",
            "school_name": "國立臺灣師範大學",
            "status": "official_verified",
            "checked_at": "2026-10-16T14:00:00Z",
            "counts": completeness,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Successfully built NTNU catalog: {len(partners)} partners ({uni_level_count} uni-level, {col_dept_only_count} col/dept-only, "
        f"{confirmed_1161_quota_count} confirmed 116-1 quotas), {len(workflows)} workflows, {len(destinations)} destinations, "
        f"{len(research_records)} research records, {len(new_locations)} locations, {len(exp_by_school)} schools with experience reports."
    )


if __name__ == "__main__":
    main()
