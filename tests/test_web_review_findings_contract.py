from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINDINGS = ROOT / "docs" / "web-review-findings.md"
CHECKLIST = ROOT / "docs" / "web-review-checklist.md"
RELEASE_CANDIDATE = ROOT / "docs" / "web-release-candidate.md"


def test_web_review_findings_template_is_explicitly_unapproved() -> None:
    text = FINDINGS.read_text(encoding="utf-8")
    release_text = RELEASE_CANDIDATE.read_text(encoding="utf-8")
    candidate = next(
        line.removeprefix("- Candidate：")
        for line in release_text.splitlines()
        if line.startswith("- Candidate：")
    )

    assert f"對應審核包：{candidate}" in text
    assert "目前狀態：`template_ready`" in text
    assert "真人走查紀錄：0" in text
    assert "開放 findings：0" in text
    assert "Web 已核准：否" in text
    assert "Flutter 移植核准：否" in text
    assert "Web 已核准移植 Flutter：是" not in text
    assert "自動化 E2E 填入" in text


def test_web_review_findings_template_has_privacy_and_reproduction_fields() -> None:
    text = FINDINGS.read_text(encoding="utf-8")

    for privacy_rule in (
        "不要記錄姓名、Email、學號、學生證影像",
        "未遮蔽截圖",
        "不得放在 repository",
        "不能當官方證據",
    ):
        assert privacy_rule in text

    for required_field in (
        "工作階段代碼",
        "對應情境",
        "路由／功能",
        "瀏覽器／視窗",
        "審核包",
        "負責任務",
        "重現步驟",
        "預期結果",
        "實際結果",
        "學生影響",
        "官方來源／產品證據",
        "處置決定",
        "自動回歸",
        "真人重驗",
    ):
        assert required_field in text


def test_web_review_findings_template_preserves_severity_and_flutter_gates() -> None:
    text = FINDINGS.read_text(encoding="utf-8")

    for severity in ("| P0 |", "| P1 |", "| P2 |", "| P3 |"):
        assert severity in text
    assert "P0／P1 不得使用 `accepted_p2_p3`" in text
    assert "WEB-09` 的 Flutter 對等刻意不在本模板內" in text
    assert "正式核准只能記錄在 `docs/web-release-candidate.md`" in text


def test_web_review_findings_template_covers_web_definition_of_done() -> None:
    text = FINDINGS.read_text(encoding="utf-8")

    expected_scenarios = {
        "WEB-01",
        "WEB-02",
        "WEB-03",
        "WEB-04",
        "WEB-05",
        "WEB-06",
        "WEB-07",
        "WEB-08",
        "WEB-10",
        "WEB-11",
        "WEB-12",
    }
    assert all(f"| {scenario} |" in text for scenario in expected_scenarios)
    assert "至少兩所合作校" in text
    assert "匿名／本名／已驗證校系" in text
    assert "同 mutation ID 重試" in text
    assert "成立不等於正式規定已修改" in text
    assert "結案不得建立 revision、approval 或 publication" in text
    assert "桌面版與 390px 手機寬度" in text
    assert "不需外部搜尋" in text
    assert "能獨立理解下一步、文件缺口與送件方式" in text


def test_web_review_checklist_links_the_findings_template() -> None:
    text = CHECKLIST.read_text(encoding="utf-8")

    assert "docs/web-review-findings.md" in text
    assert "匿名工作階段代碼" in text
    assert "P0～P3" in text
    assert "重現、處置、回歸與重驗" in text
