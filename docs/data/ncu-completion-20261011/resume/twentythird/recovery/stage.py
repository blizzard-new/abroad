from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,base64,shutil
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentythird');S=R/'sources/ncu/2026-10-11';B=R/'sources/ncu/2026-10-08';D=R/'docs/data/ncu-completion-20261011/resume/twentythird';D.mkdir(exist_ok=True);(D/'source-pages').mkdir(exist_ok=True)
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
 s['reading_status']='full_visual_and_native_reviewed';s['reading_review']={'source_sha256':s['sha256'],'pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'review_note':'7頁第二十三批全篇原生與原圖核讀；母校院別、學程與外校一般指引分列，原年、校區、條件與原件錯誤保留。'}
 s['visual_review']={'source_sha256':s['sha256'],'pdf_pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'method':'原生全文與逐頁view_image人工核對；非OCR','rendered_pages':renders,'page_notes_zh':{str(p):v for p,v in n['page_notes']}}
 s['reuse_license_note']='母校公開官方原件僅供查核；未取得頁內照片獨立開放授權，不轉作校景。'
 ledger.append({'source_id':sid,'row_id':rows[sid],'source_url':s['url'],'source_sha256':s['sha256'],'retrieved_at':receipts[sid]['receipt']['checked_at'],'reviewed_at':now,'document_year_scope':n['document_year_scope'],'pages_reviewed':pages,'native_full_read':True,'visual_full_read':True,'page_notes_zh':n['page_notes'],'current_116_approval':False,'license_scope':s['reuse_license_note'],'rendered_pages':renders})
 responses.append({'source_id':sid,'receipt':receipts[sid]['receipt'],'encoding':'base64','body':base64.b64encode(raw).decode()})
gz(B/'drive-evidence.json.gz',pack);gz(S/'resume-twentythird-original-responses.json.gz',responses);js(D/'fresh-fetch-receipts.json',list(receipts.values()));js(D/'reading-ledger.json',{'checked_at':now,'base_sha':'cd24afff066d3ca877b0a594639dc5948390741e','items':ledger})
identity={
'ncu-060':'International University of Monaco校徽及Le Stella 14 Rue Hubert Clerissi 98000 Monaco對應，國別摩納哥而非法國。',
'ncu-061':'BUEM英文標題、綠校徽、vsemba.sk及Furdekova16對應既有BUEM校景與座標；正文誤貼另一所公立EUBA的簡介，混寫原件不能移植該校資格或規模。',
'ncu-093':'母校Altinba標題少末s，但ALTINBAS校徽、伊斯坦堡Mahmutbey Dilmenler Cd.No26校址對應，未確認116實際教學校區。',
'ncu-094':'Bingol University校名校徽及土耳其Bingol Merkez Universite Caddesi No1對應，底圖2016日期不是文件版年。',
'ncu-202':'Universitas HKBP Nommensen棉蘭校徽／名稱相符；母校Perintis Kemerdekaan23與2018國際處Sutomo4A是不同用途地址，不混其他同名校。舊NHU.ac.id與母校uhn.ac.id差異保留。'}
for r in mapping:r['matching_status']='human_identity_country_and_campus_reviewed';r['identity_review']=identity[r['row_id']];r['reviewed_at']=now;r['current_116_approval']=False
js(D/'identity-review.json',mapping)
records=json.load(open(S/'reviewed-host-records.json'));base=json.load(open(B/'reviewed-host-records.json'));assert not(set(rows.values())&(set(records)|set(base)))
LIMIT='中央116年度校別、名額、方案及實際校區仍待核實；以下保留原件年度參考，不啟用期限提醒。'
def record(rid,scope):
 r={'source_ids':[s for s,v in rows.items()if v==rid],'applicability':scope+'；'+LIMIT,'checked_at':now,'fields':{},'host_documents':[]};records[rid]=r;return r
def f(r,key,points,sid,pages,gap=None,gap_only=False):
 r['fields'][key]={'points':points if isinstance(points,list)else[points],'sources':[{'id':sid,'page':p}for p in pages],'unresolved':gap or LIMIT}
 if gap_only:r['fields'][key]['gap_only']=True
 return r['fields'][key]
def more(r,key,sid,pages):r['fields'][key]['sources'] += [{'id':sid,'page':p}for p in pages]
def doc(name,sid,page=1,stage='student_application',condition=None,signatures=None):
 d={'name':name,'source_urls':[byid[sid]['url']+f'#page={page}'],'needs_confirmation':True,'stage':stage,'applicability_status':'reference_only','applicability_note':LIMIT}
 if condition:d.update(conditional=True,condition=condition)
 if signatures:d['signatures']=signatures
 return d
# Four short mother sheets: observed references and explicit gaps remain distinct.
simple=[
('ncu-060','1KFPIYVbDIoM4IDmJ3Pm2ih-o22_Ftkt3','摩納哥國際大學未註年母校介紹','摩納哥，勒斯泰拉大樓、于貝爾・克萊里西街14號，郵遞區號98000；國別是摩納哥，不能歸為法國。','母校未註年介紹列大學部與研究所，校級簡介的金融、精品、行銷及運動商管等領域不是逐一確認可申交換課程。','母校未註年表列英語B2，未給可用測驗、分數換算、效期或豁免條件。','母校未註年表列秋季10/1至2月中、春季2月中至6月底，未核當期確切日期。'),
('ncu-061','1CyLDzzp-0VMZMZ2IBciWtCK8t3AzTN50','布拉提斯拉瓦BUEM未註年母校介紹，標題與正文混校','斯洛伐克布拉提斯拉瓦，富爾代科瓦街16號，郵遞區號85104；標題、BUEM綠校徽及原列官網均對應經濟與管理大學。正文卻混入另一所公立經濟大學的簡介，不能據此變更既有BUEM照片與座標。','原件在BUEM標題下列大學部與研究所，但正文混寫另一所公立經濟大學；不能移植該公立校的學生規模、公立身分或資格。學制適用須母校釐清，未視為當期已確認。','原件列英語B2，但同頁學校簡介混寫另一所公立校；須母校釐清適用機構與最新語檢規則，不能把本欄當中央116已確認。','原件列秋季9月至2月中、春季2月中至6月底；頁面混校且未註年，須核對BUEM正式校曆。'),
('ncu-093','1GMVuGNo88SEd-3PyethyuXayIvXBiRQ0','阿爾滕巴斯大學未註年母校介紹','土耳其伊斯坦堡，馬赫穆特貝、迪爾門萊爾街26號，郵遞區號34217；標題少一個字母，但ALTINBAS校徽與地址對應。這是原件校址，不代表所有交換課都在同校區。','母校未註年介紹列大學部與研究所；創校、更名與國際學生比例為校級簡介，不能用作交換名額或保證全部學院開放。','母校未註年表列英語B2，未給測驗種類、分數換算、效期或豁免規則。','母校未註年表列秋9月中至1月中、春2月中至6月中；底圖2016/3/30不是文件年份，不能把此日期當校曆版年。'),
('ncu-094','1o6WL7QFK-W1E_qqccB-zLWCcqtBW6575','賓格爾大學未註年母校介紹','土耳其賓格爾市中心，大學大道1號，郵遞區號12000；校名、校徽及地址對應，實際交換院系與教學校區仍待核。','母校未註年介紹列大學部與研究所，未細分可申院系；創校年份與地圖年份均不能作為中央116開放佐證。','母校未註年表列英語B2，未列測驗種類、分數換算、效期及豁免條件。',None)]
for rid,sid,scope,city,eligible,language,period in simple:
 r=record(rid,scope)
 f(r,'city',city,sid,[1]);f(r,'eligibility',eligible,sid,[1],gap_only=rid=='ncu-061');f(r,'language',language,sid,[1],gap_only=rid=='ncu-061')
 if period:f(r,'study_period',period,sid,[1],gap_only=rid=='ncu-061')
 else:f(r,'study_period','母校一頁介紹未列學期起迄或迎新日；待讀外校校曆，不表示官方未公布。',sid,[1],gap_only=True)
 for key,point,gap in [
 ('host_deadline','母校一頁介紹未列提名或學生申請截止；待讀外校當期程序，不表示學校不設期限。','外校提名、學生申請截止與時區待核。'),
 ('host_documents','母校一頁介紹未列外校初申附件、入口或簽章；不能以其他校的常見清單代填。','完整初申清單、表格與當期通知待核。'),
 ('housing','母校一頁介紹未列住宿房型、租價、申請日或床位保證；待讀外校住宿來源。','住宿來源尚待核讀，不宣稱官方未公布。'),
 ('cost','母校一頁介紹未列生活費及包含範圍；待讀外校預算來源，不自行估為學校核定金額。','生活費原件、費額與年度待核。')]:f(r,key,point,sid,[1],gap=gap,gap_only=True)
# HKBP: original eight categories, conditional language evidence and old cost periods.
sid='1jQ7G1tuPU0tzXsYf0JowkRLp2ouxh0bh';r=record('ncu-202','HKBP諾門森大學母校未註年介紹及2018/8/1外校資料表；後兩頁印頁1/2對应PDF實體2/3')
f(r,'city','印尼棉蘭，母校校址為獨立先驅街23號、郵遞區號20218；2018國際處另列蘇托莫街4A號、20234。兩者用途不同，不把行政窗口當唯一授課校區；舊外校資料網址字母順序與母校官網不同，未當成已確認有效的當期入口。',sid,[1,2])
f(r,'eligibility','母校與2018資料均列大學部及研究所，最低GPA 3.0/4.0或65/100；保留原件兩種標示，不自行替學生換算。外校舊表可交換一學期或一學年，中央116可申學制、時長與學院仍待核。',sid,[1,2])
f(r,'language','母校未註年表列TOEFL ITP/PBT 400、原拼「IELST 4.0」、TOEIC 500；原拼字所指測驗須確認，沒有靜默改成已核准的雅思門檻。2018表的語言欄寫不要求，但初申附件同頁要求兩年內英語成績，並列母國官方語言為英語或學位課程英授者可豁免；兩處衝突保留，不能宣稱所有學生免語言證明。',sid,[1,2])
f(r,'host_deadline','2018/8/1資料表列秋申請4/25、春11/25；預計錄取信秋5/31、春12/15。這些是2018舊週期，未列提名截止，不轉為中央116提醒。',sid,[2])
f(r,'host_documents','2018初申共八類附件：申請表、英文完整成績、兩封推薦信、英文學習計畫、有條件的近兩年英語證明、醫師英文健康報告、彩色護照及兩張彩照。兩張照片中一張貼申請表，不是另加第三張；彩色護照須自申請日起至少有效兩年。原件說送國際處協調人，當期表格與規則仍待核。',sid,[2])
r['host_documents']=[
 doc('申請表（兩張彩照其中一張貼於表上）',sid,2),
 doc('完整成績單（譯為英文）',sid,2),
 doc('兩封推薦信',sid,2),
 doc('英文學習計畫',sid,2),
 doc('近兩年英語能力測驗成績影本',sid,2,condition='2018原件列母國官方語言為英語或學位課程英授者可豁免；同頁語言欄寫不要求存在衝突，當期須校方確認。'),
 doc('醫师英文健康聲明或基本健康報告',sid,2),
 doc('彩色護照影本（自申請日起至少有效兩年）',sid,2),
 doc('兩張彩色護照照片（45×35毫米或母國護照尺寸，其中一張貼申請表）',sid,2)]
f(r,'study_period','母校未註年表列秋9至12月、春2至6月；2018外校表建議一學期或一學年，沒有當期確切授課及考試日，不能據此訂116離校行程。',sid,[1,2])
f(r,'courses','2018外校表說課程採印尼語與英語雙語，不是全部純英授。舊表列27個大學部系及管理、英語教育、企業管理三個碩士項目，母校首頁只列前兩個碩士，不能直接擴大當期開放。選課雖寫不限制，仍須各授課教師同意；印尼語訓練對交換及訪問生免費，不等於其他課或全部學費免費。',sid,[1,3])
f(r,'housing','2018宿舍每棟房屋住4至6人，不是每間房4至6人；每學期650萬印尼盾。原表當年稱可給全體床位，不能當116住宿保證；房型、押金、期限及最新分配待核。',sid,[3])
f(r,'cost','2018外校表生活費每月200萬印尼盾，母校未註年介紹另列每學期500萬印尼盾；兩者計價週期及版本不同，不能擇低、改成同一月額或相加。來源未清楚說明是否含住宿，中央116生活預算仍待核。',sid,[1,3])
js(S/'reviewed-host-records.json',records);js(D/'added-host-records.json',{k:records[k]for k in identity})
fields=[v for k in identity for v in records[k]['fields'].values()]
print({'new_hosts':5,'fields':len(fields),'gap_only':sum(bool(v.get('gap_only'))for v in fields),'source_documents':len(ledger),'pages':sum(len(i['pages_reviewed'])for i in ledger)})
