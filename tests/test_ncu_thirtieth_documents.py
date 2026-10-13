"""Full original reading cannot erase excerpt and workbook scope limits."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/thirtieth'


def sources():
    return {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}


def test_two_blank_forms_keep_both_physical_pages_and_version_bytes():
    rows = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    raw = {r['source_id']: r for r in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-thirtieth-original-responses.json.gz').read_bytes()))}
    assert len(raw) == 2
    for row in rows:
        source = sources()[row['source_id']]
        assert source['content_status']['all_pages_read']
        assert not row['current_116_approval']
        if row['source_id'] in raw:
            assert hashlib.sha256(base64.b64decode(raw[row['source_id']]['body'])).hexdigest() == source['sha256'] == row['source_sha256']
            assert row['pages_reviewed'] == [1, 2]
            for render in row['rendered_pages']:
                assert hashlib.sha256((ROOT / render['path']).read_bytes()).hexdigest() == render['sha256']


def test_full_homestay_reading_keeps_original_public_excerpt_boundary():
    ss = sources()
    source = ss['host-kansai-next-08']
    assert source['sha256'] == ss['ncu-129-follow-3e0c81928e']['sha256']
    assert [p['page'] for p in source['pages']] == [1, 5]
    assert source['source_excerpt_only']
    assert source['visual_review']['pdf_pages_reviewed'] == [1, 2, 3, 4, 5]
    assert source['visual_review']['rendered_pages'] == []
    assert len(source['visual_review']['local_render_sha256']) == 5


def test_workbook_images_do_not_turn_selected_course_rows_into_full_reading():
    ss = sources()
    for sid in ['ncu-155-resume14-cuk-courses', 'host-xmu-course-reference-2025-26']:
        assert not ss[sid]['content_status']['all_pages_read']
    partial = ss['ncu-155-resume14-cuk-courses']['selected_visual_review']
    assert len(partial['visual_images_reviewed']) == 3
    assert not partial['full_document_read']
    assert not list(DOCS.rglob('cuk-image*'))
    records = json.loads((DOCS / 'added-host-records.json').read_text())
    assert '不保證相同合法停留期限' in records['ncu-199']['fields']['arrival']['points'][-1]
    assert '未聲稱整份工作簿已讀' in records['ncu-155']['fields']['courses']['points'][-1]
