"""Synced CGU catalogue and suggested journeys, rendered by the shared platform UI."""
from __future__ import annotations

import json
from pathlib import Path

from .cgu_catalogue import CguCatalogue, CatalogueView
from .application_path import build_levels, level

CONTENT = Path(__file__).parent / 'demo_data/content.json'


class FrozenCatalogue:
    """Offline-isolated reader over the bundled CGU snapshot synced with app.uniway."""

    def __init__(self, path):
        self.store = CguCatalogue(path / 'unused-demo-cache.json')

    def view(self) -> CatalogueView:
        return self.store.view(refresh=False)


def _cgu_term_prompt(context) -> str:
    year = str(context.get('departure_year') or '').strip()
    academic_year = str(context.get('academic_year') or '').strip()
    semester = context.get('semester')
    if semester == 'fall':
        return f'{year} 秋季（{academic_year}-1）' if academic_year else f'{year} 秋季'
    if semester == 'spring':
        return f'{year} 春季（{academic_year}-2）' if academic_year else f'{year} 春季'
    if semester == 'full_year':
        return f'{year} 秋季・全學年（{academic_year}-1）' if academic_year else f'{year} 秋季・全學年'
    return f'{year} 尚未決定'.strip()


def journey_levels(context, evaluated, catalog, values=None):
    """Keep native direction/rule steps; add explicitly suggested personal tasks.

    The shared renderer, revision checks, storage and next-step logic remain in
    application_path.py. No recommendation is represented as official approval.
    """
    data = json.loads(CONTENT.read_text(encoding='utf-8'))
    sources = {row['id']: row['url'] for row in data['sources']}
    original = [item for stage in build_levels(context, evaluated, catalog, values) for item in stage['levels']]
    for row in original:
        if row['id'] == 'term':
            row['prompt'] = _cgu_term_prompt(context)
    stages, number = [], 0
    is_116_fall = (
        str(context.get('academic_year') or '') == '116'
        and context.get('semester') in ('fall', 'full_year', 'undecided')
    )
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
            if task['id'] == 'internal-submit' and is_116_fall:
                item.update(
                    title='12/21 17:00 校內截止前完成長庚 116-1 申請（完成後自行記錄）',
                    official_deadline_at='2026-12-21T17:00:00+08:00',
                    deadline_confirmed=True,
                    deadline_source_url=sources['selection'],
                )
            items.append(item)
        for item in items:
            number += 1
            item.update(stage=index, stage_key=stage['title'], number=number)
        stages.append(dict(key=stage['id'], title=stage['title'], icon='route', index=index, levels=items))
    return stages


def source_dashboard(dashboard):
    """Keep CGU's verified platform dashboard synced while appending demo source notes."""
    from .models import SourceReference
    data = json.loads(CONTENT.read_text(encoding='utf-8'))
    existing_urls = {src.source_url for src in dashboard.sources if src.source_url}
    for row in data['sources']:
        if row['url'] not in existing_urls:
            dashboard.sources.append(
                SourceReference(
                    title=row['title'],
                    source_url=row['url'],
                    summary=row['scope'] + ' 查核日期：' + row['checked_on'],
                )
            )
            existing_urls.add(row['url'])
    return dashboard
