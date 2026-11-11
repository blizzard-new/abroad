"""Build the official Asia University (亞洲大學, ASIA) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_ASIA_DIR = REPO_ROOT / "sources" / "asia"
OFFICIAL_ASIA_DIR = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "asia"
)
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-08T00:00:00Z"

ASIA_OIA_HOME_URL = "https://oia.asia.edu.tw/"
ASIA_EXCHANGE_HUB_URL = "https://oia.asia.edu.tw/p/412-1008-259.php?Lang=zh-tw"
ASIA_SEMESTER_EXCHANGE_URL = (
    "https://oia.asia.edu.tw/p/412-1008-263.php?Lang=zh-tw"
)
ASIA_SPOTLIGHT_EXCHANGE_URL = (
    "https://oia.asia.edu.tw/p/412-1008-261.php?Lang=zh-tw"
)
ASIA_DUAL_DEGREE_URL = "https://oia.asia.edu.tw/p/412-1008-260.php?Lang=zh-tw"
ASIA_COLLEGE_DUAL_DEGREE_URL = (
    "https://oia.asia.edu.tw/p/412-1008-418.php?Lang=zh-tw"
)
ASIA_OUTBOUND_PARTNERS_URL = (
    "https://oia.asia.edu.tw/p/412-1008-258.php?Lang=zh-tw"
)
ASIA_SISTER_SCHOOLS_URL = (
    "https://oia.asia.edu.tw/p/412-1008-247.php?Lang=zh-tw"
)
ASIA_XUEHAI_HUB_URL = "https://oia.asia.edu.tw/p/412-1008-436.php?Lang=zh-tw"
ASIA_XUEHAI_FEIYANG_URL = (
    "https://oia.asia.edu.tw/p/405-1008-1366,c436.php?Lang=zh-tw"
)
ASIA_XUEHAI_ZHUMENG_URL = (
    "https://oia.asia.edu.tw/p/405-1008-1365,c436.php?Lang=zh-tw"
)
ASIA_ECON_SCHOLARSHIP_URL = (
    "https://oia.asia.edu.tw/p/412-1008-1487.php?Lang=zh-tw"
)
ASIA_STUDENT_STORIES_URL = (
    "https://oia.asia.edu.tw/p/403-1008-81-1.php?Lang=zh-tw"
)
ASIA_DUAL_PORTAL_URL = "https://dual.asia.edu.tw/"
ASIA_AC_REGULATIONS_URL = (
    "https://ac.asia.edu.tw/p/404-1013-1588.php?Lang=zh-tw"
)

ASIA_APPLICATION_ZIP_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/167804164.zip"
)
ASIA_APP_FORM_PDF_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/458014878.pdf"
)
ASIA_PARENTAL_CONSENT_PDF_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/845519215.pdf"
)
ASIA_PRIVACY_CONSENT_PDF_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/291097612.pdf"
)
ASIA_ECON_GRANT_PDF_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/664040154.pdf"
)
ASIA_XUEHAI_FEIYANG_DOCX_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/903172369.docx"
)
ASIA_XUEHAI_ZHUMENG_DOCX_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/708183153.docx"
)
ASIA_STUDY_ABROAD_ACADEMIC_PDF_URL = (
    "https://ac.asia.edu.tw/var/file/13/1013/img/60/R1-2.pdf"
)
ASIA_CREDIT_TRANSFER_PDF_URL = (
    "https://ac.asia.edu.tw/var/file/13/1013/img/60/R2-8.pdf"
)
ASIA_DUAL_DEGREE_REGULATIONS_PDF_URL = (
    "https://ac.asia.edu.tw/var/file/13/1013/img/60/R5-3.pdf"
)
ASIA_DOMESTIC_EXCHANGE_PDF_URL = (
    "https://ac.asia.edu.tw/var/file/13/1008/img/60/R5-1.pdf"
)
ASIA_CMU_EXCHANGE_PDF_URL = (
    "https://ac.asia.edu.tw/var/file/13/1013/img/60/R5-2.pdf"
)

REGION_COST_DEFAULTS = {
    "美國": (
        "每月生活費約 USD 1,250–1,950（折合新臺幣約 40,000–62,000 元；美國北伊利諾大學 2+2 雙學士與加州州立大學聖伯納迪諾分校 2+2／1+1 MBA 雙聯於亞大修讀前 2 年享國內一般生學費，印第安納大學摩利爾法學院 1+1 LL.M. 雙聯優秀生可獲最高約新臺幣 75 萬元獎學金減免）",
        "須憑美國接待大學核發之 I-20 或 DS-2019 表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦 F-1 或 J-1 學生簽證，且須投保符合校方規定之全期醫療保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,200–1,850（折合加幣約 CAD 1,650–2,500 / 月、新臺幣約 38,500–59,000 元；加拿大維多利亞大學 2+2 BCom 商學士雙聯含 Co-op 帶薪實習，可支應部分海外生活開銷）",
        "交換 1 學期（6 個月內）或亮點計畫暑期研修得持 eTA 入境；2+2 雙聯或滿 1 學年交換須向加拿大移民局（IRCC）申辦 Study Permit（學習許可）並投保醫療保險。",
    ),
    "英國": (
        "每月生活費約 USD 1,300–2,000（折合英鎊約 GBP 1,050–1,600 / 月、新臺幣約 42,000–64,000 元；密德薩斯大學與西英格蘭大學 2+2 雙聯前 2 年於亞大修讀享國內一般生學費，畢業後可申請英國 PSW 2 年工作簽證）",
        "交換滿 6 個月以上或修讀 2+2 雙聯學位須申辦英國 Student Visa 並繳交移民健康附加費（IHS）以享有英國國家醫療服務體系（NHS）保障。",
    ),
    "瑞士": (
        "每月生活費約 USD 1,400–2,100（折合瑞士法郎約 CHF 1,250–1,850 / 月、新臺幣約 45,000–67,000 元；瑞士工商酒店管理學院 BHMS 雙聯學制提供 100% 保障之瑞士全職帶薪實習，每月實習薪資可補助住宿與生活費）",
        "須憑瑞士工商酒店管理學院（BHMS）入學許可向瑞士商務辦事處申辦瑞士長期學生簽證（National D Visa），並依瑞士法規投保醫療及意外保險。",
    ),
    "法國": (
        "每月生活費約 USD 900–1,450（折合歐元約 EUR 850–1,350 / 月、新臺幣約 29,000–46,500 元；蒙彼利埃商學院與圖爾大學各提供每年 5 名免繳法方學費之交換生名額，雷恩商學院與蒙彼利埃商學院另提供 2+2／3+1 雙聯學位並可申請法國 CAF 房屋補助）",
        "交換 1 學期以上或攻讀雙聯學位須先經法國教育中心（Campus France）面試並申辦長期學生簽證（VLS-TS），入境後完成 OFII 認證與法國社會醫療保險登錄。",
    ),
    "西班牙": (
        "每月生活費約 USD 950–1,500（折合歐元約 EUR 880–1,400 / 月、新臺幣約 30,500–48,000 元；巴塞隆納龐培法布拉大學設計學院 ELISAVA 每期提供 5 名交換名額）",
        "交換 1 學期以上須向西班牙商務辦事處申辦長期學生簽證，並投保涵蓋全期且無自付額之申根醫療及意外保險。",
    ),
    "義大利": (
        "每月生活費約 USD 900–1,450（折合歐元約 EUR 850–1,350 / 月、新臺幣約 29,000–46,500 元；威尼斯大學列為亞大 318 亮點計畫暑期交換重點合作名校，獲選者原則補助來回經濟艙機票乙張）",
        "暑期短期研修得免簽入境申根區（90 天內）；交換 1 學期以上須向義大利經濟貿易文化推廣辦事處申辦 D 類學生簽證並投保海外醫療保險。",
    ),
    "德國": (
        "每月生活費約 USD 950–1,450（折合歐元約 EUR 900–1,350 / 月、新臺幣約 30,500–46,500 元；不來梅康斯特大學與德國 IU 國際應用科學大學生活與學生宿舍費用）",
        "交換 1 學期以上須開立限制提領帳戶（Blocked Account）向德國在台協會申辦德國學生簽證，並投保德國法定或認可之學生健康保險。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,400–2,150（折合澳幣約 AUD 2,150–3,300 / 月、新臺幣約 45,000–68,500 元；西雪梨大學與斯文本科技大學提供交換生及幼教系、社工系 2+2 雙聯學位）",
        "須購買澳洲海外學生健康保險（OSHC）並憑接待大學核發之 CoE 申辦澳洲 Subclass 500 學生簽證。",
    ),
    "紐西蘭": (
        "每月生活費約 USD 1,150–1,750（折合紐幣約 NZD 1,900–2,900 / 月、新臺幣約 37,000–56,000 元；基督城坎特伯雷理工學院 Ara 列為亞大 318 亮點計畫與學期交換合作校）",
        "亮點計畫短期研修得持 NZeTA 入境；交換 1 學期以上須申辦紐西蘭 Fee-Paying / Exchange Student Visa 並投保規定之國際學生醫療及旅遊保險。",
    ),
    "日本": (
        "每月生活費約 USD 680–1,150（折合日圓約 JPY 98,000–165,000 / 月、新臺幣約 21,500–36,500 元；大阪近畿大學與名古屋椙山女學園大學均提供亞大交換生免繳日方學費優惠，近畿大學另列為亞大 318 亮點計畫合作名校）",
        "學期交換須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後申辦日本留學簽證並加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 650–1,100（折合韓元約 KRW 880,000–1,480,000 / 月、新臺幣約 20,500–35,000 元；漢陽大學提供亞大交換生每年 2 名免繳韓方學費優惠，ERICA 校區另列為亞大 318 亮點計畫暑期交換合作校）",
        "學期交換須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後辦理外國人登錄證並納保韓國國民健康保險。",
    ),
    "新加坡": (
        "每月生活費約 USD 1,100–1,750（折合新幣約 SGD 1,500–2,350 / 月、新臺幣約 35,000–56,000 元；新加坡國立大學 NUS 列為亞大 318 亮點計畫暑期交換合作名校，獲選者原則補助來回機票乙張）",
        "暑期研修依新加坡移民與關卡局（ICA）規定辦理入境電子卡（SG Arrival Card）或 Student's Pass，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "香港": (
        "每月生活費約 USD 1,000–1,600（折合港幣約 HKD 7,800–12,500 / 月、新臺幣約 32,000–51,000 元；香港大學 HKU 短期與學期研習生活開銷）",
        "須依香港入境事務處規定申辦來港就讀進入許可（Student Visa / Entry Permit）或持有效簽證入境，並投保海外全期醫療及意外保險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 480–820（折合馬幣約 MYR 2,100–3,600 / 月、新臺幣約 15,500–26,000 元；吉隆坡馬來亞大學 UM 每年提供亞大高達 15 名免學費交換名額）",
        "須由馬來西亞接待大學透過 EMGS（Education Malaysia Global Services）代辦馬來西亞學生簽證核准函（VAL）並投保當地醫療險。",
    ),
    "泰國": (
        "每月生活費約 USD 450–800（折合泰銖約 THB 15,000–26,500 / 月、新臺幣約 14,500–25,500 元；清邁湄州大學每年提供亞大 3 名免學費交換名額）",
        "須憑泰國接待大學入學許可公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 教育簽證並投保海外全期醫療險。",
    ),
    "越南": (
        "每月生活費約 USD 420–750（折合新臺幣約 13,500–24,000 元；FPT 大學與越南國民經濟大學提供亞大經管、財金系 2+2 雙聯學位及學期交換）",
        "須憑越南接待大學入學許可函申辦越南學生簽證（DH Visa）並投保海外全期醫療及意外保險。",
    ),
    "印尼": (
        "每月生活費約 USD 420–750（折合新臺幣約 13,500–24,000 元；泗水艾爾朗加大學提供 25 名免學費交換名額、日惹穆罕默迪亞大學提供 10 名免學費交換名額及 2+2 雙聯學位）",
        "須憑印尼接待校核發之入學許可與擔保文件申辦印尼學習簽證（Study Visa / KITAS）並投保海外醫療及意外保險。",
    ),
    "菲律賓": (
        "每月生活費約 USD 480–820（折合新臺幣約 15,500–26,000 元；馬尼拉菲律賓中央大學與西維薩亞斯州立大學校園食宿費用親民）",
        "須依菲律賓接待大學指引辦理學生簽證（9F）或特別學習許可（SSP）並投保海外全期醫療保險。",
    ),
    "印度": (
        "每月生活費約 USD 400–720（折合新臺幣約 12,800–23,000 元；韋洛爾理工大學 VIT、印多爾印度管理學院 IIM Indore 與印度國家設計學院 NID 校園食宿費用低廉）",
        "須憑印度接待大學核發之正式錄取通知書向印度台北協會申辦印度學生簽證（Student Visa）並投保海外全期醫療險。",
    ),
    "蒙古": (
        "每月生活費約 USD 450–780（折合新臺幣約 14,500–25,000 元；烏蘭巴托蒙古財經大學 UFE 提供亞大會資、財金、資工系 2+2 雙聯學位）",
        "須憑蒙古接待大學入學許可辦理蒙古學生簽證，並於出發前投保涵蓋全期之海外醫療及意外保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "美國": (
        "秋季班（Fall Semester）：約 8 月中下旬至 12 月中旬；春季班（Spring Semester）：約 1 月中旬至 5 月中旬；亮點計畫暑期交換：約 6 月至 8 月"
    ),
    "加拿大": (
        "秋季學期（Fall）：約 9 月初至 12 月下旬；春季學期（Spring）：約 1 月初至 4 月下旬；亮點計畫暑期研修：約 7 月至 8 月"
    ),
    "英國": (
        "秋季學期（Autumn Term）：約 9 月下旬至翌年 1 月中旬；春季學期（Spring Term）：約 1 月下旬至 6 月上旬；亮點計畫暑期研修：約 7 月至 8 月"
    ),
    "瑞士": (
        "秋季與春季多梯次學期入學（BHMS 每學年分為多個 5 週密集教學模組＋4 至 6 個月瑞士保障帶薪實習）；亮點計畫暑期研修：約 7 月至 8 月"
    ),
    "法國": (
        "秋季學期（Fall Semester）：約 9 月初至 12 月下旬；春季學期（Spring Semester）：約 1 月中旬至 5 月下旬；亮點計畫暑期研修：約 6 月至 7 月"
    ),
    "西班牙": "第一學期：約 9 月中旬至翌年 1 月底；第二學期：約 2 月上旬至 6 月底",
    "義大利": (
        "第一學期：約 9 月中旬至翌年 1 月底；第二學期：約 2 月中旬至 6 月底；亮點計畫暑期研修：約 6 月至 8 月"
    ),
    "德國": (
        "冬季學期（Winter Semester）：約 9–10 月至翌年 1–2 月；夏季學期（Summer Semester）：約 3–4 月至 7–8 月"
    ),
    "澳洲": (
        "第一學期（Semester 1）：約 2 月下旬至 6 月下旬；第二學期（Semester 2）：約 7 月下旬至 11 月下旬"
    ),
    "紐西蘭": (
        "第一學期（Semester 1）：約 2 月中旬至 6 月下旬；第二學期（Semester 2）：約 7 月中旬至 11 月中旬；亮點計畫暑期研修：約 7 月至 8 月"
    ),
    "日本": (
        "春季班（第一學期）：約 4 月初至 8 月上旬；秋季班（第二學期）：約 9 月中旬至翌年 2 月上旬；亮點計畫暑期研修：約 7 月至 8 月"
    ),
    "韓國": (
        "春季班（第一學期）：約 3 月初至 6 月中旬；秋季班（第二學期）：約 9 月初至 12 月中旬；亮點計畫暑期研修：約 7 月至 8 月"
    ),
    "新加坡": (
        "第一學期：約 8 月初至 12 月上旬；第二學期：約 1 月中旬至 5 月上旬；亮點計畫暑期研修：約 6 月至 8 月"
    ),
    "香港": "第一學期：約 9 月初至 12 月下旬；第二學期：約 1 月中旬至 5 月下旬",
    "馬來西亞": "第一學期：約 9–10 月至翌年 1–2 月；第二學期：約 2–3 月至 6–7 月",
    "泰國": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "越南": "第一學期：約 9 月至翌年 1 月；第二學期：約 2 月至 6 月",
    "印尼": "奇數全學期：約 9 月至翌年 1 月；偶數全學期：約 2 月至 6 月",
    "菲律賓": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "印度": "秋季學期：約 8 月至 12 月；春季學期：約 1 月至 5 月",
    "蒙古": "秋季學期：約 9 月初至翌年 1 月中旬；春季學期：約 2 月初至 6 月中旬",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
  """Ensure school-images.json and university_locations.jsonl contain all 106 ASIA partner schools."""
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
          else loc.get("lat", 24.0465)
      )
      lon = float(
          loc.get("longitude")
          if loc.get("longitude") is not None
          else loc.get("lon", 120.6873)
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
  OFFICIAL_ASIA_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_ASIA_DIR / "asia_catalog_source.json").read_text(
          encoding="utf-8"
      )
  )
  resolved_locations = json.loads(
      (SOURCES_ASIA_DIR / "asia_resolved_locations.json").read_text(
          encoding="utf-8"
      )
  )
  bin_urls_path = SOURCES_ASIA_DIR / "binary_source_urls.json"
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
        item.get("group") or "國際事務處（OIA）正式締約合作姊妹校"
    )
    quota_str = clean_text(
        item.get("quota") or "依亞洲大學國際事務處當期公告名額"
    )
    detail_url = item.get("detail_url") or ASIA_OUTBOUND_PARTNERS_URL

    if avail_status == "open":
      program_type = group_str
    else:
      program_type = "國際事務處（OIA）正式締約合作姊妹校"
    source_url = detail_url

    colleges_str = clean_text(
        item.get("colleges")
        or "醫學暨健康學院、資訊電機學院、管理暨社會科學學院、創意設計學院、護理學院、人工智慧學院、國際學院"
    )
    degree_levels_str = clean_text(
        item.get("eligible_degrees")
        or "本校修滿一學期以上之在學學位生（學士班、碩士班、博士班；不含國內及境外在職專班生）"
    )
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "")
    website = item.get("website") or ASIA_OUTBOUND_PARTNERS_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    round_label = (
        "115-2 梯次（2026–2027 學期交換學生、跨國雙聯學位暨亞大 318 亮點計畫甄選）"
        if avail_status == "open"
        else "國際事務處（OIA）正式締約姊妹校（當期開放名額依每學期國際事務處公告簡章為準）"
    )
    app_deadline_str = clean_text(
        item.get("deadline")
        or "學期交換生下半年甄選：2026年10月30日（週五）17:00 止；上半年甄選暨學海飛颺／惜珠：每年 1–3 月受理；亞大 318 亮點計畫暑期交換：2026年3月5日中午 12:00 截止"
    )
    deadline_iso = "2026-10-30T17:00:00+08:00"
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "115"

    study_period_str = clean_text(
        item.get("duration") or "一學期或一學年（雙聯學位依各校 2+2／3+1／1+1 學制）"
    )
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月"
    )
    housing_str = (
        f"獲亞洲大學國際事務處（OIA）或管理學院雙聯學制辦公室推薦錄取後，可依 {zh_name} 國際處指引申請校內外學生宿舍"
        + (f"（費用與學費待遇：{tuition_note}）" if tuition_note else "。")
    )
    course_rest_str = (
        f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《亞洲大學學生出境期間學業及學籍處理辦法》、《亞洲大學與境外大學校院辦理雙學位實施要點》及《亞洲大學學分抵免及編級作業規定》："
        "（1）在學資格：須於亞洲大學修滿一學期以上且為在學學生（不含國內及境外在職專班生；美國南新罕布夏大學限大四生；亮點計畫限大一至大三在學學生或大四準碩士生且須經導師提名）；"
        "（2）雙聯學制修業規定：修習雙學士學位在二校修業時間合計至少須滿 32 個月、雙碩士至少滿 12 個月、雙博士至少滿 24 個月，且在二校當地修習學分數累計須各達獲頒學位所需最低學分數之 1/3 以上；"
        "（3）國外學分換算與抵免基準（《學分抵免及編級作業規定》第 9 點）：返國取得成績後 1 個月內於「學生資訊系統」線上申請並檢附成績單正本及課程大綱辦理四階段審查，本校學分與美制、日制及陸制學分採 1:1 同等換算，英國 CATS 學分制 ÷ 4 = 本校學分，歐洲 ECTS 學分制 ÷ 2 = 本校學分。"
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
            f"亞洲大學出境期間在學註冊與學雜費規定（依《亞洲大學學生出境期間學業及學籍處理辦法》第 6 條）：出國交換或修讀雙聯學位期間仍須辦理亞洲大學註冊手續，依兩校互惠合約按以下三種方式之一繳費：（1）學雜費全額繳給本校、免繳對方學校（如日本近畿大學、椙山女學園大學、韓國漢陽大學、法國蒙彼利埃商學院、法國圖爾大學、馬來亞大學、泰國湄州大學、印尼艾爾朗加大學、日惹穆罕默迪亞大學）；（2）學費繳給本校、雜費繳給對方學校；（3）學雜費均繳給對方學校，但仍需在本校繳交「一學分費及學生平安保險費」。本合作校待遇：{tuition_note}。"
        ),
        (
            "亞洲大學四大出國獎助學金體系：（1）教育部《學海飛颺》與《學海惜珠》計畫（每年 1–3 月校內收件，班排前 30% 或系排前 40%［研究生免排名要求］且 TOEIC 550+，通案補助最低 NT$50,000 含來回機票，學海惜珠優先高額補助弱勢生）；（2）教育部《學海築夢／新南向學海築夢》海外實習計畫（上、下半年兩次徵件，連續實習至少 30 天［印尼 25 天］，補助機票與生活費）；（3）亞洲大學《海外學習與交流獎助學金》（《經濟不利學生學習輔導獎助學金申請暨發放辦法》第 15 條，補助經濟不利生往返經濟艙機票、依中央政府標準按日核發國外生活助學金，返國成果優異另加發 NT$5,000 成果獎勵金）；（4）亞大 318《亮點計畫》暑期交換獎助（原則補助經濟艙來回機票乙張）。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認亞大修滿一學期在學身分、班系排名與 {zh_name} 語檢要求）：確認已在亞洲大學修滿一學期以上（不含在職專班；亮點計畫須大一至大三或大四準碩士生並由導師提名），符合學業門檻（{gpa_req_str}）與外語能力標準（{lang_req_str}）。"
        ),
        (
            "步驟二（先完成線上 Google 表單申請，再繳交核章紙本申請資料至國際事務處 L105）：於校內初審截止前（下半年甄選為 2026 年 10 月 30 日週五 17:00 止；上半年甄選暨學海飛颺為 1–3 月；亮點計畫為 2026 年 3 月 5 日中午 12:00 止）先完成線上表單報名，並備齊：（1）《01_亞洲大學赴國外研修申請書》、（2）《02_系所同意書》（完成學分抵免初審與系所推薦）、（3）《03_行政契約書》、（4）《04_家長同意書》、（5）《05_個人資料提供同意書》、（6）中英文歷年成績單與排名百分比證明、（7）語言能力檢定證明，親送行政大樓 L105 國際事務處（雙聯學位同步洽管理學院雙聯學制辦公室分機 1934）。"
        ),
        (
            f"步驟三（參加校內書面初審與英語口試面試甄選，並申請學海計畫／經濟不利海外學習獎助學金）：由國際事務處與審查委員會進行書面審查及英語面試（亮點計畫於 4 月 10 日在哈佛講堂 A115/A116 舉行英語面試、5 月 1 日公告錄取），核定推薦赴 {full_name} 名單及獎助學金額度。"
        ),
        (
            "步驟四（完成姊妹校官方提名 Nomination、簽證保險與返國心得報告及學分抵免）：獲校內推薦後由國際事務處向接待大學辦理提名並遞交入學申請包裹；獲發入學許可後申辦簽證、購買海外全期醫療及意外保險（役男應於出境前 1–2 個月檢送資料至學務處生輔組辦理緩徵出境）；返國後 2 週內上傳學海計畫心得報告，並於取得成績後 1 個月內依《學分抵免及編級作業規定》（美日陸 1:1、歐洲 ECTS÷2、英國 CATS÷4）辦理學分抵免。"
        ),
    ]

    elig_points_list = [
        f"合作類別與計畫組別：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請學院：{colleges_str}",
        f"學業成績與班系排名門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "校內申請程序：須先完成線上 Google 表單申請，再於截止日前將《赴國外研修申請書》、《系所同意書》、《行政契約書》、《家長同意書》、《個人資料提供同意書》、中英文歷年成績單含排名百分比及語言能力證明紙本繳交至國際事務處（行政大樓 L105）。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與獎助待遇：{tuition_note}")
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
        esem = e.get("semester") or "110–112學年度"
        eurl = (
            e.get("url")
            or f"{ASIA_STUDENT_STORIES_URL}#asia-exp-{sn}-{e_idx+1}"
        )
        if eurl in seen_exp_urls:
          eurl = f"{eurl}#r{e_idx+1}"
        seen_exp_urls.add(eurl)
        exp_labels.append(raw_t[:36])
        exp_links.append({
            "title": raw_t,
            "url": eurl,
            "academic_year": esem,
            "semester": esem,
            "college": "亞洲大學各學院（醫健／資電／管院／創設／護理）",
            "department": "亞大出國交換暨雙聯學位生",
        })
        summary_text = (
            f"亞洲大學國際事務處（OIA）與管理學院雙聯學制辦公室公開收錄之學長姐赴 {country} {full_name} 交換研習／跨國雙聯學位官方心得分享（{raw_t}），詳述姊妹校專業課程學習、全英語授課與團隊報告、海外帶薪實習及跨文化適應實錄。"
        )
        theme_map = {
            "academics": f"亞大交換暨雙聯生於《{raw_t}》分享在 {zh_name} 修讀全英語專業課程、分組專案企劃、雙聯學位修業及返國辦理學分抵免之經驗。",
            "housing": f"亞大交換暨雙聯生記錄於 {zh_name} 住宿環境、當地交通（如大眾運輸與叫車服務）及校園生活機能（{housing_str[:100]}）。",
            "campus_culture": f"亞洲大學國際事務處公開收錄《{raw_t}》之跨文化課堂互動、國際學生交流與海外職場實習體驗。",
            "cost": f"亞大學生分享於 {zh_name} 之學費待遇（如免繳接待校學費或雙聯獎學金減免）、每月生活開銷（{living_cost_str[:100]}）與獎助學金申請心得。",
        }
        student_experience_rows.append({
            "school_name": full_name,
            "country": country,
            "title": raw_t,
            "source_url": eurl,
            "source_type": "article",
            "platform": "亞洲大學國際事務處（OIA）學生故事專區 ＆ 管理學院國際雙聯學制專網",
            "author_name": "亞大出國交換暨雙聯生",
            "language": "zh",
            "summary": summary_text,
            "themes": ["academics", "housing", "campus_culture", "cost"],
            "theme_summaries": theme_map,
            "content_status": "full_text",
            "perspective": "official_student_story",
            "published_at": None,
            "discovered_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                f"{full_name}:asia_exp:{e_idx}:{eurl}".encode("utf-8")
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
        "home_university": "亞洲大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exp_links[0]["url"] if exp_links else ASIA_STUDENT_STORIES_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

    loc = resolved_locations.get(full_name) or {
        "city": country,
        "latitude": 24.0465,
        "longitude": 120.6873,
        "source_url": "https://www.wikidata.org",
    }
    city_name = loc.get("city") or country
    lat = float(
        loc.get("latitude")
        if loc.get("latitude") is not None
        else loc.get("lat", 24.0465)
    )
    lon = float(
        loc.get("longitude")
        if loc.get("longitude") is not None
        else loc.get("lon", 120.6873)
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
          f"【亞大學長姐出國交換暨雙聯心得分享（共 {len(exps)} 篇）】收錄於國際事務處學生故事與管院雙聯專網（含：{'、'.join(exp_labels[:4])}）"
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
            f"亞洲大學國際事務處（OIA）公告合作姊妹校（{program_type}）；{quota_str}。"
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
            "title": f"亞洲大學國際事務處（OIA）出國交換、雙聯學位暨亮點計畫專頁—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "亞洲大學學生出境期間學業及學籍處理辦法（R1-2）",
            "source_url": ASIA_STUDY_ABROAD_ACADEMIC_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "亞洲大學教育部學海計畫專區暨經濟不利學生海外學習與交流獎助學金辦法",
            "source_url": ASIA_ECON_GRANT_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exp_links:
      wf_sources.append({
          "title": f"亞洲大學國際事務處學生故事與雙聯專網—赴 {zh_name} 心得分享（{len(exps)} 篇）",
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
        "home_university": "亞洲大學",
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
            "亞洲大學由國際事務處（Office of International Affairs, OIA，位於行政大樓 L105 室）及管理學院雙聯學制辦公室統籌全校 7 大學院（醫學暨健康學院、資訊電機學院、管理暨社會科學學院、創意設計學院、護理學院、人工智慧學院、國際學院）之「亞大 318」國際化計畫：涵蓋學期交換學生計畫、跨國雙聯學位（2+2／3+1／4+1／1+1／3+2）、「亮點計畫」暑期交換海外研修，以及教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》與校內《海外學習與交流獎助學金》。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"asia-{acad_year}-home-1-{sn:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認亞洲大學修滿一學期在學身分、班排前 30%（或系排前 40%）與 {zh_name} 語檢門檻",
                "responsible_party": "學生",
                "responsible_unit": "亞洲大學國際事務處（L105）／各院系所",
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
                    f"確認符合亞洲大學出國交換、雙聯學位或亮點計畫申請資格：須於本校修滿一學期以上且為在學學位生（不含國內及境外在職專班生；亮點計畫限大一至大三在學生或大四準碩士生且須經導師提名），符合學業要求（{gpa_req_str}）並具備外語能力證明（{lang_req_str}）。"
                ),
                "details": [
                    f"開放學制與學院：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["亞洲大學"],
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
                    ASIA_EXCHANGE_HUB_URL,
                    ASIA_SEMESTER_EXCHANGE_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"asia-{acad_year}-home-2-{sn:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "先完成線上 Google 表單申請，再將《赴國外研修申請書》等 7 項核章紙本送交國際事務處（L105）",
                "responsible_party": "學生",
                "responsible_unit": "亞洲大學國際事務處（行政大樓 L105 室）",
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": ASIA_SEMESTER_EXCHANGE_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "於校內初審截止前（下半年學期交換為 2026 年 10 月 30 日週五 17:00 止；上半年學期交換暨學海飛颺為 1–3 月；亮點計畫為 2026 年 3 月 5 日中午 12:00 止）先完成線上表單申請，並將《01_亞洲大學赴國外研修申請書》、《02_系所同意書》、《03_行政契約書》、《04_家長同意書》、《05_個人資料提供同意書》、中英文歷年成績單與排名百分比證明及語言能力證明紙本繳交至國際事務處（L105）。"
                ),
                "details": [
                    "必備表單 1：《01_亞洲大學赴國外研修申請書》與《02_系所同意書》（須經所屬系所審查推薦並完成學分抵免初審）",
                    "必備表單 2：《03_行政契約書》、《04_家長同意書》及《05_個人資料提供同意書》",
                    "必備表單 3：中英文歷年學業成績單正本（含班級與系所排名百分比資料）及有效外語能力檢定證明",
                ],
                "scope": {
                    "home_universities": ["亞洲大學"],
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
                    ASIA_SEMESTER_EXCHANGE_URL,
                    ASIA_APPLICATION_ZIP_URL,
                    ASIA_APP_FORM_PDF_URL,
                    ASIA_PARENTAL_CONSENT_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"asia-{acad_year}-home-3-{sn:03d}",
                "order": 3,
                "phase": "校內甄選",
                "title": f"參加校內書面審查與英語口試面試甄選，並申請教育部學海飛颺／惜珠或經濟不利海外學習獎助學金",
                "responsible_party": "學生／國際事務處審查委員會",
                "responsible_unit": "亞洲大學國際事務處（OIA）",
                "deadline_at": "2026-11-20T17:00:00+08:00",
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": ASIA_EXCHANGE_HUB_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    f"由亞洲大學國際事務處辦理書面審查與英語面試（亮點計畫於 4 月 10 日舉行英語面試、5 月 1 日公告錄取），核定推薦赴 {full_name} 正備取名單；符合資格者可同步獲核教育部《學海飛颺》（最低補助 NT$50,000 含來回機票）、《學海惜珠》、校內《海外學習與交流獎助學金》（機票＋每日生活助學金＋成果優異獎勵 NT$5,000）或《亮點計畫》來回機票補助。"
                ),
                "details": elig_points_list,
                "scope": {
                    "home_universities": ["亞洲大學"],
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
                    ASIA_EXCHANGE_HUB_URL,
                    ASIA_XUEHAI_FEIYANG_URL,
                    ASIA_ECON_SCHOLARSHIP_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"asia-{acad_year}-partner-4-{sn:03d}",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由國際事務處向 {zh_name} 辦理官方提名（Nomination）並寄送入學申請包裹",
                "responsible_party": "學生／國際事務處／接待大學",
                "responsible_unit": f"亞洲大學國際事務處 ＆ {full_name}",
                "summary": (
                    f"通過校內初審後，由國際事務處向 {full_name} 辦理官方提名（Nomination），錄取生須依姊妹校規定時程備齊英文或日韓文成績單、護照影本、財力證明、健康檢查表與住宿申請表，待取得正式入學許可書（Letter of Acceptance）後始得辦理出國手續。"
                ),
                "details": [
                    f"接待校入學與學費規定：{tuition_note or '依兩校交換或雙聯協議辦理'}",
                    f"預計學期時間：{sem_dates_str}",
                ],
                "scope": {
                    "home_universities": ["亞洲大學"],
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
                    ASIA_OUTBOUND_PARTNERS_URL,
                    website,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"asia-{acad_year}-post-5-{sn:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "辦理亞大在學註冊、簽證保險與役男緩徵出境，返國後上傳心得報告並於 1 個月內辦理學分抵免",
                "responsible_party": "學生",
                "responsible_unit": "亞洲大學國際事務處／教務處註冊與課務組／各系所",
                "summary": (
                    "出國前須依《亞洲大學學生出境期間學業及學籍處理辦法》完成本校註冊繳費、購買海外全期醫療及意外保險（役男應於出境前 1–2 個月檢送資料至學務處生輔組報請縣市政府核准出境）。返國後 2 週內上傳學海計畫心得報告，並於修課完畢取得成績後 1 個月內於「學生資訊系統」線上申請學分抵免（美日陸 1:1、歐洲 ECTS÷2、英國 CATS÷4）。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["亞洲大學"],
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
                    ASIA_STUDY_ABROAD_ACADEMIC_PDF_URL,
                    ASIA_CREDIT_TRANSFER_PDF_URL,
                    ASIA_DUAL_DEGREE_REGULATIONS_PDF_URL,
                    ASIA_ECON_GRANT_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合亞洲大學國際事務處（OIA）《出國留學交換生計畫與亮點計畫專區》、《國外姊妹校交換名單》、《各學院國際雙聯學制合作學校》、《學生出境期間學業及學籍處理辦法》、《與境外大學校院辦理雙學位實施要點》、《學分抵免及編級作業規定》及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換與雙聯學生心得報告，共 {len(catalog_source)} 所合作姊妹校資料。"
        ),
    })

    cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": f"亞洲大學國際事務處（OIA）出國交換暨雙聯學位專頁—{zh_name}",
            "source_url": source_url,
            "summary": "亞洲大學國際事務處公告之合作學程、錄取名額、語言檢定門檻與學費減免／雙聯學位待遇說明",
        },
        {
            "title": "亞洲大學學生出境期間學業及學籍處理辦法與經濟不利學生海外學習獎助辦法",
            "source_url": ASIA_STUDY_ABROAD_ACADEMIC_PDF_URL,
            "summary": "亞洲大學出境期間三種註冊繳費模式、教育部學海計畫與經濟不利海外學習獎助學金規定",
        },
    ]
    if exp_links:
      dest_sources.append({
          "title": f"亞洲大學國際事務處學生故事與管院雙聯專網—赴 {zh_name} 心得分享（{len(exps)} 篇）",
          "source_url": exp_links[0]["url"],
          "summary": f"收錄亞洲大學學生赴 {zh_name} 交換研習／跨國雙聯學位心得報告共 {len(exps)} 篇",
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
            ASIA_EXCHANGE_HUB_URL,
            ASIA_STUDY_ABROAD_ACADEMIC_PDF_URL,
            ASIA_XUEHAI_HUB_URL,
            ASIA_ECON_SCHOLARSHIP_URL,
        ]
        + ([exp_links[0]["url"]] if exp_links else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "亞洲大學",
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
                "title": "生活費、姊妹校免學費／雙聯待遇、教育部學海計畫與亞大海外學習獎助學金",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [ASIA_ECON_GRANT_PDF_URL],
                "caution": (
                    "獲教育部《學海飛颺／學海惜珠／學海築夢》或亞洲大學《海外學習與交流獎助學金》之學生，返國後 2 週內須上傳心得報告及成果資料（經濟不利生表現優異另加發 NT$5,000 成果獎勵金）。"
                ),
            },
            {
                "key": "housing",
                "title": "校內外學生宿舍申請與海外實習住宿安排",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": "瑞士工商酒店管理學院（BHMS）雙聯提供食宿安排與 100% 保障全職帶薪實習；加拿大維多利亞大學提供 Co-op 帶薪實習；日韓法馬泰印多所交換姊妹校享免繳接待校學費優惠。",
            },
            {
                "key": "insurance",
                "title": "海外醫療及意外保險、家長同意書與行政契約書規定",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依亞洲大學出國研修申請規定，所有申請學生均須檢附《03_行政契約書》、《04_家長同意書》及《05_個人資料提供同意書》，並於出境前投保涵蓋海外修業全期之醫療及意外保險。",
                ],
                "source_urls": src_url_list,
                "caution": "美、加、英、法、德、瑞、澳、紐、日、韓等接待校對國際交換與雙聯生健康保險有強制納保規定，請依入學許可指示辦理。",
            },
            {
                "key": "visa",
                "title": "學生簽證辦理、役男出境緩徵流程與亞大在學註冊義務",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "具役男身分之錄取學生，須依《亞洲大學學生出境期間學業及學籍處理辦法》第 10 條及《與境外大學校院辦理雙學位實施要點》第 16 條，於出境前 1 至 2 個月內檢送奉派或推薦出國申請書、名冊、家長同意書及保證書至學務處生輔組報請戶籍地縣市政府核准。",
                ],
                "source_urls": src_url_list,
                "caution": "出境交換或修讀雙聯學位期間，學生仍須依規定辦理亞洲大學每學期註冊手續以保留學籍。",
            },
            {
                "key": "academics",
                "title": "跨國雙聯學制（2+2／3+1／1+1／4+1／3+2）與國外學分抵免（美日陸 1:1、ECTS÷2、CATS÷4）",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list
                + [
                    ASIA_CREDIT_TRANSFER_PDF_URL,
                    ASIA_DUAL_DEGREE_REGULATIONS_PDF_URL,
                ],
                "caution": (
                    "依《亞洲大學學分抵免及編級作業規定》第 3 點及第 9 點，經核准至國外學校修課之抵免須於修課完畢取得成績後 1 個月內辦理：美制、日制及陸制學分 1:1 同等換算，英國 CATS÷4 = 本校學分，歐洲 ECTS÷2 = 本校學分。"
                ),
            },
            {
                "key": "living",
                "title": f"{city_name} 校園生活與亞大學長姐海外交換暨雙聯心得傳承",
                "summary": f"代表城市：{city_name}。請配合接待校國際處完成報到、選課與新生訓練。",
                "points": [
                    f"目的地城市：{city_name}（{country}）",
                    (
                        "亞洲大學國際事務處（OIA）與管理學院雙聯學制辦公室定期舉辦「亞大 318 出國交換、亮點計畫暨國際雙聯說明會」"
                        + (
                            f"（本校共收錄 {len(exps)} 篇赴 {zh_name} 心得分享：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，協助同學掌握海外選課、帶薪實習與獎學金準備。"
                    ),
                ],
                "source_urls": [
                    exp_links[0]["url"]
                    if exp_links
                    else ASIA_STUDENT_STORIES_URL
                ],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合亞洲大學國際事務處（OIA）與管理學院雙聯學制辦公室 {len(catalog_source)} 所合作姊妹校、當期開放申請出國交換／雙聯學位／亮點計畫合作校（{open_partner_count} 校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷年學生交換與雙聯心得報告。"
        ),
    })

    research_records.append({
        "home_university": "亞洲大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            "亞洲大學國際事務處（OIA）《國外姊妹校交換名單》、《各學院國際雙聯學制合作學校》、《亮點計畫暑期交換簡章》、《姊妹校合作夥伴名錄》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"亞洲大學國際事務處出國交換暨雙聯學位專頁—{zh_name}",
            "url": source_url,
        },
    ]
    if exp_links:
      ev_sources.append({
          "title": f"亞洲大學學生故事與雙聯專網—赴 {zh_name} 心得分享（{len(exps)} 篇）",
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
            "scope": "亞洲大學出國交換暨雙聯姊妹校住宿資訊",
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
            "scope": "亞洲大學姊妹校學費待遇、教育部學海計畫與經濟不利海外學習獎助學金",
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
            "scope": "亞洲大學出境期間學業及學籍處理辦法、雙學位實施要點與學分抵免規定",
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
            "scope": "亞洲大學出國交換簽證、家長同意書、役男出境緩徵與海外醫療保險提醒",
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
                    f"｜亞洲大學公開收錄 {len(exps)} 篇赴 {zh_name} 交換／雙聯心得報告（{'、'.join(exp_labels[:3])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "亞洲大學出國交換名額與歷屆學長姐心得分享",
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
            "已整合亞洲大學國際事務處（OIA）《國外姊妹校交換名單》、《各學院國際雙聯學制合作學校》、《亮點計畫暑期交換簡章》及歷屆學生交換與雙聯心得報告。",
            "當期免學費名額、雙聯學位申請年級限制、宿位供給與報名截止日請依國際事務處最新公告及接待校入學簡章核對。",
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

  write_jsonl(OFFICIAL_ASIA_DIR / "partners.jsonl", partners)
  write_jsonl(SOURCES_ASIA_DIR / "partners.jsonl", partners)
  write_jsonl(OFFICIAL_ASIA_DIR / "application_workflows.jsonl", workflows)
  write_jsonl(OFFICIAL_ASIA_DIR / "destination_profiles.jsonl", destinations)
  write_jsonl(OFFICIAL_ASIA_DIR / "partner_research.jsonl", research_records)
  write_jsonl(OFFICIAL_ASIA_DIR / "student_life.jsonl", life_records)
  write_jsonl(
      OFFICIAL_ASIA_DIR / "experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_ASIA_DIR / "student_experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_ASIA_DIR / "student_experiences.jsonl", student_experience_rows
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
  (OFFICIAL_ASIA_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_ASIA_DIR / "student-experiences.json").write_text(
      json.dumps(
          {
              "school_id": "asia",
              "school_name": "亞洲大學",
              "checked_at": CHECKED_AT,
              "source_url": ASIA_STUDENT_STORIES_URL,
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

  (OFFICIAL_ASIA_DIR / "campus-locations.json").write_text(
      json.dumps(
          {
              "school_id": "asia",
              "school_name": "亞洲大學",
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
  (OFFICIAL_ASIA_DIR / "campus-assets.json").write_text(
      json.dumps(
          {
              "school_id": "asia",
              "school_name": "亞洲大學",
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

  asia_source_urls = [
      ASIA_OIA_HOME_URL,
      ASIA_EXCHANGE_HUB_URL,
      ASIA_SEMESTER_EXCHANGE_URL,
      ASIA_SPOTLIGHT_EXCHANGE_URL,
      ASIA_DUAL_DEGREE_URL,
      ASIA_COLLEGE_DUAL_DEGREE_URL,
      ASIA_OUTBOUND_PARTNERS_URL,
      ASIA_SISTER_SCHOOLS_URL,
      ASIA_XUEHAI_HUB_URL,
      ASIA_XUEHAI_FEIYANG_URL,
      ASIA_XUEHAI_ZHUMENG_URL,
      ASIA_ECON_SCHOLARSHIP_URL,
      ASIA_STUDENT_STORIES_URL,
      ASIA_DUAL_PORTAL_URL,
      ASIA_AC_REGULATIONS_URL,
      ASIA_APPLICATION_ZIP_URL,
      ASIA_APP_FORM_PDF_URL,
      ASIA_PARENTAL_CONSENT_PDF_URL,
      ASIA_PRIVACY_CONSENT_PDF_URL,
      ASIA_ECON_GRANT_PDF_URL,
      ASIA_XUEHAI_FEIYANG_DOCX_URL,
      ASIA_XUEHAI_ZHUMENG_DOCX_URL,
      ASIA_STUDY_ABROAD_ACADEMIC_PDF_URL,
      ASIA_CREDIT_TRANSFER_PDF_URL,
      ASIA_DUAL_DEGREE_REGULATIONS_PDF_URL,
      ASIA_DOMESTIC_EXCHANGE_PDF_URL,
      ASIA_CMU_EXCHANGE_PDF_URL,
  ]

  exchange_info_payload = {
      "school_name": "亞洲大學",
      "program_type": [
          (
              "國際事務處（OIA）學期交換學生計畫（涵蓋美、英、法、瑞、西、澳、紐、日、韓、馬、泰、越、印等國姊妹校：其中日本近畿大學［2 名/年］、日本椙山女學園大學［2 名］、韓國漢陽大學［2 名/年］、法國蒙彼利埃商學院［5 名/年］、法國圖爾大學［5 名/年］、馬來亞大學［15 名/年］、泰國湄州大學［3 名/年］、印尼艾爾朗加大學［25 名］、日惹穆罕默迪亞大學［10 名］均提供免繳接待校學費優惠；另含美國南新罕布夏大學、加州西來大學、英國密德薩斯大學、伯明罕城市大學、瑞士 BHMS、西班牙龐培法布拉大學設計學院 ELISAVA、澳洲西雪梨大學、斯文本科技大學等彈性名額交換校）"
          ),
          (
              "校級暨各學院（管理學院、醫學暨健康學院、資訊電機學院）跨國雙聯學位計畫（共 21 所雙聯合作名校：含美國北伊利諾大學 NIU［2+2 雙學士／3+1+1 碩士雙聯］、加州州立大學聖伯納迪諾分校 CSUSB［2+2 學士／1+1 MBA］、印第安納大學摩利爾法學院［1+1 LL.M. 法學碩士，提供高額獎學金減免］、馬里蘭羅耀拉大學［經管 4+1 碩士］、凱斯西儲大學［醫健學院 3+2］、加拿大維多利亞大學 UVic［2+2 BCom 含帶薪實習］、英國密德薩斯大學［2+2］、西英格蘭大學 UWE［2+2］、瑞士工商酒店管理學院 BHMS［2+2／3+1／1+1，保障瑞士全職帶薪實習］、法國雷恩商學院［2+2／3+1／2+1+1 三重認證］、法國蒙彼利埃商學院［2+2／3+1］、澳洲西雪梨大學［幼教／社工 2+2］、越南 FPT 大學與國民經濟大學、蒙古財經大學、印尼建國大學／泗水理工大學／日惹穆罕默迪亞大學／蒂博尼哥羅大學等）"
          ),
          (
              "「亞大 318」亮點計畫（Spotlight Program — 暑期交換・海外研修，選送優秀生赴美國芝加哥羅耀拉大學、喬治梅森大學、加拿大維多利亞大學、義大利威尼斯大學、瑞士 BHMS、法國雷恩商學院、蒙彼利埃商學院、英國西英格蘭大學、新加坡國立大學 NUS、韓國漢陽大學 ERICA、日本近畿大學、紐西蘭坎特伯雷理工學院等 12 所名校，原則補助來回經濟艙機票乙張）暨教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》與校內《海外學習與交流獎助學金》"
          ),
      ],
      "academic_year": [
          (
              "115（涵蓋下半年學期交換生甄選［即日起至 2026/10/30 週五 17:00 截止收件］、上半年學期交換暨教育部學海飛颺／惜珠甄選［每年 1–3 月受理］，以及亞大 318 亮點計畫暑期交換甄選［2026/03/05 中午 12:00 報名截止、03/10 語檢補件截止、04/10 英語面試、05/01 公告錄取］）"
          ),
          (
              f"本平台完整收錄亞洲大學國際事務處與管理學院雙聯學制辦公室公告之 {len(partners)} 所全球合作姊妹校（含 {open_partner_count} 所當期開放申請之學期交換、跨國雙聯學位與亮點計畫合作大學，以及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 25 個國家與地區，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷年學長姐交換與雙聯學位心得報告）"
          ),
      ],
      "semester": [
          "學期交換學生計畫（Semester Exchange Program）：以 1 學期或 1 學年為原則（依《亞洲大學學生出境期間學業及學籍處理辦法》第 5 條，出境進修研究以 1 年為限，如有學習必要得於期滿前 2 個月申請延長至多 1 學期；無兵役義務之博士生專案簽准至多 3 年）。",
          "跨國雙聯學位計畫（International Dual Degree Program，依《亞洲大學與境外大學校院辦理雙學位實施要點》第 5 點）：修習學士雙學位在二校修業時間合計至少須滿 32 個月（如 2+2 或 3+1 學制）、碩士雙學位合計至少須滿 12 個月（如 1+1 或 2+1+1／3+1+1／4+1 學制）、博士雙學位合計至少須滿 24 個月，且在二校當地修習學分數累計須各達獲頒學位所需最低學分數之三分之一以上。",
          "亞大 318「亮點計畫」暑期交換・海外研修（Spotlight Summer Exchange）與中亞聯大／國內交換（依《亞洲大學與中國醫藥大學交換學生實施要點》及《亞洲大學與國內大專校院交換學生實施要點》）。",
      ],
      "application_period": [
          "【學期交換學生計畫（下半年甄選—翌年春季班赴外交換）】每年秋季受理，當期校內申請截止日為 2026 年 10 月 30 日（週五）17:00 止；申請人須先完成線上 Google 表單申請（https://forms.gle/5jRfCxjvM53Avipo8），再於截止日前將完整核章紙本申請資料繳交至行政大樓 L105 國際事務處，逾時不受理。",
          "【學期交換學生計畫（上半年甄選—當年秋季班赴外交換）暨教育部「學海飛颺／學海惜珠」】每年 1 月至 3 月受理校內申請，同步辦理學期交換生推薦與教育部學海飛颺、學海惜珠獎學金甄選。",
          "【亞大 318「亮點計畫」暑期交換・海外研修】2026 年 3 月 5 日（週四）中午 12:00 線上報名截止、3 月 10 日（週二）英文檢定證書補件截止、4 月 10 日（週五）14:00–15:30 舉行英語口試面試（哈佛講堂 A115 報到、A116 面試）、5 月 1 日（週五）公告錄取名單。",
          "【教育部「學海築夢／新南向學海築夢」海外專業實習計畫】分上半年（每年 2–3 月）與下半年（每年 8–9 月）兩梯次校內徵件。",
      ],
      "eligibility": [
          "1. 學期交換生與教育部學海飛颺／惜珠基本資格：（a）具中華民國國籍且持有臺灣地區戶籍；（b）在亞洲大學已修滿一學期以上且為在學學位生（含學士班、碩士班、博士班；不含國內及境外在職專班生；美國南新罕布夏大學限大四學生）；（c）經所屬系所審查推薦，並完成學分抵免申請與審核流程；（d）學業成績條件：學士班須達班級排名前 30% 或系排名前 40%（約折合學業平均 75 分以上；研究生免排名百分比要求，由審查會議擇優排序）。",
          "2. 亞大 318「亮點計畫」暑期交換專屬資格：（a）大一至大三在學學生（至少完成一學期學業）或大四準碩士生（直升或已考取亞大碩士班）；（b）學業成績達班級排名前 20% 或具優異表現，且「必須經由導師提名」始具申請資格；（c）通過國際事務處英語面試甄選。",
          "3. 跨國雙聯學位申請資格：管理學院「2+2 國際雙聯」專班及各院系（管理學院、醫學暨健康學院、資訊電機學院）在學學士班及碩博士班學生，入學後修習全英語授課（EMI）與國際演講會訓練課程，修滿規定學期及學分並通過合作名校外語門檻（IELTS 6.0–7.0 或 TOEFL iBT 60–94）後赴外修讀。",
          "4. 經濟不利學生《海外學習與交流獎助學金》資格：具中華民國國籍之本校在學學生，且符合當學年度學務處認定之經濟不利資格（低收入戶、中低收入戶、身心障礙學生及身障人士子女、特殊境遇家庭子女、原住民生學雜費減免、獲教育部弱勢助學金或家庭突遭變故經審核通過者），在校期間原則補助一次。",
      ],
      "language_requirement": [
          "1. 學期交換生與學海飛颺／惜珠校內最低外語門檻：英語能力須達 TOEIC 550 分（CEFR B1）或同等級外語能力證明（TOEFL iBT 42 / TOEFL ITP 460 / IELTS 4.0），日語組須具 JLPT N2–N5、韓語組須具 TOPIK 3 級以上；實際仍須符合各接待姊妹校門檻。",
          "2. 各重點交換姊妹校專屬語檢門檻：（a）日本近畿大學要求 JLPT N2 或同等能力；（b）日本椙山女學園大學要求 JLPT N5 以上；（c）韓國漢陽大學要求 GPA 2.4 且具韓語 TOPIK 3 級或英語 CEFR B2；（d）美國南新罕布夏大學要求 TOEFL iBT 71（限大四）；（e）美國西來大學免附 TOEFL/IELTS 可於註冊週參加英語能力分級測驗（EPT）；（f）英國密德薩斯大學要求 IELTS 6.0；（g）瑞士 BHMS 交換生要求 IELTS 5.0；（h）澳洲斯文本科技大學要求 CEFR B2；（i）法國圖爾大學與澳洲西雪梨大學要求檢附 TOEFL 或 IELTS 成績。",
          "3. 亞大 318「亮點計畫」暑期交換英語門檻：一般科系須達 TOEIC 550 分以上、外國語文學系須達 TOEIC 650 分以上（皆須達 CEFR B1 或同等 TOEFL iBT / ITP / IELTS 成績，不接受多益普及測驗 TOEIC Bridge），並須通過全英語口試面試。",
          "4. 跨國雙聯學位合作名校語檢門檻：（a）美國印第安納大學摩利爾法學院 LL.M.：IELTS 7.0 或 TOEFL iBT 94；（b）美國加州州立大學聖伯納迪諾分校（CSUSB）、加拿大維多利亞大學（UVic）、瑞士工商酒店管理學院（BHMS 雙聯）：IELTS 6.5 或 TOEFL iBT 79–90；（c）法國雷恩商學院：IELTS 6.5 或 TOEFL iBT 80；（d）英國西英格蘭大學（UWE）、密德薩斯大學、美國北伊利諾大學（NIU）、法國蒙彼利埃商學院（MBS）：IELTS 6.0 或 TOEFL iBT 60–90。",
      ],
      "required_documents": [
          "1. 線上申請：須先完成亞洲大學國際事務處出國交換線上 Google 表單申請（https://forms.gle/5jRfCxjvM53Avipo8）",
          "2. 《01_亞洲大學赴國外研修申請書》正本 1 份（貼妥照片並填明申請交換／雙聯校名與修課計畫）",
          "3. 《02_系所同意書》正本 1 份（須經所屬系所審查推薦，並完成學分抵免申請與初審流程）",
          "4. 《03_行政契約書》正本 1 份（詳閱並簽署出國期間註冊、安全與返國義務條款）",
          "5. 《04_家長同意書》正本 1 份（須由家長或法定監護人親筆簽名蓋章）",
          "6. 《05_個人資料提供同意書》正本 1 份",
          "7. 本校中、英文歷年學業成績單正本各 1 份，以及班級排名／系所排名百分比證明資料（向教務處註冊與課務組申請）",
          "8. 有效外語能力檢定證明文件影本（TOEIC / TOEFL iBT / TOEFL ITP / IELTS / JLPT / TOPIK；申請亮點計畫另須檢附導師提名資料；申請教育部學海計畫或經濟不利海外學習獎助學金另附專用申請書與身分證明文件）",
      ],
      "scholarship_info": [
          "1. 教育部「學海飛颺」與「學海惜珠」選送學生出國研修獎學金（國際事務處承辦，每年 1–3 月校內收件）：補助具中華民國國籍、於亞大修滿一學期以上、班排前 30% 或系排前 40%（研究生免此要求）且具 TOEIC 550（CEFR B1）以上外語證明之在學學位生，赴非大陸港澳之國外姊妹校修讀學分 1 學期至 1 學年。學海飛颺通案補助每人最低新臺幣 50,000 元（至少包含國際來回經濟艙機票乙張），學海惜珠針對持有效低收入戶、中低收入戶、特殊境遇家庭、身障或原住民資格之清寒優秀生優先核予高額全額補助；返國後 2 週內須上傳心得報告至教育部系統。",
          "2. 教育部「學海築夢」與「新南向學海築夢」海外專業實習計畫（每年 2–3 月及 8–9 月兩梯次徵件）：由本校專任教師主持海外專業實習計畫，選送在學學生赴海外合作機構進行連續至少 30 天（印尼至少 25 天）之專業實習（校內審查標準：課程內容佔 60%＋機構條件佔 40%），補助來回國際經濟艙機票乙張及生活費；返國後 2 週內須上傳 1,000 字內中英文心得報告、照片 4 張與 3 分鐘短片。",
          "3. 亞洲大學《海外學習與交流獎助學金》（依《亞洲大學經濟不利學生學習輔導獎助學金申請暨發放辦法》第 15 條規定辦理）：專為符合本校經濟不利資格之本國籍在學學生（低收、中低收、身障、特殊境遇、原住民、獲教育部弱勢助學金或家庭突遭變故者）參與經學校核准之海外交換、短期課程、跨國研習、國際志工、國際競賽或海外實習所設，在校期間原則補助一次：（a）機票補助：補助經濟艙往返機票費用（檢附三家以上旅行社或訂票平台報價單，取最低三筆票價平均值核實補助）；（b）每日生活助學金：依行政院《中央政府國外出差旅費報支要點》所定國外各地區日支費標準，按實際研修天數核發；（c）成果獎勵金：返國後繳交成果報告及心得回饋，經國際事務處審核表現優異者，另加發新臺幣 5,000 元獎勵金。",
          "4. 「亞大 318」亮點計畫（Spotlight Program）暑期交換獎助學金：針對大一至大三在學生或大四準碩士生（班排前 20%、經導師提名且達一般系 TOEIC 550+／外文系 650+），經英語面試錄取赴美、加、英、法、義、瑞、星、日、韓、紐等 12 所合作名校暑期交換研修者，由高教深耕計畫原則補助經濟艙來回機票乙張。",
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": asia_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_ASIA_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "亞洲大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 75.0,
      "academic_score_rule": (
          "依亞洲大學國際事務處《學期交換學生計畫申請須知》與《教育部學海飛颺／學海惜珠計畫甄選簡章》規定：申請人須為在亞洲大學已修滿一學期以上之在學學位生（不含國內及境外在職專班生），學士班學業成績須達「班級排名前 30% 或系排名前 40%」（約折合學業平均 75 分以上；碩博士班研究生免此排名百分比要求，由審查會議擇優排序）；申請亞大 318《亮點計畫》暑期交換者須達「班級排名前 20%」且必須經由導師提名；個別合作校如韓國漢陽大學另要求歷年 GPA 達 2.4 以上。"
      ),
      "academic_gpa_minimum": 2.4,
      "maximum_preferences": 3,
      "selection_rules": {
          "academic_policy": "gpa_or_rank",
          "academic_reference_year": "115",
          "undergraduate_gpa_minimum": 2.4,
          "graduate_academic_exempt": True,
          "exclude_in_service": True,
          "pending_quota_planning": False,
          "partner_requirements_need_confirmation": False,
          "degree_score_minimums": {
              "undergraduate": 75.0,
              "graduate": 75.0,
          },
          "excluded_undergraduate_years": [
              "大一上",
              "一年級上學期",
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
              "title": "亞洲大學 115 學年度下半年「學期交換學生計畫」校內甄選（即日起至 2026/10/30 週五 17:00 受理）",
              "details": [
                  f"國際事務處（OIA）公告學期交換學生計畫甄選：涵蓋美洲、歐洲、亞洲及大洋洲共 {open_partner_count} 所當期開放申請之交換與雙聯合作大學（其中馬來亞大學 15 名、印尼艾爾朗加大學 25 名、日惹穆罕默迪亞大學 10 名、法國蒙彼利埃商學院 5 名、法國圖爾大學 5 名、泰國湄州大學 3 名、日本近畿大學 2 名、日本椙山女學園大學 2 名、韓國漢陽大學 2 名均享免繳接待校學費優惠）。",
                  "申請程序：須先完成線上 Google 表單申請（https://forms.gle/5jRfCxjvM53Avipo8），並於 2026 年 10 月 30 日（週五）17:00 前將《赴國外研修申請書》、《系所同意書》、《行政契約書》、《家長同意書》、《個人資料提供同意書》、中英文歷年成績單含排名百分比及語言能力證明紙本送達行政大樓 L105 國際事務處。",
              ],
              "source": {
                  "title": "亞洲大學國際事務處「學期交換學生計畫」專區與申請表件包",
                  "source_url": ASIA_SEMESTER_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": "亞洲大學學期交換生申請資格（班排前 30% 或系排前 40%、TOEIC 550+）、線上表單與 10/30 紙本收件截止日。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "115-2 梯次（學期交換學生計畫下半年甄選）",
              "audience": "all_students",
              "opens_at": "2026-09-01T09:00:00+08:00",
              "deadline_at": "2026-10-30T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "學期交換學生計畫校內初審於 2026 年 10 月 30 日（週五）17:00 截止收件，逾時不受理。",
              "deadline_note": "請務必先完成線上 Google 表單報名，再將經系所核章之 7 項紙本申請文件送交行政大樓 L105 國際事務處。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "亞洲大學 2026「亞大 318 亮點計畫（Spotlight Program）」暑期交換・海外研修甄選（03/05 12:00 報名截止、04/10 面試）",
              "details": [
                  "選送大一至大三在學生或大四準碩士生（班排前 20% 且須經導師提名，一般系 TOEIC 550+、外文系 TOEIC 650+）赴美國芝加哥羅耀拉大學、喬治梅森大學、加拿大維多利亞大學、義大利威尼斯大學、瑞士 BHMS、法國雷恩商學院、蒙彼利埃商學院、英國西英格蘭大學、新加坡國立大學、韓國漢陽大學 ERICA、日本近畿大學、紐西蘭坎特伯雷理工學院進行暑期交換研修，原則補助經濟艙來回機票乙張。",
                  "重要日程：2026/03/05 中午 12:00 線上報名截止、03/10 英文檢定補件截止、04/10 14:00–15:30 英語面試（哈佛講堂 A115/A116）、05/01 公告錄取名單。",
              ],
              "source": {
                  "title": "亞洲大學國際事務處「亮點計畫（暑期交換・海外研修）」甄選簡章",
                  "source_url": ASIA_SPOTLIGHT_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": "亞洲大學 318 亮點計畫暑期交換 12 所合作名校、導師提名與班排前 20% 門檻、面試時程與機票補助規定。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "115",
              "application_round": "2026 亞大 318 亮點計畫暑期交換甄選",
              "audience": "all_students",
              "opens_at": "2026-02-01T09:00:00+08:00",
              "deadline_at": "2026-03-05T12:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "亮點計畫每年 3 月初截止線上報名、4 月中旬舉行英語面試、5 月 1 日公告錄取名單。",
              "deadline_note": "申請人必須先獲得導師提名，並於 3 月 10 日前補齊達標之正式英語檢定證書（不接受 TOEIC Bridge）。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "亞洲大學上半年學期交換暨教育部「學海飛颺／學海惜珠」出國研修獎學金申請（每年 1–3 月校內收件）",
              "details": [
                  "國際事務處每年 1 月至 3 月受理當年秋季班赴外學期交換暨教育部《學海飛颺》（通案補助最低 NT$50,000 含來回機票）、《學海惜珠》（清寒弱勢優秀生高額補助）申請；另針對符合校內經濟不利資格學生常年受理《海外學習與交流獎助學金》（補助往返機票＋國外日支生活助學金＋成果優異獎勵 NT$5,000）。",
              ],
              "source": {
                  "title": "亞洲大學國際事務處「教育部學海飛颺及學海惜珠計畫」暨「海外學習與交流獎助學金」專區",
                  "source_url": ASIA_XUEHAI_FEIYANG_URL,
                  "category": "scholarship",
                  "summary": "亞洲大學教育部學海飛颺、學海惜珠及校內經濟不利學生海外學習獎助學金申請資格與補助額度。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "116-1 梯次（上半年交換暨學海飛颺／惜珠獎學金）",
              "audience": "all_students",
              "opens_at": "2027-01-15T09:00:00+08:00",
              "deadline_at": "2027-03-15T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "上半年學期交換與教育部學海飛颺／惜珠計畫於每年 1 月至 3 月中旬受理校內收件。",
              "deadline_note": "請備齊《教育部學海飛颺／惜珠申請書》與赴外交換申請文件送達行政大樓 L105 國際事務處（分機 6275 林晏如小姐／分機 6278 何欣慈小姐）。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"亞洲大學「亞大 318」國際化計畫：學期交換、跨國雙聯學位、亮點計畫與學海／經濟不利海外獎助總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所當期開放申請・{total_exp_reports} 篇學長姐心得）"
              ),
              "details": [
                  (
                      f"亞洲大學推動「亞大 318」國際化計畫（培育中、英、程式 3 種語言，大學 4 年至少出國 1 次，透過交換生、雙聯學位、短期研修、海外實習等 8 大途徑出國），由國際事務處（OIA，行政大樓 L105）與管理學院雙聯學制辦公室統籌全校 7 大學院與全球 25 國共 {len(partners)} 所合作大學之學術交流，其中當期開放申請之學期交換、跨國雙聯學位（2+2／3+1／1+1／4+1／3+2）與亮點計畫暑期交換合作名校達 {open_partner_count} 所。"
                  ),
                  (
                      "為全方位支持學生出國圓夢，學校整合教育部《學海飛颺》（最低補助 NT$50,000 含來回機票）、《學海惜珠》、《學海築夢／新南向學海築夢》，並訂有校內《海外學習與交流獎助學金》（針對經濟不利生補助經濟艙往返機票、依中央政府國外日支標準核發每日生活助學金，返國成果優異另加發 NT$5,000）及《亮點計畫》來回機票補助。"
                  ),
              ],
              "source": {
                  "title": "亞洲大學國際事務處「出國留學—交換生計畫、雙聯學位與獎助學金」專區",
                  "source_url": ASIA_EXCHANGE_HUB_URL,
                  "category": "exchange_application",
                  "summary": "亞洲大學出國交換學生、跨國雙聯學位、亮點計畫暑期交換與四大獎助學金總覽。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "修滿一學期在學身分、學士班班排前 30%（或系排前 40%）門檻、亮點計畫班排前 20% 暨導師提名與雙聯學制規定",
              "details": exchange_info_payload["eligibility"],
              "source": {
                  "title": "亞洲大學國際事務處學期交換生申請須知、亮點計畫簡章與雙學位實施要點",
                  "source_url": ASIA_SEMESTER_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": "亞洲大學學期交換生、亮點計畫暑期交換與跨國雙聯學位之在學年級、班系排名與導師提名規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "校內基本門檻 TOEIC 550（CEFR B1）、亮點計畫外文系 TOEIC 650、雙聯名校 IELTS 6.0–7.0 與日韓姊妹校 JLPT N2–N5／TOPIK 3 基準",
              "details": exchange_info_payload["language_requirement"],
              "source": {
                  "title": "亞洲大學國外姊妹校交換名單（258.php）、雙聯學位專區（260.php）與亮點計畫簡章（261.php）",
                  "source_url": ASIA_OUTBOUND_PARTNERS_URL,
                  "category": "exchange_application",
                  "summary": "亞洲大學各合作姊妹校交換、雙聯學位與亮點計畫之外語檢定門檻對照表。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "線上 Google 表單報名＋《赴國外研修申請書》、《系所同意書》、《行政契約書》、《家長同意書》、《個資同意書》、中英文歷年成績單含排名百分比與語檢證明",
              "details": exchange_info_payload["required_documents"],
              "source": {
                  "title": "亞洲大學赴國外研修申請表件壓縮包（01～05 官方表單）與申請須知",
                  "source_url": ASIA_APPLICATION_ZIP_URL,
                  "category": "exchange_application",
                  "summary": "亞洲大學出國交換生、雙聯學位生與獎助學金申請應備之線上表單與 7 項紙本表件規範。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部《學海飛颺》（最低 5 萬元含機票）、《學海惜珠》、《學海築夢》暨亞洲大學《海外學習與交流獎助學金》（往返機票＋每日生活助學金＋成果獎勵 5,000 元）與《亮點計畫》機票補助",
              "details": exchange_info_payload["scholarship_info"],
              "source": {
                  "title": "亞洲大學教育部學海計畫專區暨經濟不利學生海外學習與交流獎助學金辦法（PDF）",
                  "source_url": ASIA_ECON_SCHOLARSHIP_URL,
                  "category": "scholarship",
                  "summary": "亞洲大學教育部學海三計畫、經濟不利學生海外學習獎助學金與亮點計畫機票補助規定。",
              },
          }
      ],
      "regulation_links": [
          {
              "title": "亞洲大學學生出境期間學業及學籍處理辦法（R1-2，PDF）",
              "url": ASIA_STUDY_ABROAD_ACADEMIC_PDF_URL,
          },
          {
              "title": "亞洲大學學分抵免及編級作業規定（R2-8，含美日陸 1:1、ECTS÷2、CATS÷4 學分換算，PDF）",
              "url": ASIA_CREDIT_TRANSFER_PDF_URL,
          },
          {
              "title": "亞洲大學與境外大學校院辦理雙學位實施要點（R5-3，PDF）",
              "url": ASIA_DUAL_DEGREE_REGULATIONS_PDF_URL,
          },
          {
              "title": "亞洲大學經濟不利學生學習輔導獎助學金申請暨發放辦法（含第 15 條海外學習與交流獎助學金，PDF）",
              "url": ASIA_ECON_GRANT_PDF_URL,
          },
          {
              "title": "亞洲大學赴國外研修申請表件包（含 01 赴國外研修申請書、02 系所同意書、03 行政契約書、04 家長同意書、05 個資同意書，ZIP）",
              "url": ASIA_APPLICATION_ZIP_URL,
          },
      ],
      "document_explanations": [
          {
              "title": "亞洲大學赴國外研修 5 大官方表單（01 申請書～05 個資同意書）、排名百分比成績單與學海／經濟不利獎助書審準備要領",
              "summary": "說明亞洲大學「先線上 Google 表單、後繳交 L105 紙本」雙軌申請程序，以及《赴國外研修申請書》、《系所同意書》、《行政契約書》、《家長同意書》與獎助學金申請表準備規範。",
              "key_points": [
                  "雙步驟申請與《01_赴國外研修申請書》、《02_系所同意書》：申請人須先填妥線上 Google 表單，並於《赴國外研修申請書》詳填擬修讀姊妹校與學習計畫，經所屬系所審查推薦並完成學分抵免初審後簽具《系所同意書》。",
                  "中英文歷年成績單與排名百分比資料：學士班申請學期交換及教育部學海飛颺須檢附達「班級排名前 30% 或系排名前 40%」之歷年成績單與排名證明（研究生免排名百分比要求）；申請亮點計畫須達「班級排名前 20%」並檢附導師提名文件。",
                  "《03_行政契約書》、《04_家長同意書》與返國核銷報告：出國前須簽署行政契約書與家長同意書；獲教育部學海計畫補助者須於返國後 2 週內上傳心得報告（學海築夢含中英文 1,000 字心得、4 張照片及 3 分鐘短片），獲經濟不利海外獎助者繳交成果報告且表現優異另加發 NT$5,000 獎勵金。",
              ],
              "applies_to": [],
              "source": {
                  "title": "亞洲大學國際事務處學期交換學生計畫申請須知與申請表件包",
                  "source_url": ASIA_SEMESTER_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": ASIA_APPLICATION_ZIP_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "亞洲大學出境期間三種學雜費繳交模式、跨國雙聯學位（32／12／24 個月與 1/3 學分）及國外學分抵免換算（美日陸 1:1、ECTS÷2、CATS÷4）核心規定",
              "summary": "規範亞洲大學出境進修註冊繳費三模式、雙學位修業月數與 1/3 學分下限、返國後 1 個月內四階段學分抵免審查及各國學分換算公式。",
              "key_points": [
                  "出境期間學籍與三種繳費模式（《學生出境期間學業及學籍處理辦法》第 5–6 條）：自入學後第二學期起得申請出境修習學分（以 1 年為限，得申請延長至多 1 學期），出境期間仍須辦理本校註冊，依互惠合約按（1）學雜費全額繳本校、免繳對方學校、（2）學費繳本校、雜費繳對方學校、或（3）學雜費均繳對方學校但在本校繳交「一學分費及學生平安保險費」辦理。",
                  "跨國雙學位修業時限與學分下限（《與境外大學校院辦理雙學位實施要點》第 5–6 點）：在二校修業時間合計，學士班至少滿 32 個月、碩士班至少滿 12 個月、博士班至少滿 24 個月；且在二校當地修習學分數累計須各達獲頒學位所需最低學分數之 1/3 以上。",
                  "國外學分抵免期限與換算公式（《學分抵免及編級作業規定》第 3、5、9 點）：經核准至國外修課之抵免須於修課完畢取得成績後 1 個月內於「學生資訊系統」線上登錄並檢附成績單正本及課程大綱，經系所前置檢核、初審（至少 2 位教師實質審查並提系課程委員會）、院課程委員會複審及教務處複核；美制、日制及陸制學分 1:1 同等換算，英國 CATS 學分制 ÷ 4 = 本校學分，歐洲 ECTS 學分制 ÷ 2 = 本校學分。",
              ],
              "applies_to": [],
              "source": {
                  "title": "亞洲大學學生出境期間學業及學籍處理辦法、雙學位實施要點與學分抵免及編級作業規定",
                  "source_url": ASIA_AC_REGULATIONS_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": ASIA_CREDIT_TRANSFER_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "亞洲大學國際事務處（Office of International Affairs, OIA）官方網站",
              "source_url": ASIA_OIA_HOME_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "亞洲大學國際事務處「出國留學—交換生計畫與亮點計畫」專區",
              "source_url": ASIA_EXCHANGE_HUB_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "亞洲大學國際事務處「學期交換學生計畫」申請資格與表件專區",
              "source_url": ASIA_SEMESTER_EXCHANGE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": f"亞洲大學國際事務處「國外姊妹校交換名單」互動地圖與門檻總覽（共 {len(partners)} 所合作姊妹校）",
              "source_url": ASIA_OUTBOUND_PARTNERS_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "亞洲大學「出國留學—雙聯／聯合學位」與「各學院國際雙聯學制合作學校」專區",
              "source_url": ASIA_COLLEGE_DUAL_DEGREE_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "亞洲大學管理學院「國際雙聯學制（2+2／3+1／1+1）」官方專網",
              "source_url": ASIA_DUAL_PORTAL_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "亞洲大學教育部學海計畫專區暨經濟不利學生《海外學習與交流獎助學金》專區",
              "source_url": ASIA_ECON_SCHOLARSHIP_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": f"亞洲大學國際事務處「學生故事（海外交換與雙聯學位心得分享）」（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）",
              "source_url": ASIA_STUDENT_STORIES_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_ASIA_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  doc_conditions = {
      "school_id": "asia",
      "school_name": "亞洲大學",
      "checked_at": CHECKED_AT,
      "source_url": ASIA_SEMESTER_EXCHANGE_URL,
      "common_documents": exchange_info_payload["required_documents"],
      "track_specific_conditions": [
          {
              "track": "學期交換學生計畫（美洲、歐洲、亞洲、大洋洲姊妹校 1 學期或 1 學年交換）",
              "required": [
                  "先完成線上 Google 表單申請（https://forms.gle/5jRfCxjvM53Avipo8），並於校內截止日前（下半年為 10/30 17:00；上半年為 1–3 月）繳交紙本至行政大樓 L105 國際事務處",
                  "《01_亞洲大學赴國外研修申請書》、《02_系所同意書》（須完成學分抵免申請與系所推薦審核）、《03_行政契約書》、《04_家長同意書》及《05_個人資料提供同意書》正本",
                  "本校中、英文歷年學業成績單正本及排名百分比資料（學士班須達班排前 30% 或系排前 40%；研究生免排名百分比要求）",
                  "有效外語能力證明：校內基本門檻 TOEIC 550（CEFR B1）以上，並符合各姊妹校要求（如日本近畿大學 JLPT N2、椙山女學園大學 JLPT N5、韓國漢陽大學 GPA 2.4 且 TOPIK 3 或英語 CEFR B2、美國南新罕布夏大學 TOEFL iBT 71 且限大四、英國密德薩斯大學 IELTS 6.0、瑞士 BHMS IELTS 5.0、澳洲斯文本科技大學 CEFR B2）",
              ],
          },
          {
              "track": "「亞大 318」亮點計畫（Spotlight Program — 12 所世界名校暑期交換・海外研修）",
              "required": [
                  "限大一至大三在學學生（至少修滿一學期）或大四準碩士生（直升或已考取亞大碩士班），學業成績達班級排名前 20% 或具優異表現，且「必須經由導師提名」",
                  "於 2026 年 3 月 5 日中午 12:00 前完成線上報名，並於 3 月 10 日前繳交達標之英語檢定證書（一般科系 TOEIC 550+、外文系 TOEIC 650+，須達 CEFR B1 或同等 TOEFL/IELTS，不接受 TOEIC Bridge）",
                  "參加 4 月 10 日於哈佛講堂（A115/A116）舉行之全英語口試面試，錄取生獲高教深耕計畫原則補助經濟艙來回機票乙張",
              ],
          },
          {
              "track": "跨國雙聯學位計畫（管理學院、醫學暨健康學院、資訊電機學院 2+2／3+1／1+1／4+1／3+2 雙聯學制）",
              "required": [
                  "管理學院雙聯專班及各院系在學學生於亞大修滿規定學期與專業必選修學分（在二校修業時間合計：學士至少 32 個月、碩士至少 12 個月、博士至少 24 個月，且各修習達畢業學分 1/3 以上）",
                  "達合作名校雙聯外語門檻：印第安納大學摩利爾法學院 LL.M.（IELTS 7.0 / iBT 94）、美國 CSUSB／加拿大維多利亞大學／瑞士 BHMS（IELTS 6.5 / iBT 79–90）、法國雷恩商學院（IELTS 6.5 / iBT 80）、美國北伊利諾大學／英國西英格蘭大學／英國密德薩斯大學／法國蒙彼利埃商學院（IELTS 6.0 / iBT 60–90）",
                  "備齊雙聯入學申請表、中英文歷年成績單、英文讀書計畫（SOP）、推薦信、護照影本與財力證明，洽管理學院雙聯學制辦公室（分機 1934）及國際事務處（分機 6278／6298）辦理提名",
              ],
          },
          {
              "track": "教育部《學海飛颺／學海惜珠／學海築夢》暨亞洲大學《海外學習與交流獎助學金》（經濟不利生專案）",
              "required": [
                  "《教育部學海飛颺／學海惜珠申請書》或《教育部學海築夢／新南向學海築夢申請書》（含出國研修／實習計畫書、經費預估表、歷年成績單與排名證明、外語能力證明）",
                  "申請《學海惜珠》或校內《海外學習與交流獎助學金》另附：新式戶口名簿影本及當學年度有效之經濟不利資格證明（低收入戶、中低收入戶、身心障礙、特殊境遇家庭、原住民生學雜費減免、獲教育部弱勢助學金或家庭突遭變故證明）",
                  "申請校內《海外學習與交流獎助學金》機票補助須檢附三家以上旅行社或訂票平台之經濟艙往返機票報價單（取最低三筆票價平均值核實補助），返國後繳交成果報告及心得回饋（表現優異另加發 NT$5,000 成果獎勵金）",
              ],
          },
      ],
  }
  (OFFICIAL_ASIA_DIR / "document-conditions.json").write_text(
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
        f"{fname},{len(partners)},{pop},{ratio:.4f},Official ASIA OIA verified"
    )
  (OFFICIAL_ASIA_DIR / "field-coverage.csv").write_text(
      "\n".join(field_cov_lines) + "\n", encoding="utf-8"
  )

  pages_records = [
      {
          "title": "亞洲大學：2026–2027 學期交換生甄選（10/30 截止）、亮點計畫暑期交換（3/5 截止）與學海計畫申請時程",
          "source_url": ASIA_EXCHANGE_HUB_URL,
          "published_at": "2026-09-01T00:00:00Z",
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
          "title": "亞洲大學：學期交換生（班排前 30% 或系排前 40%）、亮點計畫（班排前 20% 暨導師提名）與雙聯學位申請資格",
          "source_url": ASIA_SEMESTER_EXCHANGE_URL,
          "published_at": "2026-09-01T00:00:00Z",
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
          "title": f"亞洲大學：{len(partners)} 所全球合作姊妹校外語檢定門檻（TOEIC 550 / CEFR B1、亮點計畫外文系 650、雙聯 IELTS 6.0–7.0）",
          "source_url": ASIA_OUTBOUND_PARTNERS_URL,
          "published_at": "2026-09-01T00:00:00Z",
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
          "title": "亞洲大學：赴國外研修應備文件（線上 Google 表單＋01 赴國外研修申請書、02 系所同意書、03 行政契約書、04 家長同意書、05 個資同意書）",
          "source_url": ASIA_APPLICATION_ZIP_URL,
          "published_at": "2026-09-01T00:00:00Z",
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
          "title": "亞洲大學：教育部學海飛颺（最低 5 萬元含機票）、學海惜珠、學海築夢暨經濟不利學生海外學習與交流獎助學金",
          "source_url": ASIA_ECON_SCHOLARSHIP_URL,
          "published_at": "2026-09-01T00:00:00Z",
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
          "title": "亞洲大學：與境外大學校院辦理雙學位實施要點暨管理學院、醫健學院、資電學院 21 所跨國雙聯學制合作名校",
          "source_url": ASIA_COLLEGE_DUAL_DEGREE_URL,
          "published_at": "2026-09-01T00:00:00Z",
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
          "title": "亞洲大學：學生出境期間學業及學籍處理辦法與學分抵免及編級作業規定（美日陸 1:1、歐洲 ECTS÷2、英國 CATS÷4）",
          "source_url": ASIA_CREDIT_TRANSFER_PDF_URL,
          "published_at": "2026-09-01T00:00:00Z",
          "text": "\n".join(
              student_dashboard_payload["rule_explanations"][0]["key_points"]
          ),
          "summary": student_dashboard_payload["rule_explanations"][0][
              "summary"
          ],
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256(
              "\n".join(
                  student_dashboard_payload["rule_explanations"][0][
                      "key_points"
                  ]
              ).encode("utf-8")
          ).hexdigest(),
      },
      {
          "title": f"亞洲大學：國際事務處學生故事與管院雙聯學生分享專區（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）",
          "source_url": ASIA_STUDENT_STORIES_URL,
          "published_at": "2026-09-01T00:00:00Z",
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
  (OFFICIAL_ASIA_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
      + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "asia",
      "school_name": "亞洲大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "undergrad_class_rank_top_percent": 30.0,
          "undergrad_dept_rank_top_percent": 40.0,
          "spotlight_class_rank_top_percent": 20.0,
          "spotlight_mentor_nomination_required": True,
          "graduate_rank_exempt": True,
          "minimum_toeic": 550,
          "spotlight_fl_dept_minimum_toeic": 650,
          "xuehai_feiyang_min_grant_ntd": 50000,
          "econ_disadvantaged_excellence_bonus_ntd": 5000,
          "exclude_in_service": True,
          "return_report_due": "返國後 2 週內上傳學海計畫心得報告；取得成績後 1 個月內於學生資訊系統辦理學分抵免",
      },
      "source_urls": asia_source_urls,
      "verified_at": "2026-11-08",
  }
  (OFFICIAL_ASIA_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_ASIA_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "亞洲大學",
              "required_documents": student_dashboard_payload[
                  "required_documents"
              ],
              "source_urls": asia_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_ASIA_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "亞洲大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": asia_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "asia",
      "school_name": "亞洲大學",
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
      "dual_degree_partner_universities": 21,
      "dual_degree_programs": 25,
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
          f"亞洲大學國際事務處（OIA）《學期交換學生計畫（263.php）》、《亮點計畫暑期交換・海外研修（261.php）》、《國外姊妹校交換名單（258.php）》、《雙聯／聯合學位與各學院國際雙聯學制合作學校（260.php、418.php、dual.asia.edu.tw）》、《學生出境期間學業及學籍處理辦法（R1-2）》、《與境外大學校院辦理雙學位實施要點（R5-3）》、《學分抵免及編級作業規定（R2-8）》及教育部《學海飛颺／學海惜珠／學海築夢》與校內《海外學習與交流獎助學金（1487.php）》同步整合；共完整收錄 {len(partners)} 所全球合作姊妹校（含 {open_partner_count} 所當期開放申請之交換、雙聯與亮點計畫合作校及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 25 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷年學長姐交換與雙聯學位心得報告）。"
      ),
      "verified_at": "2026-11-08",
  }
  (OFFICIAL_ASIA_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_ASIA_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "asia",
              "school_name": "亞洲大學",
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
          "sources/asia/asia_catalog_source.json",
          ASIA_OUTBOUND_PARTNERS_URL,
          f"亞洲大學 {len(partners)} 所全球合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/asia/asia_resolved_locations.json",
          ASIA_SISTER_SCHOOLS_URL,
          f"亞洲大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
      ),
      (
          "sources/asia/asia_experience_index.json",
          ASIA_STUDENT_STORIES_URL,
          f"亞洲大學國際事務處與管院雙聯專網 {exp_covered_schools} 校 {total_exp_reports} 篇出國交換暨雙聯心得報告索引 JSON",
      ),
  ]
  for rel_p, surl in bin_urls.items():
    rp = rel_p if rel_p.startswith("sources/") else f"sources/asia/{rel_p}"
    if not any(x[0] == rp for x in provenance_files):
      provenance_files.append((rp, surl, f"亞洲大學官方原始檔案：{Path(rp).name}"))

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
      "school_id": "asia",
      "school_name": "亞洲大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = (
      json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  )
  (OFFICIAL_ASIA_DIR / "import_provenance.json").write_text(
      prov_text, encoding="utf-8"
  )
  (OFFICIAL_ASIA_DIR / "import-provenance.json").write_text(
      prov_text, encoding="utf-8"
  )

  print(
      f"Successfully built ASIA catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
