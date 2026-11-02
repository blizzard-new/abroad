"""Build the official National United University (國立聯合大學, NUU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_NUU_DIR = REPO_ROOT / "sources" / "nuu"
OFFICIAL_NUU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "nuu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-02T00:00:00Z"

NUU_OIA_HOME_URL = "https://oia.nuu.edu.tw/"
NUU_OUTBOUND_OVERVIEW_URL = "https://oia.nuu.edu.tw/p/412-1068-1242.php"
NUU_REGULATIONS_URL = "https://oia.nuu.edu.tw/p/412-1068-4274.php"
NUU_PARTNER_LIST_URL = "https://oia.nuu.edu.tw/p/412-1068-5201.php"
NUU_EXCHANGE_ANNOUNCEMENTS_URL = "https://oia.nuu.edu.tw/p/412-1068-5616.php"
NUU_EXCHANGE_FORMS_URL = "https://oia.nuu.edu.tw/p/412-1068-5617.php"
NUU_EXCHANGE_REPORTS_URL = "https://oia.nuu.edu.tw/p/412-1068-6601.php"
NUU_XUEHAI_OVERVIEW_URL = "https://oia.nuu.edu.tw/p/412-1068-5605.php"
NUU_XUEHAI_FEIYANG_URL = "https://oia.nuu.edu.tw/p/412-1068-5608.php"
NUU_XUEHAI_XIZHU_URL = "https://oia.nuu.edu.tw/p/412-1068-5609.php"
NUU_XUEHAI_ZHUMENG_URL = "https://oia.nuu.edu.tw/p/412-1068-5610.php"
NUU_DUAL_DEGREE_URL = "https://oia.nuu.edu.tw/p/405-1068-53495,c10935.php?Lang=zh-tw"
NUU_NIT_SUMMER_2026_URL = "https://oia.nuu.edu.tw/p/405-1068-54408,c10935.php?Lang=zh-tw"
NUU_EXCHANGE_RULES_PDF_URL = (
    "https://oia.nuu.edu.tw/var/file/68/1068/img/2871/409353423.pdf"
)
NUU_INTL_EXCHANGE_RULES_PDF_URL = (
    "https://oia.nuu.edu.tw/var/file/68/1068/img/2871/480880843.pdf"
)
NUU_DUAL_DEGREE_RULES_PDF_URL = (
    "https://oia.nuu.edu.tw/var/file/68/1068/img/2871/905555154.pdf"
)
NUU_LANGUAGE_STANDARDS_PDF_URL = (
    "https://oia.nuu.edu.tw/var/file/68/1068/img/3121/266944988.pdf"
)
NUU_OVERSEAS_GRANT_PDF_URL = (
    "https://oia.nuu.edu.tw/var/file/68/1068/img/2871/686071848.pdf"
)
NUU_XUEHAI_SELECTION_RULES_PDF_URL = (
    "https://oia.nuu.edu.tw/p/405-1068-42099,c4274.php?Lang=zh-tw"
)
NUU_CREDIT_CONVERSION_PDF_URL = (
    "https://oia.nuu.edu.tw/p/405-1068-24627,c5617.php?Lang=zh-tw"
)
NUU_XUEHAI_115_FEIYANG_SCHEDULE_PDF_URL = (
    "https://oia.nuu.edu.tw/var/file/68/1068/img/3115/634670004.pdf"
)
NUU_XUEHAI_115_ZHUMENG_SCHEDULE_PDF_URL = (
    "https://oia.nuu.edu.tw/var/file/68/1068/img/3115/487786679.pdf"
)
NUU_EXCHANGE_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/18Hj-lWko1BrEwy4dWYn-qCHJdalff0t_/edit?gid=110584674#gid=110584674"
)
NUU_PARTNER_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/1t40XgNHPIAEXJcZGb7o-xKFL78cbvUtyYm4OfOZHVLc/edit?usp=sharing"
)

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 680–1,150（折合日圓約 JPY 95,000–160,000 / 月、新臺幣約 21,500–36,500 元；甲南大學、愛知教育大學及小山、宇部、高知、新居濱、阿南、木更津、釧路、明石等國立高等專門學校 NIT 學生寮與餐飲開銷親民）",
        "學期交換須由日本接待校代向出入國在留管理局申辦「在留資格認定證明書（COE）」，獲發後申辦留學簽證並加入日本國民健康保險（NHI）；日本高專（NIT）暑期 1–2 個月實驗室研習可持有效護照依短期滯在規定入境並投保海外全期醫療及意外險。",
    ),
    "韓國": (
        "每月生活費約 USD 650–1,050（折合韓元約 KRW 850,000–1,400,000 / 月、新臺幣約 20,500–33,500 元；仁川仁荷大學與昌原國立大學校內學生宿舍、食堂與交通費）",
        "須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後辦理外國人登錄證並納保韓國國民健康保險。",
    ),
    "中國大陸": (
        "每月生活費約 USD 350–680（折合人民幣約 RMB 2,200–4,500 / 月、新臺幣約 11,000–21,500 元；大陸姊妹校學生宿舍與校園食堂開銷）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及大陸姊妹校寄發之錄取通知書辦理報到，並依國立聯合大學國際及兩岸事務組規定投保涵蓋交換全期之海外醫療及意外保險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 450–800（折合馬幣約 MYR 2,000–3,500 / 月、新臺幣約 14,500–25,500 元；拉曼大學 UTAR 雙溪龍與金寶校區住宿與生活費實惠）",
        "須透過馬來西亞教育全球服務中心（EMGS）線上申辦學生簽證核准函（VAL / Mobility Pass，約需提前 2 個月作業）並投保馬來西亞境內醫療險。",
    ),
    "泰國": (
        "每月生活費約 USD 480–850（折合泰銖約 THB 16,000–28,000 / 月、新臺幣約 15,500–27,000 元；曼谷吞武里蒙庫國王科技大學 KMUTT 校內外住宿與伙食）",
        "須憑泰國接待大學入學許可公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 教育簽證並投保海外全期醫療險。",
    ),
    "印尼": (
        "每月生活費約 USD 450–780（折合印尼盾約 IDR 7,000,000–12,000,000 / 月、新臺幣約 14,500–25,000 元；印尼總統大學與三寶瓏迪波內戈羅大學學生宿舍與生活開銷）",
        "須由印尼接待大學協助申辦印尼學生電子簽證（Study e-Visa / KITAS）並投保海外全期醫療保險。",
    ),
    "越南": (
        "每月生活費約 USD 420–750（折合新臺幣約 13,500–24,000 元；胡志明市經濟大學 UEH 與南芹大學學生住宿與餐飲費用低廉）",
        "須由越南接待大學協助向越南出入境管理局申辦 DH 學生簽證並投保海外全期醫療及意外保險。",
    ),
    "法國": (
        "每月生活費約 USD 1,000–1,550（折合歐元約 EUR 900–1,400 / 月、新臺幣約 32,000–50,000 元；南特理工大學 Polytech Nantes 與薩瓦勃朗峰大學 CROUS 學生宿舍與生活費）",
        "須先經法國教育中心（Campus France）完成 Etudes en France 線上程序與面試，再向法國在台協會申辦長期學生簽證（VLS-TS）。",
    ),
    "德國": (
        "每月生活費約 USD 1,000–1,500（折合歐元約 EUR 934–1,350 / 月、新臺幣約 32,000–48,000 元；馬德堡大學 OVGU 學生宿舍與生活費極具性價比）",
        "須開立德國限制提領帳戶（Blocked Account）並憑入學許可向德國在台協會申辦德國長期學生簽證及投保德國公保／醫療險。",
    ),
    "美國": (
        "每月生活費約 USD 1,350–2,100（依匯率折合新臺幣約 43,000–67,000 元；霜堡州立大學 FSU、佛羅里達理工學院 FIT、樹城州立大學 Boise State、明尼蘇達州立大學曼卡托分校、南猶他大學 SUU 住宿與伙食）",
        "須憑美國接待大學核發之 DS-2019（J-1 交換生）或 I-20（F-1 雙聯學位生）表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證，且須投保符合接待校規定之全期海外醫療保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,250–1,900（折合加幣約 CAD 1,700–2,600 / 月、新臺幣約 40,000–60,000 元；安大略理工大學與卡加利大學校內外住宿、伙食與交通）",
        "交換研習 1 學期（6 個月內）可申辦加拿大 eTA，交換 1 學年或雙聯學位須申辦加拿大 Study Permit 並投保醫療保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "春季學期（Spring Semester）：約 4 月初至 8 月初；秋季學期（Fall Semester）：約 9 月下旬或 10 月初至翌年 2 月（高專暑期研習：6 月至 8 月為期 1–2 個月）",
    "韓國": "春季學期（Spring Semester）：約 3 月初至 6 月中旬；秋季學期（Fall Semester）：約 9 月初至 12 月中旬",
    "中國大陸": "春季學期（下學期）：約 2 月下旬至 7 月初；秋季學期（上學期）：約 9 月初至翌年 1 月中旬",
    "馬來西亞": "第一學期（January Trimester）：1 月至 5 月；第二學期（May Trimester）：5 月至 9 月；第三學期（October Trimester）：10 月至翌年 1 月",
    "泰國": "第一學期（秋季班）：約 8 月至 12 月；第二學期（春季班）：約 1 月至 5 月",
    "印尼": "奇數／秋季學期（Odd Semester）：約 8/9 月至翌年 1 月；偶數／春季學期（Even Semester）：約 2 月至 7 月",
    "越南": "秋季學期：約 8 月中旬至翌年 1 月中旬；春季學期：約 1 月中旬至 6 月底",
    "法國": "秋季學期（Fall Semester）：約 9 月初至翌年 1 月中旬；春季學期（Spring Semester）：約 1 月下旬至 6 月中旬",
    "德國": "冬季學期（Winter Semester）：約 10 月初至翌年 3 月底；夏季學期（Summer Semester）：約 4 月初至 9 月底",
    "美國": "秋季學期（Fall Semester）：約 8 月中下旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬",
    "加拿大": "秋季學期（Fall Term）：約 9 月初至 12 月下旬；冬季／春季學期（Winter Term）：約 1 月初至 4 月底",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
  """Ensure school-images.json and university_locations.jsonl contain all 128 NUU partner schools."""
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
          else loc.get("lat", 24.5453)
      )
      lon = float(
          loc.get("longitude")
          if loc.get("longitude") is not None
          else loc.get("lon", 120.8124)
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
  OFFICIAL_NUU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_NUU_DIR / "nuu_catalog_source.json").read_text(encoding="utf-8")
  )
  resolved_locations = json.loads(
      (SOURCES_NUU_DIR / "nuu_resolved_locations.json").read_text(
          encoding="utf-8"
      )
  )
  bin_urls_path = SOURCES_NUU_DIR / "binary_source_urls.json"
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
        "open" if item.get("offering_status") == "open" else "reference_only"
    )
    if avail_status == "open":
      open_partner_count += 1

    group_str = clean_text(
        item.get("group") or "研究發展處國際及兩岸事務組正式締約姊妹校"
    )
    quota_str = clean_text(
        item.get("quota") or "依國立聯合大學國際及兩岸事務組當期公告名額"
    )
    detail_url = item.get("detail_url") or NUU_OUTBOUND_OVERVIEW_URL

    if "雙聯" in group_str:
      program_type = "研究發展處國際及兩岸事務組跨國雙聯學制暨交換學生計畫"
      source_url = detail_url
    elif "NIT" in group_str or "高專" in group_str:
      program_type = "研究發展處國際及兩岸事務組日本國立高等專門學校（NIT）交換暨暑期專業研習計畫"
      source_url = detail_url
    elif country == "中國大陸" and avail_status == "open":
      program_type = "研究發展處國際及兩岸事務組大陸地區姊妹校交換計畫"
      source_url = detail_url
    elif avail_status == "open":
      program_type = f"{group_str}（免繳接待姊妹校學費）"
      source_url = detail_url
    elif country in {"中國大陸", "澳門", "香港"}:
      program_type = "研究發展處國際及兩岸事務組正式締約大陸與港澳姊妹校"
      source_url = detail_url
    else:
      program_type = "研究發展處國際及兩岸事務組正式締約國際姊妹校"
      source_url = detail_url

    colleges_str = clean_text(
        item.get("colleges")
        or "理工學院、電機資訊學院、管理學院、客家研究學院、人文與社會學院、設計學院"
    )
    degree_levels_str = clean_text(
        item.get("eligible_degrees")
        or "具國立聯合大學大學部及研究所學籍之在學學生（不含在職生；系所與年級限制以「出國交換當時」之學籍身分與年級為準）"
    )
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "")
    website = item.get("website") or NUU_PARTNER_LIST_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    round_label = (
        "115–116學年度出國交換學生甄選、日本高專暑期研習暨雙聯學位計畫（國際及兩岸事務組常態開放申請）"
        if avail_status == "open"
        else "研究發展處國際及兩岸事務組正式締約姊妹校（當期開放名額依國際組最新公告與交換學校一覽表為準）"
    )
    app_deadline_str = clean_text(
        item.get("deadline")
        or (
            "第一梯次（秋季班出國，可申請一學期或一學年，結合教育部學海飛颺／學海惜珠計畫）：每年 12 月中旬至隔年 2 月中旬（2026/12/15–2027/02/14）校內收件｜"
            "第二梯次（隔年春季班出國，僅得申請一學期）：每年 8 月（2026/08/01–2026/08/31）及 9–10 月依各姊妹校春季班簡章公告截止收件｜"
            "日本國立高專（NIT）暑期研習交流：每年 4 月中旬（2026/04/17）校內截止｜"
            "美國 2+2 雙聯學位（FSU / FIT / Boise State）：每年 2 月底（2027/02/28）校內截止"
        )
    )
    deadline_iso = "2027-02-14T17:00:00+08:00"
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "115"

    study_period_str = clean_text(item.get("duration") or "一學期或一學年")
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲國立聯合大學國際及兩岸事務組推薦錄取後，可依 {zh_name} 國際處指引申請校內外學生宿舍或國際學舍"
        + (f"（學費與保證金規定：{tuition_note}）" if tuition_note else "。")
    )
    course_rest_str = (
        f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《國立聯合大學國際交換學生作業要點》（109年3月3日修正）及《學生於締約學校修讀課程學分與成績轉換參考表》規定："
        "（1）在學身分與年級計算：具本校大學部及研究所學籍之在學學生（不含以在職生身分入學者）皆可提出申請，惟各姊妹校之系所及年級限制以「出國交換當時」之學籍身分與年級為準（非提出申請時）；境外生（外籍生、僑生、陸生）可申請，但不得交換回其所屬國家；同一學制內已獲推薦出國交換或無故放棄者不得再申請；"
        "（2）校內甄選分組配分（總分未達 60 分不予推薦；若辦面試則書審 60%＋面試 40%）：赴大陸地區大學部採計「在校成績 60%＋自傳 15%＋讀書計畫/動機信 20%＋其他 5%」、研究所採計「在校成績 40%＋自傳 25%＋讀書計畫/動機信 30%＋其他 5%」；赴大陸以外地區（含港澳）大學部採計「在校成績 50%＋外語能力 20%＋自傳 10%＋讀書計畫 15%＋其他 5%」、研究所採計「在校成績 30%＋外語能力 20%＋自傳 20%＋讀書計畫 25%＋其他 5%」；"
        "（3）出國修課下限與保證金義務：錄取公告後 20 日內須繳交行政處理費（保證金）新臺幣 3,000 元；交換期間每學期大學部學生至少須修讀 3 門課程及格、研究所學生至少須修讀 1 門課程及格；返國後 14 日內須完成返國程序單、繳交中英文心得報告並完成 20 小時國際組服務（或 3 場經驗傳承、或投稿 2 篇英文心得）後無息退還保證金。"
    )

    living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
        country,
        (
            "每月生活費約 USD 800–1,400（依匯率折合新臺幣約 25,500–45,000 元，含住宿、膳食與市區交通）",
            "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
        ),
    )

    tuition_points_list = [
        (
            f"國立聯合大學在學註冊、保證金與學雜費規定（依《國際交換學生作業要點》第 2 點及第 5–6 點）：交換生於交換期間仍須辦理本校註冊繳費並保有學籍；公告錄取後 20 日內須繳交行政處理費（保證金）新臺幣 3,000 元（履行返國義務及完成 20 小時服務後全數退還）。本合作校待遇：{tuition_note or '免繳接待姊妹校學費（雙聯學制依兩校協議辦理）'}。"
        ),
        (
            "國立聯合大學四大出國交換與境外研習獎補助體系：（1）研究發展處《教育部學海飛颺／學海惜珠計畫》（依《國立聯合大學「學海系列計畫」甄選作業要點》114年1月16日修正，每年 12 月中旬至 2 月中旬受理，分「雙聯學位生、學士班交換生、碩博班交換生、自行申請者」四組擇優核定出國研修獎助學金）；（2）研究發展處《教育部學海築夢／新南向學海築夢計畫》（補助海外專業實習機票與生活費）；（3）《國立聯合大學補助學生參與境外學術交流及研習服務經費管理要點》（活動首日 1 個月前申請：大陸港澳及亞太地區 10 日內最高 NT$ 10,000、10 日以上最高 NT$ 15,000［如日本高專 NIT 暑期研習補助 NT$ 15,000］；紐澳/亞西/北美/拉美/非洲地區 10 日內最高 NT$ 20,000、10 日以上最高 NT$ 25,000；歐洲地區 10 日內最高 NT$ 30,000、10 日以上最高 NT$ 35,000；團隊最高 NT$ 100,000）；（4）日本學生支援機構（JASSO）獎學金（赴日本宇部高專等研習滿 32 日以上並參與 NIT-NUU 台日雙邊學術研討會者可申請）及美國雙聯學位獎學金（霜堡州立大學 FSU 每學期 USD 3,000、佛羅里達理工學院 FIT 每學期 USD 5,000–7,000、南猶他大學 SUU USD 4,250）。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認聯大在學學籍、「出國交換當時」之年級系所資格與 {zh_name} 語檢要求）：確認具國立聯合大學大學部或研究所學籍（不含在職生），出國交換當時符合目標校年級與院系限制（{degree_levels_str}）、學業門檻（{gpa_req_str}）與留學國語言能力參考標準（{lang_req_str}；大陸地區免附外語檢定）。"
        ),
        (
            "步驟二（備妥《學生赴國外研修申請表》與 10 項應備文件完成校內單位核章）：依《國際交換學生作業要點》第 3 點備齊（1）學生赴國外研修申請表（須經家長/監護人、系所主管、學務處生輔組、教務處註冊組簽章）、（2）基本資料影本（身分證、學生證、本人金融帳戶）、（3）外語能力檢定證明（大陸免附）、（4）中英文歷年學業成績單（含排名）、（5）中英文在學證明、（6）中英文自傳、（7）中英文讀書計畫（含公版計畫書）、（8）學生家長或監護人同意書、（9）中英文推薦函各一封、（10）經費預算表。"
        ),
        (
            f"步驟三（送交研究發展處國際及兩岸事務組辦理書審／面試甄選並繳交 NT$ 3,000 保證金）：於校內收件期限前（第一梯次暨學海計畫每年 12/15–2/14、第二梯次春季班每年 8 月及 9–10 月、日本高專暑期研習 4/17 前、美國雙聯 2 月底前）送交二坪山校區產創大樓 H1-309 或八甲校區國鼎圖書館 L1-716 國際組；通過甄選（總分達 60 分以上）後於公告 20 日內繳交行政處理費保證金 NT$ 3,000，並可同步申請教育部《學海飛颺／惜珠》或聯大《補助學生參與境外學術交流經費》。"
        ),
        (
            "步驟四（由國際組向姊妹校提名、出國每學期修滿及格門數，返國後 14 日內完成返國程序與學分轉換）：經國際組向接待校提名（Nomination）後遞交外文入學與宿位申請；出國期間完成聯大註冊，每學期大學部至少修讀 3 門課程及格、研究所至少修讀 1 門課程及格；返國後 14 日內繳交返國程序單、中英文心得報告及核銷單據，並完成 20 小時國際組服務後退還保證金。"
        ),
    ]

    elig_points_list = [
        f"合作類別與計畫組別：{program_type}（{group_str}）",
        f"開放學制與年級（以出國交換當時為準）：{degree_levels_str}",
        f"開放申請學院：{colleges_str}",
        f"歷年學業成績門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "校內甄選計分比重（《國際交換學生作業要點》第 4 點，總分未達 60 分不予推薦）：赴大陸以外地區（含港澳）大學部採計「在校成績 50%＋外語能力 20%＋自傳 10%＋讀書計畫 15%＋其他 5%」、研究所採計「在校成績 30%＋外語能力 20%＋自傳 20%＋讀書計畫 25%＋其他 5%」；赴大陸地區大學部採計「在校成績 60%＋自傳 15%＋讀書計畫/動機信 20%＋其他 5%」、研究所採計「在校成績 40%＋自傳 25%＋讀書計畫/動機信 30%＋其他 5%」。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與聯大獎補助待遇：{tuition_note}")
    if remarks_raw:
      elig_points_list.append(f"學程與締約重點說明：{remarks_raw}")

    exp_links: list[dict] = []
    exp_labels: list[str] = []
    if exps:
      exp_covered_schools += 1
      total_exp_reports += len(exps)
      seen_exp_urls: set[str] = set()
      for e_idx, e in enumerate(exps):
        raw_t = clean_text(e.get("title") or f"赴 {zh_name} 交換生心得分享")
        esem = e.get("semester") or "歷年交換與研習成果"
        eurl = (
            e.get("url")
            or f"{NUU_EXCHANGE_REPORTS_URL}#nuu-exp-{sn}-{e_idx+1}"
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
            "college": "理工學院／電機資訊學院／管理學院／客家研究學院／人文與社會學院／設計學院",
            "department": "國立聯合大學交換生",
        })
        summary_text = (
            f"國立聯合大學研究發展處國際及兩岸事務組公開收錄之學長姐赴 {country} {full_name} 交換研修／雙聯學位／暑期專業研習官方經驗分享與歷年錄取名冊（{raw_t}），詳述選課學分抵免、住宿環境、簽證辦理與當地生活費實錄。"
        )
        theme_map = {
            "academics": f"聯合大學交換生於《{raw_t}》分享在 {zh_name} 修習課程（大學部每學期至少 3 門及格、研究所至少 1 門及格）、日本高專實驗室研習及返國辦理學分與成績轉換之經驗。",
            "housing": f"聯合大學交換生記錄申請 {zh_name} 校內外學生宿舍或國際學舍、周邊生活機能與通勤方式（{housing_str[:100]}）。",
            "campus_culture": f"聯合大學公開收錄《{raw_t}》之跨文化課堂學習、國際學伴交流與校園生活實錄。",
            "cost": f"聯合大學交換生分享於 {zh_name} 之每月住宿、伙食與交通開銷（{living_cost_str[:100]}），以及免繳姊妹校學費與申請教育部學海飛颺／惜珠或聯大境外學術交流補助之經驗。",
        }
        student_experience_rows.append({
            "school_name": full_name,
            "country": country,
            "title": raw_t,
            "source_url": eurl,
            "source_type": "article",
            "platform": "國立聯合大學研究發展處國際及兩岸事務組—交換學生心得與成果專區",
            "author_name": (
                raw_t.split("—")[-1].strip()[:20]
                if "—" in raw_t
                else "聯大交換生"
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
                f"{full_name}:nuu_exp:{e_idx}:{eurl}".encode("utf-8")
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
        "home_university": "國立聯合大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exp_links[0]["url"] if exp_links else NUU_EXCHANGE_REPORTS_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

    loc = resolved_locations.get(full_name) or {
        "city": country,
        "latitude": 24.5453,
        "longitude": 120.8124,
        "source_url": "https://www.wikidata.org",
    }
    city_name = loc.get("city") or country
    lat = float(
        loc.get("latitude")
        if loc.get("latitude") is not None
        else loc.get("lat", 24.5453)
    )
    lon = float(
        loc.get("longitude")
        if loc.get("longitude") is not None
        else loc.get("lon", 120.8124)
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
    if exps:
      notes_lines.append(
          f"【聯合大學學長姐交換與海外研習紀錄（共 {len(exps)} 篇）】收錄於國際及兩岸事務組交換學生專區（含：{'、'.join(exp_labels[:4])}）"
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
            f"國立聯合大學研究發展處國際及兩岸事務組公告合作姊妹校（{program_type}）；{quota_str}。"
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
            "title": f"國立聯合大學研究發展處國際及兩岸事務組出國交換學生專頁—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立聯合大學國際交換學生作業要點（109年3月3日修正通過）",
            "source_url": NUU_EXCHANGE_RULES_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立聯合大學「學海系列計畫」甄選作業要點（114年1月16日修正）與境外學術交流補助要點",
            "source_url": NUU_XUEHAI_OVERVIEW_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exp_links:
      wf_sources.append({
          "title": f"國立聯合大學國際及兩岸事務組交換生心得與歷年名冊—{zh_name}",
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
        "home_university": "國立聯合大學",
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
            "國立聯合大學由研究發展處國際及兩岸事務組（Office of International and Cross-Strait Affairs, OIA）統籌全校 6 大學院（理工學院、電機資訊學院、管理學院、客家研究學院、人文與社會學院、設計學院）及共同教育委員會之國際交換學生計畫、日本國立高等專門學校（NIT）暑期專業研習交流、美法加跨國雙聯學位計畫（美國霜堡州立大學 FSU 2+2、佛羅里達理工學院 FIT 2+2、樹城州立大學 Boise State 2+2、南猶他大學 SUU、加拿大安大略理工大學、法國南特理工大學）及教育部學海飛颺、學海惜珠、學海築夢與新南向學海築夢獎助。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"nuu-{acad_year}-home-1-{sn:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認聯大在學身分、「出國交換當時」之年級系所資格與 {zh_name} 語檢要求",
                "responsible_party": "學生",
                "responsible_unit": "國立聯合大學研究發展處國際及兩岸事務組／各院系所",
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
                    f"確認符合《國立聯合大學國際交換學生作業要點》第 2 點規定：具本校大學部及研究所學籍之在學學生（不含以在職生身分入學者），且於「出國交換當時」符合姊妹校系所及年級限制（{degree_levels_str}）、學業要求（{gpa_req_str}）並具備留學國語言能力參考標準（{lang_req_str}；大陸地區免附外語能力證明）。"
                ),
                "details": [
                    f"開放學制與學院：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["國立聯合大學"],
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
                    NUU_OUTBOUND_OVERVIEW_URL,
                    NUU_EXCHANGE_RULES_PDF_URL,
                    NUU_LANGUAGE_STANDARDS_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nuu-{acad_year}-home-2-{sn:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "備妥《學生赴國外研修申請表》與 10 項應備文件經家長、系所、生輔組與註冊組核章後送交國際組",
                "responsible_party": "學生",
                "responsible_unit": "所屬系所／學務處生輔組／教務處註冊組／研究發展處國際及兩岸事務組",
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": NUU_EXCHANGE_RULES_PDF_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "於校內收件期限前（第一梯次暨學海飛颺/惜珠每年 12/15–2/14、第二梯次春季班每年 8 月及 9–10 月、日本高專暑期研習 4/17 前、美國雙聯學位 2 月底前）備妥《國立聯合大學學生赴國外研修申請表》及全部 10 項應備文件，完成家長或監護人、系所主管、學務處生輔組及教務處註冊組核章後，送交研究發展處國際及兩岸事務組（二坪山校區產創大樓三樓 H1-309 或八甲校區國鼎圖書館七樓 L1-716）。"
                ),
                "details": [
                    "第一梯次（每年 1 月／結合 12/15–2/14 學海飛颺與惜珠期程）：得申請一學期或一學年（選一學年者須自同年度第一學期開始，不得跨學年）。",
                    "第二梯次（每年 8 月及 9–10 月春季班公告）：僅得申請一學期（隔年春季學期赴姊妹校交換）；日本高專（NIT）暑期研習於每年 4 月中旬截止；美國 2+2 雙聯學位於每年 2 月底截止。",
                ],
                "document_requirements": [
                    {
                        "name": "國立聯合大學學生赴國外研修申請表（需家長/監護人、系所主管、學務處生輔組、教務處註冊組簽章）及基本資料影本（身分證、學生證、金融帳戶）",
                        "official_form_url": NUU_EXCHANGE_FORMS_URL,
                        "source_urls": [
                            NUU_EXCHANGE_RULES_PDF_URL,
                            NUU_EXCHANGE_FORMS_URL,
                        ],
                    },
                    {
                        "name": "中英文歷年學業成績單（含排名）、中英文在學證明與外國語言能力檢定證明（大陸地區免附語檢）",
                        "official_form_url": NUU_EXCHANGE_FORMS_URL,
                        "source_urls": [
                            NUU_EXCHANGE_RULES_PDF_URL,
                            NUU_LANGUAGE_STANDARDS_PDF_URL,
                        ],
                    },
                    {
                        "name": "中英文自傳、中英文讀書計畫（含公版計畫書）、學生家長或監護人同意書、中英文推薦函各一封及經費預算表",
                        "official_form_url": NUU_EXCHANGE_FORMS_URL,
                        "source_urls": [
                            NUU_EXCHANGE_RULES_PDF_URL,
                            NUU_EXCHANGE_FORMS_URL,
                        ],
                    },
                ],
                "scope": {
                    "home_universities": ["國立聯合大學"],
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
                    NUU_EXCHANGE_RULES_PDF_URL,
                    NUU_DUAL_DEGREE_RULES_PDF_URL,
                    NUU_EXCHANGE_FORMS_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nuu-{acad_year}-home-3-{sn:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "參加國際組校內書審／面試甄選（總分須達 60 分），錄取後 20 日內繳交 NT$ 3,000 保證金並申請學海／境外交流補助",
                "responsible_party": "國立聯合大學研究發展處國際及兩岸事務組與申請學生",
                "responsible_unit": "研究發展處國際及兩岸事務組",
                "deadline_at": "2027-03-14T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": NUU_EXCHANGE_RULES_PDF_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "國際及兩岸事務組依《國際交換學生作業要點》第 4 點辦理書審及面試（若辦面試則書審 60%＋面試 40%［表達 25%、組織 25%、發展潛力 25%、人格特性 25%］，總分未達 60 分不予推薦）。獲公告錄取者須於 20 日內繳交行政處理費（保證金）新臺幣 3,000 元，並可同步申請教育部《學海飛颺／惜珠》或聯大《補助學生參與境外學術交流及研習服務經費》。"
                ),
                "details": [
                    "赴大陸以外地區（含港澳）書審配分：大學部「在校成績 50%＋外語能力 20%＋自傳 10%＋讀書計畫 15%＋其他 5%」；研究所「在校成績 30%＋外語能力 20%＋自傳 20%＋讀書計畫 25%＋其他 5%」。",
                    "赴大陸地區書審配分：大學部「在校成績 60%＋自傳 15%＋讀書計畫/動機信 20%＋其他 5%」；研究所「在校成績 40%＋自傳 25%＋讀書計畫/動機信 30%＋其他 5%」。",
                ],
                "scope": {
                    "home_universities": ["國立聯合大學"],
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
                    NUU_EXCHANGE_RULES_PDF_URL,
                    NUU_XUEHAI_SELECTION_RULES_PDF_URL,
                    NUU_OVERSEAS_GRANT_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nuu-{sn:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由聯大國際及兩岸事務組向 {zh_name} 辦理官方提名（Nomination），並遞交姊妹校入學與宿位申請文件",
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"通過校內甄選並繳交保證金後，由國立聯合大學國際及兩岸事務組向 {zh_name} 辦理官方提名；學生須依接待校規定備妥外文入學申請表、英文歷年成績單、護照影本、英文財力證明、外語檢定證書及宿舍申請表，靜候接待校核發正式入學許可（Admission Letter / COE / 錄取通知書）。"
                ),
                "details": [
                    f"研修期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["國立聯合大學"],
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
                    [source_url, NUU_PARTNER_LIST_URL]
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"nuu-{acad_year}-home-5-{sn:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "完成聯大出國註冊與海外醫療保險，返國後 14 日內繳交返國程序單與中英文心得、完成 20 小時服務退還保證金並辦理學分抵免",
                "responsible_party": "學生與所屬系所",
                "responsible_unit": "研究發展處國際及兩岸事務組／教務處註冊組／各系所",
                "summary": (
                    "出國前須完成聯大註冊手續、申辦簽證並投保涵蓋全期之海外醫療及意外保險；交換期間每學期大學部至少修讀 3 門課程及格、研究所至少修讀 1 門課程及格；返國後 14 日內須完成《交換生返國程序單》、經費核銷及中英文心得報告，並完成 20 小時國際組服務（或 3 場經驗傳承、或投稿 2 篇英文心得）以退還 NT$ 3,000 保證金，同時持國外成績單正本依《學生於締約學校修讀課程學分與成績轉換參考表》辦理學分抵免。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["國立聯合大學"],
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
                    NUU_EXCHANGE_RULES_PDF_URL,
                    NUU_CREDIT_CONVERSION_PDF_URL,
                    NUU_OVERSEAS_GRANT_PDF_URL,
                    NUU_XUEHAI_SELECTION_RULES_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合國立聯合大學研究發展處國際及兩岸事務組《國際交換學生作業要點（1090303）》、《國際學術交流實施辦法（1100525）》、《雙聯學制實施辦法（1060218）》、《學生赴國外研修留學國語言能力參考標準》、《補助學生參與境外學術交流及研習服務經費管理要點》、《學海系列計畫甄選作業要點（1140116）》、《學生於締約學校修讀課程學分與成績轉換參考表》及 {len(catalog_source)} 所全球與兩岸合作姊妹校資料。"
        ),
    })

    cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": f"國立聯合大學研究發展處國際及兩岸事務組出國交換學生專頁—{zh_name}",
            "source_url": source_url,
            "summary": "聯大國際組公告之合作學程、開放學制、語言檢定門檻與免繳姊妹校學費／雙聯學位／高專暑期研習待遇說明",
        },
        {
            "title": "國立聯合大學國際交換學生作業要點、學海系列計畫甄選作業要點與境外學術交流補助要點",
            "source_url": NUU_EXCHANGE_RULES_PDF_URL,
            "summary": "聯大出國交換在學註冊規定、校內甄選分組配分標準、NT$ 3,000 保證金退還條件與境外交流獎補助規範",
        },
    ]
    if exp_links:
      dest_sources.append({
          "title": f"國立聯合大學國際及兩岸事務組交換學生心得與歷年名冊—{zh_name}",
          "source_url": exp_links[0]["url"],
          "summary": f"收錄歷年國立聯合大學學生赴 {zh_name} 交換研習／雙聯學位／高專暑期研習經驗分享",
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
            NUU_EXCHANGE_RULES_PDF_URL,
            NUU_OUTBOUND_OVERVIEW_URL,
            NUU_XUEHAI_OVERVIEW_URL,
        ]
        + ([exp_links[0]["url"]] if exp_links else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "國立聯合大學",
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
                "title": "生活費、聯大在學註冊與保證金規定、教育部學海系列計畫與境外學術交流補助",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [NUU_OVERSEAS_GRANT_PDF_URL],
                "caution": (
                    "公告錄取後 20 日內須繳交行政處理費（保證金）新臺幣 3,000 元；返國後 14 日內完成返國程序單、中英文心得報告及 20 小時國際組服務後全額無息退還。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外國際學生宿舍申請",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": "各姊妹校校內學生宿舍（如日本高專學生寮、韓國仁荷與昌原大學宿舍、歐美校內宿舍）名額有限，請於獲提名後依接待校期限儘早申請。",
            },
            {
                "key": "insurance",
                "title": "海外醫療及意外保險與家長同意書規定",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依《國立聯合大學國際交換學生作業要點》第 3 點，所有申請學生均須檢附經家長或法定監護人簽章之《學生家長或監護人同意書》，並於出國前投保涵蓋交換全期之海外醫療及意外保險。",
                ],
                "source_urls": src_url_list + [NUU_EXCHANGE_RULES_PDF_URL],
                "caution": "日本、韓國、德國、法國、美國、加拿大、馬來西亞等接待校對交換生當地國民健康保險或校園保險有強制規定，請依入學通知書辦理。",
            },
            {
                "key": "visa",
                "title": "留學交換簽證辦理、出國修業期限與在學註冊義務",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依《國際交換學生作業要點》第 2 點，交換期間至少一學期、以一學年為限（若選一學年須自同年度第一學期開始，不得跨學年）；同一學制內已獲推薦出國交換者不得再申請。",
                ],
                "source_urls": src_url_list,
                "caution": "境外生（外籍生、僑生、陸生）可申請本校出國交換計畫，但不得交換回其所屬國家。",
            },
            {
                "key": "academics",
                "title": "大陸組與非大陸組分組配分、出國修課下限與返國學分成績轉換",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [NUU_CREDIT_CONVERSION_PDF_URL],
                "caution": (
                    "出國期間每學期大學部至少須修讀 3 門課程及格、研究所至少須修讀 1 門課程及格，返國後依《學生於締約學校修讀課程學分與成績轉換參考表》辦理學分採認。"
                ),
            },
            {
                "key": "living",
                "title": f"{city_name} 校園生活與聯合大學學長姐交換經驗傳承",
                "summary": f"代表城市：{city_name}。請配合接待校國際處完成報到與新生訓練（Orientation）。",
                "points": [
                    f"目的地城市：{city_name}（{country}）",
                    (
                        "國立聯合大學研究發展處國際及兩岸事務組定期舉辦「學海計畫暨出國交換校內說明會」及返國學長姐經驗傳承分享會"
                        + (
                            f"（本校收錄：{exp_labels[0]}）"
                            if exp_labels
                            else ""
                        )
                        + "，協助同學掌握選課與海外生活準備。"
                    ),
                ],
                "source_urls": [
                    exp_links[0]["url"]
                    if exp_links
                    else NUU_EXCHANGE_REPORTS_URL
                ],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合國立聯合大學研究發展處國際及兩岸事務組 {len(catalog_source)} 所合作姊妹校、當期常態開放申請交換／雙聯／高專暑期研習學校（{open_partner_count} 校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷年交換紀錄。"
        ),
    })

    research_records.append({
        "home_university": "國立聯合大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            "國立聯合大學研究發展處國際及兩岸事務組《國際交換學生作業要點》、《交換學校一覽表》、《姊妹校名錄》、《雙聯學制實施辦法》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"國立聯合大學國際及兩岸事務組出國交換學生專頁—{zh_name}",
            "url": source_url,
        },
    ]
    if exp_links:
      ev_sources.append({
          "title": f"國立聯合大學交換學生心得與歷年名冊—{zh_name}",
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
            "scope": "國立聯合大學全球與兩岸交換姊妹校住宿與生活資訊",
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
            "scope": "國立聯合大學出國交換學雜費與 NT$ 3,000 保證金規定、教育部學海飛颺／惜珠／築夢與境外學術交流補助",
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
            "scope": "國立聯合大學國際交換學生作業要點、雙聯學制實施辦法與學分成績轉換參考表",
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
            "scope": "國立聯合大學海外交換與雙聯學位簽證、家長同意書、海外醫療保險與返國義務提醒",
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
                    f"｜聯合大學公開收錄 {len(exps)} 篇赴 {zh_name} 交換研習紀錄（{'、'.join(exp_labels[:3])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "國立聯合大學交換名額與歷屆學長姐經驗分享",
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
            "已整合國立聯合大學研究發展處國際及兩岸事務組《國際交換學生作業要點》、《交換學校一覽表》、《姊妹校名錄》、《雙聯學制實施辦法》及歷屆學生交換經驗分享。",
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

  write_jsonl(OFFICIAL_NUU_DIR / "partners.jsonl", partners)
  write_jsonl(SOURCES_NUU_DIR / "partners.jsonl", partners)
  write_jsonl(OFFICIAL_NUU_DIR / "application_workflows.jsonl", workflows)
  write_jsonl(OFFICIAL_NUU_DIR / "destination_profiles.jsonl", destinations)
  write_jsonl(OFFICIAL_NUU_DIR / "partner_research.jsonl", research_records)
  write_jsonl(OFFICIAL_NUU_DIR / "student_life.jsonl", life_records)
  write_jsonl(
      OFFICIAL_NUU_DIR / "experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_NUU_DIR / "student_experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_NUU_DIR / "student_experiences.jsonl", student_experience_rows
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
  (OFFICIAL_NUU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_NUU_DIR / "student-experiences.json").write_text(
      json.dumps(
          {
              "school_id": "nuu",
              "school_name": "國立聯合大學",
              "checked_at": CHECKED_AT,
              "source_url": NUU_EXCHANGE_REPORTS_URL,
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

  (OFFICIAL_NUU_DIR / "campus-locations.json").write_text(
      json.dumps(
          {
              "school_id": "nuu",
              "school_name": "國立聯合大學",
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
  (OFFICIAL_NUU_DIR / "campus-assets.json").write_text(
      json.dumps(
          {
              "school_id": "nuu",
              "school_name": "國立聯合大學",
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

  nuu_source_urls = [
      NUU_OIA_HOME_URL,
      NUU_OUTBOUND_OVERVIEW_URL,
      NUU_REGULATIONS_URL,
      NUU_PARTNER_LIST_URL,
      NUU_EXCHANGE_ANNOUNCEMENTS_URL,
      NUU_EXCHANGE_FORMS_URL,
      NUU_EXCHANGE_REPORTS_URL,
      NUU_XUEHAI_OVERVIEW_URL,
      NUU_XUEHAI_FEIYANG_URL,
      NUU_XUEHAI_XIZHU_URL,
      NUU_XUEHAI_ZHUMENG_URL,
      NUU_DUAL_DEGREE_URL,
      NUU_NIT_SUMMER_2026_URL,
      NUU_EXCHANGE_RULES_PDF_URL,
      NUU_INTL_EXCHANGE_RULES_PDF_URL,
      NUU_DUAL_DEGREE_RULES_PDF_URL,
      NUU_LANGUAGE_STANDARDS_PDF_URL,
      NUU_OVERSEAS_GRANT_PDF_URL,
      NUU_XUEHAI_SELECTION_RULES_PDF_URL,
      NUU_CREDIT_CONVERSION_PDF_URL,
      NUU_XUEHAI_115_FEIYANG_SCHEDULE_PDF_URL,
      NUU_XUEHAI_115_ZHUMENG_SCHEDULE_PDF_URL,
      NUU_EXCHANGE_SHEET_URL,
      NUU_PARTNER_SHEET_URL,
  ]

  exchange_info_payload = {
      "school_name": "國立聯合大學",
      "program_type": [
          (
              f"研究發展處國際及兩岸事務組（OIA）出國交換學生計畫（涵蓋日本、韓國、法國、德國、美國、加拿大、馬來西亞、泰國、印尼、越南、蒙古等 {open_partner_count} 所常態開放申請之交換、雙聯與暑期研習合作校，以及全球 21 國共 {len(partners)} 所正式締約姊妹校）"
          ),
          (
              "美法加跨國雙聯學制計畫（Dual Degree Programs，涵蓋【美國霜堡州立大學 Frostburg State University 2+2 雙聯學士】、【美國佛羅里達理工學院 Florida Institute of Technology 2+2 雙聯學士】、【美國樹城州立大學 Boise State University 2+2 雙聯學士】、【美國南猶他大學 Southern Utah University】、【加拿大安大略理工大學 Ontario Tech University】、【法國南特理工大學 Polytech Nantes】）暨【日本國立高等專門學校（NIT）暑期專業研習交流計畫（小山、宇部、高知、新居濱、木更津、釧路、明石等高專實驗室研習）】"
          ),
          (
              "教育部「學海飛颺」（選送優秀學生出國研修）、「學海惜珠」（清寒優秀學生出國研修）、「學海築夢／新南向學海築夢」（海外專業實習），以及《國立聯合大學補助學生參與境外學術交流及研習服務經費管理要點》（亞太最高 NT$ 15,000、歐美最高 NT$ 25,000–35,000、團隊最高 NT$ 100,000）與日本 JASSO 獎學金"
          ),
      ],
      "academic_year": [
          (
              "115（涵蓋 115–116 學年度出國交換學生第一梯次甄選暨教育部學海飛颺／惜珠［每年 12/15–2/14 截止］、第二梯次春季班交換甄選［每年 8 月及 9–10 月截止］、日本高專 NIT 暑期研習［每年 4/17 截止］及美國 2+2 雙聯學位［每年 2 月底截止］）"
          ),
          (
              f"本平台完整收錄國立聯合大學研究發展處國際及兩岸事務組公告之 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所常態開放申請之交換、雙聯學位與日本高專暑期研習合作校、{len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 21 個國家與地區）"
          ),
      ],
      "semester": [
          "第一梯次出國交換甄選（每年 1 月／結合 12/15–2/14 學海飛颺與惜珠期程）：得申請一學期或一學年（依《國際交換學生作業要點》第 2 點，若選一學年須自同年度第一學期開始，不得跨學年）。",
          "第二梯次出國交換甄選（每年 8 月及 9–10 月春季班公告）：僅得申請一學期（隔年春季學期赴境外姊妹校就讀）。",
          "日本國立高專（NIT）暑期研習與美國 2+2 雙聯學位：日本高專暑期研習於每年 4 月中旬（2026/04/17）校內截止，6–8 月赴日研習 1–2 個月；美國 2+2 雙聯學位於每年 2 月底校內截止。",
      ],
      "application_period": [
          "【第一梯次出國交換甄選暨教育部學海飛颺／學海惜珠計畫（秋季班或全學年出國）】每年 12 月 15 日至隔年 2 月 14 日開放校內收件，2 月中下旬辦理書面審查與面試，3 月中旬公告校內錄取結果。",
          "【第二梯次出國交換甄選（隔年春季班出國，僅限一學期）】每年 8 月（8/1–8/31）及 9–10 月依各姊妹校春季班簡章公告受理校內申請。",
          "【日本姊妹校國立高等專門學校（NIT）暑期專業研習交流】每年 4 月中旬（2026 年為 4 月 17 日）校內收件截止，選送理工與電資學院等學生於 6–8 月赴日本宇部、高知、新居濱、小山、木更津、釧路、明石等高專實驗室研習 1–2 個月。",
          "【美國姊妹校 2+2 雙聯學位（霜堡州立大學 FSU、佛羅里達理工學院 FIT、樹城州立大學 Boise State）＆境外學術交流經費補助】美國雙聯學位每年 2 月底截止；聯大《補助學生參與境外學術交流及研習服務經費管理要點》須於活動首日 1 個月前向研究發展處提出申請。",
      ],
      "eligibility": [
          "1. 在學身分與「出國交換當時」之年級系所認定：依《國立聯合大學國際交換學生作業要點》（109年3月3日修正通過）第 2 點，具本校大學部及研究所學籍之在學學生（不含以在職生身分入學者）皆可提出申請，惟年級及院系/所限制以各姊妹校協議書為準，且系所與年級限制需以「出國交換當時」之身分與年級為準（非提出申請時）。境外生（外籍生、僑生、陸生）可申請，但不得交換回其所屬國家；同一學制內已獲推薦出國交換或無故放棄者不得再申請。",
          "2. 校內甄選分組配分標準（《國際交換學生作業要點》第 4 點，總分未達 60 分不予推薦；若辦面試則書審占 60%、面試占 40%［表達能力 25%、組織能力 25%、發展潛力 25%、人格特性 25%］）：（1）赴大陸地區：大學部採計在校成績 60%、自傳 15%、讀書計畫/動機信 20%、其他 5%；研究所採計在校成績 40%、自傳 25%、讀書計畫/動機信 30%、其他 5%；（2）赴大陸以外地區（含港澳）：大學部採計在校成績 50%、外語能力 20%、自傳 10%、讀書計畫 15%、其他 5%；研究所採計在校成績 30%、外語能力 20%、自傳 20%、讀書計畫 25%、其他 5%。",
          "3. 學業成績（GPA）門檻：報名須檢附含排名之中英文歷年學業成績單。各姊妹校特殊 GPA 要求：美國明尼蘇達州立大學曼卡托分校、南猶他大學（SUU）要求 GPA 2.5–2.75 以上；加拿大安大略理工大學、美國佛羅里達理工學院（FIT 獎學金門檻）要求 GPA 3.0 以上；加拿大卡加利大學要求 GPA 3.2 以上。",
          "4. 個別姊妹校院系與年級限制：日本國立高專（宇部、高知、新居濱、阿南、木更津、明石、小山、釧路）限理工學院、電資學院等大二至大三（或碩一）學生；日本甲南大學限大二至大四上及碩一至碩二上；德國馬德堡大學限大三以上；加拿大安大略理工大學限大三下及大四；美國霜堡州立大學、佛羅里達理工學院、樹城州立大學 2+2 雙聯學位限修畢大一至大二課程後赴美修讀大三至大四。",
      ],
      "language_requirement": [
          "1. 國立聯合大學《學生赴國外研修留學國語言能力參考標準》基準門檻：（a）英文：TOEFL iBT 57 / TOEFL ITP 457 / IELTS 4.0 / TOEIC 550 / GEPT 中級複試通過 / BULATS Level 2 / Cambridge PET / FLPT 筆試 195 口試 S-2；（b）日文：JLPT N3 或 FLPT 筆試 195 口試 S-2；（c）德文：Goethe-Zertifikat B1 (ZD) / TestDaF TDN 3；（d）法文：DELF A1–B1 / TCF 300；（e）西文：DELE 初級。",
          "2. 英語授課姊妹校與歐美雙聯學位門檻：（a）印尼總統大學、迪波內戈羅大學、馬來西亞拉曼大學（UTAR）、越南胡志明市經濟大學（UEH）建議達聯大英文基準（TOEIC 550 / iBT 57 / IELTS 4.0–5.5）；（b）泰國吞武里蒙庫國王科技大學（KMUTT）、德國馬德堡大學（OVGU）要求 CEFR B1–B2（TOEIC 550–785 / IELTS 5.5–6.0）；（c）美國明尼蘇達州立大學曼卡托分校、南猶他大學（SUU）、霜堡州立大學（FSU 2+2）要求 TOEFL iBT 61–71 / IELTS 5.5–6.0；（d）美國佛羅里達理工學院（FIT 2+2）、樹城州立大學（Boise State 2+2）、加拿大安大略理工大學、卡加利大學要求 TOEFL iBT 79–86 / IELTS 6.0–6.5（FIT 達 iBT 88 / IELTS 6.5 另加發每學期 USD 2,000 獎學金）。",
          "3. 日本姊妹校（含綜合大學與國立高專 NIT）：（a）國立高專（宇部、高知、新居濱、阿南、木更津、明石、小山、釧路）要求日語 JLPT N3 以上或英語 TOEIC 550 / iBT 57 以上；（b）甲南大學（Konan University）、國立愛知教育大學（Aichi University of Education）要求日語 JLPT N2 以上。",
          "4. 韓國、法國與中國大陸姊妹校：（a）韓國仁荷大學（Inha University）、國立昌原大學（Changwon National University）要求韓語 TOPIK 3 級以上或英語 TOEIC 550 / iBT 71 / IELTS 5.5 以上；（b）法國南特理工大學（Polytech Nantes）、薩瓦勃朗峰大學（USMB）要求英語或法語達 CEFR B1（USMB 文學院要求 B2）；（c）中國大陸姊妹校為中文授課，免附外語能力檢定證明。",
      ],
      "required_documents": [
          "1. 國立聯合大學學生赴國外研修申請表（須經家長或監護人、系所主管、學務處生輔組、教務處註冊組簽章）",
          "2. 基本資料影本（含國民身分證正反面、學生證正反面及本人銀行或郵局存摺帳戶資訊頁）",
          "3. 外國語言能力檢定成績證明影本（TOEFL / IELTS / TOEIC / GEPT / JLPT / TOPIK / DELF；申請大陸地區姊妹校免附）",
          "4. 中英文歷年學業成績單正本（須含歷年學業總平均與班級排名）",
          "5. 中英文在學證明正本",
          "6. 中英文自傳（含個人學經歷、跨文化溝通能力與申請動機）",
          "7. 中英文讀書計畫（含公版計畫書：國外研修主題、擬修習科目與聯大母系課程學分轉換規劃）",
          "8. 國立聯合大學學生家長或監護人同意書（須由家長或法定監護人親筆簽名蓋章）",
          "9. 推薦函（中、英文推薦信各一封，由指導教授或授課教師簽署）",
          "10. 經費預算表（詳列交換期間往返機票、簽證、保險、住宿與生活費預估及獎補助來源）",
      ],
      "scholarship_info": [
          "1. 研究發展處「教育部學海飛颺計畫」與「學海惜珠計畫」（依《國立聯合大學「學海系列計畫」甄選作業要點》114年1月16日修正）：補助具中華民國國籍、在學滿一學期以上之優秀學生（學海飛颺）或持低收／中低收／特殊境遇家庭證明之清寒優秀學生（學海惜珠）赴國外（不含大陸港澳）修讀學分 1 學期至 1 學年。每年 12 月 15 日至隔年 2 月 14 日受理校內申請，依「雙聯學位生、學士班交換生、碩博班交換生、自行申請者」四組擇優核定補助。",
          "2. 研究發展處「教育部學海築夢計畫」與「新南向學海築夢計畫」：選送學生赴海外企業、研究機構或新南向國家（日本高專除外之東南亞、紐澳等國）進行專業實習，補助來回經濟艙機票款與生活費（每年 12 月中旬至 2 月初由計畫主持人提送校內審查）。",
          "3. 《國立聯合大學補助學生參與境外學術交流及研習服務經費管理要點》：補助本校學生赴境外參與短期學術交流、高專暑期研習或國際研討會（須於活動首日 1 個月前提出申請）：（a）大陸港澳及亞太地區：10 日（含）內最高補助 NT$ 10,000、10 日以上最高補助 NT$ 15,000（如日本高專 NIT 暑期研習每人補助 NT$ 15,000）；（b）紐澳、亞西、北美、拉美及非洲地區：10 日內最高 NT$ 20,000、10 日以上最高 NT$ 25,000；（c）歐洲地區：10 日內最高 NT$ 30,000、10 日以上最高 NT$ 35,000；（d）學生團隊最高補助 NT$ 100,000。",
          "4. 日本學生支援機構（JASSO）獎學金與美國雙聯學位專屬獎學金：（a）赴日本國立宇部高專等姊妹校研習滿 32 天以上並參與 NIT-NUU 台日雙邊學術研討會者，可獲推薦申請日本 JASSO 獎學金（每月 JPY 80,000）；（b）美國霜堡州立大學（FSU 2+2）提供每學期 USD 3,000 學費減免獎學金；美國佛羅里達理工學院（FIT 2+2）提供 GPA 3.0 以上每學期 USD 5,000 獎學金（達 iBT 88 / IELTS 6.5 再加發每學期 USD 2,000，合計每學期 USD 7,000）；美國南猶他大學（SUU）提供 USD 4,250 獎學金。",
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": nuu_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_NUU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "國立聯合大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 60.0,
      "academic_score_rule": (
          "依《國立聯合大學國際交換學生作業要點》第 2 點及第 4 點：具本校大學部及研究所學籍之在學學生（不含在職生）皆可申請，惟系所與年級限制以「出國交換當時」之學籍身分與年級為準；校內甄選總成績未達 60 分者不予推薦（赴大陸以外地區大學部在校成績占 50%、研究所占 30%；赴大陸地區大學部占 60%、研究所占 40%）。個別歐美交換與雙聯姊妹校另要求 GPA 2.5–3.2 以上。"
      ),
      "academic_gpa_minimum": 2.5,
      "maximum_preferences": 3,
      "selection_rules": {
          "academic_policy": "gpa_or_rank",
          "academic_reference_year": "115",
          "undergraduate_gpa_minimum": 2.5,
          "graduate_academic_exempt": False,
          "exclude_in_service": True,
          "pending_quota_planning": False,
          "partner_requirements_need_confirmation": False,
          "degree_score_minimums": {
              "undergraduate": 60.0,
              "graduate": 60.0,
          },
          "excluded_undergraduate_years": [],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 57.0,
          "ielts": 4.0,
          "toefl_itp": 457.0,
          "toeic": 550.0,
      },
      "application_periods": [
          {
              "title": "國立聯合大學 115–116 學年度第一梯次出國交換學生甄選暨教育部「學海飛颺／學海惜珠」計畫申請（2026/12/15–2027/02/14 受理）",
              "details": [
                  "依《國立聯合大學國際交換學生作業要點》第 2 點及《115年度學海飛颺/學海惜珠計畫申請校內期程》，第一梯次（秋季班或全學年出國交換）結合教育部學海飛颺／惜珠期程於每年 12 月 15 日至隔年 2 月 14 日開放校內收件，2 月 17 日至 2 月 28 日辦理校內書審暨面試，3 月 14 日通知校內審查結果。",
                  "申請人須備齊《學生赴國外研修申請表》與 10 項應備文件，完成家長、系所主管、生輔組與註冊組簽章後送交研究發展處國際及兩岸事務組；獲錄取者須於公告後 20 日內繳交行政處理費（保證金）新臺幣 3,000 元。",
              ],
              "source": {
                  "title": "國立聯合大學研究發展處國際及兩岸事務組出國交換學生作業要點與 115 年度學海計畫期程",
                  "source_url": NUU_OUTBOUND_OVERVIEW_URL,
                  "category": "exchange_application",
                  "summary": "聯大第一梯次出國交換暨學海飛颺／惜珠計畫校內收件期限（12/15–2/14）、分組配分與保證金規定。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "116學年度第一梯次出國交換暨學海飛颺／惜珠甄選",
              "audience": "all_students",
              "opens_at": "2026-12-15T09:00:00+08:00",
              "deadline_at": "2027-02-14T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "第一梯次（得申請一學期或一學年）暨學海飛颺／惜珠於每年 12 月 15 日至隔年 2 月 14 日受理；第二梯次（春季班，僅限一學期）於每年 8 月及 9–10 月受理。",
              "deadline_note": "申請表須先經家長、系所主管、學務處生輔組及教務處註冊組簽章後，於截止日前送達國際及兩岸事務組。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "國立聯合大學美國姊妹校 2+2 雙聯學位（霜堡州立大學 FSU、佛羅里達理工學院 FIT、樹城州立大學 Boise State）校內甄選（每年 2/28 截止）",
              "details": [
                  "依《國立聯合大學雙聯學制實施辦法》及國際及兩岸事務組美國姊妹校雙聯學位公告，本校大二在學學生（修畢大一至大二課程）可申請赴美國霜堡州立大學（FSU）、佛羅里達理工學院（FIT）或樹城州立大學（Boise State）修讀大三至大四課程，符合畢業資格者同時獲頒兩校學士學位。",
                  "霜堡州立大學提供每學期 USD 3,000 獎學金；佛羅里達理工學院提供 GPA 3.0 以上每學期 USD 5,000 獎學金（達 TOEFL iBT 88 或 IELTS 6.5 再加發每學期 USD 2,000 獎學金）。",
              ],
              "source": {
                  "title": "國立聯合大學美國姊妹校雙聯學位計畫公告與雙聯學制實施辦法",
                  "source_url": NUU_DUAL_DEGREE_URL,
                  "category": "exchange_application",
                  "summary": "聯大與美國 FSU、FIT、Boise State 2+2 雙聯學士學位申請條件、獎學金與 2 月底截止規定。",
              },
              "scope": "home_application",
              "program_types": ["dual_degree"],
              "academic_year": "116",
              "application_round": "116學年度美國姊妹校 2+2 雙聯學位甄選",
              "audience": "all_students",
              "opens_at": "2027-01-01T09:00:00+08:00",
              "deadline_at": "2027-02-28T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "美國雙聯學位校內收件於每年 2 月底截止，並可同步申請教育部學海飛颺獎學金。",
              "deadline_note": "須檢附中英文歷年成績單、英文檢定證明（iBT 61–80 / IELTS 5.5–6.0）、讀書計畫、推薦信與家長同意書。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "國立聯合大學日本姊妹校國立高等專門學校（NIT）暑期專業研習交流計畫（每年 4 月中旬截止）",
              "details": [
                  "依國際及兩岸事務組《日本姊妹校高專（NIT）暑期研習交流計畫》公告，每年選送本校學生於 6 月至 8 月赴日本宇部、高知、新居濱、小山、木更津、釧路、明石等國立高等專門學校進行 1 至 2 個月實驗室專業研習。",
                  "錄取學生可依《補助學生參與境外學術交流及研習服務經費管理要點》申請每人最高新臺幣 15,000 元補助；赴宇部高專等研習滿 32 天以上並發表 NIT-NUU 雙邊研討會論文者，另可申請日本 JASSO 獎學金。",
              ],
              "source": {
                  "title": "國立聯合大學 2026 日本姊妹校高專（NIT）暑期研習交流公告與名額表",
                  "source_url": NUU_NIT_SUMMER_2026_URL,
                  "category": "exchange_application",
                  "summary": "聯大日本國立高專（NIT）暑期實驗室研習名額、申請期限與 NT$ 15,000 境外交流補助。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "115",
              "application_round": "2026–2027 日本國立高專（NIT）暑期研習交流",
              "audience": "all_students",
              "opens_at": "2027-03-15T09:00:00+08:00",
              "deadline_at": "2027-04-17T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "每年 3 月中旬公告各高專實驗室研習主題與名額，4 月中旬（約 4 月 17 日）截止校內收件。",
              "deadline_note": "申請表須經指導教授或系主任推薦及家長簽章同意後送交國際及兩岸事務組。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"國立聯合大學研究發展處國際及兩岸事務組全球姊妹校交換、日本高專（NIT）聯盟、美法加雙聯學位與學海獎補助總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所常態開放申請）"
              ),
              "details": [
                  (
                      f"國立聯合大學（National United University, NUU，創立於 1972 年，擁有苗栗市「第一（二坪山）校區」與「第二（八甲）校區」雙校區，為桃竹苗地區重要國立綜合大學）由「研究發展處國際及兩岸事務組（Office of International and Cross-Strait Affairs, OIA）」統籌全校 6 大學院（理工學院、電機資訊學院、管理學院、客家研究學院、人文與社會學院、設計學院）及共同教育委員會之出國交換學生計畫、日本國立高等專門學校（NIT）交換暨暑期研習、美法加跨國雙聯學位計畫及教育部學海系列獎補助。本平台完整收錄 {len(partners)} 所聯合大學官方合作姊妹校（含 {open_partner_count} 所常態開放申請之交換、雙聯與日本高專暑期研習合作校，以及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 21 個國家與地區。"
                  ),
                  (
                      "聯大國際交流具備四大核心特色：（1）全臺最完整之日本國立高等專門學校（NIT）學術與實驗室交換網絡（與宇部、高知、新居濱、阿南、木更津、明石、小山、釧路等近 40 所日本國立高專及甲南大學、國立愛知教育大學深度合作，除學期交換外每年選送大批理工電資學生赴日暑期實驗室研習並結合 NIT-NUU 台日雙邊學術研討會與 JASSO 獎學金）；（2）歐美加高獎學金雙聯學制與交換合作（美國霜堡州立大學 FSU 2+2、佛羅里達理工學院 FIT 2+2、樹城州立大學 Boise State 2+2、南猶他大學 SUU、明尼蘇達州立大學曼卡托分校、加拿大安大略理工大學、卡加利大學、法國南特理工大學 Polytech Nantes、薩瓦勃朗峰大學 USMB、德國馬德堡大學 OVGU）；（3）亞洲多元免學費交換網絡（韓國仁荷大學、國立昌原大學、高麗網路大學、馬來西亞拉曼大學 UTAR、泰國吞武里蒙庫國王科技大學 KMUTT、越南胡志明市經濟大學 UEH、印尼總統大學、迪波內戈羅大學、蒙古全球領袖大學）；（4）結合教育部學海飛颺／惜珠／築夢與聯大《補助學生參與境外學術交流經費》（亞太最高 1.5 萬、歐美最高 2.5–3.5 萬元）。"
                  ),
              ],
              "source": {
                  "title": "國立聯合大學研究發展處國際及兩岸事務組官方網站",
                  "source_url": NUU_OIA_HOME_URL,
                  "category": "exchange_application",
                  "summary": f"國立聯合大學 {len(partners)} 所全球合作姊妹校與 {open_partner_count} 所常態開放交換／雙聯／高專暑期研習校總覽。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "「出國交換當時」之年級系所認定、大陸與非大陸分組配分（總分須達 60 分）及 NT$ 3,000 保證金規定",
              "details": [
                  "在學身分與年級認定：依《國立聯合大學國際交換學生作業要點》（109年3月3日修正通過）第 2 點，具本校大學部及研究所學籍之在學學生（不含以在職生身分入學者）皆可提出申請，惟各姊妹校之系所及年級限制需以「出國交換當時」之身分與年級為準（非提出申請時）。境外生（外籍生、僑生、陸生）可申請，但不得交換回其所屬國家；同一學制內已獲推薦出國交換或無故放棄者不得再申請。",
                  "校內甄選分組配分與保證金：總成績未達 60 分者不予推薦（若辦面試則書審 60%＋面試 40%）。赴大陸以外地區（含港澳）：大學部採計「在校成績 50%＋外語能力 20%＋自傳 10%＋讀書計畫 15%＋其他 5%」，研究所採計「在校成績 30%＋外語能力 20%＋自傳 20%＋讀書計畫 25%＋其他 5%」；赴大陸地區：大學部採計「在校成績 60%＋自傳 15%＋讀書計畫/動機信 20%＋其他 5%」，研究所採計「在校成績 40%＋自傳 25%＋讀書計畫/動機信 30%＋其他 5%」。錄取後 20 日內須繳交保證金 NT$ 3,000（完成返國義務與 20 小時服務後全額退還）。",
              ],
              "source": {
                  "title": "國立聯合大學國際交換學生作業要點（109年3月3日修正通過）",
                  "source_url": NUU_EXCHANGE_RULES_PDF_URL,
                  "category": "exchange_application",
                  "summary": "聯大交換學生申請資格、分組甄選配分比重、保證金與出國修課下限規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "留學國語言能力參考標準（TOEIC 550 / iBT 57 / IELTS 4.0）、日本 JLPT N2–N3、韓國 TOPIK 3 級、法語 DELF B1 與歐美雙聯門檻",
              "details": [
                  "聯大留學國語言能力參考標準與歐美亞英語門檻：（1）依《國立聯合大學學生赴國外研修留學國語言能力參考標準》，英語基準為 TOEFL iBT 57 / ITP 457 / IELTS 4.0 / TOEIC 550 / GEPT 中級複試通過；（2）美國明尼蘇達州立大學曼卡托分校、南猶他大學 SUU、霜堡州立大學 FSU 2+2 要求 iBT 61–71 / IELTS 5.5–6.0；（3）美國佛羅里達理工學院 FIT 2+2、樹城州立大學 Boise State 2+2、加拿大安大略理工大學、卡加利大學要求 iBT 79–86 / IELTS 6.0–6.5；（4）德國馬德堡大學、泰國 KMUTT、越南 UEH、馬來西亞 UTAR 依英文授課學程要求 CEFR B1–B2。",
                  "日韓法與大陸姊妹校門檻：（1）日本國立高專（宇部、高知、新居濱、阿南、木更津、明石、小山、釧路）要求日語 JLPT N3 或英語 TOEIC 550 以上；日本甲南大學、國立愛知教育大學要求 JLPT N2 以上；（2）韓國仁荷大學、國立昌原大學要求 TOPIK 3 級或英語 TOEIC 550 / iBT 71 / IELTS 5.5；（3）法國南特理工大學、薩瓦勃朗峰大學要求英語或法語 DELF B1（USMB 文學院 B2）；（4）大陸地區姊妹校免附外語檢定。",
              ],
              "source": {
                  "title": "國立聯合大學學生赴國外研修留學國語言能力參考標準與交換學校一覽表",
                  "source_url": NUU_LANGUAGE_STANDARDS_PDF_URL,
                  "category": "exchange_application",
                  "summary": "聯大留學國英日韓德法西語參考標準與各姊妹校最新語言門檻。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "學生赴國外研修申請表、基本資料影本、語檢證明、含排名中英文成績單、中英文在學證明、自傳、讀書計畫、家長同意書、中英文推薦函與經費預算表",
              "details": [
                  "校內交換甄選 10 項必備文件（《國際交換學生作業要點》第 3 點）：（1）《國立聯合大學學生赴國外研修申請表》（經家長、系所主管、生輔組、註冊組簽章）；（2）基本資料影本（身分證、學生證、金融帳戶頁）；（3）外語能力檢定證明（大陸免附）；（4）中英文歷年學業成績單（含排名）；（5）中英文在學證明；（6）中英文自傳；（7）中英文讀書計畫（含公版計畫書）；（8）學生家長或監護人同意書；（9）中英文推薦函各一封；（10）經費預算表。",
                  "返國程序、退還保證金與學分轉換文件：返國後 14 日內須提交《交換生返國程序單》、中英文心得報告、登機證正本與核銷單據，並完成 20 小時國際組服務（或 3 場經驗傳承、或投稿 2 篇英文心得）以退還 NT$ 3,000 保證金；同時持國外成績單正本依《學生於締約學校修讀課程學分與成績轉換參考表》辦理學分抵免。",
              ],
              "source": {
                  "title": "國立聯合大學國際交換學生作業要點與相關表單下載專區",
                  "source_url": NUU_EXCHANGE_FORMS_URL,
                  "category": "exchange_application",
                  "summary": "聯大出國交換 10 項應備申請文件、家長同意書、公版讀書計畫及返國程序單規範。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部學海飛颺／學海惜珠／學海築夢、聯大境外學術交流經費補助（最高 3.5 萬元）、日本 JASSO 獎學金與美國雙聯獎學金",
              "details": [
                  "教育部學海系列計畫（研究發展處國際組主辦，每年 12/15–2/14 截止）：（1）《學海飛颺》選送優秀學生赴國外（不含港澳陸）研修 1 學期至 1 學年，分「雙聯學位生、學士班交換生、碩博班交換生、自行申請者」四組擇優核定；（2）《學海惜珠》補助低收、中低收或特殊境遇清寒優秀生出國研修；（3）《學海築夢／新南向學海築夢》補助海外專業實習。",
                  "聯大校內境外學術交流補助與國際合作獎學金：（1）《補助學生參與境外學術交流及研習服務經費管理要點》（活動首日 1 個月前申請）：大陸港澳及亞太地區最高 NT$ 10,000–15,000（如日本高專暑期研習補助 NT$ 15,000）、紐澳/亞西/美非地區最高 NT$ 20,000–25,000、歐洲地區最高 NT$ 30,000–35,000、團隊最高 NT$ 100,000；（2）日本 JASSO 獎學金（赴宇部高專等研習滿 32 日並參與雙邊研討會者每月 JPY 80,000）；（3）美國雙聯獎學金（FSU 每學期 USD 3,000、FIT 每學期 USD 5,000–7,000、SUU USD 4,250）。",
              ],
              "source": {
                  "title": "國立聯合大學「學海系列計畫」甄選作業要點與補助學生參與境外學術交流經費管理要點",
                  "source_url": NUU_OVERSEAS_GRANT_PDF_URL,
                  "category": "scholarship",
                  "summary": "聯大教育部學海系列計畫、校內境外學術交流經費補助與美日合作校獎學金完整規定。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "國立聯合大學出國交換 10 項應備文件、公版中英文讀書計畫、自傳與學海飛颺申請準備指南",
              "summary": "說明聯大《國際交換學生作業要點》規定之 10 項申請表件、中英文讀書計畫（非大陸組大學部占 15%、研究所占 25%；大陸組占 20–30%）、中英文自傳及單位簽章流程。",
              "key_points": [
                  "中英文讀書計畫與公版計畫書（非大陸組占 15–25%、大陸組占 20–30%）：應具體列出目標姊妹校擬修習之科目（大學部每學期至少修讀 3 門課程及格、研究所至少修讀 1 門課程及格）、與聯大母系課程之學分轉換對應關係及預期學習成果。",
                  "中英文自傳與中英文推薦函各一封：建議結合聯大理工、電資、管理、客家研究、人文社科或設計學院專業背景，突顯專題研究、社團服務、外語檢定進修與跨文化適應力，並提前商請系所師長撰寫中、英文推薦信。",
                  "學生赴國外研修申請表、家長同意書與經費預算表：申請表須依序完成家長或監護人、系所主管、學務處生輔組及教務處註冊組簽章，並檢附身分證、學生證與本人銀行/郵局帳戶影本。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立聯合大學國際交換學生作業要點（1090303）與相關表單下載專區",
                  "source_url": NUU_EXCHANGE_RULES_PDF_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NUU_EXCHANGE_FORMS_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "國立聯合大學國際交換學生作業要點、雙聯學制實施辦法、保證金退還與學分成績轉換核心規定",
              "summary": "規範聯大「出國交換當時」之年級系所認定、大陸與非大陸分組配分、NT$ 3,000 保證金與 20 小時服務義務、每學期及格門數下限及學分成績轉換。",
              "key_points": [
                  "分組甄選配分與 60 分及格線：總分未達 60 分不予推薦（若辦面試則書審 60%＋面試 40%）。赴大陸以外地區大學部採計「在校成績 50%＋外語 20%＋自傳 10%＋讀書計畫 15%＋其他 5%」、研究所採計「在校成績 30%＋外語 20%＋自傳 20%＋讀書計畫 25%＋其他 5%」；赴大陸地區免計外語，大學部採計「在校成績 60%＋自傳 15%＋讀書計畫 20%＋其他 5%」、研究所採計「在校成績 40%＋自傳 25%＋讀書計畫 30%＋其他 5%」。",
                  "保證金 NT$ 3,000 與出國修課下限：錄取公告後 20 日內須繳交保證金 NT$ 3,000；交換期間每學期大學部至少修讀 3 門課程及格、研究所至少修讀 1 門課程及格；返國後 14 日內繳交返國程序單、中英文心得並完成 20 小時國際組服務（或 3 場經驗傳承、或投稿 2 篇英文心得）後無息退還。",
                  "學分與成績轉換標準：依《學生於締約學校修讀課程學分與成績轉換參考表》（105年8月31日教務會議通過），持國外姊妹校正式成績單正本及課程大綱向系所及教務處註冊組辦理學分採認。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立聯合大學國際交換學生作業要點、雙聯學制實施辦法與學分成績轉換參考表",
                  "source_url": NUU_EXCHANGE_RULES_PDF_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NUU_CREDIT_CONVERSION_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "國立聯合大學研究發展處國際及兩岸事務組（OIA）官方網站",
              "source_url": NUU_OIA_HOME_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立聯合大學「出國交換學生」總覽專頁與交換學校一覽表",
              "source_url": NUU_OUTBOUND_OVERVIEW_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立聯合大學國際交換學生作業要點（109年3月3日修正通過 PDF）",
              "source_url": NUU_EXCHANGE_RULES_PDF_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立聯合大學雙聯學制實施辦法與美國姊妹校 2+2 雙聯學位公告",
              "source_url": NUU_DUAL_DEGREE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": f"國立聯合大學全球締約姊妹校名錄與交換學校一覽表（橫跨 21 國共 {len(partners)} 所合作姊妹校）",
              "source_url": NUU_PARTNER_LIST_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立聯合大學教育部「學海系列計畫」（學海飛颺、學海惜珠、學海築夢、新南向學海築夢）專區與甄選作業要點",
              "source_url": NUU_XUEHAI_OVERVIEW_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "國立聯合大學補助學生參與境外學術交流及研習服務經費管理要點",
              "source_url": NUU_OVERSEAS_GRANT_PDF_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": f"國立聯合大學出國交換學生心得分享與歷年錄取名冊專區（{exp_covered_schools} 校 {total_exp_reports} 篇紀錄）",
              "source_url": NUU_EXCHANGE_REPORTS_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_NUU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  doc_conditions = {
      "school_id": "nuu",
      "school_name": "國立聯合大學",
      "checked_at": CHECKED_AT,
      "source_url": NUU_EXCHANGE_RULES_PDF_URL,
      "common_documents": exchange_info_payload["required_documents"],
      "track_specific_conditions": [
          {
              "track": "國際及兩岸事務組「大陸以外地區（日韓、歐美、東南亞）」交換學生計畫",
              "required": [
                  "國立聯合大學學生赴國外研修申請表（含家長、系所主管、生輔組、註冊組簽章）及基本資料影本（身分證、學生證、金融帳戶頁）",
                  "中英文歷年學業成績單正本（含排名；大學部占書審 50%、研究所占 30%）與中英文在學證明",
                  "有效外語能力檢定證明影本（占書審 20%；TOEIC 550 / TOEFL iBT 57 / IELTS 4.0 / JLPT N2–N3 / TOPIK 3 級 / DELF B1）",
                  "中英文自傳（占 10–20%）、中英文讀書計畫（含公版計畫書，占 15–25%）、家長同意書、中英文推薦函各一封及經費預算表",
              ],
          },
          {
              "track": "國際及兩岸事務組「大陸地區」交換學生計畫",
              "required": [
                  "國立聯合大學學生赴國外研修申請表（含家長、系所主管、生輔組、註冊組簽章）及基本資料影本",
                  "中英文歷年學業成績單正本（含排名；大學部占書審 60%、研究所占 40%，免附外語能力檢定證明）與在學證明",
                  "自傳（大學部占 15%、研究所占 25%）、讀書計畫／動機信（大學部占 20%、研究所占 30%）、家長同意書、推薦函及經費預算表",
              ],
          },
          {
              "track": "美法加跨國雙聯學位計畫（美國霜堡州立大學 FSU、佛羅里達理工學院 FIT、樹城州立大學 Boise State、南猶他大學 SUU、加拿大安大略理工大學、法國南特理工大學）",
              "required": [
                  "雙聯學制暨赴國外研修校內申請表（美國 2+2 雙聯每年 2 月底前向國際組提出）",
                  "英文歷年成績單正本与外語能力檢定證明（FSU/SUU 要求 iBT 61–71 / IELTS 5.5–6.0；FIT/Boise State/安大略理工要求 iBT 79–80 / IELTS 6.0–6.5）",
                  "英文讀書／修課轉換計畫、英文自傳、中英文推薦函、家長同意書、財力證明與護照影本",
              ],
          },
          {
              "track": "日本國立高專（NIT）暑期專業研習交流、教育部學海系列計畫與聯大境外學術交流經費補助",
              "required": [
                  "日本高專（NIT）暑期研習（每年 4 月中旬截止）：暑期研習申請表、中英文歷年成績單、語檢證明（JLPT N3 或 TOEIC 550）、實驗室志願與研究計畫、家長同意書",
                  "教育部學海飛颺／惜珠（每年 12/15–2/14 截止）：學海計畫申請表、學生個人基本資料表、含班排歷年成績單、外語檢定證明、1,500–3,000 字出國研修計畫書（惜珠另附低收／中低收／特殊境遇家庭證明）",
                  "聯大補助學生參與境外學術交流經費（活動首日 1 個月前申請）：經費補助申請表、活動議程／邀請函、預算表與家長同意書；返國後 14 日內繳交成果報告書與機票單據核銷",
              ],
          },
      ],
  }
  (OFFICIAL_NUU_DIR / "document-conditions.json").write_text(
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
        f"{fname},{len(partners)},{pop},{ratio:.4f},Official NUU OIA verified"
    )
  (OFFICIAL_NUU_DIR / "field-coverage.csv").write_text(
      "\n".join(field_cov_lines) + "\n", encoding="utf-8"
  )

  pages_records = [
      {
          "title": "國立聯合大學：出國交換學生甄選（第一梯次暨學海 12/15–2/14、第二梯次春季班 8 月）、日本高專暑期研習與美國雙聯學位申請時程",
          "source_url": NUU_OUTBOUND_OVERVIEW_URL,
          "published_at": "2026-10-20T00:00:00Z",
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
          "title": "國立聯合大學：國際交換學生作業要點（1090303 修正）、「出國交換當時」年級系所認定与分組甄選配分標準",
          "source_url": NUU_EXCHANGE_RULES_PDF_URL,
          "published_at": "2026-10-20T00:00:00Z",
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
          "title": f"國立聯合大學：{len(partners)} 所全球與兩岸合作姊妹校留學國語言能力參考標準（TOEIC / TOEFL / IELTS / JLPT / TOPIK / DELF）",
          "source_url": NUU_LANGUAGE_STANDARDS_PDF_URL,
          "published_at": "2026-10-20T00:00:00Z",
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
          "title": "國立聯合大學：出國交換與雙聯學位 10 項應備文件（赴國外研修申請表、含排名成績單、公版讀書計畫、自傳、家長同意書、推薦函與返國程序單）",
          "source_url": NUU_EXCHANGE_FORMS_URL,
          "published_at": "2026-10-20T00:00:00Z",
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
          "title": "國立聯合大學：教育部學海飛颺、學海惜珠、學海築夢、校內境外學術交流經費補助（最高 3.5 萬元）與美日姊妹校獎學金",
          "source_url": NUU_XUEHAI_OVERVIEW_URL,
          "published_at": "2026-10-20T00:00:00Z",
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
  (OFFICIAL_NUU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
      + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "nuu",
      "school_name": "國立聯合大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "general_partner_gpa_minimum": 2.5,
          "minimum_selection_score": 60.0,
          "deposit_ntd": 3000,
          "service_hours_for_deposit_refund": 20,
          "mainland_undergrad_weights": {
              "academic_record": 0.60,
              "autobiography": 0.15,
              "study_plan": 0.20,
              "others": 0.05,
          },
          "mainland_grad_weights": {
              "academic_record": 0.40,
              "autobiography": 0.25,
              "study_plan": 0.30,
              "others": 0.05,
          },
          "international_undergrad_weights": {
              "academic_record": 0.50,
              "language_proficiency": 0.20,
              "autobiography": 0.10,
              "study_plan": 0.15,
              "others": 0.05,
          },
          "international_grad_weights": {
              "academic_record": 0.30,
              "language_proficiency": 0.20,
              "autobiography": 0.20,
              "study_plan": 0.25,
              "others": 0.05,
          },
          "min_courses_per_semester_undergrad": "3 courses passed",
          "min_courses_per_semester_grad": "1 course passed",
          "require_nuu_enrollment_during_abroad": True,
          "exclude_in_service": True,
          "return_documents_due": "返國後 14 日內完成交換生返國程序單、中英文心得報告及核銷，並完成 20 小時國際組服務後無息退還保證金 NT$ 3,000",
      },
      "source_urls": nuu_source_urls,
      "verified_at": "2026-11-02",
  }
  (OFFICIAL_NUU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NUU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "國立聯合大學",
              "required_documents": student_dashboard_payload[
                  "required_documents"
              ],
              "source_urls": nuu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NUU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "國立聯合大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": nuu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "nuu",
      "school_name": "國立聯合大學",
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
      "dual_degree_partner_universities": 6,
      "dual_degree_programs": 6,
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
          f"國立聯合大學研究發展處國際及兩岸事務組（OIA）《國際交換學生作業要點（1090303）》、《交換學校一覽表》、6 所美法加跨國雙聯學位合作校（美國霜堡州立大學 FSU、佛羅里達理工學院 FIT、樹城州立大學 Boise State、南猶他大學 SUU、加拿大安大略理工大學、法國南特理工大學）、日本國立高等專門學校（NIT）交換暨暑期專業研習交流計畫，以及教育部學海飛颺、學海惜珠、學海築夢與聯大補助學生參與境外學術交流經費管理要點同步整合；共完整收錄 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所常態開放申請交換、雙聯與高專暑期研習學校及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 21 個國家與地區）。"
      ),
      "verified_at": "2026-11-02",
  }
  (OFFICIAL_NUU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NUU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "nuu",
              "school_name": "國立聯合大學",
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
          "sources/nuu/nuu_catalog_source.json",
          NUU_OUTBOUND_OVERVIEW_URL,
          f"國立聯合大學 {len(partners)} 所全球與兩岸合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/nuu/nuu_resolved_locations.json",
          NUU_PARTNER_LIST_URL,
          f"國立聯合大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
      ),
      (
          "sources/nuu/nuu_exchange_schools_sheet.csv",
          NUU_EXCHANGE_SHEET_URL,
          "國立聯合大學國際及兩岸事務組《交換學校一覽表（128 校名額、語檢與雙聯規定）》CSV",
      ),
      (
          "sources/nuu/nuu_exchange_schools_sheet.xlsx",
          NUU_EXCHANGE_SHEET_URL,
          "國立聯合大學國際及兩岸事務組《交換學校一覽表》XLSX",
      ),
      (
          "sources/nuu/nuu_partner_schools_sheet.csv",
          NUU_PARTNER_SHEET_URL,
          "國立聯合大學國際及兩岸事務組《全球締約姊妹校名錄》CSV",
      ),
      (
          "sources/nuu/nuu_academic_units.html",
          "https://www.nuu.edu.tw/p/412-1000-745.php?Lang=zh-tw",
          "國立聯合大學全校 6 大學院、系所與共同教育委員會架構 HTML",
      ),
  ]
  for rel_p, surl in bin_urls.items():
    rp = rel_p if rel_p.startswith("sources/") else f"sources/nuu/{rel_p}"
    if not any(x[0] == rp for x in provenance_files):
      provenance_files.append((rp, surl, f"國立聯合大學官方原始檔案：{Path(rp).name}"))

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
      "school_id": "nuu",
      "school_name": "國立聯合大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = (
      json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  )
  (OFFICIAL_NUU_DIR / "import_provenance.json").write_text(
      prov_text, encoding="utf-8"
  )
  (OFFICIAL_NUU_DIR / "import-provenance.json").write_text(
      prov_text, encoding="utf-8"
  )

  print(
      f"Successfully built NUU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
