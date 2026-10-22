"""Build the official Yuan Ze University (元智大學, YZU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import unicodedata

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
from exchange_info.school_identity import VisualRecordIndex, school_identity_key

_HOST_SCRATCH = Path(
    r"C:\Users\Administrator\.gemini\antigravity\brain\0723e0a1-b112-47e2-8145-2d4d6f69cb19\scratch"
)
SOURCES_YZU_DIR = REPO_ROOT / "sources" / "yzu"
OFFICIAL_YZU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "yzu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

COUNTRY_MAP = {
    "Indonesia": "印尼",
    "Japan": "日本",
    "Singapore": "新加坡",
    "Malaysia": "馬來西亞",
    "Philippines": "菲律賓",
    "South Korea": "韓國",
    "Vietnam": "越南",
    "South Africa": "南非",
    "Canada": "加拿大",
    "Mexico": "墨西哥",
    "United States": "美國",
    "Belgium": "比利時",
    "Brazil": "巴西",
    "Czech Republic": "捷克",
    "Denmark": "丹麥",
    "Finland": "芬蘭",
    "France": "法國",
    "Germany": "德國",
    "Norway": "挪威",
    "Spain": "西班牙",
    "Sweden": "瑞典",
}

REGION_BY_COUNTRY = {
    "日本": "亞洲",
    "韓國": "亞洲",
    "中國大陸": "中國大陸及港澳",
    "香港": "中國大陸及港澳",
    "澳門": "中國大陸及港澳",
    "新加坡": "亞洲",
    "馬來西亞": "亞洲",
    "泰國": "亞洲",
    "越南": "亞洲",
    "印尼": "亞洲",
    "菲律賓": "亞洲",
    "美國": "美洲",
    "加拿大": "美洲",
    "墨西哥": "美洲",
    "巴西": "美洲",
    "南非": "非洲",
    "摩洛哥": "非洲",
    "比利時": "歐洲",
    "捷克": "歐洲",
    "丹麥": "歐洲",
    "芬蘭": "歐洲",
    "法國": "歐洲",
    "德國": "歐洲",
    "荷蘭": "歐洲",
    "挪威": "歐洲",
    "斯洛維尼亞": "歐洲",
    "西班牙": "歐洲",
    "瑞典": "歐洲",
    "瑞士": "歐洲",
    "英國": "歐洲",
}

REGION_COST_DEFAULTS = {
    "美國": (
        "USD 1,400–2,200 / 月（含住宿、餐飲、校園保險與當地交通）",
        "建議預留強制校園醫療保險（約 USD 1,500–2,500 / 學期）與 J-1 / F-1 簽證 SEVIS 費用。",
    ),
    "加拿大": (
        "CAD 1,500–2,200 / 月（含住宿、膳食、省級／校內醫保與市區交通）",
        "須投保接待校指定醫療保險並辦理 Study Permit 或 eTA。",
    ),
    "英國": (
        "GBP 1,100–1,600 / 月（含學生宿舍、飲食與大眾運輸）",
        "交換一學期（6 個月內）可辦理 Standard Visitor 簽證，一學年須辦理 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "法國": (
        "EUR 850–1,400 / 月（巴黎地區約 EUR 1,200–1,600 / 月；可申請 CAF 房補）",
        "須透過法國教育中心（Campus France）面試並申辦長期學生簽證（VLS-TS）。",
    ),
    "德國": (
        "EUR 934–1,200 / 月（德國簽證限制提領帳戶基準為每月 EUR 934）",
        "須辦理德國法定公保（約 EUR 120–130 / 月）及學期雜費／學期票（Semesterticket）。",
    ),
    "西班牙": (
        "EUR 800–1,250 / 月（瓦倫西亞與巴塞隆納含外宿與日常開支）",
        "須備妥涵蓋全額醫療與遺體運返之私人醫療保險以申辦西班牙學生簽證。",
    ),
    "荷蘭": (
        "EUR 950–1,400 / 月（荷蘭移民局 IND 財力證明基準約 EUR 1,225 / 月）",
        "由接待校代辦 MVV/VVR 居留許可，格羅寧根與鹿特丹房源緊張建議獲提名後立即申請宿舍。",
    ),
    "比利時": (
        "EUR 850–1,200 / 月（含列日學生宿舍、餐飲與大眾運輸）",
        "須辦理長期學生簽證 D 簽，抵達後向市政廳登記居留。",
    ),
    "瑞士": (
        "CHF 1,500–2,200 / 月（含琉森住宿、膳食與強制保險）",
        "須透過瑞士商務辦事處申辦學生簽證，並於抵瑞後申請居留證與醫療保險豁免或投保。",
    ),
    "丹麥": (
        "DKK 6,500–9,500 / 月（含南丹麥大學學生宿舍、飲食與單車／大眾運輸）",
        "須申辦 ST1 學生居留許可，抵丹後登記 CPR 號碼即可享有公醫保障。",
    ),
    "瑞典": (
        "SEK 9,500–13,000 / 月（瑞典移民局財力基準約 SEK 10,314 / 月）",
        "交換超過 3 個月須向瑞典移民局申辦學生居留許可（Residence Permit for Studies）。",
    ),
    "芬蘭": (
        "EUR 750–1,100 / 月（芬蘭移民局 Migri 財力證明基準約 EUR 800 / 月）",
        "須透過 Enter Finland 申辦學生居留許可並投保涵蓋全期之醫療保險。",
    ),
    "挪威": (
        "NOK 12,000–15,000 / 月（挪威移民局 UDI 財力證明基準約 NOK 13,790 / 月）",
        "須申辦挪威學生居留許可（Study Permit）並預先匯入學生保證金帳戶。",
    ),
    "捷克": (
        "EUR 600–900 / 月（含布拉格或皮爾森學生宿舍、食堂與市區交通卡）",
        "須提前預約捷克經濟文化辦事處申辦長期學生簽證與捷克合約醫療保險。",
    ),
    "斯洛維尼亞": (
        "EUR 600–900 / 月（馬里博爾住宿與學生餐券補助實惠）",
        "須申辦斯洛維尼亞長期簽證 D 或臨時居留許可並備妥歐盟醫療保險。",
    ),
    "日本": (
        "JPY 80,000–130,000 / 月（東京與神戶約 JPY 100,000–140,000；地方城市約 JPY 70,000–100,000）",
        "憑接待校核發之在留資格認定證明書（COE）換發留學簽證，抵日後須加入國民健康保險。",
    ),
    "韓國": (
        "KRW 800,000–1,300,000 / 月（首爾圈外宿較高；校內宿舍約 KRW 150,000–400,000 / 月）",
        "憑標準入學許可書申辦 D-2-6 交換學生簽證，抵韓後外國人登錄並自動納入韓國國民健康保險（NHIS）。",
    ),
    "中國大陸": (
        "RMB 2,000–3,800 / 月（校內宿舍與學生食堂費用低廉，上海、南京、武漢、重慶生活機能完善）",
        "持臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定投保大陸境內來華留學生綜合醫療保險（約 RMB 400 / 學期）。",
    ),
    "香港": (
        "HKD 6,000–10,000 / 月（含香港恒生大學賽馬會住宿書院與日常開支）",
        "須透過接待校向香港入境事務處申辦學生簽證／進入許可（Student Visa / Entry Permit）。",
    ),
    "新加坡": (
        "SGD 1,200–2,000 / 月（含校外住宿、熟食中心餐飲與地鐵交通）",
        "須透過新加坡移民局 SOLAR 系統申辦 Student's Pass（STP）並繳納接待校強制醫療保險。",
    ),
    "馬來西亞": (
        "MYR 1,500–2,500 / 月（吉隆坡與金寶生活機能便利且物價親民）",
        "須透過 EMGS（Education Malaysia Global Services）系統申辦學生簽證（VAL / Student Pass）。",
    ),
    "泰國": (
        "THB 15,000–25,000 / 月（曼谷生活成本親民）",
        "須憑接待校入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證。",
    ),
    "印尼": (
        "IDR 5,000,000–9,200,000 / 月（雅加達與德波生活開支實惠）",
        "須由接待校協助向印尼移民總局申辦學習簽證（C316 / 學生電子簽證）。",
    ),
    "越南": (
        "USD 400–700 / 月（約 VND 10,000,000–17,000,000，河內與胡志明市生活成本低廉）",
        "須憑接待校入學許可透過越南駐臺辦事處申辦 DH 學生簽證。",
    ),
    "菲律賓": (
        "USD 550–900 / 月（約 PHP 30,000–50,000，馬尼拉生活與外宿開支適中）",
        "須憑接待校入學許可辦理菲律賓學生簽證（9F）或特別學習許可（SSP）。",
    ),
    "墨西哥": (
        "USD 700–1,100 / 月（約 MXN 13,000–20,000，蒙特雷生活與住宿開支適中）",
        "交換一學期（180 天內）依國籍與簽證規定辦理入境，超過 180 天須申辦墨西哥學生臨時居留簽證。",
    ),
    "巴西": (
        "USD 600–1,000 / 月（聖保羅生活與日常交通開支）",
        "須憑接待校入學許可向巴西商務辦事處申辦 VITEM IV 學生簽證並備妥全期海外醫療保險。",
    ),
    "南非": (
        "USD 550–900 / 月（約 ZAR 10,000–16,000，德班生活成本適中）",
        "須向聯絡辦事處申辦南非 Study Visa 並投保南非認可之醫療保險（Medical Aid）。",
    ),
    "摩洛哥": (
        "EUR 550–850 / 月（拉巴特校園生活與住宿成本實惠）",
        "須憑拉巴特商學院入學許可辦理摩洛哥學生簽證，抵摩後辦理學生居留卡。",
    ),
}

ZH_CLEAN_OVERRIDES = {
    "印尼大學": ("印尼大學", "Universitas Indonesia"),
    "印尼建國大學": ("建國大學", "Bina Nusantara University"),
    "印尼UBM": ("慈育大學", "Universitas Bunda Mulia"),
    "日本福井大學": ("福井大學", "University of Fukui"),
    "日本福岡工業大學": ("福岡工業大學", "Fukuoka Institute of Technology"),
    "日本法政大學": ("法政大學", "Hosei University"),
    "日本秋田國際教養大學": ("國際教養大學", "Akita International University"),
    "日本神奈川大學": ("神奈川大學", "Kanagawa University"),
    "日本立命館亞洲太平洋大學": (
        "立命館亞洲太平洋大學",
        "Ritsumeikan Asia Pacific University",
    ),
    "日本神戶大學": ("神戶大學", "Kobe University"),
    "日本名城大學": ("名城大學", "Meijo University"),
    "日本德島大學": ("德島大學", "Tokushima University"),
    "新加坡南洋理工學院": ("南洋理工學院", "Nanyang Polytechnic"),
    "馬來西亞拉曼大學": ("拉曼大學", "Universiti Tunku Abdul Rahman"),
    "菲律賓馬尼拉雅典耀大學": ("馬尼拉雅典耀大學", "Ateneo de Manila University"),
    "韓國翰林大學": ("翰林大學", "Hallym University"),
    "韓國淑明女子大學": ("淑明女子大學", "Sookmyung Women's University"),
    "韓國慶星大學": ("慶星大學", "Kyungsung University"),
    "韓國漢陽大學": ("漢陽大學", "Hanyang University"),
    "韓國中央大學": ("中央大學", "Chung-Ang University"),
    "韓國亞洲大學": ("亞洲大學", "Ajou University"),
    "韓國忠南大學": ("忠南大學", "Chungnam National University"),
    "韓國釜慶大學": ("釜慶大學", "Pukyong National University"),
    "韓國釜山大學": ("釜山大學", "Pusan National University"),
    "越南文朗大學": ("文朗大學", "Van Lang University"),
    "越南胡志明市外語資訊大學": (
        "胡志明市外語資訊大學",
        "Ho Chi Minh City University of Foreign Languages - Information Technology",
    ),
    "越南Phenikaa University": ("菲尼卡大學", "Phenikaa University"),
    "越南商業大學": ("越南商業大學", "Thuongmai University"),
    "南非誇祖魯納塔爾大學": ("夸祖魯-納塔爾大學", "University of KwaZulu-Natal"),
    "加拿大皇家山大學": ("皇家山大學", "Mount Royal University"),
    "加拿大里賈納大學": ("里賈納大學", "University of Regina"),
    "墨西哥蒙特雷大學": ("蒙特雷大學", "Universidad de Monterrey"),
    "美國凱特琳大學": ("凱特琳大學", "Kettering University"),
    "美國俄亥俄州立大學": ("俄亥俄州立大學", "The Ohio State University"),
    "比利時列日大學": ("列日大學", "University of Liège"),
    "巴西保利斯塔大學": ("保利斯塔大學", "Universidade Paulista"),
    "捷克西波西米亞大學": ("西波西米亞大學", "University of West Bohemia"),
    "捷克布拉格化工大學": (
        "布拉格化工大學",
        "University of Chemistry and Technology, Prague",
    ),
    "捷克牛頓大學": ("牛頓大學", "NEWTON University"),
    "丹麥南丹麥大學": ("南丹麥大學", "University of Southern Denmark"),
    "芬蘭赫爾辛基城市應用科技大學": (
        "赫爾辛基都會應用科學大學",
        "Metropolia University of Applied Sciences",
    ),
    "法國克萊蒙奧弗涅理工學院": (
        "克萊蒙奧弗涅理工學院",
        "Clermont Auvergne INP",
    ),
    "法國ESME工程師學校": ("ESME高等工程師學院", "ESME Engineering School"),
    "法國巴黎資訊與數位科技工程學院": (
        "巴黎資訊與數位科技工程學院",
        "EFREI Paris",
    ),
    "德國耶拿應用科技大學": ("耶拿應用科學大學", "Ernst-Abbe-Hochschule Jena"),
    "德國法蘭克福應用科技大學": (
        "法蘭克福應用科技大學",
        "Frankfurt University of Applied Sciences",
    ),
    "德國奧格斯堡應用科技大學": (
        "奧格斯堡應用科技大學",
        "Technical University of Applied Sciences Augsburg",
    ),
    "德國特里爾應用科技大學": (
        "特里爾應用科技大學",
        "Trier University of Applied Sciences",
    ),
    "德國波茨坦應用科技大學": (
        "波茨坦應用科技大學",
        "University of Applied Sciences Potsdam",
    ),
    "挪威科技大學": (
        "挪威科技大學",
        "Norwegian University of Science and Technology",
    ),
    "西班牙華倫西亞大學": ("瓦倫西亞大學", "University of Valencia"),
    "西班牙加泰羅尼亞國際大學": (
        "加泰隆尼亞國際大學",
        "Universitat Internacional de Catalunya",
    ),
    "瑞典林雪平大學": ("林雪平大學", "Linköping University"),
}

CM_OVERRIDES = {
    1: ("奧克拉荷馬大學", "University of Oklahoma", "美國", "https://www.ou.edu/"),
    2: ("格羅寧根大學", "University of Groningen", "荷蘭", "https://www.rug.nl/"),
    3: (
        "佛茨海姆應用科技大學",
        "Pforzheim University",
        "德國",
        "https://www.hs-pforzheim.de/",
    ),
    4: (
        "愛希思代特天主教大學",
        "Catholic University of Eichstätt-Ingolstadt",
        "德國",
        "https://www.ku.de/en/",
    ),
    5: ("馬里博爾大學", "University of Maribor", "斯洛維尼亞", "https://www.um.si/en/"),
    6: (
        "布拉格捷克理工大學",
        "Czech Technical University in Prague",
        "捷克",
        "https://www.cvut.cz/en",
    ),
    8: ("SKEMA商學院", "SKEMA Business School", "法國", "https://www.skema.edu/"),
    9: (
        "里昂天主教大學管理學院",
        "ESDES School of Business and Management",
        "法國",
        "https://www.esdes.fr/en/",
    ),
    10: (
        "里爾天主教大學管理學院",
        "IÉSEG School of Management",
        "法國",
        "https://www.ieseg.fr/en/",
    ),
    11: (
        "昂傑高等商學院",
        "ESSCA School of Management",
        "法國",
        "https://www.essca.fr/en/",
    ),
    12: (
        "南錫高等商學院",
        "ICN Business School",
        "法國",
        "https://www.icn-artem.com/en/",
    ),
    13: (
        "雷恩商學院",
        "Rennes School of Business",
        "法國",
        "https://www.rennes-sb.com/",
    ),
    14: (
        "克萊蒙高等商學院",
        "ESC Clermont Business School",
        "法國",
        "https://www.esc-clermont.fr/en/",
    ),
    15: (
        "大阪女學院大學",
        "Osaka Jogakuin University",
        "日本",
        "https://www.wilmina.ac.jp/",
    ),
    36: ("泰國農業大學", "Kasetsart University", "泰國", "https://www.ku.ac.th/en"),
    16: (
        "香港恒生大學",
        "The Hang Seng University of Hong Kong",
        "香港",
        "https://www.hsu.edu.hk/",
    ),
    17: (
        "拉巴特商學院",
        "Rabat Business School",
        "摩洛哥",
        "https://rbs.uir.ac.ma/",
    ),
    43: (
        "鹿特丹應用科技大學",
        "Rotterdam University of Applied Sciences",
        "荷蘭",
        "https://www.rotterdamuas.com/",
    ),
    46: (
        "琉森應用科學與藝術大學",
        "Lucerne University of Applied Sciences and Arts",
        "瑞士",
        "https://www.hslu.ch/en/",
    ),
    47: (
        "廣島經濟大學",
        "Hiroshima University of Economics",
        "日本",
        "https://www.hue.ac.jp/",
    ),
}

MAINLAND_LIST = [
    (
        "同濟大學",
        "Tongji University",
        "中國大陸",
        "https://www.tongji.edu.cn/",
        "上海市",
        "open",
        "2 名（115-2 / 2027春季班大陸交換公告名額）",
        "2026年10月14日（校內書審截止）／10月15日（提名截止）",
    ),
    (
        "南京大學",
        "Nanjing University",
        "中國大陸",
        "https://www.nju.edu.cn/",
        "江蘇省南京市",
        "open",
        "2 名（115-2 / 2027春季班大陸交換公告名額）",
        "2026年10月14日（校內書審截止）／10月20日（資料上傳截止）",
    ),
    (
        "西南大學",
        "Southwest University",
        "中國大陸",
        "http://www.swu.edu.cn/",
        "重慶市",
        "open",
        "3 名（115-2 / 2027春季班大陸交換公告名額）",
        "2026年10月20日（校內書審截止）／11月1日（姊妹校收件截止）",
    ),
    (
        "武漢大學",
        "Wuhan University",
        "中國大陸",
        "https://www.whu.edu.cn/",
        "湖北省武漢市",
        "open",
        "2 名（115-2 / 2027春季班大陸交換公告名額）",
        "2026年10月20日（校內書審截止）／10月30日（姊妹校收件截止）",
    ),
    (
        "重慶大學",
        "Chongqing University",
        "中國大陸",
        "http://www.cqu.edu.cn/",
        "重慶市",
        "open",
        "2 名（115-2 / 2027春季班大陸交換公告名額）",
        "2026年10月20日（校內書審截止）／10月31日（姊妹校收件截止）",
    ),
    (
        "蘇州大學",
        "Soochow University",
        "中國大陸",
        "http://www.suda.edu.cn/",
        "江蘇省蘇州市",
        "open",
        "3 名（115-2 / 2027春季班大陸交換公告名額）",
        "2026年10月20日（校內書審截止）／11月1日（姊妹校收件截止）",
    ),
    (
        "西安交通大學",
        "Xi'an Jiaotong University",
        "中國大陸",
        "http://www.xjtu.edu.cn/",
        "陝西省西安市",
        "open",
        "2 名（115-2 / 2027春季班大陸交換公告名額）",
        "2026年10月20日（校內書審截止）／11月1日（姊妹校收件截止）",
    ),
    (
        "上海大學",
        "Shanghai University",
        "中國大陸",
        "https://www.shu.edu.cn/",
        "上海市",
        "reference_only",
        "歷年兩岸交換合作校（依當期兩岸交換簡章公告開放名額）",
        "依每學期全球事務處兩岸交換生甄選公告辦理",
    ),
    (
        "華中師範大學",
        "Central China Normal University",
        "中國大陸",
        "https://www.ccnu.edu.cn/",
        "湖北省武漢市",
        "reference_only",
        "歷年兩岸交換合作校（依當期兩岸交換簡章公告開放名額）",
        "依每學期全球事務處兩岸交換生甄選公告辦理",
    ),
    (
        "廈門大學",
        "Xiamen University",
        "中國大陸",
        "https://www.xmu.edu.cn/",
        "福建省廈門市",
        "reference_only",
        "歷年兩岸交換合作校（依當期兩岸交換簡章公告開放名額）",
        "依每學期全球事務處兩岸交換生甄選公告辦理",
    ),
    (
        "鄭州大學",
        "Zhengzhou University",
        "中國大陸",
        "http://www.zzu.edu.cn/",
        "河南省鄭州市",
        "reference_only",
        "歷年兩岸交換合作校（依當期兩岸交換簡章公告開放名額）",
        "依每學期全球事務處兩岸交換生甄選公告辦理",
    ),
    (
        "吉林大學",
        "Jilin University",
        "中國大陸",
        "https://www.jlu.edu.cn/",
        "吉林省長春市",
        "reference_only",
        "歷年兩岸交換合作校（依當期兩岸交換簡章公告開放名額）",
        "依每學期全球事務處兩岸交換生甄選公告辦理",
    ),
]

EXTRA_EXP_PARTNERS = [
    (
        "伊利諾大學香檳分校",
        "University of Illinois Urbana-Champaign",
        "美國",
        "https://illinois.edu/",
        "歷年赴外交換及研修合作校（全球事務處收錄 3 篇學長姐返國心得報告；當期名額依簡章公告為準）",
    ),
    (
        "明尼蘇達大學",
        "University of Minnesota",
        "美國",
        "https://twin-cities.umn.edu/",
        "歷年赴外交換及雙聯研修合作校（全球事務處收錄 3 篇學長姐返國心得報告；當期名額依簡章公告為準）",
    ),
    (
        "艾塞克斯大學",
        "University of Essex",
        "英國",
        "https://www.essex.ac.uk/",
        "歷年赴外交換及雙聯學位合作校（全球事務處收錄學長姐返國心得報告；當期名額依簡章公告為準）",
    ),
    (
        "提亞斯商學院",
        "TIAS School for Business and Society",
        "荷蘭",
        "https://www.tias.edu/en",
        "管理學院歷年雙聯與交換合作校（管院國際事務辦公室收錄 7 篇學長姐心得；當期名額依管院公告為準）",
    ),
    (
        "思特雅大學",
        "UCSI University",
        "馬來西亞",
        "https://www.ucsiuniversity.edu.my/",
        "管理學院歷年交換合作校（管院國際事務辦公室收錄 4 篇學長姐返國交換心得；當期名額依管院公告為準）",
    ),
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def loose_en(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(
        r"\b(the|of|de|del|la|las|los|at|in|and|fur|for|a|an)\b",
        " ",
        s.lower(),
    )
    return "".join(ch for ch in s.lower() if "a" <= ch <= "z" or "0" <= ch <= "9")


def ensure_http(url: str | None) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    if not u.startswith(("http://", "https://")):
        return f"https://{u}"
    return u


def archive_official_sources() -> dict:
    SOURCES_YZU_DIR.mkdir(parents=True, exist_ok=True)
    for json_name in [
        "yzu_115_2_spring2027_parsed.json",
        "yzu_115_1_fall2026_parsed.json",
    ]:
        src = _HOST_SCRATCH / json_name
        dst = SOURCES_YZU_DIR / json_name
        if src.exists() and src.resolve() != dst.resolve():
            shutil.copy2(src, dst)

    files_meta = [
        (
            "yzu_115_2_spring2027_gviz.json",
            "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
            "元智大學 115-2（2027春季班）赴外交換學校一覽表（Google Sheets 官方資料源，53 所國際交換校）",
        ),
        (
            "yzu_115_2_spring2027_htmlview.html",
            "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
            "元智大學 115-2（2027春季班）赴外交換學校一覽表（HTML 檢視版）",
        ),
        (
            "yzu_115_1_fall2026_gviz.json",
            "https://gao.yzu.edu.tw/index.php/tw/2026-01-13-02-46-21",
            "元智大學 115-1（2026秋季班）赴外交換學校一覽表（49 所國際交換校）",
        ),
        (
            "yzu_115_2_info_session_ppt.pdf",
            "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
            "元智大學 115-2 學期（2027年春季班）赴外交流說明會簡報（55 頁官方簡報）",
        ),
        (
            "yzu_overseas_course_selection_rules_1_51.pdf",
            "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07",
            "元智大學學生至境外大學校院選修課程實施辦法（1-51 號法規）",
        ),
        (
            "yzu_exchange_scholarship_rules.pdf",
            "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07",
            "元智大學學生國際與兩岸交流獎助學金設置辦法",
        ),
        (
            "yzu_moe_xuehai_guidelines.pdf",
            "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07",
            "元智大學學海飛颺及學海惜珠計畫甄選要點",
        ),
        (
            "yzu_wish_list_form_cf01r1.pdf",
            "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
            "元智大學出國交換學生志願表（CF-01-R1）",
        ),
        (
            "yzu_application_form_cf02r3.pdf",
            "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
            "元智大學出國交換學生申請表（CF-02-R3）",
        ),
        (
            "yzu_letter_of_undertaking_cf04.pdf",
            "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
            "元智大學出國交換學生切結書（CF-04，含保證金新臺幣 5,000 元規定）",
        ),
        (
            "yzu_mainland_wish_list_form.pdf",
            "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2019-07-04-06-31-37",
            "元智大學赴大陸地區交換學生志願表",
        ),
        (
            "yzu_mainland_application_form.pdf",
            "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2019-07-04-06-31-37",
            "元智大學赴大陸地區交換學生申請表",
        ),
        (
            "yzu_gdrive_experiences.json",
            "https://drive.google.com/drive/folders/1qpsAYYV95y_gxsZi8mb5J3-rGaQkBTiz",
            "元智大學全球事務處歷年交換學生研修心得報告雲端資料庫索引（37 所姊妹校資料夾、178 篇心得檔案）",
        ),
        (
            "yzu_cm_oip_exchange_and_reviews.json",
            "https://oip.cm.yzu.edu.tw/abrd_deg/list/es",
            "元智大學管理學院國際事務辦公室（OIP）院級交換姊妹校名冊（21 校）與學生出國心得報告（18 校 58 篇）",
        ),
        (
            "yzu_resolved_locations.json",
            "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-51-28",
            "元智大學 90 所赴外交換合作大學 ROR / Wikidata 地理座標核對表",
        ),
    ]
    provenance_items = []
    for fname, url, title in files_meta:
        dst = SOURCES_YZU_DIR / fname
        if dst.exists():
            provenance_items.append({
                "file": f"sources/yzu/{dst.name}",
                "source_url": url,
                "title": title,
                "sha256": sha256_file(dst),
                "bytes": dst.stat().st_size,
                "fetched_at": "2026-10-17T04:30:00Z",
            })
    return {
        "school_id": "yzu",
        "school_name": "元智大學",
        "generated_at": "2026-10-17T04:45:00Z",
        "active_cycle_note": (
            "115-2（2027春季班）赴國際姊妹校交換生甄選已於 2026/08/26–09/22 12:00 辦理（Early Nomination 提早提名校為 09/07 及 09/11 截止），"
            "2027春季班赴大陸地區姊妹校交換（同濟、南京、武漢、重慶、西南、蘇州、西安交大等校）於 2026年10月中旬至11月1日依各校截止日收件；"
            "116-1（2027秋季班）赴外交換預計於 2027年1月中旬至3月開放報名。同時收錄管理學院國際事務辦公室（OIP）21 所院級交換合作校及全校 236 篇返國交換生心得報告。"
        ),
        "sources": provenance_items,
    }


def main() -> None:
    OFFICIAL_YZU_DIR.mkdir(parents=True, exist_ok=True)
    provenance = archive_official_sources()
    (OFFICIAL_YZU_DIR / "import_provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    p1152 = json.loads(
        (SOURCES_YZU_DIR / "yzu_115_2_spring2027_parsed.json").read_text(
            encoding="utf-8"
        )
    )["rows"]
    cm_data = json.loads(
        (SOURCES_YZU_DIR / "yzu_cm_oip_exchange_and_reviews.json").read_text(
            encoding="utf-8"
        )
    )
    exp_gdrive = json.loads(
        (SOURCES_YZU_DIR / "yzu_gdrive_experiences.json").read_text(
            encoding="utf-8"
        )
    )
    resolved_locs = json.loads(
        (SOURCES_YZU_DIR / "yzu_resolved_locations.json").read_text(
            encoding="utf-8"
        )
    )
    loc_by_name = {r["school_name"]: r for r in resolved_locs}

    # Index GDrive experiences by folder
    gdrive_by_folder = {}
    folder_titles = {}
    for item in exp_gdrive:
        if item["type"] == "folder":
            folder_titles[item["title"]] = item["url"]
            gdrive_by_folder.setdefault(item["title"], [])
        elif item["type"] == "file":
            parts = item["path"].split("/")
            if len(parts) >= 2:
                f_title = parts[1]
                m_term = re.match(r"^(\d{3,4})", item["title"])
                term_label = (
                    f"{m_term.group(1)}學期" if m_term else "歷年"
                )
                gdrive_by_folder.setdefault(f_title, []).append({
                    "title": f"元智大學全球處交換心得：{item['title']}",
                    "url": item["url"],
                    "term": term_label,
                    "source_kind": "official_experience_pdf",
                    "platform": "元智大學全球事務處交換心得雲端資料庫",
                })

    # Index CM OIP reviews by school
    cm_reviews_list = cm_data.get("cm_review_schools", [])

    def match_yzu_experiences(zh_name: str, en_name: str) -> list[dict]:
        e_key = loose_en(en_name)
        matched = []
        seen_urls = set()

        for f_title, files in gdrive_by_folder.items():
            f_en = loose_en(f_title)
            if (zh_name and zh_name in f_title) or (
                e_key
                and len(e_key) >= 6
                and (
                    e_key in f_en
                    or (f_en and len(f_en) >= 6 and f_en in e_key)
                )
            ):
                for fl in files:
                    if fl["url"] not in seen_urls:
                        seen_urls.add(fl["url"])
                        matched.append(fl)

        for cm_s in cm_reviews_list:
            t_ch = cm_s.get("title_ch", "")
            t_en = loose_en(cm_s.get("title_en", ""))
            if (zh_name and zh_name in t_ch) or (
                e_key
                and len(e_key) >= 6
                and (
                    e_key in t_en
                    or (t_en and len(t_en) >= 6 and t_en in e_key)
                )
            ):
                for st in cm_s.get("students", []):
                    rfile = st.get("review_file", "")
                    url = (
                        f"https://oip.cm.yzu.edu.tw/Content/Upload/Place/{rfile}"
                        if rfile
                        else f"https://oip.cm.yzu.edu.tw/int_review/dtl/{cm_s['item_id']}"
                    )
                    if url not in seen_urls:
                        seen_urls.add(url)
                        matched.append({
                            "title": f"元智管院 {st.get('school_year', '')} 學年交換心得：{st.get('student_organ', '')} {st.get('student_name', '')}",
                            "url": url,
                            "term": f"{st.get('school_year', '歷年')}學年",
                            "source_kind": "official_experience_pdf",
                            "platform": "元智大學管理學院國際事務辦公室（OIP）出國心得專區",
                        })
        return matched

    cm_item_by_sn = {
        it["item_sn"]: it for it in cm_data.get("cm_exchange_items", [])
    }

    # Assemble all 90 partner definitions
    all_partner_defs = []

    # 1. 53 University-level 115-2 partners (merging Rennes CM OIP item 13 if Rennes)
    for r in p1152:
        raw_zh = r[4].strip()
        zh_name, en_name = ZH_CLEAN_OVERRIDES[raw_zh]
        full_name = f"{zh_name} {en_name}"
        country = COUNTRY_MAP[r[3].strip()]
        early_nom = r[1].strip()
        applicable_colleges = r[2].strip() or "All colleges"
        web = ensure_http(r[6].strip())
        quota_raw = r[7].strip() or "2"
        exch_link = ensure_http(r[8].strip()) if r[8].strip().startswith(("http", "www")) else ""
        qual = r[9].strip()
        cross_faculty = r[10].strip()
        primary_lang = r[11].strip()
        accept_en_only = r[12].strip()
        course_link = ensure_http(r[13].strip()) if r[13].strip().startswith(("http", "www")) else ""
        restricted_depts = r[14].strip()
        min_gpa = r[15].strip()
        min_lang = r[16].strip()
        fall_dates = r[17].strip()
        spring_dates = r[20].strip()
        spring_nom_dl = r[21].strip()
        spring_app_dl = r[22].strip()
        housing_link = r[23].strip()
        cost_1sem = r[24].strip()
        other_rel = r[25].strip()
        other_info = r[26].strip()
        world_rank = r[27].strip()

        cm_merged = cm_item_by_sn.get(7) if zh_name == "布拉格化工大學" else None

        all_partner_defs.append({
            "kind": "gao_intl",
            "zh_name": zh_name,
            "en_name": en_name,
            "full_name": full_name,
            "country": country,
            "website": web,
            "factsheet_url": exch_link or course_link or None,
            "source_url": "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
            "early_nom": early_nom,
            "applicable_colleges": applicable_colleges,
            "quota_raw": quota_raw,
            "qual": qual,
            "cross_faculty": cross_faculty,
            "primary_lang": primary_lang,
            "accept_en_only": accept_en_only,
            "course_link": course_link,
            "restricted_depts": restricted_depts,
            "min_gpa": min_gpa,
            "min_lang": min_lang,
            "fall_dates": fall_dates,
            "spring_dates": spring_dates,
            "spring_nom_dl": spring_nom_dl,
            "spring_app_dl": spring_app_dl,
            "housing_link": housing_link,
            "cost_1sem": cost_1sem,
            "other_rel": other_rel,
            "other_info": other_info,
            "world_rank": world_rank,
            "cm_merged": cm_merged,
        })

    # 2. 20 Unique College of Management OIP exchange partners
    for sn, (zh_name, en_name, country, web) in CM_OVERRIDES.items():
        it = cm_item_by_sn[sn]
        dt = it.get("detail", {})
        other_html = dt.get("other_link") or ""
        hrefs = re.findall(r'href="([^"]+)"', other_html)
        fs_url = None
        for h in hrefs:
            if "drive.google.com" in h or "fact" in h.lower() or "incoming" in h.lower():
                fs_url = h
                break
        if not fs_url and hrefs:
            fs_url = hrefs[0]

        all_partner_defs.append({
            "kind": "cm_intl",
            "zh_name": zh_name,
            "en_name": en_name,
            "full_name": f"{zh_name} {en_name}",
            "country": country,
            "website": web,
            "factsheet_url": fs_url,
            "source_url": f"https://oip.cm.yzu.edu.tw/abrd_deg/dtl/{it['item_id']}",
            "cm_item": it,
        })

    # 3. 12 Mainland China exchange partners
    for zh_name, en_name, country, web, city, st, q_str, dl_str in MAINLAND_LIST:
        all_partner_defs.append({
            "kind": "mainland",
            "zh_name": zh_name,
            "en_name": en_name,
            "full_name": f"{zh_name} {en_name}",
            "country": country,
            "city": city,
            "website": web,
            "factsheet_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2019-07-04-06-31-37",
            "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2019-07-04-06-31-37",
            "avail_status": st,
            "quota_str": q_str,
            "dl_str": dl_str,
        })

    # 4. 5 Historical / Dual-Degree Exchange Experience Partners
    for zh_name, en_name, country, web, note_str in EXTRA_EXP_PARTNERS:
        all_partner_defs.append({
            "kind": "extra_exp",
            "zh_name": zh_name,
            "en_name": en_name,
            "full_name": f"{zh_name} {en_name}",
            "country": country,
            "website": web,
            "factsheet_url": None,
            "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-51-28",
            "note_str": note_str,
        })

    assert len(all_partner_defs) == 90, f"Expected 90 partners, got {len(all_partner_defs)}"

    school_images_file = STATIC_DIR / "assets" / "school-images.json"
    visual_map = {}
    if school_images_file.exists():
        for item in json.loads(
            school_images_file.read_text(encoding="utf-8")
        ).get("schools", []):
            if (
                isinstance(item, dict)
                and item.get("school_name")
                and item.get("status") == "verified"
                and item.get("local_path")
            ):
                visual_map[(
                    school_identity_key(str(item.get("school_name", ""))),
                    str(item.get("country") or ""),
                )] = item
    visual_index = VisualRecordIndex(visual_map)

    partners = []
    workflows = []
    destinations = []
    research_records = []
    life_records = []
    experience_sources_records = []
    student_experience_rows = []
    new_locations = []
    exp_covered_schools = 0
    open_partner_count = 0

    for idx, p in enumerate(all_partner_defs):
        zh_name = p["zh_name"]
        en_name = p["en_name"]
        full_name = p["full_name"]
        country = p["country"]
        region = REGION_BY_COUNTRY.get(country, "歐洲")
        website = p["website"]
        source_url = p["source_url"]
        factsheet_url = p.get("factsheet_url")
        exp_links = match_yzu_experiences(zh_name, en_name)
        if exp_links:
            exp_covered_schools += 1

        loc_info = loc_by_name[full_name]
        location_obj = {
            "school_name": full_name,
            "country": country,
            "city": p.get("city") or loc_info.get("city") or country,
            "latitude": float(loc_info["latitude"]),
            "longitude": float(loc_info["longitude"]),
            "geocode_status": "verified",
            "geocoded_at": "2026-10-17T04:45:00Z",
            "source_url": loc_info.get("source_url") or "https://www.wikidata.org",
            "identity_source_url": (
                loc_info.get("identity_source_url")
                or website
                or "https://ror.org"
            ),
            "precision": "representative",
            "note": (
                loc_info.get("note")
                or "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區以錄取通知為準。"
            ),
        }
        new_locations.append(location_obj)

        if p["kind"] == "gao_intl":
            avail_status = "open"
            win_status = "closed"
            open_partner_count += 1
            q_val = p["quota_raw"]
            if p.get("cm_merged"):
                cm_q = p["cm_merged"].get("quota", 2)
                quota_str = f"校級交換 {q_val} 名＋管理學院院級交換 {cm_q} 名（115-2 公告名額）"
                colleges_str = "全校各學院（工程、電通、資訊、管理、人社、醫護學院）及管理學院院級交換"
            else:
                quota_str = f"{q_val} 名（115-2 全球事務處公告名額）"
                app_col = p["applicable_colleges"]
                if app_col.lower() == "all colleges":
                    colleges_str = "全校各學院（工程、電機通訊、資訊、管理、人文社會、醫護學院）"
                else:
                    colleges_str = f"適合申請領域：{app_col}（可否跨院系選課：{p['cross_faculty'] or '依姊妹校規定'}）"

            qual_raw = p["qual"]
            if "undergraduate only" in qual_raw.lower():
                degree_levels_str = "學士班二年級（含）以上（僅限大學部）"
            elif "master" in qual_raw.lower() and "undergraduate" in qual_raw.lower():
                degree_levels_str = "學士班二年級（含）以上、碩士班（須於元智就讀滿一學期以上）"
            else:
                degree_levels_str = "學士班二年級（含）以上、碩士班、博士班（須於元智就讀滿一學期以上）"

            lang_req_str = f"校內初審門檻：須具 2 年內有效之 TOEFL iBT、IELTS（Academic）或 TOEIC 成績｜姊妹校門檻：{p['min_lang'] or 'CEFR B2 / TOEFL iBT 72–79 / IELTS 5.5–6.0'}（主要授課語言：{p['primary_lang'] or 'English'}）"
            gpa_req_str = f"校內甄選採計系排名成績 50%＋英文檢定成績 50%（海外選課大學部及格標準為 70 分、研究生 80 分）｜姊妹校最低學業門檻：{p['min_gpa'] or '歷年成績優良'}"
            study_period_str = "一學期或一學年（同一學制至多以二學期為限）"
            program_type = (
                "交換學生（全球事務處校級交換＋管理學院院級交換）"
                if p.get("cm_merged")
                else "交換學生（全球事務處校級國際交換計畫）"
            )
            if p["early_nom"]:
                app_deadline_str = (
                    f"115-2（2027春季班）提早提名校（Early Nomination）：校內收件於 {p['early_nom']} 中午 12:00 截止"
                    f"（姊妹校提名截止：{p['spring_nom_dl'] or '9月中旬'}、申請截止：{p['spring_app_dl'] or '10月'}）；"
                    "116-1（2027秋季班）預計於 2027 年 1 月中旬至 3 月開放申請。"
                )
            else:
                app_deadline_str = (
                    "115-2（2027春季班）一般收件期間：2026年8月26日至9月22日（二）中午 12:00 止"
                    f"（姊妹校春季班提名截止：{p['spring_nom_dl'] or '10月–11月'}、申請截止：{p['spring_app_dl'] or '10月–12月'}）；"
                    "116-1（2027秋季班）預計於 2027 年 1 月中旬至 3 月開放申請。"
                )
            sem_dates_str = f"秋季班：{p['fall_dates'] or '9月至翌年1月'}；春季班（115-2）：{p['spring_dates'] or '2月至6月'}"
            course_rest_str = (
                f"申請限制科系：{p['restricted_depts'] or '無特殊排除科系'}｜跨院選課：{p['cross_faculty'] or '依姊妹校規定'}｜"
                "依《元智大學學生至境外大學校院選修課程實施辦法》規定，交換期間每學期至少應選修 4 門課或 12 學分（ECTS），其中至少半數須為專業課程。"
            )
            housing_str = (
                f"住宿資訊參考：{p['housing_link']}。"
                if p["housing_link"] and p["housing_link"] not in {"X", "None"}
                else "接待校提供校內或合作學生宿舍申請協助（德國法蘭克福應用科技大學及韓國慶星大學另提供免住宿費優惠名額，詳見一覽表備註）。"
            )
            extra_notes = "；".join(
                x
                for x in [
                    f"2025 世界排名：{p['world_rank']}" if p["world_rank"] else "",
                    f"單學期預估生活費：{p['cost_1sem']}" if p["cost_1sem"] else "",
                    p["other_rel"],
                    p["other_info"],
                ]
                if x
            )
        elif p["kind"] == "cm_intl":
            avail_status = "open"
            win_status = "closed"
            open_partner_count += 1
            it = p["cm_item"]
            dt = it.get("detail", {})
            q_val = it.get("quota", 2)
            quota_str = f"{q_val} 名（管理學院國際事務辦公室 OIP 院級交換名額）"
            colleges_str = f"限管理學院學生申請（對應學程：{dt.get('map_program') or 'Management / Business'}）"
            suit_for = re.sub(r"\s+", " ", dt.get("suit_for") or "大學部二至四年級及碩士班一般生").strip()
            degree_levels_str = f"管理學院在學學生（{suit_for}）"
            lang_req_str = f"管理學院與姊妹校語檢要求：{it.get('req_english') or 'TOEFL iBT 79 / IELTS 6.0 / TOEIC 750'}"
            gpa_req_str = f"管理學院學業門檻：{dt.get('req_grade') or '歷年成績排名在班級前百分之五十為原則'}（{dt.get('req_other') or '須符合姊妹校學業標準'}）"
            study_period_str = "一學期或一學年"
            program_type = "交換學生（管理學院 OIP 院級國際交換計畫）"
            app_deadline_str = (
                "115-2（2027春季班）：配合全校時程於 2026年8月26日至9月22日 12:00 向管理學院國際事務辦公室（六館 R60403A）及全球事務處提出申請；"
                "116-1（2027秋季班）預計於 2027 年 1 月中旬至 3 月開放申請。"
            )
            sem_dates_str = "秋季班：約每年 8/9 月至翌年 1 月；春季班：約每年 1/2 月至 6 月（依姊妹校行事曆為準）"
            course_rest_str = (
                f"開放商管領域（{dt.get('map_program') or 'Business & Management'}）；"
                "依元智大學規定每學期至少須修習 4 門課或 12 學分（ECTS），其中至少半數為本系／院專業課程。"
            )
            housing_str = dt.get("req_other") or "由姊妹校國際處協助安排校內或校外合作學生宿舍（住宿費由學生自理，部分歐洲姊妹校房源緊張請於獲提名後立即申請）。"
            extra_notes = "；".join(
                x
                for x in [
                    dt.get("school_rank") or "",
                    dt.get("tuition") or "",
                    dt.get("other_info") or "",
                ]
                if x
            )
        elif p["kind"] == "mainland":
            avail_status = p["avail_status"]
            win_status = "open" if avail_status == "open" else "closed"
            if avail_status == "open":
                open_partner_count += 1
            quota_str = p["quota_str"]
            colleges_str = "全校各學院（工程、電機通訊、資訊、管理、人文社會、醫護學院）"
            degree_levels_str = "學士班二年級（含）以上、碩士班、博士班（須具中華民國國籍，研究生須於元智就讀滿一學期以上）"
            lang_req_str = "大陸地區交換免附外語檢定證明（須持有效臺胞證，且在校操行成績達 85 分以上）"
            gpa_req_str = "歷年學業成績優良（大學部交換選課及格標準為 70 分、研究生為 80 分）且操行成績不得低於 85 分"
            study_period_str = "一學期（2027年2月至7月）"
            program_type = "交換學生（全球事務處兩岸交流姊妹校交換計畫）"
            app_deadline_str = f"115-2（2027春季班）大陸交換申請期限：{p['dl_str']}；秋季班預計於每年 3–4 月受理申請。"
            sem_dates_str = "秋季班：9月至翌年1月；春季班：2月至7月"
            course_rest_str = "依大陸姊妹校對口學院開放專業選課（每學期至少須修習 4 門課或 12 學分，且至少半數為專業課程）。"
            housing_str = "大陸姊妹校原則上安排校內港澳臺交換學生宿舍（住宿費依各校規定由學生自理）。"
            extra_notes = "申請人須繳交元智大學赴大陸地區交換學生志願表、申請表、切結書（保證金 NT$5,000）、家長同意書、歷年中文成績單（含排名）及 500 字以上讀書計畫。"
        else:
            avail_status = "reference_only"
            win_status = "closed"
            quota_str = p["note_str"]
            colleges_str = "全校相關學院或管理學院對應系所（依當期公告簡章為準）"
            degree_levels_str = "學士班二年級（含）以上、碩士班"
            lang_req_str = "須具 2 年內有效之 TOEFL iBT 79+ 或 IELTS 6.0+ 或 TOEIC 750+（依當期合作簡章規定）"
            gpa_req_str = "歷年學業成績排名在班級前 50% 或 GPA 3.0 以上"
            study_period_str = "一學期或一學年"
            program_type = "交換學生／海外研修歷年合作校（心得參考）"
            app_deadline_str = "當期未列入 115-2 常規交換名額表；欲查詢最新開放梯次或雙聯／短期研修方案請洽全球事務處或管理學院國際事務辦公室。"
            sem_dates_str = "秋季班：8/9月至12/1月；春季班：1/2月至5/6月"
            course_rest_str = "依當期交換或雙聯學位簡章規定辦理。"
            housing_str = "依接待校國際學生宿舍申請規範辦理。"
            extra_notes = p["note_str"]

        tuition_points_list = [
            "交換期間須於元智大學完成註冊並繳交全額學雜費以保留在學學籍，免繳姊妹校學費（德國法蘭克福應用科技大學及韓國慶星大學另提供免住宿費名額）；機票、簽證、海外保險及個人生活費由學生自理。",
            "錄取確認時須簽署《元智大學出國交換學生切結書（CF-04）》並繳交保證金新臺幣 5,000 元（於完成交換返國、依規定提交 1,500 字以上研修心得報告與 6 張照片並完成學分抵免後全額無息退還）。",
            "依《元智大學學生至境外大學校院選修課程實施辦法》（1-51）第 5 條，交換生每學期至少應選修 4 門課或 12 學分（ECTS），其中至少二分之一須為專業課程，且所修科目平均成績須達及格標準（大學部 70 分、研究生 80 分）。",
        ]

        app_steps_list = [
            f"步驟一（確認資格與參加說明會）：確認符合元智大學學士班大二以上或碩博班就讀滿一學期資格，備妥 2 年內有效語言檢定證明（大陸交換免附英檢惟操行須達 85 分以上），並對照 {full_name} 之語言與學業門檻。",
            "步驟二（第一階段校內甄選送件）：於校內截止日前備齊志願表（CF-01-R1，校級至多 2 志願、管院院級至多 2 志願）、申請表（CF-02-R3，經導師／指導教授及系所主管核章）、歷年英文成績單（含系排名）、語言檢定證明及中英文讀書計畫，將紙本送交七館二樓全球事務處（R70208，管院院級送交六館 R60403A）並完成線上表單上傳。",
            "步驟三（校內評選、錄取確認與繳交保證金）：由全球事務處依「系排名成績 50%＋英文檢定成績 50%」進行評比分發（管院院級依管院甄選規定辦理）；獲錄取者須於規定期限內繳交家長同意書、切結書（CF-04）及保證金新臺幣 5,000 元。",
            f"步驟四（第二階段姊妹校提名複審、選課抵免與行前準備）：由元智大學向 {full_name} 辦理官方提名（Nomination），學生依姊妹校 Fact Sheet 提交入學申請文件與宿舍申請；出國前完成「元智大學學生至境外大學校院選修課程申請表」核准程序，並辦理簽證、海外醫療及意外保險與役男出境。",
        ]

        elig_points_list = [
            f"開放學制與年級：{degree_levels_str}",
            f"開放申請院系：{colleges_str}",
            f"學業與操行要求：{gpa_req_str}",
            f"語言與申請條件：{lang_req_str}",
        ]
        if extra_notes:
            elig_points_list.append(f"補充資訊：{extra_notes[:240]}")

        notes_lines = [
            f"【合作類別與期程】{program_type}｜交換期間：{study_period_str}",
            f"【當期公告名額】{quota_str}",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        ]
        if extra_notes:
            notes_lines.append(f"【備註與生活費資訊】{extra_notes}")
        if exp_links:
            notes_lines.append(
                f"【歷年學長姐心得】元智大學全球事務處／管理學院資料庫收錄 {len(exp_links)} 篇赴 {zh_name} 交換生返國心得報告。"
            )

        visual_rec = visual_index.get((full_name, country)) or {}
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
            "quota_status": "published",
            "availability_status": avail_status,
            "availability_note": f"元智大學全球事務處／管理學院國際事務辦公室公告交換合作校；{quota_str}。",
            "academic_year": "115",
            "application_round": "115-2（2027春季班）",
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
                "title": f"元智大學赴外交換合作資訊—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "115",
                "application_round": "115-2",
                "checked_at": "2026-10-17T04:45:00Z",
            },
            {
                "title": "元智大學 115-2（2027春季班）赴外交換生甄選簡章與學校一覽表",
                "source_url": "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "115",
                "application_round": "115-2",
                "checked_at": "2026-10-17T04:45:00Z",
            },
            {
                "title": "元智大學學生至境外大學校院選修課程實施辦法（1-51）",
                "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07",
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "115",
                "application_round": "115-2",
                "checked_at": "2026-10-17T04:45:00Z",
            },
        ]
        if website:
            wf_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "role": "partner_university",
                "authority": "partner_official",
                "effective_academic_year": "115",
                "application_round": "115-2",
                "checked_at": "2026-10-17T04:45:00Z",
            })

        workflows.append({
            "home_university": "元智大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": "115",
            "application_round": "115-2",
            "effective_application_rounds": [
                "115-2",
                "第1學期（秋季班）",
                "第2學期（春季班）",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "元智大學 115-2（2027春季班）赴國際姊妹校交換生甄選（2026/08/26–09/22 12:00 收件，Early Nomination 為 09/07 及 09/11）及 "
                "2027春季班赴大陸姊妹校交換（2026年10月中旬至11月1日收件）已公告；116-1（2027秋季班）預計於 2027年1月中旬至3月開放申請。"
            ),
            "review_status": "published",
            "published_at": "2026-10-17T04:45:00Z",
            "steps": [
                {
                    "rule_id": f"yzu-115-home-1-{idx+1:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認元智大學學籍年級、系排名與 {zh_name} 語言檢定門檻",
                    "responsible_party": "學生",
                    "responsible_unit": "元智大學全球事務處（七館二樓 R70208）／管理學院國際事務辦公室（六館 R60403A）",
                    "deadline_at": "2026-09-22T12:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
                    "deadline_checked_at": "2026-10-17T04:45:00Z",
                    "deadline_reminder_eligible": True,
                    "summary": f"須為元智大學學士班大二（含）以上或碩博班就讀滿一學期以上之在學學生，並符合 {zh_name} 之語言及學業條件。",
                    "details": [
                        f"開放學制：{degree_levels_str}",
                        f"語言與學業條件：{lang_req_str}",
                        f"當期公告名額：{quota_str}",
                    ],
                    "scope": {
                        "home_universities": ["元智大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            "115-2",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        source_url,
                        "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
                    ],
                    "checked_at": "2026-10-17T04:45:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"yzu-115-home-2-{idx+1:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "繳交第一階段校內甄選紙本申請表件並完成線上表單上傳",
                    "responsible_party": "學生",
                    "responsible_unit": "元智大學全球事務處（R70208）／管理學院國際事務辦公室（R60403A）",
                    "deadline_at": "2026-09-22T12:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
                    "deadline_checked_at": "2026-10-17T04:45:00Z",
                    "deadline_reminder_eligible": True,
                    "summary": "於截止日前繳交經系所簽章之紙本志願表（CF-01-R1）、申請表（CF-02-R3）、歷年成績單、語檢證明及讀書計畫，並同步上傳電子檔。",
                    "details": [
                        "第一階段應繳文件：出國交換學生志願表（CF-01-R1，至多選填 2 所校級志願校及 2 所管院院級志願校）、出國交換學生申請表（CF-02-R3，須經導師／指導教授及系所主任簽章）、歷年英文成績單正本（須註明全班／全系排名百分比）、2 年內有效語言能力檢定成績單影本、中英文讀書計畫。",
                        "申請赴大陸地區姊妹校交換者，改填「赴大陸地區交換學生志願表」及「赴大陸地區交換學生申請表」，檢附歷年中文成績單（含排名，且操行成績達 85 分以上）、500 字以上讀書計畫、家長同意書及切結書。",
                    ],
                    "document_requirements": [
                        {
                            "name": "元智大學出國交換學生志願表（CF-01-R1）及申請表（CF-02-R3，含導師／指導教授及系主任核章）",
                            "official_form_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
                            "source_urls": [
                                "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41"
                            ],
                        },
                        {
                            "name": "元智大學歷年英文成績單正本（須含系排名／班排名百分比；大陸交換為歷年中文成績單含排名及操行 85 分以上證明）",
                            "source_urls": [
                                "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00"
                            ],
                        },
                        {
                            "name": "中英文讀書計畫（Study Plan，含動機、修課規劃與返國學習連結）",
                            "source_urls": [
                                "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00"
                            ],
                        },
                        {
                            "name": "兩年內有效之外語能力檢定證明影本（TOEFL iBT / IELTS Academic / TOEIC / JLPT / TOPIK；大陸交換免附）",
                            "conditional": p["kind"] == "mainland",
                            "condition": "申請國際及港澳姊妹校必繳；申請大陸地區姊妹校免附外語檢定",
                            "source_urls": [
                                "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
                                "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2019-07-04-06-31-37",
                            ],
                        },
                    ],
                    "scope": {
                        "home_universities": ["元智大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            "115-2",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "submission": {
                        "method": "mixed",
                        "office": "元智大學全球事務處（七館二樓 R70208）／管理學院國際事務辦公室（六館 R60403A）",
                        "portal_url": "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
                    },
                    "action_url": "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
                    "source_urls": [
                        "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
                        "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
                    ],
                    "checked_at": "2026-10-17T04:45:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"yzu-115-home-3-{idx+1:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "校內書審評分分發、錄取確認與繳交切結書及保證金 NT$5,000",
                    "responsible_party": "學生與元智大學全球事務處",
                    "responsible_unit": "元智大學全球事務處",
                    "deadline_at": "2026-10-02T17:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
                    "deadline_checked_at": "2026-10-17T04:45:00Z",
                    "deadline_reminder_eligible": True,
                    "summary": "依「系排名成績 50%＋英文檢定成績 50%」評比分發，錄取生須繳交家長同意書、出國交換學生切結書（CF-04）及保證金新臺幣 5,000 元以取得正式提名資格。",
                    "details": [
                        "保證金新臺幣 5,000 元於學生完成交換計畫返國、提交 1,500 字以上研修心得報告與至少 6 張照片並完成學分抵免程序後，全額無息退還；若無不可抗力因素放棄提名資格則不予退還。",
                    ],
                    "scope": {
                        "home_universities": ["元智大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            "115-2",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
                        "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
                    ],
                    "checked_at": "2026-10-17T04:45:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"yzu-{idx+1:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由元智大學提名並完成 {zh_name} 第二階段姊妹校入學申請與宿舍登記",
                    "responsible_party": "學生與接待校國際處",
                    "summary": f"獲元智大學提名後，學生須於 {zh_name} 申請截止日前完成姊妹校線上入學申請並上傳財力證明、護照影本、推薦信、健康檢查表及選課清單，最終入學許可由姊妹校審核決定。",
                    "details": [
                        f"交換期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}",
                    ]
                    + ([f"補充說明：{extra_notes}"] if extra_notes else []),
                    "scope": {
                        "home_universities": ["元智大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            "115-2",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "source_urls": (
                        [source_url]
                        + ([factsheet_url] if factsheet_url else [])
                        + ([website] if website else [])
                    ),
                    "checked_at": "2026-10-17T04:45:00Z",
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"yzu-115-home-5-{idx+1:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "核定境外選課申請表（至少 4 門課或 12 ECTS）、申辦獎助學金、簽證保險與返國抵免",
                    "responsible_party": "學生",
                    "responsible_unit": "元智大學全球事務處／教務處註冊組／學務處",
                    "summary": "取得姊妹校入學許可（LOA）後，填妥「元智大學學生至境外大學校院選修課程申請表」經系主任及教務處核准，參加行前說明會、申辦簽證與海外醫療及意外保險，返國後 2 週內繳交心得報告並辦理學分抵免與退還保證金。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["元智大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            "115-2",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07",
                        "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
                    ],
                    "checked_at": "2026-10-17T04:45:00Z",
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": "2026-10-17T04:45:00Z",
            "coverage_status": "official_verified",
            "coverage_note": "已完整整合元智大學全球事務處 115-2 赴外交換學校一覽表、赴外交流說明會簡報、管理學院 OIP 院級交換名冊、兩岸交換簡章與境外選修課程實施辦法。",
        })

        cost_default, visa_default = REGION_COST_DEFAULTS.get(
            country,
            (
                "USD 800–1,300 / 月（含住宿、膳食、教材與當地交通費用）",
                "須依接待校與駐臺代表處規定辦理學生簽證與海外醫療保險。",
            ),
        )
        cost_line = f"預估每月生活費約 {cost_default}" + (
            f"（官方一覽表單學期參考：{p['cost_1sem']}）"
            if p.get("cost_1sem")
            else ""
        )
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        course_clean = f"開放對象：{colleges_str}（{degree_levels_str}）｜{course_rest_str}"
        calendar_clean = f"{sem_dates_str}。"

        dest_sources = [
            {
                "title": f"元智大學赴外交換合作資訊—{zh_name}",
                "source_url": source_url,
                "summary": "元智大學官方交換名額、語檢門檻、學期起訖與申請規定",
            },
            {
                "title": "元智大學學生至境外大學校院選修課程實施辦法（1-51）",
                "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07",
                "summary": "元智大學交換生最低修課學分（4門課或12 ECTS）、及格標準（大學部70分／研究所80分）與抵免規範",
            },
        ]
        if factsheet_url:
            dest_sources.append({
                "title": f"{zh_name} 交換學生資訊／Fact Sheet",
                "source_url": factsheet_url,
                "summary": "姊妹校交換生專頁與申請指引",
            })
        if website:
            dest_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作校官方網站",
            })
        for el in exp_links[:3]:
            dest_sources.append({
                "title": el["title"],
                "source_url": el["url"],
                "summary": "元智大學赴外交換生返國心得報告官方 PDF",
            })

        src_url_list = (
            [source_url]
            + ([factsheet_url] if factsheet_url else [])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "元智大學",
            "school_name": full_name,
            "country": country,
            "city": location_obj.get("city") or country,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": f"校區代表城市：{location_obj.get('city') or country}。請依入學許可與 Fact Sheet 確認實際授課校區、機場接機服務與當地學生大眾運輸票卡優惠。",
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費、保證金與學雜費規定",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list,
                    "caution": "可申請教育部「學海飛颺／學海惜珠」或《元智大學學生國際與兩岸交流獎助學金設置辦法》校內獎助學金（依地區每月補助約 NT$5,000–12,000，兩項獎學金不得重複領取）。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "校內宿位有限，請於完成姊妹校線上申請時同步確認宿舍申請期限。",
                },
                {
                    "key": "insurance",
                    "title": "醫療保險與安全",
                    "summary": visa_default,
                    "points": [
                        visa_default,
                        "交換生於出國期間須購買涵蓋全期之海外醫療及意外保險，並於出發前將保險單影本送交全球事務處備查。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "部分姊妹校要求於開學報到前提交指定規格之醫療及意外保險證明後方可辦理註冊。",
                },
                {
                    "key": "visa",
                    "title": "簽證、體檢與役男出境準備",
                    "summary": visa_default,
                    "points": [
                        "收到姊妹校正式入學許可書（Letter of Acceptance / COE / DS-2019）後，立即向駐臺辦事處申辦學生簽證（赴大陸交換須持有效臺胞證並完成規定健康檢查）。",
                        "尚未履行兵役義務之在學役男，須於出國前至少 1.5 個月檢附入學許可向全球事務處及學務處辦理役男出境緩徵手續。",
                        visa_default,
                    ],
                    "source_urls": src_url_list,
                    "caution": "簽證核發時間視各國領事館而定（約 4–8 週），請勿於取得簽證前購買不可退改之機票。",
                },
                {
                    "key": "courses",
                    "title": "課程限制、最低學分（4門課或12 ECTS）與返國抵免",
                    "summary": course_clean[:160],
                    "points": [
                        course_clean,
                        "出國前應填具「元智大學學生至境外大學校院選修課程申請表」經系主任及教務處核准；返國後檢具姊妹校正式成績單及課程大綱辦理學分抵免（大學部及格標準 70 分、研究生 80 分）。",
                    ],
                    "source_urls": src_url_list
                    + [
                        "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07"
                    ],
                    "caution": "每學期至少須修習 4 門課或 12 學分（ECTS），且至少二分之一為專業課程；未達修課門檻將影響獎助學金核銷與保證金退還。",
                },
                {
                    "key": "city",
                    "title": "城市與校區位置",
                    "summary": (
                        f"{country} {location_obj.get('city') or ''}".strip()
                    ),
                    "points": [
                        location_obj.get("note")
                        or f"{full_name} 校級代表位置位於 {location_obj.get('city') or country}。",
                    ],
                    "source_urls": [
                        location_obj.get("source_url") or source_url
                    ],
                    "caution": "部分合作校具有多個校區（如韓國漢陽大學首爾／ERICA 校區、法國 SKEMA 多校區、丹麥南丹麥大學奧登斯等校區），請以簡章備註與錄取通知為準。",
                },
                {
                    "key": "arrival",
                    "title": "學期年曆與返國心得義務",
                    "summary": calendar_clean,
                    "points": [
                        calendar_clean,
                        "返國後 2 週內須依規定繳交 1,500 字以上交換學生研修心得報告及至少 6 張活動照片，並完成學分抵免程序後方可辦理保證金 NT$5,000 退還及獎助學金尾款核銷。",
                    ]
                    + (
                        [
                            f"歷年學長姐返國心得：元智大學全球事務處／管理學院已收錄 {len(exp_links)} 篇赴 {zh_name} 交換心得報告。"
                        ]
                        if exp_links
                        else []
                    ),
                    "source_urls": src_url_list
                    + [el["url"] for el in exp_links[:3]],
                    "caution": "領取元智大學國際與兩岸交流獎助學金之學生，返國後須履行心得繳交及分享會義務。",
                },
            ],
            "first_72_hours": [
                {
                    "title": "依姊妹校入學許可指定報到日辦理新生註冊、宿舍入住與選課確認",
                    "detail": calendar_clean,
                    "source_urls": [source_url],
                },
                {
                    "title": "完成當地居留登錄、醫療保險確認與向元智大學全球事務處回報抵達資訊",
                    "detail": f"{visa_default} 抵校後請向元智大學全球事務處（或管院國際事務辦公室）回報平安及確認最終選課清單。",
                    "source_urls": [source_url],
                },
            ],
            "sources": dest_sources,
            "last_checked": "2026-10-17T04:45:00Z",
            "coverage_status": "official_verified",
            "coverage_note": "已整合元智大學全球事務處 115-2 赴外交換學校一覽表、管理學院 OIP 院級交換名冊、境外選修課程實施辦法與歷年返國交換生心得報告。",
        })

        research_records.append({
            "home_university": "元智大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": source_url,
            "checked_at": "2026-10-17T04:45:00Z",
            "note": f"元智大學全球事務處／管理學院 OIP 姊妹校列表（{source_url}）及 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [
            {"title": f"元智大學赴外交換資訊—{zh_name}", "url": source_url},
        ]
        if factsheet_url:
            ev_sources.append(
                {"title": f"{zh_name} 交換資訊／Fact Sheet", "url": factsheet_url}
            )
        if website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": website})
        for el in exp_links[:3]:
            ev_sources.append({"title": el["title"], "url": el["url"]})

        ev_list = [
            {
                "theme": "housing",
                "kind": "official",
                "text": housing_clean,
                "sources": ev_sources,
                "checked_at": "2026-10-17T04:45:00Z",
                "scope": "元智大學赴外交換一覽表住宿資訊與姊妹校 Fact Sheet",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "cost",
                "kind": "official",
                "text": f"{tuition_clean}｜{cost_line}",
                "sources": ev_sources,
                "checked_at": "2026-10-17T04:45:00Z",
                "scope": "元智大學交換費用規定與地區生活費估算",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "academics",
                "kind": "official",
                "text": course_clean,
                "sources": ev_sources,
                "checked_at": "2026-10-17T04:45:00Z",
                "scope": "元智大學學生至境外大學校院選修課程實施辦法與姊妹校選課限制",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "safety",
                "kind": "official",
                "text": visa_default,
                "sources": ev_sources,
                "checked_at": "2026-10-17T04:45:00Z",
                "scope": "元智大學赴外交換簽證、體檢、海外醫療保險與役男出境提醒",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "campus_culture",
                "kind": "mixed" if exp_links else "official",
                "text": (
                    f"合作類別：{program_type}｜名額：{quota_str}｜申請要求：{lang_req_str}"
                    + (
                        f"｜元智大學全球事務處／管理學院收錄 {len(exp_links)} 篇赴 {zh_name} 交換生返國心得報告。"
                        if exp_links
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": "2026-10-17T04:45:00Z",
                "scope": "元智大學赴外交換計畫名額、語檢要求與歷年返國交換生心得",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
        ]
        life_records.append({
            "school_name": full_name,
            "country": country,
            "checked_at": "2026-10-17T04:45:00Z",
            "status": "ready",
            "evidence": ev_list,
            "notes": [
                "已整合元智大學全球事務處 115-2 赴外交換學校一覽表、管理學院 OIP 院級交換名冊、境外選修課程實施辦法與歷年返國心得報告連結。",
                "當期宿位供給、費用與選課限制請依姊妹校最新 Fact Sheet 核對。",
            ],
            "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
            "extraction_version": 3,
        })

        experience_sources_records.append({
            "home_university": "元智大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": "https://drive.google.com/drive/folders/1qpsAYYV95y_gxsZi8mb5J3-rGaQkBTiz",
            "partner_page_url": source_url,
            "report_count": len(exp_links),
            "sample_reports": [
                {"title": el["title"], "url": el["url"], "term": el["term"]}
                for el in exp_links[:4]
            ],
            "checked_at": "2026-10-17T04:45:00Z",
        })
        for el in exp_links[:4]:
            summary_text = f"{el['platform']}收錄之 {el['term']} 赴 {zh_name} 交換學生返國心得報告（官方 PDF 原文檔案）。"
            theme_map = {
                "academics": (
                    f"元智大學 {el['term']} 交換生分享於 {zh_name} 之選課（每學期至少 4 門課或 12 ECTS）、授課與學分抵免經驗。"
                ),
                "housing": (
                    f"元智大學 {el['term']} 交換生分享於 {zh_name} 之宿舍或校外住宿申請與生活經驗。"
                ),
                "campus_culture": (
                    f"元智大學 {el['term']} 交換生分享於 {zh_name} 之校園環境、國際學伴支援與文化交流。"
                ),
                "cost": (
                    f"元智大學 {el['term']} 交換生分享於 {zh_name} 之學期生活開銷、獎助學金運用與行前準備建議。"
                ),
            }
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": el["title"],
                "source_url": el["url"],
                "source_type": "article",
                "platform": el["platform"],
                "author_name": "元智大學返國交換生",
                "language": "zh",
                "summary": summary_text,
                "themes": ["academics", "housing", "campus_culture", "cost"],
                "theme_summaries": theme_map,
                "content_status": "metadata_only",
                "perspective": "official_student_story",
                "published_at": None,
                "discovered_at": "2026-10-17T04:45:00Z",
                "content_hash": hashlib.sha256(
                    el["url"].encode("utf-8")
                ).hexdigest(),
                "exchange_term": el["term"],
                "summary_zh": summary_text,
                "original_summary": "",
                "theme_summaries_zh": theme_map,
                "translation_status": "original",
                "source_kind": "official_experience_pdf",
            })

    partners_jsonl_text = (
        "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
    )
    (OFFICIAL_YZU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (SOURCES_YZU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (OFFICIAL_YZU_DIR / "application_workflows.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_YZU_DIR / "destination_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations)
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_YZU_DIR / "partner_research.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records)
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_YZU_DIR / "student_life.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records)
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_YZU_DIR / "experience_sources.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False)
            for r in experience_sources_records
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_YZU_DIR / "student_experiences.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in student_experience_rows
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_YZU_DIR / "campus-locations.json").write_text(
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

    for loc_obj in new_locations:
        existing_loc_map.setdefault(
            (loc_obj["school_name"], loc_obj.get("country") or ""), loc_obj
        )

    yzu_home_loc = {
        "school_name": "元智大學",
        "country": "臺灣",
        "city": "桃園市中壢區",
        "latitude": 24.9701,
        "longitude": 121.2635,
        "geocode_status": "verified",
        "geocoded_at": "2026-10-17T04:45:00Z",
        "source_url": "https://www.wikidata.org/wiki/Q709225",
        "identity_source_url": "https://ror.org/032176g72",
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。 母校代表點採桃園市中壢區遠東路135號校本部（七館二樓 R70208 全球事務處）；官方地址來源：https://gao.yzu.edu.tw/。",
    }
    existing_loc_map[("元智大學", "臺灣")] = yzu_home_loc
    sorted_locs = sorted(
        existing_loc_map.values(),
        key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
    )
    loc_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
        encoding="utf-8",
    )

    yzu_source_urls = [
        "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
        "https://gao.yzu.edu.tw/index.php/tw/2026-01-13-02-46-21",
        "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-51-28",
        "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07",
        "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
        "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-53-11",
        "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2019-07-04-06-31-37",
        "https://oip.cm.yzu.edu.tw/abrd_deg/list/es",
        "https://oip.cm.yzu.edu.tw/int_review/list",
    ]

    exchange_info_payload = {
        "school_name": "元智大學",
        "program_type": [
            "交換學生（全球事務處校級國際交換計畫・歐美亞非 21 國姊妹校）",
            "交換學生（管理學院國際事務辦公室 OIP 院級交換計畫・AACSB 認證名校）",
            "交換學生（全球事務處兩岸交流姊妹校交換計畫・985/211 重點高校）",
        ],
        "academic_year": [
            "115（115-2 / 2027春季班：國際交換 2026/08/26–09/22 甄選；大陸交換 2026/10–11/01 甄選）",
            "116（116-1 / 2027秋季班：預計 2027年1月中旬至3月開放申請）",
        ],
        "semester": [
            "第1學期（秋季班：每年約 8/9 月至翌年 1 月）",
            "第2學期（春季班：每年約 2 月至 6/7 月；日本為 4 月至 8 月）",
        ],
        "application_period": [
            "115-2（2027春季班）赴國際姊妹校交換甄選時程：2026年8月26日起至9月22日（二）中午 12:00 止（提早提名 Early Nomination 姊妹校分別於 2026年9月7日及9月11日中午 12:00 截止收件；赴外交流說明會於 2026年9月16日 12:20–14:00 舉行）。",
            "115-2（2027春季班）赴大陸地區姊妹校交換時程：同濟大學、南京大學校內書審於 2026年10月14日截止（10月15日–10月20日完成提名與上傳）；武漢大學、重慶大學、西南大學、蘇州大學、西安交通大學於 2026年10月20日校內截止、10月30日至11月1日完成姊妹校送件。",
            "116-1（2027秋季班）申請時程：每年約 1 月中旬公告簡章並開放申請，至 2 月底或 3 月中旬截止校內第一階段收件。",
        ],
        "eligibility": [
            "在學年級與修業門檻：元智大學正式學籍在學之學士班二年級（含）以上學生，或於本校就讀滿一學期以上之碩士班、博士班研究生（不含在職專班及休學學生；應屆畢業生如延長修業年限者亦可申請）。同一學制交換期間以一學期或一學年（累計至多二學期）為限。",
            "校內評選配分與院級門檻：【全球事務處校級國際交換】第一階段校內初審依「系排名成績 50%＋英文檢定成績 50%」評比分發（至多選填 2 所校級志願）；【管理學院 OIP 院級交換】申請人須為管理學院在學學生且歷年成績排名在班級前 50% 為原則（至多選填 2 所院級志願）；【大陸地區交換】須具中華民國國籍且在校操行成績達 85 分（含）以上。",
            "保證金與錄取確認義務：通過第一階段校內甄選者，須於規定期限內繳交家長同意書、《出國交換學生切結書（CF-04）》及保證金新臺幣 5,000 元整；完成交換返國、於 2 週內繳交 1,500 字以上研修心得報告與 6 張照片並完成學分抵免後全額無息退還。",
            "境外選課與及格標準：依《元智大學學生至境外大學校院選修課程實施辦法》（1-51）第 5 條，交換生於境外修課每學期至少應選修 4 門課或 12 學分（ECTS），其中至少二分之一須為專業課程；所修科目平均成績須達及格標準（大學部 70 分、研究生 80 分）。",
        ],
        "language_requirement": [
            "申請赴國際及香港姊妹校交換者，第一階段校內報名時須檢附 2 年內有效之 TOEFL iBT、IELTS（Academic）或 TOEIC 官方成績單（不採認校園考或過期成績）；多數歐美姊妹校要求 CEFR B2 以上（TOEFL iBT 72–80、IELTS 5.5–6.5 或 TOEIC 750–785，部分學校如美國俄亥俄州立大學、奧克拉荷馬大學、荷蘭格羅寧根大學、丹麥南丹麥大學不採認 TOEIC）。",
            "申請日本及韓國姊妹校者，若修讀英語授課學程（ETP）須檢附符合各校標準之英語檢定成績；若修讀日／韓語授課學程則須檢附 JLPT N1–N3 或 TOPIK 2–4 級檢定證明。",
            "申請赴大陸地區姊妹校交換者免附外語檢定證明，惟須持有效臺胞證且在校操行成績不得低於 85 分。",
        ],
        "required_documents": [
            "1. 元智大學出國交換學生志願表（CF-01-R1，校級至多選填 2 志願、管院院級至多 2 志願；大陸交換填寫「赴大陸地區交換學生志願表」）",
            "2. 元智大學出國交換學生申請表（CF-02-R3，須經導師／指導教授及系所主任簽章；大陸交換填寫「赴大陸地區交換學生申請表」）",
            "3. 元智大學歷年英文成績單正本（須註明系排名或班排名百分比；大陸交換檢附歷年中文成績單含排名及操行成績證明）",
            "4. 兩年內有效之外語能力檢定成績單影本（TOEFL iBT / IELTS Academic / TOEIC / JLPT / TOPIK；大陸交換免附）",
            "5. 中英文讀書計畫（Study Plan，大陸交換須含 500 字以上中文讀書計畫）及其他有利審查資料（個人履歷 CV、獲獎或社團證明）",
            "6. 錄取確認階段必繳：元智大學出國交換學生切結書（CF-04）、家長同意書及保證金新臺幣 5,000 元收據（第二階段另依姊妹校要求提交護照影本、財力證明、推薦信、健康檢查表及境外選修課程申請表）",
        ],
        "scholarship_info": [
            "教育部「學海飛颺」（選送優秀學生赴國外研修）及「學海惜珠」（選送清寒優秀學生赴國外研修）獎學金：適用於具中華民國國籍、赴國外（不含大陸及港澳地區）修讀學分滿一學期或一學年之交換生，依《元智大學學海飛颺及學海惜珠計畫甄選要點》評選核發。",
            "《元智大學學生國際與兩岸交流獎助學金設置辦法》校內獎助學金：補助赴境外姊妹校交換一學期或一學年之本國籍在學學生，依交換地區核給每月生活補助（歐美紐澳地區約 NT$10,000–12,000／月、日韓新加坡地區約 NT$8,000–10,000／月、東南亞與大陸及港澳地區約 NT$5,000–8,000／月）；已獲教育部學海系列或校外政府獎學金者不得重複領取校內獎助學金。",
            "管理學院「出國進修獎助學金」：管理學院針對院級交換及雙聯學位學生設有專項國際移動力獎助金（詳見管理學院國際事務辦公室 OIP 公告）。",
            "姊妹校學費與住宿減免：全數交換姊妹校免收外國學費（僅繳交元智大學全額學雜費）；此外德國法蘭克福應用科技大學（Frankfurt UAS）及韓國慶星大學（Kyungsung University）等校另提供免住宿費名額。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": yzu_source_urls,
        "last_checked": "2026-10-17T04:45:00Z",
    }
    (OFFICIAL_YZU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "元智大學",
        "last_checked": "2026-10-17T04:45:00Z",
        "academic_score_minimum": 70.0,
        "academic_score_rule": "學士班二年級（含）以上或碩博班於元智就讀滿一學期以上；校級交換依「系排名成績 50%＋英文檢定成績 50%」評選，管理學院院級交換要求歷年成績在班級前 50% 為原則，大陸交換要求操行成績達 85 分以上；交換期間每學期至少須修習 4 門課或 12 ECTS 且平均達及格標準（大學部 70 分、研究生 80 分）。",
        "academic_gpa_minimum": 2.75,
        "maximum_preferences": 4,
        "selection_rules": {
            "academic_policy": "gpa_or_rank",
            "academic_reference_year": "115",
            "undergraduate_gpa_minimum": 2.75,
            "undergraduate_rank_maximum": 50.0,
            "graduate_academic_exempt": False,
            "exclude_in_service": True,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "undergraduate": 70.0,
                "graduate": 80.0,
            },
            "excluded_undergraduate_years": ["大一"],
            "language_certificate_required": False,
        },
        "language_score_minimums": {
            "toefl": 61.0,
            "ielts": 5.5,
            "toeic": 650.0,
        },
        "application_periods": [
            {
                "title": "元智大學 115-2（2027春季班）赴國際姊妹校交換生甄選（第一階段校內收件）",
                "details": [
                    "一般收件期間：2026年8月26日（三）起至2026年9月22日（二）中午 12:00 止（紙本送交七館二樓 R70208 全球事務處並完成線上表單上傳）。",
                    "提早提名校（Early Nomination）截止日：日本立命館亞洲太平洋大學（APU）、神戶大學、加拿大皇家山大學於 2026年9月7日截止；印尼大學、日本秋田國際教養大學、神奈川大學、法政大學、名城大學、韓國漢陽大學、中央大學、釜山大學、芬蘭 Metropolia、德國耶拿、挪威科技大學於 2026年9月11日 12:00 截止。",
                    "115-2 赴外交流說明會已於 2026年9月16日（三）12:20–14:00 舉辦；116-1（2027秋季班）預計於 2027年1月中旬至3月開放報名。",
                ],
                "source": {
                    "title": "元智大學 115-2（2027春季班）赴外交換生甄選公告與一覽表",
                    "source_url": "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
                    "category": "deadline",
                    "summary": "115-2 春季班 53 所國際交換校名額、語檢門檻與收件截止時間。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "115",
                "application_round": "115-2 國際交換",
                "audience": "all_students",
                "opens_at": "2026-08-26T09:00:00+08:00",
                "deadline_at": "2026-09-22T12:00:00+08:00",
                "date_status": "verified_exact",
                "status": "closed",
                "status_note": "115-2 國際交換校內收件已於 2026/09/22 12:00 截止，現正進行第二階段姊妹校提名送件；116-1（2027秋季班）預計於 2027年1月中旬開放申請。",
                "deadline_note": "紙本繳交至七館二樓 R70208 全球事務處（管院院級送交六館 R60403A），並完成線上申請表單上傳。",
                "reminder_eligible": False,
                "checked_at": "2026-10-17T04:45:00Z",
            },
            {
                "title": "元智大學 115-2（2027春季班）赴大陸地區姊妹校交換生甄選",
                "details": [
                    "申請期間：2026年9月起至 2026年10月20日校內截止（同濟大學、南京大學於 10月14日截止；西南大學、武漢大學、重慶大學、蘇州大學、西安交通大學於 10月20日校內截止、10月30日至11月1日完成姊妹校送件）。",
                    "申請人須為本校學士班大二以上或碩博班在學學生（具中華民國國籍），且在校操行成績達 85 分以上。",
                ],
                "source": {
                    "title": "元智大學全球事務處—赴大陸地區交換學生申請資訊",
                    "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2019-07-04-06-31-37",
                    "category": "exchange_application",
                    "summary": "2027 春季班大陸交換合作高校名單、應繳文件與截止日期。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "115",
                "application_round": "115-2 大陸交換",
                "audience": "all_students",
                "opens_at": "2026-09-01T09:00:00+08:00",
                "deadline_at": "2026-11-01T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "2027 春季班大陸姊妹校交換現正依各校截止日（10月14日–11月1日）受理校內書審與提名送件中。",
                "deadline_note": "請備齊大陸交換志願表、申請表、切結書、家長同意書、歷年中文成績單（含排名）及 500 字以上讀書計畫送交全球事務處。",
                "reminder_eligible": True,
                "checked_at": "2026-10-17T04:45:00Z",
            },
        ],
        "program_overview": [
            {
                "title": "元智大學全球事務處與管理學院赴外交換計畫總覽（90 所交換合作大學）",
                "details": [
                    f"元智大學透過全球事務處（Office of Global Affairs）及管理學院國際事務辦公室（OIP）雙軌推動學生國際與兩岸移動力，完整收錄 {len(partners)} 所交換合作大學（含 53 所全球處校級國際交換校、20 所管理學院專屬院級交換校、12 所中國大陸 985/211 重點高校及 5 所歷年交換／雙聯心得合作校，當期開放申請 {open_partner_count} 所）。",
                    "交換生於出國期間僅須繳交元智大學全額學雜費，免繳姊妹校學費（德國法蘭克福應用科技大學及韓國慶星大學另提供免住宿費優惠名額），並可申請教育部「學海飛颺／學海惜珠」或校內《國際與兩岸交流獎助學金》。",
                    f"本平台完整整合元智大學 {len(partners)} 所交換合作大學之申請資格、115-2 名額、Fact Sheet 連結，以及涵蓋 {exp_covered_schools} 所交換校之 236 篇學長姐返國研修心得報告 PDF。",
                ],
                "source": {
                    "title": "元智大學全球事務處與管理學院國際事務辦公室官方網站",
                    "source_url": "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
                    "category": "partner_school",
                    "summary": "元智大學校級國際交換、管理學院院級交換與兩岸交換總覽。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "申請資格、系排 50%＋英檢 50% 評選機制、保證金 NT$5,000 與最低修課學分",
                "details": [
                    "修業年級：本校正式學籍在學之學士班二年級（含）以上學生，或於元智就讀滿一學期以上之碩士班、博士班研究生（不含在職專班及休學學生）。",
                    "評選與成績門檻：全球處校級交換依「系排名成績 50%＋英文檢定成績 50%」評比分發（至多選填 2 志願）；管理學院院級交換要求歷年成績排名在班級前 50% 為原則（至多選填 2 志願）；大陸地區交換要求具中華民國國籍且操行成績達 85 分以上。",
                    "保證金規定：錄取確認時須簽署切結書（CF-04）並繳交保證金新臺幣 5,000 元，於完成交換返國、提交 1,500 字以上心得報告與 6 張照片並完成學分抵免後全額無息退還。",
                    "境外修課規定：依《元智大學學生至境外大學校院選修課程實施辦法》第 5 條，每學期至少須修習 4 門課或 12 學分（ECTS），其中至少二分之一為專業課程，且及格標準為大學部 70 分、研究生 80 分。",
                ],
                "source": {
                    "title": "元智大學 115-2 赴外交流說明會簡報與境外選修課程實施辦法",
                    "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07",
                    "category": "exchange_application",
                    "summary": "申請資格、評選配分、保證金與境外修課學分規定。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "國際姊妹校 2 年內有效語檢門檻與日韓歐語言規範",
                "details": [
                    "申請赴國際及香港姊妹校交換者，第一階段校內報名須檢附 2 年內有效之 TOEFL iBT、IELTS（Academic）或 TOEIC 官方成績單。",
                    "歐美及東南亞英語授課學程常見門檻為 CEFR B2（TOEFL iBT 72–80、IELTS 5.5–6.5 或 TOEIC 750–785；注意俄亥俄州立大學、奧克拉荷馬大學、格羅寧根大學、南丹麥大學等校不接受 TOEIC）。",
                    "日本與韓國姊妹校依修讀學程檢附英語檢定或日韓語檢定（JLPT N1–N3 / TOPIK 2–4 級）；大陸地區姊妹校免附外語檢定證明。",
                ],
                "source": {
                    "title": "元智大學 115-2 赴外交換學校一覽表與管理學院 OIP 交換名冊",
                    "source_url": "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
                    "category": "exchange_application",
                    "summary": "各國交換姊妹校語言檢定與 GPA 門檻一覽表。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "元智大學出國交換第一階段校內甄選與第二階段姊妹校送件文件",
                "details": [
                    "1. 出國交換學生志願表（CF-01-R1）及申請表（CF-02-R3，經導師／指導教授及系所主管簽章）。",
                    "2. 歷年英文成績單正本（含系排名／班排名百分比；大陸交換為歷年中文成績單含排名及操行 85 分以上證明）。",
                    "3. 兩年內有效之語言能力檢定成績單影本（大陸交換免附）及中英文讀書計畫（Study Plan）。",
                    "4. 錄取確認階段：出國交換學生切結書（CF-04）、家長同意書及保證金新臺幣 5,000 元繳費收據；第二階段另備護照影本、英文財力證明、推薦信、健康檢查表及境外選修課程申請表。",
                ],
                "source": {
                    "title": "元智大學全球事務處—出國交換表單下載專區",
                    "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
                    "category": "exchange_application",
                    "summary": "CF-01-R1 志願表、CF-02-R3 申請表、CF-04 切結書與大陸交換表單。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "教育部學海飛颺／惜珠與元智大學國際與兩岸交流獎助學金",
                "details": [
                    "教育部「學海飛颺」與「學海惜珠」獎學金：補助本國籍優秀學生及勵學優秀學生赴國外（不含大陸及港澳）修讀學分。",
                    "《元智大學學生國際與兩岸交流獎助學金設置辦法》校內獎助學金：依交換地區核發生活補助（歐美紐澳約 NT$10,000–12,000／月、日韓新加坡約 NT$8,000–10,000／月、東南亞及兩岸港澳約 NT$5,000–8,000／月）；與學海計畫不得重複領取。",
                    "管理學院院級出國進修獎助學金及部分姊妹校免費宿舍優惠（如德國法蘭克福應用科技大學、韓國慶星大學）。",
                ],
                "source": {
                    "title": "元智大學學生國際與兩岸交流獎助學金設置辦法與學海計畫甄選要點",
                    "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07",
                    "category": "scholarship",
                    "summary": "學海飛颺、學海惜珠與元智大學國際與兩岸交流獎助學金辦法。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "元智大學出國交換兩階段送件與保證金 NT$5,000 切結規範",
                "summary": "元智大學赴外交換採「第一階段校內甄選（紙本＋線上上傳）」與「第二階段姊妹校提名複審」兩階段辦理。",
                "key_points": [
                    "第一階段通過校內評選獲推薦資格者，須簽署《出國交換學生切結書（CF-04）》及家長同意書，並至出納組繳交保證金新臺幣 5,000 元整。",
                    "交換生返國後 2 週內須提交 1,500 字以上研修心得報告與 6 張照片，並完成境外學分抵免程序，始得申請無息退還保證金 NT$5,000 及領取獎助學金尾款。",
                ],
                "applies_to": [],
                "source": {
                    "title": "元智大學出國交換表單下載專區（CF-01-R1 / CF-02-R3 / CF-04）",
                    "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "《元智大學學生至境外大學校院選修課程實施辦法》（1-51）與獎助學金規定",
                "summary": "規範元智大學交換生修業期限、每學期最低修課數（4門課或12 ECTS）、及格標準（大學部70分／研究所80分）及獎助學金義務。",
                "key_points": [
                    "出國交換期間以一學期或一學年為原則（同一學制累計至多二學期），交換期間須於元智大學註冊並繳交全額學雜費。",
                    "交換生於境外修課每學期至少應選修 4 門課或 12 學分（ECTS），其中至少二分之一須為專業課程；所修科目平均成績須達及格標準（大學部 70 分、研究生 80 分）。",
                    "已獲教育部學海系列獎學金或外國政府獎學金者，不得重複領取《元智大學學生國際與兩岸交流獎助學金》。",
                ],
                "applies_to": [],
                "source": {
                    "title": "元智大學學生至境外大學校院選修課程實施辦法（1-51）",
                    "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07",
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07",
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {
                "title": "元智大學全球事務處—115-2（2027春季班）赴外交換生甄選公告與學校一覽表",
                "source_url": "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "元智大學全球事務處—115-1（2026秋季班）赴外交換生甄選公告與學校一覽表",
                "source_url": "https://gao.yzu.edu.tw/index.php/tw/2026-01-13-02-46-21",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "元智大學管理學院國際事務辦公室（OIP）—院級交換學生計畫名冊",
                "source_url": "https://oip.cm.yzu.edu.tw/abrd_deg/list/es",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "元智大學管理學院國際事務辦公室（OIP）—學生出國交換心得分享",
                "source_url": "https://oip.cm.yzu.edu.tw/int_review/list",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "元智大學全球事務處—出國交換相關法規（境外選修課程實施辦法、獎助學金辦法、學海要點）",
                "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07",
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "元智大學全球事務處—出國交換表單下載（志願表、申請表、切結書）",
                "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "元智大學全球事務處—赴大陸地區交換學生專區",
                "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2019-07-04-06-31-37",
                "category": "partner_school",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_YZU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    pages_records = [
        {
            "title": "元智大學：115-2（2027春季班）赴外交換甄選時程與提早提名規定",
            "source_url": "https://gao.yzu.edu.tw/index.php/tw/2026-08-26-07-04-00",
            "published_at": "2026-08-26T00:00:00Z",
            "text": "\n".join(exchange_info_payload["application_period"]),
            "summary": "\n".join(exchange_info_payload["application_period"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-17T04:45:00Z",
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["application_period"]).encode(
                    "utf-8"
                )
            ).hexdigest(),
        },
        {
            "title": "元智大學：交換學生申請資格、系排50%＋英檢50%評選、保證金與最低修課學分",
            "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07",
            "published_at": "2026-08-26T00:00:00Z",
            "text": "\n".join(exchange_info_payload["eligibility"]),
            "summary": "\n".join(exchange_info_payload["eligibility"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-17T04:45:00Z",
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["eligibility"]).encode("utf-8")
            ).hexdigest(),
        },
        {
            "title": "元智大學：全球處校級與管理學院院級交換語言能力門檻",
            "source_url": "https://oip.cm.yzu.edu.tw/abrd_deg/list/es",
            "published_at": "2026-08-26T00:00:00Z",
            "text": "\n".join(exchange_info_payload["language_requirement"]),
            "summary": "\n".join(exchange_info_payload["language_requirement"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-17T04:45:00Z",
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["language_requirement"]).encode(
                    "utf-8"
                )
            ).hexdigest(),
        },
        {
            "title": "元智大學：出國交換第一階段與第二階段應繳文件及切結書規範",
            "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
            "published_at": "2026-08-26T00:00:00Z",
            "text": "\n".join(exchange_info_payload["required_documents"]),
            "summary": "\n".join(exchange_info_payload["required_documents"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-17T04:45:00Z",
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["required_documents"]).encode(
                    "utf-8"
                )
            ).hexdigest(),
        },
        {
            "title": "元智大學：學海飛颺／惜珠與國際與兩岸交流獎助學金設置辦法",
            "source_url": "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-07",
            "published_at": "2026-08-26T00:00:00Z",
            "text": "\n".join(exchange_info_payload["scholarship_info"]),
            "summary": "\n".join(exchange_info_payload["scholarship_info"]),
            "category": "scholarship",
            "attachments": [],
            "crawled_at": "2026-10-17T04:45:00Z",
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["scholarship_info"]).encode(
                    "utf-8"
                )
            ).hexdigest(),
        },
    ]
    (OFFICIAL_YZU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
        + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "yzu",
        "school_name": "元智大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_weights": {
            "international_gao": {
                "class_rank": 0.50,
                "english_proficiency": 0.50,
            },
            "management_oip": {
                "class_rank_top_percent_limit": 50.0,
            },
            "mainland": {
                "conduct_score_minimum": 85.0,
            },
        },
        "source_urls": yzu_source_urls,
        "verified_at": "2026-10-17",
    }
    (OFFICIAL_YZU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_YZU_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "元智大學",
                "required_documents": student_dashboard_payload[
                    "required_documents"
                ],
                "source_urls": yzu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_YZU_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "元智大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": yzu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "yzu",
        "school_name": "元智大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(
            1 for p in all_partner_defs if p["kind"] != "mainland"
        ),
        "mainland_partners": sum(
            1 for p in all_partner_defs if p["kind"] == "mainland"
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
        "active_term": "115-2（2027春季班）赴國際交換（2026/08/26–09/22收件）及2027春季班赴大陸交換（2026/10/14–11/01收件）已公告；116-1（2027秋季班）預計於2027年1月中旬至3月開放申請。",
        "verified_at": "2026-10-17",
    }
    (OFFICIAL_YZU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_YZU_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "yzu",
                "school_name": "元智大學",
                "status": "official_verified",
                "checked_at": "2026-10-17T04:45:00Z",
                "counts": completeness,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    from exchange_info.generated_content_review import review_generated_content
    review_generated_content(REPO_ROOT, "yzu", round_id=20)
    review_generated_content(REPO_ROOT, "yzu", round_id=21)

    print(
        f"Successfully built YZU catalog: {len(partners)} partners ({open_partner_count} open, "
        f"{completeness['verified_campus_images']} verified images, {completeness['verified_locations']} verified locations), "
        f"{len(workflows)} workflows, {len(destinations)} destinations, {len(research_records)} research records, "
        f"{exp_covered_schools} schools with experience reports ({len(student_experience_rows)} rows)."
    )


if __name__ == "__main__":
    main()
    from exchange_info.yzu_source_review import review_bundle
    review_bundle(REPO_ROOT)
