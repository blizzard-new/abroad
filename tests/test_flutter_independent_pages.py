from pathlib import Path


FLUTTER_ROOT = Path(__file__).resolve().parents[1] / "mobile_flutter"


def test_flutter_feature_hub_routes_to_independent_pages() -> None:
    home = (FLUTTER_ROOT / "lib/screens/home_screen.dart").read_text(encoding="utf-8")
    features = (FLUTTER_ROOT / "lib/screens/feature_screens.dart").read_text(
        encoding="utf-8"
    )

    for screen in (
        "OfficialDeadlinesScreen",
        "ScholarshipsScreen",
        "EligibilityScreen",
        "DocumentsScreen",
        "FavoritesScreen",
    ):
        assert f"const {screen}()" in home
        assert f"class {screen}" in features

    assert "Navigator.of(context).push" in home
    assert "FeaturePageScaffold" in features
    assert "每個入口都會開啟獨立頁面" not in home
    assert "先選功能" not in home
    assert "一個功能，一個頁面" not in home


def test_calendar_and_school_list_no_longer_embed_other_feature_pages() -> None:
    deadlines = (FLUTTER_ROOT / "lib/screens/deadlines_screen.dart").read_text(
        encoding="utf-8"
    )
    schools = (FLUTTER_ROOT / "lib/screens/schools_screen.dart").read_text(
        encoding="utf-8"
    )

    assert "_OfficialDeadlineArchive" not in deadlines
    assert "favoritesOnly" not in schools
