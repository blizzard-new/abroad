"""Field-level TKU evidence coverage; live links alone never count as complete."""
from __future__ import annotations
import json
from collections import Counter
from .models import SchoolCompletenessItem, SchoolDataCompleteness
from .tku_data import BUNDLE, CHECKED_AT, load_tku_records, load_tku_sources

LABELS={
    'school_name':'合作校名稱','country':'國家／地區','website':'官方計畫入口',
    'degree_levels':'淡江名額表學制','department_scope':'淡江科系限制／優先',
    'campus':'外校校區','language':'母校表列授課語言','quota':'本梯名額',
    'home_eligibility':'母校學業／年級資格','home_language':'母校語言資格',
    'host_eligibility':'外校入學资格','host_language':'外校語言资格',
    'home_deadline':'母校申請期限','department_deadline':'系所較早截止',
    'department_to_oicsa_deadline':'系所送國際處期限','host_nomination_deadline':'外校提名期限',
    'host_deadline':'外校申請期限','study_period':'母校交換期間','host_study_period':'外校計畫期間',
    'host_calendar':'外校2027行事曆','documents':'本期母校文件','host_documents':'外校文件及條件／階段',
    'latest_forms':'外校本期表單內容／取得方式','host_programme_mapping':'本梯外校計畫對應',
    'housing':'外校住宿安排','housing_application_deadline':'外校住宿申請期限',
    'housing_costs':'住宿費用及包含項目','costs':'外校費用','home_costs':'母校學雜費',
    'living_costs':'生活費用','insurance':'保險要求及費用','visa_residence':'官方簽證／居留指引',
    'arrival_date':'精確抵達日期','arrival_preparation':'行前及抵達程序','transport':'接送／通勤',
    'course_restrictions':'課程／學分限制','course_schedule_2027':'2027實際課表','scholarships':'獎助機會及條件',
}
STATUS_MAP={'verified':'available','reference_only':'partial','needs_confirmation':'needs_confirmation',
            'missing_in_source':'missing','not_verified_new':'needs_confirmation','not_applicable':'partial'}


def matrix_row(record):
    sources={s['id']:s for s in load_tku_sources()}
    cells=[]
    for key,label in LABELS.items():
        fact=record.fields.get(key)
        if fact:
            evidence=[e.model_dump(mode='json') for e in fact.evidence]
            state=fact.status;value=fact.value
            reason=fact.reason or (('舊期資料，仅參考，未核實新版。' if record.selection_status=='reference_only' else '')+
                ('已核對來源中的此欄位；適用範圍依欄位與年度。' if state=='verified' else
                 '一般／較舊來源，不能當作2027確定內容。' if state=='reference_only' else
                 '；'.join(e.locator for e in fact.evidence)))
        else:
            evidence=[record.fields['school_name'].evidence[0].model_dump(mode='json')]
            state='not_verified_new';value=None
            reason='舊期合作校清單的此項未做外校當期逐校查核；不得推定可申請或沿用他校資料。'
        entries=[dict(source_id=e['source_id'],url=e['source_url'],checked_at=e['checked_at'],
                      result=sources[e['source_id']].get('open_status','verified_open'),
                      scope='field evidence' if fact else 'archive discovery only; host not inspected') for e in evidence]
        cells.append(dict(key=key,label=label,status=state,value=value,reason=reason,
                          evidence=evidence,checked_entries=entries))
    return dict(id=record.id,school_name=record.fields['school_name'].value,round_id=record.round_id,
        academic_year=record.academic_year,application_round=record.application_round,
        selection_status=record.selection_status,checked_at=CHECKED_AT.isoformat(),
        programme_caution=record.fields.get('host_programme_mapping').value if record.fields.get('host_programme_mapping') else
                          '124筆舊期計畫：新版及外校當期資訊未核實；不是本期可選學校。',
        field_states=dict(Counter(c['status'] for c in cells)),fields=cells)


def write_tku_completeness_matrix(records):
    rows=[matrix_row(r) for r in records]
    payload=dict(checked_at=CHECKED_AT.isoformat(),fields=LABELS,schools=rows,
        interpretation='逐校逐欄狀態。verified僅表示該來源與欄位的適用內容已核對；一般頁、舊版、未知值、矛盾及非公開表不當作全部完成。無法以單一百分比代表所有流程完成。')
    (BUNDLE/'completeness_matrix.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')


def build_tku_school_completeness(partner):
    record=next((r for r in load_tku_records() if r.fields['school_name'].value==partner.school_name),None)
    if record is None:
        from .tku_census import census_school_completeness
        return census_school_completeness(partner)
    row=matrix_row(record)
    items=[]
    for cell in row['fields']:
        basis='；'.join(f"{e['applicable_year']}／{e['locator']}" for e in cell['evidence'])
        note=f"{cell['reason']} 查核2026-10-08；{basis}"
        if cell['value'] is not None:note=str(cell['value'])+' '+note
        items.append(SchoolCompletenessItem(key=cell['key'],label=cell['label'],status=STATUS_MAP[cell['status']],
            note=note,source_urls=list(dict.fromkeys(e['source_url'] for e in cell['evidence']))))
    available=sum(i.status=='available' for i in items)
    return SchoolDataCompleteness(school_name=partner.school_name,country=partner.country,home_university='淡江大學',
        items=items,available_count=available,total_count=len(items),score=available/len(items),
        priority_gaps=[i.label for i in items if i.status in {'missing','needs_confirmation'}],
        disclaimer='依逐欄來源及年度判定；一般頁或舊年度只列部分資料。本期母校已截止，外校期限不表示校內重新開放。非公開表內容尚待提供；完整度分數不表示可申請或所有流程已完成。')
