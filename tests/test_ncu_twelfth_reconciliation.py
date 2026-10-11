"""Revalidation resolves queue entries without replacing a richer prior packet."""
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).parents[1]
S = ROOT / 'sources/ncu/2026-10-11'
B = ROOT / 'src/exchange_info/official_data/ncu'
D = ROOT / 'docs/data/ncu-completion-20261011/resume/twelfth'


def unpack(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def test_twelfth_same_sha_and_zip_members_do_not_become_new_source_counts():
    manifest = json.loads((D / 'reading-manifest.json').read_text())
    sources = {s['id']: s for s in unpack(B / 'source-evidence.json.gz')}
    captures = {r['capture_id']: r for r in unpack(S / 'resume-twelfth-original-responses.json.gz') if r.get('capture_id')}
    container = next(r for r in unpack(S / 'resume-twelfth-original-responses.json.gz') if r.get('container'))
    original_zip = base64.b64decode(container['raw_base64'])
    assert hashlib.sha256(original_zip).hexdigest() == sources['host-nufs-next3-package']['sha256']
    assert not any(sid.startswith('ncu-130-resume12-') for sid in sources)
    assert manifest['new_document_sources_added'] == 0
    for r in manifest['existing_nufs_packet_revalidation']:
        raw = base64.b64decode(captures[r['capture_id']]['raw_base64'])
        assert hashlib.sha256(raw).hexdigest() == r['sha256']
        if r['source_container']:
            with zipfile.ZipFile(io.BytesIO(original_zip)) as archive:
                assert archive.read(r['source_container']['member']) == raw
        else:
            assert sources[r['same_content_as_prior_source']]['sha256'] == r['sha256']
        for p in (r.get('visual_review') or {}).get('rendered_pages', []):
            assert hashlib.sha256((ROOT / p['artifact']).read_bytes()).hexdigest() == p['render_sha256']


def test_twelfth_keeps_existing_conditional_documents_stages_and_course_readings():
    h = json.loads((S / 'reviewed-host-records.json').read_text())
    assert 'ncu-018' not in h and 'ncu-130' not in h
    original = json.loads((ROOT / 'sources/ncu/2026-10-08/reviewed-host-records.json').read_text())
    nufs = original['ncu-130']
    assert len(nufs['host_document_stages']) == 8
    assert len(next(s for s in nufs['host_document_stages'] if s['id'] == 'initial-reference')['document_requirements']) == 13
    assert 'host-nufs-next3-syllabi-spring2026' in nufs['source_ids']
    assert len(original['ncu-018']['host_documents']) == 5


def test_twelfth_queue_receipts_keep_full_pdf_counts_unchanged():
    manifest = json.loads((D / 'reading-manifest.json').read_text())
    rs = {s['id']: s for s in unpack(S / 'host-web-evidence.json.gz')}
    assert len(manifest['old_candidate_readings']) == 9
    for entry in manifest['old_candidate_readings']:
        source = rs[entry['source_id']]
        assert source['reading_review']['source_sha256'] == source['sha256']
        assert source['reading_review']['full_document_read'] is False
    counts = json.loads((B / 'catalog-completeness.json').read_text())
    assert counts['reviewed_host_records'] == 120
    assert counts['completion_source_full_text_read'] == 75
    assert counts['completion_source_full_visual_read'] == 10
