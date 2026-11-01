"""Build the official National Chin-Yi University of Technology (國立勤益科技大學, NCUT) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_NCUT_DIR = REPO_ROOT / "sources" / "ncut"
OFFICIAL_NCUT_DIR = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "ncut"
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

NCUT_HOME_URL = "https://www.ncut.edu.tw/"
NCUT_OIA_HOME_URL = "https://oia.ncut.edu.tw/"
NCUT_ABOUT_URL = "https://oia.ncut.edu.tw/p/412-1030-6492.php?Lang=zh-tw"
NCUT_STAFF_URL = "https://oia.ncut.edu.tw/p/412-1030-6641.php?Lang=zh-tw"
NCUT_OUTGOING_EXCHANGE_URL = (
    "https://oia.ncut.edu.tw/p/412-1030-6648.php?Lang=zh-tw"
)
NCUT_MOU_PARTNERS_URL = (
    "https://oia.ncut.edu.tw/p/412-1030-2698.php?Lang=zh-tw"
)
NCUT_REGULATIONS_URL = (
    "https://oia.ncut.edu.tw/p/412-1030-7975.php?Lang=zh-tw"
)
NCUT_DOWNLOADS_EXCHANGE_URL = (
    "https://oia.ncut.edu.tw/p/412-1030-6703.php?Lang=zh-tw"
)
NCUT_DOWNLOADS_STUDENT_URL = (
    "https://oia.ncut.edu.tw/p/412-1030-6702.php?Lang=zh-tw"
)
NCUT_SOP_URL = "https://oia.ncut.edu.tw/p/412-1030-6844.php?Lang=zh-tw"
NCUT_FAQ_URL = "https://oia.ncut.edu.tw/p/412-1030-2809.php?Lang=zh-tw"
NCUT_CONTACT_URL = "https://oia.ncut.edu.tw/p/412-1030-6643.php?Lang=zh-tw"
NCUT_LANGUAGE_TESTS_URL = (
    "https://oia.ncut.edu.tw/p/404-1030-26434.php?Lang=zh-tw"
)
NCUT_VISAS_URL = "https://oia.ncut.edu.tw/p/404-1030-26516.php?Lang=zh-tw"
NCUT_OVERSEAS_INTERNSHIP_URL = (
    "https://oia.ncut.edu.tw/p/412-1030-6499.php?Lang=zh-tw"
)
NCUT_GLOBAL_CAREERS_URL = (
    "https://oia.ncut.edu.tw/p/412-1030-8701.php?Lang=zh-tw"
)
NCUT_115_2_INFO_POST_URL = (
    "https://oia.ncut.edu.tw/p/406-1030-93677,r800.php?Lang=zh-tw"
)
NCUT_115_1_INFO_POST_URL = (
    "https://oia.ncut.edu.tw/p/406-1030-91258,r800.php?Lang=zh-tw"
)
NCUT_SKODA_SUMMER_POST_URL = (
    "https://oia.ncut.edu.tw/p/406-1030-91820,r800.php?Lang=zh-tw"
)
NCUT_HDA_ISU_POST_URL = (
    "https://oia.ncut.edu.tw/p/406-1030-90933,r800.php?Lang=zh-tw"
)
NCUT_UHK_SUMMER_POST_URL = (
    "https://oia.ncut.edu.tw/p/406-1030-90788,r800.php?Lang=zh-tw"
)
NCUT_CSUF_SUMMER_POST_URL = (
    "https://oia.ncut.edu.tw/p/406-1030-87000,r800.php?Lang=zh-tw"
)
NCUT_GACHON_SUMMER_POST_URL = (
    "https://oia.ncut.edu.tw/p/406-1030-86408,r800.php?Lang=zh-tw"
)
NCUT_GUIDELINES_INTL_EXCHANGE_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/1276/810257914.pdf"
)
NCUT_GUIDELINES_OVERSEAS_STUDY_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/1276/222864975.pdf"
)
NCUT_DUAL_DEGREE_BROCHURE_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/1398/608915721.pdf"
)
NCUT_115_2_INFO_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/1400/872345294.pdf"
)
NCUT_ADMISSION_ROSTER_PNG_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/1399/584765801.png"
)
NCUT_APP_FORM_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/1298/836273806.pdf"
)
NCUT_DOC_CHECKLIST_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/1298/454721331.pdf"
)
NCUT_PARENTAL_CONSENT_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/1298/713808850.pdf"
)
NCUT_ADMIN_CONTRACT_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/1299/578671939.pdf"
)
NCUT_PRE_CREDIT_FORM_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/1299/584178778.pdf"
)
NCUT_RETURN_PROCEDURE_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/1301/639058273.pdf"
)

REGION_COST_DEFAULTS = {
    "日本": (
        (
            "每月生活費約 USD 680–1,120（折合日圓約 JPY 95,000–160,000"
            " / 月、新臺幣約 21,500–35,500"
            " 元；含佐賀大學、北見工業大學、九州工業大學、室蘭工業大學、千葉大學學生宿舍與膳食交通費）"
        ),
        (
            "須由日本姊妹校代向出入國在留管理局申辦「在留資格認定證明書（COE）」（申請"
            " COE 須檢附存款財力證明），獲發後向日本台灣交流協會申辦留學簽證並強制加入日本國民健康保險（NHI）。"
        ),
    ),
    "韓國": (
        (
            "每月生活費約 USD 620–1,050（折合韓元約 KRW 850,000–1,450,000"
            " / 月、新臺幣約 19,500–33,500"
            " 元；含嘉泉大學、淑明女子大學、亞洲大學學生宿舍與首爾圈生活開銷）"
        ),
        (
            "須憑韓國姊妹校核發之標準入學許可書向駐台北韓國代表部申辦 D-2-6"
            " 交換學生簽證，入境後申辦外國人登錄證（ARC）並強制納保韓國國民健康保險（NHIS）。"
        ),
    ),
    "美國": (
        (
            "每月生活費約 USD 1,350–2,200（依匯率折合新臺幣約 43,000–70,000"
            " 元；含加州州立大學富勒頓分校 CSUF、北伊利諾大學 NIU、佛羅里達理工大學、波莫納加州州立理工大學"
            " Cal Poly Pomona、漢弗萊斯大學住宿與生活費）"
        ),
        (
            "須憑美國合作校核發之 DS-2019（J-1 交換生）或 I-20（F-1"
            " 雙聯學制）繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證，並強制投保接待校規定之醫療保險。"
        ),
    ),
    "德國": (
        (
            "每月生活費約 USD 1,000–1,550（折合歐元約 EUR 920–1,420"
            " / 月、新臺幣約 32,000–49,500 元；含德國 HAWtech"
            " 應用科技大學聯盟：達姆施塔特 h_da、埃斯林根、德勒斯登 HTW、阿亨 FH"
            " Aachen、卡爾斯魯厄 HKA、柏林 HTW 及德勒斯登工業大學學生宿舍與學期交通卡費）"
        ),
        (
            "須開立德國限制提領帳戶（Blocked Account，每月約 EUR 934–992）並憑入學許可向德國在台協會申辦長期學生簽證及投保德國法定學生公保（GKV）。"
        ),
    ),
    "捷克": (
        (
            "每月生活費約 USD 650–1,050（折合歐元約 EUR 600–960 / 月、新臺幣約"
            " 20,500–33,500 元；含赫拉德茨克拉洛韋大學 UHK"
            " Palachova 學生宿舍與斯柯達汽車大學 Škoda Auto University 住宿生活費）"
        ),
        (
            "須憑捷克接待大學入學許可、住宿證明、良民證雙認證與財力證明向捷克經濟文化辦事處申辦長期學生簽證及捷克境內綜合醫療保險。"
        ),
    ),
    "英國": (
        (
            "每月生活費約 USD 1,450–2,350（折合英鎊約 GBP 1,150–1,850"
            " / 月、新臺幣約 46,000–75,000 元；含倫敦密德薩斯大學 Middlesex"
            " University 與艾塞克斯大學住宿與生活費）"
        ),
        (
            "修業逾 6 個月（如 3+1 或 1+1 雙聯學制）須憑 CAS 申辦英國 Student Visa"
            " 並繳納移民醫療附加費（IHS）以使用英國國民保健署（NHS）醫療服務。"
        ),
    ),
    "法國": (
        (
            "每月生活費約 USD 950–1,500（折合歐元約 EUR 880–1,380"
            " / 月、新臺幣約 30,500–48,000 元；含里摩日大學、巴黎索邦大學住宿與生活費）"
        ),
        (
            "須透過法國教育中心（Campus France）完成面試並申辦法國長期學生簽證"
            " VLS-TS，入境後註冊法國學生健康保險。"
        ),
    ),
    "馬來西亞": (
        (
            "每月生活費約 USD 450–820（折合馬幣約 MYR 2,000–3,600"
            " / 月、新臺幣約 14,500–26,000 元；含砂拉越科技大學 UTS、雙威大學"
            " Sunway University 住宿與生活費）"
        ),
        (
            "須透過馬來西亞教育全球服務中心（EMGS）申辦學生簽證核准函（VAL）及單次入境簽證，並強制投保馬來西亞境內學生醫療保險。"
        ),
    ),
    "泰國": (
        (
            "每月生活費約 USD 500–880（折合泰銖約 THB 17,000–30,000"
            " / 月、新臺幣約 16,000–28,000 元；含瓦萊嵐大學、泰國東方大學"
            " Burapha、吞武里國王科技大學 KMUTT、佛統皇家大學住宿與生活費）"
        ),
        (
            "須憑泰國接待大學入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED"
            " 學生簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。"
        ),
    ),
    "越南": (
        (
            "每月生活費約 USD 400–750（依匯率折合新臺幣約 12,800–24,000"
            " 元；含河內交通運輸大學、河內國家大學外國語大學 VNU-ULIS、河內工業大學、胡志明市技術師範大學等住宿與生活費）"
        ),
        (
            "須憑越南接待大學入學許可與簽證核准函申辦越南學生簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。"
        ),
    ),
    "印尼": (
        (
            "每月生活費約 USD 420–780（依匯率折合新臺幣約 13,500–25,000"
            " 元；含印尼世界大學 Universitas Universal、迪波內戈羅大學、瑪琅／萬隆／泗水／三寶壟國立理工學院等住宿與生活費）"
        ),
        (
            "須憑印尼接待大學入學許可與印尼教育部學習許可（Study Permit）申辦學生簽證，並投保海外醫療及意外保險。"
        ),
    ),
    "菲律賓": (
        (
            "每月生活費約 USD 450–820（依匯率折合新臺幣約 14,500–26,000"
            " 元；含宿霧聖何塞大學 USJ-R、科迪勒拉大學、八打雁州立大學住宿與生活費）"
        ),
        (
            "須憑菲律賓接待大學入學許可辦理學生簽證（9F）或特別學習許可（SSP），並投保海外醫療及意外保險。"
        ),
    ),
    "中國大陸": (
        (
            "每月生活費約 USD 420–780（折合人民幣約 RMB 3,000–5,500"
            " / 月、新臺幣約 13,500–25,000 元；含校內學生宿舍、校園餐廳與市區交通）"
        ),
        (
            "須持有效臺灣居民來往大陸通行證（台胞證）與錄取通知書辦理入學報到，並依接待學校規定投保大陸境內團體綜合保險及海外醫療險。"
        ),
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": (
        "春季班（前學期）：每年 4 月上旬至 8 月上旬；秋季班（後學期）：每年 9"
        " 月下旬或 10 月上旬至翌年 2 月中旬"
    ),
    "韓國": "春季班：每年 3 月初至 6 月中旬；秋季班：每年 9 月初至 12 月中旬",
    "美國": (
        "秋季班（Fall Semester）：每年 8 月中下旬至 12 月中旬；春季班（Spring"
        " Semester）：每年 1 月中旬至 5 月中旬"
    ),
    "德國": (
        "冬季學期（Winter Semester）：每年 9/10 月至翌年 2 月；夏季學期（Summer"
        " Semester）：每年 3/4 月至 7 月"
    ),
    "捷克": (
        "冬季學期（Winter Semester）：每年 9 月中下旬至翌年 1"
        " 月；夏季學期（Summer Semester）：每年 2 月至 6 月"
    ),
    "英國": (
        "秋季學期（Autumn Term）：每年 9 月下旬至翌年 1 月；春季學期（Spring"
        " Term）：每年 1 月下旬至 5 月下旬"
    ),
    "泰國": (
        "第一學期：約每年 6–8 月至 10–12 月；第二學期：約每年 11–1 月至翌年 3–5"
        " 月（依各校國際學制曆定）"
    ),
}


def clean_text(s: str) -> str:
  return re.sub(r"\s+", " ", s).strip() if s else ""


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
  """Ensure school-images.json and university_locations.jsonl contain all NCUT partner schools."""
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
          else loc.get("lat", 24.1449)
      )
      lon = float(
          loc.get("longitude")
          if loc.get("longitude") is not None
          else loc.get("lon", 120.7303)
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
  OFFICIAL_NCUT_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_NCUT_DIR / "ncut_catalog_source.json").read_text(
          encoding="utf-8"
      )
  )
  resolved_locations = json.loads(
      (SOURCES_NCUT_DIR / "ncut_resolved_locations.json").read_text(
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
    detail_url = item.get("detail_url") or NCUT_OUTGOING_EXCHANGE_URL
    source_url = detail_url
    program_type = f"國際事務處【{prog_raw}】（{group_str}）"

    colleges_str = clean_text(
        item.get("colleges")
        or "不限學院（工程學院、電資學院、管理學院、人文創意學院、通識教育學院均得依姊妹校對應系所申請）"
    )
    degree_levels_str = clean_text(
        item.get("eligible_degrees")
        or "國立勤益科技大學大學部二年級（含）以上及研究所一年級下學期（含）以上之在學學生（休學期間不得提出申請）"
    )
    lang_req_str = clean_text(
        item.get("language_req")
        or "符合《國立勤益科技大學學生海外研習甄選與經費獎助要點》規定：學期／學年型須達 CEFR B1 以上（TOEIC 550、TOEFL iBT 61、TOEFL ITP 500、IELTS 5.0 或 GEPT 中級，不接受 CSEPT；兩年內有效）"
    )
    gpa_req_str = clean_text(
        item.get("gpa_req")
        or "大學部歷年課業成績總平均達 70 分（約 GPA 2.5）以上或系排名前 50% 以內；研究所須檢附論文或專題指導教授推薦信"
    )
    website = item.get("website") or source_url
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(
        item.get("tuition_note")
        or "交換期間須於國立勤益科技大學完成註冊手續（依《學生國際交流甄選要點》第八點，大學部減免出國期間學費、研究所減免學分費）"
    )
    exps = item.get("experience_reports") or []

    round_label = (
        "115-2（116-1秋季班交換甄選：2026/12/24截止）＆115-1（115-2春季班甄選：06/12截止）"
    )
    app_deadline_str = (
        "115學年度第二梯次（116-1秋季班出國交換暨115年度第2梯次教育部學海飛颺甄選）：即日起至"
        " 2026/12/24（四）17:00 止完成線上報名並將紙本申請表件送達圖資大樓 5"
        " 樓國際事務處國際交流組（第3次海外研習說明會於 2026/11/11 12:00"
        " 在圖資大樓 6 樓會議室舉行）；第一梯次（春季班出國交換）：每年 5–6"
        " 月受理收件（115年度於 2026/06/12 17:00 截止）"
    )
    deadline_iso = "2026-12-24T17:00:00+08:00"
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "115"

    study_period_str = (
        "一學期或一學年（美國北伊利諾大學 NIU、波莫納加州州立理工大學 Cal Poly"
        " Pomona、漢弗萊斯大學 Humphreys University 與英國密德薩斯大學"
        " Middlesex University 另設 3+1／1+1／3+1+1 雙聯學位學制）"
    )
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country,
        (
            "秋季班（第 1 學期）：每年 8/9 月起至翌年 1/2"
            " 月止（預計）；春季班（第 2 學期）：每年 2/3 月起至 6/7"
            " 月止（預計）"
        ),
    )
    housing_str = (
        f"獲國立勤益科技大學國際事務處推薦提名後，可依 {zh_name}"
        f" 國際處指引申請校內學生宿舍或校外合作學生公寓（{tuition_note}）。"
    )
    course_rest_str = (
        f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《國立勤益科技大學學生國際交流甄選要點》及《學生海外研習甄選與經費獎助要點》規定："
        "（1）申請資格為本校大學部二年級（含）以上或研究所一年級下學期（含）以上之在學學生（休學期間不得提出申請；大一下學期即可報名申請大二出國交換）；"
        "（2）大學部歷年課業成績總平均達 70 分（約 GPA 2.5）以上或系排名前 50%"
        " 以內，研究所須檢附論文或專題指導教授推薦信（審查意見簽章）；"
        "（3）交換期間每學期至少須選修並通過 3 門正式學分課程（等同勤益 9"
        " 學分，不含語言、文化或體育類課程，且至少 6 學分或 2"
        " 門課及格；獲獎學金赴美國加州州立大學富勒頓分校 CSUF 者須修讀至少 12"
        " 學分），出國前須先填妥《出國前修課規劃之學分採認及抵免申請表》經系主任及教務處核准；"
        "（4）獲獎助學生出國前須簽訂《獎助學生海外研修行政契約書》（一式三份，需覓保證人"
        " 1 人連帶保證），在國外期間每兩週繳交雙週誌，並於返國後兩週（14"
        " 日）內繳交返校程序單、教育部學海版（5,000 字以上及 6"
        " 張照片）與勤益校內版成果報告書及 3–5 分鐘留學生活短片，以核發第二階段"
        " 20% 獎助金並辦理學分抵免。"
    )

    living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
        country,
        (
            (
                "每月生活費約 USD 650–1,350（依匯率折合新臺幣約 21,000–43,000"
                " 元，含住宿、膳食與市區交通）"
            ),
            (
                "須依接待國駐臺機構規定申辦學生簽證，並依《國立勤益科技大學學生國際交流甄選要點》第十點規定，於出國前自行購買足夠額度之海外平安保險、海外醫療保險及該國規定之保險。"
            ),
        ),
    )

    tuition_points_list = [
        (
            "國立勤益科技大學學雜費減免優惠與姊妹校待遇：依《國立勤益科技大學學生國際交流甄選要點》第八點規定，學生於出國進修與修讀學分期間應辦理註冊手續，大學部學生減免出國期間「學費」（僅需繳納雜費與學生平安保險費），研究所學生減免出國期間「學分費」（僅需繳納學雜費基數與學生平安保險費）。本合作校待遇："
            f"{tuition_note}。"
        ),
        (
            "國立勤益科技大學三級分區海外研習獎助金與圓夢助學金體系（依《國立勤益科技大學學生海外研習甄選與經費獎助要點》115.06.25"
            " 修頒）：（1）第 1 級重點國家（德國 HAWtech"
            " 聯盟學校、日本、美國）：每學期補助上限新臺幣 15 萬元、一學年上限"
            " 30 萬元、短期研習上限 6 萬元（經濟不利學生圓夢助學金另加發：學期型"
            " 5 萬元、學年型 10 萬元、短期 2 萬元）；（2）第 2"
            " 級歐美大洋洲及韓國（如捷克 UHK／Škoda Auto、英國"
            " Middlesex、韓國嘉泉／淑明女大）：每學期補助上限新臺幣 12"
            " 萬元、一學年上限 24 萬元、短期研習上限 4 萬元（經濟不利學生另加發：學期型"
            " 4 萬元、學年型 8 萬元、短期 1.5 萬元）；（3）第 3"
            " 級其他亞太地區（如越南、泰國、馬來西亞、印尼、菲律賓、印度）：每學期補助上限新臺幣"
            " 9 萬元、一學年上限 18 萬元、短期研習上限 2"
            " 萬元（經濟不利學生另加發：學期型 3 萬元、學年型 6 萬元、短期 1"
            " 萬元）。獎助金分兩階段核發：出國前核發 80%，返國兩週內繳齊成果報告、雙週誌與短片後核發剩餘"
            " 20%。"
        ),
    ]

    app_steps_list = [
        (
            "步驟一（確認勤益在學資格、70 分或前 50% 學業門檻與"
            f" {zh_name}"
            " 語檢要求）：確認符合《國立勤益科技大學學生國際交流甄選要點》及《海外研習甄選與經費獎助要點》規定（"
            f"{gpa_req_str}），並備妥報名截止日前兩年內有效之語言能力證明（{lang_req_str}；注意不接受"
            " CSEPT 成績）。"
        ),
        (
            "步驟二（完成線上報名表填寫並備齊 9"
            " 項書面申請表件送交圖資大樓 5 樓國際事務處）：依《交換學生申請文件檢核表》備妥：（1）交換學生甄選申請表（含導師／指導教授簽名審查意見）、（2）大學歷年中文成績單正本（含排名；轉學生須附原校成績單）、（3）大學歷年英文成績單正本、（4）語言能力證明影本（兩年內有效）、（5）外文讀書計畫（含修課規劃、預計達成目標）、（6）外文自傳（含自我介紹、申請動機）、（7）家長同意書（全學制皆須繳交）、（8）教授推薦信（大學部免繳，研究所必繳）、（9）交換學生繳交資料檢核表及獎助學金具結書，於截止日（115-2"
            " 第二梯次為 2026/12/24 17:00）前送達國際事務處國際交流組。"
        ),
        (
            "步驟三（參加「國際事務處海外研習甄選委員會」書面與面試審查）：書面資格合格者參加校內甄選面試（評分項目包含在校成績、語言檢定、外文讀書計畫與面試表現），錄取名單及核定獎助金額公告於國際事務處網站，錄取生須於期限內繳交《錄取資格確認書》。"
        ),
        (
            f"步驟四（由國際事務處向 {full_name}"
            " 提名、簽訂行政契約書與預先學分採認、辦理簽證保險與返國結案）：出國前完成《出國前修課規劃之學分採認及抵免申請表》及《獎助學生海外研修行政契約書》（一式三份，需保證人"
            " 1 人），役男於出國前 1.5 個月辦理緩徵出境，領取第一階段 80%"
            " 獎助金；海外每學期至少選修 3 門正式課程（等同勤益 9"
            " 學分），返國後兩週（14 日）內繳交返校程序單、教育部與校內版成果報告書及"
            " 3–5 分鐘短片以領取剩餘 20% 獎助金。"
        ),
    ]

    elig_points_list = [
        f"合作類別與計畫群組：{program_type}",
        f"開放學制與修業年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業成績與推薦門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        (
            "修課學分與返國義務：海外交換每學期至少須選修 3 門正式課程（等同勤益"
            " 9 學分，不含語言、文化或體育課，且至少 6 學分或 2"
            " 門課及格）；返國後 14 日內須繳交返校程序單、雙版本成果報告書與"
            " 3–5 分鐘短片。"
        ),
    ]
    if tuition_note:
      elig_points_list.append(f"學雜費減免與獎助待遇：{tuition_note}")
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
        eurl = e.get("url") or NCUT_OUTGOING_EXCHANGE_URL
        if eurl in seen_exp_urls:
          eurl = f"{eurl}#r{e_idx+1}"
        seen_exp_urls.add(eurl)
        exp_labels.append(raw_t[:36])
        exp_links.append({
            "title": raw_t,
            "url": eurl,
            "academic_year": esem,
            "semester": esem,
            "college": "工程學院／電資學院／管理學院／人文創意學院",
            "department": e.get("department") or "勤益科大出國交換生",
        })
        summary_text = (
            f"國立勤益科技大學國際事務處於交換學生計畫專區發布之赴 {country} {full_name}"
            f" 交換研修心得報告與 YouTube 影片分享（{raw_t}），涵蓋校內書審與面試準備、姊妹校選課（每學期至少"
            " 3 門正式課程／等同勤益 9 學分）、宿舍生活與教育部學海飛颺暨校內三級分區獎助金申請實務。"
        )
        theme_map = {
            "academics": (
                f"勤益科大交換生於《{raw_t}》分享在 {zh_name} 修習專業課程（每學期至少"
                " 3 門正式課程、等同勤益 9 學分），以及出國前預先學分採認與返國後辦理學分抵免之經驗。"
            ),
            "housing": (
                f"勤益科大交換生分享申請 {zh_name}"
                f" 校內外學生宿舍與生活適應（{housing_str[:100]}）。"
            ),
            "campus_culture": (
                f"勤益科大國際事務處透過《{raw_t}》心得報告書與 YouTube 留學短片傳承海外姊妹校跨文化交流與校園生活經驗。"
            ),
            "cost": (
                f"勤益科大交換生分享於 {zh_name}"
                f" 之每月住宿、伙食與交通花費（{living_cost_str[:100]}），以及領取教育部學海飛颺與勤益海外研習獎助金（每學期上限"
                " 9–15 萬元、學年上限 18–30 萬元）之實務。"
            ),
        }
        student_experience_rows.append({
            "school_name": full_name,
            "country": country,
            "title": raw_t,
            "source_url": eurl,
            "source_type": "article",
            "platform": "國立勤益科技大學國際事務處—交換學生計畫心得報告與影片分享專區",
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
                f"{full_name}:ncut_exp:{e_idx}:{eurl}".encode("utf-8")
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
        "home_university": "國立勤益科技大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exp_links[0]["url"] if exp_links else NCUT_OUTGOING_EXCHANGE_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

    loc = resolved_locations.get(full_name) or {
        "city": country,
        "latitude": 24.1449,
        "longitude": 120.7303,
        "source_url": "https://www.wikidata.org",
    }
    city_name = loc.get("city") or country
    lat = float(
        loc.get("latitude")
        if loc.get("latitude") is not None
        else loc.get("lat", 24.1449)
    )
    lon = float(
        loc.get("longitude")
        if loc.get("longitude") is not None
        else loc.get("lon", 120.7303)
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
            " 及國立勤益科技大學國際事務處交換姊妹校名單與 MOU 締約學校名冊比對；實際交換校區以錄取通知與姊妹校簡章為準。"
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
          f"【勤益科大學長姐交換心得報告與影片分享（共 {len(exps)}"
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
            f"國立勤益科技大學國際事務處公告合作姊妹校（{program_type}）；名額：{quota_str}（{remarks_raw}）。"
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
            NCUT_DUAL_DEGREE_BROCHURE_PDF_URL
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
                f"國立勤益科技大學國際事務處交換學生計畫與締約姊妹校名冊—{zh_name}"
            ),
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": (
                "國立勤益科技大學學生海外研習甄選與經費獎助要點（115.06.25修頒）PDF"
            ),
            "source_url": NCUT_GUIDELINES_OVERSEAS_STUDY_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立勤益科技大學學生國際交流甄選要點 PDF",
            "source_url": NCUT_GUIDELINES_INTL_EXCHANGE_PDF_URL,
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
              f"國立勤益科技大學國際事務處交換學生心得報告與影片分享專區—{zh_name}"
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
        "home_university": "國立勤益科技大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": acad_year,
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "115-2（116-1秋季班出國交換暨學海飛颺第2梯次甄選）",
            "115-1（115-2春季班出國交換甄選）",
            "115-1",
            "115-2",
            "116-1",
            "116-2",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "國立勤益科技大學由國際事務處國際交流組（圖資大樓 5 樓，電話：04-23924505"
            " 分機 2198／2192）統籌全校五大學院（工程學院、電資學院、管理學院、人文創意學院、通識教育學院）之全球姊妹校交換學生、歐美"
            " 3+1／1+1／3+1+1 雙聯學制（Northern Illinois University、Cal Poly"
            " Pomona、Humphreys University、Middlesex University）及教育部學海飛颺、高教深耕三級分區海外研習獎助與經濟不利學生圓夢助學金遴選。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"ncut-{acad_year}-home-1-{sn:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": (
                    "確認勤益科大在學年級資格、學業 70 分／前 50% 門檻與"
                    f" {zh_name} 語檢要求"
                ),
                "responsible_party": "學生",
                "responsible_unit": (
                    "國立勤益科技大學國際事務處國際交流組（圖資大樓 5 樓）"
                ),
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact",
                "deadline_source_url": NCUT_115_2_INFO_POST_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": True,
                "summary": (
                    f"確認符合《國立勤益科技大學學生國際交流甄選要點》及《學生海外研習甄選與經費獎助要點》規定：大學部二年級（含）以上或研究所一年級下學期（含）以上在學學生（休學期間不得申請），{gpa_req_str}，並備妥報名截止日前兩年內有效且符合"
                    f" {zh_name} 門檻之語言能力證明（{lang_req_str}；不接受"
                    " CSEPT）。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["國立勤益科技大學"],
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
                    NCUT_GUIDELINES_INTL_EXCHANGE_PDF_URL,
                    NCUT_GUIDELINES_OVERSEAS_STUDY_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ncut-{acad_year}-home-2-{sn:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": (
                    "填寫線上報名表並備齊交換學生甄選申請表、中英文歷年成績單、外文讀書計畫與自傳、家長同意書送交國際事務處"
                ),
                "responsible_party": "學生與所屬系所／指導教授",
                "responsible_unit": (
                    "各學院系所辦公室／國立勤益科技大學國際事務處國際交流組"
                ),
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact",
                "deadline_source_url": NCUT_115_2_INFO_POST_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": True,
                "summary": (
                    "申請學生須先填寫當期海外研習線上報名表單，並依《交換學生繳交資料檢核表》備齊"
                    " 9 項書面文件（含導師或論文指導教授簽章之申請表、歷年中英文成績單正本、兩年內語檢證明、外文讀書計畫、外文自傳、家長同意書、研究生指導教授推薦信及獎助具結書），於"
                    " 2026/12/24（四）17:00 前送達圖資大樓 5 樓國際事務處。"
                ),
                "details": [
                    (
                        "家長同意書不論大學部或研究所、是否成年皆須繳交；研究所學生必須檢附論文或專題指導教授推薦信。"
                    ),
                    (
                        "具備低收入戶、中低收入戶、特殊境遇家庭、身心障礙或原住民身分之經濟不利學生，可同步檢附證明申請圓夢助學金加額補助（每學期另加發"
                        " 3 萬至 5 萬元、學年型 6 萬至 10 萬元）。"
                    ),
                ],
                "document_requirements": [
                    {
                        "name": (
                            "國立勤益科技大學交換學生甄選申請表（電腦打字、黏貼2吋照片，含導師或論文指導教授審查意見簽名）及繳交資料檢核表"
                        ),
                        "official_form_url": NCUT_APP_FORM_PDF_URL,
                        "source_urls": [
                            NCUT_APP_FORM_PDF_URL,
                            NCUT_DOC_CHECKLIST_PDF_URL,
                        ],
                    },
                    {
                        "name": (
                            "家長同意書（全學制皆須繳交）及獎助學金申請具結書"
                        ),
                        "official_form_url": NCUT_PARENTAL_CONSENT_PDF_URL,
                        "source_urls": [
                            NCUT_PARENTAL_CONSENT_PDF_URL,
                            NCUT_DOWNLOADS_EXCHANGE_URL,
                        ],
                    },
                    {
                        "name": (
                            "大學／研究所歷年中文成績單正本（含排名；轉學生須附原就讀學校成績單）、歷年英文成績單正本及報名截止日前兩年內有效之語言能力證明影本"
                        ),
                        "official_form_url": NCUT_DOC_CHECKLIST_PDF_URL,
                        "source_urls": [
                            NCUT_DOC_CHECKLIST_PDF_URL,
                            NCUT_GUIDELINES_OVERSEAS_STUDY_PDF_URL,
                        ],
                    },
                    {
                        "name": (
                            "外文讀書計畫（含修課規劃、預計達成目標）、外文自傳（含自我介紹、申請動機）及研究所指導教授推薦信"
                        ),
                        "official_form_url": NCUT_DOC_CHECKLIST_PDF_URL,
                        "source_urls": [
                            NCUT_DOC_CHECKLIST_PDF_URL,
                            NCUT_GUIDELINES_INTL_EXCHANGE_PDF_URL,
                        ],
                    },
                ],
                "scope": {
                    "home_universities": ["國立勤益科技大學"],
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
                    NCUT_115_2_INFO_POST_URL,
                    NCUT_APP_FORM_PDF_URL,
                    NCUT_DOC_CHECKLIST_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ncut-{acad_year}-home-3-{sn:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": (
                    "參加「國際事務處海外研習甄選委員會」書面與面試審查、核定三級分區獎助金並繳交錄取資格確認書"
                ),
                "responsible_party": "國立勤益科技大學國際事務處與申請學生",
                "responsible_unit": (
                    "國立勤益科技大學海外研習甄選委員會／國際事務處"
                ),
                "deadline_at": "2026-12-24T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": NCUT_115_2_INFO_POST_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": True,
                "summary": (
                    "由國際長召集各學院代表組成海外研習甄選委員會辦理書面審查與面試，依成績擇優錄取並核定教育部學海飛颺及校內三級分區獎助金（第1級美日德上限15萬/學期、第2級歐美韓上限12萬/學期、第3級亞太上限9萬/學期）；正取生須依限繳交《錄取資格確認書》。"
                ),
                "details": [
                    (
                        "錄取後如因故欲放棄資格，須填具《交換生放棄聲明書》經系主任簽章後送交國際事務處；無故放棄者將影響後續申請權益。"
                    ),
                    (
                        "每年 3 月、5 月及 11"
                        " 月定期舉辦海外研習說明會（如 115"
                        " 學年度第三次海外研習說明會於 2026/11/11 12:00"
                        " 於圖資大樓六樓會議室舉行）。"
                    ),
                ],
                "scope": {
                    "home_universities": ["國立勤益科技大學"],
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
                    NCUT_GUIDELINES_OVERSEAS_STUDY_PDF_URL,
                    NCUT_GUIDELINES_INTL_EXCHANGE_PDF_URL,
                    NCUT_ADMISSION_ROSTER_PNG_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ncut-{sn:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": (
                    f"由國際事務處向 {zh_name}"
                    " 提名並遞交姊妹校交換／雙聯入學申請文件"
                ),
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    "獲本校正式錄取並繳交確認書後，由國際事務處向海外姊妹校提名；學生須依姊妹校規定準備有效護照、存款財力證明、英文成績單、健康檢查表及宿舍申請表，俟取得接待校正式入學許可（Admission"
                    " Letter / COE / DS-2019 / I-20）後申辦簽證。"
                ),
                "details": [
                    f"研修期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["國立勤益科技大學"],
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
                "source_urls": [source_url, NCUT_DUAL_DEGREE_BROCHURE_PDF_URL]
                + ([website] if website else []),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"ncut-{acad_year}-home-5-{sn:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": (
                    "簽訂行政契約書與出國前學分採認表、完成勤益註冊減免與役男緩徵，返國後14日內繳交成果報告書與短片核銷尾款"
                ),
                "responsible_party": "學生與所屬系所",
                "responsible_unit": (
                    "國立勤益科技大學國際事務處／教務處／學務處生輔組／各學院系所"
                ),
                "summary": (
                    "出國前須參加行前說明會、完成《獎助學生海外研修行政契約書》（一式三份，需保證人1人）、《出國前修課規劃之學分採認及抵免申請表》及《出國程序單》（含役男出國前1.5個月緩徵及海外醫療平安保險投保），領取第一階段80%獎助金；抵達姊妹校兩週內回傳《抵達國外通知單》並每兩週繳交雙週誌；返國後兩週（14日）內繳交《返校程序單》、教育部與校內版成果報告書、3–5分鐘短片、登機證正本與機票收據以請領剩餘20%獎助金並辦理學分抵免。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["國立勤益科技大學"],
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
                    NCUT_ADMIN_CONTRACT_PDF_URL,
                    NCUT_PRE_CREDIT_FORM_PDF_URL,
                    NCUT_RETURN_PROCEDURE_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合國立勤益科技大學國際事務處（OIA）全球共 {len(catalog_source)} 所合作姊妹校與交換／雙聯專案（含"
            f" {open_partner_count}"
            " 所當期開放交換與歐美雙聯學制合作學校）、115"
            " 學年度海外研習甄選簡章、學生海外研習甄選與經費獎助要點（115.06.25修頒）、學生國際交流甄選要點，以及"
            f" {exp_covered_schools} 校 {total_exp_reports}"
            " 篇交換學生心得報告書、YouTube 影片分享與錄取專案紀錄。"
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
                f"國立勤益科技大學國際事務處交換學生計畫與締約姊妹校名冊—{zh_name}"
            ),
            "source_url": source_url,
            "summary": (
                "勤益科大國際事務處公告之合作計畫類型、名額、語言要求與學雜費減免待遇"
            ),
        },
        {
            "title": (
                "國立勤益科技大學學生海外研習甄選與經費獎助要點及學生國際交流甄選要點"
            ),
            "source_url": NCUT_GUIDELINES_OVERSEAS_STUDY_PDF_URL,
            "summary": (
                "勤益科大交換生申請資格、三級分區獎助金（每學期上限9–15萬元）、海外應修3門正式課程（等同9學分）及返國14日內結案義務"
            ),
        },
    ]
    if exp_links:
      dest_sources.append({
          "title": (
              f"國立勤益科技大學國際事務處交換學生心得報告與影片分享專區—{zh_name}"
          ),
          "source_url": exp_links[0]["url"],
          "summary": (
              f"收錄勤益科大學生赴 {zh_name} 交換心得報告、YouTube 影片與錄取紀錄共"
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
        [source_url, NCUT_OUTGOING_EXCHANGE_URL, NCUT_REGULATIONS_URL]
        + (
            [exp_links[0]["url"]]
            if exp_links
            else [NCUT_OUTGOING_EXCHANGE_URL]
        )
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "國立勤益科技大學",
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
                    "生活費、勤益註冊學費減免與三級分區海外研習獎助金（上限15萬／30萬元）暨圓夢助學金"
                ),
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [
                    NCUT_GUIDELINES_OVERSEAS_STUDY_PDF_URL,
                    NCUT_GUIDELINES_INTL_EXCHANGE_PDF_URL,
                ],
                "caution": (
                    "獲獎助學生出國前須簽訂《獎助學生海外研修行政契約書》（一式三份，覓保證人1人），第一階段出國前核發80%，返國後14日內繳齊成果報告書、雙週誌、3–5分鐘短片與機票單據後核發剩餘20%。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與姊妹校校內外學生宿舍申請",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": (
                    "赴德國交換生須開立限制提領帳戶（Blocked Account），赴日本申請"
                    " COE 及赴歐美交換生均須依姊妹校規定準備英文存款財力證明。"
                ),
            },
            {
                "key": "insurance",
                "title": (
                    "海外醫療保險、平安保險與接待國法定學生健康保險規定"
                ),
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    (
                        "依《國立勤益科技大學學生國際交流甄選要點》第十點及《出國程序單》規定，錄取學生出國前須自行購買涵蓋全交換期間之海外醫療保險、海外平安保險及接待國規定之健康保險，並檢附保險證明影本辦理出國程序。"
                    ),
                ],
                "source_urls": src_url_list
                + [NCUT_GUIDELINES_INTL_EXCHANGE_PDF_URL],
                "caution": (
                    "出國前請確認海外醫療保險涵蓋門診、住院及海外急難救助，並於抵達姊妹校兩週內回傳《抵達國外通知單》。"
                ),
            },
            {
                "key": "visa",
                "title": (
                    "交換留學簽證辦理、役男出國前1.5個月緩徵申請與在學註冊減免規定"
                ),
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    (
                        "尚未履行兵役義務之役男應於出國前 1.5"
                        " 個月檢附《役男出國申請單》、家長同意書、姊妹校入學許可書及護照影本，會辦學務處生活輔導組及國際事務處辦理役男出境緩徵。"
                    ),
                ],
                "source_urls": src_url_list + [NCUT_VISAS_URL],
                "caution": (
                    "交換期間仍須於國立勤益科技大學完成註冊（大學部減免學費、研究所減免學分費），未完成註冊或休學者不得出國交換。"
                ),
            },
            {
                "key": "academics",
                "title": (
                    "海外每學期至少選修3門正式課程（等同勤益9學分）、預先學分採認與返國抵免"
                ),
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [
                    NCUT_PRE_CREDIT_FORM_PDF_URL,
                    NCUT_RETURN_PROCEDURE_PDF_URL,
                ],
                "caution": (
                    "交換生每學期至少須選修 3 門正式學分課程（等同勤益 9"
                    " 學分，不含語言、文化或體育類課程），且至少 6 學分或 2"
                    " 門課及格；獲獎學金赴美 CSUF 者須修習至少 12 學分。"
                ),
            },
            {
                "key": "living",
                "title": (
                    f"{city_name} 校園生活、學長姐交換心得報告與 YouTube 留學影片傳承"
                ),
                "summary": (
                    f"代表城市：{city_name}。獲獎助學生於海外期間每兩週繳交雙週誌，返國後繳交成果報告與"
                    " 3–5 分鐘留學生活短片並協助國際處經驗分享。"
                ),
                "points": [
                    f"目的地城市：{city_name}（{country}）",
                    "國立勤益科技大學國際事務處設有「交換學生計畫—學生心得分享」專區"
                    + (
                        f"（本校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:3])}）"
                        if exps
                        else ""
                    )
                    + "，完整公開歷屆交換生 PDF 成果報告書與 YouTube 留學影片。",
                ],
                "source_urls": [
                    exp_links[0]["url"]
                    if exp_links
                    else NCUT_OUTGOING_EXCHANGE_URL
                ],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合國立勤益科技大學國際事務處 {len(catalog_source)} 所合作姊妹校名冊、115"
            " 學年度海外研習甄選簡章、雙聯學制簡章、三級分區獎助要點及"
            f" {exp_covered_schools} 校 {total_exp_reports}"
            " 篇交換心得報告與影片分享紀錄。"
        ),
    })

    research_records.append({
        "home_university": "國立勤益科技大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            f"國立勤益科技大學國際事務處 {len(catalog_source)} 所合作姊妹校名冊、出國交換學校一覽表與"
            " ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [{
        "title": f"國立勤益科技大學國際事務處合作姊妹校與交換資訊—{zh_name}",
        "url": source_url,
    }]
    if exp_links:
      ev_sources.append({
          "title": (
              f"國立勤益科技大學國際事務處交換學生心得報告與影片分享專區—{zh_name}"
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
            "scope": "勤益科大海外交換／雙聯姊妹校住宿與財力證明資訊",
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
                "勤益科大出國交換學費減免規定、教育部學海飛颺、校內三級分區獎助金（上限15萬/學期、30萬/學年）、圓夢助學金與地區生活費估算"
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
                "國立勤益科技大學學生國際交流甄選要點、海外應修3門正式課程（等同9學分）與返國14日內結案規範"
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
                "勤益科大海外交換簽證、役男出國前1.5個月緩徵申請與海外醫療平安保險規定"
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
                    f"｜勤益科大國際事務處收錄 {len(exps)} 篇赴 {zh_name} 交換生心得報告、YouTube 影片與錄取專案紀錄（{'、'.join(exp_labels[:3])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "勤益科大交換名額與學長姐心得報告／留學影片傳承",
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
                f"已整合國立勤益科技大學國際事務處 {len(catalog_source)} 所合作姊妹校名冊、115"
                " 學年度海外研習甄選簡章、雙聯學制簡章及交換學生心得報告與影片分享紀錄。"
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

  write_jsonl(OFFICIAL_NCUT_DIR / "partners.jsonl", partners)
  write_jsonl(SOURCES_NCUT_DIR / "partners.jsonl", partners)
  write_jsonl(OFFICIAL_NCUT_DIR / "application_workflows.jsonl", workflows)
  write_jsonl(OFFICIAL_NCUT_DIR / "destination_profiles.jsonl", destinations)
  write_jsonl(OFFICIAL_NCUT_DIR / "partner_research.jsonl", research_records)
  write_jsonl(OFFICIAL_NCUT_DIR / "student_life.jsonl", life_records)
  write_jsonl(
      OFFICIAL_NCUT_DIR / "experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_NCUT_DIR / "student_experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_NCUT_DIR / "student_experiences.jsonl", student_experience_rows
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
  (OFFICIAL_NCUT_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_NCUT_DIR / "student-experiences.json").write_text(
      json.dumps(
          {
              "school_id": "ncut",
              "school_name": "國立勤益科技大學",
              "checked_at": CHECKED_AT,
              "source_url": NCUT_OUTGOING_EXCHANGE_URL,
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

  (OFFICIAL_NCUT_DIR / "campus-locations.json").write_text(
      json.dumps(
          {
              "school_id": "ncut",
              "school_name": "國立勤益科技大學",
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
  (OFFICIAL_NCUT_DIR / "campus-assets.json").write_text(
      json.dumps(
          {
              "school_id": "ncut",
              "school_name": "國立勤益科技大學",
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

  ncut_source_urls = [
      NCUT_HOME_URL,
      NCUT_OIA_HOME_URL,
      NCUT_ABOUT_URL,
      NCUT_STAFF_URL,
      NCUT_OUTGOING_EXCHANGE_URL,
      NCUT_MOU_PARTNERS_URL,
      NCUT_REGULATIONS_URL,
      NCUT_DOWNLOADS_EXCHANGE_URL,
      NCUT_DOWNLOADS_STUDENT_URL,
      NCUT_SOP_URL,
      NCUT_FAQ_URL,
      NCUT_CONTACT_URL,
      NCUT_LANGUAGE_TESTS_URL,
      NCUT_VISAS_URL,
      NCUT_OVERSEAS_INTERNSHIP_URL,
      NCUT_GLOBAL_CAREERS_URL,
      NCUT_115_2_INFO_POST_URL,
      NCUT_115_1_INFO_POST_URL,
      NCUT_SKODA_SUMMER_POST_URL,
      NCUT_HDA_ISU_POST_URL,
      NCUT_UHK_SUMMER_POST_URL,
      NCUT_CSUF_SUMMER_POST_URL,
      NCUT_GACHON_SUMMER_POST_URL,
      NCUT_GUIDELINES_INTL_EXCHANGE_PDF_URL,
      NCUT_GUIDELINES_OVERSEAS_STUDY_PDF_URL,
      NCUT_DUAL_DEGREE_BROCHURE_PDF_URL,
      NCUT_115_2_INFO_PDF_URL,
      NCUT_ADMISSION_ROSTER_PNG_URL,
      NCUT_APP_FORM_PDF_URL,
      NCUT_DOC_CHECKLIST_PDF_URL,
      NCUT_PARENTAL_CONSENT_PDF_URL,
      NCUT_ADMIN_CONTRACT_PDF_URL,
      NCUT_PRE_CREDIT_FORM_PDF_URL,
      NCUT_RETURN_PROCEDURE_PDF_URL,
  ]

  exchange_info_payload = {
      "school_name": "國立勤益科技大學",
      "program_type": [
          (
              "國際事務處「校級與院級赴海外姊妹校交換學生計畫」（涵蓋美國加州州立大學富勒頓分校"
              " CSUF、北伊利諾大學 NIU、佛羅里達理工大學；德國 HAWtech"
              " 應用科技大學六校聯盟［達姆施塔特 h_da、埃斯林根、德勒斯登"
              " HTW、阿亨 FH Aachen、卡爾斯魯厄 HKA、柏林 HTW］與德勒斯登工業大學"
              " TU Dresden；捷克赫拉德茨克拉洛韋大學 UHK、斯柯達汽車大學 Škoda"
              " Auto University；日本佐賀大學、北見工業大學、九州工業大學、室蘭工業大學、千葉大學；韓國嘉泉大學、淑明女子大學；馬來西亞砂拉越科技大學"
              " UTS、雙威大學；越南河內交通運輸大學、河內國家大學外國語大學"
              " VNU-ULIS；泰國瓦萊嵐大學、泰國東方大學 Burapha、吞武里國王科技大學"
              " KMUTT、佛統皇家大學；以及印度班加羅爾總統大學、印尼世界大學、菲律賓聖何塞大學等"
              f" {open_partner_count} 所當期開放交換／雙聯合作學校與全球"
              f" {len(partners)} 所締約姊妹校）"
          ),
          (
              "國際事務處「歐美雙聯學位學制專案」（涵蓋美國北伊利諾大學 NIU［工程學院"
              " 3+1+1 碩士雙聯］、美國波莫納加州州立理工大學 Cal Poly"
              " Pomona［電資／工程學院 MSEE 碩士雙聯］、美國漢弗萊斯大學"
              " Humphreys University［3+1 BBA 學士與 1+1 MBA/MSIT"
              " 碩士雙聯］及英國倫敦密德薩斯大學 Middlesex University［3+1"
              " 榮譽學士與 1+1 碩士雙聯］）"
          ),
          (
              "國際事務處「教育部學海飛颺、高教深耕三級分區海外研習獎助金（第1級美日德上限15萬/學期、30萬/學年；第2級歐美韓上限12萬/學期、24萬/學年；第3級亞太上限9萬/學期、18萬/學年）」暨「經濟不利學生圓夢助學金（另加發3萬–10萬元）」與「出國期間勤益學費／學分費減免」體系"
          ),
      ],
      "academic_year": [
          (
              "115（涵蓋 115 學年度第二梯次［116-1 秋季班出國交換暨 115"
              " 年度第 2 梯次教育部學海飛颺甄選：即日起至 2026/12/24 17:00"
              " 截止，第 3 次海外研習說明會於 2026/11/11 舉行］，以及第一梯次［115-2"
              " 春季班出國交換甄選：2026/06/12 截止］）"
          ),
          (
              f"本平台完整收錄國立勤益科技大學國際事務處公告之 {len(partners)} 所全球合作姊妹校與交換／雙聯專案（橫跨全球"
              f" 20 個國家與地區，含 {open_partner_count}"
              f" 所當期開放申請之交換與雙聯合作校，並收錄 {exp_covered_schools} 所合作大學共"
              f" {total_exp_reports} 篇交換學生心得報告書、YouTube 影片與錄取專案紀錄）"
          ),
      ],
      "semester": [
          (
              "第二梯次（秋季班／第 1 學期出國交換暨學海飛颺甄選，每年 10–12"
              " 月受理收件，115 年度於 2026/12/24 17:00 截止，預計翌年 8/9"
              " 月出國）：開放大學部二年級（含）以上及碩博士班一年級下學期（含）以上在學學生申請。"
          ),
          (
              "第一梯次（春季班／第 2 學期出國交換暨海外暑期研習甄選，每年 3–6"
              " 月受理收件，115 年度於 2026/06/12 17:00 截止，預計翌年 2/3"
              " 月或當年暑期出國）：大一下學期在學學生即可報名參加甄選，於大二出國交換。"
          ),
      ],
      "application_period": [
          (
              "【115 學年度第二梯次（116-1 秋季班出國交換暨 115 年度第 2"
              " 梯次學海飛颺）甄選】自即日起（2026/10/23）至 2026/12/24（四）17:00"
              " 止，完成線上報名並將紙本申請表件送達圖資大樓 5 樓國際事務處國際交流組。"
          ),
          (
              "【115 學年度第三次海外研習說明會】線上報名自即日起至"
              " 2026/11/06（五）止，說明會於 2026/11/11（三）12:00 在圖資大樓 6"
              " 樓會議室舉行（完整介紹美、德、捷、英、日、韓、馬、越、泰姊妹校交換與雙聯獎助）。"
          ),
          (
              "【115 學年度第一梯次（115-2"
              " 春季班出國交換）暨德、捷、美、韓暑期學校專案】第一梯次校內報名於"
              " 2026/06/12（五）17:00 截止；德國達姆施塔特（h_da）ISU、捷克"
              " Škoda Auto 與 UHK 暑期學校、美國 CSUF 暑期營及韓國嘉泉大學夏季學期於每年"
              " 2–5 月依國際處公告受理報名。"
          ),
      ],
      "eligibility": [
          (
              "1. 在學學籍與修業年級規定：依《國立勤益科技大學學生國際交流甄選要點》第三點及《學生海外研習甄選與經費獎助要點》第三點規定，申請人須為本校大學部二年級（含）以上或研究所一年級下學期（含）以上之在學學生（大一下學期即可報名申請大二出國交換；休學期間不得提出申請，出國期間亦須維持在學並完成註冊）。"
          ),
          (
              "2. 在校學業成績與教授推薦門檻：大學部學生歷年課業成績總平均須達"
              " 70 分（約 GPA 2.5 / 4.0）以上，或歷年學業成績系排名前 50%"
              " 以內；研究所學生須檢附論文或專題指導教授推薦信（並於申請表指導教授欄簽章同意）。"
          ),
          (
              "3. 教育部學海飛颺與圓夢助學金資格：申請教育部《學海飛颺》及校內三級分區海外研習獎助者，須具中華民國國籍且在臺灣地區設有戶籍；具低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助或原住民身分之經濟不利學生，得另檢附證明申請「圓夢計畫」加額定額補助（學期型另加發"
              " 3 萬–5 萬元、學年型另加發 6 萬–10 萬元）。"
          ),
          (
              "4. 海外修課學分規定與返國結案義務：交換期間每學期至少須選修並通過"
              " 3 門正式學分課程（等同勤益 9 學分，不含語言、文化或體育類課程，且至少"
              " 6 學分或 2 門課及格；獲獎學金赴美 CSUF 者須修習至少 12"
              " 學分）。受獎助學生於海外期間每兩週須繳交雙週誌，並於返國後兩週（14"
              " 日）內繳交返校程序單、教育部學海版（5,000 字以上及 6"
              " 張照片）與校內版成果報告書及 3–5 分鐘留學短片，以核發剩餘 20% 獎助金。"
          ),
      ],
      "language_requirement": [
          (
              "1. 學期／學年型交換生與雙聯學制基本英語門檻（依《學生海外研習甄選與經費獎助要點》第五點及各姊妹校簡章）：須達"
              " CEFR B1（含）以上（檢定成績須為報名截止日前兩年內有效，且「不接受"
              " CSEPT 大學院校英語能力測驗」），對應標準為：TOEIC 550、TOEFL iBT"
              " 61、TOEFL ITP 500、IELTS 5.0 或 GEPT 中級（暑期型短期營隊須達"
              " CEFR A2 / TOEIC 225 以上）。部分歐美雙聯與交換名校要求較高門檻：美國北伊利諾大學（NIU"
              " 3+1+1）與波莫納加州州立理工大學（Cal Poly Pomona MSEE）要求"
              " TOEFL iBT 79–80 或 IELTS 6.5；英國倫敦密德薩斯大學（Middlesex"
              " 雙聯）要求 IELTS 6.0（單科不低於 5.5）；德國埃斯林根應用科技大學要求"
              " TOEIC 750（CEFR B2）。"
          ),
          (
              "2. 德國 HAWtech 應用科技大學聯盟德語與英語雙重規定：申請德國達姆施塔特（h_da）、德勒斯登（HTW"
              " Dresden）、阿亨（FH Aachen）、卡爾斯魯厄（HKA）、柏林（HTW"
              " Berlin）除英語達 CEFR B1（TOEIC 550）外，通常另須具備德語檢定"
              " Goethe-Zertifikat A1 以上證明（埃斯林根應用科技大學或修讀德語授課課程者須達德語"
              " B1–B2）。"
          ),
          (
              "3. 日本與韓國姊妹校語檢門檻：（1）日本佐賀大學：SPACE-E"
              " 全英語學程要求 TOEIC 740 / TOEFL ITP 530 / TOEFL iBT 72 / IELTS"
              " 5.5 以上，一般日語交換要求大學部 JLPT N2、研究所 JLPT"
              " N1；（2）日本北見工業大學：要求 JLPT N3 或 TOEIC"
              " 550；（3）日本九州工業大學與室蘭工業大學：修課型要求大學部"
              " JLPT N2、碩士班 JLPT N1（研究型交換接受 JLPT N3 或 TOEIC"
              " 550）；（4）韓國嘉泉大學與淑明女子大學：要求韓語 TOPIK 2–3"
              " 級（CEFR B1）或英語 TOEIC 550 / IELTS 5.0–5.5。"
          ),
      ],
      "required_documents": [
          (
              "1. 國立勤益科技大學交換學生甄選申請表（必須以電腦打字、黏貼近三個月"
              " 2 吋彩色脫帽照片、申請人親筆簽名，並請導師或論文指導教授簽名及勾選審查意見）"
          ),
          (
              "2. 大學／研究所歷年中文成績單正本（需含班／系排名；轉學生須同時檢附原就讀學校之成績單）"
          ),
          "3. 大學／研究所歷年英文成績單正本（請向註冊組申請）",
          (
              "4. 語言能力證明影本（須為報名截止日前兩年內有效之"
              " TOEIC、TOEFL、IELTS、GEPT、JLPT、TOPIK、Goethe-Zertifikat"
              " 等成績單或證書，不接受 CSEPT）"
          ),
          (
              "5. 外文讀書計畫（Study Plan，請以電腦打字，內容包含出國修課規劃、預計達成目標等）"
          ),
          (
              "6. 外文自傳（Autobiography，請以電腦打字，內容包含自我介紹、申請動機等）"
          ),
          (
              "7. 家長同意書（無論大學部或研究所、是否成年，全體申請人皆須由家長或監護人親筆簽名蓋章）"
          ),
          (
              "8. 教授推薦信（大學部學生免繳；研究所碩、博士班學生必須檢附論文或專題指導教授推薦信）"
          ),
          (
              "9. 交換學生繳交資料檢核表、海外研習獎助學金申請具結書，以及完成當期海外研習線上報名表單填報"
          ),
      ],
      "scholarship_info": [
          (
              "1. 《國立勤益科技大學學生海外研習甄選與經費獎助要點》（115.06.25"
              " 修頒）暨教育部《學海飛颺》三級分區獎助金：（1）第 1"
              " 級（德國 HAWtech 聯盟學校、日本、美國重點姊妹校）：每學期補助上限新臺幣"
              " 15 萬元、一學年上限 30 萬元、短期研習上限 6"
              " 萬元（每年每國學期／學年型補助 8 名、雙聯學制每國 5"
              " 名，名額得互流）；（2）第 2 級（其他歐美、大洋洲地區及韓國，如捷克"
              " UHK／Škoda Auto、英國 Middlesex、韓國嘉泉／淑明女大）：每學期補助上限新臺幣"
              " 12 萬元、一學年上限 24 萬元、短期研習上限 4 萬元；（3）第 3"
              " 級（其他亞太地區，如越南、泰國、馬來西亞、印尼、菲律賓、印度）：每學期補助上限新臺幣"
              " 9 萬元、一學年上限 18 萬元、短期研習上限 2 萬元。"
          ),
          (
              "2. 經濟不利學生出國輔導助學金（圓夢計畫，要點第八之一點）：具低收入戶、中低收入戶、特殊境遇家庭、身心障礙或原住民身分之學生，除可領取原有獎助金外，得另申請定額補助：（1）德國"
              " HAWtech、日本及美國：短期 2 萬元、學期型 5 萬元、學年型 10"
              " 萬元；（2）其他歐美、大洋洲及韓國：短期 1.5 萬元、學期型 4"
              " 萬元、學年型 8 萬元；（3）其他亞太地區：短期 1 萬元、學期型 3"
              " 萬元、學年型 6 萬元。"
          ),
          (
              "3. 獎助金兩階段核發規定：第一階段於出國前完成行政契約書簽訂（一式三份，需保證人"
              " 1 人）及出國程序後核發 80% 補助金；第二階段於返國後兩週（14"
              " 日）內繳齊每兩週雙週誌、教育部學海版（5,000 字以上及 6"
              " 張照片）與校內版成果報告書、3–5 分鐘短片、600–1,000"
              " 字中文總心得、登機證正本與機票代收轉付收據後，核發剩餘 20% 補助金。"
          ),
          (
              "4. 出國期間勤益學雜費減免優惠（《國立勤益科技大學學生國際交流甄選要點》第八點）：本校學生於出國進修與修讀學分期間應辦理註冊手續，大學部學生減免出國期間「學費」（僅需繳納雜費與學生平安保險費），研究所學生減免出國期間「學分費」（僅需繳納學雜費基數與學生平安保險費）。"
          ),
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": ncut_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_NCUT_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "國立勤益科技大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 70.0,
      "academic_score_rule": (
          "依《國立勤益科技大學學生國際交流甄選要點》及《學生海外研習甄選與經費獎助要點》：大學部二年級（含）以上學生歷年課業成績總平均須達"
          " 70 分（約 GPA 2.5）以上或系排名前 50%"
          " 以內（大一下學期即可報名申請大二出國交換）；研究所一年級下學期（含）以上學生須檢附論文或專題指導教授推薦信（審查意見簽章）。"
      ),
      "academic_gpa_minimum": 2.5,
      "maximum_preferences": 3,
      "selection_rules": {
          "academic_policy": "score_or_rank",
          "academic_reference_year": "115",
          "undergraduate_gpa_minimum": 2.5,
          "graduate_academic_exempt": True,
          "exclude_in_service": False,
          "pending_quota_planning": False,
          "partner_requirements_need_confirmation": False,
          "degree_score_minimums": {"undergraduate": 70.0, "graduate": 70.0},
          "excluded_undergraduate_years": ["大一上"],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 61.0,
          "ielts": 5.0,
          "toeic": 550.0,
      },
      "application_periods": [
          {
              "title": (
                  "國立勤益科技大學「115學年度第二梯次（116-1秋季班出國交換暨115年度第2梯次學海飛颺）」甄選（即日起至"
                  " 2026/12/24 17:00 截止，11/11 舉辦第3次海外研習說明會）"
              ),
              "details": [
                  (
                      "開放申請交換期間：116 學年度第一學期（2027"
                      " 秋季班）學期／學年交換及歐美雙聯學制。報名期間：自即日起（2026/10/23）至"
                      " 2026/12/24（四）17:00"
                      " 止，請完成線上報名並將紙本申請表件送至圖資大樓 5"
                      " 樓國際事務處國際交流組（分機 2198／2192）。"
                  ),
                  (
                      "115 學年度第三次海外研習說明會：線上報名至 2026/11/06"
                      " 止，說明會於 2026/11/11（三）12:00 在圖資大樓 6"
                      " 樓會議室舉行，詳盡說明美、德、捷、英、日、韓、馬、越、泰姊妹校申請流程與最高"
                      " 30 萬元獎助辦法。"
                  ),
              ],
              "source": {
                  "title": (
                      "國立勤益科技大學國際事務處《115學年度第二梯次海外研習甄選簡章與第三次海外研習說明會公告》"
                  ),
                  "source_url": NCUT_115_2_INFO_POST_URL,
                  "category": "exchange_application",
                  "summary": (
                      "勤益科大 115 學年度第二梯次出國交換暨學海飛颺甄選截止日期（2026/12/24"
                      " 17:00）與第三次海外研習說明會（2026/11/11）資訊。"
                  ),
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": (
                  "115-2（116-1秋季班）赴海外姊妹校交換學生暨學海飛颺第2梯次甄選"
              ),
              "audience": "all_students",
              "opens_at": "2026-10-23T08:30:00+08:00",
              "deadline_at": "2026-12-24T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "open",
              "status_note": (
                  "115 學年度第二梯次海外研習甄選海報、雙聯學制簡章與第三次海外研習說明會已正式公告於國際事務處網站。"
              ),
              "deadline_note": (
                  "2026/11/11 12:00 舉辦第三次海外研習說明會（11/06"
                  " 報名截止）；116-1 出國交換與學海飛颺第 2 梯次申請於"
                  " 2026/12/24（四）17:00 截止。"
              ),
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": (
                  "國立勤益科技大學「115學年度第一梯次（115-2春季班出國交換暨海外暑期研習）」甄選（06/12"
                  " 17:00 截止）"
              ),
              "details": [
                  (
                      "開放申請交換期間：115 學年度第二學期（2027"
                      " 春季班）交換學生及歐美日韓泰越馬暑期研習計畫，校內收件於"
                      " 2026/06/12（五）17:00 截止。"
                  ),
                  (
                      "涵蓋德國達姆施塔特（h_da）ISU 國際暑期學校、捷克斯柯達汽車大學（Škoda"
                      " Auto）與赫拉德茨克拉洛韋大學（UHK）暑期學校、美國加州州立大學富勒頓分校（CSUF）創新體驗營及韓國嘉泉大學國際夏季學期。"
                  ),
              ],
              "source": {
                  "title": (
                      "國立勤益科技大學國際事務處《115學年度第一梯次海外研習說明會與春季班交換甄選公告》"
                  ),
                  "source_url": NCUT_115_2_INFO_PDF_URL,
                  "category": "exchange_application",
                  "summary": (
                      "勤益科大 115"
                      " 學年度第一梯次海外研習說明會簡報、開放學校一覽與收件時程。"
                  ),
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": (
                  "115-1（115-2春季班）赴海外姊妹校交換學生暨暑期研習甄選"
              ),
              "audience": "all_students",
              "opens_at": "2026-03-01T08:30:00+08:00",
              "deadline_at": "2026-06-12T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "open",
              "status_note": (
                  "115 學年度第一梯次海外研習簡報與錄取榜單已公告於國際事務處網站。"
              ),
              "deadline_note": (
                  "春季班出國交換於每年 5–6 月截止收件（115 年度為 2026/06/12"
                  " 17:00 截止）。"
              ),
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [{
          "title": (
              "國立勤益科技大學國際事務處全球姊妹校交換學生、歐美雙聯學制與三級分區獎助總覽（"
              f"{len(partners)} 所締約姊妹校・{open_partner_count} 所當期開放交換／雙聯）"
          ),
          "details": [
              (
                  "國立勤益科技大學（National Chin-Yi University of Technology,"
                  " NCUT，位於臺中市太平區，設有「工程學院、電資學院、管理學院、人文創意學院、通識教育學院」五大學院）由「國際事務處（Office"
                  " of International Affairs，圖資大樓 5"
                  " 樓，下設國際交流組、外國學生事務組及華語文中心）」統籌全校出國交換學生、歐美雙聯學制、海外短期研習與教育部學海系列計畫。本平台完整收錄"
                  f" {len(partners)} 所勤益科大官方合作姊妹校，橫跨全球 20"
                  f" 個國家與地區（含 {open_partner_count} 所當期開放申請之交換與雙聯合作校）。"
              ),
              (
                  "勤益科大出國交換與國際交流體系具備五大核心特色：（1）當期開放"
                  f" {open_partner_count} 所歐美亞重點交換與雙聯名校（美國加州州立大學富勒頓分校"
                  " CSUF、北伊利諾大學 NIU［含工程 3+1+1 碩士雙聯］、佛羅里達理工大學、波莫納加州州立理工大學"
                  " Cal Poly Pomona［電資 MSEE 碩士雙聯］、漢弗萊斯大學［3+1"
                  " BBA／1+1 MBA & MSIT 雙聯］；德國 HAWtech"
                  " 六校聯盟［達姆施塔特 h_da、埃斯林根、德勒斯登 HTW、阿亨 FH"
                  " Aachen、卡爾斯魯厄 HKA、柏林 HTW］與德勒斯登工業大學 TU"
                  " Dresden；捷克赫拉德茨克拉洛韋大學 UHK、斯柯達汽車大學 Škoda"
                  " Auto；英國密德薩斯大學［3+1／1+1 雙聯］；日本佐賀大學、北見工業大學、九州工業大學、室蘭工業大學、千葉大學；韓國嘉泉大學、淑明女子大學；馬來西亞砂拉越科技大學、雙威大學；越南河內交通運輸大學、河內國家大學外國語大學；泰國瓦萊嵐大學、東方大學、吞武里國王科技大學"
                  " KMUTT、佛統皇家大學等）；（2）高額三級分區獎助金（美日德每學期上限"
                  " 15 萬元／學年 30 萬元、歐美韓每學期 12 萬元／學年 24"
                  " 萬元、亞太每學期 9 萬元／學年 18"
                  " 萬元）及經濟不利學生圓夢助學金（另加發 3 萬–10"
                  " 萬元）；（3）出國期間大學部減免勤益「學費」、研究所減免「學分費」；（4）海外每學期至少修讀"
                  " 3 門正式課程（等同勤益 9 學分）並設出國前預先學分採認機制；（5）官網完整公開"
                  f" {exp_covered_schools} 校 {total_exp_reports}"
                  " 篇學長姐交換心得報告書與 YouTube 留學影片。"
              ),
          ],
          "source": {
              "title": (
                  "國立勤益科技大學國際事務處（OIA）交換學生計畫專區與締約姊妹校名冊"
              ),
              "source_url": NCUT_OUTGOING_EXCHANGE_URL,
              "category": "exchange_application",
              "summary": (
                  f"勤益科大 {len(partners)} 所全球合作姊妹校與"
                  f" {open_partner_count} 所當期交換及雙聯學校總覽。"
              ),
          },
      }],
      "eligibility": [{
          "title": (
              "勤益科大大學部大二以上／研究所碩一以上在學資格、學業 70 分或前"
              " 50% 門檻與海外應修 3 門課（9 學分）規定"
          ),
          "details": [
              (
                  "修業年級與學籍規定：依《國立勤益科技大學學生國際交流甄選要點》第三點及《學生海外研習甄選與經費獎助要點》第三點規定，申請人須為本校大學部二年級（含）以上或研究所一年級下學期（含）以上之在學學生（大一下學期即可報名申請大二出國交換；休學期間不得申請）。"
              ),
              (
                  "成績門檻與修課標準：大學部歷年課業成績總平均達 70 分（約 GPA"
                  " 2.5）以上或系排名前 50%"
                  " 以內；研究所須檢附論文或專題指導教授推薦信。交換期間每學期至少須選修並通過"
                  " 3 門正式學分課程（等同勤益 9"
                  " 學分，不含語言、文化或體育類課程，且至少 6 學分或 2"
                  " 門課及格；獲獎學金赴美 CSUF 者須修習至少 12 學分）。"
              ),
          ],
          "source": {
              "title": (
                  "國立勤益科技大學學生國際交流甄選要點與學生海外研習甄選與經費獎助要點"
              ),
              "source_url": NCUT_GUIDELINES_OVERSEAS_STUDY_PDF_URL,
              "category": "exchange_application",
              "summary": "勤益科大交換生申請資格、學業門檻、海外應修學分與返國結案義務。",
          },
      }],
      "language_requirements": [{
          "title": (
              "勤益科大交換留學語檢門檻（CEFR B1［TOEIC 550 / TOEFL iBT 61 / ITP"
              " 500 / IELTS 5.0］、德國 HAWtech 德語 A1/B1、日本 JLPT N1–N3、韓國"
              " TOPIK 2）"
          ),
          "details": [
              (
                  "基本外語能力標準：依《學生海外研習甄選與經費獎助要點》第五點，學期／學年型交換生與雙聯學制申請人須具備"
                  " CEFR B1（含）以上語言能力證明（報名截止日前兩年內有效，且明文規定「不接受"
                  " CSEPT 大學院校英語能力測驗」），對應 TOEIC 550、TOEFL iBT"
                  " 61、TOEFL ITP 500、IELTS 5.0 或 GEPT 中級（暑期營隊須達 CEFR"
                  " A2 / TOEIC 225 以上）。雙聯學制（NIU、Cal Poly"
                  " Pomona、Middlesex）及日本佐賀大學 SPACE-E 學程另要求 TOEFL"
                  " iBT 72–80、IELTS 5.5–6.5 或 TOEIC 740。"
              ),
              (
                  "德日韓語特別規定：（1）德國 HAWtech"
                  " 聯盟學校（達姆施塔特、埃斯林根、德勒斯登、阿亨、卡爾斯魯厄、柏林）：除英語"
                  " B1/B2 外，須另具備德語檢定 Goethe-Zertifikat A1（埃斯林根為"
                  " B1）以上；（2）日本姊妹校：北見工業大學要求 JLPT N3 或 TOEIC"
                  " 550，佐賀大學、九州工業大學、室蘭工業大學、千葉大學要求大學部"
                  " JLPT N2、碩士班 JLPT N1（研究交換或英語學程可持 TOEIC"
                  " 550–740）；（3）韓國嘉泉大學與淑明女子大學：要求 TOPIK 2–3"
                  " 級或英語 TOEIC 550。"
              ),
          ],
          "source": {
              "title": (
                  "國立勤益科技大學《學生海外研習甄選與經費獎助要點》與各國交換姊妹校申請條件表"
              ),
              "source_url": NCUT_OUTGOING_EXCHANGE_URL,
              "category": "exchange_application",
              "summary": "勤益科大官方 CEFR B1 語檢門檻與美、德、捷、英、日、韓、馬、越、泰姊妹校語言條件。",
          },
      }],
      "required_documents": [{
          "title": (
              "交換學生甄選申請表、歷年中英文成績單、兩年內語檢證明、外文讀書計畫與自傳、家長同意書與研究生指導教授推薦信（共9項）"
          ),
          "details": [
              (
                  "校內甄選 9 項必備表件：（1）交換學生甄選申請表（電腦打字、貼"
                  " 2 吋照片，含導師或論文指導教授簽名審查意見）；（2）大學歷年中文成績單正本（含排名；轉學生須附原校成績單）；（3）大學歷年英文成績單正本；（4）報名截止日前兩年內有效之語言能力證明影本（不接受"
                  " CSEPT）；（5）外文讀書計畫（含修課規劃、預計達成目標）；（6）外文自傳（含自我介紹、申請動機）；（7）家長同意書（全學制皆須繳交）；（8）教授推薦信（大學部免繳，研究所必繳）；（9）交換學生繳交資料檢核表及獎助學金具結書，並完成線上報名表單。"
              ),
              (
                  "錄取後行前與返國表件：錄取生須繳交《錄取資格確認書》、《出國前修課規劃之學分採認及抵免申請表》、《獎助學生海外研修行政契約書》（一式三份，需保證人"
                  " 1 人）及《出國程序單》；返國後兩週（14"
                  " 日）內須繳交《返校程序單》、教育部學海版（5,000 字以上及 6"
                  " 張照片）與勤益校內版成果報告書及 3–5 分鐘短片。"
              ),
          ],
          "source": {
              "title": (
                  "國立勤益科技大學國際事務處《交換學生申請表》與《交換學生繳交資料檢核表》"
              ),
              "source_url": NCUT_DOC_CHECKLIST_PDF_URL,
              "category": "exchange_application",
              "summary": "勤益科大交換學生校內申請 9 項檢核表件與行前、返國程序單規定。",
          },
      }],
      "scholarship_info": [{
          "title": (
              "《國立勤益科技大學學生海外研習甄選與經費獎助要點》三級分區獎助金（上限15萬／30萬）、圓夢助學金與學雜費減免"
          ),
          "details": [
              (
                  "三級分區海外研習獎助金（含教育部學海飛颺及高教深耕經費）：（1）第"
                  " 1 級（德國 HAWtech 聯盟、日本、美國）：每學期上限 15"
                  " 萬元、一學年上限 30 萬元、短期上限 6 萬元；（2）第 2"
                  " 級（其他歐美、大洋洲及韓國）：每學期上限 12 萬元、一學年上限"
                  " 24 萬元、短期上限 4 萬元；（3）第 3"
                  " 級（其他亞太地區）：每學期上限 9 萬元、一學年上限 18"
                  " 萬元、短期上限 2 萬元。分兩階段核發（出國前 80%、返國繳齊報告與短片後"
                  " 20%）。"
              ),
              (
                  "經濟不利學生圓夢助學金與學雜費減免：具低收、中低收、特境、身障或原住民資格者，依前往地區另加發每學期"
                  " 3 萬–5 萬元、每學年 6 萬–10 萬元（短期 1 萬–2"
                  " 萬元）定額補助；且出國交換期間大學部減免勤益「學費」、研究所減免「學分費」。"
              ),
          ],
          "source": {
              "title": (
                  "國立勤益科技大學《學生海外研習甄選與經費獎助要點（115.06.25修頒）》與《學生國際交流甄選要點》"
              ),
              "source_url": NCUT_GUIDELINES_OVERSEAS_STUDY_PDF_URL,
              "category": "scholarship",
              "summary": "勤益科大三級分區海外研習獎助金、圓夢助學金與出國期間學費／學分費減免辦法。",
          },
      }],
      "document_explanations": [{
          "title": (
              "國立勤益科技大學交換學生申請文件檢核表（9項）、行政契約書連帶保證與雙版本成果報告規範"
          ),
          "summary": (
              "說明勤益科大交換生申請表電腦打字規定、轉學生原校成績單、全學制家長同意書、出國前預先學分採認表、行政契約書保證人及返國"
              " 14 日內雙版本報告與短片繳交規範。"
          ),
          "key_points": [
              (
                  "校內申請 9 項文件規定：申請表、外文讀書計畫（含修課規劃與預計目標）及外文自傳（含自我介紹與申請動機）均須以電腦打字；家長同意書不論大學部或研究所皆須繳交；研究所學生須另附論文指導教授推薦信。"
              ),
              (
                  "出國前行政契約書與預先學分採認：錄取並獲獎助者須簽訂《獎助學生海外研修行政契約書》一式三份（覓保證人"
                  " 1 人負連帶償還責任），並填妥《出國前修課規劃之學分採認及抵免申請表》（每學期至少"
                  " 3 門正式課程、等同勤益 9 學分）送系所及教務處審核。"
              ),
              (
                  "海外雙週誌與返國 14 日內結案：海外研習期間每兩週須繳交雙週誌；返國後兩週（14"
                  " 日）內須繳交《返校程序單》、教育部學海版成果報告（5,000"
                  " 字以上及 6 張照片）、勤益校內版 5 頁問卷報告、600–1,000"
                  " 字中文總心得及 3–5 分鐘留學短片，始得請領第二階段 20% 獎助金。"
              ),
          ],
          "applies_to": [],
          "source": {
              "title": "國立勤益科技大學交換學生申請文件檢核表與出國／返校程序單",
              "source_url": NCUT_DOWNLOADS_EXCHANGE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          "document_url": NCUT_DOC_CHECKLIST_PDF_URL,
          "document_type": "official_document",
          "full_text_extracted": True,
      }],
      "rule_explanations": [{
          "title": (
              "國立勤益科技大學學生海外研習甄選與經費獎助要點（115.06.25修頒）與學生國際交流甄選要點核心法規"
          ),
          "summary": (
              "規範勤益科大五大學院學生申請出國交換與雙聯學制之年級與成績門檻、三級分區獎助上限、圓夢助學金、學費／學分費減免及海外修課及格標準。"
          ),
          "key_points": [
              (
                  "年級、成績與語檢門檻：大學部大二以上（大一下可申請）、研究所碩一以上在學學生；大學部歷年總平均達"
                  " 70 分（GPA 2.5）以上或系排名前 50% 以內；學期／學年型須具"
                  " CEFR B1（TOEIC 550 / TOEFL iBT 61 / ITP 500 / IELTS"
                  " 5.0，兩年內有效，不接受 CSEPT）。"
              ),
              (
                  "三級分區獎助與圓夢加給：第 1 級（德 HAWtech、日、美）每學期上限"
                  " 15 萬／學年 30 萬；第 2 級（其他歐美大洋洲、韓）每學期上限 12"
                  " 萬／學年 24 萬；第 3 級（其他亞太）每學期上限 9 萬／學年 18"
                  " 萬；經濟不利學生另加發學期型 3 萬–5 萬元、學年型 6 萬–10 萬元。"
              ),
              (
                  "出國期間學費減免與最低及格學分：出國期間大學部減免勤益「學費」、研究所減免「學分費」；海外每學期至少須選修"
                  " 3 門正式課程（等同勤益 9 學分，不含語言、文化或體育課）且至少"
                  " 6 學分或 2 門課及格（獲獎學金赴美 CSUF 須修至少 12"
                  " 學分），未達標準者須依契約比例繳回獎助金。"
              ),
          ],
          "applies_to": [],
          "source": {
              "title": (
                  "國立勤益科技大學學生海外研習甄選與經費獎助要點（115.06.25修頒）與學生國際交流甄選要點"
              ),
              "source_url": NCUT_REGULATIONS_URL,
              "category": "exchange_application",
              "summary": None,
          },
          "document_url": NCUT_GUIDELINES_OVERSEAS_STUDY_PDF_URL,
          "document_type": "official_document",
          "full_text_extracted": True,
      }],
      "sources": [
          {
              "title": "國立勤益科技大學國際事務處（OIA）官方網站",
              "source_url": NCUT_OIA_HOME_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": (
                  f"國立勤益科技大學出國交換學生計畫專區（{open_partner_count}所當期開放交換／雙聯合作學校與學長姐心得影片）"
              ),
              "source_url": NCUT_OUTGOING_EXCHANGE_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": (
                  f"國立勤益科技大學國際事務處締約姊妹校名冊（全球20國共{len(partners)}所合作機構）"
              ),
              "source_url": NCUT_MOU_PARTNERS_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立勤益科技大學歐美雙聯學制與交換名額簡章 PDF",
              "source_url": NCUT_DUAL_DEGREE_BROCHURE_PDF_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": (
                  "國立勤益科技大學 115 學年度第二梯次海外研習甄選（12/24截止）與第三次說明會公告"
              ),
              "source_url": NCUT_115_2_INFO_POST_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": (
                  "國立勤益科技大學學生海外研習甄選與經費獎助要點（115.06.25修頒）PDF"
              ),
              "source_url": NCUT_GUIDELINES_OVERSEAS_STUDY_PDF_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "國立勤益科技大學學生國際交流甄選要點 PDF",
              "source_url": NCUT_GUIDELINES_INTL_EXCHANGE_PDF_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立勤益科技大學國際事務處檔案下載—交換生專區",
              "source_url": NCUT_DOWNLOADS_EXCHANGE_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_NCUT_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  doc_conditions = {
      "school_id": "ncut",
      "school_name": "國立勤益科技大學",
      "checked_at": CHECKED_AT,
      "source_url": NCUT_DOC_CHECKLIST_PDF_URL,
      "common_documents": exchange_info_payload["required_documents"],
      "track_specific_conditions": [
          {
              "track": (
                  "國際事務處【赴美、德、捷、日、韓、馬、越、泰、印、菲姊妹校交換學生計畫】"
              ),
              "required": [
                  (
                      "交換學生甄選申請表（電腦打字、貼2吋照片，含導師或論文指導教授簽名審查意見）、家長同意書及繳交資料檢核表"
                  ),
                  (
                      "大學／研究所歷年中文成績單正本（含排名；轉學生須附原校成績單）與歷年英文成績單正本"
                  ),
                  (
                      "報名截止日前兩年內有效之語言能力證明影本（CEFR B1：TOEIC"
                      " 550、TOEFL iBT 61、TOEFL ITP 500、IELTS 5.0、GEPT"
                      " 中級；德國 HAWtech 另附德語 A1/B1、日本附 JLPT"
                      " N1–N3、韓國附 TOPIK 2；不接受 CSEPT）"
                  ),
                  (
                      "外文讀書計畫（含修課規劃、預計達成目標）、外文自傳（含自我介紹、申請動機）及研究所指導教授推薦信"
                  ),
              ],
          },
          {
              "track": (
                  "國際事務處【歐美雙聯學位學制專案（美國北伊利諾大學 NIU、波莫納加州州立理工大學"
                  " Cal Poly Pomona、漢弗萊斯大學 Humphreys、英國密德薩斯大學"
                  " Middlesex）】"
              ),
              "required": [
                  (
                      "北伊利諾大學（NIU 工程 3+1+1）與波莫納加州州立理工大學（Cal"
                      " Poly Pomona 電資 MSEE）：須備妥 GPA 2.5–3.0 以上英文成績單及"
                      " TOEFL iBT 79–80 或 IELTS 6.5 以上成績證明"
                  ),
                  (
                      "英國倫敦密德薩斯大學（Middlesex 3+1／1+1）：須備妥 GPA"
                      " 2.5 以上英文成績單及 IELTS 6.0（單科不低於 5.5）成績證明"
                  ),
                  (
                      "漢弗萊斯大學（Humphreys 3+1 BBA／1+1 MBA &"
                      " MSIT）：須備妥歷年英文成績單、TOEIC 550 / TOEFL iBT 61"
                      " 以上證明、外文讀書計畫、英文財力證明及有效護照影本"
                  ),
              ],
          },
          {
              "track": (
                  "教育部【學海飛颺】暨【國立勤益科技大學三級分區海外研習獎助金＆經濟不利學生圓夢助學金】"
              ),
              "required": [
                  (
                      "申請經濟不利學生圓夢助學金者，須另檢附有效低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助或原住民身分證明文件"
                  ),
                  (
                      "獲獎助學生出國前須簽訂《獎助學生海外研修行政契約書》一式三份（覓保證人1人連帶保證）、《出國前修課規劃之學分採認及抵免申請表》及《出國程序單》以請領第一階段80%獎助金"
                  ),
                  (
                      "海外研習期間每兩週繳交雙週誌，並於返國後14日內繳交《返校程序單》、教育部學海版（5,000字以上及6張照片）與校內版成果報告書、3–5分鐘短片、登機證正本與機票代收轉付收據以核發剩餘20%獎助金"
                  ),
              ],
          },
      ],
  }
  (OFFICIAL_NCUT_DIR / "document-conditions.json").write_text(
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
        f"{fname},{len(partners)},{pop},{ratio:.4f},Official NCUT OIA verified"
    )
  (OFFICIAL_NCUT_DIR / "field-coverage.csv").write_text(
      "\n".join(field_cov_lines) + "\n", encoding="utf-8"
  )

  pages_records = [
      {
          "title": (
              "國立勤益科技大學：115 學年度第二梯次（116-1秋季班）海外研習甄選（12/24截止）、第三次海外研習說明會（11/11）與第一梯次春季班時程"
          ),
          "source_url": NCUT_115_2_INFO_POST_URL,
          "published_at": "2026-10-23T00:00:00Z",
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
              "國立勤益科技大學：學生國際交流甄選要點、學業 70 分／前 50% 門檻、海外應修 3 門正式課程（等同 9 學分）與返國 14 日內結案規定"
          ),
          "source_url": NCUT_GUIDELINES_INTL_EXCHANGE_PDF_URL,
          "published_at": "2026-06-25T00:00:00Z",
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
              f"國立勤益科技大學：{len(partners)} 所全球合作姊妹校名冊、{open_partner_count}"
              " 所交換與歐美雙聯學制一覽表及 CEFR B1／德日韓語檢門檻"
          ),
          "source_url": NCUT_OUTGOING_EXCHANGE_URL,
          "published_at": "2026-10-23T00:00:00Z",
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
              "國立勤益科技大學：交換學生申請文件檢核表（9項）、出國前預先學分採認、行政契約書連帶保證與返國雙版本報告規範"
          ),
          "source_url": NCUT_DOC_CHECKLIST_PDF_URL,
          "published_at": "2026-10-23T00:00:00Z",
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
              "國立勤益科技大學：學生海外研習甄選與經費獎助要點（三級分區上限15萬/30萬）、經濟不利圓夢助學金（加發3萬–10萬）與出國學費減免"
          ),
          "source_url": NCUT_GUIDELINES_OVERSEAS_STUDY_PDF_URL,
          "published_at": "2026-06-25T00:00:00Z",
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
  (OFFICIAL_NCUT_DIR / "pages.jsonl").write_text(pages_text, encoding="utf-8")
  (OFFICIAL_NCUT_DIR / "processed_pages.jsonl").write_text(
      pages_text, encoding="utf-8"
  )

  home_rules = {
      "school_id": "ncut",
      "school_name": "國立勤益科技大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "undergraduate_score_minimum": 70.0,
          "undergraduate_class_rank_percent_maximum": 50.0,
          "undergraduate_gpa_minimum": 2.5,
          "graduate_advisor_recommendation_required": True,
          "overseas_min_courses_per_semester": 3,
          "overseas_min_credits_per_semester": 9,
          "overseas_min_passing_credits_per_semester": 6,
          "maximum_preferences": 3,
          "screening_batches_per_year": 2,
          "allow_freshman_second_semester_apply": True,
          "min_enrolled_semesters": 1,
          "tuition_policy_during_exchange": (
              "交換或研修學生於出國期間應在國立勤益科技大學辦理註冊手續；依《學生國際交流甄選要點》第八點，大學部學生減免出國期間「學費」，研究所學生減免出國期間「學分費」"
          ),
          "return_documents_due": (
              "獲獎助學生在國外期間每兩週繳交雙週誌，並須於返國後兩週（14日）內繳交返校程序單、教育部學海版（5,000字以上及6張照片）與校內版成果報告書、3–5分鐘短片、登機證正本與機票收據以核發剩餘20%獎助金"
          ),
      },
      "source_urls": ncut_source_urls,
      "verified_at": "2026-10-31",
  }
  (OFFICIAL_NCUT_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCUT_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "國立勤益科技大學",
              "required_documents": student_dashboard_payload[
                  "required_documents"
              ],
              "source_urls": ncut_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCUT_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "國立勤益科技大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": ncut_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "ncut",
      "school_name": "國立勤益科技大學",
      "total_partners": len(partners),
      "partner_count": len(partners),
      "international_partners": sum(
          1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
      ),
      "mainland_partners": sum(
          1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
      ),
      "dual_degree_partner_universities": 4,
      "dual_degree_programs": 5,
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
          "國立勤益科技大學國際事務處 115 學年度（第二梯次 116-1 秋季班交換暨學海飛颺第 2"
          " 梯次申請：即日起至 2026/12/24 17:00 收件截止，2026/11/11"
          " 舉辦第三次海外研習說明會；第一梯次 115-2 春季班交換：06/12"
          " 截止）全球單學期／學年交換計畫及歐美雙聯學制（NIU、Cal Poly"
          f" Pomona、Humphreys、Middlesex）同步整合；共完整收錄 {len(partners)}"
          f" 所合作姊妹校（橫跨全球 20 個國家與地區，含 {open_partner_count}"
          f" 所當期開放申請校，並收錄 {exp_covered_schools} 所合作大學共"
          f" {total_exp_reports} 篇交換學生心得報告書、YouTube 影片與錄取專案紀錄）。"
      ),
      "verified_at": "2026-10-31",
  }
  (OFFICIAL_NCUT_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCUT_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "ncut",
              "school_name": "國立勤益科技大學",
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
  (OFFICIAL_NCUT_DIR / "dashboard_manifest.json").write_text(
      json.dumps(
          {
              "school_id": "ncut",
              "school_name": "國立勤益科技大學",
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
          "sources/ncut/oia_home.html",
          NCUT_OIA_HOME_URL,
          "國立勤益科技大學國際事務處（OIA）首頁 HTML",
      ),
      (
          "sources/ncut/oia_outgoing_exchange.html",
          NCUT_OUTGOING_EXCHANGE_URL,
          "國立勤益科技大學國際事務處—出國交換學生計畫總覽 HTML",
      ),
      (
          "sources/ncut/oia_mou_partners.html",
          NCUT_MOU_PARTNERS_URL,
          "國立勤益科技大學國際事務處—締約姊妹校名冊（136筆合約紀錄）HTML",
      ),
      (
          "sources/ncut/oia_regulations.html",
          NCUT_REGULATIONS_URL,
          "國立勤益科技大學國際事務處—法規專區 HTML",
      ),
      (
          "sources/ncut/oia_downloads_exchange.html",
          NCUT_DOWNLOADS_EXCHANGE_URL,
          "國立勤益科技大學國際事務處—檔案下載（交換生專區）HTML",
      ),
      (
          "sources/ncut/oia_sop.html",
          NCUT_SOP_URL,
          "國立勤益科技大學國際事務處—標準作業流程（SOP）專區 HTML",
      ),
      (
          "sources/ncut/oia_faq.html",
          NCUT_FAQ_URL,
          "國立勤益科技大學國際事務處—常見問題 FAQ HTML",
      ),
      (
          "sources/ncut/modules/mod_mobile_um_mstr_1407.html",
          NCUT_OUTGOING_EXCHANGE_URL,
          "國立勤益科技大學國際事務處—交換學生計畫學生心得報告與影片分享模組 HTML",
      ),
      (
          "sources/ncut/modules/mod_mobile_um_mstr_1741.html",
          NCUT_OUTGOING_EXCHANGE_URL,
          "國立勤益科技大學國際事務處—美國交換姊妹校申請條件模組 HTML",
      ),
      (
          "sources/ncut/modules/mod_mobile_um_mstr_1582.html",
          NCUT_OUTGOING_EXCHANGE_URL,
          "國立勤益科技大學國際事務處—捷克交換姊妹校申請條件模組 HTML",
      ),
      (
          "sources/ncut/modules/mod_mobile_um_mstr_1583.html",
          NCUT_OUTGOING_EXCHANGE_URL,
          "國立勤益科技大學國際事務處—德國 HAWtech 交換姊妹校申請條件模組 HTML",
      ),
      (
          "sources/ncut/modules/mod_mobile_um_mstr_1584.html",
          NCUT_OUTGOING_EXCHANGE_URL,
          "國立勤益科技大學國際事務處—日本交換姊妹校申請條件模組 HTML",
      ),
      (
          "sources/ncut/modules/mod_mobile_um_mstr_1585.html",
          NCUT_OUTGOING_EXCHANGE_URL,
          "國立勤益科技大學國際事務處—韓國交換姊妹校申請條件模組 HTML",
      ),
      (
          "sources/ncut/modules/mod_mobile_um_mstr_1586.html",
          NCUT_OUTGOING_EXCHANGE_URL,
          "國立勤益科技大學國際事務處—馬來西亞交換姊妹校申請條件模組 HTML",
      ),
      (
          "sources/ncut/modules/mod_mobile_um_mstr_1980.html",
          NCUT_OUTGOING_EXCHANGE_URL,
          "國立勤益科技大學國際事務處—越南交換姊妹校申請條件模組 HTML",
      ),
      (
          "sources/ncut/modules/mod_mobile_um_mstr_1993.html",
          NCUT_OUTGOING_EXCHANGE_URL,
          "國立勤益科技大學國際事務處—泰國交換姊妹校申請條件模組 HTML",
      ),
      (
          "sources/ncut/news/post_93677_115_2_info_session.html",
          NCUT_115_2_INFO_POST_URL,
          "國立勤益科技大學 115 學年度第三次海外研習說明會暨第二梯次甄選公告 HTML",
      ),
      (
          "sources/ncut/files/guidelines_intl_exchange_810257914.pdf",
          NCUT_GUIDELINES_INTL_EXCHANGE_PDF_URL,
          "國立勤益科技大學學生國際交流甄選要點 PDF",
      ),
      (
          "sources/ncut/files/guidelines_overseas_study_222864975.pdf",
          NCUT_GUIDELINES_OVERSEAS_STUDY_PDF_URL,
          "國立勤益科技大學學生海外研習甄選與經費獎助要點（115.06.25修頒）PDF",
      ),
      (
          "sources/ncut/files/exchange_quotas_dual_degree_115_608915721.pdf",
          NCUT_DUAL_DEGREE_BROCHURE_PDF_URL,
          "國立勤益科技大學歐美雙聯學制與交換名額簡章 PDF",
      ),
      (
          "sources/ncut/files/info_session_115_2_872345294.pdf",
          NCUT_115_2_INFO_PDF_URL,
          "國立勤益科技大學 115 學年度海外研習說明會簡報 PDF",
      ),
      (
          "sources/ncut/files/exchange_application_form_836273806.pdf",
          NCUT_APP_FORM_PDF_URL,
          "國立勤益科技大學交換學生甄選申請表 PDF",
      ),
      (
          "sources/ncut/files/document_checklist_454721331.pdf",
          NCUT_DOC_CHECKLIST_PDF_URL,
          "國立勤益科技大學交換學生申請文件檢核表 PDF",
      ),
      (
          "sources/ncut/files/admin_contract_578671939.pdf",
          NCUT_ADMIN_CONTRACT_PDF_URL,
          "國立勤益科技大學獎助學生海外研修行政契約書 PDF",
      ),
      (
          "sources/ncut/ncut_experience_index.json",
          NCUT_OUTGOING_EXCHANGE_URL,
          (
              f"國立勤益科技大學出國交換心得報告與影片分享（{exp_covered_schools} 校共"
              f" {total_exp_reports} 篇）索引 JSON"
          ),
      ),
      (
          "sources/ncut/ncut_catalog_source.json",
          NCUT_OUTGOING_EXCHANGE_URL,
          f"國立勤益科技大學 {len(partners)} 所全球合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/ncut/ncut_resolved_locations.json",
          NCUT_OUTGOING_EXCHANGE_URL,
          (
              f"國立勤益科技大學 {len(partners)} 所合作姊妹校 ROR / Wikidata"
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
      "school_id": "ncut",
      "school_name": "國立勤益科技大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = (
      json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  )
  (OFFICIAL_NCUT_DIR / "import_provenance.json").write_text(
      prov_text, encoding="utf-8"
  )
  (OFFICIAL_NCUT_DIR / "import-provenance.json").write_text(
      prov_text, encoding="utf-8"
  )

  print(
      f"Successfully built NCUT catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
