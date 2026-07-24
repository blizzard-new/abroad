from pathlib import Path


FLUTTER_ROOT = Path(__file__).resolve().parents[1] / "mobile_flutter"


def _read(relative: str) -> str:
    return (FLUTTER_ROOT / relative).read_text(encoding="utf-8")


def test_app_removes_internal_navigation_and_design_explanations() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "lib/screens/home_screen.dart",
            "lib/screens/feature_screens.dart",
            "lib/screens/deadlines_screen.dart",
            "lib/screens/community_screen.dart",
            "lib/screens/school_detail_screen.dart",
        )
    )

    for removed_copy in (
        "長庚大學交換資訊",
        "先選功能",
        "一個功能，一個頁面",
        "長庚大學交換服務",
        "每個入口都會開啟獨立頁面",
        "每筆日期獨立核對",
        "先看資格、金額與限制",
        "送件前快速比對",
        "摘要先讀，需要時再看全文",
        "把截止日變成可執行計畫",
        "官方期限、自訂任務與提醒集中在同一條時間線",
        "20 秒快速了解",
        "文件已先整理",
        "逐步完成",
        "有查到並整理完成的內容會排在前面",
    ):
        assert removed_copy not in combined


def test_feature_pages_do_not_repeat_app_bar_title_in_body() -> None:
    features = _read("lib/screens/feature_screens.dart")
    scaffold = features.split("class FeaturePageScaffold", maxsplit=1)[1].split(
        "class _DeadlineCard", maxsplit=1
    )[0]

    assert "title: Text(title)" in scaffold
    assert "ExchangeSectionHeader" not in scaffold
    assert "required this.eyebrow" not in scaffold
    assert "required this.icon" not in scaffold
