from __future__ import annotations

import hashlib
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from .content_summary import fetch_page_content, summarize_student_link
from .life_sources import read_life_page
from .models import (
    ExperienceHighlight,
    ExperienceInsight,
    ExperienceSourceType,
    PartnerUniversity,
    StudentExperienceDigest,
    StudentExperienceSource,
)
from .school_identity import school_identity_key
from .web_search import search_text, search_videos


COUNTRY_SEARCH_NAMES = {
    "大陸地區": "China",
    "日本": "Japan",
    "比利時": "Belgium",
    "匈牙利": "Hungary",
    "印度": "India",
    "西班牙": "Spain",
    "法國": "France",
    "波蘭": "Poland",
    "美國": "United States",
    "挪威": "Norway",
    "泰國": "Thailand",
    "紐西蘭": "New Zealand",
    "馬來西亞": "Malaysia",
    "捷克": "Czech Republic",
    "越南": "Vietnam",
    "新加坡": "Singapore",
    "瑞典": "Sweden",
    "義大利": "Italy",
    "德國": "Germany",
    "澳洲": "Australia",
    "韓國": "South Korea",
}

SCHOOL_SEARCH_ALIASES = {
    "先皇技術學院": "King Mongkut's Institute of Technology Ladkrabang KMITL",
    "法政大學": "Thammasat University Thailand",
    "蒙庫國王科技大學": "King Mongkut's University of Technology Thonburi KMUTT",
    "宋卡王子大學": "Prince of Songkla University PSU",
    "國民經濟大學": "National Economics University Vietnam",
    "鵅鴻大學": "Lac Hong University",
    "越南河內國家大學": "Vietnam National University Hanoi",
    "越南胡志明市國際大學": "International University VNU HCMC",
    "越南文朗大學": "Van Lang University",
    "越南胡志明市經濟與法律大學": "University of Economics and Law VNU HCMC",
    "國立胡志明市經濟大學": "UEH International School of Business",
    "越南德國大學": "Vietnamese-German University",
    "亞當密茲坎維奇大學": "Adam Mickiewicz University",
    "科茲明斯基大學": "Kozminski University",
    "波茲南經濟與商業大學": "Poznań University of Economics and Business",
    "波茲南科技大學": "Poznań University of Technology",
    "華沙生命科學大學": "Warsaw University of Life Sciences",
    "弗羅茨瓦夫大學": "University of Wrocław",
    "克拉科夫經濟大學": "Krakow University of Economics",
    "亞捷隆大學語言文學院": "Jagiellonian University Faculty of Philology",
    "諾歐商學院": "NEOMA Business School",
    "特魯瓦工程技術大學": "Université de Technologie de Troyes",
    "巴黎計算機電子工程師學院": "Efrei",
    "拉羅歇爾高等商學院": "Excelia Business School",
    "雷恩商學院": "Rennes School of Business",
    "法國巴黎高等對外貿易學院": "ESCE International Business School",
    "昂傑高等商學院": "ESSCA School of Management",
    "歐洲知識經濟與管理學院": "SKEMA Business School",
    "達芬奇大學": "Pôle Léonard de Vinci",
    "諾曼第管理學院": "EM Normandie Business School",
    "北方高等商學院": "EDHEC Business School",
    "TBS圖魯斯商學院": "TBS Education",
    "巴黎經濟商業管理高等商學院": "EDC Paris Business School",
    "圖魯斯第一大學": "Toulouse Capitole University",
    "法國計算機及創新技術學院": "EPITECH",
    "法國普羅旺斯艾克斯政治大學": "Sciences Po Aix",
    "法國圖盧茲政治學院": "Sciences Po Toulouse",
    "Kedge商學院": "KEDGE Business School",
    "里爾大學": "Université de Lille",
    "上海立信會計 金融學院": "Shanghai Lixin University of Accounting and Finance",
    "上海財經大學": "Shanghai University of Finance and Economics",
    "天津大學": "Tianjin University",
    "華東師範大學": "East China Normal University",
    "南開大學": "Nankai University",
    "中國人民大學": "Renmin University of China",
    "中國政法大學": "China University of Political Science and Law",
    "北京體育大學": "Beijing Sport University",
    "西南大學": "Southwest University",
    "山東師範大學": "Shandong Normal University",
    "東北林業大學": "Northeast Forestry University",
    "武漢大學": "Wuhan University",
    "華中農業大學": "Huazhong Agricultural University",
    "吉林大學": "Jilin University",
    "四川大學": "Sichuan University",
    "南京大學": "Nanjing University",
    "西北政法大學": "Northwest University of Political Science and Law",
    "西安交通大學": "Xi'an Jiaotong University",
    "廈門大學": "Xiamen University",
    "山東大學": "Shandong University",
    "中央財經大學": "Central University of Finance and Economics",
    "北京科技大學": "University of Science and Technology Beijing",
    "西南政法大學": "Southwest University of Political Science and Law",
    "東華理工大學": "East China University of Technology",
    "華東政法大學": "East China University of Political Science and Law",
    "暨南大學": "Jinan University",
    "蘭州大學": "Lanzhou University",
    "大阪大學法學研究科、法學部、大學院高等司法研究科暨大學院國際公共政策研究科": "Osaka University School of Law Graduate School of Law and Politics Osaka School of International Public Policy",
    "日本信州大學經法學部": "Shinshu University Faculty of Economics and Law",
    "東北大學": "Tohoku University",
    "金澤大學": "Kanazawa University",
    "梨花女子大學": "Ewha Womans University",
    "高麗大學世宗校區": "Korea University Sejong Campus",
    "越南融促大學": "FPT University",
    "芹苴大學－經濟學院": "Can Tho University School of Economics",
    "泰國東方大學": "Burapha University",
    "泰國清邁大學": "Chiang Mai University",
    "印度吉特卡拉大學": "Chitkara University",
    "印度阿努拉格大學": "Anurag University",
    "卡倫亞技術與科學研究所": "Karunya Institute of Technology and Sciences",
    "印尼迪安努斯萬托羅大學": "Universitas Dian Nuswantoro",
    "黎剎系統大學": "University of Rizal System",
    "百麗宮國際大學": "Paragon International University",
    "香港理工大學": "The Hong Kong Polytechnic University",
    "俄斯特拉發大學": "University of Ostrava",
    "北愛荷華大學": "University of Northern Iowa",
    "密蘇里大學藝術與科學學院": "University of Missouri College of Arts and Science",
    "新墨西哥州立大學": "New Mexico State University",
    "勞倫森大學": "Laurentian University",
    "加拿大多倫多都會大學": "Toronto Metropolitan University",
    "英屬哥倫比亞大學": "The University of British Columbia",
    "高等廣告與行銷學院": "ESPM School of Advertising and Marketing",
    "奧維第烏斯大學": "Ovidius University of Constanta",
    "蒂米什拉西部大學": "West University of Timisoara",
    "立陶宛維塔斯．馬格努斯大學": "Vytautas Magnus University",
    "格但斯克科技大學": "Gdansk University of Technology",
    "明斯特大學": "University of Münster",
    "霍夫應用科技大學": "Hof University of Applied Sciences",
    "女性高等綜合理工學院": "EPF Graduate School of Engineering",
    "里爾政治大學": "Sciences Po Lille",
    "奧斯陸大學（犯罪學與社會學法系）": "University of Oslo Department of Criminology and Sociology of Law",
    "阿提巴斯大學": "Altinbas University",
    "埃斯基謝希爾技術大學": "Eskisehir Technical University",
    "拉脫維亞大學": "University of Latvia",
    "布拉提斯拉瓦斯洛伐克工業大學": "Slovak University of Technology in Bratislava",
    "卡薩布蘭卡管理學院": "ESCA School of Management",
    "埃斯特哈茲天主教大學": "Eszterhazy Karoly Catholic University",
}

THEME_LABELS = {
    "academics": "課業與教學",
    "campus_culture": "校園風氣",
    "housing": "住宿",
    "cost": "生活成本",
    "food": "飲食與採買",
    "transport": "交通與地點",
    "climate": "氣候與穿著",
    "travel": "旅行與周邊城市",
    "safety": "安全與醫療",
    "social": "社交與社團",
    "support": "國際生支援",
    "career": "實作與職涯",
    "challenges": "可能的挑戰",
}

THEME_PATTERNS = {
    "academics": r"course|class|teaching|professor|workload|exam|academic|study|課程|課堂|課業|教學|教授|老師|作業|簡報|考試|學分",
    "campus_culture": r"campus|atmosphere|community|friendly|welcom|close[- ]knit|small university|校園|風氣|友善|融入",
    "housing": r"dorm|hall|accommodation|housing|flat|roommate|住宿|宿舍|租屋",
    "cost": r"cost|expensive|budget|rent|grocery|food price|生活費|費用|昂貴|預算",
    "food": r"food|meal|restaurant|cafeteria|grocery|supermarket|cook|飲食|餐廳|食堂|超市|煮飯",
    "transport": r"bus|transport|commute|bike|metro|subway|taxi|walk|city cent|distance|交通|公車|通勤|市區|市中心|地鐵|計程車|步行|路程|距離",
    "climate": r"weather|climate|winter|summer|rain|snow|cold|hot|氣候|天氣|冬天|夏天|下雨|下雪|寒冷|炎熱|穿著",
    "travel": r"travel|trip|weekend|nearby|flight|train|周邊|旅行|旅遊|週末|機場|火車",
    "safety": r"safe|safety|crime|emergency|doctor|hospital|health|安全|治安|緊急|醫院|醫療",
    "social": r"\bfriends?\b|club|societ|committee|party|nightlife|social|社團|朋友|社交|夜生活",
    "support": r"support|orientation|international office|doctor|health|insurance|國際處|支援|保險|醫療",
    "career": r"practical|hands[- ]on|industry|internship|career|job|實作|產業|實習|就業",
    "challenges": r"challenge|difficult|homesick|isolat|rural|quiet|lonely|agricultur|farm|land-based|limited|stress|poor|bad|困難|偏遠|安靜|孤單|不便|農業|有限|壓力|不佳|昂貴|自求多福",
}

# Public exchange reports are not limited to Chinese or English authors.
for _theme, _terms in {
    "housing": r"wohnheim|unterkunft|logement|résidence|기숙사|寮|住居",
    "cost": r"lebenshaltungskosten|miete|coût|loyer|생활비|物価|生活費",
    "food": r"mensa|lebensmittel|nourriture|repas|식당|음식|食事|学食|スーパー",
    "transport": r"verkehr|bahnhof|transports|교통|통학|通学|最寄り",
    "academics": r"vorlesung|prüfung|enseignement|수업|강의|授業|履修",
    "climate": r"wetter|hiver|날씨|気候|天候",
    "social": r"freundschaften|amis|동아리|친구|サークル|友達",
    "safety": r"krankenhaus|krankenversicherung|hôpital|médecin|병원|보험|診療所|病院|保険",
    "campus_culture": r"kulturschock|culturel|문화|異文化|文化交流",
    "travel": r"ausflug|voyage|여행|旅行",
}.items():
    THEME_PATTERNS[_theme] += "|" + _terms

THEME_DIGEST_SUMMARIES = {
    "academics": "來源談到課程內容、學習方式或課業安排；不同科系的實際感受可能差很多。",
    "campus_culture": "來源談到校園規模、整體氛圍與學生互動；應比較不同年份和學生身分。",
    "housing": "來源談到宿舍、租屋或室友經驗；房型、費用與距離仍需另外核對。",
    "cost": "來源談到房租、飲食或日常預算；實際花費會受住宿方式與匯率影響。",
    "food": "來源談到外食、校園餐飲、超市或自己煮飯；價格與選擇會因地點和飲食習慣不同。",
    "transport": "來源談到市區距離、通勤或交通工具；應先查班次與夜間移動方式。",
    "climate": "來源談到當地季節、氣候與穿著；出發月份不同，準備內容也會不同。",
    "travel": "來源談到週末旅行、機場或周邊城市；實際便利性仍受交通班次與預算影響。",
    "safety": "來源談到安全、夜間移動、就醫或緊急支援；應再核對官方旅遊與校方安全資訊。",
    "social": "來源談到交友、社團或社交生活；個人喜好與參與程度會影響感受。",
    "support": "來源談到國際生服務、醫療、保險或新生支援；出發前應逐項確認。",
    "career": "來源談到實作、產業連結、實習或職涯資源；不同學程提供的機會可能不同。",
    "challenges": "來源談到環境較安靜、地點、適應或其他挑戰；這些面向特別需要交叉比較。",
}

GENERIC_EXPERIENCE_SUMMARY_PATTERN = re.compile(
    r"^(?:這個來源主要談到|這個公開來源|\d+\s*個來源提到這個面向|來源談到)"
)
BLOCKED_OR_INTERSTITIAL_PATTERN = re.compile(
    r"just a moment|verification successful|connect with wechat|sign in with account|"
    r"dcard.{0,40}(?:驗證|連線安全)|請稍候.{0,30}驗證|操作的頻率過快|"
    r"vpn\s*(?:or|/)?\s*proxy|網路曾經有異常行為",
    re.IGNORECASE,
)
NAVIGATION_ONLY_PATTERNS = (
    re.compile(r"find a program.+program lists", re.IGNORECASE),
    re.compile(r"about us.+about cucas.+contact us", re.IGNORECASE),
    re.compile(r"university application.+accommodation booking.+airport pick-up", re.IGNORECASE),
    re.compile(r"all job opportunities.+graduate jobs.+internships", re.IGNORECASE),
    re.compile(r"cv guides?.+leonardo grants", re.IGNORECASE),
    re.compile(r"international rankings?.+masters.+mbas", re.IGNORECASE),
)
SOURCE_CHROME_PATTERN = re.compile(
    r"life housing student activities dining|all job opportunities|publish job offers|"
    r"cv guides?|leonardo grants|program lists|about cucas",
    re.IGNORECASE,
)

SIGNAL_PATTERNS = [
    (
        "campus_culture",
        r"small (?:campus|university)|close[- ]knit|most people know|規模.{0,5}(?:小|不大)",
        "校園規模較小，人際互動可能比大型綜合大學更密切",
    ),
    (
        "campus_culture",
        r"welcom|friendly|feel at home|mateship|友善|歡迎|容易融入",
        "有學生提到校園氣氛友善，國際生較容易認識同學",
    ),
    (
        "challenges",
        r"rural|countryside|agricultur|farm|land-based|偏鄉|鄉村|農業",
        "校園或學校特色較偏鄉村與農業領域，喜歡都會生活者需要先評估",
    ),
    (
        "social",
        r"club|societ|committee|student association|社團|學生會",
        "學生常透過社團與學生組織認識同學並融入校園",
    ),
    (
        "transport",
        r"bus|transport|commute|city cent|christchurch|交通|公車|通勤|市區",
        "日常移動常涉及公車、通勤與市區往返，應先查好班次、距離與末班時間",
    ),
    (
        "housing",
        r"dorm|student hall|accommodation|housing|roommate|住宿|宿舍|租屋",
        "住宿選擇會影響交友、通勤與生活成本，建議另外核對宿舍條件",
    ),
    (
        "cost",
        r"expensive|living cost|budget|rent|grocery|生活費|房租|昂貴|預算",
        "行前預算需要分開估算房租、飲食與日常採買，住宿方式會明顯影響總支出",
    ),
    (
        "career",
        r"practical|hands[- ]on|industry|internship|career|實作|產業|實習",
        "部分學生經驗包含課程實作或產業連結，適合重視應用學習者進一步核對課程",
    ),
    (
        "support",
        r"international office|orientation|doctor|health|insurance|國際處|保險|醫療|新生說明",
        "國際生支援、醫療與保險資訊值得在出發前逐項確認",
    ),
    (
        "social",
        r"party|nightlife|social life|派對|夜生活|社交生活",
        "社交與夜生活的描述因年份和個人偏好差異較大，應交叉比較多個來源",
    ),
]

LEGACY_EXPERIENCE_INSIGHTS = {
    "社團與學生組織是來源中常見的交友與融入方式": "學生常透過社團與學生組織認識同學並融入校園",
    "往返市區與日常交通需要事先確認班次、距離和時間": "日常移動常涉及公車、通勤與市區往返，應先查好班次、距離與末班時間",
    "生活費、房租或日常採買是來源提到的行前預算重點": "行前預算需要分開估算房租、飲食與日常採買，住宿方式會明顯影響總支出",
    "有來源提到課程實作或產業連結，適合重視應用經驗的學生進一步了解": "部分學生經驗包含課程實作或產業連結，適合重視應用學習者進一步核對課程",
}

EXPERIENCE_TERMS = re.compile(
    r"student life|student experience|my experience|exchange|study abroad|review|blog|vlog|campus|housing|dorm|心得|留學|交換|校園|住宿|Erfahrungsbericht|Auslandssemester|témoignage|utveksling|교환학생|체험|交換留学|留学体験",
    re.IGNORECASE,
)

EXCLUDED_HOSTS = {
    "academgo.com",
    "academicjobs.com",
    "alluniversity.info",
    "amberstudent.com",
    "applyboard.com",
    "eduniversal-ranking.com",
    "educatly.com",
    "euroleague-study.org",
    "gostudyin.com",
    "glassdoor.com",
    "hotcoursesabroad.com",
    "idp.com",
    "inigoleigh.blogspot.com",
    "jubeerich.com",
    "studyspy.ac.nz",
    "slideshare.net",
    "simplyhired.com",
    "shiksha.com",
    "standyou.com",
    "studies-overseas.com",
    "studyqa.com",
    "studee.com",
    "nexties.com",
    "niche.com",
    "college-contact.com",
    "collegedunia.com",
    "princetonreview.com",
    "queenslanduniversity.au",
    "womenuniversities.org",
    "yocket.com",
    "tripadvisor.com",
    "tripadvisor.com.sg",
    "trykandor.com",
    "unipage.net",
    "unigo.com",
    "usnews.com",
    "wentchina.com",
    "wikipedia.org",
}

STRICT_IDENTITY_NAMES = {
    "city university of hong kong",
    "sorbonne universite",
    "university of minnesota go minnesota",
}

SCHOOL_IDENTITY_ALIASES = {
    "university of perugia": {
        "universita degli studi di perugia",
        "università degli studi di perugia",
    },
    "sorbonne universite": {
        "sorbonne university",
        "paris sorbonne university",
        "universite paris sorbonne",
    },
    "university of minnesota go minnesota": {
        "go minnesota",
        "university of minnesota twin cities",
    },
    "warsaw university of life sciences": {
        "sggw",
        "wuls sggw",
    },
}

SCHOOL_IDENTITY_EXCLUSIONS = {
    "sorbonne universite": {
        "new sorbonne university",
        "paris 3 new sorbonne",
        "sorbonne nouvelle",
        "pantheon sorbonne",
        "paris 1 pantheon sorbonne",
    },
    "warsaw university of technology": {
        "university of warsaw",
        "uniwersytet warszawski",
    },
    "wuhan university": {
        "wuhan university of science and technology",
    },
    "fuzhou university": {
        "fuzhou university of international studies",
        "fuzhou university of international studies and trade",
    },
    "university of ostrava": {
        "technical university of ostrava",
        "vsb technical university of ostrava",
    },
    "rennes school of business": {
        "ciee rennes",
        "rennes liberal arts",
    },
}

SEARCH_QUERY_ALIASES = {
    "Sorbonne Université": "Sorbonne University",
}

POSITIVE_EXPERIENCE_PATTERN = re.compile(
    r"friendly|welcom|convenient|helpful|close[- ]knit|easy to|good support|vibrant|"
    r"recommend|excellent|well[- ]organized|affordable|cheap|efficient|supportive|"
    r"worth it|happy with|fulfilling|friendship|broadened|友善|歡迎|方便|容易融入|"
    r"推薦|完善|便宜|實惠|效率|收穫|值得|互動.{0,20}密切|支援.{0,10}(?:好|完善)",
    re.IGNORECASE,
)

CHALLENGE_EXPERIENCE_PATTERN = re.compile(
    r"challenge|difficult|expensive|far|rural|quiet|lonely|limited|homesick|inconvenient|"
    r"stressful|cold in|trek|distraction|not very good|traffic|scooter|crowded|"
    r"困難|昂貴|偏遠|安靜|孤單|不便|壓力|寒冷|擁擠|有限|班次|距離|需要先評估|需要事先確認",
    re.IGNORECASE,
)

REVIEW_HOSTS = {
    "blogspot.com",
    "gooverseas.com",
    "iagora.com",
    "medium.com",
    "reddit.com",
    "studyabroad101.com",
    "substack.com",
    "tiktok.com",
    "wordpress.com",
    "youtube.com",
    "youtu.be",
}

STRONG_EXPERIENCE_TERMS = re.compile(
    r"\bmy\b|\bi\b|life at|why i chose|culture shock|students?.? voice|student story|testimonial|review|vlog|day in the life|hall tour|dorm tour|past review|year in|experience report|Erfahrungsbericht|témoignage|utveksling|교환학생|체험|留学体験|心得|感想|親身|經驗分享",
    re.IGNORECASE,
)

OFFICIAL_STUDENT_STORY_TERMS = re.compile(
    r"students?[-_/'’ ]*(?:voice|story|stories|experience|experiences|testimonial)"
    r"|alumni[-_/ ]?(?:voice|story|stories|experience)"
    r"|why[-_/ ]?i[-_/ ]?chose|day[-_/ ]?in[-_/ ]?the[-_/ ]?life"
    r"|reflections?[-_/ ]?of[-_/ ]?an?[-_/ ]?exchange[-_/ ]?student"
    r"|exchange[-_/ ]?(?:at|experience|reflection|story)"
    r"|交換.{0,6}(?:心得|故事|經驗)|留學.{0,6}(?:心得|故事|經驗)",
    re.IGNORECASE,
)

VIDEO_EXPERIENCE_TERMS = re.compile(
    r"student experience|student guide|campus tour|life is like|study abroad student|exchange student|vlog|day in the life|dorm|hall tour|culture shock|心得|留學生活|交換生活",
    re.IGNORECASE,
)

NON_EXPERIENCE_TITLE_TERMS = re.compile(
    r"joins? hands|strategic partnership|partnership agreement|partnership announcement"
    r"|signs? (?:an? )?(?:mou|memorandum|agreement)|memorandum of understanding"
    r"|establish(?:es|ed|ing)? (?:an? )?(?:academic )?(?:partnership|collaboration)"
    r"|new (?:academic )?(?:partnership|collaboration)|cooperation partner(?: details)?"
    r"|(?:student )?exchange (?:program|programme)\s+"
    r"(?:spring|fall|autumn|semester|20\d{2})"
    r"|\bacceptance rate\b|\badmissions? (?:chance|chances|odds|rate)\b",
    re.IGNORECASE,
)

MARKETING_CATALOG_TITLE_TERMS = re.compile(
    r"(?:courses?|programs?).{0,24}(?:fees?|rankings?).{0,36}(?:scholarships?)"
    r"|(?:fees?).{0,24}(?:rankings?).{0,36}(?:scholarships?)"
    r"|\bstudy in .{2,100}\|\s*admissions?(?: direct)?\b"
    r"|\btop rankings?, programs? &|tuition fees?\s*[–—|-]\s*unipage",
    re.IGNORECASE,
)

TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}


def school_search_name(school_name: str) -> str:
    for local_name, search_alias in SCHOOL_SEARCH_ALIASES.items():
        if school_name.startswith(local_name):
            return search_alias

    # NTPU's quota tables commonly format a school as
    # ``中文名 (Official English Name) + requirement notes``.  Prefer that
    # bounded English name over the first ASCII character in the whole cell;
    # the older fallback could return strings such as ``ESIC(ESIC University)``
    # or include TOEFL/IELTS notes in the search identity.
    parenthesized = re.findall(r"\(([^()]*)\)", school_name)
    english_names = [
        re.sub(r"\s+", " ", candidate).strip(" ,;:-")
        for candidate in parenthesized
        if len(re.findall(r"[A-Za-z]{2,}", candidate)) >= 2
        and re.search(
            r"\b(university|college|school|institute|academy|universit|hochschule)\b",
            candidate,
            flags=re.IGNORECASE,
        )
    ]
    if english_names:
        return max(english_names, key=len)

    for index, character in enumerate(school_name):
        if character.isascii() and character.isalpha():
            candidate = school_name[index:].strip()
            return re.sub(r"[\u3400-\u9fff]+", "", candidate).strip()
    return school_name.strip()


def build_experience_queries(partner: PartnerUniversity) -> list[tuple[str, str]]:
    school_name = school_search_name(partner.school_name)
    name = SEARCH_QUERY_ALIASES.get(school_name, school_name)
    country = COUNTRY_SEARCH_NAMES.get(partner.country or "", partner.country or "")
    country_part = f" {country}" if country else ""
    return [
        (f"{name}{country_part} reddit student life exchange", "text"),
        (f"{name}{country_part} study abroad student review", "text"),
        (f"{name}{country_part} exchange student blog", "text"),
        (f'"{name}" Erasmus exchange experience report filetype:pdf', "text"),
        (f'"{name}" Erfahrungsbericht témoignage 교환학생 留学体験', "text"),
        (f"{name}{country_part} youtube student life exchange", "text"),
        (f"{name}{country_part} life at university student review", "text"),
        (f'{name} {country} international student experience campus vlog'.strip(), "video"),
    ]


def collect_student_experiences(
    partner: PartnerUniversity,
    *,
    max_sources: int = 12,
    timeout_seconds: float = 20.0,
) -> list[StudentExperienceSource]:
    queries = build_experience_queries(partner)
    max_per_query = max(3, min(6, max_sources // 2 or 3))
    candidates: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=min(4, len(queries))) as executor:
        futures = {
            executor.submit(
                _search_ddgs,
                query,
                source_type,
                max_per_query,
                timeout_seconds,
            ): (query, source_type)
            for query, source_type in queries
        }
        for future in as_completed(futures):
            query, source_type = futures[future]
            try:
                for item in future.result():
                    item["query"] = query
                    item["search_type"] = source_type
                    candidates.append(item)
            except Exception:
                continue

    sources: list[StudentExperienceSource] = []
    seen_urls: set[str] = set()
    for candidate in candidates:
        source = _candidate_to_source(candidate, partner)
        if not source or source.source_url in seen_urls:
            continue
        source = _summarize_link_content(
            source,
            partner,
            timeout_seconds=timeout_seconds,
        )
        if source is None:
            continue
        seen_urls.add(source.source_url)
        sources.append(source)

    sources.sort(key=_source_sort_key)
    return _keep_source_diversity(sources, max_sources)


def merge_refreshed_student_experiences(
    partner: PartnerUniversity,
    previous_sources: list[StudentExperienceSource],
    discovered_sources: list[StudentExperienceSource],
    *,
    max_sources: int = 12,
) -> list[StudentExperienceSource]:
    school_key = normalize_school(partner.school_name)
    merged = {
        source.source_url: _clean_stored_source_title(source, partner)
        for source in previous_sources
        if normalize_school(source.school_name) == school_key
        and _stored_source_is_allowed(source, partner)
    }
    for source in discovered_sources:
        if _stored_source_is_allowed(source, partner):
            merged[source.source_url] = source
    ordered = sorted(merged.values(), key=_source_sort_key)
    return _keep_source_diversity(ordered, max_sources)


def _clean_stored_source_title(
    source: StudentExperienceSource,
    partner: PartnerUniversity,
) -> StudentExperienceSource:
    parsed = urlparse(source.source_url)
    host = parsed.netloc.casefold().removeprefix("www.")
    title = _clean_experience_title(source.title, host, parsed.path, partner)
    if title == source.title:
        return source
    return source.model_copy(update={"title": title})


def _stored_source_is_allowed(
    source: StudentExperienceSource,
    partner: PartnerUniversity,
) -> bool:
    # Admission and award lists are program evidence, not student testimony.
    if source.perspective == "official_program_record":
        return False
    if not _source_content_is_usable(source):
        return False
    parsed = urlparse(source.source_url)
    host = parsed.netloc.casefold().removeprefix("www.")
    if not host or any(
        host == item or host.endswith(f".{item}") for item in EXCLUDED_HOSTS
    ):
        return False
    if host == "studyabroad101.com" and parsed.path.casefold().startswith("/cities/"):
        return False
    if not _special_program_url_allowed(partner, host, parsed.path):
        return False
    identity_title = _stored_identity_title(source.title, partner)
    title_and_path = (
        f"{source.title} {parsed.path.replace('-', ' ').replace('_', ' ')}"
    )
    if NON_EXPERIENCE_TITLE_TERMS.search(title_and_path):
        return False
    if MARKETING_CATALOG_TITLE_TERMS.search(source.title):
        return False
    identity = f"{identity_title} {source.source_url}"
    country_name = COUNTRY_SEARCH_NAMES.get(source.country or "", source.country or "")
    context = f"{identity} {source.summary} {source.country or ''} {country_name}"
    return _is_relevant_to_partner(identity, context, partner)


def _source_content_is_usable(source: StudentExperienceSource) -> bool:
    """Reject challenge pages and navigation chrome before they become student claims."""
    if source.content_status == "unavailable":
        return False
    combined = " ".join(
        [
            source.title,
            source.summary,
            *source.theme_summaries.values(),
        ]
    )
    if BLOCKED_OR_INTERSTITIAL_PATTERN.search(combined):
        return False
    if SOURCE_CHROME_PATTERN.search(combined):
        return False
    if sum(bool(pattern.search(combined)) for pattern in NAVIGATION_ONLY_PATTERNS) >= 2:
        return False
    return True


def _search_ddgs(
    query: str,
    source_type: str,
    max_results: int,
    timeout_seconds: float,
) -> list[dict[str, Any]]:
    if source_type == "video":
        return search_videos(
            query,
            max_results=max_results,
            timeout_seconds=timeout_seconds,
        )
    return search_text(
        query,
        max_results=max_results,
        timeout_seconds=timeout_seconds,
    )


def _candidate_to_source(
    candidate: dict[str, Any], partner: PartnerUniversity
) -> StudentExperienceSource | None:
    is_video = candidate.get("search_type") == "video"
    raw_url = (
        candidate.get("content")
        if is_video
        else candidate.get("href") or candidate.get("url")
    )
    if not raw_url:
        return None
    source_url = normalize_source_url(str(raw_url))
    if "\ufffd" in source_url:
        return None
    parsed = urlparse(source_url)
    host = parsed.netloc.lower().removeprefix("www.")
    if not host or any(host == item or host.endswith(f".{item}") for item in EXCLUDED_HOSTS):
        return None
    if parsed.path.lower().endswith((".doc", ".docx", ".ppt", ".pptx")):
        return None
    if host in {"instagram.com", "facebook.com"} and not is_video:
        return None
    if host == "tiktok.com" and parsed.path.startswith("/discover/"):
        return None
    if host == "studyabroad101.com" and parsed.path.casefold().startswith("/programs/nrcsa-"):
        return None
    if host == "studyabroad101.com" and parsed.path.casefold().startswith("/cities/"):
        return None
    if not _special_program_url_allowed(partner, host, parsed.path):
        return None

    title = _compact_text(candidate.get("title"))
    body = _compact_text(
        candidate.get("description") if is_video else candidate.get("body")
    )
    title_and_path = f"{title} {parsed.path.replace('-', ' ').replace('_', ' ')}"
    if NON_EXPERIENCE_TITLE_TERMS.search(
        title_and_path
    ) or MARKETING_CATALOG_TITLE_TERMS.search(title):
        return None
    combined = f"{title} {body} {source_url}"
    if not title or not EXPERIENCE_TERMS.search(combined):
        return None
    if not _is_relevant_to_partner(f"{title} {source_url}", combined, partner):
        return None
    title = _clean_experience_title(title, host, parsed.path, partner)
    partner_host = urlparse(partner.website or "").netloc.lower().removeprefix("www.")
    if (
        partner_host
        and _same_institution_domain(host, partner_host)
        and not OFFICIAL_STUDENT_STORY_TERMS.search(f"{title} {parsed.path}")
    ):
        return None
    source_type = _source_type(host, is_video)
    trusted_experience_host = _trusted_experience_host(host, combined)
    if not trusted_experience_host and not STRONG_EXPERIENCE_TERMS.search(combined):
        return None
    if source_type == ExperienceSourceType.VIDEO and not VIDEO_EXPERIENCE_TERMS.search(title):
        return None

    summary_context = combined
    if (
        host == "studyabroad101.com"
        and "/reviews/" not in parsed.path.casefold()
        and parsed.path.casefold().startswith(("/programs/", "/universities/"))
    ):
        # Search snippets for aggregator pages often contain text from unrelated
        # programs. Keep those pages as review indexes, but summarize only their
        # title and URL so another school's wording cannot become a student claim.
        summary_context = f"{title} {source_url}"
    themes = detect_themes(summary_context)
    summary = summarize_experience_text(summary_context, themes)
    perspective = _perspective(host, partner, source_type, combined)
    platform = _platform_name(host, candidate)
    author_name = _candidate_author(candidate)
    published_at = _compact_text(candidate.get("published")) or None
    content_hash = hashlib.sha256(source_url.encode("utf-8")).hexdigest()

    return StudentExperienceSource(
        school_name=partner.school_name,
        country=partner.country,
        title=title,
        source_url=source_url,
        source_type=source_type,
        platform=platform,
        author_name=author_name,
        language=detect_language(combined),
        summary=summary,
        themes=themes,
        perspective=perspective,
        published_at=published_at,
        content_hash=content_hash,
    )


def _summarize_link_content(
    source: StudentExperienceSource,
    partner: PartnerUniversity,
    *,
    timeout_seconds: float,
) -> StudentExperienceSource | None:
    """Open a result and summarize its body; search snippets are only a fallback."""
    if source.source_type == ExperienceSourceType.VIDEO:
        return source.model_copy(update={"content_status": "metadata_only"})
    reader = read_life_page if urlparse(source.source_url).path.lower().endswith(".pdf") else fetch_page_content
    fetched = reader(
        source.source_url,
        timeout_seconds=min(timeout_seconds, 20.0),
    )
    if not fetched:
        return source.model_copy(update={"content_status": "unavailable"})
    identity = f"{source.title} {source.source_url}"
    full_context = f"{identity} {fetched.title} {fetched.text[:12_000]}"
    if not _is_relevant_to_partner(identity, full_context, partner):
        return None
    full_themes = detect_themes(fetched.text)
    if not full_themes and not EXPERIENCE_TERMS.search(fetched.text):
        return None
    payload = summarize_student_link(
        title=fetched.title or source.title,
        source_url=fetched.final_url,
        page_text=fetched.text,
        allowed_themes=list(THEME_LABELS),
        timeout_seconds=max(20.0, min(timeout_seconds + 20.0, 55.0)),
    )
    theme_summaries: dict[str, str] = {}
    summary = ""
    if payload:
        summary = _compact_text(payload.get("summary_zh"))[:420]
        for row in payload.get("theme_points", []):
            if not isinstance(row, dict):
                continue
            theme = _compact_text(row.get("theme"))
            point = _compact_text(row.get("point_zh"))
            if theme not in THEME_LABELS or len(point) < 10:
                continue
            existing = theme_summaries.get(theme)
            theme_summaries[theme] = f"{existing}；{point}" if existing else point
    if not summary:
        summary, theme_summaries = _extractive_page_summary(fetched.text, full_themes)
    themes = list(
        dict.fromkeys(
            [*theme_summaries, *full_themes, *source.themes]
        )
    )
    if not summary:
        return source.model_copy(update={"content_status": "unavailable"})
    return source.model_copy(
        update={
            "title": fetched.title or source.title,
            "source_url": normalize_source_url(fetched.final_url),
            "language": detect_language(fetched.text),
            "summary": summary,
            "themes": themes,
            "theme_summaries": theme_summaries,
            "content_status": "full_text",
            "content_hash": hashlib.sha256(fetched.text.encode("utf-8")).hexdigest(),
        }
    )


def _extractive_page_summary(
    text: str,
    themes: list[str],
) -> tuple[str, dict[str, str]]:
    sentences = [
        _compact_text(item).strip(" -|•")
        for item in re.split(r"(?<=[。！？.!?])\s+|\n+", text)
    ]
    sentences = [item for item in sentences if 28 <= len(item) <= 280]
    theme_summaries: dict[str, str] = {}
    selected: list[str] = []
    for theme in themes:
        pattern = re.compile(THEME_PATTERNS[theme], re.IGNORECASE)
        sentence = next((item for item in sentences if pattern.search(item)), None)
        if not sentence:
            continue
        theme_summaries[theme] = sentence[:180]
        if sentence not in selected:
            selected.append(sentence)
    if not selected:
        selected = sentences[:2]
    return " ".join(selected[:3])[:420], theme_summaries


def _candidate_author(candidate: dict[str, Any]) -> str | None:
    for key in ("uploader", "channel", "author", "publisher"):
        value = candidate.get(key)
        if isinstance(value, dict):
            value = value.get("name") or value.get("title")
        compact = _compact_text(value)
        if compact:
            return compact[:120]
    return None


def normalize_source_url(url: str) -> str:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower().removeprefix("www.")
    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_KEYS
    ]
    if host in {"youtube.com", "m.youtube.com"}:
        query_items = [(key, value) for key, value in query_items if key == "v"]
        host = "youtube.com"
    if host == "studyabroad101.com":
        query_items = [
            (key, value) for key, value in query_items if key.lower() != "page"
        ]
    return urlunparse(
        (
            parsed.scheme or "https",
            host,
            parsed.path.rstrip("/") or "/",
            "",
            urlencode(query_items),
            "",
        )
    )


def detect_themes(text: str) -> list[str]:
    compact = _compact_text(text).lower()
    return [
        theme for theme, pattern in THEME_PATTERNS.items() if re.search(pattern, compact)
    ]


def summarize_experience_text(text: str, themes: list[str]) -> str:
    compact = _compact_text(text).lower()
    insights: list[str] = []
    for signal_theme, pattern, insight in SIGNAL_PATTERNS:
        if signal_theme in themes and re.search(pattern, compact) and insight not in insights:
            insights.append(insight)
        if len(insights) >= 2:
            break
    if insights:
        return "；".join(insights) + "。"
    if themes:
        labels = "、".join(THEME_LABELS[theme] for theme in themes[:3])
        return f"這個來源主要談到{labels}，可搭配其他年份與不同身分的心得交叉查看。"
    return "這個公開來源從學生角度談到在校學習或生活，建議開啟原文或影片確認完整脈絡。"


def build_experience_digest(
    school_name: str,
    country: str | None,
    sources: list[StudentExperienceSource],
) -> StudentExperienceDigest:
    partner = PartnerUniversity(
        program_type="交換學生",
        country=country,
        school_name=school_name,
        source_url="",
    )
    school_sources = [
        source
        for source in sources
        if normalize_school(source.school_name) == normalize_school(school_name)
        and _stored_source_is_allowed(source, partner)
    ]
    theme_sources: dict[str, list[StudentExperienceSource]] = {}
    for source in school_sources:
        for theme in source.themes:
            if not _theme_summary_is_usable(source, theme):
                continue
            theme_sources.setdefault(theme, []).append(source)

    highlights: list[ExperienceHighlight] = []
    for theme, related in sorted(
        theme_sources.items(), key=lambda item: (-len(item[1]), THEME_LABELS.get(item[0], item[0]))
    ):
        if not related:
            continue
        key_points = _concrete_points_for_theme(related, theme)
        summary = (
            "；".join(key_points) + "。"
            if key_points
            else "已找到相關公開連結，但摘要尚未擷取到足以列點的具體內容。"
        )
        highlights.append(
            ExperienceHighlight(
                theme=theme,
                title=THEME_LABELS.get(theme, theme),
                summary=summary,
                source_count=len(related),
                key_points=key_points,
                source_urls=[source.source_url for source in related[:4]],
            )
        )

    highlight_map = {highlight.theme: highlight for highlight in highlights}
    common_strengths: list[ExperienceInsight] = []
    common_challenges: list[ExperienceInsight] = []
    mixed_opinions: list[ExperienceInsight] = []
    for theme, related in theme_sources.items():
        highlight = highlight_map.get(theme)
        if not highlight:
            continue
        positive = [
            source
            for source in related
            if POSITIVE_EXPERIENCE_PATTERN.search(
                f"{source.title} {_summary_for_theme(source.summary, theme, source.theme_summaries)}"
            )
        ]
        challenges = [
            source
            for source in related
            if CHALLENGE_EXPERIENCE_PATTERN.search(
                f"{source.title} {_summary_for_theme(source.summary, theme, source.theme_summaries)}"
            )
        ]
        if len(positive) >= 2:
            common_strengths.append(
                ExperienceInsight(
                    title=f"常見優點：{THEME_LABELS.get(theme, theme)}",
                    summary=_experience_insight_summary(positive, theme),
                    source_count=len({source.source_url for source in positive}),
                    source_urls=[source.source_url for source in positive[:4]],
                )
            )
        if len(challenges) >= 2 or (theme == "challenges" and challenges):
            common_challenges.append(
                ExperienceInsight(
                    title=f"常見提醒：{THEME_LABELS.get(theme, theme)}",
                    summary=_experience_insight_summary(challenges, theme),
                    source_count=len({source.source_url for source in challenges}),
                    source_urls=[source.source_url for source in challenges[:4]],
                )
            )
        positive_urls = {source.source_url for source in positive}
        challenge_urls = {source.source_url for source in challenges}
        opinion_urls = positive_urls | challenge_urls
        has_distinct_sides = bool(positive_urls - challenge_urls) and bool(
            challenge_urls - positive_urls
        )
        if len(opinion_urls) >= 2 and has_distinct_sides:
            positive_summary = _experience_insight_summary(positive, theme)
            challenge_summary = _experience_insight_summary(challenges, theme)
            mixed_opinions.append(
                ExperienceInsight(
                    title=f"看法分歧：{THEME_LABELS.get(theme, theme)}",
                    summary=f"正面經驗：{positive_summary}；需要留意：{challenge_summary}",
                    source_count=len(opinion_urls),
                    source_urls=list(
                        dict.fromkeys(source.source_url for source in [*positive, *challenges])
                    )[:4],
                )
            )

    common_strengths.sort(key=lambda item: (-item.source_count, item.title))
    common_challenges.sort(key=lambda item: (-item.source_count, item.title))
    mixed_opinions.sort(key=lambda item: (-item.source_count, item.title))
    source_years: set[int] = set()
    for source in school_sources:
        match = re.search(r"(?:19|20)\d{2}", source.published_at or "")
        if match:
            source_years.add(int(match.group(0)))

    total = len(school_sources)
    if total >= 6:
        coverage_note = f"已整理 {total} 個公開來源；先看重複出現的主題，再比較不同年份與學生身分。"
    elif total:
        coverage_note = f"目前找到 {total} 個公開來源，樣本仍少，請把內容當作行前參考而非整體評價。"
    else:
        coverage_note = "目前尚未找到足夠相關的公開學生心得，系統不會以一般學校介紹冒充學生經驗。"

    last_checked = max(
        (source.discovered_at for source in school_sources),
        default=None,
    )
    return StudentExperienceDigest(
        school_name=school_name,
        country=country,
        total_sources=total,
        article_count=sum(source.source_type == ExperienceSourceType.ARTICLE for source in school_sources),
        video_count=sum(source.source_type == ExperienceSourceType.VIDEO for source in school_sources),
        community_count=sum(source.source_type == ExperienceSourceType.COMMUNITY for source in school_sources),
        highlights=highlights[:10],
        common_strengths=common_strengths[:3],
        common_challenges=common_challenges[:3],
        mixed_opinions=mixed_opinions[:3],
        source_years=sorted(source_years, reverse=True),
        sources=school_sources,
        last_checked=last_checked,
        coverage_note=coverage_note,
    )


def _summary_for_theme(
    summary: str,
    theme: str,
    theme_summaries: dict[str, str] | None = None,
) -> str:
    if theme_summaries and theme_summaries.get(theme):
        return theme_summaries[theme]
    compact = re.sub(r"\s+", " ", summary).strip()
    for legacy, concrete in LEGACY_EXPERIENCE_INSIGHTS.items():
        compact = compact.replace(legacy, concrete)
    matching = [
        insight
        for signal_theme, _, insight in SIGNAL_PATTERNS
        if signal_theme == theme and insight in compact
    ]
    return "；".join(dict.fromkeys(matching))


def _concrete_points_for_theme(
    sources: list[StudentExperienceSource], theme: str, limit: int = 4
) -> list[str]:
    """Keep only concrete, theme-specific statements for student-facing bullets."""
    points: list[str] = []
    seen: set[str] = set()
    for source in sources:
        if not _theme_summary_is_usable(source, theme):
            continue
        theme_summary = _summary_for_theme(
            source.summary,
            theme,
            source.theme_summaries,
        )
        candidates = [
            part.strip(" ，；。")
            for part in re.split(r"[。；;]", theme_summary)
            if part.strip(" ，；。")
        ]
        for point in candidates:
            if GENERIC_EXPERIENCE_SUMMARY_PATTERN.match(point):
                continue
            normalized = re.sub(r"\W+", "", point).casefold()
            if len(point) < 10 or normalized in seen:
                continue
            seen.add(normalized)
            points.append(point)
            if len(points) >= limit:
                return points
    return points


def _theme_summary_is_usable(source: StudentExperienceSource, theme: str) -> bool:
    if source.content_status != "full_text":
        return False
    summary = source.theme_summaries.get(theme, "").strip()
    if not summary or SOURCE_CHROME_PATTERN.search(summary):
        return False
    pattern = THEME_PATTERNS.get(theme)
    return bool(pattern and re.search(pattern, summary, re.IGNORECASE))


def _experience_insight_summary(
    sources: list[StudentExperienceSource], theme: str
) -> str:
    points = _concrete_points_for_theme(sources, theme, limit=2)
    if points:
        return "；".join(points) + "。"
    return THEME_DIGEST_SUMMARIES.get(theme, "建議比較不同年份與學生背景。")


def cache_is_fresh(
    sources: list[StudentExperienceSource], max_age_days: int = 30
) -> bool:
    if not sources:
        return False
    latest = max(source.discovered_at for source in sources)
    return latest >= datetime.now(timezone.utc) - timedelta(days=max_age_days)


def normalize_school(value: str) -> str:
    return school_identity_key(value)


def _is_relevant_to_partner(
    identity_text: str,
    context_text: str,
    partner: PartnerUniversity,
) -> bool:
    identity = _normalize_identity_phrase(identity_text)
    context = _normalize_identity_phrase(context_text)
    search_name = _normalize_identity_phrase(school_search_name(partner.school_name))
    identity_names = {
        search_name,
        *(
            _normalize_identity_phrase(alias)
            for alias in SCHOOL_IDENTITY_ALIASES.get(search_name, set())
        ),
    }
    identity_names.discard("")
    excluded_names = {
        _normalize_identity_phrase(name)
        for name in SCHOOL_IDENTITY_EXCLUSIONS.get(search_name, set())
    }
    if any(name in identity for name in excluded_names):
        return False
    if search_name in STRICT_IDENTITY_NAMES:
        name_match = any(name in identity or name in context for name in identity_names)
    else:
        significant_words = [
            word
            for word in re.findall(r"[a-z]{4,}", search_name)
            if word not in {"university", "college", "school"}
        ]
        name_match = any(name in identity or name in context for name in identity_names) or (
            len(significant_words) >= 2
            and all(word in identity or word in context for word in significant_words)
        )
    if not name_match:
        return False

    country_name = COUNTRY_SEARCH_NAMES.get(partner.country or "", partner.country or "").casefold()
    country_terms = [term for term in {country_name, (partner.country or "").casefold()} if term]
    if search_name in {"lincoln university", "national university", "central university"}:
        country_terms.extend(["christchurch", "canterbury", "lincoln.ac.nz"])
        return any(term in context for term in country_terms)
    return True


def _normalize_identity_phrase(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    normalized = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    ).casefold()
    return re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE).strip()


def _stored_identity_title(title: str, partner: PartnerUniversity) -> str:
    school_name = school_search_name(partner.school_name)
    review_suffix = f"｜{school_name} 交換心得"
    if review_suffix in title:
        return title.split(review_suffix, 1)[0].strip(" .|-｜")
    if title in {
        f"{school_name}｜學生評價彙整",
        f"{school_name}｜學生生活評價",
        f"{school_name}｜交換計畫學生評價",
        f"{school_name}｜交換學生心得",
    }:
        return ""
    return title


def _special_program_url_allowed(
    partner: PartnerUniversity,
    host: str,
    path: str,
) -> bool:
    search_name = _normalize_identity_phrase(school_search_name(partner.school_name))
    if host != "studyabroad101.com":
        return True
    normalized_path = path.casefold()
    if normalized_path.startswith("/providers/"):
        return False
    if search_name == "university of minnesota go minnesota":
        return any(
            marker in normalized_path
            for marker in ("go-minnesota", "university-of-minnesota-twin-cities")
        )
    if search_name == "university of minnesota":
        return "university-of-minnesota-twin-cities" in normalized_path
    if search_name == "university of california irvine":
        return any(
            marker in normalized_path
            for marker in (
                "/universities/university-of-california-irvine",
                "university-of-california-irvine-direct-enrollment",
            )
        )
    if search_name == "fordham university":
        return any(
            marker in normalized_path
            for marker in (
                "/universities/fordham-university",
                "fordham-university-new-york-direct-enrollment",
            )
        )
    return True


def _clean_experience_title(
    title: str,
    host: str,
    path: str,
    partner: PartnerUniversity,
) -> str:
    school_name = school_search_name(partner.school_name)
    normalized_path = path.casefold()
    review_suffix = f"｜{school_name} 交換心得"
    if review_suffix in title:
        lead = title.split(review_suffix, 1)[0].strip(" .|-｜")
        return f"{lead}{review_suffix}" if lead else f"{school_name}｜交換學生心得"
    canonical_titles = {
        f"{school_name}｜學生評價彙整",
        f"{school_name}｜學生生活評價",
        f"{school_name}｜交換計畫學生評價",
        f"{school_name}｜交換學生心得",
    }
    if title in canonical_titles:
        return title
    if host in {"youtube.com", "youtu.be"}:
        for marker in ("...", "…"):
            if marker in title and not title.rstrip().endswith(marker):
                return f"{title.split(marker, 1)[0].rstrip()} {marker}"
    if host == "eduopinions.com":
        if "/student-reviews-" in normalized_path:
            return title
        return f"{school_name}｜學生評價彙整"
    if host == "iagora.com":
        if "type=life" in normalized_path:
            return f"{school_name}｜學生生活評價"
        if "show=reviews" in normalized_path or normalized_path.endswith("/reviews"):
            return f"{school_name}｜學生評價彙整"
        return title
    if host != "studyabroad101.com":
        return title

    if "/reviews/" in normalized_path:
        lead = re.split(r"\s+\|\s+a review for", title, maxsplit=1, flags=re.IGNORECASE)[0]
        lead = lead.strip(" .|-")
        if lead and len(lead) <= 120:
            return f"{lead}｜{school_name} 交換心得"
        return f"{school_name}｜交換學生心得"
    if normalized_path.startswith("/universities/"):
        return f"{school_name}｜學生評價彙整"
    if normalized_path.startswith("/programs/"):
        return f"{school_name}｜交換計畫學生評價"
    return title


def _same_institution_domain(host: str, partner_host: str) -> bool:
    return _institution_domain(host) == _institution_domain(partner_host)


def _institution_domain(host: str) -> str:
    labels = host.casefold().strip(".").split(".")
    if len(labels) <= 2:
        return ".".join(labels)
    public_suffix = ".".join(labels[-2:])
    if public_suffix in {"ac.jp", "ac.nz", "ac.uk", "edu.au", "edu.hk", "edu.sg"}:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def _source_type(host: str, is_video: bool) -> ExperienceSourceType:
    if is_video or host in {"youtube.com", "youtu.be", "tiktok.com", "vimeo.com"}:
        return ExperienceSourceType.VIDEO
    if host == "reddit.com" or host.endswith(".reddit.com"):
        return ExperienceSourceType.COMMUNITY
    return ExperienceSourceType.ARTICLE


def _trusted_experience_host(host: str, text: str) -> bool:
    if any(marker in host for marker in ("blogspot", "wordpress", "medium", "substack")):
        return bool(
            STRONG_EXPERIENCE_TERMS.search(text)
            or re.search(r"exchange|studyabroad|utveksling|erasmus", host, re.IGNORECASE)
        )
    return any(host == item or host.endswith(f".{item}") for item in REVIEW_HOSTS)


def _perspective(
    host: str,
    partner: PartnerUniversity,
    source_type: ExperienceSourceType,
    text: str,
) -> str:
    partner_host = urlparse(partner.website or "").netloc.lower().removeprefix("www.")
    if partner_host and (host == partner_host or host.endswith(f".{partner_host}")):
        return "official_student_story"
    if source_type == ExperienceSourceType.COMMUNITY:
        return "community_discussion"
    if source_type == ExperienceSourceType.VIDEO:
        return "student_created" if STRONG_EXPERIENCE_TERMS.search(text) else "independent"
    if any(
        marker in host for marker in ("blogspot", "wordpress", "medium")
    ):
        return "student_created"
    return "independent"


def _platform_name(host: str, candidate: dict[str, Any]) -> str:
    known = {
        "youtube.com": "YouTube",
        "youtu.be": "YouTube",
        "tiktok.com": "TikTok",
        "reddit.com": "Reddit",
        "medium.com": "Medium",
    }
    for domain, label in known.items():
        if host == domain or host.endswith(f".{domain}"):
            return label
    provider = _compact_text(candidate.get("provider"))
    return provider or host


def detect_language(text: str) -> str:
    if re.search(r"[\u3040-\u30ff]", text):
        return "ja"
    if re.search(r"[\uac00-\ud7af]", text):
        return "ko"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"\b(?:Erfahrungsbericht|Auslandssemester|Wohnheim|Vorlesungen)\b", text, re.I):
        return "de"
    if re.search(r"\b(?:témoignage|logement|étudiants|université)\b", text, re.I):
        return "fr"
    if re.search(r"[A-Za-z]", text):
        return "en"
    return "unknown"


def _source_sort_key(source: StudentExperienceSource) -> tuple[int, int, str]:
    perspective_priority = {
        "community_discussion": 0,
        "student_created": 1,
        "independent": 2,
        "official_student_story": 3,
    }
    return (
        perspective_priority.get(source.perspective, 4),
        -len(source.themes),
        source.title.casefold(),
    )


def _keep_source_diversity(
    sources: list[StudentExperienceSource], max_sources: int
) -> list[StudentExperienceSource]:
    selected: list[StudentExperienceSource] = []
    platform_counts: dict[str, int] = {}
    mirrored_article_slugs: set[str] = set()
    for source in sources:
        if platform_counts.get(source.platform, 0) >= 4:
            continue
        if source.source_type == ExperienceSourceType.ARTICLE:
            slug = urlparse(source.source_url).path.rstrip("/").rsplit("/", 1)[-1].casefold()
            if len(slug) >= 40 and slug in mirrored_article_slugs:
                continue
            if len(slug) >= 40:
                mirrored_article_slugs.add(slug)
        selected.append(source)
        platform_counts[source.platform] = platform_counts.get(source.platform, 0) + 1
        if len(selected) >= max_sources:
            break
    return selected


def _compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()
