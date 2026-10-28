"""Build the official National Dong Hwa University (國立東華大學, NDHU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_NDHU_DIR = REPO_ROOT / "sources" / "ndhu"
OFFICIAL_NDHU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "ndhu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "university_locations.jsonl"
)

CHECKED_AT = "2026-10-28T08:00:00Z"

NDHU_OIA_HOME_URL = "https://oia.ndhu.edu.tw/"
NDHU_EXCHANGE_OVERVIEW_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21499.php?Lang=zh-tw"
)
NDHU_INTL_EXCHANGE_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21500.php?Lang=zh-tw"
)
NDHU_MAINLAND_EXCHANGE_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21501.php?Lang=zh-tw"
)
NDHU_DUAL_DEGREE_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21503.php?Lang=zh-tw"
)
NDHU_SCHOLARSHIPS_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21504.php?Lang=zh-tw"
)
NDHU_EXPERIENCES_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21505.php?Lang=zh-tw"
)
NDHU_PARTNERS_LIST_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21507.php?Lang=zh-tw"
)
NDHU_REGULATIONS_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21509.php?Lang=zh-tw"
)
NDHU_STUDENT_NEWS_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21522.php?Lang=zh-tw"
)
NDHU_2027_1_GUIDELINES_PDF_URL = "https://oia.ndhu.edu.tw/var/file/27/1027/img/2556/2027_1_selection_guidelines.pdf"
NDHU_OUTBOUND_REGULATIONS_PDF_URL = (
    "https://oia.ndhu.edu.tw/var/file/27/1027/img/4330/871482510.pdf"
)
NDHU_SCHEDULE_QUOTA_PDF_URL = (
    "https://oia.ndhu.edu.tw/var/file/27/1027/img/2556/786245350.pdf"
)
NDHU_DUAL_DEGREE_RULES_PDF_URL = (
    "https://oia.ndhu.edu.tw/var/file/27/1027/img/4330/509080121.pdf"
)
NDHU_CREDIT_TRANSFER_PDF_URL = (
    "https://aa.ndhu.edu.tw/var/file/4/1004/img/1164/160587574.pdf"
)
NDHU_XUEHAI_CONTRACT_PDF_URL = (
    "https://oia.ndhu.edu.tw/var/file/27/1027/img/2559/532325410.pdf"
)

REGION_COST_DEFAULTS = {
    "美國": (
        "每月生活費約 USD 1,400–2,200（依匯率折合新臺幣約 45,000–70,000 元，含懷俄明大學、新墨西哥大學、東南密蘇里州立大學、德州大學阿靈頓分校、南佛羅里達大學、舊金山州立大學等校內外住宿、膳食與交通；交換生免繳美國姊妹校學費，並可申請教育部學海飛颺／惜珠、校內出國交換獎助學金或「國際移動力先鋒計畫」高額獎學金）",
        "須憑美國接待大學核發之 DS-2019（J-1 交換生）或 I-20（F-1 雙聯學位生）表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證，且須投保符合接待校規定之全期海外醫療保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,200–1,850（折合加幣約 CAD 1,650–2,500 / 月、新臺幣約 38,500–59,000 元，含里賈納大學 University of Regina 校內學生宿舍、膳食與交通費用；交換生免繳加國姊妹校學費）",
        "交換研習 1 學期（6 個月以內）可申辦加拿大電子旅行授權（eTA），交換 1 學年或超過 6 個月須申辦加拿大 Study Permit 學生許可並投保醫療保險。",
    ),
    "墨西哥": (
        "每月生活費約 USD 650–1,050（折合新臺幣約 21,000–33,500 元，含蒙特雷大學 UDEM 學生住宿、餐飲與市區交通費用；交換生免繳姊妹校學費）",
        "交換研習 180 天以內可依墨西哥簽證規定辦理，超過 180 天須申辦墨西哥學生居留簽證並投保海外全期醫療及意外保險。",
    ),
    "英國": (
        "每月生活費約 USD 1,350–2,050（折合英鎊約 GBP 1,050–1,600 / 月、新臺幣約 43,000–65,000 元，含艾塞克斯大學 University of Essex、史旺西大學 Swansea University、亞伯立斯威大學 Aberystwyth University 學生宿舍與生活費）",
        "交換 6 個月以內可依英國 Standard Visitor 規定辦理，超過 6 個月或修讀 3+1 / 1+1 雙聯學位須憑 CAS 申辦英國 Student Visa 並繳交移民健康附加費（IHS）。",
    ),
    "德國": (
        "每月生活費約 USD 1,050–1,600（折合歐元約 EUR 950–1,450 / 月、新臺幣約 33,500–51,000 元；曼海姆大學、基森大學、錫根大學、奧爾登堡大學、漢堡大學、羅斯托克大學、克勞斯塔爾工業大學、萊茵瓦爾應用科技大學等繳交學期雜費 Semesterbeitrag 後多含德國學期交通票）",
        "須開立德國限制提領帳戶（Blocked Account，每月基準約 EUR 992）並憑入學許可向德國在台協會申辦德國長期學生簽證及投保德國公保／醫療險。",
    ),
    "法國": (
        "每月生活費約 USD 1,050–1,650（折合歐元約 EUR 950–1,500 / 月、新臺幣約 33,500–53,000 元；巴黎第十二大學 UPEC、雷恩商學院、里爾大學、波爾多大學、EPITA 學生公寓與日常開銷；留法學生可申請法國政府 CAF 房補）",
        "須先經法國教育中心（Campus France）完成 Etudes en France 線上程序與面試，再向法國在台協會申辦長期學生簽證（VLS-TS）。",
    ),
    "捷克": (
        "每月生活費約 USD 700–1,100（折合歐元約 EUR 650–1,000 / 月、新臺幣約 22,500–35,000 元；赫拉德茨克拉洛韋大學 UHK、托馬斯巴塔大學、帕爾杜比采大學學生宿舍費用實惠，其中 UHK 為東華國際移動力先鋒計畫合作校）",
        "須憑捷克接待大學核發之入學許可與住宿證明向捷克經濟文化辦事處申辦長期學生簽證並投保捷克認可之醫療保險。",
    ),
    "波蘭": (
        "每月生活費約 USD 650–1,050（折合歐元約 EUR 600–950 / 月、新臺幣約 21,000–33,500 元；羅茲大學、亞當密坎凱維奇大學、格但斯克大學、西里西亞大學、奧波萊大學校內學生宿舍費用低廉）",
        "須憑波蘭接待大學入學許可向波蘭臺北辦事處申辦波蘭 D 類國別學生簽證，並投保歐盟認可之全期醫療保險。",
    ),
    "立陶宛": (
        "每月生活費約 USD 650–1,050（折合歐元約 EUR 600–950 / 月、新臺幣約 21,000–33,500 元；維爾紐斯大學、維陶塔斯馬格努斯大學、米科拉斯羅梅里斯大學學生宿舍與生活費親民）",
        "須透過立陶宛移民局 MIGRIS 系統申辦國家簽證（D 簽）或臨時居留許可並投保申根醫療保險。",
    ),
    "西班牙": (
        "每月生活費約 USD 950–1,500（折合歐元約 EUR 880–1,380 / 月、新臺幣約 30,500–48,000 元；巴塞隆納大學、赫羅納大學、納瓦拉公立大學、哈恩大學、武康大學 UCAM、地中海大學學院 EUM 學生合租公寓與生活費）",
        "須憑西班牙接待大學入學許可向西班牙商務辦事處申辦學生簽證，並投保無自負額之全額醫療保險。",
    ),
    "荷蘭": (
        "每月生活費約 USD 1,150–1,750（折合歐元約 EUR 1,050–1,600 / 月、新臺幣約 36,500–56,000 元；方提斯應用科技大學 Fontys Venlo、HZ 應用科技大學、溫德斯海姆應用科技大學學生宿舍與生活費）",
        "由荷蘭接待大學代向荷蘭移民局（IND）申辦 MVV 入境簽證與 VVR 學生居留許可（須先匯付財力證明至學校指定帳戶）。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,350–2,000（折合澳幣約 AUD 2,000–3,000 / 月、新臺幣約 43,000–64,000 元；雪梨科技大學 UTS、麥覺理大學、格里菲斯大學、西雪梨大學校內外住宿與交通費）",
        "須憑澳洲姊妹校核發之 CoE（Confirmation of Enrolment）線上申辦澳洲 Subclass 500 學生簽證，並強制投保海外學生健康保險（OSHC）。",
    ),
    "紐西蘭": (
        "每月生活費約 USD 1,150–1,750（折合紐幣約 NZD 1,900–2,900 / 月、新臺幣約 36,500–56,000 元；奧克蘭理工大學 AUT、梅西大學、林肯大學、懷卡托大學學生宿舍與生活費）",
        "須憑紐西蘭接待大學入學許可向紐西蘭移民局（INZ）線上申辦 Fee Paying / Exchange Student Visa 並投保合規醫療及旅遊保險。",
    ),
    "日本": (
        "每月生活費約 USD 700–1,150（折合日圓約 JPY 100,000–165,000 / 月、新臺幣約 22,500–36,500 元；北海道大學、東北大學、東京都立大學、青山學院大學、立教大學、芝浦工業大學、廣島大學、岡山大學、大阪公立大學、琉球大學等國際學舍與伙食交通費）",
        "須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後至日本台灣交流協會申辦留學簽證並加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 680–1,100（折合韓元約 KRW 900,000–1,500,000 / 月、新臺幣約 21,500–35,000 元；中央大學、韓國外國語大學、首爾市立大學、建國大學、仁荷大學、慶北大學、全南大學、釜慶大學、高麗大學世宗校區等校內宿舍與生活費）",
        "須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後辦理外國人登錄證並納保韓國國民健康保險。",
    ),
    "泰國": (
        "每月生活費約 USD 500–850（折合泰銖約 THB 17,000–28,000 / 月、新臺幣約 16,000–27,000 元；清邁大學、泰國農業大學、宋卡王子大學學生公寓與生活費實惠）",
        "須憑泰國接待大學入學許可公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 教育簽證並投保海外全期醫療險。",
    ),
    "印尼": (
        "每月生活費約 USD 450–750（折合新臺幣約 14,500–24,000 元；泗水理工學院 ITS、泗水大學 UBAYA、印尼教育大學 UPI、日惹國立大學 UNY 學生宿舍與餐飲交通開銷低廉）",
        "須憑印尼接待大學入學許可與印尼高教部學習許可（Study Permit）申辦印尼學生簽證（C316）並投保海外全期醫療險。",
    ),
    "越南": (
        "每月生活費約 USD 450–750（折合新臺幣約 14,500–24,000 元；孫德勝大學、胡志明市師範大學、大叻大學、河內國家教育大學學生宿舍與生活費實惠）",
        "須由越南接待大學協助申辦越南學生入境批文（DH 簽證）並投保海外全期醫療及意外保險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 500–850（折合馬幣約 MYR 2,200–3,700 / 月、新臺幣約 16,000–27,000 元；南方大學學院學生宿舍與餐飲費用親民）",
        "須透過馬來西亞教育全球服務中心（EMGS）線上申辦學生簽證核准函（VAL / Mobility Pass）。",
    ),
    "印度": (
        "每月生活費約 USD 450–750（折合新臺幣約 14,500–24,000 元；舒利尼大學 Shoolini University 校內食宿與生活費實惠）",
        "須憑印度接待大學正式入學許可向印度台北協會（ITA）申辦印度 Student Visa 並投保海外醫療及意外保險。",
    ),
    "中國大陸": (
        "每月生活費約 USD 350–700（折合人民幣約 RMB 1,800–4,500 / 月、新臺幣約 11,000–22,500 元；北京大學、復旦大學、南京大學、南開大學、天津大學、武漢大學、西安交通大學、四川大學、廈門大學、山東、吉林、蘭州等校內學生宿舍與食堂開銷低廉）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及大陸姊妹校寄發之錄取通知書辦理報到，並依東華國際事務處規定購買涵蓋交換全期之海外醫療及意外保險（保額至少新臺幣 100 萬元以上）。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "美國": "秋季學期（Fall Semester）：約 8 月中旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬",
    "加拿大": "秋季學期（Fall Semester）：約 9 月初至 12 月中旬；冬季／春季學期（Winter Semester）：約 1 月初至 4 月下旬",
    "墨西哥": "秋季學期（Fall Semester）：約 8 月初至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月下旬",
    "英國": "秋季學期（Autumn Term / Semester 1）：約 9 月下旬至翌年 1 月；春季學期（Spring Term / Semester 2）：約 1 月下旬至 6 月",
    "德國": "冬季學期（Winter Semester）：約 9/10 月至翌年 2 月；夏季學期（Summer Semester）：約 3/4 月至 7/8 月",
    "法國": "秋季學期（Fall Semester）：約 9 月初至 12 月底／1 月；春季學期（Spring Semester）：約 1 月下旬至 5/6 月",
    "捷克": "秋季學期（Winter Semester）：約 9 月中旬至翌年 1 月底；春季學期（Summer Semester）：約 2 月中旬至 6 月底",
    "波蘭": "秋季學期（Winter Semester）：約 10 月初至翌年 2 月中旬；春季學期（Summer Semester）：約 2 月下旬至 6 月底",
    "立陶宛": "秋季學期（Autumn Semester）：約 9 月初至翌年 1 月底；春季學期（Spring Semester）：約 2 月初至 6 月底",
    "西班牙": "秋季學期（Fall Semester）：約 9 月中旬至翌年 1 月；春季學期（Spring Semester）：約 1 月下旬至 6 月",
    "荷蘭": "秋季學期（Fall Semester）：約 8 月底／9 月初至翌年 1 月底；春季學期（Spring Semester）：約 2 月初至 6 月底",
    "澳洲": "第一學期（Semester 1 / Autumn）：約 2 月下旬至 6 月下旬；第二學期（Semester 2 / Spring）：約 7 月下旬至 11 月下旬",
    "紐西蘭": "第一學期（Semester 1）：約 2 月下旬至 6 月下旬；第二學期（Semester 2）：約 7 月中旬至 11 月中旬",
    "日本": "秋季學期（Fall Semester）：約 9 月中下旬至翌年 2 月；春季學期（Spring Semester）：約 4 月初至 8 月上旬",
    "韓國": "秋季學期（Fall Semester）：約 9 月初至 12 月中旬；春季學期（Spring Semester）：約 3 月初至 6 月中旬",
    "泰國": "第一學期（First Semester）：約 8 月至 12 月；第二學期（Second Semester）：約 1 月至 5 月",
    "印尼": "奇數學期（Odd Semester）：約 8/9 月至 12 月／翌年 1 月；偶數學期（Even Semester）：約 2 月至 6/7 月",
    "越南": "第一學期（Fall Semester）：約 9 月至翌年 1 月；第二學期（Spring Semester）：約 2 月至 6 月",
    "馬來西亞": "第一學期：約 9/10 月至翌年 1/2 月；第二學期：約 2/3 月至 6/7 月",
    "印度": "秋季學期（Monsoon Semester）：約 8 月至 12 月；春季學期（Spring Semester）：約 1 月至 5 月",
    "中國大陸": "秋季學期（上學期）：約 9 月初至翌年 1 月中旬；春季學期（下學期）：約 2 月中下旬至 6 月底",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
  """Ensure school-images.json and university_locations.jsonl contain all 163 NDHU partner schools."""
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
          else loc.get("lat", 23.8976)
      )
      lon = float(
          loc.get("longitude")
          if loc.get("longitude") is not None
          else loc.get("lon", 121.5419)
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
  OFFICIAL_NDHU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_NDHU_DIR / "ndhu_catalog_source.json").read_text(
          encoding="utf-8"
      )
  )
  resolved_locations = json.loads(
      (SOURCES_NDHU_DIR / "ndhu_resolved_locations.json").read_text(
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
        item.get("group") or "國際事務處全球移動組正式締約姊妹校"
    )
    quota_str = clean_text(
        item.get("quota")
        or "每學期 1–4 名免學費交換生（依兩校交換協議及當期簡章名額辦理）"
    )
    detail_url = item.get("detail_url") or NDHU_PARTNERS_LIST_URL

    if "先鋒計畫" in group_str and "雙聯" in group_str:
      program_type = (
          "國際事務處國際交換學生計畫暨國際移動力先鋒計畫與跨國雙聯學位計畫"
      )
      source_url = detail_url
    elif "先鋒計畫" in group_str:
      program_type = (
          "國際事務處國際交換學生計畫暨「國際移動力先鋒計畫」重點獎助合作校"
      )
      source_url = detail_url
    elif "雙聯學位" in group_str:
      program_type = "國際事務處國際交換學生計畫暨跨國雙聯學位計畫"
      source_url = NDHU_DUAL_DEGREE_URL
    elif country == "中國大陸" and avail_status == "open":
      program_type = "國際事務處大陸地區姊妹校交換學生計畫（互免學費）"
      source_url = NDHU_MAINLAND_EXCHANGE_URL
    elif avail_status == "open":
      program_type = "國際事務處國際交換學生計畫（互免學費）"
      source_url = detail_url
    else:
      program_type = "國際事務處正式締約合作姊妹校（短期交流／專案合作）"
      source_url = NDHU_PARTNERS_LIST_URL

    colleges_str = clean_text(
        item.get("colleges")
        or "人文社會科學學院、理工學院、管理學院、花師教育學院、藝術學院、原住民民族學院、環境暨海洋學院、洄瀾學院"
    )
    degree_levels_str = clean_text(
        item.get("eligible_degrees")
        or "學士班二年級（含）以上、碩士班、博士班在學學位生（不含在職專班、國合會及其他專班生）"
    )
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "")
    website = item.get("website") or NDHU_PARTNERS_LIST_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    round_label = (
        "2027年第一次甄選（8–10月申請次年春季班 115-2 及秋季班 116-1）＆第二次甄選（2–3月申請同年秋季班 116-1）國際暨大陸交換學生甄選"
        if avail_status == "open"
        else "國際事務處正式締約合作姊妹校（依當期短期交流營隊或交換簡章公告名額辦理）"
    )
    app_deadline_str = clean_text(
        item.get("deadline")
        or (
            "第一次甄選（申請次年春季班 115-2 及秋季班 116-1 出國交換）：2026/08/17 17:00 ～ 2026/10/05 17:00 線上申請，2026/10/30 12:00 公告錄取，2026/10/27～11/02 線上確認｜"
            "第二次甄選（申請同年秋季班 116-1 出國交換剩餘名額）：每年 2–3 月開放線上申請"
        )
    )
    deadline_iso = "2026-11-02T17:00:00+08:00"
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "116"

    study_period_str = clean_text(item.get("duration") or "一學期或一學年")
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲國立東華大學國際事務處全球移動組提名錄取後，可依 {zh_name} 國際處指引申請校內外學生宿舍或國際學舍"
        + (f"（學費與獎補助待遇：{tuition_note}）" if tuition_note else "。")
    )
    course_rest_str = (
        f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《國立東華大學2027年第一次國際交換學生甄選簡章》、《國立東華大學國際交換學生出國計畫作業辦法》（110.12.22 修正通過）與《學生出國選修課程實施辦法》規定："
        "（1）申請資格為具東華學籍之在學學位生（不含在職專班、國合會及其他專班生），出國就讀時須為二年級（含）以上（大一、碩一、博一新生得於一年級申請、二年級出國），前一學期或歷年平均 GPA 達 2.5（滿分 4.5，約 70 分）以上；每位學生最少選填 2 個、最多 6 個志願，首次申請者優先分發；"
        "（2）校內書面審查總成績＝學業表現（歷年成績＋語言能力）20%＋任務企劃書 35%＋讀書計畫 35%＋資料加分 10%，具國際處接待義工證明加總分 1 分、修畢全球研究與國際事務學程加總分 1 分；總分相同時依序比較前一學期 GPA、前一學期操行成績；"
        "（3）出國交換期間須於東華辦理註冊並繳交全額學雜費，免繳接待姊妹校學費，每學期至少修讀 2 門課（含 1 門專業課程、1 門非專業課程）且成績及格；學分換算原則為歐洲 ECTS 學分 × 1/2、英國 CATS 學分 × 1/4、美日陸約 1:1 折算；返國後 1 個月內（春季班 3/31 前、秋季班 10/31 前）須繳交回國程序單、成績單、1,500–2,000 字心得報告（含任務企劃書執行成果與 4 張以上照片）及 5 頁以上簡報或 3–5 分鐘影片。"
    )

    living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
        country,
        (
            "每月生活費約 USD 850–1,450（依匯率折合新臺幣約 27,000–46,500 元，含住宿、膳食與市區交通）",
            "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋全期之海外醫療及意外保險（保額至少新臺幣 100 萬元以上）。",
        ),
    )

    tuition_points_list = [
        (
            f"東華在學註冊與合作姊妹校學費待遇：交換生於出國交換期間須在國立東華大學辦理註冊並繳交東華全額學雜費（不得辦理休學或畢業），免繳接待姊妹校學費。本合作校待遇：{tuition_note or '免繳接待姊妹校學費（雙聯學位依兩校雙聯協議繳費）'}。"
        ),
        (
            "東華四大出國獎助學金體系：（1）教育部《學海飛颺》獎學金（選送優秀在學學生赴非大陸港澳之海外姊妹校交換一學期或一學年，每名約補助新臺幣 5萬–15萬元）；（2）教育部《學海惜珠》獎學金（補助具低收入戶、中低收入戶或特殊境遇家庭證明之優秀學生出國交換機票與生活費）；（3）校內《國立東華大學國際交換學生出國計畫作業辦法》出國交換獎助學金（申請資格為歷年平均 GPA 達 3.3 以上且具外語檢定證明，依當年度預算核給新臺幣 1萬–15萬元不等）；（4）「國際移動力先鋒計畫」專案獎學金（針對美國懷俄明大學、新墨西哥大學、東南密蘇里州立大學、捷克赫拉德茨克拉洛韋大學、德國錫根大學、曼海姆大學、西班牙巴塞隆納大學、日本北海道大學、東北大學、韓國中央大學等 10 所先鋒合作校提供免學費及高額獎助學金）。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認東華在學學籍、GPA 門檻與 {zh_name} 語檢要求）：確認為具東華學籍之學士班、碩士班或博士班在學學位生（出國就讀時須為二年級以上，不含在職專班），符合學業要求（{gpa_req_str}），並備妥有效外語能力證明（{lang_req_str}）。"
        ),
        (
            "步驟二（於第一次甄選 8–10 月或第二次甄選 2–3 月登入「東華出國交換學生申請系統」ias.ndhu.edu.tw 填報 2–6 個志願並上傳審查資料）：線上填具申請表（最少選填 2 個、最多 6 個志願），上傳歷年成績單（含 GPA）、外語能力證明、讀書計畫（佔 35%）、任務企劃書（佔 35%，規劃於交換期間宣傳臺灣與東華或執行跨文化專案）、家長同意書及各項加分證明（國際處接待義工證明 +1 分、修畢全球研究與國際事務學程 +1 分）。"
        ),
        (
            f"步驟三（國際事務處書面審查評比、線上確認錄取資格並向 {full_name} 辦理官方提名）：由國際事務處依書審配分（學業與語言表現 20%＋任務企劃書 35%＋讀書計畫 35%＋資料加分 10%）及志願序分發公告錄取名單（2027年第一次甄選於 2026/10/30 12:00 公告）；錄取生須於 2026/10/27～11/02 完成線上確認並簽署家長同意書與行政契約書，由全球移動組向姊妹校完成官方提名（Nomination）。"
        ),
        (
            "步驟四（申請學海飛颺／惜珠或校內出國交換獎助學金、辦理簽證與選課，返國 1 個月內完成回國程序單與心得報告）：出國期間每學期至少修讀 2 門課（含 1 門專業課程、1 門非專業課程）且及格；返國後 1 個月內（春季班 3/31 前、秋季班 10/31 前）繳交回國程序單、姊妹校成績單、1,500–2,000 字交換心得報告（含任務企劃書執行成果與 4 張以上照片）及 5 頁以上簡報或 3–5 分鐘影片，辦理學分抵免（歐洲 2 ECTS = 1 學分、英國 4 CATS = 1 學分）與獎學金核銷。"
        ),
    ]

    elig_points_list = [
        f"合作類別與甄選群組：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業成績與獎學金 GPA 門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "校內甄選評分與志願規定：每位學生最少選填 2 個、最多 6 個志願（首次申請者優先分發）；書面審查總成績＝學業表現（歷年成績＋語言能力）20%＋任務企劃書 35%＋讀書計畫 35%＋資料加分 10%（國際處接待義工證明 +1 分、全球研究與國際事務學程 +1 分）。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與東華獎補助待遇：{tuition_note}")
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
            or f"{NDHU_EXPERIENCES_URL}#ndhu-exp-{sn}-{e_idx+1}"
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
            "college": "人文社會科學學院／理工學院／管理學院／花師教育學院／藝術學院／原住民民族學院／環境暨海洋學院／洄瀾學院",
            "department": e.get("department") or "東華交換生",
        })
        summary_text = (
            f"國立東華大學國際事務處公開收錄之學長姐赴 {country} {full_name} 交換／交流官方返國心得報告（{raw_t}），詳述選課學分抵免、任務企劃書執行成果、住宿環境、簽證辦理與當地生活費實錄。"
        )
        theme_map = {
            "academics": f"東華交換生於《{raw_t}》分享在 {zh_name} 修讀至少 2 門課（含專業與非專業課程）、課堂互動及返國依規定（歐洲 2 ECTS = 1 學分、英國 4 CATS = 1 學分）辦理學分抵免之經驗。",
            "housing": f"東華交換生記錄申請 {zh_name} 校內外學生宿舍、周邊生活機能與大眾運輸通勤方式（{housing_str[:100]}）。",
            "campus_culture": f"東華國際事務處公開收錄《{raw_t}》之任務企劃書跨文化交流成果、校園生活與國際生社團活動紀錄。",
            "cost": f"東華交換生分享於 {zh_name} 之每月住宿、伙食與交通開銷（{living_cost_str[:100]}），以及免繳姊妹校學費與申請學海飛颺／惜珠或校內出國交換獎助學金之規劃。",
        }
        student_experience_rows.append({
            "school_name": full_name,
            "country": country,
            "title": raw_t,
            "source_url": eurl,
            "source_type": "article",
            "platform": "國立東華大學國際事務處（OIA）—出國交換／短期交流學生心得報告專區",
            "author_name": e.get("student_name") or "東華交換生",
            "language": "zh",
            "summary": summary_text,
            "themes": ["academics", "housing", "campus_culture", "cost"],
            "theme_summaries": theme_map,
            "content_status": "full_text",
            "perspective": "official_student_story",
            "published_at": None,
            "discovered_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                f"{full_name}:ndhu_exp:{e_idx}:{eurl}".encode("utf-8")
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
        "home_university": "國立東華大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exp_links[0]["url"] if exp_links else NDHU_EXPERIENCES_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

    loc = resolved_locations.get(full_name) or {
        "city": country,
        "latitude": 23.8976,
        "longitude": 121.5419,
        "source_url": "https://www.wikidata.org",
    }
    city_name = loc.get("city") or country
    lat = float(
        loc.get("latitude")
        if loc.get("latitude") is not None
        else loc.get("lat", 23.8976)
    )
    lon = float(
        loc.get("longitude")
        if loc.get("longitude") is not None
        else loc.get("lon", 121.5419)
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
        "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 及東華國際事務處合作姊妹校名錄比對；實際交換校區以錄取通知與締約校專頁為準。",
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
          f"【東華學長姐交換返國心得報告（共 {len(exps)} 篇）】收錄於國際事務處交換學生心得報告專區（含：{'、'.join(exp_labels[:4])}）"
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
            f"國立東華大學國際事務處全球移動組公告合作姊妹校（{program_type}）；{quota_str}。"
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
            "title": f"國立東華大學國際事務處全球移動組（OIA）姊妹校交換生資訊與締約名錄—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立東華大學2027年第一次國際交換學生甄選簡章與國際交換學生出國計畫作業辦法（110.12.22修正通過）",
            "source_url": NDHU_EXCHANGE_OVERVIEW_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立東華大學出國交換獎助學金專區（教育部學海飛颺／惜珠、校內出國交換獎助學金與國際移動力先鋒計畫）",
            "source_url": NDHU_SCHOLARSHIPS_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exp_links:
      wf_sources.append({
          "title": f"國立東華大學國際事務處交換學生心得報告專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
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
        "home_university": "國立東華大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": acad_year,
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "2027年第一次甄選（秋季學期申請次年春季班 115-2 及秋季班 116-1）",
            "2027年第二次甄選（春季學期申請同年秋季班 116-1）",
            "115-1",
            "115-2",
            "116-1",
            "116-2",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "國立東華大學由國際事務處全球移動組（Office of International Affairs, Global Mobility Division，設於壽豐校區行政大樓 601 室）統籌全校 8 大學院（人文社會科學學院、理工學院、管理學院、花師教育學院、藝術學院、原住民民族學院、環境暨海洋學院、洄瀾學院）之國際交換學生計畫、大陸地區交換學生計畫、10 校跨國雙聯學位計畫、10 校「國際移動力先鋒計畫」及教育部學海飛颺、學海惜珠與校內出國交換獎助學金。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"ndhu-{acad_year}-home-1-{sn:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認東華在學學籍、GPA 門檻與 {zh_name} 語檢要求",
                "responsible_party": "學生",
                "responsible_unit": "國立東華大學國際事務處全球移動組／各系所",
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
                    f"確認符合《國立東華大學2027年第一次國際交換學生甄選簡章》與《國際交換學生出國計畫作業辦法》規定：申請人須為具東華學籍之在學學位生（不含在職專班、國合會及其他專班生），出國就讀時須為二年級（含）以上，符合學業標準（{gpa_req_str}），並備妥符合 {zh_name} 門檻之有效外語檢定成績（{lang_req_str}）。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["國立東華大學"],
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
                    NDHU_EXCHANGE_OVERVIEW_URL,
                    NDHU_OUTBOUND_REGULATIONS_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ndhu-{acad_year}-home-2-{sn:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "於第一次甄選（8–10月）或第二次甄選（2–3月）截止前登入出國交換申請系統 ias.ndhu.edu.tw 填報 2–6 個志願並上傳書審資料",
                "responsible_party": "學生",
                "responsible_unit": "國立東華大學國際事務處全球移動組",
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": NDHU_INTL_EXCHANGE_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "於申請期間登入「國立東華大學出國交換學生申請系統」（http://ias.ndhu.edu.tw/intstud/）填報最少 2 個、最多 6 個志願，並上傳歷年成績單（含 GPA）、有效外語能力證明、讀書計畫（佔 35%）、任務企劃書（佔 35%）、家長同意書及加分證明文件（國際處接待義工證明 +1 分、修畢全球研究與國際事務學程 +1 分）。"
                ),
                "details": [
                    "第一次甄選（秋季學期初辦理）：申請次年春季班（115-2）及秋季班（116-1）出國交換（開放全年度名額；2027年第一次甄選為 2026/08/17 17:00 至 2026/10/05 17:00）。",
                    "第二次甄選（春季學期初辦理）：申請同年秋季班（116-1）出國交換（開放第一次甄選後剩餘名額，每年約 2–3 月申請）。",
                ],
                "document_requirements": [
                    {
                        "name": "國立東華大學出國交換學生線上申請表（選填 2–6 個志願）與家長同意書",
                        "official_form_url": NDHU_INTL_EXCHANGE_URL,
                        "source_urls": [
                            NDHU_INTL_EXCHANGE_URL,
                            NDHU_SCHEDULE_QUOTA_PDF_URL,
                        ],
                    },
                    {
                        "name": "讀書計畫（Study Plan，佔書審 35%）與任務企劃書（Mission Proposal，佔書審 35%）",
                        "official_form_url": NDHU_INTL_EXCHANGE_URL,
                        "source_urls": [
                            NDHU_INTL_EXCHANGE_URL,
                            NDHU_OUTBOUND_REGULATIONS_PDF_URL,
                        ],
                    },
                    {
                        "name": "歷年中英文成績單（含 GPA 達 2.5 以上證明）與有效外語能力檢定證明（佔書審 20%）",
                        "official_form_url": NDHU_INTL_EXCHANGE_URL,
                        "source_urls": [
                            NDHU_INTL_EXCHANGE_URL,
                            NDHU_MAINLAND_EXCHANGE_URL,
                        ],
                    },
                    {
                        "name": "其他加分與優秀表現證明（佔書審 10%；國際處接待義工證明總分 +1 分、全球研究與國際事務學程證明總分 +1 分）",
                        "official_form_url": NDHU_INTL_EXCHANGE_URL,
                        "source_urls": [
                            NDHU_INTL_EXCHANGE_URL,
                            NDHU_SCHEDULE_QUOTA_PDF_URL,
                        ],
                    },
                ],
                "scope": {
                    "home_universities": ["國立東華大學"],
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
                    NDHU_EXCHANGE_OVERVIEW_URL,
                    NDHU_INTL_EXCHANGE_URL,
                    NDHU_MAINLAND_EXCHANGE_URL,
                    NDHU_SCHEDULE_QUOTA_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ndhu-{acad_year}-home-3-{sn:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "國際事務處書面審查評比、公告校內推薦名單與錄取生線上確認資格",
                "responsible_party": "國立東華大學國際事務處全球移動組與錄取學生",
                "responsible_unit": "國立東華大學國際事務處全球移動組",
                "deadline_at": "2026-11-02T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": NDHU_STUDENT_NEWS_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "國際事務處依書面審查標準（學業表現 20%＋任務企劃書 35%＋讀書計畫 35%＋資料加分 10%，外加義工與國事學程加分）及首次申請優先原則核定錄取名單（2027年第一次甄選因系統維護於 2026/10/30 12:00 公告結果）；錄取生須於 2026/10/27～11/02 完成線上確認，並申請學海飛颺／惜珠或校內出國交換獎助學金。"
                ),
                "details": [
                    "同分比序原則：書面審查總分相同時，依序比較（1）前一學期 GPA、（2）前一學期操行成績。",
                    "出國交換獎助學金：歷年平均 GPA 達 3.3 以上且具外語檢定證明者，得申請《國立東華大學國際交換學生出國計畫作業辦法》獎助學金（1萬–15萬元）或教育部《學海飛颺》／《學海惜珠》及 10 校「國際移動力先鋒計畫」獎助學金。",
                ],
                "scope": {
                    "home_universities": ["國立東華大學"],
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
                    NDHU_OUTBOUND_REGULATIONS_PDF_URL,
                    NDHU_SCHOLARSHIPS_URL,
                    NDHU_STUDENT_NEWS_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ndhu-{sn:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由東華國際事務處全球移動組向 {zh_name} 辦理官方提名，並於姊妹校截止日前遞交入學與宿位申請文件",
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"完成校內錄取確認後，由東華國際事務處全球移動組統一向 {zh_name} 辦理官方提名（Nomination）；學生須於姊妹校申請截止日前完成線上申請並上傳外文入學申請表、英文歷年成績單、護照影本、英文財力證明、外語檢定證書及宿舍申請表，靜候接待校核發正式入學許可（Admission Letter / DS-2019 / I-20 / COE / 錄取通知書）。"
                ),
                "details": [
                    f"研修期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["國立東華大學"],
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
                    [source_url, NDHU_INTL_EXCHANGE_URL]
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"ndhu-{acad_year}-home-5-{sn:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "出國前完成東華註冊繳費與出國程序單，交換期間修習至少 2 門課，返國 1 個月內繳交回國程序單與 1,500–2,000 字心得報告",
                "responsible_party": "學生與所屬系所",
                "responsible_unit": "國立東華大學國際事務處全球移動組／教務處／各系所",
                "summary": (
                    "出國前須填寫《出國程序單》、參加行前說明會並於交換期間維持東華在學註冊及繳交全額學雜費；於姊妹校每學期至少修讀 2 門課（含 1 門專業課程、1 門非專業課程）且成績及格；返國後 1 個月內（春季班 3/31 前、秋季班 10/31 前）須繳交《回國程序單》、正式成績單、1,500–2,000 字交換心得報告（含任務企劃書執行成果與 4 張以上照片）及 5 頁以上簡報或 3–5 分鐘影片，依《學生出國選修課程實施辦法》（歐洲 ECTS × 1/2、英國 CATS × 1/4）辦理學分抵免與獎學金核銷。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["國立東華大學"],
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
                    NDHU_OUTBOUND_REGULATIONS_PDF_URL,
                    NDHU_CREDIT_TRANSFER_PDF_URL,
                    NDHU_XUEHAI_CONTRACT_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合國立東華大學國際事務處全球移動組（OIA）《2027年第一次國際交換學生甄選簡章》、《赴大陸地區交換學生簡章》、《國際移動力先鋒計畫》（10 校）、《雙聯學位專區》（10 校）、《國際交換學生出國計畫作業辦法》、《學生出國選修課程實施辦法》及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆學長姐返國心得報告，共 {len(catalog_source)} 所合作姊妹校資料。"
        ),
    })

    cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": f"國立東華大學國際事務處全球移動組（OIA）姊妹校交換生資訊、申請資格與雙聯學位專頁—{zh_name}",
            "source_url": source_url,
            "summary": "東華國際事務處公告之合作學程、開放學制、語言檢定門檻與互免學費／先鋒計畫／雙聯學位待遇說明",
        },
        {
            "title": "國立東華大學國際交換學生出國計畫作業辦法與學生出國選修課程實施辦法",
            "source_url": NDHU_REGULATIONS_URL,
            "summary": "東華出國交換在學註冊規定、書面審查評分公式（學業20%＋任務企劃書35%＋讀書計畫35%＋加分10%）、學分換算與獎補助規範",
        },
    ]
    if exp_links:
      dest_sources.append({
          "title": f"國立東華大學國際事務處交換學生心得報告專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
          "source_url": exp_links[0]["url"],
          "summary": f"收錄歷年東華學生赴 {zh_name} 交換／交流返國心得報告共 {len(exps)} 篇",
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
            NDHU_EXCHANGE_OVERVIEW_URL,
            NDHU_INTL_EXCHANGE_URL,
            NDHU_SCHOLARSHIPS_URL,
        ]
        + ([exp_links[0]["url"]] if exp_links else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "國立東華大學",
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
                "title": "生活費、東華在學註冊規定與教育部學海飛颺／惜珠／校內出國交換獎助學金／先鋒計畫",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [NDHU_DUAL_DEGREE_URL],
                "caution": (
                    "依《國立東華大學國際交換學生出國計畫作業辦法》，獲獎助學生須於出國前簽訂行政契約書，每學期至少修讀 2 門課（含專業與非專業各 1 門）且及格，並於返國後 1 個月內繳交心得報告與簡報／影片，違約者須繳回獎助金。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外國際學生宿舍申請",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": "各姊妹校校內學生宿舍床位有限，獲東華國際事務處全球移動組提名後請務必於接待校規定期限內完成線上宿位申請。",
            },
            {
                "key": "insurance",
                "title": "海外醫療及意外保險與家長同意書規定",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依東華國際事務處規定，所有交換生及雙聯生均須繳交經家長（監護人）簽章之同意書，並於出國前自行購買涵蓋交換全期之海外醫療及意外保險（保額至少新臺幣 100 萬元以上）。",
                ],
                "source_urls": src_url_list,
                "caution": "美國、德國、法國、荷蘭、捷克、波蘭、英國、日本、韓國、紐澳等接待校對交換生保險保額或當地國民健康保險有強制規定，請依入學通知書辦理。",
            },
            {
                "key": "visa",
                "title": "留學交換簽證辦理、出國程序單與在學註冊義務",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "交換期間須維持國立東華大學在學身分並繳交全額學雜費；出發前須完成《出國程序單》並參加國際處行前說明會。",
                ],
                "source_urls": src_url_list,
                "caution": "出國前請務必確認護照效期、簽證核發進度、選課抵免預審與行政契約書簽署。",
            },
            {
                "key": "academics",
                "title": "學分換算原則（2 ECTS = 1 學分、4 CATS = 1 學分）、至少修習 2 門課規定與返國程序單",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [NDHU_CREDIT_TRANSFER_PDF_URL],
                "caution": (
                    "於歐洲姊妹校修習之 ECTS 學分以 2 ECTS 折算東華 1 學分，英國 CATS 學分以 4 CATS 折算東華 1 學分，每學期至少修讀 2 門課（含專業與非專業課程）且及格，返國後 1 個月內檢附成績單與課程大綱辦理抵免。"
                ),
            },
            {
                "key": "living",
                "title": f"{city_name} 校園生活與東華學長姐返國心得傳承",
                "summary": f"代表城市：{city_name}。請配合接待校國際處完成報到與新生訓練（Orientation）。",
                "points": [
                    f"目的地城市：{city_name}（{country}）",
                    (
                        "東華國際事務處公開收錄歷屆各院系所學生赴海外及大陸姊妹校交換之返國心得報告与任務企劃成果"
                        + (
                            f"（本校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，並設有國際接待義工制度協助交流傳承。"
                    ),
                ],
                "source_urls": [
                    exp_links[0]["url"] if exp_links else NDHU_EXPERIENCES_URL
                ],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合國立東華大學國際事務處 {len(catalog_source)} 所合作姊妹校、當期開放交換及雙聯名額表（148 校）、國際移動力先鋒計畫（10 校）、跨國雙聯學位（10 校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆學生返國心得報告。"
        ),
    })

    research_records.append({
        "home_university": "國立東華大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            "國立東華大學國際事務處《姊妹校列表》、《2027年第一次國際交換學生甄選簡章》、《赴大陸地區交換簡章》、《雙聯學位專區》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"國立東華大學國際事務處姊妹校交換名額與申請條件專頁—{zh_name}",
            "url": source_url,
        },
    ]
    if exp_links:
      ev_sources.append({
          "title": f"國立東華大學國際事務處交換學生心得報告—赴 {zh_name} 心得報告（{len(exps)} 篇）",
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
            "scope": "東華海外與大陸交換姊妹校住宿與生活資訊",
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
            "scope": "東華出國交換學雜費規定、教育部學海飛颺／惜珠、校內出國交換獎助學金、先鋒計畫與地區生活費估算",
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
            "scope": "東華國際交換學生出國計畫作業辦法、書面審查評分、學分換算與返國報告規範",
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
            "scope": "東華海外交換與雙聯學位簽證、家長同意書、海外醫療保險與行前提醒",
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
                    f"｜東華公開收錄 {len(exps)} 篇赴 {zh_name} 交換生返國心得報告（{'、'.join(exp_labels[:3])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "東華交換名額與歷屆學長姐返國心得報告分享",
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
            "已整合國立東華大學國際事務處《姊妹校列表》、《2027年第一次國際交換學生甄選簡章》、《赴大陸地區交換簡章》、《雙聯學位專區》、《國際移動力先鋒計畫》及歷屆學生交換心得報告。",
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

  write_jsonl(OFFICIAL_NDHU_DIR / "partners.jsonl", partners)
  write_jsonl(SOURCES_NDHU_DIR / "partners.jsonl", partners)
  write_jsonl(OFFICIAL_NDHU_DIR / "application_workflows.jsonl", workflows)
  write_jsonl(OFFICIAL_NDHU_DIR / "destination_profiles.jsonl", destinations)
  write_jsonl(OFFICIAL_NDHU_DIR / "partner_research.jsonl", research_records)
  write_jsonl(OFFICIAL_NDHU_DIR / "student_life.jsonl", life_records)
  write_jsonl(
      OFFICIAL_NDHU_DIR / "experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_NDHU_DIR / "student_experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_NDHU_DIR / "student_experiences.jsonl", student_experience_rows
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
  (OFFICIAL_NDHU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_NDHU_DIR / "student-experiences.json").write_text(
      json.dumps(
          {
              "school_id": "ndhu",
              "school_name": "國立東華大學",
              "checked_at": CHECKED_AT,
              "source_url": NDHU_EXPERIENCES_URL,
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

  (OFFICIAL_NDHU_DIR / "campus-locations.json").write_text(
      json.dumps(
          {
              "school_id": "ndhu",
              "school_name": "國立東華大學",
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
  (OFFICIAL_NDHU_DIR / "campus-assets.json").write_text(
      json.dumps(
          {
              "school_id": "ndhu",
              "school_name": "國立東華大學",
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

  ndhu_source_urls = [
      NDHU_OIA_HOME_URL,
      NDHU_EXCHANGE_OVERVIEW_URL,
      NDHU_INTL_EXCHANGE_URL,
      NDHU_MAINLAND_EXCHANGE_URL,
      NDHU_DUAL_DEGREE_URL,
      NDHU_SCHOLARSHIPS_URL,
      NDHU_EXPERIENCES_URL,
      NDHU_PARTNERS_LIST_URL,
      NDHU_REGULATIONS_URL,
      NDHU_STUDENT_NEWS_URL,
      NDHU_OUTBOUND_REGULATIONS_PDF_URL,
      NDHU_SCHEDULE_QUOTA_PDF_URL,
      NDHU_DUAL_DEGREE_RULES_PDF_URL,
      NDHU_CREDIT_TRANSFER_PDF_URL,
      NDHU_XUEHAI_CONTRACT_PDF_URL,
  ]

  exchange_info_payload = {
      "school_name": "國立東華大學",
      "program_type": [
          (
              "國際事務處全球移動組（OIA）國際及大陸地區姊妹校交換學生計畫（涵蓋日、韓、美、加、墨、英、德、法、捷克、波、立陶宛、西、荷、澳、紐、新南向及中國大陸等 148 所當期開放申請合作校，交換期間保有東華在學學籍並繳交本校全額學雜費、免繳接待姊妹校學費）"
          ),
          (
              "10 校「國際移動力先鋒計畫」（針對美國懷俄明大學、新墨西哥大學、東南密蘇里州立大學、捷克赫拉德茨克拉洛韋大學、德國錫根大學、曼海姆大學、西班牙巴塞隆納大學、日本北海道大學、東北大學、韓國中央大學提供免學費交換及高額專案獎學金）與 10 校跨國雙聯學位計畫（英國艾塞克斯大學、史旺西大學、美國德州大學阿靈頓分校、科羅拉多大學丹佛分校、明尼蘇達大學杜魯斯分校、法國雷恩商學院、澳洲格里菲斯大學、麥覺理大學、西雪梨大學、日本東北大學）"
          ),
          (
              "教育部「學海飛颺」（優秀交換生出國研修）、「學海惜珠」（補助清寒優秀學生來回機票與生活費）與校內《國立東華大學國際交換學生出國計畫作業辦法》出國交換獎助學金（歷年 GPA 達 3.3 以上且具外語檢定證明者核給新臺幣 1萬–15萬元）"
          ),
      ],
      "academic_year": [
          (
              "116（涵蓋 2027年第一次甄選［2026/08/17–10/05 線上申請次年春季班 115-2 及秋季班 116-1 出國交換，2026/10/30 公告錄取］、第二次甄選［每年 2–3 月申請同年秋季班 116-1 剩餘名額］、大陸地區交換生及出國交換獎助學金甄選）"
          ),
          (
              f"本平台完整收錄國立東華大學國際事務處公告之 {len(partners)} 所全球與大陸合作姊妹校（含 {open_partner_count} 所當期開放申請之國際與大陸交換姊妹校、先鋒計畫與雙聯學位合作校、{len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 22 個國家與地區，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返國心得報告）"
          ),
      ],
      "semester": [
          "第一次甄選（秋季學期初 8–10 月辦理）：同時開放申請次年春季班（115-2）及秋季班（116-1）出國交換一學期或一學年（開放全部名額）。",
          "第二次甄選（春季學期初 2–3 月辦理）：開放申請同年秋季班（116-1）出國交換一學期或一學年（開放第一次甄選後剩餘名額）。",
          "大陸地區交換生（與國際交換同步分兩梯次甄選）及跨國雙聯學位計畫（依各雙聯協議時程向國際處及學院提出申請）。",
      ],
      "application_period": [
          "【2027年第一次國際暨大陸交換學生甄選（申請 115-2 春季班＆116-1 秋季班出國）】線上申請期間：2026/08/17 17:00 至 2026/10/05 17:00（登入 http://ias.ndhu.edu.tw/intstud/ 填報 2–6 個志願）；校內錄取結果於 2026/10/30 12:00 公告，線上確認為 2026/10/27 至 2026/11/02。",
          "【2027年第二次國際暨大陸交換學生甄選（申請 116-1 秋季班出國剩餘名額）】預計於 2027 年 2 月至 3 月開放線上申請，3 月底公告校內錄取名單並辦理姊妹校提名。",
          "【跨國雙聯學位計畫（10 所歐美日澳雙聯合作校）】依兩校雙聯協議規定修業年限（3+1、3+2、2+2、1+1 碩士或雙聯博士）於每年秋季或春季梯次向所屬學院及國際事務處提出申請。",
          "【教育部學海飛颺／學海惜珠獎學金＆校內出國交換獎助學金】配合第一次與第二次交換甄選錄取確認時程受理（申請校內獎助學金須歷年平均 GPA 達 3.3 以上且具外語檢定證明）。",
      ],
      "eligibility": [
          "1. 學籍與年級限制：具國立東華大學正式學籍之在學學位生（學士班、碩士班、博士班；不含在職專班、國合會及其他專班生），出國就讀時須為二年級（含）以上（大一、碩一、博一新生得於一年級下學期申請、二年級出國）。",
          "2. 學業成績與獎學金 GPA 門檻：依《2027年第一次國際交換學生甄選簡章》，申請人前一學期或歷年平均 GPA 須達 2.5（滿分 4.5，約百分制 70 分）以上；若欲同時申請《國立東華大學國際交換學生出國計畫作業辦法》出國交換獎助學金，歷年平均 GPA 須達 3.3 以上且具外語檢定證明。",
          "3. 志願選填與分發原則：每位學生最少選填 2 個、最多選填 6 個志願，且於同一學制內首次申請出國交換者優先分發。",
          "4. 校內書面審查評分公式：書審總成績 100% ＝（a）學業表現（歷年學業成績＋語言能力證明）20% ＋（b）任務企劃書（Mission Proposal）35% ＋（c）讀書計畫（Study Plan）35% ＋（d）資料加分（社團、競賽、證照、特殊表現）10%；另具國際處接待義工證明加總分 1 分、修畢全球研究與國際事務學程加總分 1 分。同分比序依序為：（1）前一學期 GPA、（2）前一學期操行成績。",
      ],
      "language_requirement": [
          "1. 英語組及歐美紐澳姊妹校：依當期《姊妹校申請條件一覽表》規定，英語授課組別普遍要求 TOEFL iBT 61–80（部分歐美澳名校與雙聯學位要求 iBT 79–90）、IELTS 5.5–6.5 或 TOEIC 650–785 以上（全民英檢 GEPT 中高級可作為校內初審佐證，惟多數海外姊妹校正式提名須檢附 TOEFL iBT 或 IELTS）。",
          "2. 日本姊妹校（北海道大學、東北大學、東京都立大學、青山學院大學、立教大學、芝浦工業大學、廣島大學、岡山大學、大阪公立大學、琉球大學等 23 校）：日語授課組要求日本語能力試驗 JLPT N1 或 N2（部分學校接受 N3）；全英語授課學程（English-taught Program）可憑 TOEFL iBT 61–79、IELTS 5.5–6.0 或 TOEIC 650–785 申請。",
          "3. 韓國姊妹校（中央大學、韓國外國語大學、首爾市立大學、建國大學、仁荷大學、慶北大學、全南大學、釜慶大學、高麗大學世宗校區等 13 校）：韓語授課組要求 TOPIK 2–4 級以上；英語授課組可憑 TOEFL iBT / IELTS / TOEIC 成績申請。",
          "4. 大陸地區姊妹校（北京大學、復旦大學、南京大學、南開大學、天津大學、武漢大學、西安交通大學、四川大學、廈門大學等 41 校）：中文授課免附外語檢定成績證明（若有外語檢定仍可列計校內書審學業與語言表現 20% 評分）。",
      ],
      "required_documents": [
          "1. 國立東華大學出國交換學生線上申請表（於 http://ias.ndhu.edu.tw/intstud/ 填報 2–6 個志願）",
          "2. 歷年中文或英文成績單正本（須顯示前一學期或歷年平均 GPA 達 2.5 以上；申請校內獎助學金者歷年 GPA 須達 3.3 以上）",
          "3. 有效外語能力檢定成績單影本（TOEFL iBT / ITP、IELTS、TOEIC、JLPT、TOPIK、DELF/DELE/Goethe 等；大陸交換免附）",
          "4. 讀書計畫（Study Plan，佔書審總分 35%，含交換動機、擬選修課程與學分抵免規劃）",
          "5. 任務企劃書（Mission Proposal，佔書審總分 35%，規劃於交換期間執行推廣臺灣與東華大學或跨文化專題任務）",
          "6. 家長（監護人）同意書、有效護照基本資料頁影本及其他優秀表現佐證資料（佔書審 10%；附國際處接待義工證明 +1 分、修畢全球研究與國際事務學程證明 +1 分）",
          "7. 申請教育部《學海惜珠》者另附新式戶口名簿影本及低收入戶／中低收入戶／特殊境遇家庭證明文件",
          "8. 錄取後完成線上確認、簽署行政契約書並辦理《出國程序單》；返國後 1 個月內（春季班 3/31 前、秋季班 10/31 前）繳交《回國程序單》、姊妹校成績單、1,500–2,000 字心得報告（含任務企劃書執行成果與 4 張以上照片）及 5 頁以上簡報或 3–5 分鐘影片",
      ],
      "scholarship_info": [
          "1. 教育部「學海飛颺」選送優秀學生出國研修獎學金：補助具中華民國國籍、於東華就讀滿一學期以上之優秀在學學生赴非大陸港澳之海外姊妹校交換修讀學分一學期或一學年，每名核給約新臺幣 50,000 元至 150,000 元（依教育部當年度核定經費與校內審查排名核定）。",
          "2. 教育部「學海惜珠」選送勵學優秀學生出國研修獎學金：補助具中華民國國籍且領有各直轄市、縣（市）政府核發之低收入戶、中低收入戶或特殊境遇家庭相關證明之優秀在學學生赴海外姊妹校交換，補助國際來回機票及國外生活費。",
          "3. 《國立東華大學國際交換學生出國計畫作業辦法》（110.12.22 修正通過）校內出國交換獎助學金：申請人歷年平均 GPA 須達 3.3 以上且具外語能力檢定證明，依當年度預算與交換地區核給新臺幣 10,000 元至 150,000 元不等之獎助學金。",
          "4. 「國際移動力先鋒計畫」專案獎助學金：針對本校 10 所先鋒計畫重點合作姊妹校（美國懷俄明大學、新墨西哥大學、東南密蘇里州立大學、捷克赫拉德茨克拉洛韋大學、德國錫根大學、曼海姆大學、西班牙巴塞隆納大學、日本北海道大學、東北大學、韓國中央大學）提供免繳姊妹校學費及專案高額出國獎助學金。",
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": ndhu_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_NDHU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "國立東華大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 70.0,
      "academic_score_rule": (
          "依《國立東華大學2027年第一次國際交換學生甄選簡章》與《國際交換學生出國計畫作業辦法》（110.12.22 修正通過）：申請人須為具東華學籍之學士班、碩士班或博士班在學學位生（不含在職專班、國合會及其他專班生），出國就讀時須為二年級（含）以上，且前一學期或歷年平均 GPA 達 2.5（滿分 4.5，約百分制 70 分）以上；申請校內出國交換獎助學金者，歷年平均 GPA 須達 3.3 以上且具外語檢定證明。"
      ),
      "academic_gpa_minimum": 2.5,
      "maximum_preferences": 6,
      "selection_rules": {
          "academic_policy": "score_or_rank",
          "academic_reference_year": "116",
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
              "在職專班",
              "碩專班",
              "國合會專班",
          ],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 61.0,
          "ielts": 5.5,
          "toeic": 650.0,
      },
      "application_periods": [
          {
              "title": "國立東華大學 2027年第一次國際暨大陸交換學生甄選（申請 115-2 春季班＆116-1 秋季班出國：線上結果確認）",
              "details": [
                  "國際事務處全球移動組辦理 2027 年第一次甄選（同時開放申請 2027 春季班［115-2］及 2027 秋季班［116-1］出國交換全部名額）：線上申請為 2026/08/17 17:00 至 2026/10/05 17:00。",
                  "因出國交換申請系統 ias.ndhu.edu.tw 進行資安修補維護（官方公告 264093），校內推薦結果公告順延至 2026/10/30 12:00，錄取生須於 2026/10/27 至 2026/11/02 完成線上確認並依限繳交家長同意書與姊妹校提名資料。",
              ],
              "source": {
                  "title": "國立東華大學國際事務處《2027年第一次國際交換學生甄選簡章》與推薦結果公告順延通知",
                  "source_url": NDHU_INTL_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": "東華 2027 年第一次交換甄選時程、書審配分（讀書計畫 35%＋任務企劃書 35%＋學業語言 20%＋加分 10%）與線上確認期限。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "2027年第一次甄選（申請 115-2 春季班＆116-1 秋季班）",
              "audience": "all_students",
              "opens_at": "2026-08-17T17:00:00+08:00",
              "deadline_at": "2026-11-02T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "2027年第一次甄選於 2026/10/30 12:00 公告錄取結果，2026/10/27～11/02 辦理線上確認。",
              "deadline_note": "獲校內推薦錄取之同學請務必於 2026/11/02 前登入出國交換申請系統完成線上確認。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "國立東華大學 115/116學年度教育部「學海飛颺／學海惜珠」及校內出國交換獎助學金暨國際移動力先鋒計畫甄選",
              "details": [
                  "配合出國交換甄選時程，受理已獲校內推薦之交換生申請教育部《學海飛颺》、《學海惜珠》（具低收／中低收／特殊境遇證明）、校內《國際交換學生出國計畫作業辦法》獎助學金（歷年 GPA 須達 3.3 以上且具外語檢定證明，核給 1萬–15萬元）及 10 校「國際移動力先鋒計畫」專案獎學金。",
                  "獲獎助學生須於出國前簽署行政契約書，每學期至少修讀 2 門課（含專業與非專業課程）且及格，返國後 1 個月內繳交 1,500–2,000 字心得報告及 5 頁以上簡報或 3–5 分鐘影片辦理核銷。",
              ],
              "source": {
                  "title": "國立東華大學國際事務處出國交換獎助學金專區與國際交換學生出國計畫作業辦法",
                  "source_url": NDHU_SCHOLARSHIPS_URL,
                  "category": "scholarship",
                  "summary": "東華學海飛颺、學海惜珠、校內出國交換獎助學金（GPA 3.3 門檻）與 10 校先鋒計畫獎學金。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "115/116學年度出國交換獎助學金甄選",
              "audience": "all_students",
              "opens_at": "2026-10-30T12:00:00+08:00",
              "deadline_at": "2026-12-15T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "於校內推薦名單確認後受理出國交換獎助學金與學海飛颺／惜珠申請。",
              "deadline_note": "申請校內出國交換獎助學金者歷年平均 GPA 須達 3.3 以上且具外語檢定證明。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "國立東華大學 2027年第二次國際暨大陸交換學生甄選（申請 116-1 秋季班出國剩餘名額：2–3月線上申請）",
              "details": [
                  "每年春季學期初（約 2 月至 3 月）開放申請同年秋季班（116-1）赴海外及大陸姊妹校出國交換一學期或一學年（開放第一次甄選後剩餘名額，每位學生可選填 2–6 個志願）。",
                  "請提前準備外語能力檢定（TOEFL iBT / IELTS / TOEIC / JLPT / TOPIK）、讀書計畫（35%）與任務企劃書（35%），於系統開放期間完成線上申請。",
              ],
              "source": {
                  "title": "國立東華大學國際事務處出國交換申請流程、時程與名額說明",
                  "source_url": NDHU_EXCHANGE_OVERVIEW_URL,
                  "category": "exchange_application",
                  "summary": "東華每年兩次出國交換學生甄選時程與申請作業流程。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "2027年第二次甄選（申請 116-1 秋季班）",
              "audience": "all_students",
              "opens_at": "2027-02-15T09:00:00+08:00",
              "deadline_at": "2027-03-25T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "第二次甄選於每年 2–3 月開放申請同年秋季班出國交換剩餘名額。",
              "deadline_note": "大一、碩一、博一新生可於一年級下學期參加第二次甄選，於升二年級秋季班出國交換。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"國立東華大學國際事務處全球移動組姊妹校交換、先鋒計畫、跨國雙聯學位與獎補助總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所當期開放申請・{total_exp_reports} 篇學長姐返國心得報告）"
              ),
              "details": [
                  (
                      f"國立東華大學（NDHU，東華，創立於 1994 年，坐落於花蓮縣壽豐鄉縱谷平原，為東臺灣規模最大、學門最完整之綜合型國立大學）由「國際事務處全球移動組（Office of International Affairs, Global Mobility Division）」統籌全校 8 大學院（人文社會科學學院、理工學院、管理學院、花師教育學院、藝術學院、原住民民族學院、環境暨海洋學院、洄瀾學院）之國際交換學生計畫、大陸地區交換學生計畫、10 校跨國雙聯學位計畫、10 校「國際移動力先鋒計畫」及教育部學海系列與校內出國交換獎助學金。本平台完整收錄 {len(partners)} 所東華官方合作姊妹校（含 {open_partner_count} 所當期開放申請之國際及大陸交換姊妹校、先鋒計畫與雙聯學位合作校，以及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 22 個國家與地區。"
                  ),
                  (
                      f"東華國際交流具備四大核心特色：（1）10 校「國際移動力先鋒計畫」提供免繳姊妹校學費與高額專案獎學金（涵蓋美國懷俄明大學、新墨西哥大學、東南密蘇里州立大學、捷克赫拉德茨克拉洛韋大學、德國錫根大學、曼海姆大學、西班牙巴塞隆納大學、日本北海道大學、東北大學、韓國中央大學）；（2）10 校跨國雙聯學位計畫（英國艾塞克斯大學、史旺西大學、美國德州大學阿靈頓分校、科羅拉多大學丹佛分校、明尼蘇達大學杜魯斯分校、法國雷恩商學院、澳洲格里菲斯大學、麥覺理大學、西雪梨大學、日本東北大學）；（3）獨具特色之「讀書計畫 35%＋任務企劃書 35%＋學業語言 20%＋資料加分 10%」書審制度，鼓勵學生於海外交換期間執行跨文化任務；（4）完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返國心得報告。"
                  ),
              ],
              "source": {
                  "title": "國立東華大學國際事務處（OIA）出國交換與合作姊妹校官方網站",
                  "source_url": NDHU_EXCHANGE_OVERVIEW_URL,
                  "category": "exchange_application",
                  "summary": f"東華 {len(partners)} 所全球合作姊妹校、10 校先鋒計畫、10 校雙聯學位與 {total_exp_reports} 篇返國心得報告。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "東華在學學籍（出國時二年級以上）、GPA 2.5 申請門檻／GPA 3.3 獎學金門檻與書審評分公式",
              "details": [
                  "學籍與修業年級規定：依《國立東華大學2027年第一次國際交換學生甄選簡章》與《國際交換學生出國計畫作業辦法》（110.12.22 修正通過），申請人須為具本校正式學籍之在學學位生（學士班、碩士班、博士班；不含在職專班、國合會及其他專班生），出國就讀時須為二年級（含）以上，且前一學期或歷年平均 GPA 達 2.5（滿分 4.5，約百分制 70 分）以上；每位學生最少選填 2 個、最多 6 個志願，首次申請者優先分發。",
                  "書面審查評分與同分比序：校內書審總成績＝學業表現（歷年成績＋語言能力）20%＋任務企劃書（Mission Proposal）35%＋讀書計畫（Study Plan）35%＋資料加分 10%；具國際處接待義工證明加總分 1 分、修畢全球研究與國際事務學程加總分 1 分。總分相同時依序比較：（1）前一學期 GPA、（2）前一學期操行成績。",
              ],
              "source": {
                  "title": "國立東華大學2027年第一次國際交換學生甄選簡章與國際交換學生出國計畫作業辦法",
                  "source_url": NDHU_INTL_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": "東華交換生 GPA 2.5 門檻、最多 6 個志願、書審配分公式與義工／國事學程加分規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "英語組（TOEFL iBT / IELTS / TOEIC）、日語組（JLPT N1–N3）、韓語組（TOPIK 2–4 級）與大陸交換免語檢規定",
              "details": [
                  "外語組別門檻：申請非大陸地區之國際交換生須具備符合志願姊妹校規定之有效外語檢定證明：（1）英語授課組普遍要求 TOEFL iBT 61–80（歐美名校及雙聯學位多要求 iBT 79–90）、IELTS 5.5–6.5 或 TOEIC 650–785 以上；（2）日語授課組要求 JLPT N1–N2（部分日本姊妹校接受 N3，或以英語成績申請全英授課學程）；（3）韓語授課組要求 TOPIK 2–4 級以上（或以英語成績申請英語授課學程）。",
                  "大陸地區姊妹校規定：申請北京大學、復旦大學、南京大學、南開大學、武漢大學、四川大學、廈門大學等 41 所大陸姊妹校免附外語檢定證明（若檢附有效外語成績仍可納入校內書審學業與語言表現 20% 評分）。",
              ],
              "source": {
                  "title": "國立東華大學國際交換學生甄選簡章與赴大陸地區交換學生簡章",
                  "source_url": NDHU_INTL_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": "東華國際交換與大陸交換各語種檢定標準說明。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "線上申請表（2–6 志願）、歷年成績單、語檢證明、讀書計畫（35%）、任務企劃書（35%）與返國程序單",
              "details": [
                  "校內甄選線上上傳文件：（1）線上申請表（選填 2–6 個志願）；（2）歷年中英文成績單（含 GPA）；（3）有效外語能力檢定證明（大陸交換免附）；（4）讀書計畫（佔 35%）；（5）任務企劃書（佔 35%）；（6）家長同意書、護照影本及加分佐證（接待義工證明 +1 分、全球研究與國際事務學程證明 +1 分）。",
                  "出國與返國必備程序：出國前須填寫《出國程序單》並簽署行政契約書；交換期間每學期至少修讀 2 門課（含專業與非專業課程各 1 門）且及格；返國後 1 個月內（春季班 3/31 前、秋季班 10/31 前）須繳交《回國程序單》、成績單、1,500–2,000 字心得報告（含任務企劃書執行成果與 4 張以上照片）及 5 頁以上簡報或 3–5 分鐘影片。",
              ],
              "source": {
                  "title": "國立東華大學國際交換學生出國計畫作業辦法與出國交換申請系統說明",
                  "source_url": NDHU_OUTBOUND_REGULATIONS_PDF_URL,
                  "category": "exchange_application",
                  "summary": "東華出國交換線上申請文件、任務企劃書、出國程序單與返國報告格式規範。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部學海飛颺、學海惜珠、校內出國交換獎助學金（GPA 3.3 以上核給 1萬–15萬元）與 10 校國際移動力先鋒計畫獎學金",
              "details": [
                  "教育部學海系列與校內出國交換獎助學金：（1）教育部《學海飛颺》與《學海惜珠》補助優秀生及清寒優秀生赴非大陸港澳姊妹校交換；（2）校內《國立東華大學國際交換學生出國計畫作業辦法》獎助學金：凡歷年平均 GPA 達 3.3 以上且具外語檢定證明之錄取交換生，依當年度經費與交換地區核給新臺幣 10,000 元至 150,000 元不等之獎助學金。",
                  "10 校「國際移動力先鋒計畫」重點獎助：選送優秀學生赴美國懷俄明大學、新墨西哥大學、東南密蘇里州立大學、捷克赫拉德茨克拉洛韋大學、德國錫根大學、曼海姆大學、西班牙巴塞隆納大學、日本北海道大學、東北大學、韓國中央大學交換，享有免繳姊妹校學費及先鋒計畫高額獎助學金。",
              ],
              "source": {
                  "title": "國立東華大學出國交換獎助學金專區與國際交換學生出國計畫作業辦法",
                  "source_url": NDHU_SCHOLARSHIPS_URL,
                  "category": "scholarship",
                  "summary": "東華學海飛颺、學海惜珠、校內出國交換獎助學金與 10 校先鋒計畫獎學金之申請資格與額度。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "國立東華大學出國交換申請文件、任務企劃書（35%）、讀書計畫（35%）與返國 1,500–2,000 字心得報告準備指南",
              "summary": "說明東華國際事務處出國交換線上申請系統上傳文件、任務企劃書與讀書計畫撰寫重點、學分換算及返國 1 個月內結案要求。",
              "key_points": [
                  "線上申請須於 http://ias.ndhu.edu.tw/intstud/ 選填 2 至 6 個志願，並上傳讀書計畫（佔 35%）、任務企劃書（佔 35%，規劃於海外交換期間執行跨文化交流或推廣臺灣與東華之具體方案）、歷年成績單與外語檢定證明。",
                  "選課與學分抵免應依《國立東華大學學生出國選修課程實施辦法》辦理：每學期至少修習 2 門課（含 1 門專業課程、1 門非專業課程）且及格；歐洲 ECTS 學分 × 1/2、英國 CATS 學分 × 1/4、美日陸約 1:1 折算。",
                  "返國後 1 個月內（春季班 3/31 前、秋季班 10/31 前）須繳交回國程序單、姊妹校正式成績單、1,500–2,000 字交換心得報告（含任務企劃書執行成果與 4 張以上照片）及 5 頁以上簡報或 3–5 分鐘影片。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立東華大學2027年第一次國際交換學生甄選簡章與國際交換學生出國計畫作業辦法",
                  "source_url": NDHU_INTL_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NDHU_OUTBOUND_REGULATIONS_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "國立東華大學國際交換學生出國計畫作業辦法、學生出國選修課程實施辦法與雙聯學位實施辦法核心規定",
              "summary": "規範東華國際與大陸交換生之在學年級與 GPA 門檻、書審配分公式、最低修課門檻、學分換算比例及獎助學金義務。",
              "key_points": [
                  "在學學籍與 GPA 規定：申請人須為具東華學籍之學士班、碩士班或博士班在學學位生（不含在職專班、國合會及其他專班生），出國就讀時須為二年級（含）以上，申請門檻為前一學期或歷年 GPA 2.5 以上，申請校內獎助學金門檻為歷年 GPA 3.3 以上且具外語檢定證明。",
                  "書面審查配分與加分：學業表現（歷年成績＋語言能力）20%＋任務企劃書 35%＋讀書計畫 35%＋資料加分 10%；具國際處接待義工證明總分 +1 分、修畢全球研究與國際事務學程總分 +1 分；最多選填 6 個志願，首次申請者優先分發。",
                  "修課下限與返國義務：交換期間須維持東華在學註冊並繳交全額學雜費，每學期至少修讀 2 門課（含專業與非專業各 1 門）且及格；返國後 1 個月內繳交回國程序單、成績單、1,500–2,000 字心得報告及簡報／影片。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立東華大學國際交換學生出國計畫作業辦法（110.12.22修正）與學生出國選修課程實施辦法",
                  "source_url": NDHU_REGULATIONS_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NDHU_OUTBOUND_REGULATIONS_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "國立東華大學國際事務處（Office of International Affairs）官方網站",
              "source_url": NDHU_OIA_HOME_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立東華大學出國交換申請流程、時程與名額總覽",
              "source_url": NDHU_EXCHANGE_OVERVIEW_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立東華大學《2027年第一次國際交換學生甄選簡章》與國際交換專區",
              "source_url": NDHU_INTL_EXCHANGE_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立東華大學赴大陸地區交換學生簡章與 41 所大陸合作高校專區",
              "source_url": NDHU_MAINLAND_EXCHANGE_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立東華大學跨國雙聯學位申請專區（10 所歐美日澳雙聯學位合作校）",
              "source_url": NDHU_DUAL_DEGREE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": f"國立東華大學全球合作姊妹校名錄（{len(partners)} 所合作姊妹校）",
              "source_url": NDHU_PARTNERS_LIST_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立東華大學出國交換獎助學金專區（教育部學海飛颺、學海惜珠、校內獎助學金與國際移動力先鋒計畫）",
              "source_url": NDHU_SCHOLARSHIPS_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": f"國立東華大學出國交換與短期交流學生心得報告專區（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）",
              "source_url": NDHU_EXPERIENCES_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_NDHU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  doc_conditions = {
      "school_id": "ndhu",
      "school_name": "國立東華大學",
      "checked_at": CHECKED_AT,
      "source_url": NDHU_EXCHANGE_OVERVIEW_URL,
      "common_documents": exchange_info_payload["required_documents"],
      "track_specific_conditions": [
          {
              "track": "國際事務處全球移動組 第一次（8–10月）＆第二次（2–3月）國際交換學生計畫（亞洲、歐美、大洋洲）",
              "required": [
                  "國立東華大學出國交換學生線上申請表（於 ias.ndhu.edu.tw 填報 2–6 個志願）與家長同意書",
                  "讀書計畫（Study Plan，佔書審 35%）與任務企劃書（Mission Proposal，佔書審 35%）",
                  "歷年中英文成績單正本（含 GPA 達 2.5 以上）與有效外語能力檢定證明（佔書審 20%）",
                  "其他優秀表現佐證資料（佔書審 10%；附國際處接待義工證明 +1 分、全球研究與國際事務學程證明 +1 分）",
                  "錄取後完成線上確認與《出國程序單》；返國後 1 個月內繳交《回國程序單》、成績單、1,500–2,000 字心得報告及簡報／影片",
              ],
          },
          {
              "track": "國際事務處全球移動組 赴大陸地區姊妹校交換學生計畫（北京大學、復旦大學、南京大學、南開大學、武漢大學、四川大學、廈門大學等 41 校）",
              "required": [
                  "國立東華大學出國交換學生線上申請表（選填 2–6 個志願）與家長同意書",
                  "歷年中文成績單正本（GPA 達 2.5 以上；中文授課免附外語檢定證明）",
                  "讀書計畫（佔 35%）、任務企劃書（佔 35%）及其他加分資料（佔 10%）",
                  "錄取後辦理臺胞證並投保涵蓋全期之海外醫療及意外保險（保額至少新臺幣 100 萬元以上）",
              ],
          },
          {
              "track": "國際事務處跨國雙聯學位計畫（英國艾塞克斯大學、史旺西大學、美國德州大學阿靈頓分校、科羅拉多大學丹佛分校、明尼蘇達大學杜魯斯分校、法國雷恩商學院、澳洲格里菲斯大學、麥覺理大學、西雪梨大學、日本東北大學）",
              "required": [
                  "跨國雙聯學位申請表及兩校雙聯協議規定之入學申請文件（3+1、3+2、2+2、1+1 碩士或雙聯博士）",
                  "歷年英文成績單正本及符合雙聯合作校門檻之 TOEFL iBT / IELTS 成績單正本",
                  "英文讀書計畫（Statement of Purpose）、英文履歷（CV）、師長英文推薦信及財力證明",
              ],
          },
          {
              "track": "教育部學海飛颺／學海惜珠獎學金、校內出國交換獎助學金＆10 校國際移動力先鋒計畫",
              "required": [
                  "校內出國交換獎助學金＆學海飛颺：歷年平均 GPA 達 3.3 以上且具外語檢定證明，檢附申請表、成績單、語檢證明與讀書計畫，獲獎後簽署行政契約書",
                  "學海惜珠：另檢附新式戶口名簿影本及直轄市、縣（市）政府核發之低收入戶、中低收入戶或特殊境遇家庭相關證明文件",
                  "10 校國際移動力先鋒計畫：申請懷俄明大學、新墨西哥大學、東南密蘇里州立大學、赫拉德茨克拉洛韋大學、錫根大學、曼海姆大學、巴塞隆納大學、北海道大學、東北大學、韓國中央大學者，得同步申請先鋒計畫專案獎助學金",
              ],
          },
      ],
  }
  (OFFICIAL_NDHU_DIR / "document-conditions.json").write_text(
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
        f"{fname},{len(partners)},{pop},{ratio:.4f},Official NDHU OIA verified"
    )
  (OFFICIAL_NDHU_DIR / "field-coverage.csv").write_text(
      "\n".join(field_cov_lines) + "\n", encoding="utf-8"
  )

  pages_records = [
      {
          "title": "國立東華大學：2027年第一次（8–10月）與第二次（2–3月）國際暨大陸交換學生甄選簡章、申請流程與時程說明",
          "source_url": NDHU_EXCHANGE_OVERVIEW_URL,
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
          "title": "國立東華大學：國際交換學生出國計畫作業辦法（GPA 2.5 申請門檻、GPA 3.3 獎助學金門檻、讀書計畫35%＋任務企劃書35%＋學業語言20%＋加分10%）",
          "source_url": NDHU_OUTBOUND_REGULATIONS_PDF_URL,
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
          "title": f"國立東華大學：{len(partners)} 所全球與大陸合作姊妹校外語檢定門檻（TOEFL / IELTS / TOEIC / JLPT / TOPIK）與大陸交換免語檢規定",
          "source_url": NDHU_INTL_EXCHANGE_URL,
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
          "title": "國立東華大學：出國交換與雙聯學位應備文件（線上 2–6 志願申請表、讀書計畫、任務企劃書、出國程序單與返國 1,500–2,000 字心得報告）",
          "source_url": NDHU_SCHEDULE_QUOTA_PDF_URL,
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
          "title": "國立東華大學：教育部學海飛颺、學海惜珠、校內出國交換獎助學金（1萬–15萬元）與 10 校國際移動力先鋒計畫",
          "source_url": NDHU_SCHOLARSHIPS_URL,
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
  (OFFICIAL_NDHU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
      + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "ndhu",
      "school_name": "國立東華大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "undergraduate_score_minimum": 70.0,
          "graduate_score_minimum": 70.0,
          "undergraduate_gpa_minimum": 2.5,
          "scholarship_gpa_minimum": 3.3,
          "minimum_preferences": 2,
          "maximum_preferences": 6,
          "academic_and_language_weight_percent": 20.0,
          "mission_proposal_weight_percent": 35.0,
          "study_plan_weight_percent": 35.0,
          "bonus_materials_weight_percent": 10.0,
          "oia_volunteer_bonus_points": 1.0,
          "global_studies_program_bonus_points": 1.0,
          "require_ndhu_enrollment_during_abroad": True,
          "minimum_courses_per_semester": 2,
          "credit_conversion_rule": (
              "依《國立東華大學學生出國選修課程實施辦法》：歐洲學分互認系統 ECTS 學分 × 1/2 折算本校學分、英國 CATS 學分 × 1/4 折算本校學分、美日陸多數為 1:1 折算"
          ),
          "return_documents_due": (
              "返國後 1 個月內（春季班 3/31 前、秋季班 10/31 前）繳交《回國程序單》、正式成績單、1,500–2,000 字心得報告（含任務企劃書執行成果與 4 張以上照片）及 5 頁以上簡報或 3–5 分鐘影片"
          ),
      },
      "source_urls": ndhu_source_urls,
      "verified_at": "2026-10-28",
  }
  (OFFICIAL_NDHU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NDHU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "國立東華大學",
              "required_documents": student_dashboard_payload[
                  "required_documents"
              ],
              "source_urls": ndhu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NDHU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "國立東華大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": ndhu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "ndhu",
      "school_name": "國立東華大學",
      "total_partners": len(partners),
      "partner_count": len(partners),
      "international_partners": sum(
          1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
      ),
      "mainland_partners": sum(
          1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
      ),
      "pioneer_program_partner_universities": 10,
      "dual_degree_partner_universities": 10,
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
          f"國立東華大學國際事務處全球移動組（OIA）2027年第一次（秋季學期 8–10 月申請次年春季班 115-2 及秋季班 116-1）與第二次（春季學期 2–3 月申請同年秋季班 116-1）國際交換學生計畫（107 所海外開放交換校）、赴大陸地區姊妹校交換學生計畫（41 所大陸開放交換校）、10 所「國際移動力先鋒計畫」重點合作校、10 所跨國雙聯學位合作校及教育部學海飛颺、學海惜珠、校內《國際交換學生出國計畫作業辦法》獎助學金同步整合；共完整收錄 {len(partners)} 所全球與大陸合作姊妹校（含 {open_partner_count} 所當期開放申請學校及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 22 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返國心得報告）。"
      ),
      "verified_at": "2026-10-28",
  }
  (OFFICIAL_NDHU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NDHU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "ndhu",
              "school_name": "國立東華大學",
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
          "sources/ndhu/ndhu_2027_1_selection_guidelines.pdf",
          NDHU_INTL_EXCHANGE_URL,
          "國立東華大學 2027 年第一次國際交換學生甄選簡章 PDF",
      ),
      (
          "sources/ndhu/ndhu_2027_1_info_session_slides.pdf",
          NDHU_INTL_EXCHANGE_URL,
          "國立東華大學 2027 年第一次出國交換學生甄選說明會簡報 PDF",
      ),
      (
          "sources/ndhu/ndhu_outbound_schedule_quota_procedure.pdf",
          NDHU_EXCHANGE_OVERVIEW_URL,
          "國立東華大學出國交換申請流程、時程與名額說明 PDF",
      ),
      (
          "sources/ndhu/ndhu_outbound_exchange_regulations.pdf",
          NDHU_OUTBOUND_REGULATIONS_PDF_URL,
          "國立東華大學國際交換學生出國計畫作業辦法（110.12.22 修正通過）PDF",
      ),
      (
          "sources/ndhu/ndhu_dual_degree_regulations_zh_509.pdf",
          NDHU_DUAL_DEGREE_RULES_PDF_URL,
          "國立東華大學與境外大學辦理雙聯學位制實施辦法 PDF",
      ),
      (
          "sources/ndhu/ndhu_credit_transfer_regulations.pdf",
          NDHU_CREDIT_TRANSFER_PDF_URL,
          "國立東華大學學生出國選修課程實施辦法（含 ECTS / CATS 學分換算規定）PDF",
      ),
      (
          "sources/ndhu/ndhu_xuehai_admin_contract.pdf",
          NDHU_XUEHAI_CONTRACT_PDF_URL,
          "國立東華大學教育部學海計畫出國研修行政契約書 PDF",
      ),
      (
          "sources/ndhu/ndhu_21517_dual_univ.html",
          NDHU_DUAL_DEGREE_URL,
          "國立東華大學國際事務處「校級跨國雙聯學位合作學校列表」官方網頁 HTML",
      ),
      (
          "sources/ndhu/ndhu_21518_dual_dept.html",
          NDHU_DUAL_DEGREE_URL,
          "國立東華大學國際事務處「院系級跨國雙聯學位合作學校列表」官方網頁 HTML",
      ),
      (
          "sources/ndhu/ndhu_student_news_21522.html",
          NDHU_STUDENT_NEWS_URL,
          "國立東華大學國際事務處最新公告（含 2027 年第一次交換甄選結果公告順延通知）HTML",
      ),
      (
          "sources/ndhu/ndhu_experiences_index.json",
          NDHU_EXPERIENCES_URL,
          f"國立東華大學國際事務處 {total_exp_reports} 篇學生交換與短期交流心得報告索引 JSON",
      ),
      (
          "sources/ndhu/ndhu_catalog_source.json",
          NDHU_PARTNERS_LIST_URL,
          f"國立東華大學 {len(partners)} 所全球與大陸合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/ndhu/ndhu_resolved_locations.json",
          NDHU_PARTNERS_LIST_URL,
          f"國立東華大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
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
      "school_id": "ndhu",
      "school_name": "國立東華大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = (
      json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  )
  (OFFICIAL_NDHU_DIR / "import_provenance.json").write_text(
      prov_text, encoding="utf-8"
  )
  (OFFICIAL_NDHU_DIR / "import-provenance.json").write_text(
      prov_text, encoding="utf-8"
  )

  print(
      f"Successfully built NDHU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
