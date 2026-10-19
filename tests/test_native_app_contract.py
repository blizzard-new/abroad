from pathlib import Path

from exchange_info.university_registry import SUPPORTED_UNIVERSITIES


ROOT = Path(__file__).resolve().parents[1]


def test_legacy_native_apps_are_preserved_as_migration_references() -> None:
    archive_root = ROOT / "archive/legacy_native"
    ios_root = archive_root / "ios/ExchangeGuide/ExchangeGuide"
    android_root = (
        archive_root
        / "android/ExchangeGuideAndroid/app/src/main/java/tw/edu/cgu/exchangeguide"
    )

    assert not (ROOT / "ios/ExchangeGuide").exists()
    assert not (ROOT / "android/ExchangeGuideAndroid").exists()
    assert (archive_root / "README.md").exists()
    assert (ios_root / "App/ExchangeGuideApp.swift").exists()
    assert (ios_root / "Features/Community/ExchangeCommunityView.swift").exists()
    assert (android_root / "MainActivity.kt").exists()
    assert (android_root / "ui/screens/CommunitySection.kt").exists()


def test_flutter_is_the_shared_android_ios_app() -> None:
    flutter_root = ROOT / "mobile_flutter"
    pubspec = (flutter_root / "pubspec.yaml").read_text(encoding="utf-8")
    app = (flutter_root / "lib/app.dart").read_text(encoding="utf-8")
    home = (flutter_root / "lib/screens/home_screen.dart").read_text(
        encoding="utf-8"
    )
    detail = (flutter_root / "lib/screens/school_detail_screen.dart").read_text(
        encoding="utf-8"
    )
    community = (flutter_root / "lib/screens/community_screen.dart").read_text(
        encoding="utf-8"
    )
    global_community = (
        flutter_root / "lib/screens/global_community_screen.dart"
    ).read_text(encoding="utf-8")
    root_shell = (flutter_root / "lib/screens/root_shell.dart").read_text(
        encoding="utf-8"
    )
    visuals = (flutter_root / "lib/core/school_visuals.dart").read_text(
        encoding="utf-8"
    )

    assert (flutter_root / "android").is_dir()
    assert (flutter_root / "ios").is_dir()
    assert "ExchangeGuideApp" in app
    assert "CircularProgressIndicator" in home
    assert "highlight.keyPoints" in detail
    assert "官方圖片來源" in detail
    assert "assets/images/cgu-campus.jpg" in pubspec
    assert "class CguBoardShell" in root_shell
    assert "includeCguFeed: false" in root_shell
    assert "CommunityFeed.following" in global_community
    assert "publicCommunityBoard" in global_community
    assert "發布看板" in global_community
    assert "toggleBoardFollow" in global_community
    assert "_NeutralSchoolPlaceholder" in visuals
    assert "destination-tokyo.jpg" not in visuals

    for marker in (
        "CommunityMode.posts",
        "CommunityMode.chat",
        "CommunityMode.messages",
        "publishPost",
        "publishChat",
        "inviteConversation",
        "acceptConversation",
        "blockIdentity",
        "report",
    ):
        assert marker in community


def test_flutter_aligns_with_18_universities_and_public_api() -> None:
    flutter_root = ROOT / "mobile_flutter"
    models = (flutter_root / "lib/data/models.dart").read_text(encoding="utf-8")
    api = (flutter_root / "lib/data/exchange_api.dart").read_text(
        encoding="utf-8"
    )
    store = (flutter_root / "lib/state/exchange_store.dart").read_text(
        encoding="utf-8"
    )
    root_shell = (flutter_root / "lib/screens/root_shell.dart").read_text(
        encoding="utf-8"
    )

    assert len(SUPPORTED_UNIVERSITIES) == 18
    for university in SUPPORTED_UNIVERSITIES:
        assert f"id: '{university.id}'" in models
        assert f"schoolName: '{university.school_name}'" in models
        assert f"shortName: '{university.short_name}'" in models
        assert f"'{university.official_url}'" in models

    for endpoint in (
        "_uri('universities')",
        "_uri('student-dashboard'",
        "_uri('deadlines'",
        "'application-workflow'",
        "'student-experiences'",
        "'application-center/templates'",
        "_uri('advisor/plan')",
        "_uri('advisor/ask')",
        "_uri('community/posts'",
        "_uri('community/chat'",
    ):
        assert endpoint in api

    assert "selectUniversity" in store
    assert "selectedUniversity" in store
    assert "showUniversityPickerSheet" in root_shell
