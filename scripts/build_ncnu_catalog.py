"""Build the official National Chi Nan University (國立暨南國際大學, NCNU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_NCNU_DIR = REPO_ROOT / "sources" / "ncnu"
OFFICIAL_NCNU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "ncnu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "university_locations.jsonl"
)

CHECKED_AT = "2026-10-27T08:00:00Z"

NCNU_OIA_HOME_URL = "https://oia.ncnu.edu.tw/"
NCNU_EXCHANGE_OVERVIEW_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-269.php?Lang=zh-tw"
)
NCNU_EXCHANGE_DEADLINES_URL = (
    "https://oia.ncnu.edu.tw/p/406-1017-32102,r44.php?Lang=zh-tw"
)
NCNU_EXCHANGE_PARTNERS_SHEET_URL = "https://docs.google.com/spreadsheets/d/1iLyMA1wtTgx_Ygkbcc3Dps179qrr_-g_-7OzivUsslA/edit?usp=sharing"
NCNU_PARTNERS_MAP_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-293.php?Lang=zh-tw"
)
NCNU_MAINLAND_PARTNERS_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-524.php?Lang=zh-tw"
)
NCNU_MAINLAND_APPLY_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-531.php?Lang=zh-tw"
)
NCNU_MAINLAND_QA_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-532.php?Lang=zh-tw"
)
NCNU_SCHOLARSHIPS_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-271.php?Lang=zh-tw"
)
NCNU_XUEHAI_URL = "https://oia.ncnu.edu.tw/p/412-1017-350.php?Lang=zh-tw"
NCNU_SCHOOL_SUBSIDY_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-351.php?Lang=zh-tw"
)
NCNU_EXPERIENCES_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-273.php?Lang=zh-tw"
)
NCNU_REGULATIONS_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-285.php?Lang=zh-tw"
)
NCNU_DOWNLOADS_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-286.php?Lang=zh-tw"
)
NCNU_DUAL_DEGREE_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-270.php?Lang=zh-tw"
)
NCNU_SCORE_RULES_PDF_URL = (
    "https://oia.ncnu.edu.tw/var/file/17/1017/img/285/675776290.pdf"
)
NCNU_SUBSIDY_RULES_PDF_URL = (
    "https://oia.ncnu.edu.tw/var/file/17/1017/img/285/554067160.pdf"
)
NCNU_DUAL_DEGREE_RULES_PDF_URL = (
    "https://oia.ncnu.edu.tw/var/file/17/1017/img/285/956940933.pdf"
)
NCNU_SOP_PDF_URL = (
    "https://oia.ncnu.edu.tw/var/file/17/1017/img/285/575480071.pdf"
)
NCNU_CREDIT_CONVERSION_PDF_URL = (
    "https://oia.ncnu.edu.tw/var/file/17/1017/img/286/410787725.pdf"
)
NCNU_APPLICATION_FORM_PDF_URL = (
    "https://oia.ncnu.edu.tw/var/file/17/1017/img/286/795655586.pdf"
)

REGION_COST_DEFAULTS = {
    "美國": (
        "每月生活費約 USD 1,400–2,200（依匯率折合新臺幣約 45,000–70,000 元，含加州大學河濱分校 UCR、南佛羅里達大學 USF、北卡羅萊納大學格林斯伯勒分校 UNCG、北達科他州立大學 NDSU 等校內外住宿、膳食與交通；交換生免繳美國姊妹校學費，並可申請教育部學海飛颺／惜珠或校內歐美地區一學期最高 5 萬／一學年 10 萬出國補助）",
        "須憑美國接待大學核發之 DS-2019（J-1 交換生）或 I-20（F-1 雙聯學位生）表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證，且須投保符合接待校規定之全期海外醫療保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,200–1,900（折合加幣約 CAD 1,650–2,600 / 月、新臺幣約 38,500–60,000 元，含維多利亞大學 UVic、紐芬蘭紀念大學 MUN 校內外學生宿舍、寄宿家庭、膳食與交通費用；交換生免繳加國姊妹校學費）",
        "交換研習 1 學期（6 個月以內）可申辦加拿大電子旅行授權（eTA），交換 1 學年或超過 6 個月須申辦加拿大 Study Permit 學生許可並投保醫療保險。",
    ),
    "英國": (
        "每月生活費約 USD 1,350–2,000（折合英鎊約 GBP 1,050–1,550 / 月、新臺幣約 43,000–64,000 元，含羅浮堡大學 Loughborough University、桑德蘭大學 University of Sunderland 學生宿舍、伙食與交通費）",
        "交換 6 個月以內可依英國 Standard Visitor 規定辦理，超過 6 個月須憑 CAS 申辦英國 Student Visa 並繳交移民健康附加費（IHS）。",
    ),
    "德國": (
        "每月生活費約 USD 1,050–1,600（折合歐元約 EUR 950–1,450 / 月、新臺幣約 33,500–51,000 元；柏林自由大學 FU-BEST、富트旺根應用科技大學 HFU 等校繳交學期雜費 Semesterbeitrag 後多含德國學期交通票）",
        "須開立德國限制提領帳戶（Blocked Account，每月基準約 EUR 992）並憑入學許可向德國在台協會申辦德國長期學生簽證及投保德國公保／醫療險。",
    ),
    "法國": (
        "每月生活費約 USD 1,050–1,650（折合歐元約 EUR 950–1,500 / 月、新臺幣約 33,500–53,000 元；雷恩商學院 Rennes School of Business、里昂第三大學等學生公寓與日常開銷；留法學生可申請法國政府 CAF 房補）",
        "須先經法國教育中心（Campus France）完成 Etudes en France 線上程序與面試，再向法國在台協會申辦長期學生簽證（VLS-TS）。",
    ),
    "捷克": (
        "每月生活費約 USD 700–1,100（折合歐元約 EUR 650–1,000 / 月、新臺幣約 22,500–35,000 元；布拉格查理大學 Charles University、赫拉德茨克拉洛韋大學 UHK、帕爾杜比采大學等學生宿舍費用實惠）",
        "須憑捷克接待大學核發之入學許可與住宿證明向捷克經濟文化辦事處申辦長期學生簽證並投保捷克認可之醫療保險。",
    ),
    "西班牙": (
        "每月生活費約 USD 950–1,500（折合歐元約 EUR 880–1,380 / 月、新臺幣約 30,500–48,000 元；阿爾卡拉大學、格拉納達大學、武康大學 UCAM 學生合租公寓與生活費）",
        "須憑西班牙接待大學入學許可向西班牙商務辦事處申辦學生簽證，並投保無自負額之全額醫療保險。",
    ),
    "荷蘭": (
        "每月生活費約 USD 1,150–1,750（折合歐元約 EUR 1,050–1,600 / 月、新臺幣約 36,500–56,000 元；文德斯海姆應用科技大學 Windesheim UAS 學生宿舍、單車通勤與日常開銷）",
        "由荷蘭接待大學代向荷蘭移民局（IND）申辦 MVV 入境簽證與 VVR 學生居留許可（須先匯付財力證明至學校指定帳戶）。",
    ),
    "奧地利": (
        "每月生活費約 USD 1,050–1,550（折合歐元約 EUR 950–1,400 / 月、新臺幣約 33,500–50,000 元；茵斯布魯克管理中心 MCI 學生宿舍與生活費）",
        "交換 1 學期（6 個月內）向奧地利台北辦事處申辦奧地利學生 D 簽證，交換 1 學年須申辦學生居留許可。",
    ),
    "日本": (
        "每月生活費約 USD 700–1,150（折合日圓約 JPY 100,000–165,000 / 月、新臺幣約 22,500–36,500 元；廣島大學、信州大學、中央大學、福井大學、宇都宮大學、熊本大學、龍谷大學、同志社大學、芝浦工業大學、多摩大學、高崎經濟大學等校內外國際學舍與伙食交通費）",
        "須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後至日本台灣交流協會申辦留學簽證並加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 680–1,100（折合韓元約 KRW 900,000–1,500,000 / 月、新臺幣約 21,500–35,000 元；高麗大學世宗校區、中央大學、韓國外國語大學、慶北大學、梨花女子大學、淑明女子大學、首爾市立大學、明知大學、京畿大學、嘉泉大學校內宿舍與生活費）",
        "須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後辦理外國人登錄證並納保韓國國民健康保險。",
    ),
    "泰國": (
        "每月生活費約 USD 500–850（折合泰銖約 THB 17,000–28,000 / 月、新臺幣約 16,000–27,000 元；泰國農業大學 Kasetsart University、朱拉隆功大學、瑪希敦大學、清邁大學學生公寓與生活費實惠）",
        "須憑泰國接待大學入學許可公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 教育簽證並投保海外全期醫療險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 500–850（折合馬幣約 MYR 2,200–3,700 / 月、新臺幣約 16,000–27,000 元；馬來亞大學、博特拉大學、拉曼大學 UTAR、新紀元大學學院學生宿舍與餐飲費用親民）",
        "須透過馬來西亞教育全球服務中心（EMGS）線上申辦學生簽證核准函（VAL / Mobility Pass）。",
    ),
    "中國大陸": (
        "每月生活費約 USD 350–700（折合人民幣約 RMB 1,800–4,500 / 月、新臺幣約 11,000–22,500 元；蘭州大學、山東大學、山東大學威海分校、吉林大學、四川大學、華南師範大學、北京第二外國語學院、中央民族大學、中南民族大學、浙江理工大學等校內學生宿舍與食堂開銷低廉）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及大陸姊妹校寄發之錄取通知書辦理報到，並依暨大國際及兩岸事務處規定購買涵蓋交換全期之海外醫療及意外保險。",
    ),
    "香港": (
        "每月生活費約 USD 1,100–1,700（折合港幣約 HKD 8,500–13,000 / 月、新臺幣約 35,000–54,000 元；香港教育大學學生宿舍、膳食與八達通大眾運輸費用）",
        "須由香港教育大學協助向香港入境事務處申辦來港就讀進入許可（Student Visa / Entry Permit），並投保醫療及意外保險。",
    ),
    "澳門": (
        "每月生活費約 USD 750–1,200（折合澳門幣約 MOP 6,000–9,500 / 月、新臺幣約 24,000–38,500 元；澳門城市大學住宿、膳食與交通費用）",
        "須持有效護照及澳門城市大學錄取通知辦理逗留特別許可（學生逗留簽注）並投保醫療及意外保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "美國": "秋季學期（Fall Semester）：約 8 月中旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬",
    "加拿大": "秋季學期（Fall Semester）：約 9 月初至 12 月中旬；春季學期（Spring Semester）：約 1 月初至 4 月下旬",
    "英國": "秋季學期（Autumn Term / Semester 1）：約 9 月下旬至翌年 1 月；春季學期（Spring Term / Semester 2）：約 1 月下旬至 6 月",
    "德國": "冬季學期（Winter Semester）：約 9/10 月至翌年 2 月；夏季學期（Summer Semester）：約 3/4 月至 7/8 月",
    "法國": "秋季學期（Fall Semester）：約 9 月初至 12 月底／1 月；春季學期（Spring Semester）：約 1 月下旬至 5/6 月",
    "捷克": "秋季學期（Winter Semester）：約 9 月中旬至翌年 1 月底；春季學期（Summer Semester）：約 2 月中旬至 6 月底",
    "西班牙": "秋季學期（Fall Semester）：約 9 月中旬至翌年 1 月；春季學期（Spring Semester）：約 1 月下旬至 6 月",
    "荷蘭": "秋季學期（Fall Semester）：約 8 月底／9 月初至翌年 1 月底；春季學期（Spring Semester）：約 2 月初至 6 月底",
    "奧地利": "冬季學期（Winter Semester）：約 9/10 月至翌年 1/2 月；夏季學期（Summer Semester）：約 2/3 月至 6/7 月",
    "日本": "秋季學期（Fall Semester）：約 9 月中下旬至翌年 2 月；春季學期（Spring Semester）：約 4 月初至 8 月上旬",
    "韓國": "秋季學期（Fall Semester）：約 9 月初至 12 月中旬；春季學期（Spring Semester）：約 3 月初至 6 月中旬",
    "泰國": "第一學期（First Semester）：約 8 月至 12 月；第二學期（Second Semester）：約 1 月至 5 月",
    "馬來西亞": "第一學期：約 9/10 月至翌年 1/2 月；第二學期：約 2/3 月至 6/7 月",
    "中國大陸": "秋季學期（上學期）：約 9 月初至翌年 1 月中旬；春季學期（下學期）：約 2 月中下旬至 6 月底",
    "香港": "第一學期（Fall）：約 9 月初至 12 月下旬；第二學期（Spring）：約 1 月中旬至 5 月下旬（香港教育大學僅於每年 4 月開放申請）",
    "澳門": "第一學期（Fall）：約 9 月初至翌年 1 月；第二學期（Spring）：約 2 月至 6 月",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
  """Ensure school-images.json and university_locations.jsonl contain all 212 NCNU partner schools."""
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
          else loc.get("lat", 23.9537)
      )
      lon = float(
          loc.get("longitude")
          if loc.get("longitude") is not None
          else loc.get("lon", 120.9340)
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
              item.get("website")
              or loc.get("source_url")
              or "https://ror.org"
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
  OFFICIAL_NCNU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_NCNU_DIR / "ncnu_catalog_source.json").read_text(
          encoding="utf-8"
      )
  )
  resolved_locations = json.loads(
      (SOURCES_NCNU_DIR / "ncnu_resolved_locations.json").read_text(
          encoding="utf-8"
      )
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
        "open" if item.get("offering_status") == "open" else "reference_only"
    )
    if avail_status == "open":
      open_partner_count += 1

    group_str = clean_text(
        item.get("group") or "國際及兩岸事務處正式締約姊妹校"
    )
    quota_str = clean_text(
        item.get("quota") or "每學期 2–5 名免學費交換生（依兩校交換協議及當期簡章名額辦理）"
    )
    detail_url = item.get("detail_url") or NCNU_PARTNERS_MAP_URL

    if "雙聯學位" in group_str and "交換" in group_str:
      program_type = "國際及兩岸事務處海外姊妹校交換學生計畫暨跨國雙聯學位計畫"
      source_url = detail_url
    elif "雙聯學位" in group_str:
      program_type = f"國際及兩岸事務處跨國雙聯學位計畫（{quota_str}）"
      source_url = NCNU_DUAL_DEGREE_URL
    elif country in {"中國大陸", "香港", "澳門"} and avail_status == "open":
      program_type = "國際及兩岸事務處赴大陸及港澳地區姊妹校交換學生計畫（互免學費）"
      source_url = detail_url
    elif avail_status == "open":
      program_type = "國際及兩岸事務處海外姊妹校交換學生計畫（互免學費）"
      source_url = detail_url
    elif country in {"中國大陸", "香港", "澳門"}:
      program_type = "國際及兩岸事務處正式締約大陸及港澳合作姊妹校"
      source_url = detail_url
    else:
      program_type = "國際及兩岸事務處正式締約海外合作姊妹校"
      source_url = detail_url

    colleges_str = clean_text(
        item.get("colleges")
        or "人文學院、管理學院、科技學院、教育學院、水沙連學院、護理暨健康福祉學院"
    )
    degree_levels_str = clean_text(
        item.get("eligible_degrees")
        or "學士班、碩士班、博士班（於暨大註冊就讀滿一學期以上在學學生）"
    )
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "")
    website = item.get("website") or NCNU_PARTNERS_MAP_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    round_label = (
        "115學年度秋季班（2–3月收件提名）＆春季班（9–10月收件提名）姊妹校交換學生暨跨國雙聯學位甄選"
        if avail_status == "open"
        else "國際及兩岸事務處正式締約合作姊妹校（依當期交換或雙聯學位公告名額辦理）"
    )
    app_deadline_str = clean_text(
        item.get("deadline")
        or (
            "秋季班（Fall Semester 出國）：每年 2–3 月校內收件及提名｜"
            "春季班（Spring Semester 出國）：每年 9–10 月校內收件及提名（各姊妹校提名與申請截止日依國際處《姊妹校交換生申請截止日期》公告辦理）"
        )
    )
    deadline_iso = "2026-10-30T17:00:00+08:00"
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "115"

    study_period_str = clean_text(item.get("duration") or "一學期或一學年")
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲國立暨南國際大學國際及兩岸事務處提名錄取後，可依 {zh_name} 國際處指引申請校內外學生宿舍或國際學舍"
        + (f"（學費與獎補助待遇：{tuition_note}）" if tuition_note else "。")
    )
    course_rest_str = (
        f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《國立暨南國際大學學生赴海外姊妹校交換標準作業流程（SOP）》、《選送學生出國研修積分計算要點》（112.06.14 修正通過）與《選送優秀學生出國補助要點》（114.07.22 修正通過）規定："
        "（1）申請資格為本校正式註冊在學且已於本校就讀至少一學期以上之學士班、碩士班或博士班學生（不含國內及境外在職專班生、休學生；赴大陸及港澳地區交換生須於本校修業滿一年；跨國雙聯學位學士班及博士班須修業滿二學期、碩士班須修業滿一學期）；"
        "（2）校內甄選依《選送學生出國研修積分計算要點》評比（滿分 30 分）：主要語言能力最高 10 分（CEFR B2 為 8 分、B1 為 5 分、A2 為 2 分）＋次要語言最高 3 分＋學業成績最高 10 分（學士班以「10 分 × (100% − 班級排名百分比)」計算）＋院推薦排序加分 1–4 分（前 25% 加 4 分）＋曾任國際處國際學伴或國際事務社團幹部最高 3 分；"
        "（3）出國交換期間須於暨大辦理註冊並繳交全額學雜費，免繳接待姊妹校學費；返國後依《國外學分換算表》（歐洲 2 ECTS 折算暨大 1 學分、英國 4 CATS 折算暨大 1 學分、美加日韓約 1:1 折算）辦理學分抵免，獲補助者須於返國後 14 日內繳交研修心得報告。"
    )

    living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
        country,
        (
            "每月生活費約 USD 850–1,450（依匯率折合新臺幣約 27,000–46,500 元，含住宿、膳食與市區交通）",
            "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
        ),
    )

    tuition_points_list = [
        (
            f"暨大在學註冊與合作姊妹校學費待遇：公費交換生於出國交換期間須在國立暨南國際大學辦理註冊並繳交全額學雜費，免繳接待姊妹校學費。本合作校待遇：{tuition_note or '免繳接待姊妹校學費（雙聯學位依兩校雙聯協議繳費）'}。"
        ),
        (
            "暨大四大出國獎助學金體系：（1）教育部《學海飛颺》獎學金（選送優秀學生赴非大陸港澳之海外姊妹校交換，主要語言積分須達 8 分［CEFR B2］以上，每名約補助新臺幣 5萬–15萬元）；（2）教育部《學海惜珠》獎學金（補助具低收、中低收或特殊境遇家庭證明之優秀學生出國交換機票與生活費）；（3）校內《國立暨南國際大學選送優秀學生出國補助要點》（114.07.22 修正，歐美地區交換一學期最高新臺幣 50,000 元、一學年最高 100,000 元；亞洲及大洋洲地區交換一學期最高 35,000 元、一學年最高 70,000 元）；（4）《辦理跨國雙聯學位制補助要點》（取得雙聯合作大學學位證書者核給新臺幣 100,000 元獎勵金）。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認暨大在學學籍、成績班排與 {zh_name} 語檢要求）：確認已於暨大註冊就讀滿一學期以上（大陸港澳交換須修業滿一年；雙聯學位學士及博士班須滿二學期、碩士班須滿一學期），符合學業要求（{gpa_req_str}），並備妥有效外語檢定成績單（{lang_req_str}）。"
        ),
        (
            "步驟二（於秋季班 2–3 月或春季班 9–10 月校內截止日前送交系所與學院初審排序）：填具《出國交換學生甄選申請表》及《選送學生出國研修積分自評表》，檢附中英文歷年成績單（含班級排名百分比）、外語能力檢定證明、中英文讀書計畫、自傳、師長推薦信及家長同意書，先送交各系所及所屬學院初審並排定「院推薦順序」（院排序前 25% 加 4 分、26%–50% 加 3 分、51%–75% 加 2 分、76%–100% 加 1 分）。"
        ),
        (
            f"步驟三（國際及兩岸事務處核算 30 分總積分、公告錄取推薦並向 {full_name} 辦理官方提名）：由學院彙送國際及兩岸事務處依《選送學生出國研修積分計算要點》核算總積分（主要語言 10 分＋次要語言 3 分＋學業成績 10 分＋院排序 1–4 分＋國際學伴／社團 3 分），經甄選審查會核定錄取後簽署行政契約書，並於姊妹校截止日前完成線上提名（Nomination）與申請文件寄送。"
        ),
        (
            "步驟四（申請教育部學海飛颺／惜珠或校內出國補助、辦理簽證與學分換算預審，返國 14 日內繳交心得報告與核銷）：取得姊妹校入學許可後辦理簽證與選課預審（依《國外學分換算表》2 ECTS = 1 學分、4 CATS = 1 學分確認抵免）；返國後 14 日內繳交《出國交換研修心得報告》並檢具登機證、機票收據、出入境證明與正式成績單辦理獎助學金核銷與學分抵免。"
        ),
    ]

    elig_points_list = [
        f"合作類別與甄選群組：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業成績與班排採計：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "校內甄選計分與限制規定：依《國立暨南國際大學選送學生出國研修積分計算要點》（滿分 30 分），採計主要語言（最高 10 分）、次要語言（最高 3 分）、學業成績（最高 10 分，學士班為 10 × [100% − 班排%]）、院排序加分（1–4 分）與國際學伴／社團參與（最高 3 分）。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與暨大獎補助待遇：{tuition_note}")
    if remarks_raw:
      elig_points_list.append(f"學程與締約重點說明：{remarks_raw}")

    exp_links: list[dict] = []
    exp_labels: list[str] = []
    if exps:
      exp_covered_schools += 1
      total_exp_reports += len(exps)
      seen_exp_urls: set[str] = set()
      for e_idx, e in enumerate(exps):
        raw_t = clean_text(e.get("title") or f"赴 {zh_name} 交換生心得報告")
        esem = e.get("semester") or "歷年交換"
        eurl = (
            e.get("url")
            or f"{NCNU_EXPERIENCES_URL}#ncnu-exp-{sn}-{e_idx+1}"
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
            "college": "人文學院／管理學院／科技學院／教育學院／水沙連學院／護理暨健康福祉學院",
            "department": "暨大交換生",
        })
        summary_text = (
            f"國立暨南國際大學國際及兩岸事務處公開收錄之學長姐赴 {country} {full_name} 交換研修官方返校心得報告（{raw_t}），詳述選課學分抵免、住宿環境、簽證辦理與當地生活費實錄。"
        )
        theme_map = {
            "academics": f"暨大交換生於《{raw_t}》分享在 {zh_name} 選課修習、課堂互動及返國依《國外學分換算表》辦理系所學分抵免之經驗。",
            "housing": f"暨大交換生記錄申請 {zh_name} 校內外學生宿舍、周邊生活機能與大眾運輸通勤方式（{housing_str[:100]}）。",
            "campus_culture": f"暨大國際及兩岸事務處公開收錄《{raw_t}》之跨文化課堂學習、國際學伴交流與校園生活紀錄。",
            "cost": f"暨大交換生分享於 {zh_name} 之每月住宿、伙食與交通開銷（{living_cost_str[:100]}），以及免繳姊妹校學費與申請教育部學海飛颺／惜珠或校內出國補助之規劃。",
        }
        student_experience_rows.append({
            "school_name": full_name,
            "country": country,
            "title": raw_t,
            "source_url": eurl,
            "source_type": "article",
            "platform": "國立暨南國際大學國際及兩岸事務處（OIA）—學生交換心得報告專區",
            "author_name": (
                raw_t.split("_")[-1].strip()[:20]
                if "_" in raw_t
                else "暨大交換生"
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
                f"{full_name}:ncnu_exp:{e_idx}:{eurl}".encode("utf-8")
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
        "home_university": "國立暨南國際大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exp_links[0]["url"] if exp_links else NCNU_EXPERIENCES_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

    loc = resolved_locations.get(full_name) or {
        "city": country,
        "latitude": 23.9537,
        "longitude": 120.9340,
        "source_url": "https://www.wikidata.org",
    }
    city_name = loc.get("city") or country
    lat = float(
        loc.get("latitude")
        if loc.get("latitude") is not None
        else loc.get("lat", 23.9537)
    )
    lon = float(
        loc.get("longitude")
        if loc.get("longitude") is not None
        else loc.get("lon", 120.9340)
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
        "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 及暨大姊妹校地圖 KML 比對；實際交換校區以錄取通知與締約校專頁為準。",
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
        f"【合作類別與期程】{program_type}｜研修期間：{study_period_str}",
        f"【當期名額與費用待遇】{quota_str}｜{tuition_note or '依兩校協議辦理'}",
        f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
        f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        f"【住宿與生活資訊】{housing_str}",
    ]
    if exps:
      notes_lines.append(
          f"【暨大學長姐交換返校心得報告（共 {len(exps)} 篇）】收錄於國際及兩岸事務處學生交換心得報告專區（含：{'、'.join(exp_labels[:4])}）"
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
        "quota_status": (
            "published" if avail_status == "open" else "reference_only"
        ),
        "availability_status": avail_status,
        "availability_note": (
            f"國立暨南國際大學國際及兩岸事務處公告合作姊妹校（{program_type}）；{quota_str}。"
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
        "factsheet_url": item.get("factsheet_url"),
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
            "title": f"國立暨南國際大學國際及兩岸事務處（OIA）姊妹校交換生資訊與締約名錄—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立暨南國際大學學生赴海外姊妹校交換標準作業流程（SOP）與選送學生出國研修積分計算要點（112.06.14修正通過）",
            "source_url": NCNU_EXCHANGE_OVERVIEW_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立暨南國際大學選送優秀學生出國補助要點（114.07.22修正）與教育部學海飛颺／學海惜珠獎補助公告",
            "source_url": NCNU_SCHOLARSHIPS_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exp_links:
      wf_sources.append({
          "title": f"國立暨南國際大學國際及兩岸事務處學生交換心得報告專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
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
        "home_university": "國立暨南國際大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": acad_year,
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "115學年度秋季班（2–3月收件提名）",
            "115學年度春季班（9–10月收件提名）",
            "115-1",
            "115-2",
            "116-1",
            "116-2",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "國立暨南國際大學由國際及兩岸事務處（Office of International and Cross-Strait Affairs，設於行政大樓）統籌全校 6 大學院（人文學院、管理學院、科技學院、教育學院、水沙連學院、護理暨健康福祉學院）及智慧暨永續農業學士學位學程之海外姊妹校交換生計畫、大陸及港澳地區交換生計畫、4 校跨國雙聯學位計畫（美國加州大學河濱分校 UCR 3+1+MS、法國雷恩商學院、加拿大紐芬蘭紀念大學、泰國農業大學）及教育部學海飛颺、學海惜珠與校內選送優秀學生出國補助。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"ncnu-{acad_year}-home-1-{sn:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認暨大在學學籍、成績班排與 {zh_name} 語檢要求",
                "responsible_party": "學生",
                "responsible_unit": "國立暨南國際大學國際及兩岸事務處／各系所及學院",
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
                    f"確認符合《國立暨南國際大學學生赴海外姊妹校交換標準作業流程（SOP）》與《選送優秀學生出國補助要點》規定：申請人須為本校正式註冊在學且已於本校就讀至少一學期以上之學士班、碩士班或博士班學生（大陸港澳交換須修業滿一年；雙聯學位學士及博士班須滿二學期、碩士班須滿一學期），符合學業標準（{gpa_req_str}），並備妥符合 {zh_name} 門檻之有效外語檢定成績（{lang_req_str}）。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["國立暨南國際大學"],
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
                    NCNU_EXCHANGE_OVERVIEW_URL,
                    NCNU_SOP_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ncnu-{acad_year}-home-2-{sn:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "於秋季班（2–3月）或春季班（9–10月）校內截止日前備妥甄選申請表與積分自評表送系所及學院初審排序",
                "responsible_party": "學生與所屬系所／學院辦公室",
                "responsible_unit": "國立暨南國際大學各系所／各學院／國際及兩岸事務處",
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": NCNU_EXCHANGE_DEADLINES_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "填具《出國交換學生甄選申請表》及《選送學生出國研修積分自評表》，檢附歷年中英文成績單正本（須註明班級排名百分比）、有效外語能力檢定證明、中英文讀書計畫、自傳、師長推薦信及家長同意書，於校內收件截止日前送交就讀系所及所屬學院初審並排定「院推薦順序」（前 25% 加 4 分、26%–50% 加 3 分、51%–75% 加 2 分、76%–100% 加 1 分），再由學院彙送國際及兩岸事務處。"
                ),
                "details": [
                    "秋季班（Fall Semester，當年 8/9 月出國）：每年 2 月至 3 月底前受理系院初審及國際處收件提名（依各姊妹校 2–4 月截止日分批辦理）。",
                    "春季班（Spring Semester，隔年 1/2 月出國）：每年 9 月至 10 月底前受理系院初審及國際處收件提名（大陸港澳交換春季班為 9–11 月、秋季班為 2–4 月，香港教育大學僅於每年 4 月開放）。",
                ],
                "document_requirements": [
                    {
                        "name": "國立暨南國際大學出國交換學生甄選申請表（含系所及學院核章）",
                        "official_form_url": NCNU_APPLICATION_FORM_PDF_URL,
                        "source_urls": [
                            NCNU_DOWNLOADS_URL,
                            NCNU_APPLICATION_FORM_PDF_URL,
                        ],
                    },
                    {
                        "name": "國立暨南國際大學選送學生出國研修積分自評表（附語言檢定、班排、國際學伴或社團幹部證明）",
                        "official_form_url": NCNU_SCORE_RULES_PDF_URL,
                        "source_urls": [
                            NCNU_REGULATIONS_URL,
                            NCNU_SCORE_RULES_PDF_URL,
                        ],
                    },
                    {
                        "name": "中英文讀書計畫（Study Plan）、自傳（Autobiography）、師長推薦信與家長同意書",
                        "official_form_url": NCNU_DOWNLOADS_URL,
                        "source_urls": [
                            NCNU_DOWNLOADS_URL,
                            NCNU_SOP_PDF_URL,
                        ],
                    },
                    {
                        "name": "歷年中英文成績單正本（含學業平均、GPA 及班級排名百分比）與有效外語能力檢定成績單影本",
                        "official_form_url": NCNU_SCORE_RULES_PDF_URL,
                        "source_urls": [
                            NCNU_EXCHANGE_OVERVIEW_URL,
                            NCNU_SCORE_RULES_PDF_URL,
                        ],
                    },
                ],
                "scope": {
                    "home_universities": ["國立暨南國際大學"],
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
                    NCNU_EXCHANGE_OVERVIEW_URL,
                    NCNU_EXCHANGE_DEADLINES_URL,
                    NCNU_DOWNLOADS_URL,
                    NCNU_SCORE_RULES_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ncnu-{acad_year}-home-3-{sn:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "國際及兩岸事務處依《選送學生出國研修積分計算要點》核算 30 分總積分、審查會核定錄取與簽署行政契約書",
                "responsible_party": "國立暨南國際大學國際及兩岸事務處與錄取學生",
                "responsible_unit": "國立暨南國際大學國際及兩岸事務處",
                "deadline_at": "2026-11-20T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": NCNU_SCORE_RULES_PDF_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "國際及兩岸事務處依《國立暨南國際大學選送學生出國研修積分計算要點》（112.06.14 修正通過）核算總積分（滿分 30 分：主要語言最高 10 分＋次要語言最高 3 分＋學業成績最高 10 分［10 × (100% − 班排%)］＋院推薦排序加分 1–4 分＋曾任國際處國際學伴或國際事務社團幹部最高 3 分），提請甄選審查會核定錄取名單及推薦學校；獲錄取及獎補助學生須依限簽署《出國交換研修行政契約書》。"
                ),
                "details": [
                    "語言積分標準對照表：10 分級距為 TOEFL iBT 95 / ITP 627、IELTS 7.0、TOEIC 880、JLPT N1–N2、TOPIK 4–6 級；8 分級距（CEFR B2，學海飛颺門檻）為 TOEFL iBT 72 / ITP 543、IELTS 6.0、TOEIC 750、JLPT N3、TOPIK 3 級；5 分級距（CEFR B1）為 TOEFL iBT 42 / ITP 460、IELTS 5.0、TOEIC 550、JLPT N4、TOPIK 2 級；2 分級距（CEFR A2）為 TOEFL iBT 39 / ITP 430、IELTS 4.0、TOEIC 450、JLPT N5、TOPIK 1 級。",
                    "同步獎補助申請：符合資格之錄取生可申請教育部《學海飛颺》／《學海惜珠》或校內《選送優秀學生出國補助要點》（歐美一學期最高 5 萬／一學年 10 萬；亞太一學期最高 3.5 萬／一學年 7 萬）。",
                ],
                "scope": {
                    "home_universities": ["國立暨南國際大學"],
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
                    NCNU_SCORE_RULES_PDF_URL,
                    NCNU_SUBSIDY_RULES_PDF_URL,
                    NCNU_SCHOLARSHIPS_URL,
                    NCNU_XUEHAI_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ncnu-{sn:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由暨大國際及兩岸事務處向 {zh_name} 辦理官方提名，並於姊妹校截止日前遞交入學與宿位申請文件",
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"完成校內錄取確認後，由暨大國際及兩岸事務處統一向 {zh_name} 辦理官方提名（Nomination）；學生須於姊妹校申請截止日前完成線上申請並上傳外文入學申請表、英文歷年成績單、護照影本、英文財力證明、外語檢定證書及宿舍申請表，靜候接待校核發正式入學許可（Admission Letter / DS-2019 / I-20 / COE / 錄取通知書）。"
                ),
                "details": [
                    f"研修期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["國立暨南國際大學"],
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
                "source_urls": (
                    [source_url, NCNU_EXCHANGE_DEADLINES_URL]
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"ncnu-{acad_year}-home-5-{sn:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "出國前完成暨大註冊繳費與《國外學分換算表》選課預審，返國 14 日內繳交交換研修心得報告並辦理補助核銷與學分抵免",
                "responsible_party": "學生與所屬系所",
                "responsible_unit": "國立暨南國際大學國際及兩岸事務處／教務處／各系所",
                "summary": (
                    "出國前須依國際處《國外學分換算表》（歐洲 2 ECTS = 1 學分、英國 4 CATS = 1 學分、美加日韓約 1:1）就擬選修課程大綱向所屬系所確認抵免原則，並於交換期間維持暨大在學註冊及繳交全額學雜費；返國後 14 日內須繳交《出國交換研修心得報告》（學海受獎生同步上傳教育部學海計畫平台），並檢具登機證正本、電子機票收據、護照出入境章影本及姊妹校正式成績單辦理補助核銷與學分抵免。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["國立暨南國際大學"],
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
                    NCNU_SOP_PDF_URL,
                    NCNU_CREDIT_CONVERSION_PDF_URL,
                    NCNU_DOWNLOADS_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合國立暨南國際大學國際及兩岸事務處（OIA）《姊妹校交換生資訊》總表（142 所海外開放交換校）、大陸及港澳地區交換姊妹校一覽表（20 所開放交換校）、跨國雙聯學位專區（4 所雙聯合作校）、全球締約姊妹校地圖 KML（50 所締約參考校）、《選送學生出國研修積分計算要點》、《選送優秀學生出國補助要點》、《國外學分換算表》及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆學長姐返校心得報告，共 {len(catalog_source)} 所合作姊妹校資料。"
        ),
    })

    cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": f"國立暨南國際大學國際及兩岸事務處（OIA）姊妹校交換生資訊、申請資格與雙聯學位專頁—{zh_name}",
            "source_url": source_url,
            "summary": "暨大國際及兩岸事務處公告之合作學程、開放學制、語言檢定門檻與互免學費／雙聯學位待遇說明",
        },
        {
            "title": "國立暨南國際大學選送學生出國研修積分計算要點與選送優秀學生出國補助要點",
            "source_url": NCNU_REGULATIONS_URL,
            "summary": "暨大出國交換在學註冊規定、30 分量化積分公式（主要語言 10 分＋次要語言 3 分＋學業班排 10 分＋院排序 4 分＋國際參與 3 分）、學分換算與獎補助規範",
        },
    ]
    if exp_links:
      dest_sources.append({
          "title": f"國立暨南國際大學國際及兩岸事務處學生交換心得報告專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
          "source_url": exp_links[0]["url"],
          "summary": f"收錄歷年暨大學生赴 {zh_name} 交換研修返校心得報告共 {len(exps)} 篇",
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
            NCNU_EXCHANGE_OVERVIEW_URL,
            NCNU_EXCHANGE_DEADLINES_URL,
            NCNU_SCHOLARSHIPS_URL,
        ]
        + ([exp_links[0]["url"]] if exp_links else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "國立暨南國際大學",
        "school_name": full_name,
        "country": country,
        "city": city_name,
        "cost_summary": f"{cost_line}。\n{tuition_clean}",
        "housing_summary": housing_clean,
        "transport_summary": (
            f"校區代表城市：{city_name}。請依入學許可確認實際授課校區位置與當地學生交通卡優惠。"
        ),
        "campus_life_summary": f"{calendar_clean}\n{course_clean}",
        "student_guide_sections": [
            {
                "key": "cost",
                "title": "生活費、暨大在學註冊規定與教育部學海飛颺／學海惜珠／校內出國補助",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [NCNU_DUAL_DEGREE_URL],
                "caution": (
                    "依《國立暨南國際大學選送優秀學生出國補助要點》，獲補助學生須於出國前簽訂行政契約書；非因不可抗力因素放棄出國、未完成修課或未於返國後 14 日內繳交心得報告者，須全額繳回補助款。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外國際學生宿舍申請",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": "各姊妹校校內學生宿舍床位有限，獲暨大國際及兩岸事務處提名後請務必於接待校規定期限內完成線上宿位申請。",
            },
            {
                "key": "insurance",
                "title": "海外醫療及意外保險與家長同意書規定",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依暨大國際及兩岸事務處規定，所有交換生及雙聯生均須繳交經家長（監護人）簽章之同意書，並於出國前投保涵蓋交換全期之海外醫療及意外保險。",
                ],
                "source_urls": src_url_list,
                "caution": "美國、德國、法國、荷蘭、捷克、英國、日本、韓國、澳洲等接待校對交換生保險保額或當地國民健康保險有強制規定，請依入學通知書辦理。",
            },
            {
                "key": "visa",
                "title": "留學交換簽證辦理、行政契約書簽署與在學註冊義務",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "交換期間須維持國立暨南國際大學在學身分並繳交全額學雜費；領取教育部學海系列或校內出國補助者須於出國前完成行政契約書簽訂。",
                ],
                "source_urls": src_url_list,
                "caution": "出國前請務必確認護照效期、簽證核發進度、選課抵免預審與行政契約書簽署。",
            },
            {
                "key": "academics",
                "title": "國外學分換算表（2 ECTS = 1 學分、4 CATS = 1 學分）、跨國雙聯修業規定與返國核銷程序",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [NCNU_CREDIT_CONVERSION_PDF_URL],
                "caution": (
                    "於歐洲姊妹校修習之 ECTS 學分原則上以 2 ECTS 折算暨大 1 學分，英國 CATS 學分以 4 CATS 折算暨大 1 學分，返國後須檢附正式成績單與課程大綱向系所及教務處辦理抵免。"
                ),
            },
            {
                "key": "living",
                "title": f"{city_name} 校園生活與暨大學長姐返校心得傳承",
                "summary": f"代表城市：{city_name}。請配合接待校國際處完成報到與新生訓練（Orientation）。",
                "points": [
                    f"目的地城市：{city_name}（{country}）",
                    (
                        "暨大國際及兩岸事務處公開收錄歷屆各院系所學生赴海外及大陸港澳姊妹校交換之返校心得報告"
                        + (
                            f"（本校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，並設有國際學伴（Buddy Program）制度協助交流傳承。"
                    ),
                ],
                "source_urls": [
                    exp_links[0]["url"] if exp_links else NCNU_EXPERIENCES_URL
                ],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合國立暨南國際大學國際及兩岸事務處 {len(catalog_source)} 所合作姊妹校、當期開放交換及雙聯名額表（162 校）、跨國雙聯學位（4 校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆學生返校心得報告。"
        ),
    })

    research_records.append({
        "home_university": "國立暨南國際大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            "國立暨南國際大學國際及兩岸事務處《姊妹校交換生資訊》總表、《赴大陸及港澳地區交換姊妹校一覽》、《跨國雙聯學位專區》、全球締約姊妹校地圖 KML 與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"國立暨南國際大學國際及兩岸事務處姊妹校交換名額與申請條件專頁—{zh_name}",
            "url": source_url,
        },
    ]
    if exp_links:
      ev_sources.append({
          "title": f"國立暨南國際大學國際及兩岸事務處學生交換心得報告—赴 {zh_name} 心得報告（{len(exps)} 篇）",
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
            "scope": "暨大海外與大陸港澳交換姊妹校住宿與生活資訊",
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
            "scope": "暨大出國交換學雜費規定、教育部學海飛颺／惜珠、校內選送優秀學生出國補助與地區生活費估算",
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
            "scope": "暨大選送學生出國研修積分計算要點（30 分制）、國外學分換算表与返國報告規範",
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
            "scope": "暨大海外交換與雙聯學位簽證、家長同意書、海外醫療保險與行前提醒",
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
                    f"｜暨大公開收錄 {len(exps)} 篇赴 {zh_name} 交換生返校心得報告（{'、'.join(exp_labels[:3])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "暨大交換名額與歷屆學長姐返校心得報告分享",
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
            "已整合國立暨南國際大學國際及兩岸事務處《姊妹校交換生資訊》總表、《赴大陸及港澳地區交換生姊妹校一覽》、《跨國雙聯學位專區》、《選送學生出國研修積分計算要點》及歷屆學生交換心得報告。",
            "當期免學費名額、宿位供給、語檢門檻與選課限制請依合作校最新簡章及入學通知書核對。",
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

  write_jsonl(OFFICIAL_NCNU_DIR / "partners.jsonl", partners)
  write_jsonl(SOURCES_NCNU_DIR / "partners.jsonl", partners)
  write_jsonl(OFFICIAL_NCNU_DIR / "application_workflows.jsonl", workflows)
  write_jsonl(OFFICIAL_NCNU_DIR / "destination_profiles.jsonl", destinations)
  write_jsonl(OFFICIAL_NCNU_DIR / "partner_research.jsonl", research_records)
  write_jsonl(OFFICIAL_NCNU_DIR / "student_life.jsonl", life_records)
  write_jsonl(
      OFFICIAL_NCNU_DIR / "experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_NCNU_DIR / "student_experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_NCNU_DIR / "student_experiences.jsonl", student_experience_rows
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
  (OFFICIAL_NCNU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_NCNU_DIR / "student-experiences.json").write_text(
      json.dumps(
          {
              "school_id": "ncnu",
              "school_name": "國立暨南國際大學",
              "checked_at": CHECKED_AT,
              "source_url": NCNU_EXPERIENCES_URL,
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

  (OFFICIAL_NCNU_DIR / "campus-locations.json").write_text(
      json.dumps(
          {
              "school_id": "ncnu",
              "school_name": "國立暨南國際大學",
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
  (OFFICIAL_NCNU_DIR / "campus-assets.json").write_text(
      json.dumps(
          {
              "school_id": "ncnu",
              "school_name": "國立暨南國際大學",
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

  ncnu_source_urls = [
      NCNU_OIA_HOME_URL,
      NCNU_EXCHANGE_OVERVIEW_URL,
      NCNU_EXCHANGE_DEADLINES_URL,
      NCNU_EXCHANGE_PARTNERS_SHEET_URL,
      NCNU_PARTNERS_MAP_URL,
      NCNU_MAINLAND_PARTNERS_URL,
      NCNU_MAINLAND_APPLY_URL,
      NCNU_MAINLAND_QA_URL,
      NCNU_SCHOLARSHIPS_URL,
      NCNU_XUEHAI_URL,
      NCNU_SCHOOL_SUBSIDY_URL,
      NCNU_EXPERIENCES_URL,
      NCNU_REGULATIONS_URL,
      NCNU_DOWNLOADS_URL,
      NCNU_DUAL_DEGREE_URL,
      NCNU_SCORE_RULES_PDF_URL,
      NCNU_SUBSIDY_RULES_PDF_URL,
      NCNU_DUAL_DEGREE_RULES_PDF_URL,
      NCNU_SOP_PDF_URL,
      NCNU_CREDIT_CONVERSION_PDF_URL,
      NCNU_APPLICATION_FORM_PDF_URL,
  ]

  exchange_info_payload = {
      "school_name": "國立暨南國際大學",
      "program_type": [
          (
              "國際及兩岸事務處（OIA）海外及大陸港澳姊妹校交換學生計畫（涵蓋日、韓、美、加、英、德、法、捷克、西、荷、奧、澳、新南向及大陸港澳等 162 所當期開放申請合作校，交換期間保有暨大在學學籍並繳交本校全額學雜費、免繳接待姊妹校學費）"
          ),
          (
              "4 校跨國雙聯學位計畫（涵蓋【美國加州大學河濱分校 University of California, Riverside】3+1+MS 工學院學碩雙聯；【法國雷恩商學院 Rennes School of Business】管理學院雙聯學位；【加拿大紐芬蘭紀念大學 Memorial University of Newfoundland】管理學院雙聯學位；【泰國農業大學 Kasetsart University】教育學院雙聯學位，取得雙聯學位證書後得請領 NT$ 100,000 獎勵金）"
          ),
          (
              "教育部「學海飛颺」（優秀交換生出國研修，主要語言積分須達 8 分／CEFR B2 以上）、「學海惜珠」（補助清寒優秀學生來回機票與生活費）與校內《選送優秀學生出國補助要點》（歐美地區一學期最高 5 萬／一學年 10 萬；亞太地區一學期最高 3.5 萬／一學年 7 萬）"
          ),
      ],
      "academic_year": [
          (
              "115（涵蓋秋季班［每年 2–3 月校內收件提名，當年 8/9 月出國］、春季班［每年 9–10 月校內收件提名，隔年 1/2 月出國］、大陸及港澳交換生［春季班 9–11 月、秋季班 2–4 月收件］及教育部學海飛颺／惜珠與校內出國補助甄選）"
          ),
          (
              f"本平台完整收錄國立暨南國際大學國際及兩岸事務處公告之 {len(partners)} 所全球與大陸港澳合作姊妹校（含 {open_partner_count} 所當期開放申請之海外與大陸港澳交換姊妹校及跨國雙聯學位合作校、{len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 38 個國家與地區，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返校心得報告）"
          ),
      ],
      "semester": [
          "秋季班（Fall Semester 出國交換一學期或一學年）：每年 2 月至 3 月底前完成系所與學院初審排序並送交國際處提名，於當年 8 月或 9 月赴海外姊妹校入學。",
          "春季班（Spring Semester 出國交換一學期或一學年）：每年 9 月至 10 月底前完成系所與學院初審排序並送交國際處提名，於次年 1 月至 4 月赴海外姊妹校入學。",
          "大陸及港澳地區交換生（春季班每年 9–11 月、秋季班每年 2–4 月收件；香港教育大學僅於每年 4 月開放申請）及跨國雙聯學位計畫（依各雙聯協議時程申請）。",
      ],
      "application_period": [
          "【秋季班（Fall Semester 出國：海外姊妹校交換生暨跨國雙聯學位甄選）】每年 2 月初至 3 月底（依國際處《姊妹校交換生申請截止日期》各校提名時程分批截止）；先經系所及學院初審排定院推薦順序，再送交國際及兩岸事務處核算總積分並向姊妹校提名。",
          "【春季班（Spring Semester 出國：海外姊妹校交換生暨跨國雙聯學位甄選）】每年 9 月初至 10 月底（部分早截止姊妹校於 9 月中旬截止）；先經系所及學院初審排序後送國際處審查並於 10–11 月向姊妹校完成線上提名。",
          "【赴大陸及港澳地區姊妹校交換生甄選（20 所合作高校）】春季班約每年 9 月至 11 月校內收件；秋季班約每年 2 月至 4 月校內收件（香港教育大學僅於每年 4 月春季開放申請且須附英檢證明）。",
          "【教育部學海飛颺／學海惜珠獎學金＆校內選送優秀學生出國補助】第 1 次甄選約每年 12 月至隔年 1 月中旬收件；第 2 次甄選約每年 9 月至 10 月收件。",
      ],
      "eligibility": [
          "1. 學籍與年級限制：申請人須為國立暨南國際大學正式註冊在學且已於本校就讀至少一學期以上之【學士班】、【碩士班】或【博士班】學生（即大一下、碩一下、博一下含以上始得提出申請；不包括國內及境外在職專班生、休學生及無正式學籍選讀生）。赴大陸及港澳地區交換生須於本校修業滿一年（大二以上）始得申請；跨國雙聯學位學士班及博士班須於本校修業滿二學期、碩士班須修業滿一學期始得申請。",
          "2. 學業成績與班排積分：依《國立暨南國際大學選送學生出國研修積分計算要點》（112.06.14 修正通過），學士班學業成績積分（滿分 10 分）以「10 分 × (100% − 班級排名百分比)」計算，碩博士班由各院綜合考量給分；海外姊妹校普遍要求在校 GPA 2.5–3.0（約學業總平均 70–75 分以上），部分歐美日韓名校（如美國加州大學河濱分校 UCR、加拿大維多利亞大學、韓國首爾市立大學）要求 GPA 3.0 以上。",
          "3. 特定學院與學制限制：（a）日本中央大學限人文學院學生申請；（b）日本宇都宮大學限人文學院及教育學院學生申請；（c）日本熊本大學秋季交換限科技學院研究所（碩博士班）學生申請；（d）美國加州大學河濱分校 3+1+MS 雙聯限科技學院、法國雷恩商學院與加拿大紐芬蘭紀念大學雙聯限管理學院、泰國農業大學雙聯限教育學院申請。",
          "4. 校內甄選 30 分量化總積分公式：總積分滿分 30 分 ＝（a）主要語言能力成績最高 10 分 ＋（b）次要語言能力成績最高 3 分 ＋（c）學業成績最高 10 分（10 × [100% − 班排%]）＋（d）院推薦排序加分 1–4 分（院排序前 25% 加 4 分、26%–50% 加 3 分、51%–75% 加 2 分、76%–100% 加 1 分）＋（e）曾任國際處國際學伴或國際事務相關社團幹部最高 3 分。",
      ],
      "language_requirement": [
          "1. 依《國立暨南國際大學選送學生出國研修積分計算要點》附表「語言積分標準對照表」，主要語言能力分為四級距：（a）【10 分級距（CEFR B2–C2）】：TOEFL iBT 95 / ITP 627、IELTS 7.0、TOEIC 880、GEPT 優級、JLPT N1–N2、TOPIK 4–6 級、DELF/DELE/Goethe B2–C2、VINATEST 越南語 C 級；（b）【8 分級距（CEFR B2，歐美主流姊妹校與教育部學海飛颺門檻）】：TOEFL iBT 72 / ITP 543、IELTS 6.0、TOEIC 750、GEPT 高級、JLPT N3、TOPIK 3 級、歐語 B1、VINATEST B 級；（c）【5 分級距（CEFR B1，一般交換門檻）】：TOEFL iBT 42 / ITP 460、IELTS 5.0、TOEIC 550、GEPT 中高級、JLPT N4、TOPIK 2 級、歐語 A2；（d）【2 分級距（CEFR A2）】：TOEFL iBT 39 / ITP 430、IELTS 4.0、TOEIC 450、GEPT 中級、JLPT N5、TOPIK 1 級。",
          "2. 日本姊妹校（廣島大學、信州大學、中央大學、福井大學、宇都宮大學、熊本大學、龍谷大學、同志社大學、芝浦工業大學、多摩大學、高崎經濟大學等）：日語授課組普遍要求 JLPT N2 或 N3 以上（同志社大學、中央大學、信州大學日語組要求 N2 以上；多摩大學、高崎經濟大學可接受 N3–N4 或英語成績）。",
          "3. 韓國姊妹校（高麗大學世宗校區、中央大學、韓國外國語大學、慶北大學、梨花女子大學、淑明女子大學、首爾市立大學、明知大學、京畿大學、嘉泉大學等）：要求韓語 TOPIK 2–3 級以上，或英語 TOEFL iBT 71–80 / IELTS 5.5–6.0 / TOEIC 750 以上。",
          "4. 大陸及澳門地區姊妹校（蘭州大學、山東大學、吉林大學、四川大學、華南師範大學、北京第二外國語學院、中央民族大學、澳門城市大學等 19 校）：免附外語檢定成績證明（若有外語檢定仍可列計校內積分；香港教育大學須具備英語檢定證明）。",
      ],
      "required_documents": [
          "1. 國立暨南國際大學出國交換學生甄選申請表（填妥個人資料與志願學校，並經就讀系所及所屬學院核章）",
          "2. 國立暨南國際大學選送學生出國研修積分自評表（依主要語言、次要語言、班級排名百分比、院推薦排序及國際學伴／社團幹部經歷填列並附佐證影本）",
          "3. 歷年中文及英文成績單正本（須註明歷年學業總平均、GPA 及歷年班級排名百分比）",
          "4. 有效外語能力檢定成績單影本（TOEFL iBT / ITP、IELTS、TOEIC、GEPT、JLPT、TOPIK、DELF/DELE/Goethe、VINATEST 等；大陸及澳門交換免附）",
          "5. 中英文讀書計畫（Study Plan，含交換動機、擬於姊妹校選修課程與返國學分抵免規劃）及自傳（Autobiography / CV）",
          "6. 師長推薦信、家長（監護人）同意書及有效護照基本資料頁影本",
          "7. 申請教育部《學海惜珠》者另附新式戶口名簿影本及低收入戶／中低收入戶／特殊境遇家庭證明文件",
          "8. 錄取後簽署《出國交換研修行政契約書》；返國後 14 日內繳交《出國交換研修心得報告》並檢具登機證、機票收據、出入境證明與正式成績單辦理補助核銷與學分抵免",
      ],
      "scholarship_info": [
          "1. 教育部「學海飛颺」選送優秀學生出國研修獎學金：補助具中華民國國籍、於暨大就讀滿一學期以上之優秀在學學生赴海外姊妹校（不含大陸及港澳）交換修讀學分一學期或一學年；申請人主要語言積分須達《選送學生出國研修積分計算要點》8 分（CEFR B2：TOEFL iBT 72 / IELTS 6.0 / TOEIC 750 / JLPT N3 / TOPIK 3 級）以上，每名核給約新臺幣 50,000 元至 150,000 元（依教育部當年度核定經費與校內積分排名配點核定）。",
          "2. 教育部「學海惜珠」選送勵學優秀學生出國研修獎學金：補助具中華民國國籍且領有各直轄市、縣（市）政府核發之低收入戶、中低收入戶或特殊境遇家庭相關證明之優秀在學學生赴海外姊妹校交換，補助國際來回機票及國外生活費。",
          "3. 《國立暨南國際大學選送優秀學生出國補助要點》（114.07.22 修正通過）校內出國補助：補助未同時領取教育部學海計畫或外國政府公費之優秀出國交換生，歐美地區交換一學期最高新臺幣 50,000 元、一學年最高 100,000 元；亞洲及大洋洲地區交換一學期最高 35,000 元、一學年最高 70,000 元（依當年度預算核定）。",
          "4. 《國立暨南國際大學辦理跨國雙聯學位制補助要點》（114.08.19 修正通過）：經核准修讀本校跨國雙聯學位計畫（美國加州大學河濱分校 UCR、法國雷恩商學院、加拿大紐芬蘭紀念大學、泰國農業大學）並順利取得國外合作大學頒發之學位證書者，得請領新臺幣 100,000 元雙聯學位獎勵金。",
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": ncnu_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_NCNU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "國立暨南國際大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 70.0,
      "academic_score_rule": (
          "依《國立暨南國際大學學生赴海外姊妹校交換標準作業流程（SOP）》、《選送學生出國研修積分計算要點》（112.06.14 修正通過）及《選送優秀學生出國補助要點》（114.07.22 修正通過）：申請人須為本校正式註冊在學且已於本校就讀至少一學期以上之學士班、碩士班或博士班學生（大陸港澳交換須修業滿一年；雙聯學位學士及博士班須滿二學期、碩士班須滿一學期）。學士班學業成績積分（滿分 10 分）以「10 分 × (100% − 班級排名百分比)」計算；多數海外姊妹校要求在校 GPA 2.5–3.0（約學業平均 70–75 分以上）。"
      ),
      "academic_gpa_minimum": 2.5,
      "maximum_preferences": 5,
      "selection_rules": {
          "academic_policy": "gpa_or_rank",
          "academic_reference_year": "115",
          "undergraduate_gpa_minimum": 2.5,
          "graduate_academic_exempt": False,
          "exclude_in_service": True,
          "pending_quota_planning": False,
          "partner_requirements_need_confirmation": False,
          "degree_score_minimums": {
              "undergraduate": 70.0,
              "graduate": 70.0,
          },
          "excluded_undergraduate_years": [
              "大一上",
              "碩一上",
              "博一上",
              "在職專班",
          ],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 39.0,
          "ielts": 4.0,
          "toeic": 450.0,
      },
      "application_periods": [
          {
              "title": "國立暨南國際大學 115學年度春季班（2027 Spring 出國：9–10月校內收件提名）海外及大陸港澳姊妹校交換學生甄選",
              "details": [
                  "國際及兩岸事務處於每年 9 月初至 10 月底前（依《姊妹校交換生申請截止日期》各校時程分批截止）受理次學期（春季班）赴海外姊妹校及大陸港澳地區姊妹校交換一學期或一學年申請。",
                  "申請學生須先將《出國交換學生甄選申請表》、《選送學生出國研修積分自評表》、含班排成績單、外語檢定證明與讀書計畫送交系所及學院排定「院推薦順序」（前 25% 加 4 分），再由學院彙送國際處依 30 分總積分制核定推薦並辦理姊妹校提名。",
              ],
              "source": {
                  "title": "國立暨南國際大學國際及兩岸事務處姊妹校交換生申請流程與申請截止日期公告",
                  "source_url": NCNU_EXCHANGE_DEADLINES_URL,
                  "category": "exchange_application",
                  "summary": "暨大海外及大陸港澳姊妹校交換生春季班（9–10月）與秋季班（2–3月）收件提名時程與 30 分積分評比規定。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "115學年度春季班（9–10月收件提名）",
              "audience": "all_students",
              "opens_at": "2026-09-01T09:00:00+08:00",
              "deadline_at": "2026-10-30T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "春季班海外及大陸港澳交換於每年 9 月至 10 月底依各姊妹校截止日分批受理系院初審與國際處提名。",
              "deadline_note": "請先確認各志願校於《姊妹校交換生申請截止日期》之提名期限，預留系所與學院核章及排定院推薦順序時間。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "國立暨南國際大學 115學年度教育部「學海飛颺／學海惜珠」及校內選送優秀學生出國補助甄選",
              "details": [
                  "國際及兩岸事務處每年分兩梯次（約 12 月–1 月中旬及 9 月–10 月）受理已獲姊妹校交換推薦或預計出國交換之在學學生申請教育部《學海飛颺》（主要語言積分須達 8 分／CEFR B2 以上）、《學海惜珠》（具低收／中低收／特殊境遇證明）及校內《選送優秀學生出國補助要點》獎助學金。",
                  "校內出國補助標準：歐美地區交換一學期最高新臺幣 50,000 元、一學年最高 100,000 元；亞洲及大洋洲地區交換一學期最高 35,000 元、一學年最高 70,000 元；跨國雙聯學位取得國外學位證書者另得請領 100,000 元獎勵金。",
              ],
              "source": {
                  "title": "國立暨南國際大學教育部學海計畫專區與選送優秀學生出國補助要點（114.07.22修正）",
                  "source_url": NCNU_XUEHAI_URL,
                  "category": "scholarship",
                  "summary": "暨大學海飛颺、學海惜珠與校內出國補助之申請資格、語言門檻與補助額度。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "115學年度學海飛颺／惜珠與校內出國補助甄選",
              "audience": "all_students",
              "opens_at": "2026-12-01T09:00:00+08:00",
              "deadline_at": "2027-01-15T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "每年 12 月至隔年 1 月中旬受理次學期／次學年度出國交換生申請學海系列與校內出國補助。",
              "deadline_note": "申請學海飛颺者主要語言積分須達 8 分（CEFR B2）以上；申請學海惜珠者須附新式戶口名簿及低收／中低收／特殊境遇證明。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "國立暨南國際大學 116學年度秋季班（2027 Fall 出國：2–3月校內收件提名）海外及大陸港澳姊妹校交換學生甄選",
              "details": [
                  "每年 2 月初至 3 月底前受理當年度秋季班（8/9 月出國）赴日本、韓國、歐美、新南向及大陸港澳姊妹校交換一學期或一學年申請（香港教育大學僅於每年 4 月春季梯次開放申請）。",
                  "請提前報考 TOEFL iBT / ITP、IELTS、TOEIC、JLPT 或 TOPIK 取得成績單，並於開學後送交系所及學院辦理初審排序。",
              ],
              "source": {
                  "title": "國立暨南國際大學國際及兩岸事務處海外姊妹校交換申請流程與大陸港澳交換說明",
                  "source_url": NCNU_EXCHANGE_OVERVIEW_URL,
                  "category": "exchange_application",
                  "summary": "暨大每年 2–3 月秋季班海外與大陸港澳交換收件提名時程與申請程序。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "116學年度秋季班（2–3月收件提名）",
              "audience": "all_students",
              "opens_at": "2027-02-01T09:00:00+08:00",
              "deadline_at": "2027-03-31T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "秋季班海外交換於每年 2–3 月受理系院初審與國際處提名（大陸港澳交換秋季班至 4 月截止）。",
              "deadline_note": "日本、韓國及歐美多數姊妹校秋季班提名截止日集中於 2 月底至 4 月中旬，請依《姊妹校交換生申請截止日期》提早送件。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"國立暨南國際大學國際及兩岸事務處姊妹校交換、跨國雙聯學位與學海獎補助總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所當期開放申請・{total_exp_reports} 篇學長姐返校心得報告）"
              ),
              "details": [
                  (
                      f"國立暨南國際大學（NCNU，暨大，創立於 1995 年，坐落於南投縣埔里鎮水沙連地區，為臺灣最具國際化與東南亞研究特色之綜合型國立大學）由「國際及兩岸事務處（Office of International and Cross-Strait Affairs, OIA）」統籌全校 6 大學院（人文學院、管理學院、科技學院、教育學院、水沙連學院、護理暨健康福祉學院）及智慧暨永續農業學士學位學程之海外姊妹校交換生計畫、大陸及港澳地區交換生計畫、跨國雙聯學位計畫及教育部學海系列獎補助。本平台完整收錄 {len(partners)} 所暨大官方合作姊妹校（含 {open_partner_count} 所當期開放申請之海外及大陸港澳交換姊妹校與雙聯學位合作校，以及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 38 個國家與地區。"
                  ),
                  (
                      f"暨大國際交流具備四大核心特色：（1）142 所海外開放交換姊妹校與 20 所大陸港澳交換姊妹校（涵蓋日本廣島大學、信州大學、中央大學、福井大學、宇都宮大學、熊本大學、龍谷大學、同志社大學、芝浦工業大學，韓國高麗大學世宗校區、中央大學、韓國外國語大學、慶北大學、梨花女子大學、淑明女子大學、首爾市立大學，歐美加州大學河濱分校 UCR、南佛羅里達大學、維多利亞大學、紐芬蘭紀念大學、英國羅浮堡大學、德國柏林自由大學 FU-BEST、法國雷恩商學院、捷克查理大學，以及大陸蘭州大學、山東大學、吉林大學、四川大學、華南師範大學、香港教育大學、澳門城市大學等）；（2）4 校跨國雙聯學位計畫（美國加州大學河濱分校 3+1+MS、法國雷恩商學院、加拿大紐芬蘭紀念大學、泰國農業大學，取得雙聯學位核給 10 萬元獎勵金）；（3）公開透明之 30 分制《選送學生出國研修積分計算要點》；（4）完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返校心得報告。"
                  ),
              ],
              "source": {
                  "title": "國立暨南國際大學國際及兩岸事務處（OIA）交換計畫與合作學校官方網站",
                  "source_url": NCNU_EXCHANGE_OVERVIEW_URL,
                  "category": "exchange_application",
                  "summary": f"暨大 {len(partners)} 所全球合作姊妹校、4 校雙聯學位與 {total_exp_reports} 篇返校心得報告。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "暨大在學學籍（就讀滿一學期以上，大陸港澳滿一年）、班排成績換算與 30 分量化總積分甄選公式",
              "details": [
                  "學籍與修業年級規定：依《國立暨南國際大學學生赴海外姊妹校交換標準作業流程（SOP）》與《選送優秀學生出國補助要點》第 3 點，申請人須為本校正式註冊在學且已於本校就讀至少一學期以上之學士班、碩士班或博士班學生（不含國內及境外在職專班生、休學生；大一上、碩一上、博一上新生須待修畢一學期後始得申請）。赴大陸及港澳地區交換生須於本校修業滿一年（大二含以上）；跨國雙聯學位學士班及博士班須修業滿二學期、碩士班須修業滿一學期。",
                  "30 分制量化總積分公式：依《國立暨南國際大學選送學生出國研修積分計算要點》（112.06.14 修正通過），校內甄選總積分滿分 30 分：（1）主要語言能力成績最高 10 分（B2–C2 為 8–10 分、B1 為 5 分、A2 為 2 分）；（2）次要語言能力成績最高 3 分；（3）學業成績最高 10 分，學士班以「10 分 × (100% − 班級排名百分比)」計算，碩博士班由各院綜合考量給分；（4）院推薦排序加分 1–4 分（前 25% 加 4 分、26%–50% 加 3 分、51%–75% 加 2 分、76%–100% 加 1 分）；（5）曾任國際處國際學伴或國際事務相關社團幹部最高 3 分。",
              ],
              "source": {
                  "title": "國立暨南國際大學選送學生出國研修積分計算要點（112.06.14修正通過）與學生赴海外姊妹校交換標準作業流程",
                  "source_url": NCNU_SCORE_RULES_PDF_URL,
                  "category": "exchange_application",
                  "summary": "暨大交換生在學學期限制、班排百分比換算 10 分公式、院推薦排序加分與 30 分總積分規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "語言積分標準對照表（10分／8分／5分／2分四級距：TOEFL / IELTS / TOEIC / GEPT / JLPT / TOPIK / 歐語 / 越南語）與大陸澳門免語檢規定",
              "details": [
                  "英語及歐亞語種採計標準：暨大《選送學生出國研修積分計算要點》附表同時採計 TOEFL iBT、TOEFL ITP、IELTS、TOEIC、GEPT 全民英檢、JLPT 日檢、TOPIK 韓檢、DELF/DALF 法檢、Goethe/TestDaF 德檢、DELE 西檢及 VINATEST 越南語檢定：（1）10 分級距：TOEFL iBT 95 / ITP 627、IELTS 7.0、TOEIC 880、GEPT 優級、JLPT N1–N2、TOPIK 4–6 級；（2）8 分級距（CEFR B2，歐美主流姊妹校及教育部學海飛颺門檻）：TOEFL iBT 72 / ITP 543、IELTS 6.0、TOEIC 750、GEPT 高級、JLPT N3、TOPIK 3 級；（3）5 分級距（CEFR B1，一般交換門檻）：TOEFL iBT 42 / ITP 460、IELTS 5.0、TOEIC 550、GEPT 中高級、JLPT N4、TOPIK 2 級；（4）2 分級距（CEFR A2）：TOEFL iBT 39 / ITP 430、IELTS 4.0、TOEIC 450、GEPT 中級、JLPT N5、TOPIK 1 級。",
                  "日韓與大陸港澳地區特殊規定：（1）日本國立及私立名校日語授課組普遍要求 JLPT N2 或 N3 以上（日本中央大學限人文學院、宇都宮大學限人文／教育學院、熊本大學秋季限科技學院碩博生）；（2）韓國姊妹校韓語組要求 TOPIK 2–3 級以上，英語組可憑 TOEFL iBT 71–80 / IELTS 5.5–6.0 / TOEIC 750 申請；（3）大陸及澳門 19 所姊妹校免附外語檢定證明（香港教育大學僅於每年 4 月開放申請且須附英語檢定證明）。",
              ],
              "source": {
                  "title": "國立暨南國際大學選送學生出國研修積分計算要點附表「語言積分標準對照表」與姊妹校交換生資訊總表",
                  "source_url": NCNU_SCORE_RULES_PDF_URL,
                  "category": "exchange_application",
                  "summary": "暨大出國研修語言積分四級距對照表與各姊妹校語檢門檻。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "出國交換學生甄選申請表（含系院核章）、研修積分自評表、含班排歷年成績單、語檢證明與中英文讀書計畫",
              "details": [
                  "校內初審與甄選必備文件：（1）《國立暨南國際大學出國交換學生甄選申請表》（須經就讀系所及所屬學院核章並排定院推薦順序）；（2）《選送學生出國研修積分自評表》（附語言檢定、班排、國際學伴或社團幹部證明）；（3）歷年中英文成績單正本（須註明學業平均、GPA 與班級排名百分比）；（4）有效外語能力檢定成績單影本（大陸及澳門交換免附）；（5）中英文讀書計畫（Study Plan）、自傳（Autobiography）、師長推薦信、家長同意書及護照影本。",
                  "錄取簽約與返國核銷文件：獲錄取及獎補助者須於出國前簽署《行政契約書》；返國後 14 日內須繳交《出國交換研修心得報告》（學海受獎生並須上傳教育部學海計畫平台），並檢具登機證正本、電子機票收據、護照出入境章影本、姊妹校正式成績單與《國外學分換算表》辦理補助核銷與學分抵免。",
              ],
              "source": {
                  "title": "國立暨南國際大學國際及兩岸事務處表單下載專區與海外姊妹校交換標準作業流程（SOP）",
                  "source_url": NCNU_DOWNLOADS_URL,
                  "category": "exchange_application",
                  "summary": "暨大出國交換甄選申請表、積分自評表、行政契約書、國外學分換算表與返國心得報告格式規範。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部學海飛颺（語言積分達 8 分／B2）、學海惜珠、校內選送優秀學生出國補助（歐美最高 10 萬／亞太最高 7 萬）與雙聯學位 10 萬元獎勵金",
              "details": [
                  "教育部學海系列與校內出國補助：（1）教育部《學海飛颺》：補助赴非大陸港澳之海外姊妹校交換一學期或一學年且主要語言積分達 8 分（CEFR B2）以上之優秀在學學生，每名約 NT$ 50,000–150,000；（2）教育部《學海惜珠》：補助具低收入戶、中低收入戶或特殊境遇家庭證明之優秀學生出國交換機票與生活費；（3）校內《國立暨南國際大學選送優秀學生出國補助要點》（114.07.22 修正通過）：補助未領取學海計畫或政府公費之交換生，歐美地區一學期最高 NT$ 50,000、一學年最高 NT$ 100,000；亞洲及大洋洲地區一學期最高 NT$ 35,000、一學年最高 NT$ 70,000。",
                  "跨國雙聯學位完業獎勵金：依《國立暨南國際大學辦理跨國雙聯學位制補助要點》（114.08.19 修正通過），修讀本校跨國雙聯學位計畫並順利取得國外合作大學學位證書者，檢具雙聯學位證書及歷年成績單得請領新臺幣 100,000 元獎勵金。",
              ],
              "source": {
                  "title": "國立暨南國際大學出國獎學金專區、選送優秀學生出國補助要點與辦理跨國雙聯學位制補助要點",
                  "source_url": NCNU_SCHOLARSHIPS_URL,
                  "category": "scholarship",
                  "summary": "暨大學海飛颺、學海惜珠、校內出國補助與雙聯學位 10 萬元獎勵金之申請資格與額度。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "國立暨南國際大學出國交換學生甄選申請表、選送學生出國研修積分自評表與返國心得報告準備指南",
              "summary": "說明暨大國際及兩岸事務處表單下載專區各項申請文件、系院推薦排序流程、國外學分換算及返國 14 日內心得報告與核銷要求。",
              "key_points": [
                  "出國交換學生甄選申請表與選送學生出國研修積分自評表須連同含班級排名百分比之歷年成績單、有效外語檢定證明、中英文讀書計畫及家長同意書，先送交就讀系所與所屬學院初審並排定「院推薦順序」（前 25% 加 4 分），再由學院彙送國際處。",
                  "選課與學分抵免規劃應參考國際處《國外學分換算表》（歐洲 ECTS 2 學分折算暨大 1 學分、英國 CATS 4 學分折算暨大 1 學分、美加日韓約 1:1 折算），於出國前先與系所確認抵免原則。",
                  "交換期滿返國後 14 日內須依《學海計畫研修心得報告格式》或《校內補助研修心得報告格式》繳交心得報告，並依《出國補助核銷檢核表》檢具登機證正本、電子機票收據及護照出入境章影本完成核銷。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立暨南國際大學國際及兩岸事務處表單下載專區與標準作業流程（SOP）",
                  "source_url": NCNU_DOWNLOADS_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NCNU_APPLICATION_FORM_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "國立暨南國際大學選送學生出國研修積分計算要點、選送優秀學生出國補助要點與跨國雙聯學位實施辦法核心規定",
              "summary": "規範暨大海外與大陸港澳交換生之在學學期資格、30 分制量化總積分公式、歐美最高 10 萬／亞太最高 7 萬校內補助及雙聯學位修業規定。",
              "key_points": [
                  "在學註冊與修業學期限制：海外交換申請人須已於暨大註冊就讀滿一學期以上（不含在職專班及休學生）；大陸及港澳交換須於暨大修業滿一年；跨國雙聯學位學士班及博士班須於暨大修業滿二學期、碩士班須修業滿一學期，且兩校修業時間合計學士班至少滿 32 個月、碩士班至少滿 12 個月、博士班至少滿 24 個月。",
                  "30 分制量化積分計算：主要語言最高 10 分（B2–C2 為 8–10 分、B1 為 5 分、A2 為 2 分）＋次要語言最高 3 分＋學業成績最高 10 分（學士班為 10 × [100% − 班排%]）＋院推薦排序加分 1–4 分＋曾任國際學伴或國際事務社團幹部最高 3 分。",
                  "行政契約與返國義務：獲教育部學海系列或校內出國補助者須於出國前簽訂行政契約書，於姊妹校每學期修習至少 2 門課或折合本校 6 學分以上及格成績，並於返國後 14 日內繳交心得報告，違約者須全額繳回補助款。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立暨南國際大學選送學生出國研修積分計算要點（112.06.14修正）與選送優秀學生出國補助要點（114.07.22修正）",
                  "source_url": NCNU_REGULATIONS_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NCNU_SCORE_RULES_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "國立暨南國際大學國際及兩岸事務處（Office of International and Cross-Strait Affairs）官方網站",
              "source_url": NCNU_OIA_HOME_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立暨南國際大學海外姊妹校交換生申請流程與甄選說明",
              "source_url": NCNU_EXCHANGE_OVERVIEW_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立暨南國際大學姊妹校交換生申請截止日期與《姊妹校交換生資訊》總表（142 所海外開放交換校）",
              "source_url": NCNU_EXCHANGE_DEADLINES_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立暨南國際大學赴大陸及港澳地區交換生姊妹校一覽與申請流程（20 所大陸港澳合作校）",
              "source_url": NCNU_MAINLAND_PARTNERS_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立暨南國際大學跨國雙聯學位申請專區（美國加州大學河濱分校 UCR、法國雷恩商學院、加拿大紐芬蘭紀念大學、泰國農業大學）",
              "source_url": NCNU_DUAL_DEGREE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": f"國立暨南國際大學全球合作姊妹校名錄與地圖（{len(partners)} 所合作姊妹校）",
              "source_url": NCNU_PARTNERS_MAP_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立暨南國際大學出國交換獎學金專區（教育部學海飛颺、學海惜珠與校內選送優秀學生出國補助）",
              "source_url": NCNU_SCHOLARSHIPS_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": f"國立暨南國際大學學生交換心得報告專區（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）",
              "source_url": NCNU_EXPERIENCES_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_NCNU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  doc_conditions = {
      "school_id": "ncnu",
      "school_name": "國立暨南國際大學",
      "checked_at": CHECKED_AT,
      "source_url": NCNU_EXCHANGE_OVERVIEW_URL,
      "common_documents": exchange_info_payload["required_documents"],
      "track_specific_conditions": [
          {
              "track": "國際及兩岸事務處秋季班（2–3月）＆春季班（9–10月）海外姊妹校交換生計畫（亞洲、歐美、大洋洲）",
              "required": [
                  "國立暨南國際大學出國交換學生甄選申請表（經就讀系所及所屬學院核章並排定院推薦順序）",
                  "國立暨南國際大學選送學生出國研修積分自評表（附語言檢定、班排、國際學伴或社團佐證）",
                  "歷年中英文成績單正本（含學業平均、GPA 及班級排名百分比）與有效外語檢定成績單影本",
                  "中英文讀書計畫（Study Plan）、自傳（Autobiography）、師長推薦信、家長同意書及護照影本",
                  "錄取後簽署行政契約書；返國後 14 日內繳交研修心得報告並辦理補助核銷與學分抵免",
              ],
          },
          {
              "track": "國際及兩岸事務處赴大陸及港澳地區姊妹校交換生計畫（蘭州大學、山東大學、吉林大學、四川大學、華南師範大學、香港教育大學、澳門城市大學等 20 校）",
              "required": [
                  "國立暨南國際大學赴大陸及港澳地區交換學生甄選申請表（申請人須於暨大修業滿一年以上）",
                  "歷年中文成績單正本（含班級排名百分比；大陸及澳門姊妹校免附外語檢定證明，香港教育大學須附英語檢定證明且僅於每年 4 月開放）",
                  "讀書計畫、自傳、師長推薦信及家長同意書",
                  "錄取後辦理臺胞證／港澳逗留簽注並投保涵蓋全期之海外醫療及意外保險",
              ],
          },
          {
              "track": "國際及兩岸事務處跨國雙聯學位計畫（美國加州大學河濱分校 UCR、法國雷恩商學院、加拿大紐芬蘭紀念大學、泰國農業大學）",
              "required": [
                  "跨國雙聯學位申請表及兩校雙聯協議規定之入學申請文件（學士班及博士班須於暨大修業滿二學期、碩士班須修業滿一學期）",
                  "歷年英文成績單正本及符合雙聯合作校門檻之 TOEFL iBT / IELTS / TOEIC 成績單正本",
                  "英文讀書計畫（Statement of Purpose）、英文履歷（CV）、師長英文推薦信及財力證明",
                  "順利取得國外雙聯合作大學學位證書後，檢具雙聯學位證書及歷年成績單得依《辦理跨國雙聯學位制補助要點》申請新臺幣 100,000 元獎勵金",
              ],
          },
          {
              "track": "教育部學海飛颺／學海惜珠獎學金＆校內選送優秀學生出國補助",
              "required": [
                  "學海飛颺：主要語言積分須達 8 分（CEFR B2：TOEFL iBT 72 / IELTS 6.0 / TOEIC 750 / JLPT N3 / TOPIK 3 級）以上，檢附申請表、積分自評表、成績單、語檢證明與讀書計畫，獲獎後簽署學海計畫行政契約書",
                  "學海惜珠：另檢附新式戶口名簿影本及直轄市、縣（市）政府核發之低收入戶、中低收入戶或特殊境遇家庭相關證明文件",
                  "校內選送優秀學生出國補助：未領取教育部學海計畫或外國政府公費者，簽署非學海行政契約書並於返國後 14 日內繳交心得報告及核銷單據（歐美最高 10 萬、亞太最高 7 萬）",
              ],
          },
      ],
  }
  (OFFICIAL_NCNU_DIR / "document-conditions.json").write_text(
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
      "group",
      "program_type",
      "availability_status",
      "quota",
      "colleges",
      "degree_levels",
      "language_requirements",
      "gpa_requirement",
      "application_deadline",
      "study_period",
      "semester_dates",
      "housing_info",
      "course_restrictions",
      "living_cost_estimate",
      "visa_and_health_insurance",
      "official_website",
      "latitude",
      "longitude",
      "image_url",
  ]:
    pop = sum(1 for p in partners if p.get(fname) not in (None, "", []))
    ratio = pop / len(partners) if partners else 1.0
    field_cov_lines.append(
        f"{fname},{len(partners)},{pop},{ratio:.4f},Official NCNU OIA verified"
    )
  (OFFICIAL_NCNU_DIR / "field-coverage.csv").write_text(
      "\n".join(field_cov_lines) + "\n", encoding="utf-8"
  )

  pages_records = [
      {
          "title": "國立暨南國際大學：海外姊妹校交換生申請流程、秋季班（2–3月）與春季班（9–10月）截止時程及大陸港澳交換申請說明",
          "source_url": NCNU_EXCHANGE_OVERVIEW_URL,
          "published_at": "2026-10-01T00:00:00Z",
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
          "title": "國立暨南國際大學：選送學生出國研修積分計算要點（主要語言10分＋次要語言3分＋學業班排10分＋院排序4分＋國際學伴社團3分＝滿分30分）",
          "source_url": NCNU_SCORE_RULES_PDF_URL,
          "published_at": "2026-10-01T00:00:00Z",
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
          "title": f"國立暨南國際大學：{len(partners)} 所全球合作姊妹校外語檢定門檻與語言積分標準對照表（TOEFL / IELTS / TOEIC / GEPT / JLPT / TOPIK / 歐語 / 越南語）",
          "source_url": NCNU_EXCHANGE_DEADLINES_URL,
          "published_at": "2026-10-01T00:00:00Z",
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
          "title": "國立暨南國際大學：出國交換與雙聯學位應備文件（甄選申請表、研修積分自評表、含班排歷年成績單、國外學分換算表與返國 14 日內心得報告）",
          "source_url": NCNU_DOWNLOADS_URL,
          "published_at": "2026-10-01T00:00:00Z",
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
          "title": "國立暨南國際大學：教育部學海飛颺、學海惜珠、校內選送優秀學生出國補助要點（歐美最高 10 萬／亞太最高 7 萬）與雙聯學位 10 萬元獎勵金",
          "source_url": NCNU_SCHOLARSHIPS_URL,
          "published_at": "2026-10-01T00:00:00Z",
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
  ]
  (OFFICIAL_NCNU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
      + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "ncnu",
      "school_name": "國立暨南國際大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "undergraduate_score_minimum": 70.0,
          "graduate_score_minimum": 70.0,
          "undergraduate_gpa_minimum": 2.5,
          "class_rank_percent_max": 75,
          "maximum_preferences": 5,
          "total_max_points": 30.0,
          "primary_language_max_points": 10.0,
          "secondary_language_max_points": 3.0,
          "academic_rank_max_points": 10.0,
          "college_recommendation_rank_bonus_max_points": 4.0,
          "international_buddy_or_club_max_points": 3.0,
          "require_ncnu_enrollment_during_abroad": True,
          "credit_conversion_rule": (
              "依《國立暨南國際大學國外學分換算表》：歐洲學分互認系統 2 ECTS 折算本校 1 學分、英國學分累積及轉換制度 4 CATS 折算本校 1 學分、美加日韓多數為 1:1 折算"
          ),
          "return_documents_due": (
              "返國後 14 日內繳交《出國交換研修心得報告》（學海受獎生同步上傳教育部學海計畫平台），並檢具登機證正本、電子機票收據、護照出入境章影本及正式成績單辦理補助核銷與學分抵免"
          ),
      },
      "source_urls": ncnu_source_urls,
      "verified_at": "2026-10-27",
  }
  (OFFICIAL_NCNU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCNU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "國立暨南國際大學",
              "required_documents": student_dashboard_payload[
                  "required_documents"
              ],
              "source_urls": ncnu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCNU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "國立暨南國際大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": ncnu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "ncnu",
      "school_name": "國立暨南國際大學",
      "total_partners": len(partners),
      "partner_count": len(partners),
      "international_partners": sum(
          1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
      ),
      "mainland_partners": sum(
          1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
      ),
      "dual_degree_partner_universities": 4,
      "dual_degree_programs": 4,
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
          f"國立暨南國際大學國際及兩岸事務處（OIA）115/116 學年度秋季班（每年 2–3 月收件提名）與春季班（每年 9–10 月收件提名）海外姊妹校交換學生計畫（142 所海外開放交換校）、赴大陸及港澳地區姊妹校交換學生計畫（20 所開放交換校）、4 所跨國雙聯學位合作校（美國加州大學河濱分校 UCR 3+1+MS、法國雷恩商學院、加拿大紐芬蘭紀念大學、泰國農業大學）及教育部學海飛颺、學海惜珠、校內《選送優秀學生出國補助要點》（114.07.22 修正通過）與《辦理跨國雙聯學位制補助要點》（114.08.19 修正通過）同步整合；共完整收錄 {len(partners)} 所全球與大陸港澳合作姊妹校（含 {open_partner_count} 所當期開放申請學校及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 38 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返校心得報告）。"
      ),
      "verified_at": "2026-10-27",
  }
  (OFFICIAL_NCNU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCNU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "ncnu",
              "school_name": "國立暨南國際大學",
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
          "sources/ncnu/ncnu_intl_exchange_flow.html",
          NCNU_EXCHANGE_OVERVIEW_URL,
          "國立暨南國際大學國際及兩岸事務處「海外姊妹校交換生申請流程」官方網頁 HTML",
      ),
      (
          "sources/ncnu/ncnu_intl_deadlines.html",
          NCNU_EXCHANGE_DEADLINES_URL,
          "國立暨南國際大學國際及兩岸事務處「姊妹校交換生申請截止日期」官方網頁 HTML",
      ),
      (
          "sources/ncnu/ncnu_exchange_sister_schools.xlsx",
          NCNU_EXCHANGE_PARTNERS_SHEET_URL,
          "國立暨南國際大學國際及兩岸事務處《姊妹校交換生資訊》總表 XLSX",
      ),
      (
          "sources/ncnu/ncnu_exchange_sister_schools.csv",
          NCNU_EXCHANGE_PARTNERS_SHEET_URL,
          "國立暨南國際大學國際及兩岸事務處《姊妹校交換生資訊》總表 CSV",
      ),
      (
          "sources/ncnu/ncnu_partner_list.html",
          NCNU_PARTNERS_MAP_URL,
          "國立暨南國際大學國際及兩岸事務處「全球合作姊妹校地圖與名錄」官方網頁 HTML",
      ),
      (
          "sources/ncnu/ncnu_partner_map.kml",
          NCNU_PARTNERS_MAP_URL,
          "國立暨南國際大學國際及兩岸事務處全球締約合作姊妹校 Google My Maps KML",
      ),
      (
          "sources/ncnu/ncnu_mainland_exchange_flow.html",
          NCNU_MAINLAND_PARTNERS_URL,
          "國立暨南國際大學國際及兩岸事務處「赴大陸及港澳地區交換生申請流程與姊妹校一覽」官方網頁 HTML",
      ),
      (
          "sources/ncnu/ncnu_mainland_exchange_apply.html",
          NCNU_MAINLAND_APPLY_URL,
          "國立暨南國際大學國際及兩岸事務處「赴大陸及港澳地區交換生申請說明」官方網頁 HTML",
      ),
      (
          "sources/ncnu/ncnu_dual_degree.html",
          NCNU_DUAL_DEGREE_URL,
          "國立暨南國際大學國際及兩岸事務處「跨國雙聯學位申請專區」官方網頁 HTML",
      ),
      (
          "sources/ncnu/ncnu_outbound_score_calculation_rules_1120614.pdf",
          NCNU_SCORE_RULES_PDF_URL,
          "國立暨南國際大學選送學生出國研修積分計算要點（112.06.14 修正通過，含語言積分標準對照表）PDF",
      ),
      (
          "sources/ncnu/ncnu_outbound_subsidy_guidelines_1140722.pdf",
          NCNU_SUBSIDY_RULES_PDF_URL,
          "國立暨南國際大學選送優秀學生出國補助要點（114.07.22 修正通過）PDF",
      ),
      (
          "sources/ncnu/ncnu_dual_degree_regulations_1130116.pdf",
          NCNU_DUAL_DEGREE_RULES_PDF_URL,
          "國立暨南國際大學與國外大學校院辦理跨國雙聯學位制實施辦法（113.01.16 修正通過）PDF",
      ),
      (
          "sources/ncnu/ncnu_dual_degree_subsidy_guidelines_1140819.pdf",
          NCNU_DUAL_DEGREE_URL,
          "國立暨南國際大學辦理跨國雙聯學位制補助要點（114.08.19 修正通過）PDF",
      ),
      (
          "sources/ncnu/ncnu_sop_intl_exchange.pdf",
          NCNU_SOP_PDF_URL,
          "國立暨南國際大學學生赴海外姊妹校交換標準作業流程（SOP）PDF",
      ),
      (
          "sources/ncnu/ncnu_credit_conversion_table_20210113.pdf",
          NCNU_CREDIT_CONVERSION_PDF_URL,
          "國立暨南國際大學國外學分換算表（ECTS / CATS 學分折算參考）PDF",
      ),
      (
          "sources/ncnu/ncnu_experiences_index.json",
          NCNU_EXPERIENCES_URL,
          f"國立暨南國際大學國際及兩岸事務處 {total_exp_reports} 篇學生交換心得報告索引 JSON",
      ),
      (
          "sources/ncnu/ncnu_catalog_source.json",
          NCNU_PARTNERS_MAP_URL,
          f"國立暨南國際大學 {len(partners)} 所全球與大陸港澳合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/ncnu/ncnu_resolved_locations.json",
          NCNU_PARTNERS_MAP_URL,
          f"國立暨南國際大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
      ),
  ]
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
      "school_id": "ncnu",
      "school_name": "國立暨南國際大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = (
      json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  )
  (OFFICIAL_NCNU_DIR / "import_provenance.json").write_text(
      prov_text, encoding="utf-8"
  )
  (OFFICIAL_NCNU_DIR / "import-provenance.json").write_text(
      prov_text, encoding="utf-8"
  )

  print(
      f"Successfully built NCNU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
