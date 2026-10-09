"""Manual semantic review of all 55 non-grey Spring 2027 table entries.

Scores below are transcribed from the official PDF, never inferred from regex or
CEFR equivalence. Unselected host tracks/faculties and score ranges stay unknown.
The document audit distinguishes actual documents from nomination preconditions.
"""

import hashlib
import json
from .ccu_sources import BUNDLE, CHECKED_AT, PARTNERS_URL, ROUND, YEAR
from .models import ExchangeFieldEvidence, PartnerLanguageCondition, PartnerUniversity


CURRENT_DOCUMENT_LIST_PAGES = {
    10,
    16,
    24,
    27,
    29,
    35,
    42,
    43,
    45,
    47,
    48,
    49,
    50,
    52,
    53,
    58,
    65,
    67,
    68,
    73,
    77,
    80,
    83,
    85,
    86,
    87,
    89,
    95,
    98,
    99,
    100,
    101,
    102,
    106,
    108,
    114,
    119,
}
PARTIAL_DOCUMENT_PAGES = {23, 109}
HISTORICAL_DOCUMENT_PAGES = {32, 33, 39, 105}
PREREQUISITE_ONLY_PAGES = {26, 71, 103, 104}
LINKED_DOCUMENT_PAGES = {34, 37, 61, 88, 111}
NO_DOCUMENT_PAGES = {54, 74}
GENERAL_ADMISSION_PAGES = {107}

# All language fields were reviewed, including no score requirement and non-numeric proof.
LANGUAGE_REVIEW = {
    10: "港澳臺籍無門檻、外籍HSK5；身分範圍須確認，不能套用全體學生。",
    16: "原文無語言門檻；不推定合作校免收語言文件。",
    23: "原文無語言門檻；不推定合作校免收語言文件。",
    24: "原文無語言門檻；不推定合作校免收語言文件。",
    26: "原文無語言門檻；當期第二階文件尚未載。",
    27: "原文無語言門檻；不推定合作校免收語言文件。",
    29: "當期語言欄未載。",
    32: "英語課程寫TOEFL PBL 500，檢定名稱待確認；日語課程N4及300小時不能套用英語課。",
    33: "Japanese N2；未核實可替代的英語分數。",
    34: "英語課程與全日文課程N1分開；尚未選定授課語言。",
    35: "IPLA/JYPE/COLABS英檢與DEEP日文N1分開；不得跨計畫套用，JYPE春季適用另待確認。",
    37: "HUSTEP、SA、SRS的學制、語言及推薦函分開；尚未選定合作校計畫。",
    39: "春季JLPT N2；秋季N5不能作2027春季門檻。",
    42: "英檢列TOEIC700/iBT70/IELTS5.5；韓語程度與英文授課文件適用範圍須另核對。",
    43: "無最低分，但仍須檢附目前英文檢定；不能把無門檻當成不需文件。",
    45: "English Track的iBT82/IELTS6.5是recommended，不能作強制失敗；Korean Track TOPIK5及大二以上另列。",
    47: "英文授課英檢與韓文授課TOPIK/KLAT分開，尚未选定合作校授課語言。",
    48: "English B2或TOPIK3；不同證明選項及未明示iBT的TOEFL72待核對。",
    49: "語言欄列分數，文件欄寫語言證明Not mandatory，強制性存在疑義。",
    50: "TOEFL/IELTS分數後寫recommended，不能作強制門檻。",
    52: "TOPIK與英檢並列，兩者替代／適用範圍尚未核實。",
    53: "沒有英語最低分；韓語TOPIK3為韓語課程優先建議。",
    54: "English Track IELTS5.5與Korean Track TOPIK3分開。",
    58: "分數4.5–6.5等是不同系所範圍，合作校系所門檻未核實，不採最低端或最高端。",
    61: "允許母校背書替代檢定；學生採用的證明途徑尚未確認。",
    65: "語言欄列明iBT64/IELTS5.0/TOEIC600，未載分流或建議措辭。",
    67: "IELTS6.0/iBT79明列；TOEIC須L&R730且S&W280，不以單一TOEIC分數判斷。",
    68: "原文CEFR B2（IELTS6.0），只保留官方直接列出的分數，不自行換算。",
    71: "檢定門檻與越文授課建議分開，尚未選定授課語言。",
    73: "僅載CEFR B2，未自行換算其他檢定。",
    74: "iBT92與未註明種類的TOEFL80並列有疑義；不能擇80或92為強制值。",
    77: "無最低分，但須英文課教師親簽英文語言證明書。",
    80: "IELTS各單項、TOEFL各單項及2024/9/30後檢定日期均須確認，只有總分不足判斷。",
    83: "僅載CEFR B2，未自行換算其他檢定。",
    85: "普通學士DELF B2、研究所DELF C1、DEFLE無檢定分開。",
    86: "語言欄列iBT80/TOEIC750/IELTS6.0，未載分流或建議措辭。",
    87: "法文B1 mandatory、B2 recommended，部分學院B2/C1；須合作校系所確認。",
    88: "B2英文／法文依授課語言；未自行換算檢定分數。",
    89: "語言欄直接列iBT83/IELTS6.5；與名額的不同學院分配分開。",
    95: "語言欄直接列IELTS5.5/TOEIC L&R785/iBT72。",
    98: "僅載英文B2，未自行換算其他檢定。",
    99: "學士德文B2，碩士依英文／德文計畫，資工另須德文證明。",
    100: "CEFR B2後的檢定分數為區間，不能當成單一強制最低分；授課語言另確認。",
    101: "英文或德文B1後的分數為區間，不能把區間下限硬判為強制門檻。",
    102: "語言欄直接列IELTS5.5/TOEIC L&R785/iBT72。",
    103: "學士／碩士、英文／德文、TOEIC兩部分及檢定日期分開；尚未選定合作校課程。",
    104: "英文／德文授課及母校德文背書選項分開；尚未選定授課語言。",
    105: "原文不接受IELTS，另列iBT79/TOEIC785及到校ASBU考試選項；採用途徑需確認。",
    106: "B2與分數區間並列，未核實逐課程強制最低分。",
    107: "僅載英文B2，未自行換算其他檢定。",
    108: "B2與分數區間並列，未核實逐課程強制最低分。",
    109: "B2與分數區間並列，未核實逐課程強制最低分。",
    111: "僅載CEFR B2，未自行換算其他檢定。",
    114: "原文IELTS5.5/TOEIC785直接列出；TOEFL72未明示種類，待核對。",
    119: "英文課B2與第二階文件英／西文B1矛盾，不能判定最低門檻。",
}

# Only unscoped, directly stated mandatory scores are comparable without more input.
DIRECT_REQUIRED = {
    65: {"toefl": 64, "ielts": 5.0, "toeic": 600},
    67: {"toefl": 79, "ielts": 6.0},
    68: {"ielts": 6.0},
    86: {"toefl": 80, "toeic": 750, "ielts": 6.0},
    89: {"toefl": 83, "ielts": 6.5},
    95: {"toefl": 72, "toeic": 785, "ielts": 5.5},
    102: {"toefl": 72, "toeic": 785, "ielts": 5.5},
    114: {"toeic": 785, "ielts": 5.5},
}


def condition(row, test, score=None, level="needs_confirmation", **scope):
    original = row.field_evidence["language_requirement"]
    return PartnerLanguageCondition(
        test=test,
        minimum_score=score,
        requirement_level=level,
        test_variant="iBT" if test == "toefl" and level == "required" else None,
        evidence=original.model_copy(deep=True),
        **scope,
    )


def review_language(row):
    page = row.source_pages[0]
    row.language_review_note = LANGUAGE_REVIEW[page]
    specs = []
    for test, score in DIRECT_REQUIRED.get(page, {}).items():
        specs.append(condition(row, test, score, "required"))
    if page == 45:
        specs = [
            condition(
                row,
                "toefl",
                82,
                "recommended",
                track="English Track",
                degree_levels=["大學部"],
                scope_choice_required=True,
            ),
            condition(
                row,
                "ielts",
                6.5,
                "recommended",
                track="English Track",
                degree_levels=["大學部"],
                scope_choice_required=True,
            ),
            condition(
                row,
                "topik",
                5,
                "required",
                track="Korean Track",
                degree_levels=["大學部"],
                scope_choice_required=True,
                additional_conditions=["大二或以上"],
            ),
        ]
    elif page == 50:
        specs = [
            condition(row, "toefl", 80, "recommended"),
            condition(row, "ielts", 5.5, "recommended"),
        ]
    elif page == 58:
        specs = [
            condition(
                row,
                test,
                scope_choice_required=True,
                host_faculties=["逐系所門檻尚未核實"],
            )
            for test in ("ielts", "toefl", "toeic")
        ]
    elif page == 74:
        row.field_evidence["language_requirement"].status = "conflict"
        specs = [
            condition(row, "toefl", 92, "conflict"),
            condition(row, "toefl", 80, "conflict"),
        ]
    elif page == 49:
        row.field_evidence["language_requirement"].status = "conflict"
        specs = [
            condition(row, "ielts", 5.5, "conflict"),
            condition(row, "toefl", 71, "conflict"),
        ]
    elif page == 80:
        specs = [
            condition(
                row,
                "ielts",
                6,
                "required",
                additional_conditions=["各單項至少5.5", "檢定日期須2024/9/30以後"],
            ),
            condition(
                row,
                "toefl",
                70,
                "needs_confirmation",
                additional_conditions=[
                    "檢定種類及各單項門檻",
                    "檢定日期須2024/9/30以後",
                ],
            ),
        ]
    elif page == 103:
        specs = [
            condition(
                row,
                test,
                score,
                "required",
                degree_levels=[degree],
                teaching_language="英文",
                scope_choice_required=True,
                additional_conditions=["檢定日期須2024/11/01之後"],
            )
            for degree, test, score in [
                ("大學部", "ielts", 5.5),
                ("大學部", "toefl", 72),
                ("碩士班", "ielts", 7.0),
                ("碩士班", "toefl", 95),
            ]
        ]
    if not specs:
        level = (
            "no_score_minimum"
            if page in {16, 23, 24, 26, 27, 43, 53, 77}
            else "needs_confirmation"
        )
        specs = [
            condition(
                row,
                "other",
                level=level,
                scope_choice_required=page
                in {10, 32, 34, 35, 37, 47, 48, 52, 54, 71, 85, 87, 88, 99, 104},
            )
        ]
    row.language_conditions = specs
    row.field_evidence["language_requirement"].note = row.language_review_note


def review_documents(row):
    page = row.source_pages[0]
    evidence = row.field_evidence["partner_documents"]
    current = evidence.excerpt or ""
    body = current
    if body.startswith("必須先經過第一階段校內申請通過"):
        end = body.index("申請。") + len("申請。")
        row.partner_application_prerequisite = body[:end]
        body = body[end:].strip()
    elif page == 24:
        end = body.index("交換生材料包括")
        row.partner_application_prerequisite = body[:end]
        body = body[end:].strip()
    if row.partner_application_prerequisite:
        row.field_evidence["partner_application_prerequisite"] = ExchangeFieldEvidence(
            source_url=PARTNERS_URL,
            source_pages=evidence.source_pages,
            academic_year=YEAR,
            application_round=ROUND,
            checked_at=CHECKED_AT,
            status="verified_current",
            excerpt=row.partner_application_prerequisite,
            note="母校甄選／提名之前提，不是合作校文件清單。",
        )
    if page in CURRENT_DOCUMENT_LIST_PAGES:
        evidence.status = "verified_current"
        evidence.excerpt = body
        evidence.note = (
            "中正當期PDF列有實際文件要求；未宣稱已獨立查核海外附件或完整清單。"
        )
        row.application_info = body
    elif page in HISTORICAL_DOCUMENT_PAGES:
        reference = body if page == 105 else evidence.reference_excerpt
        row.reference_data["partner_documents"] = reference
        evidence.status = "reference_only"
        evidence.excerpt = None
        evidence.reference_excerpt = reference
        evidence.academic_year = None
        evidence.application_round = None
        evidence.note = "實際清單為灰字歷史參考／明示舊資訊；母校提名前提獨立保存。"
        row.application_info = None
    elif page in PREREQUISITE_ONLY_PAGES or page in NO_DOCUMENT_PAGES:
        evidence.status = "missing"
        evidence.excerpt = None
        evidence.note = (
            "當期只載母校甄選／提名前提，未列實際文件要求。"
            if page in PREREQUISITE_ONLY_PAGES
            else "當期未列文件要求；p74原文寫「無任何資訊」。"
            if page == 74
            else "當期文件欄空白。"
        )
        row.application_info = None
    else:
        assert (
            page
            in PARTIAL_DOCUMENT_PAGES | LINKED_DOCUMENT_PAGES | GENERAL_ADMISSION_PAGES
        )
        evidence.status = "needs_confirmation"
        if page in PARTIAL_DOCUMENT_PAGES:
            evidence.note = (
                "有當期文件片段，但清單部分實際要求仍為灰字；完整當期要求未核實。"
            )
            row.application_info = "完整當期清單待確認；目前有內容：" + body
        elif page in LINKED_DOCUMENT_PAGES:
            evidence.note = "僅載程序或外部連結；未逐份核實實際當期文件清單。"
            row.application_info = "實際當期文件清單尚未核實；程序／來源：" + body
        else:
            evidence.note = (
                "列一般入學而非核實交換文件（入學考試／繳學費），待承辦確認。"
            )
        evidence.excerpt = body
    row.student_summary_zh.application_steps = (
        [row.application_info] if row.application_info else []
    )
    if page == 105:
        # The fee is inside the same explicitly old information block.
        row.reference_data["tuition_info"] = row.tuition_info or ""
        row.tuition_info = None
        row.field_evidence["tuition_info"].status = "reference_only"
        row.field_evidence["tuition_info"].reference_excerpt = row.field_evidence[
            "tuition_info"
        ].excerpt
        row.field_evidence["tuition_info"].excerpt = None
        row.field_evidence[
            "tuition_info"
        ].note = "文件欄末註此為舊資訊供參考，不作當期费用。"


def apply_ccu_semantic_review(row: PartnerUniversity):
    if row.availability_status == "not_open":
        return
    assert row.source_pages[0] in LANGUAGE_REVIEW, (
        "New table entry requires semantic review"
    )
    lock = json.loads((BUNDLE / "semantic-review-lock.json").read_text())["pages"][
        str(row.source_pages[0])
    ]
    for field in ("language_requirement", "partner_documents"):
        for kind in ("excerpt", "reference_excerpt"):
            digest = hashlib.sha256(
                (getattr(row.field_evidence[field], kind) or "").encode()
            ).hexdigest()
            if digest != lock[field + "_" + kind]:
                raise ValueError(
                    f"Official p{row.source_pages[0]} {field} changed; reread source semantics before rebuilding"
                )
    review_language(row)
    review_documents(row)
