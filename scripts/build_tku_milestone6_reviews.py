"""Content-scoped references from the frozen42 institutions; never home policy."""
import json,subprocess
from build_tku_milestone3_host_reviews import source,fact
from tku_capture_io import BUNDLE

def main():
 rows=[]
 def add(n,fields):rows.append(dict(id='tku-sister-'+str(n),fields=fields))
 def F(sid,value,needle,page=None,year='Actual incoming body, no independent academic year; TKU agreement/current nomination unverified',known=False):return fact(source(sid),value,needle,year,page,known)
 # UADE: regular semester, dual degree, short programme and freemover distinct.
 u='ffa0f49479a4046352b741a6';p='c720341bfea7c07918a61849'
 add(290,dict(
 host_eligibility=F(p,'學期交換須有效協議與母校提名；雙學位、Doing Business／Digital Marketing短期與freemover另案，不以共同Mobility Online入口認定TKU名額。','under a valid agreement',3),
 host_nomination_deadline=F(p,'一般提名：8月開始4/30、3月開始10/31；未載獨立年度。短期Doing Business等10/31另列，不作同一學期申請日。','30 April',3),
 host_deadline=F(u,'一般學生申請：8月開始5/15、3月開始11/15；Doing Business短期11/8另案。正文未載獨立年度，不能補2027。','15 May',3),
 study_period=F(p,'可一或兩學期；一般Autumn為3–7月、Spring為8–12月。先提名第一期，再由母校确认加入第二期；兩期學生結束第二期才發成績單。','Autumn semester',2),
 host_language=F(u,'須西語證明或母校信函；所讀文件沒有明載CEFR或考試分數，不猜B1/B2。','Spanish language certificate/letter',4),
 latest_forms=F(u,'未載年度程序：簽名申請表、推薦信、手寫申請信、護照、西語證明／信函、成績單、照片；提名後寄註冊與文件上傳期限。Learning Agreement模板在帳號內，未登入取得。','Signed application form',4),
 course_restrictions=F(u,'母校提名後按接待設定期限交Learning Agreement，建議打字；期限可隨學年度變動，不能由固定5/15、11/15推定所有文件同一天。','This deadline may vary',4),
 insurance=F(u,'須UADE批准的健康保險、以及依停留期間所需學生簽證；缺兩者不得參加期末考。這是未載年度接待規則，非母校資格。','Without these documents',5),
 student_support=F(u,'單學期成績單：3–7月期9月寄、8–12月期翌年2月寄；雙學期／雙學位只在第二期結束後寄。','Transcripts for the Autumn',5)))
 # UNA: actual bilateral incoming, Spanish documents, no recoverable dates.
 # Resolve from frozen checks, keeping source IDs reproducible, not guessed.
 checks=json.loads((BUNDLE/'milestone6_official_capture_checks.json').read_text());a=next(c['source_id'] for c in checks if c['institution_id']=='tku-sister-193')
 add(193,dict(
 host_eligibility=F(a,'雙邊／協議incoming與無協議學生分開；無協議需聯絡DGPRI，費用由接收院系決定，不作淡江協議有效或免學費證明。','Movilidad de estudiantes sin convenio'),
 host_language=F(a,'非西語國學生需西語能力證明，或母校聲明能力足以聽課；本文沒有數值級別。','Certificado de conocimiento de idioma español'),
 study_period=F(a,'一般第二學期8月、第一學期2月開始；每計畫每年定日程。文字擷取未取得日程欄具體截止，不能猜日／月或稱官方沒有。','Los cronogramas'),
 course_restrictions=F(a,'學習課單每學期最多30ECTS；不是母校名額或保證所有院系課可選。','30 créditos ECTS'),
 latest_forms=F(a,'incoming申請、課單、母校成績單、護照／有效身分證、適用獎學金證明、健康險、西語能力及承諾書。官方英語承諾DOCX實際ReadTimeout，未得模板；沒有登入UNA系統。','Formulario de solicitud de movilidad entrante'),
 costs=F(a,'無合作協議者是否收費由接收院系決定；本文不證明TKU交換免學費，未載年度。','El pago de aranceles'),
 insurance=F(a,'一般incoming文件要求國際健康保險且全面涵蓋，未載年度／價格。','Seguro de salud internacional')))
 # NQU international incoming; Taiwanese domestic TKU route unverified.
 n='cfd1a14ad1323c16de5e95d3';new='d7d943061ef6dfb050e67163';old='5d00191c1318c7f554ddbb3c';ny='Undated actual international incoming rule/template; TKU Taiwan domestic exchange applicability unverified'
 def N(v,needle,sid=n,page=None):return F(sid,v,needle,page,ny)
 add(186,dict(
 host_deadline=N('一般國際incoming：秋5/31、春12/15；本文無學年。淡江臺灣學生是否用國際方案尚未核實，不作本期校外截止。','May 31'),
 study_period=N('表單選一學期約6月或一學年約12月；沒有2027精確日期，不能推定臺灣國內交換適用。','One Semester',new,2),
 department_scope=N('接收學制表勾本科或碩士；母校就讀學制包含博士，不等於金門接收博士；院系及TKU適用待确认。','Graduate-Master',new,1),
 host_language=N('表單僅中文聽說讀寫自評與學習經歷，未明示入境交換統一分數；不能把自評當語言門檻已達標。','Self-evaluation of Chinese Proficiency',new,2),
 latest_forms=N('兩個公開2頁申請表均實際打開，正文無學年度；New版有生理性別及IG/FB/Threads，舊版Facebook。網頁兩張照片與兩表三張照片矛盾。未加入TKU母校catalog。','Attach three recent',new,1),
 housing=N('兩表均寫所有外國交換生須申請校內住宿；不是保證房間，也不能套給淡江臺灣學生。','外國交換學生皆須申請校內宿舍',new,2),
 housing_costs=N('未載年估計校內住宿TWD8,300–9,300/學期，不當2027費率。','TWD 8,300-9,300'),
 living_costs=N('未載年估計餐50–90/餐、書及用品3,000/學期、個人10,000/學期；不能當當期統一預算。','TWD 50-90'),
 insurance=N('網頁未載年健康險估TWD500/月；不當當期臺灣法規／費率或淡江學生保障。','TWD 500/month'),
 costs=N('國際交換網頁表示付母校學費、免申請費；不由此推定淡江國內交換免收費。','no application fee')))
 rows[-1]['fields']['latest_forms']['evidence']+=N('','Attach three recent',old,1)['evidence'];rows[-1]['fields']['latest_forms']['evidence']+=N('','Two recent 2-inch')['evidence']
 # HQU exact2025 HMT track, not international full-degree, short research separate.
 h='377d52effdf7ecee727110fa';hy='Actual2025 Hong Kong/Macau/Taiwan incoming exchange guide dated2025-02-10; historical, new2026/2027 not verified'
 def H(v,needle):return F(h,v,needle,year=hy,known=True)
 add(174,dict(
 host_eligibility=H('歷史2025港澳台方案：有學生交流協議院校、全日制本科二年級以上，或碩博不限年級，母校推薦。未驗2026／2027新版與TKU協議。','全日制二年级及以上本科生'),
 host_deadline=H('2025正文：秋5/31、春11/30，日期以分行數字保存；不能升成2027截止或母校開放。','秋季学期报名截止日期'),
 study_period=H('2025學期交換通常一學期、可視情況延長；另研究生短期研究1週至1學年，不能混同semester方案。','通常来校交流学习期限为一学期'),
 campus=H('2025正文列泉州、廈門、龍舟池；院系列分泉州與廈門，不能把任一點當所有交換指定校區。','龙舟池校区'),
 department_scope=H('2025院系列分校區；清單不是已核實TKU當期所有科系可選；錄取後不得變更專業。','不得'),
 course_restrictions=H('2025港澳台incoming錄取後不得變更專業；學分、課程及TKU當期對應仍需新來源。','变更专业'),
 latest_forms=H('2025申請表PDF、成績單、在籍證明、身分文件、個人陳述、體檢及意外險；臺灣明列在臺有效身分與居住證／台胞證，文件有效期規則只作歷史參考。未取得新版範本。','在台湾居住的有效身份证明'),
 insurance=H('2025港澳台文件清單要求人身意外險；國際生英語頁正文僅標題，不由標題補不同國籍保險規則。','人身意外保险单')))
 # PKU HMT: university and department-level registration truly distinguished.
 k='a3512e10ce7e805a8cfbff15'
 add(139,dict(
 host_eligibility=F(k,'港澳台校級交换须先向母校申請、經北大審批後寄錄取通知给母校承辦；不是所有姊妹校必可提名。','各校级交换生需在母校'),
 department_scope=F(k,'校級交換向港澳台辦報到；院系級交換直接向院系報到。不能把校級／院系計畫或科系接收混用。','院系级交换生直接至院系'),
 course_restrictions=F(k,'教學由教務部／研究生院主管、所屬院系執行；本文沒有課程、學分或語言數值，未借用degree入學規則。','教务部、研究生院'),
 latest_forms=F(k,'本文僅錄取後註冊與期末離校程序；研究生另轉單與交換總結，本科／研究生均交電子總結。未取得當期初次申請模板／截止。','提交交换总结电子版'),
 student_support=F(k,'未載年度港澳台校級incoming安排一對一學伴及每學期兩次參訪；不保证TKU当前分配。','一对一学伴')))
 # AGU: real2027 body despite filename2007; all14+6 text pages read.
 g='a6ad8d0b582e21f47764e912';f='fe6ba0603f976dbf7c01cb6d';gy='Actual Spring2027 application instructions datedJuly20,2026 / FactSheet2027 correct as ofJuly24,2026; filename2007 is not year'
 def G(v,needle,page,sid=g,known=True):return F(sid,v,needle,page,gy,known)
 fields=dict(
 host_eligibility=G('2027春：partner在籍、GPA≥2.5/4.0或學業平均以上证明、至少一學期成績、在籍至交換完結；本科至少14學分、碩士至少一研究科科目。研究所須協議允許及預先確認接收，不作TKU母校資格。','have a 2.5',1),
 host_language=G('2027依校區／院系：日語學逾一年且N5同等，部分院系可全英替代；英IELTS5.5／iBT新4.0或舊68／DET95，母語者例外。MBA日語課須N1，部分研究科可更高。iBT Best Score／Home Edition與IELTS Indicator不收。英語替代報告條件在兩文件不一致待確認。','Language requirements:',2),
 host_deadline=G('2027春第一申請2026/10/10（已過）、最終2026/11/10（JST）；2027秋第一3/10、最終4/10。第一階段利於提早CoE處理，最終仍須完整文件；host期未截止不代表TKU校內重開。','First Application',4),
 host_nomination_deadline=G('2027春母校提名2026/10/31、2027秋2027/3/31；提名名額要向AGU確認，未轉成TKU名額。','Deadline for nominations',4),
 study_period=G('2027春3月底到日、必到orientation、4月初至7月底課、7月底至8月初考；秋9月初到日、9月中至1月底課、1月底至2月初考。','Spring 2027',1,f),
 campus=G('青山東京與相模原神奈川按學部／研究科選；兩地約80–90分鐘，可跨校區部分課，日本語學分課等例外，不把單一校區當全部計畫。','commuting between',2,f),
 department_scope=G('2027研究所接收有限、須學業背景與院系同意；研究生若登記本科program只能本科課、不得研究所課。未核實TKU協議學制／科系。','NOT allowed to take classes',2,f),
 course_restrictions=G('2027本科至少14學分，碩士至少一研究科科目；體育、教師資格、degree學生外語等部分課不開放；學分日語須placement達A2／N4同等，不能用最低入境N5當日語課合格。','14 credits per semester',3,f),
 course_schedule=G('2027申請指引引用School Year2026英語課清單，實際開課每年可能變；2027英語課表尚未核實，不從指引年或一般同課說明升成2027課表。','School Year 2026',5,known=False),
 housing=G('2027按校區有Kyoritsu推薦住宿：青山Dormy、相模原Diakonia Hashimoto／Dormy Sagamiono；住宿申請同交換期限，非人人保證。入境前安排至少前三個月可做住所登記之住處。','recommended dormitories',12),
 housing_costs=G('2027FactSheet全年12月room&board估JPY1,260,000，含房與膳食，不能當純宿舍租金或保證報價；兩校區housing handbook未另取得。','Room & Board',5,f),
 living_costs=G('2027全年估JPY1,550,000，另列書60k、交通35k、活動70k、NHI25k、其他100k；估值非保證實際花費。','Total ¥ 1,550,000',5,f),
 costs=G('2027申請財力證明：一年至少JPY1,550,000、半年JPY780,000、開立2月內；這是存款證明不是學費、也不是TKU名額。','JPY 1,550,000',7),
 insurance=G('2027接待要求入境後NHI並自備全交換期海外旅遊險，錄取後、到日前交證明；FactSheetNHI約JPY2,000/月依居住地變動，非臺灣母校保障。','purchase travel insurance',12),
 latest_forms=G('正文2027春有21項條件文件／步驟，按學制國籍個別適用；公讀1頁signature及3頁health模板未載學年度。兩校區CoE XLSX實際各8工作表，申請／樣例／Office Use分開；本體入境年2027月3、校方入學2027/4/1，青山預填3/20、相模原日空白，不作保證行事曆，Office Use不由學生填。健康指引3月／兩劑與模板一年內X光／抗體等差異待確認；不加入母校catalog。','Student Application Documents',4,known=False),
 student_support=G('2027Buddy同儕支援；青山英文諮商每週3天預約免費，兩校區日文學生諮商weekday；未保證個別安排。','Counseling Services on Campus',6,f))
 fields['host_language']['evidence']+=G('','Best Score',6)['evidence']+G('','In case TOEFL',4,f)['evidence']+G('','If an applicant cannot',3)['evidence']
 fields['latest_forms']['evidence']+=F('56586d6a4ba388679d8dc857','','Date of Signing',1,'Undated actual signature template linked2027 official application page')['evidence']+F('1f7a5b7ad67a0ee10ed03658','','within one year',3,'Undated actual health template; do not infer year from2024 URL')['evidence']+G('','three (3) months',6)['evidence']
 for sid,campus in [('bf53f687e0acbef4028554a8','Aoyama'),('366d16d98d9232b4a559db3d','Sagamihara')]:
  ev=F(sid,'','H55=2027',year='Actual2027Spring CoE; body entry year2027/month3 and office-use enrollment2027April1',known=True)['evidence']
  for e in ev:e['locator']='XLSX '+campus+' Application_1 (xl/worksheets/sheet1.xml),H55/N55/R55; campusI29 and AGU Office Use1 I41/O41/S41 separately reviewed'
  fields['latest_forms']['evidence']+=ev
 add(33,fields)
 # Aizu: actual Spring2027 but in-preparation deadline already passed;
 # explicit protected packet/checklist not fetched. OLE forms encrypted, not HTML.
 z='5113f11c4c728da620ea778d';zy='Actual2027Spring application subsection; UpdatedAug3,2026 is update date, programme overview not independently dated'
 def Z(v,n,known=False):return F(z,v,n,year=zy,known=known)
 add(39,dict(
 host_eligibility=Z('ICRP Special Audit Student本科／研究所僅指定partner；非partner須Non-Regular Student另案。沒有從100合作機構或全英degree推定TKU可申請。','designated partner universities'),
 study_period=Z('一般ICRP可一quarter至一學年，學分可能帶回母校但須母校認定；不是保證一學期或所有课程。','one quarter to one academic year'),
 host_deadline=Z('正文2027春明列Deadline Thursday2026/9/17（已過），同時Status In preparation；秋2026另標Closed。準備狀態與已過日期矛盾，沒有修正年份或稱TKU開放。','Status: In preparation',True),
 department_scope=Z('ICRP Special Audit Student與非協議Non-Regular Student分開，沒有科系／學制接收名額清單，不猜全面開放。','Non-Regular Student Admission Program'),
 latest_forms=Z('母校彙整單人PDF系統提交。Packet／Checklist需母校Office收密碼，未請求或解密；公開SAS XLSX／DOCX兩網址200實為含EncryptionInfo＋EncryptedPackage的加密OLE，保留原始opaque bytes，沒有讀到範本正文或學年度。','The password to access'),
 student_support=Z('由OSIP受理方案問題；學生先交母校International Office，母校依清單審核後提交，不登入或代送。','Submit to Home Institution')))
 assert len(rows)==7 and len({r['id'] for r in rows})==7
 prior=json.loads(subprocess.check_output(['git','show','4f142ea36e69338d2956b4ea5d3d37a9f4116e52:src/exchange_info/official_data/tku/curated_partner_facts.json'],cwd=BUNDLE.parents[3]))
 assert len(prior)==40 and not {r['id'] for r in prior}&{r['id'] for r in rows}
 (BUNDLE/'milestone6_reviewed_host_facts.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(dict(institutions=len(rows),fields=sum(len(r['fields']) for r in rows),source_period_institutions=sum(any(f['source_period_verified'] for f in r['fields'].values()) for r in rows),source_period_fields=sum(f['source_period_verified'] for r in rows for f in r['fields'].values())),ensure_ascii=False))
if __name__=='__main__':main()
