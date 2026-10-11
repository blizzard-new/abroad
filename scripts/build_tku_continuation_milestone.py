"""Full denominator continuation ledger; completion and remaining source needs."""
import json
from collections import Counter
from pathlib import Path
B=Path(__file__).resolve().parents[1]/'src/exchange_info/official_data/tku'

def main():
    audit=json.loads((B/'full_census_audit.json').read_text());acceptance=json.loads((B/'full_census_acceptance.json').read_text())
    photos={r['id']:r for r in json.loads((B/'campus_asset_manifest.json').read_text())};locations={r['id']:r for r in json.loads((B/'campus_location_manifest.json').read_text())}
    searches=json.loads((B/'commons_asset_batches.json').read_text());geo=json.loads((B/'wikidata_asset_batches.json').read_text());maps=json.loads((B/'official_geography_checks.json').read_text());visual=json.loads((B/'new_photo_visual_review_history.json').read_text())
    photo_attempts=json.loads((B/'new_photo_candidates.json').read_text());rows=[]
    dated_holds={r['id']:r for r in json.loads((B/'photo_date_holds.json').read_text())}
    initial_triage=json.loads((B/'milestone3_unread_triage.json').read_text())
    reviewed=json.loads((B/'curated_partner_facts.json').read_text())
    gap_reviews={r['id']:r for r in json.loads((B/'milestone3_asset_gap_reviews.json').read_text())} if (B/'milestone3_asset_gap_reviews.json').exists() else {}
    if (B/'milestone4_asset_source_limits.json').exists():
        gap_reviews={r['id']:r for r in json.loads((B/'milestone4_asset_source_limits.json').read_text())['schools']}
    for d in audit['schools']:
        latest={}
        for s in d['public_source_checks']:
            if s['source_url'] not in latest or s['checked_at']>latest[s['source_url']]['checked_at']:latest[s['source_url']]=s
        photo=photos.get(d['id']);location=locations.get(d['id'])
        rows.append(dict(id=d['id'],school_name=d['school_name'],country=d['country'],
            photo_status='verified_asset' if photo else 'not_verified_new',coordinate_status='verified_asset' if location else 'not_verified_new',
            selected_photo={k:photo.get(k) for k in ('source_url','sha256','license','author','photo_date','campus_pair_scope')} if photo else None,
            selected_coordinate=location.get('location') if location else None,
            photo_source_checks=[{k:r.get(k) for k in ('source_url','checked_at','http_status','error','query','phase','sha256')} for r in searches if r['institution_id']==d['id']],
            photo_download_attempts=[{k:r.get(k) for k in ('title','source_url','sha256','error','http_status')} for r in photo_attempts if r['id']==d['id']],
            photo_visual_history=visual.get(d['id'],[]),
            photo_capture_period_hold=dated_holds.get(d['id']),
            geographic_source_checks=[{k:r.get(k) for k in ('source_url','checked_at','http_status','error','query','phase','sha256')} for r in geo if r['institution_id']==d['id']],
            official_geography_checks=[r for r in maps if r['institution_id']==d['id']],
            coordinate_candidate_review=d['fields']['coordinates'].get('candidate_review'),coordinate_alternative_review=d['fields']['coordinates'].get('alternative_candidate_review'),
            latest_host_endpoints=list(latest.values()),source_scope_blockers=d['source_blockers'],
            remaining_fields=[dict(key=k,status=v['status'],reason=v['reason']) for k,v in d['fields'].items() if v['status'] not in {'verified_asset','verified_current'}],
            asset_gap_content_review=gap_reviews.get(d['id']),
            remaining_photo_requirement=None if photo else gap_reviews.get(d['id'],{}).get('photo_reason',dated_holds[d['id']]['reason'] if d['id'] in dated_holds else ('；'.join(v.get('reason','') for v in visual.get(d['id'],[]) if v.get('result') in {'reject','rejected'}) or '已查精確機構名、native別名及命名校景分類；已保存結果無符合機構身份、實見校景、自由授權及拍攝年份的候選。未取得不等於官方尚未提供。')),
            remaining_coordinate_requirement=None if location else gap_reviews.get(d['id'],{}).get('coordinate_reason','公開代表點及官方命名校園地圖已依記錄查核；多值、錯誤城市、舊新母體／校區、來源未提供數值或地圖只有視窗仍缺。需官方命名實體校區或可独立核對的單一代表點。')))
    checks=json.loads((B/'host_source_retry_checks.json').read_text());alternatives=json.loads((B/'host_source_alternative_checks.json').read_text())
    result=dict(base_commit=acceptance['base_commit'],checked_date='2026-10-11',denominator=287,
        milestone4_handoff=dict(candidate_review='milestone4_candidate_content_reviews.json',fixed_candidates=69,
            complete_available_bodies=64,partial_bodies=4,http404=1,remaining_reference_sources='milestone4_remaining_source_limits.json',
            asset_source_limits='milestone4_asset_source_limits.json',note='固定69候選均已交代；來源年份確認不代表淡江本期核實，未耗盡的命名地圖另列。'),
        milestone1=dict(photos=66,coordinates=68),current=dict(photos=len(photos),coordinates=len(locations),photo_percent=round(len(photos)/287*100,2),coordinate_percent=round(len(locations)/287*100,2),photo_gaps=287-len(photos),coordinate_gaps=287-len(locations)),
        delta_from_milestone1=dict(photos=len(photos)-66,coordinates=len(locations)-68),
        host_retry_checks=len(checks),host_retry_statuses=dict(Counter(str(r.get('http_status') or 'connection_error') for r in checks)),
        official_alternative_checks=len(alternatives),official_alternative_statuses=dict(Counter(str(r.get('http_status') or 'connection_error') for r in alternatives)),
        commons_searches=len(searches),wikidata_and_named_page_searches=len(geo),official_geography_checks=len(maps),
        scope='已查核本輪具體target及逐校留存候選；remaining triage保留尚未實讀及不適用候選。不宣稱全部公開路徑、所有來源內容／年度或6314欄完整核實。不得越過403、429或重複503。',
        stop_rules=['429按Retry-After停止服務／主機並保存恢復時間。','每個503端點至多一次後續重試；五個明治模板早期重疊抓取的實際額外次數另列歷史，不抹除。','403及挑戰回應不嘗試cookie、代理、憑證或保護繞過。','來源只提供多校區／母體不明／不同城市或沒有數值時保留缺口。','名額283校未核實本期；來源未核實新版不等於官方明示尚未公告。'],
        content_reviewed_host_references=dict(institutions=len(reviewed),fields=sum(len(r['fields']) for r in reviewed)),
        semantic_host_year_review=dict(institutions=sum(any(f.get('source_period_verified') for f in r['fields'].values()) for r in reviewed),fields=sum(bool(f.get('source_period_verified')) for r in reviewed for f in r['fields'].values()),note='有明確接待期與僅正文審核之未載年度一般生活參考分開；全為接待校參考，未推定TKU當期名額與校區。'),schools=rows)
    (B/'continuation_gap_closure.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='schools'},ensure_ascii=False))

if __name__=='__main__':main()
