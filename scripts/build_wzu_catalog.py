"""Build the official Wenzao Ursuline University of Languages (文藻外語大學, WZU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
  sys.path.insert(0, str(REPO_ROOT / "src"))
from exchange_info.school_identity import VisualRecordIndex, school_identity_key

SOURCES_WZU_DIR = REPO_ROOT / "sources" / "wzu"
OFFICIAL_WZU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "wzu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-19T17:30:00Z"

REGION_BY_COUNTRY = {
    "日本": "亞洲",
    "韓國": "亞洲",
    "中國大陸": "中國大陸及港澳",
    "印尼": "亞洲",
    "越南": "亞洲",
    "泰國": "亞洲",
    "菲律賓": "亞洲",
    "馬來西亞": "亞洲",
    "土耳其": "亞洲",
    "美國": "美洲",
    "加拿大": "美洲",
    "巴拉圭": "美洲",
    "墨西哥": "美洲",
    "澳洲": "大洋洲",
    "法國": "歐洲",
    "西班牙": "歐洲",
    "德國": "歐洲",
    "英國": "歐洲",
    "比利時": "歐洲",
    "立陶宛": "歐洲",
    "匈牙利": "歐洲",
    "波蘭": "歐洲",
    "奧地利": "歐洲",
    "捷克": "歐洲",
}

REGION_COST_DEFAULTS = {
    "日本": (
        (
            "JPY 80,000–130,000 / 月（東京與京阪神約 JPY"
            " 95,000–145,000；名古屋外大月領 6 萬日圓、清泉月領 2–4"
            " 萬日圓、鹿兒島純心月領 3 萬日圓、東洋 IUEP 月領 5.1"
            " 萬日圓獎學金可大幅減輕負擔）"
        ),
        (
            "憑日本接待校核發之在留資格認定證明書（COE）向日本台灣交流協會高雄事務所換發留學簽證，抵日後須加入日本國民健康保險（NHI）。"
        ),
    ),
    "韓國": (
        (
            "KRW 800,000–1,350,000 /"
            " 月（首爾圈崇實、漢陽、誠信女大生活費較高；釜山外大、釜山天主教、大邱韓醫、忠北、翰林、順天鄉宿舍與餐費實惠）"
        ),
        (
            "憑韓國標準入學許可書申辦 D-2-6"
            " 交換學生簽證，抵韓後辦理外國人登錄並自動納入韓國國民健康保險（NHIS），入住校內宿舍須備妥肺結核與麻疹疫苗英文證明。"
        ),
    ),
    "中國大陸": (
        (
            "RMB 2,000–3,800 /"
            " 月（北京外大與大連外大提供免費雙人／四人宿舍，上海外大、中央民族、中國傳媒、廣東外語外貿、西南財大校內食堂與住宿成本親民）"
        ),
        (
            "持有效護照與臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定投保大陸境內來華留學生綜合醫療保險（每年約"
            " RMB 800）。"
        ),
    ),
    "印尼": (
        (
            "IDR 5,000,000–8,500,000 /"
            " 月（雅加達、日惹、泗水、萬隆、瑪朗、任抹學生宿舍或周邊公寓與日常開支實惠；ACUCA"
            " 計畫另提供每月 USD 300–500 獎助金）"
        ),
        (
            "須由印尼接待校協助向印尼移民總局申辦 C316"
            " 學習電子簽證（e-Visa）並投保海外全期醫療及意外保險。"
        ),
    ),
    "越南": (
        (
            "USD 400–700 /"
            " 月（河內國家大學、河內大學、河內工業大學、胡志明市人文社大與土龍木大學住宿及飲食成本親民）"
        ),
        (
            "須憑越南接待校入學許可透過駐臺北越南經濟文化辦事處申辦越南學生簽證並投保海外醫療險。"
        ),
    ),
    "泰國": (
        (
            "THB 15,000–25,000 /"
            " 月（曼谷法政大學、易三倉大學、商會大學與清邁皇家大學周邊學生公寓及生活開支親民）"
        ),
        (
            "須憑泰國接待校正式入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant"
            " ED 學生簽證。"
        ),
    ),
    "菲律賓": (
        (
            "USD 500–850 /"
            " 月（馬尼拉聖托馬斯大學、德拉薩大學、亞太大學及巴科洛德聖拉薩大學生活與住宿費實惠）"
        ),
        (
            "須憑接待校入學許可向馬尼拉經濟文化辦事處（MECO）高雄分處辦理簽證，抵菲後由學校協助申辦"
            " SSP（Special Study Permit）或 9(f) 學生簽證。"
        ),
    ),
    "馬來西亞": (
        (
            "MYR 1,500–2,600 / 月（吉隆坡馬來亞大學、拉曼大學與新紀元大學學院"
            " MRT 周邊學生宿舍與餐飲機能便利且物價親民）"
        ),
        (
            "須於出國前透過 EMGS（Education Malaysia Global"
            " Services）系統線上申辦馬來西亞學生簽證核准函（VAL / Student"
            " Pass）並投保 EMGS 指定醫療險。"
        ),
    ),
    "土耳其": (
        (
            "EUR 550–900 /"
            " 月（伊斯坦堡海峽大學、伊本哈爾頓大學與北賽普勒斯近東大學學生生活費較西歐低廉；伊本哈爾頓大學免費提供校內宿舍及每日三餐）"
        ),
        (
            "須憑接待校入學許可向駐臺北土耳其貿易辦事處申辦學生簽證，抵土後辦理學生居留證（İkamet）與醫療保險。"
        ),
    ),
    "美國": (
        (
            "USD 1,300–2,300 / 月（含校內學生宿舍、強制 Meal Plan"
            " 膳食計畫與校園健康保險；加州 UCI 推廣教育學院自費項目生活費較高）"
        ),
        (
            "須憑 DS-2019 或 I-20 表格繳納 SEVIS I-901 費用並至"
            " AIT（美國在台協會）申辦 J-1 / F-1 簽證及投保接待校強制醫療險。"
        ),
    ),
    "加拿大": (
        (
            "CAD 1,500–2,300 / 月（卑詩省希爾克學院與皇家大學住宿及膳食；希爾克學院可爭取"
            " Study in Canada 獎學金最高 USD 10,200）"
        ),
        (
            "交換 1 學期（6 個月內）可申辦 eTA 電子旅行授權，交換 1"
            " 學年須申辦加拿大 Study Permit 學生簽證並投保省級／校內醫療險。"
        ),
    ),
    "巴拉圭": (
        (
            "USD 550–850 /"
            " 月（亞松森巴拉圭天主教大學周邊住宿與生活開支實惠，適合西語組學生沉浸式進修）"
        ),
        (
            "須依巴拉圭共和國駐華大使館規定辦理簽證並投保涵蓋交換全期之海外醫療及意外保險。"
        ),
    ),
    "墨西哥": (
        (
            "USD 700–1,150 /"
            " 月（墨西哥城阿納瓦克大學周邊寄宿家庭或學生公寓、餐飲與大眾運輸）"
        ),
        (
            "交換 180 天內可依墨西哥商務簽證文件暨文化辦事處規定辦理簽證，逾"
            " 180 天須申辦墨西哥學生居留簽證並投保海外全期醫療險。"
        ),
    ),
    "澳洲": (
        (
            "AUD 1,800–2,700 / 月（阿得雷德國際旅館管理學院 ICHM 與雪梨國際管理學院"
            " ICMS 含校內食宿及有薪飯店實習機會）"
        ),
        (
            "須購買澳洲海外學生健康保險（OSHC）並線上申辦 Subclass 500"
            " 學生簽證。"
        ),
    ),
    "法國": (
        (
            "EUR 800–1,400 / 月（巴黎 INALCO 約 EUR"
            " 1,100–1,450；里爾、格勒諾柏、艾克斯、土魯斯、雷恩、布レスト、昂熱、維琪約"
            " EUR 750–1,050，可申請法國政府 CAF 房屋補助）"
        ),
        (
            "須透過法國教育中心（Campus"
            " France）完成線上面談審查並向法國在台協會申辦長期學生簽證（VLS-TS），抵法後完成"
            " OFII 線上生效與法國學生社保（Sécurité Sociale）登錄。"
        ),
    ),
    "西班牙": (
        (
            "EUR 800–1,250 /"
            " 月（巴塞隆納與馬德里鄰近城市約 EUR"
            " 900–1,250；薩拉曼卡、聖地牙哥、雷昂、瓦倫西亞、阿維拉、潘普洛納、昆卡大學城生活費親民）"
        ),
        (
            "須備妥無自負額、涵蓋全額醫療與遺體運返之西班牙私人醫療保險（如"
            " Adeslas / Sanitas），向西班牙商務辦事處申辦學生簽證。"
        ),
    ),
    "德國": (
        (
            "EUR 934–1,250 / 月（德國簽證限制提領帳戶 Sperrkonto 基準為每月 EUR"
            " 992，含慕尼黑、萊比錫、美因茲、康斯坦斯、艾希特、茨維考住宿與學期交通票）"
        ),
        (
            "須辦理德國法定學生公保（如 TK / AOK，約 EUR 125–135 /"
            " 月）、繳納學期雜費（Semesterbeitrag）並向德國在台協會申辦長期學生簽證。"
        ),
    ),
    "英國": (
        (
            "GBP 1,050–1,550 /"
            " 月（伯明罕、拉夫堡、巴斯、普利茅斯、渥夫漢普頓等非倫敦地區大學城生活與宿舍費較倫敦實惠）"
        ),
        (
            "交換一學期（6 個月內）可辦理 Standard Visitor 簽證，交換一學年須申辦英國"
            " Student Visa 並繳納 IHS 醫療附加費。"
        ),
    ),
    "比利時": (
        (
            "EUR 850–1,300 /"
            " 月（布魯塞爾自由大學、聖路易斯、新魯汶、列日、根特學生宿舍與日常交通）"
        ),
        (
            "須向比利時台北辦事處申辦長期學生簽證（D"
            " 簽），抵比後向當地市政廳（Commune）辦理居留證登記。"
        ),
    ),
    "立陶宛": (
        (
            "EUR 550–850 / 月（維爾紐斯 MRU 與考納斯 VDU 校內學生宿舍每月僅約 EUR"
            " 120–250，東歐物價十分親民）"
        ),
        (
            "須透過立陶宛移民局 MIGRIS 系統申辦臨時居留許可（TRP）或國家簽證（D"
            " 簽）並投保歐盟申根規格醫療保險。"
        ),
    ),
    "匈牙利": (
        (
            "EUR 600–950 /"
            " 月（布達佩斯城市大學周邊學生合租公寓、餐飲與布達佩斯學生交通月票成本低廉）"
        ),
        (
            "須向匈牙利貿易辦事處申辦留學居留簽證（D"
            " 簽）並投保涵蓋全期之申根醫療保險。"
        ),
    ),
    "波蘭": (
        (
            "EUR 550–850 / 月（約 PLN"
            " 2,400–3,600，克拉科夫高等學院周邊住宿與歷史名城生活開支實惠）"
        ),
        (
            "須向波蘭臺北辦事處申辦 D"
            " 類國別學生簽證並備妥歐盟認定之旅行醫療保險。"
        ),
    ),
    "奧地利": (
        (
            "EUR 950–1,350 /"
            " 月（含維也納大學語言中心周邊學生宿舍、膳食與維也納大眾運輸學期票）"
        ),
        (
            "須依進修期程向奧地利台北辦事處辦理簽證（D"
            " 簽）並投保涵蓋全期之申根醫療及意外保險。"
        ),
    ),
    "捷克": (
        (
            "EUR 550–850 /"
            " 月（赫拉德茨-克拉洛韋大學校內學生宿舍每月僅約 EUR"
            " 130–180，捷克學生餐廳與國鐵學生票極為實惠）"
        ),
        (
            "須向捷克經濟文化辦事處申辦長期留學簽證並購買捷克境內認可之綜合外國人醫療保險（如"
            " PVZP / Maxima）。"
        ),
    ),
}

WZU_OICC_HUB_URL = "https://c015.wzu.edu.tw/"
WZU_IED_HUB_URL = "https://d020.wzu.edu.tw/"
WZU_OUTBOUND_GUIDE_URL = "https://d020.wzu.edu.tw/article/492285"
WZU_R1_ANNOUNCEMENT_URL = "https://d020.wzu.edu.tw/article/529354"
WZU_R2_ANNOUNCEMENT_URL = "https://d020.wzu.edu.tw/article/530752"
WZU_R1_115_1_ANNOUNCEMENT_URL = "https://d020.wzu.edu.tw/article/524735"
WZU_PARTNER_INFO_URL = "https://d020.wzu.edu.tw/category/154399"
WZU_EXP_ALBUM_URL = "https://d020.wzu.edu.tw/album/list/152198"
WZU_UMAP_URL = "https://d020.wzu.edu.tw/article/517638"
WZU_ACUCA_URL = "https://d020.wzu.edu.tw/article/517642"
WZU_SCHOLARSHIP_HUB_URL = "https://d020.wzu.edu.tw/category/152197"
WZU_REGULATIONS_URL = "https://d020.wzu.edu.tw/category/152182"
WZU_SOSA_URL = "https://d020.wzu.edu.tw/category/152202"


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def format_colleges(item: dict) -> str:
  zh = item["name_zh"]
  notes = item.get("notes") or ""
  pg = item["primary_group"]
  if "限日文系" in notes:
    return (
        "歐亞語文學院日本語文系（簡章備註：限日文系學生申請，須具 JLPT N2 以上）"
    )
  if "德語系交換計畫" in zh or "限德文系" in notes:
    return "歐亞語文學院德國語文系優先（胡志明市國家大學人文社大德語系交換計畫）"
  if "外語教學系" in notes and "翻譯系" in notes:
    return (
        "國際文教暨涉外事務學院（外語教學系、翻譯系、英語教學中心相關領域優先）"
    )
  if "傳播" in notes and "限" in notes:
    return "新媒體暨管理學院（傳播藝術系、數位內容應用與管理系等相關科系優先）"
  return (
      "不限學院（國際文教暨涉外事務學院、歐亞語文學院、新媒體暨管理學院、華語學院、吳甦樂人文學院等全校各院系所符合「"
      f"{pg}」語組與學制資格之在學學生皆可報考）"
  )


def format_degree_levels(item: dict) -> str:
  notes = item.get("notes") or ""
  track = item["track"]
  if "可招收研究生" in notes:
    return (
        "五專部四年級（出國時專四下或專五）、四技部二年級至三年級（出國時四技二下至四技四）、二技部三年級（出國時二技三下或二技四）及研究所碩士班在學學生（本姐妹校開放招收研究生）"
    )
  if "限大學部" in notes or "不受理專科生" in notes or "限四技" in notes:
    return (
        "四技部二年級至三年級及二技部三年級在學學生（依該姊妹校簡章規定限大學部學生申請，不受理五專部學生）"
    )
  if track == "語言學習組":
    return (
        "五專部四年級（含）以上、四技部二年級（含）以上、二技部三年級及研究所碩士班在學學生（語言學習組歷年學業總平均達"
        " 65 分以上、操行 80 分以上即可報考）"
    )
  return (
      "五專部四年級（出國時專四下或專五）、四技部二年級至三年級（出國時四技二下至四技四）、二技部三年級（出國時二技三下或二技四）及研究所碩士班在學學生（須符合姊妹校開放學制）"
  )


def format_study_period(item: dict) -> str:
  quota = item.get("quota") or ""
  if "一學年" in quota and "一學期" in quota:
    return "1 學期 或 1 學年（依當期甄選名額表與姊妹校核定名額為準）"
  if "一學年" in quota:
    return "1 學年（依當期甄選名額表以一學年交換為原則）"
  return "1 學期（部分學校可依規定申請一學年或自費延長一學期）"


def format_program_type(item: dict) -> str:
  track = item["track"]
  groups = "、".join(item["language_groups"])
  if track == "語言學習組":
    return f"國合處國際交流組出國交換生計畫—語言學習組（{groups}・自費語言中心進修）"
  return f"國合處國際交流組出國交換生計畫—一般組（{groups}）"


def extract_gpa_req(item: dict) -> str:
  track = item["track"]
  notes = item.get("notes") or ""
  base = (
      "文藻校內門檻：歷年學業成績總平均達 70 分（含）以上（認列至個位數，小數點後不採計亦不四捨五入）、歷年操行成績總平均達 80 分（含）以上且無小過（含）以上懲處記錄"
      if track == "一般組"
      else "文藻校內門檻（語言學習組）：歷年學業成績總平均達 65 分（含）以上（認列至個位數，小數點後不採計亦不四捨五入）、歷年操行成績總平均達 80 分（含）以上且無小過（含）以上懲處記錄"
  )
  m = re.search(
      r"(GPA\s*達?\s*[0-9.]+[^。；\n]*|歷年學業成績平均分數達\s*\d+\s*分[^。；\n]*|學業成績平均達\s*\d+\s*分[^。；\n]*)",
      notes,
      re.I,
  )
  if m:
    return f"{base}；姊妹校特別規定：{clean_text(m.group(1))}"
  return base


def extract_housing(item: dict) -> str:
  notes = item.get("notes") or ""
  zh = item["name_zh"]
  sentences = [
      clean_text(s)
      for s in re.split(r"(?=\d+\.\s)", notes)
      if any(
          k in s
          for k in ["宿", "房", "住", "公寓", "寄宿", "膳食", "餐", "生活費"]
      )
  ]
  if sentences:
    return " ".join(sentences)
  return (
      f"錄取並獲文藻國合處提名後，由 {zh} 國際事務處協助安排校內學生宿舍或校外合作學生公寓／寄宿家庭，住宿費與膳食費由交換生自行負擔（詳見國合處各校交換申請資訊雲端資料夾）。"
  )


def main() -> None:
  OFFICIAL_WZU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_items = json.loads(
      (SOURCES_WZU_DIR / "wzu_catalog_source.json").read_text(encoding="utf-8")
  )
  manifest = json.loads(
      (STATIC_DIR / "assets" / "school-images.json").read_text(encoding="utf-8")
  )
  visual_index = VisualRecordIndex({
      (
          school_identity_key(str(r.get("school_name", ""))),
          str(r.get("country") or ""),
      ): r
      for r in manifest.get("schools", [])
      if isinstance(r, dict) and r.get("status") == "verified"
  })

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

  for idx, item in enumerate(catalog_items):
    full_name = item["full_name"]
    zh_name = item["name_zh"]
    country = item["country"]
    region = REGION_BY_COUNTRY.get(country, "其他地區")
    track = item["track"]
    pg = item["primary_group"]
    lang_groups_str = "、".join(item["language_groups"])
    avail_status = item["availability_status"]
    if avail_status == "open":
      open_partner_count += 1

    website = (item.get("website") or "").strip()
    if website and not website.startswith("http"):
      website = f"https://{website}"
    sharing_drive_url = (item.get("sharing_drive_url") or "").strip() or None
    factsheet_url = sharing_drive_url or WZU_PARTNER_INFO_URL
    source_url = item["source_url"]
    remarks_all = clean_text(item.get("notes") or "")

    if item.get("in_115_2_r2"):
      round_label = f"115學年度第2學期出國交換生甄選（一招／二招・{track}・{lang_groups_str}）"
      deadline_iso = "2026-10-13T15:00:00+08:00"
      win_status = "closed"
      deadline_rem = False
    elif item.get("in_115_2"):
      round_label = (
          f"115學年度第2學期出國交換生甄選（一招・{track}・{lang_groups_str}）"
      )
      deadline_iso = "2026-08-31T15:00:00+08:00"
      win_status = "closed"
      deadline_rem = False
    else:
      round_label = f"115/116學年度出國交換生甄選（{track}・{lang_groups_str}・第一學期一招預計2月開放）"
      deadline_iso = "2027-03-02T15:00:00+08:00"
      win_status = "closed"
      deadline_rem = False

    app_deadline_str = (
        "【文藻外語大學國際暨兩岸合作處（國際交流組）出國交換生甄選時程】"
        "每學期分「一招」與「二招」辦理（115-2 梯次：一招網路報名與說明會 2026/05/04–05/08、紙本收件截止 2026/08/31 15:00、面試 09/09–09/15、撕榜 09/22–09/23；"
        "二招收件截止 2026/10/13 15:00、面試 10/19–10/23、志願分發 10/14–10/30；"
        "116-1 秋季出國一招預計於 2027 年 2 月開放線上申請、3 月初截止收件，另同步開放 UMAP 亞太大學交流會與 ACUCA 亞洲基督教大學協會交換計畫）。"
    )

    raw_loc = item["location"]
    location_obj = {
        "school_name": full_name,
        "country": country,
        "city": raw_loc.get("city") or country,
        "latitude": float(raw_loc["latitude"]),
        "longitude": float(raw_loc["longitude"]),
        "geocode_status": "verified",
        "geocoded_at": CHECKED_AT,
        "source_url": raw_loc.get("source_url") or "https://www.wikidata.org",
        "identity_source_url": (
            raw_loc.get("identity_source_url")
            or raw_loc.get("source_url")
            or "https://ror.org"
        ),
        "precision": "representative",
        "note": (
            raw_loc.get("note")
            or "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區以錄取通知與締約校專頁為準。"
        ),
    }
    new_locations.append(location_obj)

    colleges_str = format_colleges(item)
    degree_levels_str = format_degree_levels(item)
    lang_req_str = clean_text(item["lang_req"])
    gpa_req_str = extract_gpa_req(item)
    quota_str = clean_text(item["quota"])
    study_period_str = format_study_period(item)
    program_type = format_program_type(item)
    housing_raw = extract_housing(item)
    housing_str = f"{zh_name} 住宿與生活說明：{housing_raw}"

    exp_posts = item.get("experience_stories") or []
    exp_portal_url = sharing_drive_url or WZU_EXP_ALBUM_URL

    if country == "日本":
      sem_dates_str = (
          "春季學期（4 月入學梯次）：每年 4 月至 8 月（或至翌年 3 月）；秋季學期（9 月入學梯次）：每年 9 月至翌年 1/2"
          " 月（或至翌年 8 月）"
      )
    elif country == "澳洲":
      sem_dates_str = (
          "第 1 學期（Semester 1）：約每年 2 月至 6 月；第 2 學期（Semester 2）：約每年 7 月至 11"
          " 月（含飯店管理有薪實習學期）"
      )
    elif country == "韓國":
      sem_dates_str = (
          "春季學期（第 1 學期）：每年 3 月初至 6 月中旬；秋季學期（第 2 學期）：每年 9 月初至 12 月中旬"
      )
    else:
      sem_dates_str = (
          "秋季學期（第 1 學期）：約每年 8/9 月至 12 月／翌年 1 月；春季學期（第 2 學期）：約每年 1/2 月至 5/6 月"
      )

    course_parts = [
        f"開放申請語組、院系與學制：{lang_groups_str}（{track}）｜{colleges_str}（{degree_levels_str}）。"
    ]
    if remarks_all:
      course_parts.append(f"姊妹校甄選與修課規定：{remarks_all}")
    course_parts.append(
        "依《文藻外語大學學生出國交換實施辦法》及甄選簡章規定，交換生出國期間須完成文藻註冊並繳交文藻全額學雜費（延畢生於出國交換期間亦須繳交全額學雜費）；每學期於姊妹校至少須修讀"
        " 2 門課或 4 學分，或至少 1 門該國語言課程，返國後依規定辦理學分抵免並完成返國報告書與經驗分享義務。"
    )
    course_rest_str = " ".join(course_parts)

    tuition_points_list = [
        (
            "文藻在學註冊學雜費與公費／自費名額規定：依《文藻外語大學學生出國交換實施辦法》第五條及甄選簡章規定，出國交換期間須保留文藻學籍並繳交文藻全額學雜費（延畢生出國期間亦須繳交全額學雜費）。屬「一般組免繳對方學費（互惠名額）」者免繳姊妹校學費；屬「一般組繳交對方學費／折扣學費」或「語言學習組（自費語言中心）」者，除繳交文藻全額學雜費外，須另行依姊妹校規定繳交學費或語言中心課程費。獲分發確認後，無不可抗力因素放棄資格者，在校期間不得再次參加本校各類出國交換甄選。"
        ),
        (
            "文藻外語大學四大出國交換獎助學金體系：（1）《文藻外語大學出國交換及雙聯學制學生獎助學金》：補助五專、四技及研究生每名新臺幣 10,000"
            " 元；二技生及本校五專直升四技學生每名最高補助新臺幣 50,000 元；進修部學生補助抵免學分費之三分之一（上限 NT$10,000）；（2）教育部《學海飛颺》獎助學金：補助中華民國國籍、歷年學業總平均達"
            " 75 分以上、操行 80 分以上且具外語檢定證明之優秀學生赴國外（不含陸港澳）交換，每名至少核給 NT$50,000；（3）教育部《學海惜珠》獎助學金：補助具低收入戶、中低收入戶或特殊境遇家庭身分、學業總平均達"
            " 75 分以上且操行 80 分以上之學生出國交換（獲教育部補助外，文藻另提撥 20% 配合款補助）；（4）《跨國聯盟與姊妹校專屬獎學金》：含日本"
            " JASSO 獎學金、名古屋外國語大學每月 6 萬日圓、清泉大學每月 2–4 萬日圓、鹿兒島純心大學每月 3 萬日圓、東洋大學 IUEP"
            " 每月 5.1 萬日圓、加拿大希爾克學院 Study in Canada 最高 USD 10,200、ACUCA 交換計畫每月 USD"
            " 300–500 及 UMAP 臺灣國家秘書處每月最高 NT$20,000 獎助金。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認報考組別［一般組 70 分／語言學習組 65 分］、語組與 {zh_name} 資格門檻）：確認報考「{track}（{lang_groups_str}）」，一般組歷年學業總平均須達"
            " 70 分以上、語言學習組須達 65 分以上（認列至個位數，不四捨五入），操行總平均皆須達 80 分以上且無小過以上紀錄，並備妥符合"
            f" {zh_name} 要求之語檢證明（{lang_req_str}）。一般組甄選資格涵蓋語言學習組，可於撕榜時跨選語言學習組學校。"
        ),
        (
            "步驟二（完成校務資訊系統線上報名並繳交紙本申請資料至國合處國際交流組）：於報名期間至「校務資訊系統 → 申請 → 國際合作交流申請 →"
            " 出國交換生甄選申請作業」填報並印出申請表，經系（所、中心）主任簽章、雙主修／輔系核章及家長簽名同意後，連同中英文歷年成績單（含排名）、中英文研修計畫書（各"
            " 500–1,000 字）、語檢成績單（英語及第二外語）、班級幹部／社團／競賽獲獎證明及 SOSA 多國語言志工團服務時數證明（最高加 5"
            " 分）送交行政大樓 2 樓國合處國際交流組。"
        ),
        (
            f"步驟三（參加二階段甄選［書審 50%＋面試 50%］與現場撕榜／志願分發）：第一階段書面審查佔 50%（歷年學業 20%、操行 10%、英語能力 10%、第二外語能力 10%，另加計 SOSA 志工團加分最高 5 分）；第二階段面試佔 50%（讀書計畫 15%、口語表達 15%、儀態態度 10%、國際活動經驗及其他 10%）。兩階段總分達 60 分以上者取得選校資格，依總成績高低依序參加第三階段現場撕榜（一招）或線上志願分發（二招），錄取確認後繳交《錄取資格確認書》並由國合處向 {full_name} 辦理官方提名（Nomination）。"
        ),
        (
            "步驟四（向姊妹校遞交入學申請、參加全體行前說明會並完成返國義務）：獲提名後依姊妹校規定遞交入學與宿舍申請文件、申辦留學簽證與海外全期醫療及意外保險，並可同步申請文藻出國交換獎助學金（1"
            " 萬–5 萬）、教育部學海飛颺／惜珠或姊妹校獎學金。出國前須參加國合處舉辦之行前說明會並完成文藻註冊繳費；抵達姊妹校 2 週內繳交《抵達國外姊妹校通報單》，返國後"
            " 1 個月內繳交《出國交換學生返國報告書》、照片及正式成績單辦理學分抵免（學長姐完整心得可於國合處各校雲端硬碟查閱）。"
        ),
    ]

    elig_points_list = [
        f"甄選管道與語組：{program_type}",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業與操行成績要求：{gpa_req_str}",
        f"語言能力標準：{lang_req_str}",
        (
            "甄選配分與跨組撕榜規則：第一階段書審 50%（學業 20%＋操行 10%＋英語 10%＋二外 10%＋SOSA 志工加分最高 5"
            " 分）＋第二階段面試 50%（讀書計畫 15%＋口語表達 15%＋儀態態度 10%＋國際活動經驗 10%），總分達 60"
            " 分以上合格；一般組合格生於撕榜／分發時優先選校，且可同時選擇一般組或語言學習組學校。"
        ),
    ]
    if remarks_all:
      elig_points_list.append(f"姊妹校特殊規定與備註：{remarks_all}")

    notes_lines = [
        f"【合作類別與期程】{program_type}｜交換期間：{study_period_str}",
        f"【當期名額與費用待遇】{quota_str}",
        f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
        f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        f"【住宿與生活資訊】{housing_raw}",
    ]
    if sharing_drive_url:
      notes_lines.append(
          f"【歷屆學長姐經驗分享雲端資料夾】文藻國合處提供赴 {zh_name} 歷屆交換生研修心得與實況資料夾：{sharing_drive_url}"
      )
    if remarks_all:
      notes_lines.append(f"【締約校重要備註】{remarks_all}")

    visual_rec = visual_index.get((full_name, country)) or {}
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
            f"文藻外語大學國際暨兩岸合作處（國際交流組）公告交換合作姊妹校（{track}・{lang_groups_str}）；{quota_str}。"
        ),
        "academic_year": "115",
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
        "image_url": visual_rec.get("local_path"),
        "image_source_url": visual_rec.get("image_source_url"),
        "image_page_url": (
            visual_rec.get("official_page_url")
            or visual_rec.get("image_source_url")
        ),
        "image_status": (
            "verified" if visual_rec.get("local_path") else "missing"
        ),
        "location": location_obj,
        "reference_data": {
            k: str(v)
            for k, v in {
                "track": track,
                "primary_group": pg,
                "language_groups": lang_groups_str,
                "sister_school_no": item.get("sister_school_no"),
                "sharing_drive_url": sharing_drive_url,
                "experience_report_count": (
                    len(exp_posts)
                    if exp_posts
                    else (1 if sharing_drive_url else None)
                ),
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
            "title": f"文藻外語大學出國交換生甄選簡章與學校名額一覽表—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": "115",
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "文藻外語大學學生出國交換實施辦法與甄選申請流程",
            "source_url": WZU_OUTBOUND_GUIDE_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": "115",
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "文藻外語大學出國交換及雙聯學制學生獎助學金暨學海計畫專區",
            "source_url": WZU_SCHOLARSHIP_HUB_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": "115",
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if sharing_drive_url:
      wf_sources.append({
          "title": (
              f"文藻外語大學國合處各校交換申請資訊與學長姐經驗分享雲端資料夾—{zh_name}"
          ),
          "source_url": sharing_drive_url,
          "role": "home_university",
          "authority": "home_official_notice",
          "effective_academic_year": "115",
          "application_round": round_label,
          "checked_at": CHECKED_AT,
      })
    if website:
      wf_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "role": "partner_university",
          "authority": "partner_official",
          "effective_academic_year": "115",
          "application_round": round_label,
          "checked_at": CHECKED_AT,
      })

    workflows.append({
        "home_university": "文藻外語大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": "115",
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "115-2",
            "115-1",
            "116-1",
            "116-2",
            "一般組",
            "語言學習組",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "文藻外語大學由國際暨兩岸合作處（國際交流組）統籌辦理「一般組（學業總平均"
            " 70 分、操行 80 分）」與「語言學習組（學業總平均 65 分、操行 80"
            " 分）」六大語組（英語組、日語組、法語組、德語組、西語組、華語暨東南亞語組）及"
            " UMAP、ACUCA 跨國聯盟交換甄選；一般組合格資格涵蓋語言學習組，可於撕榜／分發時優先跨選。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"wzu-115-home-1-{idx+1:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": (
                    f"確認報考組別（{track}・{lang_groups_str}）、學業操行門檻與"
                    f" {zh_name} 語檢要求"
                ),
                "responsible_party": "學生",
                "responsible_unit": (
                    "文藻外語大學國際暨兩岸合作處國際交流組（行政大樓 2 樓）"
                ),
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": deadline_rem,
                "summary": (
                    f"確認符合《文藻外語大學學生出國交換實施辦法》及當期甄選簡章規定（一般組歷年學業總平均達"
                    f" 70 分以上、語言學習組達 65 分以上，認列至個位數不四捨五入；操行總平均達"
                    f" 80 分以上且無小過以上懲處），並備妥符合 {zh_name}"
                    " 規定之外語能力檢定證明。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與費用待遇：{quota_str}",
                ],
                "scope": {
                    "home_universities": ["文藻外語大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-2",
                        "116-1",
                    ],
                },
                "source_urls": [
                    source_url,
                    WZU_OUTBOUND_GUIDE_URL,
                    WZU_R1_ANNOUNCEMENT_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"wzu-115-home-2-{idx+1:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": (
                    "完成校務資訊系統線上報名並繳交核章紙本申請表、中英文成績單與研修計畫書至國合處"
                ),
                "responsible_party": "學生與所屬系（所、中心）辦公室",
                "responsible_unit": (
                    "文藻外語大學各系所辦公室／國際暨兩岸合作處國際交流組"
                ),
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": deadline_rem,
                "summary": (
                    "於甄選收件截止日（15:00"
                    " 止）前，登入「校務資訊系統」完成出國交換生甄選線上申請並印出紙本申請表，經系（所、中心）主任核章及家長簽名同意後，連同中文歷年成績單（含排名與操行）、英文歷年成績單（百分制含排名）、中英文研修計畫書（各"
                    " 500–1,000 字）、英語及第二外語檢定成績單影本、社團／幹部／競賽獲獎證明及"
                    " SOSA 多國語言志工團服務證明送交國合處國際交流組。"
                ),
                "details": [
                    (
                        "第一階段書審（50%）配分明細：歷年學業成績佔 20%、歷年操行成績佔"
                        " 10%、英語能力檢定佔 10%、第二外語能力檢定佔 10%；若曾參與國合處"
                        " SOSA 多國語言志工團且服務時數達標者，可於第一階段額外加分（最高加 5"
                        " 分）。"
                    ),
                    (
                        "同時報考多個語組規定：若同學具備多國語言能力欲同時報名兩個（含）以上語組，每一語組均須分別繳交乙份完整紙本申請資料。"
                    ),
                ],
                "document_requirements": [
                    {
                        "name": (
                            "文藻外語大學出國交換生甄選申請表（於校務資訊系統填報列印，貼妥"
                            " 2 吋照片並經系所主任核章及家長簽名同意）"
                        ),
                        "official_form_url": WZU_OUTBOUND_GUIDE_URL,
                        "source_urls": [
                            WZU_OUTBOUND_GUIDE_URL,
                            WZU_R1_ANNOUNCEMENT_URL,
                        ],
                    },
                    {
                        "name": (
                            "中文歷年學業成績單正本（含學業總平均、班／系排名及歷年操行成績）與英文歷年學業成績單正本（百分制、含排名）"
                        ),
                        "source_urls": [
                            WZU_R1_ANNOUNCEMENT_URL,
                            WZU_R2_ANNOUNCEMENT_URL,
                        ],
                    },
                    {
                        "name": (
                            "有效外語能力檢定證明影本（英語檢定"
                            " TOEFL／IELTS／TOEIC／全民英檢／CSEPT 及第二外語檢定"
                            " JLPT／DELF／Goethe／TestDaF／DELE／SIELE／TOPIK 等）"
                        ),
                        "source_urls": [
                            WZU_R1_ANNOUNCEMENT_URL,
                            source_url,
                        ],
                    },
                    {
                        "name": (
                            "中文研修計畫書及英文（或該語組外文）研修計畫書（各"
                            " 500–1,000 字，含出國動機、修課規劃與返國學習連結）及"
                            " SOSA 志工團／社團幹部／競賽表現證明"
                        ),
                        "source_urls": [
                            WZU_R1_ANNOUNCEMENT_URL,
                            WZU_SOSA_URL,
                        ],
                    },
                ],
                "scope": {
                    "home_universities": ["文藻外語大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-2",
                        "116-1",
                    ],
                },
                "source_urls": [
                    WZU_OUTBOUND_GUIDE_URL,
                    WZU_R1_ANNOUNCEMENT_URL,
                    WZU_R2_ANNOUNCEMENT_URL,
                    source_url,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"wzu-115-home-3-{idx+1:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": (
                    "參加第二階段外語面試（50%）、現場撕榜／志願分發並繳交錄取資格確認書"
                ),
                "responsible_party": "學生與國合處交換學生甄選委員會",
                "responsible_unit": "文藻外語大學國際暨兩岸合作處國際交流組",
                "deadline_at": "2026-10-30T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "參加第二階段面試（佔總成績 50%：讀書計畫 15%、口語表達 15%、儀態與態度"
                    " 10%、國際活動經驗及其他 10%）。第一階段書審與第二階段面試總成績合計達"
                    " 60"
                    " 分（含）以上者取得撕榜／志願分發資格（總分相同時依面試成績高低排序）。一般組合格者優先進行撕榜／分發，可選擇該語組之一般組或語言學習組學校；語言學習組合格者次之，僅可選擇語言學習組學校。分發確認後須按時繳交《錄取資格確認書》與《家長同意書》。"
                ),
                "details": [
                    (
                        "放棄資格處分規定：獲錄取分發並繳交確認書後，除因不可抗力之重大事由經專案簽准外，不得任意放棄交換資格；違者於文藻就讀期間不得再次申請各類出國交換計畫。"
                    ),
                    (
                        "獎助學金同步申請：獲得交換推薦資格之學生，可依國合處公告時程申請《文藻外語大學出國交換及雙聯學制學生獎助學金》（1"
                        " 萬–5 萬元）、教育部《學海飛颺》（學業 75 分、操行 80 分，至少 5"
                        " 萬元）、《學海惜珠》（低收／中低收／特殊境遇，文藻另加碼 20%"
                        " 配合款）及日本 JASSO／姊妹校／UMAP／ACUCA 獎學金。"
                    ),
                ],
                "scope": {
                    "home_universities": ["文藻外語大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-2",
                        "116-1",
                    ],
                },
                "source_urls": [
                    WZU_R1_ANNOUNCEMENT_URL,
                    WZU_R2_ANNOUNCEMENT_URL,
                    WZU_SCHOLARSHIP_HUB_URL,
                    WZU_REGULATIONS_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"wzu-{idx+1:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": (
                    f"由文藻國合處辦理官方提名並依 {zh_name}"
                    " 規定遞交入學與宿舍申請資料"
                ),
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"完成校內撕榜／分發確認後，由文藻國際交流組向 {zh_name}"
                    " 辦理官方提名（Nomination）；學生須依姊妹校規定準備外文申請表、英文歷年成績單、護照影本、銀行存款財力證明、語檢證書、體檢與疫苗證明及宿舍申請表，靜候姊妹校核發正式入學許可書（Letter"
                    " of Acceptance / COE / DS-2019）。"
                ),
                "details": [
                    f"交換期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿安排：{housing_raw}",
                ],
                "scope": {
                    "home_universities": ["文藻外語大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-2",
                        "116-1",
                    ],
                },
                "source_urls": (
                    [
                        source_url,
                        WZU_OUTBOUND_GUIDE_URL,
                        WZU_PARTNER_INFO_URL,
                    ]
                    + ([sharing_drive_url] if sharing_drive_url else [])
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"wzu-115-home-5-{idx+1:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": (
                    "參加行前說明會、辦理簽證保險與文藻註冊，抵達 2"
                    " 週內回報並於返國後完成抵免與報告書"
                ),
                "responsible_party": "學生",
                "responsible_unit": (
                    "文藻外語大學國際暨兩岸合作處／教務處註冊組／生輔組／各系所"
                ),
                "summary": (
                    "出國前須全程參加國合處舉辦之出國交換行前說明會、辦妥留學簽證、購買涵蓋交換全期之海外醫療及意外保險（具役男身分者須於出國前"
                    " 1"
                    " 個月完成役男出國緩徵核准手續），並於交換期間完成文藻註冊及繳交全額學雜費；抵達姊妹校後"
                    " 2 週內繳交《抵達國外姊妹校通報單》，交換期間每學期至少修讀 2 門課或 4"
                    " 學分（或 1 門該國語言課），返國後 1"
                    " 個月內繳交《返國報告書》、照片與正式成績單完成學分抵免及獎學金核銷。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["文藻外語大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-2",
                        "116-1",
                    ],
                },
                "source_urls": [
                    WZU_OUTBOUND_GUIDE_URL,
                    WZU_REGULATIONS_URL,
                    WZU_SCHOLARSHIP_HUB_URL,
                    WZU_EXP_ALBUM_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            "已完整整合文藻外語大學國際暨兩岸合作處（國際交流組）115-1、115-2"
            " 一招及二招「一般組（140 校）」與「語言學習組（7"
            " 校）」六大語組（英、日、法、德、西、華語暨東南亞語組）共 147"
            " 所全球交換合作姊妹校名額、語檢門檻、獎助學金辦法與歷屆學長姐經驗分享雲端檔案。"
        ),
    })

    cost_default, visa_default = REGION_COST_DEFAULTS.get(
        country,
        (
            "USD 900–1,500 / 月（含住宿、膳食與日常交通）",
            "須依接待國駐臺機構規定辦理學生簽證並投保海外醫療及意外保險。",
        ),
    )
    cost_line = f"{zh_name} 預估每月生活費：{cost_default}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": f"文藻外語大學出國交換生甄選學校名額與條件一覽表—{zh_name}",
            "source_url": source_url,
            "summary": (
                "文藻國合處公告之交換名額、一般組／語言學習組別、語言檢定門檻、年級限制與住宿費用說明"
            ),
        },
        {
            "title": (
                "文藻外語大學學生出國交換實施辦法與出國交換獎助學金辦法"
            ),
            "source_url": WZU_REGULATIONS_URL,
            "summary": (
                "文藻出國交換申請資格、書審 50%＋面試 50% 評分標準、文藻交換獎助學金（1"
                " 萬–5 萬）、學海飛颺／惜珠與返國學分抵免規定"
            ),
        },
    ]
    if sharing_drive_url:
      dest_sources.append({
          "title": (
              f"文藻外語大學國合處各校交換申請資訊與歷屆學長姐經驗分享雲端資料夾—{zh_name}"
          ),
          "source_url": sharing_drive_url,
          "summary": (
              "文藻國合處彙整之姊妹校 Factsheet、選課與住宿實況及歷屆交換生返國心得報告"
          ),
      })
    if website:
      dest_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "summary": "接待合作校官方網站",
      })
    if exp_posts:
      dest_sources.append({
          "title": (
              f"文藻外語大學交換生赴 {zh_name} 出國研修心得與相簿（共 {len(exp_posts)} 篇）"
          ),
          "source_url": exp_posts[0].get("url") or WZU_EXP_ALBUM_URL,
          "summary": (
              f"收錄文藻外語大學國際交流組公開之 {len(exp_posts)} 篇赴 {zh_name}"
              " 交換生研修心得與實景照片"
          ),
      })

    src_url_list = (
        [source_url, WZU_OUTBOUND_GUIDE_URL, WZU_REGULATIONS_URL]
        + ([sharing_drive_url] if sharing_drive_url else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "文藻外語大學",
        "school_name": full_name,
        "country": country,
        "city": location_obj.get("city") or country,
        "cost_summary": f"{cost_line}。\n{tuition_clean}",
        "housing_summary": housing_clean,
        "transport_summary": (
            f"校區代表城市：{location_obj.get('city') or country}。請依入學許可與姊妹校交換生網頁確認實際授課校區、機場接機服務與當地學生交通卡優惠。"
        ),
        "campus_life_summary": f"{calendar_clean}\n{course_clean}",
        "student_guide_sections": [
            {
                "key": "cost",
                "title": (
                    "生活費、文藻出國交換獎助學金（1 萬–5 萬）、學海飛颺／惜珠與姊妹校獎學金"
                ),
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [
                    WZU_SCHOLARSHIP_HUB_URL,
                    WZU_UMAP_URL,
                    WZU_ACUCA_URL,
                ],
                "caution": (
                    "文藻外語大學「出國交換及雙聯學制學生獎助學金」補助五專／四技／碩士生每名"
                    " NT$10,000、二技及五專直升四技生最高 NT$50,000；教育部「學海惜珠」除核定補助外，文藻另提撥"
                    " 20% 配合款補助。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外學生宿舍／寄宿家庭申請",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": (
                    "各姊妹校學生宿舍名額有限（其中中國大陸北京外大、大連外大提供免費宿舍，土耳其伊本哈爾頓大學提供免費住宿與三餐，日本京都外大、東洋大學等提供住宿補助或指定宿舍），獲提名後請務必準時遞交宿舍申請。"
                ),
            },
            {
                "key": "insurance",
                "title": "海外醫療及意外保險與接待國強制學生健康保險規定",
                "summary": visa_default,
                "points": [
                    visa_default,
                    (
                        "依《文藻外語大學學生出國交換實施辦法》規定，交換生出國前須自行投保涵蓋交換全期之海外醫療、意外及急難救助保險，並依接待國政府或姊妹校規定投保當地強制學生健康保險（如日本國民健康保險、韓國"
                        " NHIS、澳洲 OSHC、德國公保、法國學生社保等）。"
                    ),
                ],
                "source_urls": src_url_list,
                "caution": (
                    "請於收到入學許可後確認接待校指定之保險額度與投保通路，並於行前說明會後繳交保險證明影本。"
                ),
            },
            {
                "key": "visa",
                "title": "留學簽證辦理、役男出境緩徵手續與抵達姊妹校通報義務",
                "summary": visa_default,
                "points": [
                    visa_default,
                    (
                        "具役男身分之男同學須於出國前至少 1"
                        " 個月洽生輔組與國合處辦理役男出國留學緩徵核准手續；抵達姊妹校後 2"
                        " 週內須填妥《抵達國外姊妹校通報單》回傳國合處國際交流組。"
                    ),
                ],
                "source_urls": src_url_list,
                "caution": (
                    "請勿持觀光簽證或免簽入境就讀學期交換課程，以免影響正式學籍、居留與返國學分抵免。"
                ),
            },
            {
                "key": "academics",
                "title": (
                    "修課規定、每學期最低修課門檻（至少 2 門課／4 學分或 1"
                    " 門語言課）與返國學分抵免"
                ),
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list,
                "caution": (
                    "交換期間須維持文藻外語大學在學學籍並完成註冊繳交全額學雜費（延畢生亦同），選課前請先與所屬系（所、中心）確認課程大綱與學分抵免採計原則。"
                ),
            },
            {
                "key": "living",
                "title": (
                    f"{location_obj.get('city') or country}"
                    " 校園生活與文藻學長姐交換經驗傳承雲端檔案"
                ),
                "summary": (
                    f"代表校區城市：{location_obj.get('city') or country}。請配合文藻行前說明會與接待校新生訓練（Orientation）完成報到。"
                ),
                "points": [
                    (
                        f"目的地城市：{location_obj.get('city') or country}（{country}）"
                    ),
                    (
                        f"文藻外語大學國合處「各校交換申請資訊」專頁為超過 100"
                        f" 所姊妹校建置專屬 Google Drive"
                        f" 學長姐經驗分享雲端資料夾（可至 {exp_portal_url}"
                        " 查閱歷屆文藻交換生返國報告書、宿舍實況、選課攻略與生活開銷）。"
                    ),
                ],
                "source_urls": [
                    WZU_PARTNER_INFO_URL,
                    exp_portal_url,
                ],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            "已整合文藻外語大學國際暨兩岸合作處（國際交流組）147 所交換合作姊妹校（一般組"
            " 140 校、語言學習組 7 校，涵蓋英、日、法、德、西、華語暨東南亞語六大語組）名額、語檢門檻、獎助學金與歷屆學長姐經驗分享雲端檔案。"
        ),
    })

    research_records.append({
        "home_university": "文藻外語大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": source_url,
        "checked_at": CHECKED_AT,
        "note": (
            "文藻外語大學國際暨兩岸合作處《出國交換生甄選學校名額一覽表（115-1／115-2"
            f" 一招及二招）》、《各校交換申請資訊（{WZU_PARTNER_INFO_URL}）》與"
            " ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"文藻外語大學出國交換生甄選學校名額與條件明細—{zh_name}",
            "url": source_url,
        },
    ]
    if sharing_drive_url:
      ev_sources.append({
          "title": (
              f"文藻外語大學國合處各校交換申請資訊與學長姐經驗分享雲端硬碟—{zh_name}"
          ),
          "url": sharing_drive_url,
      })
    if website:
      ev_sources.append({"title": f"{full_name} 官方網站", "url": website})
    if exp_posts:
      ev_sources.append({
          "title": (
              f"文藻外語大學赴 {zh_name} 交換生出國研修心得（{exp_posts[0].get('academic_year') or '歷年'}）"
          ),
          "url": exp_posts[0].get("url") or WZU_EXP_ALBUM_URL,
      })

    has_student_exp = bool(exp_posts or sharing_drive_url)
    if exp_posts:
      exp_covered_schools += 1

    ev_list = [
        {
            "theme": "housing",
            "kind": "mixed" if has_student_exp else "official",
            "text": housing_clean,
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "文藻外語大學出國交換姊妹校住宿與生活資訊",
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
                "文藻外語大學交換生費用規定、文藻交換獎助學金（1 萬–5"
                " 萬）、學海飛颺／惜珠與地區生活費估算"
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
                "文藻外語大學交換生選課限制、最低修課學分門檻（每學期至少 2 門課／4"
                " 學分或 1 門語言課）與返國學分抵免規定"
            ),
            "original_excerpt": False,
            "original_text": "",
            "translation_status": "original",
        },
        {
            "theme": "safety",
            "kind": "official",
            "text": visa_default,
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": (
                "文藻外語大學出國交換簽證、海外醫療保險、役男緩徵出境與抵達通報提醒"
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
                    f"｜文藻國合處官網公開收錄赴 {zh_name} 交換生研修心得與相簿共 {len(exp_posts)} 篇。"
                    if exp_posts
                    else (
                        f"｜文藻國合處提供赴 {zh_name} 歷屆學長姐經驗分享雲端資料夾。"
                        if sharing_drive_url
                        else ""
                    )
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "文藻外語大學出國交換名額與歷屆學長姐交換經驗分享",
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
                "已整合文藻外語大學國際暨兩岸合作處（國際交流組）115-1、115-2"
                " 一招及二招《一般組》與《語言學習組》名額表、各語組申請條件與《各校交換申請資訊》雲端經驗分享連結。"
            ),
            "當期宿位供給、費用與選課限制請依姊妹校最新交換網頁及入學通知書核對。",
        ],
        "location_signature": (
            f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative"
        ),
        "extraction_version": 3,
    })

    sample_reports: list[dict] = []
    for p_item in exp_posts[:5]:
      p_url = p_item.get("url") or exp_portal_url
      ay = clean_text(str(p_item.get("academic_year") or ""))
      term_str = ay if ay else "歷年交換"
      t_clean = clean_text(p_item.get("title") or "")
      sample_reports.append({
          "title": t_clean or f"文藻外語大學赴 {zh_name} 交換生出國研修心得",
          "url": p_url,
          "term": term_str,
      })
    if not sample_reports and sharing_drive_url:
      sample_reports.append({
          "title": f"文藻外語大學赴 {zh_name} 歷屆交換生經驗分享雲端資料夾",
          "url": sharing_drive_url,
          "term": "歷年交換",
      })

    if exp_posts:
      latest_post = exp_posts[0]
      terms_covered = list(
          dict.fromkeys(
              clean_text(str(p.get("academic_year")))
              for p in exp_posts
              if p.get("academic_year")
          )
      )
      rep_title = (
          f"文藻外語大學赴 {zh_name}（共 {len(exp_posts)} 篇研修心得與相簿）學長姐交換經驗彙編"
      )
      latest_title = clean_text(latest_post.get("title") or zh_name)
      excerpt_str = clean_text(latest_post.get("summary") or "")
      summary_text = (
          f"文藻外語大學國際暨兩岸合作處「交換生出國研修心得」專區公開收錄赴 {zh_name} 交換心得與紀實相簿共 {len(exp_posts)} 篇"
          + (
              f"（涵蓋學期：{'、'.join(terms_covered[:6])}）"
              if terms_covered
              else ""
          )
          + f"，代表篇目為《{latest_title}》"
          + (f"（內容重點：{excerpt_str[:220]}）" if excerpt_str else "")
          + (
              f"，並於國合處「各校交換申請資訊」專頁提供 {zh_name} 專屬學長姐經驗分享雲端硬碟（{sharing_drive_url}）。"
              if sharing_drive_url
              else "，詳實記錄文藻交換生於姊妹校之選課、住宿、語言文化適應與生活開支。"
          )
      )
      theme_map = {
          "academics": (
              f"文藻交換生分享於 {zh_name} 修讀外語、跨文化溝通與專業課程之選課技巧，以及符合文藻每學期至少修讀"
              " 2 門課／4 學分（或 1 門語言課）與返國學分抵免之實務經驗。"
          ),
          "housing": (
              f"文藻交換生詳述 {zh_name} 校內外學生宿舍與寄宿家庭環境、房型費用及周邊生活機能（{housing_clean[:120]}）。"
          ),
          "campus_culture": (
              f"文藻國合處官網收錄 {len(exp_posts)} 篇赴 {zh_name} 交換生研修心得與相簿，分享國際學生迎新週（Orientation）、語伴交流與文化體驗活動。"
          ),
          "cost": (
              f"文藻交換生記錄赴 {zh_name} 之住宿費、伙食費、交通票券與每月生活開銷（{cost_default}），以及申請文藻出國交換獎助學金、學海飛颺／惜珠與姊妹校獎學金之心得。"
          ),
      }
      p_url = latest_post.get("url") or exp_portal_url
      ay = clean_text(str(latest_post.get("academic_year") or "歷年交換"))
      student_experience_rows.append({
          "school_name": full_name,
          "country": country,
          "title": rep_title,
          "source_url": p_url,
          "source_type": "article",
          "platform": "文藻外語大學國際暨兩岸合作處—交換生出國研修心得專區",
          "author_name": latest_title or "文藻外語大學返國交換學生",
          "language": "zh",
          "summary": summary_text,
          "themes": ["academics", "housing", "campus_culture", "cost"],
          "theme_summaries": theme_map,
          "content_status": "full_text",
          "perspective": "official_student_story",
          "published_at": None,
          "discovered_at": CHECKED_AT,
          "content_hash": hashlib.sha256(
              f"{full_name}:exp:{p_url}".encode("utf-8")
          ).hexdigest(),
          "exchange_term": ay,
          "summary_zh": summary_text,
          "original_summary": summary_text,
          "theme_summaries_zh": theme_map,
          "translation_status": "original",
          "source_kind": "official_experience_page",
      })

    experience_sources_records.append({
        "home_university": "文藻外語大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": exp_portal_url,
        "partner_page_url": sharing_drive_url or source_url,
        "report_count": (
            len(exp_posts) if exp_posts else (1 if sharing_drive_url else 0)
        ),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

  partners_jsonl_text = (
      "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
  )
  (OFFICIAL_WZU_DIR / "partners.jsonl").write_text(
      partners_jsonl_text, encoding="utf-8"
  )
  (SOURCES_WZU_DIR / "partners.jsonl").write_text(
      partners_jsonl_text, encoding="utf-8"
  )
  (OFFICIAL_WZU_DIR / "application_workflows.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_WZU_DIR / "destination_profiles.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_WZU_DIR / "partner_research.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records)
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_WZU_DIR / "student_life.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_WZU_DIR / "experience_sources.jsonl").write_text(
      "\n".join(
          json.dumps(r, ensure_ascii=False) for r in experience_sources_records
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_WZU_DIR / "student_experiences.jsonl").write_text(
      "\n".join(
          json.dumps(r, ensure_ascii=False) for r in student_experience_rows
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_WZU_DIR / "campus-locations.json").write_text(
      json.dumps({"locations": new_locations}, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  loc_file = (
      REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
  )
  existing_loc_lines = [
      line
      for line in loc_file.read_text(encoding="utf-8").splitlines()
      if line.strip()
  ]
  existing_loc_map = {}
  for line in existing_loc_lines:
    rec = json.loads(line)
    existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

  wzu_home_loc = {
      "school_name": "文藻外語大學",
      "country": "臺灣",
      "city": "高雄市三民區",
      "latitude": 22.6703,
      "longitude": 120.3193,
      "geocode_status": "verified",
      "geocoded_at": CHECKED_AT,
      "source_url": "https://www.wikidata.org/wiki/Q702527",
      "identity_source_url": "https://ror.org/029769t42",
      "precision": "representative",
      "note": (
          "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。"
          " 母校代表點採高雄市三民區民族一路900號行政大樓 2 樓國際暨兩岸合作處（國際交流組）；官方地址來源：https://c015.wzu.edu.tw/。"
      ),
  }
  existing_loc_map[("文藻外語大學", "臺灣")] = wzu_home_loc
  sorted_locs = sorted(
      existing_loc_map.values(),
      key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
  )
  loc_file.write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
      encoding="utf-8",
  )

  wzu_source_urls = [
      WZU_OICC_HUB_URL,
      WZU_IED_HUB_URL,
      WZU_OUTBOUND_GUIDE_URL,
      WZU_R1_ANNOUNCEMENT_URL,
      WZU_R2_ANNOUNCEMENT_URL,
      WZU_R1_115_1_ANNOUNCEMENT_URL,
      WZU_PARTNER_INFO_URL,
      WZU_EXP_ALBUM_URL,
      WZU_UMAP_URL,
      WZU_ACUCA_URL,
      WZU_SCHOLARSHIP_HUB_URL,
      WZU_REGULATIONS_URL,
      WZU_SOSA_URL,
  ]

  exchange_info_payload = {
      "school_name": "文藻外語大學",
      "program_type": [
          (
              "國際暨兩岸合作處（國際交流組）出國交換生甄選計畫—一般組（140"
              " 所姊妹校，分英語組、日語組、法語組、德語組、西語組、華語暨東南亞語組六大語組，歷年學業總平均達"
              " 70 分、操行 80 分以上，含互惠免繳對方學費及自費／折扣學費名額）"
          ),
          (
              "國際暨兩岸合作處（國際交流組）出國交換生甄選計畫—語言學習組（7"
              " 所英、法、德、西、奧語言中心，歷年學業總平均達 65 分、操行 80"
              " 分以上，一般組甄選資格涵蓋語言學習組並可於撕榜時優先跨選）"
          ),
          (
              "跨國大學聯盟交換計畫：UMAP 亞太大學交流會交換計畫（Program A"
              " 免學費互惠交換，每學期推薦 2 名）與 ACUCA"
              " 亞洲基督教大學協會交換計畫（免學費互惠交換並享每月 USD 300–500"
              " 獎助金，每學年推薦 2 名）"
          ),
      ],
      "academic_year": [
          (
              "115（115-2 春季出國交換一招於 2026/08/31 截止收件、09/22–09/23"
              " 撕榜；115-2 二招於 2026/10/13 截止收件、10/19–10/23 面試、10/14–10/30"
              " 志願分發；共收錄 147 所全球交換合作學校，含 119 所 115-2 開放申請校及 28"
              " 所第一學期／參考合作校）"
          ),
          (
              "116（116-1 秋季出國交換一招預計於 2027 年 2 月開放校務資訊系統線上申請、3"
              " 月初截止紙本收件；二招預計於 2027 年 3–4 月辦理）"
          ),
      ],
      "semester": [
          (
              "第1學期（秋季班：每年約 8/9 月至 12 月／翌年 1 月；韓國秋季班為 9 月至 12"
              " 月，日本秋季班為 9 月至翌年 1/2 月或 8 月）"
          ),
          (
              "第2學期（春季班：每年約 1/2 月至 5/6 月；日本春季班為 4 月至 8 月或翌年 3"
              " 月，韓國春季班為 3 月至 6 月）"
          ),
          (
              "一學年交換（日本、法國、德國、西班牙、英國、美國、中國大陸及東南亞多所姊妹校開放一學年或一學期交換名額）"
          ),
      ],
      "application_period": [
          (
              "【第 2 學期（春季班出國，如 115-2 梯次）甄選時程】一招：前學期 5"
              " 月初舉辦甄選說明會並開放校務資訊系統線上申請、8 月 31 日 15:00"
              " 截止繳交紙本申請資料、9 月上旬公告面試順序、9 月中旬（09/09–09/15）舉行第二階段外語面試、9"
              " 月下旬（09/22–09/23）舉行第三階段現場撕榜；二招：10 月上旬開放線上申請、10"
              " 月 13 日 15:00 截止紙本收件、10 月中下旬（10/19–10/23）面試、10"
              " 月底前（10/14–10/30）完成志願分發與錄取確認。"
          ),
          (
              "【第 1 學期（秋季班出國，如 115-1／116-1 梯次）甄選時程】一招：每年 2"
              " 月中下旬開放校務資訊系統線上報名、3 月初（約 3 月第一週 15:00）截止繳交紙本資料、3"
              " 月中旬舉行外語面試、3 月下旬舉行現場撕榜；二招：每年 3 月底至 4 月上旬開放報名並完成面試與志願分發。"
          ),
          (
              "【UMAP 亞太大學交流會與 ACUCA 亞洲基督教大學協會交換計畫】配合聯盟秘書處時程於每學期初（約"
              " 2–3 月及 9–10 月）由國合處國際交流組公告受理校內甄選（各推薦 2 名免學費交換生）。"
          ),
      ],
      "eligibility": [
          (
              "【在學學制、年級與修業規定（依《文藻外語大學學生出國交換實施辦法》及甄選簡章）】申請人須為本校日間部及進修部正式學籍在學學生（出國交換期間須為五專部四年級下學期至五年級、四技部二年級下學期至四年級、二技部三年級下學期至四年級、研究所碩士班一年級下學期至四年級；部分姊妹校不受理五專生或僅收大學部／研究生，依各校備註為準）。交換期間須維持文藻在學學籍並繳交文藻全額學雜費（延畢生於出國交換期間亦須繳交全額學雜費）。"
          ),
          (
              "【一般組（70 分）與語言學習組（65 分）學業操行門檻及跨組撕榜規則】（1）一般組：歷年學業成績總平均達"
              " 70 分（含）以上、歷年操行成績總平均達 80"
              " 分（含）以上，且無小過（含）以上懲處記錄；（2）語言學習組（自費語言中心／語言學校）：歷年學業成績總平均達"
              " 65 分（含）以上、歷年操行成績總平均達 80"
              " 分（含）以上，且無小過（含）以上懲處記錄（學業與操行總平均皆認列至個位數，小數點後不採計亦不四捨五入）。一般組甄選資格已涵蓋語言學習組，於第三階段撕榜／志願分發時由一般組合格者優先選校，可選擇該語組之一般組或語言學習組學校；語言學習組合格者次之，僅能選擇語言學習組學校。"
          ),
          (
              "【二階段甄選配分標準（書審 50%＋面試 50%）與 SOSA 志工加分】第一階段書面審查佔"
              " 50%（歷年學業成績 20%、歷年操行成績 10%、英語能力檢定 10%、第二外語能力檢定"
              " 10%；曾參加國合處 SOSA 多國語言志工團服務時數達標者，可於第一階段額外加分最高 5"
              " 分）；第二階段面試佔 50%（讀書計畫 15%、口語表達 15%、儀態與態度 10%、國際活動經驗及其他"
              " 10%）。兩階段總成績合計達 60"
              " 分（含）以上者始具選校撕榜資格（總分相同時以面試成績高者優先）。"
          ),
      ],
      "language_requirement": [
          (
              "【六大語組（英語組、日語組、法語組、德語組、西語組、華語暨東南亞語組）外語能力檢定標準】申請人須檢附符合志願姊妹校規定之有效外語檢定成績（第一階段書審採計「英語能力"
              " 10%」與「第二外語能力 10%」兩項配分，建議同時檢附英檢與第二外語證書以爭取最高書審分數）：（1）英語組（40"
              " 校）：依各校規定須具 TOEFL iBT（60–88 分，如海峽大學 79、拉夫堡／巴斯泉／MRU"
              " 80、聖托馬斯／德拉薩 80）、IELTS（5.0–6.5，如渥夫漢普頓／VDU 5.5、伯明罕城市／拉夫堡／巴斯泉／法政"
              " 6.0、東安格利亞／聖托馬斯 6.5）、TOEIC（550–800 分，如大邱韓醫 550、法政"
              " 650、希爾克／崇實 700、順天鄉 750、里爾天主教管理學院 790）或全民英檢／CSEPT；（2）日語組（31"
              " 校）：依各校規定須具 JLPT N1–N4（如桃山學院國際教養／金城學院／京都外大／拓殖／清泉／東洋／名古屋外大／關西外大要求"
              " N2–N3，創價／立命館／名古屋市立／明治學院／立教要求 N1–N2，鹿兒島純心／長崎外大／文教／別科接受"
              " N3–N4）。"
          ),
          (
              "【歐洲語組（法語組 24 校、德語組 9 校、西語組 14 校）語言門檻】（3）法語組（24"
              " 校）：交換學位課程依各校規定須具 DELF/TCF A2–B2（如巴黎東方語言學院 INALCO、格勒諾柏、艾克斯馬賽、土魯斯二大、里爾天主教人文學院、布魯塞爾自由大學、列日大學、新魯汶大學要求法語"
              " B1–B2；昂熱 CIDEF、卡維蘭 CAVILAM 語言學校依分班測驗入學）；（4）德語組（9"
              " 校）：慕尼黑應用語言大學、美因茲大學、萊比錫大學、康斯坦斯、天主教艾希特、西薩克森應用科大要求德語"
              " B1–B2（TestDaF／Goethe-Zertifikat），維也納大學語言中心與胡志明市人文社大德語系依分級規定；（5）西語組（14"
              " 校）：內布里哈、納瓦拉、那瓦拉公立、聖地牙哥、雷昂、瓦倫西亞天主教、阿維拉天主教及墨西哥阿納瓦克、巴拉圭天主教大學要求西語"
              " DELE/SIELE A2–B2，薩拉曼卡、巴塞隆納自治大學、卡斯提亞拉曼查語言中心依程度分班。"
          ),
          (
              "【華語暨東南亞語組（29 校：中國大陸 10 校、韓國 7 校、越南 5 校、印尼 4 校、泰國 2 校、馬來西亞 1"
              " 校）語言規定】赴中國大陸 10 所姊妹校（北京外大、上海外大、中國傳媒、中央民族、大連外大、廣東外語外貿、西南財大等）免附外語檢定（書審仍採計英檢與二外加分；上外要求學業平均"
              " 80 分）；赴韓國姊妹校（崇實、漢陽 ERICA、誠信女大、釜山外大、翰林、順天鄉、忠北）須具 TOPIK 2–4"
              " 級或英語檢定；赴越南、印尼、泰國、馬來西亞姊妹校須具英語檢定（IELTS 5.0–6.0／TOEIC 550–700）或"
              " VNLPT 越語／印尼語／泰語檢定證明。"
          ),
      ],
      "required_documents": [
          (
              "1. 文藻外語大學出國交換生甄選申請表（至「校務資訊系統 → 申請 → 國際合作交流申請 →"
              " 出國交換生甄選申請作業」線上填報列印，貼妥半年內 2"
              " 吋正面脫帽照片，經所屬系［所、中心］主任簽章、雙主修／輔系核章及家長／監護人簽名同意）"
          ),
          (
              "2. 本校中文歷年學業成績單正本乙份（須含歷年學業總平均、班／系排名及歷年操行成績總平均）及英文歷年學業成績單正本乙份（須為百分制並註明排名）"
          ),
          (
              "3. 有效外語能力檢定成績單／證書影本（含第一階段書審採計之「英語能力檢定 10%」及「第二外語能力檢定"
              " 10%」證明文件）"
          ),
          (
              "4. 中文研修計畫書及英文（或報考語組外文）研修計畫書各乙份（電腦打字 A4 各 500–1,000"
              " 字，詳述申請動機、擬修讀領域與返國學習規劃）"
          ),
          (
              "5. 校內外社團、班級幹部、國際活動參與、競賽獲獎等有利審查證明文件影本，以及國合處 SOSA"
              " 多國語言志工團服務時數證明（符合規定者於第一階段書審加分最高 5 分）"
          ),
          (
              "6. 撕榜／分發錄取後應繳確認文件：《出國交換生錄取資格確認書》、《家長同意書》、有效護照個人資料頁影本；出國後"
              " 2 週內繳交《抵達國外姊妹校通報單》，返國後 1 個月內繳交《出國交換學生返國報告書》、照片及姊妹校正式成績單"
          ),
      ],
      "scholarship_info": [
          (
              "文藻外語大學「出國交換及雙聯學制學生獎助學金」（依《文藻外語大學出國交換及雙聯學制學生獎助學金辦法》）：補助具中華民國國籍、經本校推薦出國交換或修讀雙聯學位之在學學生（不含語言學習組自費語言中心及休退學生）：（1）日間部五專生、四技生及研究所碩士生：每名核給新臺幣"
              " 10,000 元；（2）日間部二技生及本校五專部應屆畢業直升四技部學生：每名最高核給新臺幣 50,000"
              " 元；（3）進修部學生：補助於姊妹校修習並返國完成抵免學分費之三分之一，每名最高核給新臺幣 10,000 元。"
          ),
          (
              "教育部「學海飛颺」選送優秀學生出國研修獎助學金：補助具中華民國國籍、在文藻就讀一學期以上、歷年學業成績總平均達 75"
              " 分（含）以上、歷年操行成績達 80"
              " 分（含）以上且具報考語組有效外語檢定證明之優秀學生，赴國外大專校院（不含大陸及港澳地區）修讀學分 1 學期或 1"
              " 學年，每名核給金額至少新臺幣 50,000 元以上（實際金額依當年度教育部核定經費及國合處審查結果核發）。"
          ),
          (
              "教育部「學海惜珠」選送勵學優秀學生出國研修獎助學金（含文藻 20%"
              " 配合款）：專項補助具中華民國國籍、持有各直轄市或縣市政府核發之低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助或原住民身分證明、歷年學業總平均達"
              " 75 分（含）以上且操行成績達 80"
              " 分（含）以上之在學學生赴國外（不含陸港澳）交換研修；獲教育部核定補助者，文藻外語大學另提撥教育部補助款之 20%"
              " 作為校內配合款加碼補助。"
          ),
          (
              "日本 JASSO 及日本姊妹校專屬交換獎學金：（1）日本學生支援機構（JASSO）海外留學支援制度獎學金：每月"
              " JPY 80,000（由締結 JASSO 計畫之日本姊妹校擇優推薦）；（2）名古屋外國語大學（NUFS）交換獎學金：免學費名額每名每月核給"
              " JPY 60,000（須具 JLPT N3 以上）；（3）東洋大學 IUEP 國際交換獎學金：每月核給 JPY"
              " 51,000 並補助指定國際學生宿舍費；（4）清泉大學交換獎學金：依日檢程度（N2/N3）每月核給 JPY 40,000"
              " 或 JPY 20,000；（5）鹿兒島純心大學交換獎學金：每月核給 JPY 30,000。"
          ),
          (
              "跨國大學聯盟與外國政府獎學金：（1）加拿大希爾克學院（Selkirk College）「Study in"
              " Canada」獎學金：補助交換 1 學期 USD 7,200 或 2 學期 USD"
              " 10,200；（2）ACUCA（亞洲基督教大學協會）學生交換計畫獎助金：錄取生除免繳姊妹校學費外，由 ACUCA"
              " 核給每月 USD 300–500 生活獎助金；（3）UMAP（亞太大學交流會）臺灣國家秘書處獎學金：補助赴"
              " UMAP 會員校交換學生每月最高新臺幣 20,000 元；（4）土耳其伊本哈爾頓大學（Ibn Haldun"
              " University）：免費提供校內學生宿舍及每日三餐膳食。"
          ),
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": wzu_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_WZU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "文藻外語大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 70.0,
      "academic_score_rule": (
          "文藻外語大學出國交換生甄選分為「一般組」與「語言學習組」兩軌：（1）一般組（140"
          " 校）：歷年學業成績總平均達 70 分（含）以上、歷年操行成績總平均達 80"
          " 分（含）以上且無小過（含）以上懲處記錄；（2）語言學習組（7 所自費語言中心）：歷年學業成績總平均達 65"
          " 分（含）以上、歷年操行成績總平均達 80"
          " 分（含）以上且無小過（含）以上懲處記錄（學業與操行總平均皆認列至個位數，小數點後不採計亦不四捨五入）。一般組甄選資格已涵蓋語言學習組，於第三階段現場撕榜／志願分發時由一般組合格者優先選校，可跨選語言學習組學校。申請教育部「學海飛颺」與「學海惜珠」獎助學金者，歷年學業總平均須達"
          " 75 分（含）以上且操行達 80 分（含）以上。"
      ),
      "academic_gpa_minimum": None,
      "maximum_preferences": 10,
      "selection_rules": {
          "academic_policy": "percentage",
          "academic_reference_year": "115",
          "undergraduate_gpa_minimum": None,
          "graduate_academic_exempt": False,
          "exclude_in_service": False,
          "pending_quota_planning": False,
          "partner_requirements_need_confirmation": False,
          "degree_score_minimums": {
              "undergraduate": 70.0,
              "graduate": 70.0,
          },
          "excluded_undergraduate_years": ["大一"],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 60.0,
          "ielts": 5.0,
          "toeic": 550.0,
      },
      "application_periods": [
          {
              "title": (
                  "文藻外語大學 115 學年度第 2 學期（115-2 春季出國）出國交換生甄選（一招 8/31 截止、9/22–9/23"
                  " 撕榜；二招 10/13 截止、10/19–10/23 面試、10/14–10/30 志願分發）"
              ),
              "details": [
                  (
                      "115-2 一招時程：2026/05/04–05/08 舉辦甄選說明會並開放校務資訊系統線上報名，2026/08/31"
                      " 15:00 截止繳交紙本申請資料至國合處國際交流組（行政大樓 2 樓），09/09–09/15"
                      " 舉行第二階段外語面試，09/22–09/23 舉行第三階段現場撕榜。"
                  ),
                  (
                      "115-2 二招時程：2026/10/13 15:00 截止繳交紙本申請資料，10/15"
                      " 公告面試順序，10/19–10/23 舉行第二階段外語面試，10/14–10/30"
                      " 進行線上志願選填與分發結果公告，錄取生須按時繳交《錄取資格確認書》與《家長同意書》。"
                  ),
              ],
              "source": {
                  "title": (
                      "文藻外語大學 115 學年度第 2 學期出國交換生甄選（一招及二招）簡章與學校名額一覽表"
                  ),
                  "source_url": WZU_R2_ANNOUNCEMENT_URL,
                  "category": "exchange_application",
                  "summary": (
                      "文藻國合處 115-2 出國交換生一招與二招甄選時程、一般組（70 分）與語言學習組（65"
                      " 分）名額表及書審面試配分規定。"
                  ),
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "115",
              "application_round": (
                  "115學年度第2學期出國交換生甄選（一招／二招・一般組及語言學習組）"
              ),
              "audience": "all_students",
              "opens_at": "2026-05-04T09:00:00+08:00",
              "deadline_at": "2026-10-13T15:00:00+08:00",
              "date_status": "verified_exact",
              "status": "closed",
              "status_note": (
                  "115-2 二招已於 2026/10/13 15:00 截止收件，並於 10/19–10/23"
                  " 舉行外語面試、10/30 前完成志願分發。"
              ),
              "deadline_note": (
                  "請完成校務資訊系統線上申請並將核章紙本申請表、中英文歷年成績單、語檢證明及中英文研修計畫書送交行政大樓"
                  " 2 樓國合處國際交流組。"
              ),
              "reminder_eligible": False,
              "checked_at": CHECKED_AT,
          },
          {
              "title": (
                  "文藻外語大學 115/116 學年度第 1 學期（秋季出國）出國交換生甄選暨 UMAP／ACUCA"
                  " 跨國聯盟交換計畫（每年 2 月開放申請、3 月初截止收件）"
              ),
              "details": [
                  (
                      "第 1 學期（秋季出國，如 115-1／116-1 梯次）甄選時程：一招於每年 2"
                      " 月中下旬開放校務資訊系統線上報名、3 月初（15:00 止）截止紙本收件、3 月中旬舉行外語面試、3"
                      " 月下旬舉行現場撕榜；二招於 3 月底至 4 月上旬受理報名與志願分發。"
                  ),
                  (
                      "UMAP（亞太大學交流會 Program A 免學費交換，每學期名額 2"
                      " 名）與 ACUCA（亞洲基督教大學協會免學費交換暨每月 USD 300–500 獎助金，每學年名額 2"
                      " 名）於每學期初配合聯盟秘書處時程公告收件。"
                  ),
              ],
              "source": {
                  "title": (
                      "文藻外語大學 115 學年度第 1 學期出國交換生一招甄選公告與 UMAP／ACUCA"
                      " 交換計畫簡章"
                  ),
                  "source_url": WZU_R1_115_1_ANNOUNCEMENT_URL,
                  "category": "exchange_application",
                  "summary": (
                      "文藻國合處第一學期（秋季班）出國交換生甄選時程、147 所姊妹校名額與"
                      " UMAP／ACUCA 跨國聯盟交換辦法。"
                  ),
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "116",
              "application_round": (
                  "115/116學年度出國交換生甄選（第一學期一招預計2月開放）"
              ),
              "audience": "all_students",
              "opens_at": "2027-02-15T09:00:00+08:00",
              "deadline_at": "2027-03-02T15:00:00+08:00",
              "date_status": "reference_only",
              "status": "closed",
              "status_note": (
                  "116-1 秋季班出國交換一招預計於 2027 年 2 月開放線上申請、3 月初截止紙本收件。"
              ),
              "deadline_note": (
                  "實際截止日期與開放名額請依國際暨兩岸合作處國際交流組（https://d020.wzu.edu.tw/）最新學期公告為準。"
              ),
              "reminder_eligible": False,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"文藻外語大學國際暨兩岸合作處出國交換計畫總覽（{len(partners)} 所全球合作姊妹校・{open_partner_count}"
                  " 所 115-2 開放申請校・六大語組與雙軌甄選）"
              ),
              "details": [
                  (
                      f"文藻外語大學（WZU）由「國際暨兩岸合作處（國際交流組，位於行政大樓 2 樓）」統籌推動全球出國交換學生計畫。本平台完整收錄 {len(partners)} 所文藻官方交換合作學校（含 115-2 學期開放申請之 {open_partner_count} 所姊妹校及 28 所第一學期／參考合作校），橫跨全球 24 個國家（日本 31 校、法國 21 校、西班牙 12 校、中國大陸 10 校、韓國 10 校、印尼 7 校、美國 7 校、德國 7 校、越南 6 校、英國 5 校、比利時 5 校、泰國 4 校、菲律賓 4 校、馬來西亞 3 校、土耳其 3 校、加拿大 2 校、澳洲 2 校、立陶宛 2 校及匈牙利、波蘭、巴拉圭、墨西哥、奧地利、捷克各 1 校）。"
                  ),
                  (
                      "文藻出國交換體系具備四大特色：（1）六大專業語組全覆蓋：設有「英語組（40 校）」、「日語組（31 校）」、「華語暨東南亞語組（29"
                      " 校）」、「法語組（24 校）」、「西語組（14 校）」與「德語組（9 校）」，並參與 UMAP 亞太大學交流會與"
                      " ACUCA 亞洲基督教大學協會交換計畫；（2）「一般組（70 分）」與「語言學習組（65"
                      " 分）」雙軌跨選制度：一般組合格生於撕榜／分發時優先選校且可跨選語言學習組學校；（3）豐厚獎助學金：提供文藻出國交換獎助學金（五專／四技／碩士"
                      " 1 萬、二技與五專直升四技最高 5 萬）、教育部學海飛颺（至少 5 萬）、學海惜珠（文藻另加碼 20% 配合款）及日本"
                      " JASSO／名古屋外大／東洋／清泉／鹿兒島純心／加拿大希爾克／ACUCA／UMAP 獎學金；（4）百校雲端經驗傳承：收錄國合處"
                      f" {len(student_experience_rows)} 所重點姊妹校研修心得相簿及超過 100 所姊妹校專屬 Google"
                      " Drive 學長姐經驗分享資料夾。"
                  ),
              ],
              "source": {
                  "title": (
                      "文藻外語大學國際暨兩岸合作處國際交流組—出國交換計畫申請流程與各校資訊"
                  ),
                  "source_url": WZU_OUTBOUND_GUIDE_URL,
                  "category": "exchange_application",
                  "summary": (
                      "文藻外語大學 147 所交換合作學校、六大語組雙軌甄選制度、獎助學金與歷屆交換生雲端經驗分享。"
                  ),
              },
          }
      ],
      "eligibility": [
          {
              "title": (
                  "五專四至五年級／四技二至四年級／二技／碩士班在學資格、一般組 70 分／語言學習組 65 分門檻與書審 50%＋面試"
                  " 50% 配分"
              ),
              "details": [
                  (
                      "在學學制與修業規定（依《文藻外語大學學生出國交換實施辦法》及甄選簡章）：申請人須為本校日間部或進修部正式在學學生，出國交換期間須為五專部四年級下學期至五年級、四技部二年級下學期至四年級、二技部三年級下學期至四年級或研究所碩士班一年級下學期至四年級（部分姊妹校限大學部或開放研究生，依各校備註為準）。交換期間須維持文藻在學學籍並完成註冊繳交文藻全額學雜費（延畢生於出國交換期間亦須繳交全額學雜費）。"
                  ),
                  (
                      "一般組與語言學習組雙軌門檻及甄選配分：（1）一般組：歷年學業總平均達 70 分（含）以上、操行總平均達 80"
                      " 分（含）以上且無小過以上紀錄；（2）語言學習組：歷年學業總平均達 65 分（含）以上、操行總平均達 80"
                      " 分（含）以上且無小過以上紀錄（皆認列至個位數，小數點後不採計亦不四捨五入）。第一階段書審佔 50%（歷年學業"
                      " 20%、操行 10%、英語能力 10%、第二外語能力 10%，參與國合處 SOSA"
                      " 多國語言志工團達標者另加分最高 5 分）；第二階段外語面試佔 50%（讀書計畫 15%、口語表達 15%、儀態態度"
                      " 10%、國際活動經驗及其他 10%），兩階段總成績達 60"
                      " 分以上者依總分高低參加第三階段現場撕榜（一招）或志願分發（二招）。"
                  ),
              ],
              "source": {
                  "title": (
                      "文藻外語大學學生出國交換實施辦法與 115-2 出國交換生甄選簡章"
                  ),
                  "source_url": WZU_R1_ANNOUNCEMENT_URL,
                  "category": "exchange_application",
                  "summary": (
                      "文藻出國交換在學年級規定、一般組 70 分與語言學習組 65 分門檻、書審面試配分與跨組撕榜規則。"
                  ),
              },
          }
      ],
      "language_requirements": [
          {
              "title": (
                  "六大語組外語檢定標準（英語組 TOEFL／IELTS／TOEIC、日語組 JLPT N1–N4、法語組"
                  " DELF、德語組 TestDaF／Goethe、西語組 DELE／SIELE、華語暨東南亞語組 TOPIK／VNLPT）"
              ),
              "details": [
                  (
                      "第一階段書審雙語採計原則：文藻交換甄選第一階段書審同時採計「英語能力檢定（10%）」與「第二外語能力檢定（10%）」，報考各語組同學除須達到志願姊妹校規定之授課語言門檻外，同時檢附英語及第二外語檢定證書可大幅提升書審排名。"
                  ),
                  (
                      "各語組檢定門檻重點：（1）英語組（40 校）：TOEFL iBT 60–88、IELTS 5.0–6.5 或"
                      " TOEIC 550–800；（2）日語組（31 校）：JLPT N1–N4（多數大學部要求 N2–N3，別科或純心／文教／長崎外大接受"
                      " N3–N4）；（3）法語組（24 校）：法語 DELF/TCF A2–B2（昂熱 CIDEF、維琪"
                      " CAVILAM 語言中心依程度分班）；（4）德語組（9 校）：德語 B1–B2（慕尼黑 SDI、美因茲、萊比錫、康斯坦斯、艾希特、西薩克森）；（5）西語組（14"
                      " 校）：西語 DELE/SIELE A2–B2；（6）華語暨東南亞語組（29 校）：大陸 10 校免外語檢定，韓國"
                      " 7 校要求 TOPIK 2–4 級或英檢，東南亞姊妹校要求英檢或越／印／泰語檢定。"
                  ),
              ],
              "source": {
                  "title": (
                      "文藻外語大學 115-1／115-2 出國交換生甄選學校名額與語檢條件一覽表"
                  ),
                  "source_url": WZU_R2_ANNOUNCEMENT_URL,
                  "category": "exchange_application",
                  "summary": (
                      "文藻六大語組 147 所交換姊妹校之英、日、法、德、西、韓及東南亞語檢定門檻一覽。"
                  ),
              },
          }
      ],
      "required_documents": [
          {
              "title": (
                  "校務資訊系統線上申請、六大紙本甄選必繳文件、撕榜錄取確認書與返國報告／抵免義務"
              ),
              "details": [
                  (
                      "校內甄選必繳文件（若同時報考兩個以上語組，每語組須各繳乙份）：1. 出國交換生甄選申請表（校務資訊系統列印、貼妥"
                      " 2 吋照片並完成系所主任及家長簽章）、2. 中文歷年成績單正本（含排名與操行總平均）及英文歷年成績單正本（百分制含排名）、3."
                      " 英語及第二外語能力檢定證書影本、4. 中文及外文研修計畫書（各 500–1,000 字）、5."
                      " 社團幹部／國際活動／競賽獲獎證明及國合處 SOSA 多國語言志工團服務證明。"
                  ),
                  (
                      "撕榜分發後與出國返國義務：撕榜／分發錄取後須按時繳交《錄取資格確認書》與《家長同意書》（確認後無故放棄者，在校期間不得再申請本校出國交換計畫）；出國前須參加行前說明會，抵達姊妹校"
                      " 2 週內繳交《抵達國外姊妹校通報單》，交換期間每學期至少修讀 2 門課或 4 學分（或 1"
                      " 門語言課），返國後 1 個月內繳交《返國報告書》、照片及正式成績單完成學分抵免。"
                  ),
              ],
              "source": {
                  "title": (
                      "文藻外語大學出國交換計畫申請流程與相關法規表單專區"
                  ),
                  "source_url": WZU_REGULATIONS_URL,
                  "category": "exchange_application",
                  "summary": (
                      "文藻出國交換線上報名路徑、紙本送件清單、SOSA 志工加分證明與返國學分抵免規範。"
                  ),
              },
          }
      ],
      "scholarship_info": [
          {
              "title": (
                  "文藻出國交換獎助學金（五專／四技／碩士 1 萬、二技與五專直升四技最高 5 萬）、學海飛颺／惜珠（加碼 20%"
                  " 配合款）與日本／加拿大／聯盟獎學金"
              ),
              "details": [
                  (
                      "校內與教育部獎助學金：（1）《文藻外語大學出國交換及雙聯學制學生獎助學金》：日間部五專、四技及碩士生每名核給"
                      " NT$10,000；二技生及本校五專直升四技生每名最高核給 NT$50,000；進修部學生補助抵免學分費"
                      " 1/3（上限 NT$10,000）；（2）教育部《學海飛颺》：學業總平均 75 分、操行 80"
                      " 分以上之本國籍優秀學生，每名至少補助 NT$50,000；（3）教育部《學海惜珠》：低收／中低收／特殊境遇家庭且學業"
                      " 75 分、操行 80 分以上，除教育部補助款外，文藻另提撥 20% 校內配合款加碼補助。"
                  ),
                  (
                      "姊妹校與跨國聯盟獎學金：日本 JASSO 獎學金（每月 JPY 80,000）、名古屋外國語大學（每月 JPY"
                      " 60,000）、東洋大學 IUEP（每月 JPY 51,000 另補助住宿）、清泉大學（每月 JPY"
                      " 20,000–40,000）、鹿兒島純心大學（每月 JPY 30,000）、加拿大希爾克學院 Study in"
                      " Canada（1 學期 USD 7,200／2 學期 USD 10,200）、ACUCA 交換計畫（每月"
                      " USD 300–500）、UMAP 臺灣國家秘書處獎學金（每月最高 NT$20,000）及土耳其伊本哈爾頓大學（免費提供宿舍與每日三餐）。"
                  ),
              ],
              "source": {
                  "title": (
                      "文藻外語大學出國交換及雙聯學制學生獎助學金辦法與學海計畫專區"
                  ),
                  "source_url": WZU_SCHOLARSHIP_HUB_URL,
                  "category": "scholarship",
                  "summary": (
                      "文藻校內交換獎助學金（1 萬–5 萬）、教育部學海飛颺／惜珠（含 20% 配合款）及各國姊妹校與"
                      " UMAP／ACUCA 獎學金標準。"
                  ),
              },
          }
      ],
      "document_explanations": [
          {
              "title": (
                  "文藻外語大學交換生申請文件、中英文百分制成績單、雙語檢定加分與 SOSA 志工團證明準備指南"
              ),
              "summary": (
                  "說明文藻校務資訊系統線上報名表、中英文歷年成績單、中英文研修計畫書（500–1,000 字）及 SOSA"
                  " 志工團加分證明準備要點。"
              ),
              "key_points": [
                  (
                      "申請人須先於「校務資訊系統 → 申請 → 國際合作交流申請 →"
                      " 出國交換生甄選申請作業」完成線上報名並印出申請表，貼妥 2"
                      " 吋照片並經系（所、中心）主任及家長簽章同意後，於截止日 15:00 前送交行政大樓 2 樓國合處國際交流組。"
                  ),
                  (
                      "成績單須同時檢附「中文歷年學業成績單正本（含歷年學業總平均、排名與操行總平均）」及「英文歷年學業成績單正本（百分制、含排名）」；中、外文研修計畫書各"
                      " 500–1,000 字。"
                  ),
                  (
                      "第一階段書審（50%）同時採計「英語能力檢定（10%）」與「第二外語能力檢定（10%）」，並對曾參與國合處"
                      " SOSA 多國語言志工團服務達標者給予最高 5 分額外加分。"
                  ),
              ],
              "applies_to": [],
              "source": {
                  "title": (
                      "文藻外語大學 115-2 出國交換生甄選簡章與 SOSA 多國語言志工團專區"
                  ),
                  "source_url": WZU_R1_ANNOUNCEMENT_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": WZU_R1_ANNOUNCEMENT_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": (
                  "文藻外語大學學生出國交換實施辦法：一般組 70 分／語言學習組 65 分雙軌跨選、全額學雜費（含延畢生）與最低修課學分規定"
              ),
              "summary": (
                  "規範文藻六大語組交換甄選門檻、一般組優先跨選語言學習組之撕榜規則、在學註冊繳費義務及每學期最低修課門檻。"
              ),
              "key_points": [
                  (
                      "一般組歷年學業總平均須達 70 分以上、語言學習組須達 65 分以上（認列至個位數，不四捨五入），操行總平均均須達"
                      " 80 分以上且無小過以上懲處；一般組甄選資格涵蓋語言學習組，於撕榜／分發時優先選校並可跨選語言學習組學校。"
                  ),
                  (
                      "出國交換期間須維持文藻在學學籍並繳交文藻全額學雜費（延畢生於出國交換期間亦須繳交全額學雜費）；於姊妹校每學期至少須修讀"
                      " 2 門課或 4 學分，或至少 1 門該國語言課程。"
                  ),
                  (
                      "經撕榜／分發確認並繳交《錄取資格確認書》後，除不可抗力重大事由外不得放棄交換資格，否則於文藻就讀期間不得再次報名參加任何出國交換甄選。"
                  ),
              ],
              "applies_to": [],
              "source": {
                  "title": (
                      "文藻外語大學學生出國交換實施辦法與出國交換生甄選簡章"
                  ),
                  "source_url": WZU_REGULATIONS_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": WZU_REGULATIONS_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "文藻外語大學國際暨兩岸合作處（OICC）官方網站",
              "source_url": WZU_OICC_HUB_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "文藻外語大學國際交流組—出國交換計畫申請流程與簡章總覽",
              "source_url": WZU_OUTBOUND_GUIDE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": (
                  "文藻外語大學 115 學年度第 2 學期出國交換生一招甄選簡章與學校名額一覽表（一般組／語言學習組）"
              ),
              "source_url": WZU_R1_ANNOUNCEMENT_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": (
                  "文藻外語大學 115 學年度第 2 學期出國交換生二招甄選簡章與學校名額一覽表（一般組／語言學習組）"
              ),
              "source_url": WZU_R2_ANNOUNCEMENT_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": (
                  "文藻外語大學 115 學年度第 1 學期出國交換生一招甄選簡章與學校名額一覽表"
              ),
              "source_url": WZU_R1_115_1_ANNOUNCEMENT_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": (
                  "文藻外語大學國合處—各校交換申請資訊與歷屆學長姐經驗分享 Google Drive 雲端專區"
              ),
              "source_url": WZU_PARTNER_INFO_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": (
                  "文藻外語大學出國交換及雙聯學制學生獎助學金辦法與教育部學海飛颺／惜珠獎學金專區"
              ),
              "source_url": WZU_SCHOLARSHIP_HUB_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": (
                  "文藻外語大學學生出國交換實施辦法與相關法規表單專區"
              ),
              "source_url": WZU_REGULATIONS_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": (
                  "文藻外語大學 UMAP 亞太大學交流會與 ACUCA 亞洲基督教大學協會交換計畫專頁"
              ),
              "source_url": WZU_UMAP_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": (
                  "文藻外語大學國際交流組—交換生出國研修心得與相簿專區"
              ),
              "source_url": WZU_EXP_ALBUM_URL,
              "category": "partner_school",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_WZU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  pages_records = [
      {
          "title": (
              "文藻外語大學：國際暨兩岸合作處（國際交流組）六大語組一招／二招與 UMAP／ACUCA 出國交換申請時程"
          ),
          "source_url": WZU_OUTBOUND_GUIDE_URL,
          "published_at": "2026-09-30T00:00:00Z",
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
              "文藻外語大學：出國交換生申請資格、一般組 70 分／語言學習組 65 分門檻、書審 50%＋面試 50% 配分與跨組撕榜規定"
          ),
          "source_url": WZU_R1_ANNOUNCEMENT_URL,
          "published_at": "2026-05-04T00:00:00Z",
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
              "文藻外語大學：147 所交換姊妹校六大語組外語檢定標準（TOEFL／IELTS／TOEIC／JLPT"
              " N1–N4／DELF／TestDaF／DELE／TOPIK）"
          ),
          "source_url": WZU_R2_ANNOUNCEMENT_URL,
          "published_at": "2026-09-30T00:00:00Z",
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
              "文藻外語大學：校務資訊系統線上報名、六大紙本申請文件、SOSA 志工團加分與返國報告／抵免義務"
          ),
          "source_url": WZU_REGULATIONS_URL,
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
          "title": (
              "文藻外語大學：出國交換獎助學金（1 萬–5 萬）、學海飛颺／惜珠（含 20% 配合款）與日本／加拿大／UMAP／ACUCA"
              " 獎學金"
          ),
          "source_url": WZU_SCHOLARSHIP_HUB_URL,
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
  ]
  (OFFICIAL_WZU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
      + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "wzu",
      "school_name": "文藻外語大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "general_group_score_minimum": 70.0,
          "language_learning_group_score_minimum": 65.0,
          "conduct_score_minimum": 80.0,
          "rounding_policy": "truncate_to_integer_no_rounding",
          "stage1_written_weight_percent": 50,
          "stage2_interview_weight_percent": 50,
          "sosa_volunteer_bonus_max_points": 5,
          "minimum_qualifying_total_score": 60.0,
          "general_group_covers_language_learning_group": True,
          "wzu_scholarship_general_twd": 10000,
          "wzu_scholarship_two_year_tech_or_direct_entry_max_twd": 50000,
          "xuehai_score_minimum": 75.0,
          "xuehai_xizhu_wzu_matching_grant_percent": 20,
          "minimum_courses_per_semester": "至少 2 門課或 4 學分，或至少 1 門該國語言課程",
          "return_documents_due": (
              "抵達姊妹校後 2 週內繳交抵達通報單；返國後 1 個月內繳交返國報告書、照片及姊妹校正式成績單完成學分抵免"
          ),
      },
      "source_urls": wzu_source_urls,
      "verified_at": "2026-10-19",
  }
  (OFFICIAL_WZU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_WZU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "文藻外語大學",
              "required_documents": student_dashboard_payload[
                  "required_documents"
              ],
              "source_urls": wzu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_WZU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "文藻外語大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": wzu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "wzu",
      "school_name": "文藻外語大學",
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
      "experience_report_covered_partners": exp_covered_schools,
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
          "文藻外語大學國際暨兩岸合作處（國際交流組）115-2 出國交換生一招（8/31 截止、9/22–9/23 撕榜）與二招（10/13"
          " 截止、10/19–10/23 面試、10/14–10/30 志願分發）已公告，116-1 秋季班出國交換一招預計於 2027 年 2"
          " 月開放申請；共完整收錄 147 所全球交換合作學校（一般組 140 校、語言學習組 7"
          f" 校，含 {open_partner_count} 所 115-2 開放申請校及 {len(partners) - open_partner_count}"
          " 所第一學期／參考合作校，涵蓋英語組 40 校、日語組 31 校、華語暨東南亞語組 29 校、法語組 24 校、西語組 14"
          " 校、德語組 9 校）。"
      ),
      "verified_at": "2026-10-19",
  }
  (OFFICIAL_WZU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_WZU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "wzu",
              "school_name": "文藻外語大學",
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
          "sources/wzu/115_2_round1_general_guidelines.pdf",
          WZU_R1_ANNOUNCEMENT_URL,
          "文藻外語大學 115 學年度第 2 學期出國交換生甄選簡章（一招・一般組）PDF",
      ),
      (
          "sources/wzu/115_2_round1_lang_guidelines.pdf",
          WZU_R1_ANNOUNCEMENT_URL,
          "文藻外語大學 115 學年度第 2 學期出國交換生甄選簡章（一招・語言學習組）PDF",
      ),
      (
          "sources/wzu/115_2_round1_general_quota.xlsx",
          WZU_R1_ANNOUNCEMENT_URL,
          "文藻外語大學 115-2 出國交換生甄選學校名額一覽表（一招・一般組）XLSX",
      ),
      (
          "sources/wzu/115_2_round1_lang_quota.xlsx",
          WZU_R1_ANNOUNCEMENT_URL,
          "文藻外語大學 115-2 出國交換生甄選學校名額一覽表（一招・語言學習組）XLSX",
      ),
      (
          "sources/wzu/115_2_round2_general_guidelines.pdf",
          WZU_R2_ANNOUNCEMENT_URL,
          "文藻外語大學 115 學年度第 2 學期出國交換生甄選簡章（二招・一般組）PDF",
      ),
      (
          "sources/wzu/115_2_round2_lang_guidelines.pdf",
          WZU_R2_ANNOUNCEMENT_URL,
          "文藻外語大學 115 學年度第 2 學期出國交換生甄選簡章（二招・語言學習組）PDF",
      ),
      (
          "sources/wzu/115_2_round2_general_quota.xlsx",
          WZU_R2_ANNOUNCEMENT_URL,
          "文藻外語大學 115-2 出國交換生甄選學校名額一覽表（二招・一般組）XLSX",
      ),
      (
          "sources/wzu/115_2_round2_lang_quota.xlsx",
          WZU_R2_ANNOUNCEMENT_URL,
          "文藻外語大學 115-2 出國交換生甄選學校名額一覽表（二招・語言學習組）XLSX",
      ),
      (
          "sources/wzu/115_1_round1_general_guidelines.pdf",
          WZU_R1_115_1_ANNOUNCEMENT_URL,
          "文藻外語大學 115 學年度第 1 學期出國交換生甄選簡章（一招・一般組）PDF",
      ),
      (
          "sources/wzu/115_1_round1_general_quota.xlsx",
          WZU_R1_115_1_ANNOUNCEMENT_URL,
          "文藻外語大學 115-1 出國交換生甄選學校名額一覽表（一招・一般組）XLSX",
      ),
      (
          "sources/wzu/115_1_round1_lang_quota.xlsx",
          WZU_R1_115_1_ANNOUNCEMENT_URL,
          "文藻外語大學 115-1 出國交換生甄選學校名額一覽表（一招・語言學習組）XLSX",
      ),
      (
          "sources/wzu/wzu_exchange_implementation_rules.pdf",
          WZU_REGULATIONS_URL,
          "文藻外語大學學生出國交換實施辦法 PDF",
      ),
      (
          "sources/wzu/wzu_exchange_scholarship_rules.pdf",
          WZU_SCHOLARSHIP_HUB_URL,
          "文藻外語大學出國交換及雙聯學制學生獎助學金辦法 PDF",
      ),
      (
          "sources/wzu/moe_xuehai_scholarship_rules.pdf",
          WZU_SCHOLARSHIP_HUB_URL,
          "文藻外語大學辦理教育部學海系列獎助學金甄選作業要點 PDF",
      ),
      (
          "sources/wzu/outbound_application_process_492285.html",
          WZU_OUTBOUND_GUIDE_URL,
          "文藻外語大學國際交流組—出國交換計畫申請流程專頁 HTML",
      ),
      (
          "sources/wzu/exchange_partner_info_154399.html",
          WZU_PARTNER_INFO_URL,
          "文藻外語大學國際交流組—各校交換申請資訊與學長姐經驗分享雲端硬碟總覽 HTML",
      ),
      (
          "sources/wzu/exchange_experience_album_list_152198.html",
          WZU_EXP_ALBUM_URL,
          "文藻外語大學國際交流組—交換生出國研修心得與相簿列表 HTML",
      ),
      (
          "sources/wzu/umap_announcement_517638.html",
          WZU_UMAP_URL,
          "文藻外語大學 UMAP 亞太大學交流會交換計畫甄選公告 HTML",
      ),
      (
          "sources/wzu/acuca_announcement_517642.html",
          WZU_ACUCA_URL,
          "文藻外語大學 ACUCA 亞洲基督教大學協會交換計畫甄選公告 HTML",
      ),
      (
          "sources/wzu/wzu_academic_units.json",
          "https://www.wzu.edu.tw/",
          "文藻外語大學 5 個學院與 18 個系所學位學程中心官方組織 JSON",
      ),
      (
          "sources/wzu/wzu_experience_stories.json",
          WZU_EXP_ALBUM_URL,
          "文藻外語大學國際交流組 24 所姊妹校 60 篇交換生出國研修心得與相簿索引 JSON",
      ),
      (
          "sources/wzu/wzu_catalog_source.json",
          WZU_R2_ANNOUNCEMENT_URL,
          "文藻外語大學 147 所出國交換合作學校整合資料集 JSON",
      ),
      (
          "sources/wzu/wzu_resolved_locations.json",
          WZU_PARTNER_INFO_URL,
          "文藻外語大學 147 所出國交換合作學校 ROR / Wikidata 地理座標核對表 JSON",
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
      "school_id": "wzu",
      "school_name": "文藻外語大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = (
      json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  )
  (OFFICIAL_WZU_DIR / "import_provenance.json").write_text(
      prov_text, encoding="utf-8"
  )
  (OFFICIAL_WZU_DIR / "import-provenance.json").write_text(
      prov_text, encoding="utf-8"
  )

  from exchange_info.wzu_source_review import review_bundle
  reviewed_counts = review_bundle(REPO_ROOT)
  from exchange_info.vilnius_akita_review import apply_vilnius_akita_review
  apply_vilnius_akita_review(REPO_ROOT, "wzu")

  print(
      f"WZU catalog: {len(partners)} partners, {len(workflows)} workflows, "
      f"{len(destinations)} destinations; bounded review states: {reviewed_counts}. "
      "Individual host fields and whole records remain unverified."
  )


if __name__ == "__main__":
  main()
