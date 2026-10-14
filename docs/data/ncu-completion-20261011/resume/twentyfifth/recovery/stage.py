from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,base64,shutil,copy,subprocess
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentyfifth');S=R/'sources/ncu/2026-10-11';D=R/'docs/data/ncu-completion-20261011/resume/twentyfifth';BASE='46275e246b024c3a15f7e2bf6b8ac6576315f531'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==BASE
D.mkdir(exist_ok=True);(D/'source-pages').mkdir(exist_ok=True);now=datetime.now(timezone.utc).isoformat()
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def gz(p,x):p.write_bytes(gzip.compress(json.dumps(x,ensure_ascii=False).encode(),mtime=0))
sources=json.load(gzip.open(S/'host-web-evidence.json.gz'));assert len(sources)==793
records=json.load(open(S/'reviewed-host-records.json'));before=copy.deepcopy(records);notes=json.load(open(W/'reading-notes.json'));ledger=[];rawpack=[];byid={s['id']:s for s in sources};ids={}
for n in notes:
 slug=n['slug'];rid=n['row_id'];p=W/n['filename'];ext=p.suffix[1:];meta=json.load(open(p.with_suffix(p.suffix+'.source.json')));sha=hashlib.sha256(p.read_bytes()).hexdigest();assert sha==n['source_sha256']==meta['sha256'] and meta['status']==200
 sid=f'{rid}-resume25-{slug}';assert sid not in byid;ids[slug]=sid
 template=next(s for s in sources if rid in s.get('row_ids',[]))
 if ext=='pdf':pages=[{'page':i,'text':(W/f'{slug}-p{i:02}.txt').read_text()}for i in n['native_pages_read']]
 elif ext=='doc':pages=[{'page':None,'text':'\n'.join((W/f'{slug}-p{i:02}.txt').read_text()for i in n['native_pages_read'])}]
 else:pages=[{'page':None,'text':(W/f'{slug}.txt').read_text()}]
 s={'id':sid,'school_name':template['school_name'],'country':template['country'],'row_ids':[rid],'url':meta['url'],'final_url':meta.get('final_url',meta['url']),'kind':'host_official_candidate','purpose':'土耳其兩校版本差異、錯向表單與生活申請程序逐件核讀','label':slug+'（'+n['document_year_scope']+'）','authority_kind':'partner_university','checked_at':meta['checked_at'],'status':200,'sha256':sha,'content_type':meta['content_type'],'format':ext,'pages':pages,'links':json.load(open(W/(slug+'-links.json')))if ext=='html'else[],'applicability':n['document_year_scope']+'；中央116校別、名額與方案仍未核实。','reading_status':'selected_passages_reviewed'if ext=='html'else'full_visual_and_native_reviewed','reading_review':{'source_sha256':sha,'pages_reviewed':[p['page']for p in pages],'full_document_read':n['full_document_read'],'reviewed_at':now,'review_note':' '.join(t for _,t in n['page_notes']),'year_scope':n['document_year_scope']},'reuse_license_note':n['license_scope']}
 renders=[]
 for i in n['visual_pages_read']:
  png=W/f'{slug}-p{i:02}.png';dest=D/'source-pages'/png.name;shutil.copy2(png,dest);renders.append({'page':i,'page_kind':'local_doc_conversion'if ext=='doc'else'original_pdf','path':str(dest.relative_to(R)),'sha256':hashlib.sha256(png.read_bytes()).hexdigest()})
 if ext!='html':
  s['visual_review']={'source_sha256':sha,'pdf_pages_reviewed':n['visual_pages_read']if ext=='pdf'else[],'converted_pages_reviewed':n['visual_pages_read']if ext=='doc'else[],'full_document_read':True,'reviewed_at':now,'method':'原生文字全文與逐頁view_image核對；Word另以LibreOffice本地轉換頁，無原生固定PDF頁碼；非OCR。','rendered_pages':renders,'page_notes_zh':{str(i):t for i,t in n['page_notes']}}
 if ext=='doc':
  converted=W/'doc-rendered'/f'{slug}.pdf';dest=D/'source-pages'/converted.name;shutil.copy2(converted,dest);s['document_format']='doc_no_fixed_pdf_pages';s['visual_review']['converted_pdf_sha256']=hashlib.sha256(converted.read_bytes()).hexdigest();s['visual_review']['converted_pdf_path']=str(dest.relative_to(R))
 sources.append(s);byid[sid]=s;records[rid]['source_ids'].append(sid);records[rid]['checked_at']=now
 rawpack.append({'source_id':sid,'receipt':meta,'encoding':'base64','body':base64.b64encode(p.read_bytes()).decode()})
 ledger.append({**n,'source_id':sid,'retrieved_at':meta['checked_at'],'reviewed_at':now,'current_116_approval':False,'rendered_pages':renders})
LIMIT='中央116校別、名額、方案及實際校區仍未核實；僅保留原年參考，不啟用期限提醒。'
changes=[]
def field(rid,key,points,refs,unresolved=LIMIT,append=False,gap_only=False):
 r=records[rid];old=copy.deepcopy(r['fields'].get(key));p=points if isinstance(points,list)else[points];rr=[{'id':ids[slug],'page':page}for slug,page in refs]
 if append and old:p=old['points']+p;rr=old['sources']+rr
 v={'points':p,'sources':rr,'unresolved':unresolved}
 if gap_only:v['gap_only']=True
 r['fields'][key]=v;changes.append({'row_id':rid,'field':key,'previous':old,'updated':v})
def doc(name,slug,page=None,condition=None,signatures=None):
 d={'name':name,'source_urls':[byid[ids[slug]]['url']+(f'#page={page}'if page is not None else'')],'needs_confirmation':True,'stage':'student_application','applicability_status':'reference_only','applicability_note':LIMIT}
 if condition:d.update(conditional=True,condition=condition)
 if signatures:d['signatures']=signatures
 return d
rid='ncu-093';web='altinbas-incoming';old='altinbas-handbook';new='altinbas-handbook-2024-link'
records[rid]['applicability']='官網更新2024/11/5、兩版手冊頁尾2023/3/13與2023/9/20；網址2024不作版年。'+LIMIT
field(rid,'city','兩版2023手冊列三校區：蓋雷泰佩以管理、經濟社科、藝術法律等為主；馬赫穆特貝以外語、工程理科與職業學校為主；巴克爾柯伊以醫藥牙與健康為主。原代表位置不代表每名學生上課地點，需按接收院系確認，未以宿舍或其他校區取代既有座標。',[(new,8),(new,12)],append=True)
field(rid,'eligibility','外校官網要求母校先選拔及提名；大學部至少完成一年、GPA至少2.20/4，研究生至少完成一學期、GPA至少2.50/4。學院與名額仍依雙邊協議；頁面泛述秋春各2人、全年4人，不能當成中央116名額。',[(web,None)],append=True)
field(rid,'language','官網列B2或TOEFL PBT550／CBT213／iBT80，測驗須在兩年內。英語母語者或已在英語國家就讀高等教育者可免上述測驗；派出學校以英語授課者仍須母校正式英語能力證明信，不是免所有證明。該頁未另註適用學年，中央116及個人豁免需再確認。',[(web,None)],append=True)
field(rid,'host_deadline','官網提名及申請窗口：秋季／全年6月1日至7月1日，春季10月1日至11月1日，未另註學年。2023/9/20手冊寫6月初至7月初、10月初至11月初；較舊2023/3/13版則是6月中至7月中、10月底至11月底，兩版不可混用，也不改標為中央116期限。',[(web,None),(new,6),(old,6)])
field(rid,'host_documents','正式提名後校方寄網申通知，學生依系統提交；公開正文沒有完整附件清單。可確認英語能力證明及出發前學習協議，協議由相應系所交換協調人簽；錄取信在接受後由校方寄發，不能列為初申前已須持有。到後居留的住宿證明、交換中更課及離校退宿表均不是初申附件。',[(web,None)],unresolved='已核部分文件及階段，完整初申清單、系統通知、116適用仍待核。',gap_only=True)
d=doc('英語能力證明（測驗或符合條件的母校正式證明信）',web,condition='是否免測驗依英語母語或英語國家高等教育條件；母校英授仍需正式證明信，116豁免另核。');records[rid]['host_documents']=[d]
d=doc('出發前學習協議（不等於初申已完成全部附件）',web,signatures=['相應系所交換協調人']);d['stage']='post_offer';records[rid]['host_documents'].append(d)
field(rid,'courses','官網概述一般每學期5課、約20校內學分相當30 ECTS；交換生沒有固定課數要求，建議至少3課，負荷及抵免由母校核准。當期開課清單在學期初提供，先修及容量可能限制選課，跨系也須母校同意；學術協調人協助註冊，加退選週後不能任意更課。手冊學院列表不是中央全院系開放或每門英授保證。',[(web,None),(new,6),(new,7)])
field(rid,'housing','2023兩版手冊列馬赫穆特貝校區宿舍，對提出申請且按時付費的交換生寫有條件保證；官網另明寫床位有限、由宿舍管理處處理。保留差異，不宣稱中央116保證住宿；校外住宿由學生自行安排，可向學生組織詢問。宿舍房價、押金、申請期限與當期房源仍待核。',[(old,9),(new,9),(web,None)])
field(rid,'cost','2023兩版手冊分列每月私人住宿350歐元、交通5歐元、一般餐食與社交150歐元。350歐元明確不含學生宿舍，不是宿舍月租，也不是每月全部生活費；三項是舊版估算，未把它們加總冒充校方核定總額或116現價。',[(old,10),(new,10)],unresolved='2023分項預算僅原年參考，116宿舍費、實際生活費與其他支出待核。')
field(rid,'tuition','Global Exchange官網說明依大學間雙邊協議免接收校學費，但方案本身不提供獎學金。此敘述不代表中央學費免繳，也不保證沒有住宿、保險或其他費用；中央116具體方案須再核。',[(web,None)])
field(rid,'transport','2023手冊提到三校區間免費接駁及學生市區交通折扣；免費跨校區車不等於全市交通免費。未核到116班次或票價，應先按接收院系與住址確認通勤。',[(new,8),(new,10)])
field(rid,'arrival','2023手冊說迎新在開課前一週，官網介紹迎新但未列當期日期。手冊Buddy須抵達前登記，官網則說每名入境學生配對，申請方式須以當期通知確認；可參加土耳其語課但未說免費。離校須退宿、還書等，成績全登錄可能到最後考試後一個月，寄送另需數週，不能保證考完立刻取得成績單。',[(new,10),(new,11),(web,None)])
# Bingol's wrong-direction originals remain auditable, but are excluded from requirements.
rid='ncu-094';web='bingol-student-documents';la='bingol-learning';app='bingol-application';att='bingol-attendance';course='bingol-course-catalogue'
records[rid]['applicability']='母校未年介紹、賓格爾官方文件索引與未年Word表逐件方向核對；錯連出境表不作初申。'+LIMIT
for slug in [app,att]:
 byid[ids[slug]]['requirement_use']='excluded_from_initial_application'
 byid[ids[slug]]['direction_review']='索引列在入境欄，但正文為OUTGOING或your institution措辭；不當中央incoming初申要求。'
field(rid,'language','接收校為賓格爾的學習協議只提供A1至母語程度勾選欄，沒有預設最低值；不能以空白自評欄取消母校B2。錯連的出境申請表所列英法德能力自評也不是中央赴賓格爾的門檻。',[(la,None),(app,None)],append=True)
field(rid,'host_documents','官方索引的入境欄雖連到申請表，下載正文卻明寫OUTGOING，並有三所目的校志願及土耳其國籍預填，排除作中央赴賓格爾初申表。可確認另一學習協議的接收校為Bingöl、代碼TR BINGOL01；交換前表由學生與兩校負責人確認，但完整初申清單仍待核。到離境證明有向對方學校證明本校學生的措辭，亦非初申附件。',[(web,None),(app,None),(la,None),(att,None)],unresolved='已確認接收方學習協議；完整入境初申表、附件、期限、當期通知仍待核，錯向文件已排除。',gap_only=True)
d=doc('出發前學習協議（接收校Bingöl；完整初申清單仍待核）',la,signatures=['學生','派出母校負責人','賓格爾接收負責人']);d['stage']='post_offer';records[rid]['host_documents']=[d]
field(rid,'courses','官方課程索引按院系列經管、文理、工程、神學、健康、農學、獸醫及運動等連結；目前核讀到院系目錄，尚未逐課核實學分、授課語言、當期開課或中央開放範圍。學習協議須分外校修課與母校認列；交換中更課、交換後成績及回校抵免欄不要求初申時已完成。',[(course,None),(la,None)],unresolved='有官方院系入口及學習協議，個別課程、ECTS、語言與116開放仍待核。',gap_only=True)
field(rid,'arrival','學習協議的交換中變更與交換後成績、回校認列有各自階段及簽署欄，不能列為初申已完成附件。官方所連到離境證明需填實際到達與離開日期，正文方向仍有疑點；未取得116迎新或必到日。',[(la,None),(att,None)],unresolved='只有文件階段，迎新、必到日期與116適用待核。',gap_only=True)
js(S/'reviewed-host-records.json',records);gz(S/'host-web-evidence.json.gz',sources);gz(S/'resume-twentyfifth-original-responses.json.gz',rawpack);js(D/'reading-ledger.json',{'checked_at':now,'base_sha':BASE,'items':ledger});js(D/'field-reconciliation.json',changes);js(D/'added-host-records.json',{k:records[k]for k in ['ncu-093','ncu-094']});js(D/'identity-review.json',{'ncu-093':'Altinbas校徽與MahmutbeyDilmenler26互證；三校區按學院分，不更換既有代表點。兩PDF頁尾2023不同版，不依URL推學年。','ncu-094':'LA接收Bingol/TRBINGOL01核實；索引錯連OUTGOING申請表及方向有疑的到離境函排除初申。','current_116_approval':False});shutil.copy2(W/'altinbas-two-editions-comparison.json',D/'altinbas-two-editions-comparison.json')
print({'sources':len(sources),'reading_records':sum(bool(s.get('reading_review'))for s in sources),'new_hosts':0,'updated_hosts':2,'updated_fields':len(changes),'previous_gap_only_resolved_to_reference':sum(bool((x['previous']or{}).get('gap_only'))and not x['updated'].get('gap_only')for x in changes),'documents':5,'original_pdf_pages':24,'local_word_rendered_pages':6,'html_main_passages':3})
