"""Build TKU-only reference life profiles; retain four reviewed rows byte-for-byte."""
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'src/exchange_info/official_data/tku'
EXTRA_REFERENCE_LABELS={'student_support':'接待校學生支援參考'}


def build():
    from exchange_info.models import DestinationProfile,SourceReference,StudentGuideSection
    from exchange_info.tku_census import census_audit,census_school_name,programme_map
    from exchange_info.tku_assets import complete_profile
    target=BUNDLE/'destination_profiles.jsonl'
    current=[json.loads(line) for line in (BUNDLE/'partners_current.jsonl').read_text().splitlines()]
    current_names={r['fields']['school_name']['value'] for r in current}
    preserved=[line for line in target.read_text().splitlines(keepends=True)
               if json.loads(line)['school_name'] in current_names]
    assert len(preserved)==4
    enrichment={r['id']:r for r in map(json.loads,(BUNDLE/'partner_enrichment.jsonl').read_text().splitlines())}
    profiles=[]
    for row in census_audit()['schools']:
        if any(programme_map()[pid]['fields']['school_name']['value'] in current_names for pid in row.get('programme_ids',[])):
            continue
        fields=enrichment.get(row['id'],{}).get('fields',{})
        sections=[]
        sources={row['directory_url']:SourceReference(title='淡江姊妹校／計畫機構身分',source_url=row['directory_url'],category='partner_school',
            summary='286校姊妹名錄與計畫名單機構聯集；協議和歷史計畫不能作本期開放名額。查核2026-10-11。')}
        for key,fact in fields.items():
            ev=fact['evidence']
            urls=list(dict.fromkeys(e['source_url'] for e in ev))
            label=row['fields'].get(key,{}).get('label',EXTRA_REFERENCE_LABELS.get(key,key))
            sections.append(StudentGuideSection(key=key,title=label,summary=fact['value'],
                points=[f"適用：{e['applicable_year']}；{e.get('locator','')}；查核{e['checked_at']}" for e in ev],source_urls=urls,evidence_type='official',
                caution=fact['reason']))
            for evidence in ev:
                sources[evidence['source_url']]=SourceReference(title=label+'（接待校參考）',
                    source_url=evidence['source_url'],category='partner_school',summary=f"{evidence['applicable_year']}；{evidence['locator']}；{evidence['quote'][:350]}")
        def summary(*keys):
            selected=[fields[k]['value'] for k in keys if k in fields]
            return '接待校原文參考；適用年度及淡江提名／校區另核對：'+ '\n'.join(selected[:2]) if selected else None
        profile=DestinationProfile(home_university='淡江大學',school_name=census_school_name(row),country=row['country'],
            cost_summary=summary('costs','living_costs'),housing_summary=summary('housing','housing_costs'),
            transport_summary=summary('transport'),campus_life_summary=summary('course_restrictions','campus'),
            sources=list(sources.values()),student_guide_sections=sections,last_checked='2026-10-11T00:00:00+00:00',
            coverage_status='official_partial' if fields else 'not_collected',
            coverage_note='全量機構逐校缺口已列；'+('保留接待校公開原文參考，來源年度、學制、院系／校區與淡江提名對應仍須另查。' if fields else '公開入口已查，但此校生活欄尚未取得可核實原文，來源失敗另列逐校audit。')+'歷史名額不可沿用，本期母校資格／表格未核實不等於官方明示尚未公告。')
        profiles.append(complete_profile(profile))
    assert len(profiles)==283 and len({p.school_name for p in profiles})==283
    def json_line(profile):
        text=profile.model_dump_json()
        for char in ('\u0085','\u2028','\u2029'):
            text=text.replace(char,f'\\u{ord(char):04x}')
        return text+'\n'
    target.write_text(''.join(preserved)+''.join(json_line(p) for p in profiles))
    print(json.dumps(dict(profiles=4+len(profiles),reviewed_current_rows_preserved=4,reference_profiles=len(profiles),with_host_references=sum(bool(p.student_guide_sections) for p in profiles))))


if __name__=='__main__':build()
