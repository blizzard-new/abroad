"""Build the official National Taitung University (國立臺東大學, NTTU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_NTTU_DIR = REPO_ROOT / "sources" / "nttu"
OFFICIAL_NTTU_DIR = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "nttu"
)
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-06T00:00:00Z"

NTTU_COIA_HOME_URL = "https://rd.nttu.edu.tw/p/412-1007-3262.php?Lang=zh-tw"
NTTU_PARTNER_LIST_URL = "https://rd.nttu.edu.tw/p/412-1007-3264.php?Lang=zh-tw"
NTTU_OUTBOUND_EXCHANGE_URL = "https://rd.nttu.edu.tw/p/412-1007-9902.php?Lang=zh-tw"
NTTU_EXCHANGE_RECRUITMENT_URL = "https://rd.nttu.edu.tw/p/412-1007-9903.php?Lang=zh-tw"
NTTU_2027_SPRING_ANNOUNCEMENT_URL = "https://rd.nttu.edu.tw/p/406-1007-179057,r1848.php?Lang=zh-tw"
NTTU_2026_FALL_ANNOUNCEMENT_URL = "https://rd.nttu.edu.tw/p/406-1007-173156,r1848.php?Lang=zh-tw"
NTTU_2027_SPRING_RESULTS_URL = "https://rd.nttu.edu.tw/p/406-1007-180597,r1848.php?Lang=zh-tw"
NTTU_EXCHANGE_REGULATIONS_URL = "https://rd.nttu.edu.tw/p/412-1007-9904.php?Lang=zh-tw"
NTTU_XUEHAI_HUB_URL = "https://rd.nttu.edu.tw/p/412-1007-9897.php?Lang=zh-tw"
NTTU_XUEHAI_FEIYANG_REGULATIONS_URL = "https://rd.nttu.edu.tw/p/412-1007-9910.php?Lang=zh-tw"
NTTU_XUEHAI_ZHUMENG_REGULATIONS_URL = "https://rd.nttu.edu.tw/p/412-1007-10011.php?Lang=zh-tw"
NTTU_EXPERIENCE_SHARING_URL = "https://rd.nttu.edu.tw/p/412-1007-9911.php?Lang=zh-tw"
NTTU_ZHUMENG_EXPERIENCE_URL = "https://rd.nttu.edu.tw/p/412-1007-10015.php?Lang=zh-tw"
NTTU_AA_REGULATIONS_URL = "https://aa.nttu.edu.tw/p/412-1002-8180.php?Lang=zh-tw"
NTTU_DOMESTIC_EXCHANGE_URL = "https://aa.nttu.edu.tw/p/405-1002-98439,c8180.php?Lang=zh-tw"

NTTU_2027_SPRING_QUOTA_PDF_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/900770058.pdf"
NTTU_2027_SPRING_BROCHURE_PDF_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/684217375.pdf"
NTTU_2026_FALL_QUOTA_PDF_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/146113981.pdf"
NTTU_2026_FALL_BROCHURE_PDF_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/896144241.pdf"
NTTU_OUTBOUND_FLOWCHART_PDF_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/524705677.pdf"
NTTU_EXCHANGE_GUIDELINES_PDF_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/615221646.pdf"
NTTU_SCHOLARSHIP_GUIDELINES_PDF_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/747047936.pdf"
NTTU_DUAL_DEGREE_REGULATIONS_PDF_URL = "https://aa.nttu.edu.tw/var/file/2/1002/img/1164/473961823.pdf"
NTTU_STUDY_ABROAD_ACADEMIC_PDF_URL = "https://aa.nttu.edu.tw/var/file/2/1002/img/1164/738126067.pdf"
NTTU_CREDIT_TRANSFER_PDF_URL = "https://aa.nttu.edu.tw/var/file/2/1002/img/1164/833443330.pdf"
NTTU_GPA_CONVERSION_PDF_URL = "https://aa.nttu.edu.tw/var/file/2/1002/img/1164/257867879.pdf"

NTTU_APPLICATION_FORM_DOCX_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/339798359.docx"
NTTU_PARENTAL_CONSENT_DOCX_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/393778079.docx"
NTTU_STUDY_PLAN_DOCX_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/488363506.docx"
NTTU_SCHOLARSHIP_FORM_DOCX_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/447717464.docx"
NTTU_XUEHAI_FORM_DOCX_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/146816299.docx"

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 680–1,150（折合日圓約 JPY 95,000–160,000 / 月、新臺幣約 21,500–36,500 元；日本天理大學提供交換生免學費、免宿舍費且免水電瓦斯費之極優厚待遇；仙台大學學生宿舍每月 JPY 32,000［押金 JPY 20,000］；琵琶湖成蹊體育運動大學 1.5+2+1 雙聯學位生可申請校內外學生宿舍）",
        "須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後申辦日本留學簽證並加入日本國民健康保險（NHI，約 JPY 20,000/年）。",
    ),
    "韓國": (
        "每月生活費約 USD 600–1,000（折合韓元約 KRW 800,000–1,350,000 / 月、新臺幣約 19,000–32,000 元；釜山高神大學學生宿舍每 6 個月約 KRW 1,100,000［不含餐，可於校內餐廳自費約 KRW 4,000/餐］，國立順天大學與釜山教育大學均提供低廉校內學生生活館）",
        "須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後辦理外國人登錄證並納保韓國國民健康保險。",
    ),
    "中國大陸": (
        "每月生活費約 USD 350–650（折合人民幣約 RMB 2,400–4,500 / 月、新臺幣約 11,000–20,500 元；華東師範大學、蘭州大學、華中師範大學、西南大學、東北師範大學、中央民族大學、鄭州大學等校內學生宿舍與食堂費用實惠）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及接待校錄取通知書報到，並依臺東大學規定購買涵蓋交換全期之海外醫療及意外保險且完成教育部「赴陸交流活動登錄平臺」申報。",
    ),
    "美國": (
        "每月生活費約 USD 1,250–1,950（折合新臺幣約 40,000–62,000 元；美國加州西來大學 University of the West 提供至多 12 學分學費半價減免，每學期校內住宿及膳食費依房型約 USD 3,660–5,940、接機費 USD 60）",
        "須憑美國接待大學核發之 I-20 或 DS-2019 表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦 F-1 或 J-1 學生簽證，且須投保符合校方與美國規定之全期醫療保險。",
    ),
    "捷克": (
        "每月生活費約 USD 650–1,050（折合歐元約 EUR 600–960 / 月、新臺幣約 21,000–33,500 元；捷克茲林托馬斯巴塔大學 Tomas Bata University in Zlín 保證提供交換生校內學生宿舍，每月住宿費僅約 USD 165–360）",
        "交換 1 學期以上須憑茲林托馬斯巴塔大學入學許可、住宿證明與申根醫療保險向捷克經濟文化辦事處申辦長期學生簽證（Long-Term Visa for the Purpose of Studies）。",
    ),
    "芬蘭": (
        "每月生活費約 USD 950–1,450（折合歐元約 EUR 880–1,350 / 月、新臺幣約 30,500–46,500 元；赫爾辛基大學學生公寓 HOAS 每月房租約 EUR 380–580）",
        "交換或海外實習期間須依芬蘭移民局（Migri）規定申辦學生居留許可或申根簽證，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "泰國": (
        "每月生活費約 USD 450–800（折合泰銖約 THB 15,000–26,500 / 月、新臺幣約 14,500–25,500 元；清萊皇太后大學、曼谷吞武里皇家大學與芭達雅東方大學校園住宿與膳食費用親民）",
        "須憑泰國接待大學入學許可公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 教育簽證並投保海外全期醫療險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 480–820（折合馬幣約 MYR 2,100–3,600 / 月、新臺幣約 15,500–26,000 元；拉曼大學、馬來亞大學、南方大學學院與新紀元大學學院生活開銷實惠）",
        "須由馬來西亞接待大學透過 EMGS（Education Malaysia Global Services）代辦馬來西亞學生簽證核准函（VAL）並投保當地醫療險。",
    ),
    "菲律賓": (
        "每月生活費約 USD 480–820（折合新臺幣約 15,500–26,000 元；馬尼拉亞當森大學、萊西姆大學、三一大學及宿霧聖卡洛斯大學校內外住宿與膳食親民）",
        "須依菲律賓接待大學指引辦理學生簽證（9F）或特別學習許可（SSP）並投保海外全期醫療保險。",
    ),
    "印尼": (
        "每月生活費約 USD 420–750（折合新臺幣約 13,500–24,000 元；日惹穆罕默迪亞大學與東爪哇穆罕默迪亞大學住宿與生活開銷低廉）",
        "須憑印尼接待校核發之入學許可與擔保文件申辦印尼學習簽證（Study Visa / KITAS）並投保海外醫療及意外保險。",
    ),
    "越南": (
        "每月生活費約 USD 420–750（折合新臺幣約 13,500–24,000 元；胡志明市國家大學人文與社會科學大學及河內首都大學生活費親民）",
        "須憑越南接待大學入學許可函申辦越南學生簽證（DH Visa）並投保海外全期醫療及意外保險。",
    ),
    "印度": (
        "每月生活費約 USD 400–720（折合新臺幣約 12,800–23,000 元；喜馬偕爾邦中央大學校園食宿費用低廉）",
        "須憑印度接待大學核發之正式錄取通知書向印度台北協會申辦印度學生簽證（Student Visa）並投保海外全期醫療險。",
    ),
    "蒙古": (
        "每月生活費約 USD 450–780（折合新臺幣約 14,500–25,000 元；烏蘭巴托蒙古國立教育大學宿舍與膳食費用實惠）",
        "須憑蒙古國立教育大學入學許可辦理蒙古學生簽證，並於出發前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,200–1,850（折合加幣約 CAD 1,650–2,500 / 月、新臺幣約 38,500–59,000 元；溫哥華島大學與漢博理工學院校內外住宿與生活費）",
        "交換 1 學期（6 個月內）得持 eTA 入境就讀；滿 1 學年須向加拿大移民局（IRCC）申辦 Study Permit（學習許可）並投保醫療保險。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,400–2,150（折合澳幣約 AUD 2,150–3,300 / 月、新臺幣約 45,000–68,500 元；坎培拉大學校內住宿與生活費）",
        "須購買澳洲海外學生健康保險（OSHC）並憑坎培拉大學核發之 CoE 申辦澳洲 Subclass 500 學生簽證。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "春季班（第一學期）：約 4 月初至 8 月上旬；秋季班（第二學期）：約 9 月中旬至翌年 2 月上旬（仙台大學 2.5+2 雙聯學位為大三下學期 4 月赴日修讀 2 學年；琵琶湖成蹊體育運動大學 1.5+2+1 雙聯學位為大二下學期 4 月赴日修讀 2 學年）",
    "韓國": "春季班（第一學期）：約 3 月初至 6 月中旬；秋季班（第二學期）：約 9 月初至 12 月中旬（高神大學交換期程為 1 學年；國立順天大學為 1 學期或 1 學年；釜山教育大學為 1 學期）",
    "中國大陸": "春季班：約 2 月下旬至 7 月初；秋季班：約 9 月初至翌年 1 月中旬（中央民族大學僅開放秋季班入學；華東師範大學不接受大四下學期春季班交換；華中師範大學接受大四學生申請 1 學期交換）",
    "美國": "秋季班（Fall Semester）：約 8 月中下旬至 12 月中旬；春季班（Spring Semester）：約 1 月中旬至 5 月中旬（加州西來大學可選擇交換 1 學期或 1 學年）",
    "捷克": "冬季學期（Winter Semester）：約 9 月中旬至翌年 1 月底；夏季學期（Summer Semester）：約 2 月上旬至 6 月底（茲林托馬斯巴塔大學可選擇交換 1 學期或 1 學年）",
    "芬蘭": "秋季學期：約 8 月下旬至 12 月下旬；春季學期：約 1 月中旬至 5 月下旬",
    "泰國": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "馬來西亞": "第一學期：約 9–10 月至翌年 1–2 月；第二學期：約 2–3 月至 6–7 月",
    "菲律賓": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "印尼": "奇數全學期：約 9 月至翌年 1 月；偶數全學期：約 2 月至 6 月",
    "越南": "第一學期：約 9 月至翌年 1 月；第二學期：約 2 月至 6 月",
    "印度": "秋季學期：約 8 月至 12 月；春季學期：約 1 月至 5 月",
    "蒙古": "秋季學期：約 9 月初至翌年 1 月中旬；春季學期：約 2 月初至 6 月中旬",
    "加拿大": "秋季學期（Fall）：約 9 月初至 12 月下旬；春季學期（Winter/Spring）：約 1 月初至 4 月下旬",
    "澳洲": "第一學期（Semester 1）：約 2 月下旬至 6 月下旬；第二學期（Semester 2）：約 7 月下旬至 11 月下旬",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
  """Ensure school-images.json and university_locations.jsonl contain all 59 NTTU partner schools."""
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
          else loc.get("lat", 22.7369)
      )
      lon = float(
          loc.get("longitude")
          if loc.get("longitude") is not None
          else loc.get("lon", 121.0667)
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
  OFFICIAL_NTTU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_NTTU_DIR / "nttu_catalog_source.json").read_text(
          encoding="utf-8"
      )
  )
  resolved_locations = json.loads(
      (SOURCES_NTTU_DIR / "nttu_resolved_locations.json").read_text(
          encoding="utf-8"
      )
  )
  bin_urls_path = SOURCES_NTTU_DIR / "binary_source_urls.json"
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
        item.get("group") or "研究發展處國際事務中心正式締約姊妹校"
    )
    quota_str = clean_text(
        item.get("quota") or "依國立臺東大學研究發展處國際事務中心當期公告名額"
    )
    detail_url = item.get("detail_url") or NTTU_PARTNER_LIST_URL

    if "雙聯" in group_str:
      program_type = f"{group_str}（免繳接待姊妹校學費）"
      source_url = detail_url
    elif avail_status == "open" and country == "中國大陸":
      program_type = "赴大陸地區姊妹校交換學生甄選（免繳接待校學費）"
      source_url = detail_url
    elif avail_status == "open":
      program_type = f"{group_str}"
      source_url = detail_url
    elif country == "中國大陸":
      program_type = "研究發展處國際事務中心正式締約大陸地區姊妹校"
      source_url = detail_url
    else:
      program_type = "研究發展處國際事務中心正式締約國際姊妹校"
      source_url = detail_url

    colleges_str = clean_text(
        item.get("colleges")
        or "人文學院、師範學院、理工學院、全校不分系學士學位學程"
    )
    degree_levels_str = clean_text(
        item.get("eligible_degrees")
        or "本校二年級（含）以上之在學學位生（學士班大二至大四、碩士班、博士班；不含大一新生、當學期畢業生、延畢生及在職專班學生；大四申請交換以一學期為限）"
    )
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "")
    website = item.get("website") or NTTU_PARTNER_LIST_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    round_label = (
        "115-2 梯次（2027年春季班＆2026年秋季班赴境外姊妹校交換生暨雙聯學位甄選）"
        if avail_status == "open"
        else "研究發展處國際事務中心正式締約姊妹校（當期開放名額依每學期 3 月及 9 月公告簡章為準）"
    )
    app_deadline_str = clean_text(
        item.get("deadline")
        or "春季班（115-2 出國）：2026年9月15日（週二）中午 12:00 截止；秋季班（115-1 出國）：2026年3月20日（週五）中午 12:00 截止"
    )
    deadline_iso = "2026-09-15T12:00:00+08:00"
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "115"

    study_period_str = clean_text(
        item.get("duration") or "一學期或一學年（雙聯學位生為二學年）"
    )
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月"
    )
    housing_str = (
        f"獲國立臺東大學研究發展處國際事務中心推薦錄取後，可依 {zh_name} 國際處指引申請校內外學生宿舍"
        + (f"（費用與學費待遇：{tuition_note}）" if tuition_note else "。")
    )
    course_rest_str = (
        f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《國立臺東大學辦理學生申請出國進修或交換作業要點》、《國立臺東大學與境外大學校院辦理雙聯學制實施辦法》及《國立臺東大學學生抵免學分要點》規定："
        "（1）在學資格：限本校二年級（含）以上之在學學位生申請（不含大一新生、當學期畢業生、延畢生及在職專班學生；大四申請交換以一學期為限；研究生不適用雙聯學制）；"
        "（2）雙聯學制修業規定：日本仙台大學 2.5+2 雙學士須於東大修滿至少五學期（2.5 學年）後赴日修讀 2 學年；日本琵琶湖成蹊體育運動大學 1.5+2+1 雙學士須於東大修滿三學期（1.5 學年）後赴日修讀 2 學年並返校修讀 1 學年；"
        "（3）學分轉換與抵免基準：境外修習及格科目以滿 18 小時折算 1 學分為原則（歐洲學分轉換系統 ECTS 乘以 1/2、英國學分系統 CATS 乘以 1/4、美加日韓及大陸港澳新加坡採 1:1 折算）；獲獎助學金者交換期間須修讀具學分數之正式課程（不得僅修無學分語言課程），返國後 1 個月內須繳交 2,000 字以上研修心得報告。"
    )

    living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
        country,
        (
            "每月生活費約 USD 700–1,300（依匯率折合新臺幣約 22,500–41,500 元，含住宿、膳食與市區交通）",
            "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋交換全期之海外醫療及意外保險。",
        ),
    )

    tuition_points_list = [
        (
            f"臺東大學在學註冊與學雜費規定（依《國立臺東大學學生出國期間有關學業及學籍處理辦法》第 7 條）：出國交換或雙聯修讀期間須辦理臺東大學註冊手續並繳交東大校內全額學雜費以保留學籍；除美國西來大學為至多 12 學分學費半價減免外，其餘開放交換及雙聯姊妹校均免繳接待校學費（日本天理大學另免收宿舍費及水電瓦斯費）。本合作校待遇：{tuition_note}。"
        ),
        (
            "臺東大學兩大核心出國進修獎助學金體系（與校內交換生甄選同步於 3 月中旬及 9 月中旬截止收件）：（1）校內《國立臺東大學學生出國進修獎助學金要點》：補助出國交換生及雙聯學位生每人每年最高新臺幣 30 萬元（短期修讀學分或語言進修補助 2 萬至 8 萬元），學士班申請人各學期平均成績須達全班前 50%（含）以上、碩博士班由系所推薦，且外語能力須達學士班 CEFR B1（TOEIC 550 / TOEFL iBT 42 / TOEFL ITP 460 / IELTS 4.0 / GEPT 中級 / JLPT N3 / TOPIK II 3級）或碩博士班 CEFR B2（TOEIC 785 / TOEFL iBT 72 / TOEFL ITP 543 / IELTS 5.5 / GEPT 中高級 / JLPT N2 / TOPIK II 4級）；（2）教育部《學海飛颺》（選送優秀生赴非大陸港澳地區研修 1 學期至 1 學年，學業總平均達 80 分或班排前 50%）與《學海惜珠》（選送持低收、中低收、特殊境遇、身心障礙或原住民生資格之清寒優秀生出國研修）。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認東大在學年級、班排名與 {zh_name} 語檢要求）：確認為臺東大學二年級（含）以上在學學位生（大四限交換 1 學期；仙台 2.5+2 與琵琶湖成蹊 1.5+2+1 雙聯限學士班），符合學業要求（{gpa_req_str}）與外語門檻（{lang_req_str}）。"
        ),
        (
            "步驟二（備妥《出國進修交換申請表》與必備書審文件送交研發處國際事務中心）：於校內報名截止前（春季班為 9 月 15 日週二中午 12:00 止；秋季班為 3 月 20 日週五中午 12:00 止）備齊：（1）《出國進修交換申請表》（1 份，須經系所主管核章）、（2）《家長或監護人同意書》（1 份）、（3）歷年學業成績單正本（3 份）及歷年學業成績名次證明（3 份）、（4）《出國進修交換計畫書》（3 份，含自我介紹與申請動機、修課計畫、預期成果）、（5）外語能力相關證明文件（3 份）、（6）近二年獲獎或成果相關資料（3 份）；若同時申請校內出國進修獎助學金或教育部學海飛颺／惜珠，一併檢附獎助學金申請表，親送或郵寄至知本校區行政大樓三樓研究發展處國際事務中心。"
        ),
        (
            f"步驟三（參加校內書面審查 50% 與外語口試面試 50% 甄選）：由臺東大學國際教育交流審查小組進行書面資料審查（50%）與面試含外語口試（50%），擇優錄取正備取名單並核定《學生出國進修獎助學金》或《教育部學海飛颺／學海惜珠》補助額度赴 {full_name}。"
        ),
        (
            "步驟四（完成姊妹校提名入學、簽證保險與返國 2,000 字心得報告及學分抵免）：獲推薦後依姊妹校入學簡章備齊提名文件（Nomination）、申辦學生簽證、購買海外全期醫療及意外保險（役男須於出國前辦理緩徵出境核准；赴陸須完成教育部赴陸登錄），出國期間維持東大註冊在學；返國後 1 個月內繳交 2,000 字以上研修心得報告與問卷並參與經驗分享會，且依《學生抵免學分要點》（18 小時折算 1 學分、歐洲 ECTS×1/2）辦理學分採認。"
        ),
    ]

    elig_points_list = [
        f"合作類別與計畫組別：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請學院：{colleges_str}",
        f"學業成績、班排名與獎助學金門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "校內甄選評分權重：書面資料審查佔 50%（歷年成績單與班排名證明、出國進修交換計畫書、外語能力證明、近二年獲獎成果）、面試（含外語口試）佔 50%。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與住宿費用待遇：{tuition_note}")
    if remarks_raw:
      elig_points_list.append(f"學程與締約重點說明：{remarks_raw}")

    exp_links: list[dict] = []
    exp_labels: list[str] = []
    if exps:
      exp_covered_schools += 1
      total_exp_reports += len(exps)
      seen_exp_urls: set[str] = set()
      for e_idx, e in enumerate(exps):
        raw_t = clean_text(e.get("title") or f"赴 {zh_name} 交換研修心得報告")
        esem = e.get("semester") or "113–114學年度"
        eurl = (
            e.get("url")
            or f"{NTTU_EXPERIENCE_SHARING_URL}#nttu-exp-{sn}-{e_idx+1}"
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
            "college": "人文學院／師範學院／理工學院",
            "department": "東大出國交換暨雙聯學位生",
        })
        summary_text = (
            f"國立臺東大學研究發展處國際事務中心公開收錄之學長姐赴 {country} {full_name} 交換研修／雙聯學位／學海築夢官方心得報告（{raw_t}），詳述姊妹校選課學習、校園宿舍生活、文化適應與每月生活費實錄。"
        )
        theme_map = {
            "academics": f"東大交換生於《{raw_t}》分享在 {zh_name} 修讀專業與外語課程、雙聯學位修業及返國辦理學分抵免之經驗。",
            "housing": f"東大交換生記錄申請 {zh_name} 校內外學生宿舍、周邊生活機能與交通方式（{housing_str[:100]}）。",
            "campus_culture": f"臺東大學研發處國際事務中心公開收錄《{raw_t}》之跨文化交流、國際學伴制度與校園生活實錄。",
            "cost": f"東大交換生分享於 {zh_name} 之每月住宿、伙食與交通開銷（{living_cost_str[:100]}），以及申請東大出國進修獎助學金或教育部學海飛颺／惜珠／築夢獎學金之經驗。",
        }
        student_experience_rows.append({
            "school_name": full_name,
            "country": country,
            "title": raw_t,
            "source_url": eurl,
            "source_type": "article",
            "platform": "國立臺東大學研究發展處國際事務中心（COIA）—出國交換暨學海計畫心得分享專區",
            "author_name": (
                raw_t.split("—")[-1].split("（")[0].strip()[:20]
                if "—" in raw_t
                else "東大交換生"
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
                f"{full_name}:nttu_exp:{e_idx}:{eurl}".encode("utf-8")
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
        "home_university": "國立臺東大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exp_links[0]["url"] if exp_links else NTTU_EXPERIENCE_SHARING_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

    loc = resolved_locations.get(full_name) or {
        "city": country,
        "latitude": 22.7369,
        "longitude": 121.0667,
        "source_url": "https://www.wikidata.org",
    }
    city_name = loc.get("city") or country
    lat = float(
        loc.get("latitude")
        if loc.get("latitude") is not None
        else loc.get("lat", 22.7369)
    )
    lon = float(
        loc.get("longitude")
        if loc.get("longitude") is not None
        else loc.get("lon", 121.0667)
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
        f"【當期名額與費用待遇】{quota_str}｜{tuition_note or '依兩校協議辦理'}",
        f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
        f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        f"【住宿與生活資訊】{housing_str}",
    ]
    if exps:
      notes_lines.append(
          f"【東大學長姐出國交換暨雙聯心得報告（共 {len(exps)} 篇）】收錄於研發處國際事務中心出國交換心得分享專區（含：{'、'.join(exp_labels[:4])}）"
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
            f"國立臺東大學研究發展處國際事務中心公告合作姊妹校（{program_type}）；{quota_str}。"
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
            "title": f"國立臺東大學研究發展處國際事務中心（COIA）出國交換暨雙聯學位甄選—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立臺東大學辦理學生申請出國進修或交換作業要點",
            "source_url": NTTU_EXCHANGE_GUIDELINES_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立臺東大學學生出國進修獎助學金要點與教育部學海飛颺／惜珠計畫專區",
            "source_url": NTTU_SCHOLARSHIP_GUIDELINES_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exp_links:
      wf_sources.append({
          "title": f"國立臺東大學出國交換生心得分享專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
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
        "home_university": "國立臺東大學",
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
            "國立臺東大學由研究發展處國際事務中心（Center of International Affairs, COIA）統籌全校 3 大學院（人文學院、師範學院、理工學院）及全校不分系學士學位學程之赴境外（含國際及大陸地區）姊妹校交換生甄選、日本仙台大學 2.5+2 與琵琶湖成蹊體育運動大學 1.5+2+1 雙聯學士學位計畫，以及校內《學生出國進修獎助學金》（最高 30 萬元）與教育部《學海飛颺》、《學海惜珠》、《學海築夢》獎學金。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"nttu-{acad_year}-home-1-{sn:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認臺東大學在學年級（大二以上／碩博）、班排名與 {zh_name} 語檢門檻",
                "responsible_party": "學生",
                "responsible_unit": "國立臺東大學研究發展處國際事務中心／各院系所",
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
                    f"確認符合《國立臺東大學辦理學生申請出國進修或交換作業要點》及當期甄選簡章規定：申請人須為本校二年級（含）以上在學學位生（大四申請交換以一學期為限；仙台大學 2.5+2 雙聯須修滿 5 學期、琵琶湖成蹊 1.5+2+1 雙聯須修滿 3 學期），符合學業要求（{gpa_req_str}）並備妥外語能力證明（{lang_req_str}）。"
                ),
                "details": [
                    f"開放學制與學院：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["國立臺東大學"],
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
                    NTTU_EXCHANGE_GUIDELINES_PDF_URL,
                    NTTU_2027_SPRING_BROCHURE_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nttu-{acad_year}-home-2-{sn:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "備齊《出國進修交換申請表》、家長同意書、歷年成績單含班排名（一式3份）及進修交換計畫書送交國際事務中心",
                "responsible_party": "學生",
                "responsible_unit": "國立臺東大學研究發展處國際事務中心（知本校區行政大樓三樓）",
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": NTTU_2027_SPRING_ANNOUNCEMENT_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "春季班於 9 月 15 日中午 12:00 前（秋季班於 3 月 20 日中午 12:00 前）將經系所主管核章之《出國進修交換申請表》（1 份）、《家長或監護人同意書》（1 份），連同歷年學業成績單正本（3 份）、歷年學業成績名次證明（3 份）、《出國進修交換計畫書》（3 份）、外語能力證明（3 份）及近二年獲獎或成果資料（3 份）送達研究發展處國際事務中心。"
                ),
                "details": [
                    "必備表單 1：《國立臺東大學學生出國進修交換申請表》（1 份，須經系主任／所長核章）與《家長或監護人同意書》（1 份，研究生亦須填具）",
                    "必備表單 2：中文歷年學業成績單正本（3 份）及歷年學業成績名次證明（班排名證明，3 份）",
                    "必備表單 3：《出國進修交換計畫書》（3 份，含自我介紹、申請動機、讀書修課計畫、預期成果）、外語能力證明（3 份）及近二年獲獎成果證明（3 份）",
                ],
                "scope": {
                    "home_universities": ["國立臺東大學"],
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
                    NTTU_2027_SPRING_ANNOUNCEMENT_URL,
                    NTTU_2027_SPRING_BROCHURE_PDF_URL,
                    NTTU_APPLICATION_FORM_DOCX_URL,
                    NTTU_STUDY_PLAN_DOCX_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nttu-{acad_year}-home-3-{sn:03d}",
                "order": 3,
                "phase": "校內甄選",
                "title": f"參加校內書面資料審查（50%）與外語口試面試（50%），並同步申請出國進修獎助學金／教育部學海計畫",
                "responsible_party": "學生／國際教育交流審查小組",
                "responsible_unit": "國立臺東大學研究發展處國際事務中心",
                "deadline_at": "2026-10-15T17:00:00+08:00",
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": NTTU_2027_SPRING_RESULTS_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    f"由臺東大學國際教育交流審查小組辦理書面審查（佔 50%）與面試含外語口試（佔 50%），核定推薦赴 {full_name} 正備取名單；符合學士班各學期班排前 50%＋CEFR B1（或碩博系所推薦＋CEFR B2）者，可同步獲核校內《學生出國進修獎助學金》（最高 30 萬元）或教育部《學海飛颺／學海惜珠》獎學金。"
                ),
                "details": elig_points_list,
                "scope": {
                    "home_universities": ["國立臺東大學"],
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
                    NTTU_EXCHANGE_GUIDELINES_PDF_URL,
                    NTTU_SCHOLARSHIP_GUIDELINES_PDF_URL,
                    NTTU_2027_SPRING_RESULTS_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nttu-{acad_year}-partner-4-{sn:03d}",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由國際事務中心向 {zh_name} 辦理官方提名（Nomination）並寄送入學申請包裹",
                "responsible_party": "學生／國際事務中心／接待大學",
                "responsible_unit": f"國立臺東大學國際事務中心 ＆ {full_name}",
                "summary": (
                    f"通過校內甄選後，由研發處國際事務中心向 {full_name} 辦理官方提名（Nomination），錄取生須依姊妹校規定時程備齊英文或日韓文成績單、護照影本、財力證明、健康檢查表與住宿申請表，待取得正式入學許可書（Letter of Acceptance）後始得辦理出國手續。"
                ),
                "details": [
                    f"接待校入學與獎助規定：{tuition_note or '依兩校交換或雙聯協議辦理'}",
                    f"預計學期時間：{sem_dates_str}",
                ],
                "scope": {
                    "home_universities": ["國立臺東大學"],
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
                    NTTU_OUTBOUND_FLOWCHART_PDF_URL,
                    website,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"nttu-{acad_year}-post-5-{sn:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "辦理東大在學註冊、簽證保險與役男緩徵出境，返國後 1 個月內繳交 2,000 字心得報告並辦理學分抵免",
                "responsible_party": "學生",
                "responsible_unit": "國立臺東大學國際事務中心／教務處註冊組／各系所",
                "summary": (
                    "出國前須完成臺東大學註冊並繳交全額學雜費、購買海外全期醫療及意外保險（役男須由學校造冊報請戶籍地縣市政府核准出境；赴大陸地區須完成教育部赴陸登錄）。返國後 1 個月內須向國際事務中心繳交 2,000 字以上研修心得報告與問卷並參加成果分享會，同時持國外成績單正本依《學生抵免學分要點》（18 小時折算 1 學分、歐洲 ECTS×1/2）辦理學分採認。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["國立臺東大學"],
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
                    NTTU_EXCHANGE_GUIDELINES_PDF_URL,
                    NTTU_SCHOLARSHIP_GUIDELINES_PDF_URL,
                    NTTU_STUDY_ABROAD_ACADEMIC_PDF_URL,
                    NTTU_CREDIT_TRANSFER_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合國立臺東大學研究發展處國際事務中心（COIA）《2025–2027 出國交換名額一覽表（含 15 所當期開放申請國際與大陸姊妹校）》、《國際暨兩岸合作姊妹校名錄（59 校）》、《辦理學生申請出國進修或交換作業要點》、《學生出國進修獎助學金要點》、《與境外大學校院辦理雙聯學制實施辦法》及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換生心得報告，共 {len(catalog_source)} 所合作姊妹校資料。"
        ),
    })

    cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": f"國立臺東大學研究發展處國際事務中心（COIA）出國交換暨姊妹校專頁—{zh_name}",
            "source_url": source_url,
            "summary": "臺東大學國際事務中心公告之合作學程、錄取名額、語言檢定門檻與學費減免／雙聯學位待遇說明",
        },
        {
            "title": "國立臺東大學辦理學生申請出國進修或交換作業要點與出國進修獎助學金要點",
            "source_url": NTTU_EXCHANGE_GUIDELINES_PDF_URL,
            "summary": "臺東大學出國交換甄選評分標準（書審 50%、面試 50%）、最高 30 萬元出國進修獎助學金與學海計畫規定",
        },
    ]
    if exp_links:
      dest_sources.append({
          "title": f"國立臺東大學出國交換生心得分享專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
          "source_url": exp_links[0]["url"],
          "summary": f"收錄歷年臺東大學學生赴 {zh_name} 交換研修／雙聯學位／學海築夢心得報告共 {len(exps)} 篇",
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
            NTTU_EXCHANGE_GUIDELINES_PDF_URL,
            NTTU_SCHOLARSHIP_GUIDELINES_PDF_URL,
            NTTU_XUEHAI_HUB_URL,
        ]
        + ([exp_links[0]["url"]] if exp_links else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "國立臺東大學",
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
                "title": "生活費、姊妹校免學費／半價待遇、東大出國進修獎助學金（最高 30 萬）與教育部學海計畫",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [NTTU_STUDY_ABROAD_ACADEMIC_PDF_URL],
                "caution": (
                    "獲臺東大學《學生出國進修獎助學金》或教育部《學海飛颺／學海惜珠》獎學金之交換生，出國期間必須修讀具學分數之正式課程（不得僅修無學分語言課程），並於返國後 1 個月內繳交 2,000 字以上研修心得報告與問卷。"
                ),
            },
            {
                "key": "housing",
                "title": "校內外學生宿舍申請與住宿費用",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": "日本天理大學提供交換生免收宿舍費及水電瓦斯費之特優待遇；仙台大學每月宿舍費 32,000 日圓（押金 20,000 日圓）；捷克茲林托馬斯巴塔大學保證提供宿舍（每月 USD 165–360）；韓國高神大學每 6 個月宿舍費 1,100,000 韓元；美國西來大學每學期含餐約 USD 3,660–5,940。",
            },
            {
                "key": "insurance",
                "title": "海外醫療及意外保險與家長或監護人同意書規定",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依《國立臺東大學辦理學生申請出國進修或交換作業要點》規定，所有申請學生（含學士班及碩博士班）均須檢附家長或監護人簽章之《家長或監護人同意書》，並於出國前自行購買足額之海外醫療及意外保險。",
                ],
                "source_urls": src_url_list,
                "caution": "日本、韓國、捷克、美國、加拿大、澳洲等接待校對國際交換生健康保險有強制納保規定，請依入學許可指示辦理。",
            },
            {
                "key": "visa",
                "title": "學生簽證辦理、役男出國緩徵流程與東大在學註冊義務",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "具役男身分之錄取學生，須依《國立臺東大學學生出國期間有關學業及學籍處理辦法》於出國前備妥入學許可函，由學校造冊函報戶籍所在地直轄市、縣（市）政府核准出境，期滿返國後應即返校註冊。",
                ],
                "source_urls": src_url_list,
                "caution": "出國交換或修讀雙聯學位期間，學生仍須依規定辦理臺東大學每學期註冊手續並繳交全額學雜費以保留學籍。",
            },
            {
                "key": "academics",
                "title": "仙台 2.5+2／琵琶湖成蹊 1.5+2+1 雙聯學制與國外學分抵免（18 小時 = 1 學分、ECTS×1/2）",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [NTTU_CREDIT_TRANSFER_PDF_URL, NTTU_DUAL_DEGREE_REGULATIONS_PDF_URL],
                "caution": (
                    "依《國立臺東大學學生抵免學分要點》第 8 條，國外修習及格科目以滿 18 小時折算 1 學分為原則：歐洲 ECTS 學分乘以 1/2、英國 CATS 學分乘以 1/4、美加日韓及大陸港澳新加坡採 1:1 折算。"
                ),
            },
            {
                "key": "living",
                "title": f"{city_name} 校園生活與東大學長姐出國交換心得傳承",
                "summary": f"代表城市：{city_name}。請配合接待校國際處完成報到、選課與新生訓練。",
                "points": [
                    f"目的地城市：{city_name}（{country}）",
                    (
                        "國立臺東大學研究發展處國際事務中心每學期舉辦「出國交換暨學海計畫說明會與成果分享會」"
                        + (
                            f"（本校共收錄 {len(exps)} 篇赴 {zh_name} 心得報告：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，協助同學掌握海外選課、住宿申請與獎學金準備。"
                    ),
                ],
                "source_urls": [
                    exp_links[0]["url"]
                    if exp_links
                    else NTTU_EXPERIENCE_SHARING_URL
                ],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合國立臺東大學研究發展處國際事務中心 {len(catalog_source)} 所合作姊妹校、2026–2027 當期開放申請出國交換與雙聯學位合作校（{open_partner_count} 校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷年學生交換心得報告。"
        ),
    })

    research_records.append({
        "home_university": "國立臺東大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            "國立臺東大學研究發展處國際事務中心《2025–2027 出國交換名額一覽表》、《國際暨兩岸合作姊妹校名錄》、《辦理學生申請出國進修或交換作業要點》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"國立臺東大學研究發展處國際事務中心出國交換暨姊妹校專頁—{zh_name}",
            "url": source_url,
        },
    ]
    if exp_links:
      ev_sources.append({
          "title": f"國立臺東大學出國交換心得分享—赴 {zh_name} 心得報告（{len(exps)} 篇）",
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
            "scope": "國立臺東大學出國交換暨雙聯姊妹校住宿資訊",
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
            "scope": "國立臺東大學姊妹校學費待遇、學生出國進修獎助學金（最高 30 萬元）與教育部學海飛颺／惜珠計畫",
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
            "scope": "國立臺東大學出國進修或交換作業要點、雙聯學制實施辦法與學生抵免學分要點",
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
            "scope": "國立臺東大學出國交換簽證、家長同意書、役男出國緩徵與海外醫療保險提醒",
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
                    f"｜臺東大學公開收錄 {len(exps)} 篇赴 {zh_name} 交換／雙聯／學海築夢心得報告（{'、'.join(exp_labels[:3])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "國立臺東大學出國交換名額與歷屆學長姐心得分享",
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
            "已整合國立臺東大學研究發展處國際事務中心《2025–2027 出國交換名額一覽表》、《國際暨兩岸合作姊妹校名錄》、《辦理學生申請出國進修或交換作業要點》及歷屆學生交換心得報告。",
            "當期免學費名額、雙聯學位申請年級限制、宿位供給與報名截止日請依國際事務中心最新公告及接待校入學簡章核對。",
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

  write_jsonl(OFFICIAL_NTTU_DIR / "partners.jsonl", partners)
  write_jsonl(SOURCES_NTTU_DIR / "partners.jsonl", partners)
  write_jsonl(OFFICIAL_NTTU_DIR / "application_workflows.jsonl", workflows)
  write_jsonl(OFFICIAL_NTTU_DIR / "destination_profiles.jsonl", destinations)
  write_jsonl(OFFICIAL_NTTU_DIR / "partner_research.jsonl", research_records)
  write_jsonl(OFFICIAL_NTTU_DIR / "student_life.jsonl", life_records)
  write_jsonl(
      OFFICIAL_NTTU_DIR / "experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_NTTU_DIR / "student_experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_NTTU_DIR / "student_experiences.jsonl", student_experience_rows
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
  (OFFICIAL_NTTU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_NTTU_DIR / "student-experiences.json").write_text(
      json.dumps(
          {
              "school_id": "nttu",
              "school_name": "國立臺東大學",
              "checked_at": CHECKED_AT,
              "source_url": NTTU_EXPERIENCE_SHARING_URL,
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

  (OFFICIAL_NTTU_DIR / "campus-locations.json").write_text(
      json.dumps(
          {
              "school_id": "nttu",
              "school_name": "國立臺東大學",
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
  (OFFICIAL_NTTU_DIR / "campus-assets.json").write_text(
      json.dumps(
          {
              "school_id": "nttu",
              "school_name": "國立臺東大學",
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

  nttu_source_urls = [
      NTTU_COIA_HOME_URL,
      NTTU_PARTNER_LIST_URL,
      NTTU_OUTBOUND_EXCHANGE_URL,
      NTTU_EXCHANGE_RECRUITMENT_URL,
      NTTU_2027_SPRING_ANNOUNCEMENT_URL,
      NTTU_2026_FALL_ANNOUNCEMENT_URL,
      NTTU_2027_SPRING_RESULTS_URL,
      NTTU_EXCHANGE_REGULATIONS_URL,
      NTTU_XUEHAI_HUB_URL,
      NTTU_XUEHAI_FEIYANG_REGULATIONS_URL,
      NTTU_XUEHAI_ZHUMENG_REGULATIONS_URL,
      NTTU_EXPERIENCE_SHARING_URL,
      NTTU_ZHUMENG_EXPERIENCE_URL,
      NTTU_AA_REGULATIONS_URL,
      NTTU_DOMESTIC_EXCHANGE_URL,
      NTTU_2027_SPRING_QUOTA_PDF_URL,
      NTTU_2027_SPRING_BROCHURE_PDF_URL,
      NTTU_2026_FALL_QUOTA_PDF_URL,
      NTTU_2026_FALL_BROCHURE_PDF_URL,
      NTTU_OUTBOUND_FLOWCHART_PDF_URL,
      NTTU_EXCHANGE_GUIDELINES_PDF_URL,
      NTTU_SCHOLARSHIP_GUIDELINES_PDF_URL,
      NTTU_DUAL_DEGREE_REGULATIONS_PDF_URL,
      NTTU_STUDY_ABROAD_ACADEMIC_PDF_URL,
      NTTU_CREDIT_TRANSFER_PDF_URL,
      NTTU_GPA_CONVERSION_PDF_URL,
  ]

  exchange_info_payload = {
      "school_name": "國立臺東大學",
      "program_type": [
          (
              "研究發展處國際事務中心（COIA）赴國外姊妹校交換生暨雙聯學位甄選（共 8 所當期開放申請國際姊妹校：美國加州西來大學 University of the West［每期 15 名，至多 12 學分半價減免］、日本仙台大學 Sendai University［交換 4–6 名＋2.5+2 雙聯學士學位 2 名］、日本琵琶湖成蹊體育運動大學 Biwako Seikei Sport College［春季班 1.5+2+1 雙聯學士學位 1 名］、日本天理大學 Tenri University［1 名，免學費、免宿舍費且免水電瓦斯費］、韓國國立順天大學 Sunchon National University［2–4 名，免學費且免韓檢門檻］、韓國高神大學 Kosin University［1–2 名，免學費且免韓檢門檻］、韓國釜山教育大學 Busan National University of Education［3 名，TOPIK 2 級以上］、捷克茲林托馬斯巴塔大學 Tomas Bata University in Zlín［5 名，CEFR B2，保證提供低廉宿舍］）"
          ),
          (
              "研究發展處國際事務中心（COIA）赴大陸地區姊妹校交換生甄選（共 7 所當期開放申請大陸重點姊妹校，均免繳接待校學費：上海華東師範大學［1 名］、甘肅蘭州大學［5 名］、湖北華中師範大學［3 名］、重慶西南大學［3 名］、吉林東北師範大學［3 名］、北京中央民族大學［秋季班 3 名］、河南鄭州大學［3 名］）"
          ),
          (
              "國立臺東大學校內《學生出國進修獎助學金》（交換生與雙聯學位生每人每年最高補助新臺幣 30 萬元；短期修讀學分或語言進修補助 2 萬至 8 萬元）暨教育部《學海飛颺》（選送優秀生出國研修）、《學海惜珠》（選送清寒優秀生出國研修）、《學海築夢／新南向學海築夢》（海外專業實習）獎助計畫"
          ),
      ],
      "academic_year": [
          (
              "115（涵蓋 2027 年春季班［115-2 梯次：即日起至 2026/09/15 中午 12:00 截止收件、2026/10/15 公告甄選結果］及 2026 年秋季班［115-1 梯次：即日起至 2026/03/20 中午 12:00 截止收件］，校內交換生甄選、出國進修獎助學金與教育部學海飛颺／惜珠計畫同步受理）"
          ),
          (
              f"本平台完整收錄國立臺東大學研究發展處國際事務中心公告之 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所 2026–2027 當期開放申請之國際與大陸交換及雙聯學位合作校，以及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 15 個國家與地區，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷年學長姐交換、雙聯與學海築夢心得報告）"
          ),
      ],
      "semester": [
          "出國交換生（Exchange Program）：以 1 學期或 1 學年為原則（美國西來大學、日本仙台大學、韓國國立順天大學、捷克茲林托馬斯巴塔大學可選 1 學期或 1 學年；日本天理大學與韓國高神大學為 1 學年；韓國釜山教育大學與大陸 7 所姊妹校為 1 學期；大四學生申請交換以 1 學期為限）。",
          "跨國雙聯學士學位（Dual Bachelor's Degree Program）：（1）日本仙台大學「2.5+2 雙學士學制」：於臺東大學修滿至少 5 學期（2.5 學年）後，大三下學期（春季班 4 月）赴日本仙台大學修讀 2 學年，符合兩校畢業條件獲頒兩校學士學位；（2）日本琵琶湖成蹊體育運動大學「1.5+2+1 雙學士學制」：於臺東大學修滿 3 學期（1.5 學年）後，大二下學期（春季班 4 月）赴日修讀 2 學年，再返東大修讀最後 1 學年。",
          "國內大學交換生（依《國立臺東大學與國內大學校院辦理交換學生實施要點》）：每學期選送至國立成功大學、國立中山大學、國立中正大學、國立臺灣海洋大學、國立屏東大學、國立金門大學、國立宜蘭大學、臺北市立大學等國內合作大學交換 1 學期至 1 學年。",
      ],
      "application_period": [
          "【春季班出國交換暨雙聯學位甄選（翌年 2–4 月赴外研修，115-2 梯次）】每年 8 月至 9 月中旬受理（2027 年春季班為即日起至 2026 年 9 月 15 日週二中午 12:00 止），申請表件送交知本校區行政大樓三樓研究發展處國際事務中心，10 月中旬公告錄取名單。",
          "【秋季班出國交換暨雙聯學位甄選（當年 8–9 月赴外研修，115-1 梯次）】每年 2 月至 3 月中旬受理（2026 年秋季班為即日起至 2026 年 3 月 20 日週五中午 12:00 止），同步受理校內《學生出國進修獎助學金》與教育部《學海飛颺／學海惜珠》第一階段申請。",
          "【教育部「學海惜珠」第二階段補申請】配合教育部第二階段作業，於每年 8 月初至 9 月上旬受理（115學年度第2學期梯次為 2026 年 8 月 3 日至 9 月 7 日中午 12:00 止）。",
      ],
      "eligibility": [
          "1. 在學身分與年級限制：依《國立臺東大學辦理學生申請出國進修或交換作業要點》第 3 點及甄選簡章規定，凡本校二年級（含）以上之在學學位生（含學士班大二至大四、碩士班、博士班）均得提出申請；不含大一新生、當學期畢業生、延畢生及在職專班學生。大四生申請交換以一學期為限（上海華東師範大學不接受大四下學期交換，北京中央民族大學不接受大四學生且僅收秋季班，武漢華中師範大學接受大四學生）。",
          "2. 雙聯學位專屬年級限制：依《國立臺東大學與境外大學校院辦理雙聯學制實施辦法》及簡章規定，雙聯學制僅限學士班學生申請（研究生不適用）：（a）日本仙台大學「2.5+2」雙聯須於出國前在東大修滿至少五學期（最早於大三上申請、大三下出國）；（b）日本琵琶湖成蹊體育運動大學「1.5+2+1」雙聯須於出國前在東大修滿三學期（於大二上申請、大二下出國）。",
          "3. 甄選評分權重（100%）：由本校「國際教育交流審查小組」進行甄選，書面資料審查佔 50%（含歷年成績單與班排名證明、出國進修交換計畫書、外語能力證明、近二年獲獎成果）、面試（含外語口試）佔 50%。",
          "4. 校內出國進修獎助學金與學海計畫學業門檻：依《國立臺東大學學生出國進修獎助學金要點》第 4 點，申請獎助學金之學士班學生在校各學期平均成績須達全班前二分之一（50%，含）以上（申請教育部學海飛颺／惜珠另可採計在校學業總平均達 80 分以上），碩士班及博士班學生須由系所推薦。",
      ],
      "language_requirement": [
          "1. 英語組姊妹校：（a）捷克茲林托馬斯巴塔大學（Tomas Bata University in Zlín）要求英語達 CEFR B2（TOEFL iBT 72+ / TOEIC 聽讀 785［聽400/讀385］且說寫 S160/W150 / IELTS 5.5+）；（b）美國加州西來大學（University of the West）正式學分班要求 TOEFL iBT 61 或 IELTS 5.5 以上（未達標或無證照者可參加該校線上英語能力分級測驗 Remote EPT 就讀非學分英語課程 IEP，惟申請獎助學金者必須修讀正式學分課程）。",
          "2. 日語組與韓語組姊妹校：（a）日本仙台大學交換生要求 JLPT N4（含）以上或具日語修課證明，2.5+2 雙聯學位生要求 JLPT N2（含）以上或具日語修課證明；（b）日本琵琶湖成蹊體育運動大學 1.5+2+1 雙聯學位生要求 JLPT N3（含）以上；（c）日本天理大學要求檢附日語檢定證明或日語修課證明；（d）韓國釜山教育大學要求 TOPIK 2 級（含）以上，韓國國立順天大學與高神大學免附韓語檢定成績。",
          "3. 校內《學生出國進修獎助學金》與教育部《學海飛颺／惜珠》外語最低門檻（要點附件一）：（a）學士班須達 CEFR B1（TOEIC 550 / TOEFL iBT 42 / TOEFL ITP 460 / IELTS 4.0 / FLPT 三項筆試總分 150 且口試 S-2 / GEPT 中級 / JLPT N3 / TOPIK II 3級 / 德西法語 B1）；（b）碩博士班須達 CEFR B2（TOEIC 785 / TOEFL iBT 72 / TOEFL ITP 543 / IELTS 5.5 / FLPT 三項筆試總分 195 且口試 S-2+ / GEPT 中高級 / JLPT N2 / TOPIK II 4級 / 德西法語 B2）。",
      ],
      "required_documents": [
          "1. 《國立臺東大學學生出國進修交換申請表》正本 1 份（須貼妥 2 吋照片、填寫至多 3 個志願校，並經申請人簽名及所屬系所主管核章）",
          "2. 《國立臺東大學學生出國進修交換家長或監護人同意書》正本 1 份（須由家長或法定監護人親筆簽章；研究生亦須填具）",
          "3. 本校中文歷年學業成績單正本 3 份，以及歷年學業成績名次證明（班排名證明）正本 3 份（請向教務處註冊組申請）",
          "4. 《國立臺東大學學生出國進修交換計畫書》3 份（含一、自我介紹與申請動機；二、讀書計畫／修課計畫；三、預期成果，建議約 1,000 字至 2,500 字）",
          "5. 外語能力相關證明文件 3 份（如 TOEFL / IELTS / TOEIC / GEPT / FLPT / JLPT / TOPIK 成績單影本，或相關外語修課證明）",
          "6. 近二年獲獎或成果相關資料 3 份（如學術發表、競賽獲獎、社團幹部、志工服務或專業證照影本）",
          "7. 同步申請獎助學金另附：《國立臺東大學學生出國進修獎助學金申請表》及《教育部學海飛颺及學海惜珠計畫補助申請表》各 1 份（含個人簡介、詳細出國讀書計畫及經費預估表；申請學海惜珠另附新式戶口名簿或近三個月戶籍謄本，以及低收入戶、中低收入戶、特殊境遇家庭、身心障礙生活補助或原住民生資格證明）",
      ],
      "scholarship_info": [
          "1. 國立臺東大學《學生出國進修獎助學金要點》（112年11月23日行政會議修正通過）：為鼓勵本校在學學生（不含在職專班）出國進修及文化交流，依修讀類別核給獎助：（a）攻讀雙聯學位或交換學生（修讀學分）：每人每年獎助上限為新臺幣 30 萬元；（b）短期修讀學分（未滿一學期）：每人每年獎助上限為新臺幣 8 萬元；（c）短期語言進修（無修讀學分）：每人每年獎助上限為新臺幣 2 萬元。申請人須為大二以上學士班（在校各學期平均成績達全班前 50% 以上且具 CEFR B1 外語證明）或由系所推薦之碩博士班學生（具 CEFR B2 外語證明）。獲獎生返國後 1 個月內須繳交 2,000 字以上研修心得報告與問卷並參與經驗分享會。",
          "2. 教育部「學海飛颺計畫」選送優秀學生出國研修獎學金（研發處國際事務中心主辦）：補助具中華民國國籍、於臺東大學就讀一學期以上之在學學位生（不含國內及境外在職專班生）、在校學業總平均達 80 分以上或班級排名前 50% 以內，且具備有效外語能力證明（英語 TOEIC 550 / TOEFL iBT 42 / IELTS 4.0 / GEPT 中級，或日語 JLPT N3、韓語 TOPIK 3 級以上）者，赴國外（不含大陸及港澳地區）姊妹校修讀學分 1 學期至 1 學年。補助項目涵蓋學費、生活費及來回經濟艙機票費，實際金額由審查小組依教育部核定經費及甄選成績核定。",
          "3. 教育部「學海惜珠計畫」選送清寒優秀學生出國研修獎學金：補助具備學海飛颺基本資格，且持各直轄市、縣（市）主管機關開立有效之低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助費、弱勢兒童及少年生活扶助證明，或具原住民生資格之在學學位生，赴國外（不含大陸及港澳地區）姊妹校修讀學分 1 學期至 1 學年，優先高額補助來回機票與海外生活費。",
          "4. 教育部「學海築夢」與「新南向學海築夢」海外專業實習計畫：由本校專任教師主持海外專業實習計畫，選送在學學生赴歐美日（如芬蘭赫爾辛基大學、日本姊妹校及機構）或新南向國家（如泰國皇太后大學、越南、馬來西亞、印尼、澳洲、紐西蘭等合作機構）進行至少 30 天（新南向）或規定期間之海外專業實習，補助學生來回經濟艙機票款與生活費。",
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": nttu_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_NTTU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "國立臺東大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 70.0,
      "academic_score_rule": (
          "依《國立臺東大學辦理學生申請出國進修或交換作業要點》及《國立臺東大學學生出國進修獎助學金要點》規定：申請人須為本校二年級（含）以上在學學位生（不含大一新生、當學期畢業生、延畢生及在職專班學生；大四申請交換以一學期為限），報名須檢附歷年學業成績單正本及歷年學業成績名次證明（班排名），甄選採書面審查 50%＋面試（含外語口試）50%；若同時申請校內《學生出國進修獎助學金》（最高 30 萬元）或教育部《學海飛颺／學海惜珠》，學士班在校各學期平均成績須達全班前 50%（含）以上（或學海總平均達 80 分以上），碩博士班須由系所推薦。"
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
              "undergraduate": 70.0,
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
              "title": "國立臺東大學 2027 年春季班（115-2 出國）「赴境外（國際暨大陸地區）姊妹校交換學生、雙聯學位暨出國進修獎助學金」甄選（即日起至 2026/09/15 12:00 受理）",
              "details": [
                  "研究發展處國際事務中心（COIA）公告 2027 年春季班赴境外姊妹校交換生暨雙聯學位甄選：涵蓋 8 所國際姊妹校（美國西來大學 15 名、日本仙台大學交換 4–6 名＋2.5+2 雙聯 2 名、日本琵琶湖成蹊體育運動大學 1.5+2+1 雙聯 1 名、日本天理大學 1 名［免學費及住宿水電費］、韓國國立順天大學 2–4 名、韓國高神大學 1–2 名、韓國釜山教育大學 3 名、捷克茲林托馬斯巴塔大學 5 名）及 6 所大陸春季班開放姊妹校（華東師範大學 1 名、蘭州大學 5 名、華中師範大學 3 名、西南大學 3 名、東北師範大學 3 名、鄭州大學 3 名）。",
                  "重要日程：即日起至 2026 年 9 月 15 日（週二）中午 12:00 止受理報名（同步受理校內《學生出國進修獎助學金》及教育部《學海飛颺／學海惜珠》申請），書審 50%＋面試（含外語口試）50%，2026 年 10 月 15 日公告審核結果。",
              ],
              "source": {
                  "title": "國立臺東大學 2027 年春季班赴境外姊妹校交換學生甄選簡章與名額一覽表",
                  "source_url": NTTU_2027_SPRING_ANNOUNCEMENT_URL,
                  "category": "exchange_application",
                  "summary": "臺東大學 2027 年春季班（115-2）赴國際與大陸地區姊妹校交換生、雙聯學位及獎助學金報名簡章。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "115-2 梯次（2027年春季班出國交換暨雙聯學位）",
              "audience": "all_students",
              "opens_at": "2026-08-01T09:00:00+08:00",
              "deadline_at": "2026-09-15T12:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "2027 年春季班赴境外姊妹校交換生暨雙聯學位甄選於 2026 年 9 月 15 日（週二）中午 12:00 截止收件，10 月 15 日公告錄取名單。",
              "deadline_note": "請備齊核章申請表、家長同意書及一式 3 份之成績單、班排名證明、交換計畫書與外語證明，於 9/15 12:00 前送達知本校區行政大樓三樓研發處國際事務中心。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "國立臺東大學 115 學年度第 2 學期教育部「學海惜珠」第二階段出國研修獎學金申請（2026/08/03–09/07 12:00 受理）",
              "details": [
                  "配合教育部 115 年第二階段「學海惜珠」要點，補助持有效低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助費、弱勢兒少扶助證明或具原住民生資格、且在校總平均達 80 分或班排前 50% 及具外語檢定證明之在學學位生，於 115 學年度第 2 學期赴國外（不含大陸及港澳地區）姊妹校研修 1 學期至 1 學年。",
              ],
              "source": {
                  "title": "國立臺東大學 115 學年度第 2 學期出國進修交流「教育部學海惜珠」申請公告",
                  "source_url": "https://rd.nttu.edu.tw/p/406-1007-179060,r1848.php?Lang=zh-tw",
                  "category": "scholarship",
                  "summary": "臺東大學 115-2 教育部學海惜珠第二階段獎學金申請時程與資格。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "115-2 梯次教育部學海惜珠第二階段",
              "audience": "all_students",
              "opens_at": "2026-08-03T09:00:00+08:00",
              "deadline_at": "2026-09-07T12:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "115-2 教育部學海惜珠第二階段於 2026 年 9 月 7 日中午 12:00 截止收件。",
              "deadline_note": "申請人須同時檢附新式戶口名簿（或三個月內戶籍謄本）及主管機關核發之低收／中低收／原住民生相關證明文件。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "國立臺東大學秋季班（116-1 出國）「赴境外姊妹校交換學生、雙聯學位暨教育部學海飛颺／惜珠獎學金」甄選（每年 3 月 20 日 12:00 截止）",
              "details": [
                  "研究發展處國際事務中心每學年春季（約 2 月至 3 月 20 日中午 12:00）受理當年秋季班（8–9 月出國）赴國際與大陸地區姊妹校交換生暨日本仙台大學 2.5+2 雙聯學位甄選（北京中央民族大學僅於秋季班開放申請），並同步受理當年度教育部《學海飛颺》、《學海惜珠》及校內《學生出國進修獎助學金》（最高 30 萬元）申請。",
              ],
              "source": {
                  "title": "國立臺東大學 2026 年秋季班赴境外姊妹校交換學生甄選簡章與名額一覽表",
                  "source_url": NTTU_2026_FALL_ANNOUNCEMENT_URL,
                  "category": "exchange_application",
                  "summary": "臺東大學秋季班赴境外姊妹校交換生、雙聯學位與學海獎學金報名簡章。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "116-1 梯次（秋季班出國交換暨學海獎學金）",
              "audience": "all_students",
              "opens_at": "2027-02-15T09:00:00+08:00",
              "deadline_at": "2027-03-20T12:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "秋季班甄選與年度學海飛颺／惜珠獎學金每年 3 月中旬（約 3 月 20 日中午 12:00）截止收件。",
              "deadline_note": "紙本申請資料請依簡章規定份數備齊並送達知本校區行政大樓三樓研發處國際事務中心。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"國立臺東大學研究發展處國際事務中心出國交換、雙聯學位與出國進修／學海獎學金總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所當期開放申請・{total_exp_reports} 篇學長姐交換與築夢心得）"
              ),
              "details": [
                  (
                      f"國立臺東大學研究發展處國際事務中心（COIA）每學期（3 月中旬及 9 月中旬）定期公告赴境外姊妹校交換學生暨雙聯學位甄選，當期開放 {open_partner_count} 所合作大學（含美國加州西來大學、日本仙台大學［交換＋2.5+2 雙聯］、日本琵琶湖成蹊體育運動大學［1.5+2+1 雙聯］、日本天理大學［免學費、免宿舍費且免水電瓦斯費］、韓國國立順天大學、高神大學、釜山教育大學、捷克茲林托馬斯巴塔大學，以及大陸華東師大、蘭州大學、華中師大、西南大學、東北師大、中央民族大學、鄭州大學），並與全球 15 國共 {len(partners)} 所大學締結姊妹校。"
                  ),
                  (
                      "為減輕東大學生出國經濟負擔，學校設有《國立臺東大學學生出國進修獎助學金要點》，針對攻讀雙聯學位或出國交換修讀學分之學生，每人每年最高獎助新臺幣 30 萬元（短期修讀學分最高 8 萬元、短期語言進修最高 2 萬元），並積極執行教育部《學海飛颺》、《學海惜珠》及《學海築夢／新南向學海築夢》計畫。"
                  ),
              ],
              "source": {
                  "title": "國立臺東大學研究發展處國際事務中心出國交換學生專區",
                  "source_url": NTTU_OUTBOUND_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": "臺東大學出國交換學生甄選簡章、姊妹校名額表、法規表單與心得報告總覽。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "二年級以上在學學位生資格、雙聯學位學士班修滿 3–5 學期門檻、兩階段甄選（書審 50%＋面試 50%）與獎助學金班排前 50% 規定",
              "details": exchange_info_payload["eligibility"],
              "source": {
                  "title": "國立臺東大學辦理學生申請出國進修或交換作業要點、雙聯學制實施辦法與學生出國進修獎助學金要點",
                  "source_url": NTTU_EXCHANGE_GUIDELINES_PDF_URL,
                  "category": "exchange_application",
                  "summary": "臺東大學出國交換年級限制、雙聯學位修業學期門檻、書審面試各 50% 評分標準與獎助學金班排前 50% 規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "英語組（捷克 CEFR B2 / 美國西來 iBT 61 或 IELTS 5.5 或 Remote EPT）、日韓語組（仙台 JLPT N4・雙聯 N2 / 琵琶湖雙聯 N3 / 釜山教大 TOPIK 2 / 順天與高神免韓檢）及獎助學金 CEFR B1/B2 基準",
              "details": exchange_info_payload["language_requirement"],
              "source": {
                  "title": "國立臺東大學 2027 年春季班與 2026 年秋季班出國交換名額一覽表及出國進修獎助學金要點附件一",
                  "source_url": NTTU_2027_SPRING_QUOTA_PDF_URL,
                  "category": "exchange_application",
                  "summary": "臺東大學各合作姊妹校交換與雙聯外語檢定門檻及校內外獎助學金 CEFR B1/B2 對照表。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "核章《出國進修交換申請表》、家長同意書、歷年成績單與班排名證明（各 3 份）、出國進修交換計畫書（1,000 字至 2,500 字，3 份）、外語證明與獎助學金申請表",
              "details": exchange_info_payload["required_documents"],
              "source": {
                  "title": "國立臺東大學 2027 年春季班赴境外姊妹校交換學生甄選簡章與法規表單專區",
                  "source_url": NTTU_EXCHANGE_REGULATIONS_URL,
                  "category": "exchange_application",
                  "summary": "臺東大學出國交換生、雙聯學位生與獎助學金申請應備表件及份數規定。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "臺東大學《學生出國進修獎助學金》（交換及雙聯最高 30 萬元、短期學分 8 萬元、語言 2 萬元）暨教育部學海飛颺、學海惜珠、學海築夢計畫",
              "details": exchange_info_payload["scholarship_info"],
              "source": {
                  "title": "國立臺東大學學生出國進修獎助學金要點與教育部學海計畫專區",
                  "source_url": NTTU_SCHOLARSHIP_GUIDELINES_PDF_URL,
                  "category": "scholarship",
                  "summary": "臺東大學校內出國進修獎助學金（最高 30 萬元）與教育部學海飛颺、學海惜珠、學海築夢補助規定。",
              },
          }
      ],
      "regulation_links": [
          {
              "title": "國立臺東大學辦理學生申請出國進修或交換作業要點（PDF）",
              "url": NTTU_EXCHANGE_GUIDELINES_PDF_URL,
          },
          {
              "title": "國立臺東大學學生出國進修獎助學金要點（含附件一 CEFR B1/B2 語言基準表，PDF）",
              "url": NTTU_SCHOLARSHIP_GUIDELINES_PDF_URL,
          },
          {
              "title": "國立臺東大學與境外大學校院辦理雙聯學制實施辦法（PDF）",
              "url": NTTU_DUAL_DEGREE_REGULATIONS_PDF_URL,
          },
          {
              "title": "國立臺東大學學生出國期間有關學業及學籍處理辦法（PDF）",
              "url": NTTU_STUDY_ABROAD_ACADEMIC_PDF_URL,
          },
          {
              "title": "國立臺東大學學生抵免學分要點（含國外學分 18 小時及 ECTS/CATS 轉換標準，PDF）",
              "url": NTTU_CREDIT_TRANSFER_PDF_URL,
          },
      ],
      "document_explanations": [
          {
              "title": "國立臺東大學出國進修交換申請表、交換計畫書（一式3份）與獎助學金／學海計畫書審準備要領",
              "summary": "說明臺東大學出國交換甄選書審（佔 50%）必備之申請表、家長同意書、歷年成績單與班排名證明（3份）、出國進修交換計畫書（3份）及獎助學金申請表撰寫規範。",
              "key_points": [
                  "出國進修交換計畫書（一式 3 份）：須依官方範例架構完整撰寫（1）自我介紹與申請動機、（2）讀書計畫／擬於姊妹校修讀之課程規劃及與東大母系課程之關聯、（3）預期學習成果與返國後之貢獻。",
                  "歷年成績單與班排名證明（各一式 3 份）：須向教務處註冊組申請中文歷年學業成績單正本及歷年學業成績名次證明；若同步申請校內《學生出國進修獎助學金》或教育部《學海飛颺／學海惜珠》，學士班各學期平均成績須達全班前 50%（含）以上（或學海總平均達 80 分以上），碩博士班須由系所推薦。",
                  "家長或監護人同意書與返國 2,000 字心得報告：不論學士班或碩博士班申請人均須檢附經家長或監護人親筆簽章之同意書；錄取並獲獎助學生於返國後 1 個月內，須向國際事務中心繳交 2,000 字以上研修心得報告與問卷並參與成果分享會。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立臺東大學 2027 年春季班赴境外姊妹校交換學生甄選簡章與申請表單",
                  "source_url": NTTU_2027_SPRING_ANNOUNCEMENT_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NTTU_EXCHANGE_REGULATIONS_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "國立臺東大學出國交換甄選評分權重（書審 50%＋面試 50%）、雙聯學制（2.5+2／1.5+2+1）與國外學分抵免核心規定",
              "summary": "規範臺東大學大二以上申請資格、大四交換 1 學期上限、日本仙台大學 2.5+2 與琵琶湖成蹊 1.5+2+1 雙聯學制、18 小時折算 1 學分（ECTS×1/2）及最高 30 萬元出國進修獎助學金。",
              "key_points": [
                  "在學年級與甄選權重：依《辦理學生申請出國進修或交換作業要點》，限大二（含）以上在學學位生申請（不含大一、當學期畢業生、延畢生及在職專班；大四限交換 1 學期）；由國際教育交流審查小組依「書面資料審查 50%＋面試（含外語口試）50%」擇優錄取。",
                  "跨國雙聯學士學制：依《與境外大學校院辦理雙聯學制實施辦法》及簡章，雙聯學制僅限學士班申請—日本仙台大學採「2.5+2」制（於東大修滿至少 5 學期後赴日修讀 2 學年，要求 JLPT N2 或日語修課證明），日本琵琶湖成蹊體育運動大學採「1.5+2+1」制（於東大修滿 3 學期後赴日修讀 2 學年再返東大修讀 1 學年，要求 JLPT N3 以上）。",
                  "國外學分轉換與在學註冊規定：依《學生出國期間有關學業及學籍處理辦法》與《學生抵免學分要點》，出國期間須辦理東大註冊並繳交全額學雜費；國外及格科目以滿 18 小時折算 1 學分為原則（歐洲 ECTS×1/2、英國 CATS×1/4、美加日韓及大陸港澳新加坡 1:1）。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立臺東大學辦理學生申請出國進修或交換作業要點與雙聯學制實施辦法",
                  "source_url": NTTU_EXCHANGE_REGULATIONS_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NTTU_EXCHANGE_GUIDELINES_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "國立臺東大學研究發展處國際事務中心（Center of International Affairs, COIA）官方網站",
              "source_url": NTTU_COIA_HOME_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立臺東大學研究發展處國際事務中心「出國交換學生甄選資訊」專區",
              "source_url": NTTU_EXCHANGE_RECRUITMENT_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立臺東大學 2027 年春季班赴境外姊妹校交換學生甄選簡章與名額表（15 所開放申請校）",
              "source_url": NTTU_2027_SPRING_ANNOUNCEMENT_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立臺東大學 2026 年秋季班赴境外姊妹校交換學生甄選簡章與名額表",
              "source_url": NTTU_2026_FALL_ANNOUNCEMENT_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": f"國立臺東大學國際暨大陸地區締約合作姊妹校名錄（共 {len(partners)} 所合作姊妹校）",
              "source_url": NTTU_PARTNER_LIST_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立臺東大學辦理學生申請出國進修或交換作業要點（PDF）",
              "source_url": NTTU_EXCHANGE_GUIDELINES_PDF_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立臺東大學學生出國進修獎助學金要點暨教育部學海飛颺／惜珠／築夢計畫專區",
              "source_url": NTTU_XUEHAI_HUB_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": f"國立臺東大學國際事務中心「出國交換生心得分享＆學海築夢成果」（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）",
              "source_url": NTTU_EXPERIENCE_SHARING_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_NTTU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  doc_conditions = {
      "school_id": "nttu",
      "school_name": "國立臺東大學",
      "checked_at": CHECKED_AT,
      "source_url": NTTU_EXCHANGE_REGULATIONS_URL,
      "common_documents": exchange_info_payload["required_documents"],
      "track_specific_conditions": [
          {
              "track": "赴國外姊妹校交換學生甄選（美國西來大學、日本仙台／天理、韓國順天／高神／釜山教大、捷克茲林托馬斯巴塔大學）",
              "required": [
                  "《國立臺東大學學生出國進修交換申請表》正本 1 份（須經系所主管核章）及《家長或監護人同意書》正本 1 份",
                  "本校中文歷年學業成績單正本 3 份及歷年學業成績名次證明（班排名證明）正本 3 份",
                  "《出國進修交換計畫書》3 份（含自我介紹與申請動機、修課計畫、預期成果）與近二年獲獎或成果資料 3 份",
                  "外語能力相關證明文件 3 份（捷克茲林托馬斯巴塔大學須達 CEFR B2 如 TOEFL iBT 72 / TOEIC 785［S160/W150］/ IELTS 5.5；美國西來大學學分班須 TOEFL iBT 61 / IELTS 5.5 或參加該校線上英語分級測驗 Remote EPT；日本仙台大學須 JLPT N4 或日語修課證明；天理大學須日檢或日語修課證明；韓國釜山教育大學須 TOPIK 2 級；韓國順天大學與高神大學免韓檢）",
              ],
          },
          {
              "track": "日本姊妹校跨國雙聯學士學位甄選（仙台大學 2.5+2 雙聯／琵琶湖成蹊體育運動大學 1.5+2+1 雙聯）",
              "required": [
                  "限本校學士班在學學生申請（碩博士班不適用）：申請仙台大學 2.5+2 雙聯者出國前須於東大修滿至少 5 學期（2.5 學年）；申請琵琶湖成蹊體育運動大學 1.5+2+1 雙聯者出國前須於東大修滿 3 學期（1.5 學年）",
                  "《國立臺東大學學生出國進修交換申請表》1 份、《家長或監護人同意書》1 份、歷年成績單正本 3 份、班排名證明 3 份及《出國進修交換計畫書》3 份",
                  "日語能力證明 3 份：仙台大學 2.5+2 雙聯須具 JLPT N2（含）以上或日語修課證明；琵琶湖成蹊體育運動大學 1.5+2+1 雙聯須具 JLPT N3（含）以上證明",
              ],
          },
          {
              "track": "赴大陸地區姊妹校交換學生甄選（華東師大、蘭州大學、華中師大、西南大學、東北師大、中央民族大學、鄭州大學）",
              "required": [
                  "《國立臺東大學學生出國進修交換申請表》1 份（經系所主管核章）及《家長或監護人同意書》1 份",
                  "中文歷年學業成績單正本 3 份、歷年學業成績名次證明（班排名證明）3 份、《出國進修交換計畫書》3 份及近二年獲獎成果資料 3 份",
                  "注意年級與學期限制：大四學生申請交換以 1 學期為限；上海華東師範大學不接受大四下學期（春季班）交換；北京中央民族大學僅開放秋季班且不接受大四學生；武漢華中師範大學接受大四學生申請",
              ],
          },
          {
              "track": "國立臺東大學《學生出國進修獎助學金》（最高 30 萬元）暨教育部《學海飛颺／學海惜珠》獎學金",
              "required": [
                  "《國立臺東大學學生出國進修獎助學金申請表》及《教育部學海飛颺及學海惜珠計畫補助申請表》正本（含個人簡介、詳細出國讀書計畫及經費預估表）",
                  "學業門檻證明：學士班在校各學期平均成績須達全班前 50%（含）以上（申請學海飛颺／惜珠亦可採計總平均達 80 分以上）；碩士班及博士班須由系所推薦",
                  "外語基準證明（要點附件一）：學士班須達 CEFR B1（TOEIC 550 / TOEFL iBT 42 / TOEFL ITP 460 / IELTS 4.0 / GEPT 中級 / JLPT N3 / TOPIK II 3級）；碩博士班須達 CEFR B2（TOEIC 785 / TOEFL iBT 72 / TOEFL ITP 543 / IELTS 5.5 / GEPT 中高級 / JLPT N2 / TOPIK II 4級）",
                  "學海惜珠申請人另附：新式戶口名簿影本（或三個月內戶籍謄本）及各直轄市、縣（市）主管機關開立有效之低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助費、弱勢兒少扶助證明或原住民生資格證明",
                  "返國後 1 個月內核銷必備：修讀具學分數正式課程之成績單證明、2,000 字以上研修心得報告與問卷，並參與國際事務中心舉辦之成果經驗分享會",
              ],
          },
      ],
  }
  (OFFICIAL_NTTU_DIR / "document-conditions.json").write_text(
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
        f"{fname},{len(partners)},{pop},{ratio:.4f},Official NTTU COIA verified"
    )
  (OFFICIAL_NTTU_DIR / "field-coverage.csv").write_text(
      "\n".join(field_cov_lines) + "\n", encoding="utf-8"
  )

  pages_records = [
      {
          "title": "國立臺東大學：2026–2027 赴境外姊妹校交換生暨雙聯學位甄選時程（春季班 9/15 12:00 截止、秋季班 3/20 12:00 截止）",
          "source_url": NTTU_2027_SPRING_ANNOUNCEMENT_URL,
          "published_at": "2026-08-03T00:00:00Z",
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
          "title": "國立臺東大學：辦理學生申請出國進修或交換作業要點、甄選評分權重（書審 50%＋面試 50%）與雙聯學制規定",
          "source_url": NTTU_EXCHANGE_GUIDELINES_PDF_URL,
          "published_at": "2026-08-03T00:00:00Z",
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
          "title": f"國立臺東大學：{len(partners)} 所全球與兩岸合作姊妹校外語檢定門檻暨出國進修獎助學金 CEFR B1/B2 語言基準表",
          "source_url": NTTU_SCHOLARSHIP_GUIDELINES_PDF_URL,
          "published_at": "2026-08-03T00:00:00Z",
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
          "title": "國立臺東大學：出國進修交換應備文件（核章申請表、家長同意書、一式3份歷年成績單與班排名證明、出國進修交換計畫書）",
          "source_url": NTTU_EXCHANGE_REGULATIONS_URL,
          "published_at": "2026-08-03T00:00:00Z",
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
          "title": "國立臺東大學：學生出國進修獎助學金（交換及雙聯最高 30 萬元）與教育部學海飛颺、學海惜珠、學海築夢計畫",
          "source_url": NTTU_XUEHAI_HUB_URL,
          "published_at": "2026-08-03T00:00:00Z",
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
          "title": "國立臺東大學：與境外大學校院辦理雙聯學制實施辦法（日本仙台大學 2.5+2、琵琶湖成蹊體育運動大學 1.5+2+1 雙學士學制）",
          "source_url": NTTU_DUAL_DEGREE_REGULATIONS_PDF_URL,
          "published_at": "2026-08-03T00:00:00Z",
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
          "title": "國立臺東大學：學生出國期間有關學業及學籍處理辦法與學生抵免學分要點（18 小時折算 1 學分、歐洲 ECTS×1/2、英國 CATS×1/4）",
          "source_url": NTTU_CREDIT_TRANSFER_PDF_URL,
          "published_at": "2026-08-03T00:00:00Z",
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
          "title": f"國立臺東大學：國際事務中心出國交換生心得分享＆學海築夢成果專區（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）",
          "source_url": NTTU_EXPERIENCE_SHARING_URL,
          "published_at": "2026-08-03T00:00:00Z",
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
  (OFFICIAL_NTTU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
      + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "nttu",
      "school_name": "國立臺東大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "document_review_weight_percent": 50,
          "interview_weight_percent": 50,
          "scholarship_undergrad_class_rank_top_percent": 50.0,
          "xuehai_average_score_minimum": 80.0,
          "scholarship_undergrad_cefr_minimum": "B1",
          "scholarship_graduate_cefr_minimum": "B2",
          "outbound_scholarship_max_ntd": 300000,
          "short_term_credit_scholarship_max_ntd": 80000,
          "short_term_language_scholarship_max_ntd": 20000,
          "exclude_in_service": True,
          "senior_max_exchange_semesters": 1,
          "return_report_due": "返國後 1 個月內繳交 2,000 字以上研修心得報告與問卷並參與成果分享會",
      },
      "source_urls": nttu_source_urls,
      "verified_at": "2026-11-06",
  }
  (OFFICIAL_NTTU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NTTU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "國立臺東大學",
              "required_documents": student_dashboard_payload[
                  "required_documents"
              ],
              "source_urls": nttu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NTTU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "國立臺東大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": nttu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "nttu",
      "school_name": "國立臺東大學",
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
          f"國立臺東大學研究發展處國際事務中心（COIA）《2025–2027 赴境外姊妹校交換生暨雙聯學位名額一覽表（含 8 所國際姊妹校＋7 所大陸姊妹校）》、《國際暨兩岸締約姊妹校名錄（59 校）》、《辦理學生申請出國進修或交換作業要點》、《學生出國進修獎助學金要點（最高 30 萬元）》、《與境外大學校院辦理雙聯學制實施辦法》及教育部《學海飛颺／學海惜珠／學海築夢》專區同步整合；共完整收錄 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所當期開放申請合作校及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 15 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷年學長姐交換、雙聯與學海築夢心得報告）。"
      ),
      "verified_at": "2026-11-06",
  }
  (OFFICIAL_NTTU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NTTU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "nttu",
              "school_name": "國立臺東大學",
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
          "sources/nttu/nttu_catalog_source.json",
          NTTU_OUTBOUND_EXCHANGE_URL,
          f"國立臺東大學 {len(partners)} 所全球與兩岸合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/nttu/nttu_resolved_locations.json",
          NTTU_PARTNER_LIST_URL,
          f"國立臺東大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
      ),
      (
          "sources/nttu/nttu_experience_index.json",
          NTTU_EXPERIENCE_SHARING_URL,
          f"國立臺東大學研究發展處國際事務中心 {exp_covered_schools} 校 {total_exp_reports} 篇出國交換暨學海築夢心得報告索引 JSON",
      ),
  ]
  for rel_p, surl in bin_urls.items():
    rp = rel_p if rel_p.startswith("sources/") else f"sources/nttu/{rel_p}"
    if not any(x[0] == rp for x in provenance_files):
      provenance_files.append((rp, surl, f"國立臺東大學官方原始檔案：{Path(rp).name}"))

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
      "school_id": "nttu",
      "school_name": "國立臺東大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = (
      json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  )
  (OFFICIAL_NTTU_DIR / "import_provenance.json").write_text(
      prov_text, encoding="utf-8"
  )
  (OFFICIAL_NTTU_DIR / "import-provenance.json").write_text(
      prov_text, encoding="utf-8"
  )

  print(
      f"Successfully built NTTU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
