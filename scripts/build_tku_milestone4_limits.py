"""Per-school handoff for the frozen98 reference gaps and39 asset gaps."""
import json
from collections import Counter
from build_tku_milestone3_host_reviews import source
from tku_capture_io import BUNDLE
from build_tku_public_references import BAD_BODY


def write(name,value):
    (BUNDLE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def main():
    previous=json.loads((BUNDLE/'milestone3_remaining_triage.json').read_text())
    reviewed=json.loads((BUNDLE/'milestone4_candidate_content_reviews.json').read_text())
    enrichment={r['id']:r for r in map(json.loads,(BUNDLE/'partner_enrichment.jsonl').read_text().splitlines())}
    index={r['id']:r for r in json.loads((BUNDLE/'host_census_capture_index.json').read_text())}
    rows=[]
    for r in previous['host_unread']:
        checks=[]
        for m in index[r['id']]['sources']:
            s=source(m['id']);text=s.get('text')or''
            if s.get('http_status')!=200 or s.get('error'):status='external_open_failure'
            elif BAD_BODY.search(text[:1000]):status='challenge_body_not_readable_rules'
            elif not text or len(text)<100:status='empty_or_shell_body'
            elif 'login' in (s.get('title')or'').lower():status='login_body_not_public_rule'
            else:status='public_extracted_body_available_programme_scope_review_needed'
            checks.append(dict(source_id=s['id'],source_url=s['source_url'],final_url=s.get('final_url'),http_status=s.get('http_status'),error=s.get('error'),checked_at=s['checked_at'],content_sha256=s.get('sha256'),text_characters=len(text),status=status))
        candidate_reviews=[c for c in reviewed if c['institution_id']==r['id']]
        baseline='20_schools_69_candidates' if r['unread_candidates'] else '54_http200_capture_schools_without_rule_candidate' if any(s.get('http_status')==200 and not s.get('error') for s in r['source_reads']) else '24_no_successful_http200_capture_schools'
        fields=enrichment[r['id']]['fields']
        if fields:status='reference_added_current_TKU_applicability_unverified'
        elif candidate_reviews:status='all_fixed_candidates_accounted_no_applicable_reference_or_content_unavailable'
        elif any(s['status']=='public_extracted_body_available_programme_scope_review_needed' for s in checks):status='readable_public_body_needs_incoming_programme_identification_and_review'
        else:status='external_access_or_non_substantive_body_limitation'
        rows.append(dict(id=r['id'],school_name=r['school_name'],country=r['country'],baseline_group=baseline,status=status,
            added_reference_fields=list(fields),candidate_ordinals=[c['ordinal'] for c in candidate_reviews],
            candidate_assessments=[dict(ordinal=c['ordinal'],source_url=c['source_url'],status=c['status'],body_review_status=c['body_review_status'],assessment=c['assessment'],applicable_year=c['applicable_year']) for c in candidate_reviews],source_checks=checks,
            source_year_status='Known source years are host/historical references only; no current TKU mapping verified',
            next_action='向TKU核對計畫／提名／院系／年份；不從接待參考生成名額或母校文件。' if fields else '已完成固定候選集合；別的incoming公開路徑仍可能存在，沒有全網耗盡證據。' if candidate_reviews else '公開正文可讀，但未定位或讀到可用incoming規則；保持未核實，不稱未公告。' if status.startswith('readable') else '實際HTTP/連線/挑戰/外殼失敗逐URL列出；不繞過封鎖或推定官方未公告。'))
    assert len(rows)==98
    write('milestone4_remaining_source_limits.json',dict(baseline_commit='563fb9328c7ce15efc1ac3883d8c3d641df01e98',checked_date='2026-10-11',frozen_baseline_gap_institutions=98,now_without_reference=sum(not r['added_reference_fields'] for r in rows),baseline_groups=dict(Counter(r['baseline_group'] for r in rows)),current_statuses=dict(Counter(r['status'] for r in rows)),schools=rows))
    entities={}
    for batch in json.loads((BUNDLE/'wikidata_asset_entities.json').read_text()):
        for q,e in batch.get('response',{}).get('entities',{}).items():
            if q in entities:continue
            claims={k:[v['mainsnak'].get('datavalue',{}).get('value') for v in e.get('claims',{}).get(k,[])] for k in ['P625','P856','P17']}
            entities[q]=dict(source_url=batch['source_url'],checked_at=batch['checked_at'],content_sha256=batch.get('sha256'),locator=f'Actual stored entity {q} labels and P625/P856/P17',quote=json.dumps(dict(labels=e.get('labels',{}),claims=claims),ensure_ascii=False),claims=claims)
    assets=[]
    oldassets={r['id']:r for r in previous['assets']}
    for r in json.loads((BUNDLE/'milestone3_asset_gap_reviews.json').read_text()):
        a={**r,'reviewed_safe_sources_scope':'Retained exact/native/English institution queries, named Commons categories, reviewed image candidates and official geography endpoints listed here; not all Internet sources.', 'global_safe_source_exhaustion_proven':False}
        if r.get('photo_reason'):
            a['all_photo_source_checks']=oldassets[r['id']].get('photo_source_checks',[])
            a['photo_safe_candidate_set_status']='reviewed_retained_set_exhausted_no_qualified_photo'
            a['photo_next_action']='保留缺圖。新候選須同時有機構／校景身份、自由授權、可核對拍攝年及實見照片；官網公開圖片不等於已取得再發布授權。已列候選不需無限重查。'
            a['photo_external_limits']='具體查詢／年份／視覺拒收結果見photo_reason、photo_evidence及all_photo_source_checks；沒有證據證明所有官網圖片無授權。'
        if r.get('coordinate_reason'):
            qs=r.get('coordinate_candidate_review',{}).get('candidate_ids',[])
            a['all_retained_entity_evidence']=[dict(entity_id=q,**entities[q]) for q in qs if q in entities]
            a['unretrieved_known_entity_ids']=[q for q in qs if q not in entities]
            maps=[dict(source_url=c['source_url'],map_link=url) for c in r.get('official_coordinate_checks',[]) for url in (c.get('map_links') or [])]
            a['official_map_links_for_handoff']=maps
            identity=any(x in r['coordinate_reason'] for x in ['矛盾','不一致','合併','多個','多點','新母體','舊','研究所','未對應','低','粗點','精度','校区'])
            a['coordinate_safe_candidate_set_status']='not_exhausted_known_unretrieved_entity' if a['unretrieved_known_entity_ids'] else 'identity_or_campus_conflict_requires_confirmation' if identity else 'retained_sources_missing_verified_numeric_point'
            a['named_map_review_status']='ESIEA named landmark read; numeric conflict retained in milestone3_geography_review.json' if r['id']=='tku-sister-195' else 'Known public Adelaide named map not body-reviewed; institution merger already blocks automatic coordinate acceptance' if maps else 'No named map link retained from checked endpoints'
            a['coordinate_safe_source_exhaustion_proven']=False
            a['coordinate_next_action']='命名校區／機構承繼／矛盾須官方確認，保留缺值；已保存實際數值claims可交接，不能選第一點。若有未取得entity或未實讀命名map_link，安全候選仍未耗盡，逐項列出。'
            a['map_link_body_review_status']='Links retained for handoff; not automatically asserted read or accepted. Actual previous official review in coordinate_reason.'
        assets.append(a)
    assert len(assets)==39 and sum('photo_reason' in r for r in assets)==23 and sum('coordinate_reason' in r for r in assets)==23
    write('milestone4_asset_source_limits.json',dict(checked_date='2026-10-11',photo_gaps=23,coordinate_gaps=23,union_gap_institutions=39,schools=assets))
    print(json.dumps(dict(source_gaps=Counter(r['status'] for r in rows),asset_coordinate_limits=Counter(r.get('coordinate_safe_candidate_set_status') for r in assets if r.get('coordinate_reason')))))


if __name__=='__main__':main()
