from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from exchange_info.seo import SeoSettings, create_seo_router

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "submit_indexnow.py"
_SPEC = spec_from_file_location("submit_indexnow", _SCRIPT)
assert _SPEC and _SPEC.loader
submit_indexnow = module_from_spec(_SPEC)
_SPEC.loader.exec_module(submit_indexnow)

_EXAMPLE_KEY = "test-indexnow-key"
_PAGE = "https://app.uniway-tw.com/guides/exchange-budget"


@pytest.mark.parametrize("key,indexable,status", [
    (_EXAMPLE_KEY, "true", 200),
    (_EXAMPLE_KEY, "false", 404),
    ("", "true", 404),
    ("invalid/key", "true", 404),
])
def test_verification_file_only_enabled_for_valid_key_on_indexable_site(key, indexable, status):
    settings = SeoSettings.from_environment({"INDEXNOW_KEY": key, "EXCHANGE_SEO_INDEXABLE": indexable})
    app = FastAPI()
    app.include_router(create_seo_router(settings, lambda university: ([], None)))
    with TestClient(app) as client:
        response = client.get(f"/{_EXAMPLE_KEY}.txt")
        assert response.status_code == status
        assert client.head(f"/{_EXAMPLE_KEY}.txt").status_code == status
        assert client.get("/other-key.txt").status_code == 404
        if status == 200:
            assert response.text == _EXAMPLE_KEY
            assert response.headers["content-type"].startswith("text/plain")


def test_push_tool_skips_unset_and_previews_until_explicit_submit(monkeypatch, capsys):
    sent = []
    def post(*args, **kwargs):
        sent.append((args, kwargs))
        return SimpleNamespace(status_code=202)

    monkeypatch.setattr(submit_indexnow.requests, "post", post)
    monkeypatch.setenv("EXCHANGE_PUBLIC_BASE_URL", "https://app.uniway-tw.com")
    monkeypatch.setenv("EXCHANGE_SEO_INDEXABLE", "true")
    monkeypatch.delenv("INDEXNOW_KEY", raising=False)
    assert submit_indexnow.main(["--submit", _PAGE]) == 0
    monkeypatch.setenv("INDEXNOW_KEY", _EXAMPLE_KEY)
    assert submit_indexnow.main([_PAGE]) == 0
    assert sent == []
    with pytest.raises(SystemExit, match="2"):
        submit_indexnow.main(["--submit", "https://other.example/guides/exchange-budget"])
    assert sent == []
    assert submit_indexnow.main(["--submit", _PAGE]) == 0
    [(args, kwargs)] = sent
    assert args == (submit_indexnow.INDEXNOW_ENDPOINT,)
    assert kwargs["json"]["urlList"] == [_PAGE]
    assert kwargs["json"]["keyLocation"] == f"https://app.uniway-tw.com/{_EXAMPLE_KEY}.txt"
    assert kwargs["allow_redirects"] is False
    assert _EXAMPLE_KEY not in capsys.readouterr().out
