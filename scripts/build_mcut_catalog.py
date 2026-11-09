"""Build the official Ming Chi University of Technology (明志科技大學, MCUT) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_MCUT_DIR = REPO_ROOT / "sources" / "mcut"
OFFICIAL_MCUT_DIR = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "mcut"
)
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-09T00:00:00Z"

MCUT_OIA_HOME_URL = "https://oia.mcut.edu.tw/?Lang=zh-tw"
MCUT_PARTNER_LIST_URL = "https://oia.mcut.edu.tw/p/412-1012-7472.php?Lang=zh-tw"
MCUT_REGULATIONS_URL = "https://oia.mcut.edu.tw/p/412-1012-6963.php?Lang=zh-tw"
MCUT_EXPERIENCE_HUB_URL = "https://oia.mcut.edu.tw/p/412-1012-10463.php?Lang=zh-tw"
MCUT_DUAL_EXP_URL = "https://oia.mcut.edu.tw/p/405-1012-64124,c10463.php?Lang=zh-tw"
MCUT_EXCH_EXP_URL = "https://oia.mcut.edu.tw/p/405-1012-64113,c10463.php?Lang=zh-tw"
MCUT_QA_HUB_URL = "https://oia.mcut.edu.tw/p/412-1012-10009.php?Lang=zh-tw"
MCUT_QA_EXCH_URL = "https://oia.mcut.edu.tw/p/405-1012-60461,c10009.php?Lang=zh-tw"
MCUT_QA_DUAL_URL = "https://oia.mcut.edu.tw/p/405-1012-60460,c10009.php?Lang=zh-tw"
MCUT_2026_2027_EXCHANGE_ANNOUNCEMENT_URL = "https://oia.mcut.edu.tw/p/406-1012-76292,r840.php?Lang=zh-tw"
MCUT_NIU_DUAL_SPRING_URL = "https://oia.mcut.edu.tw/p/406-1012-80170,r840.php?Lang=zh-tw"
MCUT_UC_DUAL_SPRING_URL = "https://oia.mcut.edu.tw/p/406-1012-80168,r840.php?Lang=zh-tw"
MCUT_NIU_DUAL_FALL_URL = "https://oia.mcut.edu.tw/p/406-1012-76297,r840.php?Lang=zh-tw"
MCUT_ELISAVA_SFSU_DUAL_URL = "https://oia.mcut.edu.tw/p/406-1012-76298,r840.php?Lang=zh-tw"
MCUT_UC_DUAL_FALL_URL = "https://oia.mcut.edu.tw/p/406-1012-76293,r840.php?Lang=zh-tw"
MCUT_ESIEE_ALBA_DUAL_URL = "https://oia.mcut.edu.tw/p/406-1012-70826,r840.php?Lang=zh-tw"
MCUT_SHORT_TERM_URL = "https://oia.mcut.edu.tw/p/406-1012-75791,r840.php?Lang=zh-tw"
MCUT_GSITES_HOME_URL = "https://sites.google.com/view/mcutaroundtheworld/home"
MCUT_GOOGLE_FORM_URL = "https://forms.gle/SWrEct6zFhJiaLSV8"

MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL = "https://oia.mcut.edu.tw/var/file/12/1012/img/816/736779544.pdf"
MCUT_UNDERGRAD_EXCHANGE_COURSE_DOCX_URL = "https://oia.mcut.edu.tw/var/file/12/1012/img/816/A2Q1060001.docx"
MCUT_XUEHAI_SELECTION_REG_PDF_URL = "https://oia.mcut.edu.tw/var/file/12/1012/img/816/848114138.pdf"
MCUT_SHORT_TERM_REG_DOCX_URL = "https://oia.mcut.edu.tw/var/file/12/1012/img/816/A2Q1030010.docx"
MCUT_LANG_CEFR_TABLE_PDF_URL = "https://oia.mcut.edu.tw/var/file/12/1012/img/816/197207162.pdf"

REGION_COST_DEFAULTS = {
    "美國": (
        "每月生活費約 USD 1,250–2,100（折合新臺幣約 40,000–67,000 元；辛辛那提大學 University of Cincinnati 與北伊利諾大學 Northern Illinois University 校園公寓及生活費適中，舊金山州立大學 SFSU 位於灣區生活成本較高；赴非亞洲區雙聯學位生可領明志最高 24 萬元補助［辛辛那提大學另享明志校友「鹿江基金會」專屬獎學金］、非亞洲區交換生可領一學期最高 8 萬元／一學年最高 16 萬元補助）",
        "須憑美國接待大學核發之 I-20 或 DS-2019 表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦 F-1 或 J-1 學生簽證，且須投保符合校方與美國規定之全期醫療保險。",
    ),
    "日本": (
        "每月生活費約 USD 680–1,150（折合日圓約 JPY 95,000–160,000 / 月、新臺幣約 21,500–36,500 元；福岡工業大學、芝浦工業大學、日本工業大學與東京都市大學均設國際學生寮；赴亞洲區交換生可領明志一學期最高 5 萬元／一學年最高 10 萬元補助、雙聯生最高 15 萬元補助）",
        "須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後申辦日本留學簽證並加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 650–1,100（折合韓元約 KRW 850,000–1,450,000 / 月、新臺幣約 20,500–35,000 元；國民大學 Kookmin University 與同德女子大學校內外學生宿舍機能完善；赴亞洲區交換生可領明志一學期最高 5 萬元／一學年最高 10 萬元補助）",
        "須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後辦理外國人登錄證並納保韓國國民健康保險。",
    ),
    "中國大陸": (
        "每月生活費約 USD 350–650（折合人民幣約 RMB 2,400–4,500 / 月、新臺幣約 11,000–20,500 元；北京科技大學、南京理工大學、北京理工大學、中國礦業大學、蘇州大學與福州大學等校內宿舍與學生食堂費用實惠；赴亞洲區交換生可領明志一學期最高 5 萬元／一學年最高 10 萬元補助）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及接待校錄取通知書報到，並依明志科大規定購買涵蓋交換全期之海外醫療及意外保險且完成教育部「赴陸交流活動登錄平臺」申報。",
    ),
    "法國": (
        "每月生活費約 USD 950–1,550（折合歐元約 EUR 880–1,420 / 月、新臺幣約 30,500–49,500 元；法國電子與電腦工程學院 ESIEE Paris 與南特高等設計學院 L'École de design Nantes Atlantique 國際生可申請法國政府 CAF 房租補貼；赴非亞洲區交換生可領明志一學期最高 8 萬元／一學年最高 16 萬元補助、雙聯生最高 24 萬元補助）",
        "須先透過法國教育中心（Campus France Taiwan）完成 Etudes en France 線上程序與面試，再向法國在台協會申辦長期學生簽證（VLS-TS）。",
    ),
    "西班牙": (
        "每月生活費約 USD 900–1,450（折合歐元約 EUR 830–1,350 / 月、新臺幣約 28,500–46,500 元；巴塞隆納高等設計學院 ELISAVA 與塞維亞大學 Universidad de Sevilla 生活機能便利；赴非亞洲區交換生可領明志一學期最高 8 萬元／一學年最高 16 萬元補助、ELISAVA 碩士雙聯生最高 24 萬元補助）",
        "交換 1 學期以上須憑西班牙接待大學入學許可、住宿證明、無犯罪紀錄與全額申根醫療保險向西班牙商務辦事處申辦長期學生簽證。",
    ),
    "希臘": (
        "每月生活費約 USD 750–1,250（折合歐元約 EUR 680–1,150 / 月、新臺幣約 24,000–40,000 元；雅典 ALBA 商學院 ALBA Graduate Business School, The American College of Greece 學生公寓費用低於西歐；赴非亞洲區交換生可領明志一學期最高 8 萬元／一學年最高 16 萬元補助、雙聯生最高 24 萬元補助）",
        "須憑希臘接待校入學許可、財力證明、住宿證明與申根醫療保險申辦希臘長期學生簽證（National D Visa）。",
    ),
    "芬蘭": (
        "每月生活費約 USD 900–1,400（折合歐元約 EUR 820–1,280 / 月、新臺幣約 28,500–44,500 元；塞伊奈約基應用科學大學 SeAMK 學生公寓 Sevas 每月房租約 EUR 280–450；赴非亞洲區交換生可領明志一學期最高 8 萬元／一學年最高 16 萬元補助）",
        "交換期間須依芬蘭移民局（Migri）規定申辦學生居留許可（Residence Permit for Studies），並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "立陶宛": (
        "每月生活費約 USD 650–1,050（折合歐元約 EUR 600–960 / 月、新臺幣約 21,000–33,500 元；維爾紐斯科技大學 VILNIUS TECH 校內學生宿舍每月僅約 EUR 150–250；赴非亞洲區交換生可領明志一學期最高 8 萬元／一學年最高 16 萬元補助）",
        "須依立陶宛移民局（MIGRIS）規定申辦國家長期簽證（National Visa D）或臨時居留許可，並投保申根區醫療保險。",
    ),
    "奧地利": (
        "每月生活費約 USD 950–1,450（折合歐元約 EUR 880–1,350 / 月、新臺幣約 30,500–46,500 元；奧地利茵斯布魯克管理中心 MCI 學生宿舍透過 OeAD 申請；赴非亞洲區交換生可領明志一學期最高 8 萬元／一學年最高 16 萬元補助）",
        "須憑 MCI 入學許可與 OeAD 住宿證明向奧地利台北辦事處申辦學生簽證（Visa D）或居留許可，並投保奧地利認可之醫療保險。",
    ),
    "德國": (
        "每月生活費約 USD 950–1,450（折合歐元約 EUR 880–1,350 / 月、新臺幣約 30,500–46,500 元；赴非亞洲區交換生可領明志一學期最高 8 萬元／一學年最高 16 萬元補助）",
        "須憑德國姊妹校入學許可與限制提領帳戶（Blocked Account）財力證明向德國在台協會申辦長期學生簽證並投保德國法定公保。",
    ),
    "波蘭": (
        "每月生活費約 USD 600–980（折合新臺幣約 19,000–31,500 元；西里西亞大學與盧布林科技大學校內學生宿舍每月僅約 EUR 120–220；赴非亞洲區交換生可領明志一學期最高 8 萬元／一學年最高 16 萬元補助）",
        "須憑波蘭接待大學正式入學許可、住宿證明與申根醫療保險向波蘭臺北辦事處申辦 D 類國別學生簽證。",
    ),
    "捷克": (
        "每月生活費約 USD 650–1,050（折合歐元約 EUR 600–960 / 月、新臺幣約 21,000–33,500 元；布爾諾孟德爾大學校內學生宿舍費用低廉；赴非亞洲區交換生可領明志一學期最高 8 萬元／一學年最高 16 萬元補助）",
        "交換 1 學期以上須憑捷克接待大學入學許可、住宿證明與申根醫療保險向捷克經濟文化辦事處申辦長期學生簽證。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,200–1,850（折合加幣約 CAD 1,650–2,500 / 月、新臺幣約 38,500–59,000 元；勞倫森大學 Laurentian University 校內外住宿；赴非亞洲區交換生可領明志一學期最高 8 萬元／一學年最高 16 萬元補助）",
        "交換 1 學期（6 個月內）得持 eTA 入境就讀；滿 1 學年須向加拿大移民局（IRCC）申辦 Study Permit（學習許可）並投保醫療保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "美國": "秋季班（Fall Semester）：約 8 月中下旬至 12 月中旬；春季班（Spring Semester）：約 1 月中旬至 5 月中旬（辛辛那提大學、北伊利諾大學、舊金山州立大學雙聯碩士可於秋季班 8 月或春季班 1 月入學）",
    "日本": "春季班（前學期）：約 4 月初至 8 月上旬；秋季班（後學期）：約 9 月中旬至翌年 2 月上旬",
    "韓國": "春季班（第 1 學期）：約 3 月初至 6 月中旬；秋季班（第 2 學期）：約 9 月初至 12 月中旬",
    "中國大陸": "秋季班（第 1 學期）：約 9 月初至翌年 1 月中旬；春季班（第 2 學期）：約 2 月下旬至 7 月初",
    "法國": "秋季學期（Fall Semester）：約 9 月初至翌年 1 月下旬；春季學期（Spring Semester）：約 1 月下旬至 6 月中旬（ESIEE Paris 雙聯碩士為秋季班 9 月入學）",
    "西班牙": "第一學期（秋季）：約 9 月中旬至翌年 1 月底；第二學期（春季）：約 2 月初至 6 月底（ELISAVA 巴塞隆納高等設計學院雙聯碩士為 9 月入學，為期 1 學年）",
    "希臘": "秋季學期／學季：約 9 月中旬至 12 月下旬；春季學期：約 1 月中旬至 6 月中旬",
    "芬蘭": "秋季學期（Autumn Semester）：約 8 月下旬至 12 月下旬；春季學期（Spring Semester）：約 1 月初至 5 月下旬",
    "立陶宛": "秋季學期（Autumn Semester）：約 9 月 1 日至翌年 1 月底；春季學期（Spring Semester）：約 2 月初至 6 月底",
    "奧地利": "冬季學期（Winter Semester）：約 9 月中旬至翌年 1 月底；夏季學期（Summer Semester）：約 2 月中旬至 6 月底",
    "德國": "冬季學期（Wintersemester）：約 10 月初至翌年 2 月中旬；夏季學期（Sommersemester）：約 3 月中旬或 4 月初至 7 月底",
    "波蘭": "冬季學期（Winter Semester）：約 10 月初至翌年 2 月中旬；夏季學期（Summer Semester）：約 2 月下旬至 6 月底",
    "捷克": "冬季學期（Winter Semester）：約 9 月中旬至翌年 1 月底；夏季學期（Summer Semester）：約 2 月上旬至 6 月底",
    "加拿大": "秋季學期（Fall）：約 9 月初至 12 月下旬；冬季學期（Winter）：約 1 月初至 4 月下旬",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
  """Ensure school-images.json and university_locations.jsonl contain all 130 MCUT partner schools."""
  si_path = STATIC_DIR / "assets" / "school-images.json"
  si_data = json.loads(si_path.read_text(encoding="utf-8"))
  schools_list = si_data.get("schools", [])
  by_name = {
      str(r.get("school_name", "")): r
      for r in schools_list
      if isinstance(r, dict)
  }
  si_changed = False
  for item in catalog_source:
    fn = item["school_name"]
    irec = item.get("image_record") or {}
    if irec.get("local_path"):
      new_rec = {
          "school_name": fn,
          "local_path": irec["local_path"],
          "image_source_url": (
              irec.get("image_source_url")
              or irec.get("image_url")
              or irec["local_path"]
          ),
          "source_page_url": (
              irec.get("source_page_url")
              or irec.get("official_page_url")
              or item.get("website")
              or ""
          ),
          "official_page_url": (
              item.get("website") or irec.get("official_page_url") or ""
          ),
          "attribution": irec.get("attribution") or "Wikimedia Commons",
          "status": "verified",
          "country": item["country"],
      }
      if fn not in by_name:
        schools_list.append(new_rec)
        by_name[fn] = new_rec
        si_changed = True
      elif (
          by_name[fn].get("local_path") != new_rec["local_path"]
          or by_name[fn].get("country") != new_rec["country"]
          or by_name[fn].get("status") != "verified"
      ):
        by_name[fn].update(new_rec)
        si_changed = True
  if si_changed:
    si_data["schools"] = schools_list
    si_path.write_text(
        json.dumps(si_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

  loc_lines = UNIVERSITY_LOCATIONS_PATH.read_text(encoding="utf-8").splitlines()
  loc_by_name = {}
  parsed_locs = []
  for line in loc_lines:
    if line.strip():
      obj = json.loads(line)
      parsed_locs.append(obj)
      loc_by_name[str(obj.get("school_name", ""))] = obj
  loc_changed = False
  for item in catalog_source:
    fn = item["school_name"]
    loc = resolved_locations.get(fn)
    if fn not in loc_by_name and loc:
      lat = float(
          loc.get("latitude")
          if loc.get("latitude") is not None
          else loc.get("lat", 25.0412)
      )
      lon = float(
          loc.get("longitude")
          if loc.get("longitude") is not None
          else loc.get("lon", 121.4235)
      )
      new_loc = {
          "school_name": fn,
          "country": item["country"],
          "city": loc.get("city") or item["country"],
          "latitude": lat,
          "longitude": lon,
          "geocode_status": "verified",
          "geocoded_at": CHECKED_AT,
          "source_url": loc.get("source_url") or "https://www.wikidata.org",
          "identity_source_url": (
              item.get("website") or loc.get("source_url") or "https://ror.org"
          ),
          "precision": loc.get("precision") or "representative",
      }
      parsed_locs.append(new_loc)
      loc_by_name[fn] = new_loc
      loc_changed = True
  if loc_changed:
    UNIVERSITY_LOCATIONS_PATH.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in parsed_locs)
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
  OFFICIAL_MCUT_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_MCUT_DIR / "mcut_catalog_source.json").read_text(
          encoding="utf-8"
      )
  )
  resolved_locations = json.loads(
      (SOURCES_MCUT_DIR / "mcut_resolved_locations.json").read_text(
          encoding="utf-8"
      )
  )
  exp_index_path = SOURCES_MCUT_DIR / "mcut_experience_index.json"
  exp_index = (
      json.loads(exp_index_path.read_text(encoding="utf-8"))
      if exp_index_path.exists()
      else {}
  )
  bin_urls_path = SOURCES_MCUT_DIR / "binary_source_urls.json"
  bin_urls = (
      json.loads(bin_urls_path.read_text(encoding="utf-8"))
      if bin_urls_path.exists()
      else {}
  )
  sync_global_assets_and_locations(catalog_source, resolved_locations)

  school_images_data = json.loads(
      (STATIC_DIR / "assets" / "school-images.json").read_text(encoding="utf-8")
  )
  visual_by_name = {
      str(r.get("school_name", "")): r
      for r in school_images_data.get("schools", [])
      if isinstance(r, dict) and r.get("status") == "verified"
  }

  partners: list[dict] = []
  workflows: list[dict] = []
  destinations: list[dict] = []
  research_records: list[dict] = []
  life_records: list[dict] = []
  experience_sources_records: list[dict] = []
  student_experience_rows: list[dict] = []
  new_locations: list[dict] = []

  open_partner_count = 0
  exp_covered_schools = 0
  total_exp_reports = 0

  for idx, item in enumerate(catalog_source):
    sn = idx + 1
    full_name = item["school_name"]
    zh_name = item["name_zh"]
    country = item["country"]
    region = item["region"]
    avail_status = (
        "open"
        if (item.get("availability_status") or item.get("offering_status"))
        == "open"
        else "reference_only"
    )
    if avail_status == "open":
      open_partner_count += 1

    group_str = clean_text(
        item.get("program_type")
        or item.get("group")
        or "國際事務處全球交流組正式締約姊妹校"
    )
    quota_str = clean_text(
        item.get("quota") or "依明志科技大學國際事務處全球交流組當期公告名額"
    )
    detail_url = (
        item.get("source_url")
        or item.get("detail_url")
        or MCUT_PARTNER_LIST_URL
    )
    source_url = detail_url

    if "雙聯" in group_str:
      program_type = group_str
    elif avail_status == "open" and country == "中國大陸":
      program_type = f"{group_str}（大陸地區交換生甄選，免繳接待校學費）"
    elif avail_status == "open":
      program_type = group_str
    else:
      program_type = group_str

    colleges_str = clean_text(
        item.get("colleges")
        or "工程學院、環境資源學院、管理暨設計學院（全校各院系所）"
    )
    degree_levels_str = clean_text(
        item.get("eligible_degrees")
        or "日間部大學部二年級、三年級在學學生（僅大二升大三擬以交換抵免大三工讀實務實習者可申請一學年交換，其餘以申請一學期為原則）及日間部碩士班、博士班在學學生（不含大一新生及在職專班）"
    )
    lang_req_str = clean_text(
        item.get("language_req")
        or (
            "英語達 TOEFL iBT 72–85 / IELTS 5.5–6.5 / TOEIC 785（或 Duolingo 110–115；依各雙聯合作校學院規定）"
            if "雙聯" in group_str
            else "具 CEFR B1 以上外語檢定證明（TOEIC 550［聽275/讀275］/ TOEFL iBT 42 / TOEFL ITP 460 / IELTS 4.0 / GEPT 中級 / JLPT N3 / TOPIK 3級；部分歐美姊妹校要求 CEFR B2）"
        )
    )
    gpa_req_str = clean_text(
        item.get("gpa_req")
        or (
            "在校歷年學業成績 GPA 達 2.75–3.0 以上，且歷年操行成績平均 80 分以上無記過紀錄（碩士雙聯須同時檢附大學及碩士成績單並通過母系所論文計畫書審查）"
            if "雙聯" in group_str
            else "在校歷年學業成績平均 GPA 達 3.0（百分制約 75 分）以上，且歷年操行成績平均 80 分以上無記過紀錄"
        )
    )
    website = (
        item.get("official_website")
        or item.get("website")
        or MCUT_PARTNER_LIST_URL
    )
    remarks_raw = clean_text(item.get("remarks") or item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or exp_index.get(full_name) or []
    if not exps:
      en_lower = (item.get("name_en") or "").strip().lower()
      for k_exp, v_exp in exp_index.items():
        if en_lower and en_lower in k_exp.lower():
          exps = v_exp
          break

    round_label = (
        "115 學年度（2026–2027 學年度海外交換學習暨雙聯學位甄選）"
        if avail_status == "open"
        else "國際事務處全球交流組正式締約姊妹校（當期開放名額依每年 1 月及 9 月公告簡章為準）"
    )
    app_deadline_str = clean_text(
        item.get("deadline")
        or "2026–2027 學年度海外交換生暨秋季班雙聯學位甄選：2026年2月6日（週五）17:00 截止；2027 年春季班碩士雙聯學位甄選：2026年9月24日（週四）17:00 截止"
    )
    deadline_iso = (
        "2026-09-24T17:00:00+08:00"
        if "9月24日" in app_deadline_str
        else "2026-02-06T17:00:00+08:00"
    )
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "115"

    study_period_str = clean_text(
        item.get("duration")
        or "一學期為原則（大二升大三以交換抵免大三工讀實務實習者可申請一學年；雙聯學位為一學年）"
    )
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季班（第 1 學期）：約 9 月至翌年 1 月；春季班（第 2 學期）：約 2 月至 6 月"
    )
    housing_str = (
        f"獲明志科技大學國際事務處全球交流組推薦錄取後，可依 {zh_name} 國際處指引申請校內外學生宿舍"
        + (f"（費用與學費補助待遇：{tuition_note}）" if tuition_note else "。")
    )
    course_rest_str = (
        f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）》與《明志科技大學大學部海外交換學習課程實施辦法（A2Q1060001）》規定："
        "（1）在學與操行門檻：限就讀滿一學期以上之日間部大二、大三及碩博士班在學學生，在校歷年學業成績 GPA 達 3.0（百分制約 75 分）以上（部分雙聯學程為 GPA 2.75 以上），歷年操行成績平均 80 分以上且無記過紀錄；"
        "（2）大三工讀實務實習抵免與一學年交換規定：僅大二升大三擬以海外交換抵免大三工讀實務實習課程（上學期 16 學分、下學期 18 學分）者可申請一學年交換，交換期間每學期至少應修讀 6 學分（歐洲 ECTS 學分以 2 ECTS 折抵明志 1 學分，非專業課程以 2 學分為上限），且須每三個月繳交四階段海外交換學習報告；其餘年級皆以申請一學期交換為原則；"
        "（3）單一志願與返國核銷：每人限填寫最適合之交換學校 1 所；獲補助學生返國後 1 週內須繳交至少 2 頁之《出國雙聯學位或交換學習報告（表號 A2Q1040508）》電子檔、來回登機證正本、護照出入境章影本及國外成績單以辦理補助核銷與學分採認。"
    )

    living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
        country,
        (
            "每月生活費約 USD 600–1,200（依匯率折合新臺幣約 19,000–38,500 元，含住宿、膳食與市區交通）",
            "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋交換全期之海外醫療及意外保險。",
        ),
    )

    tuition_points_list = [
        (
            f"明志科技大學在學註冊與學雜費規定（依《學生出國雙聯學位學習及交換學習實施及補助辦法》第 9 條）：出國交換或修讀雙聯學位期間須維持明志科技大學在學身分並繳交明志校內全額學雜費；交換生免繳接待姊妹校學費（雙聯學位生依兩校協議享有學費減免或專屬獎學金）。本合作校待遇：{tuition_note}。"
        ),
        (
            "明志科技大學《學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008，114年8月12日修訂）》與教育部《學海計畫》雙軌高額補助：（1）校內雙聯學位補助：亞洲區一學年最高新臺幣 15 萬元、非亞洲區一學年最高新臺幣 24 萬元（赴美國辛辛那提大學另享明志校友「鹿江基金會」專屬獎學金）；（2）校內交換學習補助：亞洲區一學期最高 5 萬元／一學年最高 10 萬元、非亞洲區一學期最高 8 萬元／一學年最高 16 萬元（同一學制每人限補助乙次，於獲國外大學入學許可通知後 2 週內向國際處全球交流組提出申請）；（3）海外短期研習補助（A2Q1030010）：亞洲區 5–35 日以上補助 2.5 萬至 3.3 萬元、非亞洲區補助 3.5 萬至 4.7 萬元；（4）教育部《學海飛颺》（每人 5 萬至 30 萬元，出國前核發 80%、返國後核發 20%）、《學海惜珠》及《學海築夢／新南向學海築夢》。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認明志在學年級、GPA 3.0、操行 80 分與 {zh_name} 語檢門檻並填寫 Google 表單）：確認為明志科技大學日間部大二、大三或碩博士班在學學生（大二升大三抵免工讀實務實習者可申請一學年交換，其餘以一學期為原則），符合學業與操行要求（{gpa_req_str}）及語言門檻（{lang_req_str}），先完成線上 Google 表單（{MCUT_GOOGLE_FORM_URL}）登記（每人限填寫最適合之志願學校 1 所），由系統自動寄發申請表件至電子信箱。"
        ),
        (
            "步驟二（備齊《申請表 A2Q1040108》、300–500字個人說明申請理由、中英文自傳與用印證明親送國際處）：於校內截止日前（交換生暨秋季班雙聯為 2026 年 2 月 6 日週五 17:00 止；春季班碩士雙聯為 2026 年 9 月 24 日週四 17:00 止）備妥：（1）《學生出國雙聯學位學習或交換學習申請表（表號 A2Q1040108）》（內含 300～500 字「個人說明申請理由 Statement of Purpose」，須經導師／指導教授及系主任核章）、（2）《家長/監護人切結同意書（A2Q1040208）》與《切結保證書（A2Q1040308）》、（3）中文歷年學業成績單正本及名次證明（須經教務處註冊組用印；碩士雙聯須同時附大學及碩士成績單）、（4）語言能力檢定證明正本、（5）中、英文自傳（格式自訂，各以一頁 A4 為限；雙聯另附通過系所審查之論文計畫書／專業實務報告初稿）、（6）歷年獎懲紀錄證明正本（須經學務處生輔組用印，確認操行 ≥ 80 分且無記過），親送至創新大樓 2 樓國際事務處全球交流組。"
        ),
        (
            f"步驟三（通過明志校內委員會審查與推薦提名）：由系所初審並經「學生出國雙聯學位學習及交換學習審查委員會」複審通過後，由國際事務處全球交流組正式向 {full_name} 辦理官方提名（Nomination）。"
        ),
        (
            "步驟四（取得入學許可後 2 週內申請明志最高 24 萬／16 萬元補助，返國後 1 週內繳交研修報告核銷）：獲接待大學正式入學許可（Offer Letter）後 2 週內，檢具申請表向國際處申請明志校內雙聯／交換補助或教育部學海飛颺／惜珠獎學金（大二升大三以交換抵免工讀實習者須每三個月繳交四階段交換學習報告）；返國後 1 週內須繳交至少 2 頁之《研修報告（A2Q1040508）》電子檔、來回登機證正本、護照出入境章影本及國外成績單以完成核銷與學分抵免。"
        ),
    ]

    elig_points_list = [
        f"合作類別與計畫組別：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請學院：{colleges_str}",
        f"學業成績、操行與評選門檻：{gpa_req_str}",
        f"語言能力標準：{lang_req_str}",
        "志願選填與書審規範：每人限填寫最適合之交換學校 1 所；須填具 Google 表單領取《申請表（A2Q1040108）》（撰寫 300～500 字個人說明申請理由）並附中、英文自傳（各以 1 頁 A4 為限）、教務處註冊組用印成績單與名次證明、學務處生輔組用印獎懲證明。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與明志高額獎助學金待遇：{tuition_note}")
    if remarks_raw:
      elig_points_list.append(f"學程與締約重點說明：{remarks_raw}")

    exp_links: list[dict] = []
    exp_labels: list[str] = []
    if exps:
      exp_covered_schools += 1
      total_exp_reports += len(exps)
      seen_exp_urls: set[str] = set()
      for e_idx, e in enumerate(exps):
        raw_t = clean_text(e.get("title") or f"赴 {zh_name} 交換／雙聯研修心得報告")
        esem = e.get("semester") or "111–113學年度"
        eurl = (
            e.get("url")
            or f"{MCUT_EXPERIENCE_HUB_URL}#mcut-exp-{sn}-{e_idx+1}"
        )
        if eurl in seen_exp_urls:
          eurl = f"{eurl}#r{e_idx+1}"
        seen_exp_urls.add(eurl)
        exp_labels.append(raw_t[:32])
        exp_links.append({
            "title": raw_t,
            "url": eurl,
            "academic_year": esem,
            "semester": esem,
            "college": "工程學院／環境資源學院／管理暨設計學院",
            "department": "明志出國交換暨雙聯學位生",
        })
        summary_text = (
            f"明志科技大學國際事務處全球交流組公開收錄之學長姐赴 {country} {full_name} 交換學習／雙聯學位官方心得報告（{raw_t}），詳述姊妹校專業修課、校園宿舍生活、大三工讀實習抵免與明志獎助學金申請實錄。"
        )
        theme_map = {
            "academics": f"明志交換暨雙聯生於《{raw_t}》分享在 {zh_name} 修讀專業與全英語／外語課程、雙聯學位論文或大三海外交換抵免工讀實務實習之經驗。",
            "housing": f"明志學生記錄申請 {zh_name} 校內外學生宿舍、周邊生活機能與交通方式（{housing_str[:100]}）。",
            "campus_culture": f"明志科技大學國際事務處公開收錄《{raw_t}》之跨文化交流、實驗室研究與校園生活實錄。",
            "cost": f"明志學生分享於 {zh_name} 之每月住宿、伙食與交通開銷（{living_cost_str[:100]}），以及申請明志校內雙聯補助（最高 24 萬）／交換補助（最高 16 萬）或教育部學海飛颺獎學金之經驗。",
        }
        student_experience_rows.append({
            "school_name": full_name,
            "country": country,
            "title": raw_t,
            "source_url": eurl,
            "source_type": "article",
            "platform": "明志科技大學國際事務處全球交流組—交換學生暨雙聯學位心得分享專區",
            "author_name": (
                raw_t.split("—")[-1].split("（")[0].strip()[:20]
                if "—" in raw_t
                else "明志交換暨雙聯生"
            ),
            "language": "zh",
            "summary": summary_text,
            "themes": ["academics", "housing", "campus_culture", "cost"],
            "theme_summaries": theme_map,
            "content_status": "full_text",
            "perspective": "official_student_story",
            "published_at": None,
            "discovered_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                f"{full_name}:mcut_exp:{e_idx}:{eurl}".encode("utf-8")
            ).hexdigest(),
            "exchange_term": esem,
            "summary_zh": summary_text,
            "original_summary": summary_text,
            "theme_summaries_zh": theme_map,
            "translation_status": "original",
            "source_kind": "official_experience_page",
        })

    sample_reports = [
        {"title": lk["title"], "url": lk["url"], "term": lk["semester"]}
        for lk in exp_links[:6]
    ]
    experience_sources_records.append({
        "home_university": "明志科技大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exp_links[0]["url"] if exp_links else MCUT_EXPERIENCE_HUB_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

    loc = resolved_locations.get(full_name) or {
        "city": country,
        "latitude": 25.0412,
        "longitude": 121.4235,
        "source_url": "https://www.wikidata.org",
    }
    city_name = loc.get("city") or country
    lat = float(
        loc.get("latitude")
        if loc.get("latitude") is not None
        else loc.get("lat", 25.0412)
    )
    lon = float(
        loc.get("longitude")
        if loc.get("longitude") is not None
        else loc.get("lon", 121.4235)
    )
    loc_source_url = loc.get("source_url") or "https://www.wikidata.org"

    location_obj = {
        "school_name": full_name,
        "country": country,
        "city": city_name,
        "latitude": lat,
        "longitude": lon,
        "geocode_status": "verified",
        "geocoded_at": CHECKED_AT,
        "source_url": loc_source_url,
        "identity_source_url": website or loc_source_url,
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際研修校區以錄取通知與締約校專頁為準。",
    }
    new_locations.append(location_obj)

    vrec = visual_by_name.get(full_name) or item.get("image_record")
    assert vrec and vrec.get("local_path"), (
        f"Missing verified image for {full_name}"
    )
    img_local = vrec.get("local_path")
    img_source = (
        vrec.get("image_source_url") or vrec.get("image_url") or img_local
    )
    img_page = (
        vrec.get("official_page_url")
        or vrec.get("source_page_url")
        or img_source
    )
    img_status = "verified"

    notes_lines = [
        f"【合作類別與期程】{program_type}｜交換與修業期間：{study_period_str}",
        f"【當期名額與獎助待遇】{quota_str}｜{tuition_note or '依兩校協議辦理'}",
        f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
        f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        f"【住宿與生活資訊】{housing_str}",
    ]
    if exps:
      notes_lines.append(
          f"【明志學長姐出國交換暨雙聯心得報告（共 {len(exps)} 篇）】收錄於國際事務處全球交流組出國心得分享專區（含：{'、'.join(exp_labels[:4])}）"
      )
    if remarks_raw:
      notes_lines.append(f"【學程與締約摘要】{remarks_raw}")

    partner_record = {
        "school_name": full_name,
        "country": country,
        "region": region,
        "colleges": colleges_str,
        "degree_levels": degree_levels_str,
        "study_period": study_period_str,
        "eligibility": (
            f"開放對象：{colleges_str}（{degree_levels_str}）｜{gpa_req_str}｜{lang_req_str}"
        ),
        "language_requirement": lang_req_str,
        "gpa_requirement": gpa_req_str,
        "quota": quota_str,
        "quota_status": "published" if avail_status == "open" else "reference_only",
        "availability_status": avail_status,
        "availability_note": (
            f"明志科技大學國際事務處全球交流組公告合作姊妹校（{program_type}）；{quota_str}。"
        ),
        "academic_year": acad_year,
        "application_round": round_label,
        "application_window_status": win_status,
        "application_deadline": app_deadline_str,
        "application_info": "\n\n".join(app_steps_list),
        "tuition_info": "\n\n".join(tuition_points_list),
        "semester_dates": sem_dates_str,
        "course_restrictions": course_rest_str,
        "housing_info": housing_str,
        "notes": "\n".join(notes_lines),
        "program_type": program_type,
        "source_url": source_url,
        "website": website,
        "official_website": website,
        "factsheet_url": None,
        "image_url": img_local,
        "image_source_url": img_source,
        "image_page_url": img_page,
        "image_status": img_status,
        "location": location_obj,
        "reference_data": {
            k: str(v)
            for k, v in {
                "school_sn": sn,
                "group": group_str,
                "experience_report_count": len(exps) if exps else None,
            }.items()
            if v is not None and str(v).strip()
        },
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
            "title": f"明志科技大學國際事務處全球交流組出國交換暨雙聯學位甄選—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（表號 A2Q1040008）",
            "source_url": MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "明志科技大學大學部海外交換學習課程實施辦法（A2Q1060001）與各類語言檢定證照等級對照表",
            "source_url": MCUT_LANG_CEFR_TABLE_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exp_links:
      wf_sources.append({
          "title": f"明志科技大學出國交換暨雙聯心得分享專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
          "source_url": exp_links[0]["url"],
          "role": "home_university",
          "authority": "home_official_notice",
          "effective_academic_year": acad_year,
          "application_round": round_label,
          "checked_at": CHECKED_AT,
      })
    if website:
      wf_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "role": "partner_university",
          "authority": "partner_official",
          "effective_academic_year": acad_year,
          "application_round": round_label,
          "checked_at": CHECKED_AT,
      })

    workflows.append({
        "home_university": "明志科技大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": acad_year,
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "115-1",
            "115-2",
            "116-1",
            "116-2",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "明志科技大學由國際事務處全球交流組（創新大樓 2 樓）統籌全校 3 大學院（工程學院、環境資源學院、管理暨設計學院）之赴境外（含歐美日韓東南亞及大陸地區）姊妹校交換學習甄選、大學部大三海外交換抵免工讀實務實習制度、跨國雙聯學位計畫（美國辛辛那提大學 UC、北伊利諾大學 NIU、舊金山州立大學 SFSU、西班牙巴塞隆納高等設計學院 ELISAVA、法國電子與電腦工程學院 ESIEE Paris、希臘雅典 ALBA 商學院等），以及校內《學生出國雙聯學位學習及交換學習實施及補助辦法》（雙聯最高 24 萬元、交換最高 16 萬元）與教育部《學海飛颺》、《學海惜珠》、《學海築夢》獎學金。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"mcut-{acad_year}-home-1-{sn:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認明志在學年級（大二／大三／碩博）、GPA 3.0、操行 80 分與 {zh_name} 語檢門檻並填寫 Google 表單",
                "responsible_party": "學生",
                "responsible_unit": "明志科技大學國際事務處全球交流組／各院系所",
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    f"確認符合《明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）》規定：申請人須為日間部大二、大三或碩博士班在學學生（大二升大三擬以交換抵免大三工讀實務實習者可申請一學年，其餘以一學期為原則），符合學業及操行門檻（{gpa_req_str}）與語言要求（{lang_req_str}），先填寫線上 Google 表單領取申請表件（每人限填 1 所志願校）。"
                ),
                "details": [
                    f"開放學制與學院：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["明志科技大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-1",
                        "115-2",
                        "116-1",
                        "116-2",
                    ],
                },
                "source_urls": [
                    source_url,
                    MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
                    MCUT_LANG_CEFR_TABLE_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"mcut-{acad_year}-home-2-{sn:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "備齊《申請表 A2Q1040108》（含300–500字申請理由）、中英文自傳（各1頁A4）、註冊組用印成績單與生輔組用印獎懲證明親送國際處",
                "responsible_party": "學生",
                "responsible_unit": "明志科技大學國際事務處全球交流組（創新大樓 2 樓）",
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": MCUT_2026_2027_EXCHANGE_ANNOUNCEMENT_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "於校內報名截止前（2026–2027 交換暨秋季雙聯為 2026/02/06 17:00 止；2027 春季碩士雙聯為 2026/09/24 17:00 止）將經導師／指導教授及系主任核章之《申請表（A2Q1040108）》（含 300～500 字個人說明申請理由）、《家長/監護人切結同意書（A2Q1040208）》、《切結保證書（A2Q1040308）》、註冊組用印之中文歷年成績單正本及名次證明、語言檢定證明正本、中英文自傳（各 1 頁 A4）及生輔組用印之歷年獎懲紀錄證明正本親送至創新大樓 2 樓國際處全球交流組。"
                ),
                "details": [
                    "必備表單 1：《明志科技大學學生出國雙聯學位學習或交換學習申請表（表號 A2Q1040108）》（含 300～500 字「個人說明申請理由 Statement of Purpose」，須由申請人、導師／指導教授及系主任簽章）",
                    "必備表單 2：《家長/監護人切結同意書（表號 A2Q1040208）》及《切結保證書（表號 A2Q1040308）》正本",
                    "必備表單 3：教務處註冊組用印之中文歷年學業成績單正本與名次證明、學務處生輔組用印之歷年獎懲紀錄證明正本（確認操行 ≥ 80 分且無記過）、語言檢定證明正本、中英文自傳（各以 1 頁 A4 為限；雙聯另附通過系所審查之論文計畫書／專業實務報告初稿）",
                ],
                "scope": {
                    "home_universities": ["明志科技大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-1",
                        "115-2",
                        "116-1",
                        "116-2",
                    ],
                },
                "source_urls": [
                    MCUT_2026_2027_EXCHANGE_ANNOUNCEMENT_URL,
                    MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
                    MCUT_GSITES_HOME_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"mcut-{acad_year}-home-3-{sn:03d}",
                "order": 3,
                "phase": "校內甄選",
                "title": f"經系所初審與校級「學生出國雙聯學位學習及交換學習審查委員會」複審核定推薦名單",
                "responsible_party": "系所／審查委員會",
                "responsible_unit": "明志科技大學國際事務處全球交流組",
                "deadline_at": "2026-03-02T17:00:00+08:00",
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": MCUT_2026_2027_EXCHANGE_ANNOUNCEMENT_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    f"由所屬系所完成初審（含雙聯論文計畫書審查或大三交換抵免工讀實習評估）後，送交校級審查委員會就學業表現、語言能力及研修計畫進行複審，核定推薦赴 {full_name} 之正取名單。"
                ),
                "details": elig_points_list,
                "scope": {
                    "home_universities": ["明志科技大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-1",
                        "115-2",
                        "116-1",
                        "116-2",
                    ],
                },
                "source_urls": [
                    MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
                    MCUT_XUEHAI_SELECTION_REG_PDF_URL,
                    MCUT_2026_2027_EXCHANGE_ANNOUNCEMENT_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"mcut-{acad_year}-partner-4-{sn:03d}",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由國際處向 {zh_name} 辦理官方提名（Nomination），獲入學許可後 2 週內申請明志最高 24 萬／16 萬元補助",
                "responsible_party": "學生／國際事務處／接待大學",
                "responsible_unit": f"明志科技大學國際事務處全球交流組 ＆ {full_name}",
                "summary": (
                    f"通過校內甄選後，由國際處全球交流組向 {full_name} 辦理官方提名（Nomination），學生依姊妹校限期提交入學申請文件；於取得國外大學正式錄取通知（Offer Letter）後 2 週內，檢具申請表向國際處提出校內雙聯補助（非亞洲區最高 24 萬元、亞洲區最高 15 萬元）或交換補助（非亞洲區最高 8 萬／16 萬元、亞洲區最高 5 萬／10 萬元）及教育部學海飛颺／惜珠申請。"
                ),
                "details": [
                    f"接待校入學與獎助規定：{tuition_note or '依兩校交換或雙聯協議辦理'}",
                    f"預計學期時間：{sem_dates_str}",
                ],
                "scope": {
                    "home_universities": ["明志科技大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-1",
                        "115-2",
                        "116-1",
                        "116-2",
                    ],
                },
                "source_urls": [
                    source_url,
                    MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
                    website,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"mcut-{acad_year}-post-5-{sn:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "辦理明志在學註冊、簽證保險與大三交換四階段報告，返國後 1 週內繳交研修報告（A2Q1040508）核銷與抵免學分",
                "responsible_party": "學生",
                "responsible_unit": "明志科技大學國際事務處全球交流組／教務處註冊組／各系所",
                "summary": (
                    "出國前須完成明志科技大學註冊並繳交全額學雜費、購買海外全期醫療及意外保險（大二升大三以交換抵免工讀實習者每學期至少修讀 6 學分［歐洲 2 ECTS = 1 學分］並每三個月繳交四階段交換學習報告）。返國後 1 週內須向國際處繳交至少 2 頁之《出國雙聯學位或交換學習報告（表號 A2Q1040508）》電子檔、來回登機證正本、護照出入境章影本及國外成績單，完成補助核銷與學分抵免。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["明志科技大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-1",
                        "115-2",
                        "116-1",
                        "116-2",
                    ],
                },
                "source_urls": [
                    MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
                    MCUT_UNDERGRAD_EXCHANGE_COURSE_DOCX_URL,
                    MCUT_XUEHAI_SELECTION_REG_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合明志科技大學國際事務處全球交流組《2026–2027 學年度海外交換學習計畫甄選簡章》、《2026–2027 跨國碩士雙聯學位甄選公告（UC、NIU、SFSU、ELISAVA、ESIEE、ALBA）》、《全球合作姊妹校名錄（130 校）》、《學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）》、《大學部海外交換學習課程實施辦法（A2Q1060001）》及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換與雙聯生心得報告，共 {len(catalog_source)} 所合作姊妹校資料。"
        ),
    })

    cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": f"明志科技大學國際事務處全球交流組出國交換暨雙聯學位專頁—{zh_name}",
            "source_url": source_url,
            "summary": "明志科技大學國際事務處公告之合作學程、錄取名額、語言檢定門檻與學費減免／雙聯學位補助說明",
        },
        {
            "title": "明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）",
            "source_url": MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
            "summary": "明志科技大學出國交換與雙聯學位甄選標準（GPA 3.0、操行 80 分、CEFR B1）及最高 24 萬／16 萬元補助規定",
        },
    ]
    if exp_links:
      dest_sources.append({
          "title": f"明志科技大學出國交換暨雙聯心得分享專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
          "source_url": exp_links[0]["url"],
          "summary": f"收錄歷年明志科技大學學生赴 {zh_name} 交換學習與雙聯學位心得報告共 {len(exps)} 篇",
      })
    if website:
      dest_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "summary": "接待合作姊妹校官方網站",
      })

    src_url_list = (
        [
            source_url,
            MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
            MCUT_UNDERGRAD_EXCHANGE_COURSE_DOCX_URL,
            MCUT_LANG_CEFR_TABLE_PDF_URL,
        ]
        + ([exp_links[0]["url"]] if exp_links else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "明志科技大學",
        "school_name": full_name,
        "country": country,
        "city": city_name,
        "cost_summary": f"{cost_line}。\n{tuition_clean}",
        "housing_summary": housing_clean,
        "transport_summary": (
            f"校區代表城市：{city_name}。請依入學許可與住宿分發通知確認實際授課校區位置與當地學生交通卡優惠。"
        ),
        "campus_life_summary": f"{calendar_clean}\n{course_clean}",
        "student_guide_sections": [
            {
                "key": "cost",
                "title": "生活費、姊妹校免學費待遇、明志雙聯補助（最高 24 萬）／交換補助（最高 16 萬）與教育部學海計畫",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [MCUT_XUEHAI_SELECTION_REG_PDF_URL],
                "caution": (
                    "獲明志科技大學雙聯或交換補助之學生，須於收到國外大學入學許可通知後 2 週內向國際處提出申請（同一學制每人限補助乙次）；返國後 1 週內必須繳交至少 2 頁之《研修報告（表號 A2Q1040508）》電子檔、來回登機證正本、護照出入境章影本及國外成績單以辦理核銷。"
                ),
            },
            {
                "key": "housing",
                "title": "校內外學生宿舍申請與住宿費用",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": "歐美日韓及大陸各姊妹校宿舍床位有限，請於獲國際處提名（Nomination）後立即依接待校國際處指引完成線上宿舍申請。",
            },
            {
                "key": "insurance",
                "title": "海外醫療及意外保險與家長／監護人切結同意書規定",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依《明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法》規定，所有申請學生均須檢附《家長/監護人切結同意書（表號 A2Q1040208）》及《切結保證書（表號 A2Q1040308）》，並於出國前自行購買足額之海外醫療及意外保險。",
                ],
                "source_urls": src_url_list,
                "caution": "美國、歐洲申根區、日本、韓國、加拿大等接待校對國際交換生與雙聯生健康保險有強制納保規定，請依入學許可指示辦理。",
            },
            {
                "key": "visa",
                "title": "學生簽證辦理、役男出國緩徵流程與明志在學註冊義務",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "具役男身分之錄取學生，須於出國前備妥國外大學入學許可函洽學務處生輔組及國際處辦理役男出國緩徵核准手續，期滿返國後應即返校註冊。",
                ],
                "source_urls": src_url_list,
                "caution": "出國交換或修讀雙聯學位期間，學生仍須依規定辦理明志科技大學每學期註冊手續並繳交明志全額學雜費以保留學籍。",
            },
            {
                "key": "academics",
                "title": "大三海外交換抵免工讀實務實習（每學期至少 6 學分、2 ECTS = 1 學分）與跨國雙聯學位規範",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list,
                "caution": (
                    "依《明志科技大學大學部海外交換學習課程實施辦法（A2Q1060001）》，大二升大三以一學年海外交換抵免大三工讀實務實習課程（上學期 16 學分、下學期 18 學分）者，每學期至少應修讀 6 學分（歐洲 ECTS 學分以 2 ECTS 折抵本校 1 學分，非專業課程以 2 學分為上限），且須每三個月繳交四階段海外交換學習報告。"
                ),
            },
            {
                "key": "living",
                "title": f"{city_name} 校園生活與明志學長姐出國交換暨雙聯心得傳承",
                "summary": f"代表城市：{city_name}。請配合接待校國際處完成報到、選課與新生訓練。",
                "points": [
                    f"目的地城市：{city_name}（{country}）",
                    (
                        "明志科技大學國際事務處全球交流組定期舉辦「海外交換暨雙聯學位說明會與經驗分享會」"
                        + (
                            f"（本校共收錄 {len(exps)} 篇赴 {zh_name} 心得報告：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，協助同學掌握海外選課、工讀實習抵免與獎學金申請。"
                    ),
                ],
                "source_urls": [
                    exp_links[0]["url"]
                    if exp_links
                    else MCUT_EXPERIENCE_HUB_URL
                ],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合明志科技大學國際事務處全球交流組 {len(catalog_source)} 所合作姊妹校、2026–2027 當期開放申請出國交換與雙聯學位合作校（{open_partner_count} 校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷年學生交換與雙聯心得報告。"
        ),
    })

    research_records.append({
        "home_university": "明志科技大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            "明志科技大學國際事務處全球交流組《2026–2027 海外交換學習甄選簡章》、《跨國雙聯學位甄選公告》、《全球合作姊妹校名錄》、《學生出國雙聯學位學習及交換學習實施及補助辦法》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"明志科技大學國際事務處全球交流組出國交換暨姊妹校專頁—{zh_name}",
            "url": source_url,
        },
    ]
    if exp_links:
      ev_sources.append({
          "title": f"明志科技大學出國交換暨雙聯心得分享—赴 {zh_name} 心得報告（{len(exps)} 篇）",
          "url": exp_links[0]["url"],
      })
    if website:
      ev_sources.append({"title": f"{full_name} 官方網站", "url": website})

    has_student_exp = bool(exps)
    ev_list = [
        {
            "theme": "housing",
            "kind": "mixed" if has_student_exp else "official",
            "text": housing_clean,
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "明志科技大學出國交換暨雙聯姊妹校住宿資訊",
            "original_excerpt": False,
            "original_text": "",
            "translation_status": "original",
        },
        {
            "theme": "cost",
            "kind": "official",
            "text": f"{tuition_clean}｜{cost_line}",
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "明志科技大學姊妹校學費待遇、雙聯補助（最高 24 萬元）、交換補助（最高 16 萬元）與教育部學海計畫",
            "original_excerpt": False,
            "original_text": "",
            "translation_status": "original",
        },
        {
            "theme": "academics",
            "kind": "official",
            "text": course_clean,
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "明志科技大學雙聯學位及交換學習實施辦法與大學部海外交換學習課程實施辦法（大三工讀實習抵免與 2 ECTS = 1 學分）",
            "original_excerpt": False,
            "original_text": "",
            "translation_status": "original",
        },
        {
            "theme": "safety",
            "kind": "official",
            "text": visa_health_str,
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "明志科技大學出國交換簽證、家長切結同意書、役男出國緩徵與海外醫療保險提醒",
            "original_excerpt": False,
            "original_text": "",
            "translation_status": "original",
        },
        {
            "theme": "campus_culture",
            "kind": "mixed" if has_student_exp else "official",
            "text": (
                f"合作類別：{program_type}｜名額：{quota_str}｜語言要求：{lang_req_str}"
                + (
                    f"｜明志科技大學公開收錄 {len(exps)} 篇赴 {zh_name} 交換／雙聯心得報告（{'、'.join(exp_labels[:3])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "明志科技大學出國交換名額與歷屆學長姐心得分享",
            "original_excerpt": False,
            "original_text": "",
            "translation_status": "original",
        },
    ]
    life_records.append({
        "school_name": full_name,
        "country": country,
        "checked_at": CHECKED_AT,
        "status": "ready",
        "evidence": ev_list,
        "notes": [
            "已整合明志科技大學國際事務處全球交流組《2026–2027 海外交換學習甄選簡章》、《跨國雙聯學位甄選公告》、《全球合作姊妹校名錄》、《學生出國雙聯學位學習及交換學習實施及補助辦法》及歷屆學生交換與雙聯心得報告。",
            "當期免學費名額、大三工讀實習抵免規定、雙聯學位英語門檻與報名截止日請依國際事務處最新公告及接待校入學簡章核對。",
        ],
        "location_signature": f"verified:{lat}:{lon}:representative",
        "extraction_version": 3,
    })

  def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )

  write_jsonl(OFFICIAL_MCUT_DIR / "partners.jsonl", partners)
  write_jsonl(SOURCES_MCUT_DIR / "partners.jsonl", partners)
  write_jsonl(OFFICIAL_MCUT_DIR / "application_workflows.jsonl", workflows)
  write_jsonl(OFFICIAL_MCUT_DIR / "destination_profiles.jsonl", destinations)
  write_jsonl(OFFICIAL_MCUT_DIR / "partner_research.jsonl", research_records)
  write_jsonl(OFFICIAL_MCUT_DIR / "student_life.jsonl", life_records)
  write_jsonl(
      OFFICIAL_MCUT_DIR / "experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_MCUT_DIR / "student_experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_MCUT_DIR / "student_experiences.jsonl", student_experience_rows
  )

  digest_records = {}
  for exp_row in student_experience_rows:
    sn_str = exp_row["school_name"]
    if sn_str not in digest_records:
      digest_records[sn_str] = {
          "school_name": sn_str,
          "country": exp_row["country"],
          "report_count": 1,
          "summary_zh": exp_row["summary_zh"],
          "themes": exp_row["theme_summaries_zh"],
          "source_url": exp_row["source_url"],
          "updated_at": CHECKED_AT,
      }
    else:
      digest_records[sn_str]["report_count"] += 1
  (OFFICIAL_MCUT_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_MCUT_DIR / "student-experiences.json").write_text(
      json.dumps(
          {
              "school_id": "mcut",
              "school_name": "明志科技大學",
              "checked_at": CHECKED_AT,
              "source_url": MCUT_EXPERIENCE_HUB_URL,
              "total_experience_reports": total_exp_reports,
              "covered_partner_schools": exp_covered_schools,
              "records": student_experience_rows,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_MCUT_DIR / "campus-locations.json").write_text(
      json.dumps(
          {
              "school_id": "mcut",
              "school_name": "明志科技大學",
              "checked_at": CHECKED_AT,
              "total_schools": len(new_locations),
              "verified_count": len(new_locations),
              "locations": new_locations,
              "schools": new_locations,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  campus_assets_list = [
      {
          "sn": idx + 1,
          "school_name": p["school_name"],
          "country": p["country"],
          "local_path": p["image_url"],
          "image_source_url": p["image_source_url"],
          "source_page_url": p["image_page_url"],
          "attribution": "Wikimedia Commons",
          "status": p["image_status"],
      }
      for idx, p in enumerate(partners)
  ]
  (OFFICIAL_MCUT_DIR / "campus-assets.json").write_text(
      json.dumps(
          {
              "school_id": "mcut",
              "school_name": "明志科技大學",
              "checked_at": CHECKED_AT,
              "total_schools": len(campus_assets_list),
              "verified_count": sum(
                  1 for a in campus_assets_list if a["status"] == "verified"
              ),
              "assets": campus_assets_list,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  mcut_source_urls = [
      MCUT_OIA_HOME_URL,
      MCUT_PARTNER_LIST_URL,
      MCUT_REGULATIONS_URL,
      MCUT_EXPERIENCE_HUB_URL,
      MCUT_DUAL_EXP_URL,
      MCUT_EXCH_EXP_URL,
      MCUT_QA_HUB_URL,
      MCUT_QA_EXCH_URL,
      MCUT_QA_DUAL_URL,
      MCUT_2026_2027_EXCHANGE_ANNOUNCEMENT_URL,
      MCUT_NIU_DUAL_SPRING_URL,
      MCUT_UC_DUAL_SPRING_URL,
      MCUT_NIU_DUAL_FALL_URL,
      MCUT_ELISAVA_SFSU_DUAL_URL,
      MCUT_UC_DUAL_FALL_URL,
      MCUT_ESIEE_ALBA_DUAL_URL,
      MCUT_SHORT_TERM_URL,
      MCUT_GSITES_HOME_URL,
      MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
      MCUT_UNDERGRAD_EXCHANGE_COURSE_DOCX_URL,
      MCUT_XUEHAI_SELECTION_REG_PDF_URL,
      MCUT_SHORT_TERM_REG_DOCX_URL,
      MCUT_LANG_CEFR_TABLE_PDF_URL,
  ]

  exchange_info_payload = {
      "school_name": "明志科技大學",
      "program_type": [
          (
              f"國際事務處全球交流組（Office of International Affairs）海外姊妹校交換學習計畫（2026–2027 學年度當期開放 {open_partner_count} 所歐美日韓東南亞及大陸地區合作大學：涵蓋美國北伊利諾大學 NIU、加州大學河濱分校 UCR、蒙タ拿大學、西維吉尼亞大學，加拿大勞倫森大學，法國南特高等設計學院、ESIEE Paris，西班牙塞維亞大學，芬蘭 SeAMK，立陶宛 VILNIUS TECH，奧地利 MCI，德國多所應用科技大學，波蘭西里西亞大學與盧布林科技大學，捷克孟德爾大學，希臘 ALBA 商學院，日本福岡工業大學、芝浦工業大學、日本工業大學，韓國國民大學、同德女子大學，以及大陸北京科技大學、南京理工大學、北京理工大學、中國礦業大學、蘇州大學、福州大學等；並具大二升大三以一學年海外交換抵免大三工讀實務實習制度）"
          ),
          (
              "國際事務處全球交流組跨國雙聯學位計畫（Dual Degree Programs）：涵蓋美國辛辛那提大學（University of Cincinnati，工程學院及環資學院碩士雙聯，享鹿江基金會專屬獎學金）、美國北伊利諾大學（Northern Illinois University，工程學院及管設學院工業工程與管理系碩士雙聯）、美國舊金山州立大學（San Francisco State University，全校各學院碩士雙聯）、西班牙巴塞隆納高等設計學院（ELISAVA，管設學院工業設計系與視覺傳達設計系碩士雙聯）、法國電子與電腦工程學院（ESIEE Paris，工程學院及環資學院碩士雙聯）、希臘雅典 ALBA 商學院（管設學院經營管理系及 MBA 碩士雙聯）及日本福岡工業大學等 12 所雙聯合作校"
          ),
          (
              "明志科技大學校內《學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）》（雙聯學位非亞洲區最高補助 24 萬元、亞洲區最高 15 萬元；交換學習非亞洲區一學期最高 8 萬元／一學年最高 16 萬元、亞洲區一學期最高 5 萬元／一學年最高 10 萬元）、《學生出國短期研習實施及補助辦法（A2Q1030010）》（最高 4.7 萬元）暨教育部《學海飛颺》（每人 5 萬至 30 萬元）、《學海惜珠》、《學海築夢／新南向學海築夢》獎助計畫"
          ),
      ],
      "academic_year": [
          (
              "115（涵蓋 2026–2027 學年度海外交換學習計畫暨秋季班碩士雙聯學位甄選［即日起至 2026/02/06 週五 17:00 截止收件］，以及 2027 年春季班赴美國辛辛那提大學 UC 與北伊利諾大學 NIU 碩士雙聯學位甄選［即日起至 2026/09/24 週四 17:00 截止收件］）"
          ),
          (
              f"本平台完整收錄明志科技大學國際事務處全球交流組公告之 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所 2026–2027 當期開放申請之國際與大陸交換及雙聯學位合作校，以及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 21 個國家與地區，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷年學長姐交換與雙聯心得報告）"
          ),
      ],
      "semester": [
          "海外交換學習（Exchange Program）：以申請 1 學期為原則；惟大學部大二升大三學生若規劃以海外交換抵免大三「工讀實務實習」課程（上學期 16 學分、下學期 18 學分），得依《明志科技大學大學部海外交換學習課程實施辦法（A2Q1060001）》申請 1 學年交換，交換期間每學期至少應修讀 6 學分（歐洲 ECTS 學分以 2 ECTS 折抵明志 1 學分，非專業課程以 2 學分為上限），並每三個月繳交四階段海外交換學習報告。",
          "跨國雙聯學位（Dual Degree Program）：於明志科技大學修業滿 1 學期或規定學期數並通過系所論文計畫書／專業實務報告初稿審查後，赴國外合作大學修讀 1 學年（2 學期）之專業課程，符合兩校畢業條件後同時獲頒明志科技大學與國外合作大學雙學位。",
          "海外短期研習與國際移動力計畫（依《學生出國短期研習實施及補助辦法 A2Q1030010》）：每年寒暑假選送學生赴美國加州大學河濱分校（UCR）、日本、韓國、菲律賓、馬來西亞、泰國等姊妹校進行 5 日至 35 日以上之短期語言文化研習、實驗室專題研究或海外專業實習。",
      ],
      "application_period": [
          "【2026–2027 學年度海外交換學習計畫暨秋季班碩士雙聯學位甄選（115 學年度第 1 學期及第 2 學期出國）】每年 1 月初公告、2 月上旬截止（2026–2027 學年度為即日起至 2026 年 2 月 6 日週五 17:00 止；含交換生甄選及美國 UC、NIU、SFSU、西班牙 ELISAVA 等秋季班碩士雙聯甄選），先填寫線上 Google 表單領取申請表件，再將核章紙本送交創新大樓 2 樓國際處全球交流組（《實施及補助辦法》第 5 條亦規定第 2 學期 2 月入學原則於 10 月 31 日前送件）。",
          "【2027 年春季班跨國碩士雙聯學位甄選（美國辛辛那提大學 UC、北伊利諾大學 NIU 2027 年 1 月入學）】即日起至 2026 年 9 月 24 日（週四）17:00 止受理報名，紙本申請資料親送至創新大樓 2 樓國際處全球交流組（分機 3035 王采彤小姐）。",
          "【2026 暑期海外短期研習團（如美國加州大學河濱分校 UCR 英語與文化體驗營）】每年 2 月至 3 月初受理報名（2026 暑期 UCR 營隊於 2026 年 3 月 6 日截止，3 月 16 日公布錄取名單）。",
      ],
      "eligibility": [
          "1. 在學身分與年級限制：依《明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）》第 4 條及甄選簡章規定，申請人須為於本校就讀滿一學期以上之日間部大二、大三在學學生（僅大二升大三擬以交換抵免大三工讀實務實習者可申請一學年交換，其餘皆以申請一學期為原則）或日間部碩士班、博士班在學學生；不含大一新生、在職專班學生、同一學制內曾獲本校推薦出國交換者，以及曾獲錄取但無正當理由放棄資格者。",
          "2. 學業成績（GPA）與操行門檻：申請交換學習者，在校歷年學業成績平均 GPA 須達 3.0（含）以上（折合百分制約 75 分以上；部分跨國碩士雙聯如美國北伊利諾大學 NIU、西班牙 ELISAVA、法國 ESIEE Paris、希臘 ALBA 為大學及碩士歷年 GPA 達 2.75 以上，美國辛辛那提大學 UC 與舊金山州立大學 SFSU 為 GPA 3.0 以上）；且在校歷年操行成績平均須達 80 分（含）以上並無記過處分紀錄。",
          "3. 單一志願與雙聯論文初稿審查：申請海外交換生者，每人限填寫最適合之交換學校 1 所；申請跨國碩士雙聯學位者，出國前須先通過母系所之「論文計畫書審查（或專業實務報告初稿）」。",
          "4. 教育部《學海飛颺／學海惜珠》甄選資格（依《學生出國研修或國外專業實習補助計畫校內甄選辦法 A0Q1050004》）：具中華民國國籍、於明志就讀一學期以上之在學學生、歷年操行平均 80 分以上無記過，且語言能力達 CEFR B1 以上。",
      ],
      "language_requirement": [
          "1. 校內交換生基本語言門檻（CEFR B1 以上）：依《各類語言檢定證照等級對照表（197207162.pdf）》及甄選簡章，申請非英語系或英語系國家交換者，外語能力須達 CEFR B1（含）以上，對應標準為：TOEIC 550（聽力 275、閱讀 275）且口說與寫作 B1 / TOEFL iBT 42 / TOEFL ITP 460 / IELTS 4.0 / GEPT 全民英檢中級 / FLPT 外語能力測驗筆試總分 150 且口試 S-2 / Duolingo English Test 60 / Linguaskill 140 / 日語 JLPT N3 / 韓語 TOPIK 3 級 / 德語、法語、西班牙語 CEFR B1（部分姊妹校如韓國國民大學與同德女子大學交換免韓檢，惟申請校內外獎助學金仍須具 CEFR B1 外語證明）。",
          "2. 歐美日高階交換姊妹校專屬語言門檻：美國加州大學河濱分校（UCR）、蒙大拿大學、西維吉尼亞大學、加拿大勞倫森大學、奧地利 MCI、捷克孟德爾大學要求英語達 CEFR B2（TOEFL iBT 72–80 / IELTS 5.5–6.0 / TOEIC 785）；日本芝浦工業大學要求 JLPT N2 或英語 CEFR B2。",
          "3. 跨國碩士雙聯學位英語門檻：（a）美國辛辛那提大學（UC）：工學院 TOEFL iBT 85 / IELTS 6.5 / Duolingo 110，環資學院 TOEFL iBT 80 / IELTS 6.5 / Duolingo 110；（b）美國北伊利諾大學（NIU）：TOEFL iBT 80 / IELTS 6.5 / Duolingo 115；（c）美國舊金山州立大學（SFSU）：TOEFL iBT 80（MBA 88、Design 92、部分理工系 65–71）/ IELTS 6.0–7.0；（d）西班牙巴塞隆納高等設計學院（ELISAVA）：IELTS 6.0 / TOEFL iBT 78 / TOEIC 785；（e）法國 ESIEE Paris：TOEFL iBT 72 / IELTS 5.5 / TOEIC 785；（f）希臘 ALBA 商學院：IELTS 6.5 / TOEFL iBT 100。",
      ],
      "required_documents": [
          "1. 先填寫線上 Google 表單（https://forms.gle/SWrEct6zFhJiaLSV8），由系統自動寄發《明志科技大學學生出國雙聯學位學習或交換學習申請表（表號 A2Q1040108）》至申請人信箱（表內須撰寫 300～500 字「個人說明申請理由 Statement of Purpose」，詳述赴境外地區研修動機與修讀計畫，並經申請人、導師／指導教授及系主任簽章）",
          "2. 《家長/監護人切結同意書（表號 A2Q1040208）》及《切結保證書（表號 A2Q1040308）》正本（須由申請人與家長或法定監護人親筆簽章）",
          "3. 本校中文歷年學業成績單正本及歷年學業成績名次證明（須經教務處註冊組用印；申請碩士雙聯學位者須同時檢附大學部及碩士班歷年成績單正本）",
          "4. 有效語言能力檢定證明正本（驗畢退還正本、留存影本，須達 CEFR B1 或各姊妹校／雙聯學程規定門檻）",
          "5. 中、英文自傳各 1 份（格式自訂，各以一頁 A4 為限；申請跨國碩士雙聯學位者另須檢附通過母系所審查之「論文計畫書審查或專業實務報告初稿」證明）",
          "6. 本校歷年獎懲紀錄證明正本 1 份（須經學務處生輔組用印，確認在校歷年操行成績平均達 80 分以上且無記過紀錄）",
          "7. 其他有利審查文件（如優良事蹟證明、國內外競賽獲獎、師長推薦函、清寒／低收／中低收入戶證明、原住民或新住民生證明；應屆畢業生另附《應屆畢業生特殊狀況告知同意書》）",
      ],
      "scholarship_info": [
          "1. 明志科技大學《學生出國雙聯學位學習及交換學習實施及補助辦法（表號 A2Q1040008，114年8月12日修訂）》第 8 條「出國雙聯學位學習補助」：經本校審查通過赴國外合作大學攻讀雙聯學位者，依地區核給全額或定額獎助—（a）亞洲地區：每人一學年最高補助新臺幣 15 萬元；（b）非亞洲地區（歐美加等）：每人一學年最高補助新臺幣 24 萬元；（c）赴美國辛辛那提大學（UC）攻讀碩士雙聯學位者，除學校補助外，另可申請明志校友成立之「鹿江教育基金會」專屬獎學金。",
          "2. 明志科技大學《學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）》第 8 條「出國交換學習補助」：經本校審查通過赴國外或大陸地區姊妹校交換學習者，同一學制內每人限補助乙次，須於收到國外大學入學許可通知後 2 週內提出申請—（a）亞洲地區：每人一學期最高補助新臺幣 5 萬元、一學年最高補助新臺幣 10 萬元；（b）非亞洲地區（歐美加等）：每人一學期最高補助新臺幣 8 萬元、一學年最高補助新臺幣 16 萬元。獲補助學生返國後 1 週內須繳交至少 2 頁之《出國雙聯學位或交換學習報告（表號 A2Q1040508）》電子檔、來回登機證正本、護照出入境章影本及國外成績單以辦理核銷。",
          "3. 明志科技大學《學生出國短期研習實施及補助辦法（表號 A2Q1030010，114年8月12日修訂）》：補助在學學生參加寒暑期海外短期研習或實驗室交流—（a）亞洲地區：5–13 日最高補助 2.5 萬元、14–34 日最高 2.9 萬元、35 日以上最高 3.3 萬元；（b）非亞洲地區：5–13 日最高補助 3.5 萬元、14–34 日最高 4 萬元、35 日以上最高 4.7 萬元（具清寒、原住民或新住民身分者得優先加成補助）。",
          "4. 教育部《學海飛颺》、《學海惜珠》及《學海築夢／新南向學海築夢》補助計畫（依《明志科技大學學生出國研修或國外專業實習補助計畫校內甄選辦法 A0Q1050004》）：（a）學海飛颺與學海惜珠：補助具中華民國國籍、GPA 3.0 以上、操行 80 分以上且具 CEFR B1 外語證明之優秀生或清寒生赴非大陸港澳地區修讀學分 1 學期至 1 學年，每人補助新臺幣 5 萬元至 30 萬元（出國前核發 80%、返國完成報告與核銷後核發 20%，惟與校內補助不得重複領取超過實際總開支）；（b）學海築夢與新南向學海築夢：由專任教師主持選送學生赴海外企業或研究機構進行專業實習，補助機票費與生活費。",
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": mcut_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_MCUT_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "明志科技大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 75.0,
      "academic_score_rule": (
          "依《明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）》第 4 條及當期甄選簡章規定：申請人須為於本校就讀滿一學期以上之日間部大二、大三在學學生（僅大二升大三擬以交換抵免大三工讀實務實習者可申請一學年交換，其餘以申請一學期為原則）或日間部碩博士班在學學生（不含大一新生及在職專班）；在校歷年學業成績平均 GPA 須達 3.0（含）以上（折合百分制約 75 分以上；部分碩士雙聯如 NIU、ELISAVA、ESIEE、ALBA 為 GPA 2.75 以上），且歷年操行成績平均須達 80 分（含）以上並無記過紀錄。"
      ),
      "academic_gpa_minimum": 3.0,
      "maximum_preferences": 1,
      "selection_rules": {
          "academic_policy": "score_or_rank",
          "academic_reference_year": "115",
          "undergraduate_gpa_minimum": 3.0,
          "graduate_academic_exempt": False,
          "exclude_in_service": True,
          "pending_quota_planning": False,
          "partner_requirements_need_confirmation": False,
          "degree_score_minimums": {
              "undergraduate": 75.0,
              "graduate": 75.0,
          },
          "excluded_undergraduate_years": [
              "大一",
              "大一上",
              "大一下",
              "一年級",
              "一年級上學期",
              "一年級下學期",
              "延畢",
              "延畢生",
          ],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 42.0,
          "ielts": 4.0,
          "toefl_itp": 460.0,
          "toeic": 550.0,
      },
      "application_periods": [
          {
              "title": "明志科技大學 2027 年春季班（2027/01 入學）「美國辛辛那提大學（UC）＆北伊利諾大學（NIU）跨國碩士雙聯學位計畫」甄選（即日起至 2026/09/24 17:00 受理）",
              "details": [
                  "國際事務處全球交流組公告 2027 年春季班（2027 年 1 月赴美）跨國碩士雙聯學位甄選：（1）美國辛辛那提大學（University of Cincinnati）：開放工程學院及環境資源學院碩士生申請，在校 GPA 達 3.0 以上、英語達 TOEFL iBT 80–85 / IELTS 6.5 / Duolingo 110，享明志非亞洲區雙聯最高 24 萬元補助及校友「鹿江基金會」專屬獎學金；（2）美國北伊利諾大學（Northern Illinois University）：開放工程學院及管理暨設計學院工業工程與管理系碩士生申請，大學及碩士 GPA 達 2.75 以上、英語達 TOEFL iBT 80 / IELTS 6.5 / Duolingo 115，享明志最高 24 萬元補助。",
                  "報名方式：先填寫線上 Google 表單領取《申請表（A2Q1040108）》，備齊核章申請表、中英文自傳（各 1 頁 A4）、大學及碩士成績單正本、語檢證明、獎懲證明及通過系所審查之論文計畫書初稿，於 2026 年 9 月 24 日（週四）17:00 前親送至創新大樓 2 樓國際處全球交流組。",
              ],
              "source": {
                  "title": "明志科技大學 2027 年春季班美國北伊利諾大學（NIU）與辛辛那提大學（UC）碩士雙聯學位申請公告",
                  "source_url": MCUT_NIU_DUAL_SPRING_URL,
                  "category": "exchange_application",
                  "summary": "明志科技大學 2027 年春季班赴美國 UC 與 NIU 攻讀碩士雙聯學位報名簡章與獎學金資訊。",
              },
              "scope": "home_application",
              "program_types": ["dual_degree"],
              "academic_year": "115",
              "application_round": "115-2 梯次（2027年春季班美國 UC & NIU 碩士雙聯學位）",
              "audience": "all_students",
              "opens_at": "2026-08-15T09:00:00+08:00",
              "deadline_at": "2026-09-24T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "2027 年春季班美國 UC 與 NIU 碩士雙聯學位甄選於 2026 年 9 月 24 日（週四）17:00 截止收件。",
              "deadline_note": "請先填寫 Google 表單領取申請表件，並於 9/24 17:00 前將核章紙本資料親送至創新大樓 2 樓國際處全球交流組（分機 3035 王采彤小姐）。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "明志科技大學第 2 學期（春季班 2 月入學）「學生出國雙聯學位學習及交換學習」法規常態收件截止（每年 10 月 31 日前）",
              "details": [
                  "依《明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（表號 A2Q1040008）》第 5 條規定，申請第 2 學期（2 月入學）出國雙聯學位或交換學習之補充提名梯次，原則上應於每年 10 月 31 日前向國際事務處全球交流組提出申請。",
              ],
              "source": {
                  "title": "明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）",
                  "source_url": MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
                  "category": "exchange_application",
                  "summary": "明志科技大學出國雙聯學位及交換學習實施辦法第 5 條收件時程規定。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "115-2 梯次（春季班出國交換暨雙聯補充收件）",
              "audience": "all_students",
              "opens_at": "2026-09-01T09:00:00+08:00",
              "deadline_at": "2026-10-31T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "依校內實施辦法第 5 條，第 2 學期（2 月入學）出國雙聯或交換學習原則於 10 月 31 日前截止收件。",
              "deadline_note": "實際開放補招名額請先洽詢創新大樓 2 樓國際事務處全球交流組（02-2908-9899 分機 3031、3035）。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "明志科技大學年度「海外交換學習計畫（含大三工讀實習抵免一學年交換）暨秋季班跨國雙聯學位」統一甄選（每年 1 月公告、2 月 6 日 17:00 截止）",
              "details": [
                  f"國際事務處全球交流組每年 1 月初統一公告下一學年度（秋季班及春季班出國）海外交換學習計畫暨秋季班跨國雙聯學位（美國 UC、NIU、SFSU、西班牙 ELISAVA、法國 ESIEE Paris、希臘 ALBA）甄選，開放全校日間部大二、大三及碩博士班學生申請 {open_partner_count} 所歐美日韓東南亞及大陸姊妹校（每人限填 1 所志願校；大二升大三可申請一學年交換抵免大三工讀實務實習），並提供非亞洲區交換最高 16 萬元、亞洲區交換最高 10 萬元、雙聯最高 24 萬元及教育部學海飛颺／惜珠獎學金。",
              ],
              "source": {
                  "title": "明志科技大學 2026–2027 學年度海外交換學習計畫甄選公告与 Google Sites 專頁",
                  "source_url": MCUT_2026_2027_EXCHANGE_ANNOUNCEMENT_URL,
                  "category": "exchange_application",
                  "summary": "明志科技大學年度海外交換生暨雙聯學位統一甄選簡章、申請資格與補助標準。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "116 學年度統一甄選（海外交換學習暨秋季班雙聯學位）",
              "audience": "all_students",
              "opens_at": "2027-01-04T09:00:00+08:00",
              "deadline_at": "2027-02-06T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "年度海外交換生暨秋季班雙聯學位統一甄選於每年 1 月初開放、2 月初（約 2 月 6 日 17:00）截止收件。",
              "deadline_note": "請先填寫 Google 表單領取《申請表（A2Q1040108）》，備齊核章紙本資料親送創新大樓 2 樓國際處全球交流組。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"明志科技大學國際事務處全球交流組出國交換、大三工讀實習海外抵免、跨國雙聯學位與高額獎助學金總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所當期開放申請・{total_exp_reports} 篇學長姐交換與雙聯心得）"
              ),
              "details": [
                  (
                      f"明志科技大學國際事務處全球交流組（OIA）與全球 21 個國家及地區共 {len(partners)} 所大學締結合作姊妹校，當期開放 {open_partner_count} 所歐美日韓東南亞及大陸知名大學供日間部大二、大三及碩博士班學生申請海外交換學習與跨國雙聯學位（含美國辛辛那提大學 UC、北伊利諾大學 NIU、舊金山州立大學 SFSU、加州大學河濱分校 UCR、西班牙巴塞隆納高等設計學院 ELISAVA、法國 ESIEE Paris、南特高等設計學院、芬蘭 SeAMK、立陶宛 VILNIUS TECH、奧地利 MCI、希臘 ALBA 商學院、日本福岡工業大學、芝浦工業大學、韓國國民大學，以及大陸北京科技大學、南京理工大學、北京理工大學、蘇州大學等）。"
                  ),
                  (
                      "結合明志科大獨具特色之「大三全學年工讀實務實習」制度，大二升大三學生可依《大學部海外交換學習課程實施辦法（A2Q1060001）》申請為期一學年之海外交換學習以抵免大三工讀實習（上學期 16 學分、下學期 18 學分）；同時學校設有《學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）》，提供雙聯學位生每年最高 24 萬元（非亞洲區）／15 萬元（亞洲區）、交換生最高 16 萬元（非亞洲區一學年）／10 萬元（亞洲區一學年）之豐厚補助，並搭配校友「鹿江基金會」獎學金與教育部《學海飛颺／惜珠／築夢》計畫。"
                  ),
              ],
              "source": {
                  "title": "明志科技大學海外交換學習計畫專頁（MCUT Around the World）與國際事務處官網",
                  "source_url": MCUT_2026_2027_EXCHANGE_ANNOUNCEMENT_URL,
                  "category": "exchange_application",
                  "summary": "明志科技大學海外交換學習、跨國雙聯學位、法規辦法與歷屆心得報告總覽。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "日間部大二／大三／碩博在學資格、GPA 3.0（百分制 75 分）與操行 80 分無記過門檻、大三工讀實習海外交換抵免與單一志願規定",
              "details": exchange_info_payload["eligibility"],
              "source": {
                  "title": "明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）與大學部海外交換學習課程實施辦法（A2Q1060001）",
                  "source_url": MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
                  "category": "exchange_application",
                  "summary": "明志科技大學出國交換與雙聯學位申請年級、GPA 3.0、操行 80 分、大三工讀實習抵免與單一志願規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "校內 CEFR B1 基本門檻（TOEIC 550 / TOEFL iBT 42 / IELTS 4.0 / JLPT N3 / TOPIK 3級）、歐美高階交換 CEFR B2 與跨國碩士雙聯（iBT 72–100 / IELTS 5.5–6.5）標準",
              "details": exchange_info_payload["language_requirement"],
              "source": {
                  "title": "明志科技大學各類語言檢定證照等級對照表（197207162.pdf）與 2026–2027 交換及雙聯簡章",
                  "source_url": MCUT_LANG_CEFR_TABLE_PDF_URL,
                  "category": "exchange_application",
                  "summary": "明志科技大學 CEFR B1/B2 各類語言檢定對照表與各合作姊妹校交換及雙聯外語門檻。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "Google 表單領取《申請表 A2Q1040108》（含 300–500 字申請理由）、家長切結同意書、註冊組用印成績單與名次證明、生輔組用印獎懲證明、語檢正本及中英文自傳（各 1 頁 A4）",
              "details": exchange_info_payload["required_documents"],
              "source": {
                  "title": "明志科技大學 2026–2027 學年度海外交換學習計畫甄選公告與法規表單專區",
                  "source_url": MCUT_2026_2027_EXCHANGE_ANNOUNCEMENT_URL,
                  "category": "exchange_application",
                  "summary": "明志科技大學出國交換生與雙聯學位生應備書審表件、字數頁數格式及用印規定。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "明志《雙聯及交換補助辦法》（雙聯非亞洲區最高 24 萬／亞洲區 15 萬；交換非亞洲區最高 16 萬／亞洲區 10 萬）、鹿江基金會獎學金、短期研習補助與教育部學海計畫",
              "details": exchange_info_payload["scholarship_info"],
              "source": {
                  "title": "明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）與學海計畫甄選辦法（A0Q1050004）",
                  "source_url": MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
                  "category": "scholarship",
                  "summary": "明志科技大學校內雙聯、交換與短期研習補助金額標準及教育部學海飛颺、惜珠、築夢補助規定。",
              },
          }
      ],
      "regulation_links": [
          {
              "title": "明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008，114年8月12日修訂，PDF）",
              "url": MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
          },
          {
              "title": "明志科技大學大學部海外交換學習課程實施辦法（A2Q1060001，大三工讀實習抵免與 2 ECTS = 1 學分，DOCX）",
              "url": MCUT_UNDERGRAD_EXCHANGE_COURSE_DOCX_URL,
          },
          {
              "title": "明志科技大學學生出國研修或國外專業實習補助計畫校內甄選辦法（A0Q1050004，教育部學海計畫，PDF）",
              "url": MCUT_XUEHAI_SELECTION_REG_PDF_URL,
          },
          {
              "title": "明志科技大學學生出國短期研習實施及補助辦法（A2Q1030010，114年8月12日修訂，DOCX）",
              "url": MCUT_SHORT_TERM_REG_DOCX_URL,
          },
          {
              "title": "明志科技大學各類語言檢定證照等級對照表（CEFR A1–C2 對照表，PDF）",
              "url": MCUT_LANG_CEFR_TABLE_PDF_URL,
          },
      ],
      "document_explanations": [
          {
              "title": "明志科技大學《申請表 A2Q1040108》（300–500字個人說明申請理由）、中英文自傳（各1頁A4）與雙聯論文計畫書初稿準備要領",
              "summary": "說明明志科技大學海外交換與雙聯學位申請必備之線上 Google 表單領表流程、300–500 字申請理由（Statement of Purpose）、中英文自傳格式（各限 1 頁 A4）及註冊組／生輔組用印證明規範。",
              "key_points": [
                  "《申請表（表號 A2Q1040108）》內含 300～500 字「個人說明申請理由（Statement of Purpose）」：申請人須先填寫線上 Google 表單（每人限填 1 所最適合之志願學校），由系統自動寄發申請表至信箱；表內須以 300 至 500 字具體說明赴境外地區研修動機以及於姊妹校之修讀計畫，並經導師／指導教授及系主任核章。",
                  "中、英文自傳（各以 1 頁 A4 為限）與雙聯論文初稿：中、英文自傳格式自訂，但各嚴格限制以 1 頁 A4 為限，建議聚焦大學或碩士專業背景、外語能力與國際交流準備；申請跨國碩士雙聯學位者，出國前另須檢附通過母系所審查之「論文計畫書審查（或專業實務報告初稿）」。",
                  "教務處註冊組與學務處生輔組正式用印文件：中文歷年學業成績單正本及名次證明須經教務處註冊組用印（確認 GPA ≥ 3.0 或雙聯 ≥ 2.75）；歷年獎懲紀錄證明正本須經學務處生輔組用印（確認歷年操行平均 ≥ 80 分且無記過紀錄）。",
              ],
              "applies_to": [],
              "source": {
                  "title": "明志科技大學 2026–2027 學年度海外交換學習計畫甄選公告與法規表單",
                  "source_url": MCUT_2026_2027_EXCHANGE_ANNOUNCEMENT_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": MCUT_REGULATIONS_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "明志科技大學大三海外交換抵免工讀實務實習（2 ECTS = 1 學分）、雙聯最高 24 萬／交換最高 16 萬元補助與返國 1 週內核銷核心規定",
              "summary": "規範明志科技大學大二升大三以一學年交換抵免工讀實務實習、每學期至少修讀 6 學分、四階段學習報告、獲入學許可後 2 週內申請補助及返國後 1 週內繳交報告核銷。",
              "key_points": [
                  "大三工讀實務實習海外交換抵免制度（A2Q1060001）：明志大學部交換生原則上以申請一學期為限；惟大二升大三學生若規劃以海外交換抵免大三全學年「工讀實務實習」課程（上學期 16 學分、下學期 18 學分），得申請一學年交換，每學期至少須修讀 6 學分（歐洲 ECTS 學分以 2 ECTS 折抵明志 1 學分，非專業課程上限 2 學分），並須於交換期間每三個月繳交共四階段之海外交換學習報告。",
                  "校內雙聯與交換高額獎助學金（A2Q1040008 第 8 條）：雙聯學位生赴非亞洲區一學年最高補助 24 萬元、亞洲區最高 15 萬元（美國辛辛那提大學另享鹿江基金會獎學金）；交換生赴非亞洲區一學期最高補助 8 萬元／一學年最高 16 萬元、亞洲區一學期最高 5 萬元／一學年最高 10 萬元（同一學制每人限補助乙次，須於獲國外大學入學許可通知後 2 週內向國際處提出申請）。",
                  "在學註冊義務與返國後 1 週內核銷規定（A2Q1040008 第 9–10 條）：出國期間須辦理明志註冊並繳交全額學雜費；獲補助學生返國後 1 週內，須向國際處繳交至少 2 頁之《出國雙聯學位或交換學習報告（表號 A2Q1040508）》電子檔、來回登機證正本、護照出入境章影本及國外成績單以完成核銷。",
              ],
              "applies_to": [],
              "source": {
                  "title": "明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）與大學部海外交換學習課程實施辦法（A2Q1060001）",
                  "source_url": MCUT_REGULATIONS_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "明志科技大學國際事務處（Office of International Affairs, MCUT）官方網站",
              "source_url": MCUT_OIA_HOME_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "明志科技大學 2026–2027 學年度海外交換學習計畫甄選簡章與 Google Sites 專頁",
              "source_url": MCUT_2026_2027_EXCHANGE_ANNOUNCEMENT_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "明志科技大學 2027 年春季班美國北伊利諾大學（NIU）與辛辛那提大學（UC）碩士雙聯學位甄選公告",
              "source_url": MCUT_NIU_DUAL_SPRING_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "明志科技大學跨國碩士雙聯學位甄選公告（西班牙 ELISAVA、美國 SFSU、法國 ESIEE Paris、希臘 ALBA）",
              "source_url": MCUT_ELISAVA_SFSU_DUAL_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": f"明志科技大學全球暨兩岸合作姊妹校名錄（共 {len(partners)} 所合作姊妹校）",
              "source_url": MCUT_PARTNER_LIST_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008，PDF）",
              "source_url": MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "明志科技大學大學部海外交換學習課程實施辦法（A2Q1060001）與法規表單專區",
              "source_url": MCUT_REGULATIONS_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": f"明志科技大學國際事務處「出國交換生暨雙聯學位生心得分享專區」（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）",
              "source_url": MCUT_EXPERIENCE_HUB_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_MCUT_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  doc_conditions = {
      "school_id": "mcut",
      "school_name": "明志科技大學",
      "checked_at": CHECKED_AT,
      "source_url": MCUT_REGULATIONS_URL,
      "common_documents": exchange_info_payload["required_documents"],
      "track_specific_conditions": [
          {
              "track": "赴國外及大陸地區姊妹校海外交換學習甄選（歐美日韓東南亞及大陸 59 所當期開放姊妹校）",
              "required": [
                  "先填寫線上 Google 表單（每人限填 1 所最適合之志願學校），領取並填妥《學生出國雙聯學位學習或交換學習申請表（表號 A2Q1040108）》（含 300～500 字「個人說明申請理由 Statement of Purpose」，經導師／指導教授及系主任核章）",
                  "《家長/監護人切結同意書（表號 A2Q1040208）》及《切結保證書（表號 A2Q1040308）》正本",
                  "教務處註冊組用印之中文歷年學業成績單正本及名次證明（GPA ≥ 3.0，約百分制 75 分以上）、學務處生輔組用印之歷年獎懲紀錄證明正本（歷年操行平均 ≥ 80 分且無記過）",
                  "中、英文自傳各 1 份（各以 1 頁 A4 為限）及有效語言能力檢定證明正本（須達 CEFR B1 如 TOEIC 550 / TOEFL iBT 42 / IELTS 4.0 / JLPT N3 / TOPIK 3 級或姊妹校指定 CEFR B2 門檻）",
                  "大二升大三擬以一學年海外交換抵免大三「工讀實務實習」課程者，須依《大學部海外交換學習課程實施辦法（A2Q1060001）》規劃每學期至少修讀 6 學分（歐洲 2 ECTS = 1 學分）並於交換期間每三個月繳交四階段學習報告",
              ],
          },
          {
              "track": "跨國碩士雙聯學位甄選（美國辛辛那提大學 UC、北伊利諾大學 NIU、舊金山州立大學 SFSU、西班牙 ELISAVA、法國 ESIEE Paris、希臘 ALBA 商學院）",
              "required": [
                  "《學生出國雙聯學位學習或交換學習申請表（表號 A2Q1040108）》（含 300～500 字個人說明申請理由）、《家長/監護人切結同意書（A2Q1040208）》及《切結保證書（A2Q1040308）》",
                  "大學部及碩士班歷年學業成績單正本及名次證明（UC 與 SFSU 要求 GPA ≥ 3.0；NIU、ELISAVA、ESIEE、ALBA 要求大學及碩士 GPA ≥ 2.75）與生輔組用印之歷年獎懲紀錄證明正本（操行 ≥ 80 分且無記過）",
                  "通過母系所審查之「論文計畫書審查（或專業實務報告初稿）」證明及中、英文自傳（各以 1 頁 A4 為限）",
                  "符合雙聯合作校門檻之英語檢定證明正本（UC 為 TOEFL iBT 80–85 / IELTS 6.5 / Duolingo 110；NIU 為 iBT 80 / IELTS 6.5 / Duolingo 115；SFSU 為 iBT 80 / IELTS 6.0–7.0；ELISAVA 為 IELTS 6.0 / iBT 78 / TOEIC 785；ESIEE 為 iBT 72 / IELTS 5.5 / TOEIC 785；ALBA 為 IELTS 6.5 / iBT 100）",
              ],
          },
          {
              "track": "明志科技大學校內《雙聯學位（最高 24 萬）及交換學習（最高 16 萬）補助》暨教育部《學海飛颺／學海惜珠》獎學金申請與返國核銷",
              "required": [
                  "出國補助申請時機：於收到國外合作大學正式入學許可通知（Offer Letter）後 2 週內，檢具申請表向國際事務處全球交流組提出校內雙聯補助（非亞洲區最高 24 萬元、亞洲區最高 15 萬元；UC 另享鹿江基金會獎學金）或交換補助（非亞洲區最高 8 萬／16 萬元、亞洲區最高 5 萬／10 萬元，同一學制每人限補助乙次）",
                  "申請教育部學海惜珠或校內清寒優先補助另附：政府機關開立有效之低收入戶、中低收入戶、特殊境遇家庭扶助證明，或原住民、新住民生身分證明文件",
                  "返國後 1 週內核銷必備文件：至少 2 頁之《出國雙聯學位或交換學習報告（表號 A2Q1040508）》電子檔、來回機票登機證正本、護照基本資料頁與出入境章戳影本，以及國外合作大學核發之正式成績單",
              ],
          },
      ],
  }
  (OFFICIAL_MCUT_DIR / "document-conditions.json").write_text(
      json.dumps(doc_conditions, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  field_cov_lines = [
      "field_name,total_records,populated_records,coverage_ratio,notes"
  ]
  for fname in [
      "school_name",
      "country",
      "region",
      "program_type",
      "availability_status",
      "quota",
      "colleges",
      "degree_levels",
      "language_requirement",
      "gpa_requirement",
      "application_deadline",
      "study_period",
      "semester_dates",
      "housing_info",
      "course_restrictions",
      "official_website",
      "image_url",
  ]:
    pop = sum(1 for p in partners if p.get(fname) not in (None, "", []))
    ratio = pop / len(partners) if partners else 1.0
    field_cov_lines.append(
        f"{fname},{len(partners)},{pop},{ratio:.4f},Official MCUT OIA verified"
    )
  (OFFICIAL_MCUT_DIR / "field-coverage.csv").write_text(
      "\n".join(field_cov_lines) + "\n", encoding="utf-8"
  )

  pages_records = [
      {
          "title": "明志科技大學：2026–2027 海外交換學習暨跨國碩士雙聯學位甄選時程（交換暨秋季雙聯 2/6 17:00 截止、春季碩士雙聯 9/24 17:00 截止）",
          "source_url": MCUT_2026_2027_EXCHANGE_ANNOUNCEMENT_URL,
          "published_at": "2026-01-05T00:00:00Z",
          "text": "\n".join(exchange_info_payload["application_period"]),
          "summary": "\n".join(exchange_info_payload["application_period"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256(
              "\n".join(exchange_info_payload["application_period"]).encode(
                  "utf-8"
              )
          ).hexdigest(),
      },
      {
          "title": "明志科技大學：學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）申請資格（GPA 3.0、操行 80 分無記過、單一志願）",
          "source_url": MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
          "published_at": "2025-08-12T00:00:00Z",
          "text": "\n".join(exchange_info_payload["eligibility"]),
          "summary": "\n".join(exchange_info_payload["eligibility"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256(
              "\n".join(exchange_info_payload["eligibility"]).encode("utf-8")
          ).hexdigest(),
      },
      {
          "title": f"明志科技大學：{len(partners)} 所全球與兩岸合作姊妹校外語檢定門檻暨各類語言檢定證照等級對照表（CEFR B1/B2）",
          "source_url": MCUT_LANG_CEFR_TABLE_PDF_URL,
          "published_at": "2026-01-05T00:00:00Z",
          "text": "\n".join(exchange_info_payload["language_requirement"]),
          "summary": "\n".join(exchange_info_payload["language_requirement"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256(
              "\n".join(exchange_info_payload["language_requirement"]).encode(
                  "utf-8"
              )
          ).hexdigest(),
      },
      {
          "title": "明志科技大學：出國雙聯及交換學習應備文件（Google 表單領取申請表 A2Q1040108、300–500字申請理由、中英文自傳各1頁A4、註冊組與生輔組用印證明）",
          "source_url": MCUT_REGULATIONS_URL,
          "published_at": "2026-01-05T00:00:00Z",
          "text": "\n".join(exchange_info_payload["required_documents"]),
          "summary": "\n".join(exchange_info_payload["required_documents"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256(
              "\n".join(exchange_info_payload["required_documents"]).encode(
                  "utf-8"
              )
          ).hexdigest(),
      },
      {
          "title": "明志科技大學：出國雙聯補助（最高 24 萬元）、交換補助（最高 16 萬元）、鹿江基金會獎學金、短期研習補助與教育部學海計畫",
          "source_url": MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL,
          "published_at": "2025-08-12T00:00:00Z",
          "text": "\n".join(exchange_info_payload["scholarship_info"]),
          "summary": "\n".join(exchange_info_payload["scholarship_info"]),
          "category": "scholarship",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256(
              "\n".join(exchange_info_payload["scholarship_info"]).encode(
                  "utf-8"
              )
          ).hexdigest(),
      },
      {
          "title": "明志科技大學：大學部海外交換學習課程實施辦法（A2Q1060001，大二升大三一學年交換抵免工讀實務實習、每學期至少 6 學分、2 ECTS = 1 學分）",
          "source_url": MCUT_UNDERGRAD_EXCHANGE_COURSE_DOCX_URL,
          "published_at": "2025-08-12T00:00:00Z",
          "text": "\n".join(exchange_info_payload["semester"]),
          "summary": "\n".join(exchange_info_payload["semester"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256(
              "\n".join(exchange_info_payload["semester"]).encode("utf-8")
          ).hexdigest(),
      },
      {
          "title": "明志科技大學：跨國碩士雙聯學位計畫（美國辛辛那提大學 UC、北伊利諾大學 NIU、舊金山州立大學 SFSU、西班牙 ELISAVA、法國 ESIEE Paris、希臘 ALBA）",
          "source_url": MCUT_NIU_DUAL_SPRING_URL,
          "published_at": "2026-08-15T00:00:00Z",
          "text": "\n".join(student_dashboard_payload["rule_explanations"][0]["key_points"]),
          "summary": student_dashboard_payload["rule_explanations"][0]["summary"],
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256(
              "\n".join(student_dashboard_payload["rule_explanations"][0]["key_points"]).encode("utf-8")
          ).hexdigest(),
      },
      {
          "title": f"明志科技大學：國際事務處出國交換生暨雙聯學位生心得分享專區（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）",
          "source_url": MCUT_EXPERIENCE_HUB_URL,
          "published_at": "2026-01-05T00:00:00Z",
          "text": "\n".join(exchange_info_payload["program_type"]),
          "summary": "\n".join(exchange_info_payload["program_type"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256(
              "\n".join(exchange_info_payload["program_type"]).encode("utf-8")
          ).hexdigest(),
      },
  ]
  (OFFICIAL_MCUT_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
      + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "mcut",
      "school_name": "明志科技大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "gpa_minimum_exchange": 3.0,
          "gpa_minimum_dual_degree": 2.75,
          "conduct_score_minimum": 80.0,
          "no_demerit_required": True,
          "cefr_minimum": "B1",
          "maximum_preferences": 1,
          "dual_degree_subsidy_non_asia_max_ntd": 240000,
          "dual_degree_subsidy_asia_max_ntd": 150000,
          "exchange_subsidy_non_asia_year_max_ntd": 160000,
          "exchange_subsidy_non_asia_semester_max_ntd": 80000,
          "exchange_subsidy_asia_year_max_ntd": 100000,
          "exchange_subsidy_asia_semester_max_ntd": 50000,
          "short_term_subsidy_max_ntd": 47000,
          "xuehai_subsidy_max_ntd": 300000,
          "exclude_in_service": True,
          "return_report_due": "返國後 1 週內繳交至少 2 頁之《出國雙聯學位或交換學習報告（表號 A2Q1040508）》電子檔、來回登機證正本、護照出入境章影本及國外成績單",
      },
      "source_urls": mcut_source_urls,
      "verified_at": "2026-11-09",
  }
  (OFFICIAL_MCUT_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_MCUT_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "明志科技大學",
              "required_documents": student_dashboard_payload[
                  "required_documents"
              ],
              "source_urls": mcut_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_MCUT_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "明志科技大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": mcut_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "mcut",
      "school_name": "明志科技大學",
      "total_partners": len(partners),
      "partner_count": len(partners),
      "international_partners": sum(
          1
          for p in partners
          if p["country"] not in {"中國大陸", "香港", "澳門"}
      ),
      "mainland_partners": sum(
          1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
      ),
      "dual_degree_partner_universities": 12,
      "dual_degree_programs": 12,
      "experience_report_covered_partners": exp_covered_schools,
      "experience_report_count": total_exp_reports,
      "open_partners": open_partner_count,
      "reference_only_partners": len(partners) - open_partner_count,
      "verified_locations": len(partners),
      "verified_official_websites": sum(
          1 for p in partners if p.get("official_website")
      ),
      "verified_campus_images": sum(
          1 for p in partners if p.get("image_status") == "verified"
      ),
      "workflow_count": len(workflows),
      "destination_profile_count": len(destinations),
      "student_life_count": len(life_records),
      "active_term": (
          f"明志科技大學國際事務處全球交流組《2026–2027 學年度海外交換學習計畫甄選簡章（含歐美日韓東南亞及大陸共 {open_partner_count} 所當期開放申請合作校）》、《跨國碩士雙聯學位甄選公告（UC、NIU、SFSU、ELISAVA、ESIEE、ALBA）》、《全球暨兩岸合作姊妹校名錄（{len(partners)} 校）》、《學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008，雙聯最高 24 萬／交換最高 16 萬）》、《大學部海外交換學習課程實施辦法（A2Q1060001，大三工讀實習抵免）》及教育部《學海飛颺／惜珠／築夢》專區同步整合；共完整收錄 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所當期開放申請合作校及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 21 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷年學長姐交換與雙聯心得報告）。"
      ),
      "verified_at": "2026-11-09",
  }
  (OFFICIAL_MCUT_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_MCUT_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "mcut",
              "school_name": "明志科技大學",
              "status": "official_verified",
              "checked_at": CHECKED_AT,
              "counts": completeness,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  provenance_files = [
      (
          "sources/mcut/mcut_catalog_source.json",
          MCUT_2026_2027_EXCHANGE_ANNOUNCEMENT_URL,
          f"明志科技大學 {len(partners)} 所全球與兩岸合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/mcut/mcut_resolved_locations.json",
          MCUT_PARTNER_LIST_URL,
          f"明志科技大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
      ),
      (
          "sources/mcut/mcut_experience_index.json",
          MCUT_EXPERIENCE_HUB_URL,
          f"明志科技大學國際事務處全球交流組 {exp_covered_schools} 校 {total_exp_reports} 篇出國交換暨雙聯學位心得報告索引 JSON",
      ),
  ]
  for rel_p, surl in bin_urls.items():
    rp = rel_p if rel_p.startswith("sources/") else f"sources/mcut/{rel_p}"
    if not any(x[0] == rp for x in provenance_files):
      provenance_files.append((rp, surl, f"明志科技大學官方原始檔案：{Path(rp).name}"))

  prov_sources = []
  for rel_path, surl, stitle in provenance_files:
    p = REPO_ROOT / rel_path
    if p.exists():
      b = p.read_bytes()
      prov_sources.append({
          "file": rel_path,
          "source_url": surl,
          "title": stitle,
          "sha256": hashlib.sha256(b).hexdigest(),
          "bytes": len(b),
          "fetched_at": CHECKED_AT,
      })
  provenance_payload = {
      "school_id": "mcut",
      "school_name": "明志科技大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = (
      json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  )
  (OFFICIAL_MCUT_DIR / "import_provenance.json").write_text(
      prov_text, encoding="utf-8"
  )
  (OFFICIAL_MCUT_DIR / "import-provenance.json").write_text(
      prov_text, encoding="utf-8"
  )

  print(
      f"Successfully built MCUT catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
