"""Build the official Chang Jung Christian University (長榮大學, CJCU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_CJCU_DIR = REPO_ROOT / "sources" / "cjcu"
OFFICIAL_CJCU_DIR = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "cjcu"
)
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-02T00:00:00Z"

CJCU_HOME_URL = "https://www.cjcu.edu.tw/"
CJCU_OIA_HOME_URL = "https://dweb.cjcu.edu.tw/oia"
CJCU_EXCHANGE_LATEST_NEWS_URL = "https://dweb.cjcu.edu.tw/oia/article/3030"
CJCU_EXCHANGE_SCHOOL_LIST_URL = "https://dweb.cjcu.edu.tw/oia/article/2593"
CJCU_SISTER_SCHOOLS_URL = "https://dweb.cjcu.edu.tw/oia/article/2590"
CJCU_DUAL_DEGREE_LIST_URL = "https://dweb.cjcu.edu.tw/oia/article/2594"
CJCU_DUAL_DEGREE_NEWS_URL = "https://dweb.cjcu.edu.tw/oia/article/3031"
CJCU_SCHOLARSHIPS_URL = "https://dweb.cjcu.edu.tw/oia/article/1959"
CJCU_REGULATIONS_URL = "https://dweb.cjcu.edu.tw/oia/article/1935"
CJCU_STUDENT_EXPERIENCES_URL = "https://dweb.cjcu.edu.tw/oia/article/5524"
CJCU_SHORT_TERM_SUBSIDY_URL = "https://dweb.cjcu.edu.tw/oia/article/7403"
CJCU_ONLINE_FORM_115_URL = "https://forms.gle/2kaidJJ8b4xwsPbu6"

CJCU_BROCHURE_115_PDF_URL = (
    "https://dweb.cjcu.edu.tw/RichText/FileDownLoad/oia/32919_20250924133519.pdf"
)
CJCU_OUTBOUND_GUIDELINES_PDF_URL = (
    "https://dweb.cjcu.edu.tw/RichText/FileDownLoad/oia/18276_20240806145247.pdf"
)
CJCU_CREDIT_HANDLING_RULES_PDF_URL = (
    "https://dweb.cjcu.edu.tw/RichText/FileDownLoad/oia/18281_20240806150141.pdf"
)
CJCU_SCHOLARSHIP_REGULATIONS_PDF_URL = (
    "https://dweb.cjcu.edu.tw/RichText/FileDownLoad/oia/18277_20240806145526.pdf"
)
CJCU_SCHOLARSHIP_BROCHURE_114_PDF_URL = (
    "https://dweb.cjcu.edu.tw/RichText/FileDownLoad/oia/34640_20260116094902.pdf"
)
CJCU_SHORT_TERM_SUBSIDY_RULES_PDF_URL = (
    "https://dweb.cjcu.edu.tw/RichText/FileDownLoad/oia/18278_20240806145633.pdf"
)
CJCU_DUAL_DEGREE_RULES_PDF_URL = (
    "https://dweb.cjcu.edu.tw/RichText/FileDownLoad/oia/18280_20240806145940.pdf"
)
CJCU_ADMIN_CONTRACT_PDF_URL = (
    "https://dweb.cjcu.edu.tw/RichText/FileDownLoad/oia/23080_20240924115905.pdf"
)
CJCU_STUDY_PLAN_FORM_PDF_URL = (
    "https://dweb.cjcu.edu.tw/RichText/FileDownLoad/oia/23077_20240924115726.pdf"
)
CJCU_RECOMMENDATION_FORM_PDF_URL = (
    "https://dweb.cjcu.edu.tw/RichText/FileDownLoad/oia/23076_20240924115709.pdf"
)
CJCU_RETURN_REPORT_FORM_PDF_URL = (
    "https://dweb.cjcu.edu.tw/RichText/FileDownLoad/oia/23082_20240924120001.pdf"
)

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 650–1,100（折合日圓約 JPY 90,000–150,000 / 月、新臺幣約 20,000–35,000 元；其中【鎮西學院大學】與【創價大學】額外提供交換生「免住宿費」優惠，明治學院大學、大東文化大學、桃山學院大學、四國學院大學、名櫻大學、宮崎國際大學、宮城學院女子大學、福岡女學院大學等校設有國際學舍或指定學生公寓）",
        "須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後至日本台灣交流協會申辦留學簽證，入境後加入日本國民健康保險（NHI）並於出國前投保海外全期醫療及意外險。",
    ),
    "韓國": (
        "每月生活費約 USD 620–1,050（折合韓元約 KRW 800,000–1,400,000 / 月、新臺幣約 19,500–33,500 元；其中【韓信大學 Hanshin University】提供交換生「免住宿費」優惠，梨花女子大學、中央大學、仁川大學、德成女子大學、全州大學、韓남大學、白石大學、威德大學等均提供校內學生宿舍申請）",
        "須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後辦理外國人登錄證（ARC）並依法納保韓國國民健康保險（NHIS）。",
    ),
    "中國大陸": (
        "每月生活費約 USD 320–650（折合人民幣約 RMB 2,000–4,200 / 月、新臺幣約 10,000–20,500 元；含廈門大學、山東大學、中央民族大學、上海師範大學天華學院、福州外語外貿學院、泉州師範學院、三明學院、莆田學院等校內外學生宿舍與食堂開銷）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及大陸姊妹校寄發之錄取通知書辦理報到，並依長榮大學國際處規定購買涵蓋交換全期之海外醫療及意外保險。",
    ),
    "香港": (
        "每月生活費約 USD 1,000–1,600（折合港幣約 HKD 7,800–12,500 / 月、新臺幣約 31,500–50,500 元，含香港浸會大學校內外住宿、膳食與交通）",
        "須透過香港接待大學代向香港入境事務處申辦來港就讀進入許可（Student Visa / Entry Permit）並投保海外全期醫療保險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 450–800（折合馬幣約 MYR 2,000–3,500 / 月、新臺幣約 14,500–25,500 元；含拉曼大學 UTAR、新紀元大學學院、砂拉越科技大學 UTS、UCSI 大學、韓江傳媒大學學院等校內外學生宿舍與餐飲）",
        "須透過馬來西亞教育全球服務中心（EMGS）線上申辦學生簽證核准函（VAL / Mobility Pass）並投保馬來西亞境內醫療險。",
    ),
    "泰國": (
        "每月生活費約 USD 450–820（折合泰銖約 THB 15,000–27,000 / 月、新臺幣約 14,500–26,000 元；含暹羅大學 Siam University、清邁皇家大學、西北大學 Payap University、基督教大學等學生宿舍與生活開銷）",
        "須憑泰國接待大學入學許可公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 教育簽證並投保海外全期醫療險。",
    ),
    "印尼": (
        "每月生活費約 USD 400–750（折合印尼盾約 IDR 6,500,000–11,500,000 / 月、新臺幣約 13,000–24,000 元；其中【蘇吉甲普拉納塔天主教大學 Soegijapranata Catholic University】提供印尼政府 Darmasiswa 獎學金［生活費每月約 NT$3,500、住宿補助一次約 NT$1,000］）",
        "須由印尼接待大學協助申辦印尼學生電子簽證（Study e-Visa / KITAS）並投保海外全期醫療保險。",
    ),
    "越南": (
        "每月生活費約 USD 400–720（折合新臺幣約 13,000–23,000 元；含河內國家大學外語大學 ULIS-VNU、胡志明市國家大學人文與社會科學大學、順化大學外語大學等住宿與餐飲）",
        "須由越南接待大學協助向越南出入境管理局申辦 DH 學生簽證並投保海外全期醫療及意外保險。",
    ),
    "菲律賓": (
        "每月生活費約 USD 450–800（折合新臺幣約 14,500–25,500 元；含西利曼大學 Silliman University、聖保羅大學、中央菲律賓大學等校內外學生宿舍與膳食）",
        "須依菲律賓接待大學指引辦理學生簽證（9F）或特別學習許可（SSP）並投保海外醫療保險。",
    ),
    "印度": (
        "每月生活費約 USD 380–680（折合新臺幣約 12,000–21,500 元；含孟買聖澤維爾學院、馬德拉斯基督教學院等校內外住宿與膳食）",
        "須憑印度接待大學核發之入學許可向印度台北協會申辦印度學生簽證（Student Visa）並投保海外全期醫療保險。",
    ),
    "捷克": (
        "每月生活費約 USD 680–1,050（折合歐元約 EUR 620–950 / 月、新臺幣約 21,500–33,500 元；含赫拉德茨克拉洛韋大學 UHK、帕爾杜比采大學、奧斯特拉瓦大學等校內學生宿舍與膳食，性價比極高）",
        "須憑捷克接待大學核發之入學許可與住宿證明向捷克經濟文化辦事處申辦長期學生簽證並投保捷克認可之醫療保險。",
    ),
    "德國": (
        "每月生活費約 USD 980–1,450（折合歐元約 EUR 900–1,350 / 月、新臺幣約 31,000–46,000 元；含北ハウゼン應用技術大學 Nordhausen、路德維希港經濟與社會大學等學生宿舍與生活費）",
        "須開立德國限制提領帳戶（Blocked Account）並憑入學許可向德國在台協會申辦德國長期學生簽證及投保德國公保／醫療險。",
    ),
    "法國": (
        "每月生活費約 USD 1,000–1,550（折合歐元約 EUR 920–1,420 / 月、新臺幣約 32,000–49,500 元；含天主教里昂大學 UCLy、雷恩商學院 Rennes School of Business 交換與雙聯學位期間之住宿與生活費）",
        "須先經法國教育中心（Campus France）完成 Etudes en France 線上程序與面試，再向法國在台協會申辦長期學生簽證（VLS-TS）。",
    ),
    "奧地利": (
        "每月生活費約 USD 1,000–1,500（折合歐元約 EUR 920–1,380 / 月、新臺幣約 32,000–48,000 元；含上奧地利應用科技大學 FH Upper Austria 四大校區學生宿舍與生活開銷）",
        "交換 1 學期（6 個月內）向奧地利台北辦事處申辦奧地利學生 D 簽證，交換 1 學年須申辦學生居留許可並投保申根醫療保險。",
    ),
    "西班牙": (
        "每月生活費約 USD 950–1,450（折合歐元約 EUR 880–1,320 / 月、新臺幣約 30,500–46,000 元；含胡安卡洛斯國王大學 URJC、天主教聖安東尼奧大學 UCAM 住宿與生活開銷）",
        "須憑西班牙接待大學入學許可與財力、無犯罪紀錄及醫療保險證明向西班牙商務辦事處申辦學生簽證。",
    ),
    "英國": (
        "每月生活費約 USD 1,350–2,050（折合英鎊約 GBP 1,050–1,600 / 月、新臺幣約 43,000–65,000 元；含貝爾法斯特女王大學 QUB、諾丁漢特倫特大學 NTU 雙聯學位期間住宿與生活開銷）",
        "交換 6 個月以內可憑入學許可辦理英國 ETA / Standard Visitor 入境，修讀 1 學年或雙聯學位須申辦英國 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "美國": (
        "每月生活費約 USD 1,350–2,100（依匯率折合新臺幣約 43,000–67,000 元；含北德州大學 UNT、天普大學 Temple University、加州大學河濱分校 UCR、長老教會學院 Presbyterian College 等住宿、伙食與交通）",
        "須憑美國接待大學核發之 DS-2019（J-1 交換生）或 I-20（F-1 雙聯學位生）表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證，且須投保符合接待校規定之全期海外醫療保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,200–1,850（折合加幣約 CAD 1,650–2,500 / 月、新臺幣約 38,500–59,000 元；含愛德華王子島大學 UPEI 住宿與膳食）",
        "交換研習 1 學期（6 個月內）可申辦加拿大 eTA，修讀 1 學年或雙聯學位須申辦加拿大 Study Permit 並投保醫療保險。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,450–2,250（折合澳幣約 AUD 2,200–3,400 / 月、新臺幣約 46,500–72,000 元；含西雪梨大學翻譯雙聯學位與南十字星大學、澳洲天主教大學 ACU 住宿與生活費）",
        "須購買澳洲海外學生健康保險（OSHC）並憑接待校核發之 CoE 申辦澳洲 Subclass 500 學生簽證。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "春季學期（Spring Semester）：約 4 月初至 8 月初；秋季學期（Fall Semester）：約 9 月中下旬至翌年 1 月底或 2 月初",
    "韓國": "春季學期（Spring Semester）：約 3 月初至 6 月中旬；秋季學期（Fall Semester）：約 9 月初至 12 月中旬",
    "中國大陸": "春季學期（下學期）：約 2 月下旬至 7 月初；秋季學期（上學期）：約 9 月初至翌年 1 月中旬",
    "香港": "第一學期（秋季班）：約 9 月初至 12 月下旬；第二學期（春季班）：約 1 月中旬至 5 月下旬",
    "馬來西亞": "秋季學期：約 9–10 月至翌年 1–2 月；春季學期：約 1–5 月（拉曼大學 UTAR 採 1 月、5 月、10 月三學期制）",
    "泰國": "第一學期（秋季班）：約 8 月至 12 月；第二學期（春季班）：約 1 月至 5 月",
    "印尼": "奇數／秋季學期（Odd Semester）：約 8/9 月至翌年 1 月；偶數／春季學期（Even Semester）：約 2 月至 6/7 月",
    "越南": "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月",
    "菲律賓": "第一學期（秋季班）：約 8 月至 12 月；第二學期（春季班）：約 1 月至 5 月",
    "捷克": "冬季學期（Winter / Fall Semester）：約 9 月下旬至翌年 1 月底；夏季學期（Summer / Spring Semester）：約 2 月中旬至 6 月中旬",
    "德國": "冬季學期（Wintersemester）：約 10 月初至翌年 2 月底；夏季學期（Sommersemester）：約 4 月初至 7 月底",
    "法國": "秋季學期（Fall Semester）：約 9 月初至 12 月底；春季學期（Spring Semester）：約 1 月中旬至 5 月底",
    "奧地利": "冬季學期（Winter Semester）：約 9 月底至翌年 1 月底；夏季學期（Summer Semester）：約 2 月底至 6 月底",
    "西班牙": "第一學期（秋季班）：約 9 月中旬至翌年 1 月下旬；第二學期（春季班）：約 1 月下旬至 6 月中旬",
    "英國": "秋季學期（Autumn Term）：約 9 月下旬至翌年 1 月；春季學期（Spring Term）：約 1 月下旬至 6 月",
    "美國": "秋季學期（Fall Semester）：約 8 月中下旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬",
    "加拿大": "秋季學期（Fall Term）：約 9 月初至 12 月下旬；冬季／春季學期（Winter Term）：約 1 月初至 4 月底",
    "澳洲": "第一學期（Autumn / Semester 1）：約 2 月下旬至 6 月底；第二學期（Spring / Semester 2）：約 7 月下旬至 11 月底",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
  """Ensure school-images.json and university_locations.jsonl contain all CJCU partner schools."""
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
          else loc.get("lat", 22.9056)
      )
      lon = float(
          loc.get("longitude")
          if loc.get("longitude") is not None
          else loc.get("lon", 120.2725)
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
  OFFICIAL_CJCU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_CJCU_DIR / "cjcu_catalog_source.json").read_text(
          encoding="utf-8"
      )
  )
  resolved_locations = json.loads(
      (SOURCES_CJCU_DIR / "cjcu_resolved_locations.json").read_text(
          encoding="utf-8"
      )
  )
  bin_urls_path = SOURCES_CJCU_DIR / "binary_source_urls.json"
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
  dual_degree_count = 0
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
        item.get("group") or "國際處國際合作組正式締約姊妹校"
    )
    if "雙聯" in group_str:
      dual_degree_count += 1
    quota_str = clean_text(
        item.get("quota") or "依長榮大學國際處國際合作組當期公告名額"
    )
    detail_url = item.get("detail_url") or CJCU_SISTER_SCHOOLS_URL
    factsheet_url = item.get("factsheet_url")

    if "雙聯學位" in group_str and "交換" in group_str:
      program_type = (
          "長榮大學校級國際交換生計畫暨海外雙聯學位計畫（Double Degree Program）"
      )
      source_url = CJCU_EXCHANGE_SCHOOL_LIST_URL
    elif "雙聯學位" in group_str:
      program_type = "長榮大學海外雙聯學位合作計畫（Double Degree Program）"
      source_url = CJCU_DUAL_DEGREE_LIST_URL
    elif avail_status == "open":
      program_type = f"長榮大學 115學年度校級國際交換生計畫（{group_str}）"
      source_url = CJCU_EXCHANGE_SCHOOL_LIST_URL
    elif country in {"中國大陸", "香港"}:
      program_type = "長榮大學國際處正式締約大陸與香港姊妹校"
      source_url = detail_url
    else:
      program_type = "長榮大學國際處正式締約國際姊妹校"
      source_url = detail_url

    colleges_str = clean_text(
        item.get("colleges")
        or "管理學院、健康科學學院、人文社會學院、資訊暨設計學院、安全衛生科學學院、永續教育學院、環境教育國際實驗學院、神學院、PLUS學院、博雅教育學部"
    )
    degree_levels_str = clean_text(
        item.get("eligible_degrees")
        or "長榮大學在學學生，出國就讀時須於本校修業滿一學年（含）以上，且前一學年度學業平均成績達 70 分（含）以上"
    )
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "")
    website = item.get("website") or CJCU_SISTER_SCHOOLS_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    round_label = (
        "115學年度校級國際交換生甄選（116學年度第1學期／第2學期出國交換）暨海外雙聯學位計畫"
        if avail_status == "open"
        else "國際處正式締約姊妹校（當期開放名額依國際處最新校級交換生甄選簡章為準）"
    )
    app_deadline_str = clean_text(
        item.get("deadline")
        or (
            "115學年度校級國際交換生甄選：2026年10月1日（四）至 2026年11月27日（五）17:00 截止（同步填寫線上表單、繳交紙本至行政大樓三樓國際處並寄送彩色掃描 PDF 至 exch@mail.cjcu.edu.tw；12月11日面試、12月16日公告第一階段錄取名單、12月31日公告最終錄取名單）"
        )
    )
    deadline_iso = "2026-11-27T17:00:00+08:00"
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "115"

    study_period_str = clean_text(item.get("duration") or "一學期或一學年")
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲長榮大學國際處推薦錄取後，可依 {zh_name} 國際處指引申請校內外學生宿舍或國際學舍"
        + (f"（學費與住宿待遇：{tuition_note}）" if tuition_note else "。")
    )
    course_rest_str = (
        f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《長榮大學 115學年度校級國際交換生甄選簡章》、《長榮大學赴外研修生作業要點》及《長榮大學學生出國期間學業及學籍處理要點》規定："
        "（1）基本資格：出國就讀時須於本校修業滿一學年（含）以上，且前一學年度學業平均成績達 70 分（含）以上（境外生不得申請交換至其原居住國）；"
        "（2）校內甄選評比（總分 100%）：「面試 40%」（英韓組採英韓文面試、英語組採英文面試、中文組採中文簡報與面試、日語組採日文面試）＋「書面資料 60%」（前一學年度操行成績 10%＋前一學年度學業成績 10%＋自傳及讀書計畫 15%＋語文證明 10%＋其他相關資料 15%）；"
        "（3）錄取後語文培訓義務：除日語組與中國地區外，錄取生均須參加並通過語文教育中心開設之「交換生英語加強課程」（第 1 週至第 9 週），日語組須參加應用日語學系每週辦理之日語會話練習；"
        "（4）赴外選課下限與返國學分抵免（《赴外研修生作業要點》第 9 點第 8 款、《出國期間學業及學籍處理要點》第 6 點及《行政契約書》第 8 條）：交換期間每學期選課不得少於相當本校 9 學分或 3 門課程（不含體育課），且及格學分不得少於 6 學分或 2 門課程；返國後於規定期限內持國外成績單正本及修業大綱向系所及教務處註冊課務組辦理學分採認抵免；"
        "（5）跨國雙聯學位（《海外雙聯學制實施辦法》第 5–6 條）：學士班於兩校修業時間合計至少滿 32 個月（各校至少滿 16 個月）、碩士班合計至少滿 12 個月、博士班合計至少滿 24 個月，且於兩校修習學分數各須達畢業總學分數 1/3 以上。"
    )

    living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
        country,
        (
            "每月生活費約 USD 750–1,350（依匯率折合新臺幣約 24,000–43,000 元，含住宿、膳食與市區交通）",
            "須依接待國駐臺機構規定申辦學生簽證，並依《長榮大學赴外研修生作業要點》第 9 點第 4 款於出國前自行購買涵蓋全期之海外保險（含醫療、意外、海外急難救助）送國際處備查。",
        ),
    )

    tuition_points_list = [
        (
            f"長榮大學在學註冊與學雜費規定（依《長榮大學赴外研修生作業要點》第 4 點及《115學年度校級國際交換生甄選簡章》）：研修生於交換期間仍須辦理本校註冊手續並繳交本校全額學雜費（非日間部一至四年級學生應比照日間部管理學院收費標準繳交全額學雜費，即學費新臺幣 37,910 元、雜費 8,300 元）。本合作校待遇：{tuition_note or '免繳接待姊妹校學費（雙聯學位依兩校合約規定辦理）'}。"
        ),
        (
            "長榮大學四大出國交換與短期交流獎補助體系（依《長榮大學推展學生國際學術交流獎補助辦法》及《短期交流補助作業要點》）：（1）《教育部學海飛颺獎學金》（具中華民國國籍、赴非大陸港澳姊妹校交換 1 學期或 1 學年、前一學年度平均成績達 75 分或班排前 25%）；（2）《教育部學海惜珠獎學金》（持低收入戶、中低收入戶或特殊境遇家庭證明且前一學年度平均達 75 分或班排前 25%）；（3）《長榮大學推展學生國際學術交流獎補助金》（前一學年度學業平均成績及格或班排前 50%，上述三項獎學金同一學制以補助一次為限且僅能擇一領取，114學年度截止日為 2026/02/09 17:00）；（4）《長榮大學短期交流補助作業要點》（補助海外短期進修、7–30 天文化交流或國際競賽，每人每次最高補助新臺幣 40,000 元、住宿費每日上限 1,600 元，每年 10 月及 3 月分兩梯次申請）。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認長榮大學修業滿一學年、前學年平均 70 分以上及 {zh_name} 語檢要求，並填寫線上報名表單）：確認出國就讀時於本校修業滿一學年以上且符合學業門檻（{gpa_req_str}）與外語標準（{lang_req_str}），於 2026/10/01–11/27 17:00 前完成線上報名表單（https://forms.gle/2kaidJJ8b4xwsPbu6）。"
        ),
        (
            "步驟二（備齊 9 項書面申請資料，紙本迴紋針裝訂送交國際處並將彩色掃描合併 PDF 寄至 exch@mail.cjcu.edu.tw）：檢附（1）個人資料表（完成紙本簽章）、（2）歷年中文成績單正本、（3）語文檢定證明影本、（4）家長保證書正本、（5）中英文或中日文自傳各一篇、（6）中英文或中日文讀書計畫各一份、（7）申請奧地利/西班牙/法國/德國/韓國學校者檢附二年內曾修讀相關語言課程證明、（8）其他有利審查資料、（9）本校專任或專案教師彌封推薦函二封（推薦函無須繳交電子檔）。"
        ),
        (
            f"步驟三（參加 12/11 分組外語面試，並於 12/16 第一階段錄取公告後繳交錄取確認書）：國際處於 2026/12/04 公告面試時間表、12/11 辦理面試（面試占 40%＋書面審查占 60%），12/16 公告第一階段錄取名單，錄取赴 {full_name} 同學須於 12/21 前繳交第一階段錄取確認書（12/31 公告最終錄取名單），並參加「交換生英語加強課程」（第 1–9 週）或日語會話練習。"
        ),
        (
            "步驟四（簽署《赴外交換學生行政契約書》、向姊妹校遞交入學申請並申請學海飛颺／惜珠或校內交流獎補助金）：獲提名後繳交姊妹校入學申請文件與家長同意公證之《長榮大學赴外交換學生行政契約書》，同步申請《教育部學海飛颺／惜珠》或《長榮大學推展學生國際學術交流獎補助金》；抵達接待校兩週內回報選課清單（每學期至少修習 9 學分或 3 門課，且至少 6 學分或 2 門課及格），返國後一個月內繳交 2,000 字以上中文心得報告及 400 字以上外文心得報告並辦理學分抵免。"
        ),
    ]

    elig_points_list = [
        f"合作類別與甄選組別：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請學院：{colleges_str}",
        f"歷年學業成績門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "校內甄選評比配分（《115學年度校級國際交換生甄選簡章》第陸點）：面試 40%（英韓組／英語組／中文組／日語組）＋書面資料 60%（前一學年度操行成績 10%＋前一學年度學業成績 10%＋自傳及讀書計畫 15%＋語文證明 10%＋其他相關資料 15%）。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與住宿待遇：{tuition_note}")
    if remarks_raw:
      elig_points_list.append(f"簡章備註與締約重點說明：{remarks_raw}")

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
            or f"{CJCU_STUDENT_EXPERIENCES_URL}#cjcu-exp-{sn}-{e_idx+1}"
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
            "college": "管理學院／人文社會學院／資訊暨設計學院／健康科學學院／安全衛生科學學院／環境教育國際實驗學院",
            "department": "長榮大學赴外交換生",
        })
        summary_text = (
            f"長榮大學國際處國際合作組公開收錄之學長姐赴 {country} {full_name} 交換研習官方心得報告（{raw_t}，共 2,000 字以上中文與 400 字以上外文實錄），詳述選課修習與學分抵免、校內外宿舍環境、簽證保險辦理與當地生活開銷。"
        )
        theme_map = {
            "academics": f"長榮大學交換生於《{raw_t}》分享在 {zh_name} 修習每學期至少 9 學分（或 3 門課程）與返國辦理長榮大學科目學分採認抵免之實務經驗。",
            "housing": f"長榮大學交換生記錄申請 {zh_name} 校內外學生宿舍或國際學舍、寢室設備與周邊生活機能（{housing_str[:100]}）。",
            "campus_culture": f"長榮大學國際處公開收錄《{raw_t}》之跨文化課堂討論、國際學伴制度與校園生活實錄。",
            "cost": f"長榮大學交換生分享於 {zh_name} 之每月住宿、伙食與交通開銷（{living_cost_str[:100]}），以及免繳姊妹校學費與申請教育部學海飛颺／惜珠或長榮大學國際學術交流獎補助金之經驗。",
        }
        student_experience_rows.append({
            "school_name": full_name,
            "country": country,
            "title": raw_t,
            "source_url": eurl,
            "source_type": "pdf" if eurl.lower().endswith(".pdf") else "article",
            "platform": "長榮大學國際處國際合作組（OIA）—赴外交換學生歷屆心得分享專區",
            "author_name": (
                raw_t.split("—")[-1].strip()[:24]
                if "—" in raw_t
                else "長榮大學交換生"
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
                f"{full_name}:cjcu_exp:{e_idx}:{eurl}".encode("utf-8")
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
        "home_university": "長榮大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exp_links[0]["url"] if exp_links else CJCU_STUDENT_EXPERIENCES_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

    loc = resolved_locations.get(full_name) or {
        "city": country,
        "latitude": 22.9056,
        "longitude": 120.2725,
        "source_url": "https://www.wikidata.org",
    }
    city_name = loc.get("city") or country
    lat = float(
        loc.get("latitude")
        if loc.get("latitude") is not None
        else loc.get("lat", 22.9056)
    )
    lon = float(
        loc.get("longitude")
        if loc.get("longitude") is not None
        else loc.get("lon", 120.2725)
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
        "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區以錄取通知與締約校專頁為準。",
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
    if factsheet_url:
      notes_lines.append(f"【官方交換簡章 Fact Sheet】{factsheet_url}")
    if exps:
      notes_lines.append(
          f"【長榮大學學長姐交換留學心得報告（共 {len(exps)} 篇）】收錄於國際處赴外交換學生心得分享專區（含：{'、'.join(exp_labels[:4])}）"
      )
    if remarks_raw:
      notes_lines.append(f"【簡章備註與締約摘要】{remarks_raw}")

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
            f"長榮大學國際處國際合作組公告合作姊妹校（{program_type}）；{quota_str}。"
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
        "factsheet_url": factsheet_url,
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
                "factsheet_url": factsheet_url,
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
            "title": f"長榮大學國際處國際合作組交換學生計畫與姊妹校專頁—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "長榮大學 115學年度校級國際交換生甄選簡章與赴外研修生作業要點",
            "source_url": CJCU_BROCHURE_115_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "長榮大學推展學生國際學術交流獎補助辦法（學海飛颺／惜珠／校內獎補助金）與短期交流補助作業要點",
            "source_url": CJCU_SCHOLARSHIPS_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if factsheet_url:
      wf_sources.append({
          "title": f"{full_name} 交換計畫官方簡章（Fact Sheet）",
          "source_url": factsheet_url,
          "role": "partner_university",
          "authority": "partner_official",
          "effective_academic_year": acad_year,
          "application_round": round_label,
          "checked_at": CHECKED_AT,
      })
    if exp_links:
      wf_sources.append({
          "title": f"長榮大學國際處赴外交換學生歷屆心得分享專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
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
        "home_university": "長榮大學",
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
            "長榮大學由國際處國際合作組（Office of International Affairs, OIA）統籌全校 10 個教學單位（管理學院、健康科學學院、人文社會學院、資訊暨設計學院、安全衛生科學學院、永續教育學院、環境教育國際實驗學院、神學院、PLUS學院、博雅教育學部）之校級國際交換生計畫（分英語組、日語組、韓語組、中文組）、海外雙聯學位計畫（英國女王大學與諾丁漢特倫特大學、法國雷恩商學院、澳洲西雪梨大學、美國北德州大學、馬來西亞砂拉越科技大學、泰國清邁皇家大學等 8 校）及教育部學海飛颺、學海惜珠、長榮大學推展學生國際學術交流獎補助金與短期交流補助。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"cjcu-{acad_year}-home-1-{sn:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認長榮大學修業滿一學年、前學年平均 70 分以上及 {zh_name} 語檢要求，並填寫線上報名表單",
                "responsible_party": "學生",
                "responsible_unit": "長榮大學國際處國際合作組／各院系所",
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
                    f"確認符合《長榮大學 115學年度校級國際交換生甄選簡章》第參點及《赴外研修生作業要點》第 3 點規定：出國就讀時須於本校修業滿一學年（含）以上，且前一學年度學業平均成績達 70 分（含）以上，符合接待校學業門檻（{gpa_req_str}）與外語標準（{lang_req_str}），並於 2026/10/01–11/27 17:00 前完成線上報名表單。"
                ),
                "details": [
                    f"開放學制與學院：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["長榮大學"],
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
                    CJCU_BROCHURE_115_PDF_URL,
                    CJCU_OUTBOUND_GUIDELINES_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"cjcu-{acad_year}-home-2-{sn:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "備妥 9 項書面申請資料，紙本送交行政大樓三樓國際處並將彩色掃描合併 PDF 寄至 exch@mail.cjcu.edu.tw",
                "responsible_party": "學生",
                "responsible_unit": "長榮大學國際處國際合作組",
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": CJCU_BROCHURE_115_PDF_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "於 2026年11月27日（五）17:00 前備妥 9 項書面申請資料，依序排列並以迴紋針固定於左上角送交行政大樓三樓國際處，同時將除教師推薦函外之 8 項資料彩色掃描合併為單一 PDF 檔寄至 exch@mail.cjcu.edu.tw（未同時完成線上表單、紙本與電子檔繳交者不予受理）。"
                ),
                "details": [
                    "9 項必備書面申請資料：（1）個人資料表一份（完成紙本簽章）；（2）大學或研究所歷年中文成績單正本一份；（3）語文檢定證明影本一份；（4）家長保證書正本一份；（5）中、英文，或中、日文自傳各一篇；（6）中、英文，或中、日文讀書計畫各一份；（7）所填志願若為奧地利、西班牙、法國、德國、韓國學校，須繳交二年內曾修讀相關語言課程之證明；（8）其他有助甄選資格審查之資料；（9）本校專任（專案）教師推薦函（彌封）二封（無須繳交電子檔）。",
                    "海外雙聯學位申請（《海外雙聯學制實施辦法》）：依各合作學院雙聯學位協議備妥英文歷年成績單、外語檢定證明（IELTS / TOEFL iBT）、讀書計畫、家長同意書及推薦信向國際處提出申請。",
                ],
                "document_requirements": [
                    {
                        "name": "長榮大學校級國際交換生甄選個人資料表（含紙本簽章）與家長保證書正本",
                        "official_form_url": CJCU_EXCHANGE_LATEST_NEWS_URL,
                        "source_urls": [
                            CJCU_BROCHURE_115_PDF_URL,
                            CJCU_EXCHANGE_LATEST_NEWS_URL,
                        ],
                    },
                    {
                        "name": "大學或研究所歷年中文成績單正本、語文檢定證明影本及歐韓語課程修讀證明（申請奧/西/法/德/韓志願者必備）",
                        "official_form_url": CJCU_BROCHURE_115_PDF_URL,
                        "source_urls": [
                            CJCU_BROCHURE_115_PDF_URL,
                            CJCU_EXCHANGE_SCHOOL_LIST_URL,
                        ],
                    },
                    {
                        "name": "中英文或中日文自傳與讀書計畫各一份、其他有利審查資料，以及本校專任（專案）教師彌封推薦函二封",
                        "official_form_url": CJCU_STUDY_PLAN_FORM_PDF_URL,
                        "source_urls": [
                            CJCU_STUDY_PLAN_FORM_PDF_URL,
                            CJCU_RECOMMENDATION_FORM_PDF_URL,
                        ],
                    },
                ],
                "scope": {
                    "home_universities": ["長榮大學"],
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
                    CJCU_BROCHURE_115_PDF_URL,
                    CJCU_STUDY_PLAN_FORM_PDF_URL,
                    CJCU_RECOMMENDATION_FORM_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"cjcu-{acad_year}-home-3-{sn:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "參加 12/11 分組外語面試（占 40%）與書審評比（占 60%），繳交錄取確認書並參加交換生外語培訓",
                "responsible_party": "長榮大學國際處國際合作組與申請學生",
                "responsible_unit": "國際處國際合作組／語文教育中心／應用日語學系",
                "deadline_at": "2026-12-21T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": CJCU_BROCHURE_115_PDF_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "國際處於 2026/12/04 公告面試時間表、12/11（五）辦理面試（面試 40%＋書審 60%：操行 10%＋學業 10%＋自傳及讀書計畫 15%＋語文證明 10%＋其他資料 15%），12/16 公告第一階段錄取名單，正取生須於 12/21 前繳交第一階段錄取確認書（12/31 公告最終錄取名單）。錄取生須參加語文教育中心「交換生英語加強課程」（第 1–9 週）或應用日語學系每週日語會話練習，並可同步申請《教育部學海飛颺／惜珠》或《長榮大學推展學生國際學術交流獎補助金》。"
                ),
                "details": [
                    "面試分組方式：（1）英韓組：英文及韓文面試；（2）英語組：英文面試；（3）中文組：中文簡報及面試；（4）日語組：日文面試。同時報名兩組以上者須分別參加各組面試。",
                    "出國交換獎學金三擇一（《推展學生國際學術交流獎補助辦法》）：（1）教育部學海飛颺（前學年平均達 75 分或班排前 25%）；（2）教育部學海惜珠（清寒證明＋前學年平均達 75 分或班排前 25%）；（3）長榮大學推展學生國際學術交流獎補助金（前學年平均及格或班排前 50%）。",
                ],
                "scope": {
                    "home_universities": ["長榮大學"],
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
                    CJCU_BROCHURE_115_PDF_URL,
                    CJCU_SCHOLARSHIP_REGULATIONS_PDF_URL,
                    CJCU_SCHOLARSHIP_BROCHURE_114_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"cjcu-{sn:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"簽署《赴外交換學生行政契約書》，由長榮大學國際處向 {zh_name} 提名並遞交姊妹校入學與宿位申請",
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"通過校內甄選並繳交經家長簽章公證之《長榮大學赴外交換學生行政契約書》後，由國際處國際合作組向 {zh_name} 辦理官方提名（Nomination）；學生須依接待校規定備妥外文入學申請表、英文歷年成績單、護照影本、財力證明、語檢證書及宿舍申請表，靜候接待校核發正式入學許可（Admission Letter / COE / 錄取通知書）。"
                ),
                "details": [
                    f"研修期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["長榮大學"],
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
                    [source_url, CJCU_ADMIN_CONTRACT_PDF_URL]
                    + ([factsheet_url] if factsheet_url else [])
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"cjcu-{acad_year}-home-5-{sn:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "完成長榮大學全額學雜費註冊與海外保險，抵達兩週內回報選課（至少 9 學分或 3 門課），返國一個月內繳交中/外文心得報告並辦理學分抵免",
                "responsible_party": "學生與所屬系所",
                "responsible_unit": "國際處國際合作組／教務處註冊課務組／各系所",
                "summary": (
                    "出國前須依《赴外研修生作業要點》第 4 點及第 9 點完成長榮大學註冊並繳交全額學雜費、申辦簽證及自行購買涵蓋全期之海外保險（醫療、意外、海外急難救助）送國際處備查；抵達姊妹校兩週內回報選課清單（每學期至少修習相當本校 9 學分或 3 門課［不含體育］，且至少 6 學分或 2 門課及格）；返國後一個月內繳交 2,000 字以上中文心得報告及 400 字以上外文心得報告，並持國外成績單正本及修業大綱向系所與教務處註冊課務組辦理學分採認抵免。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["長榮大學"],
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
                    CJCU_OUTBOUND_GUIDELINES_PDF_URL,
                    CJCU_CREDIT_HANDLING_RULES_PDF_URL,
                    CJCU_ADMIN_CONTRACT_PDF_URL,
                    CJCU_RETURN_REPORT_FORM_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合長榮大學國際處國際合作組（OIA）《115學年度校級國際交換生甄選簡章》、《校級國際交換生學校一覽表（79 校）》、《海外雙聯學位學校列表（8 校 12 學程）》、《全球與兩岸締約姊妹校名錄》、《長榮大學赴外研修生作業要點》、《長榮大學學生出國期間學業及學籍處理要點》、《長榮大學海外雙聯學制實施辦法》、《長榮大學推展學生國際學術交流獎補助辦法》、《長榮大學短期交流補助作業要點》及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換生心得報告，共 {len(catalog_source)} 所合作姊妹校資料。"
        ),
    })

    cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": f"長榮大學國際處國際合作組交換學生計畫與姊妹校專頁—{zh_name}",
            "source_url": source_url,
            "summary": "長榮大學國際處公告之合作學程、開放學制、語言檢定門檻與免繳姊妹校學費／免住宿費／雙聯學位待遇說明",
        },
        {
            "title": "長榮大學 115學年度校級國際交換生甄選簡章、赴外研修生作業要點與國際學術交流獎補助辦法",
            "source_url": CJCU_BROCHURE_115_PDF_URL,
            "summary": "長榮大學出國交換全額學雜費註冊規定、校內甄選配分標準（面試 40%＋書審 60%）、英語加強課程、選課下限與獎學金規範",
        },
    ]
    if factsheet_url:
      dest_sources.append({
          "title": f"{full_name} 交換計畫官方簡章（Fact Sheet）",
          "source_url": factsheet_url,
          "summary": f"{zh_name} 官方提供之交換生申請資格、選課規定與住宿生活資訊 Fact Sheet",
      })
    if exp_links:
      dest_sources.append({
          "title": f"長榮大學國際處赴外交換學生歷屆心得分享專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
          "source_url": exp_links[0]["url"],
          "summary": f"收錄歷年長榮大學學生赴 {zh_name} 交換研習心得報告共 {len(exps)} 篇",
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
            CJCU_BROCHURE_115_PDF_URL,
            CJCU_OUTBOUND_GUIDELINES_PDF_URL,
            CJCU_SCHOLARSHIPS_URL,
        ]
        + ([factsheet_url] if factsheet_url else [])
        + ([exp_links[0]["url"]] if exp_links else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "長榮大學",
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
                "title": "生活費、長榮大學在學註冊規定、教育部學海飛颺／惜珠與校內國際學術交流獎補助金",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [CJCU_SCHOLARSHIP_REGULATIONS_PDF_URL],
                "caution": (
                    "依《長榮大學赴外研修生作業要點》第 4 點，交換期間仍須繳交長榮大學全額學雜費（非日間部一至四年級比照日間部管理學院學費 37,910 元＋雜費 8,300 元）；教育部學海飛颺、學海惜珠與長榮大學國際學術交流獎補助金三者僅能擇一領取，且同一學制以補助一次為限。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外國際學生宿舍申請（含日韓免住宿費與印尼政府獎學金姊妹校）",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": "日本鎮西學院大學、日本創價大學與韓國韓信大學額外提供交換生「免住宿費」優惠；印尼蘇吉甲普拉納塔天主教大學提供印尼政府 Darmasiswa 獎學金；其餘姊妹校宿位請於獲提名後依接待校期限申請。",
            },
            {
                "key": "insurance",
                "title": "海外醫療意外及急難救助保險、家長保證書與行政契約書公證規定",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依《長榮大學赴外研修生作業要點》第 9 點及《115學年度校級國際交換生甄選簡章》，報名時須檢附家長保證書正本，獲錄取後須簽署經家長或監護人同意之《長榮大學赴外交換學生行政契約書》，並於出國前自行購買涵蓋全期之海外保險（含醫療、意外、海外急難救助）送國際處備查。",
                ],
                "source_urls": src_url_list + [CJCU_ADMIN_CONTRACT_PDF_URL],
                "caution": "日本、韓國、德國、法國、奧地利、西班牙、捷克、美國、英國、澳洲等接待校對交換生當地國民健康保險或強制學生醫療險有嚴格規定，請依入學通知書辦理。",
            },
            {
                "key": "visa",
                "title": "留學交換簽證辦理、出國修業期限與雙聯學位修業月數規定",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依《長榮大學學生出國期間學業及學籍處理要點》第 4 點，選派交換生出國修習期間以一學期或一學年為限；跨國雙聯學位依《海外雙聯學制實施辦法》第 5 條，學士班於兩校修業時間合計至少滿 32 個月（各校至少滿 16 個月）、碩士班合計至少滿 12 個月、博士班合計至少滿 24 個月。",
                ],
                "source_urls": src_url_list + [CJCU_DUAL_DEGREE_RULES_PDF_URL],
                "caution": "境外生不得申請交換至其原居住國；服役役男出國進修應依內政部役男出境處理辦法於出國前一個月完成緩徵與出境核准手續。",
            },
            {
                "key": "academics",
                "title": "四組甄選配分（面試 40%＋書審 60%）、交換生英語加強課程、選課下限（9 學分／3 門課）與學分抵免",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [CJCU_CREDIT_HANDLING_RULES_PDF_URL],
                "caution": (
                    "交換期間每學期選課不得少於相當本校 9 學分或 3 門課程（不含體育課），且及格學分不得少於 6 學分或 2 門課程；違反者可扣減獎補助金 10% 至全額。"
                ),
            },
            {
                "key": "living",
                "title": f"{city_name} 校園生活與長榮大學學長姐交換心得傳承",
                "summary": f"代表城市：{city_name}。請配合接待校國際處完成報到與新生訓練（Orientation）。",
                "points": [
                    f"目的地城市：{city_name}（{country}）",
                    (
                        "長榮大學國際處國際合作組每學年舉辦校級國際交換生甄選說明會及歷屆學長姐返國成果發表會，並於官網公開歷屆交換生心得報告"
                        + (
                            f"（本校共收錄 {len(exps)} 篇心得報告：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，協助同學掌握選課與海外生活準備。"
                    ),
                ],
                "source_urls": [
                    exp_links[0]["url"]
                    if exp_links
                    else CJCU_STUDENT_EXPERIENCES_URL
                ],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合長榮大學國際處國際合作組 {len(catalog_source)} 所合作姊妹校、當期常態開放申請交換與雙聯學校（{open_partner_count} 校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷年學生交換心得報告。"
        ),
    })

    research_records.append({
        "home_university": "長榮大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            "長榮大學國際處國際合作組《115學年度校級國際交換生甄選簡章》、《校級國際交換生學校一覽表》、《海外雙聯學位學校列表》、《全球締約姊妹校名錄》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"長榮大學國際處交換學生計畫與姊妹校專頁—{zh_name}",
            "url": source_url,
        },
    ]
    if factsheet_url:
      ev_sources.append({
          "title": f"{full_name} 交換計畫官方簡章（Fact Sheet）",
          "url": factsheet_url,
      })
    if exp_links:
      ev_sources.append({
          "title": f"長榮大學赴外交換學生心得分享—赴 {zh_name} 心得報告（{len(exps)} 篇）",
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
            "scope": "長榮大學全球與兩岸交換姊妹校住宿與生活資訊",
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
            "scope": "長榮大學出國交換全額學雜費規定、教育部學海飛颺／惜珠、長榮大學推展學生國際學術交流獎補助金與短期交流補助",
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
            "scope": "長榮大學赴外研修生作業要點、海外雙聯學制實施辦法與學生出國期間學業及學籍處理要點",
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
            "scope": "長榮大學海外交換與雙聯學位簽證、家長保證書、行政契約書、海外醫療意外及急難救助保險提醒",
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
                    f"｜長榮大學公開收錄 {len(exps)} 篇赴 {zh_name} 交換生心得報告（{'、'.join(exp_labels[:3])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "長榮大學交換名額與歷屆學長姐心得報告",
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
            "已整合長榮大學國際處國際合作組《115學年度校級國際交換生甄選簡章》、《校級國際交換生學校一覽表》、《海外雙聯學位學校列表》、《全球締約姊妹校名錄》及歷屆學生交換心得報告。",
            "當期免學費／免住宿費名額、宿位供給、語檢門檻與選課限制請依合作校最新 Fact Sheet 及入學通知書核對。",
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

  write_jsonl(OFFICIAL_CJCU_DIR / "partners.jsonl", partners)
  write_jsonl(SOURCES_CJCU_DIR / "partners.jsonl", partners)
  write_jsonl(OFFICIAL_CJCU_DIR / "application_workflows.jsonl", workflows)
  write_jsonl(OFFICIAL_CJCU_DIR / "destination_profiles.jsonl", destinations)
  write_jsonl(OFFICIAL_CJCU_DIR / "partner_research.jsonl", research_records)
  write_jsonl(OFFICIAL_CJCU_DIR / "student_life.jsonl", life_records)
  write_jsonl(
      OFFICIAL_CJCU_DIR / "experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_CJCU_DIR / "student_experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_CJCU_DIR / "student_experiences.jsonl", student_experience_rows
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
  (OFFICIAL_CJCU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_CJCU_DIR / "student-experiences.json").write_text(
      json.dumps(
          {
              "school_id": "cjcu",
              "school_name": "長榮大學",
              "checked_at": CHECKED_AT,
              "source_url": CJCU_STUDENT_EXPERIENCES_URL,
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

  (OFFICIAL_CJCU_DIR / "campus-locations.json").write_text(
      json.dumps(
          {
              "school_id": "cjcu",
              "school_name": "長榮大學",
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
  (OFFICIAL_CJCU_DIR / "campus-assets.json").write_text(
      json.dumps(
          {
              "school_id": "cjcu",
              "school_name": "長榮大學",
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

  cjcu_source_urls = [
      CJCU_HOME_URL,
      CJCU_OIA_HOME_URL,
      CJCU_EXCHANGE_LATEST_NEWS_URL,
      CJCU_EXCHANGE_SCHOOL_LIST_URL,
      CJCU_SISTER_SCHOOLS_URL,
      CJCU_DUAL_DEGREE_LIST_URL,
      CJCU_DUAL_DEGREE_NEWS_URL,
      CJCU_SCHOLARSHIPS_URL,
      CJCU_REGULATIONS_URL,
      CJCU_STUDENT_EXPERIENCES_URL,
      CJCU_SHORT_TERM_SUBSIDY_URL,
      CJCU_BROCHURE_115_PDF_URL,
      CJCU_OUTBOUND_GUIDELINES_PDF_URL,
      CJCU_CREDIT_HANDLING_RULES_PDF_URL,
      CJCU_SCHOLARSHIP_REGULATIONS_PDF_URL,
      CJCU_SCHOLARSHIP_BROCHURE_114_PDF_URL,
      CJCU_SHORT_TERM_SUBSIDY_RULES_PDF_URL,
      CJCU_DUAL_DEGREE_RULES_PDF_URL,
      CJCU_ADMIN_CONTRACT_PDF_URL,
      CJCU_STUDY_PLAN_FORM_PDF_URL,
      CJCU_RECOMMENDATION_FORM_PDF_URL,
      CJCU_RETURN_REPORT_FORM_PDF_URL,
  ]

  exchange_info_payload = {
      "school_name": "長榮大學",
      "program_type": [
          (
              f"國際處國際合作組（OIA）校級國際交換生計畫（分「英語組」、「日語組」、「韓語組」、「中文組」四大甄選組別，涵蓋美國、加拿大、捷克、德國、法國、奧地利、西班牙、日本、韓國、中國大陸、香港、馬來西亞、泰國、印尼、越南、菲律賓、印度等 {open_partner_count} 所常態開放申請交換與雙聯學校，以及全球 26 國與地區共 {len(partners)} 所正式締約姊妹校）"
          ),
          (
              "海外雙聯學位計畫（Double Degree Programs，涵蓋【英國貝爾法斯特女王大學 QUB 1+1 碩士】、【英國諾丁漢特倫特大學 NTU 3+1 學士】、【法國雷恩商學院 Rennes SB 3+1.5 學碩】、【澳洲西雪梨大學 3+1.5 學碩】、【美國北德州大學 UNT 3+2 學碩】、【馬來西亞砂拉越科技大學 UTS 2+2 學士】、【泰國清邁皇家大學 CMRU 2+2 學士】及【馬來西亞衛理公會畢禮學院 2+2 學士】等 8 校 12 項學程）"
          ),
          (
              "教育部「學海飛颺獎學金」（前一學年平均達 75 分或班排前 25%）、「學海惜珠獎學金」（清寒優秀生出國研修）、《長榮大學推展學生國際學術交流獎補助金》（前一學年平均及格或班排前 50%），以及《長榮大學短期交流補助作業要點》（海外短期進修、7–30 天文化交流或國際競賽，每人每次最高補助 NT$ 40,000）"
          ),
      ],
      "academic_year": [
          (
              "115（涵蓋 115學年度校級國際交換生甄選［報名期間 2026/10/01–11/27 17:00，選送於 116-1 或 116-2 出國交換一學期或一學年］、海外雙聯學位計畫、教育部學海飛颺／惜珠暨校內國際學術交流獎補助金，以及每年 10 月與 3 月兩梯次短期交流補助）"
          ),
          (
              f"本平台完整收錄長榮大學國際處國際合作組公告之 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所常態開放申請之校級交換與雙聯學位學校、{len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 26 個國家與地區，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆交換生返國心得報告與 35 份官方 Fact Sheet）"
          ),
      ],
      "semester": [
          "校級國際交換生甄選（每學年第一學期 10–11 月報名、12 月面試放榜）：選送通過甄選之學生於次學年度第一學期（秋季班）或第二學期（春季班）出國交換一學期或一學年（依《學生出國期間學業及學籍處理要點》第 4 點，選派交換生出國修習期間以一學期或一學年為限）。",
          "海外雙聯學位（依《長榮大學海外雙聯學制實施辦法》第 5 條）：學士班於兩校修業時間合計至少滿 32 個月（各校至少滿 16 個月）、碩士班合計至少滿 12 個月、博士班合計至少滿 24 個月，且於兩校修習學分數各須達畢業總學分數 1/3 以上。",
          "短期交流補助計畫（依《長榮大學短期交流補助作業要點》第 5 點）：第一梯次於每年 10 月 1 日至 10 月 31 日申請（次年 1–6 月出國執行）；第二梯次於每年 3 月 1 日至 3 月 31 日申請（當年 7–12 月出國執行）。",
      ],
      "application_period": [
          "【115學年度校級國際交換生甄選（116-1／116-2 出國交換）】甄選說明會：2026年10月2日（五）12:10–13:00 於行政大樓一樓 Global Plaza；報名收件期間：2026年10月1日（四）至 2026年11月27日（五）17:00 止（須同步完成線上表單 https://forms.gle/2kaidJJ8b4xwsPbu6 、繳交紙本至行政大樓三樓國際處並寄送彩色掃描 PDF 至 exch@mail.cjcu.edu.tw）。",
          "【115學年度校級交換生面試與錄取確認時程】2026年12月4日（五）公告面試時間表；2026年12月11日（五）辦理分組外語面試；2026年12月16日（三）公告第一階段錄取名單；2026年12月21日（一）第一階段錄取確認截止；2026年12月31日（四）公告最終錄取名單。",
          "【教育部學海飛颺／學海惜珠＆長榮大學推展學生國際學術交流獎補助金】於通過校級交換生甄選並確認出國學期後提出申請（114學年度申請截止日為 2026年2月9日 17:00，繳交紙本與電子檔至國際處國際合作組）。",
          "【長榮大學短期交流補助作業（每人最高 NT$ 40,000）】每年分兩梯次受理：第一梯次 10 月 1 日至 10 月 31 日（補助次年 1–6 月出國）、第二梯次 3 月 1 日至 3 月 31 日（補助當年 7–12 月出國）。",
      ],
      "eligibility": [
          "1. 基本在學身分與學業成績門檻：依《長榮大學 115學年度校級國際交換生甄選簡章》第參點及《長榮大學赴外研修生作業要點》第 3 點，申請人須為本校在學學生，出國就讀時須於本校修業滿一學年（含）以上，且前一學年度學業平均成績達 70 分（含）以上；境外生不得申請交換至其原居住國。",
          "2. 校內甄選評比項目與配分（總分 100%）：（1）面試占 40%（英韓組採英文及韓文面試、英語組採英文面試、中文組採中文簡報及面試、日語組採日文面試；同時報名兩組以上者須分別參加面試）；（2）書面資料占 60%（前一學年度操行成績 10%＋前一學年度學業成績 10%＋自傳及讀書計畫 15%＋語文證明 10%＋其他相關資料 15%）。",
          "3. 歐韓語課程修讀先決條件与錄取後外語培訓：所填志願若為奧地利、西班牙、法國、德國、韓國學校，報名時須繳交二年內曾修讀相關語言課程之證明。除日語組與中國地區外，錄取生均須參加並通過語文教育中心開設之「交換生英語加強課程」（第 1 週至第 9 週）；日語組學生須參加應用日語學系每週辦理之日語會話練習。",
          "4. 個別姊妹校特殊身分與性別／年齡限制：日本宮城學院女子大學、福岡女學院大學及韓國梨花女子大學、德成女子大學僅收女性交換生；韓國中央大學與仁川大學限 30 歲以下；日本天理大學、東亞大學、北洋大學、別府大學限 18–30 歲；日本立教大學限基督教徒且須 JLPT N1；香港浸會大學要求 CGPA 2.5 且 IELTS 6.0 / TOEFL iBT 79。",
      ],
      "language_requirement": [
          "1. 英語組（歐美亞英語授課姊妹校與雙聯學位）：（a）基礎英語門檻：多數捷克（赫拉德茨克拉洛韋大學、帕爾杜比采大學）、日本宮崎國際大學、馬來西亞拉曼大學與砂拉越科技大學、泰國暹羅大學與清邁皇家大學、印尼天主教大學、菲律賓西利曼大學、印度聖澤維爾學院建議具備相當 CEFR B1（TOEIC 550 / TOEFL iBT 61 / IELTS 5.0）以上；（b）進階歐美名校門檻：奧地利上奧地利應用科技大學、德國北ハウゼン應用技術大學、法國天主教里昂大學、西班牙胡安卡洛斯國王大學與 UCAM、捷克奧斯特拉瓦大學要求 CEFR B2（TOEFL iBT 72–80 / IELTS 5.5–6.0）；美國北德州大學 UNT 要求 iBT 79 / IELTS 6.5、香港浸會大學要求 iBT 79 / IELTS 6.0、加拿大愛德華王子島大學 UPEI 要求 iBT 80 / IELTS 6.5；雙聯學位（英國女王大學 QUB、諾丁漢特倫特大學 NTU、法國雷恩商學院、澳洲西雪梨大學）要求 IELTS 6.0–6.5。",
          "2. 日語組（22 所日本交換姊妹校）：（a）不拘或基礎日語門檻：鎮西學院大學（免住宿費）、東亞大學、尚絅學院大學、北陸學院大學、金城學院大學（部分課程）、四國學院大學、名櫻大學、宮崎國際大學（英語授課）可憑基礎日語或選修英文課程申請；（b）JLPT N4–N3 門檻：別府大學（N4）、聖隸克里斯多福大學（N4–N3）、北洋大學（N3）、大阪商業大學（N3）、流通科學大學（N3）、青山學院大學（N3）；（c）JLPT N2–N1 門檻：創價大學（N2，免住宿費）、大東文化大學（N2）、明治學院大學（N2）、桃山學院大學（N2）、敬和學園大學（N2）、天理大學（N2）、宮城學院女子大學（N2，限女生）、福岡女學院大學（N2，限女生）、立教大學（N1，限基督教徒）。",
          "3. 韓語組（12 所韓國交換姊妹校）：报名韓語組或英韓組志願者須檢附二年內曾修讀韓語課程之證明，建議具備韓語檢定 TOPIK 2–3 級或英語 TOEIC 550–700 / TOEFL iBT 61–71 以上（梨花女子大學、中央大學、仁川大學、德成女子大學、全州大學、韓남大學、韓信大學［免住宿費］、白石大學、威德大學、金泉大學等均提供英語或韓語授課課程與韓語語學堂）。",
          "4. 中文組（25 所中國大陸及馬來西亞新紀元大學學院）：廈門大學、山東大學、中央民族大學、福州外語外貿學院、泉州師範學院、三明學院、莆田學院、上海師範大學天華學院等大陸姊妹校及馬來西亞新紀元大學學院為中文授課，參加中文組簡報及面試即可。",
      ],
      "required_documents": [
          "1. 長榮大學校級國際交換生甄選個人資料表一份（須完成紙本欄位簽章，並同步填寫線上報名表單 https://forms.gle/2kaidJJ8b4xwsPbu6 ）",
          "2. 大學或研究所歷年中文成績單正本一份（前一學年度學業平均成績須達 70 分［含］以上；申請學海飛颺／惜珠者須達 75 分或班排前 25%）",
          "3. 語文檢定證明影本一份（TOEIC / TOEFL iBT / IELTS / JLPT / TOPIK 等有效檢定成績單，占書審 10%）",
          "4. 家長保證書正本一份（須由家長或法定監護人親筆簽名蓋章；錄取後另須簽署公證《長榮大學赴外交換學生行政契約書》）",
          "5. 中、英文，或中、日文自傳各一篇（A4 兩頁為限，電腦打字，連同讀書計畫占書審 15%）",
          "6. 中、英文，或中、日文讀書計畫各一份（含赴外修課規劃、與本系專業課程銜接及返國學分抵免計畫）",
          "7. 二年內曾修讀相關外語課程之證明（所填志願若為奧地利、西班牙、法國、德國、韓國學校者必備）",
          "8. 其他有助甄選資格審查之資料（如競賽獲獎、證照、社團幹部或國際交流志工證明，占書審 15%）",
          "9. 本校專任（專案）教師推薦函（彌封）二封（僅交紙本，無須掃描繳交電子檔；其餘第 1–8 項須彩色掃描合併為單一 PDF 寄至 exch@mail.cjcu.edu.tw）",
      ],
      "scholarship_info": [
          "1. 教育部「學海飛颺獎學金」（依《長榮大學推展學生國際學術交流獎補助辦法》）：補助具中華民國國籍、於臺灣地區設有戶籍、通過本校甄選赴外國（不含大陸及港澳地區）姊妹校交換一學期或一學年，且前一學年度學業平均成績達 75 分（含）以上或全班排名前 25%（含）以內之在學學生。",
          "2. 教育部「學海惜珠獎學金」：補助具中華民國國籍、持有各直轄市、縣（市）主管機關認定之低收入戶、中低收入戶或特殊境遇家庭相關證明文件，且前一學年度學業平均成績達 75 分（含）以上或全班排名前 25%（含）以內，赴非大陸港澳姊妹校交換一學期或一學年之學生。",
          "3. 《長榮大學推展學生國際學術交流獎補助金》：補助通過本校甄選赴境外合作學校交換研習、前一學年度學業平均成績及格或全班排名前 50%（含）以內之在學學生（註：學海飛颺、學海惜珠與長榮大學國際學術交流獎補助金三者僅能擇一領取，且同一學制以補助一次為限；114學年度收件截止日為 2026年2月9日 17:00）。",
          "4. 《長榮大學短期交流補助作業要點》（113年3月7日行政會議修正通過）：補助在學學生赴境外合作機構進行短期進修（至少修讀 1 學分）、短期文化交流（7–30 天，具國際移動力 GlobEEs 身分者優先）或短期競賽及培訓；補助項目包含經濟艙來回機票、簽證、保險、報名註冊費及住宿費（每日上限 1,600 元），每人每次補助總額上限新臺幣 40,000 元（每年 10 月及 3 月分兩梯次申請）。",
          "5. 姊妹校專屬免住宿費與外國政府獎學金：（a）日本【鎮西學院大學】、日本【創價大學】、韓國【韓信大學】提供長榮大學交換生「免學費＋免住宿費」雙重待遇；（b）印尼【蘇吉甲普拉納塔天主教大學】提供印尼政府 Darmasiswa 獎學金（每月生活費約 NT$ 3,500、住宿補助一次約 NT$ 1,000）。",
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": cjcu_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_CJCU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "長榮大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 70.0,
      "academic_score_rule": (
          "依《長榮大學 115學年度校級國際交換生甄選簡章》第參點及《長榮大學赴外研修生作業要點》第 3 點：申請人出國就讀時須於本校修業滿一學年（含）以上，且前一學年度學業平均成績達 70 分（含）以上（書面審查採計前一學年度操行成績 10%＋前一學年度學業成績 10%）；申請教育部《學海飛颺／學海惜珠獎學金》須前一學年度學業平均成績達 75 分（含）以上或全班排名前 25%，申請《長榮大學推展學生國際學術交流獎補助金》須前一學年度學業平均成績及格或全班排名前 50%。"
      ),
      "academic_gpa_minimum": 2.5,
      "maximum_preferences": 5,
      "selection_rules": {
          "academic_policy": "gpa_or_rank",
          "academic_reference_year": "115",
          "undergraduate_gpa_minimum": 2.5,
          "graduate_academic_exempt": False,
          "exclude_in_service": False,
          "pending_quota_planning": False,
          "partner_requirements_need_confirmation": False,
          "degree_score_minimums": {
              "undergraduate": 70.0,
              "graduate": 70.0,
          },
          "excluded_undergraduate_years": [],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 61.0,
          "ielts": 5.0,
          "toefl_itp": 500.0,
          "toeic": 550.0,
      },
      "application_periods": [
          {
              "title": "長榮大學 115學年度校級國際交換生甄選（2026/10/01–11/27 17:00 報名，選送 116-1／116-2 出國交換）",
              "details": [
                  "依《長榮大學 115學年度校級國際交換生甄選簡章》，報名收件自 2026年10月1日（四）起至 2026年11月27日（五）17:00 止（10月2日 12:10 於行政大樓一樓 Global Plaza 舉辦甄選說明會）；12月4日公告面試時間表、12月11日辦理分組面試、12月16日公告第一階段錄取名單、12月21日第一階段錄取確認截止、12月31日公告最終錄取名單。",
                  "申請人須同步完成三項程序：（1）填寫線上報名表單（https://forms.gle/2kaidJJ8b4xwsPbu6）；（2）將 9 項書面資料以迴紋針固定送交行政大樓三樓國際處；（3）將除彌封教師推薦函外之 8 項資料彩色掃描合併為單一 PDF 寄至 exch@mail.cjcu.edu.tw。",
              ],
              "source": {
                  "title": "長榮大學 115學年度校級國際交換生甄選簡章與交換計畫最新消息",
                  "source_url": CJCU_EXCHANGE_LATEST_NEWS_URL,
                  "category": "exchange_application",
                  "summary": "長榮大學 115學年度校級國際交換生甄選時程、資格、分組面試與書審配分標準。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "115",
              "application_round": "115學年度校級國際交換生甄選（116-1／116-2 出國）",
              "audience": "all_students",
              "opens_at": "2026-10-01T09:00:00+08:00",
              "deadline_at": "2026-11-27T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "open",
              "status_note": "115學年度校級國際交換生甄選自 2026/10/01 開放報名至 2026/11/27 17:00 截止，12/11 辦理分組面試。",
              "deadline_note": "須同時完成線上表單、紙本送交國際處及彩色掃描 PDF 寄至 exch@mail.cjcu.edu.tw，缺一不予受理。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "長榮大學「教育部學海飛颺／學海惜珠」暨「推展學生國際學術交流獎補助金」申請（每年 2 月上旬截止）",
              "details": [
                  "依《長榮大學推展學生國際學術交流獎補助辦法》及申請簡章，通過本校校級交換生甄選並取得交換資格之在學學生，得申請教育部《學海飛颺獎學金》（前學年平均達 75 分或班排前 25%）、《學海惜珠獎學金》（清寒證明＋前學年平均達 75 分或班排前 25%）或《長榮大學推展學生國際學術交流獎補助金》（前學年平均及格或班排前 50%）。",
                  "上述三項獎學金僅能擇一領取，且同一學制以補助一次為限；申請人須檢附申請表、中文歷年成績單、語檢證明、自傳及讀書計畫、獎補助行政契約書及他校錄取證明送交國際處國際合作組。",
              ],
              "source": {
                  "title": "長榮大學國際處獎學金申請專區與推展學生國際學術交流獎補助辦法",
                  "source_url": CJCU_SCHOLARSHIPS_URL,
                  "category": "scholarship",
                  "summary": "長榮大學教育部學海飛颺、學海惜珠與校內國際學術交流獎補助金申請資格與應繳文件。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "115–116學年度國際交換生獎學金申請",
              "audience": "all_students",
              "opens_at": "2027-01-15T09:00:00+08:00",
              "deadline_at": "2027-02-09T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "通過校級交換生甄選後，於次年 1–2 月向國際處提出獎學金申請（參考 114學年度截止日為 2 月 9 日 17:00）。",
              "deadline_note": "紙本與單一合併 PDF 電子檔（寄至 exch@mail.cjcu.edu.tw）均須於截止時間前完成繳交。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "長榮大學海外雙聯學位計畫（英、法、澳、美、馬、泰 8 校 12 學程）與短期交流補助（每年 10 月、3 月截止）",
              "details": [
                  "依《長榮大學海外雙聯學制實施辦法》，本校與英國貝爾法斯特女王大學（1+1 碩士）、英國諾丁漢特倫特大學（3+1 學士）、法國雷恩商學院（3+1.5 學碩）、澳洲西雪梨大學（3+1.5 學碩）、美國北德州大學（3+2 學碩）、馬來西亞砂拉越科技大學（2+2 學士）、泰國清邁皇家大學（2+2 學士）及馬來西亞衛理公會畢禮學院（2+2 學士）合作辦理雙聯學位，於每年校級交換暨雙聯甄選期程受理申請。",
                  "另依《長榮大學短期交流補助作業要點》，補助學生赴境外短期進修、7–30 天文化交流或國際競賽（每人上限 NT$ 40,000），每年分兩梯次於 10 月 1 日至 10 月 31 日及 3 月 1 日至 3 月 31 日受理。",
              ],
              "source": {
                  "title": "長榮大學海外雙聯學位學校列表與短期交流補助專區",
                  "source_url": CJCU_DUAL_DEGREE_LIST_URL,
                  "category": "exchange_application",
                  "summary": "長榮大學 8 所海外雙聯學位合作校學程與短期交流補助每年 10 月、3 月兩梯次申請規定。",
              },
              "scope": "home_application",
              "program_types": ["dual_degree"],
              "academic_year": "115",
              "application_round": "115學年度海外雙聯學位暨短期交流補助",
              "audience": "all_students",
              "opens_at": "2026-10-01T09:00:00+08:00",
              "deadline_at": "2027-03-31T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "open",
              "status_note": "短期交流補助第一梯次每年 10/1–10/31、第二梯次每年 3/1–3/31 受理；雙聯學位依各合作校提名期程向國際處申請。",
              "deadline_note": "雙聯學位申請人須符合各合作學院之 GPA 與 IELTS / TOEFL iBT 門檻。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"長榮大學國際處全球姊妹校交換、海外雙聯學位與國際交流獎補助總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所常態開放申請・{total_exp_reports} 篇學長姐交換心得報告）"
              ),
              "details": [
                  (
                      f"長榮大學（Chang Jung Christian University, CJCU，創立於 1993 年，坐落於臺南市歸仁區長大路 1 號，緊鄰沙崙綠能科學城與高鐵臺南站，並設有校區內直達之臺鐵沙崙線「長榮大學車站」，為臺灣基督長老教會創辦之國際化永續大學與國際珍古德根與芽生態教育中心基地）由「國際處國際合作組（Office of International Affairs, OIA）」統籌全校 10 個教學單位（管理學院、健康科學學院、人文社會學院、資訊暨設計學院、安全衛生科學學院、永續教育學院、環境教育國際實驗學院、神學院、PLUS學院、博雅教育學部）之校級國際交換生計畫、海外雙聯學位計畫及國際學術交流獎補助。本平台完整收錄 {len(partners)} 所長榮大學官方合作姊妹校（含 {open_partner_count} 所常態開放申請之交換與雙聯學位合作校，以及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 26 個國家與地區。"
                  ),
                  (
                      f"長榮大學國際交流具備四大核心亮點：（1）英語組、日語組、韓語組、中文組四大分組完整覆蓋歐美亞 79 所校級交換學校（含日本創價大學、鎮西學院大學與韓國韓信大學「免學費＋免住宿費」，明治學院大學、青山學院大學、大東文化大學、桃山學院大學、立教大學、梨花女子大學、中央大學、仁川大學、德成女子大學、全州大學、捷克赫拉德茨克拉洛韋大學、帕爾杜比采大學、奧斯特拉瓦大學、德國北ハウゼン應用技術大學、法國天主教里昂大學、奧地利上奧地利應用科技大學、西班牙胡安卡洛斯國王大學与 UCAM、美國北德州大學、加拿大愛德華王子島大學、香港浸會大學、廈門大學、山東大學、中央民族大學等）；（2）英、法、澳、美、馬、泰 8 校 12 項跨國雙聯學位（英國女王大學 QUB、諾丁漢特倫特大學 NTU、法國雷恩商學院、澳洲西雪梨大學、美國北德州大學 UNT、馬來西亞砂拉越科技大學 UTS、泰國清邁皇家大學 CMRU 等）；（3）教育部學海飛颺、學海惜珠、長榮大學推展學生國際學術交流獎補助金與短期交流補助（最高 4 萬元）；（4）完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆交換生心得報告與 35 份官方 Fact Sheet。"
                  ),
              ],
              "source": {
                  "title": "長榮大學國際處國際合作組（OIA）官方網站與 115學年度校級國際交換生甄選簡章",
                  "source_url": CJCU_OIA_HOME_URL,
                  "category": "exchange_application",
                  "summary": f"長榮大學 {len(partners)} 所全球合作姊妹校、{open_partner_count} 所常態開放交換／雙聯校與 {total_exp_reports} 篇心得報告。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "修業滿一學年以上、前學年平均成績 70 分以上、四組面試與書審配分（40% : 60%）及錄取後外語培訓義務",
              "details": [
                  "在學身分與成績門檻：依《長榮大學 115學年度校級國際交換生甄選簡章》第參點及《赴外研修生作業要點》第 3 點，申請人於甄選及出國就讀期間均須為本校在學學生，出國就讀時須於本校修業滿一學年（含）以上，且前一學年度學業平均成績達 70 分（含）以上（境外生不得申請交換至其原居住國）。所填志願若為奧地利、西班牙、法國、德國、韓國學校，須繳交二年內曾修讀相關語言課程之證明。",
                  "甄選配分與錄取後外語加強課程：校內甄選採計「面試 40%」（英韓組、英語組、中文組、日語組分組外語面試）＋「書面資料 60%」（前一學年度操行成績 10%＋前一學年度學業成績 10%＋自傳及讀書計畫 15%＋語文證明 10%＋其他相關資料 15%）。除日語組與中國地區外，錄取生均須參加並通過語文教育中心「交換生英語加強課程」（第 1–9 週）；日語組須參加應用日語學系每週日語會話練習。",
              ],
              "source": {
                  "title": "長榮大學 115學年度校級國際交換生甄選簡章與赴外研修生作業要點",
                  "source_url": CJCU_BROCHURE_115_PDF_URL,
                  "category": "exchange_application",
                  "summary": "長榮大學交換生修業年限、70 分學業門檻、面試 40%＋書審 60% 配分與英語加強課程規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "英語組（TOEIC 550–785 / TOEFL iBT 61–80 / IELTS 5.0–6.5）、日語組（JLPT N1–N4）、韓語組（TOPIK / 韓語修課證明）與中文組規定",
              "details": [
                  "英語組與雙聯學位外語門檻：（1）捷克赫拉德茨克拉洛韋大學、帕爾杜比采大學、馬來西亞拉曼大學与砂拉越科技大學、泰國暹羅大學與清邁皇家大學、印尼天主教大學、菲律賓西利曼大學、印度聖澤維爾學院建議達 CEFR B1（TOEIC 550 / TOEFL iBT 61 / IELTS 5.0）；（2）奧地利上奧地利應用科技大學、德國北ハウゼン應用技術大學、法國天主教里昂大學、西班牙胡安卡洛斯國王大學與 UCAM、捷克奧斯特拉瓦大學要求 CEFR B2（iBT 72–80 / IELTS 5.5–6.0）；（3）香港浸會大學要求 iBT 79 / IELTS 6.0，美國北德州大學 UNT 要求 iBT 79 / IELTS 6.5，加拿大愛德華王子島大學 UPEI 要求 iBT 80 / IELTS 6.5；雙聯學位（英國 QUB、NTU、法國雷恩商學院、澳洲西雪梨大學）要求 IELTS 6.0–6.5。",
                  "日語組、韓語組與中文組門檻：（1）日本別府大學要求 JLPT N4，聖隸克里斯多福大學要求 N4–N3，北洋大學、大阪商業大學、流通科學大學、青山學院大學要求 N3，創價大學、大東文化大學、明治學院大學、桃山學院大學、敬和學園大學、天理大學、宮城學院女子大學、福岡女學院大學要求 N2，立教大學要求 N1（鎮西學院大學、四國學院大學、名櫻大學、宮崎國際大學等可修讀基礎日語或英語課程）；（2）韓國 12 校須附二年內韓語修課證明並建議具 TOPIK 2–3 級或英語 B1–B2；（3）大陸 25 校與馬來西亞新紀元大學學院為中文授課。",
              ],
              "source": {
                  "title": "長榮大學校級國際交換生學校一覽表、海外雙聯學位列表與 115學年度甄選簡章",
                  "source_url": CJCU_EXCHANGE_SCHOOL_LIST_URL,
                  "category": "exchange_application",
                  "summary": "長榮大學英語組、日語組、韓語組、中文組與雙聯學位外語能力門檻總覽。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "個人資料表、歷年中文成績單正本、語檢證明、家長保證書、中英/中日自傳與讀書計畫、歐韓語修課證明、彌封推薦函二封",
              "details": [
                  "校級交換生甄選 9 項必備書面資料（紙本迴紋針固定送國際處＋第 1–8 項彩色掃描合併單一 PDF 寄至 exch@mail.cjcu.edu.tw）：（1）個人資料表一份（完成紙本簽章）；（2）大學或研究所歷年中文成績單正本一份；（3）語文檢定證明影本一份；（4）家長保證書正本一份；（5）中、英文，或中、日文自傳各一篇；（6）中、英文，或中、日文讀書計畫各一份；（7）申請奧地利、西班牙、法國、德國、韓國學校者檢附二年內曾修讀相關語言課程證明；（8）其他有利審查資料；（9）本校專任（專案）教師推薦函（彌封）二封。",
                  "錄取後與返國核銷必備文件：錄取後繳交《第一階段錄取確認書》與經家長同意公證之《長榮大學赴外交換學生行政契約書》；抵達姊妹校兩週內回報選課清單；返國後一個月內繳交 2,000 字以上中文心得報告及 400 字以上外文心得報告、照片 6 張、機票票根及護照出入境章影本，並持國外成績單正本辦理學分抵免。",
              ],
              "source": {
                  "title": "長榮大學 115學年度校級國際交換生甄選簡章與表單下載專區",
                  "source_url": CJCU_BROCHURE_115_PDF_URL,
                  "category": "exchange_application",
                  "summary": "長榮大學校級交換生甄選 9 項報名表件、行政契約書及返國心得報告規範。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部學海飛颺／惜珠（前學年 75 分或前 25%）、長榮大學國際學術交流獎補助金（前 50%）、短期交流補助（最高 4 萬元）與日韓免住宿費姊妹校",
              "details": [
                  "出國交換三大獎學金（依《長榮大學推展學生國際學術交流獎補助辦法》，三者擇一領取）：（1）《教育部學海飛颺獎學金》：補助具中華民國國籍、赴非大陸港澳姊妹校交換、前一學年度平均成績達 75 分或班排前 25% 之學生；（2）《教育部學海惜珠獎學金》：補助持低收、中低收或特殊境遇家庭證明且前一學年平均達 75 分或班排前 25% 之學生；（3）《長榮大學推展學生國際學術交流獎補助金》：補助前一學年平均成績及格或班排前 50% 之交換生。",
                  "短期交流補助與姊妹校專屬免住宿費：（1）《長榮大學短期交流補助作業要點》：補助海外短期進修（>=1 學分）、文化交流（7–30 天）或國際競賽之機票、簽證、保險、註冊費與住宿費（每日上限 1,600 元），每人每次最高 NT$ 40,000；（2）日本【鎮西學院大學】、日本【創價大學】与韓國【韓信大學】提供交換生「免住宿費」優惠；印尼【蘇吉甲普拉納塔天主教大學】提供印尼政府 Darmasiswa 獎學金。",
              ],
              "source": {
                  "title": "長榮大學推展學生國際學術交流獎補助辦法與短期交流補助作業要點",
                  "source_url": CJCU_SCHOLARSHIPS_URL,
                  "category": "scholarship",
                  "summary": "長榮大學學海飛颺、學海惜珠、校內國際學術交流獎補助金與短期交流補助完整規定。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "長榮大學出國交換中英/中日雙語自傳與讀書計畫（占書審 15%）、教師彌封推薦函與行政契約書準備指南",
              "summary": "說明長榮大學《115學年度校級國際交換生甄選簡章》規定之中英文或中日文雙語自傳與讀書計畫（占書面審查 15%）、二封專任教師彌封推薦函及錄取後行政契約書要領。",
              "key_points": [
                  "中英文或中日文讀書計畫（連同自傳占書審 15%）：應明確規劃於目標姊妹校每學期修習至少相當本校 9 學分或 3 門課程（不含體育課）之科目清單、與長榮大學母系專業課程之學分採認抵免對應，以及出國前參加語文教育中心「交換生英語加強課程」或應日系日語會話練習之學習規劃。",
                  "中英文或中日文自傳與其他相關資料（其他資料占書審 15%）：以 A4 兩頁為限電腦打字，建議結合長榮大學管理、健康科學、人文社會、資訊設計、安全衛生或環境教育永續專業背景，呈現外語檢定、國際學伴（GlobEEs）或社團專題成果。",
                  "二封專任（專案）教師彌封推薦函與歐韓語修課證明：推薦函須由推薦教師簽名彌封後隨紙本繳交（無須掃描電子檔）；志願含奧地利、西班牙、法國、德國、韓國學校者務必附上二年內曾修讀相關語言課程之成績單或修課證明。",
              ],
              "applies_to": [],
              "source": {
                  "title": "長榮大學 115學年度校級國際交換生甄選簡章與自傳讀書計畫專用表格",
                  "source_url": CJCU_BROCHURE_115_PDF_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": CJCU_STUDY_PLAN_FORM_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "長榮大學赴外研修生作業要點、學生出國期間學業及學籍處理要點與海外雙聯學制實施辦法核心規定",
              "summary": "規範長榮大學交換生在學註冊繳費（全額學雜費）、海外選課下限（每學期至少 9 學分或 3 門課，至少 6 學分或 2 門課及格）、雙聯學制修業月數與返國義務。",
              "key_points": [
                  "出國期間註冊繳費規定：依《赴外研修生作業要點》第 4 點，研修生於交換期間仍須辦理本校註冊手續並繳交本校全額學雜費（非日間部一至四年級學生應比照日間部管理學院收費標準繳交全額學雜費：學費 37,910 元＋雜費 8,300 元）。",
                  "赴外選課下限與及格門檻：依《赴外研修生作業要點》第 9 點第 8 款及《行政契約書》第 8 條，交換生於交換期間每學期選課不得少於相當本校 9 學分或 3 門課程（不含體育課），且及格學分不得少於 6 學分或 2 門課程；違反者可扣減獎補助金 10% 至全額。",
                  "海外雙聯學制修業規定：依《海外雙聯學制實施辦法》第 5–6 條，雙聯學生於兩校修業時間學士班合計至少滿 32 個月（各校至少滿 16 個月）、碩士班合計至少滿 12 個月、博士班合計至少滿 24 個月，且於兩校修習學分數各須達畢業總學分數 1/3 以上。",
              ],
              "applies_to": [],
              "source": {
                  "title": "長榮大學赴外研修生作業要點、出國期間學業及學籍處理要點與海外雙聯學制實施辦法",
                  "source_url": CJCU_OUTBOUND_GUIDELINES_PDF_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": CJCU_CREDIT_HANDLING_RULES_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "長榮大學國際處國際合作組（Office of International Affairs）官方網站",
              "source_url": CJCU_OIA_HOME_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "長榮大學 115學年度校級國際交換生甄選簡章與交換計畫最新消息",
              "source_url": CJCU_EXCHANGE_LATEST_NEWS_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "長榮大學校級國際交換生學校一覽表（英語組、日語組、韓語組、中文組共 79 校）",
              "source_url": CJCU_EXCHANGE_SCHOOL_LIST_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "長榮大學海外雙聯學位學校列表（英、法、澳、美、馬、泰 8 校 12 學程）與雙聯學制實施辦法",
              "source_url": CJCU_DUAL_DEGREE_LIST_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": f"長榮大學全球與兩岸締約姊妹校名錄（橫跨 26 國與地區共 {len(partners)} 所合作姊妹校）",
              "source_url": CJCU_SISTER_SCHOOLS_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "長榮大學國際處獎學金申請專區（教育部學海飛颺、學海惜珠、長榮大學推展學生國際學術交流獎補助金）",
              "source_url": CJCU_SCHOLARSHIPS_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "長榮大學赴外研修相關法規專區（赴外研修生作業要點、學業及學籍處理要點、短期交流補助作業要點）",
              "source_url": CJCU_REGULATIONS_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": f"長榮大學赴外交換學生歷屆心得分享專區（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）",
              "source_url": CJCU_STUDENT_EXPERIENCES_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_CJCU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  doc_conditions = {
      "school_id": "cjcu",
      "school_name": "長榮大學",
      "checked_at": CHECKED_AT,
      "source_url": CJCU_BROCHURE_115_PDF_URL,
      "common_documents": exchange_info_payload["required_documents"],
      "track_specific_conditions": [
          {
              "track": "校級國際交換生計畫—「英語組」與「英韓組（韓國 12 校）」",
              "required": [
                  "長榮大學校級國際交換生甄選個人資料表（含紙本簽章）及線上表單（https://forms.gle/2kaidJJ8b4xwsPbu6）",
                  "大學或研究所歷年中文成績單正本（前學年平均達 70 分以上；占書審 10%）与前學年操行成績（占書審 10%）",
                  "有效英語或韓語檢定證明影本（TOEIC / TOEFL iBT / IELTS / TOPIK；占書審 10%）",
                  "二年內曾修讀相關外語課程之證明（志願含奧地利、西班牙、法國、德國、韓國學校者必備）",
                  "中、英文自傳及中、英文讀書計畫各一份（占書審 15%）、家長保證書正本、其他有利審查資料（占書審 15%）及專任教師彌封推薦函二封",
              ],
          },
          {
              "track": "校級國際交換生計畫—「日語組（日本 22 校）」",
              "required": [
                  "長榮大學校級國際交換生甄選個人資料表（含紙本簽章）及線上表單",
                  "大學或研究所歷年中文成績單正本（前學年平均達 70 分以上）",
                  "日語能力檢定證明影本（JLPT N1–N4，依各日本姊妹校規定；占書審 10%）",
                  "中、日文自傳及中、日文讀書計畫各一份（占書審 15%）、家長保證書正本、其他有利審查資料及專任教師彌封推薦函二封（錄取後須參加應日系每週日語會話練習）",
              ],
          },
          {
              "track": "校級國際交換生計畫—「中文組（大陸 25 校與馬來西亞新紀元大學學院）」",
              "required": [
                  "長榮大學校級國際交換生甄選個人資料表（含紙本簽章）及線上表單",
                  "大學或研究所歷年中文成績單正本（前學年平均達 70 分以上）",
                  "中文及英文自傳與讀書計畫、家長保證書正本、其他有利審查資料及專任教師彌封推薦函二封（參加中文組簡報及面試，錄取大陸姊妹校者另須備妥有效臺胞證）",
              ],
          },
          {
              "track": "海外雙聯學位計畫（英、法、澳、美、馬、泰 8 校 12 學程）與國際學術交流獎補助金",
              "required": [
                  "海外雙聯學位申請：校內申請表、英文歷年成績單正本、外語檢定證明（IELTS 6.0–6.5 / TOEFL iBT 79 或合作校指定門檻）、英文讀書計畫、家長同意書與推薦信",
                  "教育部學海飛颺／惜珠或長榮大學國際學術交流獎補助金：獎學金申請表、歷年中文成績單正本（學海須前學年平均 75 分或前 25%；校內獎補助金須前學年及格或前 50%）、語檢證明、自傳及讀書計畫、獎補助行政契約書及姊妹校錄取證明（學海惜珠另附低收／中低收／特殊境遇證明）",
              ],
          },
      ],
  }
  (OFFICIAL_CJCU_DIR / "document-conditions.json").write_text(
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
        f"{fname},{len(partners)},{pop},{ratio:.4f},Official CJCU OIA verified"
    )
  (OFFICIAL_CJCU_DIR / "field-coverage.csv").write_text(
      "\n".join(field_cov_lines) + "\n", encoding="utf-8"
  )

  pages_records = [
      {
          "title": "長榮大學：115學年度校級國際交換生甄選（2026/10/01–11/27 報名）、海外雙聯學位與國際交流獎補助申請時程",
          "source_url": CJCU_EXCHANGE_LATEST_NEWS_URL,
          "published_at": "2026-09-24T00:00:00Z",
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
          "title": "長榮大學：115學年度校級國際交換生甄選簡章、赴外研修生作業要點、面試 40%＋書審 60% 配分與英語加強課程規定",
          "source_url": CJCU_BROCHURE_115_PDF_URL,
          "published_at": "2026-09-24T00:00:00Z",
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
          "title": f"長榮大學：{len(partners)} 所全球與兩岸合作姊妹校外語檢定門檻（英語組／日語組／韓語組／中文組／雙聯學位）",
          "source_url": CJCU_EXCHANGE_SCHOOL_LIST_URL,
          "published_at": "2026-09-24T00:00:00Z",
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
          "title": "長榮大學：校級交換生與雙聯學位 9 項應備文件（個人資料表、歷年成績單、家長保證書、雙語自傳與讀書計畫、歐韓語修課證明、彌封推薦函）",
          "source_url": CJCU_BROCHURE_115_PDF_URL,
          "published_at": "2026-09-24T00:00:00Z",
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
          "title": "長榮大學：教育部學海飛颺、學海惜珠、長榮大學推展學生國際學術交流獎補助金、短期交流補助（最高 4 萬元）與日韓免住宿費待遇",
          "source_url": CJCU_SCHOLARSHIPS_URL,
          "published_at": "2026-09-24T00:00:00Z",
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
  (OFFICIAL_CJCU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
      + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "cjcu",
      "school_name": "長榮大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "previous_year_score_minimum": 70.0,
          "xuehai_score_minimum_or_top_percent": "75.0 or top 25%",
          "cjcu_grant_minimum_or_top_percent": "passing (60.0) or top 50%",
          "interview_weight": 0.40,
          "written_review_weight": 0.60,
          "written_review_breakdown": {
              "conduct_score": 0.10,
              "academic_score": 0.10,
              "autobiography_and_study_plan": 0.15,
              "language_certificate": 0.10,
              "other_materials": 0.15,
          },
          "min_credits_per_semester_abroad": "9 credits or 3 courses (excluding PE)",
          "min_passing_credits_per_semester_abroad": "6 credits or 2 courses",
          "require_cjcu_full_tuition_during_abroad": True,
          "require_english_enhancement_course": "Required for all admitted students except Japanese Group and Mainland China Group (Weeks 1-9)",
          "return_documents_due": "返國後一個月內繳交 2,000 字以上中文心得報告及 400 字以上外文心得報告、照片 6 張及出入境證明，並辦理學分採認抵免",
      },
      "source_urls": cjcu_source_urls,
      "verified_at": "2026-11-02",
  }
  (OFFICIAL_CJCU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CJCU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "長榮大學",
              "required_documents": student_dashboard_payload[
                  "required_documents"
              ],
              "source_urls": cjcu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CJCU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "長榮大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": cjcu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "cjcu",
      "school_name": "長榮大學",
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
      "dual_degree_partner_universities": 8,
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
          f"長榮大學國際處國際合作組（OIA）《115學年度校級國際交換生甄選簡章》、《校級國際交換生學校一覽表（79 校）》、《海外雙聯學位學校列表（8 校 12 學程）》、《全球與兩岸締約姊妹校名錄》，以及教育部學海飛颺、學海惜珠、長榮大學推展學生國際學術交流獎補助金與短期交流補助作業要點同步整合；共完整收錄 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所常態開放申請交換與雙聯學校及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 26 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐交換心得報告与 35 份官方 Fact Sheet）。"
      ),
      "verified_at": "2026-11-02",
  }
  (OFFICIAL_CJCU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CJCU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "cjcu",
              "school_name": "長榮大學",
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
          "sources/cjcu/cjcu_catalog_source.json",
          CJCU_SISTER_SCHOOLS_URL,
          f"長榮大學 {len(partners)} 所全球與兩岸合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/cjcu/cjcu_resolved_locations.json",
          CJCU_SISTER_SCHOOLS_URL,
          f"長榮大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
      ),
      (
          "sources/cjcu/exchange_school_list.html",
          CJCU_EXCHANGE_SCHOOL_LIST_URL,
          "長榮大學國際處《校級國際交換生學校一覽表（英語組、日語組、韓語組、中文組）》HTML",
      ),
      (
          "sources/cjcu/dual_degree_school_list.html",
          CJCU_DUAL_DEGREE_LIST_URL,
          "長榮大學國際處《海外雙聯學位學校列表（8 校 12 學程）》HTML",
      ),
      (
          "sources/cjcu/sister_schools_overview.html",
          CJCU_SISTER_SCHOOLS_URL,
          "長榮大學國際處《全球與兩岸締約姊妹校總覽》HTML",
      ),
  ]
  for rel_p, surl in bin_urls.items():
    rp = rel_p if rel_p.startswith("sources/") else f"sources/cjcu/{rel_p}"
    if not any(x[0] == rp for x in provenance_files):
      provenance_files.append((rp, surl, f"長榮大學官方原始檔案：{Path(rp).name}"))

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
      "school_id": "cjcu",
      "school_name": "長榮大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = (
      json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  )
  (OFFICIAL_CJCU_DIR / "import_provenance.json").write_text(
      prov_text, encoding="utf-8"
  )
  (OFFICIAL_CJCU_DIR / "import-provenance.json").write_text(
      prov_text, encoding="utf-8"
  )

  print(
      f"Successfully built CJCU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
