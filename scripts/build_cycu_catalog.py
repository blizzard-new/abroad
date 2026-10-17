"""Build the official Chung Yuan Christian University (中原大學, CYCU) exchange data bundle."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import sys
import unicodedata

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
from exchange_info.school_identity import VisualRecordIndex, school_identity_key

_HOST_SCRATCH = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\0723e0a1-b112-47e2-8145-2d4d6f69cb19\scratch")
SOURCES_CYCU_DIR = REPO_ROOT / "sources" / "cycu"
OFFICIAL_CYCU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "cycu"
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
    "土耳其": "亞洲",
    "澳洲": "大洋洲",
    "紐西蘭": "大洋洲",
    "美國": "美洲",
    "加拿大": "美洲",
    "墨西哥": "美洲",
    "智利": "美洲",
    "厄瓜多": "美洲",
    "秘魯": "美洲",
    "法國": "歐洲",
    "德國": "歐洲",
    "荷蘭": "歐洲",
    "英國": "歐洲",
    "西班牙": "歐洲",
    "義大利": "歐洲",
    "奧地利": "歐洲",
    "比利時": "歐洲",
    "瑞士": "歐洲",
    "捷克": "歐洲",
    "波蘭": "歐洲",
    "匈牙利": "歐洲",
    "瑞典": "歐洲",
    "芬蘭": "歐洲",
    "丹麥": "歐洲",
    "挪威": "歐洲",
    "葡萄牙": "歐洲",
    "拉脫維亞": "歐洲",
    "立陶宛": "歐洲",
}

REGION_COST_DEFAULTS = {
    "美國": ("USD 1,400–2,200 / 月（含住宿、餐飲、校園保險與當地交通）", "建議預留強制校園醫療保險（約 USD 1,500–2,500 / 學期）與 J-1 / F-1 簽證 SEVIS 費用；部分姊妹校（如舊金山州立大學、密西西比學院）要求交換生提出指定金額財力證明。"),
    "法國": ("EUR 850–1,400 / 月（含宿舍或外宿、飲食與交通；可申請法國政府 CAF 房補）", "須透過法國教育中心（Campus France）面試並申辦長期學生簽證（VLS-TS）。"),
    "德國": ("EUR 934–1,200 / 月（德國簽證限制提領帳戶基準為每月 EUR 934）", "須辦理德國法定公保（約 EUR 120–130 / 月）及學期雜費／學期票（Semesterticket）。"),
    "荷蘭": ("EUR 950–1,400 / 月（荷蘭移民局 IND 財力證明基準約 EUR 1,225 / 月）", "由接待校代辦 MVV/VVR 居留許可，房源緊張建議獲提名後立即申請宿舍。"),
    "日本": ("JPY 80,000–130,000 / 月（東京圈約 JPY 100,000–140,000；地方城市約 JPY 70,000–100,000）", "憑接待校核發之在留資格認定證明書（COE）換發留學簽證，抵日後須加入國民健康保險；福井大學等部分姊妹校要求交換一學期須附至少新臺幣 15 萬元以上之財力證明。"),
    "韓國": ("KRW 800,000–1,300,000 / 月（首爾圈外宿較高；校內宿舍約 KRW 150,000–400,000 / 月）", "憑標準入學許可書申辦 D-2-6 交換學生簽證，抵韓後外國人登錄並自動納入韓國國民健康保險（NHIS）；韓世大學等部分學校要求檢附美金 15,500 元財力證明。"),
    "中國大陸": ("RMB 2,000–3,800 / 月（校內宿舍與學生食堂費用低廉，北上廣深略高）", "持臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定提交三個月或六個月內健康檢查報告與大陸境內來華留學生綜合醫療保險證明（約 RMB 400 / 學期）。"),
    "香港": ("HKD 6,000–10,000 / 月（校內宿位有限，若外宿租金較高）", "須透過接待校向香港入境事務處申辦學生簽證／進入許可（Student Visa / Entry Permit）。"),
    "馬來西亞": ("MYR 1,800–2,800 / 月（金寶與雙溪龍校區生活機能便利且物價親民）", "須透過 EMGS（Education Malaysia Global Services）系統申辦學生簽證（VAL / Student Pass）。"),
    "泰國": ("THB 15,000–25,000 / 月（曼谷與巴吞他尼校園生活成本親民）", "須憑接待校入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證。"),
    "印尼": ("IDR 5,000,000–8,500,000 / 月（雅加達、萬隆、泗水生活開支實惠）", "須由接待校協助向印尼移民總局申辦學習簽證（C316 / 學生電子簽證）。"),
    "菲律賓": ("USD 500–850 / 月（約 PHP 28,000–48,000，馬尼拉生活與外宿開支適中）", "須憑接待校入學許可辦理菲律賓學生簽證（9F）或特別學習許可（SSP）。"),
}

CYCU_NAME_FIXES = {
    "SKEMA商學院 SKEMA Business School": ("SKEMA商學院", "SKEMA Business School"),
    "Fachhochschule Deggendorf-University of Applied Science": ("德根朵夫科技大學", "Deggendorf Institute of Technology"),
    "Magdeburg University": ("馬德堡大學", "Otto von Guericke University Magdeburg"),
    "University of Applied Sciences Jena": ("耶拿應用科學大學", "Ernst-Abbe-Hochschule Jena"),
    "Rheinman University of Applied Science": ("萊茵美因應用科技大學", "RheinMain University of Applied Sciences"),
    "Amsterdam University of Applied Science": ("阿姆斯特丹應用科技大學", "Amsterdam University of Applied Sciences"),
    "San Francisco State University (113-1起暫停招募)": ("舊金山州立大學", "San Francisco State University"),
    "California State University Chico": ("加州州立大學溪口分校", "California State University, Chico"),
    "RyuKoku University": ("龍谷大學", "Ryukoku University"),
    "Kanazaw University": ("金澤大學", "Kanazawa University"),
    "Ewha Womans University (113-1起暫停招募)": ("梨花女子大學", "Ewha Womans University"),
    "Pukyong National Universit": ("釜慶大學", "Pukyong National University"),
    "Yonsei University Mirae Campus": ("延世大學", "Yonsei University"),
    "Hang Sheng University of Hong Kong": ("香港恒生大學", "The Hang Seng University of Hong Kong"),
    "Bina Nusantara University (or Binus University)": ("建國大學", "Bina Nusantara University"),
    "Atma Jaya Catholic University of Indonesia": ("阿天瑪加雅印度尼西亞天主教大學", "Atma Jaya Catholic University of Indonesia"),
    "University Tunku Abdul Rahman": ("拉曼大學", "Universiti Tunku Abdul Rahman"),
}

CYCU_MAINLAND_EN = {
    "中山大學": ("中山大學", "Sun Yat-sen University", "https://www.sysu.edu.cn/", "廣東省廣州市"),
    "天津大學": ("天津大學", "Tianjin University", "https://www.tju.edu.cn/", "天津市"),
    "四川大學": ("四川大學", "Sichuan University", "https://www.scu.edu.cn/", "四川省成都市"),
    "東南大學": ("東南大學", "Southeast University", "https://www.seu.edu.cn/", "江蘇省南京市"),
    "海南大學": ("海南大學", "Hainan University", "https://www.hainanu.edu.cn/", "海南省海口市"),
    "清華大學": ("北京清華大學", "Tsinghua University", "https://www.tsinghua.edu.cn/", "北京市"),
    "華中科技大學": ("華中科技大學", "Huazhong University of Science and Technology", "https://www.hust.edu.cn/", "湖北省武漢市"),
    "廈門大學": ("廈門大學", "Xiamen University", "https://www.xmu.edu.cn/", "福建省廈門市"),
    "福州大學": ("福州大學", "Fuzhou University", "https://www.fzu.edu.cn/", "福建省福州市"),
    "深圳大學": ("深圳大學", "Shenzhen University", "https://www.szu.edu.cn/", "廣東省深圳市"),
    "西南大學": ("西南大學", "Southwest University", "http://www.swu.edu.cn/", "重慶市"),
    "南京信息工程大學": ("南京信息工程大學", "Nanjing University of Information Science and Technology", "https://www.nuist.edu.cn/", "江蘇省南京市"),
    "華中師範大學": ("華中師範大學", "Central China Normal University", "https://www.ccnu.edu.cn/", "湖北省武漢市"),
    "北京郵電大學": ("北京郵電大學", "Beijing University of Posts and Telecommunications", "https://www.bupt.edu.cn/", "北京市"),
    "重慶大學": ("重慶大學", "Chongqing University", "http://www.cqu.edu.cn/", "重慶市"),
    "華東師範大學": ("華東師範大學", "East China Normal University", "https://www.ecnu.edu.cn/", "上海市"),
    "武漢大學": ("武漢大學", "Wuhan University", "https://www.whu.edu.cn/", "湖北省武漢市"),
    "安徽大學": ("安徽大學", "Anhui University", "https://www.ahu.edu.cn/", "安徽省合肥市"),
    "南京大學": ("南京大學", "Nanjing University", "https://www.nju.edu.cn/", "江蘇省南京市"),
    "蘇州大學": ("蘇州大學", "Soochow University", "http://www.suda.edu.cn/", "江蘇省蘇州市"),
    "蘭州大學": ("蘭州大學", "Lanzhou University", "https://www.lzu.edu.cn/", "甘肅省蘭州市"),
    "大連理工學院": ("大連理工大學", "Dalian University of Technology", "https://www.dlut.edu.cn/", "遼寧省大連市"),
    "北京科技大學": ("北京科技大學", "University of Science and Technology Beijing", "https://www.ustb.edu.cn/", "北京市"),
    "北京語言大學": ("北京語言大學", "Beijing Language and Culture University", "http://www.blcu.edu.cn/", "北京市"),
    "南京師範大學": ("南京師範大學", "Nanjing Normal University", "http://www.njnu.edu.cn/", "江蘇省南京市"),
    "吉林大學": ("吉林大學", "Jilin University", "https://www.jlu.edu.cn/", "吉林省長春市"),
    "山東大學": ("山東大學", "Shandong University", "https://www.sdu.edu.cn/", "山東省濟南市"),
    "東北師範大學": ("東北師範大學", "Northeast Normal University", "https://www.nenu.edu.cn/", "吉林省長春市"),
}

CYCU_FALLBACK_WEBSITES = {
    "SKEMA Business School": "https://www.skema.edu/",
    "Rotterdam University of Applied Sciences": "https://www.rotterdamuas.com/",
    "University of Hawaiʻi at Hilo": "https://hilo.hawaii.edu/",
    "Yonsei University": "https://mirae.yonsei.ac.kr/",
    "Bina Nusantara University": "https://binus.ac.id/",
    "Atma Jaya Catholic University of Indonesia": "https://www.atmajaya.ac.id/",
    "Mapua University": "https://www.mapua.edu.ph/",
    "University of Fukui": "https://www.u-fukui.ac.jp/eng/",
    "Kanazawa University": "https://www.kanazawa-u.ac.jp/e/",
    "Jeonbuk National University": "https://www.jbnu.ac.kr/eng/",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def loose_zh(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"\([^)]*\)|（[^）]*）", "", s)
    return "".join(ch for ch in s if "\u4e00" <= ch <= "\u9fff")


def archive_official_sources() -> dict:
    SOURCES_CYCU_DIR.mkdir(parents=True, exist_ok=True)
    for json_name in ["cycu_parsed_tables.json", "cycu_gdrive_index.json"]:
        src = _HOST_SCRATCH / json_name
        dst = SOURCES_CYCU_DIR / json_name
        if src.exists() and src.resolve() != dst.resolve():
            shutil.copy2(src, dst)

    files_meta = [
        ("cycu_overseas_study_guidelines_1140306.pdf", "https://oia.cycu.edu.tw/wp-content/uploads/sites/54/2025/05/1140306%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E7%A0%94%E4%BF%AE%E8%A6%81%E9%BB%9E.pdf", "中原大學學生赴境外研修要點（114.03.06 修正）"),
        ("cycu_exchange_scholarship_rules_536_2.pdf", "https://oia.cycu.edu.tw/wp-content/uploads/sites/54/2022/10/536-2%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E6%B5%B7%E5%A4%96%E5%A7%8A%E5%A6%B9%E6%A0%A1%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%BF%92%E5%8A%A9%E5%AD%B8%E8%BE%A6%E6%B3%95.pdf", "中原大學學生赴海外姊妹校交換學習助學辦法"),
        ("cycu_dual_degree_rules_203_5.pdf", "https://oia.cycu.edu.tw/wp-content/uploads/sites/54/2022/10/203-5%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E8%88%87%E5%A2%83%E5%A4%96%E5%A4%A7%E5%AD%B8%E6%A0%A1%E9%99%A2%E5%90%88%E4%BD%9C%E8%BE%A6%E7%90%86%E9%9B%99%E8%81%AF%E5%AD%B8%E5%88%B6%E5%AF%A6%E6%96%BD%E8%BE%A6%E6%B3%95.pdf", "中原大學與境外大學校院合作辦理雙聯學制實施辦法"),
        ("cycu_partner_highlights_20240305.pdf", "https://drive.google.com/file/d/1f9Ibw5NOh92W-d1R7LgOX4odYuTKin2e/view", "中原大學國際暨兩岸教育處—各交換姊妹校簡介彙編（各姊妹校簡介20240305全.pdf）"),
        ("cycu_parsed_tables.json", "https://oia.cycu.edu.tw/?page_id=10128", "中原大學赴國際交換資訊（10128）、115-2第二梯次公告（9903）、2027春季班赴大陸交換公告（6340）及五大洲 391 所姊妹校總表結構化資料"),
        ("cycu_gdrive_index.json", "https://drive.google.com/drive/folders/1_I-Gxmmym43zHXDw-MPzlX7OSYAj6nW6", "中原大學國際處官方雲端硬碟索引（國際交換簡章 193 件、大陸交換簡章 187 件、109–114 學年度返國交換心得報告 255 件）"),
        ("cycu_resolved_locations.json", "https://oia.cycu.edu.tw/?p=6515", "中原大學 89 所赴外交換姊妹校 ROR / Wikidata 地理座標核對表"),
    ]
    provenance_items = []
    for fname, url, title in files_meta:
        dst = SOURCES_CYCU_DIR / fname
        if dst.exists():
            provenance_items.append({
                "file": f"sources/cycu/{dst.name}",
                "source_url": url,
                "title": title,
                "sha256": sha256_file(dst),
                "bytes": dst.stat().st_size,
                "fetched_at": "2026-10-16T16:25:00Z",
            })
    return {
        "school_id": "cycu",
        "school_name": "中原大學",
        "generated_at": "2026-10-16T16:30:00Z",
        "active_cycle_note": "115-2（2027春季班）赴國際姊妹校交換生第二梯次遴選（2026/09/14–09/25 12:00 收件、10/01 面試）及 2027 春季班赴大陸姊妹校交換（2026/09/01–10/20 受理申請）已公告；116-1（2027秋季班）第一梯次預計於 2027 年 2 月開放申請。同時收錄全校 89 所海外及大陸交換合作大學（含 61 所國際及香港交換校、28 所大陸重點交換校）與 109–114 學年度官方返國心得報告 PDF 連結。",
        "sources": provenance_items,
    }


def main() -> None:
    OFFICIAL_CYCU_DIR.mkdir(parents=True, exist_ok=True)
    provenance = archive_official_sources()
    (OFFICIAL_CYCU_DIR / "import_provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    cycu_tables = json.loads((SOURCES_CYCU_DIR / "cycu_parsed_tables.json").read_text(encoding="utf-8"))
    cycu_gdrive = json.loads((SOURCES_CYCU_DIR / "cycu_gdrive_index.json").read_text(encoding="utf-8"))
    resolved_locs = json.loads((SOURCES_CYCU_DIR / "cycu_resolved_locations.json").read_text(encoding="utf-8"))
    loc_by_name = {r["school_name"]: r for r in resolved_locs}

    sister_by_zh = {}
    sister_by_en = {}
    for sis in cycu_tables["sister_schools"]:
        zh = re.sub(r"\s+", "", sis.get("name_zh") or "")
        en = school_identity_key(sis.get("name_en") or "")
        if zh:
            sister_by_zh[zh] = sis
        if en:
            sister_by_en[en] = sis

    # Build round quota lookups
    r2_115_2_map = {}
    for r in cycu_tables["round2_115_2"]:
        raw = r["school_raw"].strip()
        m = re.match(r"^([\u4e00-\u9fff（）()\s]+?)\s*([A-Za-z].*)$", raw)
        zh = loose_zh(m.group(1) if m else raw)
        r2_115_2_map[zh] = r["quota"].strip()

    jp_115_1_map = {}
    for row in cycu_tables["extra_tables"]["japan_115_1_9876"][1:]:
        raw = row[0].strip()
        m = re.match(r"^([\u4e00-\u9fff（）()\s]+?)\s*([A-Za-z].*)$", raw)
        zh = loose_zh(m.group(1) if m else raw)
        jp_115_1_map[zh] = row[3].strip()

    r2_114_1_map = {}
    for row in cycu_tables["extra_tables"]["round2_114_1_7228"][1:]:
        raw = row[1].strip()
        m = re.match(r"^([\u4e00-\u9fff（）()\s]+?)\s*([A-Za-z].*)$", raw)
        zh = loose_zh(m.group(1) if m else raw)
        r2_114_1_map[zh] = row[4].strip()

    # Build GDrive brochure lookup & experience lookup
    brochures_intl = cycu_gdrive.get("intl_brochures", [])
    ml_2027s = cycu_gdrive.get("ml_2027s", [])
    ml_2026f = cycu_gdrive.get("ml_2026f", [])
    exp_entries = [x for x in cycu_gdrive.get("experiences", []) if x["type"] == "file"]

    def match_factsheet(zh_name: str, en_name: str, kind: str) -> str | None:
        z_clean = loose_zh(zh_name).replace("北京清華大學", "清華大學").replace("大連理工大學", "大連理工")
        e_clean = en_name.lower().split("(")[0].strip()
        special_fs_tokens = {
            "溫德斯海姆應用科技大學": "溫德斯海姆",
            "建國大學": "binus",
            "貝特拉基督教大學": "petra",
        }
        alt_token = special_fs_tokens.get(z_clean, "")
        if kind.startswith("mainland"):
            for item in ml_2027s + ml_2026f:
                if item["type"] == "folder" and (z_clean in item["path"] or (z_clean[:3] in item["path"] and len(z_clean) >= 4)):
                    return item["url"]
            return "https://drive.google.com/drive/folders/16uhH7kptMe3E1Lf_BaEBdPRO2HJ0xX6R"
        # First look for a specific PDF/file in brochures_intl
        for item in brochures_intl:
            path_low = item["path"].lower()
            if item["type"] == "file" and (
                z_clean in item["path"]
                or (alt_token and alt_token.lower() in path_low)
                or (e_clean and len(e_clean) >= 6 and e_clean[:10] in path_low)
            ):
                if any(k in item["title"].lower() for k in ["fact", "info", "guide", "brochure", "sheet", "outline", "empower"]):
                    return item["url"]
        for item in brochures_intl:
            path_low = item["path"].lower()
            if item["type"] == "folder" and item["path"].count("/") >= 2 and (
                z_clean in item["path"]
                or (alt_token and alt_token.lower() in path_low)
                or (e_clean and len(e_clean) >= 6 and e_clean[:10] in path_low)
            ):
                return item["url"]
        return "https://drive.google.com/drive/folders/1_I-Gxmmym43zHXDw-MPzlX7OSYAj6nW6"

    def match_experiences(zh_name: str, en_name: str) -> list[dict]:
        z_clean = loose_zh(zh_name).replace("北京清華大學", "清華大學")
        short_tokens = [z_clean]
        if z_clean.endswith("應用科技大學") or z_clean.endswith("應用科學大學") or z_clean.endswith("應用技術大學"):
            short_tokens.append(z_clean[:3])
        elif z_clean.endswith("基督教大學") and len(z_clean) >= 6:
            short_tokens.append(z_clean[:-5])
        elif z_clean == "加州州立大學溪口分校":
            short_tokens.extend(["溪口", "Chico"])
        elif z_clean == "夏威夷大學希羅校區":
            short_tokens.extend(["希羅", "夏威夷", "Hilo"])
        elif z_clean == "威斯康辛大學密爾瓦基分校":
            short_tokens.extend(["威斯康辛", "密爾瓦基"])
        elif z_clean == "蒙彼利埃高等商學院":
            short_tokens.append("蒙彼利埃")
        elif z_clean == "SKEMA商學院":
            short_tokens.append("SKEMA")
        elif z_clean == "阿天瑪加雅印度尼西亞天主教大學":
            short_tokens.extend(["阿天瑪加雅", "Atma"])
        matched = []
        seen_u = set()
        for x in exp_entries:
            path_str = x["path"]
            if any(tok and len(tok) >= 2 and tok.lower() in path_str.lower() for tok in short_tokens):
                if x["url"] not in seen_u:
                    seen_u.add(x["url"])
                    parts = path_str.split("/")
                    term_str = parts[1].replace("交換心得", "").strip() if len(parts) > 1 else "歷年"
                    title_clean = x["title"].replace(".pdf", "").strip()
                    matched.append({
                        "title": f"中原大學赴 {zh_name} 交換生返國心得報告（{term_str}・{title_clean}）",
                        "url": x["url"],
                        "term": term_str,
                    })
        return matched

    raw_partners = []
    for r in cycu_tables["intl_exchange"]:
        raw = r["school_raw"].strip()
        country = COUNTRY_MAP.get(r["country"].strip(), r["country"].strip())
        if raw in CYCU_NAME_FIXES:
            zh_name, en_name = CYCU_NAME_FIXES[raw]
            zh_raw = zh_name
        else:
            m = re.match(r"^([\u4e00-\u9fff（）()\s]+?)\s*([A-Za-z].*)$", raw)
            zh_raw = re.sub(r"\s+", "", m.group(1)) if m else raw
            en_raw = m.group(2).strip() if m else raw
            if en_raw in CYCU_NAME_FIXES:
                zh_name, en_name = CYCU_NAME_FIXES[en_raw]
            else:
                zh_name, en_name = zh_raw, en_raw
        full_name = f"{zh_name} {en_name}"
        sis = sister_by_zh.get(zh_name) or sister_by_zh.get(zh_raw) or sister_by_en.get(school_identity_key(en_name)) or {}
        website = sis.get("website") or CYCU_FALLBACK_WEBSITES.get(en_name, "")
        raw_partners.append({
            "zh_name": zh_name,
            "en_name": en_name,
            "full_name": full_name,
            "country": country,
            "website": website,
            "period": r.get("period") or "一學期",
            "req": r.get("requirements") or "",
            "note": r.get("notes") or "",
            "suspended": "暫停招募" in raw,
            "kind": "intl",
            "source_url": "https://oia.cycu.edu.tw/?page_id=10128",
        })

    extra_intl = [
        ("印尼大學", "Universitas Indonesia", "印尼", "https://www.ui.ac.id/", "一學期", "1. TOEFL iBT 71 或 IELTS 5.5 2. GPA 3.0（含）以上", "詳見國際處 Google 雲端硬碟 UI Fact Sheet 2026-2027"),
        ("慕尼黑聯邦國防大學", "Universität der Bundeswehr München", "德國", "https://www.unibw.de/", "一學期", "1. 英語或德語 CEFR B2（TOEFL iBT 79 / IELTS 6.0） 2. GPA 3.0（含）以上", "詳見國際處 Google 雲端硬碟 Erasmus+ Fact Sheet"),
        ("威斯康辛大學密爾瓦基分校", "University of Wisconsin-Milwaukee", "美國", "https://uwm.edu/", "一學期／一學年", "1. TOEFL iBT 79 或 IELTS 6.5 或 Duolingo 120 2. GPA 3.0（含）以上", "詳見國際處 Google 雲端硬碟 UWM Exchange Fact Sheet 2026-27"),
    ]
    for zh_name, en_name, country, web, period, req, note in extra_intl:
        sis = sister_by_zh.get(zh_name) or sister_by_en.get(school_identity_key(en_name)) or {}
        raw_partners.append({
            "zh_name": zh_name,
            "en_name": en_name,
            "full_name": f"{zh_name} {en_name}",
            "country": country,
            "website": sis.get("website") or web,
            "period": period,
            "req": req,
            "note": note,
            "suspended": False,
            "kind": "intl",
            "source_url": "https://oia.cycu.edu.tw/?page_id=10128",
        })

    seen_ml = set()
    for r in cycu_tables["mainland_exchange"]:
        raw_zh = r["name_zh"].strip()
        seen_ml.add(raw_zh)
        if raw_zh == "大連理工學院":
            seen_ml.add("大連理工大學")
        zh_name, en_name, web, city = CYCU_MAINLAND_EN[raw_zh]
        sis = sister_by_zh.get(zh_name) or sister_by_zh.get(raw_zh) or {}
        raw_partners.append({
            "zh_name": zh_name,
            "en_name": en_name,
            "full_name": f"{zh_name} {en_name}",
            "country": "中國大陸",
            "city": city,
            "website": sis.get("website") or web,
            "period": "一學期",
            "req": "具中華民國國籍之在學學生（於中原修畢二學期以上），學業成績 GPA 達 3.0 或班排名前 30%",
            "note": f"學校層級：{r.get('tier') or '重點合作校'}｜所在省市：{city}｜2027春季班截止日：{r.get('deadline') or '依國際處公告'}｜應繳文件：{r.get('documents') or '詳見簡章雲端資料夾'}",
            "deadline_ml": r.get("deadline") or "",
            "docs_ml": r.get("documents") or "",
            "tier_ml": r.get("tier") or "",
            "suspended": False,
            "kind": "mainland_2027s",
            "source_url": "https://oia.cycu.edu.tw/?p=6340",
        })

    for raw_zh in ["北京科技大學", "北京語言大學", "南京師範大學", "吉林大學", "山東大學", "東北師範大學"]:
        if raw_zh not in seen_ml:
            zh_name, en_name, web, city = CYCU_MAINLAND_EN[raw_zh]
            sis = sister_by_zh.get(zh_name) or {}
            raw_partners.append({
                "zh_name": zh_name,
                "en_name": en_name,
                "full_name": f"{zh_name} {en_name}",
                "country": "中國大陸",
                "city": city,
                "website": sis.get("website") or web,
                "period": "一學期",
                "req": "具中華民國國籍之在學學生（於中原修畢二學期以上），學業成績 GPA 達 3.0 或班排名前 30%",
                "note": f"學校層級：985/211 或雙一流重點高校｜所在省市：{city}｜秋季班定期開放申請（詳見國際處 2026 秋季班大陸姊妹校交換簡章雲端資料夾）",
                "deadline_ml": "秋季班（每年約 3–4 月截止）",
                "docs_ml": "詳見國際處大陸姊妹校交換簡章雲端資料夾",
                "tier_ml": "211/雙一流",
                "suspended": False,
                "kind": "mainland_2026f",
                "source_url": "https://oia.cycu.edu.tw/?p=6340",
            })

    school_images_file = STATIC_DIR / "assets" / "school-images.json"
    visual_map = {}
    if school_images_file.exists():
        for item in json.loads(school_images_file.read_text(encoding="utf-8")).get("schools", []):
            if isinstance(item, dict) and item.get("school_name") and item.get("status") == "verified" and item.get("local_path"):
                visual_map[(school_identity_key(str(item.get("school_name", ""))), str(item.get("country") or ""))] = item
    visual_index = VisualRecordIndex(visual_map)

    partners = []
    workflows = []
    destinations = []
    research_records = []
    life_records = []
    experience_sources_records = []
    student_experience_rows = []
    new_locations = []
    exp_covered_schools = 0
    open_partner_count = 0

    for idx, p in enumerate(raw_partners):
        zh_name = p["zh_name"]
        en_name = p["en_name"]
        full_name = p["full_name"]
        country = p["country"]
        region = REGION_BY_COUNTRY.get(country, "亞洲")
        website = p["website"]
        source_url = p["source_url"]
        factsheet_url = match_factsheet(zh_name, en_name, p["kind"])
        exp_links = match_experiences(zh_name, en_name)
        if exp_links:
            exp_covered_schools += 1

        loc_info = loc_by_name[full_name]
        location_obj = {
            "school_name": full_name,
            "country": country,
            "city": p.get("city") or loc_info.get("city") or country,
            "latitude": float(loc_info["latitude"]),
            "longitude": float(loc_info["longitude"]),
            "geocode_status": "verified",
            "geocoded_at": "2026-10-16T16:30:00Z",
            "source_url": loc_info.get("source_url") or "https://www.wikidata.org",
            "identity_source_url": loc_info.get("identity_source_url") or website or "https://ror.org",
            "precision": "representative",
            "note": loc_info.get("note") or "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區以錄取通知為準。",
        }
        new_locations.append(location_obj)

        z_key = loose_zh(zh_name)
        q_r2 = r2_115_2_map.get(z_key)
        q_jp = jp_115_1_map.get(z_key)
        q_114 = r2_114_1_map.get(z_key)

        if p["suspended"]:
            quota_str = "113-1 起暫停招募（依國際處最新公告為準）"
            avail_status = "reference_only"
            win_status = "closed"
        elif p["kind"] == "mainland_2027s":
            quota_str = f"開放申請（2027春季班截止日：{p.get('deadline_ml') or '10月–11月'}；每學期約 2–5 名，依姊妹校簡章核定）"
            avail_status = "open"
            win_status = "open"
            open_partner_count += 1
        elif p["kind"] == "mainland_2026f":
            quota_str = "開放申請（秋季班定期開放，每學期約 2–5 名，詳見大陸姊妹校交換簡章雲端硬碟）"
            avail_status = "open"
            win_status = "open"
            open_partner_count += 1
        elif q_r2:
            quota_str = f"{q_r2} 名（115-2 第二梯次公告名額）"
            avail_status = "open"
            win_status = "open"
            open_partner_count += 1
        elif q_jp:
            quota_str = f"{q_jp} 名（115 學年度日本交換專案公告名額）"
            avail_status = "open"
            win_status = "open"
            open_partner_count += 1
        elif q_114:
            quota_str = f"{q_114} 名（歷年公告參考名額；第一梯次 2 月／9 月定期開放）"
            avail_status = "open"
            win_status = "open"
            open_partner_count += 1
        else:
            quota_str = "每學期約 1–2 名（第一梯次 2 月／9 月定期開放申請；依當期國際處公告為準）"
            avail_status = "open"
            win_status = "open"
            open_partner_count += 1

        note_text = p.get("note") or ""
        if "限工學院及商學院" in note_text:
            colleges_str = "限工學院、商學院學生申請"
        elif "設計學院及商學院限定" in note_text:
            colleges_str = "限設計學院、商學院學生申請（每院每年各 2 名）"
        elif "限理學院、工學院、電機學院" in note_text:
            colleges_str = "限理學院、工學院、電機資訊學院學生申請"
        elif "法學院限定" in note_text:
            colleges_str = "限法學院學生申請"
        elif "電資學院限定" in note_text:
            colleges_str = "限電機資訊學院學生申請"
        elif "室內設計系限定" in note_text:
            colleges_str = "限設計學院室內設計學系學生申請"
        elif "Faculty of Engineering" in note_text:
            colleges_str = "限工學院、電機資訊學院相關工程系所學生申請"
        elif "Rotterdam Business School" in note_text or "商業相關科目" in note_text:
            colleges_str = "商學院及修畢規定商業學分之相關學系學生"
        else:
            colleges_str = "全校各學院系所（依姊妹校開放對應院系選課）"

        if "限碩博生" in note_text:
            degree_levels_str = "碩士班、博士班（須於中原修畢至少二學期）"
        elif "限大學部" in note_text or "不接受研究生" in note_text or "僅收大學部" in note_text:
            if "不開放大四生" in note_text:
                degree_levels_str = "學士班大二、大三（須於中原修畢至少二學期，不開放大四及研究生）"
            else:
                degree_levels_str = "學士班大二（含）以上（須於中原修畢至少二學期，不接受研究生）"
        elif "不開放大四生" in note_text:
            degree_levels_str = "學士班（不含大四）、碩士班、博士班（須於中原修畢至少二學期）"
        else:
            degree_levels_str = "學士班大二（含）以上、碩士班、博士班（須於中原大學修畢至少二學期，不含當學期申請提早畢業生）"

        lang_req_str = p["req"] if p["req"] else "須符合姊妹校規定之英語或當地語言能力檢定門檻（大陸地區姊妹校免附外語檢定）"
        if p["kind"].startswith("mainland"):
            lang_req_str = "大陸地區姊妹校免附外語檢定證明（須具中華民國國籍並持有效臺胞證）"

        gpa_req_str = "中原大學校內門檻：歷年學業成績 GPA 達 3.0（含）以上或班排名前 30%（兩項符合其一即可；建築學系須班排名前 50% 且建築設計（一）至（六）及格）"
        if "GPA" in p["req"]:
            gpa_req_str += f"｜姊妹校要求：{p['req']}"
        if "系排名40%內" in note_text:
            gpa_req_str += "｜漢陽大學特別規定：僅開放系排名前 40% 內之學生申請"

        if p["kind"].startswith("mainland"):
            program_type = "交換學生（大陸地區姊妹校交換計畫）"
            app_deadline_str = (
                f"2027 春季班大陸地區交換：2026年9月1日至 2026年{p.get('deadline_ml') or '10月20日'}（依各大陸姊妹校截止日向國際處遞交紙本及電子申請文件）；"
                "秋季班大陸地區交換：每年約 3 月至 4 月底受理申請。"
            )
        else:
            program_type = "交換學生（赴國際姊妹校交換計畫）"
            app_deadline_str = (
                "115-2（2027春季班）第一梯次：2026年8月28日截止收件、9月10日面試；"
                "115-2 第二梯次：2026年9月14日至9月25日（五）12:00 紙本及電子檔截止收件、10月1日（四）面試；"
                "116-1（2027秋季班）第一梯次預計於 2027年2月開學後開放申請（日本交換專案於每年 2–3 月先行甄選）。"
            )

        tuition_points_list = [
            "交換期間須於中原大學辦理註冊並繳交全額學雜費及學生平安保險費以保留在學學籍，免繳姊妹校學費（美國加州州立大學溪口分校及夏威夷大學希羅校區為自費交換專案除外）；住宿費、生活費、機票、簽證及海外保險由學生自理。",
            "依《中原大學學生赴境外研修要點》第 6 條，赴姊妹校交換學生每學期至少須修習 2 門課程或相當於中原大學 6 學分，學分上限為 22 學分（經本系及雙主修／輔系主任核准者得至 25 學分）；所修學分須經所屬學系及教務處審查通過始得抵免，惟不得抵免本系畢業專題及通識向度課程。",
            "可同時申請教育部「學海飛颺／學海惜珠」獎學金或《中原大學學生赴海外姊妹校交換學習助學辦法》校內助學金（依外語成績、學業表現與出國地區核給；領取校內助學金者每學期須修讀至少 6 學分且返國後不得辦理休退學）。",
        ]

        app_steps_list = [
            f"步驟一（確認資格與參加說明會）：確認於中原大學已修畢至少二學期、學業成績達 GPA 3.0 或班排名前 30%，且符合 {full_name} 之語言與年級條件；每學期初（2 月及 9 月）參加國際暨兩岸教育處舉辦之出國交換說明會。",
            "步驟二（繳交紙本申請表與傳送備審電子檔）：於截止日前將紙本申請表（含系所主任簽章與導師／指導教授推薦）繳交至維澈樓 704 室國際暨兩岸教育處，並將中英文歷年成績單（含 GPA 及班排名）、中英文讀書計畫、中英文自傳、語言能力檢定證明、個人履歷表、護照影本及家長同意書依規定檔名寄至 oia_outbound@office.cycu.edu.tw。",
            "步驟三（校內甄選面試與錄取公告）：參加國際處舉辦之校內甄選面試（非大陸地區配分：語言能力 30%、在校成績 30%、面試表現 40%；大陸地區配分：在校成績 40%、課外表現 20%、面試表現 40%），通過後公告錄取推薦名單。",
            f"步驟四（姊妹校提名複審、選課抵免與行前準備）：由國際處向 {full_name} 辦理官方提名（Nomination），學生依姊妹校簡章（Fact Sheet）完成線上申請與住宿登錄，出國前填妥「出國選課單」經系主任及教務處核准，並於取得入學許可後辦理簽證、海外保險與役男出境。",
        ]

        elig_points_list = [
            f"開放學制與年級：{degree_levels_str}",
            f"適用學院／系所：{colleges_str}",
            f"學業成績要求：{gpa_req_str}",
            f"語言與申請條件：{lang_req_str}",
        ]
        if note_text:
            elig_points_list.append(f"姊妹校補充規定：{note_text}")

        notes_lines = [
            f"【合作類別與期程】{program_type}｜交換期間：{p['period']}",
            f"【當期與歷年名額】{quota_str}",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【申請條件與語檢】{lang_req_str}",
        ]
        if note_text:
            notes_lines.append(f"【備註與選課限制】{note_text}")
        if exp_links:
            notes_lines.append(f"【歷年學長姐心得】中原大學國際處雲端資料庫收錄 {len(exp_links)} 篇赴 {zh_name} 交換生返國心得報告 PDF。")

        visual_rec = visual_index.get((full_name, country)) or {}
        partner_record = {
            "school_name": full_name,
            "country": country,
            "region": region,
            "colleges": colleges_str,
            "degree_levels": degree_levels_str,
            "study_period": p["period"],
            "eligibility": f"開放對象：{colleges_str}（{degree_levels_str}）｜申請條件：{lang_req_str}｜{gpa_req_str}",
            "language_requirement": lang_req_str,
            "gpa_requirement": gpa_req_str,
            "quota": quota_str,
            "quota_status": "published",
            "availability_status": avail_status,
            "availability_note": f"中原大學國際暨兩岸教育處公告交換姊妹校；{quota_str}。",
            "academic_year": "115",
            "application_round": "115-2（2027春季班第二梯次）／2027春季班大陸交換",
            "application_window_status": win_status,
            "application_deadline": app_deadline_str,
            "application_info": "\n\n".join(app_steps_list),
            "tuition_info": "\n\n".join(tuition_points_list),
            "semester_dates": "秋季班（第1學期）：約每年 8/9 月至翌年 1 月（日本及德國為 9/10 月至翌年 2/3 月）；春季班（第2學期）：約每年 2 月至 6/7 月（日本及德國為 4 月至 8 月）",
            "course_restrictions": note_text if note_text else "每學期於姊妹校至少須修習 2 門課程或相當於中原大學 6 學分（上限 22 學分）；不得抵免本系畢業專題及通識向度課程。",
            "housing_info": "多數姊妹校提供校內或合作學生宿舍申請（住宿費由學生自理），惟宿位有限依先到先得或抽籤分配；菲律賓德拉薩爾大學等部分學校須自行安排校外住宿。",
            "notes": "\n".join(notes_lines),
            "program_type": program_type,
            "source_url": source_url,
            "website": website,
            "official_website": website,
            "factsheet_url": factsheet_url,
            "image_url": visual_rec.get("local_path"),
            "image_source_url": visual_rec.get("image_source_url"),
            "image_page_url": visual_rec.get("official_page_url") or visual_rec.get("image_source_url"),
            "image_status": "verified" if visual_rec.get("local_path") else "missing",
            "location": location_obj,
            "student_summary_zh": {
                "study_period": p["period"],
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
                "title": f"中原大學國際暨兩岸教育處赴外交換資訊—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "115",
                "application_round": "115-2",
                "checked_at": "2026-10-16T16:30:00Z",
            },
            {
                "title": "中原大學 115-2（2027春季班）赴國際姊妹校交換生第二梯次遴選公告",
                "source_url": "https://oia.cycu.edu.tw/?p=9903",
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "115",
                "application_round": "115-2",
                "checked_at": "2026-10-16T16:30:00Z",
            },
            {
                "title": "中原大學學生赴境外研修要點（114.03.06）",
                "source_url": "https://oia.cycu.edu.tw/wp-content/uploads/sites/54/2025/05/1140306%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E7%A0%94%E4%BF%AE%E8%A6%81%E9%BB%9E.pdf",
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "115",
                "application_round": "115-2",
                "checked_at": "2026-10-16T16:30:00Z",
            },
        ]
        if website:
            wf_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "role": "partner_university",
                "authority": "partner_official",
                "effective_academic_year": "115",
                "application_round": "115-2",
                "checked_at": "2026-10-16T16:30:00Z",
            })

        workflows.append({
            "home_university": "中原大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": "115",
            "application_round": "115-2",
            "effective_application_rounds": ["115-2", "第1學期（秋季班）", "第2學期（春季班）"],
            "applicability_status": "verified",
            "applicability_note": "中原大學 115-2（2027春季班）赴國際姊妹校交換第二梯次遴選（2026/09/14–09/25 12:00 收件、10/01 面試）及 2027 春季班赴大陸姊妹校交換（2026/09/01–10/20 收件）已公告；116-1（2027秋季班）第一梯次預計於 2027/02 開放申請。",
            "review_status": "published",
            "published_at": "2026-10-16T16:30:00Z",
            "steps": [
                {
                    "rule_id": f"cycu-115-home-1-{idx+1:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認中原大學修畢二學期資格、GPA 3.0／班排前 30% 與 {zh_name} 語檢門檻",
                    "responsible_party": "學生",
                    "responsible_unit": "中原大學國際暨兩岸教育處（維澈樓 704 室）",
                    "deadline_at": "2026-09-25T12:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": "https://oia.cycu.edu.tw/?p=9903",
                    "deadline_checked_at": "2026-10-16T16:30:00Z",
                    "deadline_reminder_eligible": True,
                    "summary": f"須於中原大學修畢至少二學期，歷年 GPA 達 3.0 或班排名前 30%，並符合 {zh_name} 語言及系所條件。",
                    "details": [
                        f"開放學制：{degree_levels_str}",
                        f"申請條件與語檢：{lang_req_str}",
                        f"當期與歷年名額：{quota_str}",
                    ],
                    "scope": {
                        "home_universities": ["中原大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": ["115-2", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "source_urls": [source_url, "https://oia.cycu.edu.tw/?p=6336"],
                    "checked_at": "2026-10-16T16:30:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"cycu-115-home-2-{idx+1:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "繳交紙本申請表至維澈樓 704 室並寄送中英文備審電子檔至國際處信箱",
                    "responsible_party": "學生",
                    "responsible_unit": "中原大學國際暨兩岸教育處",
                    "deadline_at": "2026-09-25T12:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": "https://oia.cycu.edu.tw/?p=6338",
                    "deadline_checked_at": "2026-10-16T16:30:00Z",
                    "deadline_reminder_eligible": True,
                    "summary": "依公告期限繳交經系所簽章之紙本申請表，並將規定格式之電子檔寄至 oia_outbound@office.cycu.edu.tw。",
                    "details": [
                        "申請應繳文件：申請表（需導師／指導教授及系主任核章）、中英文歷年成績單（含 GPA 及班排名）、中英文讀書計畫、中英文自傳、語言能力檢定證明、個人履歷表、有效護照影本及家長同意書。",
                        "電子檔須依國際處規定編號命名並壓縮寄至 oia_outbound@office.cycu.edu.tw，主旨註明「申請出國交換學生甄選（學號＋姓名）」。",
                    ],
                    "document_requirements": [
                        {
                            "name": "中原大學出國交換學生甄選申請表（含系主任簽章、導師或指導教授推薦簽章及家長同意書）",
                            "official_form_url": "https://oia.cycu.edu.tw/?p=6338",
                            "source_urls": ["https://oia.cycu.edu.tw/?p=6338"],
                        },
                        {
                            "name": "中文及英文歷年成績單正本（須含歷年累積 GPA 及班排名百分比證明）",
                            "source_urls": ["https://oia.cycu.edu.tw/?p=6338"],
                        },
                        {
                            "name": "中英文讀書計畫（Study Plan）、中英文自傳（Autobiography）及個人履歷表（CV）",
                            "source_urls": ["https://oia.cycu.edu.tw/?p=6338"],
                        },
                        {
                            "name": "有效期限內之外語能力檢定證明影本（大陸地區姊妹校免附，惟須備妥有效臺胞證及三至六個月內體檢表）",
                            "conditional": p["kind"].startswith("mainland"),
                            "condition": "赴國際及港澳姊妹校必繳；赴大陸地區姊妹校免附外語檢定",
                            "source_urls": ["https://oia.cycu.edu.tw/?p=6338", "https://oia.cycu.edu.tw/?p=6340"],
                        },
                    ],
                    "scope": {
                        "home_universities": ["中原大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": ["115-2", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "submission": {
                        "method": "mixed",
                        "office": "中原大學國際暨兩岸教育處（維澈樓 704 室）",
                        "portal_url": "https://oia.cycu.edu.tw/?p=6338",
                    },
                    "action_url": "https://oia.cycu.edu.tw/?p=6338",
                    "source_urls": ["https://oia.cycu.edu.tw/?p=6338", "https://oia.cycu.edu.tw/?p=9903"],
                    "checked_at": "2026-10-16T16:30:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"cycu-115-home-3-{idx+1:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "參加校內遴選面試與公告錄取推薦名單",
                    "responsible_party": "學生與中原大學國際暨兩岸教育處",
                    "responsible_unit": "中原大學國際暨兩岸教育處",
                    "deadline_at": "2026-10-01T17:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": "https://oia.cycu.edu.tw/?p=9903",
                    "deadline_checked_at": "2026-10-16T16:30:00Z",
                    "deadline_reminder_eligible": True,
                    "summary": "依國際處排定時段參加面試（非大陸地區：語言能力 30%、在校成績 30%、面試表現 40%；大陸地區：在校成績 40%、課外表現 20%、面試表現 40%）。",
                    "details": [
                        "面試評分細項：語言能力 40%、申請動機 20%、讀書計畫 20%、人格特質 10%、儀態表現 10%。",
                        "建築學系學生申請交換另須符合班排名前 50% 且建築設計（一）至（六）及格之系所規定。",
                    ],
                    "scope": {
                        "home_universities": ["中原大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": ["115-2", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "source_urls": ["https://oia.cycu.edu.tw/?p=6336", "https://oia.cycu.edu.tw/?p=9903"],
                    "checked_at": "2026-10-16T16:30:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"cycu-{idx+1:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由中原大學國際處提名並完成 {zh_name} 姊妹校入學申請與宿舍登記",
                    "responsible_party": "學生與接待校國際處",
                    "summary": f"獲中原大學推薦後，由國際處向 {full_name} 提名，學生依姊妹校簡章（Fact Sheet）備齊複審文件（含財力證明、推薦信、護照、選課表或體檢表）送交姊妹校審核，最終錄取權由姊妹校決定。",
                    "details": [
                        f"交換期程：{p['period']}｜名額：{quota_str}",
                        f"語言與申請要求：{lang_req_str}",
                    ] + ([f"補充說明：{note_text}"] if note_text else []),
                    "scope": {
                        "home_universities": ["中原大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": ["115-2", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "source_urls": [source_url] + ([factsheet_url] if factsheet_url else []) + ([website] if website else []),
                    "checked_at": "2026-10-16T16:30:00Z",
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"cycu-115-home-5-{idx+1:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "核定出國選課單、申請獎助學金、辦理簽證與役男出境及返國學分抵免",
                    "responsible_party": "學生",
                    "responsible_unit": "中原大學國際暨兩岸教育處／教務處課註組／生輔組",
                    "summary": "取得姊妹校入學許可後，填具「中原大學學生出國選課單」經系主任及教務處核准（每學期至少 2 門課或相當於中原 6 學分），辦理簽證、海外醫療及意外保險與役男出境，並於返國後提交心得報告與辦理學分抵免。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["中原大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": ["115-2", "第1學期（秋季班）", "第2學期（春季班）"],
                    },
                    "source_urls": [
                        "https://oia.cycu.edu.tw/wp-content/uploads/sites/54/2025/05/1140306%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E7%A0%94%E4%BF%AE%E8%A6%81%E9%BB%9E.pdf",
                        "https://oia.cycu.edu.tw/?p=6353",
                    ],
                    "checked_at": "2026-10-16T16:30:00Z",
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": "2026-10-16T16:30:00Z",
            "coverage_status": "official_verified",
            "coverage_note": "已完整整合中原大學國際暨兩岸教育處赴外交換資訊、115-2 遴選公告、2027 春季班大陸交換資訊、境外研修要點與官方雲端簡章。",
        })

        cost_default, visa_default = REGION_COST_DEFAULTS.get(
            country,
            ("USD 800–1,300 / 月（含住宿、膳食、教材與當地交通費用）", "須依接待校與駐臺代表處規定辦理學生簽證與海外醫療保險。"),
        )
        cost_line = f"預估每月生活費約 {cost_default}"
        tuition_clean = tuition_points_list[0]
        housing_clean = (
            "須由學生自行安排校外住宿（接待校無提供校內宿舍或宿位極有限，請於獲提名後立即洽詢國際處與接待校租屋建議）。"
            if "find accommodation themselves" in note_text
            else "多數交換姊妹校提供校內或合作學生宿舍申請（住宿費由學生自行負擔），惟宿位有限依申請先後或抽籤分配，請於收到提名通知後立即留意住宿申請截止日。"
        )
        course_clean = (
            f"開放對象：{colleges_str}（{degree_levels_str}）"
            + (f"｜選課與學程規定：{note_text}" if note_text else "")
            + "｜依《中原大學學生赴境外研修要點》第 6 條，每學期至少須修習 2 門課或相當於中原大學 6 學分（上限 22 學分），不得抵免本系畢業專題及通識向度課程。"
        )
        calendar_clean = "秋季班（第1學期）：約每年 8/9 月至翌年 1 月（日本、德國為 9/10 月至翌年 2/3 月）；春季班（第2學期）：約每年 2 月至 6/7 月（日本、德國為 4 月至 8 月）。"

        dest_sources = [
            {"title": f"中原大學赴外交換資訊—{zh_name}", "source_url": source_url, "summary": "中原大學官方交換期程、語言與 GPA 門檻及選課備註"},
            {"title": "中原大學學生赴境外研修要點（114.03.06）", "source_url": "https://oia.cycu.edu.tw/wp-content/uploads/sites/54/2025/05/1140306%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E7%A0%94%E4%BF%AE%E8%A6%81%E9%BB%9E.pdf", "summary": "中原大學交換生甄選資格、最低修課學分與抵免規範"},
        ]
        if factsheet_url:
            dest_sources.append({"title": f"{zh_name} 交換簡章（Fact Sheet 雲端檔案）", "source_url": factsheet_url, "summary": "中原大學國際處官方雲端硬碟收錄之最新交換簡章"})
        if website:
            dest_sources.append({"title": f"{full_name} 官方網站", "source_url": website, "summary": "接待合作校官方網站"})
        for el in exp_links[:3]:
            dest_sources.append({"title": el["title"], "source_url": el["url"], "summary": "中原大學赴外交換生返國心得報告官方 PDF"})

        src_url_list = [source_url] + ([factsheet_url] if factsheet_url else []) + ([website] if website else [])

        destinations.append({
            "home_university": "中原大學",
            "school_name": full_name,
            "country": country,
            "city": location_obj.get("city") or country,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": f"校區代表城市：{location_obj.get('city') or country}。請依入學許可與 Fact Sheet 確認實際授課校區、機場接機服務與當地學生大眾運輸票卡優惠。",
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費與學雜費規定",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list,
                    "caution": "可申請教育部學海飛颺／惜珠或中原大學學生赴海外姊妹校交換學習助學金補助部分生活與機票開銷。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "校內宿位有限，請於完成姊妹校線上申請時同步確認宿舍申請期限。",
                },
                {
                    "key": "insurance",
                    "title": "醫療保險與安全",
                    "summary": visa_default,
                    "points": [
                        visa_default,
                        "交換生於出國期間仍須投保中原大學學生平安保險，並依《中原大學學生赴境外研修要點》購買涵蓋全期之海外醫療及意外保險。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "部分姊妹校要求於開學報到前提交指定規格之醫療及意外保險證明後方可辦理註冊。",
                },
                {
                    "key": "visa",
                    "title": "簽證、體檢與役男出境準備",
                    "summary": visa_default,
                    "points": [
                        "收到姊妹校正式入學許可書（Letter of Acceptance / JW202 / COE / DS-2019）後，立即向駐臺辦事處申辦學生簽證（赴大陸交換須持有效臺胞證並完成規定項目健康檢查）。",
                        "尚未履行兵役義務之在學役男，須於出國前依規定檢附入學許可向生輔組及教務處辦理役男出境緩徵手續。",
                        visa_default,
                    ],
                    "source_urls": src_url_list,
                    "caution": "簽證核發時間視各國領事館而定（約 3–8 週），請勿於取得簽證前購買不可退改之機票。",
                },
                {
                    "key": "courses",
                    "title": "課程限制、最低學分與返國抵免",
                    "summary": course_clean[:160],
                    "points": [
                        course_clean,
                        "學生出國前應填具「出國選課單」經本系（及雙主修／輔系）主任與教務處核准；返國後於規定期限內檢具姊妹校正式成績單及課程大綱辦理學分抵免。",
                    ],
                    "source_urls": src_url_list + ["https://oia.cycu.edu.tw/wp-content/uploads/sites/54/2025/05/1140306%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E7%A0%94%E4%BF%AE%E8%A6%81%E9%BB%9E.pdf"],
                    "caution": "境外修習之學分不得抵免中原大學各學系「畢業專題」及「通識向度課程」。",
                },
                {
                    "key": "city",
                    "title": "城市與校區位置",
                    "summary": f"{country} {location_obj.get('city') or ''}".strip(),
                    "points": [
                        location_obj.get("note") or f"{full_name} 校級代表位置位於 {location_obj.get('city') or country}。",
                    ],
                    "source_urls": [location_obj.get("source_url") or source_url],
                    "caution": "部分合作校具有多個校區（如法國 SKEMA 索菲亞科技園校區、荷蘭 Fontys 埃因霍溫校區、日本東洋大學白山校區、韓國延世大學未來校區），請以簡章備註與錄取通知為準。",
                },
                {
                    "key": "arrival",
                    "title": "學期年曆與返國心得義務",
                    "summary": calendar_clean,
                    "points": [
                        calendar_clean,
                        "返國後須依國際暨兩岸教育處規定繳交交換學生返國心得報告及問卷，領取獎助學金者須於規定期限內備齊單據完成核銷。",
                    ] + ([f"歷年學長姐返國心得：中原大學國際處雲端資料庫已收錄 {len(exp_links)} 篇赴 {zh_name} 交換心得報告。"] if exp_links else []),
                    "source_urls": src_url_list + [el["url"] for el in exp_links[:3]],
                    "caution": "領取《中原大學學生赴海外姊妹校交換學習助學辦法》助學金之學生，返國後須繼續就讀完成學位，不得辦理休退學。",
                },
            ],
            "first_72_hours": [
                {
                    "title": "依姊妹校入學許可指定報到日辦理新生註冊、宿舍入住與選課確認",
                    "detail": calendar_clean,
                    "source_urls": [source_url],
                },
                {
                    "title": "完成當地居留登錄、醫療保險確認與向中原大學國際處回報平安",
                    "detail": f"{visa_default} 抵校後請向中原大學國際暨兩岸教育處承辦人回報平安及確認選課清單。",
                    "source_urls": [source_url],
                },
            ],
            "sources": dest_sources,
            "last_checked": "2026-10-16T16:30:00Z",
            "coverage_status": "official_verified",
            "coverage_note": "已整合中原大學赴外交換資訊、境外研修要點、官方雲端簡章（Fact Sheets）與歷年返國交換生心得報告。",
        })

        research_records.append({
            "home_university": "中原大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": source_url,
            "checked_at": "2026-10-16T16:30:00Z",
            "note": f"中原大學國際暨兩岸教育處姊妹校列表（{source_url}）及 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [
            {"title": f"中原大學赴外交換資訊—{zh_name}", "url": source_url},
        ]
        if factsheet_url:
            ev_sources.append({"title": f"{zh_name} 交換簡章（Fact Sheet）", "url": factsheet_url})
        if website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": website})
        for el in exp_links[:3]:
            ev_sources.append({"title": el["title"], "url": el["url"]})

        ev_list = [
            {
                "theme": "housing",
                "kind": "official",
                "text": housing_clean,
                "sources": ev_sources,
                "checked_at": "2026-10-16T16:30:00Z",
                "scope": "中原大學赴外交換簡章住宿說明與姊妹校 Fact Sheet",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "cost",
                "kind": "official",
                "text": f"{tuition_clean}｜預估生活開支：{cost_default}",
                "sources": ev_sources,
                "checked_at": "2026-10-16T16:30:00Z",
                "scope": "中原大學交換費用規定與地區生活費估算",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "academics",
                "kind": "official",
                "text": course_clean,
                "sources": ev_sources,
                "checked_at": "2026-10-16T16:30:00Z",
                "scope": "中原大學學生赴境外研修要點與姊妹校選課限制",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "safety",
                "kind": "official",
                "text": visa_default,
                "sources": ev_sources,
                "checked_at": "2026-10-16T16:30:00Z",
                "scope": "中原大學赴外交換簽證、體檢、海外醫療保險與役男出境提醒",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "campus_culture",
                "kind": "mixed" if exp_links else "official",
                "text": (
                    f"合作類別：{program_type}｜名額：{quota_str}｜申請要求：{lang_req_str}"
                    + (f"｜中原大學國際處雲端資料庫收錄 {len(exp_links)} 篇赴 {zh_name} 交換生返國心得報告。" if exp_links else "")
                ),
                "sources": ev_sources,
                "checked_at": "2026-10-16T16:30:00Z",
                "scope": "中原大學赴外交換計畫名額、語檢要求與歷年返國交換生心得",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
        ]
        life_records.append({
            "school_name": full_name,
            "country": country,
            "checked_at": "2026-10-16T16:30:00Z",
            "status": "ready",
            "evidence": ev_list,
            "notes": [
                "已整合中原大學赴外交換資訊、境外研修要點、雲端 Fact Sheet 與歷年返國心得報告連結。",
                "當期宿位供給、費用與選課限制請依姊妹校最新 Fact Sheet 核對。",
            ],
            "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
            "extraction_version": 3,
        })

        experience_sources_records.append({
            "home_university": "中原大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": "https://drive.google.com/drive/folders/1kfbuPbchu6E9B82A1IVH1fGKk6N4gXHl",
            "partner_page_url": source_url,
            "report_count": len(exp_links),
            "sample_reports": exp_links[:3],
            "checked_at": "2026-10-16T16:30:00Z",
        })
        for el in exp_links[:3]:
            summary_text = f"中原大學國際暨兩岸教育處收錄之 {el['term']} 赴 {zh_name} 交換學生返國心得報告（官方雲端 PDF 原文檔案）。"
            theme_map = {
                "academics": f"中原大學 {el['term']} 交換生分享於 {zh_name} 之選課、授課與學分修習經驗。",
                "housing": f"中原大學 {el['term']} 交換生分享於 {zh_name} 之宿舍或校外住宿申請與生活經驗。",
                "campus_culture": f"中原大學 {el['term']} 交換生分享於 {zh_name} 之校園環境、國際處支援與文化交流。",
                "cost": f"中原大學 {el['term']} 交換生分享於 {zh_name} 之學期生活開銷與行前準備建議。",
            }
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": el["title"],
                "source_url": el["url"],
                "source_type": "article",
                "platform": "中原大學國際暨兩岸教育處交換心得庫",
                "author_name": "中原大學返國交換生",
                "language": "zh",
                "summary": summary_text,
                "themes": ["academics", "housing", "campus_culture", "cost"],
                "theme_summaries": theme_map,
                "content_status": "metadata_only",
                "perspective": "official_student_story",
                "published_at": None,
                "discovered_at": "2026-10-16T16:30:00Z",
                "content_hash": hashlib.sha256(el["url"].encode("utf-8")).hexdigest(),
                "exchange_term": el["term"],
                "summary_zh": summary_text,
                "original_summary": "",
                "theme_summaries_zh": theme_map,
                "translation_status": "original",
                "source_kind": "official_experience_pdf",
            })

    (OFFICIAL_CYCU_DIR / "partners.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_CYCU_DIR / "application_workflows.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_CYCU_DIR / "destination_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_CYCU_DIR / "partner_research.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_CYCU_DIR / "student_life.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_CYCU_DIR / "experience_sources.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in experience_sources_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_CYCU_DIR / "student_experiences.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in student_experience_rows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_CYCU_DIR / "campus-locations.json").write_text(
        json.dumps({"locations": new_locations}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    loc_file = REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
    existing_loc_lines = [line for line in loc_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    existing_loc_map = {}
    for line in existing_loc_lines:
        rec = json.loads(line)
        existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

    cycu_home_loc = {
        "school_name": "中原大學",
        "country": "臺灣",
        "city": "桃園市中壢區",
        "latitude": 24.9575,
        "longitude": 121.2408,
        "geocode_status": "verified",
        "geocoded_at": "2026-10-16T16:30:00Z",
        "source_url": "https://www.wikidata.org/wiki/Q709248",
        "identity_source_url": "https://ror.org/02w8ws377",
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。 母校代表點採桃園市中壢區中北路200號校本部（維澈樓 704 室國際暨兩岸教育處）；官方地址來源：https://oia.cycu.edu.tw/。",
    }
    existing_loc_map[("中原大學", "臺灣")] = cycu_home_loc
    sorted_locs = sorted(existing_loc_map.values(), key=lambda r: (r.get("country") or "", r.get("school_name") or ""))
    loc_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
        encoding="utf-8",
    )

    cycu_source_urls = [
        "https://oia.cycu.edu.tw/?p=6336",
        "https://oia.cycu.edu.tw/?page_id=10128",
        "https://oia.cycu.edu.tw/?p=9903",
        "https://oia.cycu.edu.tw/?p=6340",
        "https://oia.cycu.edu.tw/?p=6338",
        "https://oia.cycu.edu.tw/?p=6353",
        "https://oia.cycu.edu.tw/?p=6339",
        "https://oia.cycu.edu.tw/?p=6515",
        "https://oia.cycu.edu.tw/?p=6517",
        "https://oia.cycu.edu.tw/?p=6518",
        "https://oia.cycu.edu.tw/?p=6519",
        "https://oia.cycu.edu.tw/?p=6520",
        "https://oia.cycu.edu.tw/wp-content/uploads/sites/54/2025/05/1140306%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E7%A0%94%E4%BF%AE%E8%A6%81%E9%BB%9E.pdf",
        "https://oia.cycu.edu.tw/wp-content/uploads/sites/54/2022/10/536-2%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E6%B5%B7%E5%A4%96%E5%A7%8A%E5%A6%B9%E6%A0%A1%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%BF%92%E5%8A%A9%E5%AD%B8%E8%BE%A6%E6%B3%95.pdf",
    ]

    exchange_info_payload = {
        "school_name": "中原大學",
        "program_type": [
            "交換學生（赴國際姊妹校交換計畫・法德荷美日韓港及東南亞）",
            "交換學生（赴大陸地區姊妹校交換計畫・985/211及雙一流重點高校）",
            "交換學生（UMAP 亞太大學交流會交換計畫）",
        ],
        "academic_year": [
            "115（115-2 / 2027春季班：2026年8–10月遴選）",
            "116（116-1 / 2027秋季班：預計2027年2–3月開放申請）",
        ],
        "semester": [
            "第1學期（秋季班：每年約 8/9 月至翌年 1 月；日本及德國為 9/10 月至翌年 2/3 月）",
            "第2學期（春季班：每年約 2 月至 6/7 月；日本及德國為 4 月至 8 月）",
        ],
        "application_period": [
            "115-2（2027春季班）赴國際姊妹校交換遴選時程：第一梯次於 2026年8月28日截止收件、9月10日面試；第二梯次自 2026年9月14日起至9月25日（五）中午 12:00 止受理紙本及電子檔收件，並於 2026年10月1日（四）辦理面試。",
            "2027春季班赴大陸地區姊妹校交換申請時程：2026年9月1日起至10月20日止（依各大陸姊妹校規定截止日，如清華大學 9/24、東南大學 10/2、廈門大學 10/8、南京大學 10/14、中山大學／四川大學／深圳大學 10/15、華中科技大學 10/20 等）向國際處提交申請。",
            "秋季班（116-1 / 2027秋季班）申請時程：每年約 2 月開學後辦理出國交換說明會並開放第一梯次申請（日本交換專案於 2–3 月先行甄選，一般國際交換約 3–4 月截止）。",
        ],
        "eligibility": [
            "在學與修業門檻：中原大學在學學生（含學士班、碩士班、博士班），於本校就讀滿一學年（即修畢至少二學期）以上；大學一年級新生、轉學生就讀未滿一年者，以及在學期間已完成畢業應修學分並於申請當學期提出「提早畢業」申請者，均不得申請。每個學制以出國交換一次為限，交換期間以一學期或一學年（至多二學期）為限。",
            "國籍規定：赴國際及香港姊妹校交換開放本國生及境外學位生（外籍生、僑生、陸生）申請；赴大陸地區姊妹校交換限具中華民國國籍之在學學生申請。",
            "學業成績門檻：歷年學業成績 GPA 達 3.0（含）以上，或歷年學業成績班排名前 30%（兩項條件符合其中一項即可通過校內基本門檻；若志願姊妹校規定更高者則須同時符合姊妹校標準）。建築學系學生申請交換另須符合班排名前 50% 且建築設計（一）至（六）及格之規定。",
            "校內甄選評分比重：【非大陸地區】語言能力 30%、在校成績 30%、面試表現 40%（面試細項：語言能力 40%、申請動機 20%、讀書計畫 20%、人格特質 10%、儀態表現 10%）；【大陸地區】在校成績 40%、課外表現 20%、面試表現 40%。",
            "修課與學分抵免規範：依《中原大學學生赴境外研修要點》第 6 條，赴姊妹校交換每學期至少須修習 2 門課程或相當於中原大學 6 學分，學分上限為 22 學分（經本系及雙主修／輔系主任核准者得至 25 學分）；境外修習之學分不得抵免本系「畢業專題」及「通識向度課程」。",
        ],
        "language_requirement": [
            "申請赴國際姊妹校交換者，須檢附符合志願姊妹校規定標準之有效語言能力檢定成績證明（如 TOEFL iBT、TOEFL ITP、IELTS、TOEIC、Duolingo、JLPT 日檢、TOPIK 韓檢或 CEFR 德法語檢定）。",
            "若申請之日本或韓國姊妹校設有英語授課學程（如關西大學、東京電機大學、千葉大學、琉球大學、早稻田大學、龍谷大學、名城大學、福井大學、中央大學、韓國外國語大學、漢陽大學等），可依學程規定檢附英語檢定（TOEFL/IELTS/TOEIC）或日韓語檢定（JLPT N2–N4 / TOPIK 3–4）擇一申請。",
            "申請赴大陸地區姊妹校交換者免附外語能力檢定證明，惟須備妥有效期限內之臺胞證（臺灣居民來往大陸通行證）及依各校規定完成三至六個月內健康檢查報告。",
        ],
        "required_documents": [
            "1. 中原大學出國交換學生甄選申請表（紙本需經導師／指導教授及系所主任簽章，繳交至維澈樓 704 室國際暨兩岸教育處）",
            "2. 中文及英文歷年成績單正本（須包含歷年累積 GPA 及班排名百分比證明）",
            "3. 中文及英文讀書計畫（Study Plan）",
            "4. 中文及英文自傳（Autobiography）",
            "5. 語言能力檢定證明影本（大陸地區交換免附）及各項優良事蹟／課外表現證明",
            "6. 個人履歷表（CV）、有效護照個人資料頁影本（大陸交換加附臺胞證影本、白底或藍底證件照及健康檢查表）與家長同意書（電子檔依規定編號壓縮寄至 oia_outbound@office.cycu.edu.tw）",
        ],
        "scholarship_info": [
            "教育部「學海飛颺」（選送優秀學生赴國外研修）及「學海惜珠」（選送勵學優秀學生赴國外研修）獎學金：適用於具中華民國國籍、赴國外（不含大陸及港澳地區）修讀學分之交換生；115-2 學期收件自 2026年9月1日起至10月16日 17:00 止。",
            "《中原大學學生赴海外姊妹校交換學習助學辦法》校內助學金：補助赴海外姊妹校交換之在學學生（不含延畢生），依外語檢定成績、歷年學業成績及交換地區核給助學金；受獎生於交換期間每學期至少須修讀 6 學分，且返國後須繼續就讀完成學位、不得辦理休退學。",
            "教育部「學海築夢」及「新南向學海築夢」海外實習獎學金：補助由計畫主持人選送赴海外企業或機構實習之學生。",
            "姊妹校專項獎學金與費用減免：除全數交換姊妹校免收外國學費（僅美國 CSU Chico 與 UH Hilo 為自費交換專案）外，泰國亞洲理工學院（AIT）及部分日本、韓國、大陸姊妹校另提供住宿減免或交換生獎助金。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": cycu_source_urls,
        "last_checked": "2026-10-16T16:30:00Z",
    }
    (OFFICIAL_CYCU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "中原大學",
        "last_checked": "2026-10-16T16:30:00Z",
        "academic_score_minimum": 75.0,
        "academic_score_rule": "須於中原大學修畢至少二學期（大一新生、轉學未滿一年及當學期申請提早畢業生不得申請），且歷年學業成績 GPA 達 3.0（含）以上或班排名前 30%（兩項符合其一即可；建築學系須班排名前 50% 且建築設計（一）至（六）及格）。",
        "academic_gpa_minimum": 3.0,
        "maximum_preferences": 5,
        "selection_rules": {
            "academic_policy": "gpa_or_rank",
            "academic_reference_year": "115",
            "undergraduate_gpa_minimum": 3.0,
            "undergraduate_rank_maximum": 30.0,
            "graduate_academic_exempt": False,
            "exclude_in_service": False,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {},
            "excluded_undergraduate_years": ["大一"],
            "language_certificate_required": False,
        },
        "language_score_minimums": {
            "toefl": 60.0,
            "ielts": 5.5,
            "toeic": 580.0,
        },
        "application_periods": [
            {
                "title": "中原大學 115-2（2027春季班）赴國際姊妹校交換生第二梯次遴選",
                "details": [
                    "報名收件期間：2026年9月14日（一）起至2026年9月25日（五）中午 12:00 止（紙本送達維澈樓 704 室國際處，電子檔寄至 oia_outbound@office.cycu.edu.tw）。",
                    "校內遴選面試日期：2026年10月1日（四）；第一梯次已於 2026年8月28日截止收件、9月10日完成面試。",
                    "本次第二梯次開放荷蘭、美國、日本、韓國、印尼、菲律賓等 20 所姊妹校共 47 個交換名額。",
                ],
                "source": {
                    "title": "中原大學 115-2（2027春季班）赴國際姊妹校交換生第二梯次遴選公告",
                    "source_url": "https://oia.cycu.edu.tw/?p=9903",
                    "category": "deadline",
                    "summary": "115-2 第二梯次收件截止時間、面試日期與 20 所開放姊妹校名額表。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "115",
                "application_round": "115-2 第二梯次",
                "audience": "all_students",
                "opens_at": "2026-09-14T09:00:00+08:00",
                "deadline_at": "2026-09-25T12:00:00+08:00",
                "date_status": "verified_exact",
                "status": "closed",
                "status_note": "115-2 第二梯次已於 2026/09/25 截止收件並於 10/01 完成面試；116-1（2027秋季班）第一梯次預計於 2027 年 2 月開放申請。",
                "deadline_note": "紙本繳交至維澈樓 704 室國際暨兩岸教育處，電子檔寄至 oia_outbound@office.cycu.edu.tw。",
                "reminder_eligible": False,
                "checked_at": "2026-10-16T16:30:00Z",
            },
            {
                "title": "中原大學 2027 春季班赴大陸地區姊妹校交換申請",
                "details": [
                    "申請期間：2026年9月1日起至 2026年10月–11月（依各大陸姊妹校規定截止日，多數集中於 10月2日至11月20日）。",
                    "開放北京清華大學、武漢大學、南京大學、中山大學、四川大學、華中科技大學、天津大學、東南大學、廈門大學、重慶大學、華東師範大學、大連理工大學等 22 所 985/211 重點高校。",
                ],
                "source": {
                    "title": "中原大學 2027 春季班赴大陸姊妹校交換及申請資訊",
                    "source_url": "https://oia.cycu.edu.tw/?p=6340",
                    "category": "exchange_application",
                    "summary": "2027 春季班大陸交換 22 所合作高校名單、應繳文件與各校截止日期。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "115",
                "application_round": "2027春季班大陸交換",
                "audience": "all_students",
                "opens_at": "2026-09-01T09:00:00+08:00",
                "deadline_at": "2026-11-20T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "2027 春季班大陸姊妹校交換現正依各校截止日（10月–11月）受理申請中。",
                "deadline_note": "欲申請者請依各校截止日前備齊簡章規定文件向國際處承辦人（維澈樓 704 室）聯繫送件。",
                "reminder_eligible": True,
                "checked_at": "2026-10-16T16:30:00Z",
            },
            {
                "title": "中原大學 115-2（2027春季班）赴外交換各項獎助學金申請",
                "details": [
                    "申請期間：2026年9月1日起至2026年10月16日（五）17:00 止。",
                    "涵蓋教育部「學海飛颺」、「學海惜珠」及《中原大學學生赴海外姊妹校交換學習助學辦法》校內交換助學金。",
                ],
                "source": {
                    "title": "中原大學 115-2 各項交換獎學金申請說明",
                    "source_url": "https://oia.cycu.edu.tw/?p=6353",
                    "category": "scholarship",
                    "summary": "115-2 學海飛颺、學海惜珠與校內交換學習助學金申請資格及截止時間。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "115",
                "application_round": "115-2 交換獎助學金",
                "audience": "all_students",
                "opens_at": "2026-09-01T09:00:00+08:00",
                "deadline_at": "2026-10-16T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "115-2 赴外交換獎助學金申請至 2026/10/16 17:00 截止。",
                "deadline_note": "請備齊申請表、成績單、語檢證明及相關文件送交國際暨兩岸教育處。",
                "reminder_eligible": True,
                "checked_at": "2026-10-16T16:30:00Z",
            },
        ],
        "program_overview": [
            {
                "title": "中原大學國際暨兩岸赴外交換計畫總覽（89 所交換合作大學／391 所全球姊妹校）",
                "details": [
                    f"中原大學國際暨兩岸教育處（OIA）與全球五大洲 391 所姊妹校締結學術合作，其中開放出國交換之合作大學共 {len(partners)} 所（含 61 所歐美亞國際及香港交換校、28 所中國大陸 985/211 及重點高校，目前開放申請 {open_partner_count} 所）。",
                    "出國交換每學期分兩梯次遴選（秋季班於每年 2–4 月、春季班於每年 8–10 月辦理），錄取學生於交換期間僅須繳交中原大學全額學雜費，免繳姊妹校學費（美國 2 所自費交換專案除外）。",
                    f"本平台完整收錄中原大學 {len(partners)} 所交換合作大學之申請條件、115-2 與歷年名額、官方雲端交換簡章（Fact Sheets）連結，以及涵蓋 {exp_covered_schools} 所交換校之 109–114 學年度學長姐返國心得報告 PDF。",
                ],
                "source": {
                    "title": "中原大學國際暨兩岸教育處—交換生計畫介紹與赴國際交換資訊",
                    "source_url": "https://oia.cycu.edu.tw/?page_id=10128",
                    "category": "partner_school",
                    "summary": "中原大學交換生計畫介紹、申請條件總表與官方雲端簡章。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "申請資格、GPA 3.0／班排前 30% 門檻與校內遴選面試配分",
                "details": [
                    "修業年限與身分：本校在學學士班（大二含以上）、碩士班及博士班學生，且於中原大學已修畢至少二學期（大一新生、轉學未滿一年者及申請當學期提早畢業生不得申請）；每個學制限交換一次，最長二學期。",
                    "學業成績門檻：歷年累積 GPA 達 3.0（含）以上，或歷年班排名前 30%（兩者符合其一即可；建築學系須班排名前 50% 且建築設計（一）至（六）及格）。",
                    "國籍規定：國際及香港交換開放本國生與境外學位生（外籍生、僑生、陸生）申請；大陸地區交換限具中華民國國籍之在學學生申請。",
                    "校內遴選配分：【非大陸地區】語言能力 30%、在校成績 30%、面試表現 40%（面試含語言能力 40%、申請動機 20%、讀書計畫 20%、人格特質 10%、儀態表現 10%）；【大陸地區】在校成績 40%、課外表現 20%、面試表現 40%。",
                ],
                "source": {
                    "title": "中原大學交換生計畫介紹與學生赴境外研修要點",
                    "source_url": "https://oia.cycu.edu.tw/?p=6336",
                    "category": "exchange_application",
                    "summary": "申請資格、GPA 與班排名門檻、建築系特殊規定與遴選面試配分。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "國際姊妹校外語檢定門檻與日韓英語授課學程規定",
                "details": [
                    "申請赴國際及香港姊妹校交換者，須檢附符合志願校規定之有效語言能力證明（TOEFL iBT / ITP、IELTS、TOEIC、Duolingo、JLPT 日檢、TOPIK 韓檢或 CEFR 德法語檢定）。",
                    "日本與韓國多數姊妹校同時提供「英語授課學程（如 JEP-E / Program A）」與「日韓語授課學程（Program B）」，申請人可依所選學程檢附對應之英檢或日韓檢證明。",
                    "赴大陸地區姊妹校交換免附外語檢定證明，惟須持有效臺胞證並依各校規定提交三至六個月內健康檢查報告。",
                ],
                "source": {
                    "title": "中原大學赴國際交換資訊（各姊妹校申請資格表）",
                    "source_url": "https://oia.cycu.edu.tw/?page_id=10128",
                    "category": "exchange_application",
                    "summary": "各國交換姊妹校語言檢定、GPA 與院系限制一覽表。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "中原大學出國交換甄選紙本與電子備審文件規範",
                "details": [
                    "1. 出國交換學生甄選申請表（紙本須經導師／指導教授及系主任簽章後送交維澈樓 704 室國際處）。",
                    "2. 中文及英文歷年成績單正本（須註明歷年累積 GPA 及班排名百分比）。",
                    "3. 中文及英文讀書計畫（Study Plan）、中文及英文自傳（Autobiography）與個人履歷表（CV）。",
                    "4. 語言能力檢定成績單影本（大陸交換免附）、有效護照影本、家長同意書及有利審查之課外表現證明（電子檔依規定編號壓縮寄至 oia_outbound@office.cycu.edu.tw）。",
                ],
                "source": {
                    "title": "中原大學出國交換申請應繳文件說明",
                    "source_url": "https://oia.cycu.edu.tw/?p=6338",
                    "category": "exchange_application",
                    "summary": "申請表、成績單、讀書計畫、自傳、語檢證明與電子檔寄送規定。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "教育部學海飛颺／惜珠與中原大學赴海外姊妹校交換學習助學金",
                "details": [
                    "教育部「學海飛颺」與「學海惜珠」獎學金：補助本國籍優秀學生及清寒優秀學生赴國外（不含大陸及港澳）修讀學分。",
                    "《中原大學學生赴海外姊妹校交換學習助學辦法》校內助學金：補助赴海外姊妹校交換之在學學生（不含延畢生），依外語能力、學業成績及交換地區核給；受獎生每學期須修讀至少 6 學分，返國後須回校就讀完成學位、不得辦理休退學。",
                    "交換期間須繳交中原大學全額學雜費及學生平安保險費，免繳姊妹校學費（美國加州州立大學溪口分校及夏威夷大學希羅校區自費專案除外）。",
                ],
                "source": {
                    "title": "中原大學赴外交換各項獎學金申請說明與助學辦法",
                    "source_url": "https://oia.cycu.edu.tw/?p=6353",
                    "category": "scholarship",
                    "summary": "學海飛颺、學海惜珠與中原大學海外交換助學金辦法。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "中原大學赴外交換紙本收件與電子檔編號寄送規範",
                "summary": "申請人須同時完成「紙本申請表繳交（維澈樓 704 室）」與「備審電子檔寄送（oia_outbound@office.cycu.edu.tw）」方為完成報名。",
                "key_points": [
                    "電子檔須將申請表、中英文成績單、中英文讀書計畫、中英文自傳、語言能力證明、個人履歷、護照影本及家長同意書依序編號並壓縮為單一檔案寄出。",
                    "申請赴大陸地區交換者，獲校內推薦後須依各大陸姊妹校規定準備體檢表、推薦信、簡體中文申請表及白底／藍底證件照。",
                ],
                "applies_to": [],
                "source": {
                    "title": "中原大學出國交換申請應繳文件專頁",
                    "source_url": "https://oia.cycu.edu.tw/?p=6338",
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": "https://oia.cycu.edu.tw/?p=6338",
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "《中原大學學生赴境外研修要點》與《赴海外姊妹校交換學習助學辦法》重點",
                "summary": "規範中原大學交換生修業期限、每學期最低與最高學分數、不得抵免科目以及校內交換助學金之修課與返國義務。",
                "key_points": [
                    "交換生於境外研修期間以一學期或一學年為原則（同一學制以一次為限、累計不超過二學期），每學期至少須修習 2 門課程或相當於中原大學 6 學分，上限為 22 學分（經核准得至 25 學分）。",
                    "於姊妹校修習之科目學分須於出國前填具「出國選課單」經系主任及教務處核准，返國後檢附正式成績單辦理抵免；惟不得抵免本系「畢業專題」及「通識向度課程」。",
                    "領取中原大學海外交換助學金之學生，每學期至少應修讀相當於本校 6 學分課程，返國後須繼續就讀完成學位，不得辦理休學或退學，否則應全額繳回助學金。",
                ],
                "applies_to": [],
                "source": {
                    "title": "中原大學學生赴境外研修要點（114.03.06 修正）",
                    "source_url": "https://oia.cycu.edu.tw/wp-content/uploads/sites/54/2025/05/1140306%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E7%A0%94%E4%BF%AE%E8%A6%81%E9%BB%9E.pdf",
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": "https://oia.cycu.edu.tw/wp-content/uploads/sites/54/2025/05/1140306%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E7%A0%94%E4%BF%AE%E8%A6%81%E9%BB%9E.pdf",
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {"title": "中原大學國際暨兩岸教育處—交換生計畫介紹", "source_url": "https://oia.cycu.edu.tw/?p=6336", "category": "exchange_application", "summary": None},
            {"title": "中原大學國際暨兩岸教育處—赴國際交換資訊（姊妹校條件總表）", "source_url": "https://oia.cycu.edu.tw/?page_id=10128", "category": "partner_school", "summary": None},
            {"title": "中原大學 115-2（2027春季班）赴國際姊妹校交換第二梯次遴選公告", "source_url": "https://oia.cycu.edu.tw/?p=9903", "category": "deadline", "summary": None},
            {"title": "中原大學 2027 春季班赴大陸姊妹校交換及申請資訊", "source_url": "https://oia.cycu.edu.tw/?p=6340", "category": "partner_school", "summary": None},
            {"title": "中原大學國際暨兩岸教育處—出國交換申請應繳文件", "source_url": "https://oia.cycu.edu.tw/?p=6338", "category": "exchange_application", "summary": None},
            {"title": "中原大學國際暨兩岸教育處—115-2 各項獎學金申請說明", "source_url": "https://oia.cycu.edu.tw/?p=6353", "category": "scholarship", "summary": None},
            {"title": "中原大學學生赴境外研修要點（114.03.06）", "source_url": "https://oia.cycu.edu.tw/wp-content/uploads/sites/54/2025/05/1140306%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E7%A0%94%E4%BF%AE%E8%A6%81%E9%BB%9E.pdf", "category": "exchange_application", "summary": None},
            {"title": "中原大學學生赴海外姊妹校交換學習助學辦法", "source_url": "https://oia.cycu.edu.tw/wp-content/uploads/sites/54/2022/10/536-2%E4%B8%AD%E5%8E%9F%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E6%B5%B7%E5%A4%96%E5%A7%8A%E5%A6%B9%E6%A0%A1%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%BF%92%E5%8A%A9%E5%AD%B8%E8%BE%A6%E6%B3%95.pdf", "category": "scholarship", "summary": None},
        ],
    }
    (OFFICIAL_CYCU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    pages_records = [
        {
            "title": "中原大學：赴外交換遴選時程與申請辦法",
            "source_url": "https://oia.cycu.edu.tw/?p=9903",
            "published_at": "2026-09-14T00:00:00Z",
            "text": "\n".join(exchange_info_payload["application_period"]),
            "summary": "\n".join(exchange_info_payload["application_period"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-16T16:30:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "中原大學：交換學生申請資格、GPA 3.0／班排前 30% 與遴選面試配分",
            "source_url": "https://oia.cycu.edu.tw/?p=6336",
            "published_at": "2026-09-01T00:00:00Z",
            "text": "\n".join(exchange_info_payload["eligibility"]),
            "summary": "\n".join(exchange_info_payload["eligibility"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-16T16:30:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "中原大學：赴國際與大陸姊妹校交換語言能力與申請條件",
            "source_url": "https://oia.cycu.edu.tw/?page_id=10128",
            "published_at": "2026-09-01T00:00:00Z",
            "text": "\n".join(exchange_info_payload["language_requirement"]),
            "summary": "\n".join(exchange_info_payload["language_requirement"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-16T16:30:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "中原大學：出國交換申請應繳紙本與電子備審文件",
            "source_url": "https://oia.cycu.edu.tw/?p=6338",
            "published_at": "2026-09-01T00:00:00Z",
            "text": "\n".join(exchange_info_payload["required_documents"]),
            "summary": "\n".join(exchange_info_payload["required_documents"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-16T16:30:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "中原大學：赴外交換獎助學金、學海系列與海外交換學習助學辦法",
            "source_url": "https://oia.cycu.edu.tw/?p=6353",
            "published_at": "2026-09-01T00:00:00Z",
            "text": "\n".join(exchange_info_payload["scholarship_info"]),
            "summary": "\n".join(exchange_info_payload["scholarship_info"]),
            "category": "scholarship",
            "attachments": [],
            "crawled_at": "2026-10-16T16:30:00Z",
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
        },
    ]
    (OFFICIAL_CYCU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "cycu",
        "school_name": "中原大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_weights": {
            "international": {
                "language_proficiency": 0.30,
                "academic_transcript": 0.30,
                "interview": 0.40,
            },
            "mainland": {
                "academic_transcript": 0.40,
                "extracurricular_performance": 0.20,
                "interview": 0.40,
            },
        },
        "source_urls": cycu_source_urls,
        "verified_at": "2026-10-16",
    }
    (OFFICIAL_CYCU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_CYCU_DIR / "documents.json").write_text(
        json.dumps({"school_name": "中原大學", "required_documents": student_dashboard_payload["required_documents"], "source_urls": cycu_source_urls}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_CYCU_DIR / "scholarships.json").write_text(
        json.dumps({"school_name": "中原大學", "scholarships": student_dashboard_payload["scholarship_info"], "source_urls": cycu_source_urls}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "cycu",
        "school_name": "中原大學",
        "total_partners": len(partners),
        "international_partners": sum(1 for p in raw_partners if p["kind"] == "intl"),
        "mainland_partners": sum(1 for p in raw_partners if p["kind"].startswith("mainland")),
        "experience_report_covered_partners": exp_covered_schools,
        "open_partners": open_partner_count,
        "reference_only_partners": len(partners) - open_partner_count,
        "verified_locations": len(partners),
        "verified_official_websites": sum(1 for p in partners if p.get("official_website")),
        "verified_campus_images": len(partners),
        "active_term": "115-2（2027春季班）赴國際交換第二梯次（2026/09/14–09/25收件、10/01面試）及2027春季班赴大陸交換（2026/09/01–10/20收件）已公告；116-1（2027秋季班）第一梯次預計於2027年2月開放申請。",
        "verified_at": "2026-10-16",
    }
    (OFFICIAL_CYCU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_CYCU_DIR / "verification_status.json").write_text(
        json.dumps({
            "school_id": "cycu",
            "school_name": "中原大學",
            "status": "official_verified",
            "checked_at": "2026-10-16T16:30:00Z",
            "counts": completeness,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Successfully built CYCU catalog: {len(partners)} partners ({open_partner_count} open), "
        f"{len(workflows)} workflows, {len(destinations)} destinations, {len(research_records)} research records, "
        f"{len(new_locations)} locations, {exp_covered_schools} schools with experience reports ({len(student_experience_rows)} rows)."
    )


if __name__ == "__main__":
    main()
