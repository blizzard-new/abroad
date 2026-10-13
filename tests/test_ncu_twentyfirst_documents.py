"""Document phases, programme limits and old-year prices survive the generated workflows."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/twentyfirst'


def test_eleven_originals_and_twenty_pages_have_matching_bytes():
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    raw = {s['source_id']: s for s in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-twentyfirst-original-responses.json.gz').read_bytes()))}
    assert len(ledger) == 11 and sum(len(r['pages_reviewed']) for r in ledger) == 20
    for row in ledger:
        source = sources[row['source_id']]
        assert hashlib.sha256(base64.b64decode(raw[row['source_id']]['body'])).hexdigest() == source['sha256'] == row['source_sha256']
        assert source['content_status']['all_pages_read']
        assert source['content_status']['visual_reviewed_page_count'] == len(source['pages'])
        assert not row['current_116_approval']
        for render in row['rendered_pages']:
            assert hashlib.sha256((ROOT / render['path']).read_bytes()).hexdigest() == render['sha256']


def test_initial_and_post_offer_documents_are_separated():
    from exchange_info import storage
    workflows = [w for w in storage.load_bundled_application_workflows() if w.home_university == '國立中央大學']
    steps = {s.rule_id: s for w in workflows for s in w.steps}
    initial = steps['ncu-110-host-apply']
    later = steps['ncu-110-host-accepted-i20']
    assert len(initial.document_requirements) == 5
    assert not any('財力' in d.name or '護照' in d.name for d in initial.document_requirements)
    assert initial.document_requirements[-1].conditional
    assert len(later.document_requirements) == 3
    assert initial.order < later.order
    assert all(d.stage == 'post_offer' and d.conditional for d in later.document_requirements)
    assert len(steps['ncu-145-host-apply'].document_requirements) == 6
    insurance = steps['ncu-145-host-visa-issued-insurance']
    assert insurance.order > steps['ncu-145-host-apply'].order
    assert len(insurance.document_requirements) == 1
    assert '可於學生簽證核發後補交' in insurance.timing
    assert len(steps['ncu-204-host-apply'].document_requirements) == 10
    course_form = steps['ncu-204-host-accepted-course-form']
    assert course_form.order > steps['ncu-204-host-apply'].order
    assert course_form.document_requirements[0].stage == 'post_offer'
    assert len(steps['ncu-003-host-apply'].document_requirements) == 4
    geneva = steps['ncu-057-host-apply'].document_requirements
    assert len(geneva) == 6 and geneva[4].conditional
    assert all(w.review_status == 'pending_review' for w in workflows)
    assert not any(s.deadline_reminder_eligible for w in workflows for s in w.steps)


def test_scope_and_source_ambiguities_are_not_silently_resolved():
    rows = json.loads((ROOT / 'sources/ncu/2026-10-11/reviewed-host-records.json').read_text())
    txt = lambda rid, field: '\n'.join(rows[rid]['fields'][field]['points'])
    assert '非學位交換可接受B1' in txt('ncu-003', 'language')
    assert '法語C1' in txt('ncu-057', 'language')
    assert '不能自行改成英文C1' in txt('ncu-057', 'language')
    assert '只合計1200' in txt('ncu-057', 'cost')
    assert '2024–25' in txt('ncu-110', 'tuition')
    assert '僅屬該院交換方案' in txt('ncu-204', 'tuition')
    assert '中央與天普兩校學雜費' in txt('ncu-110', 'tuition')
    assert '4學期不可填成4名' in txt('ncu-110', 'eligibility')
    assert '聽力與閱讀各390' in txt('ncu-110', 'language')
    assert '碩士至少兩門、最多9學分' in txt('ncu-145', 'courses')
    assert '一山校區' in txt('ncu-145', 'city')
    assert '不能二選一' in txt('ncu-145', 'insurance')
    assert '大於525' in txt('ncu-204', 'language')
    assert '不自行改成大於等於' in txt('ncu-204', 'language')
    assert '原件只用$未明幣別' in txt('ncu-204', 'housing')
    from exchange_info.ncu_student_view import fetch_ncu_partner_universities
    assert all(p.quota is None and p.availability_status == 'agreement_only' for p in fetch_ncu_partner_universities())
