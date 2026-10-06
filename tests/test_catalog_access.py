"""Catalog isolation and administrator publishing, with isolated accounts/data."""
import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from exchange_info import api
from exchange_info.models import AccountSessionRecord, DestinationProfile, PartnerUniversity, StudentDashboard, UserAccount, utc_now
from exchange_info.storage import save_account_sessions, save_user_accounts

NTPU = "國立臺北大學"
CGU = "長庚大學"


@pytest.fixture
def catalog(tmp_path, monkeypatch):
    monkeypatch.setenv("EXCHANGE_ACCOUNT_REPOSITORY", "jsonl")
    monkeypatch.setenv("EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS", "platform-admin")
    accounts = [
        UserAccount(id="platform-admin", display_name="臺北大學管理員", email_verified=True,
                    student_status_verified=True, verified_university=NTPU, home_university=NTPU),
        UserAccount(id="ntpu-student", display_name="一般學生", email_verified=True,
                    student_status_verified=True, verified_university=NTPU, home_university=CGU),
        UserAccount(id="cgu-student", display_name="一般學生", email_verified=True,
                    student_status_verified=True, verified_university=CGU, home_university=CGU),
        UserAccount(id="unverified", display_name="臺北大學管理員", email_verified=True,
                    home_university=NTPU),
        UserAccount(id="no-school", display_name="尚未選校", email_verified=True,
                    home_university="尚未選擇"),
    ]
    save_user_accounts(accounts, tmp_path)
    save_account_sessions([AccountSessionRecord(
        account_id=a.id, token_hash=hashlib.sha256(a.id.encode()).hexdigest(),
        expires_at=utc_now() + timedelta(days=1),
    ) for a in accounts], tmp_path)
    partners = {
        CGU: [PartnerUniversity(program_type="交換學生", school_name="長庚限定合作校", country="日本", source_url="https://example.edu/exchange")],
        NTPU: [PartnerUniversity(program_type="交換學生", school_name="北大限定合作校", country="日本", source_url="https://example.edu/exchange")],
    }
    monkeypatch.setattr(api, "fetch_partner_universities", lambda: partners[CGU])
    monkeypatch.setattr(api, "fetch_ntpu_partner_universities", lambda: partners[NTPU])
    monkeypatch.setattr(api, "build_student_dashboard", lambda *a, **k: StudentDashboard(school_name=CGU, partner_universities=partners[CGU]))
    monkeypatch.setattr(api, "build_ntpu_student_dashboard", lambda **k: StudentDashboard(school_name=NTPU, partner_universities=partners[NTPU]))
    monkeypatch.setattr(api, "load_destination_profiles", lambda *a, **k: [
        DestinationProfile(school_name=rows[0].school_name, home_university=home)
        for home, rows in partners.items()
    ])
    return TestClient(api.create_app(tmp_path))


def auth(account):
    return {"Authorization": f"Bearer {account}"}


@pytest.mark.parametrize("path", [
    "/student-dashboard", "/exchange-info", "/coverage", "/sources", "/documents",
    "/deadlines", "/search?q=交換", "/destination-profiles", "/application-center/templates",
    "/application-workflow?school=北大限定合作校", "/ai/structured-sources",
])
def test_guests_can_read_the_catalog_without_an_account(catalog, path):
    response = catalog.get(path)
    assert response.status_code == 200, response.text
    assert "no-store" not in response.headers.get("cache-control", "")


def test_guests_choose_the_school_and_every_school_is_readable(catalog):
    for school, partner in [(CGU, "長庚限定合作校"), (NTPU, "北大限定合作校"), ("CGU", "長庚限定合作校"), ("北大", "北大限定合作校")]:
        response = catalog.get("/student-dashboard", params={"school": school})
        assert response.status_code == 200
        assert response.json()["partner_universities"][0]["school_name"] == partner
    assert catalog.get("/student-dashboard", params={"school": "不存在大學"}).status_code == 404
    assert catalog.get("/student-dashboard", headers={"Authorization": "Bearer expired"}).status_code == 200


def test_account_school_is_only_the_default_and_profile_cannot_escalate(catalog):
    headers = auth("ntpu-student")
    own = catalog.get("/student-dashboard", headers=headers)
    assert own.status_code == 200
    assert own.json()["school_name"] == NTPU
    assert own.json()["partner_universities"][0]["school_name"] == "北大限定合作校"
    assert "no-store" in own.headers["cache-control"]
    other = catalog.get("/student-dashboard", params={"school": CGU}, headers=headers)
    assert other.status_code == 200 and other.json()["school_name"] == CGU
    spoof = catalog.patch("/auth/me", json={"is_platform_admin": True, "catalog_home_university": CGU}, headers=headers)
    assert spoof.status_code == 200
    assert spoof.json()["is_platform_admin"] is False
    assert spoof.json()["catalog_home_university"] == NTPU
    assert spoof.json()["school_basis"] == "student_verified"


def test_unverified_account_opens_on_its_declared_school_and_may_change_it(catalog):
    headers = auth("unverified")
    profile = catalog.get("/auth/me", headers=headers).json()
    assert (profile["catalog_home_university"], profile["school_basis"]) == (NTPU, "self_declared")
    assert catalog.get("/student-dashboard", headers=headers).json()["school_name"] == NTPU
    changed = catalog.patch("/auth/me", json={"home_university": "長庚"}, headers=headers)
    assert changed.status_code == 200
    assert (changed.json()["home_university"], changed.json()["catalog_home_university"]) == (CGU, CGU)
    assert catalog.get("/student-dashboard", headers=headers).json()["school_name"] == CGU
    assert catalog.patch("/auth/me", json={"home_university": "   "}, headers=headers).status_code == 422
    # A picked school stays for three days (tests/test_school_choice.py covers the lock itself).
    assert catalog.patch("/auth/me", json={"home_university": "國立某某大學"}, headers=headers).status_code == 409
    catalog.app.state.account_repository.patch_account_fields(
        "unverified", {"home_university_changed_at": utc_now() - timedelta(days=4)})
    other = catalog.patch("/auth/me", json={"home_university": "國立某某大學"}, headers=headers)
    assert other.status_code == 200
    assert other.json()["home_university"] == "國立某某大學"
    assert other.json()["catalog_home_university"] is None and other.json()["school_basis"] is None
    assert catalog.get("/student-dashboard", headers=headers).json()["school_name"] == CGU


def test_admin_can_switch_catalogs_and_read_private_responses(catalog):
    for home in [CGU, NTPU]:
        response = catalog.get("/student-dashboard", params={"school": home}, headers=auth("platform-admin"))
        assert response.status_code == 200
        assert response.json()["school_name"] == home
        assert "no-store" in response.headers["cache-control"]
        assert "Cookie" in response.headers["vary"]
    assert catalog.get("/auth/me", headers=auth("platform-admin")).json()["is_platform_admin"] is True


def test_destination_profiles_and_direct_links_follow_the_requested_school(catalog):
    headers = auth("ntpu-student")
    rows = catalog.get("/destination-profiles", headers=headers).json()
    assert [r["school_name"] for r in rows] == ["北大限定合作校"]
    cgu_rows = catalog.get("/destination-profiles", params={"home_school": CGU}, headers=headers).json()
    assert [r["school_name"] for r in cgu_rows] == ["長庚限定合作校"]
    # Without a named home school a direct link is found in whichever catalogue lists it.
    assert catalog.get("/application-workflow", params={"school": "長庚限定合作校"}, headers=headers).status_code == 200
    assert catalog.get("/application-workflow", params={"school": "長庚限定合作校", "home_school": CGU}, headers=headers).status_code == 200
    assert catalog.get("/application-workflow", params={"school": "長庚限定合作校", "home_school": NTPU}, headers=headers).status_code == 404


def test_request_scopes_do_not_leak_between_simultaneous_accounts(catalog):
    def get_own(account):
        result = catalog.get("/student-dashboard", headers=auth(account))
        assert result.status_code == 200
        return result.json()["school_name"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(get_own, ["ntpu-student", "cgu-student"] * 4))
    assert results == [NTPU, CGU] * 4
    guest = catalog.get("/student-dashboard")
    assert guest.status_code == 200 and guest.json()["school_name"] == CGU


def writer_headers(catalog, account):
    response = catalog.post("/auth/community-identity", headers=auth(account))
    assert response.status_code in (200, 201), response.text
    identity = response.json()
    return {**auth(account), "X-Anonymous-ID": identity["id"], "X-Anonymous-Token": identity["access_token"]}


def test_every_verified_email_account_can_post_on_every_board(catalog):
    admin = writer_headers(catalog, "platform-admin")
    student = writer_headers(catalog, "ntpu-student")
    guest_only_declared = writer_headers(catalog, "unverified")
    boards = catalog.get("/community/boards", headers=admin).json()
    assert all(board["can_post"] and board["can_comment"] for board in boards)
    assert all(board["posting_requirement"] == "verified_email" for board in boards)
    for headers in (student, guest_only_declared):
        rows = {row["id"]: row for row in catalog.get("/community/boards", headers=headers).json()}
        assert rows["ntpu"]["can_post"] and rows["cgu"]["can_post"], "school boards need only a verified e-mail"
    payload = {"title": "交換申請測試問題", "body": "這是隔離資料夾內的交換申請權限測試。"}
    for board in ["public-study-abroad", "language-school", "cgu", "ntpu"]:
        response = catalog.post("/community/posts", json={**payload, "board_id": board}, headers=admin)
        assert response.status_code == 201, response.text
        comment = catalog.post(f"/community/posts/{response.json()['id']}/comments", json={"body": "測試回覆"}, headers=admin)
        assert comment.status_code == 201
    for headers in (student, guest_only_declared):
        for board in ["ntpu", "cgu"]:
            posted = catalog.post("/community/posts", json={**payload, "board_id": board}, headers=headers)
            assert posted.status_code == 201, posted.text
            commented = catalog.post(f"/community/posts/{posted.json()['id']}/comments", json={"body": "測試回覆"}, headers=headers)
            assert commented.status_code == 201, commented.text
    stolen = {**student, **auth("platform-admin")}
    assert catalog.post("/community/posts", json={**payload, "board_id": "cgu"}, headers=stolen).status_code == 403
    assert all(not b["can_post"] for b in catalog.get("/community/boards").json())


def test_a_school_byline_still_needs_a_verified_student(catalog):
    no_school = writer_headers(catalog, "no-school")
    declared = writer_headers(catalog, "unverified")
    verified = writer_headers(catalog, "cgu-student")
    payload = {"title": "交換申請測試問題", "body": "這是隔離資料夾內的交換申請權限測試。", "board_id": "cgu"}
    for mode in ("verified_school", "verified_department"):
        denied = catalog.post("/community/posts", json={**payload, "identity_mode": mode}, headers=no_school)
        assert denied.status_code == 403, (mode, denied.text)
    # Nobody checks enrolment any more: the school an account picked is what its byline shows.
    picked = catalog.post("/community/posts", json={**payload, "identity_mode": "verified_school"}, headers=declared)
    assert picked.status_code == 201, picked.text
    assert picked.json()["display_name"] == f"{NTPU}學生"
    assert catalog.post("/community/posts", json={**payload, "identity_mode": "verified_school"}, headers=verified).status_code == 201
