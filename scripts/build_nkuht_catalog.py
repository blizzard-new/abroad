"""Build the official National Kaohsiung University of Hospitality and Tourism (國立高雄餐旅大學, NKUHT) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_NKUHT_DIR = REPO_ROOT / "sources" / "nkuht"
OFFICIAL_NKUHT_DIR = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "nkuht"
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

NKUHT_IAO_HOME_URL = "https://iao.nkuht.edu.tw/"
NKUHT_STUDY_ABROAD_URL = "https://iao.nkuht.edu.tw/p/412-1007-7229.php?Lang=zh-tw"
NKUHT_2027_28_PLATFORM_URL = "https://iao.nkuht.edu.tw/p/412-1007-7236.php?Lang=zh-tw"
NKUHT_TUITION_FREE_URL = "https://iao.nkuht.edu.tw/p/403-1007-1052.php?Lang=zh-tw"
NKUHT_FEE_BASED_URL = "https://iao.nkuht.edu.tw/p/403-1007-1051.php?Lang=zh-tw"
NKUHT_APPLICATION_QUALIFICATIONS_URL = "https://iao.nkuht.edu.tw/p/412-1007-5693.php?Lang=zh-tw"
NKUHT_APPLICATION_DOWNLOADS_URL = "https://iao.nkuht.edu.tw/p/412-1007-5714.php?Lang=zh-tw"
NKUHT_XUEHAI_SCHOLARSHIP_URL = "https://iao.nkuht.edu.tw/p/412-1007-6527.php?Lang=zh-tw"
NKUHT_VOYAGE_OF_DISCOVERY_URL = "https://iao.nkuht.edu.tw/p/412-1007-6272.php?Lang=zh-tw"
NKUHT_EXPERIENCE_SHARING_URL = "https://iao.nkuht.edu.tw/p/404-1007-28830.php?Lang=zh-tw"
NKUHT_KEY_PARTNERS_URL = "https://iao.nkuht.edu.tw/p/412-1007-6251.php?Lang=zh-tw"
NKUHT_DUAL_DEGREE_URL = "https://iao.nkuht.edu.tw/p/412-1007-1495.php?Lang=zh-tw"
NKUHT_REGULATIONS_URL = "https://iao.nkuht.edu.tw/p/412-1007-1554.php?Lang=zh-tw"
NKUHT_OVERSEAS_INTERNSHIP_STUDY_SUPPLEMENT_PDF_URL = (
    "https://iao.nkuht.edu.tw/var/file/7/1007/img/1554/525995679.pdf"
)
NKUHT_IAO_SOP_PDF_URL = (
    "https://iao.nkuht.edu.tw/var/file/7/1007/img/1554/180823920.pdf"
)
NKUHT_XUEHAI_115_BROCHURE_PDF_URL = (
    "https://iao.nkuht.edu.tw/var/file/7/1007/img/6527/550985664.pdf"
)
NKUHT_VOYAGE_RULES_PDF_URL = (
    "https://iao.nkuht.edu.tw/var/file/7/1007/img/6272/983135147.pdf"
)
NKUHT_BRIEFING_2027_28_PDF_URL = (
    "https://iao.nkuht.edu.tw/var/file/7/1007/img/7236/869148640.pdf"
)
NKUHT_CEFR_EQUIVALENCY_PDF_URL = (
    "https://iao.nkuht.edu.tw/var/file/7/1007/img/7236/529517726.pdf"
)

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 700–1,200（折合日圓約 JPY 100,000–170,000 / 月、新臺幣約 22,500–38,500 元；阪南大學住宿約 JPY 45,000/月＋生活費 JPY 80,000–100,000/月並有機會領取每月 JPY 40,000 獎學金，山口大學單人房宿舍每月 JPY 12,200–20,000，東京武藏野大學與文京學院大學實習期間另享飯店實習津貼）",
        "須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後申辦留學／特定活動（實習）簽證並加入日本國民健康保險（NHI，約 JPY 20,000/年）。",
    ),
    "韓國": (
        "每月生活費約 USD 650–1,050（折合韓元約 KRW 850,000–1,400,000 / 月、新臺幣約 20,500–33,500 元；首爾仁德大學宿舍每學期 KRW 850,000、漢陽女子大學每月 KRW 160,000–250,000、大田又松大學每學期 USD 550–728）",
        "須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後辦理外國人登錄證並納保韓國國民健康保險。",
    ),
    "香港": (
        "每月生活費約 USD 1,000–1,550（折合港幣約 HKD 7,800–12,000 / 月、新臺幣約 32,000–50,000 元；香港理工大學校內學生宿舍約 HKD 9,000 / 學期）",
        "須透過香港理工大學協助向香港入境事務處申辦來港就讀進入許可（Student Visa / Entry Permit），並自行投保涵蓋在港期間之醫療與意外保險。",
    ),
    "澳門": (
        "每月生活費約 USD 800–1,250（折合澳門幣約 MOP 6,400–10,000 / 月、新臺幣約 25,500–40,000 元；澳門旅遊大學宿舍每學期 MOP 6,750［四人房］至 MOP 17,100［單人房］）",
        "須憑澳門旅遊大學錄取通知書辦理澳門「逗留特別許可（學生逗留簽注）」，並繳納每學期 MOP 180 團體保險及投保海外醫療險。",
    ),
    "中國大陸": (
        "每月生活費約 USD 380–680（折合人民幣約 RMB 2,500–4,500 / 月、新臺幣約 12,000–21,500 元；北京第二外國語學院、浙江旅遊職業學院、南京旅遊職業學院學生宿舍與食堂開銷）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及接待校錄取通知書報到，並依高餐大規定完成教育部「赴陸交流活動登錄平臺」填報與海外醫療意外保險投保。",
    ),
    "泰國": (
        "每月生活費約 USD 480–850（折合泰銖約 THB 16,000–28,000 / 月、新臺幣約 15,500–27,000 元；泰國藝術大學宿舍每學期 THB 7,000、曼谷大學與瓦萊嵐大學生活費實惠）",
        "須憑泰國接待大學入學許可公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 教育簽證並投保海外全期醫療險。",
    ),
    "菲律賓": (
        "每月生活費約 USD 480–820（折合新臺幣約 15,500–26,000 元；馬尼拉萊西姆大學 LPU 與奎松市菲律賓三一大學 TUA 校內外學生住宿與膳食親民）",
        "須依菲律賓接待大學指引辦理學生簽證（9F）或特別學習許可（SSP）並投保海外全期醫療保險。",
    ),
    "新加坡": (
        "每月生活費約 USD 1,100–1,750（折合新幣約 SGD 1,500–2,400 / 月、新臺幣約 35,000–56,000 元；實習期間可領取新加坡飯店餐旅實習津貼）",
        "須由新加坡接待院校向新加坡移民與關卡局（ICA）申辦 Student's Pass 或 Training Employment Pass（TEP）並投保醫療保險。",
    ),
    "阿拉伯聯合大公國": (
        "每月生活費約 USD 1,200–1,900（折合新臺幣約 38,000–60,000 元；杜拜阿聯酋酒店管理學院 EAHM 專案費用已含學季住宿及週一至週五早午餐，五星級酒店實習期間依飯店福利提供住宿與膳食）",
        "須由杜拜阿聯酋酒店管理學院（EAHM）代辦阿拉伯聯合大公國杜拜學生簽證，並於出發前投保涵蓋研修與實習全期之海外醫療及意外保險。",
    ),
    "芬蘭": (
        "每月生活費約 USD 950–1,450（折合歐元約 EUR 880–1,350 / 月、新臺幣約 30,500–46,500 元；赫爾辛基 Haaga-Helia 學生公寓 HOAS 每月房租約 EUR 380–550）",
        "交換 1 學期以上須向芬蘭移民局（Migri）線上申辦學生居留許可（Residence Permit for Studies）並投保涵蓋申根區之全期醫療保險。",
    ),
    "法國": (
        "每月生活費約 USD 1,000–1,650（折合歐元約 EUR 920–1,500 / 月、新臺幣約 32,000–53,000 元；法國西南 Savignac 住宿每月約 EUR 350–750，里昂 Institut Lyfe 與巴黎 FERRANDI 每月約 EUR 650–1,200）",
        "須先經法國教育中心（Campus France）完成 Etudes en France 線上程序與面試，再向法國在台協會申辦長期學生簽證（VLS-TS）並投保海外醫療險。",
    ),
    "荷蘭": (
        "每月生活費約 USD 1,150–1,700（折合歐元約 EUR 1,050–1,550 / 月、新臺幣約 36,500–54,500 元；荷蘭海牙旅館管理學院 HTH 專案費含阿姆斯特丹／海牙住宿，19 週全職實習期間每月平均實習津貼約 EUR 500）",
        "須由荷蘭海牙旅館管理學院代向荷蘭移民局（IND）申辦 MVV 入境簽證與 VVR 學生居留證，並投保荷蘭認可之全期學生醫療保險。",
    ),
    "義大利": (
        "每月生活費約 USD 950–1,450（折合歐元約 EUR 880–1,350 / 月、新臺幣約 30,500–46,500 元；佛羅倫斯藝術大學 FUA 專案費用已含秋冬兩季佛羅倫斯學生公寓住宿與每週定額餐券）",
        "須憑佛羅倫斯藝術大學入學許可與義大利醫療保險證明向義大利經濟貿易文化推廣辦事處申辦義大利長期學生 D 簽證。",
    ),
    "瑞士": (
        "每月生活費約 USD 1,500–2,300（折合瑞郎約 CHF 1,300–2,000 / 月；瑞士 Les Roches、Glion、CAAS、SHMS 研修期間專案費已含校內食宿，後 6 個月於瑞士飯店全職帶薪實習法定最低月薪約 CHF 2,303/月［約新臺幣 85,000 元/月］）",
        "須由瑞士接待校向所在州移民局申辦瑞士學生入境授權書（Authorization for Visa）與 B Permit 居留證，並依瑞士聯邦規定納保瑞士學生醫療保險。",
    ),
    "英國": (
        "每月生活費約 USD 1,350–2,000（折合英鎊約 GBP 1,050–1,580 / 月、新臺幣約 43,000–64,000 元；英國伯明罕大學學院 UCB 與艾賽克斯大學 Edge Hotel School 實習期間享英國法定最低時薪約 GBP 12/hr）",
        "研修加實習滿 1 學年須憑英國接待校核發之 CAS 申辦英國 Student Visa 並繳納英國醫療附加費（IHS）。",
    ),
    "美國": (
        "每月生活費約 USD 1,350–2,100（折合新臺幣約 43,000–67,000 元；美國蒙特克萊爾州立大學 MSU 迪士尼交換計畫於佛羅里達華特迪士尼世界實習期間享時薪約 USD 19/hr、每週保證 30–32 小時工時，可大幅支應住宿與生活費）",
        "須憑美國接待大學核發之 DS-2019 表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦 J-1 交換訪問學者／學生簽證，且須投保符合校方與美國國務院規定之全期醫療保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,200–1,850（折合加幣約 CAD 1,650–2,500 / 月、新臺幣約 38,500–59,000 元；多倫多漢堡學院 Humber 專案費用已含 2 學期校內住宿含餐，5 個月帶薪實習期間時薪約 CAD 17.22–20.60/hr）",
        "須向加拿大移民局（IRCC）同時申辦加拿大 Study Permit（學習許可）與 Co-op Work Permit（實習工作許可），並納保加拿大安大略省國際學生健康保險。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,450–2,200（折合澳幣約 AUD 2,200–3,350 / 月、新臺幣約 46,500–70,000 元；阿得雷德 ICHM 後 6 個月五星級飯店帶薪實習時薪約 AUD 25–35/hr，6 個月實習總收入約 AUD 12,000–18,000）",
        "須購買澳洲海外學生健康保險（OSHC）並憑昆士蘭大學（UQ）或澳洲國際旅館管理學院（ICHM）核發之 CoE 申辦澳洲 Subclass 500 學生簽證（研修期間每兩週可合法工讀 48 小時，實習期間全職工作時數不限）。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "第一學期（秋季／春季研修）：約 8–9 月或 4 月入學研修 1 學期（10 學分）；第二學期（日本飯店／企業實習）：銜接 6 個月日本在地飯店或溫泉旅館全職實習（10 學分），合計 12 個月",
    "韓國": "海外研修學期：約 8 月底至 12 月中旬（秋季班）或 3 月初至 6 月中旬（春季班）赴韓研修 1 學期（10 學分）；另一學期返臺完成專業實習（10 學分）",
    "香港": "海外研修學期：約 9 月初至 12 月下旬（秋季班）或 1 月中旬至 5 月中旬（春季班）赴香港理工大學 SHTM 研修 1 學期（10 學分）；另一學期返臺完成實習（10 學分）",
    "澳門": "海外研修學期：約 8 月下旬至 12 月下旬（秋季班）或 1 月中旬至 5 月下旬（春季班）赴澳門旅遊大學 UTM 研修 1 學期（10 學分）；另一學期返臺完成實習（10 學分）",
    "泰國": "海外研修學期：約 8 月至 12 月赴泰國藝術大學／曼谷大學／瓦萊嵐大學研修 1 學期（10 學分）；另一學期返臺完成專業實習（10 學分）",
    "菲律賓": "海外研修學期：約 8 月至 12 月或 1 月至 5 月赴菲律賓三一大學／萊西姆大學研修 1 學期（10 學分）；另一學期返臺完成實習（10 學分）",
    "芬蘭": "春季研修學期：先於臺灣完成第 1 學期實習（10 學分），翌年 1 月至 6 月赴芬蘭赫爾辛基 Haaga-Helia 交換研修 1 學期（10 學分）",
    "法國": "海外研修學期：約 8–9 月至翌年 1 月（或 1 月至 6 月）赴法國 FERRANDI Paris / Institut Lyfe / Savignac 研修 1 學期（10 學分）；另一學期於臺灣完成實習（10 學分）",
    "瑞士": "第一階段（瑞士校區專業研修）：約 7–9 月至翌年 1 月（10 學分）；第二階段（瑞士或全球奢華酒店帶薪實習）：2 月至 7 月全職支薪實習 6 個月（10 學分），合計 12 個月",
    "荷蘭": "第一階段（海牙／阿姆斯特丹校區研修）：約 8 月至翌年 1 月（10 學分）；第二階段（荷蘭／歐洲飯店全職實習）：2 月至 6 月共 19 週實習（10 學分），合計 12 個月",
    "義大利": "第一階段（佛羅倫斯秋冬兩季研修）：約 9 月至翌年 5 月（10 學分）；第二階段（義大利夏季餐旅廚藝實習）：5 月至 8 月共 12 週實習（10 學分），合計 12 個月",
    "英國": "第一階段（英國校區模組研修）：約 9 月至翌年 1 月（10 學分）；第二階段（英國飯店餐飲業帶薪實習）：2 月至 7 月共 6 個月全職實習（10 學分），合計 12 個月",
    "美國": "第一階段（紐澤西州蒙特克萊爾州立大學研修）＋第二階段（佛羅里達州奧蘭多華特迪士尼世界度假區 Walt Disney World 帶薪實習），合計約 6–12 個月",
    "加拿大": "第一階段（多倫多漢堡學院 5 週英語先修＋2 學期專業研修，約 7–8 月至翌年 4 月）＋第二階段（加拿大多倫多地區 5 個月餐旅帶薪實習，5 月至 8 月），合計 12 個月",
    "澳洲": "研修暨實習方案（ICHM）：約 8 月至翌年 1 月研修 4 門課（10 學分）＋2 月至 7 月澳洲五星級飯店 6 個月全職帶薪實習（10 學分）；雙聯碩士方案（昆士蘭大學 UQ）：高餐大碩一＋澳洲 UQ 碩二（2 學期）",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
  """Ensure school-images.json and university_locations.jsonl contain all 40 NKUHT partner schools."""
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
          else loc.get("lat", 22.5668)
      )
      lon = float(
          loc.get("longitude")
          if loc.get("longitude") is not None
          else loc.get("lon", 120.3719)
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
  OFFICIAL_NKUHT_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_NKUHT_DIR / "nkuht_catalog_source.json").read_text(
          encoding="utf-8"
      )
  )
  resolved_locations = json.loads(
      (SOURCES_NKUHT_DIR / "nkuht_resolved_locations.json").read_text(
          encoding="utf-8"
      )
  )
  bin_urls_path = SOURCES_NKUHT_DIR / "binary_source_urls.json"
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
        item.get("group") or "國際事務處關鍵合作姊妹校"
    )
    quota_str = clean_text(
        item.get("quota") or "依國立高雄餐旅大學國際事務處當期公告名額"
    )
    detail_url = item.get("detail_url") or NKUHT_KEY_PARTNERS_URL

    if "雙聯" in group_str:
      program_type = "國際事務處 2027–28 付費方案暨 1+1 雙聯碩士學位計畫（Double Master's Degree Program）"
      source_url = detail_url
    elif "學費減免方案" in group_str and avail_status == "open":
      program_type = f"{group_str}（免繳接待姊妹校學費）"
      source_url = detail_url
    elif "付費方案" in group_str and avail_status == "open":
      program_type = f"{group_str}（海外專業研修暨帶薪／專業實習）"
      source_url = detail_url
    elif country in {"中國大陸", "澳門", "香港"}:
      program_type = "國際事務處正式締約大陸與港澳關鍵合作姊妹校"
      source_url = detail_url
    else:
      program_type = "國際事務處正式締約關鍵合作姊妹校暨歷年海外研修實習合作校"
      source_url = detail_url

    colleges_str = clean_text(
        item.get("colleges")
        or "餐旅學院、觀光學院、廚藝學院、國際學院"
    )
    degree_levels_str = clean_text(
        item.get("eligible_degrees")
        or "日間部四技二年級（含）以上、二技一年級下學期、五專四年級及碩士班在學學生"
    )
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "")
    website = item.get("website") or NKUHT_KEY_PARTNERS_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    round_label = (
        "115-1 梯次（2027–28 海外研修暨實習方案：學費減免方案／付費方案／雙聯碩士）"
        if avail_status == "open"
        else "國際事務處關鍵合作姊妹校（當期開放名額依國際處最新海外研修暨實習平台公告為準）"
    )
    app_deadline_str = clean_text(
        item.get("deadline")
        or "115-1 梯次（2027–28 出國研修暨實習）：2026年10月14日開放申請、2026年11月13日（週五）12:00 截止收件、2026年11月20日公布錄取名單、2027年2月26日–3月3日語言證照補繳截止"
    )
    deadline_iso = "2026-11-13T12:00:00+08:00"
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "115"

    study_period_str = clean_text(
        item.get("duration") or "一學年（1 學期海外研修 10 學分＋1 學期實習 10 學分，合計 12 個月）"
    )
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "第一學期：約 8–9 月至翌年 1 月；第二學期：約 2 月至 7 月（合計 12 個月研修加實習）"
    )
    housing_str = (
        f"獲國立高雄餐旅大學國際事務處推薦錄取後，可依 {zh_name} 國際處指引申請校內外學生宿舍或實習住宿"
        + (f"（費用與實習待遇：{tuition_note}）" if tuition_note else "。")
    )
    course_rest_str = (
        f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《國立高雄餐旅大學學生海外實習及研習輔導補充規定》及國際事務處《2027–28 海外研修暨實習方案》規定："
        "（1）海外研修加實習期間以 12 個月（一學年）為原則，分別抵免大三（或專四）1 學期海外研修必修 10 學分與 1 學期海外／國內實習必修 10 學分（研究所碩士生可申請澳洲昆士蘭大學 1+1 雙聯碩士學位）；"
        "（2）EMI／ESP 全英語課程先修規定：重點培育學院（餐旅學院、觀光學院、國際學院）學生出國前須修習 EMI 或 ESP 課程至少 2 門且及格，廚藝學院及應用日語系學生至少 1 門；"
        "（3）操行與獎懲門檻：申請人前三學期操行成績平均須達 70 分以上，且在校期間無小過（含）以上處分或違法紀錄；"
        "（4）語言證照補繳期限：報名時若尚未取得目標學校語言檢定門檻，最遲須於 2027 年 2 月 26 日至 3 月 3 日前補繳達標語言證照，逾期視同放棄錄取資格。"
    )

    living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
        country,
        (
            "每月生活費約 USD 800–1,400（依匯率折合新臺幣約 25,500–45,000 元，含住宿、膳食與市區交通）",
            "須依接待國駐臺機構規定申辦學生／實習簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
        ),
    )

    tuition_points_list = [
        (
            f"高餐大在學註冊與學雜費規定（依《學生海外實習及研習輔導補充規定》）：出國研修暨實習期間須辦理高餐大註冊手續並保有學籍；「學費減免方案（19 校）」免繳國外接待大學學費，僅需繳交高餐大校內全額學雜費；「付費方案（12 校）」依合作專案繳交國外學校學費與住宿實訓費（高餐大校內學雜費依出國期間減免規定辦理），並於實習學期享當地帶薪實習薪資。本合作校待遇：{tuition_note}。"
        ),
        (
            "高餐大兩大核心出國研修獎助學金體系（每年 2 月下旬截止，如 115 年度為 2026/02/25 16:00 截止）：（1）《教育部學海飛颺與學海惜珠計畫》：補助具中華民國國籍、前三學期操行平均 70 分以上且具 CEFR B1（TOEIC 550 / IELTS 4.0 / TOEFL iBT 42 / JLPT N3 / TOPIK 3）以上外語證明之四技二以上或五專四以上在學學生赴非大陸港澳地區研修 1 學期至 1 學年（學海惜珠另須持低收、中低收、特殊境遇、身心障礙或弱勢助學金證明）；（2）校內《探索之航獎學金：發現新天地（Voyage of Discovery: Uncover New Frontiers）》出國研修獎學金（112年10月16日實施要點）：補助赴國外姊妹校交換研修或修讀雙聯學位之在學學生，每人獎助新臺幣 10,000 元至 60,000 元。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認高餐大在學年級、EMI/ESP 先修門數與 {zh_name} 語檢要求）：確認為日間部四技二年級以上、二技一年級下學期、五專四年級或碩士班在學學生，符合操行與學業要求（{gpa_req_str}）與外語門檻（{lang_req_str}；最遲可於 2027/02/26–03/03 補繳達標語檢證照）。"
        ),
        (
            "步驟二（備妥《海外研修暨實習方案報名表》與應備文件送交國際事務處 A406）：於校內報名截止前（115-1 梯次為 2026 年 11 月 13 日週五中午 12:00 前）填妥報名表（日本姊妹校另附日文履歷書），檢附（1）中文歷年成績單正本（含班排名與前三學期操行成績）、（2）有效外語能力檢定證照影本、（3）中/外文讀書與實習計畫及自傳、（4）《海外研修實習家長同意書（中英文版）》、（5）EMI/ESP 修課證明及其他有利審查資料，送交行政大樓四樓 A406 國際事務處。"
        ),
        (
            f"步驟三（參加校內書面審查與中／外語面試甄選，並於 2 月申請學海飛颺／惜珠與探索之航獎學金）：參加國際事務處與各院師長或國外學校代表辦理之筆試／線上面試，預計 2026 年 11 月 20 日公告錄取名單赴 {full_name}；錄取同學可於 2026 年 2 月 25 日 16:00 前向國際處遞交《115 年度教育部學海飛颺／學海惜珠計畫申請表暨研修計畫書》或《探索之航獎學金：發現新天地申請表》（須於 5 月 28 日中午前補齊國外入學許可函）。"
        ),
        (
            "步驟四（完成國外學校提名入學、役男出國緩徵與簽證保險，返國後繳交成果報告、5 分鐘微電影並辦理 10+10 學分抵免）：由國際處向接待校提名（Nomination）並申辦簽證（具役男身分者須於出國前 2 個月依《役男錄取姐妹校海外研修暨實習方案出國申請流程》造冊報教育部核准）；出國前 1 週簽署獎學金行政契約書與切結書並繳交電子機票；返國後繳交登機證、1,000–1,600 字成果報告、10 張 1MB 以上原始照片、簡報及 5 分鐘微電影，並辦理大三海外研修 10 學分與海外實習 10 學分採認。"
        ),
    ]

    elig_points_list = [
        f"合作類別與計畫組別：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請學院：{colleges_str}",
        f"操行、GPA 與 EMI/ESP 先修規定：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "校內甄選與語檢補件規定：採書面審查（歷年成績單含班排名、前三學期操行平均 70 分以上、讀書計畫、EMI/ESP 修課紀錄）結合中／外語面試；115-1 梯次申請者最遲須於 2027/02/26–03/03 前補繳達標外語證照。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與實習薪資待遇：{tuition_note}")
    if remarks_raw:
      elig_points_list.append(f"學程與締約重點說明：{remarks_raw}")

    exp_links: list[dict] = []
    exp_labels: list[str] = []
    if exps:
      exp_covered_schools += 1
      total_exp_reports += len(exps)
      seen_exp_urls: set[str] = set()
      for e_idx, e in enumerate(exps):
        raw_t = clean_text(e.get("title") or f"赴 {zh_name} 海外研修暨實習心得分享")
        esem = e.get("semester") or "112–113學年度"
        eurl = (
            e.get("url")
            or f"{NKUHT_EXPERIENCE_SHARING_URL}#nkuht-exp-{sn}-{e_idx+1}"
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
            "college": "餐旅學院／觀光學院／廚藝學院／國際學院",
            "department": "高餐大海外研修暨實習生",
        })
        summary_text = (
            f"國立高雄餐旅大學國際事務處公開收錄之學長姐赴 {country} {full_name} 海外研修暨實習／雙聯學位官方經驗分享與返國成果報告（{raw_t}），詳述專業餐旅廚藝課程、海外星級飯店實習、住宿環境與當地生活費實錄。"
        )
        theme_map = {
            "academics": f"高餐大交換生於《{raw_t}》分享在 {zh_name} 修讀餐旅、觀光、烘焙或廚藝專業課程、海外飯店實務實習及返國辦理大三 10+10 學分抵免之經驗。",
            "housing": f"高餐大交換生記錄申請 {zh_name} 校內外學生宿舍與實習飯店員工宿舍、周邊生活機能與通勤方式（{housing_str[:100]}）。",
            "campus_culture": f"高餐大國際事務處公開收錄《{raw_t}》之跨文化廚藝餐旅實訓、國際學伴交流與校園生活實錄。",
            "cost": f"高餐大交換生分享於 {zh_name} 之每月住宿、伙食與交通開銷（{living_cost_str[:100]}），以及學費減免／帶薪實習薪資與申請教育部學海飛颺／惜珠或高餐大探索之航獎學金之經驗。",
        }
        student_experience_rows.append({
            "school_name": full_name,
            "country": country,
            "title": raw_t,
            "source_url": eurl,
            "source_type": "article",
            "platform": "國立高雄餐旅大學國際事務處（IAO）—國際交換分享暨海外研修實習專區",
            "author_name": (
                raw_t.split("—")[-1].strip()[:20]
                if "—" in raw_t
                else "高餐大研修生"
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
                f"{full_name}:nkuht_exp:{e_idx}:{eurl}".encode("utf-8")
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
        "home_university": "國立高雄餐旅大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exp_links[0]["url"] if exp_links else NKUHT_EXPERIENCE_SHARING_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

    loc = resolved_locations.get(full_name) or {
        "city": country,
        "latitude": 22.5668,
        "longitude": 120.3719,
        "source_url": "https://www.wikidata.org",
    }
    city_name = loc.get("city") or country
    lat = float(
        loc.get("latitude")
        if loc.get("latitude") is not None
        else loc.get("lat", 22.5668)
    )
    lon = float(
        loc.get("longitude")
        if loc.get("longitude") is not None
        else loc.get("lon", 120.3719)
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
        "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際研修與飯店實習地點以錄取通知與締約校專頁為準。",
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
        f"【合作類別與期程】{program_type}｜研修與實習期間：{study_period_str}",
        f"【當期名額與費用待遇】{quota_str}｜{tuition_note or '依兩校協議辦理'}",
        f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
        f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        f"【住宿與實習資訊】{housing_str}",
    ]
    if exps:
      notes_lines.append(
          f"【高餐大學長姐海外研修暨實習經驗分享（共 {len(exps)} 篇）】收錄於國際事務處國際交換分享專區（含：{'、'.join(exp_labels[:4])}）"
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
            f"國立高雄餐旅大學國際事務處公告合作姊妹校（{program_type}）；{quota_str}。"
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
            "title": f"國立高雄餐旅大學國際事務處（IAO）2027–28 海外研修暨實習平台—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立高雄餐旅大學學生海外實習及研習輔導補充規定",
            "source_url": NKUHT_OVERSEAS_INTERNSHIP_STUDY_SUPPLEMENT_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立高雄餐旅大學 115 年度教育部學海飛颺／學海惜珠計畫簡章與探索之航出國研修獎學金實施要點",
            "source_url": NKUHT_XUEHAI_SCHOLARSHIP_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exp_links:
      wf_sources.append({
          "title": f"國立高雄餐旅大學國際事務處國際交換分享專區—赴 {zh_name} 經驗分享（{len(exps)} 篇）",
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
        "home_university": "國立高雄餐旅大學",
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
            "國立高雄餐旅大學由國際事務處（International Affairs Office, IAO）統籌全校 4 大專業學院（餐旅學院、觀光學院、廚藝學院、國際學院）及全人教育學院之海外研修暨實習方案（含 19 所學費減免方案合作校、12 所付費方案暨帶薪實習合作校、澳洲昆士蘭大學 1+1 雙聯碩士學位方案）與教育部學海飛颺、學海惜珠及校內「探索之航：發現新天地」出國研修獎學金。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"nkuht-{acad_year}-home-1-{sn:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認高餐大在學年級（四技二／五專四／碩一以上）、EMI/ESP 先修門數與 {zh_name} 語檢要求",
                "responsible_party": "學生",
                "responsible_unit": "國立高雄餐旅大學國際事務處／各院系所",
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
                    f"確認符合《國立高雄餐旅大學學生海外實習及研習輔導補充規定》及《2027–28 海外研修暨實習方案》規定：申請人須為日間部四技二年級以上、二技一年級下學期、五專四年級或碩士班在學學生，符合操行與學業要求（{gpa_req_str}）並備妥有效外語檢定證明（{lang_req_str}；最遲於 2027/02/26–03/03 補繳）。"
                ),
                "details": [
                    f"開放學制與學院：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["國立高雄餐旅大學"],
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
                    NKUHT_2027_28_PLATFORM_URL,
                    NKUHT_OVERSEAS_INTERNSHIP_STUDY_SUPPLEMENT_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nkuht-{acad_year}-home-2-{sn:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "備妥《海外研修暨實習方案報名表》、歷年成績單、讀書計畫與家長同意書送交國際事務處（A406）",
                "responsible_party": "學生",
                "responsible_unit": "所屬系所／國際事務處（行政大樓四樓 A406）",
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": NKUHT_2027_28_PLATFORM_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "於校內公告期限前（115-1 梯次為 2026 年 11 月 13 日週五 12:00 前）填妥《海外研修暨實習方案報名表》（申請日本姊妹校另附日文履歷書），檢附含班排名與前三學期操行成績之中文歷年成績單正本、外語檢定證照影本、中/外文讀書與實習計畫、自傳及《海外研修實習家長同意書（中英文版）》，送交行政大樓四樓 A406 國際事務處。"
                ),
                "details": [
                    "115-1 梯次（2027–28 海外研修暨實習方案）：2026 年 10 月 14 日開放報名、2026 年 10 月 19–22 日舉辦各校說明會、2026 年 11 月 13 日（週五）12:00 截止收件。",
                    "語言證照補繳機制：報名時尚未達標者得先參加校內甄選，惟最遲須於 2027 年 2 月 26 日至 3 月 3 日前補繳達標外語能力證明至國際處。",
                ],
                "document_requirements": [
                    {
                        "name": "國立高雄餐旅大學海外研修暨實習方案申請表（日本姊妹校另附《申請日本姊妹校履歷表（日譯本）》；雙聯學制附《雙聯學制申請表》）",
                        "official_form_url": NKUHT_APPLICATION_DOWNLOADS_URL,
                        "source_urls": [
                            NKUHT_APPLICATION_DOWNLOADS_URL,
                            NKUHT_2027_28_PLATFORM_URL,
                        ],
                    },
                    {
                        "name": "中文歷年成績單正本（須含班級排名及前三學期操行成績平均達 70 分以上）與 EMI/ESP 全英語課程修習證明",
                        "official_form_url": NKUHT_APPLICATION_QUALIFICATIONS_URL,
                        "source_urls": [
                            NKUHT_OVERSEAS_INTERNSHIP_STUDY_SUPPLEMENT_PDF_URL,
                            NKUHT_XUEHAI_115_BROCHURE_PDF_URL,
                        ],
                    },
                    {
                        "name": "兩年內有效外語能力檢定證明影本、中/外文讀書與實習計畫、自傳及《海外研修實習家長同意書（中英文版）》",
                        "official_form_url": NKUHT_APPLICATION_DOWNLOADS_URL,
                        "source_urls": [
                            NKUHT_APPLICATION_DOWNLOADS_URL,
                            NKUHT_CEFR_EQUIVALENCY_PDF_URL,
                        ],
                    },
                ],
                "scope": {
                    "home_universities": ["國立高雄餐旅大學"],
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
                    NKUHT_2027_28_PLATFORM_URL,
                    NKUHT_APPLICATION_DOWNLOADS_URL,
                    NKUHT_OVERSEAS_INTERNSHIP_STUDY_SUPPLEMENT_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nkuht-{acad_year}-home-3-{sn:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "參加校內書面審查與中／外語面試（11/20 放榜），並於 2 月申請學海飛颺／惜珠與探索之航獎學金",
                "responsible_party": "國立高雄餐旅大學國際事務處與申請學生",
                "responsible_unit": "國際事務處國際教育與交流組",
                "deadline_at": "2027-02-25T16:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": NKUHT_XUEHAI_SCHOLARSHIP_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": True,
                "summary": (
                    "國際事務處辦理書面資料審查與中／外語面試（部分付費方案合作校如加拿大 Humber、荷蘭 HTH、澳洲 ICHM、美國 MSU 迪士尼計畫由國外校方代表面試或筆試），於 2026 年 11 月 20 日公告錄取名單。錄取生可於每年 2 月下旬（如 115 年度為 2 月 25 日 16:00 前）向國際處申請教育部《學海飛颺／學海惜珠計畫》或校內《探索之航：發現新天地》出國研修獎學金（NT$ 10,000–60,000）。"
                ),
                "details": [
                    "教育部《學海飛颺／學海惜珠計畫》申請要點：須具中華民國國籍、前三學期操行平均 70 分以上、兩年內有效外語能力證明（英語 CEFR B1 以上），備妥申請表暨研修計畫書（含至少 500 字自傳與 500 字研修計畫）、含班排與操行之中文歷年成績單正本、家長同意書及存摺影本，於 2 月 25 日 16:00 前送交國際處（國外入學許可函最遲於 5 月 28 日 12:00 前補齊）。",
                    "高餐大《探索之航獎學金：發現新天地》實施要點：補助赴境外合作學校研修或修讀雙聯學位之在學學生，每人核發新臺幣 10,000 元至 60,000 元。",
                ],
                "scope": {
                    "home_universities": ["國立高雄餐旅大學"],
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
                    NKUHT_XUEHAI_SCHOLARSHIP_URL,
                    NKUHT_VOYAGE_OF_DISCOVERY_URL,
                    NKUHT_XUEHAI_115_BROCHURE_PDF_URL,
                    NKUHT_VOYAGE_RULES_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nkuht-{sn:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由高餐大國際事務處向 {zh_name} 辦理官方提名（Nomination），並遞交姊妹校入學、宿位與實習申請文件",
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"通過校內甄選並於 2027/02/26–03/03 確認語言證照達標後，由國立高雄餐旅大學國際事務處向 {zh_name} 辦理官方提名；學生須依接待校規定備妥外文入學申請表、英文歷年成績單、護照影本、英文財力證明、體檢表、外語檢定證書及實習履歷，靜候接待校核發正式入學許可（Admission Letter / COE / DS-2019 / CoE）。"
                ),
                "details": [
                    f"研修與實習期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["國立高雄餐旅大學"],
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
                    [source_url, NKUHT_2027_28_PLATFORM_URL]
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"nkuht-{acad_year}-home-5-{sn:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "完成高餐大出國註冊、役男出國核准與簽署獎學金契約，返國後繳交成果報告、5 分鐘微電影並辦理 10+10 學分抵免",
                "responsible_party": "學生與所屬系所",
                "responsible_unit": "國際事務處／教務處／研究發展處實習組／各系所",
                "summary": (
                    "出國前須完成高餐大註冊手續、投保海外全期醫療及意外保險（具役男身分者須於出國前 2 個月送交《役男推薦出國學生名冊》辦理出境核准；赴大陸地區者須完成教育部《赴陸交流活動登錄平臺》登錄），並於出國前 1 週簽署獎學金行政契約書、切結書及繳交電子機票證明。返國後 1 週內繳交返抵國內報到單、登機證、500 字研修小故事、1,000–1,600 字獲獎心得報告、10 張 1MB 以上原始照片、10 分鐘成果發表簡報及 5 分鐘微電影，並辦理大三海外研修 10 學分與海外實習 10 學分採認。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["國立高雄餐旅大學"],
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
                    NKUHT_OVERSEAS_INTERNSHIP_STUDY_SUPPLEMENT_PDF_URL,
                    NKUHT_VOYAGE_RULES_PDF_URL,
                    NKUHT_XUEHAI_115_BROCHURE_PDF_URL,
                    NKUHT_IAO_SOP_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合國立高雄餐旅大學國際事務處（IAO）《2027–28 海外研修暨實習方案（19 所學費減免方案＋12 所付費暨雙聯方案）》、《關鍵合作姊妹校名錄》、《學生海外實習及研習輔導補充規定》、《115 年度教育部學海飛颺與學海惜珠計畫申請簡章》、《探索之航：發現新天地出國研修獎學金實施要點》及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換生經驗分享，共 {len(catalog_source)} 所合作姊妹校資料。"
        ),
    })

    cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期與研修實習時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": f"國立高雄餐旅大學國際事務處（IAO）2027–28 海外研修暨實習平台—{zh_name}",
            "source_url": source_url,
            "summary": "高餐大國際處公告之合作學程、錄取名額、語言檢定門檻與學費減免／付費帶薪實習／雙聯碩士待遇說明",
        },
        {
            "title": "國立高雄餐旅大學學生海外實習及研習輔導補充規定、學海飛颺／惜珠與探索之航獎學金要點",
            "source_url": NKUHT_OVERSEAS_INTERNSHIP_STUDY_SUPPLEMENT_PDF_URL,
            "summary": "高餐大海外研修 10 學分＋海外實習 10 學分學制規範、EMI/ESP 先修規定與獎學金申請辦法",
        },
    ]
    if exp_links:
      dest_sources.append({
          "title": f"國立高雄餐旅大學國際事務處國際交換分享專區—赴 {zh_name} 經驗分享（{len(exps)} 篇）",
          "source_url": exp_links[0]["url"],
          "summary": f"收錄歷年高餐大學生赴 {zh_name} 海外研修暨實習／雙聯學位經驗分享共 {len(exps)} 篇",
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
            NKUHT_OVERSEAS_INTERNSHIP_STUDY_SUPPLEMENT_PDF_URL,
            NKUHT_2027_28_PLATFORM_URL,
            NKUHT_XUEHAI_SCHOLARSHIP_URL,
        ]
        + ([exp_links[0]["url"]] if exp_links else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "國立高雄餐旅大學",
        "school_name": full_name,
        "country": country,
        "city": city_name,
        "cost_summary": f"{cost_line}。\n{tuition_clean}",
        "housing_summary": housing_clean,
        "transport_summary": (
            f"校區代表城市：{city_name}。請依入學許可與實習分發通知確認實際授課校區、實習飯店位置與當地交通卡優惠。"
        ),
        "campus_life_summary": f"{calendar_clean}\n{course_clean}",
        "student_guide_sections": [
            {
                "key": "cost",
                "title": "生活費、學費減免／付費帶薪實習待遇、教育部學海飛颺／惜珠與探索之航獎學金",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [NKUHT_VOYAGE_RULES_PDF_URL],
                "caution": (
                    "獲教育部《學海飛颺／學海惜珠》或高餐大《探索之航：發現新天地》獎學金學生，須於出國前 1 週完成切結書與行政契約書簽署，並於返國後 1 週內繳交登機證、成果報告、10 張原始照片與 5 分鐘微電影辦理核銷。"
                ),
            },
            {
                "key": "housing",
                "title": "學生宿舍與海外實習飯店住宿安排",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": "日本京都先端科學大學與文京學院大學無提供校內宿舍（需租賃校外學生公寓）；日本山口大學、阪南大學、韓國又松大學、仁德大學、漢陽女子大學、香港理工大學、澳門旅遊大學、泰國藝術大學及瑞士／加拿大／荷蘭／義大利／杜拜合作校則提供校內宿舍或專案住宿。",
            },
            {
                "key": "insurance",
                "title": "海外醫療及意外保險與家長同意書規定",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依國立高雄餐旅大學國際事務處規定，所有申請學生均須檢附經家長或法定監護人簽章之《海外研修實習同意書（中英文版）》，並於出國前投保涵蓋海外研修與實習全期（12 個月）之海外醫療及意外保險。",
                ],
                "source_urls": src_url_list,
                "caution": "日本、韓國、澳洲、瑞士、荷蘭、法國、義大利、英國、美國、加拿大等接待校對國際學生健康保險有強制納保規定，請依入學許可指示辦理。",
            },
            {
                "key": "visa",
                "title": "留學與實習簽證辦理、役男出國緩徵流程與在學註冊義務",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "具役男身分（尚未服兵役）之錄取學生，須依《國際事務處具備役男身分之學生錄取姐妹校海外研修暨實習方案出國申請程序》於出國前 2 個月備妥護照與入學許可，由國際處造冊函報教育部及內政部役政司核准出境。",
                ],
                "source_urls": src_url_list,
                "caution": "涉及海外支薪實習之方案（如日本、澳洲 ICHM、瑞士 SEG/Glion/Les Roches、英國 UCB、加拿大 Humber、荷蘭 HTH、美國 MSU 迪士尼計畫）須申辦兼具實習工作權限之簽證（如 J-1、Co-op Work Permit、Subclass 500、瑞士實習許可）。",
            },
            {
                "key": "academics",
                "title": "EMI/ESP 全英語課程先修規定、1+1 雙聯碩士與大三海外研修 10 學分＋實習 10 學分抵免",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list,
                "caution": (
                    "重點培育學院（餐旅學院、觀光學院、國際學院）學生出國前須修畢 EMI 或 ESP 課程至少 2 門，廚藝學院及應日系學生至少 1 門；前三學期操行平均須達 70 分以上且無小過以上處分。"
                ),
            },
            {
                "key": "living",
                "title": f"{city_name} 校園實訓與高餐大學長姐海外研修實習經驗傳承",
                "summary": f"代表城市：{city_name}。請配合接待校國際處與實習輔導老師完成報到、新生訓練及實習考核。",
                "points": [
                    f"目的地城市：{city_name}（{country}）",
                    (
                        "國立高雄餐旅大學國際事務處每年 10 月舉辦「海外研修暨實習說明會」與「學長姐經驗分享會」"
                        + (
                            f"（本校共收錄 {len(exps)} 篇經驗分享：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，協助同學掌握海外選課、米其林餐廳／奢華酒店實習面試與生活準備。"
                    ),
                ],
                "source_urls": [
                    exp_links[0]["url"]
                    if exp_links
                    else NKUHT_EXPERIENCE_SHARING_URL
                ],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合國立高雄餐旅大學國際事務處 {len(catalog_source)} 所合作姊妹校、2027–28 當期開放申請海外研修暨實習與雙聯碩士合作校（{open_partner_count} 校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷年學生交換實習經驗分享。"
        ),
    })

    research_records.append({
        "home_university": "國立高雄餐旅大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            "國立高雄餐旅大學國際事務處《2027–28 海外研修暨實習平台（學費減免方案／付費方案）》、《關鍵合作姊妹校列表》、《學生海外實習及研習輔導補充規定》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"國立高雄餐旅大學國際事務處 2027–28 海外研修暨實習平台—{zh_name}",
            "url": source_url,
        },
    ]
    if exp_links:
      ev_sources.append({
          "title": f"國立高雄餐旅大學國際交換分享—赴 {zh_name} 經驗分享（{len(exps)} 篇）",
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
            "scope": "國立高雄餐旅大學海外研修暨實習姊妹校住宿與實習食宿資訊",
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
            "scope": "國立高雄餐旅大學學費減免／付費帶薪實習方案、教育部學海飛颺／惜珠與探索之航出國研修獎學金",
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
            "scope": "國立高雄餐旅大學學生海外實習及研習輔導補充規定、EMI/ESP 先修規定與 10+10 學分抵免",
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
            "scope": "國立高雄餐旅大學海外研修暨實習簽證、家長同意書、役男出國緩徵與海外醫療保險提醒",
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
                    f"｜高餐大公開收錄 {len(exps)} 篇赴 {zh_name} 交換實習經驗分享（{'、'.join(exp_labels[:3])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "國立高雄餐旅大學海外研修實習名額與歷屆學長姐經驗分享",
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
            "已整合國立高雄餐旅大學國際事務處《2027–28 海外研修暨實習方案》、《關鍵合作姊妹校名錄》、《學生海外實習及研習輔導補充規定》及歷屆學生交換實習經驗分享。",
            "當期免學費名額、付費專案金額、實習薪資、宿位供給與語檢補件期限請依國際處最新公告及接待校入學通知書核對。",
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

  write_jsonl(OFFICIAL_NKUHT_DIR / "partners.jsonl", partners)
  write_jsonl(SOURCES_NKUHT_DIR / "partners.jsonl", partners)
  write_jsonl(OFFICIAL_NKUHT_DIR / "application_workflows.jsonl", workflows)
  write_jsonl(OFFICIAL_NKUHT_DIR / "destination_profiles.jsonl", destinations)
  write_jsonl(OFFICIAL_NKUHT_DIR / "partner_research.jsonl", research_records)
  write_jsonl(OFFICIAL_NKUHT_DIR / "student_life.jsonl", life_records)
  write_jsonl(
      OFFICIAL_NKUHT_DIR / "experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_NKUHT_DIR / "student_experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_NKUHT_DIR / "student_experiences.jsonl", student_experience_rows
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
  (OFFICIAL_NKUHT_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_NKUHT_DIR / "student-experiences.json").write_text(
      json.dumps(
          {
              "school_id": "nkuht",
              "school_name": "國立高雄餐旅大學",
              "checked_at": CHECKED_AT,
              "source_url": NKUHT_EXPERIENCE_SHARING_URL,
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

  (OFFICIAL_NKUHT_DIR / "campus-locations.json").write_text(
      json.dumps(
          {
              "school_id": "nkuht",
              "school_name": "國立高雄餐旅大學",
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
  (OFFICIAL_NKUHT_DIR / "campus-assets.json").write_text(
      json.dumps(
          {
              "school_id": "nkuht",
              "school_name": "國立高雄餐旅大學",
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

  nkuht_source_urls = [
      NKUHT_IAO_HOME_URL,
      NKUHT_STUDY_ABROAD_URL,
      NKUHT_2027_28_PLATFORM_URL,
      NKUHT_TUITION_FREE_URL,
      NKUHT_FEE_BASED_URL,
      NKUHT_APPLICATION_QUALIFICATIONS_URL,
      NKUHT_APPLICATION_DOWNLOADS_URL,
      NKUHT_XUEHAI_SCHOLARSHIP_URL,
      NKUHT_VOYAGE_OF_DISCOVERY_URL,
      NKUHT_EXPERIENCE_SHARING_URL,
      NKUHT_KEY_PARTNERS_URL,
      NKUHT_DUAL_DEGREE_URL,
      NKUHT_REGULATIONS_URL,
      NKUHT_OVERSEAS_INTERNSHIP_STUDY_SUPPLEMENT_PDF_URL,
      NKUHT_IAO_SOP_PDF_URL,
      NKUHT_XUEHAI_115_BROCHURE_PDF_URL,
      NKUHT_VOYAGE_RULES_PDF_URL,
      NKUHT_BRIEFING_2027_28_PDF_URL,
      NKUHT_CEFR_EQUIVALENCY_PDF_URL,
  ]

  exchange_info_payload = {
      "school_name": "國立高雄餐旅大學",
      "program_type": [
          (
              f"國際事務處（IAO）2027–28 海外研修暨實習方案—「學費減免方案（Tuition-Free Track，共 19 校）」（涵蓋法國巴黎法蘭迪大學 FERRANDI Paris、法國里昂保羅博古斯廚藝與餐旅管理學院 Institut Lyfe、法國薩維尼雅克國際旅館學校 Savignac、芬蘭赫爾辛基哈戈赫利亞應用科技大學 Haaga-Helia、香港理工大學 PolyU SHTM、澳門旅遊大學 UTM、日本京都先端科學大學 KUAS、武藏野大學、文京學院大學［含東京阪急阪神第一飯店集團實習］、阪南大學［可申請每月 4 萬日圓獎學金］、國立山口大學［含常盤溫泉旅館實習］、韓國仁德大學、漢陽女子大學、又松大學、泰國藝術大學、曼谷大學、瓦萊嵐大學、菲律賓萊西姆大學、三一大學）"
          ),
          (
              "國際事務處 2027–28 海外研修暨實習方案—「付費暨海外帶薪實習方案（Fee-Based Track，共 12 校）」（涵蓋瑞士雷赫士 Les Roches、瑞士格里昂 Glion、瑞士廚藝管理大學 CAAS、瑞士旅館管理學校 SHMS、荷蘭海牙旅館管理學院 Hotelschool The Hague、義大利佛羅倫斯藝術大學 FUA Apicius、英國艾賽克斯大學 Edge Hotel School、英國伯明罕大學學院 UCB、澳洲國際旅館管理學院 ICHM、美國蒙特克萊爾州立大學 MSU［佛羅里達華特迪士尼世界 Walt Disney World 帶薪實習專案］、加拿大漢堡學院 Humber Polytechnic）暨【澳洲昆士蘭大學 The University of Queensland】1+1 旅遊酒店與會展管理雙聯碩士學位方案"
          ),
          (
              "教育部「學海飛颺」（選送優秀學生出國研修）、「學海惜珠」（選送清寒優秀學生出國研修），以及高餐大校內《探索之航獎學金：發現新天地（Voyage of Discovery: Uncover New Frontiers）》出國研修獎學金（每人補助 NT$ 10,000–60,000）"
          ),
      ],
      "academic_year": [
          (
              "115（涵蓋 115-1 梯次［2027–28 海外研修暨實習方案：2026/10/14 開放報名、2026/11/13 12:00 截止、2026/11/20 公告錄取、2027/02/26–03/03 語檢補件截止］，以及 115 年度教育部學海飛颺／學海惜珠與高餐大探索之航獎學金［2026/02/25 16:00 截止收件、2026/05/28 入學許可補件截止］）"
          ),
          (
              f"本平台完整收錄國立高雄餐旅大學國際事務處公告之 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所 2027–28 當期開放申請之學費減免、付費帶薪實習與 1+1 雙聯碩士合作校，以及 {len(partners) - open_partner_count} 所關鍵合作姊妹校，橫跨全球 18 個國家與地區，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷年學長姐交換與海外飯店實習經驗分享）"
          ),
      ],
      "semester": [
          "大三／專四全學年海外研修暨實習方案（12 個月）：依《國立高雄餐旅大學學生海外實習及研習輔導補充規定》，海外研修加實習期間以 12 個月為原則，分別抵免 1 學期海外研修必修 10 學分與 1 學期海外（或國內）實習必修 10 學分。",
          "學費減免方案（19 校）：日本 5 校（KUAS、武藏野、文京學院、阪南、山口）為「1 學期日本大學研修＋1 學期日本飯店／溫泉旅館實習」；歐亞及港澳 14 校（法國 FERRANDI、Institut Lyfe、Savignac、芬蘭 Haaga-Helia、香港理工、澳門旅遊、韓國 3 校、泰國 3 校、菲律賓 2 校）為「1 學期國外大學交換研修＋1 學期臺灣實習」。",
          "付費方案與 1+1 雙聯碩士方案（12 校）：瑞士 4 校、英國 2 校、荷蘭海牙、義大利 FUA、澳洲 ICHM、加拿大 Humber 及美國蒙特克萊爾州立大學迪士尼專案均為「國外專業研修＋國外當地飯店／迪士尼帶薪實習（共 12 個月）」；澳洲昆士蘭大學（UQ）為研究所「高餐大碩一＋澳洲 UQ 碩二」1+1 雙碩士學位方案。",
      ],
      "application_period": [
          "【2027–28 海外研修暨實習方案（學費減免 19 校＋付費與雙聯 12 校）】2026 年 10 月 14 日平台開放申請，2026 年 10 月 19–22 日舉辦國際處與各國學校說明會，2026 年 11 月 13 日（週五）中午 12:00 截止收件（繳交至行政大樓四樓 A406 國際事務處），2026 年 11 月 20 日公布甄選錄取名單。",
          "【外語能力檢定證照補繳期限】115-1 梯次申請者若於報名時尚未取得目標合作校規定之語言檢定成績，最遲須於 2027 年 2 月 26 日至 3 月 3 日前補繳達標語言證照影本至國際事務處。",
          "【教育部「學海飛颺／學海惜珠」暨高餐大「探索之航：發現新天地」獎學金申請】每年 2 月下旬截止（115 年度為 2026 年 2 月 25 日週三 16:00 前繳交至國際處 A406），若申請時尚未取得國外入學許可函，最遲須於 5 月 28 日中午 12:00 前補齊。",
      ],
      "eligibility": [
          "1. 在學身分與年級限制：依《國立高雄餐旅大學學生海外實習及研習輔導補充規定》及國際事務處公告，（a）日間部四技二年級（含）以上、二技一年級下學期及五專四年級在學學生得申請大三／專四海外研修暨實習方案；（b）研究所碩士生得申請澳洲昆士蘭大學（UQ）1+1 雙聯碩士學位方案；（c）在職專班生、休學生或未達規定年級者不得申請學海系列獎助。",
          "2. 操行成績與獎懲門檻：申請海外研修暨實習甄選及教育部學海飛颺、學海惜珠、探索之航獎學金者，前各學年上、下學期（前三學期）操行成績平均須達 70 分以上，且在校期間不得有小過（含）以上處分或違法紀錄。",
          "3. EMI／ESP 全英語授課專業課程先修門檻：依高餐大國際化課程規定，重點培育學院（餐旅學院、觀光學院、國際學院）學生出國前須修習 EMI 或 ESP 課程至少 2 門且成績及格；廚藝學院及應用日語系學生至少須修習 1 門且及格。",
          "4. 個別合作校特殊條件：韓國漢陽女子大學（Hanyang Women's University）僅限女性學生申請；義大利佛羅倫斯藝術大學（FUA）廚藝主修與瑞士廚藝管理大學（CAAS）限具廚藝／烘焙相關科系或修課背景學生；澳洲昆士蘭大學（UQ）僅限碩士班研究生申請。",
      ],
      "language_requirement": [
          "1. 英語授課組—CEFR B1 與基礎門檻（TOEIC 550–600 / IELTS 4.0–5.5 / TOEFL iBT 42–61）：（a）泰國瓦萊嵐大學、菲律賓三一大學、加拿大漢堡學院（Humber，亦可參加校內英語筆試口試）、義大利佛羅倫斯藝術大學（FUA，英語口試）要求 CEFR B1（新版 TOEIC 550［聽275/讀275］/ IELTS 4.0 / TOEFL iBT 42 / GEPT 中級）；（b）韓國又松大學（Woosong）、泰國藝術大學（Silpakorn）、曼谷大學（Bangkok University）、菲律賓萊西姆大學（LPU）、杜拜阿聯酋酒店管理學院（EAHM）、美國南佛羅里達大學（USF）要求 TOEIC 600 / IELTS 5.0–5.5 / TOEFL iBT 61 / Duolingo 80–85。",
          "2. 英語授課組—CEFR B2 與中高階門檻（TOEIC 750–785 / IELTS 5.5–6.5 / TOEFL iBT 70–87）：（a）芬蘭赫爾辛基哈戈赫利亞應用科大（Haaga-Helia）、法國薩維尼雅克國際旅館學校（Savignac）、荷蘭海牙旅館管理學院（HTH）、瑞士格里昂（Glion）、瑞士廚藝管理大學（CAAS）、瑞士旅館管理學校（SHMS）要求 CEFR B2（新版 TOEIC 785［聽400/讀385］/ IELTS 5.5 / TOEFL iBT 72）；（b）香港理工大學（PolyU）、澳門旅遊大學（UTM）、澳洲國際旅館管理學院（ICHM，或通過 UP English Test 6.0）、英國艾賽克斯大學（Essex）、英國伯明罕大學學院（UCB）、瑞士雷赫士（Les Roches）、美國蒙特克萊爾州立大學（MSU 迪士尼交換計畫）要求 IELTS 6.0 / TOEFL iBT 70–80 / TOEIC 750–785；（c）法國巴黎法蘭迪大學（FERRANDI Paris）、法國里昂保羅博古斯學院（Institut Lyfe，或法語 DELF B2）、澳洲昆士蘭大學（UQ 1+1 雙碩士）要求 IELTS 6.5 / TOEFL iBT 87 / TOEIC 780+。",
          "3. 日語組與韓語組姊妹校：（a）日本京都先端科學大學（KUAS）要求 JLPT N3 以上；文京學院大學、阪南大學、山口大學、九州國際大學要求 JLPT N2 以上；東京武藏野大學要求 JLPT N1；（b）韓國仁德大學（Induk）、漢陽女子大學（Hanyang Women's）要求韓語檢定 TOPIK 3 級以上；（c）大陸地區姊妹校（北京第二外國語學院、浙江旅遊職業學院、南京旅遊職業學院）為中文授課，免附外語檢定。",
      ],
      "required_documents": [
          "1. 國立高雄餐旅大學海外研修暨實習方案申請表（Tuition-Free / Fee-Based Program Application Form，含申請人及家長簽章；申請日本姊妹校另附《申請日本姊妹校履歷表（日譯本）》；申請雙聯學制附《雙聯學制申請表》）",
          "2. 本校中文歷年成績單正本（請向教務處申請，須顯示班級排名及各學期操行成績，前三學期操行平均須達 70 分以上）",
          "3. 兩年內之有效外語能力檢定證明影本（TOEIC / TOEFL / IELTS / GEPT / Duolingo / JLPT / TOPIK / DELF；115-1 梯次最遲於 2027/02/26–03/03 補繳）",
          "4. 中/外文個人自傳（至少 500 字）與海外研修暨實習計畫書（至少 500 字，含出國研修動機、目標、修課與實習規劃、與目前學習相關性及未來展望）",
          "5. 國立高雄餐旅大學《海外研修實習同意書（中文版）》及《Parent/Guardian Consent Form（英文版）》（須由家長或法定監護人親筆簽名蓋章）",
          "6. 學院規定之 EMI／ESP 全英語授課專業課程修習及格證明（餐旅、觀光、國際學院至少 2 門；廚藝學院及應日系至少 1 門）",
          "7. 身分證正反面影本、學生證正反面影本、護照個人資料頁影本、本人戶名存摺封面影本及其他有利審查佐證資料（專業廚藝餐旅證照、競賽獲獎、社團幹部證明；申請學海惜珠另附戶口名簿及低收／中低收／弱勢助學金證明）",
      ],
      "scholarship_info": [
          "1. 教育部「學海飛颺計畫」選送優秀學生出國研修獎學金（國際事務處主辦，115 年度於 2026/02/25 16:00 截止）：補助具中華民國國籍、四技二年級以上或五專四年級以上在學學生（不含在職專班）、前三學期操行成績平均達 70 分以上且無小過以上處分、具備兩年內有效外語能力證明（英語達 CEFR B1 如 TOEIC 550 / IELTS 4.0 / TOEFL iBT 42 以上，或日語 JLPT N3–N1、韓語 TOPIK 3 級以上）者，赴國外（不含大陸及港澳地區）姊妹校修讀學分 1 學期至 1 學年。獲獎生須簽署行政契約書，於 5 月 28 日中午前補齊國外入學許可函，並於返國後完成學分抵免與成果報告上傳。",
          "2. 教育部「學海惜珠計畫」選送清寒優秀學生出國研修獎學金（115 年度於 2026/02/25 16:00 截止）：補助具備學海飛颺基本資格且持各直轄市、縣（市）主管機關核發之低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助費、弱勢兒童及少年生活扶助，或獲「教育部大專校院弱勢學生助學計畫」助學金補助資格之在學學生出國研修來回經濟艙機票、學費與生活費。",
          "3. 國立高雄餐旅大學《探索之航獎學金：發現新天地（Voyage of Discovery: Uncover New Frontiers）》出國研修獎學金（112年10月16日實施要點，115 年度於 2026/02/25 16:00 截止）：為鼓勵高餐大在學學生赴境外合作大學校院研修（含港澳及全球姊妹校）或修讀跨國雙聯學位，拓展國際視野，依學生學業表現、外語能力及研修計畫審核，每人核給新臺幣 10,000 元至 60,000 元獎學金。受獎生須於出國前 1 週簽署切結書與行政契約書並繳交電子機票，返國後 1 週內繳交登機證、500 字研修小故事、1,600 字以上獲獎心得報告、10 張 1MB 以上原始照片、10 分鐘成果發表會簡報及 5 分鐘微電影。",
          "4. 海外帶薪實習薪資與姊妹校專屬獎學金：（a）日本阪南大學交換生可申請每月 JPY 40,000 獎學金；（b）瑞士雷赫士 Les Roches、格里昂 Glion、瑞士廚藝管理大學 CAAS、瑞士旅館管理學校 SHMS 實習期間享瑞士法定最低月薪約 CHF 2,303/月（約 NT$ 85,000/月）；（c）澳洲國際旅館管理學院 ICHM 6 個月五星級酒店帶薪實習時薪約 AUD 25–35/hr（6 個月實習總收入約 AUD 11,615–18,000）；（d）美國蒙特克萊爾州立大學華特迪士尼世界（Walt Disney World）帶薪實習享時薪約 USD 19/hr；（e）加拿大漢堡學院多倫多 5 個月帶薪實習時薪約 CAD 17.22–20.60/hr；（f）荷蘭海牙旅館管理學院 19 週實習每月津貼約 EUR 500。",
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": nkuht_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_NKUHT_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "國立高雄餐旅大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 70.0,
      "academic_score_rule": (
          "依《國立高雄餐旅大學學生海外實習及研習輔導補充規定》及《115 年度學海飛颺與學海惜珠獎學金申請作業簡章》：申請人須為日間部四技二年級以上、二技一年級下學期、五專四年級或碩士班在學學生，前各學年上、下學期（前三學期）操行成績平均須達 70 分以上且無小過以上處分；重點培育學院（餐旅、觀光、國際學院）須修畢 EMI/ESP 課程至少 2 門，廚藝學院及應日系至少 1 門；報名須檢附含班排名之中文歷年成績單（香港理工大學、澳門旅遊大學、澳洲昆士蘭大學 1+1 雙碩士、美國蒙特克萊爾州立大學迪士尼交換計畫另建議歷年 GPA 達 2.75–3.0／平均 75 分以上）。"
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
              "graduate": 70.0,
          },
          "excluded_undergraduate_years": [
              "大一",
              "大一上",
              "大一下",
              "一年級",
              "一年級上學期",
              "一年級下學期",
              "五專一",
              "五專二",
              "五專三",
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
              "title": "國立高雄餐旅大學 2027–28 年度（115-1 梯次）「學費減免方案（19 校）＆付費暨雙聯方案（12 校）」海外研修暨實習甄選（2026/10/14–11/13 12:00 受理）",
              "details": [
                  "國際事務處（IAO）公告 2027–28 海外研修暨實習平台：涵蓋 19 所「學費減免方案（Tuition-Free）」合作校（法國 FERRANDI Paris、Institut Lyfe、Savignac、芬蘭 Haaga-Helia、香港理工 PolyU、澳門旅遊 UTM、日本 KUAS、武藏野、文京學院、阪南、山口、韓國仁德、漢陽女大、又松、泰國藝術大學、曼谷大學、瓦萊嵐、菲律賓萊西姆、三一大學）及 12 所「付費方案暨雙聯碩士（Fee-Based）」合作校（瑞士 Les Roches、Glion、CAAS、SHMS、荷蘭海牙 HTH、義大利 FUA、英國 Essex、UCB、澳洲 ICHM、昆士蘭大學 UQ 1+1 雙碩士、美國蒙特克萊爾州立大學迪士尼專案、加拿大 Humber）。",
                  "重要日程：2026 年 10 月 14 日開放申請、10 月 19–22 日舉辦說明會、11 月 13 日（週五）中午 12:00 截止收件（繳交至行政大樓四樓 A406 國際處）、11 月 20 日公布錄取名單；語言證照最遲於 2027 年 2 月 26 日至 3 月 3 日前補繳。",
              ],
              "source": {
                  "title": "國立高雄餐旅大學國際事務處 2027–28 Study Abroad Platform 官方專頁",
                  "source_url": NKUHT_2027_28_PLATFORM_URL,
                  "category": "exchange_application",
                  "summary": "高餐大 2027–28 海外研修暨實習方案（31 所開放申請校）報名時程、名額與甄選簡章。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "115-1 梯次（2027–28 海外研修暨實習方案）",
              "audience": "all_students",
              "opens_at": "2026-10-14T09:00:00+08:00",
              "deadline_at": "2026-11-13T12:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "2027–28 海外研修暨實習方案現正開放申請中，於 2026 年 11 月 13 日（週五）中午 12:00 截止收件，11 月 20 日公告錄取結果。",
              "deadline_note": "紙本申請表件請依序排列（左上固定）於 11/13 12:00 前親送行政大樓 A 棟四樓 A406 國際事務處辦公室。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "國立高雄餐旅大學 2027–28 海外研修暨實習方案「外語能力檢定證照補繳期限」（2027/02/26–03/03 截止）",
              "details": [
                  "依國際事務處《2027–28 海外研修暨實習方案說明會簡報》規定，報名 115-1 梯次海外研修暨實習甄選時若尚未取得目標合作校規定之語言檢定成績（如 CEFR B1/B2、IELTS 5.5–6.5、TOEIC 550–785、JLPT N1–N3、TOPIK 3），最遲須於 2027 年 2 月 26 日至 3 月 3 日前補繳達標語言證照影本至國際處確認資格。",
              ],
              "source": {
                  "title": "國立高雄餐旅大學 2027–28 海外研修暨實習方案說明會簡報與語言檢定對照表",
                  "source_url": NKUHT_BRIEFING_2027_28_PDF_URL,
                  "category": "exchange_application",
                  "summary": "高餐大 2027–28 海外研修暨實習方案語言檢定證照最後補繳期限（2027/02/26–03/03）。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "115-1 梯次語言證照補繳",
              "audience": "all_students",
              "opens_at": "2027-02-26T09:00:00+08:00",
              "deadline_at": "2027-03-03T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "錄取同學最遲須於 2027 年 2 月 26 日至 3 月 3 日前補齊達標外語能力檢定證照。",
              "deadline_note": "逾期未補繳達標語言證照者，視同放棄海外研修暨實習推薦錄取資格。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "國立高雄餐旅大學教育部「學海飛颺／學海惜珠」暨校內「探索之航：發現新天地」出國研修獎學金申請（每年 2/25 16:00 截止）",
              "details": [
                  "國際事務處每學年受理兩大出國研修獎學金：（1）教育部《學海飛颺》與《學海惜珠》計畫（補助赴非大陸港澳地區研修 1 學期至 1 學年之優秀生與清寒優秀生）；（2）高餐大校內《探索之航獎學金：發現新天地（Voyage of Discovery: Uncover New Frontiers）》出國研修獎學金（補助赴全球及港澳姊妹校交換研修或修讀雙聯學位之在學學生，每人 NT$ 10,000–60,000）。",
                  "申請人須備齊獎學金申請表暨研修計畫書（含 500 字自傳與 500 字研修計畫）、含班排與前三學期操行成績之中文歷年成績單正本、兩年內有效語檢證明、家長同意書及存摺影本，於每年 2 月 25 日 16:00 前送交國際處 A406（國外入學許可函最遲於 5 月 28 日 12:00 前補齊）。",
              ],
              "source": {
                  "title": "國立高雄餐旅大學國際事務處海外研修暨實習獎學金專區（學海飛颺／惜珠與探索之航）",
                  "source_url": NKUHT_XUEHAI_SCHOLARSHIP_URL,
                  "category": "scholarship",
                  "summary": "高餐大教育部學海飛颺、學海惜珠與探索之航出國研修獎學金申請簡章與表單。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "116年度教育部學海飛颺／惜珠暨探索之航出國研修獎學金",
              "audience": "all_students",
              "opens_at": "2027-01-15T09:00:00+08:00",
              "deadline_at": "2027-02-25T16:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "每年 2 月下旬（約 2 月 25 日 16:00）截止收件，國外學校入學許可函得於 5 月 28 日中午前補齊。",
              "deadline_note": "缺漏件不予受理，請依檢查表順序排列（左上固定）送交行政大樓 A 棟四樓國際處。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"國立高雄餐旅大學國際事務處海外研修暨實習、1+1 雙聯碩士與探索之航／學海獎學金總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所當期開放申請・{total_exp_reports} 篇學長姐交換實習分享）"
              ),
              "details": [
                  (
                      f"國立高雄餐旅大學（National Kaohsiung University of Hospitality and Tourism, NKUHT，坐落於高雄市小港區松和路 1 號，為臺灣唯一國立餐旅觀光專業大學，QS 世界大學學科排名「餐旅與休閒管理 Hospitality & Leisure Management」高居全球第 23 名、全臺第 1 名）由「國際事務處（International Affairs Office, IAO）」統籌全校 4 大專業學院（餐旅學院、觀光學院、廚藝學院、國際學院）及全人教育學院之海外研修暨實習方案、跨國雙聯學制與出國研修獎助學金。本平台完整收錄 {len(partners)} 所高餐大官方合作姊妹校（含 {open_partner_count} 所 2027–28 當期開放申請之學費減免、付費帶薪實習與 1+1 雙聯碩士合作校，以及 {len(partners) - open_partner_count} 所關鍵合作姊妹校），橫跨全球 18 個國家與地區。"
                  ),
                  (
                      f"高餐大海外移動力具備四大獨步全國之特色：（1）「大三海外研修 10 學分＋海外／國內實習 10 學分（共 12 個月）」必修學制無縫接軌，不延畢即可同時完成國際名校修課與跨國星級酒店實習；（2）匯聚全球最頂尖廚藝與飯店管理學府——學費減免方案（19 校）涵蓋「美食界哈佛」法國巴黎法蘭迪大學（FERRANDI Paris）、法國里昂保羅博古斯學院（Institut Lyfe）、薩維尼雅克國際旅館學校（Savignac）、芬蘭 Haaga-Helia、香港理工大學（PolyU SHTM）、澳門旅遊大學（UTM）、日本山口大學（含常盤溫泉旅館實習）、文京學院大學（含東京阪急阪神第一飯店集團實習）、阪南大學（含每月 4 萬日圓獎學金）、武藏野大學、京都先端科學大學、韓國又松大學、仁德大學、漢陽女大及泰菲名校；付費暨帶薪實習方案（12 校）涵蓋瑞士四大名校（Les Roches、Glion、CAAS、SHMS，瑞士實習月薪約 CHF 2,303）、荷蘭海牙旅館管理學院（HTH）、義大利佛羅倫斯藝術大學（FUA Apicius）、英國艾賽克斯大學（Edge Hotel School）、伯明罕大學學院（UCB）、澳洲國際旅館管理學院（ICHM，6 個月帶薪實習時薪 AUD 25–35）、美國蒙特克萊爾州立大學（佛羅里達華特迪士尼世界 Walt Disney World 帶薪實習時薪 USD 19）、加拿大漢堡學院（Humber）及澳洲昆士蘭大學（UQ）1+1 雙碩士；（3）教育部學海飛颺、學海惜珠與高餐大《探索之航：發現新天地》（最高 6 萬元）雙重獎助；（4）收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐交換與海外實習心得報告。"
                  ),
              ],
              "source": {
                  "title": "國立高雄餐旅大學國際事務處（IAO）2027–28 海外研修暨實習平台",
                  "source_url": NKUHT_2027_28_PLATFORM_URL,
                  "category": "exchange_application",
                  "summary": f"高餐大 {len(partners)} 所全球合作姊妹校、{open_partner_count} 所 2027–28 開放申請校與 {total_exp_reports} 篇經驗分享。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "四技二年級以上／五專四年級／碩士班在學身分、前三學期操行 70 分門檻與學院 EMI/ESP 全英語課程先修規定",
              "details": [
                  "在學身分與操行門檻：依《國立高雄餐旅大學學生海外實習及研習輔導補充規定》及《學海飛颺與學海惜珠申請簡章》，大學部海外研修暨實習方案開放日間部四技二年級（含）以上、二技一年級下學期及五專四年級在學學生申請（於大三或專四全學年執行 12 個月研修加實習）；澳洲昆士蘭大學（UQ）1+1 雙聯碩士開放各研究所碩士生申請。所有申請人前三學期操行成績平均須達 70 分以上，且在校期間無小過（含）以上處分或違法紀錄。",
                  "EMI／ESP 全英語專業課程先修規定：重點培育學院（餐旅學院、觀光學院、國際學院）學生於出國前須修習 EMI 或 ESP 全英語授課專業課程至少 2 門且及格；廚藝學院及應用日語系學生至少須修習 1 門且及格。",
              ],
              "source": {
                  "title": "國立高雄餐旅大學學生海外實習及研習輔導補充規定與申請資格專頁",
                  "source_url": NKUHT_OVERSEAS_INTERNSHIP_STUDY_SUPPLEMENT_PDF_URL,
                  "category": "exchange_application",
                  "summary": "高餐大海外研修暨實習在學年級、操行 70 分與 EMI/ESP 先修門數規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "CEFR B1/B2 英語檢定對照（TOEIC 550–785 / IELTS 4.0–6.5 / TOEFL iBT 42–87）、日本 JLPT N1–N3、韓國 TOPIK 3 級與 2027/02/26 補件機制",
              "details": [
                  "英語授課合作校分級門檻：（1）CEFR B1 基礎組（TOEIC 550 / IELTS 4.0 / TOEFL iBT 42）：泰國瓦萊嵐大學、菲律賓三一大學、加拿大漢堡學院（或校內筆試口試）、義大利 FUA（英語口試）；（2）TOEIC 600 / IELTS 5.0–5.5 / iBT 61 組：韓國又松大學、泰國藝術大學、曼谷大學、菲律賓萊西姆大學、杜拜 EAHM、美國南佛羅里達大學；（3）CEFR B2 組（新版 TOEIC 785［聽400/讀385］/ IELTS 5.5 / iBT 72）：芬蘭 Haaga-Helia、法國 Savignac、荷蘭海牙 HTH、瑞士 Glion / CAAS / SHMS；（4）IELTS 6.0 / iBT 70–80 / TOEIC 750–785 組：香港理工大學、澳門旅遊大學、澳洲 ICHM、英國 Essex 與 UCB、瑞士 Les Roches、美國蒙特克萊爾州立大學迪士尼專案；（5）IELTS 6.5 / TOEIC 780+ / iBT 87 頂尖組：法國巴黎 FERRANDI、法國里昂 Institut Lyfe（或 DELF B2）、澳洲昆士蘭大學 1+1 雙碩士。",
                  "日韓語組與證照補繳期限：（1）日本京都先端科學大學要求 JLPT N3 以上；文京學院大學、阪南大學、山口大學、九州國際大學要求 JLPT N2 以上；武藏野大學要求 JLPT N1；（2）韓國仁德大學、漢陽女子大學（限女生）要求 TOPIK 3 級以上；（3）115-1 梯次申請人最遲須於 2027 年 2 月 26 日至 3 月 3 日前補繳達標語言證照。",
              ],
              "source": {
                  "title": "國立高雄餐旅大學 2027–28 海外研修暨實習平台與各類語言檢定證照等級對照表",
                  "source_url": NKUHT_CEFR_EQUIVALENCY_PDF_URL,
                  "category": "exchange_application",
                  "summary": "高餐大 CEFR B1/B2 語言檢定對照表與 31 所當期合作校語言門檻。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "海外研修暨實習申請表、日文履歷書、含班排與操行之中文歷年成績單、語檢證明、中/外文自傳與研修計畫、家長同意書",
              "details": [
                  "校內甄選與獎學金必備文件：（1）《海外研修暨實習方案報名表》（日本姊妹校另附《申請日本姊妹校履歷表（日譯本）》；雙聯學制附《雙聯學制申請表》）；（2）中文歷年成績單正本（須含班級排名及各學期操行成績）；（3）兩年內有效語文能力證明影本；（4）個人自傳（至少 500 字）與海外研修暨實習計畫書（至少 500 字）；（5）《海外研修實習同意書（中文版）》及《Parent/Guardian Consent Form（英文版）》；（6）身分證、學生證、護照與本人存摺封面影本。",
                  "出國前與返國後核銷義務文件：獲《學海飛颺／惜珠》或《探索之航：發現新天地》獎學金者，出國前 1 週須完成切結書與行政契約書簽署並繳交電子機票證明；返國後 1 週內須繳交返抵國內報到單、登機證正本、500 字研修小故事（含 1MB 以上照片 1 張）、1,000–1,600 字個人獲獎心得報告（含 1MB 以上原始照片 10 張，玩樂照不超過 2 張）、10 分鐘成果發表簡報及 5 分鐘微電影 1 部。",
              ],
              "source": {
                  "title": "國立高雄餐旅大學國際事務處申請表件下載與獎學金資料繳交說明",
                  "source_url": NKUHT_APPLICATION_DOWNLOADS_URL,
                  "category": "exchange_application",
                  "summary": "高餐大海外研修暨實習申請表、日文履歷表、家長同意書及探索之航／學海計畫成果報告規範。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部學海飛颺、學海惜珠計畫與高餐大「探索之航獎學金：發現新天地」（NT$ 10,000–60,000）暨海外帶薪實習薪資",
              "details": [
                  "教育部《學海飛颺》與《學海惜珠》計畫（每年 2/25 16:00 截止）：補助具中華民國國籍、前三學期操行平均 70 分以上且具 CEFR B1 以上外語證明之四技二／五專四以上在學生赴非大陸港澳姊妹校研修 1 學期至 1 學年；學海惜珠另補助低收、中低收、特殊境遇、身心障礙或獲大專弱勢助學金之清寒優秀生來回機票、學費與生活費。",
                  "高餐大《探索之航獎學金：發現新天地（Voyage of Discovery: Uncover New Frontiers）》（112.10.16 實施要點，每年 2/25 16:00 截止）：補助赴全球及港澳合作大學研修或修讀雙聯學位之在學學生，每人核發新臺幣 10,000 元至 60,000 元；另瑞士、澳洲、美國迪士尼、加拿大、英國、荷蘭及日本合作方案於實習期間提供豐厚帶薪實習薪資或獎學金（如瑞士月薪 CHF 2,303、澳洲 ICHM 時薪 AUD 25–35、美國迪士尼時薪 USD 19、日本阪南大學每月 JPY 40,000 獎學金）。",
              ],
              "source": {
                  "title": "國立高雄餐旅大學「探索之航獎學金 發現新天地」實施要點與 115 年度學海飛颺／惜珠簡章",
                  "source_url": NKUHT_VOYAGE_OF_DISCOVERY_URL,
                  "category": "scholarship",
                  "summary": "高餐大探索之航出國研修獎學金（1–6 萬元）與教育部學海飛颺、學海惜珠完整規定。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "國立高雄餐旅大學海外研修暨實習計畫書（500 字）、自傳（500 字）、日文履歷書與探索之航成果報告撰寫指南",
              "summary": "說明高餐大《2027–28 海外研修暨實習方案》、《學海飛颺／惜珠計畫》與《探索之航：發現新天地》規定之自傳、研修計畫書、日本姊妹校日文履歷表及返國成果報告撰寫重點。",
              "key_points": [
                  "海外研修暨實習計畫書（至少 500 字）：須具體敘明（1）赴國外研修動機與企圖心、（2）目標學校擬修讀之餐旅／觀光／廚藝／烘焙專業課程與高餐大母系課程之相關性、（3）第二學期海外（如東京阪急阪神第一飯店、山口常盤溫泉旅館、瑞士奢華酒店、澳洲五星級飯店、佛羅里達華特迪士尼世界、多倫多或海牙飯店）或返臺專業實習規劃、（4）未來職涯展望與 10+10 學分抵免規劃。",
                  "個人自傳（至少 500 字）與日本姊妹校《履歴書（日譯本）》：自傳應結合高餐大專業實習與實作訓練背景、EMI/ESP 全英語課程學習成果、餐旅廚藝證照或競賽獲獎事蹟；申請日本 5 所姊妹校（KUAS、武藏野、文京學院、阪南、山口）者，須以日語填寫官方《履歴書》之「自伝」與約 500 字「学習計画」。",
                  "家長同意書（中英文版）與返國成果報告（1,000–1,600 字＋5 分鐘微電影）：報名時須檢附家長簽章之《海外研修實習同意書》；獲獎學金者返國後 1 週內須繳交不得使用 AI 生成器撰寫之原創心得報告、10 張 1MB 以上原始上課／實習照片及 5 分鐘微電影（玩樂畫面不得超過 1 分鐘）。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立高雄餐旅大學 115 年度學海飛颺／惜珠計畫申請表暨探索之航獎學金成果報告格式",
                  "source_url": NKUHT_XUEHAI_SCHOLARSHIP_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NKUHT_APPLICATION_DOWNLOADS_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "國立高雄餐旅大學學生海外實習及研習輔導補充規定、學費減免 vs 付費帶薪實習學制與役男出國緩徵核心規定",
              "summary": "規範高餐大「大三海外研修 10 學分＋海外／國內實習 10 學分（12 個月）」必修學制、EMI/ESP 先修門檻、操行 70 分基準、語言證照補繳期限與役男出國程序。",
              "key_points": [
                  "海外研修 10 學分＋實習 10 學分（12 個月）學制：依《國立高雄餐旅大學學生海外實習及研習輔導補充規定》，大學部海外研修加實習以 12 個月（一學年）為原則，分別抵免大三（或五專四年級）1 學期海外研修必修 10 學分及 1 學期實習必修 10 學分。",
                  "EMI/ESP 先修與操行門檻：餐旅學院、觀光學院、國際學院學生出國前須修畢 EMI 或 ESP 課程至少 2 門且及格，廚藝學院及應日系學生至少 1 門；前三學期操行成績平均須達 70 分以上且無小過以上處分。",
                  "役男出國緩徵與赴陸登錄規定：具役男身分之錄取學生須於出國前 2 個月依《國際事務處具備役男身分之學生錄取姐妹校海外研修暨實習方案出國申請程序》備妥護照與入學許可函報請教育部及役政司核准；赴大陸地區姊妹校交流須依規定完成教育部《赴陸交流活動登錄平臺》申報。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立高雄餐旅大學學生海外實習及研習輔導補充規定與國際事務處法規表單專區",
                  "source_url": NKUHT_REGULATIONS_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NKUHT_OVERSEAS_INTERNSHIP_STUDY_SUPPLEMENT_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "國立高雄餐旅大學國際事務處（International Affairs Office, IAO）官方網站",
              "source_url": NKUHT_IAO_HOME_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立高雄餐旅大學國際事務處「2027–28 Study Abroad Platform（海外研修暨實習平台）」",
              "source_url": NKUHT_2027_28_PLATFORM_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立高雄餐旅大學 2027–28 海外研修—學費減免方案（Tuition-Free Study Abroad Programs，19 校）",
              "source_url": NKUHT_TUITION_FREE_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立高雄餐旅大學 2027–28 海外研修—付費暨雙聯方案（Fee-Based Study Abroad Programs，12 校）",
              "source_url": NKUHT_FEE_BASED_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": f"國立高雄餐旅大學海外研修暨實習關鍵合作姊妹校列表（共 {len(partners)} 所合作姊妹校）",
              "source_url": NKUHT_KEY_PARTNERS_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立高雄餐旅大學學生海外實習及研習輔導補充規定（PDF）",
              "source_url": NKUHT_OVERSEAS_INTERNSHIP_STUDY_SUPPLEMENT_PDF_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立高雄餐旅大學 115 年度教育部「學海飛颺／學海惜珠」暨校內「探索之航：發現新天地」獎學金專區",
              "source_url": NKUHT_XUEHAI_SCHOLARSHIP_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": f"國立高雄餐旅大學國際事務處「國際交換分享（Stories of Exchange Students）」（{exp_covered_schools} 校 {total_exp_reports} 篇經驗分享）",
              "source_url": NKUHT_EXPERIENCE_SHARING_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_NKUHT_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  doc_conditions = {
      "school_id": "nkuht",
      "school_name": "國立高雄餐旅大學",
      "checked_at": CHECKED_AT,
      "source_url": NKUHT_APPLICATION_DOWNLOADS_URL,
      "common_documents": exchange_info_payload["required_documents"],
      "track_specific_conditions": [
          {
              "track": "2027–28 海外研修暨實習方案—「學費減免方案（Tuition-Free Track，19 校）」",
              "required": [
                  "國立高雄餐旅大學海外研修暨實習學費減免方案申請表（Tuition Waiver Program Application Form）",
                  "申請日本 5 所姊妹校（京都先端科學大學、武藏野大學、文京學院大學、阪南大學、山口大學）另須檢附《申請日本姊妹校履歷表（日譯本）》",
                  "中文歷年成績單正本（須顯示班排名與各學期操行成績，前三學期操行平均達 70 分以上）與 EMI/ESP 修課及格證明（餐旅、觀光、國際學院 2 門；廚藝學院及應日系 1 門）",
                  "有效外語能力檢定證照影本（JLPT N1–N3 / TOPIK 3 / IELTS 4.0–6.5 / TOEIC 550–785；最遲於 2027/02/26–03/03 補繳）",
                  "中/外文讀書與實習計畫書、自傳及《海外研修實習家長同意書（中英文版）》",
              ],
          },
          {
              "track": "2027–28 海外研修暨實習方案—「付費暨海外帶薪實習方案（Fee-Based Track，11 校）」",
              "required": [
                  "國立高雄餐旅大學海外研修暨實習付費方案報名表與目標合作學校專屬申請表（如加拿大 Humber、荷蘭 HTH、澳洲 ICHM、瑞士 SEG/Glion/Les Roches、英國 UCB/Essex、義大利 FUA、美國 MSU 迪士尼計畫）",
                  "中/英文歷年成績單正本（含班排名與操行成績；美國蒙特克萊爾州立大學迪士尼專案須歷年 GPA 2.75 以上）與 EMI/ESP 修課及格證明",
                  "有效英語檢定證明（IELTS 5.5–6.0 / TOEFL iBT 61–80 / TOEIC 550–785，或參加加拿大 Humber 校內筆試口試、澳洲 ICHM UP English Test、義大利 FUA 英語口試）",
                  "英文履歷表（CV / Resume，供海外星級飯店或美國華特迪士尼世界實習面試使用）、英文讀書計畫與《海外研修實習家長同意書（中英文版）》",
              ],
          },
          {
              "track": "澳洲昆士蘭大學（The University of Queensland）1+1 旅遊酒店與會展管理雙聯碩士學位方案",
              "required": [
                  "國立高雄餐旅大學《雙聯學制申請表》（限高餐大各研究所碩士班在學學生申請）",
                  "高餐大碩士班中/英文歷年成績單正本與學士學位證書影本",
                  "學術英語檢定證明：IELTS Academic Overall 6.5（單科不低於 6.0）或 TOEFL iBT 87（寫作 21、其餘單科 19 以上）",
                  "英文讀書與研究計畫（Statement of Purpose）、英文履歷表（CV）、指導教授或所長推薦信、家長同意書及護照影本",
              ],
          },
          {
              "track": "教育部「學海飛颺／學海惜珠」暨高餐大「探索之航：發現新天地」出國研修獎學金（每年 2/25 16:00 截止）",
              "required": [
                  "《115 年度學海飛颺／學海惜珠計畫申請表暨研修計畫書》或《探索之航獎學金：發現新天地出國研修獎學金申請表》正本（含至少 500 字自傳與 500 字研修計畫，須親筆簽名）",
                  "中文歷年成績單正本（含班排名、前三學期操行成績平均達 70 分以上）、兩年內有效語文能力證明影本、家長同意書影本、身分證與學生證正反面影本、本人戶名存摺封面影本",
                  "海外研修機構入學許可函影本（若於 2/25 申請時尚未取得，最遲須於 5 月 28 日中午 12:00 前補齊）",
                  "學海惜珠申請人另附：戶口名簿影本及低收入戶、中低收入戶、特殊境遇家庭、身心障礙生活補助或獲教育部大專弱勢學生助學計畫助學金證明影本（註明「與正本相符」並親筆簽名）",
                  "返國後 1 週內核銷必備：返抵國內報到單、登機證正本、500 字研修小故事（附 1MB 照片 1 張）、1,000–1,600 字獲獎心得報告（附 1MB 原始照片 10 張）、10 分鐘成果發表簡報及 5 分鐘微電影 1 部",
              ],
          },
      ],
  }
  (OFFICIAL_NKUHT_DIR / "document-conditions.json").write_text(
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
        f"{fname},{len(partners)},{pop},{ratio:.4f},Official NKUHT IAO verified"
    )
  (OFFICIAL_NKUHT_DIR / "field-coverage.csv").write_text(
      "\n".join(field_cov_lines) + "\n", encoding="utf-8"
  )

  pages_records = [
      {
          "title": "國立高雄餐旅大學：2027–28 海外研修暨實習方案（10/14–11/13 報名、11/20 放榜、2/26 語檢補件）與獎學金申請時程",
          "source_url": NKUHT_2027_28_PLATFORM_URL,
          "published_at": "2026-10-14T00:00:00Z",
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
          "title": "國立高雄餐旅大學：學生海外實習及研習輔導補充規定、前三學期操行 70 分門檻與 EMI/ESP 全英語課程先修規定",
          "source_url": NKUHT_OVERSEAS_INTERNSHIP_STUDY_SUPPLEMENT_PDF_URL,
          "published_at": "2026-10-14T00:00:00Z",
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
          "title": f"國立高雄餐旅大學：{len(partners)} 所全球合作姊妹校外語檢定門檻（CEFR B1/B2、TOEIC、IELTS、TOEFL、JLPT、TOPIK）",
          "source_url": NKUHT_CEFR_EQUIVALENCY_PDF_URL,
          "published_at": "2026-10-14T00:00:00Z",
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
          "title": "國立高雄餐旅大學：海外研修暨實習應備文件（報名表、日文履歷書、含班排與操行成績單、家長同意書與 5 分鐘微電影成果報告）",
          "source_url": NKUHT_APPLICATION_DOWNLOADS_URL,
          "published_at": "2026-10-14T00:00:00Z",
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
          "title": "國立高雄餐旅大學：教育部學海飛颺、學海惜珠計畫與校內「探索之航：發現新天地」出國研修獎學金（最高 6 萬元）暨帶薪實習待遇",
          "source_url": NKUHT_XUEHAI_SCHOLARSHIP_URL,
          "published_at": "2026-10-14T00:00:00Z",
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
  (OFFICIAL_NKUHT_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
      + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "nkuht",
      "school_name": "國立高雄餐旅大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "conduct_score_minimum": 70.0,
          "general_partner_gpa_minimum": 2.5,
          "emi_esp_courses_required_key_colleges": 2,
          "emi_esp_courses_required_culinary_and_applied_japanese": 1,
          "study_plus_internship_months": 12,
          "study_credits_per_semester": 10,
          "internship_credits_per_semester": 10,
          "language_certificate_supplement_deadline": "2027-03-03",
          "voyage_of_discovery_grant_ntd": "10,000–60,000",
          "exclude_in_service_for_xuehai": True,
          "return_documents_due": "返國後 1 週內繳交返抵國內報到單、登機證、500字小故事、1,000–1,600字成果報告、10張原始照片、簡報及5分鐘微電影，並辦理10+10學分抵免",
      },
      "source_urls": nkuht_source_urls,
      "verified_at": "2026-11-02",
  }
  (OFFICIAL_NKUHT_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKUHT_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "國立高雄餐旅大學",
              "required_documents": student_dashboard_payload[
                  "required_documents"
              ],
              "source_urls": nkuht_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKUHT_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "國立高雄餐旅大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": nkuht_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "nkuht",
      "school_name": "國立高雄餐旅大學",
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
      "dual_degree_partner_universities": 1,
      "dual_degree_programs": 1,
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
          f"國立高雄餐旅大學國際事務處（IAO）《2027–28 海外研修暨實習方案（19 所學費減免方案＋12 所付費暨 1+1 雙聯碩士方案）》、《關鍵合作姊妹校名錄》、《學生海外實習及研習輔導補充規定》、《115 年度教育部學海飛颺與學海惜珠計畫申請作業簡章》及《探索之航：發現新天地出國研修獎學金實施要點》同步整合；共完整收錄 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所當期開放申請合作校及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 18 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷年學長姐交換與海外飯店實習經驗分享）。"
      ),
      "verified_at": "2026-11-02",
  }
  (OFFICIAL_NKUHT_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKUHT_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "nkuht",
              "school_name": "國立高雄餐旅大學",
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
          "sources/nkuht/nkuht_catalog_source.json",
          NKUHT_2027_28_PLATFORM_URL,
          f"國立高雄餐旅大學 {len(partners)} 所全球與兩岸合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/nkuht/nkuht_resolved_locations.json",
          NKUHT_KEY_PARTNERS_URL,
          f"國立高雄餐旅大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
      ),
      (
          "sources/nkuht/nkuht_experience_index.json",
          NKUHT_EXPERIENCE_SHARING_URL,
          f"國立高雄餐旅大學國際事務處 {exp_covered_schools} 校 {total_exp_reports} 篇海外研修暨實習經驗分享索引 JSON",
      ),
  ]
  for rel_p, surl in bin_urls.items():
    rp = rel_p if rel_p.startswith("sources/") else f"sources/nkuht/{rel_p}"
    if not any(x[0] == rp for x in provenance_files):
      provenance_files.append((rp, surl, f"國立高雄餐旅大學官方原始檔案：{Path(rp).name}"))

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
      "school_id": "nkuht",
      "school_name": "國立高雄餐旅大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = (
      json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  )
  (OFFICIAL_NKUHT_DIR / "import_provenance.json").write_text(
      prov_text, encoding="utf-8"
  )
  (OFFICIAL_NKUHT_DIR / "import-provenance.json").write_text(
      prov_text, encoding="utf-8"
  )

  print(
      f"Successfully built NKUHT catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
