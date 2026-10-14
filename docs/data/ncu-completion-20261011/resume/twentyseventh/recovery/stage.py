from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,base64,shutil,copy,subprocess
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentyseventh');S=R/'sources/ncu/2026-10-11';B=R/'sources/ncu/2026-10-08';D=R/'docs/data/ncu-completion-20261011/resume/twentyseventh';D.mkdir(exist_ok=True);(D/'source-pages').mkdir(exist_ok=True)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='573126cce6def44dc4c35c7c0f8ce9b59e093a0b'
now=datetime.now(timezone.utc).isoformat()
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def gz(p,x):p.write_bytes(gzip.compress(json.dumps(x,ensure_ascii=False).encode(),mtime=0))
receipts={r['source_id']:r for r in json.load(open(W/'fetch-receipts.json'))};pack=json.load(gzip.open(B/'drive-evidence.json.gz'));byid={s['id']:s for s in pack};notes=json.load(open(W/'reading-notes.json'));mapping=json.load(open(W/'candidate-identity-mapping.json'));rows={sid:r['row_id']for r in mapping for sid in r['files']};ledger=[];responses=[]
for n in notes:
 sid=n['source_id'];s=byid[sid];pages=list(range(1,len(s['pages'])+1));assert n['native_pages_read']==n['visual_pages_read']==pages
 raw=(W/f'{sid}.pdf').read_bytes();assert hashlib.sha256(raw).hexdigest()==s['sha256']==n['sha256']==receipts[sid]['sha256']
 renders=[]
 for page in pages:
  p=W/f'{sid}-p{page:02}.png';q=D/'source-pages'/p.name;shutil.copy2(p,q);renders.append({'pdf_page':page,'path':str(q.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 s['reading_status']='full_visual_and_native_reviewed';s['reading_review']={'source_sha256':s['sha256'],'pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'review_note':'5份10頁第二十七批全篇原生與原圖核讀；方案、年度、學科限制與原件衝突保留。'}
 s['visual_review']={'source_sha256':s['sha256'],'pdf_pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'method':'原生全文與逐頁view_image人工核對；非OCR','rendered_pages':renders,'page_notes_zh':{str(p):v for p,v in n['page_notes']}}
 s['reuse_license_note']='母校公開官方原件僅供查核；未取得頁內照片獨立開放授權，不轉作校景。'
 if n.get('selected_passages'):
  s['visual_review']['page_transcriptions']=n['selected_passages'];s['visual_review']['include_native_with_selected_passages']=True
  s['page_transcriptions']=n['selected_passages']
  js(B/f'{sid}-visual-review.json',s['visual_review'])
 ledger.append({'source_id':sid,'row_id':rows[sid],'source_url':s['url'],'source_sha256':s['sha256'],'retrieved_at':receipts[sid]['receipt']['checked_at'],'reviewed_at':now,'document_year_scope':n['document_year_scope'],'pages_reviewed':pages,'native_full_read':True,'native_text_limitations':n.get('native_text_limitations'),'blank_visual_pages':n.get('blank_visual_pages',[]),'selected_passages':n.get('selected_passages',[]),'visual_full_read':True,'page_notes_zh':n['page_notes'],'current_116_approval':False,'license_scope':s['reuse_license_note'],'rendered_pages':renders})
 responses.append({'source_id':sid,'receipt':receipts[sid]['receipt'],'encoding':'base64','body':base64.b64encode(raw).decode()})
gz(B/'drive-evidence.json.gz',pack);gz(S/'resume-twentyseventh-original-responses.json.gz',responses);js(D/'fresh-fetch-receipts.json',list(receipts.values()));js(D/'reading-ledger.json',{'checked_at':now,'base_sha':'573126cce6def44dc4c35c7c0f8ce9b59e093a0b','items':ledger})
js(D/'identity-review.json',mapping)
records=json.load(open(S/'reviewed-host-records.json'));base=json.load(open(B/'reviewed-host-records.json'));before=copy.deepcopy(records);changes=[]
LIMIT='中央116校別、名額、方案與實際校區仍未核實；以下依原件學年作參考，不啟用期限提醒。'
for sid,rid in rows.items():
 if rid not in records:records[rid]={'source_ids':[],'fields':{},'applicability':'中央公開未年學校介紹，僅歷史參考。','host_documents':[]}
 if sid not in records[rid]['source_ids']:records[rid]['source_ids'].append(sid)
 records[rid]['checked_at']=now
 records[rid]['applicability']+='；第二十七批核讀'+next(n['document_year_scope']for n in notes if n['source_id']==sid)+'。'+LIMIT

def field(rid,key,points,sid,pages,unresolved=LIMIT,append=True,gap_only=False):
 r=records[rid];old=copy.deepcopy(r['fields'].get(key,base.get(rid,{}).get('fields',{}).get(key)));p=points if isinstance(points,list)else[points];refs=[{'id':sid,'page':page}for page in pages]
 if append and old:p=old['points']+p;refs=old['sources']+refs
 v={'points':p,'sources':refs,'unresolved':unresolved}
 if gap_only:v['gap_only']=True
 r['fields'][key]=v;changes.append({'row_id':rid,'field':key,'previous':old,'updated':v})
def doc(name,sid,page=1,condition=None,signatures=None,stage='student_application'):
 d={'name':name,'source_urls':[byid[sid]['url']+f'#page={page}'],'needs_confirmation':True,'stage':stage,'applicability_status':'reference_only','applicability_note':LIMIT}
 if condition:d.update(conditional=True,condition=condition)
 if signatures:d['signatures']=signatures
 return d
rid='ncu-012';sid='1q5M5_iYOGRTDESA9MXtnHvocmxg2ONAr'
field(rid,'eligibility','中央未年介紹限大學三年級以上、只Global Engineering Program；「適合資管系及機械系」是適合對象，不自行改成僅限兩系。校徽出現Casablanca不代表中央協議開放摩洛哥校區。',sid,[1])
field(rid,'language','中央未年介紹列英語B2及法語A2，兩者並列；既有2024–25外校表在B1／B2上的差異仍保留，沒有逕選較低值或取消法語要求。本人116適用以兩校確認。',sid,[1])
field(rid,'study_period','中央未年介紹明列僅秋季一學期，9月至12月；不能因外校通用資料列春季，就推定中央本方案可以春季或一年。',sid,[1])
field(rid,'courses','中央未年介紹限定Global Engineering Program，需依該課程組及中央核定方案選課；外校其他英法語路徑不自動對本協議開放。',sid,[1])
field(rid,'housing','中央未年介紹說沒有自己的宿舍，只提供外部住宿名單；6月1日／12月1日在住宿段落，是住宿相關日期，不移成交換入學截止或保證配房。',sid,[1])
rid='ncu-073';sid='18uF0TkNzOklcOqAuFibsmrAbeApPkBuW'
field(rid,'city','中央未年介紹的接收單位為西班牙馬德里Comillas ICAI，地址Alberto Aguilera街23號；不同學院及校區的課程位置仍須逐課核對。',sid,[1])
field(rid,'eligibility','中央未年介紹列大學部與研究所，限中央工學院及資电學院學生申請；ICAI的工業工程及電信工程領域不能擴成Comillas全校無限制。',sid,[1])
field(rid,'language','中央未年介紹用語是強烈建議英語達CEFR B2；保留recommended語氣，不改成外校已證實硬性最低。中央校內正式語檢文件仍須依母校簡章，116實際條件另核。',sid,[1])
field(rid,'study_period','中央未年介紹第一學期約8月底至12月22日，第二學期約1月7日至5月底，包含考試；均是約期與未年資料，不生成當期截止或確定離校日。',sid,[1])
field(rid,'courses','介紹中的ICAI有工業工程（機械、電機及電子）與電信工程兩主要領域；未附逐課目錄、選課學分或最新開課名額，不能保證任一課可修。',sid,[1])
field(rid,'insurance','中央未年介紹要求全體學生綜合醫療保險，到校後向國際處交保單副本才可註冊課程；非歐盟學生須涵蓋全期疾病、住院、意外及民事責任。此為舊校方要求，當期保障及保費另核。',sid,[1])
field(rid,'host_documents','本介紹只確認到校註冊時須向國際處出示保單副本，沒有完整初申附件；不能把到校保單或常見護照、成績單自行當成已核初申清單。',sid,[1],gap_only=True,unresolved='初申完整清單、表格、簽章與116當期通知未列於本原件。')
records[rid]['host_documents']=[doc('綜合醫療保險保單副本（到校註冊課程時向國際處出示）',sid,stage='post_offer')]
field(rid,'host_deadline','本未年介紹列學期約期，沒有提名或學生申請截止；學期開始日不是截止日。',sid,[1],gap_only=True,unresolved='提名與學生申請截止未公布在此原件，仍須讀當期官方通知。')
field(rid,'housing','本介紹未提供宿舍申請、房型、租金或住宿保證；馬德里生活概覽不能替代住宿規則。',sid,[1,2],gap_only=True,unresolved='住房類型、申請日、租金及保證條件未核。')
field(rid,'cost','本介紹只有馬德里生活及交通概覽，未列完整生活預算或分項價格；不以一般城市估價代替校方原件。',sid,[2],gap_only=True,unresolved='每月預算及幣別價格週期未列，後續官方來源待讀。')
field(rid,'transport','未年介紹列機場距市區約12公里及公車、地鐵、計程車等交通方式；未提供當期票價或班表，不能當即時路線安排。',sid,[2])
rid='ncu-100';sid='1K6mXo5lNNese80U4L9TA0QLoQ_UTYuw8'
field(rid,'eligibility','中央未年Douglas介紹限大學部；中央歷史項目的一學期限制仍需保留。不能用一般訪問學生入學資格推定研究所亦可交換。',sid,[1])
field(rid,'language','中央未年介紹列TOEFL83（未註制式）、IELTS6.5或CEFR C1；不取消已讀官網IELTS各科6.0要求，也不把ELLA語言課程的4.5門檻套到一般學術交換。',sid,[1])
field(rid,'courses','中央未年介紹說健康及人類／社會服務課程不開放；當代藝術（音樂及視覺藝術）與運動科學須取得許可。秋冬課程較多、夏季較少；不是保證所有列出的科目有名額。',sid,[1])
field(rid,'study_period','中央未年介紹秋季9月至12月、冬季1月至4月；舊學期月份不等於本期實際開放或精確考試日。',sid,[1])
field(rid,'housing','中央未年介紹明列無校內住宿，可選寄宿家庭或自行租屋，國際處協助找房；協助不等於床位或房價保證。',sid,[2])
field(rid,'cost','中央未年介紹估每學期5500–7500加幣生活費，會依住宿而變；這是每學期、不是每月，也不是包含所有學費的當期總價。與官網較新按月房租及每週餐食分項分開保留，不混成單一新預算。',sid,[2])
field(rid,'tuition','這份中央介紹檔名標付費、內文卻泛稱交換；不能僅依檔名推翻已讀官方Exchange免外校學費與Visiting付費的區別。中央116究竟適用哪個方案仍未確認，不能保證本項免費或逕定一律付費。',sid,[1,2])
rid='ncu-109';sid='1lvagqWUlDqhK_qQ7Pv9TH2zpIaw716ON'
field(rid,'city','原件為美國亞利桑那大學Tucson，地址Arizona85721；不是Flagstaff的北亞利桑那大學，兩校資產與規則不能互用。',sid,[1])
field(rid,'eligibility','中央未年介紹只限大學部、GPA2.5以上，不開放管理學院學生。圖片語言表雖有Graduate列，也不能用該列推定研究生可申請本方案。',sid,[1])
field(rid,'language','人工核讀未年原頁影像表：大學部Internet-based TOEFL70、工程79；IELTS6.0、工程6.5；PTE Academic53。研究生列僅保存原文，本方案限大學部不套該列。這些是舊表分數，不保證116當期測驗制式及門檻。',sid,[1])
field(rid,'study_period','中央未年介紹秋季8月至12月、春季1月至5月；沒有確切學年、報到或考試日，不視為116已核校曆。',sid,[1])
field(rid,'tuition','中央115目錄另將此列為自費項目；本未年介紹卻只連到exchange-students入口，沒有解釋與付費方案的對應或費額。保留方案未核，不能以連結名稱抵銷母校自費註記或認定外校免學費。',sid,[1],gap_only=True,unresolved='母校歷史自費註記已保留；外校方案、費額、折扣與116適用尚待確認。')
field(rid,'host_documents','本介紹沒有初申文件清單；第2物理頁已實看為全空白，不捏造漏頁或常見附件。',sid,[1],gap_only=True,unresolved='外校完整初申文件及表格未列，需續查相同付費方案。')
field(rid,'host_deadline','本介紹只有學期月份，沒有提名或學生申請截止。',sid,[1],gap_only=True,unresolved='外校方案與兩階段截止均未核。')
field(rid,'housing','本介紹沒有宿舍、租金、申請或住宿保證內容。',sid,[1],gap_only=True,unresolved='同一付費方案的住房選項及價格待查。')
field(rid,'cost','本介紹沒有每月生活預算，不能由GPA、語言表或自費標籤推導費額。',sid,[1],gap_only=True,unresolved='生活分項及計價週期待查。')
rid='ncu-111';sid='1hqaCisXb0JKE2xJnmyzffbaoMi4mdQQv'
field(rid,'city','中央未年介紹對應UCI繼續教育方案及Irvine校內Building I #238、Pereira at Brandywine辦公位置；不是宣稱所有課程都在該棟或另改地球校址。',sid,[1])
field(rid,'eligibility','中央未年介紹限大學二年級以上，付費方案只可申請ACP系列或ASAP；不是一般本科免費交換。成績行原件寫「GAP 3.0」，疑義保留，不靜默改字後做自動資格判斷。',sid,[1])
field(rid,'language','中央未年介紹列TOEFL iBT80、IELTS6.5或TOEIC685；該行另寫GAP3.0，原件拼法及真正GPA規則需校方確認，未自改或保證當期有效。',sid,[1])
field(rid,'study_period','中央未年介紹秋季9月至12月、春季3月至6月；本頁以Semester稱學期，費用頁卻使用quarter，週期應各照原文，不擅統一。',sid,[1,2])
field(rid,'courses','中央未年介紹限ACP或ASAP，列12學分範圍；超過12學分須額外付學分費，不是禁止選第13學分，也不保證任一課程可選。',sid,[1])
field(rid,'tuition','中央未年介紹須繳中央及UCI學雜費；舊列15%學雜費折扣即85折，只針對學雜費，不把食宿、保險及個人支出全打85折。費額依UCI公告，超過12學分另繳，116優惠及總額未核。',sid,[1])
field(rid,'cost','未年原件第2頁圖片列費用未含機票、接送、醫保、SEVIS及簽證、食宿、課本、付費活動及個人支出。沒有完整月生活預算；每季585美元只是舊保險報價，不是每學期學費或當期生活總額。',sid,[2],gap_only=True,unresolved='已核哪些項目不包含，完整生活預算及116費額仍未核。')
field(rid,'insurance','未年原件第1頁說需購買強制健康保險；第2頁影像卻允許自備符合UCI保障要求的保單，或使用UCI每季585美元保險。保留兩頁說明差異，不改成強制購買UCI方案；每季quarter不是每學期semester，價格及豁免條件須更新確認。',sid,[1,2])
field(rid,'transport','未年原件第2頁列接機須事先安排且另外付費：LAX洛杉磯機場90美元、SNA橙郡機場50美元。這是歷史單項報價，未保證目前價格、單程往返範圍或已訂妥接送。',sid,[2])
field(rid,'housing','未年原件說食宿依個人實際支出，費用未包含房租與餐食；沒有可選宿舍、住房保證或租價，不能把未含食宿讀成免費住宿。',sid,[1,2],gap_only=True,unresolved='住宿方案、申請與價格未列，須核相同ACP／ASAP方案。')
field(rid,'host_documents','這份兩頁介紹沒有ACP／ASAP完整初申附件，不能僅凭保險、簽證費排除項目建立必繳文件表。',sid,[1,2],gap_only=True,unresolved='方案明確但初申清單、表格及簽章待查。')
field(rid,'host_deadline','本介紹未列提名與學生截止，秋春月份不能代替申請窗口。',sid,[1],gap_only=True,unresolved='ACP／ASAP當期截止與116提名安排待查。')
js(S/'reviewed-host-records.json',records);js(D/'field-reconciliation.json',changes);js(D/'added-host-records.json',{rid:records[rid]for rid in rows.values()})
print({'reviewed_docs':5,'physical_pdf_pages':10,'updated_hosts':5,'new_hosts':3,'updated_fields':len(changes),'previous_gap_only_with_reference':sum(bool((x['previous']or{}).get('gap_only'))and not x['updated'].get('gap_only')for x in changes)})
