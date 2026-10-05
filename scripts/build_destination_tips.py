"""Write ``official_data/destination_tips_zh.json`` from the curated notes below.

    python scripts/build_destination_tips.py

Every item names the public page it was taken from, and the output must pass ``validate_guides`` before it is
written. Nothing here is marked reviewed: guides stay ``draft`` until two reviewers sign off.

Research date for every item: pages were opened on 2026-10-04 (``CHECKED``). Pages that refused automated access
(陸委會 403, IEC 403) are cited only for statements another opened page also supports, or for the page's own title.
Deeper, country-specific notes exist for 中國大陸, 日本, 韓國, 法國 and 美國 so far; every other country carries the shared
notes, its local emergency numbers and the mains voltage. Add a country by extending ``DEEP`` and re-running this script.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from exchange_info.destination_tips import GUIDES_FILE, TOPICS, validate_guides  # noqa: E402

CHECKED = "2026-10-04"

SOURCES = {
    "boca_visa": ("外交部領事事務局：各國暨各地區簽證及入境須知", "https://www.boca.gov.tw/sp-foof-countrylp-03-1.html"),
    "boca_warning": ("外交部領事事務局：旅遊警示", "https://www.boca.gov.tw/sp-trwa-list-1.html"),
    "boca_register": ("外交部領事事務局：旅外動態登錄說明", "https://www.boca.gov.tw/sp-abre-main-1.html"),
    "boca_emergency": ("外交部領事事務局：外交部緊急聯絡中心", "https://www.boca.gov.tw/fp-53-378-353fb-1.html"),
    "sef_handbook": ("海基會：2025 中國大陸旅行安全手冊", "https://www.sef.org.tw/eBook/CHebook/2025/index.html"),
    "sef_emergency": ("海基會：兩岸人民急難服務中心", "https://www.sef.org.tw/article-1-15-1326"),
    "seftb_notes": ("海基會兩岸經貿網：中國大陸旅行注意事項", "https://www.seftb.org/cp-1038-1026-263d8-1.html"),
    "seftb_health": ("海基會兩岸經貿網：赴中國大陸前之準備", "https://www.seftb.org/cp-1039-1033-4ebdc-1.html"),
    "mac_risk": ("陸委會：國人赴陸港澳風險專區", "https://www.mac.gov.tw/cp.aspx?n=16F6C9D66219D903"),
    "mac_emergency": ("陸委會：陸港澳緊急服務資訊", "https://www.mac.gov.tw/cp.aspx?n=D685A20065F89CCD"),
    "mac_study": ("陸委會：赴陸就學你不能不知道的8件事", "https://www.mac.gov.tw/cp.aspx?n=F85CABCA09695756&s=066C2FE066864ADA"),
    "nia_card": ("國家移民管理局：台灣居民來往大陸通行證簽發服務指南", "https://s.nia.gov.cn/mps/bszy/wldl/sqwldl/201903/t20190312_999.html"),
    "bj_wechat": ("北京市政府：外國人如何使用微信支付（2023-03-10）", "https://english.beijing.gov.cn/livinginbeijing/finance/mobilepaymentlist/202005/t20200516_1899230.html"),
    "bjchy_cards": ("北京市朝陽區政府：微信支付與支付寶接受的海外銀行卡", "https://english.bjchy.gov.cn/overseas-bank-cards-accepted-weixin-pay-and-alipay"),
    "cna_registration": ("中央社：忘記住宿登記，中國公安請你進警局（2020-01-12）", "https://www.cna.com.tw/news/acn/202001120152.aspx"),
    "cht_roaming": ("中華電信：中國輕量型漫遊，原機原號、中國免翻牆（2019）", "https://www.cht.com.tw/zh-tw/home/cht/messages/2019/msg-190426-153000"),
    "miit_vpn": ("北京新聞：工信部回應 VPN 管控，合法使用受法律保護", "https://m.bjnews.com.cn/detail/156896310115210.html"),
    "boca_services": ("外交部領事事務局：駐外館處提供旅外國人急難救助服務項目", "https://www.boca.gov.tw/cp-85-244-cdfdb-1.html"),
    # Japan
    "sij_immigration": ("Study in Japan（日本學生支援機構）：Immigration and Students Visas", "https://www.studyinjapan.go.jp/en/planning/immigration-procedures/"),
    "sij_residing": ("Study in Japan：Status of Residence", "https://www.studyinjapan.go.jp/en/life/residing-in-japan/"),
    "sij_insurance": ("Study in Japan：Insurance", "https://www.studyinjapan.go.jp/en/life/insurance/"),
    "sij_accommodation": ("Study in Japan：Accommodation", "https://www.studyinjapan.go.jp/en/life/accomodation/"),
    "sij_cost": ("Study in Japan：Living Costs and Expenses", "https://www.studyinjapan.go.jp/en/life/cost-of-living/"),
    "fsa_bank": ("日本金融廳：Living in Japan, How to Open a Bank Account and Send Money（2024-09 修訂）", "https://www.fsa.go.jp/en/user/livinginjapan.html"),
    "mofa_tw_japan": ("外交部：駐日本代表處", "https://www.mofa.gov.tw/OverseasOffice_Content.aspx?n=168&sms=87&s=142&os=79"),
    # Korea
    "sik_residence": ("Study in Korea：Residence Eligibility and Stay Duration", "https://www.studyinkorea.go.kr/ko/life/residenceAndStayInfo.do"),
    "sik_living": ("Study in Korea：Living and Housing Information", "https://www.studyinkorea.go.kr/ko/life/livingAndHousing.do"),
    "nhis_2021": ("韓國國民健康保險公團：2021 Notification for International Students in Korea on NHI（2021-03-04）", "https://www.nhis.or.kr/english/wbheaa03500m01.do?mode=view&articleNo=10805709&title=2021+Notification+for+International+Students+in+Korea+on+NHI"),
    "korea_net_nhi": ("Korea.net：6-month stay for expats required from April for health insurance（2024-01-25）", "https://www.korea.net/NewsFocus/policies/view?articleId=245999"),
    "korea_net_phone": ("Korea.net：Getting mobile phone service（2019-03-19）", "https://www.korea.net/NewsFocus/Society/view?articleId=169210"),
    "korea_net_bank": ("Korea.net：Expats can use mobile ID card to open bank accounts（2025-03-21）", "https://www.korea.net/NewsFocus/policies/view?articleId=268434"),
    "mofa_tw_korea": ("外交部：駐韓國代表處", "https://www.mofa.gov.tw/OverseasOffice_Content.aspx?n=168&sms=87&s=59&os=4"),
    # France
    "cf_validate": ("Campus France：如何在抵達法國後驗證長期簽證（頁面更新 2026-08-12）", "https://www.campusfrance.org/en/how-to-validate-your-long-stay-visa-visa-long-sejour-upon-your-arrival-in-france"),
    "cf_vlst": ("Campus France：The student Temporary Long Term Visa, or VLS-T", "https://www.campusfrance.org/en/the-temporary-long-term-visa-or-vls-t"),
    "cf_health": ("Campus France：Healthcare and student social security", "https://www.campusfrance.org/en/healthcare-student-social-security"),
    "etu_social": ("etudiant.gouv.fr：Social security, your medical expenditure coverage（2021-09-13）", "https://www.etudiant.gouv.fr/en/social-security-your-medical-expenditure-coverage-217"),
    "etu_cvec": ("etudiant.gouv.fr：Do you have to pay the CVEC contribution?", "https://www.etudiant.gouv.fr/en/do-you-have-pay-cvec-contribution-955"),
    "caf_apl": ("法國家庭津貼局 CAF：APL，2026 年 7 月 1 日起部分學生的變更（2026-07-03）", "https://www.caf.fr/allocataires/actualites/actualites-nationales/apl-ce-qui-change-pour-certains-etudiants-partir-du-1er-juillet-2026"),
    "etu_visale": ("etudiant.gouv.fr：Visale 租屋擔保（2021-04-27）", "https://www.etudiant.gouv.fr/fr/aide-pour-la-caution-visale-se-porte-garant-pour-les-etudiants-739"),
    "mofa_tw_france": ("外交部：駐法國代表處", "https://www.mofa.gov.tw/OverseasOffice_Content.aspx?n=168&sms=87&s=52&os=65"),
    # United States
    "dhs_i20": ("美國國土安全部 Study in the States：Students and the Form I-20（2025-04-29 更新）", "https://studyinthestates.dhs.gov/students/prepare/students-and-the-form-i-20"),
    "dhs_ssn": ("Study in the States：Obtaining a Social Security Number（2023-05-25）", "https://studyinthestates.dhs.gov/students/work/obtaining-a-social-security-number"),
    "dhs_driving": ("Study in the States：Driving in the United States（2023-05-25）", "https://studyinthestates.dhs.gov/students/study/driving-in-the-united-states"),
    "dhs_faq": ("Study in the States：Frequently Asked Questions（2023-05-25）", "https://studyinthestates.dhs.gov/tools-menu/frequently-asked-questions"),
    "dhs_benefits": ("Study in the States：Benefits for International Students（2014-03-10，頁面可能已過時）", "https://studyinthestates.dhs.gov/2014/03/benefits-international-students"),
    "j1_state": ("美國國務院 J-1：How to Administer a Program（22 CFR 62.14 保險最低標準）", "https://j1visa.state.gov/sponsors/how-to-administer-a-program/"),
    "mofa_tw_usa": ("外交部：駐美國代表處", "https://www.mofa.gov.tw/OverseasOffice_Content.aspx?n=168&sms=87&s=63&os=92"),
    "wiki_emergency": ("Wikipedia：List of emergency telephone numbers", "https://en.wikipedia.org/wiki/List_of_emergency_telephone_numbers"),
    "wiki_power": ("Wikipedia：Mains electricity by country", "https://en.wikipedia.org/wiki/Mains_electricity_by_country"),
}


def src(*keys: str) -> list[dict]:
    return [{"name": SOURCES[key][0], "url": SOURCES[key][1]} for key in keys]


def tip(title: str, detail: str, importance: str, *keys: str) -> dict:
    return {"title": title, "detail": detail, "importance": importance, "sources": src(*keys), "checked_at": CHECKED}


def topic(key: str, *tips: dict) -> dict:
    return {"topic": key, "title": TOPICS[key], "tips": list(tips)}


# --------------------------------------------------------------------------------------------- shared notes

def shared_documents(country: str) -> list[dict]:
    return [
        tip(f"出發前先查{country}的簽證與入境規定",
            "外交部領事事務局整理了各國對台灣護照的簽證與入境須知（免簽、落地簽、電子簽、停留天數、護照效期等）。"
            "規定會變動，出發前和買機票前各查一次，並以官方頁面為準，不要只看部落格或旅行社的舊文章。",
            "must", "boca_visa"),
        tip("出國前先做旅外動態登錄",
            "出國前把姓名、護照、聯絡方式、緊急聯絡人、行程與住宿地點登錄給外交部，發生天災、動亂或需要協尋時，駐外館處才能主動聯絡你。"
            "資料在旅程結束後保存 3 個月，之後自動刪除或去識別化。",
            "should", "boca_register"),
        tip("看一下目的地目前的旅遊警示等級",
            "外交部把旅遊警示分成灰（提醒）、黃（注意）、橙（避免前往）、紅（儘速離境）四級。出發前和出發當週都查一次，等級變動時要重新評估行程。",
            "should", "boca_warning"),
    ]


def shared_emergency() -> list[dict]:
    return [
        tip("把外交部緊急聯絡中心的電話存進手機",
            "外交部緊急聯絡中心全年 24 小時，專門處理旅外國人的急難救助：台灣境內免付費電話 0800-085-095，從海外撥打是 +886-800-085-095（付費）。"
            "只有急難才打，護照、簽證等一般業務請在上班時間找其他窗口。",
            "must", "boca_emergency"),
        tip("先知道駐外館處能幫什麼、不能幫什麼",
            "駐外館處可以補發護照或核發入國證明書、代為聯絡家人親友或雇主、協助聯絡保險公司、陪同重大犯罪被害人報案、提供當地醫師律師翻譯名單，並在當事人被外國政府逮捕或拘禁時（經該國同意）行使領事探視。"
            "它們不提供金錢救濟，不代墊醫藥費、罰款、保釋金或律師費，也不能介入外國司法程序、提供法律意見或當你的代理人。出事前就先把這條界線記在心裡，旅行平安險和海外急難保險才是花錢的那一邊。",
            "should", "boca_services"),
    ]


EMERGENCY = {  # (what to dial, note)
    "法國": ("警察 17、救護 15、消防 18", "歐盟通用 112 也能撥。"),
    "日本": ("警察 110、救護與消防 119", ""),
    "韓國": ("警察 112、救護與消防 119", ""),
    "美國": ("警察、救護、消防都是 911", ""),
    "德國": ("警察 110、救護與消防 112", ""),
    "波蘭": ("警察 997、救護 999、消防 998", "也可撥歐盟通用 112。"),
    "越南": ("警察 113、救護 115、消防 114", ""),
    "捷克": ("通用 112；警察 158、救護 155、消防 150", ""),
    "泰國": ("警察 191、救護 1669、消防 199", "號碼可能調整，請以當地公告為準。"),
    "印度": ("通用 112；警察 100、救護 108、消防 101", ""),
    "香港": ("警察、救護、消防都是 999", ""),
    "西班牙": ("通用 112", ""),
    "瑞典": ("通用 112", ""),
    "印尼": ("通用 112；警察 110、救護 118 或 119、消防 113", ""),
    "土耳其": ("通用 112", ""),
    "俄羅斯": ("警察 102、救護 103、消防 101", "也可撥 112。"),
    "加拿大": ("警察、救護、消防都是 911", ""),
    "荷蘭": ("通用 112", ""),
    "比利時": ("通用 112；警察另有 101", ""),
    "義大利": ("通用 112；救護 118、消防 115", "部分地區 112 的運作方式不同，到了當地再確認。"),
    "立陶宛": ("通用 112", ""),
    "挪威": ("警察 112、救護 113、消防 110", ""),
    "馬來西亞": ("警察、救護、消防都是 999", "手機也可撥 112。"),
    "羅馬尼亞": ("通用 112", ""),
    "斯洛伐克": ("通用 112；警察 158、救護 155、消防 150", ""),
    "奧地利": ("通用 112；警察 133、救護 144、消防 122", ""),
    "新加坡": ("警察 999、救護與消防 995", ""),
    "菲律賓": ("通用 911", "手機也可撥 112。"),
    "英國": ("通用 999", "也可撥 112。"),
    "拉脫維亞": ("通用 112", ""),
    "巴西": ("警察 190、救護 192、消防 193", ""),
    "匈牙利": ("通用 112；警察 107、救護 104、消防 105", ""),
    "哈薩克": ("通用 112；警察 102、救護 103、消防 101", ""),
    "孟加拉": ("警察、救護、消防都是 999", ""),
    "阿爾巴尼亞": ("警察 129、救護 127、消防 128", ""),
    "瑞士": ("警察 117、救護 144、消防 118", "各州使用情形略有差異。"),
    "紐西蘭": ("警察、救護、消防都是 111", ""),
    "澳洲": ("警察、救護、消防都是 000", ""),
    "蒙古": ("警察 102、救護 103、消防 101", ""),
    "緬甸": ("警察 199、救護 192、消防 191", ""),
    "摩洛哥": ("警察 19、救護 15", "手機也可撥 112。"),
    "柬埔寨": ("警察 117、救護 119、消防 118", ""),
}

VOLTAGE = {  # country -> (voltage text, extra)
    "日本": ("約 100 V（東日本 50 Hz、西日本 60 Hz）", "台灣電器多為 110 V，在日本通常可直接使用，插座為 A、B 型。"),
    "美國": ("約 120 V、60 Hz", "與台灣電器相近，插座為 A、B 型。"),
    "加拿大": ("約 120 V、60 Hz", "與台灣電器相近，插座為 A、B 型。"),
    "韓國": ("約 220 V、60 Hz", "台灣 110 V 電器需確認支援 220 V，否則要變壓器；插座為 C、F 型。"),
    "菲律賓": ("約 220 V、60 Hz", "台灣 110 V 電器需確認支援 220 V，否則要變壓器。"),
    "巴西": ("依地區約 127 V 或 220 V、60 Hz", "各州不一樣，到了當地先問清楚再插電。"),
    "英國": ("約 230 V、50 Hz", "插座為 G 型（英式三孔），台灣 110 V 電器需確認支援 230 V。"),
    "香港": ("約 220 V、50 Hz", "插座為 G 型（英式三孔），台灣 110 V 電器需確認支援 220 V。"),
    "新加坡": ("約 230 V、50 Hz", "插座為 G 型（英式三孔），台灣 110 V 電器需確認支援 230 V。"),
    "馬來西亞": ("約 230 V、50 Hz", "插座以 G 型（英式三孔）為主，台灣 110 V 電器需確認支援 230 V。"),
    "紐西蘭": ("約 230 V、50 Hz", "插座為 I 型（斜三腳），台灣 110 V 電器需確認支援 230 V。"),
    "澳洲": ("約 230 V、50 Hz", "插座為 I 型（斜三腳），台灣 110 V 電器需確認支援 230 V。"),
}
DEFAULT_VOLTAGE = ("約 220–240 V、50 Hz", "台灣電器多為 110 V，使用前看電器標示是否支援 220–240 V，不支援就要變壓器；各國插座型式不同，建議帶萬用轉接頭並向合作校或房東確認。")


def shared_packing(country: str) -> list[dict]:
    voltage, extra = VOLTAGE.get(country, DEFAULT_VOLTAGE)
    return [tip(f"{country}的電壓與插座", f"一般市電電壓{voltage}。{extra}實際以當地插座與電器標示為準。", "good_to_know", "wiki_power")]


# --------------------------------------------------------------------------------------------- 中國大陸

CHINA = {
    "country": "大陸地區",
    "display_name": "中國大陸",
    "intro": "去中國大陸的差別不在簽證本身，而在落地後的日常：證件要用台胞證、上網方式要先決定、付款幾乎都靠手機，還有住宿登記與資料安全這些容易被忽略的事。以下依官方與政府單位的公開說明整理，標出了出處與查證日期。",
    "topics": [
        topic("documents",
              tip("進出大陸要用台胞證，轉機也要",
                  "台灣居民進出大陸使用「台灣居民來往大陸通行證」（俗稱台胞證）。海基會手冊提醒，即使只是在大陸機場轉機，也要有有效的台胞證。出發前確認證件還沒過期，並核對台胞證與護照上的資料一致。",
                  "must", "nia_card", "sef_handbook"),
              tip("台胞證有幾種，電子版也存在",
                  "國家移民管理局說明台胞證分兩種：五年期、可多次出入境的，以及入境口岸現場申請、三個月內一次出入境有效的。"
                  "持卡式台胞證也可以申請換成電子台胞證。到底要辦哪一種，先問學校國際處與合作校。",
                  "should", "nia_card", "sef_handbook"),
              tip("赴大陸要到陸委會網站另外登錄行程",
                  "外交部的旅外動態登錄頁面特別註明：去大陸、香港、澳門的人要到陸委會網站另行登錄，不是登錄在外交部那一套。出發前順手完成。",
                  "must", "boca_register", "mac_risk"),
              tip("護照與證件留影本，遺失立刻報案",
                  "護照、台胞證、身分證要妥善保管並備好影本；證件遺失時馬上向當地公安報案、取得報案證明，後續補辦才有依據。海基會手冊也提醒，進入他國須持有至少 6 個月效期的護照，出發前一併檢查護照效期。",
                  "should", "seftb_notes", "sef_handbook"),
              tip("入學與簽注文件向兩邊學校確認",
                  "到大陸就讀的證明文件與簽注要求會因合作校與學期而不同。陸委會有整理「赴陸就學前要知道的事」，並請在出發前向本校國際處與合作校國際處書面確認需要哪些文件。",
                  "should", "mac_study")),
        topic("phone_internet",
              tip("先決定怎麼上網：原機原號的國際漫遊最不容易出錯",
                  "台灣電信業者的國際漫遊走的是台灣網路，所以 Google、LINE、Facebook 這些在大陸被限制的服務通常照常使用，中華電信官網就把它列為「中國免翻牆」的方案。"
                  "出發前先向電信業者申辦漫遊、確認天數與費率；長期留學要比較漫遊、當地門號與 eSIM 的總花費。方案內容會調整，請以業者最新公告為準。",
                  "must", "cht_roaming"),
              tip("手機和電腦先備份，刪掉不該被檢查的內容",
                  "海基會手冊建議出發前把手機、電腦備份後，刪除可能引來陸方檢查或沒收的內容。這項要在入境之前做完，而不是在機場才處理。",
                  "must", "sef_handbook"),
              tip("不要假設能用 VPN，必要的事別押在它身上",
                  "工信部在 2017 年的通知說明：未經電信主管部門批准，個人與單位不得自行建立或租用專線（含 VPN）從事跨境業務；官方同時表示合法的使用受法律保護。"
                  "對旅客與學生來說，意思是不要依賴 VPN 處理必要的聯絡、銀行或學校事務，出發前就用漫遊或當地替代方案測試過。規定的適用範圍請以最新法規與學校說明為準。",
                  "should", "miit_vpn"),
              tip("大陸門號要實名，台胞證是驗證證件",
                  "在大陸辦電話卡需要用台胞證做實名認證。拿門號去綁支付寶、微信支付等服務時，海基會手冊提醒要謹慎保管個人資訊，不要外流。",
                  "should", "sef_handbook"),
              tip("使用大陸當地 App 前想清楚權限",
                  "海基會手冊建議注意使用大陸當地 App，避免個人的電信足跡外流。訂票、支付、地圖常常少不了當地 App，建議只裝必要的、檢查它要求的權限，不用的就移除。",
                  "should", "sef_handbook"),
              tip("大陸撥回台灣的號碼格式",
                  "從大陸撥台灣市話或手機，格式是 00-886-區域碼（去掉開頭的 0）-電話號碼；手機則是 00-886-手機號碼（去掉開頭的 0）。",
                  "good_to_know", "seftb_notes")),
        topic("payment",
              tip("手機支付要先在台灣綁好卡並小額試付",
                  "北京市政府與朝陽區政府的說明指出：外國訪客可以用海外信用卡綁定微信支付與支付寶。微信支付接受 Visa、Mastercard、JCB 等，支付寶接受 Visa、Mastercard、Diners、Discover 等；"
                  "實名驗證可以用港澳台居民往來內地通行證（台胞證），不需要 +86 門號，國際門號能收驗證簡訊即可。建議出發前在台灣先綁卡並小額測試，確認驗證簡訊收得到再出發。",
                  "must", "bjchy_cards", "bj_wechat"),
              tip("海外卡有額度與手續費，以 App 內顯示為準",
                  "朝陽區政府頁面列出海外卡的單筆、月累計與年累計上限，並說明單筆低於 200 元人民幣不收手續費、超過則收 3%。該頁面沒有標示日期，額度可能已調整，實際以支付寶與微信的 App 內說明為準。",
                  "should", "bjchy_cards"),
              tip("外國用戶的微信支付只能消費，不能轉帳和發紅包",
                  "北京市政府（2023-03-10）說明外國用戶的微信支付只支援消費與掃碼付款，不支援一般轉帳與發紅包。想跟朋友分攤費用要另外想辦法，例如當面付現或請對方先付款。",
                  "should", "bj_wechat"),
              tip("現金：入境超過 2 萬元人民幣要申報",
                  "海基會手冊說明：出境攜帶人民幣以 2 萬元為限，入境攜帶超過 2 萬元要向海關申報。新臺幣可以在中國銀行部分城市的分行兌換，用美金兌換時要帶台胞證並填匯兌水單。",
                  "should", "sef_handbook"),
              tip("用金融卡提款要先在台灣開通國外提款",
                  "在大陸 ATM 提款，要認有 Cirrus 或 Plus 標誌的機器，並且先在台灣向銀行開通國外提款功能；提款會收手續費，出發前向發卡銀行問清楚。",
                  "should", "sef_handbook"),
              tip("錢不露白，分散放",
                  "海基會提醒：現金不要露白、分散存放，付款盡量用小額鈔票，避免招來不必要的麻煩。",
                  "good_to_know", "seftb_notes")),
        topic("housing",
              tip("落地後 24 小時內要完成住宿登記",
                  "中央社引述規定：台灣居民在大陸短期停留要辦理暫住登記。住旅館等機構由業者代辦；住在親友家或自己租屋，本人或親友要在 24 小時內（農村 72 小時）到當地派出所或戶籍辦公室登記，"
                  "逾期可能被警告，或罰人民幣 100 元以上、500 元以下。這則報導是 2020 年的，細節可能變動；住學校宿舍的人請向合作校國際處確認是否由學校代辦。",
                  "must", "cna_registration"),
              tip("住宿要留意訪客限制，陌生人敲門先別開",
                  "海基會提醒住旅館要注意訪客的限制規定；有陌生人敲門不要立刻開門，可疑的人請飯店協助處理。",
                  "should", "seftb_notes"),
              tip("自來水不要直接喝",
                  "海基會手冊提醒，住房內的自來水不適合直接飲用，要喝煮沸的水或瓶裝水。",
                  "good_to_know", "sef_handbook")),
        topic("health_insurance",
              tip("保險要含突發疾病與海外急難運送",
                  "海基會手冊建議投保含突發疾病的旅行平安險，或高額的海外急難運送保險。買之前看清楚理賠範圍包不包含留學期間，以及就醫要先墊付還是直接付費。",
                  "must", "sef_handbook"),
              tip("出發前去旅遊醫學門診，查疾管署國際旅遊與健康專區",
                  "到國際旅遊醫學門診評估要不要打疫苗、帶預防藥；備好體溫計、口罩、乾洗手等；疾病管制署的「國際旅遊與健康專區」有目的地的疫情資料。",
                  "should", "seftb_health"),
              tip("飲食衛生與高海拔",
                  "不要吃生食，路邊攤留意衛生；去高海拔地區要先評估體能，心血管疾病患者不適合前往，建議先問醫師。",
                  "good_to_know", "seftb_notes", "sef_handbook")),
        topic("safety_law",
              tip("出發前做風險評估，了解當地制度與法令",
                  "陸委會提醒赴陸就學、交流前，要先評估風險，了解當地的制度、法令與資訊，才能保障自己的權益，並提供「國人赴陸港澳風險專區」彙整相關資訊。",
                  "must", "mac_risk", "mac_study"),
              tip("敏感書籍、照片與話題要避免",
                  "海基會手冊建議避免攜帶政治、歷史、宗教相關書籍，避免拍攝港口、機場、軍事演習場所，也避免觸及或討論敏感議題。",
                  "must", "sef_handbook"),
              tip("禁止攜帶的物品",
                  "海基會手冊列出禁止攜帶：武器、彈藥與爆炸物，毒藥與使人成癮的麻醉品、精神藥物，以及具爭議性的印刷品與影音、光碟等。不確定的東西先不要帶。",
                  "must", "sef_handbook"),
              tip("不要單獨去陌生地方，不搭超載或夜間車輛",
                  "海基會提醒盡量結伴出遊、避免單獨前往陌生地點，不要搭乘超載的交通工具或夜車。",
                  "should", "seftb_notes")),
        topic("packing_power",
              tip("電壓 220 V，插座常見 A、I 型",
                  "大陸一般市電約 220 V、50 Hz，插座常見 A、I 型，有時也會遇到 C 型。台灣電器多為 110 V，使用前看標示是否支援 220 V，不支援就要變壓器；建議帶萬用轉接頭。",
                  "good_to_know", "wiki_power")),
        topic("emergency",
              tip("海基會 24 小時緊急服務專線 (02)2533-9995",
                  "在大陸遇到人身安全、旅行意外、證件遺失、旅遊糾紛等急難，可以撥海基會兩岸人民急難服務中心的 24 小時專線 (02)2533-9995；從大陸撥回台灣記得加 00-886，並去掉區域碼前的 0。",
                  "must", "sef_emergency", "seftb_notes"),
              tip("大陸當地緊急電話",
                  "警察 110、救護車 120、消防 119（交通事故另有 122）。陸委會也彙整了陸港澳的緊急服務資訊，出發前存下來。",
                  "must", "wiki_emergency", "mac_emergency")),
    ],
}

# --------------------------------------------------------------------------------------------- 日本、韓國、法國、美國
# Deeper notes for the four most common destinations after 中國大陸. They are merged into the shared notes of each country.

JAPAN = {
    "intro": "日本的重點是落地後 14 天內的行政手續（住民登錄、國民健康保險）、在留卡要隨身帶，以及銀行帳戶絕對不能借給別人。以下整理自日本政府的留學官方網站與金融廳，並標出了出處；手機門號與交通卡等細節還沒查到官方說明，所以沒有寫。",
    "topics": {
        "documents": [
            tip("留學的在留資格與 COE",
                "在日本讀大學的外國學生會取得「留學」在留資格，居留期間由法務大臣決定，最長 4 年 3 個月。入國前通常由接收學校代為向入管局申請「在留資格認定證明書（COE）」，申請時要附財力證明（擔保人的存款證明、過去一年的收入證明等）。交換生實際要怎麼辦，請向合作校國際處確認。",
                "must", "sij_immigration"),
            tip("停留超過 3 個月會拿到在留卡，要隨身帶",
                "在日本停留超過 3 個月的人會拿到在留卡。成田、羽田、中部、關西等主要機場可以當場領，從其他機場入境的人之後再領取。官方提醒在留卡要隨身攜帶。",
                "must", "sij_immigration", "sij_residing"),
            tip("14 天內辦住民登錄，之後會拿到 My Number",
                "確定住址後 14 天內，要到居住地的市區町村公所辦理住民登錄。完成後會拿到 12 位數的個人編號（My Number），辦市政手續、申請打工和海外匯款等會用到。國民健康保險通常在同一個窗口一起辦。",
                "must", "sij_immigration", "sij_insurance"),
            tip("在日本打工要先申請許可",
                "學生身分原則上不能工作，但可以向入管局申請「資格外活動許可」。首次入境、確認停留超過 3 個月的人，可以在入境時於機場申請；入境後則向地方入管局申請。官方頁面沒有列每週工時上限，請向學校國際處確認。",
                "should", "sij_residing", "sij_immigration"),
            tip("出國旅行與再入境",
                "持有效護照和在留卡、一年內回到日本的話，不需要另外申請特別再入國許可；離境時要帶著在留卡，並勾選特別再入國許可的欄位。超過一年才回來，就要事先申請。",
                "should", "sij_residing"),
            tip("地址、學校與證件變更要申報，延長要提早",
                "姓名、國籍、學校變更，或在留卡遺失、破損，要向入管局申報；日本境內搬家、完成學業離開日本，則向市公所申報。需要延長居留要在期限屆滿前申請，通常在屆滿前三個月就可以提出。",
                "should", "sij_residing")],
        "health_insurance": [
            tip("國民健康保險：看病自付 30%",
                "在日本停留 3 個月以上的外國居民必須加入國民健康保險，住民登錄後到同一個市區町村公所辦理。看病時保險付 70%、自己付 30%。保費依前一年的收入（包含兼職）計算，收入低於一定門檻可以申請減免，但要先申報收入。單月醫療費超過自付上限的部分可以申請退款，住院前可以先申請限額證明。",
                "must", "sij_insurance"),
            tip("學生的意外與財產保險",
                "日本多數學校採用 Gakkensai（學生教育研究災害傷害保險），涵蓋上課、通勤與其他傷害；大學生協也有 Kyosai 互助方案。涵蓋的例子包括廚房失火、騎腳踏車撞傷別人、房間遭竊。入學時問清楚學校有沒有統一加入。",
                "should", "sij_insurance")],
        "housing": [
            tip("宿舍和公寓怎麼選",
                "學生宿舍租金較低，有些附家具電器，也比較容易交朋友，但名額有限、有門禁、設施共用；公寓比較自由，但家具和電器要自己買。",
                "should", "sij_accommodation"),
            tip("租金與租屋的初期費用",
                "官方引用 2023 年資料：全國平均月租約 41,000 日圓、東京約 57,000 日圓；東京的學生宿舍約 28,000 日圓，鄉下地方約 30,000–40,000 日圓。租公寓通常要先付敷金（相當於數個月房租的押金）和禮金，也常要保證人，學校人員可以擔任留學生的保證人。官方建議加入留學生綜合租屋保險。",
                "should", "sij_accommodation")],
        "payment": [
            tip("生活費大約多少",
                "日本學生支援機構 2023 年的調查顯示，私費留學生不含學費的每月生活費平均約 105,000 日圓，其中住宿全國平均 41,000 日圓、東京 57,000 日圓。大都市的租金和通勤費較高，離校園近的房子也比較難找。",
                "good_to_know", "sij_cost"),
            tip("開銀行帳戶要帶什麼，開了之後怎麼用",
                "開戶要帶在留卡和護照等證件，各金融機構要求的文件可能不同。銀行會確認姓名、住址、停留期間與在留資格。開戶後電費、瓦斯、水費和電話費都可以由帳戶自動扣款。住址、停留期間或在留資格有變，或遺失存摺和提款卡，都要通知銀行；離開日本前請結清帳戶。",
                "should", "fsa_bank"),
            tip("絕對不要賣或借出你的銀行帳戶",
                "把銀行帳戶交給別人，或幫別人處理來路不明的匯款，是違法的，嚴重時可能無法繼續待在日本、也無法再入境。不確定時先找學校商量。金融廳的使用者諮詢窗口是 0570-016811（IP 電話 03-5251-6811），平日 10:00–17:00，只提供日語；英文只受理電子郵件 equestion@fsa.go.jp。",
                "must", "fsa_bank")],
        "emergency": [
            tip("駐日代表處的緊急電話",
                "東京：從台灣撥 (81-80)1009-7179、(81-80)1009-7436，在日本境內直撥 080-1009-7179、080-1009-7436；大阪辦事處：日本境內 090-8794-4568，漫遊手機撥 +81-90-8794-4568。這些號碼專供遭逮捕或拘禁、重大犯罪受害、緊急就醫等急難使用。福岡、橫濱、那霸、札幌也各有自己的號碼，請看外交部頁面。",
                "must", "mofa_tw_japan")],
    },
}

KOREA = {
    "intro": "韓國的重點是入境後 90 天內的外國人登錄，之後手機月租、銀行等很多事都要用登錄證。健康保險的規則這幾年改過，一學期的交換生要不要加入沒有查到明確說法，所以請向學校與健保公團確認。以下整理自韓國政府的留學官方網站與 Korea.net，並標出了出處。",
    "topics": {
        "documents": [
            tip("入境後 90 天內要辦外國人登錄",
                "停留超過 90 天的人，要在入境後 90 天內辦外國人登錄。流程是備文件、在 HiKorea 網站線上預約、到所在地的出入境辦公室辦理。官方頁面列的文件有護照、申請書、照片、入學證明與結核檢查證明；實際要帶哪些，以學校與出入境辦公室的通知為準。",
                "must", "sik_residence"),
            tip("D-2、D-4 身分與延長、變更",
                "D-2 是學位課程學生，D-4 是語言研修生。要變更身分，必須在開始新的活動之前申請；要延長停留，必須在期限屆滿前申請。",
                "should", "sik_residence"),
            tip("搬家後 15 天內要向出入境辦公室申報",
                "搬家後 15 天內要向當地出入境辦公室申報新地址，逾期最高可罰 100 萬韓元。",
                "must", "sik_residence"),
            tip("打工要先取得許可",
                "學生打工要先向出入境辦公室取得許可，並備好僱傭契約和大學確認書。學位課程學生與語言研修生（滿 6 個月後才可申請）的規定不同，時數上限也依身分與韓語能力而異，請向學校國際處確認，不要先做再補。",
                "should", "sik_residence")],
        "health_insurance": [
            tip("國民健康保險（NHIS）：先向學校確認要不要加入",
                "韓國國民健康保險公團公告：從 2021 年 3 月 1 日起，國際學生可以加入國民健康保險。另外 Korea.net 報導，從 2024 年 4 月 3 日起，外籍人士原則上要在韓國居住滿 6 個月才能加入，其中 D-2（學位或交換學生）等簽證的家屬可以免除 6 個月的限制。"
                "一學期、不到 6 個月的交換生到底要不要加入，我沒有查到明確說明，請向合作校國際處與健保公團確認；在確認之前，先準備一份涵蓋就醫的旅遊或留學保險。",
                "must", "nhis_2021", "korea_net_nhi")],
        "phone_internet": [
            tip("手機：沒有登錄證先辦預付，月租要登錄證",
                "剛到、還沒有外國人登錄證的人，用護照可以辦預付方案；要辦月租方案需要登錄證，可能還要韓國的銀行帳戶或信用卡。三大電信業者是 SK Telecom、KT、LG U+，都有外語客服。這是 2019 年的報導，方案與規定可能已調整。",
                "should", "korea_net_phone")],
        "payment": [
            tip("銀行開戶要帶的東西與營業時間",
                "開戶要帶護照（或外國人登錄證）、印章或簽名，以及交易目的證明。銀行營業時間大多是 9:00–16:00。官方頁面也說明海外匯款一年內一定金額以內不用另外附文件（頁面寫的上限是 10 萬美元）。",
                "should", "sik_living"),
            tip("2025 年 3 月起可用行動外國人登錄證開戶",
                "Korea.net 報導：從 2025 年 3 月 21 日起，14 歲以上的外籍居民可以用行動居民登錄證（手機版外國人登錄證）開設銀行帳戶，第一階段有新韓、韓亞、iM、釜山、全北、濟州六家銀行，之後陸續擴大。",
                "good_to_know", "korea_net_bank")],
        "housing": [
            tip("韓國常見的住房類型",
                "官方頁面列出：大學宿舍（設施完善但隱私有限）、寄宿家庭（包含房間與餐食）、傳統租賃（付押金，租期結束全額退回）、傳貰（一次付大額押金，租期內不用月租）和月租（押金加每月租金）。頁面沒有列具體金額，請向學校與房東問清楚押金與月租再簽約。",
                "should", "sik_living")],
        "emergency": [
            tip("駐韓國台北代表部的緊急電話",
                "緊急電話 82-10-9080-2761，全年無休，專供車禍、搶劫、生命安全等急難使用；護照、簽證等一般領務請在上班時間找辦公室，不要撥這支。",
                "must", "mofa_tw_korea")],
    },
}

FRANCE = {
    "intro": "法國的重點是簽證種類（決定你抵達後要不要驗證、能不能領住房補助）、法國社會保險要自己上網註冊，以及 2026 年 7 月起住房補助對非歐盟學生的新限制。以下整理自 Campus France、法國教育部學生網站與家庭津貼局，並標出了出處；手機與銀行開戶沒有查到官方說明，所以沒有寫。",
    "topics": {
        "documents": [
            tip("學生長期簽證（VLS-TS）要在 3 個月內上網驗證",
                "Campus France 說明：拿到「學生」長期簽證兼居留證（VLS-TS）的人，要在抵達法國後 3 個月內，到內政部的 ANEF 網站線上驗證，才算有居留資格。驗證要準備電子郵件、簽證資訊、抵達日期、法國住址，以及付款用的銀行卡或電子印花；頁面（2026-08-12 更新）寫居留稅是 100 歐元，實際金額以 ANEF 頁面為準。"
                "超過 3 個月沒驗證，離開法國後再回來就必須重新申請簽證；前 3 個月可以自由出入法國。",
                "must", "cf_validate"),
            tip("如果拿到的是暫時長期簽證（VLS-T）",
                "Campus France 說明，「學生」暫時長期簽證 VLS-T 可停留 4 到 12 個月、不能延長，抵達後不用驗證，但不能工作、不能用 Visale 租屋擔保，也不能申請 CAF 住房補助。你拿到的是哪一種簽證，要看簽證上的註記，不確定就問合作校。這個頁面無法自動讀取，內容來自搜尋結果的摘要，請自己打開確認。",
                "should", "cf_vlst"),
            tip("CVEC：依協議到法國的交換生免繳",
                "法國的學生與校園生活費（CVEC）：依兩校之間的協議到法國交換的國際學生不用繳；其他學生要在註冊前繳費並取得收據，學校沒有收據就不能完成註冊。頁面寫的金額是 103 歐元，每年會調整。你是否需要先領免繳證明，請向法國合作校確認。",
                "must", "etu_cvec")],
        "health_insurance": [
            tip("法國社會保險：免費，但要自己上網註冊",
                "國際學生在法國社會保險的註冊是免費且強制的。拿到學校的入學證明後，到 etudiant-etranger.ameli.fr 線上註冊並上傳身分文件。社會保險只報銷約 60% 的醫療費用，官方強烈建議再買補充保險（mutuelle），並確認保單含學習與實習地點的民事責任。大學健康中心（SUMPPS）提供免費的避孕、檢測、疫苗與心理支援服務。",
                "must", "cf_health", "etu_social")],
        "housing": [
            tip("2026 年 7 月起：非歐盟學生領住房補助的條件變嚴",
                "法國家庭津貼局公告（2026-07-03）：從 2026 年 7 月 1 日起，持長期簽證或「繼續學習」居留的非歐盟學生，必須領有「社會救助大學獎學金」才能領個人住房補助（APL）；已經在領但不符新條件的人，補助從 2026 年 7 月起終止，7 月 1 日後才申請又不符條件的人不會被核准。"
                "也就是說，租房預算不要假設一定拿得到 APL。",
                "must", "caf_apl"),
            tip("租房要有擔保人：Visale 免費擔保",
                "私人租屋通常要法國人當擔保人。Visale 是免費的租金擔保：18–30 歲的學生可以申請，非歐盟學生需持有效學生簽證，須是正式註冊學生。頁面（2021-04-27）寫的租金上限是巴黎 800 歐元、其他地區 600 歐元（含管理費），金額可能已調整；到 visale.fr 申請，證明有效 6 個月，每年要重新申請。拿 VLS-T 的人不能用 Visale。",
                "should", "etu_visale", "cf_vlst")],
        "emergency": [
            tip("駐法國代表處的緊急電話",
                "緊急電話：(33) 680074994，在法國境內直撥 0680074994，專供車禍、搶劫、生命安全等急難使用，非急難請不要撥打。",
                "must", "mofa_tw_france")],
    },
}

USA = {
    "intro": "美國的重點是 I-20 與 SEVIS 費用的順序、入境時機，以及保險要自己負責（J-1 有最低標準）。以下整理自美國國土安全部的 Study in the States 與國務院，並標出了出處與頁面日期；簽證面談、手機、銀行與租屋沒有查到可讀的官方頁面，所以沒有寫。",
    "topics": {
        "documents": [
            tip("I-20：最多只能在開學前 30 天入境，要帶正本",
                "F 和 M 學生都需要 I-20。課程開始日前最多 30 天才能入境美國；入境時要帶著已簽名的 I-20 原件，不要放進託運行李。",
                "must", "dhs_i20"),
            tip("SEVIS I-901 費用：拿到 I-20 之後、拿簽證之前繳",
                "I-901 SEVIS 費用要在拿到 I-20 之後繳，並且要在美國國務院核發簽證之前完成。I-20 由學生與學校的指定官員（DSO）都簽名，18 歲以下要由家長簽。",
                "must", "dhs_i20"),
            tip("社會安全號碼（SSN）不是人人要辦",
                "只有獲准工作的 F、M 學生需要 SSN。辦駕照、學校註冊、買私人健康保險都不需要 SSN。要申請的話，抵達後要等 10 天，而且 SEVIS 記錄要處於有效狀態至少兩天。部分州要求辦駕照前先申請過 SSN 或拿到拒發證明。",
                "should", "dhs_ssn")],
        "health_insurance": [
            tip("F-1 學生要自己負責健康保險",
                "官方 FAQ 說明：F-1、M-1 學生有責任為自己和家人在美國求學期間購買健康保險。學校可能提供醫療保險，但要求和費用各校不同。入學前先問清楚學校有沒有強制或提供的方案。",
                "must", "dhs_faq"),
            tip("如果是 J-1 交換訪客：保險有最低標準",
                "美國國務院的規定（22 CFR 62.14）：J-1 交換訪客與家屬的保險至少要有每次事故或疾病 100,000 美元的醫療給付、25,000 美元的遺體遣返、50,000 美元的返國醫療撤送，且自付額不能超過 500 美元。你是 F-1 還是 J-1，看學校給你的文件（I-20 或 DS-2019）。",
                "must", "j1_state")],
        "transport": [
            tip("開車要拿州駕照，抵達後先等 10 天",
                "F、M 學生可以在美國開車，但要成功申請並取得州駕照。抵達後要等 10 天再申請，讓入境資料更新到政府系統。要準備全部簽名的 I-20、有效護照、簽證，以及居住證明（各州要求不同）；各州是否要 SSN 也不一樣，請向當地 DMV 和學校的 DSO 確認。",
                "should", "dhs_driving")],
        "safety_law": [
            tip("沒有許可不能打工",
                "F-1 學生要在校內外工作，需要指定學校官員或移民局的核准，官方明講美國政府非常嚴肅看待非法打工。要打工先問 DSO，不要先做再補。這個頁面是 2014 年的，細節請以學校 DSO 的說明為準。",
                "must", "dhs_benefits", "dhs_ssn")],
        "emergency": [
            tip("駐美國代表處的緊急電話",
                "華盛頓特區的駐美國代表處緊急電話是 (1-202) 669-0180，專供車禍、搶劫、生命安全等急難使用，非急難請不要撥打。各地辦事處（亞特蘭大、波士頓、芝加哥、檀香山、休士頓、洛杉磯、邁阿密、紐約、舊金山、西雅圖等）各有自己的緊急電話，請在外交部頁面查你所在地區的號碼並存進手機。",
                "must", "mofa_tw_usa")],
    },
}

DEEP_ADDITIONS = {"日本": JAPAN, "韓國": KOREA, "法國": FRANCE, "美國": USA}


def merge_deep(guide: dict, extra: dict) -> dict:
    """Put a country's deeper notes in front of the shared ones, topic by topic, in the usual topic order."""
    by_topic = {item["topic"]: list(item["tips"]) for item in guide["topics"]}
    for key, tips in extra["topics"].items():
        titles = {new["title"] for new in tips}
        by_topic[key] = [*tips, *[old for old in by_topic.get(key, []) if old["title"] not in titles]]
    guide["topics"] = [topic(key, *by_topic[key]) for key in TOPICS if key in by_topic]
    guide["intro"] = extra["intro"]
    return guide


# --------------------------------------------------------------------------------------------- build

HONG_KONG_DOCS = [
    tip("赴港澳要到陸委會網站另外登錄行程",
        "外交部的旅外動態登錄頁面註明：去大陸、香港、澳門的人要到陸委會網站另行登錄，不是登錄在外交部那一套。",
        "must", "boca_register", "mac_risk"),
    tip("看一下目的地目前的旅遊警示等級",
        "外交部把旅遊警示分成灰（提醒）、黃（注意）、橙（避免前往）、紅（儘速離境）四級。出發前和出發當週都查一次。",
        "should", "boca_warning"),
]

DEEP = {"大陸地區": CHINA}


def baseline(country: str) -> dict:
    numbers, note = EMERGENCY[country]
    documents = HONG_KONG_DOCS if country == "香港" else shared_documents(country)
    emergency = [
        tip(f"{country}的當地緊急電話", f"{numbers}。{note}".replace("。。", "。"), "must", "wiki_emergency"),
        *([tip("陸委會彙整的港澳緊急服務資訊", "香港的求助管道可參考陸委會整理的「陸港澳緊急服務資訊」，出發前存下來。", "should", "mac_emergency")] if country == "香港" else shared_emergency()),
    ]
    return {
        "country": country,
        "display_name": country,
        "intro": "這份是各國共通的基本提醒：簽證與入境、動態登錄、旅遊警示、緊急電話與電壓。更細的當地生活提醒（手機、付款、住宿登記）還在整理，會逐國補上。",
        "topics": [topic("documents", *documents), topic("packing_power", *shared_packing(country)), topic("emergency", *emergency)],
    }


def build() -> dict:
    guides: dict[str, dict] = {}
    for country in sorted(EMERGENCY):
        guides[country] = baseline(country)
        if country in DEEP_ADDITIONS:
            merge_deep(guides[country], DEEP_ADDITIONS[country])
    guides.update(DEEP)
    for guide in guides.values():
        guide.setdefault("review_status", "draft")
        guide["reviewers"] = []
        guide["last_checked"] = CHECKED
    return {"version": 1, "guides": dict(sorted(guides.items()))}


def main() -> None:
    payload = build()
    problems = validate_guides(payload)
    if problems:
        raise SystemExit("資料未通過驗證：\n- " + "\n- ".join(problems))
    GUIDES_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum(len(t["tips"]) for g in payload["guides"].values() for t in g["topics"])
    print(f"{len(payload['guides'])} 個國家、{total} 項提醒，已寫入 {GUIDES_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
