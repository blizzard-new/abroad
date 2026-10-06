import hashlib
from datetime import timedelta

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import (
    AccountSessionRecord,
    CommunityAnswer,
    CommunityIdentityMode,
    CommunityQuestion,
    CommunityReport,
    CommunityReportStatus,
    CommunityTopic,
    ExperienceSubmission,
    ModerationStatus,
    PartnerUniversity,
    PublicChatMessage,
    UserAccount,
    utc_now,
)
from exchange_info.storage import (
    append_community_answer,
    append_community_question,
    append_community_report,
    append_experience_submission,
    append_public_chat_message,
    ensure_data_dirs,
    load_account_sessions,
    load_anonymous_identities,
    load_community_answers,
    load_community_post_comments,
    load_community_posts,
    load_community_publish_events,
    load_community_questions,
    load_community_reports,
    load_experience_submissions,
    load_private_conversations,
    load_public_chat_messages,
    load_user_accounts,
    save_account_sessions,
    save_user_accounts,
)


def _account(
    data_dir,
    client: TestClient,
    name: str,
    *,
    email: str | None = None,
    email_verified: bool = True,
    verified_university: str | None = None,
    verified_department: str | None = None,
    home_university: str | None = None,
) -> tuple[UserAccount, dict[str, str], dict]:
    account = UserAccount(
        email=email,
        display_name=name,
        email_verified=email_verified,
        **({"home_university": home_university} if home_university else {}),
        student_status_verified=bool(verified_university),
        verified_university=verified_university,
        verified_department=verified_department,
    )
    access_token = f"account-token-{account.id}"
    save_user_accounts([*load_user_accounts(data_dir), account], data_dir)
    save_account_sessions(
        [
            *load_account_sessions(data_dir),
            AccountSessionRecord(
                account_id=account.id,
                token_hash=hashlib.sha256(access_token.encode("utf-8")).hexdigest(),
                expires_at=utc_now() + timedelta(days=1),
            ),
        ],
        data_dir,
    )
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    identity = client.post("/auth/community-identity", headers=auth_headers).json()
    return account, {
        **auth_headers,
        "X-Anonymous-ID": identity["id"],
        "X-Anonymous-Token": identity["access_token"],
    }, identity


def _post_payload(board: str, **updates) -> dict:
    payload = {
        "school_name": board,
        "post_type": "discussion",
        "topic": "application",
        "title": "交換申請流程討論",
        "body": "想和同學一起整理申請步驟與校內繳交文件。",
    }
    payload.update(updates)
    return payload


def test_unlinked_anonymous_identity_cannot_bypass_login(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    identity = client.post(
        "/community/identities", json={"display_name": "舊匿名身分"}
    ).json()

    response = client.post(
        "/community/posts",
        headers={
            "X-Anonymous-ID": identity["id"],
            "X-Anonymous-Token": identity["access_token"],
        },
        json=_post_payload("公共留學板"),
    )

    assert response.status_code == 401


def test_guest_can_read_every_board_but_unverified_email_cannot_publish(
    tmp_path,
) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    guest_boards = client.get("/community/boards")
    assert guest_boards.status_code == 200
    assert {row["id"] for row in guest_boards.json()} == {
        "public-study-abroad",
        "language-school",
        "university:cgu",
        "university:ntpu",
    }
    assert all(row["can_read"] is True for row in guest_boards.json())
    assert all(row["can_post"] is False for row in guest_boards.json())
    assert client.get("/community/posts").status_code == 200

    _, headers, _ = _account(
        tmp_path,
        client,
        "尚未驗證 Email",
        email="pending@example.com",
        email_verified=False,
    )
    denied = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload("公共留學板"),
    )
    assert denied.status_code == 403
    assert "Email" in denied.json()["detail"]


def test_post_rejects_unknown_or_conflicting_board_identifiers(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _, headers, _ = _account(tmp_path, client, "一般會員")

    unknown = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload("公共留學板", board_id="partner:anywhere"),
    )
    assert unknown.status_code == 422
    assert "不存在" in unknown.json()["detail"]

    conflicting = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload("長庚大學", board_id="public-study-abroad"),
    )
    assert conflicting.status_code == 422
    assert "不一致" in conflicting.json()["detail"]


def test_account_without_a_school_posts_anonymously_on_public_and_school_boards(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _, headers, _ = _account(tmp_path, client, "一般會員", home_university="尚未選擇")

    public_post = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload("公共留學板"),
    )
    assert public_post.status_code == 201
    assert public_post.json()["display_name"] == "匿名學生"
    assert public_post.json()["identity_mode"] == "anonymous"

    # School boards are open to any account with a verified e-mail; without a picked school the byline stays anonymous.
    school_post = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload("長庚大學"),
    )
    assert school_post.status_code == 201
    assert school_post.json()["display_name"] == "匿名學生"
    school_byline = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload("長庚大學", identity_mode="verified_school"),
    )
    assert school_byline.status_code == 403

    options = client.get(
        "/auth/community-identity-options", headers=headers
    ).json()
    school_option = next(
        row for row in options["options"] if row["mode"] == "verified_school"
    )
    assert options["default_mode"] == "anonymous"
    assert school_option["enabled"] is False

    forged_school_name = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload("公共留學板", identity_mode="verified_school"),
    )
    assert forged_school_name.status_code == 403


def test_language_school_board_is_a_public_topic_board(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _, headers, _ = _account(tmp_path, client, "一般會員")

    created = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload(
            "語言學校板",
            title="語言學校課程怎麼選",
            body="想了解短期課程、住宿安排與學生簽證的實際準備方式。",
        ),
    )
    assert created.status_code == 201
    assert created.json()["school_name"] == "語言學校板"
    assert created.json()["display_name"] == "匿名學生"

    guest_feed = client.get("/community/posts", params={"school": "語言學校板"})
    assert guest_feed.status_code == 200
    assert [row["post"]["id"] for row in guest_feed.json()] == [created.json()["id"]]

    public_feed = client.get("/community/posts", params={"school": "公共留學板"})
    assert public_feed.status_code == 200
    assert public_feed.json() == []

    comment = client.post(
        f"/community/posts/{created.json()['id']}/comments",
        headers=headers,
        json={"body": "我也想知道不同國家的課程時數差異。"},
    )
    assert comment.status_code == 201

    unauthenticated_post = client.post(
        "/community/posts",
        json=_post_payload("語言學校板"),
    )
    assert unauthenticated_post.status_code == 401


def test_verified_student_can_use_matching_school_identity_only(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _, headers, _ = _account(
        tmp_path,
        client,
        "王小明",
        verified_university="長庚大學",
    )

    cgu_post = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload("長庚大學", identity_mode="verified_school"),
    )
    assert cgu_post.status_code == 201
    assert cgu_post.json()["display_name"] == "長庚大學學生"

    # Another school's board is open too, but only under an anonymous or real-name byline.
    other_school_post = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload("國立臺北大學"),
    )
    assert other_school_post.status_code == 201
    assert other_school_post.json()["display_name"] == "匿名學生"

    department_post = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload("公共留學板", identity_mode="verified_department"),
    )
    assert department_post.status_code == 403

    options = client.get(
        "/auth/community-identity-options", headers=headers
    ).json()["options"]
    assert next(row for row in options if row["mode"] == "verified_school")[
        "enabled"
    ] is True
    assert next(row for row in options if row["mode"] == "verified_department")[
        "enabled"
    ] is False


def test_ntpu_student_can_use_only_ntpu_board_for_posts_and_comments(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _, ntpu_headers, _ = _account(
        tmp_path,
        client,
        "臺北大學學生",
        verified_university="國立臺北大學",
    )
    _, cgu_headers, _ = _account(
        tmp_path,
        client,
        "長庚大學學生",
        verified_university="長庚大學",
    )

    access = {
        row["id"]: row
        for row in client.get("/community/boards", headers=ntpu_headers).json()
    }
    assert access["public-study-abroad"]["can_post"] is True
    assert access["language-school"]["can_post"] is True
    assert access["university:ntpu"]["can_post"] is True
    assert access["university:ntpu"]["can_comment"] is True
    assert access["university:cgu"]["can_post"] is False
    assert access["university:cgu"]["can_comment"] is False

    ntpu_post = client.post(
        "/community/posts",
        headers=ntpu_headers,
        json=_post_payload(
            "國立臺北大學",
            board_id="university:ntpu",
            title="臺北大學交換申請討論",
        ),
    )
    assert ntpu_post.status_code == 201

    matching_comment = client.post(
        f"/community/posts/{ntpu_post.json()['id']}/comments",
        headers=ntpu_headers,
        json={"body": "這是同校學生補充的申請經驗。"},
    )
    assert matching_comment.status_code == 201

    cross_school_comment = client.post(
        f"/community/posts/{ntpu_post.json()['id']}/comments",
        headers=cgu_headers,
        json={"body": "跨校帳號不應能在臺北大學板留言。"},
    )
    assert cross_school_comment.status_code == 403

    guest_comment = client.post(
        f"/community/posts/{ntpu_post.json()['id']}/comments",
        json={"body": "未登入使用者也不應能留言。"},
    )
    assert guest_comment.status_code == 401


def test_verified_department_identity_is_derived_by_server(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _, headers, _ = _account(
        tmp_path,
        client,
        "陳同學",
        verified_university="長庚大學",
        verified_department="資訊工程學系",
    )

    response = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload("長庚大學", identity_mode="verified_department"),
    )

    assert response.status_code == 201
    assert response.json()["display_name"] == "長庚大學 資訊工程學系"
    assert response.json()["identity_mode"] == "verified_department"


def test_identity_is_selected_per_submission_and_public_name_is_server_derived(
    tmp_path,
) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _, headers, identity = _account(
        tmp_path,
        client,
        "陳小華",
        verified_university="長庚大學",
        verified_department="資訊工程學系",
    )

    options = client.get(
        "/auth/community-identity-options",
        headers=headers,
    ).json()
    assert options["default_mode"] == "anonymous"
    assert [row["label"] for row in options["options"]] == [
        "匿名學生",
        "陳小華",
        "長庚大學學生",
        "長庚大學 資訊工程學系",
    ]

    real_name_post = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload(
            "公共留學板",
            identity_mode="real_name",
            display_name="偽造公開名稱",
            verified_department="偽造學系",
        ),
    )
    assert real_name_post.status_code == 201
    assert real_name_post.json()["display_name"] == "陳小華"
    assert real_name_post.json()["identity_mode"] == "real_name"

    anonymous_comment = client.post(
        f"/community/posts/{real_name_post.json()['id']}/comments",
        headers=headers,
        json={
            "body": "這一則留言改回匿名，不沿用上一則的本名。",
            "display_name": "另一個偽造名稱",
        },
    )
    assert anonymous_comment.status_code == 201
    assert anonymous_comment.json()["display_name"] == "匿名學生"
    assert anonymous_comment.json()["identity_mode"] == "anonymous"

    department_comment = client.post(
        f"/community/posts/{real_name_post.json()['id']}/comments",
        headers=headers,
        json={
            "body": "這一則留言另外選擇顯示已驗證校系。",
            "identity_mode": "verified_department",
            "display_name": "不能覆寫的名稱",
            "verified_department": "不能覆寫的學系",
        },
    )
    assert department_comment.status_code == 201
    assert department_comment.json()["display_name"] == "長庚大學 資訊工程學系"
    assert department_comment.json()["identity_mode"] == "verified_department"

    stored_posts = load_community_posts(tmp_path)
    stored_comments = load_community_post_comments(tmp_path)
    assert stored_posts[0].author_id == identity["id"]
    assert all(row.author_id == identity["id"] for row in stored_comments)


def test_public_post_threads_hide_internal_author_ids_but_keep_owner_controls(
    tmp_path,
) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _, owner_headers, owner_identity = _account(tmp_path, client, "貼文作者")
    _, other_headers, _ = _account(tmp_path, client, "其他讀者")

    created = client.post(
        "/community/posts",
        headers=owner_headers,
        json=_post_payload("公共留學板"),
    )
    assert created.status_code == 201
    assert created.json()["author_id"] == ""
    assert created.json()["viewer_can_delete"] is True

    comment = client.post(
        f"/community/posts/{created.json()['id']}/comments",
        headers=owner_headers,
        json={"body": "作者自己補充一則匿名留言。"},
    )
    assert comment.status_code == 201
    assert comment.json()["author_id"] == ""
    assert comment.json()["viewer_can_delete"] is True

    guest_thread = client.get(
        "/community/posts",
        params={"school": "公共留學板"},
    ).json()[0]
    assert guest_thread["post"]["author_id"] == ""
    assert guest_thread["post"]["viewer_can_delete"] is False
    assert guest_thread["comments"][0]["author_id"] == ""
    assert guest_thread["comments"][0]["viewer_can_delete"] is False

    owner_thread = client.get(
        "/community/posts",
        params={"school": "公共留學板"},
        headers=owner_headers,
    ).json()[0]
    assert owner_thread["post"]["author_id"] == ""
    assert owner_thread["post"]["viewer_can_delete"] is True
    assert owner_thread["comments"][0]["viewer_can_delete"] is True

    other_thread = client.get(
        "/community/posts",
        params={"school": "公共留學板"},
        headers=other_headers,
    ).json()[0]
    assert other_thread["post"]["viewer_can_delete"] is False
    assert other_thread["comments"][0]["viewer_can_delete"] is False
    assert load_community_posts(tmp_path)[0].author_id == owner_identity["id"]


def test_high_risk_content_waits_for_review_and_sensitive_ids_are_blocked(
    tmp_path,
) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _, headers, _ = _account(tmp_path, client, "一般會員")

    pending = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload(
            "公共留學板",
            title="付費代辦保證錄取",
            body="這是風險式審核測試內容，不應直接出現在公開頁面。",
        ),
    )
    assert pending.status_code == 201
    assert pending.json()["status"] == "pending"
    assert client.get(
        "/community/posts", params={"school": "公共留學板"}
    ).json() == []

    sensitive = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload(
            "公共留學板",
            body="我的護照號碼：A12345678，請幫我確認資料。",
        ),
    )
    assert sensitive.status_code == 422

    obfuscated = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload(
            "公共留學板",
            title="付 費 代 辦保證錄取",
            body="即使刻意插入空白，這則廣告仍應進入待審。",
        ),
    )
    assert obfuscated.status_code == 201
    assert obfuscated.json()["status"] == "pending"

    full_width_sensitive = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload(
            "公共留學板",
            body="我的護照號碼：Ａ１２３４５６７８，請幫忙核對。",
        ),
    )
    assert full_width_sensitive.status_code == 422


def test_new_account_has_a_ten_minute_publish_limit(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _, headers, _ = _account(tmp_path, client, "新會員")

    for index in range(5):
        response = client.post(
            "/community/posts",
            headers=headers,
            json=_post_payload(
                "公共留學板",
                title=f"交換流程討論第 {index + 1} 篇",
            ),
        )
        assert response.status_code == 201

    assert len(load_community_publish_events(tmp_path)) == 5
    client = TestClient(create_app(tmp_path))

    limited = client.post(
        "/community/posts",
        headers=headers,
        json=_post_payload("公共留學板", title="第六篇應被頻率限制"),
    )
    assert limited.status_code == 429
    assert limited.headers["Retry-After"] == "600"


def test_reports_and_blocks_validate_targets_and_report_review_is_audited(
    tmp_path, monkeypatch
) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", "admin@example.com")
    client = TestClient(create_app(tmp_path))
    _, admin_headers, _ = _account(
        tmp_path,
        client,
        "內容管理員",
        email="admin@example.com",
    )
    _, author_headers, _ = _account(tmp_path, client, "原文作者")
    _, reporter_headers, reporter_identity = _account(tmp_path, client, "檢舉者")
    _, stranger_headers, stranger_identity = _account(tmp_path, client, "陌生使用者")

    post = client.post(
        "/community/posts",
        headers=author_headers,
        json=_post_payload("公共留學板"),
    ).json()

    invalid_report = client.post(
        "/community/reports",
        headers=reporter_headers,
        json={
            "resource_type": "post",
            "resource_id": "missing-resource",
            "reason": "找不到的內容不能建立檢舉。",
        },
    )
    assert invalid_report.status_code == 404

    own_report = client.post(
        "/community/reports",
        headers=author_headers,
        json={
            "resource_type": "post",
            "resource_id": post["id"],
            "reason": "不能用自己的帳號檢舉自己的文章。",
        },
    )
    assert own_report.status_code == 422

    reported = client.post(
        "/community/reports",
        headers=reporter_headers,
        json={
            "resource_type": "post",
            "resource_id": post["id"],
            "reason": "這項申請資訊可能已經過期，請人工核對。",
        },
    )
    assert reported.status_code == 202
    assert reported.json()["status"] == "pending"

    duplicate = client.post(
        "/community/reports",
        headers=reporter_headers,
        json={
            "resource_type": "post",
            "resource_id": post["id"],
            "reason": "重複送出不應再新增第二筆檢舉。",
        },
    )
    assert duplicate.status_code == 202
    assert duplicate.json()["id"] == reported.json()["id"]
    assert len(load_community_reports(tmp_path)) == 1

    assert client.get(
        "/admin/community/reports",
        headers=reporter_headers,
    ).status_code == 403
    pending_reports = client.get(
        "/admin/community/reports",
        headers=admin_headers,
    )
    assert pending_reports.status_code == 200
    assert [row["id"] for row in pending_reports.json()] == [reported.json()["id"]]

    resolved = client.patch(
        f"/admin/community/reports/{reported.json()['id']}",
        headers=admin_headers,
        json={"status": "resolved", "note": "已核對原文並完成必要處置。"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["resource_type"] == "report"
    assert resolved.json()["previous_status"] == "pending"
    assert resolved.json()["new_status"] == "resolved"
    assert client.patch(
        f"/admin/community/reports/{reported.json()['id']}",
        headers=admin_headers,
        json={"status": "dismissed", "note": "不能重複結案。"},
    ).status_code == 409
    reviewed = client.get(
        "/admin/community/reports",
        params={"status": "resolved"},
        headers=admin_headers,
    ).json()[0]
    assert reviewed["reviewed_by"]
    assert reviewed["reviewed_at"]
    assert reviewed["resolution_note"] == "已核對原文並完成必要處置。"

    assert client.post(
        "/community/blocks",
        headers=reporter_headers,
        json={"target_id": reporter_identity["id"]},
    ).status_code == 422
    assert client.post(
        "/community/blocks",
        headers=reporter_headers,
        json={"target_id": "missing-user"},
    ).status_code == 404
    assert client.post(
        "/community/blocks",
        headers=reporter_headers,
        json={"target_id": stranger_identity["id"]},
    ).status_code == 403


def test_admin_can_review_pending_content_and_temporarily_suspend_account(
    tmp_path, monkeypatch
) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", "admin@example.com")
    client = TestClient(create_app(tmp_path))
    _, admin_headers, _ = _account(
        tmp_path,
        client,
        "內容管理員",
        email="admin@example.com",
        verified_university="長庚大學",
    )
    _, student_headers, student_identity = _account(
        tmp_path,
        client,
        "待審學生",
        email="student@example.com",
    )
    pending = client.post(
        "/community/posts",
        headers=student_headers,
        json=_post_payload(
            "公共留學板",
            title="付費代辦保證錄取",
            body="這則內容應先進入管理者待審清單。",
        ),
    ).json()

    queue = client.get(
        "/admin/community/moderation-queue", headers=admin_headers
    )
    assert queue.status_code == 200
    assert [row["id"] for row in queue.json()["post"]] == [pending["id"]]

    approved = client.patch(
        f"/admin/community/post/{pending['id']}",
        headers=admin_headers,
        json={"status": "approved", "note": "已人工確認並移除風險疑慮。"},
    )
    assert approved.status_code == 200
    assert approved.json()["previous_status"] == "pending"
    assert client.get(
        "/community/posts", params={"school": "公共留學板"}
    ).json()[0]["post"]["id"] == pending["id"]
    assert client.patch(
        f"/admin/community/post/{pending['id']}",
        headers=admin_headers,
        json={"status": "approved", "note": "不能重複核准同一狀態。"},
    ).status_code == 409

    suspended = client.post(
        f"/admin/community/identities/{student_identity['id']}/suspend",
        headers=admin_headers,
        json={
            "suspended_until": (utc_now() + timedelta(days=7)).isoformat(),
            "reason": "多次發布違反社群規範的內容。",
        },
    )
    assert suspended.status_code == 200
    assert suspended.json()["new_status"] == "suspended"
    assert client.post(
        "/community/posts",
        headers=student_headers,
        json=_post_payload("公共留學板", title="停權後不能發文"),
    ).status_code == 403
    assert len(
        client.get(
            "/admin/community/moderation-audits", headers=admin_headers
        ).json()
    ) == 2


def test_author_can_delete_own_post_but_not_another_users_post(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _, first_headers, _ = _account(tmp_path, client, "第一位學生")
    _, second_headers, _ = _account(tmp_path, client, "第二位學生")
    post = client.post(
        "/community/posts",
        headers=first_headers,
        json=_post_payload("公共留學板"),
    ).json()

    assert client.delete(
        f"/community/posts/{post['id']}", headers=second_headers
    ).status_code == 403
    assert client.delete(
        f"/community/posts/{post['id']}", headers=first_headers
    ).status_code == 204
    assert client.get(
        "/community/posts", params={"school": "公共留學板"}
    ).json() == []


def test_account_deletion_keeps_public_content_but_removes_private_links(
    tmp_path, monkeypatch
) -> None:
    ensure_data_dirs(tmp_path)
    partner = PartnerUniversity(
        program_type="交換學生",
        country="日本",
        school_name="範例大學 Example University",
        source_url="https://example.edu/exchange",
    )
    monkeypatch.setattr(
        "exchange_info.api.fetch_partner_universities", lambda: [partner]
    )
    client = TestClient(create_app(tmp_path))
    first_account, first_headers, first_identity = _account(
        tmp_path,
        client,
        "準備交換的小林",
        verified_university="長庚大學",
    )
    _, second_headers, second_identity = _account(
        tmp_path,
        client,
        "交換回來的小陳",
        verified_university="長庚大學",
    )

    post = client.post(
        "/community/posts",
        headers=first_headers,
        json=_post_payload("公共留學板", identity_mode="real_name"),
    ).json()
    comment = client.post(
        f"/community/posts/{post['id']}/comments",
        headers=first_headers,
        json={"body": "補充一份校內流程說明。", "identity_mode": "real_name"},
    )
    assert comment.status_code == 201
    conversation = client.post(
        "/community/conversations",
        headers=first_headers,
        json={
            "school_name": partner.school_name,
            "recipient_id": second_identity["id"],
            "initial_message": "想詢問你整理資料的方法，可以嗎？",
        },
    )
    assert conversation.status_code == 201

    question = append_community_question(
        CommunityQuestion(
            author_id=first_identity["id"],
            school_name=partner.school_name,
            home_university="長庚大學",
            topic=CommunityTopic.APPLICATION,
            title="申請時程怎麼安排",
            body="想請問交換申請時程與文件準備順序。",
            display_name=first_account.display_name,
            identity_mode=CommunityIdentityMode.REAL_NAME,
            status=ModerationStatus.APPROVED,
        ),
        tmp_path,
    )
    append_community_answer(
        CommunityAnswer(
            author_id=first_identity["id"],
            question_id=question.id,
            body="建議先確認校內截止日，再依序準備各項文件。",
            display_name=first_account.display_name,
            identity_mode=CommunityIdentityMode.REAL_NAME,
            status=ModerationStatus.APPROVED,
        ),
        tmp_path,
    )
    append_public_chat_message(
        PublicChatMessage(
            school_name=partner.school_name,
            author_id=first_identity["id"],
            display_name=first_account.display_name,
            identity_mode=CommunityIdentityMode.REAL_NAME,
            body="有人也在準備這間學校嗎？",
        ),
        tmp_path,
    )
    append_experience_submission(
        ExperienceSubmission(
            author_id=first_identity["id"],
            school_name=partner.school_name,
            home_university="長庚大學",
            title="交換申請經驗整理",
            summary="這是一份交換申請經驗整理，包含文件準備與時程安排。",
            exchange_year="2026",
            source_url="https://example.com/personal-profile",
            display_name=first_account.display_name,
            identity_mode=CommunityIdentityMode.REAL_NAME,
        ),
        tmp_path,
    )
    retained_report = append_community_report(
        CommunityReport(
            reporter_id=first_identity["id"],
            resource_type="post",
            resource_id="reported-post-1",
            reason="這是尚待管理員處理的安全事件。",
        ),
        tmp_path,
    )
    append_community_report(
        CommunityReport(
            reporter_id=first_identity["id"],
            resource_type="post",
            resource_id="reported-post-2",
            reason="這筆案件已經完成處理。",
            status=CommunityReportStatus.RESOLVED,
            reviewed_by="content-admin",
            reviewed_at=utc_now(),
            resolution_note="已完成處理。",
        ),
        tmp_path,
    )
    reviewed_report = append_community_report(
        CommunityReport(
            reporter_id=second_identity["id"],
            resource_type="post",
            resource_id="reported-post-3",
            reason="由即將刪除帳號的管理員處理。",
            status=CommunityReportStatus.RESOLVED,
            reviewed_by=first_account.id,
            reviewed_at=utc_now(),
            resolution_note="已完成處理。",
        ),
        tmp_path,
    )

    deleted = client.delete("/auth/me", headers=first_headers)
    assert deleted.status_code == 204

    thread = client.get(
        "/community/posts", params={"school": "公共留學板"}
    ).json()[0]
    assert thread["post"]["display_name"] == "已刪除帳號"
    assert thread["post"]["identity_mode"] == "anonymous"
    assert thread["post"]["author_id"] == ""
    assert thread["comments"][0]["display_name"] == "已刪除帳號"
    assert thread["comments"][0]["author_id"] == ""
    assert load_community_posts(tmp_path)[0].author_id == ""
    assert load_community_post_comments(tmp_path)[0].author_id == ""
    assert load_community_questions(tmp_path)[0].author_id is None
    assert load_community_questions(tmp_path)[0].display_name == "已刪除帳號"
    assert load_community_answers(tmp_path)[0].author_id is None
    assert load_public_chat_messages(tmp_path)[0].author_id == ""
    anonymized_experience = load_experience_submissions(tmp_path)[0]
    assert anonymized_experience.author_id is None
    assert anonymized_experience.display_name == "已刪除帳號"
    assert anonymized_experience.source_url is None
    reports = load_community_reports(tmp_path)
    pending = next(row for row in reports if row.id == retained_report.id)
    assert pending.reporter_id == ""
    assert pending.status == CommunityReportStatus.PENDING
    assert pending.retained_until is not None
    assert pending.retained_until > utc_now() + timedelta(days=89)
    assert all(row.resource_id != "reported-post-2" for row in reports)
    reviewed = next(row for row in reports if row.id == reviewed_report.id)
    assert reviewed.reviewed_by is None
    assert all(row.id != first_account.id for row in load_user_accounts(tmp_path))
    assert all(
        row.id != first_identity["id"] for row in load_anonymous_identities(tmp_path)
    )
    assert all(
        row.account_id != first_account.id
        for row in load_community_publish_events(tmp_path)
    )
    assert load_private_conversations(tmp_path) == []
    assert client.get("/community/conversations", headers=second_headers).json() == []


def test_deidentified_safety_report_expires_and_is_removed_after_review(
    tmp_path, monkeypatch
) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", "admin@example.com")
    client = TestClient(create_app(tmp_path))
    _, admin_headers, _ = _account(
        tmp_path,
        client,
        "內容管理員",
        email="admin@example.com",
    )
    expired = append_community_report(
        CommunityReport(
            reporter_id="",
            resource_type="post",
            resource_id="expired-report-target",
            reason="已超過必要保留期限的去識別檢舉。",
            retained_until=utc_now() - timedelta(seconds=1),
        ),
        tmp_path,
    )
    active = append_community_report(
        CommunityReport(
            reporter_id="",
            resource_type="post",
            resource_id="active-report-target",
            reason="仍在必要保留期限內的去識別檢舉。",
            retained_until=utc_now() + timedelta(days=1),
        ),
        tmp_path,
    )

    pending = client.get("/admin/community/reports", headers=admin_headers)

    assert pending.status_code == 200
    assert [row["id"] for row in pending.json()] == [active.id]
    assert all(row.id != expired.id for row in load_community_reports(tmp_path))

    reviewed = client.patch(
        f"/admin/community/reports/{active.id}",
        headers=admin_headers,
        json={"status": "resolved", "note": "已完成必要安全處置。"},
    )

    assert reviewed.status_code == 200
    assert all(row.id != active.id for row in load_community_reports(tmp_path))
