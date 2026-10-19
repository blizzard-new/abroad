"""Original editorial checklists. Country facts stay linked to official authorities."""
from .seo_articles import ARTICLES

COUNTRIES = {
    "japan": {"name": "日本", "aliases": {"日本"},
        "intro": "赴日交換先確認可選方案的授課語言、學期與校區，再比較學費協議、宿舍及日常支出。日本語授課與英語授課方案的門檻可能不同，同一校內也可能依學院而異。",
        "checks": [("語言與課程", "逐一核對方案接受的日語或英語證明、成績效期，以及交換生能否選修目標課程。不要把某一方案的語言門檻套用到整所大學。"),
                   ("生活費與住宿", "用目的地城市與宿舍實際報價編列日圓預算，分開估算房租、水電、交通、餐費、保險與入住初期費用。JASSO 的平均值可作參考，但不是個人的保證支出。"),
                   ("學期與入境", "確認春秋學期與臺灣校曆是否衝突，並依合作校通知準備在留資格與入境文件；先取得錄取及住宿安排，再決定不可退的行程。")],
        "sources": [("JASSO：日本留學與生活費", "https://www.studyinjapan.go.jp/en/life/cost-of-living/"),
                    ("日本外務省：留學簽證", "https://www.mofa.go.jp/j_info/visit/visa/long/visa6.html")]},
    "south-korea": {"name": "韓國", "aliases": {"韓國", "南韓", "大韓民國"},
        "intro": "赴韓交換要分清楚英語與韓語授課、各學院選課限制，以及宿舍是否另行申請。學校的合作關係並不代表所有課程都對交換生開放。",
        "checks": [("語言與選課", "核對合作方案需要 TOPIK、英語證明或其他條件，再查看當學期實際開課語言與先修限制。免繳語言成績不等於所有課程都能選。"),
                   ("生活費與住宿", "以韓元分列宿舍或租屋、押金、餐費、交通、保險與通訊。首爾及其他城市的支出可能不同；以合作校當期宿舍與費用公告為準。"),
                   ("申請與入境", "校內甄選、母校提名、合作校申請與簽證是不同步驟。依錄取身分在官方入口確認適用簽證，不直接套用其他學生的經驗。")],
        "sources": [("韓國政府 Study in Korea", "https://www.studyinkorea.go.kr/"),
                    ("Korea Visa Portal", "https://www.visa.go.kr/")]},
    "germany": {"name": "德國", "aliases": {"德國"},
        "intro": "赴德交換先確認授課語言、學期時間與課程學分，再拆開比較學費、學期費、保險與住宿。合作協議免學費，不代表沒有其他校方費用或生活支出。",
        "checks": [("語言與學分", "核對英語或德語門檻、模組開課學期及學分採認方式。先與母校確認 Learning Agreement 或課程計畫，避免將課程目錄視為一定能修讀。"),
                   ("生活費與保險", "用歐元分列房租與押金、學期費、餐費、交通及保險。所需財力證明與實際生活預算是不同概念，適用金額需查閱申請當時的官方規定。"),
                   ("住宿與入境", "確認宿舍申請是否與交換申請分開，以及保險、簽證或居留手續的時程；不要假設獲得交換名額就一定有宿舍。")],
        "sources": [("DAAD：德國留學規劃", "https://www.daad.de/en/studying-in-germany/"),
                    ("德國外交部：簽證與居留資訊", "https://www.auswaertiges-amt.de/en/visa-service")]},
}

# Article files are the single source for routes, cards and sitemap membership.
GUIDES = {slug: article.model_dump(mode="json") for slug, article in ARTICLES.items()}


def country_slug(country: str | None) -> str | None:
    return next((slug for slug, data in COUNTRIES.items() if (country or "").strip() in data["aliases"]), None)
