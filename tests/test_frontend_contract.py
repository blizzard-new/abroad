import json
from pathlib import Path


STATIC_DIR = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static"


def test_first_visit_school_choice_is_optional_and_current() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "你目前就讀哪一所台灣大學？" in html
    assert "選擇我的學校" in html
    assert "先看看全部交換學校" in html
    assert "62 所合作校" in html
    assert "partner_count: 62" in script
    assert "browseWithoutSchoolSelection" in script


def test_partner_schools_use_verified_official_photo_manifest() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    manifest = json.loads(
        (STATIC_DIR / "assets" / "school-images.json").read_text(encoding="utf-8")
    )

    assert 'id="school-detail-photo"' in html
    assert 'fetchJson("/static/assets/school-images.json")' in script
    assert "renderSchoolPhoto(item, \"table\")" in script
    assert "renderSchoolPhoto(item, \"card\")" in script
    assert "官方圖片來源" in script
    verified = {
        row["school_name"]
        for row in manifest["schools"]
        if row.get("status") == "verified"
    }
    assert len(verified) >= 71
    assert "蔚山科技大學(Ulsan National Institute of Science and Technology)" in verified
    assert "明知大學(Myongi university)" in verified
    assert "世宗大學 (Sejong University)" in verified


def test_school_onboarding_supports_keyboard_dismissal_and_focus_return() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'event.key === "Escape"' in script
    assert 'event.key !== "Tab"' in script
    assert "onboardingReturnFocus" in script
    assert "returnFocus.focus()" in script


def test_school_detail_does_not_recrawl_empty_experiences_on_open() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'fetchJson(`/student-experiences?school=${school}&home_school=${encodeURIComponent(activeHomeSchool())}`)' in script
    assert "if (!forceRefresh && digest.total_sources === 0)" not in script
    assert "/student-experiences/refresh?school=" in script


def test_ntpu_uses_the_same_dynamic_web_shell() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'data-home-school="國立臺北大學"' in html
    assert "/static/assets/ntpu-campus.jpg" in html
    assert "refreshHomeUniversityData" in script
    assert "school: requestedSchool" in script
    assert "academicMinimum()" in script
    assert 'href="#university-posts"' in html


def test_home_school_switch_rejects_stale_dashboard_responses() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "function isCurrentHomeSchool" in script
    assert "const requestedSchool = homeSchool;" in script
    assert "if (!isCurrentHomeSchool(requestedSchool)) return false;" in script
    assert 'window.history.replaceState({}, "", "#partners")' in script
    assert "const dashboardMismatch = Boolean(state.dashboard?.school_name)" in script
    assert "if (needsRefresh && reload) refreshHomeUniversityData();" in script


def test_school_detail_uses_accessible_real_tabs() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'role="tablist"' in html
    detail_tabs = html.split('<nav class="detail-tabs"', 1)[1].split("</nav>", 1)[0]
    assert detail_tabs.count('role="tab"') == 5
    assert 'role="tabpanel"' in script
    assert "activateDetailTab" in script
    assert 'event.key === "ArrowRight"' in script
    assert 'event.key === "ArrowLeft"' in script
    assert 'event.key === "Home"' in script
    assert 'event.key === "End"' in script
    assert "scrollIntoView" in script


def test_student_life_has_ten_decision_categories_and_progressive_disclosure() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    life_block = script.split("const LIFE_SECTIONS = [", 1)[1].split("];", 1)[0]
    assert life_block.count("{ theme:") == 10
    for label in (
        "住宿與宿舍",
        "每月生活預算",
        "飲食與採買",
        "交通與地點",
        "課業與教學",
        "氣候與穿著",
        "校園活動與社交",
        "安全、醫療與保險",
        "文化適應與交朋友",
        "旅行與周邊城市",
    ):
        assert label in life_block
    assert "hasConcretePoints" in script
    assert "renderLifeSourceLinks" in script
    assert "尚無足夠的公開學生來源" in script
    assert "不以一般學校介紹代替真實經驗" in script


def test_student_life_prioritizes_sources_and_uses_concrete_points() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    render_block = script.split("function renderStudentLife", 1)[1].split(
        "function experienceKeyPoints", 1
    )[0]
    points_block = script.split("function buildLifeKeyPoints", 1)[1].split(
        "function renderLifeSourceLinks", 1
    )[0]

    assert ".sort((left, right)" in render_block
    assert "source_count" in render_block
    assert "highlight.key_points" in points_block
    assert "樣本仍有限" not in points_block


def test_direct_school_link_returns_to_partner_list() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'window.location.hash.startsWith("#school=")' in script
    assert '? "#partners"' in script


def test_quick_overview_explains_fit_strengths_and_risks() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "這間學校適合我嗎？" in script
    assert "適合先列入候選，如果你…" in script
    assert "學生常提到的優點" in script
    assert "申請前先確認" in script
    assert "合作校公開條件" in script
    assert "官方條件與學生經驗分開標示" in script
    assert "updateQuickDecisionFit(digest)" in script


def test_partner_pages_use_chinese_bullet_summaries_instead_of_raw_english() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert "student_summary_zh" in script
    assert "renderStudentPointList" in script
    assert "學生版中文重點" in script
    assert "資格與語言重點" in script
    assert "英文資料已翻成中文" in script
    assert "const fullCondition = [item.eligibility, item.application_info]" not in script
    assert ".student-point-list" in styles
    assert ".partner-summary-groups" in styles


def test_school_detail_uses_full_background_photo_liquid_panels_and_scroll_motion() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'variant === "detail"' in script
    assert "setSchoolHeroProgress" in script
    assert "queueSchoolHeroMotion" in script
    assert 'window.addEventListener("scroll", queueSchoolHeroMotion' in script
    assert ".school-detail-photo {\n  position: absolute;" in styles
    assert "--hero-photo-opacity" in styles
    assert ".school-detail-copy,\n.detail-primary-facts" in styles
    assert "backdrop-filter: saturate(170%) blur(28px)" in styles
    assert "/* Liquid Glass interaction system */" in styles
    assert "@media (prefers-reduced-motion: reduce)" in styles


def test_school_detail_cards_wrap_highlights_and_replace_long_urls_with_links() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert "function renderSummaryText" in script
    assert 'class="summary-inline-link"' in script
    assert ".map((point) => `<li>${renderSummaryText(point)}</li>`)" in script
    assert ".summary-inline-link" in styles
    assert ".text-highlight {\n  -webkit-box-decoration-break: clone;" in styles
    assert "overflow-wrap: anywhere" in styles
    assert "grid-template-columns: repeat(auto-fit, minmax(210px, 1fr))" in styles


def test_premium_web_material_keeps_glass_hierarchy_without_heavy_button_chrome() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert "20260721-student-survival-4" in html
    assert "Premium product refinement" in styles
    assert "Final cascade for the premium material" in styles
    assert "--premium-surface" in styles
    assert ".featured-board-card:hover" in styles
    assert ".partner-results" in styles
    assert ".community-empty" in styles
    assert "background-color: rgba(17, 30, 44, 0.94)" in styles


def test_grounded_advisor_and_document_checker_are_independent_pages() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'href="#advisor" data-section="advisor"' in html
    assert 'data-university-page="advisor"' in html
    assert 'data-university-page="document-check"' in html
    assert 'data-university-page="writing-assistant"' in html
    assert "僅依已查核來源作答；符合度不是錄取機率" in html
    assert 'id="advisor-department"' in html
    assert 'id="advisor-current-year"' in html
    assert 'fetchJson("/ai/status")' in script
    assert "advisorCitationMeta" in script
    assert "使用 AI 深度檢查" in html
    assert 'fetchJson("/advisor/plan"' in script
    assert 'fetchJson("/document-check"' in script
    assert 'fetchJson("/ai/rewrite-document"' in script
    assert "AI 建議稿" in script
    assert "addAdvisorTaskToCalendar" in script
    assert '<details class="document-issue' in script
    assert '<details class="document-check-suggestions' in script
    assert "Grounded advisor and document review" in styles
    assert "backdrop-filter: blur(28px) saturate(170%)" in styles


def test_repeated_information_cards_use_compact_progressive_disclosure() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert "點開文件名稱查看整理重點與官方來源" in html
    assert '<small>${escapeHtml(truncate(rule.summary, 60))}</small>' not in script
    assert '<small>${escapeHtml(truncate(item.summary, 58))}</small>' not in script
    assert '<details class="deadline-card">' in script
    assert '<details class="search-result-card">' in script
    assert '<details class="favorite-card">' in script
    assert "Compact disclosure lists" in styles
    assert '<small>${escapeHtml(truncate(meta, 72))}</small>' in script
    assert "-webkit-line-clamp: 2" in styles


def test_wide_desktop_workspace_fills_the_canvas_without_centered_cut_edges() -> None:
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert "Wide desktop canvas" in styles
    assert "@media (min-width: 961px)" in styles
    assert "--workspace-pad-x: clamp(30px, 2.8vw, 56px)" in styles
    assert ".workspace {\n    --workspace-pad-x" in styles
    assert "max-width: none" in styles
    assert "margin-inline: calc(0px - var(--workspace-pad-x))" in styles
    assert ".page-section {\n    border: 0;\n    background: transparent;" in styles
    assert "Partner filters: layered Liquid Glass" in styles
    assert "backdrop-filter: blur(30px) saturate(170%);" in styles
    assert "#clear-partner-filters {" in styles


def test_school_community_has_posts_chat_invitation_only_messages_and_safety() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "學生社群" in html
    assert "動態貼文" in script
    assert "公開聊天室" in script
    assert "私訊邀請" in script
    assert "對方接受邀請後" in script
    assert "/community/posts" in script
    assert "/community/chat" in script
    assert "/community/conversations" in script
    assert "/community/blocks" in script
    assert "/community/reports" in script


def test_account_and_global_community_web_flows_are_present() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'id="auth-dialog"' in html
    assert 'id="register-form"' in html
    assert 'data-oauth-provider="google"' in html
    assert 'data-oauth-provider="facebook"' in html
    assert 'id="profile-form"' in html
    assert 'id="community-hub"' in html
    assert 'id="global-community-form"' in html
    assert "/auth/register" in script
    assert "/auth/login" in script
    assert "/auth/community-identity" in script
    assert "loadGlobalCommunity" in script
    assert "renderApplicationJourney" in script


def test_application_calendar_combines_official_and_personal_planning() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'id="calendar"' in html
    assert 'id="application-calendar-grid"' in html
    assert 'id="calendar-event-form"' in html
    assert "Google 日曆" in script
    assert "downloadCalendarEvents" in script
    assert "BEGIN:VCALENDAR" in script
    assert "officialCalendarEvents" in script
    assert "exchange-guide-calendar-events" in script
    assert 'id="calendar-sync-panel"' in html
    assert 'data-calendar-provider="google"' in html
    assert 'fetchJson("/calendar-sync/events"' in script
    assert "subscription_url" in script
    assert ".application-calendar-layout" in styles
    assert "min-width: 44px" in styles


def test_student_plan_connects_matching_budget_scholarships_and_documents() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'id="personal-plan-snapshot"' in html
    assert 'id="recommended-match-list"' in html
    assert 'id="budget-form"' in html
    assert 'id="document-workspace-list"' in html
    assert 'id="scholarship-match-summary"' in html
    assert "function partnerMatch" in script
    assert "function nextPlanAction" in script
    assert "function renderBudgetPlanner" in script
    assert "function scholarshipMatch" in script
    assert "function renderDocumentWorkspace" in script
    assert ".personal-plan-snapshot" in styles
    assert ".recommended-match-card" in styles
    assert ".budget-layout" in styles


def test_application_center_turns_each_document_into_an_independent_form_page() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'href="#application-center"' in html
    assert 'data-university-page="application-center"' in html
    assert 'data-university-page="application-form"' in html
    assert 'id="application-context-form"' in html
    assert 'id="application-profile-form"' in html
    assert 'id="application-document-form"' in html
    assert 'id="download-application-packet"' in html
    assert "#application-form=" in script
    assert "loadApplicationTemplates" in script
    assert "generateApplicationPdf" in script
    assert "APPLICATION_DOCUMENT_STATUSES" in script
    assert "applicationFieldHasValue" in script
    assert 'data-application-status-template' in script
    assert 'fetch("/application-center/pdf"' in script
    assert ".application-center-layout" in styles
    assert ".application-form-layout" in styles
    assert ".application-status-control" in styles
    assert "min-height: 44px" in styles


def test_application_forms_remember_shared_fields_without_persisting_sensitive_ids() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'id="application-remember-profile"' in html
    assert 'id="clear-application-profile-memory"' in html
    assert 'id="application-autofill-status"' in html
    assert "function rememberApplicationField" in script
    assert "function persistApplicationProfileMemory" in script
    assert "function clearApplicationProfileMemory" in script
    assert "APPLICATION_PERSISTENT_PROFILE_KEYS" in script
    assert '"id_number",\n    "birth_date",\n    "passport_number",\n    "guardian_id_number",' in script
    assert "delete state.applicationAnswers[template.id][field.id]" in script
    assert ".application-memory-controls" in styles
    assert ".application-autofill-status" in styles


def test_application_pages_keep_primary_actions_visible_and_move_explanations_into_disclosures() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert '<h2 id="application-center-title">申請文件</h2>' in html
    assert "只填一次，自動套入文件" not in html
    assert "線上完成資料、產生可列印 PDF" not in html
    assert "系統會只列出需要的文件" not in html
    assert "在任何文件填過的共用欄位" not in html
    assert '<details class="application-compact-help">' in html
    assert "填寫說明" in html
    assert "列印提醒" in html
    assert "function applicationFieldInput(template, field, inputId" in script
    assert 'class="application-field-help"' in script
    assert '<div><dt>版本</dt>' not in script
    assert 'badge.textContent = template.official_layout ? "官方格式" : "申請整理"' in script
    assert ".application-field-help > summary" in styles
    assert ".application-compact-help > summary" in styles


def test_registration_requires_privacy_first_student_card_verification() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'id="student-card-front"' in html
    assert 'id="student-card-back"' in html
    assert 'name="student_verification_token"' in html
    assert "完成後立即刪除原圖" in html
    assert 'fetchJson("/auth/student-verification"' in script
    assert "clearStudentCardFiles" in script
    assert ".student-card-upload-grid" in styles


def test_global_home_board_routing_and_following_are_present() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'href="#home"' in html
    assert 'href="#following"' in html
    assert 'href="#board=長庚大學"' in html
    assert 'data-follow-board="長庚大學"' in html
    assert '<span>發布看板</span>' in html
    assert '<option value="公共留學板">公共留學板</option>' in html
    assert '<option value="長庚大學">長庚大學板</option>' in html
    assert "globalCommunityFeed" in script
    assert "followed_boards" in script
    assert "toggleBoardFollow" in script
    assert "applyAppRoute" in script
