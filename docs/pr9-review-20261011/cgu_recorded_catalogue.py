"""Review-only offline fixture from the independently recorded 77-row baseline."""
def pytest_sessionstart(session):
    import json
    from pathlib import Path
    from exchange_info import api
    from exchange_info.models import PartnerUniversity
    rows=json.loads(Path('/workspace/globe-evidence-20261011/local-base-export/snapshots/cgu-dashboard.json').read_text())['partner_universities']
    partners=[PartnerUniversity.model_validate(row) for row in rows]
    assert len(partners)==77
    api.fetch_partner_universities=lambda: list(partners)
