"""Check actual local asset references without freezing a historical release tag."""
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


STATIC_DIR = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static"


def assert_versioned_static_assets(html: str, names: tuple[str, ...]) -> dict[str, str]:
    class AssetReferences(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.urls: list[str] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            attribute = "src" if tag == "script" else "href" if tag == "link" else None
            if attribute and (url := dict(attrs).get(attribute)):
                self.urls.append(url)

    parser = AssetReferences()
    parser.feed(html)
    versions = {}
    for name in names:
        matches = [urlsplit(url) for url in parser.urls if urlsplit(url).path == f"/static/{name}"]
        assert len(matches) == 1, f"{name} must have exactly one asset reference"
        assert (STATIC_DIR / name).is_file(), f"{name} must resolve to a local asset"
        values = parse_qs(matches[0].query).get("v", [])
        assert len(values) == 1 and re.fullmatch(r"\d{8}-[a-z0-9-]+", values[0]), (
            f"{name} must have a nonempty versioned cache key"
        )
        versions[name] = values[0]
    return versions
