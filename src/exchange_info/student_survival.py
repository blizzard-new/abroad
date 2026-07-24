from __future__ import annotations

from .models import (
    DestinationProfile,
    PageCategory,
    SourceReference,
    StudentGuideChecklistItem,
    StudentGuideSection,
)


CHINA_LIVING_GUIDE_URL = (
    "https://english.www.gov.cn/2025special/bizexpatsinchina2025"
)
CHINA_PAYMENT_GUIDE_URL = (
    "https://english.www.gov.cn/news/202408/22/"
    "content_WS66c71b3ec6d0868f4e8ea2b1.html"
)
TAIWAN_TRAVEL_PERMIT_URL = (
    "https://www.nia.gov.cn/n741440/n741587/n1316094/n1355872/"
    "c1356367/content.html"
)

JAPAN_LIVING_GUIDE_URL = (
    "https://www.moj.go.jp/isa/support/portal/guidebook_all.html?hl=ja"
)
JAPAN_IMMIGRATION_URL = (
    "https://studyinjapan.go.jp/en/planning/immigration-procedures/"
)
JAPAN_ACCOMMODATION_URL = "https://studyinjapan.go.jp/en/life/accomodation/"
JAPAN_IC_CARD_URL = "https://www.japan.travel/en/plan/ic-card/"
JAPAN_CASHLESS_URL = (
    "https://www.japan.travel/en/plan/cashless-payments-in-japan/"
)

KOREA_LIVING_GUIDE_URL = (
    "https://www.studyinkorea.go.kr/graduate/life/livingAndHousing.do"
)
KOREA_RESIDENCE_URL = (
    "https://www.studyinkorea.go.kr/eng/life/residenceAndStayInfo.do"
)
KOREA_TRANSPORT_CARD_URL = (
    "https://english.visitkorea.or.kr/svc/contents/infoBscView.do"
    "?menuSn=479&vcontsId=140663"
)

FRANCE_ARRIVAL_URL = "https://www.campusfrance.org/en/organise-arrival-France"
FRANCE_VISA_URL = "https://www.campusfrance.org/en/student-long-stay-visa"
FRANCE_HOUSING_URL = "https://www.campusfrance.org/en/student-housing-france"
FRANCE_BANK_URL = "https://www.campusfrance.org/en/getting-a-bank-account"
FRANCE_TRANSPORT_URL = (
    "https://www.campusfrance.org/en/how-to-get-around-every-day-in-france"
)

POLAND_VISA_URL = "https://study.gov.pl/visa-application"
POLAND_RESIDENCE_URL = (
    "https://www.mos.cudzoziemcy.gov.pl/en/categories-information/"
    "possibilities-legalization/non-eu-continued-stay/permit-temporary/"
    "study/permit-studies/introduction/"
)
POLAND_LIVING_COST_URL = "https://study.gov.pl/cost-living-poland"
POLAND_TRANSPORT_URL = "https://study.gov.pl/transportation"
POLAND_ARRIVAL_URL = "https://study.gov.pl/how-to-apply"

VIETNAM_EVISA_URL = "https://evisa.gov.vn/?fs=e"
VIETNAM_STUDENT_TRANSPORT_URL = (
    "https://sotuphap.hochiminhcity.gov.vn/tin-tuc-su-kien/-/"
    "asset_publisher/emZ19pfF3Yyq/content/id/4641779/"
    "mien-giam-gia-ve-dich-vu-cong-cong-cho-hoc-sinh-sinh-vien-"
)
VIETNAM_PAYMENT_URL = (
    "https://www.sbv.gov.vn/vi/web/sbv_portal/"
    "m%E1%BB%99t-s%E1%BB%91-th%C3%B4ng-tin-v%E1%BB%81-th%E1%BA%BB-ng%C3%A2n-h%C3%A0ng"
)
VIETNAM_ISB_LIFE_URL = (
    "https://international.isb.edu.vn/transfer-programs/international-students/"
)

THAILAND_EVISA_URL = "https://www.thaievisa.go.th/"
THAILAND_ED_VISA_URL = (
    "https://budapest.thaiembassy.org/en/publicservice/"
    "non-immigrant-ed-and-ed-plus-visa?cate=698497c323290a095267d1c3"
)
THAILAND_SIM_URL = (
    "https://www.nbtc.go.th/News/Press-Center/72452.aspx?lang=th-th"
)
THAILAND_PAYMENT_URL = (
    "https://www.bot.or.th/th/satang-story/fraud/card-fraud.html"
)
THAILAND_AIRPORT_TRANSPORT_URL = (
    "https://suvarnabhumi.airportthai.co.th/service/airport-guide/detail/"
    "Transportation_BKK"
)


CHINA_SHARED_SOURCES = (
    SourceReference(
        title="Guide to Working and Living in China (2025) | The State Council",
        source_url=CHINA_LIVING_GUIDE_URL,
        category=PageCategory.OTHER,
        summary=(
            "中國國務院英文生活指南整理境外人士辦理 SIM、銀行卡、行動支付、人民幣現金與交通的做法；"
            "其中證件要求以外籍人士為例，臺灣交換生仍需帶台胞證並向校方、門市或銀行確認當期受理文件。"
        ),
    ),
    SourceReference(
        title="Guide to Payment Services in China | The State Council",
        source_url=CHINA_PAYMENT_GUIDE_URL,
        category=PageCategory.OTHER,
        summary=(
            "官方支付指南列出銀行卡、行動支付、現金、銀行帳戶與數位人民幣等方式，並提醒境外使用者可依平台規則綁定國際卡。"
        ),
    ),
    SourceReference(
        title="臺灣居民來往大陸通行證簽發服務指南 | 國家移民管理局",
        source_url=TAIWAN_TRAVEL_PERMIT_URL,
        category=PageCategory.OTHER,
        summary=(
            "國家移民管理局說明台胞證申請、換補發、效期與住宿登記相關要求；出發前應確認證件涵蓋完整交換期間並保留影本。"
        ),
    ),
)

JAPAN_SHARED_SOURCES = (
    SourceReference(
        title="生活・就労ガイドブック | 日本出入國在留管理廳",
        source_url=JAPAN_LIVING_GUIDE_URL,
        category=PageCategory.OTHER,
        summary=(
            "日本出入國在留管理廳提供多語生活指南，涵蓋住居、交通、手機契約、銀行帳戶、醫療與日常生活規則。"
        ),
    ),
    SourceReference(
        title="Immigration and Student Visas | Study in Japan",
        source_url=JAPAN_IMMIGRATION_URL,
        category=PageCategory.OTHER,
        summary=(
            "日本官方留學網站說明學生簽證、在留卡及住址登記；停留超過三個月者取得住處後，原則上應在 14 天內到市區町村辦理住民登記。"
        ),
    ),
    SourceReference(
        title="Accommodation | Study in Japan",
        source_url=JAPAN_ACCOMMODATION_URL,
        category=PageCategory.OTHER,
        summary=(
            "日本官方留學網站比較學生宿舍與民間租屋，提醒宿舍房數有限、可能有門禁或共用設施，錄取後應盡早確認住宿。"
        ),
    ),
    SourceReference(
        title="IC Travel Cards | Japan National Tourism Organization",
        source_url=JAPAN_IC_CARD_URL,
        category=PageCategory.OTHER,
        summary=(
            "日本政府觀光局說明 Suica、PASMO 等預付 IC 卡可搭乘多數電車與巴士，也能在部分商店與自動販賣機小額付款。"
        ),
    ),
    SourceReference(
        title="Cashless Payments in Japan | Japan National Tourism Organization",
        source_url=JAPAN_CASHLESS_URL,
        category=PageCategory.OTHER,
        summary=(
            "日本政府觀光局說明信用卡與電子支付日益普及，但部分地點仍只收現金；出發與抵達初期都應保留日圓備援。"
        ),
    ),
)

KOREA_SHARED_SOURCES = (
    SourceReference(
        title="Living and Housing in Korea | Study in Korea",
        source_url=KOREA_LIVING_GUIDE_URL,
        category=PageCategory.OTHER,
        summary=(
            "韓國政府 Study in Korea 平台整理住宿、銀行、手機、交通、醫療與保險；預付門號可用護照辦理，後付方案通常需要外國人登錄證。"
        ),
    ),
    SourceReference(
        title="Residence and Stay Information | Study in Korea",
        source_url=KOREA_RESIDENCE_URL,
        category=PageCategory.OTHER,
        summary=(
            "韓國政府留學平台說明預計停留超過 90 天者應在入境後 90 天內完成外國人登錄，並列出護照、照片與在學證明等基本文件。"
        ),
    ),
    SourceReference(
        title="Transportation Cards | VISITKOREA",
        source_url=KOREA_TRANSPORT_CARD_URL,
        category=PageCategory.OTHER,
        summary=(
            "韓國觀光公社說明 T-money、EZL 等預付交通卡可在便利商店購買與加值，用於大眾運輸及部分加盟商店。"
        ),
    ),
)

FRANCE_SHARED_SOURCES = (
    SourceReference(
        title="Checklist: Prepare Your Arrival in France | Campus France",
        source_url=FRANCE_ARRIVAL_URL,
        category=PageCategory.OTHER,
        summary=(
            "法國政府 Campus France 抵達清單涵蓋住宿、學校註冊、CVEC、銀行、保險與抵達後第一個月應完成的事項。"
        ),
    ),
    SourceReference(
        title="Long-stay Student Visa (VLS-TS) | Campus France",
        source_url=FRANCE_VISA_URL,
        category=PageCategory.OTHER,
        summary=(
            "Campus France 說明學生 VLS-TS 抵達法國後須在線上完成驗證，最晚不得超過入境後三個月，並列出驗證所需的簽證、入境日與法國住址等資料。"
        ),
    ),
    SourceReference(
        title="Student Housing in France | Campus France",
        source_url=FRANCE_HOUSING_URL,
        category=PageCategory.OTHER,
        summary=(
            "Campus France 比較 CROUS、私人學生住宅與一般租屋，提醒交換生應先問接待校住宿安排，並預先確認保證人、VISALE、押金、入住點交與住宅保險。"
        ),
    ),
    SourceReference(
        title="Getting a Bank Account | Campus France",
        source_url=FRANCE_BANK_URL,
        category=PageCategory.OTHER,
        summary=(
            "Campus France 說明外國學生可在法國銀行開戶，本地帳戶可用於房租、電話、交通、網路及醫療退款；卡費、跨境匯款與提款費用應逐家比較。"
        ),
    ),
    SourceReference(
        title="Getting Around Every Day in France | Campus France",
        source_url=FRANCE_TRANSPORT_URL,
        category=PageCategory.OTHER,
        summary=(
            "Campus France 說明各城市公車、路面電車與地鐵系統不同，學生或未滿 26 歲者常有優惠，辦月票／年票通常要出示學生證或身分證件。"
        ),
    ),
)

POLAND_SHARED_SOURCES = (
    SourceReference(
        title="Visa and Application | Study in Poland",
        source_url=POLAND_VISA_URL,
        category=PageCategory.OTHER,
        summary=(
            "波蘭政府 Study in Poland 說明非歐盟學生的護照、簽證與抵達後居留程序；"
            "若需要延長停留，應在合法居留期間、簽證到期前向所在地省政府申請暫時居留。"
        ),
    ),
    SourceReference(
        title="Temporary Residence Permit for Studies | Office for Foreigners",
        source_url=POLAND_RESIDENCE_URL,
        category=PageCategory.OTHER,
        summary=(
            "波蘭外國人事務辦公室說明就學用暫時居留許可的適用對象與基本條件；"
            "交換生仍應依簽證效期與接待校指示，確認自己是否需要申請。"
        ),
    ),
    SourceReference(
        title="Cost of Living in Poland | Study in Poland",
        source_url=POLAND_LIVING_COST_URL,
        category=PageCategory.OTHER,
        summary=(
            "波蘭官方留學平台提供住宿、交通、保險、電話網路與飲食的月支出參考，"
            "並提醒華沙、克拉科夫等城市與住宿選擇會造成明顯差異。"
        ),
    ),
    SourceReference(
        title="Transportation | Study in Poland",
        source_url=POLAND_TRANSPORT_URL,
        category=PageCategory.OTHER,
        summary=(
            "波蘭官方留學平台說明各城市公車、電車、地鐵與學生長期票；"
            "部分城市可把票證整合進波蘭學生證，查票時仍須持有效學生身分證明。"
        ),
    ),
    SourceReference(
        title="How to Apply and Prepare for Poland | Study in Poland",
        source_url=POLAND_ARRIVAL_URL,
        category=PageCategory.OTHER,
        summary=(
            "波蘭官方留學平台將住宿、房內網路、本地 SIM 與文化適應列為出發及抵達初期應處理的事項。"
        ),
    ),
)

VIETNAM_SHARED_SOURCES = (
    SourceReference(
        title="Viet Nam E-Visa | Immigration Department",
        source_url=VIETNAM_EVISA_URL,
        category=PageCategory.OTHER,
        summary=(
            "越南公安部出入境管理局的官方電子簽證入口說明線上填表、繳費與查收結果；"
            "交換生應先由接待校確認適用簽證類別與入境口岸，不把觀光電子簽證直接當成就學文件。"
        ),
    ),
    SourceReference(
        title="Student Public Transport Discounts | Ho Chi Minh City Department of Justice",
        source_url=VIETNAM_STUDENT_TRANSPORT_URL,
        category=PageCategory.OTHER,
        summary=(
            "胡志明市政府轉載 2026 年學生公共服務優惠規定：學生出示有效學生證明時，"
            "公車、鐵路、捷運與渡輪等公共運輸可依地方規則享有減免；實際票價仍須查所在城市最新公告。"
        ),
    ),
    SourceReference(
        title="Bank Card Information | State Bank of Vietnam",
        source_url=VIETNAM_PAYMENT_URL,
        category=PageCategory.OTHER,
        summary=(
            "越南國家銀行說明國內卡、國際卡、簽帳卡、信用卡與預付卡的差異，並提醒保護卡號、PIN、"
            "啟用交易通知及發現異常時立即聯絡銀行。"
        ),
    ),
    SourceReference(
        title="International Students | UEH-ISB",
        source_url=VIETNAM_ISB_LIFE_URL,
        category=PageCategory.OTHER,
        summary=(
            "UEH-ISB 官方交換生頁整理胡志明市住宿協助、壅塞交通、叫車／公車等移動方式、"
            "熱帶衣物、防蚊、防曬、常用藥、筆電與備援付款等實用行前清單。"
        ),
    ),
)

THAILAND_SHARED_SOURCES = (
    SourceReference(
        title="Thailand E-Visa | Ministry of Foreign Affairs",
        source_url=THAILAND_EVISA_URL,
        category=PageCategory.OTHER,
        summary=(
            "泰國外交部官方電子簽證入口供申請人建立申請、上傳文件與查收結果；交換生應先等接待校提供"
            "錄取及簽證文件，再依臺灣所在地適用的泰國辦事處要求送件。"
        ),
    ),
    SourceReference(
        title="Non-Immigrant ED and ED Plus Visa | Royal Thai Embassy",
        source_url=THAILAND_ED_VISA_URL,
        category=PageCategory.OTHER,
        summary=(
            "泰國官方 2026 年 ED 簽證說明把交換、短期課程與實習列入 Non-Immigrant ED 適用情形，"
            "並提醒一般 ED 的停留、延長及離境再入境安排要事前確認；各地辦事處仍可能要求不同補件。"
        ),
    ),
    SourceReference(
        title="Foreign SIM Registration Measures | NBTC Thailand",
        source_url=THAILAND_SIM_URL,
        category=PageCategory.OTHER,
        summary=(
            "泰國國家廣播及電信委員會的現行措施要求外國人以護照完成 SIM 實名，並限制外國人登記數量；"
            "觀光 SIM 最長使用 60 天且不能靠儲值延長，因此一學期交換不要只看機場短期方案。"
        ),
    ),
    SourceReference(
        title="Card Fraud and ATM Safety | Bank of Thailand",
        source_url=THAILAND_PAYMENT_URL,
        category=PageCategory.OTHER,
        summary=(
            "泰國銀行提醒使用 ATM 前檢查讀卡槽與鍵盤、輸入 PIN 時遮擋、刷卡時讓卡片保持在視線內，"
            "並持續核對交易通知；交換生仍應保留泰銖現金及第二張實體卡作為備援。"
        ),
    ),
    SourceReference(
        title="Transportation To and From Suvarnabhumi Airport | Airports of Thailand",
        source_url=THAILAND_AIRPORT_TRANSPORT_URL,
        category=PageCategory.OTHER,
        summary=(
            "泰國機場公司列出蘇凡納布機場的排班計程車、合法叫車、公車、客運、接駁車與 Airport Rail Link；"
            "這只適用曼谷入境，前往宋卡王子大學等外地校區要另查轉機與接待校路線。"
        ),
    ),
)

ALL_SHARED_SOURCES = (
    *CHINA_SHARED_SOURCES,
    *JAPAN_SHARED_SOURCES,
    *KOREA_SHARED_SOURCES,
    *FRANCE_SHARED_SOURCES,
    *POLAND_SHARED_SOURCES,
    *VIETNAM_SHARED_SOURCES,
    *THAILAND_SHARED_SOURCES,
)


def _school_source_urls(profile: DestinationProfile) -> list[str]:
    shared_urls = {source.source_url for source in ALL_SHARED_SOURCES}
    urls = [
        source.source_url
        for source in profile.sources
        if source.source_url not in shared_urls
    ]
    return list(dict.fromkeys(urls))[:3]


def _available_or_missing(value: str | None, missing: str) -> str:
    compact = " ".join(
        str(value or "").replace("\ufffc", " ").replace("\u200b", " ").split()
    )
    return compact or missing


def _regional_guide_config(country: str) -> dict | None:
    if country == "日本":
        return {
            "shared_sources": JAPAN_SHARED_SOURCES,
            "housing_url": JAPAN_ACCOMMODATION_URL,
            "transport_url": JAPAN_IC_CARD_URL,
            "living_urls": [JAPAN_LIVING_GUIDE_URL, JAPAN_IMMIGRATION_URL],
            "payment_urls": [JAPAN_CASHLESS_URL, JAPAN_LIVING_GUIDE_URL],
            "mobile_summary": (
                "日本官方生活指南提醒，手機契約所需證件與付款方式依業者而異，可先查多語門市；銀行開戶通常會核對在留卡、學生證等文件。"
                "日本雖已普遍接受信用卡與電子支付，部分商店與地區仍需要日圓現金。"
            ),
            "mobile_points": [
                "短期預付 SIM／eSIM 與長期門號的證件、流量、通話和解約條件不同，先按交換長度選擇。",
                "保留一張可收臺灣簡訊的門號，避免銀行與帳號驗證中斷。",
                "抵達初期同時準備國際信用卡與日圓現金，不把單一行動支付當唯一付款方式。",
                "要開日本銀行帳戶時，先問校方推薦分行與所需的在留卡、學生證、住址及印章／簽名規定。",
            ],
            "transport_points": [
                "先存報到校區、宿舍名稱、日文地址與最近車站，不要只存大學名稱。",
                "Suica、PASMO 等 IC 卡可搭乘多數電車與巴士，也能在部分商店小額付款。",
                "不同地區使用的 IC 卡名稱可能不同；先確認通勤路線，再決定實體卡或手機版。",
            ],
            "residence_title": "確認在留卡與住址登記",
            "residence_detail": (
                "停留超過三個月者通常會取得在留卡；確定住址後原則上應在 14 天內到市區町村辦理住民登記。"
                "抵達前三天先向校方確認陪同、窗口、營業時間與所需文件。"
            ),
            "residence_timing": "前 72 小時先排程",
            "documents_detail": (
                "護照、簽證、COE、錄取／提名文件、住宿通知、保險與證件照；另做加密雲端備份與紙本影本。"
            ),
            "phone_detail": (
                "先用機場／校園 Wi-Fi 聯絡接待人，再依交換長度選預付 SIM、eSIM 或月租門號；確認手機已解鎖。"
            ),
            "payment_detail": (
                "先測試國際卡與一筆小額付款，準備日圓現金；若需要銀行帳戶，向校方確認分行、住址及文件要求。"
            ),
            "transport_purchase_title": "通勤地區適用的 IC 交通卡",
            "transport_purchase_detail": (
                "先確認每天使用的鐵路與巴士，再購買可互通的實體 IC 卡或設定手機版；首次加值保留日圓現金。"
            ),
            "country_note": (
                "日本出入國在留管理廳、Study in Japan 與政府觀光局官方指南補足在留、門號、銀行、付款與交通流程"
            ),
        }
    if country == "韓國":
        return {
            "shared_sources": KOREA_SHARED_SOURCES,
            "housing_url": KOREA_LIVING_GUIDE_URL,
            "transport_url": KOREA_TRANSPORT_CARD_URL,
            "living_urls": [KOREA_LIVING_GUIDE_URL, KOREA_RESIDENCE_URL],
            "payment_urls": [KOREA_LIVING_GUIDE_URL],
            "mobile_summary": (
                "韓國政府 Study in Korea 指南說明，預付門號可依業者規定持護照辦理，後付方案通常需要外國人登錄證；"
                "銀行開戶會核對護照／登錄證與交易目的證明，實際文件依銀行而異。"
            ),
            "mobile_points": [
                "還沒有外國人登錄證時，可先詢問護照可辦的預付 SIM；拿到登錄證後再比較是否轉後付方案。",
                "保留一張可收臺灣簡訊的門號，避免銀行與帳號驗證中斷。",
                "開戶前先問校方推薦分行，並帶護照、登錄證、學生證／在學證明與交易目的文件。",
                "抵達初期保留韓元現金與國際信用卡，確認本地卡或行動支付可用後再降低現金備援。",
            ],
            "transport_points": [
                "先存報到校區、宿舍名稱、韓文地址與最近地鐵／公車站，不要只存大學英文名。",
                "T-money、EZL 等預付交通卡可在便利商店購買與加值，用於大眾運輸及部分加盟商店。",
                "首爾以外城市的交通路線與加值方式可能不同，先依實際通勤城市確認。",
            ],
            "residence_title": "預約外國人登錄並備齊文件",
            "residence_detail": (
                "預計停留超過 90 天者應在入境後 90 天內完成外國人登錄；前 72 小時先向校方確認團體辦理、預約方式、照片與在學證明。"
            ),
            "residence_timing": "前 72 小時先預約",
            "documents_detail": (
                "護照、簽證、錄取／提名文件、住宿通知、保險、在學證明與近期證件照；另做加密雲端備份與紙本影本。"
            ),
            "phone_detail": (
                "先用機場／校園 Wi-Fi 聯絡接待人，再持護照詢問預付 SIM；後付門號通常等外國人登錄證完成後再比較。"
            ),
            "payment_detail": (
                "先測試國際卡並保留韓元現金；需要銀行帳戶時，向校方確認可受理外籍學生的分行與文件。"
            ),
            "transport_purchase_title": "T-money 或當地適用交通卡",
            "transport_purchase_detail": (
                "先確認每天使用的地鐵與公車，再到便利商店購買、加值；不同卡種與城市適用範圍以官方最新說明為準。"
            ),
            "country_note": (
                "韓國政府 Study in Korea 與韓國觀光公社官方指南補足外國人登錄、門號、銀行與交通流程"
            ),
        }
    if country == "法國":
        return {
            "shared_sources": FRANCE_SHARED_SOURCES,
            "housing_url": FRANCE_HOUSING_URL,
            "transport_url": FRANCE_TRANSPORT_URL,
            "living_urls": [FRANCE_ARRIVAL_URL, FRANCE_VISA_URL],
            "payment_urls": [FRANCE_BANK_URL, FRANCE_ARRIVAL_URL],
            "mobile_summary": (
                "法國電信方案的證件、付款與解約條件依業者而異；剛抵達可先用短期 SIM／eSIM 維持聯絡，"
                "取得法國住址與銀行資料後再比較長期方案。Campus France 說明外國學生可開法國銀行帳戶，"
                "用於房租、電話、交通與網路等固定支出。"
            ),
            "mobile_points": [
                "出發前確認手機已解鎖，先準備可立即使用的短期 SIM／eSIM，再依交換長度比較月租方案。",
                "保留一張可收臺灣簡訊的門號，避免銀行與帳號驗證中斷。",
                "開戶前向接待校詢問常受理國際學生的分行，並備妥護照、簽證／居留資料、在學證明與法國住址證明。",
                "抵達初期同時保留歐元現金與可海外交易的實體信用卡，確認本地卡可用後再降低現金備援。",
            ],
            "transport_points": [
                "先存報到校區、宿舍名稱、法文地址與最近車站，不要只存學校英文名稱。",
                "各城市交通票證不同；確認實際通勤城市後，再辦當地學生月票或年票。",
                "學生／未滿 26 歲常有優惠，申辦時通常要帶學生證或身分證件；機場到校先買單程票即可。",
            ],
            "residence_title": "完成 VLS-TS 線上驗證與學校註冊",
            "residence_detail": (
                "持學生 VLS-TS 者抵達後應盡快在線上完成驗證，最晚不得超過入境後三個月；"
                "前 72 小時先確認法國住址、入境日期、付款方式與接待校協助窗口。"
            ),
            "residence_timing": "前 72 小時先建檔",
            "documents_detail": (
                "護照、簽證、錄取／提名文件、住宿證明、保險、在學證明與證件照；"
                "另準備法國住址、入境日期及加密雲端備份。"
            ),
            "phone_detail": (
                "先用機場／校園 Wi-Fi 聯絡接待人，再啟用短期 SIM／eSIM；取得住址與銀行資料後，"
                "再比較長期方案的合約、解約與付款條件。"
            ),
            "payment_detail": (
                "先測試國際卡並保留歐元現金；需要法國帳戶時，向校方確認分行、預約方式與住址證明等文件。"
            ),
            "transport_purchase_title": "所在城市的學生交通票證",
            "transport_purchase_detail": (
                "先確認宿舍到校路線與營運公司，再帶學生證／身分證件申辦學生月票或年票；"
                "巴黎與其他城市使用不同票證，不要預先買錯。"
            ),
            "country_note": (
                "法國政府 Campus France 官方指南補足 VLS-TS、住宿、銀行、付款與城市交通流程"
            ),
        }
    if country == "波蘭":
        return {
            "shared_sources": POLAND_SHARED_SOURCES,
            "housing_url": POLAND_LIVING_COST_URL,
            "transport_url": POLAND_TRANSPORT_URL,
            "living_urls": [
                POLAND_VISA_URL,
                POLAND_RESIDENCE_URL,
                POLAND_ARRIVAL_URL,
            ],
            "payment_urls": [POLAND_LIVING_COST_URL, POLAND_ARRIVAL_URL],
            "mobile_summary": (
                "波蘭官方留學平台把本地 SIM、住宿網路與日常預算列為落地準備；"
                "電信實名、銀行開戶與付款文件仍依業者而異。抵達初期先保留波蘭茲羅提現金與可海外交易的實體卡，"
                "拿到波蘭學生證、住址與本地門號後，再比較長期電信與銀行方案。"
            ),
            "mobile_points": [
                "出發前確認手機已解鎖，先準備短期 SIM／eSIM；抵達後再比較本地預付或月租方案。",
                "保留一張可收臺灣簡訊的門號，避免銀行與帳號驗證中斷。",
                "開戶前先問接待校推薦分行，並備妥護照、簽證／居留文件、在學證明、波蘭住址與本地門號。",
                "不要把刷卡當唯一付款方式；交通售票機、小店或系統故障時仍需茲羅提現金備援。",
            ],
            "transport_points": [
                "先存報到校區、宿舍名稱、波蘭文地址與最近電車／公車站，不要只存學校英文名稱。",
                "華沙、克拉科夫、波茲南與弗羅茨瓦夫使用不同城市票證；先依通勤城市辦卡。",
                "長期學生票可能需有效波蘭學生證並在查票時一併出示；學生證尚未完成前先買一般單程票。",
            ],
            "residence_title": "核對簽證效期與暫時居留需求",
            "residence_detail": (
                "抵達後先由接待校依交換長度、簽證類別與效期確認是否需申請暫時居留；"
                "若需要，應在合法居留期間、簽證到期前向所在地省政府辦理，並預留預約與補件時間。"
            ),
            "residence_timing": "前 72 小時先確認",
            "documents_detail": (
                "護照、簽證、錄取／提名文件、住宿證明、保險、財力、在學證明與證件照；"
                "另保存接待校窗口、當地住址及加密雲端備份。"
            ),
            "phone_detail": (
                "先用機場／校園 Wi-Fi 聯絡接待人並啟用短期 SIM／eSIM；"
                "確認宿舍網路與本地門號後，再選涵蓋完整交換期間的方案。"
            ),
            "payment_detail": (
                "先測試國際卡與提款功能並保留少量茲羅提；需要本地帳戶時，"
                "先向校方確認分行、預約方式、住址與在學文件。"
            ),
            "transport_purchase_title": "所在城市的學生交通票",
            "transport_purchase_detail": (
                "拿到有效波蘭學生證後，向當地交通公司確認能否整合學生票或申辦交通卡；"
                "查票時同時攜帶有效學生證明。"
            ),
            "country_note": (
                "波蘭政府 Study in Poland 與外國人事務辦公室官方指南補足簽證、居留、生活費、門號與城市交通流程"
            ),
        }
    if country == "越南":
        return {
            "shared_sources": VIETNAM_SHARED_SOURCES,
            "housing_url": VIETNAM_ISB_LIFE_URL,
            "transport_url": VIETNAM_STUDENT_TRANSPORT_URL,
            "living_urls": [VIETNAM_EVISA_URL, VIETNAM_ISB_LIFE_URL],
            "payment_urls": [VIETNAM_PAYMENT_URL, VIETNAM_ISB_LIFE_URL],
            "mobile_summary": (
                "先準備可立即連線的短期 eSIM／漫遊，抵達後再由接待校推薦的電信門市用護照辦理本地門號；"
                "門號實名、方案與解約規則依業者當期要求為準。越南國家銀行說明國際卡可用於境內外交易，"
                "但學生仍應保留越南盾現金與第二張實體卡，避免小店、交通或系統中斷時無法付款。"
            ),
            "mobile_points": [
                "出發前確認手機已解鎖，保留能收臺灣簡訊的原門號，再準備短期 eSIM／漫遊作為落地網路。",
                "本地 SIM 請到學校推薦或電信商正式門市辦理，帶護照並現場核對實名、流量、通話與效期。",
                "攜帶兩張分開保管、已開啟海外交易的實體卡，並先在臺灣確認提款與交易通知設定。",
                "抵達初期準備小額越南盾；不在路邊或來路不明場所換匯，也不讓卡片離開視線。",
            ],
            "transport_points": [
                "先存報到校區、宿舍越南文地址與接待人電話；同一所大學可能有不同校區。",
                "胡志明市通勤可能包含公車、捷運與合規叫車服務；河內則需依宿舍位置重新規劃，不共用同一套票證假設。",
                "學生交通優惠通常要出示有效學生證明；尚未取得當地學生證前，先用一般票並保留付款備援。",
            ],
            "residence_title": "確認就學簽證、入境口岸與住宿登記",
            "residence_detail": (
                "越南官方電子簽證入口不等於交換生一定適用的簽證類別；出發前由接待校確認邀請／核准文件、"
                "簽證效期與指定入境口岸，入住後再依宿舍或房東指示完成住宿登記。"
            ),
            "residence_timing": "出發前完成、入住後確認",
            "documents_detail": (
                "護照、簽證或核准文件、錄取／提名信、住宿證明、保險、英文成績單、在學證明與證件照；"
                "另保存接待校窗口、越南文住址與加密雲端備份。"
            ),
            "phone_detail": (
                "先用機場／校園 Wi-Fi 或短期 eSIM 聯絡接待人；報到後再到正式門市辦本地 SIM，"
                "當場測試行動網路、簡訊與熱點分享。"
            ),
            "payment_detail": (
                "先測試國際卡與 ATM 提款並保留小額越南盾；若交換期間確實需要本地帳戶，"
                "先問接待校與銀行應備護照、簽證、在學及住址文件，不預設每家銀行都受理。"
            ),
            "transport_purchase_title": "所在城市的學生票或常用交通方案",
            "transport_purchase_detail": (
                "拿到當地學生證後，再向學校或營運單位確認學生優惠、有效路線與申辦方式；"
                "短期先用一般票或合規叫車，避免一抵達就預付不適用的長期方案。"
            ),
            "country_note": (
                "越南公安部、越南國家銀行、胡志明市政府與 UEH-ISB 官方資料補足簽證、付款、交通與落地行李流程"
            ),
        }
    if country == "泰國":
        return {
            "shared_sources": THAILAND_SHARED_SOURCES,
            "housing_urls": [],
            "transport_url": THAILAND_AIRPORT_TRANSPORT_URL,
            "living_urls": [THAILAND_EVISA_URL, THAILAND_ED_VISA_URL],
            "payment_urls": [THAILAND_PAYMENT_URL, THAILAND_SIM_URL],
            "mobile_summary": (
                "出發前先準備可立即連線的短期 eSIM／漫遊，抵達後再到學校建議的正式電信門市辦本地門號。"
                "泰國 NBTC 現行規定要求外國人以護照實名，觀光 SIM 最長使用 60 天且不能靠儲值延長，"
                "一學期交換要確認買到可涵蓋停留期間的方案。付款方面不要只靠行動支付；先保留泰銖現金、"
                "兩張分開保管的實體卡，若確實需要本地帳戶再向接待校及銀行確認 KYC 文件。"
            ),
            "mobile_points": [
                "確認手機已解鎖，保留可收臺灣簡訊的原門號，另準備短期 eSIM／漫遊作為落地網路。",
                "本地 SIM 到電信商正式門市辦理，帶護照並確認不是只能使用 60 天的觀光 SIM。",
                "攜帶兩張已開啟海外交易、分開保管的實體卡，並先在臺灣測試提款及交易通知。",
                "抵達初期準備小額泰銖；ATM 操作前檢查讀卡槽與鍵盤，刷卡時不要讓卡片離開視線。",
            ],
            "transport_points": [
                "先存報到校區、宿舍泰文地址與接待人電話；法政大學、KMUTT 與 PSU 都可能涉及不同校區。",
                "曼谷三校的通勤位置差異很大，不能把 BTS／MRT 當成每個校區都能直達；先用實際課表與住宿地址規劃。",
                "若從蘇凡納布機場入境，可從 AOT 官方頁確認排班計程車、合法叫車、公車及 Airport Rail Link；前往合艾或其他城市要另查轉機。",
            ],
            "residence_title": "確認 ED 簽證、停留期限與再次入境安排",
            "residence_detail": (
                "交換計畫通常由接待校協助準備 Non-Immigrant ED 文件；抵達後立即核對入境章、允許停留日期、"
                "延長辦理時間與 90 日相關程序。若交換期間要離開泰國旅行，先向國際處或移民局確認是否需辦 re-entry permit。"
            ),
            "residence_timing": "出發前完成、抵達後立即核對",
            "documents_detail": (
                "護照、電子簽證核准頁、錄取／提名信、校方簽證文件、住宿證明、保險、英文成績單、"
                "在學證明、財力資料與證件照；另保存接待校窗口、泰文住址及加密雲端備份。"
            ),
            "phone_detail": (
                "先用機場 Wi-Fi 或短期 eSIM 聯絡接待人；報到後持護照到正式門市辦 SIM，"
                "當場確認實名、效期、流量、熱點分享與續約方式。"
            ),
            "payment_detail": (
                "先測試國際卡與 ATM 並保留泰銖現金；若需本地帳戶，向校方詢問常受理國際學生的分行，"
                "再依銀行要求準備護照、簽證、在學與住址文件。"
            ),
            "transport_purchase_title": "所在城市與校區適用的交通方案",
            "transport_purchase_detail": (
                "先確認宿舍到上課校區的實際路線，再選單程票、儲值票或月票；"
                "曼谷與合艾的交通系統不同，也不要在尚未確定校區前購買長期方案。"
            ),
            "country_note": (
                "泰國外交部、NBTC、泰國銀行與泰國機場公司的官方資料補足簽證、門號、付款與落地交通流程"
            ),
        }
    return None


def _apply_regional_student_survival_guide(
    profile: DestinationProfile,
    config: dict,
) -> DestinationProfile:
    school_urls = _school_source_urls(profile)
    school_source = school_urls[:2]
    housing_config_sources = config.get("housing_urls")
    if housing_config_sources is None:
        housing_config_sources = [config["housing_url"]]
    housing_sources = list(
        dict.fromkeys(
            source_url
            for source_url in [*school_source, *housing_config_sources]
            if source_url
        )
    )
    transport_sources = list(
        dict.fromkeys([*school_source, config["transport_url"]])
    )
    housing = _available_or_missing(
        profile.housing_summary,
        "目前可讀取的校方頁面沒有公布交換生宿舍配置、保證床位或房價；錄取後要直接向接待窗口確認宿舍校區、房型與付款期限。",
    )
    transport = _available_or_missing(
        profile.transport_summary,
        "校方公開頁面尚未提供可核對的機場／車站到校路線；出發前應把報到校區、宿舍地址與接待窗口電話存在離線備忘錄。",
    )
    campus = _available_or_missing(
        profile.campus_life_summary,
        "校方公開頁面未提供足夠的交換生活細節；錄取後應索取迎新、選課、校園卡、保險與國際生服務清單。",
    )

    sources = {source.source_url: source for source in profile.sources}
    for source in config["shared_sources"]:
        sources.setdefault(source.source_url, source)

    sections = [
        StudentGuideSection(
            key="courses_and_workload",
            title="課程、選課與會不會很嚴",
            summary=(
                "現有公開資料不足以替整間學校下『嚴格／輕鬆』結論；點名、報告、考試與評分通常由課程和教師決定。"
                "錄取後要用當期課表、課綱與學分規則逐門確認。"
            ),
            points=[
                "先確認交換生可修學院、授課語言、最低／最高學分與加退選期限。",
                "向系所或學長姐詢問每門課的點名、分組報告、期中期末與補考規則。",
                f"目前校方生活／交換資料可確認的範圍：{campus}",
            ],
            source_urls=school_source,
            evidence_type="official",
            caution="課程難度會隨學期、教師與科系改變，不能把單一心得當成全校規則。",
        ),
        StudentGuideSection(
            key="faculty_and_teaching",
            title="師資與上課方式怎麼判斷",
            summary=(
                "師資名單應以要交換的院系官網和當期課表為準；若公開交換頁未列授課教師，就保留為待確認，不以學校名氣代替教學品質。"
            ),
            points=[
                "選課前查看教師頁、課綱、授課語言與考核比例。",
                "若課名相同但教師不同，仍要分開判斷工作量與評分方式。",
                "準備抵免學分時，先保存課綱 PDF、課程時數與評量方式。",
            ],
            source_urls=school_source,
            evidence_type="practical_inference",
            caution="目前沒有足夠官方資料時，頁面會明確標示，而不自行產生教師評價。",
        ),
        StudentGuideSection(
            key="housing_reality",
            title="宿舍、房型與入住雷點",
            summary=housing,
            points=[
                "問清楚床位是否保證、住宿校區、房型、人數、衛浴、冷暖氣、洗衣、餐食與門禁。",
                "不要在不知道床墊尺寸、宿舍是否供寢具前，先從臺灣帶整套棉被。",
                "校外租屋要先確認合約、押金／禮金或管理費、保證人規則及通勤時間。",
            ],
            source_urls=housing_sources,
            evidence_type="mixed",
            caution="住宿費、押金與房型最容易隨學期變動，付款前再核對錄取通知。",
        ),
        StudentGuideSection(
            key="neighborhood_and_daily_life",
            title="學校附近機能與日常採買",
            summary=(
                f"目前能從校方資料確認的生活／交通重點：{transport} "
                "公開頁沒有列出的超商、醫療、夜間交通與採買範圍，抵達前應用宿舍的精確地址再查一次。"
            ),
            points=[
                "先找宿舍到上課校區、最近車站／公車站、超市、藥局與醫院。",
                "把宿舍當地語言地址、校區名稱與國際處電話下載到離線備忘錄。",
                "第一次採買先買三天份用品，再依宿舍收納與氣候補齊。",
            ],
            source_urls=transport_sources,
            evidence_type="mixed",
            caution="商店與交通路線變動快，地圖結果需在出發前重新確認。",
        ),
        StudentGuideSection(
            key="mobile_money_and_cards",
            title="門號、現金、付款與辦卡",
            summary=config["mobile_summary"],
            points=config["mobile_points"],
            source_urls=list(
                dict.fromkeys([*config["payment_urls"], *config["living_urls"]])
            ),
            evidence_type="mixed",
            caution="電信、銀行 KYC、支付與交易限額會變動，出發前及抵達後各確認一次。",
        ),
        StudentGuideSection(
            key="transport_and_arrival",
            title="到校交通與第一天怎麼活下來",
            summary=transport,
            points=config["transport_points"],
            source_urls=transport_sources,
            evidence_type="mixed",
            caution="機場接送、校區與報到地點以錄取通知為準。",
        ),
    ]

    first_72_hours = [
        StudentGuideChecklistItem(
            title="完成宿舍入住並取得收據",
            detail="向宿舍櫃台確認房號、押金／收據、門禁、網路、垃圾分類、洗衣與緊急聯絡方式。",
            source_urls=housing_sources,
            timing="抵達當天",
            evidence_type="mixed",
        ),
        StudentGuideChecklistItem(
            title="取得可用網路與本地門號",
            detail=config["phone_detail"],
            source_urls=config["living_urls"],
            timing="第 1 天",
            evidence_type="official",
        ),
        StudentGuideChecklistItem(
            title=config["residence_title"],
            detail=config["residence_detail"],
            source_urls=config["living_urls"],
            timing=config["residence_timing"],
            evidence_type="official",
        ),
        StudentGuideChecklistItem(
            title="完成學校報到與校園帳號",
            detail="帶錄取文件、護照與照片完成國際處／院系報到，確認學生證、校園卡、網路、保險與緊急聯絡方式。",
            source_urls=school_source,
            timing="第 1–2 天",
            evidence_type="official",
        ),
        StudentGuideChecklistItem(
            title="設定付款與交通備援",
            detail=config["payment_detail"],
            source_urls=list(
                dict.fromkeys([*config["payment_urls"], config["transport_url"]])
            ),
            timing="前 72 小時",
            evidence_type="mixed",
        ),
    ]

    packing_from_taiwan = [
        StudentGuideChecklistItem(
            title="入境、錄取與住宿文件",
            detail=config["documents_detail"],
            source_urls=list(
                dict.fromkeys([*school_source, *config["living_urls"]])
            ),
            timing="出發前",
            evidence_type="official",
        ),
        StudentGuideChecklistItem(
            title="可收驗證碼的臺灣門號與備援付款",
            detail="確認漫遊或最低資費可收簡訊，帶一張開啟海外交易的實體卡與少量當地現金。",
            source_urls=config["payment_urls"],
            timing="出發前",
            evidence_type="practical_inference",
        ),
        StudentGuideChecklistItem(
            title="常用藥與處方說明",
            detail="帶個人固定用藥、英文處方或診斷說明；液體與大量藥品先查航空及入境規定。",
            timing="出發前",
            evidence_type="practical_inference",
        ),
        StudentGuideChecklistItem(
            title="手機、充電與離線資料",
            detail="確認手機已解鎖、充電器支援當地電壓，離線保存宿舍地址、報到流程、接待人與緊急聯絡方式。",
            source_urls=school_source,
            timing="出發前",
            evidence_type="practical_inference",
        ),
    ]

    buy_after_arrival = [
        StudentGuideChecklistItem(
            title="本地 SIM 與合適流量方案",
            detail="依實際上課、導航、外送與視訊需求選方案；先確認涵蓋交換期間的合約與解約方式。",
            source_urls=config["living_urls"],
            timing="抵達後",
            evidence_type="official",
        ),
        StudentGuideChecklistItem(
            title="符合宿舍尺寸的寢具",
            detail="先看床型、冷暖氣與校方提供品項，再買床墊、被子、枕頭和收納用品。",
            source_urls=housing_sources,
            timing="入住後",
            evidence_type="practical_inference",
        ),
        StudentGuideChecklistItem(
            title=config["transport_purchase_title"],
            detail=config["transport_purchase_detail"],
            source_urls=[config["transport_url"]],
            timing="開始通勤前",
            evidence_type="official",
        ),
        StudentGuideChecklistItem(
            title="季節衣物與日用品",
            detail="先帶三天份基本用品，抵達並確認宿舍收納、城市氣候與校園穿著需求後再補買。",
            source_urls=school_source,
            timing="入住後",
            evidence_type="practical_inference",
        ),
    ]

    note = profile.coverage_note.split("；另以", 1)[0].rstrip("。")
    note += (
        f"；另以{config['country_note']}，"
        "校方未公開的師資、課程難度、房型與周邊機能仍明確標示待確認。"
    )
    return profile.model_copy(
        update={
            "student_guide_sections": sections,
            "first_72_hours": first_72_hours,
            "packing_from_taiwan": packing_from_taiwan,
            "buy_after_arrival": buy_after_arrival,
            "sources": list(sources.values()),
            "coverage_note": note,
        }
    )


def apply_shared_student_survival_guide(
    profile: DestinationProfile,
) -> DestinationProfile:
    """Fill a transparent, source-backed baseline for researched partners.

    School-specific official summaries stay primary. Country-level guidance is
    shared only for arrival logistics, and anything not publicly documented is
    explicitly marked for confirmation instead of being inferred as fact.
    """

    if profile.student_guide_sections:
        shared_urls = {source.source_url for source in ALL_SHARED_SOURCES}
        has_generated_baseline = any(
            source.source_url in shared_urls for source in profile.sources
        )
        if not has_generated_baseline:
            return profile

    regional_config = _regional_guide_config(profile.country or "")
    if regional_config:
        return _apply_regional_student_survival_guide(profile, regional_config)

    if profile.country != "大陸地區":
        return profile

    school_urls = _school_source_urls(profile)
    school_source = school_urls[:2]
    living_sources = [CHINA_LIVING_GUIDE_URL, TAIWAN_TRAVEL_PERMIT_URL]
    payment_sources = [CHINA_PAYMENT_GUIDE_URL, CHINA_LIVING_GUIDE_URL]
    housing = _available_or_missing(
        profile.housing_summary,
        "目前可讀取的校方頁面沒有公布交換生住宿配置、保證床位或房價；錄取後要直接向接待窗口確認宿舍校區、房型與付款期限。",
    )
    transport = _available_or_missing(
        profile.transport_summary,
        "校方公開頁面尚未提供可核對的機場／車站到校路線；出發前應把報到校區、宿舍中文地址與接待窗口電話存在離線備忘錄。",
    )
    campus = _available_or_missing(
        profile.campus_life_summary,
        "校方公開頁面未提供足夠的交換生活細節；錄取後應索取迎新、選課、校園卡、保險與國際生服務清單。",
    )

    sources = {source.source_url: source for source in profile.sources}
    for source in CHINA_SHARED_SOURCES:
        sources.setdefault(source.source_url, source)

    sections = [
        StudentGuideSection(
            key="courses_and_workload",
            title="課程、選課與會不會很嚴",
            summary=(
                "現有公開資料不足以替整間學校下『嚴格／輕鬆』結論；點名、報告、考試與評分通常由課程和教師決定。"
                "錄取後要用當期課表、課綱與學分規則逐門確認。"
            ),
            points=[
                "先確認交換生可修學院、授課語言、最低／最高學分與加退選期限。",
                "向系所或學長姐詢問每門課的點名、分組報告、期中期末與補考規則。",
                f"目前校方生活／交換資料可確認的範圍：{campus}",
            ],
            source_urls=school_source,
            evidence_type="official",
            caution="課程難度會隨學期、教師與科系改變，不能把單一心得當成全校規則。",
        ),
        StudentGuideSection(
            key="faculty_and_teaching",
            title="師資與上課方式怎麼判斷",
            summary=(
                "師資名單應以要交換的院系官網和當期課表為準；若公開交換頁未列授課教師，就先保留為待確認，不以學校名氣代替教學品質。"
            ),
            points=[
                "選課前查看教師頁、課綱、授課語言與考核比例。",
                "若課名相同但教師不同，仍要分開判斷工作量與評分方式。",
                "準備抵免學分時，先保存課綱 PDF、課程時數與評量方式。",
            ],
            source_urls=school_source,
            evidence_type="practical_inference",
            caution="目前沒有足夠官方資料時，頁面會明確標示，而不自行產生教師評價。",
        ),
        StudentGuideSection(
            key="housing_reality",
            title="宿舍、房型與入住雷點",
            summary=housing,
            points=[
                "問清楚床位是否保證、住宿校區、房型、人數、衛浴、冷暖氣、洗衣與門禁。",
                "不要在不知道床墊尺寸、宿舍是否供寢具前，先從臺灣帶整套棉被。",
                "校外租屋要先確認能否辦住宿登記，並保存合約、房東聯絡方式與付款紀錄。",
            ],
            source_urls=school_source,
            evidence_type="official",
            caution="住宿費、押金與房型最容易隨學期變動，付款前再核對錄取通知。",
        ),
        StudentGuideSection(
            key="neighborhood_and_daily_life",
            title="學校附近機能與日常採買",
            summary=(
                f"目前能從校方資料確認的生活／交通重點：{transport} "
                "公開頁沒有列出的超商、醫療、夜間交通與外送範圍，抵達前應用宿舍的精確地址再查一次。"
            ),
            points=[
                "先找宿舍到上課校區、最近地鐵／公車站、超市、藥局與醫院。",
                "把宿舍中文地址、校區名稱與國際處電話下載到離線備忘錄。",
                "第一次採買先買三天份用品，再依宿舍收納與氣候補齊。",
            ],
            source_urls=school_source,
            evidence_type="mixed",
            caution="商店與交通路線變動快，地圖結果需在出發前重新確認。",
        ),
        StudentGuideSection(
            key="mobile_money_and_cards",
            title="門號、現金、行動支付與辦卡",
            summary=(
                "官方生活指南提供境外人士持有效證件到電信自營門市辦 SIM，並以微信、支付寶、雲閃付、銀行卡與人民幣現金付款的做法；"
                "臺灣交換生應攜台胞證，實際受理文件與能否開戶要以當地門市、銀行及校方說明為準。"
            ),
            points=[
                "出發前保留一張可收臺灣簡訊的門號，避免銀行或帳號驗證中斷。",
                "抵達後優先辦本地門號，再綁定校園 App、外送、叫車與支付服務。",
                "行動支付未完成前保留小額人民幣現金與可海外交易的實體卡。",
                "不要把『能綁國際卡』等同於每家店、每筆交易都一定成功。",
            ],
            source_urls=payment_sources + [TAIWAN_TRAVEL_PERMIT_URL],
            evidence_type="practical_inference",
            caution="銀行 KYC、平台實名與交易限額會變動，出發前及抵達後各確認一次。",
        ),
        StudentGuideSection(
            key="transport_and_arrival",
            title="到校交通與第一天怎麼活下來",
            summary=transport,
            points=[
                "不要只存學校名稱；要存報到校區、宿舍名稱、中文地址與接待窗口。",
                "官方指南列出鐵路 12306、地鐵單程票／交通碼、公車現金或支付碼及叫車 App 等方式。",
                "身分驗證或行動支付尚未完成時，先走人工櫃檯並保留人民幣零錢。",
            ],
            source_urls=list(dict.fromkeys(school_source + living_sources)),
            evidence_type="mixed",
            caution="機場接送、校區與報到地點以錄取通知為準。",
        ),
    ]

    first_72_hours = [
        StudentGuideChecklistItem(
            title="完成宿舍入住並確認住宿登記",
            detail="向宿舍櫃台確認房號、押金／收據、門禁、網路及住宿登記是否已代辦；若需自行辦理，立即向校方確認窗口。",
            source_urls=list(dict.fromkeys(school_source + [TAIWAN_TRAVEL_PERMIT_URL])),
            timing="抵達當天",
            evidence_type="mixed",
        ),
        StudentGuideChecklistItem(
            title="取得可用網路與本地門號",
            detail="先用機場／校園 Wi-Fi 聯絡接待人，再持台胞證依門市規定申辦本地 SIM；保留臺灣門號收驗證碼。",
            source_urls=living_sources,
            timing="第 1 天",
            evidence_type="practical_inference",
        ),
        StudentGuideChecklistItem(
            title="設定付款備援",
            detail="先測試國際卡、微信／支付寶綁卡與一筆小額支付，同時保留人民幣現金；辦中國銀行卡前先問校方推薦網點與文件。",
            source_urls=payment_sources,
            timing="第 1–2 天",
            evidence_type="official",
        ),
        StudentGuideChecklistItem(
            title="完成學校報到與校園卡",
            detail="帶錄取文件、台胞證與照片完成國際處／院系報到，確認學生證、校園卡、網路、保險與緊急聯絡方式。",
            source_urls=school_source,
            timing="第 1–2 天",
            evidence_type="official",
        ),
        StudentGuideChecklistItem(
            title="鎖定選課與第一週期限",
            detail="登入教務系統，確認授課校區、時間、加退選、學分上下限與抵免所需課綱；遇到權限問題立刻找接待窗口。",
            source_urls=school_source,
            timing="前 72 小時",
            evidence_type="practical_inference",
        ),
    ]

    packing_from_taiwan = [
        StudentGuideChecklistItem(
            title="證件與錄取文件原件",
            detail="台胞證、臺灣身分證、錄取／提名文件、保險、住宿通知與證件照；另做加密雲端備份與紙本影本。",
            source_urls=[TAIWAN_TRAVEL_PERMIT_URL] + school_source,
            timing="出發前",
            evidence_type="official",
        ),
        StudentGuideChecklistItem(
            title="可收驗證碼的臺灣門號與備援付款",
            detail="確認漫遊或最低資費可收簡訊，帶一張開啟海外交易的實體卡與少量人民幣現金。",
            source_urls=payment_sources,
            timing="出發前",
            evidence_type="practical_inference",
        ),
        StudentGuideChecklistItem(
            title="常用藥與處方說明",
            detail="帶個人固定用藥、英文／中文處方或診斷說明；液體與大量藥品先查航空及入境規定。",
            timing="出發前",
            evidence_type="practical_inference",
        ),
        StudentGuideChecklistItem(
            title="手機、充電與離線資料",
            detail="確認手機已解鎖、充電器支援當地電壓，離線保存宿舍地址、報到流程、接待人與緊急聯絡方式。",
            source_urls=school_source,
            timing="出發前",
            evidence_type="practical_inference",
        ),
    ]

    buy_after_arrival = [
        StudentGuideChecklistItem(
            title="本地 SIM 與合適流量方案",
            detail="依實際上課、導航、外送與視訊需求選方案，不必在臺灣先買長約。",
            source_urls=[CHINA_LIVING_GUIDE_URL],
            timing="抵達後",
            evidence_type="official",
        ),
        StudentGuideChecklistItem(
            title="符合宿舍尺寸的寢具",
            detail="先看床型、暖氣／冷氣與校方提供品項，再買床墊、被子、枕頭和收納用品。",
            source_urls=school_source,
            timing="入住後",
            evidence_type="practical_inference",
        ),
        StudentGuideChecklistItem(
            title="盥洗、洗衣與清潔用品",
            detail="先買三天份日用品，確認共用浴室、洗衣付款方式與宿舍收納後再補齊。",
            source_urls=school_source,
            timing="入住後",
            evidence_type="practical_inference",
        ),
        StudentGuideChecklistItem(
            title="交通卡或城市乘車碼",
            detail="先試用單程票；確認每天通勤路線後，再決定辦實體交通卡或開通支付 App 乘車碼。",
            source_urls=[CHINA_LIVING_GUIDE_URL],
            timing="開始通勤後",
            evidence_type="official",
        ),
    ]

    note = profile.coverage_note.split("；另以", 1)[0].rstrip("。")
    note += (
        "；另以中國政府與移民管理官方指南補足門號、支付、交通及台胞證的共同落地流程，"
        "校方未公開的師資、課程難度、房型與周邊機能仍明確標示待確認。"
    )
    return profile.model_copy(
        update={
            "student_guide_sections": sections,
            "first_72_hours": first_72_hours,
            "packing_from_taiwan": packing_from_taiwan,
            "buy_after_arrival": buy_after_arrival,
            "sources": list(sources.values()),
            "coverage_note": note,
        }
    )
