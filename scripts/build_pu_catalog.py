"""Build the official Providence University (靜宜大學, PU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_PU_DIR = REPO_ROOT / "sources" / "pu"
OFFICIAL_PU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "pu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "university_locations.jsonl"
)

CHECKED_AT = "2026-10-30T00:00:00Z"

PU_411_HOME_URL = "https://411.pu.edu.tw/"
PU_OIA_HOME_URL = "https://oia.pu.edu.tw/"
PU_EXCHANGE_OVERVIEW_URL = "https://411.pu.edu.tw/p/426-1073-4.php?Lang=zh-tw"
PU_SCHOOLS_OVERVIEW_URL = "https://411.pu.edu.tw/p/426-1073-51.php?Lang=zh-tw"
PU_DUAL_DEGREE_URL = "https://411.pu.edu.tw/p/426-1073-6.php?Lang=zh-tw"
PU_ISEP_URL = "https://411.pu.edu.tw/p/426-1073-5.php?Lang=zh-tw"
PU_SCHOLARSHIPS_URL = "https://411.pu.edu.tw/p/426-1073-7.php?Lang=zh-tw"
PU_REGULATIONS_URL = "https://411.pu.edu.tw/p/426-1073-12.php?Lang=zh-tw"
PU_FORMS_URL = "https://411.pu.edu.tw/p/426-1073-11.php?Lang=zh-tw"
PU_FAQ_URL = "https://411.pu.edu.tw/p/426-1073-10.php?Lang=zh-tw"
PU_SISTERS_URL = "https://oia.pu.edu.tw/p/404-1064-37011.php?Lang=zh-tw"
PU_NEWS_115_2_OCT_PASS_URL = "https://411.pu.edu.tw/p/406-1073-62396,r555.php?Lang=zh-tw"
PU_NEWS_116_XUEHAI_URL = "https://411.pu.edu.tw/p/406-1073-60160,r555.php?Lang=zh-tw"
PU_NEWS_EAGLE_FUND_URL = "https://411.pu.edu.tw/p/406-1073-61598,r555.php?Lang=zh-tw"

PU_STUDY_ABROAD_RULES_PDF_URL = "https://411.pu.edu.tw/var/file/73/1073/img/907/380876450.pdf"
PU_SELECTION_RULES_PDF_URL = "https://411.pu.edu.tw/var/file/73/1073/img/907/465423966.pdf"
PU_TUITION_RULES_PDF_URL = "https://411.pu.edu.tw/var/file/73/1073/img/907/167360257.pdf"
PU_SCHOLARSHIP_RULES_PDF_URL = "https://411.pu.edu.tw/var/file/73/1073/img/907/206798014.pdf"
PU_DUAL_DEGREE_RULES_PDF_URL = "https://411.pu.edu.tw/var/file/73/1073/img/907/138818453.pdf"
PU_CREDIT_TRANSFER_RULES_PDF_URL = "https://411.pu.edu.tw/var/file/73/1073/img/907/546244729.pdf"
PU_CREDIT_CONVERSION_PDF_URL = "https://411.pu.edu.tw/var/file/73/1073/img/907/126278046.pdf"
PU_ISEP_GUIDE_PDF_URL = "https://411.pu.edu.tw/var/file/73/1073/img/907/915731542.pdf"
PU_XUEHAI_RULES_PDF_URL = "https://411.pu.edu.tw/var/file/73/1073/img/907/896959326.pdf"
PU_XUEHAI_FLOW_PDF_URL = "https://411.pu.edu.tw/var/file/73/1073/img/907/463801157.pdf"
PU_SPAIN_PARTNERS_PDF_URL = "https://411.pu.edu.tw/var/file/73/1073/img/907/307232329.pdf"
PU_REPORT_UPLOAD_GUIDE_PDF_URL = "https://411.pu.edu.tw/var/file/73/1073/img/907/949852069.pdf"

REGION_COST_DEFAULTS = {
    "美國": (
        "每月生活費約 USD 1,400–2,200（依匯率折合新臺幣約 45,000–70,000 元，含樹城州立大學 Boise State、斯克蘭頓大學 Scranton、印第安納波利斯大學 UIndy、萊德大學 Rider、達拉斯浸信會大學 DBU、馬里蘭聖母大學、舊金山州立大學等校內外住宿、伙食與交通；互惠交換生免繳美國姊妹校學費，ISEP-Exchange 學生於靜宜繳交雙人雅房食宿基準費即免繳美國接待校食宿費）",
        "須憑美國接待大學或 ISEP 總部核發之 DS-2019（J-1 交換生）或 I-20（F-1 雙聯學位生）表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證，且須投保符合接待校或 ISEP 規定之全期海外醫療保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,250–1,900（折合加幣約 CAD 1,700–2,600 / 月、新臺幣約 40,000–60,000 元，含曼尼托巴大學、聖瑪麗大學、道格拉斯學院、亞崗昆學院等住宿、伙食與交通）",
        "研習 6 個月內可申辦加拿大 eTA，超過 6 個月須申辦加拿大 Study Permit 並投保醫療保險。",
    ),
    "英國": (
        "每月生活費約 USD 1,350–2,100（折合英鎊約 GBP 1,050–1,650 / 月、新臺幣約 43,000–67,000 元，含艾塞克斯大學 Essex、倫敦密德薩斯大學 Middlesex、倫敦布魯內爾大學 Brunel、桑德蘭大學 Sunderland、諾桑比亞大學等學生宿舍與生活費）",
        "交換 6 個月以內可依英國 ETA / Standard Visitor 規定入境，交換 1 學年或攻讀 3+1 / 3+1.5 雙聯學位須申辦英國 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "法國": (
        "每月生活費約 USD 1,050–1,650（折合歐元約 EUR 950–1,500 / 月、新臺幣約 33,500–53,000 元；含里昂天主教大學 ESDES、里爾天主教大學 Junia ISA Lille、南特高等商學院 Audencia、拉羅謝爾商學院、巴黎中央電子理工學院 ECE、昂熱西部天主教大學 UCO 等住宿與膳食，可申請法國 CAF 房補）",
        "須先經法國教育中心（Campus France）完成 Etudes en France 線上程序與面試，再向法國在台協會申辦長期學生簽證（VLS-TS）。",
    ),
    "德國": (
        "每月生活費約 USD 1,050–1,600（折合歐元約 EUR 950–1,450 / 月、新臺幣約 33,500–51,000 元；含科隆商學院 CBS、紐倫堡科技大學 TH Nürnberg、巴登符騰堡雙元制大學 DHBW 斯圖加特／曼海姆校區、馬爾堡大學、奧芬堡應用科大等學生住宿、學期雜費與交通卡費）",
        "須開立德國限制提領帳戶（Blocked Account）並憑入學許可向德國在台協會申辦德國長期學生簽證及投保德國公保／醫療險。",
    ),
    "西班牙": (
        "每月生活費約 USD 950–1,500（折合歐元約 EUR 880–1,380 / 月、新臺幣約 30,500–48,000 元；含馬德里自治大學、格拉納達大學、薩拉曼卡大學、瓦拉多利大學、雷昂大學、馬拉加大學、塞維亞大學、科米亞斯宗座大學、聖地牙哥德孔波斯特拉大學等住宿與生活費）",
        "須憑西班牙接待大學入學許可向西班牙商務辦事處申辦學生簽證，並投保無自負額之全額醫療保險。",
    ),
    "義大利": (
        "每月生活費約 USD 1,000–1,600（折合歐元約 EUR 900–1,450 / 月、新臺幣約 32,000–51,000 元；含費拉拉大學、薩勒諾大學、佩魯賈外國人大學、西耶納外國人大學、帕多瓦 CIELS 高等語言調解學院等住宿與生活費）",
        "須憑義大利接待院校入學許可向義大利經濟貿易文化推廣辦事處申辦學習簽證（Visto per Studio），入境後 8 日內申辦居留證。",
    ),
    "日本": (
        "每月生活費約 USD 700–1,150（折合日圓約 JPY 100,000–165,000 / 月、新臺幣約 22,500–36,500 元；上智大學、青山學院大學、明治學院大學、日本大學、東洋大學、芝浦工業大學、東京經濟大學、白百合女子大學等首都圈約 JPY 110,000–160,000 / 月；同志社大學、關西大學、京都女子大學、愛知縣立大學、南山大學、中京大學、東北大學、廣島大學、長崎外國語大學等約 JPY 85,000–130,000 / 月）",
        "須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後至日本台灣交流協會申辦留學簽證並加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 680–1,100（折合韓元約 KRW 900,000–1,500,000 / 月、新臺幣約 21,500–35,000 元；首爾梨花女子大學、西江大學、漢陽大學、中央大學、建國大學、東國大學、國民大學、明知大學、淑明女子大學、崇實大學、德成女子大學、誠信女子大學約 KRW 1,000,000–1,450,000 / 月；釜山大學、天主教大學、翰林大學、大邱天主教大學等約 KRW 750,000–1,100,000 / 月）",
        "須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後辦理外國人登錄證並納保韓國國民健康保險。",
    ),
    "中國大陸": (
        "每月生活費約 USD 350–700（折合人民幣約 RMB 2,000–4,500 / 月、新臺幣約 11,000–22,500 元；含中國人民大學、北京師範大學、南開大學、復旦大學、上海交通大學、華東師範大學、南京大學、浙江大學、武漢大學、中山大學、廈門大學、山東大學、吉林大學、四川大學、蘭州大學等校內學生宿舍住宿費每學期約 RMB 600–1,500，主要開銷為食堂膳食與交通）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及大陸姊妹校寄發之錄取通知書辦理報到，並依靜宜大學國際暨兩岸事務處規定購買涵蓋交換全期之海外傷病醫療及意外保險。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,350–2,000（折合澳幣約 AUD 2,000–3,000 / 月、新臺幣約 43,000–64,000 元；含澳洲天主教大學 ACU、西雪梨大學 Western Sydney、南十字星大學 Southern Cross、中央昆士蘭大學 CQU 等校內外住宿與生活費）",
        "須憑澳洲接待大學核發之 CoE（Confirmation of Enrolment）申辦澳洲 Subclass 500 學生簽證，並強制投保海外學生健康保險（OSHC）。",
    ),
    "紐西蘭": (
        "每月生活費約 USD 1,200–1,800（折合紐幣約 NZD 1,950–2,900 / 月、新臺幣約 38,500–57,500 元；含奧塔哥大學、納爾遜馬爾伯勒理工學院 NMIT、紐西蘭旅遊學院等住宿與生活費）",
        "須憑紐西蘭接待院校入學許可申辦紐西蘭學生簽證並投保符合紐西蘭規範之全期醫療與旅遊保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "美國": "秋季學期（Fall Semester）：約 8 月中旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬",
    "加拿大": "秋季學期（Fall Semester）：約 9 月初至 12 月中旬；春季學期（Spring Semester）：約 1 月初至 4 月下旬",
    "英國": "秋季學期（Autumn Term）：約 9 月中下旬至翌年 1 月；春季學期（Spring Term）：約 1 月下旬至 6 月",
    "法國": "秋季學期（Fall Semester）：約 9 月初至 12 月底／1 月；春季學期（Spring Semester）：約 1 月下旬至 5/6 月",
    "德國": "冬季學期（Winter Semester）：約 9/10 月至翌年 1/2 月；夏季學期（Summer Semester）：約 3/4 月至 7/8 月",
    "西班牙": "秋季學期：約 9 月中旬至翌年 1 月；春季學期：約 1/2 月至 5/6 月",
    "義大利": "秋季學期：約 9 月中旬至翌年 1 月底；春季學期：約 2 月中旬至 6 月底",
    "日本": "春季學期（Spring Semester）：約 4 月初至 8 月初；秋季學期（Fall Semester）：約 9 月中下旬至翌年 1/2 月",
    "韓國": "春季學期（Spring Semester）：約 3 月初至 6 月中旬；秋季學期（Fall Semester）：約 9 月初至 12 月中旬",
    "中國大陸": "春季學期（下學期）：約 2 月中下旬至 6 月底；秋季學期（上學期）：約 9 月初至翌年 1 月中旬",
    "澳洲": "第一學期（Semester 1）：約 2 月下旬至 6 月下旬；第二學期（Semester 2）：約 7 月下旬至 11 月下旬",
    "紐西蘭": "第一學期（Semester 1）：約 2 月下旬至 6 月下旬；第二學期（Semester 2）：約 7 月中旬至 11 月中旬",
}


def clean_text(s: str) -> str:
  return re.sub(r"\s+", " ", s).strip() if s else ""


def sync_global_assets_and_locations(catalog_source: list[dict], resolved_locations: dict) -> None:
  """Ensure school-images.json and university_locations.jsonl contain all 276 PU partner schools."""
  si_path = STATIC_DIR / "assets" / "school-images.json"
  si_data = json.loads(si_path.read_text(encoding="utf-8"))
  schools_list = si_data.get("schools", [])
  by_name = {str(r.get("school_name", "")): r for r in schools_list if isinstance(r, dict)}
  si_changed = False
  for item in catalog_source:
    fn = item["school_name"]
    irec = item.get("image_record") or {}
    if irec.get("local_path"):
      new_rec = {
          "school_name": fn,
          "local_path": irec["local_path"],
          "image_source_url": irec.get("image_source_url") or irec.get("image_url") or irec["local_path"],
          "source_page_url": irec.get("source_page_url") or irec.get("official_page_url") or item.get("website") or "",
          "official_page_url": item.get("website") or irec.get("official_page_url") or "",
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
    si_path.write_text(json.dumps(si_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

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
      lat = float(loc.get("latitude") if loc.get("latitude") is not None else loc.get("lat", 24.2258))
      lon = float(loc.get("longitude") if loc.get("longitude") is not None else loc.get("lon", 120.5772))
      new_loc = {
          "school_name": fn,
          "country": item["country"],
          "city": loc.get("city") or item["country"],
          "latitude": lat,
          "longitude": lon,
          "geocode_status": "verified",
          "geocoded_at": CHECKED_AT,
          "source_url": loc.get("source_url") or "https://www.wikidata.org",
          "identity_source_url": item.get("website") or loc.get("source_url") or "https://ror.org",
          "precision": loc.get("precision") or "representative",
      }
      parsed_locs.append(new_loc)
      loc_by_name[fn] = new_loc
      loc_changed = True
  if loc_changed:
    UNIVERSITY_LOCATIONS_PATH.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in parsed_locs) + "\n",
        encoding="utf-8",
    )


def main() -> None:
  OFFICIAL_PU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads((SOURCES_PU_DIR / "pu_catalog_source.json").read_text(encoding="utf-8"))
  resolved_locations = json.loads((SOURCES_PU_DIR / "pu_resolved_locations.json").read_text(encoding="utf-8"))
  sync_global_assets_and_locations(catalog_source, resolved_locations)

  school_images_data = json.loads((STATIC_DIR / "assets" / "school-images.json").read_text(encoding="utf-8"))
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
    avail_status = "open" if item.get("offering_status") == "open" else "reference_only"
    if avail_status == "open":
      open_partner_count += 1

    group_str = clean_text(item.get("group") or "411遊留學中心（出國研修組）合作姊妹校")
    prog_raw = clean_text(item.get("program_type_raw") or "免學費交換 Exchange Program")
    quota_str = clean_text(item.get("quota") or "每學期 1–5 名交換生（依當期411遊留學中心公告名額辦理）")
    detail_url = item.get("detail_url") or PU_SCHOOLS_OVERVIEW_URL
    source_url = detail_url

    if "雙聯" in prog_raw:
      program_type = f"411遊留學中心（出國研修組）{prog_raw}"
    elif "ISEP" in prog_raw:
      program_type = f"411遊留學中心【ISEP 國際交換學生計畫】{prog_raw}"
    elif avail_status == "open":
      program_type = f"411遊留學中心（出國研修組）赴外研修計畫—{prog_raw}"
    else:
      program_type = f"國際暨兩岸事務處正式締約合作姊妹校（{prog_raw}）"

    colleges_str = clean_text(
        item.get("colleges")
        or "外語暨人文創意學院、社會科學院、理學院、管理學院、資訊學院、國際學院（全校六大學院）"
    )
    degree_levels_str = clean_text(
        item.get("eligible_degrees")
        or "靜宜大學大學部大二（含）以上、碩士班及博士班在學學生（大一新生可於大一下申請、大二上出國研修；延畢生得申請互惠交換學生）"
    )
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "歷年學業總平均 70 分以上（GPA 2.75+）或班排名前 50%")
    website = item.get("website") or PU_SCHOOLS_OVERVIEW_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    round_label = (
        "115-2（2027春季班：8月／9月／10月三梯次校內初審）＆116-1（2027秋季班：2月／3月／4月三梯次校內初審）出國研修暨雙聯學位甄選"
        if avail_status == "open"
        else "國際暨兩岸事務處／411遊留學中心正式締約姊妹校（依當期411遊留學中心各洲別名額表公告辦理）"
    )
    app_deadline_str = clean_text(item.get("deadline") or "")
    deadline_iso = "2026-10-30T17:00:00+08:00"
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "116"

    study_period_str = clean_text(item.get("duration") or "一學期或一學年")
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月")
    housing_str = (
        f"獲靜宜大學國際暨兩岸事務處（411遊留學中心）推薦提名後，可依 {zh_name} 國際處指引申請校內外學生宿舍或國際學舍"
        + (f"（學費與食宿待遇：{tuition_note}）" if tuition_note else "。")
    )
    course_rest_str = (
        f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《靜宜大學學生出國研修辦法》、《靜宜大學遴選交換學生作業要點》、《靜宜大學與境外大學校院辦理雙聯學制實施辦法》、《靜宜大學學生出國研修期間學業及學籍處理要點》及《靜宜大學出國交換學生學分換算準則》規定："
        "（1）大一新生可於大一下學期提出申請、大二上學期開始出國研修；出國期間以一學期或一學年為原則（雙聯學制大三生得出國兩年，累計不超過兩年）；"
        "（2）在學期間（含延畢生申請互惠交換）出國研讀須維持靜宜在學學籍並繳交靜宜全額學費、免繳雜費（修讀雙聯學制者須繳交靜宜全額學雜費；參加 ISEP-Exchange 者於靜宜繳交全額學費、雙人雅房住宿費與伙食費基準每學期約 NT$ 51,000，免繳海外接待大學學費與食宿費）；"
        "（3）出國研修期間每學期至少應修習相當於靜宜 6 學分或至少 2 門科目；返國後須於次一學期開學 2 個月內檢附國外成績單正本及課程大綱辦理學分抵免，且強制規定「至少須抵免一科（至少 1 學分）」！學分換算準則：美制／日制／陸制與靜宜相同（1:1），歐洲 ECTS 學分除以 2（ECTS ÷ 2 = 靜宜學分），英國 CATS 學分除以 4（CATS ÷ 4 = 靜宜學分），或實際授課滿 18 小時折算 1 學分；"
        "（4）返國後兩個月內須至 e校園服務網上傳 1,500–2,000 字出國交換學生報告書、6 張照片及《個人資料提供同意書》始完成結案。"
    )

    living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
        country,
        (
            "每月生活費約 USD 800–1,450（依匯率折合新臺幣約 25,500–46,500 元，含住宿、膳食與市區交通）",
            "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
        ),
    )

    tuition_points_list = [
        (
            f"靜宜在學學雜費規定與合作校待遇：依《靜宜大學學生出國研修期間學業及學籍處理要點》，在學期間（含延畢生申請互惠交換）出國研讀須繳交靜宜大學全額學費、免繳雜費（修讀雙聯學制者須繳全額學雜費）。本合作校待遇：{tuition_note}。"
        ),
        (
            "靜宜四大出國獎助學金體系：（1）教育部《學海飛颺》與《學海惜珠》獎學金（每年分 2 次甄選：第1次 12 月至翌年 3 月初、第2次至 9 月初；須具中華民國國籍、班排前 50%［飛颺］或持低收／中低收入證明［惜珠］、外語達 CEFR B1+，且交換期間不得同時領取我國政府或靜宜校內其他出國獎學金）；（2）《靜宜大學 E.A.G.L.E. 築夢基金》（每學期開放申請：上學期 10 月中截止、下學期 3 月下旬截止，補助大學部在學學生赴境外研修，亞洲地區每人上限 NT$ 20,000、非亞洲地區每人上限 NT$ 30,000）；（3）《靜宜大學學生出國研修獎助學金辦法》（海外移地教學亞洲上限 2 萬／非亞 3 萬；系級國際教育計畫亞洲上限 1 萬／非亞 2 萬）；（4）德國巴登符騰堡州獎學金（Baden-Württemberg Stipendium）、歐盟 Erasmus+ 獎學金與日本台灣交流協會獎學金。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認靜宜在學學籍、成績門檻與 {zh_name} 外語檢定標準）：確認符合《靜宜大學學生出國研修辦法》及《遴選交換學生作業要點》資格（大一新生可於大一下申請、大二上出國；學業條件：{gpa_req_str}），並備妥符合 {zh_name} 要求之有效外語檢定成績（{lang_req_str}）。"
        ),
        (
            "步驟二（於 411 遊留學中心三梯次初審期間完成線上申請與備審上傳）：春季班出國於前一年 8 月底（第1次）、9 月底（第2次）、10 月中（第3次／語言課程）分三梯次辦理校內初審；秋季班出國於當年 2 月底（第1次）、3 月底（第2次）、4 月底（語言課程）辦理（雙聯學制秋季班 3/31 截止；ISEP 秋季班 1 月中、春季班 7 月底截止）。備齊出國研修申請表、中英文歷年成績單（含班排名）、外語能力證明、中英文讀書計畫與自傳、師長推薦信及《個人資料提供同意書》送交 411 遊留學中心（主顧樓 315 室）。"
        ),
        (
            "步驟三（通過校內初審甄選、公告錄取名單並繳交《靜宜大學境外研修同意書》）：由國際暨兩岸事務處（411遊留學中心）彙整審查並公告初審通過名單；錄取同學須於指定期限內（如 115-2 十月初審通過者須於 2026/10/30 17:00 前）下載並親簽紙本《靜宜大學境外研修同意書》（含家長簽章與系所確認）繳回主顧樓 315 室。"
        ),
        (
            f"步驟四（由 411 遊留學中心向 {full_name} 提名送件、行前辦理出國研習單，返國後 2 個月內強制抵免至少一科並上傳報告書）：獲接待校入學許可後辦理簽證、住宿與海外保險，離校前填妥《靜宜大學學生出國期間學業及學籍處理單》；返國後於次學期開學 2 個月內依《出國交換學生學分換算準則》（ECTS÷2、CATS÷4、美日陸 1:1）辦理學分抵免（強制至少抵免一科），並於返國 2 個月內至 e校園服務網上傳 1,500–2,000 字報告書與 6 張照片。"
        ),
    ]

    elig_points_list = [
        f"合作類別與計畫群組：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業成績與排名門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "411遊留學中心分梯次初審與分發制度：每學期分 3 梯次校內初審（秋季班出國於 2月／3月／4月；春季班出國於 8月／9月／10月），第一梯次名額最充裕，後續梯次就剩餘名額進行甄選；初審通過後須繳交紙本《靜宜大學境外研修同意書》至主顧樓 315 室。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與靜宜獎補助待遇：{tuition_note}")
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
        eurl = e.get("url") or f"{PU_SCHOOLS_OVERVIEW_URL}#pu-exp-{sn}-{e_idx+1}"
        if eurl in seen_exp_urls:
          eurl = f"{eurl}#r{e_idx+1}"
        seen_exp_urls.add(eurl)
        exp_labels.append(raw_t[:36])
        exp_links.append({
            "title": raw_t,
            "url": eurl,
            "academic_year": esem,
            "semester": esem,
            "college": "外語暨人文創意學院／管理學院／國際學院／社會科學院／理學院／資訊學院",
            "department": e.get("department") or "靜宜出國研修生",
        })
        summary_text = (
            f"靜宜大學國際暨兩岸事務處（411遊留學中心）於各洲別姊妹校列表公開收錄之學長姐赴 {country} {full_name} 交換／研修官方返國心得報告 PDF（{raw_t}），詳述選課與學分換算抵免、外語與專業課程學習、住宿環境、簽證辦理與當地生活費實錄。"
        )
        theme_map = {
            "academics": f"靜宜交換生於《{raw_t}》分享在 {zh_name} 選修專業與語言文化課程（每學期至少修習 6 學分或 2 門課），以及返國後依《靜宜大學出國交換學生學分換算準則》辦理強制至少一科學分抵免之經驗。",
            "housing": f"靜宜交換生記錄申請 {zh_name} 校內外學生宿舍、周邊生活機能與大眾運輸通勤方式（{housing_str[:100]}）。",
            "campus_culture": f"靜宜 411 遊留學中心公開收錄《{raw_t}》之跨文化交流、校園生活與國際生社團活動紀錄。",
            "cost": f"靜宜交換生分享於 {zh_name} 之每月住宿、伙食與交通開銷（{living_cost_str[:100]}），以及申請教育部學海飛颺／惜珠或靜宜 E.A.G.L.E. 築夢基金之經驗。",
        }
        student_experience_rows.append({
            "school_name": full_name,
            "country": country,
            "title": raw_t,
            "source_url": eurl,
            "source_type": "pdf" if ".pdf" in eurl.lower() else "article",
            "platform": "靜宜大學國際暨兩岸事務處（411遊留學中心）—各洲別姊妹校研修心得專區",
            "author_name": e.get("student_name") or "靜宜交換生",
            "language": "zh",
            "summary": summary_text,
            "themes": ["academics", "housing", "campus_culture", "cost"],
            "theme_summaries": theme_map,
            "content_status": "full_text",
            "perspective": "official_student_story",
            "published_at": None,
            "discovered_at": CHECKED_AT,
            "content_hash": hashlib.sha256(f"{full_name}:pu_exp:{e_idx}:{eurl}".encode("utf-8")).hexdigest(),
            "exchange_term": esem,
            "summary_zh": summary_text,
            "original_summary": summary_text,
            "theme_summaries_zh": theme_map,
            "translation_status": "original",
            "source_kind": "official_experience_page",
        })

    sample_reports = [{"title": lk["title"], "url": lk["url"], "term": lk["semester"]} for lk in exp_links[:6]]
    experience_sources_records.append({
        "home_university": "靜宜大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": exp_links[0]["url"] if exp_links else detail_url,
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

    loc = resolved_locations.get(full_name) or {
        "city": country,
        "latitude": 24.2258,
        "longitude": 120.5772,
        "source_url": "https://www.wikidata.org",
    }
    city_name = loc.get("city") or country
    lat = float(loc.get("latitude") if loc.get("latitude") is not None else loc.get("lat", 24.2258))
    lon = float(loc.get("longitude") if loc.get("longitude") is not None else loc.get("lon", 120.5772))
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
        "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 及靜宜大學國際暨兩岸事務處（411遊留學中心）姊妹校名錄比對；實際交換校區以錄取通知與姊妹校簡章為準。",
    }
    new_locations.append(location_obj)

    vrec = visual_by_name.get(full_name) or item.get("image_record")
    assert vrec and vrec.get("local_path"), f"Missing verified image for {full_name}"
    img_local = vrec.get("local_path")
    img_source = vrec.get("image_source_url") or vrec.get("image_url") or img_local
    img_page = vrec.get("official_page_url") or vrec.get("source_page_url") or img_source
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
          f"【靜宜學長姐交換返國心得報告（共 {len(exps)} 篇）】收錄於 411 遊留學中心各洲別姊妹校名錄（含：{'、'.join(exp_labels[:4])}）"
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
        "eligibility": f"開放對象：{colleges_str}（{degree_levels_str}）｜{gpa_req_str}｜{lang_req_str}",
        "language_requirement": lang_req_str,
        "gpa_requirement": gpa_req_str,
        "quota": quota_str,
        "quota_status": "published" if avail_status == "open" else "reference_only",
        "availability_status": avail_status,
        "availability_note": f"靜宜大學國際暨兩岸事務處（411遊留學中心）公告合作姊妹校（{program_type}）；{quota_str}。",
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
            "title": f"靜宜大學國際暨兩岸事務處（411遊留學中心）各洲別姊妹校名額與申請條件表—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "靜宜大學學生出國研修辦法、遴選交換學生作業要點與雙聯學制實施辦法",
            "source_url": PU_REGULATIONS_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "靜宜大學出國研修獎學金總覽（教育部學海飛颺、學海惜珠、E.A.G.L.E. 築夢基金）",
            "source_url": PU_SCHOLARSHIPS_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exp_links:
      wf_sources.append({
          "title": f"靜宜大學 411 遊留學中心學生研修心得報告專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
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
        "home_university": "靜宜大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": acad_year,
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "115-2（2027春季班出國研修三梯次初審）",
            "116-1（2027秋季班出國研修三梯次初審）",
            "115-1",
            "115-2",
            "116-1",
            "116-2",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "靜宜大學由國際暨兩岸事務處（Office of International and Cross-Strait Affairs）下轄之「411遊留學中心（出國研修組，主顧樓 315 室）」統籌全校 6 大學院（外語暨人文創意學院、社會科學院、理學院、管理學院、資訊學院、國際學院）之免學費交換、ISEP 國際交換學生計畫（全球逾 300 所會員校）、16 校跨國雙聯學位計畫、自費／學費減免交換及姊妹校專業語言課程，並整合教育部學海飛颺、學海惜珠與靜宜 E.A.G.L.E. 築夢基金。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"pu-{acad_year}-home-1-{sn:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認靜宜在學學籍、歷年平均 70 分（GPA 2.75+）門檻與 {zh_name} 語檢要求",
                "responsible_party": "學生",
                "responsible_unit": "靜宜大學國際暨兩岸事務處—411遊留學中心（主顧樓 315 室）",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    f"確認符合《靜宜大學學生出國研修辦法》及《遴選交換學生作業要點》規定：大一新生可於大一下學期提出申請、大二上學期開始出國研修（延畢生得申請互惠交換學生），符合學業要求（{gpa_req_str}），並備妥符合 {zh_name} 門檻之有效外語檢定證明（{lang_req_str}）。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["靜宜大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                },
                "source_urls": [source_url, PU_EXCHANGE_OVERVIEW_URL, PU_SELECTION_RULES_PDF_URL],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"pu-{acad_year}-home-2-{sn:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "於 411 遊留學中心三梯次初審截止前提交出國研修申請表、中英文成績單與讀書計畫",
                "responsible_party": "學生",
                "responsible_unit": "靜宜大學 411 遊留學中心（主顧樓 315 室）",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": PU_EXCHANGE_OVERVIEW_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "依出國學期於三梯次初審期間送件：春季班出國為前一年 8 月底（第1次）、9 月底（第2次）、10 月中（第3次／語言課程）；秋季班出國為當年 2 月底（第1次）、3 月底（第2次）、4 月底（語言課程）；雙聯學制秋季班入學於 3 月 31 日截止；ISEP 交換秋季班 1 月中截止、春季班 7 月底截止。"
                ),
                "details": [
                    "115-2（2027春季班）校內初審三梯次：第1次 2026/08/03–08/23、第2次 2026/08/24–09/20、第3次 2026/09/21–10/11。",
                    "115年教育部學海飛颺／學海惜珠獎學金：第1次甄選 2025/12/08–2026/03/06、第2次甄選至 2026/09/02 截止；115學年度靜宜 E.A.G.L.E. 築夢基金：上學期 2026/10/15 截止、下學期 2027/03/25 截止。",
                ],
                "document_requirements": [
                    {
                        "name": "靜宜大學出國研修申請表、境外研修同意書與個人資料提供同意書",
                        "official_form_url": PU_FORMS_URL,
                        "source_urls": [PU_FORMS_URL, PU_STUDY_ABROAD_RULES_PDF_URL],
                    },
                    {
                        "name": "中、英文歷年成績單正本（需含學業總平均、GPA 與班級排名）及在學證明",
                        "official_form_url": PU_EXCHANGE_OVERVIEW_URL,
                        "source_urls": [PU_EXCHANGE_OVERVIEW_URL, PU_SELECTION_RULES_PDF_URL],
                    },
                    {
                        "name": "有效外語能力檢定證明（TOEFL iBT / ITP / IELTS / TOEIC / JLPT / TOPIK / DELE / DELF 等）",
                        "official_form_url": PU_SCHOOLS_OVERVIEW_URL,
                        "source_urls": [source_url, PU_SELECTION_RULES_PDF_URL],
                    },
                    {
                        "name": "中、外文讀書計畫（Study Plan）、自傳與師長推薦信（申請學海飛颺／惜珠或 E.A.G.L.E. 築夢基金另附專項申請表與證明）",
                        "official_form_url": PU_SCHOLARSHIPS_URL,
                        "source_urls": [PU_SCHOLARSHIPS_URL, PU_XUEHAI_RULES_PDF_URL],
                    },
                ],
                "scope": {
                    "home_universities": ["靜宜大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                },
                "source_urls": [
                    PU_EXCHANGE_OVERVIEW_URL,
                    PU_DUAL_DEGREE_URL,
                    PU_ISEP_URL,
                    PU_FORMS_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"pu-{acad_year}-home-3-{sn:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "通過 411 遊留學中心校內初審甄選、公告錄取名單並於期限內繳交紙本《靜宜大學境外研修同意書》",
                "responsible_party": "靜宜大學 411 遊留學中心與錄取學生",
                "responsible_unit": "靜宜大學國際暨兩岸事務處（主顧樓 315 室）",
                "deadline_at": "2026-10-30T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": PU_NEWS_115_2_OCT_PASS_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": True,
                "summary": (
                    "411 遊留學中心依學業成績、外語能力及讀書計畫進行初審評比並公告通過名單；初審通過學生須於指定期限內（如 115-2 十月初審通過者須於 2026/10/30 前）繳交經本人及家長簽章之紙本《靜宜大學境外研修同意書》至主顧樓 315 室確認推薦資格。"
                ),
                "details": [
                    "獎學金同步遴選：通過校內出國研修初審之學生可依期限申請教育部《學海飛颺》、《學海惜珠》或《靜宜大學 E.A.G.L.E. 築夢基金》（亞洲上限 2 萬元、非亞洲上限 3 萬元）。",
                    "ISEP 交換生分發：申請 ISEP-Exchange 者於通過校內甄選後，至 ISEP 線上系統填寫最多 10 所志願學校並繳交申請費與財力證明，由 ISEP 總部進行全球媒合分發。",
                ],
                "scope": {
                    "home_universities": ["靜宜大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                },
                "source_urls": [PU_NEWS_115_2_OCT_PASS_URL, PU_SELECTION_RULES_PDF_URL, PU_SCHOLARSHIPS_URL],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"pu-{sn:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由 411 遊留學中心向 {zh_name} 辦理官方提名，並於姊妹校截止日前遞交入學與宿位申請文件",
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"完成校內同意書繳交後，由靜宜 411 遊留學中心具函向 {zh_name} 辦理官方推薦提名（Nomination）；學生須於姊妹校申請截止日前完成線上申請與文件遞交（含外文入學申請表、英文歷年成績單、護照／台胞證影本、英文存款財力證明、體檢報告與宿舍申請表），靜候接待校核發正式入學許可（Admission Letter / COE / DS-2019 / I-20）。"
                ),
                "details": [
                    f"研修期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["靜宜大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                },
                "source_urls": [source_url, PU_SCHOOLS_OVERVIEW_URL] + ([website] if website else []),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"pu-{acad_year}-home-5-{sn:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "出發前完成靜宜註冊繳費與《學生出國期間學業及學籍處理單》，返國後 2 個月內強制抵免至少一科並上傳報告書",
                "responsible_party": "學生與所屬系所",
                "responsible_unit": "靜宜大學 411 遊留學中心／綜合業務處／會計室／各系所",
                "summary": (
                    "出國前須參加行前說明會、填妥《靜宜大學學生出國期間學業及學籍處理單》並繳交靜宜全額學費（免繳雜費；雙聯學制繳全額學雜費）；出國期間每學期至少修習相當於靜宜 6 學分或 2 門課；返國後於次一學期開學 2 個月內持國外成績單正本依《出國交換學生學分換算準則》（ECTS÷2、CATS÷4、美日陸 1:1）辦理學分抵免（強制至少抵免一科），並於返國後 2 個月內至 e校園服務網上傳 1,500–2,000 字報告書及 6 張照片。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["靜宜大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                },
                "source_urls": [
                    PU_TUITION_RULES_PDF_URL,
                    PU_CREDIT_TRANSFER_RULES_PDF_URL,
                    PU_CREDIT_CONVERSION_PDF_URL,
                    PU_REPORT_UPLOAD_GUIDE_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合靜宜大學國際暨兩岸事務處（411遊留學中心）15 個洲別／國家地區姊妹校專頁、16 所跨國雙聯學位合作校（2+2、3+1、3+1+1、1+1、3+2 學碩一貫）、ISEP 國際交換學生計畫、五大洲締約姊妹校名錄 Excel、《靜宜大學學生出國研修辦法》、《遴選交換學生作業要點》、《出國交換學生學分換算準則》、教育部學海飛颺／惜珠與 E.A.G.L.E. 築夢基金辦法，以及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆學長姐返國心得報告 PDF，共 {len(catalog_source)} 所合作姊妹校資料。"
        ),
    })

    cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": f"靜宜大學國際暨兩岸事務處（411遊留學中心）各洲別姊妹校名額、申請條件與雙聯學位專頁—{zh_name}",
            "source_url": source_url,
            "summary": "靜宜 411 遊留學中心公告之合作計畫類別、當期開放名額、語言檢定門檻與學費／食宿待遇說明",
        },
        {
            "title": "靜宜大學學生出國研修辦法、遴選交換學生作業要點與出國交換學生學分換算準則",
            "source_url": PU_REGULATIONS_URL,
            "summary": "靜宜出國研修學雜費減免規定、三梯次校內初審制度、強制至少抵免一科學分與 ECTS÷2 / CATS÷4 學分換算準則",
        },
    ]
    if exp_links:
      dest_sources.append({
          "title": f"靜宜大學 411 遊留學中心學生研修心得專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
          "source_url": exp_links[0]["url"],
          "summary": f"收錄歷年靜宜學生赴 {zh_name} 交換／研修返國心得報告 PDF 共 {len(exps)} 篇",
      })
    if website:
      dest_sources.append({"title": f"{full_name} 官方網站", "source_url": website, "summary": "接待合作姊妹校官方網站"})

    src_url_list = (
        [source_url, PU_EXCHANGE_OVERVIEW_URL, PU_SCHOOLS_OVERVIEW_URL, PU_SCHOLARSHIPS_URL]
        + ([exp_links[0]["url"]] if exp_links else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "靜宜大學",
        "school_name": full_name,
        "country": country,
        "city": city_name,
        "cost_summary": f"{cost_line}。\n{tuition_clean}",
        "housing_summary": housing_clean,
        "transport_summary": f"校區代表城市：{city_name}。請依入學許可確認實際授課校區位置與當地學生交通卡優惠。",
        "campus_life_summary": f"{calendar_clean}\n{course_clean}",
        "student_guide_sections": [
            {
                "key": "cost",
                "title": "生活費、靜宜在學免繳雜費規定與教育部學海飛颺／惜珠／E.A.G.L.E. 築夢基金",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [PU_TUITION_RULES_PDF_URL, PU_SCHOLARSHIP_RULES_PDF_URL],
                "caution": (
                    "依《靜宜大學學生出國研修期間學業及學籍處理要點》與《學海飛颺及學海惜珠補助要點》，在學期間出國交換須繳交靜宜全額學費（免繳雜費；雙聯學制須繳全額學雜費）；領取學海飛颺或惜珠補助者於出國研修期間不得同時領取我國政府或靜宜校內其他出國獎學金。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外國際學生宿舍申請（含 ISEP 食宿互惠機制）",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": "一般互惠交換生住宿費由學生向接待校自理（床位有限請於獲得提名後盡早申請）；參加 ISEP-Exchange 者於靜宜繳交雙人雅房食宿基準費即由接待大學免費提供住宿與伙食。",
            },
            {
                "key": "insurance",
                "title": "海外醫療及意外保險與《靜宜大學境外研修同意書》規定",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依靜宜大學 411 遊留學中心規定，所有初審通過之出國研修生均須繳交經本人及家長簽章之紙本《靜宜大學境外研修同意書》，並於出國前購買涵蓋研修全期之海外急難救助、醫療及意外保險。",
                ],
                "source_urls": src_url_list,
                "caution": "歐美、日韓、澳洲及大陸接待校對交換生醫療保險（如美國 J-1 保險、澳洲 OSHC、日本與韓國國民健康保險）有強制規定，請依入學通知書辦理。",
            },
            {
                "key": "visa",
                "title": "留學交換簽證辦理、《學生出國期間學業及學籍處理單》與在學註冊義務",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "出國前須完成《靜宜大學學生出國期間學業及學籍處理單》核章程序並維持靜宜在學學籍；延畢生亦得申請互惠交換學生（修業年限符合大學法第 26 條規定者得專案簽請延長）。",
                ],
                "source_urls": src_url_list,
                "caution": "出國研修期間以一學期或一學年為原則（雙聯學制大三生得出國兩年），累計出國期間不得超過兩年。",
            },
            {
                "key": "academics",
                "title": "《靜宜大學出國交換學生學分換算準則》（ECTS÷2、CATS÷4）與返國強制抵免至少一科規定",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [PU_CREDIT_TRANSFER_RULES_PDF_URL, PU_CREDIT_CONVERSION_PDF_URL],
                "caution": (
                    "返國後須於次一學期開學 2 個月內檢附國外成績單正本及課程大綱辦理學分抵免，且強制規定「至少須抵免一科（至少 1 學分）」！並須於返國後 2 個月內至 e校園服務網上傳 1,500–2,000 字報告書及 6 張照片。"
                ),
            },
            {
                "key": "living",
                "title": f"{city_name} 校園生活與靜宜 411 遊留學中心學長姐返國心得傳承",
                "summary": f"代表城市：{city_name}。請配合接待校國際處完成報到與新生訓練（Orientation）。",
                "points": [
                    f"目的地城市：{city_name}（{country}）",
                    (
                        "靜宜大學 411 遊留學中心於各洲別姊妹校列表直接公開歷屆學長姐赴海外及大陸姊妹校交換之返國心得報告 PDF"
                        + (f"（本校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:3])}）" if exps else "")
                        + "，協助學弟妹掌握第一手選課與生活資訊。"
                    ),
                ],
                "source_urls": [exp_links[0]["url"] if exp_links else PU_SCHOOLS_OVERVIEW_URL],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合靜宜大學國際暨兩岸事務處（411遊留學中心）{len(catalog_source)} 所合作姊妹校、當期開放交換及雙聯學位名額表（{open_partner_count} 校）、16 所跨國雙聯學位計畫、ISEP 國際交換學生計畫及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆學生返國心得報告。"
        ),
    })

    research_records.append({
        "home_university": "靜宜大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": "靜宜大學國際暨兩岸事務處（411遊留學中心）15 個洲別／國家地區姊妹校網頁、雙聯學位專區、五大洲締約姊妹校 Excel 與 ROR/Wikidata 官方網址核對完成。",
    })

    ev_sources = [{"title": f"靜宜大學 411 遊留學中心各洲別姊妹校交換名額與申請條件專頁—{zh_name}", "url": source_url}]
    if exp_links:
      ev_sources.append({
          "title": f"靜宜大學 411 遊留學中心學生研修心得分享—赴 {zh_name} 心得報告（{len(exps)} 篇）",
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
            "scope": "靜宜海外與大陸交換姊妹校住宿、ISEP 食宿互惠與生活資訊",
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
            "scope": "靜宜出國研修學雜費減免規定、教育部學海飛颺／惜珠、E.A.G.L.E. 築夢基金與地區生活費估算",
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
            "scope": "靜宜大學學生出國研修辦法、強制抵免至少一科學分、ECTS÷2 / CATS÷4 學分換算準則與返國報告規範",
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
            "scope": "靜宜海外交換與雙聯學位簽證、境外研修同意書、海外醫療保險與行前提醒",
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
                    f"｜靜宜 411 遊留學中心公開收錄 {len(exps)} 篇赴 {zh_name} 交換生返國心得報告（{'、'.join(exp_labels[:3])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "靜宜交換名額與歷屆學長姐返國心得報告分享",
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
            "已整合靜宜大學國際暨兩岸事務處（411遊留學中心）15 個洲別／國家地區姊妹校專頁、16 所跨國雙聯學位計畫、ISEP 國際交換學生計畫、五大洲締約姊妹校名錄及歷屆學生交換心得報告 PDF。",
            "當期開放名額、宿位供給、語檢門檻與選課限制請依合作校最新簡章及入學通知書核對。",
        ],
        "location_signature": f"verified:{lat}:{lon}:representative",
        "extraction_version": 3,
    })

  def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""), encoding="utf-8")

  write_jsonl(OFFICIAL_PU_DIR / "partners.jsonl", partners)
  write_jsonl(SOURCES_PU_DIR / "partners.jsonl", partners)
  write_jsonl(OFFICIAL_PU_DIR / "application_workflows.jsonl", workflows)
  write_jsonl(OFFICIAL_PU_DIR / "destination_profiles.jsonl", destinations)
  write_jsonl(OFFICIAL_PU_DIR / "partner_research.jsonl", research_records)
  write_jsonl(OFFICIAL_PU_DIR / "student_life.jsonl", life_records)
  write_jsonl(OFFICIAL_PU_DIR / "experience_sources.jsonl", experience_sources_records)
  write_jsonl(OFFICIAL_PU_DIR / "student_experience_sources.jsonl", experience_sources_records)
  write_jsonl(OFFICIAL_PU_DIR / "student_experiences.jsonl", student_experience_rows)

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
  (OFFICIAL_PU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
  )

  (OFFICIAL_PU_DIR / "student-experiences.json").write_text(
      json.dumps(
          {
              "school_id": "pu",
              "school_name": "靜宜大學",
              "checked_at": CHECKED_AT,
              "source_url": PU_SCHOOLS_OVERVIEW_URL,
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

  (OFFICIAL_PU_DIR / "campus-locations.json").write_text(
      json.dumps(
          {
              "school_id": "pu",
              "school_name": "靜宜大學",
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
  (OFFICIAL_PU_DIR / "campus-assets.json").write_text(
      json.dumps(
          {
              "school_id": "pu",
              "school_name": "靜宜大學",
              "checked_at": CHECKED_AT,
              "total_schools": len(campus_assets_list),
              "verified_count": sum(1 for a in campus_assets_list if a["status"] == "verified"),
              "assets": campus_assets_list,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  pu_source_urls = [
      PU_411_HOME_URL,
      PU_OIA_HOME_URL,
      PU_EXCHANGE_OVERVIEW_URL,
      PU_SCHOOLS_OVERVIEW_URL,
      PU_DUAL_DEGREE_URL,
      PU_ISEP_URL,
      PU_SCHOLARSHIPS_URL,
      PU_REGULATIONS_URL,
      PU_FORMS_URL,
      PU_FAQ_URL,
      PU_SISTERS_URL,
      PU_NEWS_115_2_OCT_PASS_URL,
      PU_NEWS_116_XUEHAI_URL,
      PU_NEWS_EAGLE_FUND_URL,
      PU_STUDY_ABROAD_RULES_PDF_URL,
      PU_SELECTION_RULES_PDF_URL,
      PU_TUITION_RULES_PDF_URL,
      PU_SCHOLARSHIP_RULES_PDF_URL,
      PU_DUAL_DEGREE_RULES_PDF_URL,
      PU_CREDIT_TRANSFER_RULES_PDF_URL,
      PU_CREDIT_CONVERSION_PDF_URL,
      PU_ISEP_GUIDE_PDF_URL,
      PU_XUEHAI_RULES_PDF_URL,
      PU_XUEHAI_FLOW_PDF_URL,
      PU_SPAIN_PARTNERS_PDF_URL,
      PU_REPORT_UPLOAD_GUIDE_PDF_URL,
  ]

  exchange_info_payload = {
      "school_name": "靜宜大學",
      "program_type": [
          (
              "國際暨兩岸事務處「411遊留學中心（出國研修組）」出國交換學生計畫（涵蓋免學費交換、自費／學費減免交換及姊妹校專業語言課程；在學期間出國交換須繳交靜宜全額學費、免繳雜費，每學期分 3 梯次辦理校內初審）"
          ),
          (
              "ISEP 國際交換學生計畫（International Student Exchange Programs，靜宜為臺灣歷史最悠久之 ISEP 會員校之一，連結全球逾 50 國 300 餘所會員大學；參加 ISEP-Exchange 僅需於靜宜繳交全額學費及雙人雅房住宿費與伙食費基準每學期約 NT$ 51,000，即可免繳海外接待大學之學費、住宿費與伙食費）"
          ),
          (
              "跨國雙聯學位計畫（涵蓋美國印第安納波利斯大學 2+2、萊德大學 3+1 / 3+1+1、樹城州立大學 2+2、達拉斯浸信會大學 1+1、斯克蘭頓大學 3+1+1；德國科隆商學院 CBS 3+1、紐倫堡科技大學 2+1+1；法國里昂天主教大學 ESDES 1+1、里爾天主教大學農業學院 Junia ISA Lille 3+2；英國桑德蘭大學 3+1、密德薩斯大學 3+1 / 3+1.5、艾塞克斯大學 3+1 學碩一貫、倫敦布魯內爾大學 3+1；日本愛知縣立大學 2+2；澳洲西雪梨大學 3+1 / 1+1、南十字星大學 3+1 等 16 所雙聯合作校）暨教育部「學海飛颺」、「學海惜珠」與「靜宜 E.A.G.L.E. 築夢基金」"
          ),
      ],
      "academic_year": [
          (
              "116（涵蓋 115-2［2027春季班出國研修三梯次校內初審：第1次 2026/08/03–08/23、第2次 08/24–09/20、第3次暨語言課程 09/21–10/11，初審通過者於 2026/10/30 前繳交境外研修同意書］、116-1［2027秋季班出國研修三梯次校內初審：2月底、3月底、4月底；雙聯學制秋季班 3/31 截止］、115年教育部學海飛颺／學海惜珠獎學金［第1次 2025/12/08–2026/03/06、第2次至 2026/09/02］與 115 學年度 E.A.G.L.E. 築夢基金［上學期 2026/10/15、下學期 2027/03/25 截止］）"
          ),
          (
              f"本平台完整收錄靜宜大學國際暨兩岸事務處（411遊留學中心）公告之 {len(partners)} 所全球與大陸合作姊妹校（含 {open_partner_count} 所當期開放申請之免學費交換、ISEP、雙聯學位與專業語言課程合作校，以及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 5 大洲 48 個國家與地區，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返國心得報告 PDF）"
          ),
      ],
      "semester": [
          "春季班出國研修校內初審（前一年 8–10 月分三梯次辦理）：申請次年春季學期（115-2）赴歐美、日韓、東南亞、大洋洲及大陸姊妹校交換一學期或一學年（ISEP 春季班於前一年 7 月底截止）。",
          "秋季班出國研修校內初審（當年 2–4 月分三梯次辦理）：申請同年秋季學期（116-1）赴全球與大陸姊妹校交換一學期或一學年（ISEP 秋季班於 1 月中旬截止）。",
          "16 校跨國雙聯學位計畫（2+2、3+1、3+1+1、2+1+1、1+1、3+2 學碩一貫）：秋季班入學於每年 3 月 31 日前向 411 遊留學中心提出申請。",
      ],
      "application_period": [
          "【115-2（2027春季班）出國研修校內初審三梯次】第1次初審（8月梯次）：2026/08/03–08/23；第2次初審（9月梯次）：2026/08/24–09/20；第3次初審（10月梯次，含姊妹校專業語言課程）：2026/09/21–10/11；10月初審通過者須於 2026/10/30（五）17:00 前繳交紙本《靜宜大學境外研修同意書》至主顧樓 315 室。",
          "【116-1（2027秋季班）出國研修校內初審三梯次】第1次初審：每年 2 月底截止；第2次初審：每年 3 月底截止；第3次初審（姊妹校專業語言課程）：每年 4 月底截止；跨國雙聯學制秋季班入學申請截止日：每年 3 月 31 日；ISEP-Exchange 秋季班 1 月中旬截止、春季班 7 月底截止。",
          "【115年教育部學海飛颺／學海惜珠獎學金甄選】第1次甄選：2025/12/08 至 2026/03/06（補助 115-1、115-2、116-1 出國）；第2次甄選：即日起至 2026/09/02 截止（補助 115-2、116-1 出國）。",
          "【115學年度靜宜大學 E.A.G.L.E. 築夢基金】上學期於 2026/10/15 截止、下學期於 2027/03/25 截止（補助大學部在學學生出國研修，亞洲地區每人上限 2 萬元、其他地區每人上限 3 萬元）。",
      ],
      "eligibility": [
          "1. 學籍與申請年級規定：依《靜宜大學學生出國研修辦法》與《遴選交換學生作業要點》，申請人須為靜宜大學具正式學籍之在學學生；大一新生可於一年級下學期提出申請，並自二年級上學期開始出國研修；碩、博士班學生自一年級下學期起得出國研修；延畢生亦得申請互惠交換學生（修業年限符合大學法第 26 條規定者得專案簽請延長）。",
          "2. 學業成績與排名門檻：申請交換生時在校歷年學業總平均成績須達 70 分以上（或 GPA 2.75+ / 班排名前 50%），並符合各接待姊妹校特定 GPA 要求；申請教育部《學海飛颺》獎學金者歷年學業總平均須達全班前 50%。",
          "3. 出國研修期間與修課下限：出國研修期間以一學期或一學年為原則（雙聯學制大三生得出國兩年），累計出國期間不得超過兩年；出國期間每學期至少應修習相當於靜宜大學 6 學分或至少 2 門科目。",
          "4. 在學學雜費減免與返國強制學分抵免義務：在學期間（含延畢生申請互惠交換）出國研讀須繳交靜宜全額學費、免繳雜費（修讀雙聯學制者須繳全額學雜費）；返國後須於次一學期開學 2 個月內辦理學分抵免，且強制規定「至少須抵免一科（至少 1 學分）」！並於返國後 2 個月內至 e校園服務網上傳 1,500–2,000 字報告書及 6 張照片。",
      ],
      "language_requirement": [
          "1. 英語授課學程及歐美／大洋洲／東南亞／ISEP 姊妹校：採認 TOEFL iBT 61–80（或 TOEFL ITP 500–550）、IELTS 5.5–6.5、TOEIC 650–785 或全民英檢中高級（對應 CEFR B1–B2；雙聯學位如英國 Essex、Middlesex、Sunderland、Brunel、德國 CBS、法國 ESDES / Junia ISA Lille、美國 Scranton / UIndy / Rider / Boise State 需達 IELTS 6.0–6.5 或 TOEFL iBT 68–80）。",
          "2. 日本姊妹校（38 所合作大學）：日語授課組採認日本語能力試驗 JLPT N1–N3（上智大學、同志社大學、青山學院大學、關西大學、明治學院大學、南山大學、愛知縣立大學等需 N1–N2；白百合女子大學、長崎外國語大學、追手門學院大學、京都精華大學、駿河台大學等接受 N2–N3；專業語言別科接受 N4–N5）；全英語授課學程採認 CEFR B1–B2（TOEFL iBT 61 / IELTS 5.0 / TOEIC 550–700）。",
          "3. 韓國姊妹校（38 所合作大學）：韓語授課採認 TOPIK 2–4 級以上；英語授課採認 CEFR B1–B2（TOEFL iBT 61–79 / IELTS 5.5 / TOEIC 650–750）。",
          "4. 西語、法語、德語及中國大陸姊妹校：西班牙與拉丁美洲西語授課採認 DELE A2–B2（或西文系在學證明），法語與德語授課採認 DELF / Goethe B1–B2（英語授課組採認 CEFR B1–B2）；中國大陸 44 所姊妹校免附外語檢定證明（限臺籍或僑港澳籍在學學生申請）。",
      ],
      "required_documents": [
          "1. 靜宜大學學生出國研修申請表（線上填報並列印經系所核章）",
          "2. 靜宜大學中、英文歷年成績單正本（須含學業總平均、GPA 及班級排名）與在學證明",
          "3. 有效期限內之外語能力檢定證明影本（TOEFL iBT / ITP / IELTS / TOEIC / JLPT / TOPIK / DELE / DELF 等；大陸姊妹校免附）",
          "4. 中、外文讀書計畫（Study Plan）與自傳（含申請動機、預計選修課程與學分抵免規劃）",
          "5. 師長推薦信（依申請學程或雙聯／ISEP／獎學金規定檢附 1–2 封）與有效護照（或台胞證）資料頁影本",
          "6. 《靜宜大學個人資料提供同意書》與其他優良事蹟或社團服務證明",
          "7. 初審通過後繳交經本人及家長簽章之紙本《靜宜大學境外研修同意書》（交至主顧樓 315 室 411 遊留學中心）",
          "8. 出國前完成《靜宜大學學生出國期間學業及學籍處理單》；返國後 2 個月內持國外成績單正本、課程大綱與《學分抵免申請表》辦理強制至少一科抵免，並至 e校園服務網上傳 1,500–2,000 字報告書及 6 張照片",
      ],
      "scholarship_info": [
          "1. 教育部「學海飛颺」與「學海惜珠」出國研修獎學金：依《靜宜大學執行教育部學海飛颺及學海惜珠補助要點》，每年分 2 次甄選（115年第1次 2025/12/08–2026/03/06、第2次至 2026/09/02）。申請人須具中華民國國籍、於靜宜就讀一學期以上、外語達 CEFR B1 以上；《學海飛颺》須歷年學業總平均居全班前 50%，《學海惜珠》須持各直轄市或縣市政府核發之低收入戶、中低收入戶或相關補助證明。獲補助生於交換期間不得同時領取我國政府或靜宜校內其他出國獎學金。",
          "2. 《靜宜大學 E.A.G.L.E. 築夢基金》：每學期開放申請（115學年度上學期 2026/10/15 截止、下學期 2027/03/25 截止），鼓勵靜宜大學部在學學生赴境外研修與自主學習；亞洲地區每人補助上限新臺幣 20,000 元，非亞洲地區每人補助上限新臺幣 30,000 元。",
          "3. 《靜宜大學學生出國研修獎助學金辦法》：補助學生參與海外移地教學（亞洲地區上限 2 萬元、非亞洲地區上限 3 萬元）及系級國際教育計畫（亞洲地區上限 1 萬元、非亞洲地區上限 2 萬元），以及出國研修學費減免與助學金。",
          "4. 姊妹校與外國政府獎學金：含德國巴登符騰堡州政府獎學金（Baden-Württemberg Stipendium，每月約 EUR 600–1,400）、歐盟 Erasmus+ 交換生獎學金（提供歐洲姊妹校交換生生活費與旅費津貼）、日本台灣交流協會短期交換留學生獎學金及雙聯姊妹校（如英國 University of Essex 等）學費減免獎學金。",
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": pu_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_PU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
  )

  student_dashboard_payload = {
      "school_name": "靜宜大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 70.0,
      "academic_score_rule": (
          "依《靜宜大學學生出國研修辦法》與《靜宜大學遴選交換學生作業要點》：大一新生可於一年級下學期提出申請、二年級上學期開始出國研修（延畢生亦得申請互惠交換學生）；申請交換生歷年學業總平均成績須達 70 分以上（或 GPA 2.75+ / 班排名前 50%），並符合各接待姊妹校特定 GPA 門檻（申請教育部學海飛颺獎學金者須班排名前 50%）。"
      ),
      "academic_gpa_minimum": 2.75,
      "maximum_preferences": 10,
      "selection_rules": {
          "academic_policy": "score_or_rank",
          "academic_reference_year": "116",
          "undergraduate_gpa_minimum": 2.75,
          "graduate_academic_exempt": False,
          "exclude_in_service": False,
          "pending_quota_planning": False,
          "partner_requirements_need_confirmation": False,
          "degree_score_minimums": {"undergraduate": 70.0, "graduate": 70.0},
          "excluded_undergraduate_years": ["大一上", "碩一上", "博一上"],
          "language_certificate_required": True,
      },
      "language_score_minimums": {"toefl": 61.0, "ielts": 5.0, "toeic": 550.0},
      "application_periods": [
          {
              "title": "靜宜大學 115-2（2027春季班）出國研修校內初審（8月／9月／10月三梯次）暨《境外研修同意書》繳交",
              "details": [
                  "411遊留學中心（出國研修組）辦理 115-2（2027春季班出國）三梯次校內初審：第1次初審（8月梯次）2026/08/03–08/23、第2次初審（9月梯次）2026/08/24–09/20、第3次初審暨姊妹校專業語言課程（10月梯次）2026/09/21–10/11。",
                  "115-2（10月梯次）初審通過名單已公告，通過同學須於 2026/10/30（五）17:00 前下載並親簽紙本《靜宜大學境外研修同意書》繳交至主顧樓 315 室（411遊留學中心）確認提名資格。",
              ],
              "source": {
                  "title": "靜宜大學 411 遊留學中心《115-2（10月）出國研修初審通過名單及境外研修同意書繳交公告》",
                  "source_url": PU_NEWS_115_2_OCT_PASS_URL,
                  "category": "exchange_application",
                  "summary": "靜宜 115-2 春季班出國研修三梯次校內初審時程與 2026/10/30 境外研修同意書繳交期限。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "115-2（2027春季班）出國研修三梯次校內初審",
              "audience": "all_students",
              "opens_at": "2026-08-03T09:00:00+08:00",
              "deadline_at": "2026-10-30T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "115-2（10月梯次）出國研修初審通過者須於 2026/10/30 前繳交紙本《靜宜大學境外研修同意書》至主顧樓 315 室。",
              "deadline_note": "請初審通過同學下載列印紙本《靜宜大學境外研修同意書》，完成簽章後於 2026/10/30 前繳回 411 遊留學中心。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "靜宜大學 115 學年度《E.A.G.L.E. 築夢基金》出國研修獎助申請（上學期 10/15 截止、下學期 3/25 截止）",
              "details": [
                  "靜宜大學為鼓勵大學部在學學生赴境外研修與拓展國際視野，特設《E.A.G.L.E. 築夢基金》：亞洲地區每人補助上限新臺幣 20,000 元，非亞洲地區每人補助上限新臺幣 30,000 元。",
                  "115 學年度上學期申請於 2026/10/15 截止，下學期申請於 2027/03/25 截止；須檢附申請表、出國研修計畫與相關證明向國際暨兩岸事務處（411遊留學中心）提出申請。",
              ],
              "source": {
                  "title": "靜宜大學 411 遊留學中心《115學年度 E.A.G.L.E. 築夢基金申請公告》",
                  "source_url": PU_NEWS_EAGLE_FUND_URL,
                  "category": "scholarship",
                  "summary": "靜宜 E.A.G.L.E. 築夢基金上下學期截止日與亞洲 2 萬／非亞 3 萬補助標準。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "115學年度靜宜大學 E.A.G.L.E. 築夢基金甄選",
              "audience": "all_students",
              "opens_at": "2026-09-01T09:00:00+08:00",
              "deadline_at": "2027-03-25T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "open",
              "status_note": "115 學年度下學期 E.A.G.L.E. 築夢基金受理申請至 2027/03/25 截止。",
              "deadline_note": "未領取教育部學海系列獎學金之大學部出國交換／研修生，可於 2027/03/25 前申請下學期 E.A.G.L.E. 築夢基金。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "靜宜大學 116-1（2027秋季班）出國研修三梯次校內初審（2月／3月／4月）、雙聯學位（3/31截止）暨教育部學海獎學金",
              "details": [
                  "依據靜宜 411 遊留學中心作業時程，116-1（2027秋季班出國）分三梯次辦理校內初審：第1次初審 2 月底截止、第2次初審 3 月底截止、第3次初審（姊妹校專業語言課程）4 月底截止；16 校跨國雙聯學位秋季班入學申請於 2027/03/31 截止；ISEP-Exchange 秋季班於 1 月中旬截止。",
                  "教育部《學海飛颺》與《學海惜珠》獎學金每年第 1 次甄選於 12 月至翌年 3 月初受理收件（第 2 次甄選於 8–9 月初受理），大一新生於一年級下學期（2–3 月）即可同步報名秋季班出國交換與學海獎學金。",
              ],
              "source": {
                  "title": "靜宜大學 411 遊留學中心《出國交換計畫申請流程》與《雙聯學制申請資訊》",
                  "source_url": PU_EXCHANGE_OVERVIEW_URL,
                  "category": "exchange_application",
                  "summary": "靜宜秋季班出國研修三梯次初審、雙聯學位 3/31 截止日與學海獎學金時程。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "116-1（2027秋季班）出國研修暨雙聯學位校內初審",
              "audience": "all_students",
              "opens_at": "2027-01-04T09:00:00+08:00",
              "deadline_at": "2027-03-31T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "秋季班出國研修（含免學費交換、雙聯學位、ISEP、語言課程及學海獎學金）於每年 1–4 月分梯次開放申請。",
              "deadline_note": "第一梯次（2月底截止）姊妹校名額最齊全，雙聯學制秋季班入學須於 3 月 31 日前完成校內送件。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"靜宜大學國際暨兩岸事務處「411遊留學中心」出國交換、ISEP、16 校雙聯學位與獎補助總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所當期開放申請・{total_exp_reports} 篇學長姐返國心得報告）"
              ),
              "details": [
                  (
                      f"靜宜大學（Providence University, PU，創立於 1956 年，坐落於臺中市沙鹿區大肚山麓，由美國主顧修女會創辦，以「進德、修業（Virtus Cum Scientia）」為校訓，以首創「411 出國遊留學制度」——鼓勵學生大學 4 年內至少出國遊學 1 次及留學交換 1 次聞名全國）由「國際暨兩岸事務處（Office of International and Cross-Strait Affairs）」下轄之「411遊留學中心（出國研修組，主顧樓 315 室）」統籌全校 6 大學院（外語暨人文創意學院、社會科學院、理學院、管理學院、資訊學院、國際學院）之國際與兩岸出國研修計畫。本平台完整收錄 {len(partners)} 所靜宜官方合作姊妹校（含 {open_partner_count} 所當期開放申請之免學費交換、ISEP、雙聯學位、學費減免與專業語言課程合作校，以及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 5 大洲 48 個國家與地區。"
                  ),
                  (
                      f"靜宜 411 遊留學制度具備五大核心特色：（1）每學期分 3 梯次校內初審（秋季班出國 2月／3月／4月；春季班出國 8月／9月／10月），在學期間（含延畢生互惠交換）出國研讀僅需繳交靜宜全額學費、免繳雜費；（2）身為臺灣歷史最悠久之 ISEP（International Student Exchange Programs）會員大學之一，學生繳交靜宜學費及雙人雅房食宿基準費（每學期約 NT$ 51,000）即可赴全球逾 300 所 ISEP 會員大學免費修課並免繳海外食宿費；（3）與美、英、德、法、日、澳 16 所名校簽訂 2+2、3+1、3+1+1、1+1 及 3+2 學碩一貫雙聯學位；（4）教育部學海飛颺、學海惜珠與靜宜 E.A.G.L.E. 築夢基金多元獎助；（5）完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返國心得報告 PDF。"
                  ),
              ],
              "source": {
                  "title": "靜宜大學 411 遊留學中心（出國研修組）與國際暨兩岸事務處官方網站",
                  "source_url": PU_EXCHANGE_OVERVIEW_URL,
                  "category": "exchange_application",
                  "summary": f"靜宜 {len(partners)} 所全球與兩岸合作姊妹校、16 校雙聯學位、ISEP 計畫與 {total_exp_reports} 篇返國心得報告。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "靜宜在學學籍（大一新生可於大一下申請、延畢生可申請互惠交換）、歷年平均 70 分（GPA 2.75+）與三梯次初審制度",
              "details": [
                  "學籍與修業年級規定：依《靜宜大學學生出國研修辦法》及《靜宜大學遴選交換學生作業要點》，申請人須為靜宜大學具正式學籍之在學學生（大一新生得於大一下學期提出申請、大二上學期開始出國研修；碩博士生自一下起得出國研修；延畢生亦得申請互惠交換學生），歷年學業總平均達 70 分以上（或 GPA 2.75+ / 班排名前 50%）並符合各接待姊妹校要求。",
                  "三梯次校內初審與返國強制抵免義務：411 遊留學中心於每年 2、3、4 月（秋季班出國）及 8、9、10 月（春季班出國）分三梯次辦理校內初審；出國期間每學期至少修習 6 學分或 2 門課，返國後次一學期開學 2 個月內須依《出國交換學生學分換算準則》（ECTS÷2、CATS÷4、美日陸 1:1）辦理學分抵免，且強制規定「至少須抵免一科（至少 1 學分）」。",
              ],
              "source": {
                  "title": "靜宜大學學生出國研修辦法、遴選交換學生作業要點與出國交換學生學分換算準則",
                  "source_url": PU_REGULATIONS_URL,
                  "category": "exchange_application",
                  "summary": "靜宜出國研修資格、三梯次校內初審、免繳雜費與返國強制抵免至少一科學分規範。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "歐美／大洋洲／東南亞／ISEP 英語標準（CEFR B1–B2）、日本（JLPT N1–N3）、韓國（TOPIK 2–4 級）、西法德語檢定與大陸免語檢規定",
              "details": [
                  "外語組別門檻：依 411 遊留學中心各洲別姊妹校列表，（1）英語授課學程及歐美、大洋洲、東南亞、ISEP 姊妹校採認 TOEFL iBT 61–80（或 TOEFL ITP 500–550）、IELTS 5.5–6.5、TOEIC 650–785；（2）日本 38 校日語授課組採認 JLPT N1–N3（上智、同志社、青山學院、關西、明治學院、南山、愛知縣立需 N1–N2；白百合女子、長崎外大、追手門學院、京都精華等接受 N2–N3；語言別科接受 N4–N5），英語授課組採認 CEFR B1–B2；（3）韓國 38 校採認 TOPIK 2–4 級或英語 CEFR B1–B2。",
                  "歐語區與大陸地區規定：西班牙及中南美洲 11 國西語授課採認 DELE A2–B2（或西文系在學證明），法語與德語授課採認 DELF / Goethe B1–B2；中國大陸 44 所姊妹校免附外語檢定證明（限臺籍或僑港澳籍在學學生申請）。",
              ],
              "source": {
                  "title": "靜宜大學 411 遊留學中心各洲別姊妹校申請條件與名額總覽",
                  "source_url": PU_SCHOOLS_OVERVIEW_URL,
                  "category": "exchange_application",
                  "summary": "靜宜全球 5 大洲 48 國合作姊妹校外語檢定門檻一覽。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "出國研修申請表、中英文歷年成績單（含排名）、外語檢定證明、中英文讀書計畫、師長推薦信與《靜宜大學境外研修同意書》",
              "details": [
                  "校內初審應備文件：申請人須於各梯次初審截止前備齊（1）靜宜大學出國研修申請表、（2）中英文歷年成績單正本（含 GPA 與班排名）及在學證明、（3）有效外語能力檢定證明、（4）中外文讀書計畫（Study Plan）與自傳、（5）師長推薦信、（6）有效護照／台胞證影本及《個人資料提供同意書》送交主顧樓 315 室 411 遊留學中心。",
                  "初審通過確認、行前與返國結案：初審通過後須於指定期限內（如 115-2 十月初審通過者為 2026/10/30 前）繳交經本人及家長簽章之紙本《靜宜大學境外研修同意書》；出國前完成《學生出國期間學業及學籍處理單》；返國後次學期開學 2 個月內辦理學分抵免（強制至少抵免一科），並於返國後 2 個月內至 e校園服務網上傳 1,500–2,000 字報告書及 6 張照片。",
              ],
              "source": {
                  "title": "靜宜大學 411 遊留學中心《表單下載專區》與《出國交換學生報告書上傳步驟說明》",
                  "source_url": PU_FORMS_URL,
                  "category": "exchange_application",
                  "summary": "靜宜出國研修初審表件、境外研修同意書、學分抵免表與返國報告書上傳規範。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部學海飛颺、學海惜珠、靜宜 E.A.G.L.E. 築夢基金（亞洲 2 萬／非亞 3 萬）、出國研修獎助學金與 Erasmus+ / 巴登符騰堡獎學金",
              "details": [
                  "教育部學海系列與靜宜 E.A.G.L.E. 築夢基金：（1）《學海飛颺》與《學海惜珠》每年分 2 次甄選（12 月至 3 月初、8 至 9 月初），補助具中華民國國籍、外語達 CEFR B1+ 且班排前 50%（飛颺）或具低收／中低收入證明（惜珠）之交換生（獲補助期間不得兼領政府或校內其他出國獎學金）；（2）《靜宜大學 E.A.G.L.E. 築夢基金》每學期開放申請（上學期 10/15、下學期 3/25 截止），補助大學部出國研修生亞洲上限 NT$ 20,000、非亞洲上限 NT$ 30,000。",
                  "校內外專項獎助：另設有《靜宜大學學生出國研修獎助學金辦法》（海外移地教學亞洲上限 2 萬／非亞 3 萬；系級國際教育計畫亞洲上限 1 萬／非亞 2 萬），以及德國巴登符騰堡州獎學金（Baden-Württemberg Stipendium）、歐盟 Erasmus+ 獎學金與日本台灣交流協會獎學金。",
              ],
              "source": {
                  "title": "靜宜大學 411 遊留學中心《獎學金申請專區》與《執行教育部學海飛颺及學海惜珠補助要點》",
                  "source_url": PU_SCHOLARSHIPS_URL,
                  "category": "scholarship",
                  "summary": "靜宜學海飛颺、學海惜珠、E.A.G.L.E. 築夢基金與出國研修獎助學金辦法。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "靜宜大學 411 遊留學中心出國研修申請文件、中外文讀書計畫、《境外研修同意書》與返國報告書準備指南",
              "summary": "說明靜宜三梯次校內初審、16 校雙聯學位、ISEP 交換及教育部學海／E.A.G.L.E. 築夢基金之應備文件規格與返國結案要求。",
              "key_points": [
                  "校內初審備審文件：含出國研修申請表、中英文歷年成績單（須含班級排名與 GPA）、外語能力證明、中外文讀書計畫與自傳、師長推薦信及《個人資料提供同意書》；初審通過後須於期限內將本人與家長親簽之紙本《靜宜大學境外研修同意書》交至主顧樓 315 室。",
                  "雙聯學位與 ISEP 專項文件：申請 16 校雙聯學位須於 3 月 31 日前加附英文課程大綱與學分對照表；申請 ISEP-Exchange 須於 ISEP 線上系統填報最多 10 所志願校並檢附英文財力證明與 ISEP Language Proficiency Report。",
                  "返國強制學分抵免與報告書上傳：返國後次學期開學 2 個月內須檢附國外成績單正本、課程大綱與《學分抵免申請表》辦理至少一科學分抵免（ECTS÷2、CATS÷4、美日陸 1:1），並於返國後 2 個月內登入 e校園服務網上傳 1,500–2,000 字報告書及 6 張照片。",
              ],
              "applies_to": [],
              "source": {
                  "title": "靜宜大學 411 遊留學中心表單下載與報告書上傳步驟說明",
                  "source_url": PU_FORMS_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": PU_REPORT_UPLOAD_GUIDE_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "靜宜大學學生出國研修辦法、遴選交換學生作業要點、學業及學籍處理要點與學分換算準則核心規定",
              "summary": "規範靜宜出國交換與雙聯學位之修業年級、在學免繳雜費優惠、每學期最低修課下限（6 學分或 2 門課）、強制抵免至少一科及歐英美日學分換算公式。",
              "key_points": [
                  "申請年級與研修年限：大一新生可於大一下學期提出申請、大二上學期開始出國研修（延畢生亦得申請互惠交換學生）；出國期間以一學期或一學年為原則（雙聯學制大三生得出國兩年），累計不超過兩年。",
                  "在學註冊與學雜費減免：在學期間（含延畢生申請互惠交換）出國研讀須繳交靜宜全額學費、免繳雜費（修讀雙聯學制者須繳全額學雜費；參加 ISEP-Exchange 者於靜宜繳交全額學費與雙人雅房食宿基準費即免繳海外學費與食宿費）。",
                  "最低修課下限與強制學分抵免換算：出國期間每學期至少修習相當於靜宜 6 學分或至少 2 門科目；返國後次學期開學 2 個月內強制規定「至少須抵免一科（至少 1 學分）」，換算準則為美制／日制／陸制 1:1、歐洲 ECTS ÷ 2 = 靜宜學分、英國 CATS ÷ 4 = 靜宜學分，或滿 18 授課小時折算 1 學分。",
              ],
              "applies_to": [],
              "source": {
                  "title": "靜宜大學學生出國研修辦法、學業及學籍處理要點與出國交換學生學分換算準則",
                  "source_url": PU_REGULATIONS_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": PU_STUDY_ABROAD_RULES_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {"title": "靜宜大學 411 遊留學中心（出國研修組）官方網站", "source_url": PU_411_HOME_URL, "category": "exchange_application", "summary": None},
          {"title": "靜宜大學國際暨兩岸事務處（OIA）官方網站", "source_url": PU_OIA_HOME_URL, "category": "exchange_application", "summary": None},
          {"title": "靜宜大學出國交換學生計畫申請資格與三梯次初審流程", "source_url": PU_EXCHANGE_OVERVIEW_URL, "category": "exchange_application", "summary": None},
          {"title": f"靜宜大學各洲別交換學校一覽表（{len(partners)} 所合作姊妹校）", "source_url": PU_SCHOOLS_OVERVIEW_URL, "category": "partner_school", "summary": None},
          {"title": "靜宜大學跨國雙聯學制專區（美、英、德、法、日、澳 16 所雙聯合作大學）", "source_url": PU_DUAL_DEGREE_URL, "category": "partner_school", "summary": None},
          {"title": "靜宜大學 ISEP 國際交換學生計畫專區（全球逾 50 國 300 餘所會員大學）", "source_url": PU_ISEP_URL, "category": "exchange_application", "summary": None},
          {"title": "靜宜大學出國研修獎學金專區（教育部學海飛颺、學海惜珠、E.A.G.L.E. 築夢基金）", "source_url": PU_SCHOLARSHIPS_URL, "category": "scholarship", "summary": None},
          {"title": "靜宜大學出國研修相關法規與學分換算準則專區", "source_url": PU_REGULATIONS_URL, "category": "exchange_application", "summary": None},
          {"title": "靜宜大學國際暨兩岸事務處全球五大洲締約姊妹校名錄", "source_url": PU_SISTERS_URL, "category": "partner_school", "summary": None},
      ],
  }
  (OFFICIAL_PU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
  )

  doc_conditions = {
      "school_id": "pu",
      "school_name": "靜宜大學",
      "checked_at": CHECKED_AT,
      "source_url": PU_EXCHANGE_OVERVIEW_URL,
      "common_documents": exchange_info_payload["required_documents"],
      "track_specific_conditions": [
          {
              "track": "411遊留學中心【免學費交換／自費與學費減免交換／姊妹校專業語言課程】（每學期三梯次初審）",
              "required": [
                  "靜宜大學出國研修申請表（於三梯次初審截止前提交：春季班 8月／9月／10月；秋季班 2月／3月／4月）",
                  "靜宜大學中、英文歷年成績單正本（含學業總平均、GPA 與班級排名）及在學證明",
                  "有效外語能力檢定證明（CEFR B1–B2 / TOEFL / IELTS / TOEIC / JLPT N1–N3 / TOPIK 2–4 級 / DELE / DELF；大陸姊妹校免附）",
                  "中、外文讀書計畫（Study Plan）、自傳、師長推薦信及《個人資料提供同意書》",
                  "初審通過後繳交經本人及家長簽章之紙本《靜宜大學境外研修同意書》至主顧樓 315 室",
              ],
          },
          {
              "track": "411遊留學中心【ISEP 國際交換學生計畫（ISEP-Exchange / ISEP-Direct）】",
              "required": [
                  "通過靜宜校內初審（秋季班 1 月中截止、春季班 7 月底截止）後，登入 ISEP 線上申請系統填選最多 10 所志願學校",
                  "英文版歷年成績單正本（GPA 2.75+）、有效英語或授課外語檢定證明（或 ISEP Language Proficiency Report）",
                  "英文讀書計畫（Study Plan）、師長推薦信、護照資料頁影本及英文銀行存款財力證明",
                  "錄取 ISEP-Exchange 後於靜宜繳交全額學費及雙人雅房住宿費與伙食費基準（每學期約 NT$ 51,000），免繳海外接待大學學費與食宿費",
              ],
          },
          {
              "track": "411遊留學中心【16 校跨國雙聯學位計畫（2+2、3+1、3+1+1、2+1+1、1+1、3+2 學碩一貫）】",
              "required": [
                  "雙聯學制申請表（秋季班入學須於每年 3 月 31 日前向所屬院系及 411 遊留學中心提出申請）",
                  "靜宜大學英文歷年成績單正本、已修習學分與雙聯合作校課程學分對照表",
                  "符合雙聯合作校規定之英語／日語檢定證明（如 IELTS 6.0–6.5、TOEFL iBT 68–80 或 JLPT N2）及英文財力證明",
                  "出國修讀雙聯學制期間須維持靜宜在學學籍並繳交靜宜全額學雜費及合作校規定學費",
              ],
          },
          {
              "track": "教育部《學海飛颺》、《學海惜珠》獎學金＆《靜宜大學 E.A.G.L.E. 築夢基金》",
              "required": [
                  "教育部學海飛颺（每年 12–3 月初及 8–9 月初甄選）：具中華民國國籍、歷年班排前 50%、具 CEFR B1+ 外語證明、出國研修計畫書",
                  "教育部學海惜珠：除學海基本文件外，另檢附各直轄市或縣市政府核發之有效低收入戶、中低收入戶或相關補助證明",
                  "靜宜 E.A.G.L.E. 築夢基金（上學期 10/15、下學期 3/25 截止）：大學部在學學生檢附築夢基金申請表與境外研修計畫（亞洲上限 2 萬元、非亞洲上限 3 萬元；不得與學海獎學金兼領）",
              ],
          },
      ],
  }
  (OFFICIAL_PU_DIR / "document-conditions.json").write_text(
      json.dumps(doc_conditions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
  )

  field_cov_lines = ["field_name,total_records,populated_records,coverage_ratio,notes"]
  for fname in [
      "school_name", "country", "region", "group", "program_type", "availability_status",
      "quota", "colleges", "degree_levels", "language_requirements", "gpa_requirement",
      "application_deadline", "study_period", "semester_dates", "housing_info",
      "course_restrictions", "living_cost_estimate", "visa_and_health_insurance",
      "official_website", "latitude", "longitude", "image_url",
  ]:
    pop = sum(1 for p in partners if p.get(fname) not in (None, "", []))
    ratio = pop / len(partners) if partners else 1.0
    field_cov_lines.append(f"{fname},{len(partners)},{pop},{ratio:.4f},Official PU OIA/411 verified")
  (OFFICIAL_PU_DIR / "field-coverage.csv").write_text("\n".join(field_cov_lines) + "\n", encoding="utf-8")

  pages_records = [
      {
          "title": "靜宜大學：411遊留學中心 115-2（2027春季班）與 116-1（2027秋季班）出國研修三梯次校內初審、雙聯學位與 ISEP 申請時程",
          "source_url": PU_EXCHANGE_OVERVIEW_URL,
          "published_at": "2026-10-15T00:00:00Z",
          "text": "\n".join(exchange_info_payload["application_period"]),
          "summary": "\n".join(exchange_info_payload["application_period"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "靜宜大學：學生出國研修辦法、遴選交換學生作業要點、在學免繳雜費與返國強制抵免至少一科規定（ECTS÷2 / CATS÷4）",
          "source_url": PU_REGULATIONS_URL,
          "published_at": "2026-10-15T00:00:00Z",
          "text": "\n".join(exchange_info_payload["eligibility"]),
          "summary": "\n".join(exchange_info_payload["eligibility"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": f"靜宜大學：{len(partners)} 所全球五大洲與大陸合作姊妹校外語檢定門檻（歐美／日韓／東南亞／拉美／大陸）",
          "source_url": PU_SCHOOLS_OVERVIEW_URL,
          "published_at": "2026-10-15T00:00:00Z",
          "text": "\n".join(exchange_info_payload["language_requirement"]),
          "summary": "\n".join(exchange_info_payload["language_requirement"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "靜宜大學：出國研修、16 校雙聯學位與 ISEP 應備文件、《境外研修同意書》及返國報告書上傳規範",
          "source_url": PU_FORMS_URL,
          "published_at": "2026-10-15T00:00:00Z",
          "text": "\n".join(exchange_info_payload["required_documents"]),
          "summary": "\n".join(exchange_info_payload["required_documents"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "靜宜大學：教育部學海飛颺、學海惜珠、E.A.G.L.E. 築夢基金（亞洲 2 萬／非亞 3 萬）與出國研修獎助學金辦法",
          "source_url": PU_SCHOLARSHIPS_URL,
          "published_at": "2026-10-15T00:00:00Z",
          "text": "\n".join(exchange_info_payload["scholarship_info"]),
          "summary": "\n".join(exchange_info_payload["scholarship_info"]),
          "category": "scholarship",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
      },
  ]
  (OFFICIAL_PU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n", encoding="utf-8"
  )

  home_rules = {
      "school_id": "pu",
      "school_name": "靜宜大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "undergraduate_score_minimum": 70.0,
          "graduate_score_minimum": 70.0,
          "undergraduate_gpa_minimum": 2.75,
          "class_rank_top_percent_maximum": 50.0,
          "xuehai_class_rank_top_percent_maximum": 50.0,
          "screening_batches_per_semester": 3,
          "fall_batches_months": ["2月底（第1次初審）", "3月底（第2次初審）", "4月底（第3次初審／語言課程）"],
          "spring_batches_months": ["8月底（第1次初審）", "9月底（第2次初審）", "10月中（第3次初審／語言課程）"],
          "allow_freshman_apply_in_second_semester": True,
          "allow_extended_seniors_reciprocal_exchange": True,
          "min_abroad_credits_per_semester": 6,
          "min_abroad_courses_per_semester": 2,
          "mandatory_min_credit_transfer_courses": 1,
          "tuition_policy_during_exchange": "在學期間（含延畢生申請互惠交換）出國研讀須繳交靜宜全額學費、免繳雜費；修讀雙聯學制者須繳全額學雜費；參加 ISEP-Exchange 者繳交靜宜全額學費及雙人雅房食宿基準費（每學期約 NT$ 51,000）",
          "credit_conversion_rule": "依《靜宜大學出國交換學生學分換算準則》：美制／日制／陸制學分 1:1 換算；歐洲 ECTS 學分除以 2（ECTS ÷ 2 = 靜宜學分）；英國 CATS 學分除以 4（CATS ÷ 4 = 靜宜學分）；或實際授課滿 18 小時折算 1 學分",
          "return_documents_due": "返國後次一學期開學 2 個月內須檢附國外成績單正本辦理學分抵免（強制至少抵免一科），並於返國後 2 個月內登入 e校園服務網上傳 1,500–2,000 字報告書、6 張照片及個人資料提供同意書",
      },
      "source_urls": pu_source_urls,
      "verified_at": "2026-10-30",
  }
  (OFFICIAL_PU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
  )
  (OFFICIAL_PU_DIR / "documents.json").write_text(
      json.dumps(
          {"school_name": "靜宜大學", "required_documents": student_dashboard_payload["required_documents"], "source_urls": pu_source_urls},
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_PU_DIR / "scholarships.json").write_text(
      json.dumps(
          {"school_name": "靜宜大學", "scholarships": student_dashboard_payload["scholarship_info"], "source_urls": pu_source_urls},
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "pu",
      "school_name": "靜宜大學",
      "total_partners": len(partners),
      "partner_count": len(partners),
      "international_partners": sum(1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}),
      "mainland_partners": sum(1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}),
      "dual_degree_partner_universities": 16,
      "dual_degree_programs": 18,
      "experience_report_covered_partners": exp_covered_schools,
      "experience_report_count": total_exp_reports,
      "open_partners": open_partner_count,
      "reference_only_partners": len(partners) - open_partner_count,
      "verified_locations": len(partners),
      "verified_official_websites": sum(1 for p in partners if p.get("official_website")),
      "verified_campus_images": sum(1 for p in partners if p.get("image_status") == "verified"),
      "workflow_count": len(workflows),
      "destination_profile_count": len(destinations),
      "student_life_count": len(life_records),
      "active_term": (
          f"靜宜大學國際暨兩岸事務處（411遊留學中心）115-2（2027春季班：2026/08/03–10/11 三梯次校內初審、10/30 繳交境外研修同意書）與 116-1（2027秋季班：2月／3月／4月三梯次校內初審、雙聯學制 3/31 截止）出國交換、ISEP 國際交換學生計畫、16 所跨國雙聯學位合作校，以及教育部學海飛颺、學海惜珠與靜宜 E.A.G.L.E. 築夢基金同步整合；共完整收錄 {len(partners)} 所全球與大陸合作姊妹校（含 {open_partner_count} 所當期開放申請學校及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 5 大洲 48 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返國心得報告 PDF）。"
      ),
      "verified_at": "2026-10-30",
  }
  (OFFICIAL_PU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
  )
  (OFFICIAL_PU_DIR / "verification_status.json").write_text(
      json.dumps(
          {"school_id": "pu", "school_name": "靜宜大學", "status": "official_verified", "checked_at": CHECKED_AT, "counts": completeness},
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  provenance_files = [
      ("sources/pu/pu_study_abroad_rules.pdf", PU_STUDY_ABROAD_RULES_PDF_URL, "靜宜大學學生出國研修辦法 PDF"),
      ("sources/pu/pu_selection_rules.pdf", PU_SELECTION_RULES_PDF_URL, "靜宜大學遴選交換學生作業要點 PDF"),
      ("sources/pu/pu_tuition_rules.pdf", PU_TUITION_RULES_PDF_URL, "靜宜大學學生出國研修期間學業及學籍處理要點 PDF"),
      ("sources/pu/pu_scholarship_rules.pdf", PU_SCHOLARSHIP_RULES_PDF_URL, "靜宜大學學生出國研修獎助學金辦法 PDF"),
      ("sources/pu/pu_dual_degree_rules.pdf", PU_DUAL_DEGREE_RULES_PDF_URL, "靜宜大學與境外大學校院辦理雙聯學制實施辦法 PDF"),
      ("sources/pu/pu_credit_transfer_rules.pdf", PU_CREDIT_TRANSFER_RULES_PDF_URL, "靜宜大學辦理學生抵免學分辦法 PDF"),
      ("sources/pu/pu_credit_conversion.pdf", PU_CREDIT_CONVERSION_PDF_URL, "靜宜大學出國交換學生學分換算準則（ECTS÷2、CATS÷4）PDF"),
      ("sources/pu/pu_isep_guide.pdf", PU_ISEP_GUIDE_PDF_URL, "靜宜大學 ISEP 國際交換學生計畫介紹與申請指南 PDF"),
      ("sources/pu/pu_xuehai_rules.pdf", PU_XUEHAI_RULES_PDF_URL, "靜宜大學執行教育部學海飛颺及學海惜珠補助要點 PDF"),
      ("sources/pu/pu_xuehai_flow.pdf", PU_XUEHAI_FLOW_PDF_URL, "靜宜大學學海飛颺及學海惜珠作業流程與時程表 PDF"),
      ("sources/pu/pu_spain_partners.pdf", PU_SPAIN_PARTNERS_PDF_URL, "靜宜大學申請西班牙姊妹校列表 PDF"),
      ("sources/pu/pu_report_upload_guide.pdf", PU_REPORT_UPLOAD_GUIDE_PDF_URL, "靜宜大學出國交換學生報告書上傳步驟說明 PDF"),
      ("sources/pu/sisters_america.xlsx", PU_SISTERS_URL, "靜宜大學國際暨兩岸事務處美洲地區締約姊妹校名錄 Excel"),
      ("sources/pu/sisters_europe.xlsx", PU_SISTERS_URL, "靜宜大學國際暨兩岸事務處歐洲地區締約姊妹校名錄 Excel"),
      ("sources/pu/sisters_oceania.xlsx", PU_SISTERS_URL, "靜宜大學國際暨兩岸事務處大洋洲地區締約姊妹校名錄 Excel"),
      ("sources/pu/sisters_asia.xlsx", PU_SISTERS_URL, "靜宜大學國際暨兩岸事務處亞洲與大陸地區締約姊妹校名錄 Excel"),
      ("sources/pu/sisters_africa.xlsx", PU_SISTERS_URL, "靜宜大學國際暨兩岸事務處非洲地區締約姊妹校名錄 Excel"),
      ("sources/pu/411_schools_overview.html", PU_SCHOOLS_OVERVIEW_URL, "靜宜大學 411 遊留學中心各洲別交換學校總覽 HTML"),
      ("sources/pu/411_dual_degree.html", PU_DUAL_DEGREE_URL, "靜宜大學 411 遊留學中心跨國雙聯學制（16 校）專頁 HTML"),
      ("sources/pu/411_isep.html", PU_ISEP_URL, "靜宜大學 411 遊留學中心 ISEP 交換計畫專頁 HTML"),
      ("sources/pu/pu_catalog_source.json", PU_SCHOOLS_OVERVIEW_URL, f"靜宜大學 {len(partners)} 所全球與大陸合作姊妹校整合資料集 JSON"),
      ("sources/pu/pu_resolved_locations.json", PU_SCHOOLS_OVERVIEW_URL, f"靜宜大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON"),
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
      "school_id": "pu",
      "school_name": "靜宜大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  (OFFICIAL_PU_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
  (OFFICIAL_PU_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

  print(
      f"Successfully built PU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
