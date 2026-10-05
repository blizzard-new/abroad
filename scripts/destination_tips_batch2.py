"""Deep notes for ten more destinations, as plain data for ``build_destination_tips.py``.

德國、波蘭、越南、捷克、泰國、香港、印度、西班牙、瑞典、加拿大 — the ten countries with the most partner schools that did not have
deep notes yet. Pages were opened on 2026-10-05 (``CHECKED``). Each row is ``(title, detail, importance, source keys)``.

House rules, same as the first batch:
- a statement is only here if a page we opened supports it; pages that refused automated access are not cited for facts;
- where two sources disagreed (Frankfurt's emergency number, India's e-Visa list, a Canada summary about Taiwan passports) the
  tip says so or leaves the number out instead of picking one;
- what was not researched is named in each country's ``intro`` rather than filled from blogs.
"""
from __future__ import annotations

CHECKED = "2026-10-05"

SOURCES: dict[str, tuple[str, str]] = {
    # 德國
    "de_visa_study": ("德國在台協會：就讀德國高等學院之單國長期簽證（頁面更新 2026-05-01）", "https://taipei.diplo.de/tw-zh-tw/service/visa-einreise/2453292-2453292"),
    "de_visa_qa": ("德國在台協會：單國德國長期簽證 Q&A", "https://taipei.diplo.de/tw-zh-tw/service/visa-einreise/-/1695756"),
    "de_registration": ("Handbook Germany（德國聯邦政府移民資訊）：Registration", "https://handbookgermany.de/en/registration"),
    "de_daad_health": ("DAAD：Healthcare and Health Insurance", "https://www.daad.de/en/studying-in-germany/living-in-germany/health-insurance/"),
    "de_tk_health": ("TK 健保：無社會保險協定國家的國際學生需要哪種保險", "https://www.tk.de/en/become-a-member/join-tk/study-germany-health-insurance-enrollment-2154038"),
    "de_rundfunk": ("Rundfunkbeitrag（廣播電視費）：Informationen für Studierende", "https://www.rundfunkbeitrag.de/buergerinnen-und-buerger/informationen/informationen-fuer-studierende"),
    "de_bgb551": ("德國民法典 § 551：租賃押金", "https://www.gesetze-im-internet.de/bgb/__551.html"),
    "de_tkg172": ("德國電信法 § 172：預付卡的身分核驗", "https://www.gesetze-im-internet.de/tkg_2021/__172.html"),
    "mofa_tw_germany": ("外交部：駐德國代表處", "https://www.mofa.gov.tw/OverseasOffice_Content.aspx?n=168&sms=87&s=127&os=39"),
    # 波蘭
    "pl_taipei_d": ("波蘭駐台辦事處（Polish Office in Taipei）：D-type national visa", "https://poland.tw/web/taiwan/d-type-national-visa"),
    "pl_study_visa": ("Study in Poland（波蘭政府）：Visa and application", "https://study.gov.pl/visa-application"),
    "pl_mfa_visas": ("波蘭外交部：Visas", "https://www.gov.pl/web/diplomacy/visas"),
    "pl_study_health": ("Study in Poland（波蘭政府）：Health insurance", "https://study.gov.pl/health-insurance"),
    "pl_sip_health": ("Study in Poland：Health care", "https://www.studyinpoland.pl/en/practical-information/29-health-care"),
    "pl_accommodation": ("Study in Poland（波蘭政府）：Accommodation（頁面無日期）", "https://study.gov.pl/accommodation"),
    "pl_cost": ("Study in Poland（波蘭政府）：Cost of living in Poland（頁面無日期）", "https://study.gov.pl/cost-living-poland"),
    "pl_uke_prepaid": ("波蘭電子通訊局 UKE：預付卡登記（2016-07-25）", "https://archiwum.uke.gov.pl/aktualnosci/biezace-informacje/komunikaty/obowiazek-rejestracji-kart-prepaid,5966.html"),
    "pl_digital_prepaid": ("波蘭數位事務部：預付卡登記提醒（2017-01-25）", "https://www.gov.pl/web/cyfryzacja/ministerstwo-cyfryzacji-przypomina-o-obowiazku-rejestracji-kart-pre-paid"),
    "mofa_tw_poland": ("駐波蘭臺北代表處：聯絡方式", "https://www.roc-taiwan.org/pl_pl/post/41.html"),
    # 越南
    "vn_visa_notes": ("駐越南台北經濟文化辦事處：簽證及入境須知（頁面無日期）", "https://www.roc-taiwan.org/vn/post/16640.html"),
    "vn_visa_warning": ("駐越南台北經濟文化辦事處：申請越南簽證，請注意（頁面無日期）", "https://www.roc-taiwan.org/vn/post/27653.html"),
    "vn_sim": ("越南通訊主管機關 MIC（英文網站）：行動用戶生物辨識核驗（2026-04-10）", "https://beta-en.mic.gov.vn/biometric-verification-required-for-mobile-device-changes-from-april-15-197260410180048155.htm"),
    "cdc_vn": ("衛福部疾管署：國際旅遊處方箋－越南", "https://www.cdc.gov.tw/InternationalTravel/Print?cid=499&Type=full"),
    "vn_drivers": ("VietnamPlus：Requirements for foreign drivers, vehicles operating in Vietnam（2024-12-11）", "https://en.vietnamplus.vn/requirements-for-foreign-drivers-vehicles-operating-in-vietnam-post306494.vnp"),
    "mofa_tw_vietnam": ("外交部：駐越南代表處", "https://www.mofa.gov.tw/OverseasOffice_Content.aspx?n=168&sms=87&s=128&os=116"),
    # 捷克
    "cz_visa_info": ("捷克駐台北經濟文化辦事處：簽證資訊（頁面更新 2024-01-08）", "https://mzv.gov.cz/taipei/en/visas_and_consular_information/visa_information_for_foreigners/index.html"),
    "cz_study": ("捷克駐台北經濟文化辦事處：長期留學簽證及長期就學居留申請須知", "https://mzv.gov.cz/taipei/en/visas_and_consular_information/visa_information_for_foreigners/long_term_visa_and_residence_permits/long_term_residence_permit_for_the/index.html"),
    "cz_insurance": ("捷克外交部：長期簽證與長期居留須證明全面健康保險", "https://mzv.gov.cz/tirana/en/visa_and_consular_services/information_on_visas/obligation_to_prove_comprehensive_health.html"),
    "cz_pid": ("布拉格整合交通 PID：Discounts", "https://pid.cz/en/discounts/"),
    "mofa_tw_czech": ("外交部：駐捷克代表處", "https://www.mofa.gov.tw/OverseasOffice_Content.aspx?n=168&sms=87&s=42&os=42"),
    # 泰國
    "th_visa": ("駐泰國代表處：簽證及入境須知（頁面無日期，含 2026-09-15 起的新規）", "https://www.roc-taiwan.org/th/post/11266.html"),
    "th_ed_exchange": ("泰國貿易經濟辦事處：Non-immigrant ED（學校對學校短期交換 1–6 個月）", "https://tteo.thaiembassy.org/cn/publicservice/62386-non-immigrant-ed-%E5%AD%B8%E6%A0%A1%E5%B0%8D%E5%AD%B8%E6%A0%A1%E7%9F%AD%E6%9C%9F%E4%BA%A4%E6%8F%9B-1-6%E5%80%8B%E6%9C%88-%E4%B9%8B%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E7%B0%BD%E8%AD%89?page=5d7dc71915e39c072c004f10&menu=5d7dc71915e39c072c004f11"),
    "th_ed": ("泰國貿易經濟辦事處：Non-immigrant ED（留學簽證）", "https://tteo.thaiembassy.org/cn/publicservice/56233-non-immigrant-ed-%E7%95%99%E5%AD%B8%E7%B0%BD%E8%AD%89?page=5d7dc71915e39c072c004f10&menu=5d7dc71915e39c072c004f11"),
    "th_immigration": ("泰國移民局：Notification of staying in the Kingdom over 90 days（網站拒絕自動讀取，僅引用頁面名稱）", "https://www.immigration.go.th/en/?page_id=1666"),
    "cdc_th": ("衛福部疾管署：國際旅遊處方箋－泰國", "https://www.cdc.gov.tw/InternationalTravel/Print?cid=498&Type=full"),
    "mofa_tw_thailand": ("外交部：駐泰國代表處", "https://www.mofa.gov.tw/OverseasOffice_Content.aspx?n=168&sms=87&s=186&os=99"),
    # 香港
    "hk_prereg": ("香港入境事務處：台灣居民預辦入境登記須知 ID(C)1016（2024-06）", "https://www.immd.gov.hk/pdforms/ID(C)1016.pdf"),
    "hk_study_faq": ("香港入境事務處：就讀（常見問題）", "https://www.immd.gov.hk/hkt/faq/imm-policy-study.html"),
    "hk_study": ("香港入境事務處：學生", "https://www.immd.gov.hk/hkt/services/visas/study.html"),
    "hk_hkid": ("香港入境事務處：登記或補領香港身份證", "https://www.immd.gov.hk/hkt/services/hkid/reg_replace.html"),
    "hk_ha_fees": ("香港醫院管理局：醫療收費（2026-01-01 起）", "https://www.ha.org.hk/visitor/fees_and_charges.asp?lang=CHIB5"),
    "hk_ofca_sim": ("香港通訊事務管理局：電話智能卡實名登記常見問題", "https://www.ofca.gov.hk/tc/consumer_focus/guide/hot_topics/sim_registration/faq/index.html"),
    "hko_rain": ("香港天文台：暴雨警告系統", "https://www.hko.gov.hk/tc/wservice/warning/rainstor.htm"),
    "hko_typhoon": ("香港天文台：有關部門在颱風或暴雨警告下的安排", "https://www.weather.gov.hk/tc//informtc/advisorye.htm"),
    "teco_hk": ("台北經濟文化辦事處（香港）", "https://www.teco-hk.org"),
    # 印度
    "in_frro": ("Study in India（印度政府）：Onboarding & FRRO", "https://studyinindia.gov.in/Onboarding-&-FRRO"),
    "in_mea_frro": ("印度外交部：Checklist for FRRO/FRO Registration Formalities", "https://www.mea.gov.in/checklist-for-frro-fro-registration-formalities"),
    "in_evisa": ("印度政府 e-Visa 官網（資格頁）", "https://indianvisaonline.gov.in/evisa/tvoa.html"),
    "cdc_in": ("衛福部疾管署：國際旅遊處方箋－印度", "https://www.cdc.gov.tw/InternationalTravel/Print?cid=532&Type=full"),
    "mofa_tw_india": ("外交部：駐印度代表處", "https://www.mofa.gov.tw/OverseasOffice_Content.aspx?n=168&sms=87&s=30&os=15"),
    "roc_india": ("駐印度台北經濟文化中心：地址、電話及上班時間", "https://www.roc-taiwan.org/in/post/413.html"),
    # 西班牙
    "es_visa_study": ("西班牙外交部：Visados Nacionales－Visado de estudios（台北領事處）", "https://www.exteriores.gob.es/en/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Taiw%C3%A1n&scd=188&scca=Visados&scs=Visados+Nacionales+-+Visado+de+estudios"),
    "es_tie": ("西班牙外交部：Foreigner Identity Card (TIE)", "https://www.exteriores.gob.es/Embajadas/ottawa/en/ServiciosConsulares/Paginas/Foreigner-Identity-Card-(TIE).aspx"),
    "es_padron": ("西班牙國家統計局 INE：Padrón Municipal 法規", "https://idapadron.ine.es/repositorio/legislacion/A2301vol.htm"),
    "es_taipei_health": ("西班牙駐台北領事處：教育與衛生", "https://www.exteriores.gob.es/Consulados/taipei/es/VajarA/Paginas/Educacion-y-Sanidad.aspx"),
    "mofa_tw_spain": ("外交部：駐西班牙代表處", "https://www.mofa.gov.tw/OverseasOffice_Content.aspx?n=168&sms=87&s=107&os=113"),
    # 瑞典
    "se_migration": ("瑞典移民局：Apply for a residence permit for studies at higher education", "https://www.migrationsverket.se/en/you-want-to-apply/study/higher-education.html"),
    "se_tax": ("瑞典稅務局：Coordination numbers", "https://www.skatteverket.se/servicelankar/otherlanguages/englishengelska/individualsandemployees/coordinationnumbers.4.1657ce2817f5a993c3a7d2a.html"),
    "mofa_tw_sweden": ("外交部：駐瑞典代表處", "https://www.mofa.gov.tw/OverseasOffice_Content.aspx?n=168&sms=87&s=171&os=93"),
    # 加拿大
    "ca_no_permit": ("加拿大政府：Study permit－Who can study without a permit（頁面日期 2026-09-09）", "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/eligibility/study-without-permit.html"),
    "ca_eta_guide": ("加拿大移民部 IRCC：eTA 申請指南（PDF）", "https://www.canada.ca/content/dam/ircc/documents/pdf/english/eta/english.pdf"),
    "ca_eta_faq": ("加拿大移民部 IRCC：免簽國家申請學習或工作許可時需要 eTA 嗎", "https://ircc.canada.ca/English/helpcentre/answer.asp?qnum=1051&top=16%2F"),
    "ca_apply": ("加拿大政府：Study permit－How to apply（頁面日期 2026-09-02）", "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/apply.html"),
    "ca_work": ("加拿大政府：Work off campus as an international student（頁面日期 2026-04-15）", "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work/work-off-campus.html"),
    "ca_educanada": ("EduCanada：Canadian health care（修改日期 2024-12-24）", "https://www.educanada.ca/study-plan-etudes/before-avant/health-care-assurance-maladie.aspx?lang=eng"),
    "ca_bc_health": ("卑詩省政府：Health fee for international students（2024-01-08）", "https://www2.gov.bc.ca/gov/content/health/accessing-health-care/health-fee-international-students"),
    "mofa_tw_canada": ("外交部：駐加拿大代表處（渥太華）", "https://www.mofa.gov.tw/OverseasOffice_Content.aspx?n=168&sms=87&s=51&os=38"),
    "mofa_tw_vancouver": ("外交部：駐溫哥華辦事處", "https://www.mofa.gov.tw/OverseasOffice_Content.aspx?n=168&sms=87&s=51&os=30"),
    "roc_canada_emergency": ("駐加拿大台北經濟文化代表處：急難救助", "https://www.roc-taiwan.org/ca/post/23.html"),
}

COUNTRIES: dict[str, dict] = {}

# --------------------------------------------------------------------------------------------- 德國
COUNTRIES["德國"] = {
    "intro": "德國的重點是：台灣護照要先辦簽證才能入境讀書、入境後兩週內辦住址登記、一定要有被接受的健康保險，以及廣播費和預付卡這些容易漏掉的小事。以下整理自德國在台協會、德國聯邦政府的移民資訊網站、DAAD、保險公司的留學生說明與法條，並標出出處。學生票、宿舍申請時程和銀行開戶沒有查到可以打開的官方頁面，所以沒有寫。",
    "topics": {
        "documents": [
            ("台灣護照要先辦簽證，才能入境德國讀書",
             "德國在台協會的頁面（2026 年 5 月 1 日更新）說，澳洲、加拿大、以色列、日本、紐西蘭、南韓和美國公民可以入境後再申請居留，其他人入境德國前要先取得簽證；台灣不在這份例外名單裡。自 2025 年起，學生簽證一律先在 Auslandsportal 線上系統申請。頁面寫完整申請的處理時間大約 2 到 3 週，案情較複雜會更久，所以拿到入學許可就開始準備。",
             "must", ("de_visa_study", "de_visa_qa")),
            ("簽證要備的文件與財力證明",
             "該頁面列出的文件有：有效護照、德國高等學校的入學許可、德文或英文的健康保險證明、護照影本與證件照、語言能力證明，以及（交換學生）成績單。財力證明要達每月至少 992 歐元，做法是開限制提領帳戶（Sperrkonto）並存入至少 11,904 歐元，或提出政府獎學金證明。交換生實際要哪些，以合作校與德國在台協會的最新說明為準。",
             "must", ("de_visa_study",)),
            ("簽證效期是 90 天或 6 個月，入境後還要申請長期居留證",
             "德國在台協會核發的學生簽證效期是 90 天或 6 個月，入境後要再申請長期居留證，拿到簽證不是結束。居留證在哪裡辦、要不要先預約，請向合作校國際處確認。",
             "must", ("de_visa_study",)),
            ("打工有上限：一年最多 120 個全天或 240 個半天",
             "同一頁面寫，持學生簽證且在高等學校註冊後可以工作或當學生工讀，一年合計最多 120 個全天或 240 個半天。不要超過這個上限，排班前先算好天數。",
             "should", ("de_visa_study",)),
            ("免簽入境只適合短期語言課",
             "德國在台協會的 Q&A 寫，台灣護照的免簽規定並不禁止報名德國的語言課程，但半年內最多 90 天；打算長期停留就必須申請長期簽證。所以免簽入境不能拿來當長期留學的入境方式。",
             "good_to_know", ("de_visa_qa",)),
        ],
        "housing": [
            ("搬進去後 2 週內要辦住址登記（Anmeldung）",
             "德國聯邦政府的移民資訊網站 Handbook Germany 寫：搬入新住址後 2 週內，要到居住地的居民登記處（Bürgeramt 或 Einwohnermeldeamt）登記。要帶護照（與居留許可）、登記表，以及房東的書面確認（Wohnungsgeberbestätigung）；只有租約不夠，房東應在 2 週內提供這份確認。有些邦可以線上登記，但第一次登記必須本人到場。離開德國時要辦註銷（Abmeldung），否則健保與廣播費之類的義務會繼續。",
             "must", ("de_registration",)),
            ("押金最多三個月的淨租金",
             "德國民法 § 551 規定，住宅租賃的押金最高是 3 個月的租金（不含以包幹或預付形式列出的雜費）；承租人有權分 3 期等額付款，第一期在租期開始時付。房東要把押金與自己的財產分開存放，利息屬於承租人，不過學生與青年宿舍不必付息。房東要求的金額超過上限，就拿這條去談。",
             "should", ("de_bgb551",)),
        ],
        "payment": [
            ("廣播電視費：每戶每月 18.36 歐元",
             "Rundfunkbeitrag 是每戶（不是每人）每月 18.36 歐元。合租時只要有一位成年住戶登記並繳費，其他人可以退登記，所以搬進合租房先問室友誰在繳。留學生因為申請居留時要證明財力，通常不屬於可以免繳的困難案例；領德國 BAföG 學生補助的人才有一般的免繳申請。",
             "should", ("de_rundfunk",)),
        ],
        "health_insurance": [
            ("沒有被接受的健康保險，簽證與註冊都過不了",
             "DAAD 說德國人人都要有健康保險，留學生要在註冊或申請簽證時證明自己的保險等同德國標準；簽證文件清單也要求德文或英文版的健康保險證明。TK 健保也寫，來自沒有社會保險協定國家的學生，沒有有效保險就不能在學校註冊。台灣的全民健保能不能被接受，我沒有查到說明，請不要假設可以，先問合作校國際處與德國在台協會。",
             "must", ("de_daad_health", "de_tk_health", "de_visa_study")),
            ("法定保險的學生費率，以及私人保險的陷阱",
             "DAAD 說 30 歲以下的學生可以用優惠費率，每月約 120–130 歐元，滿 30 歲後保費高很多。私人保險不一定被學校接受，而且選了私人保險之後，就無法再改回法定保險。有帶薪實習或兼職的人必須有德國的保險，母國保險不夠。",
             "should", ("de_daad_health",)),
        ],
        "phone_internet": [
            ("買預付卡要通過身分核驗",
             "德國電信法 § 172 要求預付卡業者在啟用前核驗用戶身分，可接受的證件包括護照與居留許可，也可以用法律認可的其他驗證方式。所以買 SIM 卡時帶護照，卡要完成身分驗證才會啟用。",
             "should", ("de_tkg172",)),
        ],
        "emergency": [
            ("駐德國代表處（柏林）的緊急電話",
             "專供急病、災難、遭搶騙、被捕等急難使用：從海外撥 +49-171 3898257，在德國境內撥 0171-3898257；非急難事件請在上班時間聯絡領務組。法蘭克福、漢堡、慕尼黑辦事處各有自己的緊急號碼，請直接看外交部頁面；我在不同來源讀到的法蘭克福號碼不一致，所以這裡不放。",
             "must", ("mofa_tw_germany",)),
        ],
    },
}

# --------------------------------------------------------------------------------------------- 波蘭
COUNTRIES["波蘭"] = {
    "intro": "波蘭的重點是：停留超過 90 天要先辦 D 簽證（要本人到波蘭駐台辦事處送件）、非歐盟學生要辦居留卡、要自己有保險。以下整理自波蘭駐台辦事處、波蘭政府的留學網站與電子通訊局，並標出出處。宿舍與生活費的頁面沒有日期，只當量級參考；銀行、BLIK 行動支付和學生交通折扣沒有查到可靠的官方說明，所以沒有寫。",
    "topics": {
        "documents": [
            ("停留超過 90 天要先辦 D 簽證，而且要本人到台北送件",
             "波蘭駐台辦事處的頁面說，D 簽證最長一年，持有人也可以在其他申根國停留 90/180 天。簽證申請必須本人到辦事處（台北市基隆路一段 333 號 TWTC/ITB 1601-1602）送件，預約要走 e-konsulat 系統。最早可以在出發前 6 個月送件，原則上最晚在出發前 15 個曆日；頁面寫審核期是 15 個曆日，最長可到 45 日，所以不要卡在最後兩週。",
             "must", ("pl_taipei_d",)),
            ("簽證費用與保險門檻",
             "頁面寫申請費為新台幣 7,492 元（現金），不退費，不論核准與否。需要的醫療旅遊保險，保額不得低於 30,000 歐元；波蘭外交部的頁面另寫，也可以是符合波蘭公共資金健保規定的保險。金額會調整，辦理前再看一次頁面。",
             "should", ("pl_taipei_d", "pl_mfa_visas")),
            ("非歐盟學生要辦居留卡（karta pobytu）",
             "波蘭政府的留學網站寫，每位非歐盟學生都要辦居留卡：第一次核發 15 個月，之後可延長，最長 3 年且不超過學程。申請費頁面寫 390 波蘭茲羅提，要在簽證到期前向當地省政府辦公室（Voivodship Office）遞件。只讀一學期的交換生要不要辦、何時辦，頁面沒有說明，請問合作校國際處。",
             "should", ("pl_study_visa",)),
        ],
        "health_insurance": [
            ("非歐盟學生要自己有保險",
             "波蘭留學網站建議非歐盟學生在出發前先買國際醫療保險；簽證要求的保額至少 30,000 歐元。替代做法是和國家健保署（NFZ）簽自願健保合約，約每月 15 歐元，之後可以使用學校的醫療中心。另外可以自費加買意外險。私人診所的門診大約 80–150 茲羅提。",
             "must", ("pl_study_health", "pl_sip_health")),
        ],
        "housing": [
            ("宿舍與租房的價格量級",
             "波蘭政府留學網站的頁面（沒有標日期）寫：宿舍雙人房每月約 60–80 歐元，單人房約 100–150 歐元；私人出租的房間約 150–200 歐元，押金約一個月租金；華沙的獨立公寓約 300 歐元起。另一頁寫學生的月生活費最低約 1,500 茲羅提，其中宿舍 400–600 茲羅提、大眾運輸 50–60 茲羅提。兩頁都沒有日期，物價會變，只能當量級參考，實際以合作校的宿舍公告為準。",
             "good_to_know", ("pl_accommodation", "pl_cost")),
        ],
        "phone_internet": [
            ("預付卡要實名登記",
             "波蘭電子通訊局（UKE）的說明：預付卡要本人持身分證或護照登記，掃描檔或影本不被接受。2016 年 7 月 25 日前啟用的舊卡，登記期限是 2017 年 2 月 1 日，沒登記的會被停用。所以買 SIM 卡時要帶護照到門市。",
             "should", ("pl_uke_prepaid", "pl_digital_prepaid")),
        ],
        "emergency": [
            ("駐波蘭臺北代表處的緊急電話",
             "(48) 668-027-574，專供急難使用；一般領務請在上班時間打辦公室電話 (48) 22-213-0060，領事部門的時段頁面寫週一到週五 09:00–12:00。代表處在華沙。",
             "must", ("mofa_tw_poland",)),
        ],
    },
}

# --------------------------------------------------------------------------------------------- 越南
COUNTRIES["越南"] = {
    "intro": "越南的重點是：電子簽證資料要一字不差、住宿要向公安登記、手機卡要通過生物辨識核驗，以及蚊媒疾病和騎機車的風險。以下整理自駐越南代表處、越南政府網站與疾管署，並標出出處。越南的法條與移民局網站打不開，所以住宿申報的時限、臨時居留證，和台灣駕照能不能騎車這三件事，我沒有寫確定的說法，請向合作校與當地確認。",
    "topics": {
        "documents": [
            ("電子簽證的資料錯一個字，都可能被拒絕入境",
             "駐越南代表處提醒，近日有數起國人因電子簽證問題被越南海關拒絕入境；簽證資訊有誤，海關可以依法拒絕入境並遣返。申請時請確認姓名、生日、護照號碼、簽證效期都正確，收到電子簽證後再核對一次。官方申請網站是 evisa.gov.vn，別輕信網路廣告，要找旅行社就選有信譽的。電子簽證約 3–7 個工作天。",
             "must", ("vn_visa_warning", "vn_visa_notes")),
            ("讀書相關的簽證類別（DH）",
             "代表處的頁面列出的簽證類別裡，DH 是來越南實習或學習用，效期不超過 1 年，而且簽證效期要比護照效期至少短 30 天。越南簽證的相關規定向越南駐台北經濟文化辦事處查詢（台北市松江路 65 號 3 樓，(02) 2516-6626）。交換生到底要辦電子簽證還是 DH 簽證，我沒有查到官方說明，請問合作校國際處。",
             "should", ("vn_visa_notes",)),
            ("入境前三天的線上申報，和現金申報門檻",
             "越南試辦入境申報（PAI），網站是 prearrival.immigration.gov.vn，頁面建議入境前三天完成。攜帶外幣超過 5,000 美元或越盾超過 1,500 萬要申報；黃金塊不能帶，18K 金飾品超過 300 公克也要申報。",
             "good_to_know", ("vn_visa_notes",)),
        ],
        "housing": [
            ("住宿一定要向公安申報；租民宅要透過房東",
             "駐越南代表處的頁面寫，外國人住民宅，須透過房東向當地公安局申報；頁面也提醒，外國人與房東若不是夫妻關係，必須住飯店、旅館或旅社，違反會被處罰。租屋前先向學校問清楚能住哪些地方、誰負責申報。申報的時限頁面沒有寫，我也沒能打開法條確認，所以不寫小時數。",
             "must", ("vn_visa_notes",)),
        ],
        "phone_internet": [
            ("手機卡自 2026 年 4 月 15 日起要通過生物辨識核驗",
             "越南通訊主管機關的英文網站（2026 年 4 月 10 日）說，從 4 月 15 日起，行動用戶要核驗證件號碼、姓名、生日與臉部生物特徵；換手機會被偵測到，業者會暫停外撥，要在 30 天內完成臉部重新驗證，否則服務會全部停掉。可以用 VNeID、業者 App 或到門市辦。那篇文章講的是越南公民用身分證號的規則，沒有寫外國護照持有人怎麼辦，所以買卡時依門市要求辦，換手機前先問業者。",
             "should", ("vn_sim",)),
        ],
        "health_insurance": [
            ("出發前要評估的疫苗與蚊媒疾病",
             "疾管署的越南旅遊處方箋（涵蓋到 2026 年 9 月 29 日的疫情資料）建議：A 型肝炎疫苗（當地飲食與飲水有傳染風險）；日本腦炎疫苗在行程達一個月以上或常去農村時建議；狂犬病疫苗給有動物接觸風險的人，要提早一個月諮詢；麻疹與德國麻疹的 MMR 疫苗；傷寒疫苗給會去偏遠或衛生條件差地區的人。蚊媒疾病有登革熱、日本腦炎、屈公病、瘧疾和茲卡；全境有瘧疾風險，但都市中心、紅河與湄公河三角洲除外。出發前先到旅遊醫學門診評估。",
             "must", ("cdc_vn",)),
            ("防蚊、飲水與動物接觸",
             "疾管署建議：穿淺色長袖長褲、包鞋與長襪，使用含 DEET、派卡瑞丁或 IR3535 的防蚊劑，住有空調或紗窗的房子；不吃未煮熟的食物（沙拉、生海鮮、半熟肉），只喝包裝完整或確認煮沸過的水，少碰冰品與含冰飲料；不要逗弄或餵食蝙蝠與哺乳動物，被咬或被抓要立刻用大量肥皂水沖洗 15 分鐘；避開活禽市場。回台後 21 天內有不適要就醫，並告知旅遊史。",
             "should", ("cdc_vn",)),
        ],
        "transport": [
            ("騎機車與駕照：先別假設台灣駕照能用",
             "VietnamPlus（2024 年 12 月 11 日）寫，外國駕駛要有適用該車種的駕照，並能出示護照、駕照、在越南的居留文件、車輛登記與強制責任險。那篇文章沒有說台灣駕照或台灣核發的國際駕照能不能在越南合法騎車，我也沒查到官方說明，所以請不要假設可以；租車、買車之前先向學校與當地業者問清楚。",
             "must", ("vn_drivers",)),
        ],
        "emergency": [
            ("駐越南代表處的緊急電話",
             "河內：從海外撥 +84-913219986，越南境內撥 0913219986；胡志明市辦事處：+84-903927019，境內 0903-927019。專供車禍、搶劫、危及生命等急難；一般護照、簽證請在上班時間打辦公室電話。",
             "must", ("mofa_tw_vietnam",)),
        ],
    },
}

# --------------------------------------------------------------------------------------------- 捷克
COUNTRIES["捷克"] = {
    "intro": "捷克的重點是：超過 90 天要先在台北辦簽證、抵達後 3 個工作日內向外事警察報到、保險要符合簽證規定。以下整理自捷克駐台北經濟文化辦事處、捷克外交部與布拉格交通局，並標出出處。辦事處的就學簽證頁面引用的是 2008、2010 年的舊文件，金額與期限可能已經改了；捷克的手機、租屋和銀行沒有查到可靠的官方說明，所以沒有寫。",
    "topics": {
        "documents": [
            ("超過 90 天要先辦簽證，在台北預約送件",
             "捷克駐台北經濟文化辦事處的頁面（更新於 2024 年 1 月 8 日）說，持有身分證字號的台灣護照可以免簽停留最多 90 天；停留超過 90 天，任何台灣護照都要辦簽證。辦事處週一到週四 8:30–16:30，只接受預約；簽證受理時段是週一到週四 9:00–12:00。預約寄信到 Taipei.Visa@mzv.gov.cz，通常 3–5 天內回信。",
             "must", ("cz_visa_info",)),
            ("就學簽證要備的文件，審理期最長要 60 到 90 天",
             "辦事處的頁面列出：申請表；護照（效期要超過停留期至少 3 個月）；入學許可；財力證明至少新台幣 180,000 元（信用卡對帳單與同一家銀行的存款餘額）；雙方簽名的住宿合約；經公證與外交部認證並附捷克文翻譯的無犯罪紀錄；2 張照片；文件須是 180 天內核發的正本或公證本。頁面把學程分三種：教育部認證學程的長期簽證、超過 6 個月的長期居留，以及未經認證的課程（例如語言課程）適用的「其他目的」長期簽證。標準審理期：就學簽證 60 天，其他目的 90 天。交換生會被歸到哪一種，頁面沒有明說，請直接問辦事處。這些金額與期限來自一個引用舊文件的頁面，請以辦事處最新公告為準。",
             "must", ("cz_study",)),
            ("抵達後 3 個工作日內要向外事警察報到",
             "辦事處的頁面寫，抵達後 3 個工作日內要向外事警察報到；簽證效期最長 180 天，可到移民局申請延長；申請居留者要到移民局辦理，居留證在 60 天內核發。",
             "must", ("cz_study",)),
        ],
        "health_insurance": [
            ("保險要涵蓋全程，且要符合捷克的規定",
             "辦事處的頁面說，領取簽證時要出示涵蓋整個就學期間的健康保險合約。捷克外交部另寫：自 2021 年 8 月 2 日起，停留超過 90 天的外國人，入境後 90 天內要有涵蓋全面醫療的保險，而且 2021 年 8 月 2 日到 2026 年 8 月 2 日這五年，只能向 Pojišťovna VZP 投保。這個獨家期限已經過了，之後的規定我沒查到，請向辦事處與合作校確認，買保險前先問清楚簽證接不接受那張保單。",
             "must", ("cz_study", "cz_insurance")),
        ],
        "transport": [
            ("布拉格的學生月票折扣",
             "布拉格整合交通（PID）的頁面寫：18–26 歲、全日制學生可以買折扣的長期票（月票、季票、年票）；在國外就讀的學生只要出示有效的 ISIC 就能享有折扣。單程票沒有學生折扣。布拉格以外的區域，18–26 歲持 ISIC 所有票種都是半價。",
             "good_to_know", ("cz_pid",)),
        ],
        "emergency": [
            ("駐捷克代表處的緊急電話",
             "重大急難：從海外撥 +(420) 603-166-707，捷克境內撥 603-166-707；一般護照、簽證請在上班時間打辦公室電話 +(420) 233-320-606。頁面也提醒當地可撥 112（歐盟通用，有英、捷、德語服務）、救護 155、報警 158。",
             "must", ("mofa_tw_czech",)),
        ],
    },
}

# --------------------------------------------------------------------------------------------- 泰國
COUNTRIES["泰國"] = {
    "intro": "泰國的重點是：2026 年 9 月 15 日起免簽 30 天、入境前要先申請電子入境卡 TDAC、交換生有專屬的 ED 簽證，以及逾期停留的罰則很重。以下整理自駐泰國代表處、泰國貿易經濟辦事處與疾管署，並標出出處。泰國移民局網站拒絕自動讀取，住宿通報與 90 天通報的細節沒有寫；手機卡、付款與交通沒有查到可靠的官方說明，所以也沒有寫。",
    "topics": {
        "documents": [
            ("2026 年 9 月 15 日起免簽 30 天，但入境前要做的事不少",
             "駐泰國代表處的頁面寫，自 2026 年 9 月 15 日起，持台灣護照入境泰國每次可免簽停留不超過 30 天。入境需要：效期剩 6 個月以上的護照、回程機票證明、訂房或住宿聯絡資料、足夠的財力（每人至少 2 萬泰銖現金，每個家庭至少 4 萬），以及完成泰國電子入境卡（TDAC，自 2025 年 5 月 1 日起施行，要在抵泰前 72 小時內線上申請）。停留超過 30 天要事先在網路上申請對應事由的電子簽證（eVisa）。",
             "must", ("th_visa",)),
            ("交換生有專屬的 ED 簽證（學校對學校、1–6 個月）",
             "泰國貿易經濟辦事處有一頁專門講「學校對學校短期交換（1–6 個月）」的 Non-immigrant ED 簽證。大學以上要備：護照（效期 6 個月以上）、身分證影本、2 吋照片、移民署的入出國日期證明（1 個月內）、泰國學校致貿易經濟辦事處的信（1 個月內）、泰國學校的執照影本、台灣學校的保證函（1 個月內）與台灣學校的執照影本。簽證費新台幣 2,300 元，不退費；效期 3 個月，停留不超過 90 天。入境時移民局可能要求證明資金（個人 2 萬泰銖、家庭 4 萬）。需要台灣學校出保證函，所以先找合作校國際處。",
             "must", ("th_ed_exchange",)),
            ("正式學位的 ED 簽證：存款證明與停留期限",
             "辦事處另有一頁講留學用的 Non-immigrant ED 簽證：大學以上要英文存款證明，並附三個月以上的存款明細，金額不低於新台幣 200,000 元；單次簽證效期 3 個月、停留不超過 90 天。頁面特別寫，簽證有效期不等於在泰國的停留期限。簽證費新台幣 2,300 元，不論核發與否都不退。",
             "should", ("th_ed",)),
            ("逾期停留的罰則很重",
             "駐泰國代表處的頁面寫：逾期停留每天罰 500 銖（最高 20,000 銖）；逾期 90 天以上到一年內被查獲，5 年內禁止再入境；逾期超過一年，10 年內禁止再入境。簽證或停留期限到之前就要處理延長，不要讓它過期。",
             "must", ("th_visa",)),
            ("住宿通報與 90 天通報：我沒能讀到細節",
             "泰國移民局有針對外國人的住宿通報（TM.30）和停留超過 90 天的定期通報（TM.47）。移民局的網站拒絕自動讀取，所以我沒有寫誰要通報、期限與罰款；請向合作校國際處問你需不需要辦、由誰辦，並以移民局頁面為準。",
             "good_to_know", ("th_immigration",)),
        ],
        "health_insurance": [
            ("出發前要評估的疫苗",
             "疾管署的泰國旅遊處方箋（疫情資料涵蓋到 2026 年 9 月）建議：A 型肝炎疫苗（當地飲食與飲水有傳染風險）；日本腦炎疫苗在行程達一個月以上或常去農村時建議；狂犬病疫苗給有動物接觸風險的人，要提早一個月諮詢；MMR；傷寒疫苗給會去偏遠或衛生條件差地區的人。出發前先到旅遊醫學門診評估。",
             "must", ("cdc_th",)),
            ("蚊媒疾病、飲水與動物接觸",
             "泰國的蚊媒疾病有日本腦炎、瘧疾、登革熱、茲卡與屈公病。疾管署建議穿淺色長袖長褲、包鞋與長襪，使用含 DEET 或派卡瑞丁的防蚊劑，住有空調或紗窗的房子；不吃未煮熟的食物，水果自己洗過削皮，只喝包裝完整或煮沸過的水，避開冰品；不要逗弄或餵食哺乳動物，避開蝙蝠洞窟與活禽市場，被咬或被抓用肥皂水沖洗 15 分鐘後立刻就醫；也要避免接觸淡水（有血吸蟲風險）。回台後 21 天內有症狀要就醫，並告知旅遊史。",
             "should", ("cdc_th",)),
        ],
        "emergency": [
            ("駐泰國代表處的緊急電話",
             "從海外撥 +66-81-6664006，泰國境內撥 081-6664006，專供在海外遇到緊急危難使用；一般護照、簽證請在上班時間打辦公室電話 +66-2-119-3555。",
             "must", ("mofa_tw_thailand",)),
        ],
    },
}

# --------------------------------------------------------------------------------------------- 香港
COUNTRIES["香港"] = {
    "intro": "香港的重點是：用「台灣居民預辦入境登記」入境的人不能就讀，交換生要另外辦就讀的入境許可；停留超過 180 天要登記香港身份證；沒有保險的話公立醫院的收費非常高。以下整理自香港入境事務處、醫院管理局、通訊事務管理局、天文台與駐港辦事處，並標出出處。陸委會的頁面拒絕自動讀取，所以港澳風險與緊急服務只放陸委會頁面的名稱；租屋、銀行與交通沒有查到可靠的官方說明，所以沒有寫。",
    "topics": {
        "documents": [
            ("不能用「台灣居民預辦入境登記」入境讀書",
             "入境處的須知（ID(C)1016，2024 年 6 月）說，預辦入境登記是給「來港旅遊」的，免費，有效期兩個月，可入境兩次，每次最多 30 天，而且要持有效期不少於 6 個月的回台證件。須知第 18 段明確寫：獲准以訪客身份入境的人，不得在香港就讀於學校、大學或其他教育機構。所以交換生不能拿這個入境，要另外辦就讀的入境許可。",
             "must", ("hk_prereg",)),
            ("就讀入境許可怎麼辦",
             "入境處的頁面寫：學生本人遞表格 ID 995A，本地保證人（通常是學校）遞 ID 995B；一般約需六星期，6 到 8 月旺季可能更久；台灣居民要附戶籍謄本與身分證影本。台灣學生獲批後，由保證人向入境處的「其他簽證及入境許可組」領取單次入境許可證，再交給學生；入境後要申請「多次入境許可證」並轉移學生逗留條件。要延長逗留，請在期滿前四個星期內申請。",
             "must", ("hk_study", "hk_study_faq")),
            ("學生在香港能不能工作",
             "入境處的頁面寫，一般非本地學生不得做有薪或無薪的僱傭工作；全日制學士以上課程（至少一學年）的學生，才可以做相關實習與校內兼職（學期中每週最多 20 小時），且要經學校安排並獲批准。交換生是否符合這些條件，請問合作校。",
             "should", ("hk_study", "hk_study_faq")),
        ],
        "housing": [
            ("停留超過 180 天，抵港 30 天內要登記香港身份證",
             "入境處的頁面寫：獲准在香港逗留超過 180 天的人，要在抵港後 30 天內登記領取香港身份證。逗留不超過 180 天的交換生不在此列；你的逗留期是多久，以入境許可上的為準。",
             "should", ("hk_hkid",)),
        ],
        "health_insurance": [
            ("沒有保險，公立醫院的收費非常高",
             "醫院管理局的頁面（2026 年 1 月 1 日起）列出非符合資格人士的收費：急症室每次 2,100 港元；普通科醫院住院每天 7,400 港元；門診首次診治每次 1,090–2,580 港元。你是否適用較低的符合資格人士收費，要看醫管局的定義，請不要假設。出發前先買涵蓋住院與急診的保險。",
             "must", ("hk_ha_fees",)),
        ],
        "phone_internet": [
            ("買儲值卡要實名登記",
             "通訊事務管理局的常見問題說，沒有香港身份證的人，可以用有效的旅遊證件或護照做實名登記；沒有在期限內完成登記，儲值卡的登記會被取消；2022 年 3 月 1 日後的月費服務，啟用前就要完成登記。",
             "should", ("hk_ofca_sim",)),
        ],
        "safety_law": [
            ("颱風與暴雨警告：八號信號時學校停課，黑雨要留在室內",
             "香港天文台的說明：發出八號或以上的熱帶氣旋警告信號時，教育局會宣布所有學校停課一天，部分公共交通可能很快停止服務。暴雨警告分三級：黃色是每小時雨量超過 30 毫米，紅色超過 50 毫米，黑色超過 70 毫米；黑色暴雨時要留在室內安全的地方，僱主也不應要求員工上班。",
             "should", ("hko_typhoon", "hko_rain")),
        ],
        "emergency": [
            ("台北經濟文化辦事處（香港）的 24 小時緊急電話",
             "852-61439012；辦公室電話 852-25258642，地址在香港灣仔港灣道 18 號中環廣場 49 樓 4907 室。",
             "must", ("teco_hk",)),
        ],
    },
}

# --------------------------------------------------------------------------------------------- 印度
COUNTRIES["印度"] = {
    "intro": "印度的重點是：學生簽證效期超過 180 天要在 14 天內向外國人登記局（FRRO）登記、簽證怎麼申請要先向印度台北協會確認，以及疫苗與蚊媒疾病。以下整理自印度政府的留學網站、外交部與疾管署，並標出出處。台灣護照能不能線上申請印度 e-Visa，我讀到的來源說法不一致，所以沒有下結論；手機卡、付款與交通沒有查到可靠的官方說明，所以沒有寫。",
    "topics": {
        "documents": [
            ("學生簽證效期超過 180 天，14 天內要向 FRRO 登記",
             "印度政府的 Study in India 網站寫：持學生簽證、研究簽證、醫療簽證、就業簽證等，效期超過 180 天的人，要在首次抵達印度後 14 天內向所屬的外國人登記局（FRRO）登記。登記走 e-FRRO 線上系統，除非被通知，不用預約到辦公室；證件會用郵寄與電郵寄給學生。頁面建議至少提早 2 週申請，也警告延遲繳費、上傳文件或面談可能被依印度法律起訴或罰款。",
             "must", ("in_frro",)),
            ("FRRO 登記要備的文件",
             "印度外交部的清單寫：簽證超過 6 個月的外國人要登記，首次抵達後 14 天內辦理；要備蓋有簽證的護照正本與影本、4 張照片、居住證明；學生還要學校出具的在學證明（bonafide certificate）。清單另外寫，簽證超過一年且年齡在 15 到 60 歲之間的人，要附 WHO 認可機構出具的 HIV 檢驗報告；一學期的交換生通常用不到，但請向學校確認。",
             "should", ("in_mea_frro",)),
            ("台灣護照怎麼申請學生簽證：請先向印度台北協會確認",
             "印度政府 e-Visa 官網的資格頁（我打開時）寫有 e-Student 簽證：自核准起 365 天、可多次入境，要有印度認可學校的入學許可等文件。但我讀到的另一個搜尋結果說台灣不在 e-Visa 名單，兩邊矛盾，我也沒能從官方名單確認，所以不下結論。台灣護照到底能不能線上申請、不行的話要怎麼申請，請向印度台北協會與官網確認，並在拿到入學許可後就開始辦。",
             "must", ("in_evisa",)),
        ],
        "health_insurance": [
            ("出發前要評估的疫苗",
             "疾管署的印度旅遊處方箋（涵蓋 2023 年 11 月到 2026 年 9 月的資料）建議：A 型肝炎疫苗（當地飲食與飲水有傳染風險）；日本腦炎疫苗在行程超過一個月或常去農村時建議；狂犬病疫苗給有動物接觸風險的人；傷寒疫苗給會去偏遠或衛生條件差地區的人；MMR。處方箋也提到黃熱病：入境時需要持證明以避免被隔離，是否適用於你，以處方箋的說明為準。出發前先到旅遊醫學門診評估。",
             "must", ("cdc_in",)),
            ("蚊媒疾病、飲水與動物接觸",
             "印度的蚊媒疾病有登革熱、屈公病、瘧疾、日本腦炎與茲卡，全境有瘧疾風險。疾管署建議穿長袖長褲、使用含 DEET 或派卡瑞丁的防蚊劑；不吃未煮熟的食物與生海鮮，水果自己洗過削皮，只喝包裝完整或煮沸過的水；避免接觸蝙蝠、狗、貓等哺乳動物與活禽市場，被咬要立刻就醫；避免接觸淡水（有血吸蟲風險）。返國一年內發燒要就醫。",
             "should", ("cdc_in",)),
        ],
        "emergency": [
            ("駐印度代表處（新德里）的緊急電話",
             "我讀到兩個外交部系統的頁面都寫：從海外撥 +91-9810-642-658，印度境內撥 9810642658；辦公室電話 +91-11-46077777。專供車禍、搶劫、危及生命等急難。我另外在搜尋摘要看到不同的號碼，所以請在出發前自己點進來源頁面核對，再存進手機。",
             "must", ("mofa_tw_india", "roc_india")),
        ],
    },
}

# --------------------------------------------------------------------------------------------- 西班牙
COUNTRIES["西班牙"] = {
    "intro": "西班牙的重點是：停留超過 90 天要先辦學生簽證、超過 180 天要在一個月內辦外國人身分證 TIE、住下來要到市政府登記，以及台灣健保在西班牙沒有用。以下整理自西班牙外交部、西班牙駐台北領事處、國家統計局的法規說明，並標出出處。租屋、銀行、手機與治安沒有查到可靠的官方說明，所以沒有寫。",
    "topics": {
        "documents": [
            ("停留超過 90 天要先辦學生簽證，至少兩個月前申請",
             "西班牙外交部的頁面（台北領事處）說，停留超過 90 天要有學生簽證，短於 90 天的就學不需要。簽證要在學業開始前至少兩個月申請，用線上系統 sutramiteconsular.maec.es，透過最近的西班牙領事館辦理，台北有西班牙領事處。",
             "must", ("es_visa_study",)),
            ("學生簽證要備的文件",
             "頁面列出：入學與繳費證明；財力證明，金額至少是 IPREM 的 100%（第一位受扶養者加 75%，之後每人加 50%）；公共或私人的健康保險證明，保險公司要是獲准在西班牙營運的；停留超過 180 天要附無犯罪紀錄；以及依 2005 年國際衛生條例出具的醫療證明。實際要哪些份數與翻譯，以領事處最新說明為準。",
             "must", ("es_visa_study",)),
            ("停留超過 180 天要在入境一個月內辦 TIE",
             "頁面寫：停留不超過 180 天，簽證涵蓋整段停留，不需要外國人身分證（TIE）。停留超過 180 天，簽證最長 365 天，入境後要在一個月內到簽證辦理省份的警察局或移民局申請 TIE。西班牙外交部的 TIE 頁面提醒，預約可能排在申請後好幾週，所以要早點訂時間。",
             "must", ("es_visa_study", "es_tie")),
        ],
        "housing": [
            ("住下來要到市政府登記（empadronamiento）",
             "西班牙的地方政府法規定，住在西班牙的人都有義務到居住地的市政府登記（Padrón），不管是本國人或外國人，市政府登記不等於取得居留資格，居留由內政部管。登記資料是你住在那個市的證明。",
             "should", ("es_padron",)),
        ],
        "health_insurance": [
            ("台灣健保在西班牙沒用，簽證要有西班牙可接受的保險",
             "西班牙駐台北領事處的頁面寫，西班牙與台灣沒有簽署社會保障協議。學生簽證要的是公共或私人健康保險的證明，而且保險公司要是獲准在西班牙營運的，所以出發前要買符合的保單，不要只帶台灣健保。",
             "must", ("es_taipei_health", "es_visa_study")),
        ],
        "emergency": [
            ("駐西班牙代表處（馬德里）的緊急電話",
             "從海外撥 (+34) 639384883，西班牙境內撥 639384883，專供車禍、搶劫、危及生命等急難。一般領務請在週一到週五 09:30–17:00 打辦公室電話 (+34) 915714678；護照遺失要電郵身分證件影本與警方報案證明到 esp@mofa.gov.tw。",
             "must", ("mofa_tw_spain",)),
        ],
    },
}

# --------------------------------------------------------------------------------------------- 瑞典
COUNTRIES["瑞典"] = {
    "intro": "瑞典的重點是：超過 90 天要先拿到居留許可才能入境、2026 年生活費門檻是每月 10,656 瑞典克朗、學程不到一年要有全面的健康保險，以及短期停留用協調號碼代替個人號碼。以下整理自瑞典移民局、稅務局與駐瑞典代表處，並標出出處。瑞典的學生住宿很緊張，但我能打開的官方頁面不夠，所以沒有寫；BankID 與 Swish 行動支付也沒查到，沒有寫。",
    "topics": {
        "documents": [
            ("超過 90 天要先拿到居留許可才能入境",
             "瑞典移民局的頁面（2026 年內容）說，非歐盟／EEA 公民在瑞典讀書超過 90 天要申請居留許可，少於三個月就不要申請。申請要在前往瑞典前提出，而且許可核發了才能入境。頁面寫近期 75% 的案件在 3 個月內決定，所以錄取後馬上辦。交換生適用相同的規定。",
             "must", ("se_migration",)),
            ("2026 年的生活費門檻：每月 10,656 瑞典克朗",
             "頁面寫，2026 年申請的人要證明每月至少有 10,656 瑞典克朗；如果免費供應住宿，可以減 4,736 克朗，免費供餐可以減 2,960 克朗。其他文件包括護照、學校的錄取決定，學程不到一年的還要附健康保險證明。",
             "must", ("se_migration",)),
        ],
        "health_insurance": [
            ("學程不到一年，要有涵蓋全程的全面健康保險",
             "移民局寫：學程少於一年、而且沒有登記在瑞典人口登記冊的人，要提出全面健康保險的證明；保險要涵蓋緊急與其他醫療、住院和緊急牙科，並且在整段停留期間有效。",
             "must", ("se_migration",)),
        ],
        "housing": [
            ("停留不到一年，銀行與就業會用協調號碼（samordningsnummer）",
             "瑞典稅務局說，從未登記在人口登記冊、而且計畫在瑞典停留少於一年的人，如果與瑞典有關聯（例如在大學讀書）並且需要，可以申請協調號碼。要用電子服務申請，並預約到稅務局服務中心當面驗證身分（帶護照）。頁面說協調號碼用在就業登記、房產與銀行等事務；日後登記為居民，會換成個人號碼。停留一年以上，應該申報遷入。",
             "should", ("se_tax",)),
        ],
        "emergency": [
            ("駐瑞典代表處的緊急電話",
             "從海外撥 +46-70-675 5089；專供車禍、搶劫、危及生命等急難；一般護照、簽證請在上班時間打辦公室電話 +46-(0)8-728 85 13。",
             "must", ("mofa_tw_sweden",)),
        ],
    },
}

# --------------------------------------------------------------------------------------------- 加拿大
COUNTRIES["加拿大"] = {
    "intro": "加拿大的重點是：課程超過 6 個月才需要學習許可、台灣護照搭飛機入境要有 eTA、健康保險因省份而異，以及校外工作有每週 24 小時的上限。以下整理自加拿大政府、加拿大移民部、EduCanada、卑詩省政府與駐加拿大代表處，並標出出處。SIN 社會保險號碼的申請細節、銀行、手機與冬季準備沒有查，所以沒有寫。",
    "topics": {
        "documents": [
            ("課程 6 個月以內不需要學習許可，超過就要，而且要在入境前申請",
             "加拿大政府的頁面（2026 年 9 月 9 日）寫：課程在 6 個月以內，不需要學習許可；如果課程可能超過 6 個月，要在抵達前先申請學習許可。沒有學習許可，就不能在加拿大邊讀書邊工作。交換生要看自己課程的長短，不確定就問合作校。",
             "must", ("ca_no_permit",)),
            ("台灣護照搭飛機入境要有 eTA",
             "加拿大移民部的 eTA 申請指南寫：持外交部核發台灣護照的人可以申請 eTA，申請時要輸入護照上的身分證字號。搭飛機入境前要先申請；如果先申請學習或工作許可，核准後會自動核發 eTA，不用另外申請也不用再付費。我曾讀到一個摘要說台灣需要簽證，但原文指南寫的是可申請 eTA，請你出發前再用 IRCC 的「確認是否需要簽證或 eTA」頁面核對。",
             "must", ("ca_eta_guide", "ca_eta_faq", "ca_apply")),
            ("學習許可申請要備的東西",
             "加拿大政府的頁面（2026 年 9 月 2 日）寫：一般要在來加拿大前申請；要有學校（指定學習機構）的錄取信；省或地區的證明信（PAL 或 TAL），符合例外的人要提出證明；足夠的財力；14 到 79 歲通常要按指紋與拍照，遞件時就要繳生物辨識費。處理時間請看 IRCC 的處理時間頁面。",
             "should", ("ca_apply",)),
            ("校外工作每週最多 24 小時，短期交換生可能不符合",
             "加拿大政府的頁面（2026 年 4 月 15 日）寫：學期中校外工作每週最多 24 小時，學校排定的假期不限時數；學程要至少 6 個月、且能取得學位、文憑或證書；要有 SIN 社會保險號碼，初次學習許可上也要印有允許校外工作的條件。一學期的交換生可能不符合這些條件，工作前先問學校。",
             "should", ("ca_work",)),
        ],
        "health_insurance": [
            ("健康保險因省份而異：先問學校，不要空窗",
             "EduCanada 說，答案取決於你去的省份：提供免費醫療的省，可能要求先居住一段時間才給保障；沒有免費保障的地方，學校會要求買私人醫療保險；安大略的所有國際學生都必須加入學校的 UHIP。以卑詩省為例，政府的頁面（2024 年 1 月 8 日）寫：持學習許可、一年至少讀六個月的國際學生，每月要繳 75 加幣的國際學生健康費並加入 MSP；保障有等待期，是入境居住當月剩餘的日子再加兩個月，等待期間應該有私人保險；只有成年的國際學生可以正式退出 MSP 以免繳費。",
             "must", ("ca_educanada", "ca_bc_health")),
        ],
        "emergency": [
            ("駐加拿大代表處與辦事處的緊急電話",
             "渥太華（代表處）(613) 762-6090；多倫多辦事處 (416) 587-8111；溫哥華辦事處 (604) 377-8730，辦公室 (604) 689-4111。蒙特婁辦事處也有專線，請看駐加拿大代表處的急難救助頁面。專供車禍、搶劫、危及生命等急難，一般領務請在上班時間打辦公室電話。",
             "must", ("mofa_tw_canada", "mofa_tw_vancouver", "roc_canada_emergency")),
        ],
    },
}
