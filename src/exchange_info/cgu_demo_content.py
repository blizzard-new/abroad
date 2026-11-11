"""Dated CGU data and suggested journeys, rendered by the shared platform UI."""
from __future__ import annotations

import json
from pathlib import Path

from .cgu_catalogue import CguCatalogue, CatalogueView
from .application_path import build_levels, level

CONTENT = Path(__file__).parent / 'demo_data/content.json'
REFERENCE_NOTE = '2026-10-11 歷史資料；當期名額、語言、學期與截止日待確認，不代表開放申請。'


class FrozenCatalogue:
    def __init__(self, path):
        self.store = CguCatalogue(path / 'unused-demo-cache.json')

    def view(self):
        view = self.store.view(refresh=False)
        rows = []
        for original in view.partners:
            row = original.model_copy(deep=True)
            row.reference_data.update({key: str(getattr(row, key)) for key in
                ('quota', 'application_deadline', 'eligibility', 'language_requirement') if getattr(row, key)})
            row.availability_status = 'quota_unconfirmed'
            row.availability_note = REFERENCE_NOTE
            row.quota_status = 'reference_only'
            row.application_window_status = 'needs_confirmation'
            row.quota = '當期待確認'
            row.student_summary_zh.application_deadline = None
            row.application_deadline = None
            row.partner_application_deadline = None
            row.nomination_deadline = None
            row.partner_exchange_details.pop('application_deadline', None)
            row.program_options = []  # unverified historical options must not bypass the row's status
            row.eligibility = '歷史條件參考（當期待確認）：' + (row.eligibility or '資料不足，請查官方來源')
            row.language_requirement = '當期待確認；請核對目的校官方要求。'
            row.language_conditions = []
            row.checked_at = None  # retrieval is not a current-cycle verification
            rows.append(row)
        return CatalogueView(rows, view.source)


def journey_levels(context, evaluated, catalog, values=None):
    """Keep native direction/rule steps; add explicitly suggested personal tasks.

    The shared renderer, revision checks, storage and next-step logic remain in
    application_path.py. No recommendation is represented as official approval.
    """
    data = json.loads(CONTENT.read_text(encoding='utf-8'))
    sources = {row['id']: row['url'] for row in data['sources']}
    original = [item for stage in build_levels(context, evaluated, catalog, values) for item in stage['levels']]
    stages, number = [], 0
    for index, stage in enumerate(data['stages']):
        items = [row for row in original if row['id'] in ('home', 'term', 'target')] if index == 0 else []
        if index == 1:
            items.extend(row for row in original if row['id'].startswith('check-'))
        for task in stage['tasks']:
            source = task.get('source')
            detail = task['detail']
            if source == 'lincoln' and 'Lincoln' not in context['target_school']:
                source = None
                detail = '此事項是否適用、文件及日期待目的校通知確認；請記下你查到的結果。'
            item = level('cgu-' + task['id'], task['title'], 'confirm', detail,
                         stage['title'], warning='個人準備紀錄／適用性待確認；不代表已送件、受理或錄取。')
            item['source_urls'] = [sources[source]] if source in sources else []
            items.append(item)
        for item in items:
            number += 1
            item.update(stage=index, stage_key=stage['title'], number=number)
        stages.append(dict(key=stage['id'], title=stage['title'], icon='route', index=index, levels=items))
    return stages


def source_dashboard(dashboard):
    """Only the actually checked home-school excerpt supplies demonstration rules."""
    from .models import SourceReference, StudentInfoItem
    data = json.loads(CONTENT.read_text(encoding='utf-8'))
    refs = {row['id']: SourceReference(title=row['title'], source_url=row['url'],
        summary=row['scope'] + ' 查核日期：' + row['checked_on']) for row in data['sources']}
    items = [StudentInfoItem(title=row['title'], details=[row['body']], source=refs[row['source']])
             for row in data['rules']]
    dashboard.maximum_preferences = 2
    dashboard.language_score_minimums = {'toeic': 700}
    dashboard.eligibility = [items[0]]
    dashboard.language_requirements = [items[0]]
    dashboard.required_documents = [items[1]]
    dashboard.program_overview = [items[2], items[3]]
    dashboard.sources = list(refs.values())
    # Exact dates stay in the cited excerpt until a verified structured cycle is available.
    dashboard.application_periods = []
    return dashboard
