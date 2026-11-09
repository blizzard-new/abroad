"""Data files are UTF-8. A text read that leaves the encoding to the platform fails on a Taiwanese Windows machine
(cp950), where it turns a school's whole dashboard into a 500."""
import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "exchange_info"


def _unpinned_reads(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "read_text":
            if not node.args and not any(keyword.arg == "encoding" for keyword in node.keywords):
                yield node.lineno


@pytest.mark.parametrize("path", sorted(SRC.glob("*.py")), ids=lambda p: p.name)
def test_every_text_read_names_its_encoding(path: Path) -> None:
    assert list(_unpinned_reads(path)) == [], f"{path.name}: read_text() without encoding=\"utf-8\""


def test_the_ncu_campus_assets_are_not_readable_as_cp950_but_load_as_utf8() -> None:
    # The file really is UTF-8 that cp950 cannot decode, so only an explicit encoding makes the NCU dashboard load.
    from exchange_info import ncu_completion

    raw = ncu_completion.ASSETS.read_bytes()
    with pytest.raises(UnicodeDecodeError):
        raw.decode("cp950")
    ncu_completion._assets_snapshot.cache_clear()
    assert ncu_completion._assets_snapshot((0, 0))
