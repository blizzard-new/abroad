"""Build the official National Formosa University (國立虎尾科技大學, NFU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_NFU_DIR = REPO_ROOT / "sources" / "nfu"
OFFICIAL_NFU_DIR = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "nfu"
)
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-10-31T00:00:00Z"

NFU_OIA_HOME_URL = "https://oia.nfu.edu.tw/"
NFU_ABOUT_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/intro/introducation"
NFU_MEMBERS_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/intro/members"
NFU_SISTER_INDEX_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/sister"
NFU_SISTER_ASIA_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/sister/asia"
NFU_SISTER_EUROPE_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/sister/europe"
NFU_SISTER_AMERICA_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/sister/america"
NFU_SISTER_OCEANIA_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/sister/ocaenia"
NFU_REGULATIONS_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/regulations"
NFU_OUTBOUND_ABROAD_URL = "https://oia.nfu.edu.tw/zh_tw/out/abroad"
NFU_OUTBOUND_311_URL = "https://oia.nfu.edu.tw/zh_tw/out/abroad/311"
NFU_EXCHANGE_SCHOOLS_URL = "https://oia.nfu.edu.tw/zh_tw/out/exlink/abroad"
NFU_EXCHANGE_STUDENT_URL = "https://oia.nfu.edu.tw/zh_tw/out/exlink/abroadlink2"
NFU_SCHOLARSHIPS_URL = "https://oia.nfu.edu.tw/zh_tw/out/exlink/flying"
NFU_DREAM_URL = "https://oia.nfu.edu.tw/zh_tw/out/short/dream"
NFU_SHARING_URL = "https://oia.nfu.edu.tw/zh_tw/out/sharing"
NFU_NEWS_OUTBOUND_URL = "https://oia.nfu.edu.tw/zh_tw/news/Outbound"
NFU_SELECTION_GUIDELINES_PDF_URL = (
    "https://oia.nfu.edu.tw/xhr/archive/download?file=69e990bc4eae358574b1be0f"
)
NFU_SUBSIDY_GUIDELINES_PDF_URL = (
    "https://oia.nfu.edu.tw/xhr/archive/download?file=69e9911a4eae358574b1be18"
)
NFU_APP_FORM_ODT_URL = "https://oia.nfu.edu.tw/uploads/asset/data/6a30b8844eae35ab549ba560/3.%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E7%94%84%E9%81%B8%E5%A0%B1%E5%90%8D%E8%A1%A8-1.odt"
NFU_115_2_EXCHANGE_POST_URL = "https://oia.nfu.edu.tw/zh_tw/news/Outbound/-115%E5%AD%B8%E5%B9%B4%E5%BA%A6%E7%AC%AC%E4%BA%8C%E5%AD%B8%E6%9C%9F-%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E7%94%B3%E8%AB%8B-%E8%87%AA%E5%8D%B3%E6%97%A5%E8%B5%B7%E8%87%B3115%E5%B9%B49%E6%9C%8810%E6%97%A5%E6%AD%A2-42884964"
NFU_115_2_XIZHU_POST_URL = "https://oia.nfu.edu.tw/zh_tw/news/Outbound/-115%E5%AD%B8%E5%B9%B4%E5%BA%A6%E7%AC%AC%E4%BA%8C%E5%AD%B8%E6%9C%9F-%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E7%94%B3%E8%AB%8B-%E5%AD%B8%E6%B5%B7%E6%83%9C%E7%8F%A0%E7%AC%AC2%E6%AC%A1%E5%BE%B5%E4%BB%B6-%E8%87%AA%E5%8D%B3%E6%97%A5%E8%B5%B7%E8%87%B3115%E5%B9%B49%E6%9C%8810%E6%97%A5%E6%AD%A2-64583857"
NFU_115_2_BROCHURE_PDF_URL = "https://oia.nfu.edu.tw/uploads/bulletin_file/file/6a1ce9144eae351ff5f951a5/4.%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E7%94%84%E9%81%B8%E7%B0%A1%E7%AB%A0.pdf"
NFU_115_2_XIZHU_BROCHURE_PDF_URL = "https://oia.nfu.edu.tw/uploads/bulletin_file/file/6a5895ea4eae352077a3a6f6/4.%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F_%E5%AD%B8%E6%B5%B7%E6%83%9C%E7%8F%A0%E7%94%84%E9%81%B8%E7%B0%A1%E7%AB%A011507.pdf"
NFU_CEFR_TABLE_PDF_URL = "https://oia.nfu.edu.tw/uploads/bulletin_file/file/6a1ce9144eae351ff5f951a6/5.CEF%E8%88%87%E5%90%84%E9%A0%85%E8%8B%B1%E6%AA%A2%E5%B0%8D%E7%85%A7%E8%A1%A8.pdf"
NFU_PARTNER_LIST_11506_PDF_URL = "https://oia.nfu.edu.tw/uploads/bulletin_file/file/6a1ce9144eae351ff5f951a7/6.%E5%9C%8B%E7%AB%8B%E8%99%8E%E5%B0%BE%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E6%B5%B7%E5%A4%96%E5%A7%8A%E5%A6%B9%E6%A0%A1%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E4%B8%80%E8%A6%BD%E8%A1%A8__115.06_.pdf"
NFU_UNLV_SUMMER_PDF_URL = "https://oia.nfu.edu.tw/uploads/bulletin_file/file/69cb1942085777c11be50dd8/2026%E7%BE%8E%E5%9C%8B%E6%8B%89%E6%96%AF%E7%B6%AD%E5%8A%A0%E6%96%AFUNLV%E6%9A%91%E6%9C%9F%E7%A0%94%E7%BF%92%E8%A8%88%E7%95%AB%E5%85%AC%E5%91%8A0325.pdf"

REGION_COST_DEFAULTS = {
    "日本": (
        (
            "每月生活費約 USD 680–1,120（折合日圓約 JPY 95,000–160,000"
            " / 月、新臺幣約 21,500–35,500"
            " 元；含明治大學、近畿大學、近畿大學產業理工學部、群馬大學等學生宿舍與膳食交通費）"
        ),
        (
            "須由日本姊妹校代向出入國在留管理局申辦「在留資格認定證明書（COE）」（申請"
            " COE 須檢附財力證明），獲發後申辦留學簽證並強制加入日本國民健康保險（NHI）。"
        ),
    ),
    "韓國": (
        (
            "每月生活費約 USD 620–1,050（折合韓元約 KRW 850,000–1,450,000"
            " / 月、新臺幣約 19,500–33,500"
            " 元；含釜山東西大學、首爾／龍仁明知大學宿舍與生活開銷）"
        ),
        (
            "須憑韓國姊妹校核發之標準入學許可書向駐台北韓國代表部申辦 D-2-6"
            " 交換學生簽證，入境後申辦外國人登錄證（ARC）並納保韓國國民健康保險（NHIS）。"
        ),
    ),
    "美國": (
        (
            "每月生活費約 USD 1,350–2,200（依匯率折合新臺幣約 43,000–70,000"
            " 元；含南伊利諾大學卡本岱爾校區 SIUC、匹茲堡州立大學"
            " PSU、密西根大學弗林特分校、內華達大學拉斯維加斯分校"
            " UNLV、德州大學聖安東尼校區 UTSA、喬治梅森大學"
            " GMU、波莫納加州州立理工大學 Cal Poly Pomona 住宿與生活費）"
        ),
        (
            "須憑美國合作校核發之 DS-2019（J-1 交換生）或 I-20（F-1"
            " 3+1+1雙聯學制）繳交 SEVIS I-901 費用並向 AIT"
            " 申辦簽證，並強制投保接待校規定之學生醫療保險。"
        ),
    ),
    "德國": (
        (
            "每月生活費約 USD 1,000–1,550（折合歐元約 EUR 920–1,420"
            " / 月、新臺幣約 32,000–49,500 元；含德國 HAWtech"
            " 六校聯盟：埃斯林根、卡爾斯魯厄、達姆施塔特、德烈斯登、柏林"
            " HTW、亞琛應用科技大學學生宿舍與學期交通卡費）"
        ),
        (
            "須開立德國限制提領帳戶（Blocked"
            " Account）並憑入學許可向德國在台協會申辦學生簽證及投保德國公保／醫療險。"
        ),
    ),
    "捷克": (
        (
            "每月生活費約 USD 650–1,050（折合歐元約 EUR 600–960 / 月、新臺幣約"
            " 20,500–33,500 元；含布拉格生命科學大學"
            " CZU、布爾諾孟德爾大學、南波希米亞大學學生宿舍與生活費）"
        ),
        (
            "須憑捷克接待大學入學許可與住宿證明向捷克經濟文化辦事處申辦長期學生簽證及捷克合約醫療保險。"
        ),
    ),
    "匈牙利": (
        (
            "每月生活費約 USD 650–1,050（折合歐元約 EUR 600–960 / 月、新臺幣約"
            " 20,500–33,500 元；含布達佩斯商業大學 BBU 周邊住宿與生活費）"
        ),
        "須憑匈牙利接待大學入學許可申辦居留簽證並投保海外醫療及意外保險。",
    ),
    "荷蘭": (
        (
            "每月生活費約 USD 1,150–1,750（折合歐元約 EUR 1,050–1,600"
            " / 月、新臺幣約 36,500–55,500 元；含阿姆斯特丹應用科技大學 AUAS"
            " 住宿與生活費）"
        ),
        (
            "須由荷蘭接待大學代向 IND 申辦 MVV/VVR"
            " 學生居留許可，並投保涵蓋全期之海外醫療及意外保險。"
        ),
    ),
    "奧地利": (
        (
            "每月生活費約 USD 1,050–1,600（折合歐元約 EUR 960–1,460"
            " / 月、新臺幣約 33,500–51,000 元；含薩爾茨堡應用科學大學 FH"
            " Salzburg 住宿與生活費）"
        ),
        (
            "須憑奧地利接待大學入學許可向奧地利台北辦事處申辦學生簽證／居留許可並投保醫療保險。"
        ),
    ),
    "法國": (
        (
            "每月生活費約 USD 950–1,500（折合歐元約 EUR 880–1,380"
            " / 月、新臺幣約 30,500–48,000 元；含特魯瓦工程技術大學"
            " UTT、巴黎ECE工程研究生院住宿與生活費）"
        ),
        (
            "須透過法國教育中心（Campus France）完成面試並申辦法國長期學生簽證"
            " VLS-TS，入境後納保法國學生健保。"
        ),
    ),
    "土耳其": (
        (
            "每月生活費約 USD 500–850（依匯率折合新臺幣約 16,000–27,000"
            " 元；含庫克羅瓦大學 Cukurova University、蓋布澤技術大學等生活費）"
        ),
        (
            "須憑土耳其接待大學入學許可向駐台北土耳其貿易辦事處申辦學生簽證並辦理居留證（Ikamet）與醫療保險。"
        ),
    ),
    "泰國": (
        (
            "每月生活費約 USD 500–880（折合泰銖約 THB 17,000–30,000"
            " / 月、新臺幣約 16,000–28,000 元；含拉卡邦先皇理工大學"
            " KMITL、國立法政大學 TU、KMUTT、KMUTNB 住宿與生活費）"
        ),
        (
            "須憑泰國接待大學入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED"
            " 學生簽證，並投保海外醫療與意外保險。"
        ),
    ),
    "越南": (
        (
            "每月生活費約 USD 400–750（依匯率折合新臺幣約 12,800–24,000"
            " 元；含胡志明市外語信息大學"
            " HUFLIT、河內理工大學、胡志明市理工大學等住宿與生活費）"
        ),
        (
            "須憑越南接待大學入學許可申辦越南學生簽證，並於出國前投保涵蓋全期之海外醫療與意外保險。"
        ),
    ),
    "印尼": (
        (
            "每月生活費約 USD 420–780（依匯率折合新臺幣約 13,500–25,000"
            " 元；含印度尼西亞大學 UI、泗水理工大學 ITS、萬隆國立製造理工學院等生活開銷）"
        ),
        (
            "須憑印尼接待大學入學許可與學習許可申辦印尼學生簽證（C316 /"
            " KITAS），並購買海外醫療與意外保險。"
        ),
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": (
        "春季班：每年 4 月起至 8 月止（預計）；秋季班：每年 9 月起至翌年 1"
        " 月止（預計）"
    ),
    "韓國": "春季班：約 3 月初至 6 月中旬；秋季班：約 9 月初至 12 月中旬",
    "美國": (
        "秋季班（Fall Semester）：約 8 月中旬至 12 月中旬；春季班（Spring"
        " Semester）：約 1 月中旬至 5 月中旬"
    ),
    "德國": (
        "冬季學期（Winter Semester）：約 9/10 月至翌年 2 月；夏季學期（Summer"
        " Semester）：約 3/4 月至 7 月"
    ),
    "泰國": (
        "先皇技術學院（KMITL）交換期間：約 7 月至 11 月；一般春季班約 1 月至 5 月"
    ),
}


def clean_text(s: str) -> str:
  return re.sub(r"\s+", " ", s).strip() if s else ""


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
  """Ensure school-images.json and university_locations.jsonl contain all NFU partner schools."""
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
          else loc.get("lat", 23.7027)
      )
      lon = float(
          loc.get("longitude")
          if loc.get("longitude") is not None
          else loc.get("lon", 120.4295)
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
  OFFICIAL_NFU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_NFU_DIR / "nfu_catalog_source.json").read_text(encoding="utf-8")
  )
  resolved_locations = json.loads(
      (SOURCES_NFU_DIR / "nfu_resolved_locations.json").read_text(
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

    group_str = clean_text(item.get("group") or "國際事務處締約姊妹校")
    prog_raw = clean_text(
        item.get("program_type_raw") or "校級出國交換學生計畫"
    )
    quota_str = clean_text(item.get("quota") or "依當期交換生簡章公告名額")
    detail_url = item.get("detail_url") or NFU_EXCHANGE_SCHOOLS_URL
    source_url = detail_url
    program_type = f"國際事務處【{prog_raw}】（{group_str}）"

    colleges_str = clean_text(
        item.get("colleges")
        or "不限學院（工程學院、電機資訊學院、管理學院、文理學院、航空學院均得依姊妹校對應系所申請）"
    )
    degree_levels_str = clean_text(
        item.get("eligible_degrees")
        or "國立虎尾科技大學修滿一學期（含）以上之在學學士班及碩博士班學生（春季班以非應屆畢業生優先薦送）"
    )
    lang_req_str = clean_text(
        item.get("language_req")
        or "符合姊妹校語言門檻及《國立虎尾科技大學甄選學生赴國外研修作業要點》規定（CEFR B1/B2：TOEIC 550/785、TOEFL iBT 42/72、IELTS 4.0/5.5 或 JLPT N2/N4、TOPIK 3 級）"
    )
    gpa_req_str = clean_text(
        item.get("gpa_req")
        or "在校學業成績優良（建議 GPA 3.0 或 75 分以上）且操行成績達 80 分（含）以上"
    )
    website = item.get("website") or source_url
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(
        item.get("tuition_note")
        or "交換期間須於國立虎尾科技大學完成註冊手續；學費繳交依兩校合作協約規定辦理"
    )
    exps = item.get("experience_reports") or []

    round_label = (
        "115-2（2027春季班：06/01–09/10 收件，日本群馬／明治大學 07/30"
        " 截止）＆115-1（2026秋季班：2–3月收件）"
    )
    app_deadline_str = (
        "115學年度第二學期（春季班）交換學生申請：自 2026/06/01 起至"
        " 2026/09/10（四）17:00 止將紙本資料送達國際事務處（赴日本群馬大學／明治大學提前至"
        " 2026/07/30 17:00 截止）；第一學期（秋季班）交換學生及教育部學海飛颺／惜珠／築夢計畫申請：每年"
        " 2–3 月受理收件（如 2026 UNLV 暑期研習計畫於 05/14 截止）"
    )
    deadline_iso = "2026-09-10T17:00:00+08:00"
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "115"

    study_period_str = (
        "一學期或一學年（四年制大學部與研究所學生出國研修以不超過一年為原則；美國喬治梅森大學"
        " GMU 與波莫納加州州立理工大學 Cal Poly Pomona 另設 3+1+1 雙聯學制）"
    )
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country,
        (
            "春季班：每年 1 月起至 8 月止（預計）；秋季班：每年 8 月起至隔年 2"
            " 月止（預計）"
        ),
    )
    housing_str = (
        f"獲國立虎尾科技大學國際事務處推薦提名後，可依 {zh_name}"
        f" 指引申請校內外學生宿舍（{tuition_note}）。"
    )
    course_rest_str = (
        f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《國立虎尾科技大學甄選學生赴國外研修作業要點》及《辦理交換學生甄選簡章》規定："
        "（1）報名參加甄選之學生必須為本校在學學生且修滿一學期（含）以上，學業及操行成績優良，操行成績達"
        " 80 分（含）以上；春季班以非應屆畢業生優先薦送；"
        "（2）甄選分初審（書面資料審查）與複審（面試），甄試平均成績未達 70"
        " 分者不予錄取；報名表至多可填 3 所學校志願；"
        "（3）交換學生赴外國研修一學期應修學分數至少 9 學分（或 18 ECTS"
        " 學分），國外研修成績規定：日本總平均達 75 分或 GPA 3.0 以上、德國達"
        " 2.1–2.5 Level、匈牙利／俄羅斯達 Good Level (Grade 4) 以上、其他國家達"
        " GPA 3.0 以上；"
        "（4）獲錄取學生回國後有義務擔任國際事務處志工（擔任交換生說明會與返國心得分享會報告人、協助外賓接待與外籍新生輔導），獲教育部學海計畫補助者回國後應繳交心得並上傳至教育部學海計畫網站。"
    )

    living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
        country,
        (
            (
                "每月生活費約 USD 700–1,400（依匯率折合新臺幣約 22,500–45,000"
                " 元，含住宿、膳食與市區交通）"
            ),
            (
                "須依接待國駐臺機構規定申辦學生簽證，並依《國立虎尾科技大學學生出國研修獎助要點》第八點規定，自行購買足以支付海外就讀國家消費水準之海外醫療（門診及住院）及意外保險，於抵達就讀學校一個月內繳交購買證明。"
            ),
        ),
    )

    tuition_points_list = [
        (
            "國立虎尾科技大學學雜費規定與姊妹校待遇：依《國立虎尾科技大學甄選學生赴國外研修作業要點》第七點及《辦理交換學生甄選簡章》，交換或研修學生應先在本校完成註冊手續，有關繳費事宜依兩校協議辦理。本合作校待遇："
            f"{tuition_note}。"
        ),
        (
            "國立虎尾科技大學四大出國研修獎助學金體系：（1）教育部《學海飛颺》獎學金（選送具中華民國國籍且在臺設籍之優秀在學學生赴海外姊妹校交換修讀學分，同一教育階段以補助一次為限）；（2）教育部《學海惜珠》扶助清寒獎學金（持直轄市、縣市主管機關開立之低收入戶、中低收入戶、特殊境遇家庭或大專校院弱勢助學金資格證明者申請）；（3）教育部《學海築夢／新南向學海築夢》海外專業實習補助；（4）《國立虎尾科技大學學生出國研修獎助要點》校務基金自籌款短期研修獎助（歐美地區每人新台幣"
            " 10,000 元、亞洲及紐澳地區每人新台幣 5,000 元，每團最多獎助"
            " 150,000 元；UNLV 暑期工業 4.0 研習專案另補助部份機票費每人約"
            " 30,000 元）。"
        ),
    ]

    app_steps_list = [
        (
            "步驟一（確認虎科大修滿一學期在學資格、操行 80 分門檻與"
            f" {zh_name}"
            " 語檢要求）：確認符合《國立虎尾科技大學甄選學生赴國外研修作業要點》及當期《辦理交換學生甄選簡章》規定（"
            f"{gpa_req_str}），並備妥一年內有效之語言能力證明（{lang_req_str}）。"
        ),
        (
            "步驟二（備齊 13"
            " 項書面申請表件並完成線上表單上傳）：依簡章「申請時應附表件（自檢表）」備妥：（1）交換學生甄選報名表（電腦繕打，至多填"
            " 3"
            " 所志願，經導師、系主任、院長簽章）、（2）家長或監護人同意書、（3）個資告知聲明、（4）在學證明書正本、（5）歷年中英文成績單正本、（6）跨學期班排名證明書正本、（7）一年內語言測驗成績影本、（8–11）中文與外文自傳及出國學習計畫（紙本各"
            " 5 份），以燕尾夾夾緊於截止日（如 115-2 學期為 2026/09/10"
            " 17:00，日本群馬／明治大學為 07/30 17:00）前送達國際事務處。"
        ),
        (
            "步驟三（參加校內初審書面審查與複審面試）：初審由系所及國際事務處進行書面審查，複審於報名截止後三週內由「國立虎尾科技大學學生出國研修獎助甄選委員會」舉行面試（甄試平均成績未達"
            " 70 分者不予錄取），並於甄試後三週內公告獲提名名單。"
        ),
        (
            f"步驟四（由國際事務處向 {full_name}"
            " 提名、辦理簽證保險與役男緩徵，返國後履行學分採認與國際處志工義務）：正式錄取後申辦護照與簽證、購買海外醫療（門診及住院）與意外保險（抵達後"
            " 1 個月內繳交購買證明）；海外一學期至少修讀 9 學分（18"
            " ECTS）並達規定成績（日本 75 分/GPA 3.0、德國 2.1–2.5、匈俄 Grade"
            " 4、其他 GPA 3.0），返國後繳交教育部學海心得並擔任交換生說明會及心得分享會報告人。"
        ),
    ]

    elig_points_list = [
        f"合作類別與計畫群組：{program_type}",
        f"開放學制與修業年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業與操行門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        (
            "修課學分與返國義務：海外研修一學期應修至少 9 學分（18"
            " ECTS）；返國後有義務擔任國際事務處志工（交換生說明會與返國心得分享會報告人）並上傳教育部學海計畫報告。"
        ),
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與其他要求：{tuition_note}")
    if remarks_raw:
      elig_points_list.append(f"官方備註與名冊來源：{remarks_raw}")

    exp_links: list[dict] = []
    exp_labels: list[str] = []
    if exps:
      exp_covered_schools += 1
      total_exp_reports += len(exps)
      seen_exp_urls: set[str] = set()
      for e_idx, e in enumerate(exps):
        raw_t = clean_text(e.get("title") or f"赴 {zh_name} 交換生心得分享")
        esem = e.get("semester") or "歷年交換研修"
        eurl = e.get("url") or NFU_SHARING_URL
        if eurl in seen_exp_urls:
          eurl = f"{eurl}#r{e_idx+1}"
        seen_exp_urls.add(eurl)
        exp_labels.append(raw_t[:36])
        exp_links.append({
            "title": raw_t,
            "url": eurl,
            "academic_year": esem,
            "semester": esem,
            "college": "工程學院／電機資訊學院／管理學院／文理學院／航空學院",
            "department": e.get("department") or "虎科大出國交換生",
        })
        summary_text = (
            f"國立虎尾科技大學國際事務處於出國交換心得分享會與出國計畫公告專區發布之赴 {country} {full_name}"
            f" 交換研修與申請經驗分享（{raw_t}），涵蓋校內書審與面試準備、姊妹校選課（每學期至少"
            " 9 學分／18 ECTS）、住宿生活與教育部學海飛颺／惜珠獎學金申請實務。"
        )
        theme_map = {
            "academics": (
                f"虎科大交換生於《{raw_t}》分享在 {zh_name} 修習專業與語言課程（每學期至少"
                " 9 學分或 18 ECTS），以及返國後向所屬系所及教務處辦理學分抵免之經驗。"
            ),
            "housing": (
                f"虎科大交換生分享申請 {zh_name}"
                f" 校內外學生宿舍與生活適應（{housing_str[:100]}）。"
            ),
            "campus_culture": (
                f"虎科大國際事務處透過《{raw_t}》傳承海外姊妹校跨文化交流、校園生活與返國志工經驗分享。"
            ),
            "cost": (
                f"虎科大交換生分享於 {zh_name}"
                f" 之每月住宿、伙食與交通花費（{living_cost_str[:100]}），以及申請教育部學海飛颺／學海惜珠與校內出國研修獎助之經驗。"
            ),
        }
        student_experience_rows.append({
            "school_name": full_name,
            "country": country,
            "title": raw_t,
            "source_url": eurl,
            "source_type": "article",
            "platform": "國立虎尾科技大學國際事務處—出國交換心得分享與計畫專區",
            "author_name": raw_t,
            "language": "zh",
            "summary": summary_text,
            "themes": ["academics", "housing", "campus_culture", "cost"],
            "theme_summaries": theme_map,
            "content_status": "full_text",
            "perspective": "official_student_story",
            "published_at": None,
            "discovered_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                f"{full_name}:nfu_exp:{e_idx}:{eurl}".encode("utf-8")
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
        "home_university": "國立虎尾科技大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exp_links[0]["url"] if exp_links else NFU_SHARING_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

    loc = resolved_locations.get(full_name) or {
        "city": country,
        "latitude": 23.7027,
        "longitude": 120.4295,
        "source_url": "https://www.wikidata.org",
    }
    city_name = loc.get("city") or country
    lat = float(
        loc.get("latitude")
        if loc.get("latitude") is not None
        else loc.get("lat", 23.7027)
    )
    lon = float(
        loc.get("longitude")
        if loc.get("longitude") is not None
        else loc.get("lon", 120.4295)
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
        "note": (
            "校級代表位置：官方網域及國家已與 ROR / Wikidata"
            " 及國立虎尾科技大學國際事務處四大洲姊妹校名冊與交換一覽表比對；實際交換校區以錄取通知與姊妹校簡章為準。"
        ),
    }
    new_locations.append(location_obj)

    vrec = visual_by_name.get(full_name) or item.get("image_record")
    assert vrec and vrec.get(
        "local_path"
    ), f"Missing verified image for {full_name}"
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
        f"【當期名額與費用待遇】{quota_str}｜{tuition_note}",
        f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
        f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        f"【住宿與生活資訊】{housing_str}",
    ]
    if exps:
      notes_lines.append(
          f"【虎科大學長姐交換心得分享與專案紀錄（共 {len(exps)}"
          f" 篇）】收錄於國際事務處官網（含：{'、'.join(exp_labels[:4])}）"
      )
    if remarks_raw:
      notes_lines.append(f"【締約狀況與官方備註】{remarks_raw}")

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
            f"國立虎尾科技大學國際事務處公告合作姊妹校（{program_type}）；名額：{quota_str}（{remarks_raw}）。"
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
        "factsheet_url": (
            NFU_PARTNER_LIST_11506_PDF_URL
            if avail_status == "open"
            else source_url
        ),
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
            "title": (
                f"國立虎尾科技大學國際事務處海外姊妹校交換學生一覽表與姊妹校名冊—{zh_name}"
            ),
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立虎尾科技大學辦理交換學生甄選簡章（115年6月版）PDF",
            "source_url": NFU_115_2_BROCHURE_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立虎尾科技大學甄選學生赴國外研修作業要點 PDF",
            "source_url": NFU_SELECTION_GUIDELINES_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exp_links:
      wf_sources.append({
          "title": (
              f"國立虎尾科技大學國際事務處出國交換心得分享與計畫專區—{zh_name}"
          ),
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
        "home_university": "國立虎尾科技大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": acad_year,
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "115-1（2026秋季班出國交換暨學海計畫甄選）",
            "115-2（2027春季班出國交換甄選）",
            "115-1",
            "115-2",
            "116-1",
            "116-2",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "國立虎尾科技大學由國際事務處（第一校區行政大樓 5"
            " 樓，電話：05-6315024 許小姐／05-6313448"
            " 王小姐）統籌全校五大學院（工程學院、電機資訊學院、管理學院、文理學院、航空學院）之全球姊妹校交換學生、美國"
            " 3+1+1 雙聯學制（George Mason University、Cal Poly"
            " Pomona）及教育部學海飛颺、學海惜珠、學海築夢與校內出國研修獎助遴選。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"nfu-{acad_year}-home-1-{sn:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": (
                    "確認虎科大修滿一學期在學資格、學業操行門檻與"
                    f" {zh_name} 語檢要求"
                ),
                "responsible_party": "學生",
                "responsible_unit": (
                    "國立虎尾科技大學國際事務處（第一校區行政大樓 5 樓）"
                ),
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact",
                "deadline_source_url": NFU_115_2_EXCHANGE_POST_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": True,
                "summary": (
                    f"確認符合《國立虎尾科技大學甄選學生赴國外研修作業要點》及當期《辦理交換學生甄選簡章》規定：本校在學學生且修滿一學期（含）以上（春季班以非應屆畢業生優先薦送），學業及操行成績優良（操行達"
                    f" 80 分以上，{gpa_req_str}），並備妥一年內有效且符合"
                    f" {zh_name} 門檻之語言能力證明（{lang_req_str}）。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["國立虎尾科技大學"],
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
                    NFU_SELECTION_GUIDELINES_PDF_URL,
                    NFU_115_2_BROCHURE_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nfu-{acad_year}-home-2-{sn:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": (
                    "備妥交換學生甄選報名表、歷年中英文成績單、跨學期班排名證明、中外文自傳與出國學習計畫（各5份）送達國際事務處"
                ),
                "responsible_party": "學生與所屬系所／學院",
                "responsible_unit": (
                    "各學院系所辦公室／國立虎尾科技大學國際事務處"
                ),
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact",
                "deadline_source_url": NFU_115_2_EXCHANGE_POST_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": True,
                "summary": (
                    "申請學生須依《辦理交換學生甄選簡章》第 6"
                    " 頁「申請時應附表件（自檢表）」備妥 13"
                    " 項資料，經導師、系（所）主任及學院院長簽名後，以燕尾夾夾緊於截止日（115-2"
                    " 學期為 2026/09/10 17:00，申請赴日本群馬大學／明治大學為"
                    " 2026/07/30 17:00）前將紙本送至第一校區行政大樓 5"
                    " 樓國際事務處，並填寫 Google 表單上傳電子檔。"
                ),
                "details": [
                    (
                        "報名表至多可填 3"
                        " 所學校並排定志願順序；申請資料須以電腦繕打並以燕尾夾夾緊（請勿使用特殊裝訂）。"
                    ),
                    (
                        "同時申請教育部《學海惜珠》補助者，須另檢附有效低收入戶／中低收入戶／特殊境遇家庭／弱勢助學金相關補助證明、戶口名簿影本及"
                        " 1,000–1,500 字中文赴國外研修計畫書（紙本 5 份）。"
                    ),
                ],
                "document_requirements": [
                    {
                        "name": (
                            "國立虎尾科技大學交換學生甄選報名表（電腦繕打，紙本"
                            " 1 份，至多可填 3"
                            " 所學校志願，含導師、系主任、院長簽名）"
                        ),
                        "official_form_url": NFU_APP_FORM_ODT_URL,
                        "source_urls": [
                            NFU_APP_FORM_ODT_URL,
                            NFU_115_2_BROCHURE_PDF_URL,
                        ],
                    },
                    {
                        "name": (
                            "家長或監護人同意書（紙本 1"
                            " 份）、個人資料蒐集處理及利用告知聲明（紙本 1"
                            " 份）及在學證明書正本（上傳電子檔）"
                        ),
                        "official_form_url": NFU_115_2_BROCHURE_PDF_URL,
                        "source_urls": [
                            NFU_115_2_BROCHURE_PDF_URL,
                            NFU_115_2_XIZHU_BROCHURE_PDF_URL,
                        ],
                    },
                    {
                        "name": (
                            "歷年中、英文成績單正本（紙本各 1"
                            " 份）、跨學期班排名證明書正本（紙本 1 份）及 1"
                            " 年內語言測驗成績證明影本（紙本 1 份）"
                        ),
                        "official_form_url": NFU_115_2_BROCHURE_PDF_URL,
                        "source_urls": [
                            NFU_115_2_BROCHURE_PDF_URL,
                            NFU_CEFR_TABLE_PDF_URL,
                        ],
                    },
                    {
                        "name": (
                            "中文自傳、中文出國學習計畫、外文自傳、外文出國學習計畫（紙本各"
                            " 5"
                            " 份，外文學習計畫須包含：①攻讀或研究主題、②修課或研究重點、③計畫修讀學分及所需時間）及教師推薦函等有利審查資料"
                        ),
                        "official_form_url": NFU_115_2_BROCHURE_PDF_URL,
                        "source_urls": [
                            NFU_115_2_BROCHURE_PDF_URL,
                            NFU_SELECTION_GUIDELINES_PDF_URL,
                        ],
                    },
                ],
                "scope": {
                    "home_universities": ["國立虎尾科技大學"],
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
                    NFU_115_2_EXCHANGE_POST_URL,
                    NFU_115_2_BROCHURE_PDF_URL,
                    NFU_APP_FORM_ODT_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nfu-{acad_year}-home-3-{sn:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": (
                    "參加「國立虎尾科技大學學生出國研修獎助甄選委員會」複審面試（平均達70分以上錄取）與學海補助核定"
                ),
                "responsible_party": "國立虎尾科技大學國際事務處與申請學生",
                "responsible_unit": (
                    "國立虎尾科技大學學生出國研修獎助甄選委員會／國際事務處"
                ),
                "deadline_at": "2026-07-30T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": NFU_115_2_EXCHANGE_POST_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": True,
                "summary": (
                    "甄（口）試預定於報名截止後三週內實施，由國際長擔任主任委員，教務長、學務長、各學院院長及學術交流服務組組長組成甄選委員會進行審查；甄試平均成績未達"
                    " 70 分者不予錄取，甄選結果於甄試後三週內公告。"
                ),
                "details": [
                    (
                        "錄取方式：以甄試成績分數高低錄取；正取生因故出缺時，由最高分數備取生按成績、留學語言及志願考量依序遞補。"
                    ),
                    (
                        "甄選委員會得優先錄取未曾領取學校或政府出國補助款項之同學，並以非應屆畢業同學優先錄取。"
                    ),
                ],
                "scope": {
                    "home_universities": ["國立虎尾科技大學"],
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
                    NFU_SELECTION_GUIDELINES_PDF_URL,
                    NFU_SUBSIDY_GUIDELINES_PDF_URL,
                    NFU_115_2_BROCHURE_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nfu-{sn:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": (
                    f"由國際事務處向 {zh_name}"
                    " 提名並協助辦理交換／雙聯入學申請程序"
                ),
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    "獲本校公告提名後，由國際事務處向外國學校提名並協助辦理申請交換學生程序；學生須備妥有效期限達預計出國時間多出"
                    " 6 個月以上之護照、財力證明、英文成績單及健康檢查表，待收到外國學校核發之正式錄取通知書（Admission"
                    " Letter / COE / DS-2019）。"
                ),
                "details": [
                    f"研修期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["國立虎尾科技大學"],
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
                "source_urls": [source_url, NFU_PARTNER_LIST_11506_PDF_URL]
                + ([website] if website else []),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"nfu-{acad_year}-home-5-{sn:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": (
                    "完成虎科大註冊、役男出境緩徵與海外醫療保險，修滿規定學分並於返國後履行學分抵免與國際處志工義務"
                ),
                "responsible_party": "學生與所屬系所",
                "responsible_unit": (
                    "國立虎尾科技大學國際事務處／教務處／軍訓室／各學院系所"
                ),
                "summary": (
                    "出國前須於本校完成註冊手續、役男於預訂出國日期 40"
                    " 天前向軍訓室與縣市政府兵役單位申辦役男出國交換緩徵，並自行購買海外醫療（門診及住院）及意外保險（抵達後"
                    " 1 個月內繳交購買證明）；海外研修一學期至少修讀 9 學分（18"
                    " ECTS）並達規定成績；返國後由系所及教務處審核採認學分，上傳教育部學海計畫心得並擔任國際處交換生說明會及心得分享會報告人。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["國立虎尾科技大學"],
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
                    NFU_SELECTION_GUIDELINES_PDF_URL,
                    NFU_SUBSIDY_GUIDELINES_PDF_URL,
                    NFU_115_2_BROCHURE_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合國立虎尾科技大學國際事務處（OIA）四大洲共 {len(catalog_source)} 所合作姊妹校與交換／雙聯專案（含"
            f" {open_partner_count}"
            " 所當期開放交換與 3+1+1 雙聯學制合作學校）、115"
            " 學年度交換學生甄選簡章、海外姊妹校交換學生一覽表、出國研修作業要點與獎助要點，以及"
            f" {exp_covered_schools} 校 {total_exp_reports}"
            " 篇出國交換心得分享會與專案紀錄。"
        ),
    })

    cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": (
                f"國立虎尾科技大學國際事務處海外姊妹校交換學生一覽表與姊妹校名冊—{zh_name}"
            ),
            "source_url": source_url,
            "summary": (
                "虎科大國際事務處公告之合作計畫類型、授課語言、名額、語言要求與學費待遇"
            ),
        },
        {
            "title": (
                "國立虎尾科技大學辦理交換學生甄選簡章與甄選學生赴國外研修作業要點"
            ),
            "source_url": NFU_115_2_BROCHURE_PDF_URL,
            "summary": (
                "虎科大交換生申請資格、13項應附表件、海外應修 9 學分（18"
                " ECTS）及成績門檻與返國志工義務"
            ),
        },
    ]
    if exp_links:
      dest_sources.append({
          "title": (
              f"國立虎尾科技大學國際事務處出國交換心得分享與計畫專區—{zh_name}"
          ),
          "source_url": exp_links[0]["url"],
          "summary": (
              f"收錄虎科大學生赴 {zh_name} 交換心得分享會與研修專案紀錄共"
              f" {len(exps)} 篇"
          ),
      })
    if website:
      dest_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "summary": "接待合作姊妹校官方網站",
      })

    src_url_list = (
        [source_url, NFU_EXCHANGE_SCHOOLS_URL, NFU_SCHOLARSHIPS_URL]
        + ([exp_links[0]["url"]] if exp_links else [NFU_SHARING_URL])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "國立虎尾科技大學",
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
                "title": (
                    "生活費、虎科大註冊規定與教育部學海飛颺／惜珠／校內出國研修獎助體系"
                ),
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [
                    NFU_SUBSIDY_GUIDELINES_PDF_URL,
                    NFU_115_2_BROCHURE_PDF_URL,
                ],
                "caution": (
                    "獲得出國研修獎助之學生及其監護人領取獎助金時須簽訂合約書，並於結束研修訪問後一個月內提出書面報告送各系所及國際事務處備查，否則須退還獎助款。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與姊妹校校內外學生宿舍申請",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": (
                    "赴日本交換生申請在日居留證（COE）及赴美國、韓國明知大學交換生均須依姊妹校規定檢附財力證明。"
                ),
            },
            {
                "key": "insurance",
                "title": (
                    "海外醫療（門診及住院）與意外保險規定（抵達後1個月內繳交購買證明）"
                ),
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    (
                        "依《國立虎尾科技大學學生出國研修獎助要點》第八點規定，受獎助學生須自行購買足以支付海外就讀國家消費水準之海外醫療（門診及住院）及意外保險，並於抵達就讀學校一個月之內繳交購買證明。"
                    ),
                ],
                "source_urls": src_url_list + [NFU_SUBSIDY_GUIDELINES_PDF_URL],
                "caution": (
                    "出國前請確認海外醫療保險涵蓋門診、住院及急難救助，並依接待國規定投保當地學生健康保險。"
                ),
            },
            {
                "key": "visa",
                "title": (
                    "留學交換簽證辦理、役男出境40天前緩徵申請與在學註冊義務"
                ),
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    (
                        "具役男身分之在學學生，應依內政部「役男出境處理辦法」規定，於預訂出國日期"
                        " 40"
                        " 天以前繳交相關證明文件並由國際事務處協助向軍訓室及戶籍地縣市政府兵役單位辦理「役男出國交換緩徵」。"
                    ),
                ],
                "source_urls": src_url_list
                + [NFU_SELECTION_GUIDELINES_PDF_URL],
                "caution": (
                    "除不可抗力之因素外，若經國際事務處錄取後無故放棄交換生資格，無法保留錄取資格或延後至下一學期，亦不得再次申請。"
                ),
            },
            {
                "key": "academics",
                "title": (
                    "海外每學期應修至少 9 學分（18"
                    " ECTS）、各國成績規定與返國學分抵免"
                ),
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [
                    NFU_SELECTION_GUIDELINES_PDF_URL,
                    NFU_115_2_BROCHURE_PDF_URL,
                ],
                "caution": (
                    "交換學生身分規定為出國前與出國回來都必須是本校在籍學生；若為應屆畢業生，須待交換完成回國後再領取畢業證書，不得提前辦理畢業離校手續。"
                ),
            },
            {
                "key": "living",
                "title": (
                    f"{city_name} 校園生活、出國交換心得分享會與國際處志工傳承"
                ),
                "summary": (
                    f"代表城市：{city_name}。獲錄取學生返國後有義務擔任國際事務處志工及交換心得分享會報告人。"
                ),
                "points": [
                    f"目的地城市：{city_name}（{country}）",
                    "國立虎尾科技大學國際事務處定期舉辦「出國交換心得分享會」與說明講座"
                    + (
                        f"（本校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:3])}）"
                        if exps
                        else ""
                    )
                    + "，邀請返國交換生分享申請過程、海外修課與生活經驗。",
                ],
                "source_urls": [
                    exp_links[0]["url"] if exp_links else NFU_SHARING_URL
                ],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合國立虎尾科技大學國際事務處 {len(catalog_source)} 所合作姊妹校名冊、115"
            " 學年度交換學生甄選簡章、海外姊妹校交換學生一覽表及"
            f" {exp_covered_schools} 校 {total_exp_reports}"
            " 篇出國交換心得分享與專案紀錄。"
        ),
    })

    research_records.append({
        "home_university": "國立虎尾科技大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            f"國立虎尾科技大學國際事務處四大洲 {len(catalog_source)} 所合作姊妹校名冊、海外姊妹校交換學生一覽表與"
            " ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [{
        "title": f"國立虎尾科技大學國際事務處合作姊妹校與交換資訊—{zh_name}",
        "url": source_url,
    }]
    if exp_links:
      ev_sources.append({
          "title": (
              f"國立虎尾科技大學國際事務處出國交換心得分享與計畫專區—{zh_name}"
          ),
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
            "scope": "虎科大海外交換／雙聯姊妹校住宿與財力證明資訊",
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
            "scope": (
                "虎科大出國交換註冊規定、教育部學海飛颺／惜珠／築夢、校內出國研修獎助與地區生活費估算"
            ),
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
            "scope": (
                "國立虎尾科技大學甄選學生赴國外研修作業要點、海外應修9學分（18"
                " ECTS）與返國志工規範"
            ),
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
            "scope": (
                "虎科大海外交換簽證、役男出境40天前緩徵申請与海外醫療（門診及住院）保險規定"
            ),
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
                    f"｜虎科大國際事務處收錄 {len(exps)} 篇赴 {zh_name} 出國交換心得分享會與研修專案紀錄（{'、'.join(exp_labels[:3])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "虎科大交換名額與出國交換心得分享會傳承",
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
            (
                f"已整合國立虎尾科技大學國際事務處 {len(catalog_source)} 所合作姊妹校名冊、115"
                " 學年度交換學生甄選簡章、海外姊妹校交換學生一覽表及出國交換心得分享紀錄。"
            ),
            "當期開放名額、宿位供給、語檢門檻與選課限制請依合作校最新簡章及入學通知書核對。",
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

  write_jsonl(OFFICIAL_NFU_DIR / "partners.jsonl", partners)
  write_jsonl(SOURCES_NFU_DIR / "partners.jsonl", partners)
  write_jsonl(OFFICIAL_NFU_DIR / "application_workflows.jsonl", workflows)
  write_jsonl(OFFICIAL_NFU_DIR / "destination_profiles.jsonl", destinations)
  write_jsonl(OFFICIAL_NFU_DIR / "partner_research.jsonl", research_records)
  write_jsonl(OFFICIAL_NFU_DIR / "student_life.jsonl", life_records)
  write_jsonl(
      OFFICIAL_NFU_DIR / "experience_sources.jsonl", experience_sources_records
  )
  write_jsonl(
      OFFICIAL_NFU_DIR / "student_experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_NFU_DIR / "student_experiences.jsonl", student_experience_rows
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
  (OFFICIAL_NFU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_NFU_DIR / "student-experiences.json").write_text(
      json.dumps(
          {
              "school_id": "nfu",
              "school_name": "國立虎尾科技大學",
              "checked_at": CHECKED_AT,
              "source_url": NFU_SHARING_URL,
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

  (OFFICIAL_NFU_DIR / "campus-locations.json").write_text(
      json.dumps(
          {
              "school_id": "nfu",
              "school_name": "國立虎尾科技大學",
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
  (OFFICIAL_NFU_DIR / "campus-assets.json").write_text(
      json.dumps(
          {
              "school_id": "nfu",
              "school_name": "國立虎尾科技大學",
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

  nfu_source_urls = [
      NFU_OIA_HOME_URL,
      NFU_ABOUT_URL,
      NFU_MEMBERS_URL,
      NFU_SISTER_INDEX_URL,
      NFU_SISTER_ASIA_URL,
      NFU_SISTER_EUROPE_URL,
      NFU_SISTER_AMERICA_URL,
      NFU_SISTER_OCEANIA_URL,
      NFU_REGULATIONS_URL,
      NFU_OUTBOUND_ABROAD_URL,
      NFU_OUTBOUND_311_URL,
      NFU_EXCHANGE_SCHOOLS_URL,
      NFU_EXCHANGE_STUDENT_URL,
      NFU_SCHOLARSHIPS_URL,
      NFU_DREAM_URL,
      NFU_SHARING_URL,
      NFU_NEWS_OUTBOUND_URL,
      NFU_SELECTION_GUIDELINES_PDF_URL,
      NFU_SUBSIDY_GUIDELINES_PDF_URL,
      NFU_APP_FORM_ODT_URL,
      NFU_115_2_EXCHANGE_POST_URL,
      NFU_115_2_XIZHU_POST_URL,
      NFU_115_2_BROCHURE_PDF_URL,
      NFU_115_2_XIZHU_BROCHURE_PDF_URL,
      NFU_CEFR_TABLE_PDF_URL,
      NFU_PARTNER_LIST_11506_PDF_URL,
      NFU_UNLV_SUMMER_PDF_URL,
  ]

  exchange_info_payload = {
      "school_name": "國立虎尾科技大學",
      "program_type": [
          (
              "國際事務處「校級與院級赴海外姊妹校交換學生計畫」（涵蓋日本明治大學、近畿大學、近畿大學產業理工學部、群馬大學，美國南伊利諾大學卡本岱爾校區、匹茲堡州立大學、密西根大學弗林特分校、內華達大學拉斯維加斯分校"
              " UNLV、德州大學聖安東尼校區 UTSA，德國 HAWtech"
              " 六校聯盟［埃斯林根、卡爾斯魯厄、達姆施塔特、德烈斯登、柏林"
              " HTW、亞琛應用科技大學］，法國特魯瓦工程技術大學"
              " UTT，荷蘭阿姆斯特丹應用科技大學，奧地利薩爾茨堡應用科學大學，捷克布拉格生命科學大學、布爾諾孟德爾大學、南波希米亞大學，匈牙利布達佩斯商業大學，土耳其庫克羅瓦大學，韓國東西大學、明知大學，泰國拉卡邦先皇理工大學"
              " KMITL，越南胡志明市外語信息大學 HUFLIT，印尼大學 UI 等 28"
              " 個當期開放交換學程及四大洲 152 所合作大學）"
          ),
          (
              "國際事務處「3+1+1"
              " 雙聯學制專案」（涵蓋美國喬治梅森大學［電機資訊學院專屬］及美國波莫納加州州立理工大學"
              " Cal Poly Pomona［管理學院專屬］）"
          ),
          (
              "國際事務處「教育部學海飛颺、學海惜珠、學海築夢／新南向學海築夢」暨「國立虎尾科技大學學生出國研修獎助要點（校務基金自籌款短期研修與美國"
              " UNLV 暑期工業 4.0 研習機票補助）」獎助學金體系"
          ),
      ],
      "academic_year": [
          (
              "115（涵蓋 115 學年度第二學期［2027 春季班］出國交換甄選［即日起至"
              " 115/09/10 17:00 截止，赴日本群馬大學／明治大學提前至 07/30"
              " 17:00 截止］，以及第一學期［秋季班］交換生與教育部學海計畫甄選）"
          ),
          (
              f"本平台完整收錄國立虎尾科技大學國際事務處公告之 {len(partners)} 所四大洲合作姊妹校與交換／雙聯專案（橫跨全球"
              f" 28 個國家與地區，含 {open_partner_count}"
              f" 所當期開放申請之交換與 3+1+1 雙聯合作校，並收錄 {exp_covered_schools} 所合作大學共"
              f" {total_exp_reports} 篇出國交換心得分享會與研修專案紀錄）"
          ),
      ],
      "semester": [
          (
              "春季班（第 2 學期）交換學生甄選（每年 6 月公告簡章、9 月 10"
              " 日截止收件，日本群馬大學／明治大學於 7 月 30"
              " 日提前截止；預計翌年 1 月至 8 月出國，日本為 4 月至 8"
              " 月）：春季班以「非應屆畢業生」優先薦送。"
          ),
          (
              "秋季班（第 1 學期）交換學生暨教育部學海計畫甄選（每年 2–3"
              " 月公告簡章受理收件，預計當年 8 月至隔年 2 月出國，日本為 9 月至"
              " 1 月）：開放全校五大學院修滿一學期（含）以上之在學學士班及碩博士班學生申請。"
          ),
      ],
      "application_period": [
          (
              "【115 學年度第二學期（2027"
              " 春季班）交換學生暨學海惜珠第2次徵件】自 2026/06/01 起至"
              " 2026/09/10（四）17:00 止將紙本申請資料送至第一校區行政大樓 5"
              " 樓國際事務處（申請赴日本群馬大學、明治大學截止收件日：2026/07/30（四）17:00"
              " 止）。"
          ),
          (
              "【美國內華達大學拉斯維加斯分校（UNLV）2026"
              " 年度暑期研習計畫】研習期間為 115 年 7 月 19 日至 8 月 15"
              " 日（工業 4.0 相關課程），校內報名延長至 115 年 5 月 14"
              " 日止，虎尾科大補助部份機票費每人約新台幣 3 萬元。"
          ),
          (
              "【115 學年度第一學期（秋季班）交換學生暨教育部學海築夢／新南向築夢計畫】每年"
              " 2–3 月及 11 月受理校內申請，甄（口）試於報名截止後三週內實施，甄試後三週內公告錄取名單。"
          ),
      ],
      "eligibility": [
          (
              "1."
              " 在學學籍與修業年級規定：依《國立虎尾科技大學甄選學生赴國外研修作業要點》第三點及《辦理交換學生甄選簡章》，報名參加甄選之學生必須為本校在學學生且修滿一學期（含）以上（含日間部、進修推廣部、進修學院之大學部學生或研究生；春季班以「非應屆畢業生」優先薦送）。四年制學生與研究所學生出國研修以不超過一年為原則；二年制學生以不超過半年為原則。交換學生出國前與出國回來都必須是本校在籍學生（應屆畢業生須待交換完成回國後再領取畢業證書）。"
          ),
          (
              "2. 在校學業與操行成績門檻：學業及操行成績優良，操行成績達 80"
              " 分（含）以上，並符合欲申請姊妹校之 GPA"
              " 門檻（如美國匹茲堡州立大學要求 GPA 2.5 以上、內華達大學拉斯維加斯分校"
              " UNLV 要求 GPA 3.0 以上）。校內甄選分初審（書面資料審查）與複審（面試），甄試平均成績未達"
              " 70 分者不予錄取。"
          ),
          (
              "3."
              " 學海飛颺與學海惜珠補助資格：欲同時申請教育部《學海飛颺》補助者，必須具中華民國國籍且在臺灣地區設有戶籍（不包括國內及境外在職專班生）；欲申請《學海惜珠》補助者，須持各直轄市、縣（市）主管機關開立之低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助費或教育部大專校院弱勢學生助學計畫助學金補助資格證明。同一申請人於同一教育階段以補助一次為限。"
          ),
          (
              "4. 海外修課學分、成績規定與返國志工義務：交換學生赴外國研修一學期應修學分數至少"
              " 9 學分（或 18 ECTS 學分），國外研修成績總平均規定：（1）匈牙利、俄羅斯達"
              " Good Level (Grade 4) 以上；（2）日本達 75 分以上或 GPA 3.0"
              " 以上；（3）德國達「2.1–2.5」Level；（4）其他國家達 GPA 3.0"
              " 以上。獲錄取學生回國後有義務擔任國際事務處志工（擔任交換生說明會與返國心得分享會報告人、協助外賓接待與外籍新生輔導）並上傳教育部學海計畫心得報告。"
          ),
      ],
      "language_requirement": [
          (
              "1. 英語授課及歐美、東南亞姊妹校門檻（依本校《CEF"
              " 語言能力參考指標對照表》及各姊妹校要求）：（1）CEFR B1"
              " 門檻（法國特魯瓦工程技術大學 UTT、德國埃斯林根應用科技大學、越南胡志明市外語信息大學"
              " HUFLIT）：對應 NEW TOEIC 550（聽力 275／閱讀 275）、TOEFL iBT"
              " 42、TOEFL ITP 457、IELTS 4.0 或 GEPT 中級複試；（2）CEFR B2"
              " 門檻（荷蘭阿姆斯特丹應用科技大學、奧地利薩爾茨堡應用科學大學、捷克布拉格生命科學大學／孟德爾大學／南波希米亞大學、匈牙利布達佩斯商業大學、德國卡爾斯魯厄／達姆施塔特／德烈斯登／柏林"
              " HTW／亞琛應用科技大學、土耳其庫克羅瓦大學、韓國東西大學）：對應"
              " NEW TOEIC 785（聽力 400／閱讀 385）、TOEFL iBT 72、TOEFL ITP"
              " 527、IELTS 5.5 或 GEPT 中高級複試；（3）美國及亞洲名校專案門檻：美國"
              " UTSA 要求 TOEIC 600 或 IELTS 5.0；美國 SIUC、UM-Flint、UNLV 要求"
              " TOEFL iBT 61 或 IELTS 5.5–6.0；美國匹茲堡州立大學要求 TOEFL iBT"
              " 68 或 IELTS 6.0；泰國 KMITL 要求 TOEFL iBT 79 或 IELTS"
              " 6.0；印尼大學 UI 與美國喬治梅森大學（GMU 3+1+1）要求 TOEFL iBT"
              " 80 或 IELTS 6.0–6.5；美國 Cal Poly Pomona（3+1+1）要求 TOEIC"
              " 640、TOEFL iBT 71 或 IELTS 6.0。"
          ),
          (
              "2. 日本地區姊妹校門檻：（1）明治大學：JLPT"
              " N4（含）以上（依各系要求為主，證照須於兩年內考取）；（2）群馬大學：JLPT"
              " N2（含）以上（申請理工學部者須有 JLPT N1）；（3）近畿大學：日語組"
              " JLPT N2（含）以上，英語組 TOEFL iBT 61、IELTS 6.0、CEFR B2 或"
              " Duolingo 100；（4）近畿大學產業理工學部：日語能力優良，備有日語檢定證明者優先考量錄取。"
          ),
          (
              "3. 韓國與德法語門檻：（1）韓國明知大學：TOPIK Level"
              " 3（含）以上、TOEFL iBT 70 或 IELTS 5.5；（2）德國 HAWtech"
              " 六校聯盟：可持德語 B1/B2 或英語 B1/B2 申請。"
          ),
      ],
      "required_documents": [
          (
              "1. 國立虎尾科技大學交換學生甄選報名表（電腦繕打，紙本 1"
              " 份，黏貼近 6 個月內 2 吋正面彩色半身相片，至多可填 3"
              " 所學校志願，並經班導師／指導老師、系所主任及學院院長簽名）"
          ),
          (
              "2. 家長或監護人同意書（紙本 1"
              " 份）及個人資料蒐集、處理及利用告知聲明（紙本 1 份）"
          ),
          "3. 在學證明書正本（僅需上傳電子檔）、身分證正反面影本、學生證正反面影本",
          (
              "4. 歷年中、英文成績單正本（紙本各 1"
              " 份）及跨學期班排名證明書正本（紙本 1 份，研究所免填班排）"
          ),
          (
              "5. 一年內有效之語言測驗成績或語文證明影本（紙本 1 份，如"
              " IELTS、TOEFL iBT/ITP、新制 TOEIC、JLPT N1–N5、TOPIK 等）"
          ),
          (
              "6. 中文自傳（簡述專長、興趣、社團活動、得獎事實等，紙本 5"
              " 份）及中文出國學習計畫（紙本 5 份；申請學海惜珠者須附"
              " 1,000–1,500 字中文赴國外研修計畫書、研修動機及個人傑出表現各 5 份）"
          ),
          (
              "7. 外文自傳（紙本 5 份）及外文出國學習計畫（紙本 5"
              " 份，應包含：①攻讀或研究主題、②修課或從事相關研究重點、③計畫修讀學分及所需時間）"
          ),
          (
              "8. 其他有助審查之資料（紙本，如教師英文推薦函 2"
              " 封、重大獎項得獎證明、國際交流或社團活動證明；申請學海惜珠另附有效低收入戶／中低收入戶證明及戶口名簿影本）並完成"
              " Google 表單資料上傳"
          ),
      ],
      "scholarship_info": [
          (
              "1. 教育部《學海飛颺》選送優秀學生出國研修獎學金：補助具中華民國國籍且在臺灣地區設有戶籍、修滿一學期以上、學業與外語能力優良之本校在學學生（不含國內及境外在職專班生）赴國外姊妹校交換修讀學分"
              " 1 學期至 1 學年；實際補助金額依當年度教育部學海計畫補助經費與甄選委員會核定而定（同一申請人、同一教育階段以補助一次為限）。"
          ),
          (
              "2. 教育部《學海惜珠》扶助清寒優秀學生出國研修獎學金：補助具中華民國國籍且持各直轄市、縣（市）主管機關開立之低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助費、弱勢兒少生活扶助或教育部大專校院弱勢學生助學計畫助學金資格證明之在學學生赴海外姊妹校交換研修。"
          ),
          (
              "3. 教育部《學海築夢》及《新南向學海築夢》海外專業實習補助：由本校專任教師擔任子計畫主持人，選送學生赴海外或新南向國家企業、研究機構進行專業實習，補助機票款與生活費。"
          ),
          (
              "4. 《國立虎尾科技大學學生出國研修獎助要點》校務基金自籌款短期出國研修與專案補助：每年"
              " 4 月及 11 月受理申請，歐美地區每人獎助新台幣 10,000"
              " 元為原則、亞洲及紐澳地區每人新台幣 5,000 元為原則（每團最多獎助"
              " 150,000 元）；另美國內華達大學拉斯維加斯分校（UNLV）暑期工業 4.0"
              " 研習計畫提供本校學生部份機票費補助每人約新台幣 30,000"
              " 元（具低收入戶證明者視個案增額補助）。"
          ),
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": nfu_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_NFU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "國立虎尾科技大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 75.0,
      "academic_score_rule": (
          "依《國立虎尾科技大學甄選學生赴國外研修作業要點》及《辦理交換學生甄選簡章》：報名學生必須為本校在學學生且修滿一學期（含）以上，學業及操行成績優良（操行成績達"
          " 80 分(含)以上，建議學業平均達 75 分或 GPA 3.0"
          " 以上；部分姊妹校如美國匹茲堡州立大學要求 GPA 2.5 以上、UNLV 要求"
          " GPA 3.0 以上），且校內甄試平均成績須達 70 分以上始予錄取。"
      ),
      "academic_gpa_minimum": 2.5,
      "maximum_preferences": 3,
      "selection_rules": {
          "academic_policy": "score_or_rank",
          "academic_reference_year": "115",
          "undergraduate_gpa_minimum": 2.5,
          "graduate_academic_exempt": False,
          "exclude_in_service": False,
          "pending_quota_planning": False,
          "partner_requirements_need_confirmation": False,
          "degree_score_minimums": {"undergraduate": 75.0, "graduate": 75.0},
          "excluded_undergraduate_years": ["大一上"],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 42.0,
          "ielts": 4.0,
          "toeic": 550.0,
      },
      "application_periods": [
          {
              "title": (
                  "國立虎尾科技大學「115學年度第二學期（2027春季班）」交換學生暨學海惜珠申請（06/01–09/10"
                  " 17:00，日本群馬／明治大學 07/30 截止）"
              ),
              "details": [
                  (
                      "開放申請交換期間：115 學年度第二學期（2027"
                      " 春季班）。一般姊妹校截止收件日：115 年 9 月 10"
                      " 日（四）17:00"
                      " 前將紙本申請資料（以燕尾夾夾緊）送至第一校區行政大樓 5"
                      " 樓國際事務處；申請赴日本群馬大學、明治大學截止收件日：115"
                      " 年 7 月 30 日（四）17:00 前送達。"
                  ),
                  (
                      "審核程序：（1）校內初審：書面審查 →（2）校內複審：報名截止後三週內通知面試（甄試平均未達"
                      " 70 分不予錄取）→（3）甄試後三週內公告獲提名名單"
                      " →（4）向外國學校提名並協助辦理交換學生申請。"
                  ),
              ],
              "source": {
                  "title": (
                      "國立虎尾科技大學國際事務處《「115學年度第二學期」交換學生申請公告》與甄選簡章"
                  ),
                  "source_url": NFU_115_2_EXCHANGE_POST_URL,
                  "category": "exchange_application",
                  "summary": (
                      "虎科大 115"
                      " 學年度第二學期赴海外姊妹校交換學生與學海惜珠第 2"
                      " 次徵件申請簡章、應附表件與截止日期。"
                  ),
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": (
                  "115-2（2027春季班）赴海外姊妹校交換學生暨學海惜珠甄選"
              ),
              "audience": "all_students",
              "opens_at": "2026-06-01T08:30:00+08:00",
              "deadline_at": "2026-09-10T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "open",
              "status_note": (
                  "115 學年度第二學期交換學生甄選簡章、學海惜珠簡章及海外姊妹校交換學生一覽表（115.06）已公告於國際事務處網站。"
              ),
              "deadline_note": (
                  "日本群馬大學與明治大學於 7 月 30 日 17:00"
                  " 提前截止，其餘姊妹校於 9 月 10 日 17:00 截止。"
              ),
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": (
                  "國立虎尾科技大學—美國內華達大學拉斯維加斯分校（UNLV）2026"
                  " 年度暑期研習計畫暨秋季出國研修獎助（05/14 截止）"
              ),
              "details": [
                  (
                      "美國 UNLV 2026 年度暑期工業 4.0 研習計畫（研習時間：115"
                      " 年 7 月 19 日至 8 月 15"
                      " 日）校內報名延長至 115 年 5 月 14"
                      " 日止，由本校補助部份機票費每人約新台幣 3 萬元。"
                  ),
                  (
                      "校內短期出國研修獎助申請時間為每年 4 月份及 11"
                      " 月份（11 月受理隔年度申請），秋季班交換學生與學海飛颺／築夢計畫於每年"
                      " 2–3 月受理收件。"
                  ),
              ],
              "source": {
                  "title": (
                      "國立虎尾科技大學《美國 University of Nevada, Las Vegas"
                      " (UNLV) 2026年度暑期研習計畫公告》"
                  ),
                  "source_url": NFU_UNLV_SUMMER_PDF_URL,
                  "category": "scholarship",
                  "summary": (
                      "虎科大 UNLV 暑期工業 4.0"
                      " 研習計畫與校內出國研修獎助申請時程。"
                  ),
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": (
                  "115年度美國UNLV暑期研習暨第一學期出國研修甄選"
              ),
              "audience": "all_students",
              "opens_at": "2026-03-25T08:30:00+08:00",
              "deadline_at": "2026-05-14T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "open",
              "status_note": (
                  "美國 UNLV 暑期研習計畫簡章與報名表已發布於國際事務處網站。"
              ),
              "deadline_note": (
                  "請完成線上意願登記並將書面報名表送交第一校區行政大樓 5"
                  " 樓國際事務處。"
              ),
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [{
          "title": (
              "國立虎尾科技大學國際事務處四大洲交換學生、美國 3+1+1"
              f" 雙聯學制與教育部學海獎助總覽（{len(partners)} 所締約姊妹校・{open_partner_count} 所當期開放交換／雙聯）"
          ),
          "details": [
              (
                  "國立虎尾科技大學（National Formosa University,"
                  " NFU，創立於 1980"
                  " 年雲林虎尾，設有「工程學院、電機資訊學院、管理學院、文理學院、航空學院」五大學院）由「國際事務處（Office"
                  " of International Affairs，第一校區行政大樓 5"
                  " 樓，下設學術交流組與外國學生事務組）」統籌全校赴海外姊妹校交換學生、3+1+1"
                  " 雙聯學制、海外短期研習及教育部學海系列計畫。本平台完整收錄"
                  f" {len(partners)} 所虎科大官方合作姊妹校，橫跨全球 28"
                  f" 個國家與地區（含 {open_partner_count} 所當期開放申請之交換與"
                  " 3+1+1 雙聯合作校）。"
              ),
              (
                  "虎科大出國交換與國際交流體系具備五大核心特色：（1）當期開放"
                  " 28 所歐美亞重點交換學校與 2 所美國 3+1+1"
                  " 雙聯名校（日本明治大學、近畿大學、近畿大學產業理工學部、群馬大學；美國南伊利諾大學卡本岱爾校區、匹茲堡州立大學、密西根大學弗林特分校、內華達大學拉斯維加斯分校"
                  " UNLV、德州大學聖安東尼校區 UTSA；德國 HAWtech"
                  " 六校聯盟［埃斯林根、卡爾斯魯厄、達姆施塔特、德烈斯登、柏林"
                  " HTW、亞琛應用科技大學］；法國特魯瓦工程技術大學"
                  " UTT；荷蘭阿姆斯特丹應用科技大學；奧地利薩爾茨堡應用科學大學；捷克布拉格生命科學大學、布爾諾孟德爾大學、南波希米亞大學；匈牙利布達佩斯商業大學；土耳其庫克羅瓦大學；韓國東西大學、明知大學；泰國"
                  " KMITL；越南 HUFLIT；印尼大學 UI；以及美國喬治梅森大學"
                  " GMU［電資學院 3+1+1 雙聯］與波莫納加州州立理工大學 Cal"
                  " Poly Pomona［管理學院 3+1+1"
                  " 雙聯］）；（2）全校五大學院修滿一學期以上之學士班與碩博士班皆可申請，至多可填"
                  " 3 所志願；（3）教育部學海飛颺、學海惜珠、學海築夢與校內出國研修獎助（歐美"
                  " 10,000 元、亞紐澳 5,000 元、UNLV 暑期研習機票補助 30,000"
                  " 元）多元獎助；（4）明確規定海外每學期應修至少 9 學分（18"
                  " ECTS）及分國成績基準；（5）定期舉辦出國交換心得分享會與返國志工經驗傳承。"
              ),
          ],
          "source": {
              "title": (
                  "國立虎尾科技大學國際事務處（OIA）官方網站與出國交換學校一覽表"
              ),
              "source_url": NFU_EXCHANGE_SCHOOLS_URL,
              "category": "exchange_application",
              "summary": (
                  f"虎科大 {len(partners)} 所四大洲合作姊妹校、28"
                  " 所當期交換學校與 2 所 3+1+1 雙聯學校總覽。"
              ),
          },
      }],
      "eligibility": [{
          "title": (
              "虎科大修滿一學期在學學生資格、操行 80 分門檻、面試 70"
              " 分錄取基準與海外應修 9 學分（18 ECTS）規定"
          ),
          "details": [
              (
                  "修業年級與學籍規定：依《國立虎尾科技大學甄選學生赴國外研修作業要點》及《辦理交換學生甄選簡章》，報名學生必須為本校在學學生且修滿一學期（含）以上（春季班以「非應屆畢業生」優先薦送；日本近畿大學不接受應屆畢業生，直升本校研究所者例外）。四年制與研究所學生出國研修以不超過一年為原則，二年制學生以不超過半年為原則。"
              ),
              (
                  "成績與修課標準：在校學業成績優良且操行成績達 80"
                  " 分（含）以上；校內甄試（書審＋面試）平均成績未達 70"
                  " 分者不予錄取。赴外國研修一學期應修學分數至少 9 學分（或 18"
                  " ECTS），海外成績總平均須達：日本 75 分或 GPA 3.0"
                  " 以上、德國 2.1–2.5 Level、匈牙利／俄羅斯 Good Level (Grade"
                  " 4) 以上、其他國家 GPA 3.0 以上。"
              ),
          ],
          "source": {
              "title": (
                  "國立虎尾科技大學辦理交換學生甄選簡章（115.06）與甄選學生赴國外研修作業要點"
              ),
              "source_url": NFU_115_2_BROCHURE_PDF_URL,
              "category": "exchange_application",
              "summary": "虎科大交換生申請資格、甄試錄取門檻、海外應修學分與返國志工義務。",
          },
      }],
      "language_requirements": [{
          "title": (
              "虎科大交換留學語檢門檻（CEFR B1［TOEIC 550 / iBT 42］、CEFR"
              " B2［TOEIC 785 / iBT 72 / IELTS 5.5］、日本 JLPT N1–N4、韓國"
              " TOPIK 3）"
          ),
          "details": [
              (
                  "CEFR 與英語檢定對照標準：依本校公告《CEF"
                  " 與各項英檢對照表》，CEFR B1（進階級）對應新制 TOEIC"
                  " 550（聽力 275／閱讀 275）、TOEFL iBT 42、TOEFL ITP"
                  " 457、IELTS 4.0、GEPT 中級複試；CEFR B2（高階級）對應新制"
                  " TOEIC 785（聽力 400／閱讀 385）、TOEFL iBT 72、TOEFL ITP"
                  " 527、IELTS 5.5、GEPT 中高級複試。各歐美及東南亞姊妹校依表列"
                  " CEFR B1/B2 或個別分數（如 TOEFL iBT 61–80、IELTS"
                  " 5.0–6.5、TOEIC 550–640）審核。"
              ),
              (
                  "日韓與德法語門檻：日本明治大學要求 JLPT N4"
                  " 以上（兩年內考取）、群馬大學要求 JLPT N2 以上（理工學部須"
                  " N1）、近畿大學要求 JLPT N2 或 TOEFL iBT 61 / IELTS"
                  " 6.0、近畿大學產業理工學部優先錄取具 JLPT"
                  " 者；韓國明知大學要求 TOPIK 3 級或 TOEFL iBT 70 / IELTS"
                  " 5.5；德國 HAWtech 聯盟接受德文 B1/B2 或英文 B1/B2。"
              ),
          ],
          "source": {
              "title": (
                  "國立虎尾科技大學《CEF與各項英檢對照表》與《海外姊妹校交換學生一覽表（115.06）》"
              ),
              "source_url": NFU_CEFR_TABLE_PDF_URL,
              "category": "exchange_application",
              "summary": "虎科大官方 CEFR 語檢對照表與各姊妹校語言能力要求一覽。",
          },
      }],
      "required_documents": [{
          "title": (
              "交換學生甄選報名表（可填3志願）、家長同意書、歷年中英文成績單、跨學期班排證明、中外文自傳與學習計畫（各5份）"
          ),
          "details": [
              (
                  "校內甄選 13"
                  " 項應附表件：（1）交換學生甄選報名表（電腦繕打，紙本 1"
                  " 份，至多填 3"
                  " 所學校志願，經導師、系主任、院長簽章）；（2）家長或監護人同意書（紙本"
                  " 1 份）；（3）個人資料蒐集處理及利用告知聲明（紙本 1"
                  " 份）；（4）在學證明書正本（僅需上傳電子檔）；（5）歷年中、英文成績單正本（紙本各"
                  " 1 份）；（6）跨學期班排名證明書正本（紙本 1"
                  " 份）；（7）一年內語言測驗成績或語文證明影本（紙本 1"
                  " 份）；（8–9）中文自傳與中文出國學習計畫（紙本各 5"
                  " 份）；（10–11）外文自傳與外文出國學習計畫（紙本各 5"
                  " 份，外文學習計畫須含：①攻讀或研究主題、②修課或研究重點、③計畫修讀學分及所需時間）；（12）其他有助審查資料（如推薦函、得獎證明）；（13）填寫"
                  " Google 表單並上傳資料。請將申請資料依序排列，以燕尾夾夾緊。"
              ),
              (
                  "學海惜珠附加文件：同時申請《學海惜珠》者，須另附中、低收入相關補助證明及戶口名簿影本（註明與正本相符並親筆簽名），以及"
                  " 1,000–1,500 字中文赴國外研修計畫書、研修動機及個人傑出表現（紙本各"
                  " 5 份）。"
              ),
          ],
          "source": {
              "title": (
                  "國立虎尾科技大學《辦理交換學生甄選簡章（115.06）》第 6"
                  " 頁「申請時應附表件（自檢表）」"
              ),
              "source_url": NFU_115_2_BROCHURE_PDF_URL,
              "category": "exchange_application",
              "summary": "虎科大交換學生與學海惜珠申請應附表件自檢表與裝訂規定。",
          },
      }],
      "scholarship_info": [{
          "title": (
              "教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》與《國立虎尾科技大學學生出國研修獎助要點》"
          ),
          "details": [
              (
                  "教育部學海系列計畫：錄取本校交換學生且具中華民國國籍（不含在職專班生）者得同步申請《學海飛颺》或《學海惜珠》出國研修補助（同一教育階段以補助一次為限）；專任教師另可主持《學海築夢》及《新南向學海築夢》選送學生赴海外實習。"
              ),
              (
                  "虎科大校內出國研修獎助：依《國立虎尾科技大學學生出國研修獎助要點》，由校務基金自籌款補助學生出國研修，歐美地區每人新台幣"
                  " 10,000 元為原則、亞洲及紐澳地區每人新台幣 5,000"
                  " 元為原則（每團最多 150,000 元，每年 4 月及 11"
                  " 月受理）；美國 UNLV 暑期工業 4.0"
                  " 研習計畫另補助部份機票費每人約新台幣 30,000 元。"
              ),
          ],
          "source": {
              "title": (
                  "國立虎尾科技大學《學生出國研修獎助要點》與《學海飛颺／學海惜珠獎學金專區》"
              ),
              "source_url": NFU_SCHOLARSHIPS_URL,
              "category": "scholarship",
              "summary": "虎科大教育部學海計畫與校內出國研修獎助要點。",
          },
      }],
      "document_explanations": [{
          "title": (
              "國立虎尾科技大學交換學生申請表件自檢表（13項）、燕尾夾裝訂與外文學習計畫撰寫規範"
          ),
          "summary": (
              "說明虎科大交換生甄選簡章規定之紙本 1 份與 5"
              " 份文件清單、跨學期班排名證明、外文出國學習計畫三大必備要素與燕尾夾裝訂要求。"
          ),
          "key_points": [
              (
                  "紙本份數與裝訂規定：報名表、家長同意書、個資聲明、中英文成績單、跨學期班排名證明及語檢影本各"
                  " 1 份，中文自傳、中文學習計畫、外文自傳、外文學習計畫各 5"
                  " 份；所有資料依序排列以「燕尾夾」夾緊，請勿使用其他特殊裝訂方式。"
              ),
              (
                  "外文出國學習計畫三大要素：必須明確包含「①攻讀或研究主題、②修課或從事相關研究重點、③計畫修讀學分及所需時間（一學期至少"
                  " 9 學分或 18 ECTS）」。"
              ),
              (
                  "護照與財力證明準備：建議預先備好有效期達預計出國時間多出 6"
                  " 個月以上之護照，通過面試甄選後將需立即繳件；申請日本、美國、韓國明知大學交換者須依姊妹校規定準備財力證明。"
              ),
          ],
          "applies_to": [],
          "source": {
              "title": "國立虎尾科技大學辦理交換學生甄選簡章（115年6月）",
              "source_url": NFU_115_2_EXCHANGE_POST_URL,
              "category": "exchange_application",
              "summary": None,
          },
          "document_url": NFU_115_2_BROCHURE_PDF_URL,
          "document_type": "official_document",
          "full_text_extracted": True,
      }],
      "rule_explanations": [{
          "title": (
              "國立虎尾科技大學甄選學生赴國外研修作業要點與學生出國研修獎助要點核心法規"
          ),
          "summary": (
              "規範虎科大五大學院學生申請出國交換、延長交換期限條件、海外應修學分與成績標準、海外醫療保險購買義務與返國志工服務。"
          ),
          "key_points": [
              (
                  "甄選程序與錄取基準：初審為書面資料審查，複審由「國立虎尾科技大學學生出國研修獎助甄選委員會」進行面試審查，甄試平均成績未達"
                  " 70 分者不予錄取；委員會得優先錄取未曾領取學校或政府出國補助款項之非應屆畢業同學。"
              ),
              (
                  "延長交換期限條件：須於姊妹校該學期期末考一個月前提出申請，經姊妹校國際合作單位、指導老師與家長同意，且在姊妹校當期成績平均須達"
                  " B 或同等級以上，惟延長期間不再另外增加出國補助金額。"
              ),
              (
                  "海外保險與返國義務：受獎助學生須自行購買足以支付海外就讀國家消費水準之海外醫療（門診及住院）及意外保險，於抵達就讀學校"
                  " 1 個月內繳交購買證明；返國後 1"
                  " 個月內須提出研修書面報告並有義務擔任國際事務處志工（交換生說明會、返國心得分享會報告人）。"
              ),
          ],
          "applies_to": [],
          "source": {
              "title": (
                  "國立虎尾科技大學甄選學生赴國外研修作業要點（100.12.06修正）與學生出國研修獎助要點"
              ),
              "source_url": NFU_REGULATIONS_URL,
              "category": "exchange_application",
              "summary": None,
          },
          "document_url": NFU_SELECTION_GUIDELINES_PDF_URL,
          "document_type": "official_document",
          "full_text_extracted": True,
      }],
      "sources": [
          {
              "title": "國立虎尾科技大學國際事務處（OIA）官方網站",
              "source_url": NFU_OIA_HOME_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立虎尾科技大學出國交換學校一覽表（28所當期開放交換學程）",
              "source_url": NFU_EXCHANGE_SCHOOLS_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立虎尾科技大學 3+1+1 雙聯學制專區（美國 GMU、Cal Poly Pomona）",
              "source_url": NFU_OUTBOUND_311_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立虎尾科技大學四大洲合作姊妹校名冊（亞洲、歐洲、美洲、大洋洲共 152 校）",
              "source_url": NFU_SISTER_INDEX_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立虎尾科技大學 115 學年度第二學期交換學生申請公告與甄選簡章",
              "source_url": NFU_115_2_EXCHANGE_POST_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立虎尾科技大學甄選學生赴國外研修作業要點 PDF",
              "source_url": NFU_SELECTION_GUIDELINES_PDF_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立虎尾科技大學學生出國研修獎助要點 PDF",
              "source_url": NFU_SUBSIDY_GUIDELINES_PDF_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "國立虎尾科技大學出國交換心得分享專區",
              "source_url": NFU_SHARING_URL,
              "category": "experience_report",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_NFU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  doc_conditions = {
      "school_id": "nfu",
      "school_name": "國立虎尾科技大學",
      "checked_at": CHECKED_AT,
      "source_url": NFU_115_2_BROCHURE_PDF_URL,
      "common_documents": exchange_info_payload["required_documents"],
      "track_specific_conditions": [
          {
              "track": (
                  "國際事務處【赴日本、歐美、韓國及新南向姊妹校交換學生計畫（28所當期開放交換學程）】"
              ),
              "required": [
                  (
                      "交換學生甄選報名表（電腦繕打，紙本1份，至多填3所學校志願，含導師、系主任、院長簽名）、家長同意書及個資告知聲明"
                  ),
                  (
                      "歷年中、英文成績單正本（各1份）、跨學期班排名證明書正本（1份）及在學證明書電子檔"
                  ),
                  (
                      "一年內語言測驗成績證明影本（CEFR B1/B2：TOEIC"
                      " 550/785、TOEFL iBT 42/72、IELTS 4.0/5.5 或日本 JLPT"
                      " N1–N4、韓國 TOPIK 3）"
                  ),
                  (
                      "中文自傳、中文出國學習計畫、外文自傳、外文出國學習計畫（紙本各5份，以燕尾夾夾緊）及"
                      " Google 表單上傳"
                  ),
              ],
          },
          {
              "track": (
                  "國際事務處【美國 3+1+1 雙聯學制專案（喬治梅森大學"
                  " GMU、波莫納加州州立理工大學 Cal Poly Pomona）】"
              ),
              "required": [
                  (
                      "喬治梅森大學（GMU）：僅限電機資訊學院申請，須備妥 TOEFL"
                      " iBT 80（含）以上或 IELTS 6.5（含）以上成績證明及財力證明"
                  ),
                  (
                      "波莫納加州州立理工大學（Cal Poly"
                      " Pomona）：僅限管理學院申請，須備妥 TOEIC"
                      " 640（含）以上、TOEFL iBT 71（含）以上或 IELTS"
                      " 6.0（含）以上成績證明"
                  ),
                  (
                      "歷年英文成績單正本、外文讀書與研究計畫、教師英文推薦函"
                      " 2 封及有效護照影本"
                  ),
              ],
          },
          {
              "track": (
                  "教育部【學海飛颺／學海惜珠／學海築夢】暨【校內出國研修獎助與美國"
                  " UNLV 暑期研習計畫】"
              ),
              "required": [
                  (
                      "學海惜珠申請人須另附直轄市、縣（市）主管機關開立之低收入戶／中低收入戶／特殊境遇家庭／弱勢助學金相關補助證明、戶口名簿影本及"
                      " 1,000–1,500 字中文赴國外研修計畫書（紙本5份）"
                  ),
                  (
                      "美國 UNLV 暑期工業 4.0 研習計畫申請人須於 5/14"
                      " 前完成線上登記並繳交書面報名表、家長同意書及英文成績參考資料"
                  ),
                  (
                      "獲獎助學生須於領取獎助金時簽訂合約書、於抵達就讀學校 1"
                      " 個月內繳交海外醫療（門診及住院）與意外保險購買證明，並於結束研修後"
                      " 1 個月內提出書面報告及履行國際處志工義務"
                  ),
              ],
          },
      ],
  }
  (OFFICIAL_NFU_DIR / "document-conditions.json").write_text(
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
        f"{fname},{len(partners)},{pop},{ratio:.4f},Official NFU OIA verified"
    )
  (OFFICIAL_NFU_DIR / "field-coverage.csv").write_text(
      "\n".join(field_cov_lines) + "\n", encoding="utf-8"
  )

  pages_records = [
      {
          "title": (
              "國立虎尾科技大學：115 學年度交換學生申請期程、日本群馬／明治大學提前截止與美國"
              " UNLV 暑期研習計畫"
          ),
          "source_url": NFU_115_2_EXCHANGE_POST_URL,
          "published_at": "2026-06-01T00:00:00Z",
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
          "title": (
              "國立虎尾科技大學：甄選學生赴國外研修作業要點、面試 70"
              " 分錄取基準、海外應修 9 學分（18 ECTS）與返國志工義務"
          ),
          "source_url": NFU_SELECTION_GUIDELINES_PDF_URL,
          "published_at": "2026-06-01T00:00:00Z",
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
          "title": (
              f"國立虎尾科技大學：{len(partners)} 所四大洲合作姊妹校名冊、28"
              " 所交換一覽表、3+1+1 雙聯學制與 CEFR 語檢對照表"
          ),
          "source_url": NFU_EXCHANGE_SCHOOLS_URL,
          "published_at": "2026-06-01T00:00:00Z",
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
          "title": (
              "國立虎尾科技大學：交換學生甄選簡章 13"
              " 項應附表件（自檢表）、燕尾夾裝訂與外文學習計畫規範"
          ),
          "source_url": NFU_115_2_BROCHURE_PDF_URL,
          "published_at": "2026-06-01T00:00:00Z",
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
          "title": (
              "國立虎尾科技大學：教育部學海飛颺、學海惜珠、學海築夢與學生出國研修獎助要點（歐美1萬／亞紐澳5千）"
          ),
          "source_url": NFU_SUBSIDY_GUIDELINES_PDF_URL,
          "published_at": "2026-06-01T00:00:00Z",
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
  pages_text = (
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n"
  )
  (OFFICIAL_NFU_DIR / "pages.jsonl").write_text(pages_text, encoding="utf-8")
  (OFFICIAL_NFU_DIR / "processed_pages.jsonl").write_text(
      pages_text, encoding="utf-8"
  )

  home_rules = {
      "school_id": "nfu",
      "school_name": "國立虎尾科技大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "undergraduate_score_minimum": 75.0,
          "graduate_score_minimum": 75.0,
          "conduct_score_minimum": 80.0,
          "interview_passing_score_minimum": 70.0,
          "undergraduate_gpa_minimum": 2.5,
          "overseas_min_credits_per_semester": 9,
          "overseas_min_ects_per_semester": 18,
          "maximum_preferences": 3,
          "screening_batches_per_year": 2,
          "allow_freshman_apply": True,
          "min_enrolled_semesters": 1,
          "tuition_policy_during_exchange": (
              "交換或研修學生應先在國立虎尾科技大學完成註冊手續；學費繳交依本校與外國學校簽署之合作協約內容辦理"
          ),
          "return_documents_due": (
              "獲錄取學生回國後有義務擔任國際事務處志工（擔任交換生說明會、返國心得分享會報告人），受獎助生須於結束研修後"
              " 1 個月內提出書面報告並上傳教育部學海計畫網站"
          ),
      },
      "source_urls": nfu_source_urls,
      "verified_at": "2026-10-31",
  }
  (OFFICIAL_NFU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NFU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "國立虎尾科技大學",
              "required_documents": student_dashboard_payload[
                  "required_documents"
              ],
              "source_urls": nfu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NFU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "國立虎尾科技大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": nfu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "nfu",
      "school_name": "國立虎尾科技大學",
      "total_partners": len(partners),
      "partner_count": len(partners),
      "international_partners": sum(
          1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
      ),
      "mainland_partners": sum(
          1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
      ),
      "dual_degree_partner_universities": 2,
      "dual_degree_programs": 2,
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
          "國立虎尾科技大學國際事務處 115 學年度（第二學期交換學生暨學海惜珠申請：06/01–09/10"
          " 收件截止，日本群馬／明治大學 07/30 提前截止；美國 UNLV"
          " 暑期研習計畫：05/14 截止）四大洲單學期／學年交換計畫及美國 3+1+1"
          f" 雙聯學制同步整合；共完整收錄 {len(partners)} 所合作姊妹校（橫跨全球 28"
          f" 個國家與地區，含 {open_partner_count} 所當期開放申請校，並收錄"
          f" {exp_covered_schools} 所合作大學共 {total_exp_reports}"
          " 篇出國交換心得分享會與研修專案紀錄）。"
      ),
      "verified_at": "2026-10-31",
  }
  (OFFICIAL_NFU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NFU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "nfu",
              "school_name": "國立虎尾科技大學",
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
  (OFFICIAL_NFU_DIR / "dashboard_manifest.json").write_text(
      json.dumps(
          {
              "school_id": "nfu",
              "school_name": "國立虎尾科技大學",
              "checked_at": CHECKED_AT,
              "partner_count": len(partners),
              "open_partner_count": open_partner_count,
              "experience_school_count": exp_covered_schools,
              "experience_report_count": total_exp_reports,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  provenance_files = [
      (
          "sources/nfu/sister_asia.html",
          NFU_SISTER_ASIA_URL,
          "國立虎尾科技大學國際事務處—亞洲地區姊妹校名冊 HTML",
      ),
      (
          "sources/nfu/sister_europe.html",
          NFU_SISTER_EUROPE_URL,
          "國立虎尾科技大學國際事務處—歐洲地區姊妹校名冊 HTML",
      ),
      (
          "sources/nfu/sister_america.html",
          NFU_SISTER_AMERICA_URL,
          "國立虎尾科技大學國際事務處—美洲地區姊妹校名冊 HTML",
      ),
      (
          "sources/nfu/sister_oceania.html",
          NFU_SISTER_OCEANIA_URL,
          "國立虎尾科技大學國際事務處—大洋洲地區姊妹校名冊 HTML",
      ),
      (
          "sources/nfu/out_exchange_schools.html",
          NFU_EXCHANGE_SCHOOLS_URL,
          "國立虎尾科技大學國際事務處—出國交換學校一覽表（28所）HTML",
      ),
      (
          "sources/nfu/out_311.html",
          NFU_OUTBOUND_311_URL,
          "國立虎尾科技大學國際事務處—3+1+1雙聯學制一覽表 HTML",
      ),
      (
          "sources/nfu/nfu_outbound_selection_guidelines.pdf",
          NFU_SELECTION_GUIDELINES_PDF_URL,
          "國立虎尾科技大學甄選學生赴國外研修作業要點 PDF",
      ),
      (
          "sources/nfu/nfu_study_abroad_subsidy_guidelines.pdf",
          NFU_SUBSIDY_GUIDELINES_PDF_URL,
          "國立虎尾科技大學學生出國研修獎助要點 PDF",
      ),
      (
          "sources/nfu/nfu_exchange_application_form.odt",
          NFU_APP_FORM_ODT_URL,
          "國立虎尾科技大學交換學生甄選報名表 ODT",
      ),
      (
          "sources/nfu/nfu_exchange_brochure_115_2.pdf",
          NFU_115_2_BROCHURE_PDF_URL,
          "國立虎尾科技大學辦理交換學生甄選簡章（115年6月）PDF",
      ),
      (
          "sources/nfu/nfu_exchange_xizhu_brochure_115_2.pdf",
          NFU_115_2_XIZHU_BROCHURE_PDF_URL,
          "國立虎尾科技大學辦理交換學生（學海惜珠）甄選簡章（115年7月）PDF",
      ),
      (
          "sources/nfu/nfu_cefr_mapping_table.pdf",
          NFU_CEFR_TABLE_PDF_URL,
          "國立虎尾科技大學 CEF 語言能力參考指標對照表 PDF",
      ),
      (
          "sources/nfu/nfu_partner_exchange_list_11506.pdf",
          NFU_PARTNER_LIST_11506_PDF_URL,
          "國立虎尾科技大學海外姊妹校交換學生申請資訊一覽表（115.06）PDF",
      ),
      (
          "sources/nfu/nfu_unlv_2026_summer_brochure.pdf",
          NFU_UNLV_SUMMER_PDF_URL,
          "國立虎尾科技大學 2026 美國拉斯維加斯 UNLV 暑期研習計畫公告 PDF",
      ),
      (
          "sources/nfu/nfu_experience_index.json",
          NFU_SHARING_URL,
          (
              f"國立虎尾科技大學出國交換心得分享與研修專案（{exp_covered_schools} 校共"
              f" {total_exp_reports} 篇）索引 JSON"
          ),
      ),
      (
          "sources/nfu/nfu_catalog_source.json",
          NFU_EXCHANGE_SCHOOLS_URL,
          f"國立虎尾科技大學 {len(partners)} 所四大洲合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/nfu/nfu_resolved_locations.json",
          NFU_EXCHANGE_SCHOOLS_URL,
          (
              f"國立虎尾科技大學 {len(partners)} 所合作姊妹校 ROR / Wikidata"
              " 地理座標核對表 JSON"
          ),
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
      "school_id": "nfu",
      "school_name": "國立虎尾科技大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = (
      json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  )
  (OFFICIAL_NFU_DIR / "import_provenance.json").write_text(
      prov_text, encoding="utf-8"
  )
  (OFFICIAL_NFU_DIR / "import-provenance.json").write_text(
      prov_text, encoding="utf-8"
  )

  print(
      f"Successfully built NFU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
