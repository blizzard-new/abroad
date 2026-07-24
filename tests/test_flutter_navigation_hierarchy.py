from pathlib import Path


FLUTTER_ROOT = Path(__file__).resolve().parents[1] / "mobile_flutter"


def test_flutter_separates_global_and_cgu_navigation_spaces() -> None:
    shell = (FLUTTER_ROOT / "lib/screens/root_shell.dart").read_text(
        encoding="utf-8"
    )
    global_community = (
        FLUTTER_ROOT / "lib/screens/global_community_screen.dart"
    ).read_text(encoding="utf-8")
    community = (FLUTTER_ROOT / "lib/screens/community_screen.dart").read_text(
        encoding="utf-8"
    )

    assert "class CguBoardShell" in shell
    assert "MaterialPageRoute(builder: (_) => const CguBoardShell())" in shell
    assert "includeCguFeed: false" in shell
    assert "showCguChatShortcut: false" in shell

    global_shell, cgu_shell = shell.split("class CguBoardShell", maxsplit=1)
    assert "const SchoolsScreen()" not in global_shell
    assert "const DeadlinesScreen()" not in global_shell
    assert "HomeScreen(" not in global_shell

    for page in (
        "HomeScreen(",
        "const SchoolsScreen(showPageHeader: false)",
        "const ApplicationDocumentsScreen()",
        "const DeadlinesScreen()",
        "const CommunityScreen(",
    ):
        assert page in cgu_shell
    assert "MaterialPageRoute(builder: (_) => const AccountScreen())" in cgu_shell

    for label in ("留學首頁", "追蹤", "發文", "長庚板"):
        assert f"label: '{label}'" in global_shell
    for label in ("計畫", "找學校", "填文件", "時程", "討論板"):
        assert f"label: '{label}'" in cgu_shell

    assert "class GlobalCommunityScreenState" in global_community
    assert "Future<void> openComposer()" in global_community
    assert "lockedToInitialSchool: true" in cgu_shell
    assert "if (widget.lockedToInitialSchool) return" in community
    assert "長庚學生可在這裡發文" not in community
