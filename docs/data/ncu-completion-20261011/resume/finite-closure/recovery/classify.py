from pathlib import Path
from datetime import datetime,timezone
import json,gzip,collections,csv,re
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/finite-closure');D=R/'docs/data/ncu-completion-20261011/resume/finite-closure';B=R/'sources/ncu/2026-10-08'
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
sources={s['id']:s for s in json.load(gzip.open(R/'src/exchange_info/official_data/ncu/source-evidence.json.gz'))};frozen=json.load(gzip.open(R/'docs/data/ncu-completion-20261011/resume/twentyeighth/long-document-inventory.json.gz'))['items'];previous=json.load(open('/workspace/ncu-resume-work/thirtysecond/long-document-inventory.json'))['items'];uncited=[s for s in previous if not s['cited_by_reviewed_host']];indices={s['id']:i for i,s in enumerate(uncited,1)};assert len(uncited)==221
records={}
for dt in ['2026-10-08','2026-10-11']:
 for rid,r in json.load(open(R/'sources/ncu'/dt/'reviewed-host-records.json')).items():
  old=records.get(rid,{});records[rid]={**old,**r,'fields':{**old.get('fields',{}),**r['fields']},'source_ids':list(dict.fromkeys(old.get('source_ids',[])+r['source_ids']))}
references=collections.defaultdict(list);background=collections.defaultdict(list)
for rid,r in records.items():
 for sid in r['source_ids']:background[sid].append(rid)
 for field,f in r['fields'].items():
  for ref in f['sources']:references[ref['id']].append({'row_id':rid,'field':field,'page':ref.get('page')})
mapping=json.load(open(B/'source-map-candidates.json'));mapped=collections.defaultdict(list)
for row in mapping:
 for sid in row['files']:mapped[sid].append(row['row_id'])
fullhash=collections.defaultdict(list)
for s in sources.values():
 if s.get('sha256')and s['content_status']['all_pages_read']:fullhash[s['sha256']].append(s['id'])
course={23,24,32,45,53,54,56,57,64,73,77,84,91,92,93,94,97,122,135,152,168,185,192,212}
orphans={4,7,12,22,23,24,27,28,30,32,101,171,172,173,174,195}
illustrated={21,47,58,117,118,158,159}
intro={1,2,3,5,6,8,9,10,11,15,18,25,26,29,31,33,40,42,43,48,50,55,63,67,70,75,80,83,87,88,96,110,128,130,132,133,138,144,145,149,151,157,162,163,165,167,170,179,181,182,183,184,197,203,209,210,213,216,217,218,220,221}
items=[]
for old in frozen:
 sid=old['id'];s=sources[sid];sha=s.get('sha256');review=s.get('reading_review',{});v=s.get('visual_review',{});read=set(review.get('pages_reviewed',[])if sha and review.get('source_sha256')==sha else [])|set(v.get('pdf_pages_reviewed',[])if sha and v.get('source_sha256')==sha else []);refs=references[sid];missing=sorted({r['page'] for r in refs if r['page'] not in read},key=str);index=indices.get(sid);header=(s.get('pages')or[{}])[0].get('text','')[:200];dup=[x for x in fullhash.get(sha,[])if x!=sid]
 if s['content_status']['all_pages_read']:category='full_original_reviewed';reason='已有同SHA原件全頁阅读證據，年度與方案限制仍保留。'
 elif refs and not missing:category='cited_pages_verified_remainder_unread';reason='實際欄位引用頁已有同SHA閱讀／視讀紀錄；其他頁未讀，不需為現有引用全部翻譯。'
 elif sid=='host-hcm-iex-2018-browser':category='historical_excerpt_original_refresh_blocked';reason='僅2018既有兩頁摘錄；本次HTML challenge及正常瀏覽器TLS失敗，原件SHA未知。未繞過TLS；非當期表。'
 elif refs:category='cited_page_review_unresolved';reason='仍有實際欄位引用頁缺閱讀證據，應先處理，不可稱外部阻礙。'
 elif background[sid]:category='background_source_only_no_field_claim';reason='校級來源集合列名，未在人工欄位引用任何頁；不得把集合列名當全文核讀。'
 elif dup:category='exact_sha_alias_of_reviewed_original';reason='完整原件SHA與已核讀來源相同，可追溯重用；未另增閱讀或全讀筆數。'
 elif index in {34,160}:category='identity_or_address_conflict_reference';reason=('原文錫耶納校名與Dorsoduro Venezia地址不一致。'if index==34 else 'VISP Wisconsin校名與1801 Broad Street Philadelphia地址不一致。')+'不得用作校區定位；僅候選，不升當期。'
 elif index==196:category='filename_document_year_conflict';reason='檔名2026–27，首段正文卻標2025 Fall–2026 Spring；依正文保留舊年，不按檔名改當期。'
 elif index in orphans:category='identity_mapping_unresolved';reason='只有封面／首段及檔名候選，未確立214列中的校名國別校區與方案對應，不自動按近似名稱套用。'
 elif index in course:category='course_reference_partial_unread';reason='課程清單／學院課程參考；僅首段辨識，詳細課綱未讀，非所有課對中央開放或116開課保證。'
 elif index in illustrated:category='visual_original_review_needed_if_used';reason='影像／圖文主體尚未逐頁視讀；首段或檔名不能代替全文，若用於欄位須再看指定原頁。'
 elif index in intro:category='background_or_historical_intro_unread';reason='簡介、宣傳、地圖或舊年操作參考，只完成首段／檔名分流；規則未全文讀、不當116正式接收條件。'
 else:category='potentially_applicable_fact_or_guide_unread';reason='資料表／指南可能仍可補參考缺口，目前僅首段與檔名有限分流；待讀是後續研究工作，不是官方未公布或外部阻礙。'
 items.append({'source_id':sid,'source_url':s['url'],'label':s.get('label'),'frozen_source_sha256':old.get('sha256'),'source_sha256':sha,'retrieved_at':s.get('checked_at'),'pdf_pages_or_parts':len(s.get('pages',[])),'classification':category,'reason_zh':reason,'year_tokens_in_label':sorted(set(re.findall(r'20\d{2}(?:[–_/ -]+(?:20)?\d{2})?',s.get('label','')))),'year_scope_note':'標題年份只是檢索線索，正文／適用學年以各份閱讀紀錄為準；全項不等中央116核准。','header_preview_for_triage':header,'header_scope':'僅先前實際顯示的首段摘要與檔名分流，不計整頁／全文已讀'if index else '詳同SHA閱讀紀錄','candidate_mapping_row_ids':mapped[sid],'mapping_note':'候選對照，不因表列即完成身份核實；兩個拉曼已另人工分開','manual_field_references':refs,'background_only_rows':background[sid]if not refs else [],'native_or_visual_pages_reviewed':sorted(read,key=str),'missing_field_reference_pages':missing,'alias_full_read_source_ids':dup,'full_original_read':s['content_status']['all_pages_read'],'content_status':s['content_status'],'license_scope':'公開來源只供資料引用與查核；頁內照片無獨立授權不作校景','current_116_approval':False})
counts=dict(collections.Counter(x['classification']for x in items));remaining=[x for x in items if not x['full_original_read']];cited=[x for x in remaining if x['manual_field_references']or x['background_only_rows']];hashes={x['source_sha256']for x in cited if x['source_sha256']};null=sum(not x['source_sha256']for x in cited)
report={'checked_at':datetime.now(timezone.utc).isoformat(),'frozen_baseline':'c9cc78890403998adc7848c59564751217ca79bd','scope':'第28批凍結300來源；本輪有限核引用、身份及適用性分流，不宣稱所有214校或所有候選內容完成','frozen_sources':len(items),'frozen_valid_unique_sha':len({x['sha256']for x in frozen if x.get('sha256')}),'frozen_sources_without_sha':sum(not x.get('sha256')for x in frozen),'category_counts':counts,'full_original_read_since_freeze':sum(x['full_original_read']for x in items),'remaining_not_full_read':len(remaining),'remaining_cited_sources':len(cited),'remaining_cited_valid_unique_sha':len(hashes),'remaining_cited_sources_without_sha':null,'remaining_cited_alias_extras':len(cited)-len(hashes)-null,'remaining_uncited_candidates':len(uncited),'remaining_cited_total_pages_or_parts':sum(x['pdf_pages_or_parts']for x in cited),'cited_field_sources_without_reading_evidence':[x['source_id']for x in items if x['classification']=='cited_page_review_unresolved'],'blocked_original_source_ids':['host-hcm-iex-2018-browser'],'items':items}
assert len(items)==300 and len(set(x['source_id']for x in items))==300;assert not report['cited_field_sources_without_reading_evidence'];js(D/'frozen-candidate-classification.json',report)
fields=['source_id','classification','label','source_url','source_sha256','pdf_pages_or_parts','candidate_mapping_row_ids','native_or_visual_pages_reviewed','missing_field_reference_pages','reason_zh']
with (D/'frozen-candidate-classification.csv').open('w')as f:
 w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader()
 for x in items:w.writerow({k:(';'.join(map(str,x[k]))if isinstance(x[k],list)else x[k])for k in fields})
audit=json.load(open(R/'src/exchange_info/official_data/ncu/field-audit.json'))
unreviewed=[p for p in audit if not any(rid in records for rid in p['source_rows'])]
js(D/'schools-without-manual-host-review.json',[{'source_rows':p['source_rows'],'school_name':p['school_name'],'country':p['country'],'candidate_source_ids':list(dict.fromkeys(sid for rid in p['source_rows'] for sid in next((m['files']for m in mapping if m['row_id']==rid),[]))),'reason':'尚無逐校人工host欄位紀錄；公開候選待讀，不稱官方未公布或外部阻礙。'}for p in unreviewed])
assert len(unreviewed)==59
print(json.dumps({k:v for k,v in report.items()if k!='items'},ensure_ascii=False));print('unreviewed_partners',len(unreviewed))
