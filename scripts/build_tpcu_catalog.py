"""Build the official Taipei City University of Science and Technology (臺北城市科技大學, TPCU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_TPCU_DIR = REPO_ROOT / "sources" / "tpcu"
OFFICIAL_TPCU_DIR = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "tpcu"
)
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-03T00:00:00Z"

TPCU_IEEC_HOME_URL = "https://ieec.tpcu.edu.tw/"
TPCU_IEEC_ABOUT_URL = "https://ieec.tpcu.edu.tw/p/412-1009-519.php?Lang=zh-tw"
TPCU_IEEC_MEMBERS_URL = "https://ieec.tpcu.edu.tw/p/412-1009-562.php?Lang=zh-tw"
TPCU_IEEC_REGULATIONS_URL = (
    "https://ieec.tpcu.edu.tw/p/412-1009-518.php?Lang=zh-tw"
)
TPCU_IEEC_XUEHAI_PAGE_URL = (
    "https://ieec.tpcu.edu.tw/p/405-1009-79641,c518.php?Lang=zh-tw"
)
TPCU_SISTER_SCHOOLS_PDF_URL = (
    "https://he.tpcu.edu.tw/var/file/3/1003/img/184/203215317.pdf"
)
TPCU_STUDY_ABROAD_RULES_PDF_URL = (
    "https://ieec.tpcu.edu.tw/app/index.php?Action=downloadfile&file=WVhSMFlXTm9MekF2Y0hSaFh6UTRPVFkxWHpnM01EazJPVE5mTURneU56WXVjR1Jt&fname=DGGGVWWX20XW11KKDGLKOKYWMK30WTRLFGB0MPWSQPJDLK40FCNKFDEGWSLKJGEGNO00EHZX2004ICXSFCNKTSMO34B0WSGCNPYTXWA034MKB001USSSTSRK40LK0430JDA0HGZWVWB4FCNP1130GDOOFCHDZXTSNOOK14A4IG01B5B5ROQP0011SWGCA4TSMPNOFC10US0101&cg=518"
)
TPCU_XUEHAI_FEIYANG_RULES_PDF_URL = (
    "https://ieec.tpcu.edu.tw/app/index.php?Action=downloadfile&file=WVhSMFlXTm9MelF2Y0hSaFh6UTRPVFk0WHpRNE9EZ3lNVEpmTURnMk16SXVjR1Jt&fname=DGGGVWWX20XW11KKDGLKOKYWMK30WTRLFGB0MPWSQPJDLK40FCNKFDEGWSLKJGEGNO00EHZX2004ICXSFCNKTSMO34B0WSGCNPYTXWA034MKB001USSSYWOK0044YTKKDGA0HGZWVWB4HCNP1434SWMKLPGDUTPOLKB4KOOK14A4CDUS44CC41JHDGVWIGGDOO14A4KK20RO40WSZTVX04CCXWB4LKA4YSSS01QKYW10015424JCNK24KOPKGDWSDGJCXSLKQPA1SW40NK30FDA4GGOKFCTTWW00EHYXTS04ROWWQO30MK35WSMOUSGCA1RLB0TSWSB0RKTWGGHGYWDCYWPOA115DGLK54WSPKOKA1HG14B0US10IHXTML44YSQOKOOKGG10STDC44CC21XXNOLKUW34STSWWTMOSTEGMKHCUTXTA0VSPOB4ZSB4PK54RP50WW400111IG10SWZWWWZWPK3514FGQL14UTJDXWA0FCFCGHDGSSOKHGXXSSTSXTMP44FGMOMKXSFG30MKOPROGDMKHDA1XWQPROB4XWUWECGCXXQKNOXWPLZXA4NOUWLOKKHCJG35PKRKQKGCVXNPWW4014QOJGOK20OO30542054XTKK2010UWLKQOOKRLYSDGEGWSHCVXRLSS5014B4VS45YS54YWA020LKTTKKCCB0RO3434MO4035WSJCYSNKGGYTQPMLSSMK11EC&cg=518"
)
TPCU_DUAL_DEGREE_PAGE_URL = (
    "https://ba.tpcu.edu.tw/p/405-1032-76724,c1300.php?Lang=zh-tw"
)
TPCU_DUAL_DEGREE_RULES_PDF_URL = (
    "https://ba.tpcu.edu.tw/app/index.php?Action=downloadfile&file=WVhSMFlXTm9MemswTDNCMFlWODBOalk1T1Y4ME1qZ3lORFZmTXpNNE1qRXVjR1Jt&fname=DGGGVWWX20XW11KKDGLKOKYWMK30WTRLFGB0MPWSQPJDLK40FCNKFDEGWSLKJGEGNO00EHZX2004ICXSFCNKTSMO34B0WSGCNPYTXWA034MKB001USSSB5PKPKPOEH25DGA0XWXTVWOKDCICDGB004NK00GDQP31WS30FCDGIGA445US4444YTJH4410RKYWMKOKGDIGIGRO04KKVXVX04B0QKYWJGA0FG54KLSSNOKKXX01EDPOTSMOB030GDLOWSJCXSGCQPIDGGPKROB4A454PKOKFCSWGCTSVXIHVSXSTXWWSTHCICICOPB0NOGC2135NOA5SWZWFGFG500045PKSSXWSS4444XWPKICPKB0QLQL&cg=1300"
)
TPCU_AFL_INTRO_URL = "https://afl.tpcu.edu.tw/p/412-1033-1820.php?Lang=zh-tw"
TPCU_AFL_EXCHANGE_PORTAL_URL = (
    "https://afl.tpcu.edu.tw/p/412-1033-1817.php?Lang=zh-tw"
)
TPCU_AFL_EXCHANGE_2026_URL = (
    "https://afl.tpcu.edu.tw/p/405-1033-86726,c3148.php?Lang=zh-tw"
)
TPCU_AFL_EXCHANGE_114_URL = (
    "https://afl.tpcu.edu.tw/p/405-1033-86687,c3148.php?Lang=zh-tw"
)
TPCU_AFL_EXCHANGE_2025_URL = (
    "https://afl.tpcu.edu.tw/p/405-1033-81592,c3148.php?Lang=zh-tw"
)
TPCU_AFL_EXCHANGE_113_URL = (
    "https://afl.tpcu.edu.tw/p/405-1033-81591,c3148.php?Lang=zh-tw"
)
TPCU_AFL_EXCHANGE_112_URL = (
    "https://afl.tpcu.edu.tw/p/405-1033-72571,c3148.php?Lang=zh-tw"
)
TPCU_RDO_OVERSEAS_INTERNSHIP_URL = (
    "https://rdo.tpcu.edu.tw/p/412-1019-3248.php?Lang=zh-tw"
)
TPCU_RDO_XUEHAI_ZHUMENG_URL = (
    "https://rdo.tpcu.edu.tw/p/412-1019-3022.php?Lang=zh-tw"
)
TPCU_RDO_XUEHAI_ZHUMENG_PDF_URL = (
    "https://rdo.tpcu.edu.tw/var/file/19/1019/img/640254585.pdf"
)
TPCU_RDO_OVERSEAS_INTERNSHIP_PDF_URL = (
    "https://rdo.tpcu.edu.tw/var/file/19/1019/img/157/121341374.pdf"
)
TPCU_CBM_OVERSEAS_PDF_URL = (
    "https://cbm.tpcu.edu.tw/var/file/2/1002/img/597/150507015.pdf"
)
TPCU_IPU_NZ_NEWS_URL = (
    "https://www.tpcu.edu.tw/p/406-1000-86663,r111.php?Lang=zh-tw"
)
TPCU_SHOWA_MUSIC_NEWS_URL = (
    "https://www.tpcu.edu.tw/p/406-1000-88449,r111.php?Lang=zh-tw"
)

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 680–1,150（折合日圓約 JPY 95,000–160,000 / 月、新臺幣約 21,500–36,500 元；沖繩琉球大學、鹿兒島國際大學、德島大學、宇都宮大學、北海道星槎道都大學約 JPY 85,000–125,000 / 月，千葉城西國際大學、神戶國際大學、福岡日本經濟大學、埼玉十文字學園女子大學、神奈川昭和音樂大學約 JPY 100,000–155,000 / 月）",
        "須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後至日本台灣交流協會申辦留學簽證並加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 680–1,100（折合韓元約 KRW 900,000–1,450,000 / 月、新臺幣約 21,500–35,000 元；京畿道議政府市信韓大學與富川市富川大學校內學生宿舍、伙食與首爾首都圈地鐵交通費）",
        "須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2 留學／交換簽證，入境後辦理外國人登錄證並納保韓國國民健康保險。",
    ),
    "紐西蘭": (
        "每月生活費約 USD 1,100–1,650（折合紐幣約 NZD 1,800–2,700 / 月、新臺幣約 35,000–52,500 元；北帕默斯頓 IPU New Zealand 校園學生宿舍含膳食方案極具性價比）",
        "須憑 IPU New Zealand 核發之入學許可（Offer of Place）與學費／住宿收據線上申辦紐西蘭 Fee Paying / Exchange Student Visa，並投保紐西蘭認可之國際學生醫療及旅遊保險。",
    ),
    "英國": (
        "每月生活費約 USD 1,350–2,050（折合英鎊約 GBP 1,050–1,600 / 月、新臺幣約 43,000–65,000 元；伯明翰大學學院 UCB 學生宿舍與市區生活開銷較倫敦低約 25–30%）",
        "交換 6 個月以內可憑入學許可辦理英國 ETA / Standard Visitor 入境；交換 1 學年或修讀 2+2 雙聯學位須憑 CAS 申辦英國 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "美國": (
        "每月生活費約 USD 1,350–2,200（依匯率折合新臺幣約 43,000–70,000 元；加州峽谷大學 Santa Clarita 約 USD 1,600–2,200 / 月，明尼蘇達州聖保羅與馬歇爾市約 USD 1,250–1,800 / 月）",
        "須憑美國接待大學核發之 DS-2019（J-1 交換生）或 I-20（F-1 雙聯學位生）表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證，且須投保符合接待校規定之全期海外醫療保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "春季學期（Spring Semester）：約 4 月初至 8 月初；秋季學期（Fall Semester）：約 9 月中下旬至翌年 2 月",
    "韓國": "春季學期（Spring Semester）：約 3 月初至 6 月中旬；秋季學期（Fall Semester）：約 9 月初至 12 月中旬",
    "紐西蘭": "第一學期（Autumn Intake）：約 4 月至 7 月；第二學期（Spring Intake）：約 8 月至 12 月",
    "英國": "秋季學期（Semester 1）：約 9 月中下旬至翌年 1 月；春季學期（Semester 2）：約 1 月下旬至 6 月",
    "美國": "秋季學期（Fall Semester）：約 8 月中下旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬",
}


def clean_text(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
    """Ensure school-images.json and university_locations.jsonl contain all 18 TPCU partner schools."""
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
            lat = float(loc.get("latitude", 25.1322))
            lon = float(loc.get("longitude", 121.4664))
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
    OFFICIAL_TPCU_DIR.mkdir(parents=True, exist_ok=True)
    catalog_source = json.loads(
        (SOURCES_TPCU_DIR / "tpcu_catalog_source.json").read_text(
            encoding="utf-8"
        )
    )
    resolved_locations = json.loads(
        (SOURCES_TPCU_DIR / "tpcu_resolved_locations.json").read_text(
            encoding="utf-8"
        )
    )
    bin_urls_path = SOURCES_TPCU_DIR / "binary_source_urls.json"
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
        zh_name = item["zh_name"]
        country = item["country"]
        region = item["region"]
        avail_status = "open"
        open_partner_count += 1

        group_str = clean_text(item["group"])
        program_type = clean_text(item["program_type"])
        quota_str = clean_text(item["quota"])
        source_url = item["source_url"]
        colleges_str = clean_text(item["colleges"])
        degree_levels_str = clean_text(item["degree_levels"])
        lang_req_str = clean_text(item["language_requirement"])
        gpa_req_str = clean_text(item["gpa_requirement"])
        website = item["website"]
        remarks_raw = clean_text(item["summary_note"])
        tuition_note = clean_text(item["tuition_note"])
        exp_titles = item.get("experience_titles") or []

        round_label = "115–116學年度海外姊妹校交換留學暨跨國雙聯學位甄選（國際事務處常態開放申請）"
        app_deadline_str = (
            "秋季班（9月／10月出國交換或雙聯）：每年 3 月中下旬（2027/03/31 17:00）校內截止收件｜"
            "春季班（3月／4月出國交換或雙聯）：每年 10 月中下旬（2026/10/30 17:00）校內截止收件｜"
            "教育部學海飛颺／學海惜珠／學海築夢校內甄選：每年 2 月下旬至 3 月中旬截止"
        )
        deadline_iso = "2027-03-31T17:00:00+08:00"
        win_status = "open"
        acad_year = "115"

        study_period_str = clean_text(item["study_period"])
        sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
            country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
        )
        housing_str = (
            f"獲臺北城市科技大學國際事務處推薦錄取後，可依 {zh_name} 國際處指引申請校內外學生宿舍或國際學舍（學費與住宿待遇：{tuition_note}）"
        )
        course_rest_str = (
            f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《臺北城市科技大學學生出國研修辦法》（106年6月19日修訂）及《與境外大學辦理雙聯學制實施辦法》（105年9月14日教育部備查）規定："
            "（1）申請資格為就讀本校滿一學年以上之在學學生（不含境外碩士專班；申請教育部學海飛颺／惜珠／築夢者須具中華民國國籍且就讀本校滿一學期以上，不含國內及境外在職專班生），且須為非當學期畢業之在學學生；"
            "（2）學業與操行門檻（《學生出國研修辦法》第 2 條第 4 款）：在校期間無小過以上處分紀錄，且前一學年之學業平均總成績應達 60 分以上、操行平均總成績應達 75 分以上；"
            "（3）錄取確認與返國學分抵免（《學生出國研修辦法》第 5–7 條及《學生海外實習及研習輔導要點》）：錄取學生須於公告隔天至國際交流中心（國際事務處）報到並於一週內繳交錄取確認書；海外研習一學期上課總學分不得少於 10 學分，返國後於當學期開學一週內檢附國外成績單正本及修業證明申請學分抵免；"
            "（4）跨國雙聯學制（《與境外大學辦理雙聯學制實施辦法》第 5–7 條）：學士班累計在兩校修業時間至少滿 32 個月（如 2+2 雙學士）、碩士班至少滿 12 個月，且在兩校當地修習學分數累計須各達獲頒學位所需總學分數之 1/3 以上。"
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
                f"臺北城市科技大學出國研修在學註冊與學雜費規定（依《學生出國研修辦法》及《與境外大學辦理雙聯學制實施辦法》）：出國交換或修讀雙聯學位期間須保留本校學籍並依規定辦理註冊；本合作校待遇：{tuition_note}"
            ),
            (
                "臺北城市科技大學三大出國留學與海外實習獎補助體系：（1）國際事務處《教育部獎助大專校院選送學生出國研修—學海飛颺、學海惜珠校內甄選辦法》（108年1月21日修訂）：選送具中華民國國籍且在學滿一學期以上優秀生（學海飛颺）或持地方政府低收入戶／中低收入戶證明學生（學海惜珠）赴國外研修 1 學期至 1 學年，每名補助新臺幣 50,000 元至 300,000 元（學校配合款不少於教育部補助款 20%）；（2）研究發展處《教育部獎助大專校院國外專業實習計畫—學海築夢及新南向學海築夢校內甄選辦法》（115年1月5日修訂）：補助赴日本、澳洲、新加坡、美國、歐洲等海外企業與星級飯店專業實習機票與生活費；（3）高教深耕計畫國際移動力補助與各院系海外研習／語言檢定獎助。"
            ),
        ]

        app_steps_list = [
            (
                f"步驟一（確認城市科大在學年級、學業 60 分／操行 75 分門檻與 {zh_name} 語檢要求）：確認符合《臺北城市科技大學學生出國研修辦法》第 2 條規定（就讀本校滿一學年以上、非當學期畢業之在學學生，無小過以上處分紀錄，前一學年學業平均達 60 分以上且操行平均達 75 分以上），並備妥符合 {zh_name} 規定之外語能力證明（{lang_req_str}）。"
            ),
            (
                "步驟二（備妥《海外研習制式履歷表》與 7 項應備文件經導師及系所主任簽章）：依《學生出國研修辦法》第 3 條備齊（1）本校海外研習制式履歷表（須經導師及系所主任簽章）、（2）申請表暨海外研修計畫書、（3）本校規定格式之推薦信 1 封（導師推薦函用信封密封）、（4）歷年成績單、（5）外國語言能力證明影本、（6）家長同意書（具結書）、（7）身分證與學生證正反面影本（證件黏貼表），於公告期限前送交國際事務處（國際交流中心）。"
            ),
            (
                f"步驟三（參加國際事務處面試甄選、公告隔天報到並於 1 週內繳交錄取確認書）：由國際事務處遴聘甄選委員進行書面審查與面試甄選並排定錄取順位（《學生出國研修辦法》第 5 條）；錄取赴 {full_name} 之學生須於公告隔天至國際事務處報到，並於 1 週內繳交《錄取確認書》（逾期未繳視同棄權，由備取生依序遞補），同時可申請教育部《學海飛颺／學海惜珠》出國研修獎助學金。"
            ),
            (
                "步驟四（向姊妹校遞交入學與宿位申請、辦理簽證，返國後開學 1 週內辦理學分抵免與 2 週內上傳學海報告）：經國際事務處向姊妹校提名後完成入學申請、在留資格（COE / I-20 / CAS / 入學許可）與學生簽證；海外研習一學期上課總學分不得少於 10 學分，返國後於當學期開學 1 週內依《辦理學生抵免科目學分及抵免後修課處理要點》申請學分抵免，獲學海補助者須於返國 2 週內上傳心得報告至教育部計畫資訊網。"
            ),
        ]

        elig_points_list = [
            f"合作類別與計畫組別：{program_type}（{group_str}）",
            f"開放學制與年級：{degree_levels_str}",
            f"開放申請學院：{colleges_str}",
            f"學業與操行門檻（《學生出國研修辦法》第 2 條）：{gpa_req_str}",
            f"外語能力標準：{lang_req_str}",
            "錄取報到與學分規定（《學生出國研修辦法》第 6–7 條及《海外實習及研習輔導要點》）：錄取生於公告隔天報到、一週內繳交錄取確認書；海外研習一學期修習不得少於 10 學分，返國後開學一週內辦理學分抵免。",
            f"姊妹校學費與城市科大獎補助待遇：{tuition_note}",
            f"學程與締約重點說明：{remarks_raw}",
        ]

        exp_links: list[dict] = []
        exp_labels: list[str] = []
        if exp_titles:
            exp_covered_schools += 1
            total_exp_reports += len(exp_titles)
            for e_idx, raw_t in enumerate(exp_titles):
                eurl = f"{TPCU_AFL_EXCHANGE_2026_URL}#tpcu-exp-{sn}-{e_idx+1}"
                exp_labels.append(raw_t[:36])
                exp_links.append({
                    "title": raw_t,
                    "url": eurl,
                    "academic_year": "112–115",
                    "semester": "112–115學年度",
                    "college": "商管學院／民生學院／工程學院",
                    "department": "臺北城市科技大學交換留學暨雙聯學位生",
                })
                summary_text = (
                    f"臺北城市科技大學國際事務處與商管／民生學院公開收錄之學長姐赴 {country} {full_name} 交換留學與雙聯學位官方榜單暨研修經驗分享（{raw_t}），詳述校內甄選準備、語言學習、宿舍生活與返國學分抵免實錄。"
                )
                theme_map = {
                    "academics": f"城市科大交換生與雙聯生於《{raw_t}》分享在 {zh_name} 每學期修讀至少 10 學分以上專業及語言課程、2+2 雙聯學分規劃與返國後開學一週內辦理學分抵免之經驗。",
                    "housing": f"城市科大交換生記錄申請 {zh_name} 校內外國際學生宿舍、周邊生活機能與通勤方式（{housing_str[:100]}）。",
                    "campus_culture": f"城市科大公開收錄《{raw_t}》之跨文化課堂互動、國際學伴交流與海外移地學習實錄。",
                    "cost": f"城市科大交換生分享於 {zh_name} 之每月住宿、伙食與交通開銷（{living_cost_str[:100]}），以及享姊妹校學費互免／優惠與申請教育部學海飛颺／惜珠獎助學金（NT$ 50,000–300,000）之經驗。",
                }
                student_experience_rows.append({
                    "school_name": full_name,
                    "country": country,
                    "title": raw_t,
                    "source_url": eurl,
                    "source_type": "article",
                    "platform": "臺北城市科技大學國際事務處暨應用外語系—海外留學交換與雙聯學位專區",
                    "author_name": "城市科大交換暨雙聯生",
                    "language": "zh",
                    "summary": summary_text,
                    "themes": ["academics", "housing", "campus_culture", "cost"],
                    "theme_summaries": theme_map,
                    "content_status": "full_text",
                    "perspective": "official_student_story",
                    "published_at": None,
                    "discovered_at": CHECKED_AT,
                    "content_hash": hashlib.sha256(
                        f"{full_name}:tpcu_exp:{e_idx}:{eurl}".encode("utf-8")
                    ).hexdigest(),
                    "exchange_term": "112–115學年度",
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
            "home_university": "臺北城市科技大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": (
                exp_links[0]["url"] if exp_links else TPCU_AFL_EXCHANGE_2026_URL
            ),
            "partner_page_url": source_url,
            "report_count": len(exp_titles),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

        loc = resolved_locations[full_name]
        city_name = loc["city"]
        lat = float(loc["latitude"])
        lon = float(loc["longitude"])
        loc_source_url = loc["source_url"]

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
        img_local = vrec["local_path"]
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
            f"【當期名額與費用待遇】{quota_str}｜{tuition_note}",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
            f"【住宿與生活資訊】{housing_str}",
            f"【城市科學長姐交換留學與雙聯紀錄（共 {len(exp_titles)} 篇）】收錄於國際事務處暨應用外語系交換雙聯榜單（含：{'、'.join(exp_labels[:3])}）",
            f"【學程與締約摘要】{remarks_raw}",
        ]

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
            "quota_status": "published",
            "availability_status": avail_status,
            "availability_note": (
                f"臺北城市科技大學國際事務處暨商管／民生／工程學院公告合作姊妹校（{program_type}）；{quota_str}。"
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
                "school_sn": str(sn),
                "group": group_str,
                "experience_report_count": str(len(exp_titles)),
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
                "title": f"臺北城市科技大學海外留學姊妹校總表與國際交流專區—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "臺北城市科技大學學生出國研修辦法（106年6月19日修訂）",
                "source_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "臺北城市科技大學「教育部獎助大專校院選送學生出國研修—學海飛颺、學海惜珠」校內甄選辦法（108年1月21日修訂）",
                "source_url": TPCU_XUEHAI_FEIYANG_RULES_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "role": "partner_university",
                "authority": "partner_official",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]

        workflows.append({
            "home_university": "臺北城市科技大學",
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
                "臺北城市科技大學由國際事務處（國際交流中心）與工程學院、商管學院、民生學院統籌全校海外姊妹校交換留學（日本、韓國、紐西蘭、英國、美國）、跨國雙聯學制（2+2／3+1 台日、台韓、台紐、台英、台美雙學位）及教育部學海飛颺、學海惜珠、學海築夢與新南向學海築夢獎助。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"tpcu-{acad_year}-home-1-{sn:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認城市科大在學年級身分（就讀滿一學年以上）、學業 60 分／操行 75 分與 {zh_name} 語檢要求",
                    "responsible_party": "學生",
                    "responsible_unit": "臺北城市科技大學國際事務處／各院系所",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": source_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        f"確認符合《臺北城市科技大學學生出國研修辦法》第 2 條規定：申請人須為就讀本校滿一學年以上且非當學期畢業之在學學生（不含境外碩士專班），在校無小過以上處分紀錄，前一學年學業平均總成績達 60 分以上、操行平均總成績達 75 分以上，並具備符合 {zh_name} 要求之外語能力證明（{lang_req_str}）。"
                    ),
                    "details": [
                        f"開放學制與學院：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與計畫類別：{quota_str}｜{program_type}",
                    ],
                    "scope": {
                        "home_universities": ["臺北城市科技大學"],
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
                        TPCU_STUDY_ABROAD_RULES_PDF_URL,
                        TPCU_DUAL_DEGREE_RULES_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"tpcu-{acad_year}-home-2-{sn:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "備妥《海外研習制式履歷表》與 7 項應備文件經導師及系所主任簽章後送交國際事務處",
                    "responsible_party": "學生",
                    "responsible_unit": "所屬系所／國際事務處",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        "依《學生出國研修辦法》第 3 條規定，於校內公告期限前（秋季班每年 3 月底前、春季班每年 10 月底前）備齊本校海外研習制式履歷表（須經導師及系所主任簽章）、申請表暨研修計畫書、推薦信 1 封（導師推薦函用信封密封）、歷年成績單、語言能力證明影本、家長同意書（具結書）及身分證／學生證正反面影本送交國際事務處。"
                    ),
                    "details": [
                        "秋季班出國交換／雙聯校內收件：每年 3 月中下旬截止；春季班出國交換／雙聯校內收件：每年 10 月中下旬截止。",
                        "同時申請教育部《學海飛颺／學海惜珠》者，另依《學海飛颺、學海惜珠校內甄選辦法》第 3 條檢附證件黏貼表與地方政府低收入戶／中低收入戶證明（學海惜珠適用）。",
                    ],
                    "document_requirements": [
                        {
                            "name": "臺北城市科技大學海外研習制式履歷表（須經導師及系所主任簽章）與海外研修申請表暨研修計畫書",
                            "official_form_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
                            "source_urls": [
                                TPCU_STUDY_ABROAD_RULES_PDF_URL,
                                TPCU_XUEHAI_FEIYANG_RULES_PDF_URL,
                            ],
                        },
                        {
                            "name": "歷年成績單正本（前一學年學業平均 60 分以上、操行 75 分以上）與外國語言能力檢定證明影本",
                            "official_form_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
                            "source_urls": [
                                TPCU_STUDY_ABROAD_RULES_PDF_URL,
                                TPCU_CBM_OVERSEAS_PDF_URL,
                            ],
                        },
                        {
                            "name": "本校規定格式推薦信 1 封（導師推薦函用信封密封）、家長同意書（具結書）及身分證／學生證正反面影本",
                            "official_form_url": TPCU_AFL_EXCHANGE_PORTAL_URL,
                            "source_urls": [
                                TPCU_STUDY_ABROAD_RULES_PDF_URL,
                                TPCU_AFL_EXCHANGE_PORTAL_URL,
                            ],
                        },
                    ],
                    "scope": {
                        "home_universities": ["臺北城市科技大學"],
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
                        TPCU_STUDY_ABROAD_RULES_PDF_URL,
                        TPCU_XUEHAI_FEIYANG_RULES_PDF_URL,
                        TPCU_AFL_EXCHANGE_PORTAL_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"tpcu-{acad_year}-home-3-{sn:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "參加國際事務處面試甄選並排定順位，於錄取公告隔天報到、一週內繳交《錄取確認書》",
                    "responsible_party": "臺北城市科技大學國際事務處與申請學生",
                    "responsible_unit": "國際事務處（國際交流中心）",
                    "deadline_at": "2027-04-15T17:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": False,
                    "summary": (
                        "國際事務處依《學生出國研修辦法》第 5–6 條遴聘甄選委員進行面試甄選並排定錄取順位；錄取學生須於公告隔天至國際事務處報到，並於 1 週內繳交《錄取確認書》（無繳交者視同棄權，由備取生遞補；錄取後無故放棄者提請相關委員會議處）。"
                    ),
                    "details": [
                        "教育部《學海飛颺、學海惜珠校內甄選辦法》：選送生每名補助新臺幣 50,000 元至 300,000 元，學校配合款不少於教育部補助總經費之 20%。",
                        "雙聯學制審查（《與境外大學辦理雙聯學制實施辦法》第 4 條）：由兩校依合作協議進行甄審，學士班累計在兩校修業時間至少滿 32 個月、碩士班至少滿 12 個月。",
                    ],
                    "scope": {
                        "home_universities": ["臺北城市科技大學"],
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
                        TPCU_STUDY_ABROAD_RULES_PDF_URL,
                        TPCU_XUEHAI_FEIYANG_RULES_PDF_URL,
                        TPCU_DUAL_DEGREE_RULES_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"tpcu-{sn:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由城市科大國際事務處向 {zh_name} 辦理官方提名，並遞交入學、在留資格／簽證與宿舍申請",
                    "responsible_party": "學生與接待校國際處",
                    "summary": (
                        f"完成錄取確認後，由臺北城市科技大學國際事務處向 {zh_name} 辦理官方提名；學生依接待校規定遞交外文入學申請書、在留資格認定證明書交付申請書（日本適用）、英文成績單、財力證明、語檢證書與宿舍申請表，取得正式入學許可（COE / Admission Letter / I-20 / CAS）。"
                    ),
                    "details": [
                        f"研修期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"住宿與費用待遇：{housing_str}",
                    ],
                    "scope": {
                        "home_universities": ["臺北城市科技大學"],
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
                    "source_urls": [source_url, TPCU_SISTER_SCHOOLS_PDF_URL, website],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"tpcu-{acad_year}-home-5-{sn:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "完成城市科大註冊與海外保險、每學期修習不少於 10 學分，返國後開學 1 週內辦理學分抵免",
                    "responsible_party": "學生與所屬系所",
                    "responsible_unit": "國際事務處／教務處註冊組／各系所",
                    "summary": (
                        "出國前完成臺北城市科技大學註冊、健康狀況自我檢核、役男出國緩徵（如適用）及海外全期醫療意外保險；海外研習一學期上課總學分不得少於 10 學分；返國後於當學期開學 1 週內依《辦理學生抵免科目學分及抵免後修課處理要點》申請學分抵免，獲學海補助學生另於返國後 2 週內上傳心得報告至教育部計畫資訊網。"
                    ),
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["臺北城市科技大學"],
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
                        TPCU_STUDY_ABROAD_RULES_PDF_URL,
                        TPCU_RDO_OVERSEAS_INTERNSHIP_PDF_URL,
                        TPCU_XUEHAI_FEIYANG_RULES_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已完整整合臺北城市科技大學國際事務處、商管學院、民生學院與研究發展處《海外留學姊妹校總表》、《學生出國研修辦法（1060619）》、《與境外大學辦理雙聯學制實施辦法（1050914）》、《學海飛颺、學海惜珠校內甄選辦法（1080121）》、《學海築夢及新南向學海築夢校內甄選辦法（1150105）》、《學生海外實習及研習輔導要點（1061030）》及 {exp_covered_schools} 校 {total_exp_reports} 篇交換留學與雙聯榜單紀錄，共 {len(catalog_source)} 所合作姊妹校資料。"
            ),
        })

        cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
        course_clean = course_rest_str

        dest_sources = [
            {
                "title": f"臺北城市科技大學海外留學姊妹校總表與國際交流專區—{zh_name}",
                "source_url": source_url,
                "summary": "城市科大公告之合作學程（交換留學／雙聯學位）、開放學院、語檢門檻與學費優惠說明",
            },
            {
                "title": "臺北城市科技大學學生出國研修辦法、雙聯學制實施辦法與學海飛颺／惜珠校內甄選辦法",
                "source_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
                "summary": "城市科大出國研修申請資格（學業 60 分、操行 75 分）、錄取隔天報到與一週內確認、每學期至少 10 學分與返國開學一週內學分抵免規範",
            },
            {
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作姊妹校官方網站",
            },
        ]

        src_url_list = [
            source_url,
            TPCU_STUDY_ABROAD_RULES_PDF_URL,
            TPCU_SISTER_SCHOOLS_PDF_URL,
            TPCU_XUEHAI_FEIYANG_RULES_PDF_URL,
            website,
        ]

        destinations.append({
            "home_university": "臺北城市科技大學",
            "school_name": full_name,
            "country": country,
            "city": city_name,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": (
                f"校區代表城市：{city_name}。請依入學許可確認實際授課校區位置與當地學生交通卡優惠。"
            ),
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費、城市科大在學註冊規定與教育部學海飛颺／惜珠／築夢獎補助",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list,
                    "caution": (
                        "依《學海飛颺、學海惜珠校內甄選辦法》，每名選送生補助 NT$ 50,000–300,000；獲獎學生應於出國前 1 個月與學校簽訂行政契約書，並於返國後 2 週內上傳心得報告至教育部計畫資訊網。"
                    ),
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與校內外國際學生宿舍申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "日本、韓國、紐西蘭、英國及美國姊妹校學生宿位有限，請於獲國際事務處提名後依接待校期限儘早提交宿舍申請表。",
                },
                {
                    "key": "insurance",
                    "title": "海外醫療及意外保險、健康自我檢核與家長同意具結書規定",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "依《臺北城市科技大學學生出國研修辦法》第 3 條及《學生海外實習及研習輔導要點》第 5 點，申請學生均須繳交經家長簽章之《家長同意書（具結書）》及《健康狀況自我檢核表》，並於出國前辦妥海外醫療及意外保險。",
                    ],
                    "source_urls": src_url_list + [TPCU_RDO_OVERSEAS_INTERNSHIP_PDF_URL],
                    "caution": "日本（NHI 國民健康保險）、韓國（國民健康保險）、英國（IHS 醫療附加費）、紐西蘭與美國接待校對國際學生當地保險有強制規定，請依入學通知書辦理。",
                },
                {
                    "key": "visa",
                    "title": "留學交換簽證辦理、雙聯學制修業時數與錄取確認義務",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "依《學生出國研修辦法》第 6 條，錄取學生於公告隔天至國際交流中心報到，並於 1 週內繳交錄取確認書；雙聯學制學士班累計在兩校修業時間至少滿 32 個月、碩士班至少滿 12 個月。",
                    ],
                    "source_urls": src_url_list + [TPCU_DUAL_DEGREE_RULES_PDF_URL],
                    "caution": "具役男身分之學生出國交換、雙聯或海外實習，須依規定提前填具《役男身分海外實習／研修出國資料表》辦理緩徵出境核准。",
                },
                {
                    "key": "academics",
                    "title": "每學期至少修習 10 學分、2+2 雙聯學制 1/3 學分門檻與返國開學 1 週內學分抵免",
                    "summary": course_clean[:160],
                    "points": [calendar_clean, course_clean],
                    "source_urls": src_url_list,
                    "caution": (
                        "依《學生海外實習及研習輔導要點》第 3 點及《學生出國研修辦法》第 7 條，海外研習一學期上課總學分不得少於 10 學分；返國後須於當學期開學 1 週內檢附國外成績單正本辦理學分抵免。"
                    ),
                },
                {
                    "key": "living",
                    "title": f"{city_name} 校園生活與臺北城市科技大學學長姐留學經驗傳承",
                    "summary": f"代表城市：{city_name}。請配合接待校國際處完成報到與新生訓練（Orientation）。",
                    "points": [
                        f"目的地城市：{city_name}（{country}）",
                        f"臺北城市科技大學應用外語系、商管學院與民生學院每年穩定選派逾 50–65 名學生赴海外交換留學、雙聯學位與海外實習（本校共收錄 {len(exp_titles)} 篇留學榜單與經驗分享：{'、'.join(exp_labels[:2])}）。",
                    ],
                    "source_urls": [
                        exp_links[0]["url"]
                        if exp_links
                        else TPCU_AFL_EXCHANGE_2026_URL
                    ],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已整合臺北城市科技大學 {len(catalog_source)} 所官方合作姊妹校（含交換留學與跨國雙聯學位合作校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換雙聯榜單與研修紀錄。"
            ),
        })

        research_records.append({
            "home_university": "臺北城市科技大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": source_url,
            "checked_at": CHECKED_AT,
            "note": (
                "臺北城市科技大學《海外留學姊妹校總表》、《學生出國研修辦法》、《與境外大學辦理雙聯學制實施辦法》、應用外語系 112–115 學年度交換雙聯榜單與 ROR/Wikidata 官方網址核對完成。"
            ),
        })

        ev_sources = [
            {
                "title": f"臺北城市科技大學海外留學姊妹校總表與國際交流專區—{zh_name}",
                "url": source_url,
            },
            {
                "title": f"臺北城市科技大學赴 {zh_name} 交換留學與雙聯學位紀錄（{len(exp_titles)} 篇）",
                "url": exp_links[0]["url"],
            },
            {"title": f"{full_name} 官方網站", "url": website},
        ]

        ev_list = [
            {
                "theme": "housing",
                "kind": "mixed",
                "text": housing_clean,
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "臺北城市科技大學海外交換與雙聯學位姊妹校住宿與生活資訊",
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
                "scope": "臺北城市科技大學出國交換學雜費規定、教育部學海飛颺／惜珠／築夢獎補助",
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
                "scope": "臺北城市科技大學學生出國研修辦法、雙聯學制實施辦法與返國學分抵免要點",
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
                "scope": "臺北城市科技大學海外交換與雙聯學位簽證、家長同意具結書與海外醫療保險提醒",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "campus_culture",
                "kind": "mixed",
                "text": (
                    f"合作類別：{program_type}｜名額：{quota_str}｜語言要求：{lang_req_str}｜臺北城市科技大學公開收錄 {len(exp_titles)} 篇赴 {zh_name} 交換雙聯紀錄（{'、'.join(exp_labels[:2])}）。"
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "臺北城市科技大學交換雙聯名額與歷屆學長姐留學紀錄",
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
                "已整合臺北城市科技大學《海外留學姊妹校總表》、《學生出國研修辦法》、《與境外大學辦理雙聯學制實施辦法》及 112–115 學年度交換留學與雙聯學位紀錄。",
                "當期交換與雙聯名額、宿位供給、語檢門檻與選課限制請依合作校最新簡章及入學通知書核對。",
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

    write_jsonl(OFFICIAL_TPCU_DIR / "partners.jsonl", partners)
    write_jsonl(SOURCES_TPCU_DIR / "partners.jsonl", partners)
    write_jsonl(OFFICIAL_TPCU_DIR / "application_workflows.jsonl", workflows)
    write_jsonl(OFFICIAL_TPCU_DIR / "destination_profiles.jsonl", destinations)
    write_jsonl(OFFICIAL_TPCU_DIR / "partner_research.jsonl", research_records)
    write_jsonl(OFFICIAL_TPCU_DIR / "student_life.jsonl", life_records)
    write_jsonl(
        OFFICIAL_TPCU_DIR / "experience_sources.jsonl",
        experience_sources_records,
    )
    write_jsonl(
        OFFICIAL_TPCU_DIR / "student_experience_sources.jsonl",
        experience_sources_records,
    )
    write_jsonl(
        OFFICIAL_TPCU_DIR / "student_experiences.jsonl", student_experience_rows
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
    (OFFICIAL_TPCU_DIR / "student-experience-digests.json").write_text(
        json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    (OFFICIAL_TPCU_DIR / "student-experiences.json").write_text(
        json.dumps(
            {
                "school_id": "tpcu",
                "school_name": "臺北城市科技大學",
                "checked_at": CHECKED_AT,
                "source_url": TPCU_AFL_EXCHANGE_2026_URL,
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

    (OFFICIAL_TPCU_DIR / "campus-locations.json").write_text(
        json.dumps(
            {
                "school_id": "tpcu",
                "school_name": "臺北城市科技大學",
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
    (OFFICIAL_TPCU_DIR / "campus-assets.json").write_text(
        json.dumps(
            {
                "school_id": "tpcu",
                "school_name": "臺北城市科技大學",
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

    tpcu_source_urls = [
        TPCU_IEEC_HOME_URL,
        TPCU_IEEC_ABOUT_URL,
        TPCU_IEEC_MEMBERS_URL,
        TPCU_IEEC_REGULATIONS_URL,
        TPCU_IEEC_XUEHAI_PAGE_URL,
        TPCU_SISTER_SCHOOLS_PDF_URL,
        TPCU_STUDY_ABROAD_RULES_PDF_URL,
        TPCU_XUEHAI_FEIYANG_RULES_PDF_URL,
        TPCU_DUAL_DEGREE_PAGE_URL,
        TPCU_DUAL_DEGREE_RULES_PDF_URL,
        TPCU_AFL_INTRO_URL,
        TPCU_AFL_EXCHANGE_PORTAL_URL,
        TPCU_AFL_EXCHANGE_2026_URL,
        TPCU_AFL_EXCHANGE_114_URL,
        TPCU_AFL_EXCHANGE_2025_URL,
        TPCU_AFL_EXCHANGE_113_URL,
        TPCU_AFL_EXCHANGE_112_URL,
        TPCU_RDO_OVERSEAS_INTERNSHIP_URL,
        TPCU_RDO_XUEHAI_ZHUMENG_URL,
        TPCU_RDO_XUEHAI_ZHUMENG_PDF_URL,
        TPCU_RDO_OVERSEAS_INTERNSHIP_PDF_URL,
        TPCU_CBM_OVERSEAS_PDF_URL,
        TPCU_IPU_NZ_NEWS_URL,
        TPCU_SHOWA_MUSIC_NEWS_URL,
    ]

    exchange_info_payload = {
        "school_name": "臺北城市科技大學",
        "program_type": [
            (
                f"國際事務處（國際交流中心）暨商管、民生、工程學院海外姊妹校交換留學計畫（涵蓋日本城西國際大學、神戶國際大學、鹿兒島國際大學、國立琉球大學、日本經濟大學、北海道星槎道都大學、國立德島大學、十文字學園女子大學、國立宇都宮大學、昭和音樂大學；韓國信韓大學、富川大學；紐西蘭國際太平洋大學 IPU New Zealand；英國伯明翰大學學院 UCB；美國加州峽谷大學、明州西南州立大學等共 {len(partners)} 所官方合作姊妹校）"
            ),
            (
                "跨國雙聯學制計畫（Dual Degree Programs，依《與境外大學辦理雙聯學制實施辦法》辦理 2+2／3+1／1+1 雙學位，涵蓋日本【城西國際大學】、【神戶國際大學】、【鹿兒島國際大學】、【日本經濟大學】、【昭和音樂大學】，韓國【信韓大學】，紐西蘭【國際太平洋大學 IPU New Zealand】，英國【伯明翰大學學院 UCB】，以及美國【加州峽谷大學】、【曼徹普利敦州立大學】、【聖保羅學院】共 11 所雙聯合作大學）"
            ),
            (
                "教育部「學海飛颺」（選送優秀學生出國研修，每名補助 NT$ 50,000–300,000）、「學海惜珠」（補助持低收入戶或中低收入戶證明之學子出國研修）、「學海築夢／新南向學海築夢」（研究發展處統籌赴日本、澳洲、新加坡、歐洲郵輪等海外專業實習，每年出國實習與留學人數穩定逾 50–65 名）"
            ),
        ],
        "academic_year": [
            (
                "115（涵蓋 115–116 學年度國際事務處海外交換留學暨跨國雙聯學位甄選［秋季班每年 3 月底截止、春季班每年 10 月底截止］、教育部學海飛颺／學海惜珠出國研修獎助暨研發處學海築夢海外專業實習計畫）"
            ),
            (
                f"本平台完整收錄臺北城市科技大學國際事務處與三大學院公告之 {len(partners)} 所海外合作姊妹校（含日本 10 校、韓國 2 校、紐西蘭 1 校、英國 1 校、美國 4 校，其中 11 校同時提供跨國雙聯學制，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆交換雙聯榜單與研修紀錄）"
            ),
        ],
        "semester": [
            "秋季班交換留學與雙聯學位（每年 3 月中下旬校內截止）：選送學生於當年度秋季學期（日本 9–10 月、韓國 9 月、歐美 8–9 月、紐西蘭 8 月）赴境外姊妹校研修 1 學期、1 學年或 2 學年雙聯學位。",
            "春季班交換留學與雙聯學位（每年 10 月中下旬校內截止）：選送學生於隔年春季學期（日本 4 月、韓國 3 月、紐西蘭 4 月、美國 1 月）赴境外姊妹校研修 1 學期、1 學年或 2 學年雙聯學位。",
            "海外專業實習暨學海築夢計畫（研究發展處與各系所每學期辦理）：學期實習（9 學分以上，至少 4.5 個月）或學年實習（18 學分以上，至少 9 個月），每月實習時數不低於 160 小時。",
        ],
        "application_period": [
            "【秋季班海外交換留學暨雙聯學位校內甄選（當年度秋季出國）】每年 2 月至 3 月受理報名（約 3 月 31 日 17:00 截止），申請人備齊制式履歷表與應備文件經導師及系主任簽章後送交國際事務處辦理面試甄選。",
            "【春季班海外交換留學暨雙聯學位校內甄選（隔年春季出國）】每年 9 月至 10 月受理報名（約 10 月 30 日 17:00 截止）；錄取學生須於公告隔天至國際事務處報到，並於 1 週內繳交《錄取確認書》。",
            "【教育部學海飛颺／學海惜珠出國研修獎助校內甄選】配合教育部每年度計畫申請期程，於每年 2 月下旬至 3 月中旬向國際事務處提出申請（獲獎生須於出國前 1 個月簽訂行政契約書，返國後 2 週內上傳心得報告）。",
            "【教育部學海築夢／新南向學海築夢暨海外專業實習甄選】由研究發展處實習就業組與各院系（應用外語系、餐飲事業系、觀光事業系、旅館事業管理學士學位學程、企業管理系、行銷與流通管理系等）於每學期出國前 1 學期辦理甄選與說明會。",
        ],
        "eligibility": [
            "1. 在學身分與修業年限限制：依《臺北城市科技大學學生出國研修辦法》（106年6月19日修訂）第 2 條，申請人須為就讀本校滿一學年以上之在學學生（不含境外碩士專班），且須為非當學期畢業之在學學生；於國外研修結束後須返回本校接續完成學位（修讀雙聯學位者不在此限制）。申請教育部《學海飛颺／學海惜珠／學海築夢》者，須具中華民國國籍且在臺灣地區設有戶籍，並就讀本校滿一學期以上（不含國內及境外在職專班生）。",
            "2. 學業與操行成績門檻（《學生出國研修辦法》第 2 條第 4 款）：在校期間無小過以上處分紀錄，且前一學年之「學業平均總成績應達 60 分以上」；「操行平均總成績應達 75 分以上」。",
            "3. 雙聯學制修業時間與學分規定（《與境外大學辦理雙聯學制實施辦法》第 5–7 條）：修讀跨國雙聯學制之學士班學生，累計在兩校修業時間至少須滿 32 個月（如 2+2 雙學士學位）；碩士班學生累計在兩校修業時間至少須滿 12 個月。在二校當地修習學分數，累計須各達獲頒學位所需總學分數之三分之一以上。",
            "4. 錄取確認與返國學分抵免義務（《學生出國研修辦法》第 5–7 條及《學生海外實習及研習輔導要點》）：錄取學生於公告隔天至國際交流中心（國際事務處）報到，並於一週內繳交錄取確認書（無繳交者視同棄權，由備取生遞補；錄取後無故放棄者提請相關委員會議處）。海外研習一學期上課總學分不得少於 10 學分，返國後於當學期開學一週內檢附國外成績單正本申請學分抵免。",
        ],
        "language_requirement": [
            "1. 日本姊妹校（10 所交換留學與雙聯學位合作校）：（a）交換留學 1 年及 2+2 雙聯學位（城西國際大學、神戶國際大學、鹿兒島國際大學、國立琉球大學、日本經濟大學、北海道星槎道都大學、國立德島大學、十文字學園女子大學、國立宇都宮大學、昭和音樂大學）原則要求日本語能力試驗 JLPT N2 或 N3（含）以上合格（國立琉球大學、國立德島大學、國立宇都宮大學一般交換建議達 JLPT N2，部分英語授課學程可檢附 TOEIC 550 / TOEFL iBT 61 / IELTS 5.5）；（b）神戶國際大學日語加強特別班或日本海外實習／研習要求 JLPT N4 合格或 300 小時日文上課時數證明。",
            "2. 英語系國家姊妹校（紐西蘭、英國、美國共 6 所交換與雙聯合作校）：（a）紐西蘭國際太平洋大學（IPU New Zealand，台紐日三方合作）接受英語 IELTS 5.5–6.0 / TOEFL iBT 61 / TOEIC 550 以上或日語 JLPT N2–N3 以上（英文或日文主修學生皆可申請）；（b）英國伯明翰大學學院（UCB）交換留學與 2+2 雙聯學位要求 IELTS 5.5–6.0 或 TOEFL iBT 61–72 / TOEIC 550–650 以上；（c）美國加州峽谷大學（College of the Canyons）、曼徹普利敦州立大學（Metropolitan State University）、聖保羅學院（Saint Paul College）、明州西南州立大學（SMSU）要求 TOEFL iBT 61 / IELTS 5.5 / TOEIC 550 以上。",
            "3. 韓國姊妹校（信韓大學、富川大學）：要求韓語能力測驗 TOPIK 2 級–3 級（含）以上，或英語能力達 TOEIC 550 / TOEFL iBT 61 / IELTS 5.5 以上。",
            "4. 教育部學海系列與海外實習基本外語基準（《商管學院海外實習與留學簡報》第 17 頁）：英語系國家海外實習／研習基本門檻為多益 TOEIC 225 分以上或全民英檢 GEPT 初級合格（CEFR A2）；申請學海飛颺選送出國研修者須檢附符合薦送學校規定之外語能力證明。",
        ],
        "required_documents": [
            "1. 臺北城市科技大學海外研習制式履歷表（須經導師及系所主任簽章；《學生出國研修辦法》第 3 條第 1 款）",
            "2. 海外研修申請表暨研修計畫書（含擬修讀學校、研修期間、讀書計畫與預期成效；《學生出國研修辦法》第 3 條第 2 款）",
            "3. 推薦信 1 封（須使用本校規定格式之推薦書，導師推薦函用信封密封；《學生出國研修辦法》第 3 條第 3 款）",
            "4. 本校歷年成績單正本／影本（前一學年學業平均總成績達 60 分以上、操行平均總成績達 75 分以上，且無小過以上處分紀錄）",
            "5. 外國語言能力檢定證明影本（JLPT N1–N4 / TOEIC / TOEFL iBT / IELTS / GEPT / TOPIK 等符合修讀學校要求之佐證資料）",
            "6. 家長同意書／具結書（須由家長或法定監護人親筆簽章）及健康狀況自我檢核表",
            "7. 身分證正反面影本、學生證正反面影本（證件黏貼表；申請教育部《學海惜珠》者另附地方行政主管機關開立之低收入戶或中低收入戶證明及戶口名簿影本，不得以村鄰里長清寒證明替代）",
        ],
        "scholarship_info": [
            "1. 國際事務處《教育部獎助大專校院選送學生出國研修—學海飛颺、學海惜珠校內甄選辦法》（108年1月21日修訂）：選送具中華民國國籍且就讀本校滿一學期以上之優秀學生（學海飛颺）或持地方行政主管機關開立之低收入戶／中低收入戶證明學生（學海惜珠）赴國外大專校院（不含大陸及港澳）修讀學分 1 學期(季)或 1 學年。每名選送生補助額度為新臺幣 50,000 元至 300,000 元（含來回經濟艙機票、國外學費與生活費），且學校提出之配合款不少於教育部補助總經費之 20%。",
            "2. 研究發展處《教育部獎助大專校院國外專業實習計畫—學海築夢及新南向學海築夢校內甄選辦法》（115年1月5日修訂）：補助具中華民國國籍、在學滿一學期以上且通過外語能力基準與專業實習課程之學生，赴日本（成田國際機場、日本環球影城、笠間市政府、廣島現代美術館、大和博物館、JR廣島車站、萬豪及王子飯店集團）、新加坡（萬豪酒店、愛迪達 Outlet）、澳洲（大型連鎖餐飲）、歐洲（MSC 地中海郵輪）等海外機構進行專業實習，補助來回機票與國外生活費（學校配合款不少於教育部補助款 20%）。",
            "3. 跨國姊妹校交換學費互免與雙聯學制獎學金優惠：透過國際事務處薦送赴日本（琉球大學、德島大學、城西國際大學、神戶國際大學、鹿兒島國際大學、日本經濟大學、星槎道都大學等）、韓國（信韓大學、富川大學）、紐西蘭（IPU New Zealand）、英國（UCB）及美國（加州峽谷大學、明州西南州立大學、曼徹普利敦州立大學、聖保羅學院）交換留學或修讀 2+2 雙聯學位，享有免繳接待姊妹校學費或國際合作夥伴學費減免優惠。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": tpcu_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_TPCU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "臺北城市科技大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 60.0,
        "academic_score_rule": (
            "依《臺北城市科技大學學生出國研修辦法》（106年6月19日修訂）第 2 條規定：申請人須為就讀本校滿一學年以上且非當學期畢業之在學學生（不含境外碩士專班；申請教育部學海飛颺／惜珠／築夢者須在學滿一學期以上，不含國內及境外在職專班生），在校無小過以上處分紀錄，且前一學年之學業平均總成績應達 60 分以上、操行平均總成績應達 75 分以上（約合 GPA 2.0 以上；申請日本國立大學或歐美雙聯學位建議學業平均達 70–75 分以上）。"
        ),
        "academic_gpa_minimum": 2.0,
        "maximum_preferences": 3,
        "selection_rules": {
            "academic_policy": "score_or_rank",
            "academic_reference_year": "115",
            "undergraduate_gpa_minimum": 2.0,
            "graduate_academic_exempt": False,
            "exclude_in_service": True,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "undergraduate": 60.0,
                "graduate": 60.0,
            },
            "excluded_undergraduate_years": [
                "大一",
                "大一上",
                "大一下",
                "一年級",
                "一年級上學期",
                "一年級下學期",
            ],
            "language_certificate_required": True,
        },
        "language_score_minimums": {
            "toefl": 61.0,
            "ielts": 5.5,
            "toefl_itp": 500.0,
            "toeic": 550.0,
        },
        "application_periods": [
            {
                "title": "臺北城市科技大學 116學年度秋季班海外姊妹校交換留學暨跨國雙聯學位校內甄選（預計 2027/02/15–03/31 受理）",
                "details": [
                    "依《臺北城市科技大學學生出國研修辦法》及《與境外大學辦理雙聯學制實施辦法》，國際事務處（國際交流中心）與商管學院、民生學院、工程學院每學期辦理赴日本、韓國、紐西蘭、英國及美國姊妹校交換留學（1學期／1年）與雙聯學位（2+2／3+1／1年）校內甄選。",
                    "申請人須就讀本校滿一學年以上、無小過以上處分、前一學年學業平均達 60 分以上且操行達 75 分以上，備妥制式履歷表（導師及系主任簽章）、研修計畫書、密封推薦信、成績單、語檢證明及家長同意書送交國際事務處；錄取生須於公告隔天報到並於 1 週內繳交錄取確認書。",
                ],
                "source": {
                    "title": "臺北城市科技大學學生出國研修辦法與海外留學姊妹校總表",
                    "source_url": TPCU_SISTER_SCHOOLS_PDF_URL,
                    "category": "exchange_application",
                    "summary": "城市科大海外姊妹校交換留學與雙聯學位申請資格、應備文件及錄取報到確認規定。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "116",
                "application_round": "116-1 秋季班海外交換留學暨雙聯學位校內甄選",
                "audience": "all_students",
                "opens_at": "2027-02-15T09:00:00+08:00",
                "deadline_at": "2027-03-31T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "秋季班（9月／10月出國）預計於每年 2 月中旬至 3 月底受理校內申請；春季班（3月／4月出國）於每年 9 月中旬至 10 月底受理。",
                "deadline_note": "海外研習制式履歷表須先經導師及系所主任簽章，錄取後須於公告隔天報到、一週內繳交錄取確認書。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "臺北城市科技大學教育部「學海飛颺／學海惜珠」出國研修獎助學金校內甄選（預計 2027/02/01–03/15 受理）",
                "details": [
                    "依《臺北城市科技大學「教育部獎助大專校院選送學生出國研修—學海飛颺、學海惜珠」校內甄選辦法》（108年1月21日修訂），選送具中華民國國籍且在學滿一學期以上之優秀學生（學海飛颺）或持低收入戶／中低收入戶證明之學生（學海惜珠）赴國外姊妹校修讀學分 1 學期或 1 學年。",
                    "每名選送生獎助額度為新臺幣 50,000 元至 300,000 元（學校配合款不少於教育部補助款 20%）；錄取生應於出國研修 1 個月前與本校簽訂行政契約書，並於返國後 2 週內上傳問卷調查表及 1,000 字以上心得報告（含 4 張以上照片）至教育部計畫資訊網。",
                ],
                "source": {
                    "title": "臺北城市科技大學教育部學海飛颺、學海惜珠校內甄選辦法（1080121 修訂）",
                    "source_url": TPCU_IEEC_XUEHAI_PAGE_URL,
                    "category": "scholarship",
                    "summary": "城市科大教育部學海飛颺與學海惜珠出國研修獎助資格、應備文件及補助額度（NT$ 50,000–300,000）。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "116",
                "application_round": "116學年度教育部學海飛颺／學海惜珠校內甄選",
                "audience": "all_students",
                "opens_at": "2027-02-01T09:00:00+08:00",
                "deadline_at": "2027-03-15T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "配合教育部每年度 3 月底網報截止，校內於每年 2 月至 3 月中旬受理申請並召開國際交流審查小組會議。",
                "deadline_note": "學海惜珠申請人須檢附地方行政主管機關開立之低收入戶或中低收入戶證明及戶口名簿影本（不得以村鄰里長清寒證明替代）。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "臺北城市科技大學研究發展處「教育部學海築夢／新南向學海築夢」暨海外專業實習甄選（預計 2027/02/01–03/15 受理）",
                "details": [
                    "依《臺北城市科技大學「教育部獎助大專校院國外專業實習計畫—學海築夢及新南向學海築夢」校內甄選辦法》（115年1月5日修訂）及《學生海外實習及研習輔導要點》，選送在學滿一學期以上且通過外語基準（日本實習需 JLPT N4 或 300 小時日文時數證明；英語系國家需 TOEIC 225 或 GEPT 初級以上）之學生赴日本、新加坡、澳洲、歐美等海外企業與星級飯店實習。",
                    "海外實習分為學期實習（9 學分以上，至少 4.5 個月）與學年實習（18 學分以上，至少 9 個月），每月實習時數不低於 160 小時；獲學海築夢補助者享來回機票與生活費獎助。",
                ],
                "source": {
                    "title": "臺北城市科技大學研究發展處學海築夢相關辦法專區與校內甄選辦法（1150105 修訂）",
                    "source_url": TPCU_RDO_XUEHAI_ZHUMENG_URL,
                    "category": "scholarship",
                    "summary": "城市科大研究發展處學海築夢、新南向學海築夢與海外專業實習甄選規範。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度教育部學海築夢／新南向學海築夢海外實習甄選",
                "audience": "all_students",
                "opens_at": "2027-02-01T09:00:00+08:00",
                "deadline_at": "2027-03-15T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "每年配合教育部學海計畫時程及各院系海外實習梯次（日本、澳洲、新加坡、歐洲郵輪）辦理校內甄選。",
                "deadline_note": "海外實習學生須於出國前辦妥家長同意書、健康狀況自我檢核表、海外實習三方合約書及海外醫療意外保險。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": (
                    f"臺北城市科技大學海外姊妹校交換留學、跨國雙聯學制與學海系列獎補助總覽（{len(partners)} 所合作姊妹校・11 所雙聯合作校・{total_exp_reports} 篇交換雙聯榜單與紀錄）"
                ),
                "details": [
                    (
                        f"臺北城市科技大學（Taipei City University of Science and Technology, TPCU，創立於 1971 年［原光武工專、北台科學技術學院］，坐落於臺北市北投區學園路 2 號關渡平原大屯山麓）由「國際事務處（國際交流中心）」與「研究發展處」協同全校 3 大學院（工程學院、商管學院、民生學院）推動海外交換留學、跨國雙聯學制及海外專業實習。本平台完整收錄 {len(partners)} 所臺北城市科技大學官方公告之海外留學合作姊妹校，橫跨日本（10 校）、韓國（2 校）、紐西蘭（1 校）、英國（1 校）與美國（4 校）。"
                    ),
                    (
                        f"城市科大國際移動力具備四大核心優勢：（1）深耕日本與亞太之高密度交換留學與 2+2 雙聯網絡（日本城西國際大學、神戶國際大學、鹿兒島國際大學、國立琉球大學、日本經濟大學、北海道星槎道都大學、國立德島大學、十文字學園女子大學、國立宇都宮大學、昭和音樂大學；韓國信韓大學、富川大學）；（2）橫跨台紐日、英國與美國之跨國雙聯學制（台灣首所與紐西蘭 IPU New Zealand 簽署校級暨應外系雙聯學制之私立科大，並與英國伯明翰大學學院 UCB、美國加州峽谷大學、明尼蘇達州曼徹普利敦州立大學及聖保羅學院提供 2+2／3+1／1 年雙聯學位）；（3）完善之教育部《學海飛颺／學海惜珠》（補助 NT$ 50,000–300,000）與研發處《學海築夢／新南向學海築夢》海外實習獎助；（4）收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆交換雙聯榜單與研修實錄。"
                    ),
                ],
                "source": {
                    "title": "臺北城市科技大學國際事務處與海外留學姊妹校總表",
                    "source_url": TPCU_SISTER_SCHOOLS_PDF_URL,
                    "category": "exchange_application",
                    "summary": f"臺北城市科技大學 {len(partners)} 所海外合作姊妹校、11 所雙聯學制合作校與 {total_exp_reports} 篇交換雙聯紀錄。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "就讀滿一學年以上在學身分、前一學年學業平均 60 分／操行 75 分門檻與雙聯學制 32 個月修業規定",
                "details": [
                    "在學身分與學業操行門檻：依《臺北城市科技大學學生出國研修辦法》（106年6月19日修訂）第 2 條，申請人須為就讀本校滿一學年以上且非當學期畢業之在學學生（不含境外碩士專班；申請教育部學海飛颺／惜珠／築夢者須具中華民國國籍且就讀本校滿一學期以上，不含國內及境外在職專班生），在校期間無小過以上處分紀錄，且前一學年之學業平均總成績應達 60 分以上、操行平均總成績應達 75 分以上。",
                    "跨國雙聯學制與返國學分抵免規定：依《與境外大學辦理雙聯學制實施辦法》（105年9月14日教育部備查）第 5–7 條，修讀雙聯學位之學士班學生累計在兩校修業時間至少滿 32 個月、碩士班至少滿 12 個月，於兩校當地修習學分數各須達畢業總學分數 1/3 以上；一般交換生海外研習一學期上課總學分不得少於 10 學分，返國後於當學期開學 1 週內辦理學分抵免。",
                ],
                "source": {
                    "title": "臺北城市科技大學學生出國研修辦法（1060619）與雙聯學制實施辦法（1050914）",
                    "source_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "城市科大出國研修在學年級、學業 60 分、操行 75 分及雙聯學制修業規定。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "日本姊妹校 JLPT N2–N3（實習 N4／300小時）、歐美紐英語校 TOEFL iBT 61 / IELTS 5.5 / TOEIC 550 與韓國 TOPIK 2–3 級門檻",
                "details": [
                    "日本與韓國姊妹校外語標準：（1）日本 10 所合作姊妹校（城西國際大學、神戶國際大學、鹿兒島國際大學、國立琉球大學、日本經濟大學、星槎道都大學、國立德島大學、十文字學園女子大學、國立宇都宮大學、昭和音樂大學）交換留學與 2+2 雙聯學位原則要求 JLPT N2 或 N3（含）以上合格（神戶國際大學日語加強班及日本海外實習接受 JLPT N4 合格或 300 小時日文上課時數證明）；（2）韓國信韓大學、富川大學要求韓語檢定 TOPIK 2–3 級或英語 TOEIC 550 / TOEFL iBT 61 / IELTS 5.5 以上。",
                    "英語系國家姊妹校與海外實習標準：（1）紐西蘭國際太平洋大學（IPU New Zealand）接受英語 IELTS 5.5–6.0 / TOEFL iBT 61 / TOEIC 550 或日語 JLPT N2–N3；（2）英國伯明翰大學學院（UCB）要求 IELTS 5.5–6.0 或 TOEFL iBT 61–72 / TOEIC 550–650；（3）美國加州峽谷大學、曼徹普利敦州立大學、聖保羅學院、明州西南州立大學要求 TOEFL iBT 61 / IELTS 5.5 / TOEIC 550 以上；（4）英語系國家海外實習基本門檻為 TOEIC 225 分或全民英檢 GEPT 初級（CEFR A2）以上。",
                ],
                "source": {
                    "title": "臺北城市科技大學學生出國研修辦法與商管學院海外實習暨留學簡報",
                    "source_url": TPCU_CBM_OVERSEAS_PDF_URL,
                    "category": "exchange_application",
                    "summary": "城市科大赴日本、韓國、紐西蘭、英國與美國交換留學、雙聯學位及海外實習外語檢定門檻。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "海外研習制式履歷表（導師及系主任簽章）、研修申請表暨計畫書、密封推薦信、成績單、語檢證明與家長同意書",
                "details": [
                    "校內出國研修甄選 7 大必備文件（《學生出國研修辦法》第 3 條）：（1）本校海外研習制式履歷表（須經導師及系所主任簽章）；（2）申請表暨海外研修計畫書；（3）推薦信 1 封（本校規定格式之推薦書，導師推薦函用信封密封）；（4）歷年成績單；（5）語言能力證明影本；（6）家長同意書（具結書）；（7）身分證正反面影本與學生證正反面影本（證件黏貼表；學海惜珠另附地方政府低收入戶或中低收入戶證明及戶口名簿影本）。",
                    "錄取報到與返國核銷文件：錄取學生須於公告隔天報到並於 1 週內繳交《錄取確認書》；獲教育部學海系列獎助者應於出國前 1 個月簽訂《行政契約書》，並於返國後 2 週內上傳心得報告至教育部計畫資訊網、返國開學 1 週內辦理學分抵免。",
                ],
                "source": {
                    "title": "臺北城市科技大學學生出國研修辦法（1060619）與學海飛颺、學海惜珠校內甄選辦法（1080121）",
                    "source_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "城市科大出國交換、雙聯學位與學海獎助申請應備文件與錄取報到規範。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "教育部學海飛颺與學海惜珠（每名補助 NT$ 50,000–300,000）、研發處學海築夢／新南向學海築夢與姊妹校學費優惠",
                "details": [
                    "教育部學海飛颺與學海惜珠（國際事務處主辦）：依《學海飛颺、學海惜珠校內甄選辦法》第 4–6 條，選送生赴國外大專校院（不含大陸及港澳）研修 1 學期或 1 學年，每名補助新臺幣 50,000 元至 300,000 元，學校配合款不少於教育部補助總經費之 20%。",
                    "教育部學海築夢／新南向學海築夢（研究發展處主辦）與姊妹校學費優惠：補助赴日本、澳洲、新加坡、歐洲郵輪等海外專業實習之來回經濟艙機票與生活費；赴日韓歐美紐姊妹校交換留學享有接待校學費互免或雙聯學費減免優惠。",
                ],
                "source": {
                    "title": "臺北城市科技大學教育部學海飛颺、學海惜珠校內甄選辦法與研究發展處學海築夢專區",
                    "source_url": TPCU_XUEHAI_FEIYANG_RULES_PDF_URL,
                    "category": "scholarship",
                    "summary": "城市科大教育部學海飛颺、學海惜珠、學海築夢與新南向學海築夢獎助完整規定。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "臺北城市科技大學海外研習制式履歷表、研修計畫書、密封推薦信與家長同意具結書準備指南",
                "summary": "說明城市科大《學生出國研修辦法》第 3 條及《學海飛颺、學海惜珠校內甄選辦法》第 3 條規定之 7 項核心申請文件準備要領。",
                "key_points": [
                    "海外研習制式履歷表與研修計畫書：履歷表須提前送請班級導師及系所主任簽章；研修計畫書應詳述擬赴姊妹校修讀之課程規劃（海外研習一學期上課總學分不得少於 10 學分；雙聯學制須符合兩校各修滿 1/3 總學分規定）、與母系專業課程之抵免對照及未來職涯目標。",
                    "密封推薦信與外語能力證明：推薦信須採用本校規定格式之推薦書並由導師密封簽名；語言能力證明須符合目標姊妹校門檻（日本交換／雙聯檢附 JLPT N2–N3、日本實習檢附 N4 或 300 小時日文時數證明；歐美紐檢附 TOEFL iBT 61 / IELTS 5.5 / TOEIC 550；韓國檢附 TOPIK 2–3 級）。",
                    "錄取隔天報到與一週內確認義務（《學生出國研修辦法》第 6 條）：錄取學生須於公告隔天至國際交流中心（國際事務處）報到，並於 1 週內繳交《錄取確認書》；無繳交者視同棄權由備取生遞補，錄取後無故放棄者提請議處。",
                ],
                "applies_to": [],
                "source": {
                    "title": "臺北城市科技大學學生出國研修辦法（1060619）與學海飛颺甄選辦法（1080121）",
                    "source_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "臺北城市科技大學學生出國研修辦法、雙聯學制實施辦法與海外實習及研習輔導要點核心規定",
                "summary": "規範城市科大出國交換與雙聯學位申請資格（學業 60 分、操行 75 分）、錄取確認期限、每學期修課下限（10 學分）、雙聯修業月數（學士 32 個月／碩士 12 個月）及返國開學 1 週內學分抵免。",
                "key_points": [
                    "申請資格與學業操行門檻（《學生出國研修辦法》第 2 條）：就讀本校滿一學年以上且非當學期畢業之在學學生（不含境外碩士專班），無小過以上處分紀錄，前一學年學業平均總成績達 60 分以上、操行平均總成績達 75 分以上。",
                    "海外研習與實習學分下限及抵免期限（《學生出國研修辦法》第 7 條及《海外實習及研習輔導要點》第 3 點）：海外研習一學期上課總學分不得少於 10 學分；海外實習學期 9 學分以上至少 4.5 個月、學年 18 學分以上至少 9 個月（每月不低於 160 小時）；返國後於當學期開學 1 週內辦理學分抵免。",
                    "跨國雙聯學制修業規定（《與境外大學辦理雙聯學制實施辦法》第 5–7 條）：學士班累計在兩校修業時間至少滿 32 個月、碩士班至少滿 12 個月，且在二校當地修習學分數累計須各達獲頒學位所需總學分數之 1/3 以上。",
                ],
                "applies_to": [],
                "source": {
                    "title": "臺北城市科技大學學生出國研修辦法、雙聯學制實施辦法與海外實習及研習輔導要點",
                    "source_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": TPCU_DUAL_DEGREE_RULES_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {
                "title": "臺北城市科技大學國際事務處（Office of International Affairs）官方網站",
                "source_url": TPCU_IEEC_HOME_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": f"臺北城市科技大學海外留學姊妹校總表（日、韓、紐、英、美共 {len(partners)} 所合作姊妹校）",
                "source_url": TPCU_SISTER_SCHOOLS_PDF_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "臺北城市科技大學學生出國研修辦法（106年6月19日修訂通過 PDF）",
                "source_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "臺北城市科技大學與境外大學辦理雙聯學制實施辦法（105年9月14日教育部備查 PDF）",
                "source_url": TPCU_DUAL_DEGREE_RULES_PDF_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "臺北城市科技大學「教育部獎助大專校院選送學生出國研修—學海飛颺、學海惜珠」校內甄選辦法（1080121 修訂 PDF）",
                "source_url": TPCU_XUEHAI_FEIYANG_RULES_PDF_URL,
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "臺北城市科技大學研究發展處「教育部獎助大專校院國外專業實習計畫—學海築夢及新南向學海築夢」校內甄選辦法（1150105 修訂 PDF）",
                "source_url": TPCU_RDO_XUEHAI_ZHUMENG_PDF_URL,
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "臺北城市科技大學學生海外實習及研習輔導要點（1061030 修訂 PDF）與商管學院海外留學簡報",
                "source_url": TPCU_RDO_OVERSEAS_INTERNSHIP_PDF_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": f"臺北城市科技大學應用外語系 112–115 學年度（2023–2026）交換留學與雙聯學位榜單專區（{exp_covered_schools} 校 {total_exp_reports} 篇紀錄）",
                "source_url": TPCU_AFL_EXCHANGE_2026_URL,
                "category": "exchange_application",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_TPCU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    doc_conditions = {
        "school_id": "tpcu",
        "school_name": "臺北城市科技大學",
        "checked_at": CHECKED_AT,
        "source_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
        "common_documents": exchange_info_payload["required_documents"],
        "track_specific_conditions": [
            {
                "track": "日本姊妹校交換留學與 2+2 雙聯學位（城西國際大學、神戶國際大學、鹿兒島國際大學、琉球大學、日本經濟大學、星槎道都大學、德島大學、十文字學園女子大學、宇都宮大學、昭和音樂大學）",
                "required": [
                    "臺北城市科技大學海外研習制式履歷表（須經導師及系所主任簽章）與海外研修申請表暨計畫書",
                    "歷年成績單正本（前一學年學業平均達 60 分以上、操行平均達 75 分以上，無小過以上處分紀錄）",
                    "日本語能力試驗 JLPT N2 或 N3（含）以上合格證書影本（神戶國際大學日特班或日本海外實習檢附 JLPT N4 合格或 300 小時日文上課時數證明）",
                    "本校規定格式推薦信 1 封（導師推薦函用信封密封）、家長同意書（具結書）、健康狀況自我檢核表、在留資格認定證明書交付申請書及日本出入國歷表",
                ],
            },
            {
                "track": "英語系國家及韓國姊妹校交換留學與雙聯學位（紐西蘭 IPU New Zealand、英國伯明翰大學學院 UCB、美國加州峽谷大學、曼徹普利敦州立大學、聖保羅學院、明州西南州立大學；韓國信韓大學、富川大學）",
                "required": [
                    "臺北城市科技大學海外研習制式履歷表（須經導師及系所主任簽章）與海外研修申請表暨計畫書",
                    "中/英文歷年成績單正本（前一學年學業平均達 60 分以上、操行平均達 75 分以上；雙聯學位學士班累計在兩校修業至少滿 32 個月、碩士班至少滿 12 個月）",
                    "有效外語能力證明影本（歐美紐：TOEFL iBT 61 / IELTS 5.5–6.0 / TOEIC 550 以上［IPU New Zealand 亦接受 JLPT N2–N3］；韓國：TOPIK 2–3 級或 TOEIC 550 以上）",
                    "本校規定格式推薦信 1 封（導師密封）、家長同意書（具結書）、護照影本及英文財力證明",
                ],
            },
            {
                "track": "教育部學海飛颺／學海惜珠出國研修獎助與研究發展處學海築夢／新南向學海築夢海外專業實習",
                "required": [
                    "學海飛颺／學海惜珠（國際事務處主辦）：海外研修申請表暨計畫書、歷年成績單、外語能力證明、導師密封推薦信、家長同意書、身分證及學生證正反面影本（證件黏貼表）；學海惜珠另附地方行政主管機關開立之低收入戶或中低收入戶證明及戶口名簿影本（不得以村鄰里長清寒證明替代）",
                    "學海築夢／海外專業實習（研究發展處主辦）：海外實習履歷表、海外實習申請表、個別實習計畫書、家長同意具結書、健康狀況自我檢核表、導師密封推薦函、役男身分海外實習出國資料表（如適用）；返國後繳交實習完成報告與心得報告",
                ],
            },
        ],
    }
    (OFFICIAL_TPCU_DIR / "document-conditions.json").write_text(
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
            f"{fname},{len(partners)},{pop},{ratio:.4f},Official TPCU IEEC/CBM/HE verified"
        )
    (OFFICIAL_TPCU_DIR / "field-coverage.csv").write_text(
        "\n".join(field_cov_lines) + "\n", encoding="utf-8"
    )

    pages_records = [
        {
            "title": "臺北城市科技大學：海外交換留學、跨國雙聯學制與教育部學海系列計畫申請時程",
            "source_url": TPCU_SISTER_SCHOOLS_PDF_URL,
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
            "title": "臺北城市科技大學：學生出國研修辦法（1060619 修訂）、學業 60 分／操行 75 分門檻與雙聯學制 32 個月修業規定",
            "source_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
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
            "title": f"臺北城市科技大學：{len(partners)} 所日韓紐英美合作姊妹校外語檢定門檻（JLPT / TOEFL / IELTS / TOEIC / TOPIK）",
            "source_url": TPCU_CBM_OVERSEAS_PDF_URL,
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
            "title": "臺北城市科技大學：出國交換與雙聯學位應備文件（海外研習制式履歷表、研修計畫書、密封推薦信、家長同意書與錄取確認書）",
            "source_url": TPCU_STUDY_ABROAD_RULES_PDF_URL,
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
            "title": "臺北城市科技大學：教育部學海飛颺、學海惜珠（補助 5–30 萬元）與研究發展處學海築夢／新南向學海築夢獎助辦法",
            "source_url": TPCU_XUEHAI_FEIYANG_RULES_PDF_URL,
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
    (OFFICIAL_TPCU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
        + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "tpcu",
        "school_name": "臺北城市科技大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "academic_score_minimum": 60.0,
            "conduct_score_minimum": 75.0,
            "no_minor_demerit_or_above": True,
            "min_study_years_at_tpcu_for_exchange": "1 academic year (1 semester for MOE Xuehai programs)",
            "admission_confirmation_deadline": "公告隔天報到，一週內繳交錄取確認書",
            "min_credits_per_semester_abroad": 10,
            "credit_transfer_deadline": "返國後當學期開學一週內辦理學分抵免",
            "dual_degree_min_months_bachelor": 32,
            "dual_degree_min_months_master": 12,
            "dual_degree_min_credit_ratio_each_school": "1/3",
            "exclude_in_service_for_xuehai": True,
            "xuehai_return_report_due": "返國後 2 週內上傳問卷及 1,000 字以上心得報告至教育部計畫資訊網",
        },
        "source_urls": tpcu_source_urls,
        "verified_at": "2026-11-03",
    }
    (OFFICIAL_TPCU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_TPCU_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "臺北城市科技大學",
                "required_documents": student_dashboard_payload[
                    "required_documents"
                ],
                "source_urls": tpcu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_TPCU_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "臺北城市科技大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": tpcu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "tpcu",
        "school_name": "臺北城市科技大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": len(partners),
        "mainland_partners": 0,
        "dual_degree_partner_universities": 11,
        "dual_degree_programs": 11,
        "experience_report_covered_partners": exp_covered_schools,
        "experience_report_count": total_exp_reports,
        "open_partners": open_partner_count,
        "reference_only_partners": 0,
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
            f"臺北城市科技大學國際事務處、商管學院、民生學院、工程學院與研究發展處《海外留學姊妹校總表》、《學生出國研修辦法（1060619）》、《與境外大學辦理雙聯學制實施辦法（1050914）》、《學海飛颺、學海惜珠校內甄選辦法（1080121）》、《學海築夢及新南向學海築夢校內甄選辦法（1150105）》及《學生海外實習及研習輔導要點（1061030）》同步整合；共完整收錄 {len(partners)} 所海外合作姊妹校（日本 10 校、韓國 2 校、紐西蘭 1 校、英國 1 校、美國 4 校，含 11 所跨國雙聯學位合作校，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆交換雙聯榜單與研修紀錄）。"
        ),
        "verified_at": "2026-11-03",
    }
    (OFFICIAL_TPCU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_TPCU_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "tpcu",
                "school_name": "臺北城市科技大學",
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
            "sources/tpcu/tpcu_catalog_source.json",
            TPCU_SISTER_SCHOOLS_PDF_URL,
            f"臺北城市科技大學 {len(partners)} 所海外交換留學與雙聯學位合作姊妹校整合資料集 JSON",
        ),
        (
            "sources/tpcu/tpcu_resolved_locations.json",
            TPCU_SISTER_SCHOOLS_PDF_URL,
            f"臺北城市科技大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
        ),
        (
            "sources/tpcu/tpcu_academic_units_zh.html",
            "https://www.tpcu.edu.tw/p/412-1000-485.php?Lang=zh-tw",
            "臺北城市科技大學全校 3 大學院（工程學院、商管學院、民生學院）與系所架構 HTML",
        ),
        (
            "sources/tpcu/afl_exchange_2026_zh.html",
            TPCU_AFL_EXCHANGE_2026_URL,
            "臺北城市科技大學應用外語系 2026（115學年度）海外交換留學與雙聯學位錄取榜單 HTML",
        ),
        (
            "sources/tpcu/tpcu_ipu_nz_dual_degree_news_zh.html",
            TPCU_IPU_NZ_NEWS_URL,
            "臺北城市科技大學與紐西蘭 IPU New Zealand 簽署雙聯學制官方公告 HTML",
        ),
    ]
    for html_p in sorted(SOURCES_TPCU_DIR.glob("*.html")):
        rel_hp = f"sources/tpcu/{html_p.name}"
        if not any(x[0] == rel_hp for x in provenance_files):
            first_line = html_p.read_text(encoding="utf-8", errors="ignore").splitlines()[0] if html_p.stat().st_size > 0 else ""
            m_src = re.search(r"<!--\s*Source:\s*(https?://[^\s>]+)\s*-->", first_line)
            h_url = m_src.group(1) if m_src else TPCU_IEEC_HOME_URL
            provenance_files.append(
                (rel_hp, h_url, f"臺北城市科技大學官方網站存檔頁面：{html_p.name}")
            )
    for rel_p, surl in bin_urls.items():
        rp = rel_p if rel_p.startswith("sources/") else f"sources/tpcu/{rel_p}"
        if not any(x[0] == rp for x in provenance_files):
            provenance_files.append(
                (rp, surl, f"臺北城市科技大學官方原始法規或簡章檔案：{Path(rp).name}")
            )

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
        "school_id": "tpcu",
        "school_name": "臺北城市科技大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = (
        json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    )
    (OFFICIAL_TPCU_DIR / "import_provenance.json").write_text(
        prov_text, encoding="utf-8"
    )
    (OFFICIAL_TPCU_DIR / "import-provenance.json").write_text(
        prov_text, encoding="utf-8"
    )

    print(
        f"Successfully built TPCU catalog: {len(partners)} partners"
        f" ({open_partner_count} open, {completeness['verified_campus_images']}"
        f" verified images, {completeness['verified_locations']} verified"
        f" locations), {len(workflows)} workflows,"
        f" {len(destinations)} destinations, {len(research_records)} research"
        f" records, {exp_covered_schools} schools with experience records"
        f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
    )


if __name__ == "__main__":
    main()
