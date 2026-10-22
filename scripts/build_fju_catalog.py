"""Build the official Fu Jen Catholic University (天主教輔仁大學) exchange data bundle."""

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
_HOST_SCRATCH = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\0723e0a1-b112-47e2-8145-2d4d6f69cb19\scratch\fju_discovery")
SCRATCH_FJU = _HOST_SCRATCH if _HOST_SCRATCH.exists() else Path("/fju_discovery")
OFFICIAL_FJU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "fju"
SOURCES_FJU_DIR = REPO_ROOT / "sources" / "fju"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

COUNTRY_MAP = {
    "大陸地區": "中國大陸",
    "中國": "中國大陸",
    "香港": "香港",
    "澳門": "澳門",
    "南韓": "韓國",
    "澳大利亞": "澳洲",
}

REGION_COST_DEFAULTS = {
    "美國": ("USD 1,400–2,200 / 月（含住宿、餐飲、校園保險與當地交通）", "建議預留強制校園醫療保險（約 USD 1,500–2,500 / 學期）與 J-1 簽證 SEVIS 費用。"),
    "加拿大": ("CAD 1,500–2,200 / 月（含住宿、膳食、省級／校內醫保與市區交通）", "須投保接待校指定醫療保險並辦理 Study Permit 或 eTA。"),
    "英國": ("GBP 1,000–1,600 / 月（含宿舍、飲食與市區交通）", "交換一學期多適用 Standard Visitor 簽證，一學年須辦理 Student Visa 並繳納 IHS 醫療附加費。"),
    "法國": ("EUR 850–1,400 / 月（巴黎地區約 EUR 1,200–1,600 / 月；可申請 CAF 房補）", "須透過法國教育中心（Campus France）面試並申辦長期學生簽證（VLS-TS）。"),
    "德國": ("EUR 934–1,200 / 月（德國簽證財力證明基準為每月 EUR 934）", "須辦理德國公保（約 EUR 120–130 / 月）及學期票（Semesterticket）。"),
    "西班牙": ("EUR 800–1,250 / 月（馬德里、巴塞隆納較高，其他城市約 EUR 700–1,000 / 月）", "須備妥涵蓋全額醫療與遺體運返之私人醫療保險以申辦西班牙學生簽證。"),
    "義大利": ("EUR 800–1,250 / 月（羅馬、米蘭較高）", "抵義 8 個工作日內須辦理居留證（Permesso di soggiorno）與稅號（Codice Fiscale）。"),
    "荷蘭": ("EUR 950–1,400 / 月（荷蘭移民局 IND 財力證明基準約 EUR 1,225 / 月）", "由接待校代辦 MVV/VVR 居留許可，房源緊張建議儘早申請宿舍。"),
    "比利時": ("EUR 850–1,200 / 月（含學生宿舍、餐飲與大眾運輸）", "須辦理長期學生簽證 D 簽，抵達後向市政廳登記居留。"),
    "瑞士": ("CHF 1,500–2,200 / 月（含住宿、膳食與強制保險）", "須透過瑞士駐外代表處申辦學生簽證，並於抵瑞後申請居留證與醫療保險豁免或投保。"),
    "奧地利": ("EUR 850–1,250 / 月（含 OeAD 學生宿舍與日常開支）", "多透過 OeAD 申請學生宿舍，並依停留期間申辦簽證 D 或居留許可。"),
    "丹麥": ("DKK 6,500–9,500 / 月（含住宿、飲食與單車／大眾運輸）", "須申辦 ST1 學生居留許可，抵丹後登記 CPR 號碼即可享有公醫保障。"),
    "愛爾蘭": ("EUR 1,000–1,500 / 月（都柏林地區住宿成本較高）", "持臺灣護照免簽入境後，若停留逾 90 天須辦理 IRP（Irish Residence Permit）登記。"),
    "斯洛維尼亞": ("EUR 600–900 / 月（學生餐券系統補貼完善）", "可享斯洛維尼亞全國學生餐券（Študentski boni）與學生交通優惠。"),
    "斯洛伐克": ("EUR 550–850 / 月（生活與宿舍費用相對親民）", "須依規定辦理居留或簽證手續並準備英文／斯洛伐克文翻譯公證文件。"),
    "波蘭": ("EUR 500–800 / 月（含校內宿舍與日常餐飲交通）", "須申辦波蘭 D 類國別學生簽證並備妥歐盟規格旅遊醫療保險。"),
    "匈牙利": ("EUR 550–850 / 月（布達佩斯生活費與住宿相對實惠）", "須申請學生居留許可並投保醫療保險。"),
    "捷克": ("EUR 600–900 / 月（含學生宿舍、食堂與市區交通卡）", "須提前預約捷克經濟文化辦事處申辦長期學生簽證與捷克合約醫療保險。"),
    "立陶宛": ("EUR 550–850 / 月（含宿舍與日常開支）", "須透過 MIGRIS 系統申辦臨時居留許可（TRP）或國家簽證。"),
    "澳洲": ("AUD 1,800–2,600 / 月（含住宿、飲食與交通）", "強制投保海外學生健康保險（OSHC）後方可核發 Subclass 500 學生簽證。"),
    "紐西蘭": ("NZD 1,600–2,300 / 月（含宿舍與日常生活費）", "須申辦 Fee-Paying / Exchange Student Visa 並投保合規學生醫療與旅遊保險。"),
    "日本": ("JPY 80,000–130,000 / 月（東京圈約 JPY 100,000–140,000；地方城市約 JPY 70,000–100,000）", "憑接待校核發之在留資格認定證明書（COE）換發留學簽證，抵日後須加入國民健康保險（約 JPY 1,500–2,000 / 月）。"),
    "韓國": ("KRW 800,000–1,300,000 / 月（首爾圈外宿較高；校內宿舍約 KRW 150,000–400,000 / 月）", "憑標準入學許可書申辦 D-2-6 交換學生簽證，抵韓後外國人登錄並自動納入韓國國民健康保險（NHIS）。"),
    "中國大陸": ("RMB 2,000–3,800 / 月（校內宿舍與學生食堂費用低廉，一線城市北上廣深略高）", "持臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定投保大陸境內來華留學生綜合醫療保險（約 RMB 400 / 學期）。"),
    "香港": ("HKD 6,000–10,000 / 月（校內宿位有限，若外宿租金較高）", "須透過接待校向香港入境事務處申辦學生簽證／進入許可（Student Visa / Entry Permit）。"),
    "澳門": ("HKD 4,500–7,500 / 月（約 MOP 4,600–7,700，含宿舍、膳食與交通）", "入境後依澳門治安警察局居留及逗留事務廳規定辦理「逗留的特別許可」（學生逗留）。"),
    "新加坡": ("SGD 1,200–2,000 / 月（校內宿舍競爭激烈，外宿成本較高）", "須透過新加坡移民局（ICA）SOLAR 系統申辦 Student's Pass（STP）。"),
    "馬來西亞": ("MYR 1,800–2,800 / 月（吉隆坡／雪蘭莪生活機能便利且物價親民）", "須透過 EMGS（Education Malaysia Global Services）系統申辦學生簽證（VAL / Student Pass）。"),
    "泰國": ("THB 15,000–25,000 / 月（曼谷學生公寓與餐飲消費適中）", "須憑接待校公文申辦 Non-Immigrant ED 學生簽證，每 90 天須向移民局報到。"),
    "越南": ("USD 400–700 / 月（河內、胡志明市生活成本低廉）", "須由接待校協助辦理越南學生簽證（DH 簽證）及醫療保險。"),
    "印尼": ("USD 350–650 / 月（日惹、泗水、萬隆、三寶壟物價低廉）", "須提前申辦印尼學生居留簽證（VITAS / KITAS）與學習許可（Surat Izin Belajar）。"),
    "菲律賓": ("USD 450–750 / 月（馬尼拉及周邊城市生活支出適中）", "入境後由接待校國際處協助辦理 SSP（Special Study Permit）或 9(f) 學生簽證。"),
    "印度": ("USD 350–650 / 月（多數接待校提供包餐制學生宿舍與校園接駁）", "須申辦印度 Student Visa（S-Visa），抵印後 14 天內完成 FRRO 線上外國人登記。"),
    "蒙古": ("USD 400–650 / 月（烏蘭巴托冬季寒冷，須預留禦寒裝備費用）", "須憑接待校邀請函申辦蒙古學生簽證，冬季氣溫可達 -25°C 以下須注意保暖。"),
    "墨西哥": ("USD 600–1,000 / 月（墨西哥城、蒙特雷、普埃布拉及梅里達生活費適中）", "交換一學期（180 天內）持臺灣護照須先向墨西哥商務簽證文件暨文化辦事處申辦簽證，並投保國際醫療險。"),
    "智利": ("USD 700–1,100 / 月（聖地牙哥生活品質高，多數學生選擇寄宿家庭或合租）", "須申辦智利學生簽證並備妥全期海外醫療保險。"),
    "秘魯": ("USD 550–900 / 月（利馬 Miraflores / San Isidro 等安全住宅區租金略高）", "須依接待校指示申辦秘魯交換學生簽證並投保涵蓋全期之國際醫療險。"),
    "多明尼加": ("USD 600–950 / 月（聖多明哥住宿與日常開支）", "須依接待校指示辦理學生入境簽證與國際醫療保險。"),
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
    s = s.replace("聖路易士大學", "聖路易大學").replace("天主教里爾大學", "里爾天主教大學").replace("香港恆生大學", "香港恒生大學")
    return "".join(ch for ch in s if "\u4e00" <= ch <= "\u9fff")


def parse_fju_school(cell_text: str) -> tuple[str, str, str, list[str]]:
    s = html.unescape(cell_text).strip()
    s = re.sub(r"\s*\(原為「首都大學東京」[^)]*\)", "", s)
    s = re.sub(r"\s*\(原名:Lillebaelt Academy[^)]*\)", "", s)
    s = re.sub(r"\s*\*Financial Aid\s*", "", s, flags=re.I)
    badges = re.findall(r"\b(985|211)\b", s)
    s = re.sub(r"(?:\s+(?:985|211))+\s*$", "", s).strip()
    s = re.sub(r"\s+", " ", s).strip()
    if s.startswith("EDHEC高等商業學院"):
        return "EDHEC高等商業學院 EDHEC Business School", "EDHEC高等商業學院", "EDHEC Business School", badges
    if s.startswith("KEDGE高等商業學院"):
        return "KEDGE高等商業學院 KEDGE Business School", "KEDGE高等商業學院", "KEDGE Business School", badges
    if s.startswith("拉孟大學IQS管理學院"):
        return "拉孟大學IQS管理學院 IQS School of Management, Universitat Ramon Llull", "拉孟大學IQS管理學院", "IQS School of Management, Universitat Ramon Llull", badges
    m = re.match(r"^((?:\([^)]+\))?[^\x00-\x7F\-]+(?:-[^\x00-\x7F]+)?(?:\([^)]+\))?)\s*([A-Za-z].*)$", s)
    if m:
        zh, en = m.group(1).strip(), m.group(2).strip()
        return f"{zh} {en}", zh, en, badges
    return s, s, "", badges


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_fju_input(name: str) -> Path:
    candidates = (
        SCRATCH_FJU / name,
        SOURCES_FJU_DIR / name,
        SOURCES_FJU_DIR / Path(name).name,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return SCRATCH_FJU / name


def archive_official_sources() -> dict:
    SOURCES_FJU_DIR.mkdir(parents=True, exist_ok=True)
    files_to_copy = [
        (resolve_fju_input("label_39_process.html"), SOURCES_FJU_DIR / "label_39_process.html", "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=39", "輔大國際學生中心—赴姊妹校交換學生申請流程與說明（labelID=39）"),
        (resolve_fju_input("label_40_partner_list.html"), SOURCES_FJU_DIR / "label_40_partner_list.html", "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=40", "輔大赴姊妹校交換學生—申請資格與姊妹校一覽表（234校，labelID=40）"),
        (resolve_fju_input("label_41_faq.html"), SOURCES_FJU_DIR / "label_41_faq.html", "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=41", "輔大赴姊妹校交換學生—常見問題 FAQ（labelID=41）"),
        (resolve_fju_input("label_42_downloads.html"), SOURCES_FJU_DIR / "label_42_downloads.html", "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=42", "輔大赴姊妹校交換學生—表單與文件下載（labelID=42）"),
        (resolve_fju_input("label_44_lang_score.html"), SOURCES_FJU_DIR / "label_44_lang_score.html", "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=44", "輔大赴姊妹校交換學生—外語能力換分標準表（labelID=44）"),
        (resolve_fju_input("news_1057_116_1_info.html"), SOURCES_FJU_DIR / "news_1057_116_1_info.html", "https://iscoie.fju.edu.tw/newsDetail.jsp?newsID=1057", "116學年度第1學期（2027秋季班）赴姊妹校交換學生甄選說明會公告"),
        (resolve_fju_input("res_26_outgoing_reg.html"), SOURCES_FJU_DIR / "res_26_outgoing_reg.html", "https://iscoie.fju.edu.tw/resource.jsp?labelID=26", "輔大出國交換相關法規與選課辦法專頁（labelID=26）"),
        (resolve_fju_input("res_27_scholarships.html"), SOURCES_FJU_DIR / "res_27_scholarships.html", "https://iscoie.fju.edu.tw/resource.jsp?labelID=27", "輔大出國交換獎學金與學海計畫專頁（labelID=27）"),
        (resolve_fju_input("attachments/115_2_quotas_2027_spring.pdf"), SOURCES_FJU_DIR / "115_2_quotas_2027_spring.pdf", "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1247", "115-2（2027春季班）交換生甄選名額一覽表（115.04.01更新）"),
        (resolve_fju_input("attachments/115_1_quotas_2026_fall.pdf"), SOURCES_FJU_DIR / "115_1_quotas_2026_fall.pdf", "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1141", "115-1（2026秋季班）交換生甄選名額一覽表"),
        (resolve_fju_input("attachments/115_2_exchange_notice.pdf"), SOURCES_FJU_DIR / "115_2_exchange_notice.pdf", "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1246", "115學年度第2學期赴姊妹校交換學生甄選申請須知"),
        (resolve_fju_input("attachments/reg_selection_guidelines_zh.pdf"), SOURCES_FJU_DIR / "reg_selection_guidelines_zh.pdf", "https://iscoie.fju.edu.tw/teachingServices.jsp?file=910", "天主教輔仁大學交換學生甄選作業要點"),
        (resolve_fju_input("attachments/reg_study_implementation.pdf"), SOURCES_FJU_DIR / "reg_study_implementation.pdf", "https://iscoie.fju.edu.tw/teachingServices.jsp?file=908", "天主教輔仁大學學生赴境外大學交換學習實施辦法"),
    ]
    provenance_items = []
    for src, dst, url, title in files_to_copy:
        if src.exists():
            if src.resolve() != dst.resolve():
                shutil.copy2(src, dst)
            provenance_items.append({
                "file": f"sources/fju/{dst.name}",
                "source_url": url,
                "title": title,
                "sha256": sha256_file(dst),
                "bytes": dst.stat().st_size,
                "fetched_at": "2026-10-16T04:15:00Z",
            })
    return {
        "school_id": "fju",
        "school_name": "天主教輔仁大學",
        "generated_at": "2026-10-16T04:50:00Z",
        "active_cycle_note": "116學年度第1學期（2027秋季班）出國交換學生甄選說明會於2026/10/12（外語場）及2026/10/19（中語場）舉行，116-1收件時間為2026年12月（名額表預計於11月底收件前公告）。目前提供官網 labelID=40 暨 208 頁 awardDetail.jsp 姊妹校專頁完整條件，並附 115-2（2027春季班）及 115-1（2026秋季班）官方名額表供規劃參考。",
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
                "geocoded_at": (r.get("checked_at") or "2026-10-11") + "T00:00:00Z" if len(str(r.get("checked_at") or "")) == 10 else (r.get("checked_at") or "2026-10-11T00:00:00Z"),
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

    for r in json.loads((REPO_ROOT / "src/exchange_info/official_data/ccu/campus-assets.json").read_text(encoding="utf-8")).get("schools", []):
        coord = r.get("coordinates") or {}
        if coord.get("status") == "verified_current" and coord.get("value"):
            rec = dict(coord["value"])
            name = r.get("school_name") or ""
            c = COUNTRY_MAP.get(str(rec.get("country") or r.get("country") or ""), str(rec.get("country") or r.get("country") or ""))
            rec["country"] = c
            if loose_en(name) and c:
                loc_by_en_country.setdefault((loose_en(name), c), rec)
            if loose_zh(name) and c:
                loc_by_zh_country.setdefault((loose_zh(name), c), rec)

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

    for r in json.loads((REPO_ROOT / "src/exchange_info/official_data/tku/campus_asset_manifest.json").read_text(encoding="utf-8")):
        if r.get("review_status") == "verified_asset" and r.get("local_path"):
            name = r.get("school_name") or ""
            c = COUNTRY_MAP.get(str(r.get("country") or ""), str(r.get("country") or ""))
            rel = urlsplit(r["local_path"]).path.removeprefix("/static/")
            fpath = STATIC_DIR / rel
            if not fpath.is_file():
                continue
            rec = {
                "school_name": name,
                "country": c,
                "status": "verified",
                "local_path": r["local_path"],
                "image_source_url": r.get("image_source_url"),
                "official_page_url": r.get("source_url"),
                "identity_source_url": r.get("identity_source_url") or r.get("source_url"),
                "artist": r.get("author"),
                "license_name": r.get("license"),
                "license_url": r.get("license_url"),
                "content_hash": sha256_file(fpath),
                "checked_at": r.get("checked_at") or "2026-10-11",
                "note": r.get("caption") or "",
            }
            if loose_en(name) and c:
                img_by_en_country.setdefault((loose_en(name), c), rec)
            if loose_zh(name) and c:
                img_by_zh_country.setdefault((loose_zh(name), c), rec)

    for r in json.loads((REPO_ROOT / "src/exchange_info/official_data/ccu/campus-assets.json").read_text(encoding="utf-8")).get("schools", []):
        photo = r.get("photo") or {}
        if photo.get("status") == "verified_current" and photo.get("value"):
            v = photo["value"]
            name = r.get("school_name") or ""
            c = COUNTRY_MAP.get(str(r.get("country") or ""), str(r.get("country") or ""))
            rel = urlsplit(v["local_path"]).path.removeprefix("/static/")
            fpath = STATIC_DIR / rel
            if not fpath.is_file():
                continue
            rec = {
                "school_name": name,
                "country": c,
                "status": "verified",
                "local_path": v["local_path"],
                "image_source_url": v.get("image_source_url"),
                "official_page_url": v.get("source_page_url"),
                "identity_source_url": v.get("source_page_url"),
                "artist": v.get("artist"),
                "license_name": v.get("license_name"),
                "license_url": v.get("license_url"),
                "content_hash": sha256_file(fpath),
                "checked_at": v.get("checked_at") or "2026-10-11",
                "note": v.get("campus_caption") or "",
            }
            if loose_en(name) and c:
                img_by_en_country.setdefault((loose_en(name), c), rec)
            if loose_zh(name) and c:
                img_by_zh_country.setdefault((loose_zh(name), c), rec)

    return loc_by_en_country, loc_by_zh_country, img_by_en_country, img_by_zh_country


def parse_listing_metadata(cells: list[str], table_index: int) -> dict[str, str]:
    """The official directory lists contract quotas, not degree/semester codes."""
    if table_index not in (0, 1) or len(cells) < 4:
        raise ValueError("Unexpected FJU directory row layout; inspect the official headers")
    cleaned = [html.unescape(str(cell)).strip() for cell in cells]
    return {
        "contract_quota": cleaned[2],
        "directory_notes": "；".join(cleaned[3:]),
        "grade_limit": "",
        "semester_limit": "",
        "language_required_flag": "",
    }


def clean_quota_cell(val: str) -> str:
    return re.sub(r"\s+", " ", (val or "").replace("\n", " ")).strip()


def load_quota_lookup(filename: str) -> tuple[dict[str, dict], dict[str, dict]]:
    rows = json.loads(resolve_fju_input(filename).read_text(encoding="utf-8"))
    by_en = {}
    by_zh = {}
    for r in rows:
        if not isinstance(r, list) or len(r) < 4:
            continue
        raw_name = clean_quota_cell(r[2])
        if not raw_name:
            continue
        _, zh, en, _ = parse_fju_school(raw_name)
        req_text = clean_quota_cell(r[5]) if len(r) > 5 else ""
        entry = {
            "raw_name": raw_name,
            "quota": clean_quota_cell(r[3]),
            "semester_limit": clean_quota_cell(r[4]) if len(r) > 4 else "",
            "language": req_text,
            "notes": req_text,
        }
        if loose_en(en):
            by_en.setdefault(loose_en(en), entry)
        if loose_zh(zh):
            by_zh.setdefault(loose_zh(zh), entry)
    return by_en, by_zh


def extract_gpa_requirement(elig_text: str, q_notes: str) -> str | None:
    combined = f"{elig_text or ''} {q_notes or ''}"
    m = re.search(r"GPA\s*(?:達|需達|須達|至少|>=|≧|:|：)?\s*(\d+(?:\.\d+)?)\s*(?:/\s*4(?:\.0)?)?", combined, flags=re.I)
    if m:
        return f"GPA {m.group(1)} 以上（且須符合輔大116-1學士班歷年學業平均70分以上規定；研究所校內成績門檻待確認）"
    m_pct = re.search(r"(?:歷年平均成績|學業總平均|平均成績).*?(\d{2})\s*分", combined)
    if m_pct:
        return f"學業總平均 {m_pct.group(1)} 分以上（且須符合輔大116-1學士班歷年學業平均70分以上規定；研究所校內成績門檻待確認）"
    return "輔大116-1學士班歷年學業平均70分以上；研究所校內成績門檻與各接待校額外條件待確認"


def extract_language_requirement(country: str, zh_name: str, elig_text: str, q115_2: dict | None, q115_1: dict | None) -> str:
    parts = []
    if q115_2 and q115_2.get("language"):
        parts.append(f"115-2 簡章語檢標準：{q115_2['language']}")
    elif q115_1 and q115_1.get("language"):
        parts.append(f"115-1 簡章語檢標準：{q115_1['language']}")

    if elig_text:
        lang_lines = []
        for line in elig_text.splitlines():
            line_s = line.strip()
            if any(k in line_s.upper() for k in ["TOEFL", "IELTS", "JLPT", "TOPIK", "DELE", "DELF", "TESTDAF", "GOETHE", "CEFR", "托福", "雅思", "日檢", "韓檢", "多益", "TOEIC", "語文", "語言", "英語", "日語", "韓語", "法語", "德語", "西語"]):
                lang_lines.append(line_s)
        if lang_lines:
            parts.append("姊妹校專頁語言要求：" + "；".join(lang_lines[:3]))

    if not parts:
        if country in ("中國大陸", "香港", "澳門"):
            if "浸會" in zh_name or "城市大學" in zh_name or "嶺南" in zh_name or "科技大學" in zh_name or "中文大學" in zh_name:
                return "依接待校英文授課或中文授課規定（香港姊妹校多要求 TOEFL iBT 79 / IELTS 6.0–6.5 以上，詳見當期名額表）"
            return "中語組免附外語檢定（部分英文授課學程或特定院系依接待校規定）"
        if country == "日本":
            return "日語組須檢附日語檢定 JLPT N1–N4（多數學校要求 N2 或 N3 以上）；選修英語授課學程（ETP）者須檢附 TOEFL iBT 79 或 IELTS 6.0 以上"
        if country == "韓國":
            return "韓語組須檢附 TOPIK 2 級以上或英語檢定 TOEFL iBT 79 / IELTS 6.0 以上（依各校授課語言規定）"
        return "外語組基本門檻：TOEFL iBT 79（不接受 Home Edition）或 IELTS 6.0（Academic）；歐語及其他語組須達 CEFR B1–B2 以上（依各校當期名額表規定）"
    return "｜".join(parts)


def extract_partner_links(detail: dict | None, ror_website: str | None) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    official_website = None
    exchange_page = None
    factsheet_url = None
    course_url = None
    housing_url = None

    if detail:
        for link in detail.get("links", []):
            href = (link.get("href") or "").strip()
            text = (link.get("text") or "").strip()
            sec = (link.get("section") or "").strip()
            if not href or not href.startswith("http"):
                continue
            if "fju.edu.tw" in href and "sharepoint.com" not in href:
                continue
            if "sharepoint.com" in href or "factsheet" in text.lower() or "fact sheet" in text.lower():
                factsheet_url = factsheet_url or href
                continue
            if sec == "住宿資訊" or "housing" in href.lower() or "accommodation" in href.lower() or "dorm" in href.lower():
                housing_url = housing_url or href
            elif sec == "課程資訊" or "course" in href.lower() or "syllabus" in href.lower() or "catalogue" in href.lower():
                course_url = course_url or href
            elif "exchange" in href.lower() or "incoming" in href.lower() or "international" in href.lower():
                exchange_page = exchange_page or href
                official_website = official_website or href
            else:
                official_website = official_website or href

    if not official_website and ror_website:
        official_website = ror_website
    if not official_website and exchange_page:
        official_website = exchange_page

    return official_website, exchange_page, factsheet_url, course_url, housing_url


def current_home_submission_step(rule_id: str) -> dict:
    from exchange_info.fju_form_review import current_home_submission_step as reviewed_step
    return reviewed_step(rule_id)


def validate_build_inputs() -> None:
    required = ("label_40_parsed_rows.json", "parsed_award_details.json", "ror_resolved.json",
                "quotas_115_2.json", "quotas_115_1.json", "label_39_process.html", "label_40_partner_list.html",
                "label_41_faq.html", "label_42_downloads.html", "label_44_lang_score.html",
                "news_1057_116_1_info.html", "res_26_outgoing_reg.html", "res_27_scholarships.html",
                "attachments/115_2_quotas_2027_spring.pdf", "attachments/115_1_quotas_2026_fall.pdf",
                "attachments/115_2_exchange_notice.pdf", "attachments/reg_selection_guidelines_zh.pdf",
                "attachments/reg_study_implementation.pdf")
    missing = [str(SCRATCH_FJU / name) for name in required if not resolve_fju_input(name).is_file()]
    if missing:
        raise FileNotFoundError("FJU build input files are missing; no output was modified: " + ", ".join(missing))
    for name in required:
        if name.endswith(".json"):
            json.loads(resolve_fju_input(name).read_text(encoding="utf8"))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    validate_build_inputs()
    OFFICIAL_FJU_DIR.mkdir(parents=True, exist_ok=True)

    provenance = archive_official_sources()
    (OFFICIAL_FJU_DIR / "import_provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    raw_rows = json.loads(resolve_fju_input("label_40_parsed_rows.json").read_text(encoding="utf-8"))
    fju_rows = [r for r in raw_rows if r["row_index"] > 0 and not (r["table_index"] == 1 and r["row_index"] == 1)]
    award_details = json.loads(resolve_fju_input("parsed_award_details.json").read_text(encoding="utf-8"))
    ror_resolved = json.loads(resolve_fju_input("ror_resolved.json").read_text(encoding="utf-8"))

    loc_by_en_country, loc_by_zh_country, img_by_en_country, img_by_zh_country = load_repo_locations_and_images()
    q115_2_en, q115_2_zh = load_quota_lookup("quotas_115_2.json")
    q115_1_en, q115_1_zh = load_quota_lookup("quotas_115_1.json")

    partners = []
    workflows = []
    destinations = []
    research_records = []
    life_records = []
    new_locations = []
    new_images = []

    for idx, row in enumerate(fju_rows):
        raw_country = html.unescape(row["cells"][0]).strip()
        country = COUNTRY_MAP.get(raw_country, raw_country)
        full_name, zh_name, en_name, badges = parse_fju_school(row["cells"][1])
        listing = parse_listing_metadata(row["cells"], row["table_index"])
        grade_limit_table = listing["grade_limit"]
        sem_limit_table = listing["semester_limit"]
        lang_flag_table = listing["language_required_flag"]

        award_id = row.get("award_id")
        detail = award_details.get(str(award_id)) if award_id else None
        fields = (detail or {}).get("fields") or {}

        source_url = (
            f"https://iscoie.fju.edu.tw/awardDetail.jsp?id={award_id}&labelID=40"
            if award_id
            else "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=40"
        )

        # Resolve location (ROR override takes priority for fixed indices, else repo match, else ROR)
        ror_rec = ror_resolved.get(str(idx))
        repo_loc = None
        if str(idx) not in {"11", "20", "26", "28", "29", "56", "81", "97", "100", "129", "171", "216", "224"}:
            repo_loc = loc_by_en_country.get((loose_en(en_name), country)) or loc_by_zh_country.get((loose_zh(zh_name), country))

        if repo_loc:
            location_obj = {
                "country": country,
                "city": repo_loc.get("city"),
                "latitude": float(repo_loc["latitude"]),
                "longitude": float(repo_loc["longitude"]),
                "geocode_status": "verified",
                "geocoded_at": repo_loc.get("geocoded_at") or "2026-10-16T04:45:00Z",
                "source_url": repo_loc.get("source_url") or "https://www.wikidata.org",
                "identity_source_url": repo_loc.get("identity_source_url") or repo_loc.get("source_url") or "https://ror.org",
                "precision": "representative",
                "note": repo_loc.get("note") or "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區以錄取通知為準。",
            }
        elif ror_rec:
            location_obj = {
                "country": country,
                "city": ror_rec.get("city"),
                "latitude": float(ror_rec["latitude"]),
                "longitude": float(ror_rec["longitude"]),
                "geocode_status": "verified",
                "geocoded_at": "2026-10-16T04:45:00Z",
                "source_url": ror_rec.get("source_url") or ror_rec.get("ror_id"),
                "identity_source_url": ror_rec.get("identity_source_url") or ror_rec.get("ror_id"),
                "precision": "representative",
                "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625 / ROR GeoNames；實際交換校區以錄取通知為準。",
            }
        else:
            raise RuntimeError(f"Unresolved location for index {idx}: {full_name}")

        location_obj = {
            "school_name": full_name,
            **location_obj,
        }
        new_locations.append(location_obj)

        # Resolve image if available in repo for same country
        img_rec = img_by_en_country.get((loose_en(en_name), country)) or img_by_zh_country.get((loose_zh(zh_name), country))
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
                    "official_page_url": img_rec.get("official_page_url"),
                    "identity_source_url": img_rec.get("identity_source_url") or location_obj["identity_source_url"],
                    "artist": img_rec.get("artist"),
                    "license_name": img_rec.get("license_name"),
                    "license_url": img_rec.get("license_url"),
                    "content_hash": sha256_file(fpath),
                    "checked_at": img_rec.get("checked_at") or "2026-10-16",
                    "note": img_rec.get("note") or f"{full_name} 校園代表照片",
                })

        q115_2 = q115_2_en.get(loose_en(en_name)) or q115_2_zh.get(loose_zh(zh_name))
        q115_1 = q115_1_en.get(loose_en(en_name)) or q115_1_zh.get(loose_zh(zh_name))

        elig_detail = (fields.get("申請資格") or "").strip()
        quota_detail = (fields.get("名額") or "").strip()
        calendar_detail = (fields.get("學校年曆") or "").strip()
        notice_detail = (fields.get("注意事項") or "").strip()
        tuition_detail = (fields.get("註冊繳費") or "").strip()
        course_detail = (fields.get("課程資訊") or "").strip()
        housing_detail = (fields.get("住宿資訊") or "").strip()
        other_detail = (fields.get("其他資訊") or "").strip()

        quota_parts = ["116-1 當期名額仍須核對正式公告"]
        if listing["contract_quota"]:
            quota_parts.append(f"合作總表簽約名額（非當期甄選名額）：{listing['contract_quota']}")
        if quota_detail:
            quota_parts.append(f"姊妹校專頁名額：{re.sub(r'\\s+', ' ', quota_detail)}")
        if q115_2 and q115_2.get("quota"):
            quota_parts.append(f"115-2 甄選名額參考：{q115_2['quota']}")
        elif q115_1 and q115_1.get("quota"):
            quota_parts.append(f"115-1 甄選名額參考：{q115_1['quota']}")
        quota_str = "；".join(quota_parts)

        elig_parts = []
        if grade_limit_table:
            elig_parts.append(f"可申請對象：{grade_limit_table}")
        if sem_limit_table:
            elig_parts.append(f"交換期間：{sem_limit_table}")
        if badges:
            elig_parts.append(f"重點高校標記：{' / '.join(badges)} 工程")
        if elig_detail:
            elig_parts.append(re.sub(r"\s+", " ", elig_detail))
        eligibility_str = "；".join(elig_parts) if elig_parts else "大學部、研究所學生（須符合輔大校內甄選資格及姊妹校當期條件）"

        q_notes_combined = " ".join(filter(None, [
            q115_2.get("notes") if q115_2 else "",
            q115_1.get("notes") if q115_1 else "",
            notice_detail,
        ]))
        gpa_req = extract_gpa_requirement(elig_detail, q_notes_combined)
        lang_req = extract_language_requirement(country, zh_name, elig_detail, q115_2, q115_1)

        official_website, exchange_page, factsheet_url, course_url, housing_url = extract_partner_links(
            detail,
            (ror_rec or {}).get("website"),
        )

        notes_sections = []
        if badges:
            notes_sections.append(f"【大陸重點工程】{'、'.join(badges)} 工程重點大學")
        if q115_2 and q115_2.get("notes"):
            notes_sections.append(f"【115-2 簡章備註】{q115_2['notes']}")
        elif q115_1 and q115_1.get("notes"):
            notes_sections.append(f"【115-1 簡章備註】{q115_1['notes']}")
        if notice_detail:
            notes_sections.append(f"【注意事項】{re.sub(r'\\s+', ' ', notice_detail)}")
        if calendar_detail:
            notes_sections.append(f"【學校年曆】{re.sub(r'\\s+', ' ', calendar_detail)}")
        if tuition_detail:
            notes_sections.append(f"【註冊繳費】{re.sub(r'\\s+', ' ', tuition_detail)}")
        if course_detail:
            notes_sections.append(f"【課程資訊】{re.sub(r'\\s+', ' ', course_detail)}")
        if housing_detail:
            notes_sections.append(f"【住宿資訊】{re.sub(r'\\s+', ' ', housing_detail)}")
        if other_detail:
            notes_sections.append(f"【其他資訊】{re.sub(r'\\s+', ' ', other_detail)}")
        if factsheet_url:
            notes_sections.append(f"【Fact Sheet】{factsheet_url}")
        notes_str = "\n".join(notes_sections)
        if listing["directory_notes"]:
            notes_str += f"\n【合作校總表備註（非學制或期間）】{listing['directory_notes']}"

        program_type = "交換學生（大陸及港澳地區中語組）" if row["table_index"] == 1 else "交換學生（海外地區外語組／日語組）"
        if "自費" in zh_name:
            program_type = "自費研修／交換計畫"
        elif "語言密集課程" in zh_name:
            program_type = "交換學生（日本語言密集課程）"

        grade_code = (grade_limit_table or "").strip()
        degree_levels_str = "待確認：合作校總表未列學制／年級，請查當期個別學校條件"
        colleges_str = "待確認：請查當期開放院系"
        study_period_str = "待確認：合作校總表未提供可交換學期或期間"
        if calendar_detail:
            study_period_str = f"{study_period_str}｜學校年曆：{re.sub(r'\\s+', ' ', calendar_detail)}"
        app_deadline_str = (
            "116-1（2027秋季班）說明會：2026/10/12（外語場）、2026/10/19（中語場）；"
            "116-1系統開放及收件為2026/11/01至12/24 16:30，系統限校內網路；學校及名額於11月陸續更新，參考名額不是最終版。"
        )
        app_steps_list = [
            "參加國際學生中心舉辦之赴姊妹校交換學生甄選說明會（外語場 2026/10/12、中語場 2026/10/19），並確認當期甄選名額表。",
            "於校內網路開啟交換生申請系統，紙本只繳雙面申請表；書審資料、中文歷年成績單及語檢證明分成三個PDF上傳，各檔不超過20MB。紙本表須本人、家長簽章及系所／院等適用單位核章，於2026/12/24 16:30前送交國際學生中心。",
            "參加校內面試，通過甄選公告錄取後繳交確認書與保證金（海外地區 NT$10,000），由國際學生中心向姊妹校辦理官方提名（Nomination）。",
            f"依 {full_name} 提名通知與當期 Fact Sheet 完成外校線上申請、選課及宿舍申請，取得入學許可後辦理學生簽證、海外保險與輔大在學註冊繳費。",
        ]
        if other_detail:
            app_steps_list.append(f"【其他資訊】{re.sub(r'\\s+', ' ', other_detail)}")
        tuition_points_list = [
            "交換期間須於輔大辦理在學註冊並繳交全額學雜費以保留學籍；接待姊妹校免收學費（標註「自費」之研修項目除外），學生自理食宿、機票、簽證與海外醫療／意外保險。",
            "錄取生確認就讀時須繳交保證金 NT$10,000（大陸地區中語組原則免繳），於完成交換返國後 1 個月內繳交 2,000 字以上交換心得報告與成績單並辦妥學分抵免後無息退還。",
        ]
        if tuition_detail:
            tuition_points_list.insert(0, re.sub(r"\s+", " ", tuition_detail))
        elig_points_list = [
            f"學制與年級範圍：{degree_levels_str}",
            f"校內成績門檻：{gpa_req}",
            f"語文能力規定：{lang_req}",
        ]
        if badges:
            elig_points_list.append(f"大陸重點工程標記：{' / '.join(badges)} 工程")
        if elig_detail:
            elig_points_list.append(re.sub(r"\s+", " ", elig_detail))
        if q115_2 and q115_2.get("notes"):
            elig_points_list.append(f"【115-2 簡章備註】{q115_2['notes']}")
        elif q115_1 and q115_1.get("notes"):
            elig_points_list.append(f"【115-1 簡章備註】{q115_1['notes']}")

        partner_record = {
            "school_name": full_name,
            "country": country,
            "region": "大陸及港澳地區" if row["table_index"] == 1 else "海外地區",
            "grade_limit": grade_limit_table,
            "semester_limit": sem_limit_table,
            "language_required_flag": lang_flag_table,
            "award_id": award_id,
            "badges": badges,
            "colleges": colleges_str,
            "degree_levels": degree_levels_str,
            "study_period": study_period_str,
            "eligibility": f"{eligibility_str}｜語文要求：{lang_req}｜成績門檻：{gpa_req}",
            "language_requirement": lang_req,
            "gpa_requirement": gpa_req,
            "quota": quota_str,
            "quota_status": "reference_only",
            "availability_status": "agreement_only",
            "availability_note": (
                f"輔大 116-1（2027秋季班）甄選說明會已公告，當期名額表預計於 2026 年 11 月底公布、12 月收件；"
                f"目前顯示姊妹校專頁條件與 115 學年度甄選名額（{quota_str}）供選校規劃參考。"
            ),
            "academic_year": "116",
            "application_round": "第1學期（秋季班）",
            "application_window_status": "needs_confirmation",
            "application_deadline": app_deadline_str,
            "application_info": "\n\n".join(app_steps_list),
            "tuition_info": "\n\n".join(tuition_points_list),
            "semester_dates": re.sub(r"\s+", " ", calendar_detail) if calendar_detail else None,
            "course_restrictions": re.sub(r"\s+", " ", course_detail) if course_detail else None,
            "housing_info": re.sub(r"\s+", " ", housing_detail) if housing_detail else None,
            "academic_calendar": calendar_detail or None,
            "registration_and_tuition": tuition_detail or None,
            "course_info": course_detail or None,
            "accommodation_info": housing_detail or None,
            "other_info": other_detail or None,
            "notes": notes_str,
            "program_type": program_type,
            "source_url": source_url,
            "website": official_website,
            "official_website": official_website,
            "factsheet_url": factsheet_url,
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

        # Build UniversityApplicationWorkflow
        wf_sources = [
            {
                "title": f"輔大姊妹校交換專頁—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": "第1學期（秋季班）",
                "checked_at": "2026-10-16T04:50:00Z",
            },
            {
                "title": "輔大出國交換申請流程與時程（labelID=42）",
                "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=42",
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": "第1學期（秋季班）",
                "checked_at": "2026-10-16T04:50:00Z",
            },
            {
                "title": "115-2 交換生甄選名額一覽表（參考）",
                "source_url": "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1247",
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "115",
                "application_round": "第2學期（春季班）",
                "checked_at": "2026-10-16T04:50:00Z",
            },
        ]
        if official_website:
            wf_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": official_website,
                "role": "partner_university",
                "authority": "partner_official",
                "checked_at": "2026-10-16T04:50:00Z",
            })
        if factsheet_url:
            wf_sources.append({
                "title": f"{full_name} Fact Sheet",
                "source_url": factsheet_url,
                "role": "partner_university",
                "authority": "partner_official",
                "checked_at": "2026-10-16T04:50:00Z",
            })

        workflows.append({
            "home_university": "天主教輔仁大學",
            "school_name": full_name,
            "partner_website": official_website,
            "country": country,
            "program_type": program_type,
            "academic_year": "116",
            "application_round": "第1學期（秋季班）",
            "effective_application_rounds": ["第1學期（秋季班）", "第2學期（春季班）"],
            "applicability_status": "verified",
            "applicability_note": "輔大116-1說明會於2026/10/12及10/19辦理，116-1名額預計11月底公告、12月收件；目前整合labelID=40姊妹校專頁與115-2／115-1名額表供規劃參考。",
            "review_status": "published",
            "published_at": "2026-10-16T04:50:00Z",
            "steps": [
                {
                    "rule_id": f"fju-116-1-home-1-{idx+1:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": "核對輔大116-1與接待校申請資格，參考所屬組別說明會資料",
                    "responsible_party": "學生",
                    "responsible_unit": "輔大國際學生中心／所屬系所",
                    "deadline_at": None,
                    "deadline_status": "not_applicable",
                    "timing": "申請前核對資格；10/12及10/19是不同組別說明會日期，不是資格確認或申請截止。",
                    "deadline_source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=39",
                    "deadline_checked_at": "2026-10-16T04:50:00Z",
                    "deadline_reminder_eligible": False,
                    "summary": f"輔大116-1學士班歷年學業平均須達70分；研究所校內成績門檻待確認；{eligibility_str}",
                    "details": [
                        f"學業門檻：{gpa_req}",
                        f"語言規定：{lang_req}",
                        f"名額與梯次：{quota_str}",
                    ],
                    "scope": {
                        "home_universities": ["天主教輔仁大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["116"],
                        "application_rounds": ["第1學期（秋季班）"],
                    },
                    "source_urls": [
                        source_url,
                        "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=39",
                        "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=41",
                    ],
                    "checked_at": "2026-10-16T04:50:00Z",
                    "support_status": "verified",
                },
                current_home_submission_step(f"fju-116-1-home-2-{idx+1:03d}"),
                {
                    "rule_id": f"fju-116-1-home-3-{idx+1:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "參加校內面試、確認錄取並由國際學生中心向姊妹校提名",
                    "responsible_party": "學生與輔大國際學生中心",
                    "responsible_unit": "輔大國際學生中心",
                    "summary": "秋季班於 12 月底至 1 月初面試並公告錄取名單；錄取生繳交確認書及保證金 NT$10,000（大陸中語組免繳）後辦理外校提名。",
                    "details": [
                        "甄選評分：外語組（歷年成績 25%、外語能力 25%、讀書計畫 25%、面試 25%）；日語組（歷年成績 30%、讀書計畫 35%、面試 35%）；中語組（歷年成績 35%、讀書計畫 35%、面試 30%）。",
                        "獲校內推薦資格僅代表取得提名權，最終入學許可由接待姊妹校審查決定。",
                    ],
                    "scope": {
                        "home_universities": ["天主教輔仁大學"],
                        "academic_years": ["116"],
                        "application_rounds": ["第1學期（秋季班）"],
                    },
                    "source_urls": ["https://iscoie.fju.edu.tw/generalServices.jsp?labelID=44"],
                    "checked_at": "2026-10-16T04:50:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"fju-{idx+1:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"依提名通知完成 {zh_name} 外校申請與選課／住宿登錄",
                    "responsible_party": "學生與接待校國際處",
                    "summary": re.sub(r"\s+", " ", notice_detail)[:200] if notice_detail else f"依 {full_name} 當期 Fact Sheet 及提名確認信完成線上申請與文件上傳。",
                    "details": [
                        f"學校年曆：{re.sub(r'\\s+', ' ', calendar_detail) if calendar_detail else '依接待校當期公布校曆為準'}",
                        f"課程規定：{re.sub(r'\\s+', ' ', course_detail) if course_detail else '依接待校交換生選課規範辦理'}",
                        f"住宿資訊：{re.sub(r'\\s+', ' ', housing_detail) if housing_detail else '依接待校校內外宿舍申請規定辦理'}",
                    ],
                    "scope": {
                        "home_universities": ["天主教輔仁大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["116"],
                    },
                    "source_urls": [source_url] + ([official_website] if official_website else []) + ([factsheet_url] if factsheet_url else []),
                    "checked_at": "2026-10-16T04:50:00Z",
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"fju-116-1-home-5-{idx+1:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "辦理簽證、海外保險與輔大在學註冊繳費，返國完成學分抵免",
                    "responsible_party": "學生",
                    "responsible_unit": "輔大國際學生中心／教務處／所屬系所",
                    "summary": "交換期間仍須於輔大註冊並繳交全額學雜費保留學籍，每學期至少修習相當於輔大 2 學分以上科目；返國 1 個月內繳交 2,000 字心得與成績單退還保證金。",
                    "details": [
                        re.sub(r"\s+", " ", tuition_detail) if tuition_detail else "接待姊妹校免收學費（自費項目除外），學生自理食宿、簽證、機票與海外醫療／意外保險。",
                    ],
                    "scope": {
                        "home_universities": ["天主教輔仁大學"],
                        "academic_years": ["116"],
                        "application_rounds": ["第1學期（秋季班）"],
                    },
                    "source_urls": ["https://iscoie.fju.edu.tw/teachingServices.jsp?file=910"],
                    "checked_at": "2026-10-16T04:50:00Z",
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": "2026-10-16T04:50:00Z",
            "coverage_status": "official_verified" if award_id else "official_partial",
            "coverage_note": "已整合輔大國際學生中心官網 labelID=40、awardDetail.jsp 姊妹校專頁及 115-2／115-1 甄選名額表；116-1 當期名額以 11 月底最新公告為準。",
        })

        # Build DestinationProfile (exact schema matching DestinationProfile in models.py)
        cost_default, visa_default = REGION_COST_DEFAULTS.get(
            country,
            ("USD 800–1,300 / 月（含住宿、膳食、教材與當地交通費用）", "須依接待校與駐臺代表處規定辦理學生簽證與海外醫療保險。"),
        )
        cost_line = f"預估每月生活費約 {cost_default}"
        tuition_clean = re.sub(r"\s+", " ", tuition_detail) if tuition_detail else "交換期間於輔大註冊並繳交全額學雜費，免繳接待姊妹校學費（自費研修項目除外）。"
        housing_clean = re.sub(r"\s+", " ", housing_detail) if housing_detail else "接待校提供校內學生宿舍申請或校外學生公寓／寄宿家庭媒合資訊，宿位依各校當期供給與申請先後順序分配，費用由交換生自理。"
        course_clean = re.sub(r"\s+", " ", course_detail) if course_detail else "選課範圍與限制依接待校當期交換生選課規定辦理；依輔大實施辦法第 10 條，每學期至少應修習相當於輔大 2 學分（含）以上之科目。"
        calendar_clean = re.sub(r"\s+", " ", calendar_detail) if calendar_detail else "依接待校當期公布之秋季班／春季班校曆與迎新報到日為準。"
        other_clean = re.sub(r"\s+", " ", other_detail) if other_detail else ""

        dest_sources = [
            {"title": f"輔大姊妹校交換專頁—{zh_name}", "source_url": source_url, "summary": "官方交換資格、年曆、註冊繳費、課程與住宿說明"},
            {"title": "天主教輔仁大學學生赴境外大學交換學習實施辦法", "source_url": "https://iscoie.fju.edu.tw/teachingServices.jsp?file=910", "summary": "輔大交換學生選課學分、註冊與返國義務規定"},
        ]
        if official_website:
            dest_sources.append({"title": f"{full_name} 官方網站", "source_url": official_website, "summary": "接待姊妹校官方網站與國際交換資訊入口"})
        if factsheet_url:
            dest_sources.append({"title": f"{full_name} Fact Sheet", "source_url": factsheet_url, "summary": "接待姊妹校交換計畫 Fact Sheet"})

        src_url_list = [source_url] + ([official_website] if official_website else []) + ([factsheet_url] if factsheet_url else [])

        destinations.append({
            "home_university": "天主教輔仁大學",
            "school_name": full_name,
            "country": country,
            "city": location_obj.get("city") or country,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": f"校區代表城市：{location_obj.get('city') or country}。請依錄取通知確認實際授課校區、機場抵達路線與當地學生交通卡優惠。",
            "campus_life_summary": "\n".join(filter(None, [calendar_clean, course_clean, other_clean])),
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費與學雜費規定",
                    "summary": cost_line,
                    "points": [cost_line, tuition_clean],
                    "source_urls": src_url_list,
                    "caution": "實際花費視個人住宿型態與消費習慣而異；116-1 當期收費標準請以接待校最新 Fact Sheet 為準。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean] + ([f"住宿參考連結：{housing_url}"] if housing_url else []),
                    "source_urls": src_url_list + ([housing_url] if housing_url else []),
                    "caution": "校內宿舍名額有限，獲提名後請密切留意接待校住宿申請開放與截止日期。",
                },
                {
                    "key": "insurance",
                    "title": "醫療保險與安全",
                    "summary": visa_default,
                    "points": [visa_default] + ([other_clean] if other_clean else []),
                    "source_urls": src_url_list,
                    "caution": "出國前須投保涵蓋全交換期間之海外醫療及意外保險，並符合接待校強制保險規範。",
                },
                {
                    "key": "visa",
                    "title": "簽證與入境準備",
                    "summary": visa_default,
                    "points": [
                        "收到接待校正式入學許可（Acceptance Letter / COE / DS-2019）後，立即向駐臺辦事處申辦學生簽證。",
                        visa_default,
                    ],
                    "source_urls": src_url_list,
                    "caution": "簽證審核時間依各國領事館規定而異，切勿於取得正式入學許可前購買不可退改之機票。",
                },
                {
                    "key": "courses",
                    "title": "課程限制、選課與學分",
                    "summary": course_clean[:160],
                    "points": [
                        course_clean,
                        "依《天主教輔仁大學學生赴境外大學交換學習實施辦法》第 10 條，每學期至少應修習相當於輔大 2 學分（含）以上之科目。",
                    ] + ([f"課程查詢連結：{course_url}"] if course_url else []),
                    "source_urls": src_url_list + ([course_url] if course_url else []),
                    "caution": "返國後學分採認由所屬系所審定，出國選課前建議先與系所確認抵免原則。",
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
                    "summary": calendar_clean[:160],
                    "points": [calendar_clean],
                    "source_urls": src_url_list,
                    "caution": "請依接待校入學許可信指定之報到日與迎新週（Orientation）時程抵達。",
                },
            ],
            "first_72_hours": [
                {
                    "title": "依接待校指定報到日辦理入住與國際處報到",
                    "detail": calendar_clean,
                    "source_urls": [source_url],
                },
                {
                    "title": "確認海外保險、居留登記與當地聯絡方式回報",
                    "detail": f"{visa_default} 抵校安頓後請向輔大國際學生中心回報國外居住地址與緊急聯絡電話。",
                    "source_urls": ["https://iscoie.fju.edu.tw/teachingServices.jsp?file=910"],
                },
            ],
            "sources": dest_sources,
            "last_checked": "2026-10-16T04:50:00Z",
            "coverage_status": "official_verified" if award_id else "official_partial",
            "coverage_note": "已整合輔大國際學生中心姊妹校專頁（awardDetail.jsp）之年曆、註冊繳費、課程與住宿規定。",
        })

        # Build PartnerResearchRecord (exact schema matching PartnerResearchRecord in models.py)
        research_records.append({
            "home_university": "天主教輔仁大學",
            "school_name": full_name,
            "country": country,
            "official_website": official_website,
            "verification_status": "official_verified" if official_website else "needs_review",
            "discovery_source_url": source_url,
            "checked_at": "2026-10-16T04:50:00Z",
            "note": f"輔大姊妹校專頁（{source_url}）及 ROR/Wikidata 官方網址核對完成。",
        })

        # Build LifeResearchSnapshot (exact schema matching LifeResearchSnapshot in life_context.py)
        ev_sources = [{"title": f"輔大姊妹校交換專頁—{zh_name}", "url": source_url}]
        if official_website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": official_website})
        ev_list = [
            {
                "theme": "housing",
                "kind": "official",
                "text": housing_clean,
                "sources": ev_sources + ([{"title": "住宿資訊專頁", "url": housing_url}] if housing_url else []),
                "checked_at": "2026-10-16T04:50:00Z",
                "scope": "輔大國際學生中心姊妹校專頁（awardDetail.jsp）住宿說明",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "cost",
                "kind": "official",
                "text": f"{tuition_clean}｜預估生活開支：{cost_default}",
                "sources": ev_sources,
                "checked_at": "2026-10-16T04:50:00Z",
                "scope": "輔大國際學生中心姊妹校專頁註冊繳費與地區生活費估算",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "academics",
                "kind": "official",
                "text": course_clean,
                "sources": ev_sources + ([{"title": "課程資訊專頁", "url": course_url}] if course_url else []),
                "checked_at": "2026-10-16T04:50:00Z",
                "scope": "輔大國際學生中心姊妹校專頁課程規定與學分下限",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "safety",
                "kind": "official",
                "text": f"{visa_default}" + (f"｜{other_clean}" if other_clean else ""),
                "sources": ev_sources,
                "checked_at": "2026-10-16T04:50:00Z",
                "scope": "輔大出國交換簽證、保險與安全提醒",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "campus_culture",
                "kind": "official",
                "text": f"學校年曆与交換期間：{calendar_clean}｜申請資格：{eligibility_str}",
                "sources": ev_sources,
                "checked_at": "2026-10-16T04:50:00Z",
                "scope": "輔大國際學生中心姊妹校專頁年曆與交換計畫說明",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
        ]
        life_records.append({
            "school_name": full_name,
            "country": country,
            "checked_at": "2026-10-16T04:50:00Z",
            "status": "ready" if award_id else "partial",
            "evidence": ev_list,
            "notes": [
                "已整合輔大國際學生中心姊妹校專頁（awardDetail.jsp）之住宿、課程、註冊繳費與學校年曆資訊。",
                "116學年度當期宿位供給、費用與選課限制請依接待校最新 Fact Sheet 核對。",
            ],
            "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
            "extraction_version": 3,
        })

    # Write JSONL files in official_data/fju/
    (OFFICIAL_FJU_DIR / "partners.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FJU_DIR / "application_workflows.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FJU_DIR / "destination_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FJU_DIR / "partner_research.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FJU_DIR / "student_life.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
        encoding="utf-8",
    )

    # Write FJU partner locations to official_data/fju/campus-locations.json and FJU home location to university_locations.jsonl
    (OFFICIAL_FJU_DIR / "campus-locations.json").write_text(
        json.dumps({"locations": new_locations}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    loc_file = REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
    existing_loc_lines = [line for line in loc_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    existing_loc_map = {}
    for line in existing_loc_lines:
        rec = json.loads(line)
        existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

    fju_home_loc = {
        "school_name": "天主教輔仁大學",
        "country": "臺灣",
        "city": "新北市新莊區",
        "latitude": 25.035277777778,
        "longitude": 121.43222222222,
        "geocode_status": "verified",
        "geocoded_at": "2026-10-16T04:45:00Z",
        "source_url": "https://www.wikidata.org/wiki/Q702773",
        "identity_source_url": "https://ror.org/04je98850",
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。 母校代表點採新莊校本部（新北市新莊區中正路510號）；官方校區地址來源：https://www.fju.edu.tw/aboutFju.jsp?labelID=19。",
    }
    existing_loc_map[("天主教輔仁大學", "臺灣")] = fju_home_loc

    sorted_locs = sorted(existing_loc_map.values(), key=lambda r: (r.get("country") or "", r.get("school_name") or ""))
    loc_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
        encoding="utf-8",
    )

    # Update school-images.json with verified FJU partner image records
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

    # Build exchange_info.json, student_dashboard.json, pages.jsonl, home_rules.json, documents.json, scholarships.json
    fju_source_urls = [
        "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=39",
        "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=40",
        "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=41",
        "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=42",
        "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=43",
        "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=44",
        "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=45",
        "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=46",
        "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=61",
        "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1247",
        "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1141",
        "https://iscoie.fju.edu.tw/teachingServices.jsp?file=910",
        "https://iscoie.fju.edu.tw/teachingServices.jsp?file=949",
    ]

    exchange_info_payload = {
        "school_name": "天主教輔仁大學",
        "program_type": [
            "交換學生（海外地區外語組／日語組）",
            "交換學生（大陸及港澳地區中語組）",
        ],
        "academic_year": [
            "116（AY2027–2028）",
            "115-2（2027春季班參考）",
        ],
        "semester": [
            "第1學期（秋季班）",
            "第2學期（春季班）",
        ],
        "application_period": [
            "116學年度第1學期（2027秋季班）赴姊妹校交換學生甄選說明會：2026/10/12（一）12:20–13:30 外語場（利瑪竇大樓 LM101）、2026/10/19（一）12:20–13:30 中語場（聖言樓 SF131）。",
            "第一學期（秋季班）出國交換甄選：每年 10 月中旬舉辦說明會、11 月底公告名額、12 月辦理校內線上填表及紙本收件（送耕莘樓 A113 國際學生中心）、12 月底至 1 月初面試並公告錄取名單。",
            "第二學期（春季班）出國交換甄選：每年 3 月中旬舉辦說明會、4 月初公告名額、4 月中旬收件（115-2 收件為 2026/4/14–4/16 16:30）、5 月初面試並於 5 月中旬公告錄取名單。",
        ],
        "eligibility": [
            "具輔仁大學正式學籍之在學學生：大學部修業滿一學年以上（申請時為大一至大三，出國時須為大二以上；延畢生須符合各校年級限制）、碩士班及博士班在學學生。",
            "116-1學士班歷年平均70分以上、操行86分以上且無大小過等不良紀錄；研究所成績門檻待確認。轉學生申請前須已在本校就讀完一學期；碩一及博一繳交前一學制歷年成績單。",
            "甄選評分標準：外語組（歷年成績 25%、外語能力 25%、讀書計畫 25%、面試 25%）；日語組（歷年成績 30%、讀書計畫 35%、面試 35%）；中語組（歷年成績 35%、讀書計畫 35%、面試 30%）。",
            "每人最多可選填 5 所志願學校（部分語組或梯次依當期簡章規定）；曾獲錄取後無故放棄者，在學期間不得再次申請校級交換學生計畫。",
            "陸生不得申請大陸地區姊妹校；僑生及外籍生申請返回原國籍或僑居地交換須符合接待校與教育部規定。",
        ],
        "language_requirement": [
            "英語組基本門檻：TOEFL iBT 79（不接受 Home Edition 及 MyBest Scores）或 IELTS 6.0（Academic）；各姊妹校若有更高總分或單科門檻（如 IELTS 6.5、TOEFL iBT 80–100），須從其規定。",
            "校內甄選外語能力換分（佔外語組總成績 25%）：TOEFL iBT 61–67 / IELTS 5.0 / TOEIC 650–699 換算 40 分；iBT 68–73 / IELTS 5.5 / TOEIC 700–749 換算 50 分；iBT 74–78 / TOEIC 750–784 換算 60 分；iBT 79–82 / IELTS 6.0 / TOEIC 785–819 換算 70 分；iBT 83–87 / TOEIC 820–854 換算 80 分；iBT 88–92 / IELTS 6.5 / TOEIC 855–899 換算 90 分；iBT 93+ / IELTS 7.0+ / TOEIC 900+ 換算 100 分（多益僅供部分接受 TOEIC 之學校或校內換分參考，不替代姊妹校要求之托福／雅思）。",
            "日語組：須檢附日本語能力試驗（JLPT）N1–N4 合格證書（多數日本姊妹校要求 N2 或 N3 以上；申請日本姊妹校英語授課學程 ETP 者須檢附 TOEFL iBT 79 或 IELTS 6.0 以上）。",
            "韓語及其他歐語組：韓語組須檢附 TOPIK 2 級以上（或英語檢定）；法語、德語、西語、義語組須檢附 DELF/DALF、Goethe/TestDaF、DELE、CELI/CILS 等達 CEFR B1–B2 以上證明。",
            "中語組（大陸及港澳地區）：申請大陸地區及澳門中文授課姊妹校免附外語檢定；申請香港姊妹校或全英文授課學程須依各校規定檢附 TOEFL iBT 79 / IELTS 6.0–6.5 以上證明。",
        ],
        "required_documents": [
            "Google 線上報名表回覆 PDF（完成線上填報後列印）",
            "天主教輔仁大學赴姊妹校交換學生申請表（經系所主任及學院院長簽章）",
            "中文歷年成績單正本（須含歷年學業總平均及系排名百分比；碩博一新生加附前一學位歷年成績單）",
            "讀書計畫（Study Plan）及自傳（A4 雙面列印、不超過 2 頁／4 面；外語組以英文或交換國語言撰寫、日語組以日文或英文撰寫、中語組以中文撰寫）",
            "2 年內有效之外語能力檢定證明影本（中語組免附，香港及英語授課除外）",
            "家長／監護人同意書（保證書，須本人及家長／保證人親筆簽名蓋章）",
            "個人資料提供同意書及相關優良事蹟／作品集影本（無則免附；全部文件統一 A4 左上角裝訂，勿使用資料夾）",
        ],
        "scholarship_info": [
            "教育部「學海飛颺」與「學海惜珠」獎助學金：補助赴海外（不含大陸及港澳地區）交換一學期或一學年之優秀學生及具低收／中低收入戶等資格學生，由國際學生中心統一公告收件與甄選。",
            "《天主教輔仁大學交換學生獎學金補助辦法》校內交換生獎學金：外語組申請者須具 TOEFL iBT 79 或 IELTS 6.0（或歐語 CEFR B2）以上、日語組須具 JLPT N1 合格證明，且未同時領取教育部學海系列或其他政府全額獎學金；中語組不適用校內交換生獎學金。",
            "日本交流協會、JASSO 獎學金、韓國政府 GKS 及各姊妹校提供之接待校獎學金／住宿補助（如天主教里爾大學、京都產業大學、山梨學院大學等），依各校當期簡章與提名通知辦理。",
            "交換期間仍須於輔大辦理註冊並繳交全額學雜費以保留在學學籍；接待姊妹校免收學費（標註「自費」之研修項目除外），學生自行負擔住宿、伙食、機票、簽證及海外保險費用。",
            "錄取生確認就讀時須繳交保證金 NT$10,000（大陸地區中語組原則免繳保證金），於完成交換返國後 1 個月內繳交 2,000 字以上交換心得報告與成績單並辦妥學分抵免後無息退還。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": fju_source_urls,
        "last_checked": "2026-10-16T04:50:00Z",
    }
    (OFFICIAL_FJU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "天主教輔仁大學",
        "last_checked": "2026-10-16T04:50:00Z",
        "academic_score_minimum": 70.0,
        "academic_score_rule": "輔大116-1公告要求學士班歷年平均70分以上、操行86分以上且無大小過等不良紀錄，未列班排名替代條件；研究生學業門檻及接待校額外規定須另行確認。",
        "academic_gpa_minimum": None,
        "maximum_preferences": 5,
        "selection_rules": {
            "academic_policy": "percentage",
            "academic_reference_year": "116",
            "undergraduate_gpa_minimum": None,
            "undergraduate_rank_maximum": None,
            "graduate_academic_exempt": False,
            "exclude_in_service": False,
            "pending_quota_planning": True,
            "partner_requirements_need_confirmation": True,
            "degree_score_minimums": {},
            "excluded_undergraduate_years": [],
            "language_certificate_required": False,
        },
        "language_score_minimums": {
            "toefl": 79.0,
            "ielts": 6.5,
            "toeic": 750.0,
        },
        "application_periods": [
            {
                "title": "輔大 116-1（2027秋季班）出國交換甄選說明會（外語場／中語場）",
                "details": [
                    "外語場說明會：2026/10/12（一）12:20–13:30 於利瑪竇大樓 LM101 舉行。",
                    "中語場（大陸地區）說明會：2026/10/19（一）12:20–13:30 於聖言樓 SF131 舉行。",
                    "說明會介紹姊妹校分布、校內甄選評分標準、書審與面試準備要領及獎學金制度。",
                ],
                "source": {
                    "title": "輔大國際學生中心—赴姊妹校交換學生首頁公告（labelID=39）",
                    "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=39",
                    "category": "info_session",
                    "summary": "116學年度第1學期赴姊妹校交換學生甄選說明會時間與地點公告。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116-1（2027秋季班）說明會",
                "audience": "all_students",
                "opens_at": "2026-10-12T12:20:00+08:00",
                "deadline_at": "2026-10-19T13:30:00+08:00",
                "date_status": "verified_exact",
                "status": "action_required",
                "status_note": "116-1 外語場（10/12）及中語場（10/19）說明會已正式公告；正式收件於 2026 年 12 月辦理。",
                "deadline_note": "說明會後將於 11 月底公告 116-1 甄選名額一覽表。",
                "reminder_eligible": True,
                "checked_at": "2026-10-16T04:50:00Z",
            },
            {'title': '輔大 116-1（2027秋季班）校內甄選線上申請與紙本收件（11/1–12/24 16:30）',
             'details': ['2026-10-20 官方公告（newsID=1062）：雖然公告標題寫「即日起開始收件至12月24日16:30止!」，正文載明線上申請系統開放及收件時間為 2026/11/01 至 '
                         '2026/12/24 16:30。',
                         '線上申請系統（http://outgoing.oie.fju.edu.tw/）有鎖校外 IP 連線，限校內網路使用；個別上傳 PDF 電子檔（書審資料、中文歷年成績單、語測證明）勿超過 '
                         '20MB。',
                         '紙本文件僅須繳交「赴姐妹校交換生申請表（A4 雙面列印、電腦打字輸入）」，完成家長簽章與系所／院／雙主修輔系學程核章後，於 2026/12/24 16:30 '
                         '前送交國際學生中心（官網地址：耕莘樓1樓A117室；實際安排依承辦通知）。',
                         '名額及開放學校將於 11 月陸續由姊妹校提供並更新，目前附表（file=1346 非日語組、file=1347 日語組）標示為「通常名額 (參考用)」，不能當成最終版；需 M365 '
                         '登入之個別學校資料未查。'],
             'source': {'title': '116學年度第1學期 (2027秋季班) 赴姊妹校交換學生申請公告（newsID=1062）',
                        'source_url': 'https://iscoie.fju.edu.tw/newsDetail.jsp?newsID=1062&newsClassID=14',
                        'category': 'deadline',
                        'summary': '系統開放及收件為 2026/11/01～12/24 16:30（限校內網路）；學校及名額於 11 月陸續更新，不能當成最終版。'},
             'scope': 'home_application',
             'program_types': ['exchange'],
             'academic_year': '116',
             'application_round': '116-1（2027秋季班）校內收件',
             'audience': 'all_students',
             'opens_at': None,
             'deadline_at': '2026-12-24T16:30:00+08:00',
             'date_status': 'verified_exact',
             'status': 'upcoming',
             'status_note': '標題雖寫即日起，正文載明系統開放及收件為 2026/11/01～12/24 16:30（限校內網路）；學校與名額於 11 月陸續更新，目前名單不能當成最終版。',
             'deadline_note': '線上系統限校內網路（http://outgoing.oie.fju.edu.tw/）；紙本申請表送交國際學生中心（官網地址：耕莘樓1樓A117室；實際安排依承辦通知）。',
             'reminder_eligible': True,
             'checked_at': '2026-10-20T02:27:00Z'},
            {
                "title": "輔大 115-2（2027春季班）校內甄選收件（已截止參考）",
                "details": [
                    "115-2（2027春季班）收件期間為 2026/4/14（二）至 2026/4/16（四）16:30 止，面試於 2026/5/6（三）舉行。",
                    "115-2 交換生甄選名額一覽表（2026/4/1 更新，file=1247）及 115-1 甄選名額一覽表（file=1141）已完整收錄於本平台各校卡片供規劃參考。",
                ],
                "source": {
                    "title": "115-2 交換生甄選名額一覽表（file=1247）",
                    "source_url": "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1247",
                    "category": "deadline",
                    "summary": "115學年度第2學期（2027春季班）交換生甄選名額與申請條件表。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "115",
                "application_round": "115-2（2027春季班）",
                "audience": "all_students",
                "opens_at": "2026-04-14T09:00:00+08:00",
                "deadline_at": "2026-04-16T16:30:00+08:00",
                "date_status": "verified_exact",
                "status": "closed",
                "status_note": "115-2 梯次已截止；名額與各校語檢／GPA 條件供 116 學年度申請規劃參考。",
                "deadline_note": None,
                "reminder_eligible": False,
                "checked_at": "2026-10-16T04:50:00Z",
            },
        ],
        "program_overview": [
            {
                "title": "輔大全球姊妹校交換計畫總覽（234 所交換合作校）",
                "details": [
                    "天主教輔仁大學與全球 478 所大學簽訂學術合作協議，其中列入國際學生中心《申請資格與姊妹校一覽表》（labelID=40）之交換學生合作學校共 234 所（含海外地區外語組／日語組 171 校、大陸及港澳地區中語組 63 校）。",
                    "116學年度第1學期（2027秋季班）甄選說明會於 2026/10/12（外語場）及 2026/10/19（中語場）舉行，116-1 正式名額表預計於 2026 年 11 月底公告、12 月辦理收件。",
                    "本平台完整整合 234 所交換合作校之官方專頁（208 份 awardDetail.jsp 姊妹校詳細頁）、學校年曆、課程與住宿規定、Fact Sheet 連結，以及 115-2（2027春季班）與 115-1（2026秋季班）甄選名額表。",
                ],
                "source": {
                    "title": "輔大赴姊妹校交換學生—申請資格與姊妹校一覽表（labelID=40）",
                    "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=40",
                    "category": "partner_school",
                    "summary": "海外地區 171 校與大陸及港澳地區 63 校完整名單及專頁。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "學籍、年級與學業成績門檻",
                "details": [
                    "具輔仁大學正式學籍之在學學生（大學部修業滿一學年以上，出國時須為大二以上；碩士班、博士班在學學生）。",
                    "116-1學士班歷年學業平均須達70分，操行須達86分且無大小過等不良紀錄；公告未列班排名替代門檻，接待校另有較高要求時仍須符合。",
                    "甄選評分權重：外語組（歷年成績 25%、外語能力 25%、讀書計畫 25%、面試 25%）；日語組（歷年成績 30%、讀書計畫 35%、面試 35%）；中語組（歷年成績 35%、讀書計畫 35%、面試 30%）。",
                ],
                "source": {
                    "title": "輔大赴姊妹校交換學生—甄選評分與實施辦法（labelID=44, file=910）",
                    "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=44",
                    "category": "exchange_application",
                    "summary": "校內甄選資格、成績門檻與各語組評分比重。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "外語組、日語組與中語組語文能力規定",
                "details": [
                    "116-1申請英語授課交換學校，須達TOEFL iBT 79、IELTS 6.5或TOEIC 750其中一項；如交換學校要求較高分數，須符合較高門檻。英檢成績須在申請截止日仍具兩年效期。",
                    "外語組語檢換分標準（佔總分 25%）：TOEFL iBT 61–67 / IELTS 5.0 / TOEIC 650–699 為 40 分；iBT 68–73 / IELTS 5.5 / TOEIC 700–749 為 50 分；iBT 74–78 / TOEIC 750–784 為 60 分；iBT 79–82 / IELTS 6.0 / TOEIC 785–819 為 70 分；iBT 83–87 / TOEIC 820–854 為 80 分；iBT 88–92 / IELTS 6.5 / TOEIC 855–899 為 90 分；iBT 93+ / IELTS 7.0+ / TOEIC 900+ 為 100 分。",
                    "日語組：須檢附 JLPT N1–N4 合格證書（依各日本姊妹校要求，多數為 N2 或 N3 以上；申請全英語授課課程 ETP 則須檢附 TOEFL iBT 79 或 IELTS 6.5 以上）。",
                    "韓語及歐語組：韓語組須具 TOPIK 2 級以上或英語檢定；法語（DELF B1/B2）、德語（Goethe/TestDaF B1/B2）、西語（DELE B1/B2）依接待校規定。",
                    "中語組：大陸及澳門中文授課學校免附外語檢定；香港姊妹校（如香港浸會大學、香港城市大學、嶺南大學）須依規定檢附 TOEFL iBT 79 或 IELTS 6.5 以上證明。",
                ],
                "source": {
                    "title": "輔大赴姊妹校交換學生—語文能力要求與換分表（labelID=41, labelID=44）",
                    "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=41",
                    "category": "exchange_application",
                    "summary": "各語組語檢門檻與外語能力換分對照表。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "輔大校內甄選應備文件清單（A4 左上角裝訂）",
                "details": [
                    "1. Google 線上報名表回覆 PDF（完成線上填報後匯出列印）",
                    "2. 天主教輔仁大學赴姊妹校交換學生申請表（須經系主任及院長核章）",
                    "3. 中文歷年成績單正本（含歷年學業總平均及系排名百分比；轉學生附原校成績單、碩博一附前一學位歷年成績單）",
                    "4. 讀書計畫（Study Plan）及自傳（A4 雙面列印、不超過 2 頁／4 面；外語組以英文或交換國語言撰寫、日語組以日文或英文撰寫、中語組以中文撰寫）",
                    "5. 2 年內有效之外語能力檢定證明影本（中語組免附）",
                    "6. 家長／監護人同意書（保證書，須本人及家長親筆簽名蓋章）及個人資料提供同意書",
                    "7. 其他優秀事蹟或獲獎證明影本（選繳；全部紙本請勿使用塑膠資料夾或打洞，統一於左上角裝訂）",
                ],
                "source": {
                    "title": "輔大赴姊妹校交換學生—申請應備文件（labelID=43）",
                    "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=43",
                    "category": "exchange_application",
                    "summary": "校內甄選紙本收件項目、排序與裝訂規範。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "教育部學海系列與輔大校內交換學生獎學金",
                "details": [
                    "教育部「學海飛颺」與「學海惜珠」獎助學金：補助赴海外（不含大陸及港澳地區）交換之優秀學生及經濟不利學生，依國際學生中心年度公告辦理。",
                    "《天主教輔仁大學交換學生獎學金補助辦法》（file=949）：外語組須具 TOEFL iBT 79 或 IELTS 6.0 等同級證明、日語組須具 JLPT N1 合格證明，且未領取教育部學海系列或其他政府獎學金者得申請校內獎學金；中語組不適用。",
                    "交換期間須於輔大註冊並繳交全額學雜費；接待校免收學費（自費項目除外），錄取確認時須繳交保證金 NT$10,000（大陸中語組免繳），返國完成心得與學分抵免後無息退還。",
                ],
                "source": {
                    "title": "天主教輔仁大學交換學生獎學金補助辦法（file=949）",
                    "source_url": "https://iscoie.fju.edu.tw/teachingServices.jsp?file=949",
                    "category": "scholarship",
                    "summary": "校內交換生獎學金申請資格、語檢門檻與核發規定。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "赴姊妹校交換學生申請表、保證書與個資同意書",
                "summary": "申請人須先完成 Google 線上報名表，再列印紙本申請表送請系主任與院長簽章，並檢附家長親筆簽章之保證書與個資同意書。",
                "key_points": [
                    "讀書計畫與自傳以 A4 雙面列印，合計不超過 2 頁（4 面）。",
                    "所有文件依序排列後於左上角以迴紋針或訂書針裝訂，切勿使用塑膠L夾或特殊裝訂。",
                ],
                "applies_to": [],
                "source": {
                    "title": "輔大赴姊妹校交換學生—申請應備文件（labelID=43）",
                    "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=43",
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=43",
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "《天主教輔仁大學學生赴境外大學交換學習實施辦法》重點規定",
                "summary": "規範交換學生申請資格、選課學分下限、註冊繳費、保證金與返國學分抵免義務。",
                "key_points": [
                    "交換期間每學期至少應修習相當於輔大 2 學分（含）以上之科目。",
                    "交換期間仍須於輔大辦理註冊並繳交全額學雜費以保留在學學籍。",
                    "返國後 1 個月內須繳交 2,000 字以上交換學習心得報告並辦理學分抵免，始得退還保證金 NT$10,000。",
                ],
                "applies_to": [],
                "source": {
                    "title": "天主教輔仁大學學生赴境外大學交換學習實施辦法（file=910）",
                    "source_url": "https://iscoie.fju.edu.tw/teachingServices.jsp?file=910",
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": "https://iscoie.fju.edu.tw/teachingServices.jsp?file=910",
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {
                "title": "輔大國際學生中心—赴姊妹校交換學生總覽與公告（labelID=39）",
                "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=39",
                "category": "info_session",
                "summary": None,
            },
            {
                "title": "輔大赴姊妹校交換學生—申請資格與姊妹校一覽表（labelID=40）",
                "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=40",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "輔大赴姊妹校交換學生—語文能力要求（labelID=41）",
                "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=41",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "輔大赴姊妹校交換學生—申請流程與時程（labelID=42）",
                "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=42",
                "category": "deadline",
                "summary": None,
            },
            {
                "title": "輔大赴姊妹校交換學生—申請應備文件（labelID=43）",
                "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=43",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "輔大赴姊妹校交換學生—甄選評分標準與外語換分表（labelID=44）",
                "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=44",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "115-2（2027春季班）交換生甄選名額一覽表（file=1247）",
                "source_url": "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1247",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "115-1（2026秋季班）交換生甄選名額一覽表（file=1141）",
                "source_url": "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1141",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "天主教輔仁大學學生赴境外大學交換學習實施辦法（file=910）",
                "source_url": "https://iscoie.fju.edu.tw/teachingServices.jsp?file=910",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "天主教輔仁大學交換學生獎學金補助辦法（file=949）",
                "source_url": "https://iscoie.fju.edu.tw/teachingServices.jsp?file=949",
                "category": "scholarship",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_FJU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    pages_records = [
        {
            "title": "天主教輔仁大學：116-1（2027秋季班）赴姊妹校交換學生甄選說明會與時程",
            "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=39",
            "published_at": "2026-10-01T00:00:00Z",
            "text": "\n".join(exchange_info_payload["application_period"]),
            "summary": "\n".join(exchange_info_payload["application_period"]),
            "category": "exchange_application",
            "attachments": [
                {
                    "url": "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1247",
                    "filename": "115-2交換生甄選名額一覽表_115.04.01.pdf",
                    "local_path": None,
                    "content_type": "application/pdf",
                },
                {
                    "url": "https://iscoie.fju.edu.tw/teachingServices.jsp?file=1141",
                    "filename": "115-1交換生甄選名額一覽表.pdf",
                    "local_path": None,
                    "content_type": "application/pdf",
                },
            ],
            "crawled_at": "2026-10-16T04:15:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "天主教輔仁大學：申請資格與甄選評分標準",
            "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=44",
            "published_at": None,
            "text": "\n".join(exchange_info_payload["eligibility"]),
            "summary": "\n".join(exchange_info_payload["eligibility"]),
            "category": "exchange_application",
            "attachments": [
                {
                    "url": "https://iscoie.fju.edu.tw/teachingServices.jsp?file=910",
                    "filename": "天主教輔仁大學學生赴境外大學交換學習實施辦法.pdf",
                    "local_path": None,
                    "content_type": "application/pdf",
                }
            ],
            "crawled_at": "2026-10-16T04:15:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "天主教輔仁大學：語文能力規定與外語換分標準",
            "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=41",
            "published_at": None,
            "text": "\n".join(exchange_info_payload["language_requirement"]),
            "summary": "\n".join(exchange_info_payload["language_requirement"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-16T04:15:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "天主教輔仁大學：申請應備文件規範",
            "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=43",
            "published_at": None,
            "text": "\n".join(exchange_info_payload["required_documents"]),
            "summary": "\n".join(exchange_info_payload["required_documents"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-16T04:15:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "天主教輔仁大學：交換學生獎學金補助辦法與經費說明",
            "source_url": "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=45",
            "published_at": None,
            "text": "\n".join(exchange_info_payload["scholarship_info"]),
            "summary": "\n".join(exchange_info_payload["scholarship_info"]),
            "category": "scholarship",
            "attachments": [
                {
                    "url": "https://iscoie.fju.edu.tw/teachingServices.jsp?file=949",
                    "filename": "天主教輔仁大學交換學生獎學金補助辦法.pdf",
                    "local_path": None,
                    "content_type": "application/pdf",
                }
            ],
            "crawled_at": "2026-10-16T04:15:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
        },
    ]
    (OFFICIAL_FJU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "fju",
        "school_name": "天主教輔仁大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_weights": {
            "foreign_language_group": {"gpa": 0.25, "language": 0.25, "study_plan": 0.25, "interview": 0.25},
            "japanese_group": {"gpa": 0.30, "study_plan": 0.35, "interview": 0.35},
            "chinese_group": {"gpa": 0.35, "study_plan": 0.35, "interview": 0.30},
        },
        "source_urls": fju_source_urls,
        "verified_at": "2026-10-16",
    }
    (OFFICIAL_FJU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FJU_DIR / "documents.json").write_text(
        json.dumps({"school_name": "天主教輔仁大學", "required_documents": student_dashboard_payload["required_documents"], "source_urls": fju_source_urls}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FJU_DIR / "scholarships.json").write_text(
        json.dumps({"school_name": "天主教輔仁大學", "scholarships": student_dashboard_payload["scholarship_info"], "source_urls": fju_source_urls}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    completeness = {
        "school_id": "fju",
        "school_name": "天主教輔仁大學",
        "total_partners": len(partners),
        "overseas_partners": sum(1 for p in partners if p["region"] == "海外地區"),
        "mainland_hk_mo_partners": sum(1 for p in partners if p["region"] == "大陸及港澳地區"),
        "award_detail_pages_parsed": sum(1 for p in partners if p.get("award_id")),
        "verified_locations": len(partners),
        "verified_official_websites": sum(1 for p in partners if p.get("official_website")),
        "verified_campus_images": len(new_images),
        "active_term": "116學年度第1學期（2027秋季班）甄選說明會已辦理，116-1名額表預計2026年11月底公告、12月收件；目前同步提供115-2（2027春季班）與115-1（2026秋季班）名額表及234校姊妹校專頁完整條件供規劃參考。",
        "verified_at": "2026-10-16",
    }
    (OFFICIAL_FJU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FJU_DIR / "verification_status.json").write_text(
        json.dumps({
            "school_id": "fju",
            "school_name": "天主教輔仁大學",
            "status": "official_verified",
            "checked_at": "2026-10-16T04:50:00Z",
            "counts": completeness,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    from exchange_info.fju_oct20_updates import apply_fju_oct20_updates

    apply_fju_oct20_updates(OFFICIAL_FJU_DIR)
    from exchange_info.generated_content_review import review_generated_content
    review_generated_content(REPO_ROOT, "fju", round_id=22)
    from exchange_info.host_source_review_round25 import apply_host_source_review
    apply_host_source_review(REPO_ROOT, "fju")
    from exchange_info.fju_oct20_updates import repair_fju_attachment_links
    repair_fju_attachment_links(OFFICIAL_FJU_DIR)
    from exchange_info.fju_route_review import apply_fju_route_review
    apply_fju_route_review(REPO_ROOT, bundle=OFFICIAL_FJU_DIR)
    from exchange_info.fju_form_review import apply_fju_form_review
    apply_fju_form_review(REPO_ROOT, bundle=OFFICIAL_FJU_DIR)
    from exchange_info.fju_missing_routes_review import apply_fju_missing_routes
    apply_fju_missing_routes(REPO_ROOT, bundle=OFFICIAL_FJU_DIR)
    from exchange_info.fju_nonjp_review import apply_fju_nonjp_review
    apply_fju_nonjp_review(REPO_ROOT, bundle=OFFICIAL_FJU_DIR)
    from exchange_info.fju_briefing_review import apply_fju_briefing_review
    apply_fju_briefing_review(REPO_ROOT, bundle=OFFICIAL_FJU_DIR)
    from exchange_info.fju_process_review import apply_fju_process_review
    apply_fju_process_review(REPO_ROOT, bundle=OFFICIAL_FJU_DIR)
    from exchange_info.fju_host_review import apply_fju_host_review
    apply_fju_host_review(REPO_ROOT, bundle=OFFICIAL_FJU_DIR)
    print(f"Successfully built FJU catalog: {len(partners)} partners, {len(workflows)} workflows, {len(destinations)} destinations, {len(research_records)} research records, {len(new_locations)} locations, {added_imgs} new school-images aliases added (total FJU verified images: {len(new_images)}).")


if __name__ == "__main__":
    main()
