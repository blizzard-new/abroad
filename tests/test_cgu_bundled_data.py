from __future__ import annotations

import json

from exchange_info import storage
from exchange_info.models import ApplicationDeadlineStatus
from exchange_info.workflow_structuring import workflow_structure_issues


def test_bundled_cgu_workflows_are_available_without_local_cache(
    monkeypatch, tmp_path
) -> None:
    assert storage.load_application_workflows(tmp_path) == []
    monkeypatch.setattr(storage, "DEFAULT_DATA_DIR", tmp_path)

    workflows = [
        row
        for row in storage.load_application_workflows(tmp_path)
        if row.home_university == "長庚大學"
    ]

    assert len(workflows) == 77
    assert sum(len(row.steps) for row in workflows) == 465
    assert all(row.sources for row in workflows)
    assert all(not workflow_structure_issues(row) for row in workflows)
    assert all(
        step.deadline_status == ApplicationDeadlineStatus.REFERENCE_ONLY
        and not step.deadline_reminder_eligible
        for row in workflows
        for step in row.steps
    )
    assert all(
        requirement.copies is None or requirement.copies >= 1
        for row in workflows
        for step in row.steps
        for requirement in step.document_requirements
    )


def test_bundled_cgu_destination_profiles_are_available_without_local_cache(
    monkeypatch,
    tmp_path,
) -> None:
    assert storage.load_destination_profiles(tmp_path) == []
    monkeypatch.setattr(storage, "DEFAULT_DATA_DIR", tmp_path)

    profiles = [
        row
        for row in storage.load_destination_profiles(tmp_path)
        if row.home_university == "長庚大學"
    ]

    assert len(profiles) == 77
    assert sum(row.coverage_status == "official_verified" for row in profiles) == 58
    assert sum(row.coverage_status == "official_verified" for row in profiles) == 19
    assert {row.coverage_status for row in profiles} == {
        "official_verified",
        "official_verified",
    }
    assert all(row.last_checked for row in profiles)
    assert all(row.sources for row in profiles)
    assert all(
        source.source_url.startswith("https://")
        for row in profiles
        for source in row.sources
    )
    assert all(
        row.housing_summary
        and row.cost_summary
        and row.transport_summary
        and row.campus_life_summary
        for row in profiles
    )

    lincoln = next(row for row in profiles if row.school_name == "林肯大學 Lincoln University")
    storage.save_destination_profiles(
        [lincoln.model_copy(update={"coverage_note": "本機人工補正優先。"})],
        tmp_path,
    )
    merged = [
        row
        for row in storage.load_destination_profiles(tmp_path)
        if row.home_university == "長庚大學"
    ]
    assert len(merged) == 77
    assert next(row for row in merged if row.school_name == lincoln.school_name).coverage_note == (
        "本機人工補正優先。"
    )


def test_bundled_cgu_completeness_report_matches_export() -> None:
    report = json.loads(
        (storage.BUNDLED_CGU_DIR / "catalog-completeness.json").read_text(
            encoding="utf-8"
        )
    )

    assert report["home_university"] == "長庚大學"
    assert report["partner_count"] == 77
    assert report["central_current_partner_count"] == 75
    assert report["departmental_reference_partner_count"] == 2
    assert report["partner_availability_status"] == {
        "departmental_reference": 2,
        "open": 75,
    }
    assert report["workflow_catalog_count"] == 77
    assert report["workflow_partner_match_count"] == 77
    assert report["partners_without_workflow_count"] == 0
    assert report["workflows_without_visible_partner_count"] == 0
    assert report["workflows_without_current_partner_count"] == 0
    assert report["destination_profile_count"] == 77
    assert report["destination_profile_status"] == {
        "official_verified": 58,
        "official_verified": 19,
    }
    assert report["destination_profile_source_count"] == 318
    assert report["destination_profiles_checked_at"] == "2026-08-13T00:00:00+08:00"
    assert len(report["partner_list_source_urls"]) == 4
    assert report["partner_list_checked_at"]
    assert report["workflow_structure"] == {
        "workflow_count": 77,
        "structured_workflow_count": 77,
        "step_count": 465,
        "structured_step_count": 465,
        "known_submission_method_count": 47,
        "steps_needing_confirmation": 465,
        "document_count": 1238,
        "documents_needing_confirmation": 1238,
        "source_count": 581,
        "prioritized_source_count": 581,
        "published_workflow_count": 0,
        "legacy_workflow_count": 77,
        "published_at_workflow_count": 0,
        "applicability_verified_workflow_count": 0,
        "verified_exact_deadline_count": 0,
        "reference_only_deadline_count": 465,
        "deadlines_needing_confirmation_count": 0,
        "deadline_not_applicable_count": 0,
        "reminder_eligible_deadline_count": 0,
        "structure_issue_count": 0,
    }
    assert len(report["schools"]) == 77
    assert sum(row["structured_workflow"] for row in report["schools"]) == 77
    assert report["coverage_status"] == {
        "official_verified": 76,
        "official_verified": 1,
    }
    assert report["workflow_catalog_orphans"] == []
    departmental_references = [
        row
        for row in report["schools"]
        if row["availability_status"] == "departmental_reference"
    ]
    assert {row["school_name"] for row in departmental_references} == {
        "法國艾克斯馬賽大學管理研究所 IAE Aix-Marseille Graduate School of Management",
        "雷恩商學院 Rennes School of Business",
    }
    assert all("中央" in row["availability_note"] for row in departmental_references)


def test_cgu_destination_batch_001_keeps_current_limits_and_review_status(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-001-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-001"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 9,
        "remaining_partner_profiles": 43,
    }

    expected_source_counts = {
        "馬來西亞馬來亞大學 Universiti Malaya": 3,
        "波蘭波茲南理工大學 Poznan University of Technology": 4,
        "加泰隆尼亞國際大學 Universitat Internacional de Catalunya": 2,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    assert "2026 秋季" in profiles[
        "馬來西亞馬來亞大學 Universiti Malaya"
    ].housing_summary
    assert "不保證" in profiles[
        "波蘭波茲南理工大學 Poznan University of Technology"
    ].housing_summary
    assert "不直接與學生簽住宿合約" in profiles[
        "加泰隆尼亞國際大學 Universitat Internacional de Catalunya"
    ].housing_summary


def test_cgu_destination_batch_002_keeps_current_limits_and_review_status(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-002-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-002"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 14,
        "remaining_partner_profiles": 40,
    }

    expected_source_counts = {
        "香港中文大學 The Chinese University of Hong Kong": 4,
        "北京清華大學 Tsinghua University": 4,
        "威斯康辛大學密爾基分校 University of Wisconsin-Milwaukee": 6,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    assert "2025/26" in profiles[
        "香港中文大學 The Chinese University of Hong Kong"
    ].cost_summary
    assert "房型描述不完全一致" in profiles[
        "北京清華大學 Tsinghua University"
    ].coverage_note
    assert "24 小時" in profiles[
        "北京清華大學 Tsinghua University"
    ].housing_summary
    assert "2026-05-01" in profiles[
        "威斯康辛大學密爾基分校 University of Wisconsin-Milwaukee"
    ].housing_summary
    assert "候補" in profiles[
        "威斯康辛大學密爾基分校 University of Wisconsin-Milwaukee"
    ].housing_summary


def test_cgu_destination_batch_003_keeps_current_limits_and_review_status(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-003-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-003"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 13,
        "remaining_partner_profiles": 37,
    }

    expected_source_counts = {
        "福坦莫大學 Fordham University": 4,
        "義大利佩魯賈大學 University of Perugia": 4,
        "法國薩克雷大學 University of Paris-Saclay": 5,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    assert "財力證明而非預算" in profiles[
        "福坦莫大學 Fordham University"
    ].coverage_note
    assert "2025/26" in profiles[
        "福坦莫大學 Fordham University"
    ].coverage_note
    assert "2026-04-28" in profiles[
        "義大利佩魯賈大學 University of Perugia"
    ].coverage_note
    assert "住宿意願不等於床位分配" in profiles[
        "義大利佩魯賈大學 University of Perugia"
    ].coverage_note
    assert "48 小時" in profiles[
        "法國薩克雷大學 University of Paris-Saclay"
    ].housing_summary
    assert "2021 年舊金額" in profiles[
        "法國薩克雷大學 University of Paris-Saclay"
    ].coverage_note


def test_cgu_destination_batch_004_keeps_current_limits_and_review_status(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-004-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-004"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 14,
        "remaining_partner_profiles": 34,
    }

    expected_source_counts = {
        "西班牙馬拉加大學 Universidad de Málaga": 5,
        "法國凱致商學院 KEDGE Business School": 4,
        "比利時托馬斯莫爾應用科技大學 Thomas More University of Applied Sciences": 5,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    assert "不提供學生住宿" in profiles[
        "西班牙馬拉加大學 Universidad de Málaga"
    ].housing_summary
    assert "沒有公布可作 2026/27 完整預算" in profiles[
        "西班牙馬拉加大學 Universidad de Málaga"
    ].cost_summary
    assert "Bordeaux 或 Marseille 校區" in profiles[
        "法國凱致商學院 KEDGE Business School"
    ].coverage_note
    assert "2025/26" in profiles[
        "法國凱致商學院 KEDGE Business School"
    ].coverage_note
    thomas_more = profiles[
        "比利時托馬斯莫爾應用科技大學 Thomas More University of Applied Sciences"
    ]
    assert "EUR 850–1,150" in thomas_more.cost_summary
    assert "不含學費與交通" in thomas_more.cost_summary
    assert "blocked account 金額仍標示 2025/26" in thomas_more.coverage_note


def test_cgu_destination_batch_005_keeps_current_limits_and_review_status(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-005-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-005"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 14,
        "remaining_partner_profiles": 31,
    }

    expected_source_counts = {
        "上海交通大學 Shanghai Jiao Tong University": 4,
        "復旦大學 Fudan University": 5,
        "德國呂貝克應用科技大學 Technische Hochschule Lübeck": 5,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    sjtu = profiles["上海交通大學 Shanghai Jiao Tong University"]
    assert "2020 年核准" in sjtu.cost_summary
    assert "床位有限且不保證" in sjtu.housing_summary
    fudan = profiles["復旦大學 Fudan University"]
    assert "候補" in fudan.housing_summary
    assert "校級與院級" in fudan.coverage_note
    assert "不能把特定學院或舊年度 fact sheet" in fudan.coverage_note
    th_luebeck = profiles[
        "德國呂貝克應用科技大學 Technische Hochschule Lübeck"
    ]
    assert "EUR 900–1,000" in th_luebeck.cost_summary
    assert "EUR 394.30" in th_luebeck.cost_summary
    assert "已過的 2026 年 3 月日期" in th_luebeck.coverage_note


def test_cgu_destination_batch_006_separates_current_facts_from_stale_prices(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-006-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-006"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 13,
        "remaining_partner_profiles": 28,
    }

    expected_source_counts = {
        "捷克俄斯特拉發科技大學 VSB – Technical University of Ostrava": 4,
        "法國國立工業系統工程學校 EIGSI Engineering School": 5,
        "韓國江原國立大學 Kangwon National University": 4,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    vsb = profiles[
        "捷克俄斯特拉發科技大學 VSB – Technical University of Ostrava"
    ]
    assert "EUR 500／月" in vsb.cost_summary
    assert "CZK 8,000" in vsb.housing_summary
    assert "2026-09-07 至 09-13" in vsb.campus_life_summary
    assert "沒有把 Faculty of Economics" in vsb.coverage_note

    eigsi = profiles["法國國立工業系統工程學校 EIGSI Engineering School"]
    assert "2026–2027 fact sheet" in eigsi.cost_summary
    assert "房間目前已滿" in eigsi.housing_summary
    assert "春季大多為法語" in eigsi.campus_life_summary
    assert "沒有混入 Casablanca" in eigsi.coverage_note

    kangwon = profiles["韓國江原國立大學 Kangwon National University"]
    assert "宿舍費頁本身標示「As of 2019」" in kangwon.cost_summary
    assert "交換專案頁明示交換生宿舍有保障" in kangwon.housing_summary
    assert "Buddy 是學生自願活動" in kangwon.campus_life_summary
    assert "限定 Chuncheon Campus" in kangwon.coverage_note


def test_cgu_destination_batch_007_keeps_fee_and_campus_scope_explicit(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-007-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-007"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 12,
        "remaining_partner_profiles": 25,
    }

    expected_source_counts = {
        (
            "德國拉芬斯堡-魏恩加騰應用科技大學 "
            "Ravensburg-Weingarten University of Applied Sciences"
        ): 4,
        "德國開姆尼茨工業大學 Chemnitz University of Technology": 5,
        "歐洲知識經濟與管理學院 Skema Business School": 3,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    rwu = profiles[
        "德國拉芬斯堡-魏恩加騰應用科技大學 "
        "Ravensburg-Weingarten University of Applied Sciences"
    ]
    assert "EUR 215" in rwu.cost_summary
    assert "EUR 1,500" in rwu.cost_summary
    assert "交換生原則上自動免除" in rwu.cost_summary
    assert "勾選住宿意願不等於取得床位" in rwu.housing_summary

    chemnitz = profiles[
        "德國開姆尼茨工業大學 Chemnitz University of Technology"
    ]
    assert "EUR 341.40" in chemnitz.cost_summary
    assert "底層引用 2021 年調查" in chemnitz.cost_summary
    assert "不是床位保證" in chemnitz.housing_summary
    assert "疑似小數誤植" in chemnitz.coverage_note

    skema = profiles["歐洲知識經濟與管理學院 Skema Business School"]
    assert "EUR 900–1,800" in skema.cost_summary
    assert "不能套到 Lille 或 Sophia Antipolis" in skema.cost_summary
    assert "都沒有校內住宿" in skema.housing_summary
    assert "學生必須等錄取確認實際法國校區" in skema.coverage_note


def test_cgu_destination_batch_008_keeps_conflicts_and_stale_terms_visible(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-008-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-008"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 13,
        "remaining_partner_profiles": 22,
    }

    expected_source_counts = {
        "波蘭華沙生命科學大學 Warsaw University of Life Sciences": 4,
        (
            "法國國立圖盧茲綜合理工學院 "
            "National Polytechnic Institute of Toulouse"
        ): 5,
        "印度昌迪加爾大學 Chandigarh University": 4,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    sggw = profiles["波蘭華沙生命科學大學 Warsaw University of Life Sciences"]
    assert "PLN 550–870／月" in sggw.cost_summary
    assert "不保證有宿舍" in sggw.housing_summary
    assert "不提供機場接送" in sggw.transport_summary
    assert "提名期限不一致" in sggw.coverage_note

    toulouse = profiles[
        "法國國立圖盧茲綜合理工學院 "
        "National Polytechnic Institute of Toulouse"
    ]
    assert "EUR 250–600" in toulouse.cost_summary
    assert "未承諾每位申請者都有床位" in toulouse.housing_summary
    assert "各自提名及收件" in toulouse.campus_life_summary
    assert "FEIP 更明示英法語各半" in toulouse.campus_life_summary

    chandigarh = profiles["印度昌迪加爾大學 Chandigarh University"]
    assert chandigarh.city == "Mohali, Punjab"
    assert "不收 Chandigarh University 學費" in chandigarh.cost_summary
    assert "一般國際學生費率" in chandigarh.housing_summary
    assert "2021 fact sheet 的免費住宿" in chandigarh.coverage_note


def test_cgu_destination_batch_009_keeps_fee_categories_and_options_separate(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-009-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-009"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 13,
        "remaining_partner_profiles": 19,
    }

    expected_source_counts = {
        "波蘭華沙醫學大學 Medical University of Warsaw": 5,
        "韓國嘉泉大學 Gachon University": 4,
        "捷克布拉格紐約大學 University of New York in Prague (UNYP)": 4,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    wum = profiles["波蘭華沙醫學大學 Medical University of Warsaw"]
    assert "PLN 1,220／月" in wum.cost_summary
    assert "PLN 1,312／月" in wum.cost_summary
    assert "不能自行採較低費率" in wum.cost_summary
    assert "不等於保證床位" in wum.housing_summary
    assert "主要授課語言是波蘭語" in wum.campus_life_summary

    gachon = profiles["韓國嘉泉大學 Gachon University"]
    assert "KRW 1,486,400" in gachon.cost_summary
    assert "舊國際處宿舍頁的較低價格" in gachon.cost_summary
    assert "頁面未標適用學期" in gachon.transport_summary
    assert "Medical Campus" in gachon.campus_life_summary
    assert "不能把『有英語課』理解為全校英語環境" in gachon.campus_life_summary

    unyp = profiles[
        "捷克布拉格紐約大學 University of New York in Prague (UNYP)"
    ]
    assert "USD 6,000" in unyp.cost_summary
    assert "不是所有交換生的必付費用" in unyp.cost_summary
    assert "沒有自己的校內宿舍" in unyp.housing_summary
    assert "兩種路徑不能混為同一項住宿承諾" in unyp.housing_summary
    assert "2026-04-17" in unyp.campus_life_summary
    assert "已在本次查核日前截止" in unyp.campus_life_summary


def test_cgu_destination_batch_010_preserves_program_and_housing_boundaries(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-010-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-010"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 13,
        "remaining_partner_profiles": 16,
    }

    expected_source_counts = {
        "法國EPF工程師學校 EPF École d'ingénieurs": 4,
        "里昂精英工程師學校 ECAM LaSelle": 4,
        "日本成城大學經濟學院 Seijo University, Faculty of Economics": 5,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    epf = profiles["法國EPF工程師學校 EPF École d'ingénieurs"]
    assert "只適用 2026 暑期法語工程師課程" in epf.cost_summary
    assert "不能拿來估算一般學期交換住宿" in epf.cost_summary
    assert "不保證配到宿舍" in epf.housing_summary
    assert "不能跨校區套用交通資訊" in epf.transport_summary
    assert "秋季只開放五年級課程" in epf.campus_life_summary
    assert "Montpellier" in epf.campus_life_summary

    ecam = profiles["里昂精英工程師學校 ECAM LaSelle"]
    assert "EUR 770–1,149" in ecam.cost_summary
    assert "不是交換生專屬費率或保證價格" in ecam.cost_summary
    assert "subject to availability" in ecam.housing_summary
    assert "不能因此推定交換生一定有校內房間" in ecam.housing_summary
    assert "母校提名 4 月 3 日前" in ecam.campus_life_summary

    seijo = profiles[
        "日本成城大學經濟學院 Seijo University, Faculty of Economics"
    ]
    assert "不能預設每位學生都會取得" in seijo.cost_summary
    assert "不是學生自行保證選到特定房型" in seijo.housing_summary
    assert "20 個交換生房間" in seijo.housing_summary
    assert "只有被分派至 Amista" in seijo.transport_summary
    assert "Chang Gung University, College of Management" in seijo.campus_life_summary


def test_cgu_destination_batch_011_preserves_fee_housing_and_term_boundaries(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-011-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-011"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 13,
        "remaining_partner_profiles": 13,
    }

    expected_source_counts = {
        "法國航太工程高等學院 Institute of Polytechnic Science and Aeronautics (IPSA)": 4,
        "德國巴登-符騰堡州立合作大學 Duale Hochschule Baden-Württemberg Karlsruhe, Germany Baden-Wuerttemberg Cooperative State University": 5,
        "雷恩商學院 Rennes School of Business": 4,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    ipsa = profiles[
        "法國航太工程高等學院 Institute of Polytechnic Science and Aeronautics (IPSA)"
    ]
    assert "EUR 4,500／學期" in ipsa.cost_summary
    assert "不是長庚經合作協議提名" in ipsa.cost_summary
    assert "只適用 2025/26" in ipsa.cost_summary
    assert "不能當成 2026/27" in ipsa.cost_summary
    assert "一、二年級不開放交換" in ipsa.campus_life_summary
    assert "與現行網頁已不同" in ipsa.campus_life_summary

    dhbw = profiles[
        "德國巴登-符騰堡州立合作大學 Duale Hochschule Baden-Württemberg Karlsruhe, Germany Baden-Wuerttemberg Cooperative State University"
    ]
    assert "2023 年 DZHW" in dhbw.cost_summary
    assert "Spring 2026" in dhbw.cost_summary
    assert "至少租六個月" in dhbw.housing_summary
    assert "提早離開仍須支付" in dhbw.housing_summary
    assert "平日 18:00–06:00" in dhbw.transport_summary
    assert "不能寫成全時段免費交通" in dhbw.transport_summary

    rennes = profiles["雷恩商學院 Rennes School of Business"]
    assert "EUR 450–700" in rennes.cost_summary
    assert "不能套用 Paris" in rennes.cost_summary
    assert "不是保證床位" in rennes.housing_summary
    assert "2026 年 9 月" in rennes.housing_summary
    assert "Level 2" in rennes.campus_life_summary
    assert "兩個官方來源不一致" in rennes.campus_life_summary
    assert "不能自行判定 Level 2 春季可申請" in rennes.campus_life_summary


def test_cgu_destination_batch_012_preserves_program_age_and_identity_boundaries(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-012-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-012"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 13,
        "remaining_partner_profiles": 10,
    }

    expected_source_counts = {
        "泰國清邁大學公衛學院 Chiang Mai University, Faculty of Public Health": 4,
        "越南胡志明市科技教育大學 HCMC University of Technology and Education": 4,
        "馬來西亞管理與科技大學 Management and Science University": 5,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    cmu = profiles[
        "泰國清邁大學公衛學院 Chiang Mai University, Faculty of Public Health"
    ]
    assert "THB 9,000–15,000／月" in cmu.cost_summary
    assert "不是 Faculty of Public Health 保證價格" in cmu.cost_summary
    assert "只承諾 host faculty 協助" in cmu.housing_summary
    assert "沒有承諾校內宿舍或保證床位" in cmu.housing_summary
    assert "免費校車不等於全清邁免費交通" in cmu.transport_summary
    assert "課程清單僅供參考" in cmu.campus_life_summary
    assert "不能把校級英文課清單" in cmu.campus_life_summary

    hcmute = profiles[
        "越南胡志明市科技教育大學 HCMC University of Technology and Education"
    ]
    assert "一次繳 12 個月" in hcmute.cost_summary
    assert "不能當作一學期外籍交換生房價" in hcmute.cost_summary
    assert "2020 Teaching Practicum" in hcmute.cost_summary
    assert "不能套用一般交換" in hcmute.cost_summary
    assert "沒有承諾免費接機" in hcmute.transport_summary
    assert "Ho Chi Minh City University of Technology and Engineering" in (
        hcmute.campus_life_summary
    )
    assert "產品保留長庚既有合作校名稱" in hcmute.campus_life_summary

    msu = profiles["馬來西亞管理與科技大學 Management and Science University"]
    assert "March 2023" in msu.cost_summary
    assert "不能當成 2026/27 現價" in msu.cost_summary
    assert "LOCAL STUDENT ONLY" in msu.housing_summary
    assert "長庚交換生不能用這個較低價格估算" in msu.housing_summary
    assert "最短租六個月" in msu.housing_summary
    assert "不能據此宣稱 2026 已正式營運" in msu.transport_summary
    assert "不能直接建立 2026/27 提醒" in msu.campus_life_summary


def test_cgu_destination_batch_013_preserves_dual_degree_and_department_boundaries(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-013-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-013"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 13,
        "remaining_partner_profiles": 7,
    }

    expected_source_counts = {
        "馬里蘭大學巴爾的摩分校 The University of Maryland School of Nursing": 4,
        "明尼蘇達大學 University of Minnesota": 5,
        "法國艾克斯馬賽大學管理研究所 IAE Aix-Marseille Graduate School of Management": 4,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    umson = profiles[
        "馬里蘭大學巴爾的摩分校 The University of Maryland School of Nursing"
    ]
    assert "不是長庚雙學位學生的應繳帳單" in umson.cost_summary
    assert "沒有替長庚雙學位學生保留或保證床位" in umson.housing_summary
    assert "不能在 UMSON 確認實際校區前" in umson.transport_summary
    assert "限定長庚大學護理學生" in umson.campus_life_summary
    assert "overall GPA 3.0" in umson.campus_life_summary
    assert "science GPA 3.0" in umson.campus_life_summary
    assert "1 月 15 日" in umson.campus_life_summary
    assert "2 月 1 日" in umson.campus_life_summary
    assert "7 月 15 日優先期限不能取代" in umson.campus_life_summary

    umn = profiles["明尼蘇達大學 University of Minnesota"]
    assert "沒有指出對應學院、校區、學位" in umn.cost_summary
    assert "USD 11,527" in umn.cost_summary
    assert "USD 26,951" in umn.cost_summary
    assert "USD 69,780" in umn.cost_summary
    assert "任何一個數字都不能冒充長庚雙學位" in umn.cost_summary
    assert "2023–24" in umn.cost_summary
    assert "不證明長庚雙學位屬 Carlson" in umn.housing_summary
    assert "不得依『University of Minnesota』名稱自行選定" in umn.transport_summary
    assert "未取得專案文件前" in umn.campus_life_summary
    assert "不能把任何一般交換截止日" in umn.campus_life_summary

    iae = profiles[
        "法國艾克斯馬賽大學管理研究所 IAE Aix-Marseille Graduate School of Management"
    ]
    assert "不是長庚管理學院交換的固定帳單" in iae.cost_summary
    assert "120 小時" in iae.housing_summary
    assert "EUR 70" in iae.housing_summary
    assert "不能選宿舍或房型" in iae.housing_summary
    assert "先到先得" in iae.housing_summary
    assert "Puyricard" in iae.transport_summary
    assert "只作長庚管理學院的院級交換參考" in iae.campus_life_summary
    assert "free mover 或直接申請不符合資格" in iae.campus_life_summary
    assert "學士三年級且年滿 21 歲" in iae.campus_life_summary
    assert "課程全部為 Master’s level" in iae.campus_life_summary


def test_cgu_destination_batch_014_preserves_program_year_and_housing_boundaries(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-014-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-014"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 13,
        "remaining_partner_profiles": 4,
    }

    expected_source_counts = {
        "羅格斯大學 Rutgers, The State University of New Jersey": 4,
        "荷蘭恩荷芬理工大學 Eindhoven University of Technology": 4,
        "韓國車醫科大學 CHA University": 5,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert all(source.source_url.startswith("https://") for source in profile.sources)
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    rutgers = profiles["羅格斯大學 Rutgers, The State University of New Jersey"]
    assert "沒有指出長庚雙學位所屬" in rutgers.cost_summary
    assert "Camden／Newark／New Brunswick" in rutgers.cost_summary
    assert "USD 62,782" in rutgers.cost_summary
    assert "不是長庚雙學位帳單" in rutgers.cost_summary
    assert "USD 70" in rutgers.cost_summary
    assert "沒有保證床位" in rutgers.housing_summary
    assert "不能替學生選定機場" in rutgers.transport_summary
    assert "3 封推薦信" in rutgers.campus_life_summary
    assert "不能在專案未確認時自動加入" in rutgers.campus_life_summary

    tue = profiles["荷蘭恩荷芬理工大學 Eindhoven University of Technology"]
    assert "EUR 1,200／月" in tue.cost_summary
    assert "一般學位生參考，不是長庚交換帳單" in tue.cost_summary
    assert "2023–24 Chemical Engineering and Chemistry" in tue.cost_summary
    assert "free mover" in tue.cost_summary
    assert "非常有限" in tue.housing_summary
    assert "先到先得" in tue.housing_summary
    assert "約短缺 1,500 個學生住宿單位" in tue.housing_summary
    assert "不能直接建立 2026/27 提醒" in tue.campus_life_summary
    assert "課程容量不保證" in tue.campus_life_summary

    cha = profiles["韓國車醫科大學 CHA University"]
    assert "學費繳給母校" in cha.cost_summary
    assert "不代表住宿、保險、簽證" in cha.cost_summary
    assert "沒有交換生專屬名額" in cha.housing_summary
    assert "標示已保留床位" in cha.housing_summary
    assert "Pocheon 主校區路線" in cha.transport_summary
    assert "Bundang" in cha.transport_summary
    assert "(~2019)" in cha.campus_life_summary
    assert "2023 planned" in cha.campus_life_summary
    assert "不能當成現在仍開放的學期交換" in cha.campus_life_summary


def test_cgu_destination_batch_015_preserves_current_and_historical_boundaries(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-015-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-015"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 3,
        "sources_added": 13,
        "remaining_partner_profiles": 1,
    }

    expected_source_counts = {
        "巴西聖保羅聯邦大學 Universidade Federal de São Paulo": 4,
        "武漢大學 Wuhan University": 5,
        "福州大學 Fuzhou University": 4,
    }
    assert {row["school_name"] for row in manifest["profiles"]} == set(
        expected_source_counts
    )
    for school_name, source_count in expected_source_counts.items():
        profile = profiles[school_name]
        assert profile.coverage_status == "official_verified"
        assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
        assert len(profile.sources) == source_count
        assert all(source.source_url.startswith("https://") for source in profile.sources)
        assert "尚未完成第二位真人內容審查" in profile.coverage_note

    unifesp = profiles[
        "巴西聖保羅聯邦大學 Universidade Federal de São Paulo"
    ]
    assert "tuition and miscellaneous fees 繳給母校" in unifesp.cost_summary
    assert "不能把『母校繳費』顯示成零成本" in unifesp.cost_summary
    assert "seguro fiança" in unifesp.housing_summary
    assert "不是校方宿舍、保留床位或租金保證" in unifesp.housing_summary
    assert "七個 campus" in unifesp.transport_summary
    assert "15 October" in unifesp.campus_life_summary
    assert "15 May" in unifesp.campus_life_summary
    assert "不能直接建立下一梯次精確提醒" in unifesp.campus_life_summary

    wuhan = profiles["武漢大學 Wuhan University"]
    assert "June 2016" in wuhan.cost_summary
    assert "沒有列出長庚大學" in wuhan.cost_summary
    assert "RMB 600–1,400／月" in wuhan.cost_summary
    assert "不能當成 2026/27 預算或帳單" in wuhan.cost_summary
    assert "沒有公開長庚交換生" in wuhan.housing_summary
    assert "2022 校園文章曾寫 school bus 調整為免費" in wuhan.transport_summary
    assert "2026 Campus Card" in wuhan.transport_summary
    assert "不能把 2022 免費校車當成現行交換生權益" in wuhan.transport_summary
    assert "不能支持 workflow 內的 15 April／15 October" in wuhan.campus_life_summary

    fuzhou = profiles["福州大學 Fuzhou University"]
    assert "合作協議含互免學費條款" in fuzhou.cost_summary
    assert "不是長庚交換帳單或固定預算" in fuzhou.cost_summary
    assert "RMB 3,500／學年" in fuzhou.housing_summary
    assert "RMB 7,000／年" in fuzhou.housing_summary
    assert "沒有交換生床位保證" in fuzhou.housing_summary
    assert "Qishan Campus" in fuzhou.transport_summary
    assert "舊語言生頁的接機服務也不能套用校際交換" in fuzhou.transport_summary
    assert "2025 秋季 15 May" in fuzhou.campus_life_summary
    assert "不能直接建立 2026/27 提醒" in fuzhou.campus_life_summary


def test_cgu_destination_batch_016_keeps_icd_campus_cost_and_deadline_boundaries(
    tmp_path,
) -> None:
    manifest = json.loads(
        (
            storage.BUNDLED_CGU_DIR.parents[3]
            / "docs"
            / "review-batches"
            / "data-006-batch-016-destination-profiles.json"
        ).read_text(encoding="utf-8")
    )
    profiles = {
        row.school_name: row
        for row in storage.load_destination_profiles(
            tmp_path,
            include_bundled_baseline=True,
        )
        if row.home_university == "長庚大學"
    }

    assert manifest["batch_id"] == "DATA-006-BATCH-016"
    assert manifest["review_status"] == "human_review_required"
    assert manifest["public_student_data_changed"] is True
    assert manifest["approvals_created"] is False
    assert manifest["coverage_effect"] == {
        "profiles_added": 1,
        "sources_added": 5,
        "remaining_partner_profiles": 0,
    }

    profile = profiles["法國ICD商學院 ICD Business School"]
    assert profile.coverage_status == "official_verified"
    assert profile.last_checked.isoformat() == "2026-08-13T00:00:00+08:00"
    assert len(profile.sources) == 5
    assert all(source.source_url.startswith("https://") for source in profile.sources)
    assert "尚未完成第二位真人內容審查" in profile.coverage_note

    assert "EUR 5,495／學期" in profile.cost_summary
    assert "不適用交換生" in profile.cost_summary
    assert "Toulouse fact sheet 也寫明交換生不收學費" in profile.cost_summary
    assert "不代表生活成本免費" in profile.cost_summary
    assert "Paris 學生公寓約 EUR 900–1,200／月" in profile.housing_summary
    assert "Toulouse 學生公寓 EUR 500–700" in profile.housing_summary
    assert "不保證床位" in profile.housing_summary
    assert "EUR 90.80／月" in profile.transport_summary
    assert "EUR 15.50／月" in profile.transport_summary
    assert "未滿 25 歲" in profile.transport_summary
    assert "Paris 與 Toulouse" in profile.city
    assert "Lyon" in profile.city
    assert "只公開 Paris 與 Toulouse" in profile.city
    assert "15 November" in profile.campus_life_summary
    assert "1 November" in profile.campus_life_summary
    assert "不能直接建立提醒" in profile.campus_life_summary
    assert "GPA 2.5／4" in profile.campus_life_summary
    assert "TOEFL iBT 70／B2" in profile.campus_life_summary
    assert "25–30 ECTS" in profile.campus_life_summary


def test_backfilled_cgu_workflows_keep_current_details_reference_only() -> None:
    workflows = {
        row.school_name: row
        for row in storage.load_bundled_application_workflows()
        if row.home_university == "長庚大學"
    }

    sjtu = workflows["上海交通大學 Shanghai Jiao Tong University"]
    assert sjtu.coverage_status == "official_verified"
    assert any("國籍認定" in detail for step in sjtu.steps for detail in step.details)

    paris_saclay = workflows["法國薩克雷大學 University of Paris-Saclay"]
    assert any("2026-10-30" in (step.timing or "") for step in paris_saclay.steps)
    assert all(
        step.deadline_status == ApplicationDeadlineStatus.REFERENCE_ONLY
        and not step.deadline_reminder_eligible
        for step in paris_saclay.steps
    )

    warsaw = workflows["波蘭華沙醫學大學 Medical University of Warsaw"]
    tue = workflows["荷蘭恩荷芬理工大學 Eindhoven University of Technology"]
    icd = workflows["法國ICD商學院 ICD Business School"]
    assert warsaw.partner_website == "https://www.wum.edu.pl/en"
    assert tue.partner_website == "https://www.tue.nl/en/"
    assert icd.partner_website == "https://www.icd-bs.com/"
