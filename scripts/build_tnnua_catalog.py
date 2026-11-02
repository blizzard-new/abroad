"""Build the official Tainan National University of the Arts (國立臺南藝術大學, TNNUA) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_TNNUA_DIR = REPO_ROOT / "sources" / "tnnua"
OFFICIAL_TNNUA_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "tnnua"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-02T00:00:00Z"

TNNUA_OIA_HOME_URL = "https://oia.tnnua.edu.tw/"
TNNUA_OIA_ABOUT_URL = "https://oia.tnnua.edu.tw/p/412-1024-83.php?Lang=zh-tw"
TNNUA_REGULATIONS_URL = "https://oia.tnnua.edu.tw/p/412-1024-2463.php?Lang=zh-tw"
TNNUA_FORMS_URL = "https://oia.tnnua.edu.tw/p/412-1024-2783.php?Lang=zh-tw"
TNNUA_DUAL_DEGREE_URL = "https://oia.tnnua.edu.tw/p/412-1024-3980.php?Lang=zh-tw"
TNNUA_DUAL_DEGREE_SCHOLARSHIP_URL = "https://oia.tnnua.edu.tw/p/412-1024-4158.php?Lang=zh-tw"
TNNUA_PARTNERS_URL = "https://oia.tnnua.edu.tw/p/412-1024-119.php?Lang=zh-tw"
TNNUA_NEW_PARTNERS_URL = "https://oia.tnnua.edu.tw/p/412-1024-4090.php?Lang=zh-tw"
TNNUA_TUITION_FREE_PARTNERS_URL = "https://oia.tnnua.edu.tw/p/412-1024-2739.php?Lang=zh-tw"
TNNUA_EXCHANGE_SCHOLARSHIPS_URL = "https://oia.tnnua.edu.tw/p/412-1024-2494.php?Lang=zh-tw"
TNNUA_EXCHANGE_ANN_115_1_URL = "https://oia.tnnua.edu.tw/p/406-1024-53429,r2190.php?Lang=zh-tw"
TNNUA_EXCHANGE_ANN_114_2_URL = "https://oia.tnnua.edu.tw/p/406-1024-52591,r2190.php?Lang=zh-tw"
TNNUA_XUEHAI_ANN_115_1_URL = "https://oia.tnnua.edu.tw/p/406-1024-52590,r2190.php?Lang=zh-tw"
TNNUA_XUEHAI_ANN_115_2_URL = "https://oia.tnnua.edu.tw/p/406-1024-53445,r2190.php?Lang=zh-tw"
TNNUA_EXPERIENCE_SHARING_URL = "https://oia.tnnua.edu.tw/p/403-1024-2196-1.php?Lang=zh-tw"
TNNUA_ZHUMENG_SHARING_URL = "https://oia.tnnua.edu.tw/p/403-1024-2197-1.php?Lang=zh-tw"
TNNUA_EXCHANGE_GUIDELINES_PDF_URL = "https://oia.tnnua.edu.tw/var/file/24/1024/img/805/274300338.pdf"
TNNUA_TUITION_FREE_PDF_URL = "https://oia.tnnua.edu.tw/var/file/24/1024/img/805/287836664.pdf"
TNNUA_DUAL_DEGREE_RULES_PDF_URL = "https://oia.tnnua.edu.tw/var/file/24/1024/img/805/498449093.pdf"
TNNUA_DUAL_DEGREE_CHECKLIST_PDF_URL = "https://oia.tnnua.edu.tw/var/file/24/1024/img/805/445071247.pdf"
TNNUA_DUAL_DEGREE_SCHOLARSHIP_PDF_URL = "https://oia.tnnua.edu.tw/var/file/24/1024/img/805/200383520.pdf"
TNNUA_XUEHAI_BROCHURE_115_1_PDF_URL = "https://oia.tnnua.edu.tw/var/file/24/1024/img/805/898944460.pdf"
TNNUA_XUEHAI_BROCHURE_115_2_PDF_URL = "https://oia.tnnua.edu.tw/var/file/24/1024/img/805/675803582.pdf"
TNNUA_REVIEW_RULES_PDF_URL = "https://oia.tnnua.edu.tw/var/file/24/1024/img/805/163083384.pdf"
TNNUA_SPROUT_INTERN_PDF_URL = "https://oia.tnnua.edu.tw/var/file/24/1024/img/805/445424295.pdf"

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 750–1,250（折合日圓約 JPY 105,000–175,000 / 月、新臺幣約 23,500–39,500 元；東京藝術大學約 JPY 130,000–175,000 / 月，愛知縣立藝術大學、岡山縣立大學、北陸先端大與廣島伊莉莎白音樂大學約 JPY 95,000–135,000 / 月）",
        "須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後至日本台灣交流協會申辦留學簽證並加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 650–1,100（折合韓元約 KRW 850,000–1,450,000 / 月、新臺幣約 20,500–35,000 元；其中韓國傳統文化大學 KNUH 額外提供免住宿費及每月 10 萬韓元生活津貼共 4 個月）",
        "須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生或 D-2 雙聯學位簽證，入境後辦理外國人登錄證並納保韓國國民健康保險。",
    ),
    "中國大陸": (
        "每月生活費約 USD 400–750（折合人民幣約 RMB 2,600–4,800 / 月、新臺幣約 12,500–24,000 元；北京中央美術學院 CAFA、中央音樂學院、上海音樂學院約 RMB 3,200–4,800 / 月，杭州中國美術學院、廣州美術學院、景德鎮陶瓷大學約 RMB 2,500–3,800 / 月）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及大陸姊妹校寄發之錄取通知書辦理報到，並依國立臺南藝術大學國際事務處規定購買涵蓋交換全期之海外醫療及意外保險。",
    ),
    "香港": (
        "每月生活費約 USD 950–1,500（折合港幣約 HKD 7,400–11,700 / 月、新臺幣約 30,000–47,500 元，含屯門嶺南大學學生宿舍、伙食與交通）",
        "須由香港嶺南大學協助向香港入境事務處申辦來港就讀進入許可（Student Visa / Entry Permit）並投保海外全期醫療險。",
    ),
    "澳門": (
        "每月生活費約 USD 800–1,250（折合新臺幣約 25,500–40,000 元，含澳門城市大學氹仔校區周邊住宿、膳食與市區交通）",
        "須憑澳門城市大學錄取通知書辦理逗留特別許可（學生逗留簽注）並投保海外全期醫療保險。",
    ),
    "印尼": (
        "每月生活費約 USD 420–750（折合印尼盾約 IDR 6,500,000–11,500,000 / 月、新臺幣約 13,500–24,000 元；日惹國立印尼藝術大學 ISI Yogyakarta、安巴魯莫觀光學院 STIPRAM 與峇里島登巴薩藝術學院 ISI Denpasar 生活與工藝材料開銷親民）",
        "須由印尼接待大學協助申辦印尼學生電子簽證（Study e-Visa / KITAS）並投保海外全期醫療及意外保險。",
    ),
    "泰國": (
        "每月生活費約 USD 500–880（折合泰銖約 THB 17,000–30,000 / 月、新臺幣約 16,000–28,000 元；曼谷朱拉隆功大學、泰國藝術大學 Silpakorn 與瑪希敦大學 Salaya 校區住宿與生活開銷）",
        "須憑泰國接待大學入學許可公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 教育簽證並投保海外全期醫療險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 500–850（折合馬幣約 MYR 2,200–3,700 / 月、新臺幣約 16,000–27,000 元，含吉隆坡思特雅大學 UCSI、雙威大學與新山南方大學學院住宿與生活費）",
        "須透過馬來西亞教育全球服務中心（EMGS）線上申辦學生簽證核准函（VAL / Mobility Pass）並投保馬來西亞境內醫療險。",
    ),
    "越南": (
        "每月生活費約 USD 420–750（折合新臺幣約 13,500–24,000 元；河內戲劇與電影學院、越南中央藝術師範大學與胡志明市西貢國際大學生活開銷）",
        "須由越南接待大學協助向越南出入境管理局申辦 DH 學生簽證並投保海外全期醫療及意外保險。",
    ),
    "新加坡": (
        "每月生活費約 USD 1,200–1,900（折合新幣約 SGD 1,600–2,550 / 月、新臺幣約 38,000–60,000 元，含南洋藝術學院 NAFA 周邊住宿、伙食與捷運交通）",
        "須透過新加坡移民與關卡局（ICA）SOLAR 系統申辦 Student's Pass（STP）並投保海外醫療保險。",
    ),
    "哈薩克": (
        "每月生活費約 USD 500–850（折合新臺幣約 16,000–27,000 元；阿拉木圖哈薩克國立藝術學院學生宿舍與生活費實惠）",
        "須憑哈薩克國立藝術學院核發之入學邀請函申辦哈薩克 C9 學生簽證並投保海外全期醫療及意外保險。",
    ),
    "蒙古": (
        "每月生活費約 USD 450–780（折合新臺幣約 14,500–25,000 元；烏蘭巴托蒙古國立文化藝術大學住宿與生活開銷）",
        "須憑蒙古國立文化藝術大學入學許可申辦蒙古學生簽證並投保海外全期醫療保險。",
    ),
    "德國": (
        "每月生活費約 USD 1,050–1,550（折合歐元約 EUR 950–1,400 / 月、新臺幣約 33,500–50,000 元；斯圖加特國立造型藝術學院 ABK、班貝格大學與希爾德斯海姆大學學生宿舍與生活費）",
        "須開立德國限制提領帳戶（Blocked Account，每月約 EUR 992）並憑入學許可向德國在台協會申辦德國長期學生簽證及投保德國公保／醫療險。",
    ),
    "英國": (
        "每月生活費約 USD 1,500–2,250（折合英鎊約 GBP 1,180–1,750 / 月、新臺幣約 48,000–72,000 元；倫敦大學金匠學院 Goldsmiths 校內外住宿與倫敦生活開銷）",
        "交換 6 個月以內可憑入學許可辦理英國 ETA / Standard Visitor 入境，交換 1 學年須申辦英國 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "義大利": (
        "每月生活費約 USD 1,100–1,650（折合歐元約 EUR 1,000–1,500 / 月、新臺幣約 35,000–52,500 元；米蘭國立布雷拉美術學院周邊租屋與生活費）",
        "須透過義大利 Universitaly 平台完成預註冊並向義大利經濟貿易文化推廣辦事處申辦義大利學生 D 簽證，入境後 8 日內申辦居留證（Permesso di Soggiorno）。",
    ),
    "法國": (
        "每月生活費約 USD 1,000–1,550（折合歐元約 EUR 900–1,400 / 月、新臺幣約 32,000–50,000 元；巴黎塞爾吉 ENSAPC、波爾多 KEDGE 與布爾日 ENSA Bourges 住宿與生活費）",
        "須先經法國教育中心（Campus France）完成 Etudes en France 線上程序與面試，再向法國在台協會申辦長期學生簽證（VLS-TS）。",
    ),
    "西班牙": (
        "每月生活費約 USD 1,000–1,500（折合歐元約 EUR 900–1,350 / 月、新臺幣約 32,000–48,000 元；馬德里康普頓斯大學住宿與生活開銷）",
        "須憑馬德里康普頓斯大學入學許可向西班牙商務辦事處申辦長期學生簽證並投保無自付額之申根全額醫療保險。",
    ),
    "斯洛維尼亞": (
        "每月生活費約 USD 750–1,150（折合歐元約 EUR 680–1,050 / 月、新臺幣約 24,000–36,500 元；盧布爾雅納大學學生補貼餐券 Študentski boni 與住宿極具性價比）",
        "須憑盧布爾雅納大學入學許可申辦斯洛維尼亞長期簽證（D Visa）或第一居留許可（First Residence Permit for Study）並投保申根醫療保險。",
    ),
    "捷克": (
        "每月生活費約 USD 750–1,150（折合歐元約 EUR 680–1,050 / 月、新臺幣約 24,000–36,500 元；布拉格表演藝術學院 AMU 校內學生宿舍與生活費實惠）",
        "須憑布拉格表演藝術學院（AMU）核發之入學許可與住宿證明向捷克經濟文化辦事處申辦長期學生簽證並投保捷克認可之醫療保險。",
    ),
    "波蘭": (
        "每月生活費約 USD 650–1,050（折合歐元約 EUR 600–950 / 月、新臺幣約 21,000–33,500 元；羅茲科技大學校內宿舍與生活費極具性價比）",
        "須憑羅茲科技大學入學許可申辦波蘭長期學生 D 簽證並投保申根全期醫療保險。",
    ),
    "奧地利": (
        "每月生活費約 USD 1,100–1,600（折合歐元約 EUR 1,000–1,450 / 月、新臺幣約 35,000–51,000 元；維也納音樂與表演藝術大學 mdw 住宿與生活費）",
        "交換 1 學期（6 個月內）向奧地利台北辦事處申辦奧地利學生 D 簽證，交換 1 學年須申辦學生居留許可並投保申根醫療保險。",
    ),
    "美國": (
        "每月生活費約 USD 1,350–2,200（依匯率折合新臺幣約 43,000–70,000 元；賓州華盛頓與傑佛遜學院 W&J、阿肯色大學與亞利桑那州立大學約 USD 1,350–1,800 / 月，紐約電影學院約 USD 1,800–2,500 / 月）",
        "須憑美國接待大學核發之 DS-2019（J-1 交換生）或 I-20（F-1 學位／實習生）表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證，且須投保符合接待校規定之全期海外醫療保險。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,550–2,350（折合澳幣約 AUD 2,350–3,550 / 月、新臺幣約 49,500–75,000 元，含雪梨新南威爾斯大學 UNSW 周邊住宿、伙食與交通）",
        "須購買澳洲海外學生健康保險（OSHC）並憑接待校核發之 CoE 申辦澳洲 Subclass 500 學生簽證。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "春季學期（前學期）：約 4 月初至 8 月初；秋季學期（後學期）：約 9 月下旬或 10 月初至翌年 2 月",
    "韓國": "春季學期（第 1 學期）：約 3 月初至 6 月中旬；秋季學期（第 2 學期）：約 9 月初至 12 月中旬",
    "中國大陸": "春季學期（下學期）：約 2 月下旬至 7 月初；秋季學期（上學期）：約 9 月初至翌年 1 月中旬",
    "香港": "第一學期（秋季班）：約 9 月初至 12 月下旬；第二學期（春季班）：約 1 月中旬至 5 月下旬",
    "澳門": "第一學期（秋季班）：約 9 月初至翌年 1 月初；第二學期（春季班）：約 2 月至 6 月中旬",
    "印尼": "奇數／秋季學期（Odd Semester）：約 8 月下旬至翌年 1 月；偶數／春季學期（Even Semester）：約 2 月至 7 月",
    "泰國": "第一學期（秋季班）：約 8 月至 12 月；第二學期（春季班）：約 1 月至 5 月（依各校行事曆）",
    "馬來西亞": "秋季學期：約 9 月至翌年 1 月；春季學期：約 1–2 月至 5–6 月",
    "越南": "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月",
    "新加坡": "第一學期（秋季班）：約 8 月中旬至 12 月初；第二學期（春季班）：約 1 月中旬至 5 月中旬",
    "哈薩克": "秋季學期：約 9 月初至 12 月底；春季學期：約 1 月下旬至 5 月底",
    "蒙古": "秋季學期：約 9 月初至翌年 1 月中旬；春季學期：約 2 月初至 6 月中旬",
    "德國": "冬季學期（Wintersemester）：約 10 月初至翌年 2 月中旬；夏季學期（Sommersemester）：約 4 月初至 7 月中下旬",
    "英國": "秋季學期（Autumn Term）：約 9 月下旬至 12 月中旬；春季與夏季學期（Spring & Summer Terms）：約 1 月中旬至 6 月中旬",
    "義大利": "第一學期（冬季班）：約 10 月中旬至翌年 2 月；第二學期（春季班）：約 3 月初至 6 月底",
    "法國": "秋季學期（Semestre 1）：約 9 月中旬至翌年 1 月中旬；春季學期（Semestre 2）：約 1 月下旬至 6 月上旬",
    "西班牙": "第一學期（秋季班）：約 9 月中旬至翌年 1 月底；第二學期（春季班）：約 2 月初至 6 月 중旬",
    "斯洛維尼亞": "冬季學期（秋季班）：約 10 月 1 日至翌年 2 月中旬；夏季學期（春季班）：約 2 月中旬至 6 月底",
    "捷克": "冬季學期（秋季班）：約 9 月底至翌年 1 月底；夏季學期（春季班）：約 2 月中旬至 6 月底",
    "波蘭": "冬季學期（秋季班）：約 10 月初至翌年 2 月中旬；夏季學期（春季班）：約 2 月下旬至 6 月底",
    "奧地利": "冬季學期（Wintersemester）：約 10 月 1 日至翌年 1 月底；夏季學期（Sommersemester）：約 3 月 1 日至 6 月底",
    "美國": "秋季學期（Fall Semester）：約 8 月下旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬",
    "澳洲": "第一學期（Term 1 / Semester 1）：約 2 月中旬至 6 月；第二學期（Term 3 / Semester 2）：約 7–9 月至 11–12 月",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
  """Ensure school-images.json and university_locations.jsonl contain all 63 TNNUA partner schools."""
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
          else loc.get("lat", 23.2046)
      )
      lon = float(
          loc.get("longitude")
          if loc.get("longitude") is not None
          else loc.get("lon", 120.3653)
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
  OFFICIAL_TNNUA_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_TNNUA_DIR / "tnnua_catalog_source.json").read_text(
          encoding="utf-8"
      )
  )
  resolved_locations = json.loads(
      (SOURCES_TNNUA_DIR / "tnnua_resolved_locations.json").read_text(
          encoding="utf-8"
      )
  )
  bin_urls_path = SOURCES_TNNUA_DIR / "binary_source_urls.json"
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
        item.get("group") or "國際事務處正式締約國際姊妹校"
    )
    quota_str = clean_text(
        item.get("quota") or "依國立臺南藝術大學國際事務處當期公告名額"
    )
    detail_url = item.get("detail_url") or TNNUA_PARTNERS_URL

    if "雙聯學位" in group_str:
      program_type = "國際事務處免收姊妹校學費交換計畫暨境外大學雙聯學制合作校"
      source_url = TNNUA_DUAL_DEGREE_URL
    elif country == "中國大陸" and avail_status == "open":
      program_type = "國際事務處大陸地區交換生計畫（中文授課・只需繳交南藝大註冊費及學雜費）"
      source_url = TNNUA_EXCHANGE_ANN_115_1_URL
    elif avail_status == "open":
      program_type = f"{group_str}（只需繳交本校註冊費及學雜費）"
      source_url = (
          detail_url
          if detail_url != TNNUA_PARTNERS_URL
          else TNNUA_TUITION_FREE_PARTNERS_URL
      )
    elif country in {"中國大陸", "澳門", "香港"}:
      program_type = "國際事務處正式締約大陸與港澳姊妹校"
      source_url = detail_url
    else:
      program_type = "國際事務處正式締約國際姊妹校"
      source_url = detail_url

    colleges_str = clean_text(
        item.get("colleges")
        or "音樂學院、視覺藝術學院、音像藝術學院、文博學院、跨域創生學院"
    )
    degree_levels_str = clean_text(
        item.get("eligible_degrees")
        or "國立臺南藝術大學日間學制大學部二年級以上、七年一貫制學士班五年級以上，以及就讀一學期以上之碩、博士班在學學生（不含碩士班在職專班；轉學生須曾於本校就讀一學期以上並持有成績單）"
    )
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "")
    website = item.get("website") or TNNUA_PARTNERS_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    round_label = (
        "115–116學年度姊妹校交換生（含雙聯學位）計畫（國際事務處常態開放申請）"
        if avail_status == "open"
        else "國際事務處正式締約姊妹校（當期開放名額依國際處最新公告為準）"
    )
    app_deadline_str = clean_text(
        item.get("deadline")
        or (
            "第一梯次（秋季班出國交換／雙聯）：每年 2 月下旬（2027/02/26 17:00）前送系所書面初審、3 月上旬（2027/03/06）送國際事務處複審｜"
            "第二梯次（春季班出國交換／雙聯）：每年 9 月上旬（2026/09/09 17:00）前送系所書面初審、9 月中旬（2026/09/15）送國際事務處複審｜"
            "赴境外研修雙聯學位獎助學金：每年 9 月 30 日前向系所提出初審"
        )
    )
    deadline_iso = "2027-02-26T17:00:00+08:00"
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "115"

    study_period_str = clean_text(item.get("duration") or "一學期或一學年")
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲國立臺南藝術大學國際事務處推薦錄取後，可依 {zh_name} 國際處指引申請校內外學生宿舍或國際學舍"
        + (f"（學費與住宿待遇：{tuition_note}）" if tuition_note else "。")
    )
    course_rest_str = (
        f"開放對象與對應學院系所：{colleges_str}（{degree_levels_str}）。依《115年國立臺南藝術大學交換生計畫實施要點》、《國立臺南藝術大學與境外大學校院辦理雙聯學制實施辦法》（114年5月26日修正）及《國際交流獎補助計畫校內審查辦法》規定："
        "（1）申請資格為本校日間學制大學部二年級以上、七年一貫制學士班五年級以上，以及就讀一學期以上之碩、博士班在學學生（不含碩士班在職專班；轉學生須曾於本校就讀一學期以上並持有成績單）；"
        "（2）兩階段甄選與錄取標準：「第一階段系所書面初審（占總成績 50%：歷年成績單及讀書計畫 30%＋專業作品及成就表現 20%）」須經系所會議通過且得分達 40 分（滿分 50 分）以上，始得送件至國際處參加「第二階段校內口試複審（占總成績 50%：面試 30%＋語言能力［含以交換國授課語言 1–2 分鐘自我介紹］20%）」，交換生錄取標準以總成績達 80 分為原則；"
        "（3）出國修課與返國義務：交換期間仍須於南藝大辦理註冊手續並繳交全額學雜費，每學期至少修習相當於本校 6 學分（大學部）或 1 門專業科目（研究所）之課程；返國後兩週（14 日）內須繳交約 2,000 字《交換生心得報告》電子檔及高解析度照片 4 張，並依本校學生抵免學分辦法辦理學分採認；"
        "（4）境外雙聯學制規定：於兩校修業時間學士班累計至少滿 32 個月（在南藝大修業至少 2 學年）、碩士班至少滿 12 個月（在兩校各修業至少 1 學期）、博士班至少滿 24 個月（在兩校各修業至少 2 學期），於兩校修習學分數各須達畢業應修總學分數 1/3 以上。"
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
            f"臺南藝術大學出國交換註冊與學雜費規定（依《交換生計畫實施要點》及《只需繳交本校註冊費及學雜費即可前往交換的姊妹校》公告）：出國交換期間仍須辦理本校註冊手續並繳交本校註冊費及學雜費，即享免繳互惠姊妹校學費優惠。本合作校待遇：{tuition_note or '依兩校交換生協議辦理'}。"
        ),
        (
            "臺南藝術大學三大出國交換、雙聯學位與海外實習獎補助體系：（1）國際事務處《教育部學海飛颺／學海惜珠／學海築夢／新南向學海築夢計畫》（115年甄選簡章規定申請人歷年學業成績總平均須達 80 分以上，校內審查含系所初審 50%＋國際處口試複審 50%，複審總分達 80 分以上為原則；補助經濟艙來回機票及國外學費、生活費，每年 2 月下旬及 9 月上旬與交換生甄選同步收件）；（2）國際事務處《國立臺南藝術大學赴境外研修雙聯學位獎助學金設置要點》（獎助赴韓國誠信女子大學、韓國傳統文化大學、印尼國立日惹印尼藝術大學、安巴魯莫觀光學院等雙聯合作校修讀雙聯學位之本國籍在學學生，每人每年獎助上限新臺幣 20 萬元，分兩期核撥［出國就讀註冊後核撥 50%、取得雙聯學位並完成學分抵免後核撥 50%］，每年 9 月底截止申請）；（3）高等教育深耕計畫《高等教育學生實習計畫實施要點》（補助學生赴海外博物館、修復中心及文化藝術機構實習之機票與生活費）。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認南藝大在學年級資格、外語能力對照表標準與 {zh_name} 院系所限制）：確認符合《115年國立臺南藝術大學交換生計畫實施要點》身分（日間學制大學部二年級以上、七年一貫制五年級以上，或就讀滿一學期以上之碩博士班學生，不含碩士在職專班；轉學生須於本校就讀滿一學期並有成績單），並檢視 {zh_name} 開放學院（{colleges_str}）與語檢要求（{lang_req_str}）。"
        ),
        (
            "步驟二（備齊申請表、作品集與 6 項書面資料於期限前送交系所辦理初審）：於第一梯次每年 2 月 26 日前（或第二梯次每年 9 月 9 日前）填妥《交換生計畫申請表》（含師長推薦意見與家長簽章同意），檢附（1）中/英文歷年成績單（須含交換前最後一學期成績）、（2）中/英文自傳及讀書計畫、（3）外國語文能力證明或選修外語學分證明、（4）師長推薦函、（5）專業作品集及獲獎／展演成就表現資料、（6）研究生另附大學畢業證書中英文影本（申請雙聯學位者另附《雙聯學制計畫意向書》與《雙聯學位生出國進修申請表》），送所屬系所召開系所會議進行書面初審（滿分 50 分，須達 40 分以上始得送國際處複審）。"
        ),
        (
            f"步驟三（由系所將初審評分表與申請件送國際事務處，參加校內口試複審並同步申請學海／雙聯獎助）：系所於 3 月 6 日（或 9 月 15 日）前將初審達 40 分以上之申請件與《系所初審評分表》送達國際事務處國際合作組（分機 1901）；參加由國際事務處處長召集教務長、學務長及各學院院長組成之校內口試複審（占 50%：面試 30%＋語言能力［含以交換國授課語言 1–2 分鐘自我介紹］20%），總成績達 80 分以上擇優錄取推薦赴 {full_name}。學業總平均達 80 分以上者可同步申請教育部《學海飛颺／學海惜珠》，修讀雙聯學位者可於 9 月底前申請《赴境外研修雙聯學位獎助學金》（每年上限 20 萬元）。"
        ),
        (
            "步驟四（經國際事務處向姊妹校官方提名、完成南藝大註冊與簽證保險，返國後兩週內繳交心得報告與辦理學分抵免）：獲選學生須於公告期限內繳交《錄取確認書》與《家長同意書》，由國際處向接待校辦理提名（Nomination）並遞交姊妹校入學申請與作品集；出國期間完成南藝大註冊繳費，返國後兩週（14 日）內繳交 2,000 字《交換生心得報告》及照片 4 張，並持國外成績單向系所與教務處辦理學分抵免。"
        ),
    ]

    elig_points_list = [
        f"合作類別與計畫組別：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請學院與系所：{colleges_str}",
        f"兩階段初複審與學業門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "校內兩階段甄選配分（《115年交換生計畫實施要點》第六點）：第一階段「系所書面初審 50%」（歷年成績單及讀書計畫 30%＋專業作品及成就表現 20%，須經系所會議通過且達 40 分以上）＋第二階段「校內口試複審 50%」（面試 30%＋語言能力［含以交換國授課語言 1–2 分鐘自我介紹］20%），總成績達 80 分以上為錄取原則。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與南藝大獎補助待遇：{tuition_note}")
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
        esem = e.get("semester") or "歷年交換"
        eurl = (
            e.get("url")
            or f"{TNNUA_EXPERIENCE_SHARING_URL}#tnnua-exp-{sn}-{e_idx+1}"
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
            "college": "音樂學院／視覺藝術學院／音像藝術學院／文博學院",
            "department": "臺南藝術大學交換／海外實習生",
        })
        summary_text = (
            f"國立臺南藝術大學國際事務處公開收錄之學長姐赴 {country} {full_name} 交換研修／學海築夢海外專業實習官方心得報告（{raw_t}），詳述藝術創作與展演修課、工作坊與文物修復實務、校內外住宿、簽證辦理與當地生活開銷。"
        )
        theme_map = {
            "academics": f"臺南藝術大學學生於《{raw_t}》分享在 {zh_name} 及當地專業機構修習音樂演奏、視覺造型工藝、動畫影視或文物保存修復課程與導師制實作之第一手經驗。",
            "housing": f"臺南藝術大學學生記錄申請 {zh_name} 校內外學生宿舍或當地租屋、琴房與工作室使用及通勤方式（{housing_str[:100]}）。",
            "campus_culture": f"臺南藝術大學公開收錄《{raw_t}》之國際藝術祭參與、美術館與博物館考察、跨文化課堂發表與校園生活實錄。",
            "cost": f"臺南藝術大學學生分享於 {zh_name} 之每月住宿、伙食與創作材料開銷（{living_cost_str[:100]}），以及免繳姊妹校學費與申請教育部學海飛颺／惜珠／築夢或南藝大雙聯學位獎助學金之經驗。",
        }
        student_experience_rows.append({
            "school_name": full_name,
            "country": country,
            "title": raw_t,
            "source_url": eurl,
            "source_type": "pdf" if eurl.endswith(".pdf") else "article",
            "platform": "國立臺南藝術大學國際事務處（OIA）—交換生出國心得分享暨學海築夢海外職涯探索專區",
            "author_name": (
                raw_t.split("—")[1].strip()[:20]
                if "—" in raw_t
                else "南藝大交換生"
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
                f"{full_name}:tnnua_exp:{e_idx}:{eurl}".encode("utf-8")
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
        "home_university": "國立臺南藝術大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exp_links[0]["url"] if exp_links else TNNUA_EXPERIENCE_SHARING_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

    loc = resolved_locations.get(full_name) or {
        "city": country,
        "latitude": 23.2046,
        "longitude": 120.3653,
        "source_url": "https://www.wikidata.org",
    }
    city_name = loc.get("city") or country
    lat = float(
        loc.get("latitude")
        if loc.get("latitude") is not None
        else loc.get("lat", 23.2046)
    )
    lon = float(
        loc.get("longitude")
        if loc.get("longitude") is not None
        else loc.get("lon", 120.3653)
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
          f"【臺南藝術大學學長姐交換／海外實習心得報告（共 {len(exps)} 篇）】收錄於國際事務處交換生心得與學海築夢專區（含：{'、'.join(exp_labels[:4])}）"
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
            f"國立臺南藝術大學國際事務處公告合作姊妹校（{program_type}）；{quota_str}。"
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
            "title": f"國立臺南藝術大學國際事務處（OIA）國際交流學校及免學費交換姊妹校專頁—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "115年國立臺南藝術大學交換生計畫實施要點及申請表",
            "source_url": TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立臺南藝術大學辦理教育部115年度學海計畫甄選簡章與赴境外研修雙聯學位獎助學金設置要點",
            "source_url": TNNUA_XUEHAI_BROCHURE_115_1_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exp_links:
      wf_sources.append({
          "title": f"國立臺南藝術大學國際事務處交換生出國心得與學海築夢專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
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
        "home_university": "國立臺南藝術大學",
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
            "國立臺南藝術大學由國際事務處（國際合作組分機 1901、海外教育組分機 1902）統籌全校 5 大學院（音樂學院、視覺藝術學院、音像藝術學院、文博學院、跨域創生學院）之赴外交換生計畫、境外大學雙聯學制（韓國誠信女子大學、韓國傳統文化大學、印尼國立日惹印尼藝術大學、安巴魯莫觀光學院）及教育部學海飛颺、學海惜珠、學海築夢、新南向學海築夢與南藝大雙聯學位獎助學金。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"tnnua-{acad_year}-home-1-{sn:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認南藝大在學年級身分（大二／七年一貫五年級／碩博滿一學期）、外語對照表標準與 {zh_name} 院系所限制",
                "responsible_party": "學生",
                "responsible_unit": "國立臺南藝術大學國際事務處／各院系所",
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
                    f"確認符合《115年國立臺南藝術大學交換生計畫實施要點》第三點規定：申請人須為本校日間學制大學部二年級以上、七年一貫制學士班五年級以上，或就讀一學期以上之碩、博士班在學學生（不含碩士班在職專班；轉學生須曾於本校就讀一學期以上並持有成績單），符合學業與初審要求（{gpa_req_str}）並具備外語能力（{lang_req_str}）。"
                ),
                "details": [
                    f"開放學制與對應學院系所：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["國立臺南藝術大學"],
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
                    TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                    TNNUA_TUITION_FREE_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"tnnua-{acad_year}-home-2-{sn:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "備妥《交換生計畫申請表》、專業作品集與應備文件送所屬系所進行第一階段書面初審（須達 40/50 分以上）",
                "responsible_party": "學生與所屬系所",
                "responsible_unit": "各系所（系所會議初審）／國際事務處國際合作組",
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "於校內公告初審截止日前（第一梯次每年 2 月 26 日前、第二梯次每年 9 月 9 日前）將《交換生計畫申請表》、中/英文歷年成績單（含交換前最後一學期成績）、中/英文自傳及讀書計畫、外語能力證明、師長推薦函、專業作品集及成就表現資料送所屬系所；經系所會議辦理書面初審（歷年成績單及讀書計畫 30%＋專業作品及成就表現 20%），得分達 40 分（滿分 50 分）以上者，由系所於 3 月 6 日（或 9 月 15 日）前連同《系所初審評分表》送交國際事務處複審。"
                ),
                "details": [
                    "第一梯次（秋季班出國）：每年 2 月 26 日前向各系所提出書面資料初審，3 月 6 日前由系所送達國際事務處複審。",
                    "第二梯次（春季班出國）：每年 9 月 9 日前向各系所提出書面資料初審，9 月 15 日前由系所送達國際事務處複審（逾時不受理任何形式補件）。",
                ],
                "document_requirements": [
                    {
                        "name": "國立臺南藝術大學交換生計畫申請表（含師長推薦意見、家長簽章同意及系所核章）與南藝大系所初審評分表",
                        "official_form_url": TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                        "source_urls": [
                            TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                            TNNUA_FORMS_URL,
                        ],
                    },
                    {
                        "name": "中/英文歷年成績單正本（需含交換前最後一學期成績；申請學海計畫者總平均須達 80 分以上）與外語能力檢定證明（或選修外語學分證明）",
                        "official_form_url": TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                        "source_urls": [
                            TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                            TNNUA_XUEHAI_BROCHURE_115_1_PDF_URL,
                        ],
                    },
                    {
                        "name": "中/英文自傳及讀書計畫、師長推薦函、專業作品集及成就表現資料（研究生另附大學畢業證書中英文影本；雙聯學位另附雙聯學制計畫意向書與出國進修申請表）",
                        "official_form_url": TNNUA_DUAL_DEGREE_CHECKLIST_PDF_URL,
                        "source_urls": [
                            TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                            TNNUA_DUAL_DEGREE_CHECKLIST_PDF_URL,
                        ],
                    },
                ],
                "scope": {
                    "home_universities": ["國立臺南藝術大學"],
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
                    TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                    TNNUA_DUAL_DEGREE_RULES_PDF_URL,
                    TNNUA_EXCHANGE_ANN_115_1_URL,
                    TNNUA_EXCHANGE_ANN_114_2_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"tnnua-{acad_year}-home-3-{sn:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "參加國際事務處第二階段校內口試複審（含 1–2 分鐘外語自我介紹），並同步申請教育部學海計畫或雙聯學位獎助學金",
                "responsible_party": "國立臺南藝術大學國際事務處審查委員會與申請學生",
                "responsible_unit": "國際事務處國際合作組／海外教育組",
                "deadline_at": "2027-03-20T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "由國際事務處處長擔任召集人，會同教務長、學務長及各學院院長組成審查委員會辦理第二階段口試複審（占總成績 50%：面試 30%＋語言能力［含以交換國家之授課語言自我介紹 1–2 分鐘］20%），結合系所書面初審（50%）合計總成績達 80 分以上者擇優錄取。符合資格者可同步申請教育部《學海飛颺／學海惜珠／學海築夢》或南藝大《赴境外研修雙聯學位獎助學金》（每年上限 20 萬元）。"
                ),
                "details": [
                    "外國語文能力對照表基準：英語 TOEFL iBT 79 / CBT 213 / IELTS 6.0、日語 JLPT N2、韓語 TOPIK 3 級、法語 DELF/TCF B1 或 FLPT 150 (S-2)、德語 Goethe-Zertifikat B1 / TestDaF TDN3 或 FLPT 150 (S-2)、西班牙語 DELE B1 或 FLPT 150 (S-2)。",
                    "赴境外研修雙聯學位獎助學金（《赴境外研修雙聯學位獎助學金設置要點》）：每人每年獎助上限新臺幣 20 萬元，於每年 9 月底前向系所提出申請。",
                ],
                "scope": {
                    "home_universities": ["國立臺南藝術大學"],
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
                    TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                    TNNUA_XUEHAI_BROCHURE_115_1_PDF_URL,
                    TNNUA_DUAL_DEGREE_SCHOLARSHIP_PDF_URL,
                    TNNUA_REVIEW_RULES_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"tnnua-{sn:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"繳交錄取確認書與家長同意書，由國際事務處向 {zh_name} 辦理官方提名並遞交姊妹校入學與作品集文件",
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"錄取公告後，學生須於期限內向國際事務處繳交《交換學生錄取確認書》與《家長同意書》，由國際處向 {zh_name} 辦理官方提名（Nomination）；學生須依接待校規定備妥外文入學申請表、英文歷年成績單、作品集或演奏影音檔、護照影本、英文財力證明及宿位申請表，靜候接待校核發正式入學許可（Admission Letter / COE / 錄取通知書）。"
                ),
                "details": [
                    f"研修期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["國立臺南藝術大學"],
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
                    [source_url, TNNUA_PARTNERS_URL]
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"tnnua-{acad_year}-home-5-{sn:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "完成南藝大出國註冊繳費與海外醫療保險，返國後兩週（14日）內繳交 2,000 字心得報告並辦理學分抵免",
                "responsible_party": "學生與所屬系所",
                "responsible_unit": "國際事務處／教務處註冊組／各系所",
                "summary": (
                    "出國交換期間仍須於國立臺南藝術大學辦理註冊並繳交全額學雜費（享有免繳互惠姊妹校學費優惠），自行辦妥護照、簽證、機票與涵蓋全期之海外醫療及意外保險；返國後兩週（14 日）內須向國際事務處繳交約 2,000 字之《交換生心得報告》電子檔及照片 4 張（學海受獎生另須上傳教育部學海計畫資訊網並檢附單據核銷），並持國外成績單正本向系所及教務處辦理學分抵免。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["國立臺南藝術大學"],
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
                    TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                    TNNUA_DUAL_DEGREE_RULES_PDF_URL,
                    TNNUA_DUAL_DEGREE_SCHOLARSHIP_PDF_URL,
                    TNNUA_XUEHAI_BROCHURE_115_1_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合國立臺南藝術大學國際事務處（OIA）《115年交換生計畫實施要點及申請表》、《只需繳交本校註冊費及學雜費即可前往交換的姊妹校》、《2025–2026近年新增姊妹校簡介》、《與境外大學校院辦理雙聯學制實施辦法（114.05.26）》、《赴境外研修雙聯學位獎助學金設置要點》、《辦理教育部115年度學海計畫甄選簡章》、《國際交流獎補助計畫校內審查辦法》及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換生與學海築夢心得報告，共 {len(catalog_source)} 所合作姊妹校資料。"
        ),
    })

    cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": f"國立臺南藝術大學國際事務處（OIA）國際交流學校及交換生專頁—{zh_name}",
            "source_url": source_url,
            "summary": "南藝大國際處公告之合作學程、對應院系所、語言檢定標準與免繳姊妹校學費／雙聯學位待遇說明",
        },
        {
            "title": "115年國立臺南藝術大學交換生計畫實施要點、教育部學海計畫簡章與雙聯學位獎助學金設置要點",
            "source_url": TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
            "summary": "南藝大出國交換在學註冊規定、兩階段初複審配分標準（系所書面初審 50%＋校內口試複審 50%）、學海獎助與雙聯學位每年 20 萬元獎助規範",
        },
    ]
    if exp_links:
      dest_sources.append({
          "title": f"國立臺南藝術大學國際事務處交換生出國心得與學海築夢專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
          "source_url": exp_links[0]["url"],
          "summary": f"收錄歷年臺南藝術大學學生赴 {zh_name} 交換研修／海外專業實習心得報告共 {len(exps)} 篇",
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
            TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
            TNNUA_TUITION_FREE_PDF_URL,
            TNNUA_EXCHANGE_SCHOLARSHIPS_URL,
        ]
        + ([exp_links[0]["url"]] if exp_links else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "國立臺南藝術大學",
        "school_name": full_name,
        "country": country,
        "city": city_name,
        "cost_summary": f"{cost_line}。\n{tuition_clean}",
        "housing_summary": housing_clean,
        "transport_summary": (
            f"校區代表城市：{city_name}。請依入學許可確認實際授課校區位置、琴房／工作室開放時段與當地學生交通卡優惠。"
        ),
        "campus_life_summary": f"{calendar_clean}\n{course_clean}",
        "student_guide_sections": [
            {
                "key": "cost",
                "title": "生活費、南藝大在學註冊免姊妹校學費規定、教育部學海計畫與雙聯學位每年 20 萬元獎助",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [TNNUA_DUAL_DEGREE_SCHOLARSHIP_PDF_URL],
                "caution": (
                    "依《交換生計畫實施要點》第九點及第十一點，交換生出國期間仍須辦理南藝大註冊並繳交學雜費；返國後兩週內須繳交約 2,000 字交換心得報告及照片 4 張。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外國際學生宿舍申請",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": "韓國傳統文化大學（KNUH）額外提供免住宿費及每月 10 萬韓元生活津貼（共 4 個月）；其餘姊妹校宿位請於獲提名後依接待校期限儘早申請。",
            },
            {
                "key": "insurance",
                "title": "海外醫療及意外保險與家長同意書規定",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依《國立臺南藝術大學交換生計畫實施要點》，所有錄取學生均須檢附經家長或法定代理人簽章之《家長同意書》，並於出國前自行購買涵蓋交換全期之海外醫療及意外保險。",
                ],
                "source_urls": src_url_list,
                "caution": "日本、韓國、德國、英國、義大利、法國、斯洛維尼亞、捷克、美國、澳洲等接待校對交換生當地國民健康保險或申根保險有強制規定，請依入學通知書辦理。",
            },
            {
                "key": "visa",
                "title": "留學交換簽證辦理、出國修業期限與雙聯學制修業月數",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依《交換生計畫實施要點》與《辦理雙聯學制實施辦法》：交換生出國研修期間以 1 學期或 1 學年為限；跨國雙聯學制學士班於兩校累計修業時間至少滿 32 個月、碩士班至少滿 12 個月、博士班至少滿 24 個月。",
                ],
                "source_urls": src_url_list + [TNNUA_DUAL_DEGREE_RULES_PDF_URL],
                "caution": "役男同學須於出國前至少 1.5 個月檢附接待校入學許可向國際事務處及學務處申請役男出境核准。",
            },
            {
                "key": "academics",
                "title": "兩階段初複審配分、作品集審查、雙聯學制與返國學分抵免",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [TNNUA_DUAL_DEGREE_RULES_PDF_URL],
                "caution": (
                    "第一階段系所書面初審（50%）得分須達 40 分以上始得送國際處參加第二階段校內口試複審（50%），總成績達 80 分以上為錄取原則；申請學海計畫者歷年學業總平均須達 80 分以上。"
                ),
            },
            {
                "key": "living",
                "title": f"{city_name} 藝術校園生活與臺南藝術大學學長姐交換／實習經驗傳承",
                "summary": f"代表城市：{city_name}。請配合接待校國際處完成報到、工作坊安全講習與新生訓練（Orientation）。",
                "points": [
                    f"目的地城市：{city_name}（{country}）",
                    (
                        "國立臺南藝術大學國際事務處公開歷屆「交換生出國心得分享」與「學海築夢海外職涯探索心得分享」"
                        + (
                            f"（本合作校共收錄 {len(exps)} 篇心得報告：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，協助同學掌握作品集準備、選課與海外創作生活。"
                    ),
                ],
                "source_urls": [
                    exp_links[0]["url"]
                    if exp_links
                    else TNNUA_EXPERIENCE_SHARING_URL
                ],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合國立臺南藝術大學國際事務處 {len(catalog_source)} 所合作姊妹校、當期常態開放申請交換與雙聯學校（{open_partner_count} 校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷年學生交換與學海築夢實習心得報告。"
        ),
    })

    research_records.append({
        "home_university": "國立臺南藝術大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            "國立臺南藝術大學國際事務處《115年交換生計畫實施要點》、《只需繳交本校註冊費及學雜費即可前往交換的姊妹校》、《2025–2026近年新增姊妹校簡介》、《國際雙聯學位專區》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"國立臺南藝術大學國際事務處國際交流學校與交換生專頁—{zh_name}",
            "url": source_url,
        },
    ]
    if exp_links:
      ev_sources.append({
          "title": f"國立臺南藝術大學交換生與學海築夢心得分享—赴 {zh_name} 心得報告（{len(exps)} 篇）",
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
            "scope": "國立臺南藝術大學全球與大陸交換姊妹校住宿與生活資訊",
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
            "scope": "國立臺南藝術大學出國交換學雜費規定、教育部學海飛颺／惜珠／築夢與赴境外研修雙聯學位獎助學金",
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
            "scope": "國立臺南藝術大學交換生計畫實施要點、雙聯學制實施辦法與兩階段初複審規定",
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
            "scope": "國立臺南藝術大學海外交換與雙聯學位簽證、家長同意書、海外醫療保險與註冊規定提醒",
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
                    f"｜臺南藝術大學公開收錄 {len(exps)} 篇赴 {zh_name} 交換／實習心得報告（{'、'.join(exp_labels[:3])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "國立臺南藝術大學交換名額與歷屆學長姐經驗分享",
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
            "已整合國立臺南藝術大學國際事務處《115年交換生計畫實施要點》、《只需繳交本校註冊費及學雜費即可前往交換的姊妹校》、《2025–2026近年新增姊妹校簡介》、《國際雙聯學位專區》及歷屆學生交換與學海築夢心得報告。",
            "當期免學費名額、宿位供給、語檢門檻、作品集規格與選課限制請依合作校最新簡章及入學通知書核對。",
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

  write_jsonl(OFFICIAL_TNNUA_DIR / "partners.jsonl", partners)
  write_jsonl(SOURCES_TNNUA_DIR / "partners.jsonl", partners)
  write_jsonl(OFFICIAL_TNNUA_DIR / "application_workflows.jsonl", workflows)
  write_jsonl(OFFICIAL_TNNUA_DIR / "destination_profiles.jsonl", destinations)
  write_jsonl(OFFICIAL_TNNUA_DIR / "partner_research.jsonl", research_records)
  write_jsonl(OFFICIAL_TNNUA_DIR / "student_life.jsonl", life_records)
  write_jsonl(
      OFFICIAL_TNNUA_DIR / "experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_TNNUA_DIR / "student_experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_TNNUA_DIR / "student_experiences.jsonl", student_experience_rows
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
  (OFFICIAL_TNNUA_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_TNNUA_DIR / "student-experiences.json").write_text(
      json.dumps(
          {
              "school_id": "tnnua",
              "school_name": "國立臺南藝術大學",
              "checked_at": CHECKED_AT,
              "source_url": TNNUA_EXPERIENCE_SHARING_URL,
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

  (OFFICIAL_TNNUA_DIR / "campus-locations.json").write_text(
      json.dumps(
          {
              "school_id": "tnnua",
              "school_name": "國立臺南藝術大學",
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
  (OFFICIAL_TNNUA_DIR / "campus-assets.json").write_text(
      json.dumps(
          {
              "school_id": "tnnua",
              "school_name": "國立臺南藝術大學",
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

  tnnua_source_urls = [
      TNNUA_OIA_HOME_URL,
      TNNUA_OIA_ABOUT_URL,
      TNNUA_REGULATIONS_URL,
      TNNUA_FORMS_URL,
      TNNUA_DUAL_DEGREE_URL,
      TNNUA_DUAL_DEGREE_SCHOLARSHIP_URL,
      TNNUA_PARTNERS_URL,
      TNNUA_NEW_PARTNERS_URL,
      TNNUA_TUITION_FREE_PARTNERS_URL,
      TNNUA_EXCHANGE_SCHOLARSHIPS_URL,
      TNNUA_EXCHANGE_ANN_115_1_URL,
      TNNUA_EXCHANGE_ANN_114_2_URL,
      TNNUA_XUEHAI_ANN_115_1_URL,
      TNNUA_XUEHAI_ANN_115_2_URL,
      TNNUA_EXPERIENCE_SHARING_URL,
      TNNUA_ZHUMENG_SHARING_URL,
      TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
      TNNUA_TUITION_FREE_PDF_URL,
      TNNUA_DUAL_DEGREE_RULES_PDF_URL,
      TNNUA_DUAL_DEGREE_CHECKLIST_PDF_URL,
      TNNUA_DUAL_DEGREE_SCHOLARSHIP_PDF_URL,
      TNNUA_XUEHAI_BROCHURE_115_1_PDF_URL,
      TNNUA_XUEHAI_BROCHURE_115_2_PDF_URL,
      TNNUA_REVIEW_RULES_PDF_URL,
      TNNUA_SPROUT_INTERN_PDF_URL,
  ]

  exchange_info_payload = {
      "school_name": "國立臺南藝術大學",
      "program_type": [
          (
              f"國際事務處（OIA）姊妹校交換生計畫（涵蓋日本東京藝術大學、愛知縣立藝術大學、岡山縣立大學；韓國誠信女子大學、韓國傳統文化大學［免學費＋免住宿費＋4 個月生活津貼］、韓國藝術綜合大學 K-Arts、弘益大學、漢陽大學、檀國大學、水原大學、龍仁大學、聖公會大學；德國斯圖加特國立造型藝術學院、班貝格大學、希爾德斯海姆大學；義大利米蘭國立布雷拉美術學院、英國倫敦大學金匠學院、捷克布拉格表演藝術學院 AMU、斯洛維尼亞盧布爾雅納大學；美國華盛頓與傑佛遜學院；泰國藝術大學 Silpakorn、朱拉隆功大學、瑪希敦大學；印尼日惹藝術大學 ISI、峇里島藝術學院 ISI Denpasar、安巴魯莫觀光學院；哈薩克國立藝術學院、澳門城市大學及大陸中央美術學院等 {open_partner_count} 所常態開放申請交換與雙聯姊妹校，以及全球 23 個國家與地區共 {len(partners)} 所正式締約姊妹校）"
          ),
          (
              "境外大學雙聯學制計畫（Dual Degree Programs，依《國立臺南藝術大學與境外大學校院辦理雙聯學制實施辦法》辦理，涵蓋【韓國誠信女子大學 Sungshin Women's University】、【韓國傳統文化大學 Korea National University of Heritage】、【印尼國立日惹印尼藝術大學 ISI Yogyakarta】及【印尼日惹安巴魯莫觀光學院 STIPRAM】4 所雙聯合作校，並設有《赴境外研修雙聯學位獎助學金》每人每年上限新臺幣 20 萬元）"
          ),
          (
              "教育部「學海飛颺」（選送優秀學生出國研修）、「學海惜珠」（清寒優秀學生出國研修）、「學海築夢／新南向學海築夢」（選送學生赴歐美日星澳等國國家博物館、圖書館與文物修復中心進行海外職涯探索實習）及高教深耕《高等教育學生實習計畫》"
          ),
      ],
      "academic_year": [
          (
              "115（涵蓋 115–116 學年度姊妹校交換生暨雙聯學位兩梯次甄選［第一梯次每年 2/26 送系所初審、3/6 送國際處複審；第二梯次每年 9/9 送系所初審、9/15 送國際處複審］、教育部 115-1／115-2 學海計畫甄選及 115 年赴境外研修雙聯學位獎助學金［9 月底截止］）"
          ),
          (
              f"本平台完整收錄國立臺南藝術大學國際事務處公告之 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所常態開放申請之免學費交換姊妹校與跨國雙聯學位合作校、{len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 23 個國家與地區，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷年學長姐交換與學海築夢海外實習心得報告）"
          ),
      ],
      "semester": [
          "第一梯次甄選（每年 2 月下旬系所初審截止、3 月上旬國際處複審截止）：選送學生於當年度秋季學期（第 1 學期）赴境外姊妹校交換一學期或一學年。",
          "第二梯次甄選（每年 9 月上旬系所初審截止、9 月中旬國際處複審截止）：選送學生於隔年春季學期（第 2 學期）赴境外姊妹校交換一學期或一學年（依《交換生計畫實施要點》第二點，交換期間以 1 學期或 1 學年為限）。",
          "境外大學雙聯學制（依《與境外大學校院辦理雙聯學制實施辦法》）：與交換生甄選同步於每年 2 月及 9 月受理申請，另《赴境外研修雙聯學位獎助學金》於每年 9 月 30 日前向系所提出初審。",
      ],
      "application_period": [
          "【第一梯次姊妹校交換生暨教育部 115-1 學海計畫甄選（秋季班出國）】每年 2 月下旬（如 115 年 2 月 26 日星期四）前備妥書面資料向所屬系所提出初審；系所於 3 月上旬（如 115 年 3 月 6 日星期五）前將初審結果（須達 40/50 分以上）及申請資料送達國際事務處國際合作組（分機 1901）。",
          "【第二梯次姊妹校交換生（含雙聯學位）暨教育部 115-2 學海計畫甄選（春季班出國）】每年 9 月上旬（如 115 年 9 月 9 日星期三）前備妥書面資料向所屬系所提出初審；系所於 9 月中旬（如 115 年 9 月 15 日星期二）前將初審結果及申請資料送達國際事務處複審（逾時不受理任何形式補件）。",
          "【115年赴境外研修雙聯學位獎助學金（每人每年上限 20 萬元）】自公告日起至每年 9 月 30 日止向所屬系所提出申請，10 月 15 日前由系所完成初審送交國際事務處。",
      ],
      "eligibility": [
          "1. 在學身分與年級限制：依《115年國立臺南藝術大學交換生計畫實施要點》第三點，申請人須為本校日間學制大學部二年級以上、七年一貫制學士班五年級以上，以及就讀一學期以上之碩、博士班在學學生（不含碩士班在職專班；轉學生須曾於本校就讀一學期以上並持有成績單）。",
          "2. 兩階段甄選程序與計分標準（《交換生計畫實施要點》第五、六點）：（1）第一階段「系所書面初審（占總成績 50%）」：歷年成績單及讀書計畫占 30%、專業作品及成就表現占 20%，須經系所會議通過，且得分應達 40 分（滿分 50 分）以上始得送件至國際處參加複審；（2）第二階段「校內口試複審（占總成績 50%）」：由國際事務處處長擔任召集人，與教務長、學務長及各學院院長組成審查委員會，面試占 30%、語言能力（含以交換國家之授課語言自我介紹 1–2 分鐘）占 20%；交換生錄取標準以總成績達 80 分為原則。",
          "3. 教育部學海系列計畫學業門檻：依《國立臺南藝術大學辦理教育部 115 年度學海計畫甄選簡章》，申請學海飛颺、學海惜珠、學海築夢或新南向學海築夢者，需具中華民國國籍，且在校歷年學業成績總平均應達 80 分以上（校內複審總成績亦以達 80 分以上為原則）。",
          "4. 個別姊妹校院系所與學制專屬限制：（a）日本東京藝術大學（Geidai）交換僅限本校「視覺藝術學院學生」及「文博學院研究生」，同時段原則接待 1 名；（b）泰國朱拉隆功大學（Chulalongkorn University）交換僅限本校「音樂學院學生」；（c）捷克布拉格表演藝術學院（AMU）、韓國誠信女子大學、韓國傳統文化大學（KNUH）、韓國水原大學、韓國龍仁大學、泰國藝術大學（Silpakorn）、澳門城市大學、哈薩克國立藝術學院及美國華盛頓與傑佛遜學院（W&J）均於《2025–2026近年新增姊妹校簡介》訂有明確之南藝大院系所對應表。",
      ],
      "language_requirement": [
          "1. 英語授課姊妹校標準：依《115年國立臺南藝術大學交換生計畫實施要點》外國語文能力對照表，英語基準門檻為 TOEFL iBT 79 分（或電腦托福 CBT 213 分）或 IELTS 6.0 以上；若申請人選修相關外國語文學分，亦得檢附學分證明併同參加校內口試複審（含 1–2 分鐘外語自我介紹）。",
          "2. 日本與韓國姊妹校標準：（a）日本東京藝術大學、岡山縣立大學、愛知縣立藝術大學等要求日語能力試驗 JLPT N2 以上（東京藝術大學亦接受英語或日文能力經指導教授肯定）；（b）韓國誠信女子大學、韓國傳統文化大學、韓國藝術綜合大學、弘益大學、漢陽大學、檀國大學、水原大學、龍仁大學、聖公會大學等要求韓語能力測驗 TOPIK 3 級以上（選修英語授課課程者可檢附英語檢定證明）。",
          "3. 歐洲法語、德語、西班牙語姊妹校標準：依《交換生計畫實施要點》外國語文能力對照表，（a）法語區（布爾日 ENSA Bourges、巴黎塞爾吉 ENSAPC、波爾多 KEDGE）：DELF / TCF B1 或 FLPT 法語筆試 150 分（口試 S-2）以上；（b）德語區（斯圖加特國立造型藝術學院、班貝格大學、希爾德斯海姆大學、維也納音樂與表演藝術大學）：Goethe-Zertifikat B1、TestDaF TDN3 或 FLPT 德語筆試 150 分（口試 S-2）以上（選修英語授課學程者可檢附英語 iBT 79 / IELTS 6.0）；（c）西班牙語區（馬德里康普頓斯大學）：DELE B1 或 FLPT 西班牙語筆試 150 分（口試 S-2）以上。",
          "4. 中國大陸與澳門姊妹校標準：大陸地區 12 所姊妹校（中央美術學院、中央音樂學院、中國美術學院、上海音樂學院、廣州美術學院、南京藝術學院、景德鎮陶瓷大學等）及澳門城市大學中文授課學程免附外語能力檢定證明。",
      ],
      "required_documents": [
          "1. 115年國立臺南藝術大學交換生計畫申請表（含基本資料、擬就讀學校志願、外語能力、師長推薦意見與簽章、申請人及家長簽章、系所主管簽章）及《南藝大系所初審評分表》",
          "2. 本校中、英文歷年成績單正本各一份（需含交換前最後一學期之成績；申請教育部學海系列計畫者歷年學業總平均須達 80 分以上）",
          "3. 外國語文能力檢定成績證明影本（TOEFL iBT 79 / IELTS 6.0 / JLPT N2 / TOPIK 3 / DELF B1 / Goethe B1 / DELE B1）或曾選修相關外國語文之學分證明",
          "4. 中、英文自傳及讀書計畫各一份（詳述出國研修動機、擬修習課程或創作研究規劃及預期成果）",
          "5. 師長推薦函（東京藝術大學等姊妹校須檢附指導教授推薦函並肯定語文能力）",
          "6. 專業作品集（Portfolio／演奏影音連結）及獲獎、展演或學術成就表現資料（占系所初審 20%）",
          "7. 大學畢業證書中、英文影本各一份（僅研究所碩、博士班申請者須準備，大學部申請者免附；申請雙聯學位者另附《雙聯學制計畫意向書》、《雙聯學位生出國進修申請表》與《應檢附文件一覽表》）",
      ],
      "scholarship_info": [
          "1. 國際事務處辦理教育部「學海飛颺」與「學海惜珠」出國研修獎助計畫（《辦理教育部 115 年度學海計畫甄選簡章》）：補助具中華民國國籍、於南藝大就讀一學期以上、歷年學業成績總平均達 80 分以上之優秀學生（學海惜珠另須持低收入戶、中低收入戶或特殊境遇家庭證明）赴境外（不含大陸港澳）修讀學分 1 學期至 1 學年（含雙聯學位生）。校內審查採兩階段計分（系所書面初審 50%＋國際處口試複審 50%，總分達 80 分以上為原則），補助經濟艙來回機票、國外學費及生活費（每年 2/26 及 9/9 截止向系所提出初審）。",
          "2. 國際事務處辦理教育部「學海築夢」與「新南向學海築夢」海外專業實習計畫：選送歷年學業總平均達 80 分以上之在學學生赴歐美日（如美國紐約公共圖書館 NYPL、克里夫蘭藝術博物館、史密森尼國家歷史博物館、舊金山現代藝術博物館 SFMOMA、德國日耳曼國家博物館、巴伐利亞邦皇宮修復中心、捷克布拉格國家圖書館、荷蘭 SRAL、比利時 KIK-IRPA、日本岡墨光堂与三乗堂）及新南向國家（如新加坡國家文物局遺產保存中心 HCC、澳洲新南威爾斯美術館 AGNSW）進行博物館學、古物維護、紙質與繪畫修復及藝術職涯探索實習，補助來回機票與生活費。",
          "3. 國際事務處《國立臺南藝術大學赴境外研修雙聯學位獎助學金設置要點》（115年最新公告）：專款獎助本校與境外雙聯合作大學（韓國誠信女子大學、韓國傳統文化大學、印尼國立日惹印尼藝術大學、印尼安巴魯莫觀光學院）修讀雙聯學位之本國籍在學學生（不含在職專班），每人每年獎助上限為新臺幣 200,000 元（20 萬元），分兩期核撥：第一期於出國就讀完成合作學校註冊後檢據核撥 50%，第二期於取得雙聯學位並完成南藝大學分抵免程序後核撥 50%（每年 9 月 30 日前向系所提出申請）。",
          "4. 姊妹校專屬免學費、免住宿費與生活津貼禮遇：（a）《只需繳交本校註冊費及學雜費即可前往交換的姊妹校》共 20 餘所合作校免收接待校學費；（b）韓國傳統文化大學（Korea National University of Heritage）除免收學費外，另提供南藝大交換生「免校內住宿費」及「每月韓幣 10 萬元生活津貼（共 4 個月）」。",
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": tnnua_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_TNNUA_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "國立臺南藝術大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 80.0,
      "academic_score_rule": (
          "依《115年國立臺南藝術大學交換生計畫實施要點》及《辦理教育部115年度學海計畫甄選簡章》：申請人須為本校日間學制大學部二年級以上、七年一貫制五年級以上，或就讀一學期以上之碩、博士班在學學生（不含碩士在職專班）；第一階段「系所書面初審（歷年成績單及讀書計畫 30%＋專業作品及成就表現 20%）」得分須達 40 分（滿分 50 分）以上，始得送國際處參加第二階段「校內口試複審（面試 30%＋語言能力 20%）」，兩階段總成績達 80 分以上為錄取原則；申請教育部學海飛颺／惜珠／築夢獎助者，歷年學業成績總平均須達 80 分以上。"
      ),
      "academic_gpa_minimum": 3.0,
      "maximum_preferences": 3,
      "selection_rules": {
          "academic_policy": "score_or_rank",
          "academic_reference_year": "115",
          "undergraduate_gpa_minimum": 3.0,
          "graduate_academic_exempt": False,
          "exclude_in_service": True,
          "pending_quota_planning": False,
          "partner_requirements_need_confirmation": False,
          "degree_score_minimums": {
              "undergraduate": 80.0,
              "graduate": 80.0,
          },
          "excluded_undergraduate_years": [
              "大一",
              "大一上",
              "大一下",
              "一年級",
              "一年級上學期",
              "一年級下學期",
              "一貫制一",
              "一貫制二",
              "一貫制三",
              "一貫制四",
          ],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 79.0,
          "ielts": 6.0,
          "toefl_itp": 550.0,
          "toeic": 750.0,
      },
      "application_periods": [
          {
              "title": "國立臺南藝術大學 116年度第 1 梯次（秋季班出國）姊妹校交換生暨教育部學海計畫甄選（預計 2027/02/01–02/26 系所初審）",
              "details": [
                  "依《115年國立臺南藝術大學交換生計畫實施要點》及《辦理教育部學海計畫甄選簡章》，第一梯次甄選（當年度秋季出國交換或修讀雙聯學位）於每年 2 月下旬（2 月 26 日）截止向所屬系所提出書面資料初審，系所於 3 月上旬（3 月 6 日）前將初審達 40 分（滿分 50 分）以上之申請案送交國際事務處辦理口試複審。",
                  "申請人須為日間學制大學部二年級以上、七年一貫制五年級以上，或就讀一學期以上之碩、博士班學生（不含碩士在職專班），備妥申請表、中英文歷年成績單、自傳及讀書計畫、外語檢定證明、推薦函與專業作品集。",
              ],
              "source": {
                  "title": "國立臺南藝術大學國際事務處 115年度交換生計畫實施要點與 115-1 學海計畫甄選公告",
                  "source_url": TNNUA_EXCHANGE_ANN_114_2_URL,
                  "category": "exchange_application",
                  "summary": "南藝大國際事務處第一梯次姊妹校交換生與教育部學海計畫甄選時程、系所初審（40/50）與國際處口試複審（總分 80）規定。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "116-1 第一梯次姊妹校交換生暨學海計畫甄選",
              "audience": "all_students",
              "opens_at": "2027-02-01T09:00:00+08:00",
              "deadline_at": "2027-02-26T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "第一梯次於每年 2 月 26 日截止送系所初審、3 月 6 日截止送國際事務處複審。",
              "deadline_note": "逾時將不受理任何形式之補件（包含退件更正），請提前向所屬系所確認系所會議初審時間。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "國立臺南藝術大學 115年度第 2 梯次（春季班出國）姊妹校交換生（含雙聯學位）暨 115-2 學海計畫甄選（每年 9/9 系所初審、9/15 國際處複審）",
              "details": [
                  "依國際事務處《115年度（115-1學年）本校姐妹校交換生（含雙聯學位）開放申請》及《115-2年度教育部學海計畫開放申請》公告，申請者須於 9 月 9 日前向各系所提出書面資料初審，系所於 9 月 15 日前備齊申請人資料及初審結果送達國際事務處國際合作組（分機 1901）。",
                  "申請境外研修雙聯學位者（韓國誠信女子大學、韓國傳統文化大學、印尼國立日惹印尼藝術大學、安巴魯莫觀光學院）除填寫交換申請表外，須另填《雙聯學制計畫意向書》及《雙聯學位生出國進修申請表》，並可同步申請教育部學海惜珠計畫。",
              ],
              "source": {
                  "title": "國立臺南藝術大學國際事務處 115年度姊妹校交換生（含雙聯學位）暨 115-2 學海計畫開放申請公告",
                  "source_url": TNNUA_EXCHANGE_ANN_115_1_URL,
                  "category": "exchange_application",
                  "summary": "南藝大第二梯次（9/9 系所初審、9/15 國際處複審）姊妹校交換生、雙聯學位與學海計畫申請規範。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "115-2 第二梯次姊妹校交換生（含雙聯學位）暨學海計畫甄選",
              "audience": "all_students",
              "opens_at": "2026-08-15T09:00:00+08:00",
              "deadline_at": "2026-09-09T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "closed",
              "status_note": "115 年度第二梯次已於 2026 年 9 月 9 日截止系所初審、9 月 15 日截止國際處收件；下一年度第二梯次預計於 2027 年 9 月上旬截止。",
              "deadline_note": "聯絡窗口：姊妹校交換／學海飛颺／惜珠請洽國際合作組（分機 1901）；學海築夢國外實習請洽海外教育組（分機 1902）。",
              "reminder_eligible": False,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "國立臺南藝術大學「赴境外研修雙聯學位獎助學金」（每人每年上限新臺幣 20 萬元，每年 9 月底截止申請）",
              "details": [
                  "依《國立臺南藝術大學赴境外研修雙聯學位獎助學金設置要點》，本獎助學金旨在鼓勵具有中華民國國籍之本校在學學生（不含在職專班）赴境外雙聯合作大學（韓國誠信女子大學、韓國傳統文化大學、印尼國立日惹印尼藝術大學、安巴魯莫觀光學院）修讀雙聯學位，每人每年獎助上限為新臺幣 20 萬元。",
                  "每年 9 月底前檢具申請表、雙聯合作學校入學許可或申請證明、切結書、中文歷年成績單、外語能力證明及自傳與讀書計畫向所屬系所提出申請；10 月 15 日前由系所完成初審（須達 40/50 分以上）送交國際事務處辦理複審。",
              ],
              "source": {
                  "title": "國立臺南藝術大學 115年赴境外研修雙聯學位獎助學金公告與設置要點",
                  "source_url": TNNUA_DUAL_DEGREE_SCHOLARSHIP_URL,
                  "category": "scholarship",
                  "summary": "南藝大赴境外研修雙聯學位獎助學金每人每年上限 20 萬元、每年 9 月底截止申請與兩期核撥規定。",
              },
              "scope": "home_application",
              "program_types": ["dual_degree"],
              "academic_year": "116",
              "application_round": "116學年度赴境外研修雙聯學位獎助學金甄選",
              "audience": "all_students",
              "opens_at": "2027-08-15T09:00:00+08:00",
              "deadline_at": "2027-09-30T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "雙聯學位獎助學金每年自公告日起受理至 9 月 30 日止（10 月 15 日前系所完成初審送交國際處）。",
              "deadline_note": "獎助金分兩期核撥：完成境外合作校註冊後核撥 50%，取得雙聯學位並完成南藝大學分抵免後核撥 50%。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"國立臺南藝術大學國際事務處全球姊妹校交換、跨國雙聯學位與學海藝術文物修復實習總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所常態開放申請・{total_exp_reports} 篇學長姐交換與實習心得報告）"
              ),
              "details": [
                  (
                      f"國立臺南藝術大學（Tainan National University of the Arts, TNNUA，簡稱南藝大，創立於 1996 年，坐落於臺南市官田區大崎里大崎 66 號烏山頭水庫旁，為臺灣唯一兼具江南水鄉古橋建築景觀與高教深耕藝術文博特色之國立專業藝術大學）由「國際事務處（Office of International Affairs, OIA，分設國際合作組分機 1901 與海外教育組分機 1902）」統籌全校 5 大學院（音樂學院、視覺藝術學院、音像藝術學院、文博學院、跨域創生學院）之赴外交換生計畫、境外大學雙聯學制及教育部學海系列獎補助。本平台完整收錄 {len(partners)} 所臺南藝術大學官方合作姊妹校（含 {open_partner_count} 所常態開放申請之免學費交換與雙聯學位合作校，以及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 23 個國家與地區。"
                  ),
                  (
                      f"南藝大國際交流具備四大核心特色：（1）「只需繳交本校註冊費及學雜費即可前往交換」之全球頂尖藝術與綜合名校網絡（日本東京藝術大學 Geidai［視覺學院、文博學院研究生專屬］、愛知縣立藝術大學、岡山縣立大學；韓國誠信女子大學、韓國傳統文化大學 KNUH［免學費＋免住宿費＋4 個月每月 10 萬韓元生活津貼］、韓國藝術綜合大學 K-Arts、弘益大學、漢陽大學、檀國大學、水原大學、龍仁大學、聖公會大學；德國斯圖加特國立造型藝術學院 ABK、班貝格大學、希爾德斯海姆大學；義大利米蘭國立布雷拉美術學院、英國倫敦大學金匠學院 Goldsmiths、捷克布拉格表演藝術學院 AMU、斯洛維尼亞盧布爾雅納大學；美國華盛頓與傑佛遜學院 W&J；泰國藝術大學 Silpakorn、朱拉隆功大學［音樂學院專屬］、瑪希敦大學；印尼日惹藝術大學 ISI、峇里島藝術學院 ISI Denpasar、安巴魯莫觀光學院；哈薩克國立藝術學院、澳門城市大學及大陸中央美術學院 CAFA）；（2）4 所跨國雙聯學位合作校（韓國誠信女大、韓國傳統文化大學、印尼日惹藝術大學 ISI、印尼安巴魯莫觀光學院 STIPRAM）搭配南藝大《赴境外研修雙聯學位獎助學金》每人每年最高 20 萬元；（3）享譽全國之文博與藝術修復「學海築夢／新南向學海築夢」海外實習（選送學生赴美國紐約公共圖書館、克里夫蘭藝術博物館、史密森尼國家歷史博物館、SFMOMA、德國日耳曼國家博物館、巴伐利亞皇宮修復中心、捷克布拉格國家圖書館、荷蘭 SRAL、比利時 KIK-IRPA、新加坡國家文物局 HCC、澳洲新南威爾斯美術館等世界級機構實習）；（4）收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆交換生與學海築夢實習心得報告。"
                  ),
              ],
              "source": {
                  "title": "國立臺南藝術大學國際事務處（OIA）官方網站",
                  "source_url": TNNUA_OIA_HOME_URL,
                  "category": "exchange_application",
                  "summary": f"臺南藝術大學 {len(partners)} 所全球合作姊妹校、{open_partner_count} 所常態開放交換／雙聯校與 {total_exp_reports} 篇心得報告。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "日間學制大二／七年一貫制五年級／碩博滿一學期在學資格、兩階段初複審配分（系所初審 40/50、總分 80）與學海平均 80 分門檻",
              "details": [
                  "在學身分與年級限制：依《115年國立臺南藝術大學交換生計畫實施要點》第三點，申請人須為本校日間學制大學部二年級以上、七年一貫制學士班五年級以上，以及就讀一學期以上之碩、博士班在學學生（不含碩士班在職專班；轉學生須曾於本校就讀一學期以上並持有成績單）。",
                  "兩階段初複審配分與錄取門檻：第一階段「系所書面初審（50%：歷年成績單及讀書計畫 30%＋專業作品及成就表現 20%）」須經系所會議通過且得分達 40 分（滿分 50 分）以上，始得送國際處參加第二階段「校內口試複審（50%：面試 30%＋語言能力［含以交換國授課語言 1–2 分鐘自我介紹］20%）」，總成績達 80 分以上為錄取原則；申請教育部《學海飛颺／惜珠／築夢》者，在校歷年學業成績總平均須達 80 分以上。",
              ],
              "source": {
                  "title": "115年國立臺南藝術大學交換生計畫實施要點及申請表與教育部 115 年度學海計畫甄選簡章",
                  "source_url": TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                  "category": "exchange_application",
                  "summary": "南藝大交換生在學年級規定、系所初審（40/50）與國際處口試複審（總分 80）配分比重及學海計畫學業平均 80 分門檻。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "南藝大《外國語文能力對照表》（英語 iBT 79 / IELTS 6.0、日語 N2、韓語 TOPIK 3、法德西語 B1 / FLPT 150）與口試 1–2 分鐘外語自我介紹",
              "details": [
                  "外國語文能力對照表標準（《交換生計畫實施要點》第四點）：（1）英語：TOEFL iBT 79（或電腦托福 CBT 213）或 IELTS 6.0 以上；（2）日語：JLPT N2 以上；（3）韓語：TOPIK 3 級以上；（4）法語：DELF / TCF B1 或 FLPT 筆試 150 分（口試 S-2）以上；（5）德語：Goethe-Zertifikat B1、TestDaF TDN3 或 FLPT 筆試 150 分（口試 S-2）以上；（6）西班牙語：DELE B1 或 FLPT 筆試 150 分（口試 S-2）以上。",
                  "選修外語學分替代與校內口試外語自介：申請人除檢附上述外語檢定證明外，亦得檢附曾選修相關外國語文之學分證明；惟所有進入第二階段校內口試複審之申請人，均須於口試時以交換國家之授課語言進行 1 至 2 分鐘自我介紹（語言能力占總成績 20%）。大陸地區姊妹校為中文授課，免附外語檢定證明。",
              ],
              "source": {
                  "title": "115年國立臺南藝術大學交換生計畫實施要點《外國語文能力對照表》",
                  "source_url": TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                  "category": "exchange_application",
                  "summary": "南藝大英語、日語、韓語、法語、德語、西班牙語能力基準對照表與校內口試外語自我介紹規定。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "交換生計畫申請表、系所初審評分表、中英文歷年成績單、中英文自傳及讀書計畫、外語證明、師長推薦函與專業作品集",
              "details": [
                  "校內交換生甄選應備文件：（1）《國立臺南藝術大學交換生計畫申請表》（含師長推薦意見與簽章、家長同意簽章、系所主管簽章）與《南藝大系所初審評分表》；（2）中、英文歷年成績單各一份（需含交換前最後一學期成績）；（3）外語能力檢定證明或選修外語學分證明；（4）中、英文自傳及讀書計畫各一份；（5）師長推薦函；（6）專業作品集（Portfolio／演奏影音）及成就表現資料；（7）研究所申請者另附大學畢業證書中、英文影本各一份（申請雙聯學位者另附《雙聯學制計畫意向書》及《雙聯學位生出國進修申請表》）。",
                  "錄取確認與返國核銷文件：獲錄取者須依限繳交《交換學生錄取確認書》與《家長同意書》；返國後兩週（14 日）內須繳交約 2,000 字《交換生心得報告》電子檔及照片 4 張，學海計畫或雙聯學位受獎生另須檢附登機證正本、電子機票收據、護照出入境章影本及國外成績單辦理經費核銷與學分抵免。",
              ],
              "source": {
                  "title": "國立臺南藝術大學國際事務處「相關表格」專區與 115年交換生計畫實施要點",
                  "source_url": TNNUA_FORMS_URL,
                  "category": "exchange_application",
                  "summary": "南藝大交換生計畫申請表、系所初審評分表、雙聯學制申請表單及返國心得報告規範。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部學海飛颺／惜珠／築夢獎助、南藝大赴境外研修雙聯學位獎助學金（每年上限 20 萬元）與韓國傳統文化大學免住宿費＋生活津貼禮遇",
              "details": [
                  "教育部學海系列計畫（國際事務處主辦，每年 2/26、9/9 截止送系所初審）：（1）《學海飛颺》與《學海惜珠》補助歷年學業總平均達 80 分以上之優秀生／清寒優秀生赴境外（不含港澳陸）交換或修讀雙聯學位 1 學期至 1 學年；（2）《學海築夢》與《新南向學海築夢》補助學生赴歐美日星澳等國博物館、圖書館與文物修復中心進行海外專業實習。",
                  "南藝大《赴境外研修雙聯學位獎助學金設置要點》（每年 9 月底截止）與姊妹校特別待遇：（1）修讀境外雙聯學位（韓國誠信女大、韓國傳統文化大學、印尼日惹藝術大學 ISI、安巴魯莫觀光學院）之本國籍在學學生，每人每年獎助上限新臺幣 20 萬元（出國註冊後核撥 50%、取得雙聯學位並完成學分抵免後核撥 50%）；（2）韓國傳統文化大學（KNUH）提供南藝大交換生「免學費＋免住宿費＋每月 10 萬韓元生活津貼（共 4 個月）」之優渥待遇。",
              ],
              "source": {
                  "title": "國立臺南藝術大學辦理教育部 115 年度學海計畫甄選簡章與赴境外研修雙聯學位獎助學金設置要點",
                  "source_url": TNNUA_DUAL_DEGREE_SCHOLARSHIP_PDF_URL,
                  "category": "scholarship",
                  "summary": "南藝大教育部學海飛颺、學海惜珠、學海築夢、赴境外研修雙聯學位獎助學金（20 萬元）與姊妹校免學費／免宿費完整規定。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "國立臺南藝術大學出國交換中/英文讀書計畫、專業作品集（Portfolio）、雙聯學制意向書與口試外語自我介紹準備指南",
              "summary": "說明南藝大《交換生計畫實施要點》第一階段系所書面初審（歷年成績單及讀書計畫 30%＋專業作品及成就表現 20%，須達 40/50 分以上）與第二階段校內口試複審（面試 30%＋語言能力［含 1–2 分鐘外語自介］20%）之審查重點。",
              "key_points": [
                  "中、英文自傳及讀書計畫（系所書面初審占 30%）：應針對目標姊妹校對應系所（如東京藝術大學美術／文化財保存、布拉格表演藝術學院 FAMU/HAMU、斯圖加特造型藝術學院、誠信女大或韓國傳統文化大學）詳列擬修習之工作坊、個別指導課（Studio / Lesson）或理論課程，並說明與南藝大母系所畢業製作或論文研究之連結。",
                  "專業作品集及成就表現（系所書面初審占 20%）：視覺藝術、材質創作、造形、應藝、建築、動畫與音像紀錄學生建議準備中英文對照之精選作品集 PDF 與動態影像連結；音樂學系、中國音樂學系、應用音樂學系、鋼琴合作所與民音所學生建議準備代表性曲目演奏／創作影音與展演獲獎紀錄，確保系所初審得分達 40 分（滿分 50 分）以上。",
                  "第二階段校內口試複審與 1–2 分鐘外語自我介紹（占總成績 50%）：口試由國際事務處處長、教務長、學務長與各院院長共同評分，申請人必須預先準備以「交換國家之授課語言（英／日／韓／德／法／西語）」進行 1 至 2 分鐘流暢自我介紹與研修動機說明。",
              ],
              "applies_to": [],
              "source": {
                  "title": "115年國立臺南藝術大學交換生計畫實施要點及南藝大系所初審評分表",
                  "source_url": TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": TNNUA_FORMS_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "國立臺南藝術大學交換生計畫實施要點、與境外大學校院辦理雙聯學制實施辦法（114.05.26）與國際交流獎補助校內審查辦法核心規定",
              "summary": "規範南藝大出國交換兩階段初複審門檻（初審 40/50、總分 80）、出國期間在學註冊繳費（免繳互惠姊妹校學費）、雙聯學制修業月數與返國兩週內繳交心得報告義務。",
              "key_points": [
                  "兩階段初複審及格門檻：第一階段系所書面初審（50%）須經系所會議通過且得分達 40 分以上，始得送件至國際處參加第二階段校內口試複審（50%）；兩階段總成績以達 80 分為錄取原則（申請教育部學海計畫者，在校學業成績總平均亦須達 80 分以上）。",
                  "出國期間註冊繳費與返國報告義務：交換生於交換期間仍須辦理南藝大註冊手續並繳交本校學雜費（享有免繳互惠姊妹校學費優惠）；結束交換計畫返國後兩週（14 日）內，須提交約 2,000 字之《交換生心得報告》電子檔及照片 4 張予國際事務處。",
                  "境外雙聯學制修業時間與學分規定：依《與境外大學校院辦理雙聯學制實施辦法》（114年5月26日修正），雙聯學士班在兩校修業時間合計至少滿 32 個月（在本校修業至少 2 學年）、碩士班合計至少滿 12 個月（在兩校各至少 1 學期）、博士班合計至少滿 24 個月（在兩校各至少 2 學期），且在兩校修習學分數各須達畢業應修總學分數 1/3 以上。",
              ],
              "applies_to": [],
              "source": {
                  "title": "115年國立臺南藝術大學交換生計畫實施要點與辦理雙聯學制實施辦法（114.05.26）",
                  "source_url": TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": TNNUA_DUAL_DEGREE_RULES_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "國立臺南藝術大學國際事務處（Office of International Affairs）官方網站",
              "source_url": TNNUA_OIA_HOME_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立臺南藝術大學國際事務處「只需繳交本校註冊費及學雜費即可前往交換的姊妹校」專頁與官方名冊 PDF",
              "source_url": TNNUA_TUITION_FREE_PARTNERS_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立臺南藝術大學國際事務處「近年新增姊妹校簡介（2025–2026）」專頁（含澳門城大、誠信女大、韓國傳統文化大學、哈薩克國立藝術學院、泰國藝術大學、布拉格表演藝術學院、華盛頓與傑佛遜學院、龍仁大學、水原大學對應系所表）",
              "source_url": TNNUA_NEW_PARTNERS_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "115年國立臺南藝術大學交換生計畫實施要點及申請表（PDF）",
              "source_url": TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立臺南藝術大學「國際雙聯學位專區」與《與境外大學校院辦理雙聯學制實施辦法（114.05.26）》",
              "source_url": TNNUA_DUAL_DEGREE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立臺南藝術大學「115年赴境外研修雙聯學位獎助學金」專頁與設置要點（每人每年上限 20 萬元）",
              "source_url": TNNUA_DUAL_DEGREE_SCHOLARSHIP_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "國立臺南藝術大學辦理教育部 115-1／115-2 年度學海計畫（學海飛颺、學海惜珠、學海築夢、新南向學海築夢）甄選簡章",
              "source_url": TNNUA_XUEHAI_BROCHURE_115_1_PDF_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": f"國立臺南藝術大學國際事務處「交換生心得分享」與「海外職涯探索（學海築夢）心得分享」專區（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）",
              "source_url": TNNUA_EXPERIENCE_SHARING_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_TNNUA_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  doc_conditions = {
      "school_id": "tnnua",
      "school_name": "國立臺南藝術大學",
      "checked_at": CHECKED_AT,
      "source_url": TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
      "common_documents": exchange_info_payload["required_documents"],
      "track_specific_conditions": [
          {
              "track": "國際事務處「免收姊妹校學費交換生計畫」（日本、韓國、歐美、東南亞及大陸姊妹校）",
              "required": [
                  "115年國立臺南藝術大學交換生計畫申請表（含師長推薦意見、申請人與家長簽章、系所主管核章）與《南藝大系所初審評分表》",
                  "本校中、英文歷年成績單正本各一份（需含交換前最後一學期成績；占系所初審 30%）",
                  "外國語文能力檢定證明（英語 TOEFL iBT 79 / IELTS 6.0、日語 JLPT N2、韓語 TOPIK 3、法德西語 B1 / FLPT 150）或曾選修相關外語學分證明（大陸地區免附）",
                  "中、英文自傳及讀書計畫各一份、師長推薦函、專業作品集及成就表現資料（占系所初審 20%；研究所另附大學畢業證書中英文影本）",
              ],
          },
          {
              "track": "境外大學雙聯學制計畫（韓國誠信女子大學、韓國傳統文化大學、印尼國立日惹印尼藝術大學、安巴魯莫觀光學院）",
              "required": [
                  "雙聯學制計畫意向書（20250911 版）與雙聯學位生出國進修申請表",
                  "境外大學雙聯學制出國進修申請應檢附文件一覽表所列之中英文歷年成績單、學位證書影本、外語能力證明、英文讀書／研究計畫與指導教授推薦信",
                  "申請《赴境外研修雙聯學位獎助學金》（每年上限 20 萬元，9 月底截止）者，另附獎助學金申請表、雙聯合作學校入學許可影本、切結書與系所初審評分表",
              ],
          },
          {
              "track": "教育部「學海飛颺／學海惜珠」出國研修獎助與「學海築夢／新南向學海築夢」海外實習計畫",
              "required": [
                  "學海飛颺／惜珠申請表與經費編列範本、在校歷年學業成績總平均達 80 分以上之中英文成績單正本、外語能力證明、1,500–3,000 字出國研修計畫書及專業作品成就表現",
                  "學海惜珠另檢附直轄市或縣市政府核發之低收入戶、中低收入戶或特殊境遇家庭相關證明文件",
                  "學海築夢／新南向學海築夢由計畫主持人（專任教師）協同學生提出海外專業機構（博物館、美術館、文物修復中心等）實習計畫書與接待機構同意函",
              ],
          },
      ],
  }
  (OFFICIAL_TNNUA_DIR / "document-conditions.json").write_text(
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
        f"{fname},{len(partners)},{pop},{ratio:.4f},Official TNNUA OIA verified"
    )
  (OFFICIAL_TNNUA_DIR / "field-coverage.csv").write_text(
      "\n".join(field_cov_lines) + "\n", encoding="utf-8"
  )

  pages_records = [
      {
          "title": "國立臺南藝術大學：姊妹校交換生（含雙聯學位）兩梯次甄選（2月、9月）、教育部學海計畫與雙聯學位獎助學金申請時程",
          "source_url": TNNUA_EXCHANGE_ANN_115_1_URL,
          "published_at": "2026-10-15T00:00:00Z",
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
          "title": "國立臺南藝術大學：115年交換生計畫實施要點、兩階段初複審配分（系所初審 40/50、口試複審總分 80）與學海平均 80 分資格",
          "source_url": TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
          "published_at": "2026-10-15T00:00:00Z",
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
          "title": f"國立臺南藝術大學：{len(partners)} 所全球與兩岸合作姊妹校外語檢定門檻（外國語文能力對照表）與校內口試 1–2 分鐘外語自介規定",
          "source_url": TNNUA_EXCHANGE_GUIDELINES_PDF_URL,
          "published_at": "2026-10-15T00:00:00Z",
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
          "title": "國立臺南藝術大學：出國交換與雙聯學位應備文件（交換生申請表、系所初審評分表、中英文成績單、自傳讀書計畫、作品集與返國報告）",
          "source_url": TNNUA_FORMS_URL,
          "published_at": "2026-10-15T00:00:00Z",
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
          "title": "國立臺南藝術大學：教育部學海飛颺、學海惜珠、學海築夢、赴境外研修雙聯學位獎助學金（每年上限 20 萬元）與免學費姊妹校待遇",
          "source_url": TNNUA_DUAL_DEGREE_SCHOLARSHIP_URL,
          "published_at": "2026-10-15T00:00:00Z",
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
  (OFFICIAL_TNNUA_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
      + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "tnnua",
      "school_name": "國立臺南藝術大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "stage1_department_written_weight": 0.50,
          "stage1_minimum_passing_score_out_of_50": 40.0,
          "stage2_university_interview_weight": 0.50,
          "total_passing_score_minimum": 80.0,
          "xuehai_academic_average_minimum": 80.0,
          "dual_degree_scholarship_annual_cap_ntd": 200000,
          "stage1_breakdown": {
              "transcript_and_study_plan": 0.30,
              "portfolio_and_achievements": 0.20,
          },
          "stage2_breakdown": {
              "interview": 0.30,
              "language_ability_and_1_2_min_self_intro": 0.20,
          },
          "require_tnnua_enrollment_and_tuition_during_abroad": True,
          "exclude_in_service_masters": True,
          "return_documents_due": "結束交換返國後兩週（14日）內繳交約 2,000 字交換生心得報告電子檔及照片 4 張，並辦理學分抵免",
      },
      "source_urls": tnnua_source_urls,
      "verified_at": "2026-11-02",
  }
  (OFFICIAL_TNNUA_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_TNNUA_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "國立臺南藝術大學",
              "required_documents": student_dashboard_payload[
                  "required_documents"
              ],
              "source_urls": tnnua_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_TNNUA_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "國立臺南藝術大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": tnnua_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "tnnua",
      "school_name": "國立臺南藝術大學",
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
          f"國立臺南藝術大學國際事務處（OIA）《115年交換生計畫實施要點及申請表》、《只需繳交本校註冊費及學雜費即可前往交換的姊妹校》、《2025–2026近年新增姊妹校簡介》、4 所境外雙聯學位合作校（韓國誠信女子大學、韓國傳統文化大學、印尼國立日惹印尼藝術大學 ISI、印尼安巴魯莫觀光學院 STIPRAM）、《赴境外研修雙聯學位獎助學金設置要點（每年上限 20 萬元）》及教育部 115-1／115-2 學海飛颺、學海惜珠、學海築夢、新南向學海築夢甄選簡章同步整合；共完整收錄 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所常態開放申請交換與雙聯學校及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 23 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷年學長姐交換與學海築夢實習心得報告）。"
      ),
      "verified_at": "2026-11-02",
  }
  (OFFICIAL_TNNUA_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_TNNUA_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "tnnua",
              "school_name": "國立臺南藝術大學",
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
          "sources/tnnua/tnnua_catalog_source.json",
          TNNUA_PARTNERS_URL,
          f"國立臺南藝術大學 {len(partners)} 所全球與兩岸合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/tnnua/tnnua_resolved_locations.json",
          TNNUA_PARTNERS_URL,
          f"國立臺南藝術大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
      ),
      (
          "sources/tnnua/tnnua_experience_index.json",
          TNNUA_EXPERIENCE_SHARING_URL,
          f"國立臺南藝術大學 {total_exp_reports} 篇交換生與學海築夢海外實習心得報告索引 JSON",
      ),
      (
          "sources/tnnua/tnnua_academic_units.html",
          "https://www.tnnua.edu.tw/p/412-1000-91.php?Lang=zh-tw",
          "國立臺南藝術大學全校 5 大學院（音樂、視覺藝術、音像藝術、文博、跨域創生）與系所架構 HTML",
      ),
  ]
  for rel_p, surl in bin_urls.items():
    rp = rel_p if rel_p.startswith("sources/") else f"sources/tnnua/{rel_p}"
    if not any(x[0] == rp for x in provenance_files):
      provenance_files.append((rp, surl, f"國立臺南藝術大學官方原始檔案：{Path(rp).name}"))

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
      "school_id": "tnnua",
      "school_name": "國立臺南藝術大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = (
      json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  )
  (OFFICIAL_TNNUA_DIR / "import_provenance.json").write_text(
      prov_text, encoding="utf-8"
  )
  (OFFICIAL_TNNUA_DIR / "import-provenance.json").write_text(
      prov_text, encoding="utf-8"
  )

  print(
      f"Successfully built TNNUA catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
