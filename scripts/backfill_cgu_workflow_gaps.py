from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from exchange_info.application_workflow_collector import (
    build_cgu_reference_workflow,
)
from exchange_info.models import (
    ApplicationSubmissionMethod,
    PartnerUniversity,
    UniversityApplicationWorkflow,
)
from exchange_info.school_identity import school_identity_key
from exchange_info.storage import data_paths, read_jsonl, write_jsonl
from exchange_info.student_view import fetch_partner_universities


CHECKED_AT = datetime(2026, 7, 29, tzinfo=timezone.utc)
CGU_NAME = "長庚大學"


@dataclass(frozen=True)
class WorkflowSeed:
    school_name: str
    partner_website: str
    sources: tuple[tuple[str, str], ...]
    summary: str
    details: tuple[str, ...]
    documents: tuple[str, ...]
    timing: str = "以長庚提名信與合作校當期通知為準"
    submission_method: ApplicationSubmissionMethod = (
        ApplicationSubmissionMethod.UNKNOWN
    )
    submission_email: str | None = None
    portal_url: str | None = None
    coverage_note: str | None = None


SEEDS = (
    WorkflowSeed(
        school_name="上海交通大學 Shanghai Jiao Tong University",
        partner_website="https://global.sjtu.edu.cn/",
        sources=((
            "Shanghai Jiao Tong University Semester Exchange Program 2026-2027",
            "https://global.sjtu.edu.cn/en/study-sjtu/prospective/non-degree-programs/281",
        ),),
        summary="長庚完成提名後，學生會收到上海交通大學的個人線上申請連結。",
        details=(
            "2026/27 官方頁列 GPA 3.0/4.0、中文授課 HSK 5、英文授課 IELTS 6.0 或 TOEFL 90，並要求至少完成兩學期。",
            "官方頁另列 Non-Chinese citizen；台灣學生的國籍認定與實際適用資格必須由兩校國際處書面確認。",
            "醫學院與上海高級金融學院不開放校級交換，其他院系也可能限制選課。",
        ),
        documents=(
            "護照資料頁",
            "英文歷年成績單",
            "履歷",
            "母校推薦或提名信",
            "讀書計畫",
            "證件照",
            "語言能力證明（如適用）",
        ),
        timing="2026/27 Fact Sheet：秋季 3/30、春季 10/30；個人期限以提名信為準",
        submission_method=ApplicationSubmissionMethod.ONLINE,
        coverage_note="已查到 2026/27 官方交換說明；國籍限制與長庚協議適用範圍仍須由兩校確認。",
    ),
    WorkflowSeed(
        school_name="巴西聖保羅聯邦大學 Universidade Federal de São Paulo",
        partner_website="https://www.unifesp.br/",
        sources=((
            "UNIFESP undergraduate mobility institutional procedures",
            "https://www.unifesp.br/world/images/arquivos/Undergraduate_students_Institutional_procedures.pdf",
        ),),
        summary="依 UNIFESP 校級程序，由母校國際處完成校際聯繫後，以電子郵件送交申請文件。",
        details=(
            "官方文件列出的研修期間通常為 2–6 月或 8–11 月。",
            "課程、語言與實際收件版本仍須由 UNIFESP 接待單位確認。",
        ),
        documents=(
            "UNIFESP 申請表",
            "母校介紹或推薦信",
            "葡萄牙文翻譯歷年成績單",
            "動機信",
            "讀書與修課計畫",
        ),
        submission_method=ApplicationSubmissionMethod.EMAIL,
        submission_email="international@unifesp.br",
    ),
    WorkflowSeed(
        school_name="復旦大學 Fudan University",
        partner_website="https://ogp.fudan.edu.cn/",
        sources=(
            ("Fudan University incoming students portal", "https://ogp.fudan.edu.cn/"),
            (
                "Fudan University School of Management incoming exchange",
                "https://www.fdsm.fudan.edu.cn/En/IncomingExchange/list.htm",
            ),
        ),
        summary="先由長庚依校際協議提名，再依復旦接待院系與提名信提供的入口完成申請。",
        details=(
            "公開頁可確認交換須以合作協議與母校提名為前提。",
            "校級當期文件清單、申請入口與院系限制未在同一公開頁完整列出，不能套用舊年度表格。",
        ),
        documents=("護照影本", "英文或中文歷年成績單", "讀書與修課計畫", "提名信要求的其他附件"),
        coverage_note="已連結復旦校級入境入口與管理學院交換頁；當期校級文件與院系規則仍待提名信確認。",
    ),
    WorkflowSeed(
        school_name="德國呂貝克應用科技大學 Technische Hochschule Lübeck",
        partner_website="https://www.th-luebeck.de/en/",
        sources=(
            (
                "Technische Hochschule Lübeck International Office",
                "https://www.th-luebeck.de/en/international/thl-international/international-office/",
            ),
            (
                "TH Lübeck application instructions for exchange students",
                "https://www.th-luebeck.de/fileadmin/media/02_Studium/03_Internationales/International-Office/Application_instructions_for_exchange_students.pdf",
            ),
        ),
        summary="依 TH Lübeck 國際處交換生說明完成線上申請，並上傳官方要求的附件。",
        details=(
            "2025-10-01 更新的官方說明列有線上申請、成績單與語言證明。",
            "若全部選修英文授課課程，公開說明未要求德文證明；實際課程語言仍須逐門確認。",
        ),
        documents=("英文歷年成績單", "英文能力證明（非英語母語者）", "提名信要求的其他附件"),
        submission_method=ApplicationSubmissionMethod.ONLINE,
    ),
    WorkflowSeed(
        school_name="捷克俄斯特拉發科技大學 VSB – Technical University of Ostrava",
        partner_website="https://www.vsb.cz/en/",
        sources=(
            ("VSB exchange students", "https://www.vsb.cz/en/study/exchange-students/"),
            (
                "VSB Faculty of Economics incoming admission procedure",
                "https://www.ekf.vsb.cz/en/international/mobility-short-term-study/incoming-students/erasmus-students/admission-procedure/",
            ),
        ),
        summary="由長庚提名後，依 VSB 接待學院的入境交換程序完成申請。",
        details=(
            "校級頁提供交換生入口；文件與流程可能由接待學院分別管理。",
            "經濟學院公開的文件不能直接視為所有學院共同規則。",
        ),
        documents=("申請資料", "英文歷年成績單", "Learning Agreement／修課協議", "語言能力證明（依學院要求）"),
        submission_method=ApplicationSubmissionMethod.ONLINE,
    ),
    WorkflowSeed(
        school_name="法國EPF工程師學校 EPF École d'ingénieurs",
        partner_website="https://www.epf.fr/en",
        sources=((
            "EPF non-degree seeking students and double degrees",
            "https://www.epf.fr/en/non-degree-seeking-students-and-double-degrees",
        ),),
        summary="EPF 僅受理合作校預選與提名的交換生，提名後依官方頁完成申請。",
        details=(
            "官方頁列英文 B2 或法文 B1，並建議每學期修讀 20–30 ECTS。",
            "頁面列出的 4/30 與 10/30 未附適用年度，只能作準備參考。",
        ),
        documents=("護照影本", "雙方簽署的 Learning Agreement", "語言能力證明", "履歷", "動機信", "歷年成績單", "證件照"),
        timing="官方頁列秋季 4/30、春季 10/30；未附年度，個人期限以提名信為準",
        submission_method=ApplicationSubmissionMethod.ONLINE,
    ),
    WorkflowSeed(
        school_name="法國ICD商學院 ICD Business School",
        partner_website="https://www.icd-bs.com/",
        sources=((
            "ICD Business School incoming exchange students",
            "https://www.icd-bs.com/incoming-exchange-students",
        ),),
        summary="ICD 公開頁說明交換僅限合作校學生；先由長庚確認名額與提名，再依當期通知申請。",
        details=(
            "公開頁列秋季、春季與全學年交換選項。",
            "6/15 與 11/15 未附適用年度，不能直接加入截止提醒。",
        ),
        documents=("當期 ICD 申請資料", "英文歷年成績單", "護照影本", "語言能力證明（依提名信）"),
        timing="官方頁列秋季 6/15、春季 11/15；未附年度，個人期限以提名信為準",
    ),
    WorkflowSeed(
        school_name="法國國立圖盧茲綜合理工學院 National Polytechnic Institute of Toulouse",
        partner_website="https://www.inp-toulouse.fr/en/",
        sources=(
            (
                "Toulouse INP international exchange application",
                "https://www.inp-toulouse.fr/en/international/international-students/application.html",
            ),
            (
                "Toulouse INP exchange programmes in English",
                "https://www.inp-toulouse.fr/en/study/exchange-programmes-in-english.html",
            ),
        ),
        summary="由長庚提名後，依 Toulouse INP 實際接待學院的申請方式與期限送件。",
        details=(
            "官方頁顯示 ENSEEIHT 與 AgroToulouse 等單位使用不同申請方式。",
            "不得把單一學院的文件與期限套用到所有 Toulouse INP 學院。",
        ),
        documents=("護照影本", "英文歷年成績單", "動機信", "履歷", "雙方簽署的 Learning Agreement", "語言能力證明（依學院要求）"),
        submission_method=ApplicationSubmissionMethod.ONLINE,
    ),
    WorkflowSeed(
        school_name="法國國立工業系統工程學校 EIGSI Engineering School",
        partner_website="https://www.eigsi.fr/?lang=en",
        sources=((
            "EIGSI international students within an exchange programme",
            "https://www.eigsi.fr/admissions-engineering-school-france/international-students-within-an-exchange-programme/?lang=en",
        ),),
        summary="EIGSI 交換申請以合作校身分為前提，長庚提名後依官方頁準備申請資料。",
        details=(
            "官方頁列英文 B1，以及履歷、動機信、申請表與 Learning Agreement。",
            "舊年度 fact sheet 不作為目前期限來源。",
        ),
        documents=("履歷", "動機信", "EIGSI 申請表", "Learning Agreement／修課協議", "英文 B1 證明"),
    ),
    WorkflowSeed(
        school_name="法國薩克雷大學 University of Paris-Saclay",
        partner_website="https://www.universite-paris-saclay.fr/en",
        sources=(
            (
                "Université Paris-Saclay incoming exchange programme",
                "https://www.universite-paris-saclay.fr/admission/etudiants-internationaux/venir-etudier-luniversite-paris-saclay-en-programme-dechange-erasmus-ou-accord-bilateral",
            ),
            (
                "Université Paris-Saclay incoming application portal",
                "https://www.universite-paris-saclay.fr/formation/partir-letranger/venir-upsaclay-portail-de-candidature",
            ),
        ),
        summary="先由長庚依合作協議提名，之後使用 Paris-Saclay 寄送的個人連結完成線上申請。",
        details=(
            "2026/27 官方頁列第一學期或全學年線上申請至 2026-05-15，第二學期至 2026-10-30。",
            "接待學院、關係企業與成員學校可能有獨立程序，申請前必須確認實際接待單位。",
            "一般建議 B2；法律經濟管理學院要求語言證明。",
        ),
        documents=("雙方簽署的 Learning Agreement", "歷年成績單", "語言能力證明（接待學院要求時）"),
        timing="2026/27 官方頁：第一學期／全學年至 2026-05-15，第二學期至 2026-10-30；仍以提名信為準",
        submission_method=ApplicationSubmissionMethod.ONLINE,
        portal_url="https://www.universite-paris-saclay.fr/formation/partir-letranger/venir-upsaclay-portail-de-candidature",
        coverage_note="已查到 2026/27 校級入境交換頁；成員學校與接待學院的獨立程序仍須逐案確認。",
    ),
    WorkflowSeed(
        school_name="波蘭華沙醫學大學 Medical University of Warsaw",
        partner_website="https://www.wum.edu.pl/en",
        sources=(
            (
                "Medical University of Warsaw Faculty of Medicine incoming exchange",
                "https://zagranica.wum.edu.pl/faculty-medicine-content",
            ),
            ("Medical University of Warsaw Erasmus", "https://www.wum.edu.pl/en/international-cooperation/erasmus"),
        ),
        summary="先由長庚提名，再依華沙醫學大學當期線上流程與接待學院要求完成申請。",
        details=(
            "官方頁顯示 2026/27 冬季申請已關閉，夏季申請預計 2026-10-25 開放。",
            "臨床交換生到校前須準備刑事紀錄證明；適用對象與格式必須向接待學院確認。",
            "校方正轉換線上 Learning Agreement 流程，部分 PDF 文件仍可能依通知以電子郵件補交。",
        ),
        documents=("線上申請資料", "Learning Agreement／修課協議", "接待學院要求的 PDF 附件", "刑事紀錄證明（臨床交換適用）"),
        timing="2026/27 冬季申請已關閉；夏季申請頁預計 2026-10-25 開放，截止時間待當期通知",
        submission_method=ApplicationSubmissionMethod.MIXED,
    ),
    WorkflowSeed(
        school_name="荷蘭恩荷芬理工大學 Eindhoven University of Technology",
        partner_website="https://www.tue.nl/en/",
        sources=(("Eindhoven University of Technology official website", "https://www.tue.nl/en/"),),
        summary="長庚完成提名後，依 TU/e 實際接待系所寄送的申請入口與文件清單辦理。",
        details=(
            "目前未找到可確認所有學院共用的現行校級 incoming exchange 申請頁。",
            "不得使用舊年度、其他大學或單一系所的期限作為 TU/e 全校規則。",
        ),
        documents=("接待系所通知的申請資料", "英文歷年成績單", "護照影本", "語言能力證明（依接待系所要求）"),
        coverage_note="已修正合作校官方網站；公開的現行校級交換申請細節不足，全部期限與文件仍待提名信確認。",
    ),
    WorkflowSeed(
        school_name="韓國江原國立大學 Kangwon National University",
        partner_website="https://admission.kangwon.ac.kr/english/",
        sources=((
            "Kangwon National University Student Exchange Program",
            "https://admission.kangwon.ac.kr/english/contents.do?key=1407",
        ),),
        summary="長庚提名後，依江原國立大學寄送的線上連結填寫申請並依通知補送掃描文件。",
        details=(
            "官方頁列申請者須已完成至少兩學期，並符合英文或韓文能力及 GPA 要求。",
            "醫學、獸醫、護理與法律等領域有限制。",
            "5/10 與 11/10 為未附年度的例行日期，只能作準備參考。",
        ),
        documents=("交換申請表", "自我介紹與讀書計畫", "護照影本", "英文歷年成績單", "在學證明", "推薦信"),
        timing="官方頁列秋季 5/10、春季 11/10；未附年度，個人期限以提名信為準",
        submission_method=ApplicationSubmissionMethod.MIXED,
    ),
    WorkflowSeed(
        school_name="韓國車醫科大學 CHA University",
        partner_website="https://global.cha.ac.kr/",
        sources=(("CHA University inbound exchange", "https://global.cha.ac.kr/inbound/"),),
        summary="CHA 公開頁確認 inbound exchange 僅開放合作校學生；先由長庚提名再依承辦人通知申請。",
        details=(
            "公開頁未完整列出當期文件、申請入口與期限。",
            "不得以 CHA 學位生招生頁取代交換生規則。",
        ),
        documents=("提名信要求的交換申請資料", "英文歷年成績單", "護照影本", "語言能力證明（如適用）"),
        coverage_note="已確認合作校 inbound exchange 入口；當期文件與期限尚未公開完整，須以兩校提名通知為準。",
    ),
    WorkflowSeed(
        school_name="香港中文大學 The Chinese University of Hong Kong",
        partner_website="https://www.oalglobal.cuhk.edu.hk/",
        sources=(
            ("CUHK incoming application", "https://www.oalglobal.cuhk.edu.hk/application/"),
            (
                "CUHK incoming online application guide",
                "https://www.oalglobal.cuhk.edu.hk/files/incoming/online_app_guide.pdf",
            ),
        ),
        summary="先經長庚選拔與提名，再依香港中文大學 Office of Academic Links 的線上指引完成申請。",
        details=(
            "官方申請頁與線上指南要求申請人先備妥個人、學業與交換目的資料。",
            "接待計畫、課程先修與學生身分可能影響額外附件，須依當期提名通知確認。",
        ),
        documents=("護照或身分資料", "英文歷年成績單", "不超過 300 字的 Statement of Purpose", "當期線上指南要求的其他附件"),
        submission_method=ApplicationSubmissionMethod.ONLINE,
    ),
)


def _seed_map() -> dict[str, WorkflowSeed]:
    result = {school_identity_key(seed.school_name): seed for seed in SEEDS}
    if len(result) != len(SEEDS):
        raise RuntimeError("CGU workflow seeds contain duplicate school identities")
    return result


def build_missing_workflows(
    partners: list[PartnerUniversity],
    existing: list[UniversityApplicationWorkflow],
) -> list[UniversityApplicationWorkflow]:
    seeds = _seed_map()
    existing_keys = {
        school_identity_key(row.school_name)
        for row in existing
        if row.home_university == CGU_NAME
    }
    missing = [
        partner
        for partner in partners
        if school_identity_key(partner.school_name) not in existing_keys
    ]
    unseeded = [
        partner.school_name
        for partner in missing
        if school_identity_key(partner.school_name) not in seeds
    ]
    if unseeded:
        raise RuntimeError(
            "Current CGU partners are missing reviewed workflow seeds: "
            + ", ".join(sorted(unseeded))
        )

    built: list[UniversityApplicationWorkflow] = []
    for partner in missing:
        seed = seeds[school_identity_key(partner.school_name)]
        built.append(
            build_cgu_reference_workflow(
                partner,
                partner_sources=list(seed.sources),
                partner_application_summary=seed.summary,
                partner_application_details=list(seed.details),
                required_documents=list(seed.documents),
                timing=seed.timing,
                submission_method=seed.submission_method,
                submission_email=seed.submission_email,
                portal_url=seed.portal_url,
                partner_website=seed.partner_website,
                coverage_note=seed.coverage_note,
                checked_at=CHECKED_AT,
            )
        )
    return built


def main() -> int:
    workflow_path: Path = data_paths()["application_workflows"]
    existing = read_jsonl(workflow_path, UniversityApplicationWorkflow)
    partners = fetch_partner_universities()
    if not partners:
        raise RuntimeError("Could not load the current CGU partner catalog")
    built = build_missing_workflows(partners, existing)
    if built:
        write_jsonl(workflow_path, [*existing, *built])
    print(
        f"CGU partners={len(partners)} existing_workflows={len(existing)} "
        f"backfilled={len(built)}"
    )
    for workflow in built:
        print(f"- {workflow.school_name}: {len(workflow.steps)} reference steps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
