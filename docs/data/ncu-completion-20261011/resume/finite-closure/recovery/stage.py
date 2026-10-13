from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,shutil,copy,subprocess
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/finite-closure');B=R/'sources/ncu/2026-10-08';D=R/'docs/data/ncu-completion-20261011/resume/finite-closure';BASE='bfbef5202eb2ab4e918553ad8721a063552ab1be'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==BASE
D.mkdir(exist_ok=True);(D/'source-pages').mkdir(exist_ok=True);(D/'selected-native-text').mkdir(exist_ok=True);now=datetime.now(timezone.utc).isoformat()
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def gz(p,x):p.write_bytes(gzip.compress(json.dumps(x,ensure_ascii=False).encode(),mtime=0))
packs={p:json.load(gzip.open(B/p))for p in ['drive-evidence.json.gz','host-web-evidence.json.gz']};byid={s['id']:s for pack in packs.values()for s in pack};notes=json.load(open(W/'reading-notes.json'));ledger=[]
for n in notes:
 if n['id']=='host-sgntu-info':n['visual_pages_read']=[4,14]
 if n['id']=='host-tohoku-attachment-24':
  n['visual_pages_read']=[10,11];n['note_zh']=n['note_zh'].replace('表房型對應需原圖','已原圖核對表格合併房型欄，不把原生錯序任意指派房型')
 sid=n['id'];s=byid[sid];old=copy.deepcopy(s);stem=sid+'-confirmed' if sid=='host-tuaf-newhandbook' else sid;raw=(W/(stem+'.pdf')).read_bytes();receipt=json.load(open(W/(stem+'.pdf.source.json')));sha=hashlib.sha256(raw).hexdigest();assert raw.startswith(b'%PDF-') and sha==receipt['sha256']
 if s.get('sha256'):assert sha==s['sha256']
 else:
  assert sid=='host-kyutech-lsse-timetable2026-en-web-excerpt';js(D/'kyutech-previous-excerpt.json',old);s.update({'sha256':sha,'status':200,'content_type':'application/pdf','source_excerpt_only':False,'retrieval_method':'official_pdf_download','checked_at':receipt['checked_at'],'status_note':'official_complete_pdf_retrieved_historical_2026','label':'若松LSSE 2026/3/17英文課表（完整原件兩頁，非116）','title':'若松LSSE 2026/3/17英文課表（完整原件兩頁，非116）','previous_excerpt_archive':str((D/'kyutech-previous-excerpt.json').relative_to(R)),'pages':[{'page':i,'text':(W/f'{sid}-p{i:03}.txt').read_text()}for i in [1,2]]});shutil.copy2(W/(sid+'.pdf'),D/(sid+'.pdf'))
  js(B/f'{sid}-index-review.json',{'source_sha256':sha,'quarantined_pdf_pages':[1,2],'isolation_note_zh':'2026年3月17日LSSE課表只作2026參考，非中央116／2027核准開課；英語標題不表示全英語授課，原生表格混序不自動指定星期。'})
 prior=s.get('reading_review',{});read=sorted(set(prior.get('pages_reviewed',[]) if prior.get('source_sha256')==sha else [])|set(n['native_pages_read']));full=set(p['page']for p in s['pages'])<=set(read)
 s['reading_review']={**prior,'source_sha256':sha,'pages_reviewed':read,'full_document_read':full,'reviewed_at':now,'scope':n['document_year_scope']+('；全物理頁原生核讀'if full else '；只核讀列出引用頁，未全文讀'),'note_zh':n['note_zh']}
 s['reading_status']='full_native_reviewed' if full else 'cited_pages_native_reviewed';s['source_read_scope_note_zh']=s['reading_review']['scope']+'；不代表中央116接收核准、名額或外鏈已讀。';s['reuse_license_note']='官方公開來源僅作查核與引用；未取得頁內照片獨立授權，不轉作校園照片。'
 visual=copy.deepcopy(s.get('visual_review',{}));renders=[]
 for i in n['native_pages_read']:shutil.copy2(W/f'{sid}-p{i:03}.txt',D/'selected-native-text'/f'{sid}-p{i:03}.txt')
 for i in n['visual_pages_read']:
  p=W/f'{sid}-p{i:03}.png';q=D/'source-pages'/p.name;shutil.copy2(p,q);renders.append({'pdf_page':i,'path':str(q.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 if renders:
  visual_pages=sorted(set(visual.get('pdf_pages_reviewed',[]) if visual.get('source_sha256')==sha else [])|set(n['visual_pages_read']));visual.update({'source_sha256':sha,'pdf_pages_reviewed':visual_pages,'full_document_read':set(p['page']for p in s['pages'])<=set(visual_pages),'reviewed_at':now,'method':'實際view_image原頁圖核對；不以已轉圖計已讀','rendered_pages':visual.get('rendered_pages',[])+renders,'latest_note_zh':n['note_zh']});s['visual_review']=visual;js(B/f'{sid}-visual-review.json',visual)
 ledger.append({'source_id':sid,'source_url':s['url'],'source_sha256':sha,'retrieval_receipt':receipt,'pages_this_review':n['native_pages_read'],'visual_pages_this_review':n['visual_pages_read'],'native_full_document_read':full,'year_scope':n['document_year_scope'],'reviewed_at':now,'note_zh':n['note_zh'],'license_scope':s['reuse_license_note']})
# Keep the old HCM historical excerpt intact and archive the bounded failed refresh.
hcm=byid['host-hcm-iex-2018-browser'];hcm['latest_original_retrieval_attempt']={'checked_at':now,'retrieved_original':False,'reason_zh':'官方同址HTTP200是HTML cookie challenge，正常ChromiumTLS失敗；未繞過TLS。保留既有2018短摘錄，無原件SHA，不作完整當期表。','receipt':json.load(open(W/'host-hcm-iex-2018-browser.pdf.source.json')),'browser_receipt':json.load(open(W/'hcm-browser-receipt.json'))};js(D/'blocked-hcm-original.json',hcm['latest_original_retrieval_attempt'])
# Explicit identity split; never change shared matcher or infer identity from Chinese homonyms.
mapping=json.load(open(B/'source-map-candidates.json'));before=[];identities=[]
splits={
'ncu-074':('Spain','Universitat Ramon Llull / La Salle','Carrer Claravall 1, 3, Barcelona; url.edu; salle.url.edu','1mbJ4AXfVhm8cX7JoSPkuJ2hPckOPwYjE',['1HYmdDx6sva1ynGq5AmpXp49nH46kxjpZ','1wBS543cWlwXllG7O_07PAcEUBODZkfna'],'1wBS543cWlwXllG7O_07PAcEUBODZkfna'),
'ncu-198':('Malaysia','Universiti Tunku Abdul Rahman / UTAR','Kampar Perak / Sungai Long, Malaysia; utar.edu.my','1QafOF_bzLZOwxZxJZ6SQf7V3d5zLyYgb',['11uwy88MmxrQHRjbOfm4FVh7u6i5yYwgy','1WsTInUxjDxZiXk65Q2Kh4JGhyrYcdmiF','1FZYems1C2SyG5Yevthc2bqTxJKk-Ejxy','1cWQi5Dl3m374SttYuL6C0IZ0_sALdB50'],'1cWQi5Dl3m374SttYuL6C0IZ0_sALdB50')}
for row in mapping:
 if row['row_id']not in splits:continue
 rid=row['row_id'];country,school,identity,folder,files,intro=splits[rid];before.append(copy.deepcopy(row));row['files']=files;row['matched_entries']=[e for e in row['matched_entries']if e['id']in [folder,intro]];row['matching_status']='manually_verified_identity_country_scope_pending';row['identity_review']={'checked_at':now,'country':country,'school':school,'identity_evidence':identity,'method':'逐份原件校名、國別、地址、官方網域與母校folder核對；不是中文相同自動套用','applicability':'只確認來源身份；2024／2025–26與無年簡介不升116當期'}
 s=byid[intro];receipt=json.load(open(W/(intro+'.pdf.source.json')));sha=hashlib.sha256((W/(intro+'.pdf')).read_bytes()).hexdigest();assert sha==s['sha256']==receipt['sha256'];assert len(s['pages'])==1
 s['reading_review']={'source_sha256':sha,'pages_reviewed':[1],'full_document_read':True,'reviewed_at':now,'scope':'母校未標年度一頁簡介，原生與原圖已讀；僅歷史參考及校名國別辨識'};p=W/f'{intro}-p001.png';q=D/'source-pages'/p.name;shutil.copy2(p,q);s['visual_review']={'source_sha256':sha,'pdf_pages_reviewed':[1],'full_document_read':True,'reviewed_at':now,'method':'原生加view_image實際看圖','rendered_pages':[{'pdf_page':1,'path':str(q.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}],'note_zh':identity+'；馬來西亞保險嵌圖未標年，不當2027移民政策。'};js(B/f'{intro}-visual-review.json',s['visual_review']);(D/'selected-native-text'/f'{intro}-p001.txt').write_text(s['pages'][0]['text'])
 identities.append({'row_id':rid,**row['identity_review'],'sources':[{'id':sid,'url':byid[sid]['url'],'sha256':byid[sid]['sha256'],'read_scope':'one-page original native and visual'if sid==intro else 'page 1 identity header only; remaining content unread'}for sid in files],'receipt':receipt})
js(B/'source-map-candidates.json',mapping);js(D/'identity-before.json',before);js(D/'identity-review.json',identities)
for p,pack in packs.items():gz(B/p,pack)
js(W/'reading-notes.json',notes);js(D/'reading-ledger.json',{'base_sha':BASE,'checked_at':now,'items':ledger,'blocked_sources':1,'blocked_cited_parts':2});js(D/'reading-notes.json',notes)
print({'reviewed_sources':len(ledger),'cited_parts_read':sum(len(x['pages_this_review'])for x in ledger),'identity_rows_fixed':len(identities),'new_source_images':len(list((D/'source-pages').glob('*.png')))})
