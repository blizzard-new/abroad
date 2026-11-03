from __future__ import annotations

import re

from .university_registry import TPCU, resolve_university

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

TPCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 61.0),
    "ielts": ("IELTS", 5.5),
    "toefl_itp": ("TOEFL ITP/PBT", 500.0),
    "toeic": ("TOEIC", 550.0),
}


def is_tpcu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == TPCU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "臺北城市科技大學",
        "台北城市科技大學",
        "城市科大",
        "城市大學",
        "北台科大",
        "光武工專",
        "tpcu",
        "taipei city university of science and technology",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def tpcu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《臺北城市科技大學學生出國研修辦法》第 2 條及《教育部獎助大專校院選送學生出國研修—學海飛颺、學海惜珠校內甄選辦法》第 2 條：申請出國交換研修者須為就讀本校滿一學年以上且非當學期畢業之在學學生（不含境外碩士專班）；申請教育部學海飛颺／惜珠／築夢者須具中華民國國籍且就讀本校滿一學期以上（不含國內及境外在職專班生）。"
            ),
        )
    if any(
        token in degree or token in year
        for token in (
            "境外碩士專班",
            "在職專班",
            "碩專",
            "emba",
            "EMBA",
            "學分班",
            "選修生",
            "休學",
        )
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《臺北城市科技大學學生出國研修辦法》第 2 條及《學海飛颺、學海惜珠校內甄選辦法》第 2 條，境外碩士專班、國內及境外在職專班生、休學生或無正式一般生學籍者不得申請出國交換與教育部學海系列獎助。"
            ),
        )
    is_grad = _is_graduate(degree)
    if not is_grad and year in {
        "大一",
        "大一上",
        "大一下",
        "一年級",
        "一年級上學期",
        "一年級下學期",
    }:
        return (
            "fail",
            (
                f"已填報 {degree}（{year}）；依《臺北城市科技大學學生出國研修辦法》第 2 條第 1 款規定，申請出國交換研修者須為「就讀本校滿一學年以上」之在學學生。建議於一年級期間修讀英日韓外語課程並考取檢定（如 JLPT N4–N2、TOEIC 550），於二年級起提出海外交換留學或 2+2 雙聯學位申請。"
            ),
        )
    grad_note = (
        "（提醒：跨國雙聯學制碩士班依《與境外大學辦理雙聯學制實施辦法》第 5 條累計在兩校修業時間至少須滿 12 個月，且於兩校當地修習學分數累計須各達獲頒學位所需總學分數之 1/3 以上）"
        if is_grad
        else "（提醒：跨國雙聯學制學士班依《與境外大學辦理雙聯學制實施辦法》第 5 條累計在兩校修業時間至少須滿 32 個月［如日本城西國際大學、神戶國際大學、鹿兒島國際大學、紐西蘭 IPU New Zealand、英國伯明翰大學學院 UCB、美國加州峽谷大學 2+2 雙學士］，且於兩校當地修習學分數各須達畢業總學分數 1/3 以上）"
    )
    return (
        "pass",
        (
            f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合臺北城市科技大學《學生出國研修辦法》第 2 條（就讀本校滿一學年以上之在學學生）及雙聯學制之在學身分規定{grad_note}。"
        ),
    )


def tpcu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 60.0
    gpa_min = 2.0
    details: list[str] = []
    passes_general = False
    passes_competitive = False

    if academic_score is not None:
        details.append(f"學業平均 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_general = True
        if academic_score >= 75.0:
            passes_competitive = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_general = True
        if academic_gpa >= 3.0:
            passes_competitive = True
    if class_rank_percent is not None:
        details.append(f"班排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= 50.0:
            passes_general = True
        if class_rank_percent <= 30.0:
            passes_competitive = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫歷年學業平均成績或 GPA；依《臺北城市科技大學學生出國研修辦法》（106年6月19日修訂）第 2 條第 4 款規定：申請學生在校期間須無小過以上處分紀錄，且前一學年之「學業平均總成績應達 60 分以上」、「操行平均總成績應達 75 分以上」；若同時申請日本國立大學（國立琉球大學、國立德島大學、國立宇都宮大學）、歐美雙聯學位或教育部《學海飛颺》獎助學金，建議學業平均達 70–75 分（GPA 2.5–3.0）以上。"
            ),
        )

    if passes_general:
        tier_note = (
            "已達《學生出國研修辦法》第 2 條第 4 款學業平均 60 分以上門檻，且具備申請日本國立大學（琉球大學、德島大學、宇都宮大學）、歐美紐雙聯學位及教育部《學海飛颺》獎助學金之優良競爭力（另請確認操行平均達 75 分以上且無小過以上處分紀錄）"
            if passes_competitive
            else "已達《學生出國研修辦法》第 2 條第 4 款規定之前一學年學業平均總成績 60 分（GPA 2.0）以上門檻（另須確認操行平均總成績達 75 分以上且無小過以上處分紀錄；若申請日本國立大學或歐美雙聯學位建議達 70–75 分以上）"
        )
        return (
            "pass",
            f"已填報 {summary}；符合臺北城市科技大學出國交換與雙聯學位學業成績門檻（{tier_note}）。",
        )

    return (
        "fail",
        (
            f"已填報 {summary}；未達《臺北城市科技大學學生出國研修辦法》第 2 條第 4 款規定之「前一學年學業平均總成績應達 60 分以上（且操行平均總成績應達 75 分以上、無小過以上處分紀錄）」最低申請門檻。"
        ),
    )


def tpcu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫外語能力檢定成績。依《臺北城市科技大學學生出國研修辦法》第 2 條第 5 款及商管／民生學院海外留學規定：（1）日本姊妹校（城西國際大學、神戶國際大學、鹿兒島國際大學、國立琉球大學、日本經濟大學、北海道星槎道都大學、國立德島大學、十文字學園女子大學、國立宇都宮大學、昭和音樂大學）交換留學與 2+2 雙聯學位原則要求 JLPT N2 或 N3（含）以上合格（神戶國際大學日語加強班及日本海外實習要求 JLPT N4 合格或 300 小時日文上課時數證明）；（2）英語系國家姊妹校（紐西蘭 IPU New Zealand、英國伯明翰大學學院 UCB、美國加州峽谷大學、曼徹普利敦州立大學、聖保羅學院、明州西南州立大學）要求 TOEFL iBT 61 / IELTS 5.5–6.0 / TOEIC 550 以上（IPU New Zealand 亦接受 JLPT N2–N3；英語系國家海外實習基本門檻為 TOEIC 225 或 GEPT 初級以上）；（3）韓國姊妹校（信韓大學、富川大學）要求韓語檢定 TOPIK 2–3 級或 TOEIC 550 以上。"
            ),
        )
    if test in TPCU_ENGLISH_MINIMUMS:
        label, minimum = TPCU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        if (
            (test == "toefl" and language_score >= 72)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toefl_itp" and language_score >= 540)
            or (test == "toeic" and language_score >= 650)
        ):
            tier_note = "符合英國伯明翰大學學院（UCB）、紐西蘭國際太平洋大學（IPU New Zealand）、美國加州峽谷大學、曼徹普利敦州立大學、聖保羅學院、明州西南州立大學及教育部《學海飛颺》全部英語系姊妹校交換與雙聯學位高階門檻"
        elif passed:
            tier_note = "符合紐西蘭國際太平洋大學（IPU New Zealand）、美國加州峽谷大學、明州西南州立大學、曼徹普利敦州立大學、聖保羅學院、英國伯明翰大學學院（UCB 交換）及韓國姊妹校英語授課學程門檻"
        elif test == "toeic" and language_score >= 225:
            tier_note = "雖未達歐美紐大學交換／雙聯學位門檻（TOEIC 550），但已達商管／民生學院英語系國家海外專業實習（學海築夢）基本門檻（TOEIC 225 / GEPT 初級 / CEFR A2）"
        else:
            tier_note = f"未達臺北城市科技大學英語系國家姊妹校交換與雙聯學位標準（{label} {minimum:g}）"
        return (
            "pass" if passed else "fail",
            (
                f"{label} {language_score:g} {'符合' if passed else '未達'}臺北城市科技大學海外交換留學與雙聯學位英語檢定門檻（最低基準：{label} {minimum:g}；{tier_note}）。"
            ),
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 4
        if level in (1, 2):
            tier_note = "符合日本國立琉球大學、國立德島大學、國立宇都宮大學、城西國際大學、神戶國際大學、鹿兒島國際大學、日本經濟大學、北海道星槎道都大學、十文字學園女子大學、昭和音樂大學及紐西蘭 IPU New Zealand 全部交換留學與 2+2 雙聯學位最高日語門檻"
        elif level == 3:
            tier_note = "符合城西國際大學、神戶國際大學、鹿兒島國際大學、日本經濟大學、星槎道都大學、十文字學園女子大學、昭和音樂大學及紐西蘭 IPU New Zealand 交換／雙聯門檻（國立琉球大學、德島大學、宇都宮大學一般交換建議達 JLPT N2）"
        elif level == 4:
            tier_note = "符合神戶國際大學日語加強特別班及日本海外專業實習（學海築夢）之 JLPT N4 門檻（一般日本大學部交換留學與 2+2 雙聯學位建議達 JLPT N3–N2 以上）"
        else:
            tier_note = "日本海外實習與神戶國際大學日特班最低要求 JLPT N4 合格（或 300 小時日文上課時數證明），一般日本大學交換與 2+2 雙聯要求 JLPT N3–N2 以上"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}臺北城市科技大學日本姊妹校交換留學、雙聯學位與海外實習日語檢定基準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = 2 <= level <= 6
        if level >= 3:
            tier_note = "符合韓國信韓大學（Shinhan University，交換留學與 2+2 雙聯學位）及富川大學（Bucheon University，交換留學）全部韓語門檻"
        elif level == 2:
            tier_note = "符合韓國富川大學與信韓大學交換留學韓語基本門檻（TOPIK 2 級）"
        else:
            tier_note = "韓國信韓大學與富川大學交換留學要求 TOPIK 2 級以上（或改以英語 TOEIC 550 / TOEFL iBT 61 / IELTS 5.5 申請）"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}臺北城市科技大學韓國姊妹校交換與雙聯韓語基準（{tier_note}）。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照臺北城市科技大學《學生出國研修辦法》與各姊妹校簡章（JLPT N1–N4、TOEFL iBT、IELTS、TOEIC、TOPIK）確認目標學校語言門檻。",
    )
