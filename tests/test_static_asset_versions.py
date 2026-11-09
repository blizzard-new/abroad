"""A changed static file must be requested with a new ?v= tag, or returning visitors keep the old one for a year."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("update_static_versions", ROOT / "scripts/update_static_versions.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def test_no_static_file_changed_without_a_new_version_tag() -> None:
    recorded = json.loads(tool.LOCK.read_text(encoding="utf-8"))
    assert tool.stale(recorded, tool.current()) == []


def test_the_version_record_is_current() -> None:
    # Fails after any edit to a versioned file or tag until `python scripts/update_static_versions.py` has been run,
    # which itself refuses a file that kept its old tag.
    assert json.loads(tool.LOCK.read_text(encoding="utf-8")) == tool.current()
