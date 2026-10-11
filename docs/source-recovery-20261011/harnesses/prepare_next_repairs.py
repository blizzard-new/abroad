"""Apply only after frozen 3129 acceptance ends and fixed NCU e25 is integrated."""
from pathlib import Path
import json,subprocess,sys,os,gzip,hashlib
root=Path('/workspace/abroad-globe-20261011')
assert sys.argv[1:] == ['--apply-after-frozen-acceptance']
raw=Path('/workspace/recovery-evidence-20261011')
assert json.loads((raw/'ccu2-full-supabase-runtime/metadata.json').read_text())['test_result']=='passed'
for i in range(4):assert json.loads((raw/f'ccu2-full-shard-{i}/metadata.json').read_text())['test_result']!='running'
for mode in ['cold','warm']:assert json.loads((raw/f'ccu2-final-{mode}-memory-command/metadata.json').read_text())['test_result']!='running'
# Require the exact NCU asset input, including its later photographed-date fix.
path='sources/ncu/2026-10-11/resume-third-location-review.json'
assert (root/path).read_bytes()==subprocess.check_output(['git','show','e25ff02a1ebc69ea126a814d105e88b272539351:'+path],cwd=root)
def write(path,text):
 tmp=path.with_name(path.name+'.integration-tmp');tmp.write_text(text);os.replace(tmp,path)
def dump(p,o):write(p,json.dumps(o,ensure_ascii=False,indent=2)+'\n')
# Preserve separately reviewed source details; do not merge every old/new field blindly.
p=root/'sources/ncu/2026-10-11/reviewed-host-records.json';supplements=json.loads(p.read_text());old=json.loads((root/'sources/ncu/2026-10-08/reviewed-host-records.json').read_text())['ncu-081'];row=supplements['ncu-081']
for name,indexes in {'language':[1],'courses':[0,1,2],'eligibility':[0],'arrival':[0,1],'host_documents':[2,3]}.items():
 prior=old['fields'][name];current=row['fields'][name]
 for i in indexes:
  point='2026/10/08 原件補充（116適用仍待確認）：'+prior['points'][i]
  assert point not in current['points'];current['points'].append(point)
 for source in prior['sources']:
  if source not in current['sources']:current['sources'].append(source)
 if prior.get('unresolved'):
  current['unresolved']='；'.join(dict.fromkeys(filter(None,[current.get('unresolved'),prior['unresolved']])))
row['source_ids']=list(dict.fromkeys(row['source_ids']+old['source_ids']))
# Keep evidence of the optional form distinct from other accepted language proofs.
language=next(d for d in old['host_documents'] if 'Language Assessment Sheet' in d['name']).copy()
language.update(name='Language Assessment Sheet（選用此語言證明時）',conditional=True,condition='僅選用此表作語言能力證明者；認可測驗或適用豁免附件不因此另加此表。',stage='student_application',applicability_status='reference_only',applicability_note='2026/10/08 已查核公開表格的欄位；116適用版本、語言證明選項與本人資格仍須確認。')
language['source_urls']=list(dict.fromkeys(language['source_urls']+[language['official_form_url']]))
row['host_documents'].append(language)
la=next(d for d in row['host_documents'] if d['name']=='Learning Agreement（非EU雙邊，母校要求時）')
original_la=next(d for d in old['host_documents'] if 'Learning Agreement' in d['name'])
for key in ['official_form_url','signatures','stamps']:la[key]=original_la[key]
la['source_urls']=list(dict.fromkeys(la['source_urls']+[la['official_form_url']]))
la['applicability_note']+=' 2026/10/08 所讀non-EU Word表列學生與兩校各departmental／institutional coordinator欄；使用此表與當期簽章次序仍須兩校確認。'
dump(p,supplements)
policies=root/'sources/ncu/2026-10-11/document-conditions.json';conditions=json.loads(policies.read_text());conditions.append({'school_name':'圖爾庫大學 University of Turku','rule_id':'ncu-081-host-apply','requirement_name':language['name'],'source_urls':[language['official_form_url']],'source_versions':[{'url':language['official_form_url'],'source_id':'host-turku-languageform','sha256':'19e5b1d39ae0a663afb83bbab4257fc7f2a52f83c3c4edd7807147ab4db01d67'}],'requires_on_campus_housing':False,'requires_institutional_confirmation':True,'confirmation_note':language['condition']+' 當期可接受選項及表格須核對。','scope_note':'原已查核表格參考；不核准中央116當期。'});dump(policies,conditions)
# Explicit multi-campus / relocation holds must not be revived by a shared fallback.
# Preserve only still-unresolved scope holds; the new Chuo and SJTU named-campus
# evidence supersedes their old hold, without asserting current exchange placement.
p=root/'sources/ncu/2026-10-11/campus-locations.json';locations=json.loads(p.read_text())
held=[]
for file,ids in [('resume-visual-review.json',{'ncu-042','ncu-060','ncu-075','ncu-084','ncu-115'}),
                 ('resume-discovery-review.json',{'ncu-009','ncu-023','ncu-024','ncu-025','ncu-078','ncu-079','ncu-080','ncu-154','ncu-179','ncu-205','ncu-208','ncu-212'})]:
    review=json.loads((root/'sources/ncu/2026-10-11'/file).read_text())
    for decision in review['coordinate_decisions']:
        id=decision.get('capture_row_id',decision.get('row_id'))
        if id not in ids:continue
        assert 'pending' in decision['decision']
        prior=next((r for r in locations['locations'] if r['school_name']==decision['school_name']),None)
        assert not prior or prior['geocode_status']!='verified'
        receipt=decision.get('source_receipt')
        if receipt is None:
            pack=json.loads(gzip.decompress((root/'sources/ncu/2026-10-11/resume-discovery-sourcepack.json.gz').read_bytes()))
            captured=next(x for x in pack if x['local_evidence_key']=='entity-discovery/'+id+'/entity.json')
            receipt=captured['receipt'];assert hashlib.sha256(captured['raw_utf8'].encode()).hexdigest()==receipt['sha256']
            assert json.loads(captured['raw_utf8'])['entities'][decision['qid']]['claims'].get('P625',[])==decision['original_P625']
        held_row={'school_name':decision['school_name'],'country':decision['country'],
            'latitude':None,'longitude':None,'geocode_status':'needs_review','geocoded_at':review['checked_at'],
            'source_url':receipt['url'],'identity_source_url':decision.get('identity_source_url'),
            'precision':'representative','note':'校區／現址仍待確認：'+decision['reason']+' 不使用共用舊點取代本校明確待確認結果。',
            'source_sha256':receipt['sha256'],'review_record':file+'#'+id,'allow_shared_fallback':False}
        if prior:locations['locations'].remove(prior)
        locations['locations'].append(held_row);held.append(held_row)
assert len(held)==17
dump(p,locations)
dump(raw/'next-ncu-explicit-location-holds.json',{'fixed_input':'e25ff02a1ebc69ea126a814d105e88b272539351','held':held,'resolved_by_new_named_campus_evidence':['Chuo Korakuen','SJTU Minhang'],'zero_P625_missing_not_automatically_held':True})
p=root/'src/exchange_info/ncu_completion.py';s=p.read_text()
s=s.replace('    rows = {}\n    for row in data["locations"]:', '    rows = {}\n    holds = set()\n    for row in data["locations"]:')
s=s.replace('        rows[(school_identity_key(row["school_name"]), row["country"])] = location\n    return rows', '        key = (school_identity_key(row["school_name"]), row["country"])\n        rows[key] = location\n        if row.get("allow_shared_fallback") is False:\n            if location.geocode_status == "verified":\n                raise ValueError("An explicit location hold cannot publish coordinates")\n            holds.add(key)\n    return rows, frozenset(holds)')
s=s.replace('    candidate = _locations_snapshot((stat.st_mtime_ns, stat.st_size)).get(\n        (school_identity_key(partner.school_name), partner.country))', '    locations, holds = _locations_snapshot((stat.st_mtime_ns, stat.st_size))\n    key = (school_identity_key(partner.school_name), partner.country)\n    candidate = locations.get(key)\n    if key in holds:\n        return candidate')
assert 'return rows, frozenset(holds)' in s and 'if key in holds:' in s
write(p,s)
# New upstream browser tests must use integrated semantics/counts and isolated output.
p=root/'tests/e2e/test_ncu_resume_assets.py';s=p.read_text().replace('import re','import re\nimport os',1)
s=s.replace("OUTPUT = Path('docs/data/ncu-completion-20261011/resume/third/browser')", "OUTPUT = Path(os.environ.get('NCU_RESUME_BROWSER_OUTPUT', '/tmp/ncu-resume-browser'))")
s=s.replace('本期名額待公告','本期名額待核實')
write(p,s)

# Test lifecycle assertions remain identical; isolate their event loop from Playwright's session fixture.
p=root/'tests/test_catalogue_memory.py';s=p.read_text();assert s.count('    asyncio.run(check())')==1;s=s.replace('    asyncio.run(check())','    # Playwright may keep its sync-driver loop active in the pytest main thread.\n    # A dedicated loop checks the same startup bound and shutdown restoration.\n    with ThreadPoolExecutor(max_workers=1) as pool:\n        pool.submit(asyncio.run, check()).result(timeout=10)');write(p,s)
# Catalogue source health belongs to catalogue exploration, not calendar/global forum layout.
p=root/'src/exchange_info/static/glass-theme.css';s=p.read_text();s+='''\n/* Keep catalogue provenance in its own reading area without displacing tools. */\nbody:not(.public-exploration-mode) #catalogue-source-status { display: none; }\nbody.unified-shell .catalogue-source-status {\n  width: calc(100% - 144px); max-width: 1400px; margin: 16px 32px 0 112px;\n}\n@media (min-width: 1600px) {\n  body.unified-shell .catalogue-source-status { margin-left: calc(112px + (100% - 1544px) / 2); }\n}\n@media (max-width: 900px) {\n  body.unified-shell .catalogue-source-status { width: calc(100% - 28px); margin: 14px 14px 0; }\n}\n''';write(p,s)
p=root/'src/exchange_info/static/index.html';s=p.read_text();assert 'glass-theme.css?v=20261001-ui-refinements-1' in s;write(p,s.replace('glass-theme.css?v=20261001-ui-refinements-1','glass-theme.css?v=20261011-source-layout-1'))
print('Applied bounded repairs; rebuild NCU generated data and validate before committing.')
