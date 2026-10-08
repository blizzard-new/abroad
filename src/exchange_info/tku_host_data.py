"""Reviewed host facts and phase-specific documents for TKU's four latest choices.

Every statement is scoped to its source programme/year. General UEC rules and
2026 housing budgets remain references even when the pages are currently live.
"""
from __future__ import annotations

from .tku_data import CHECKED_AT, TKUEvidence, TKUFact, load_tku_sources


def source_map():
    return {s['id']:s for s in load_tku_sources()}


def host_fact(value, source_id, locator, *, status='verified', reason=None, quote=''):
    s=source_map()[source_id]
    return TKUFact(value=value,status=status,reason=reason,evidence=[TKUEvidence(
        source_id=source_id,source_url=s['source_url'],locator=locator,
        applicable_year=s['applicable_year'],application_round='2027春季外校申請／淡江日語二甄後續',
        role=s['role'],checked_at=CHECKED_AT,quote=quote)])


def enrich_current(record):
    slug=record.id.rsplit('-',1)[-1]; f=record.fields
    def put(key,value,source,locator,**kw):f[key]=host_fact(value,source,locator,**kw)
    # Do not mix outbound academic/language thresholds with host admission rules.
    f['home_language']=TKUFact(value='日語授課大學部JLPT N2、研究所N1；立命館另須N1；英語課程大學部例外與研究所豁免須分開確認。',
        status='needs_confirmation',reason='UEC英語課程例外及名額表連接詞與外校規則差異須承辦確認。',
        evidence=[e.model_copy(update={'locator':'PDF p.2 壹一（三）；名額表p.1 row 1/4'}) for e in f['home_eligibility'].evidence])
    if slug!='uec':
        f['home_language'].value='立命館本期JLPT N1；淡江日語課程大學部N2、研究所N1。' if slug=='ritsumeikan' else '淡江日語課程大學部JLPT N2、研究所N1。'
        f['home_language'].status='verified';f['home_language'].reason=None
    put('visa_residence','臺灣護照且已取得COE者：護照（含舊護照如有）、本人簽名簽證申請書、4.5×3.5cm白底近6月照片、身分證正本及雙面影本、COE正本及雙面影本／電子COE列印。原則5個工作天，可能追加文件。COE不保證簽證；照片規格與外校申請不同。',
        'taiwan-coe-visa','必要書類1–5／注意事項／所要日数',status='reference_only',reason='官方一般簽證指引，依國籍、居住地及送件時最新規定；不是2027學校表單。')
    if slug=='ritsumeikan':
        guide='ritsumeikan-2027-guide'
        put('host_programme_mapping','2027春季SKP；淡江表列立命館，須由淡江承辦提名，track與校區需與提名一致。',guide,'PDF p.8; p.14–15')
        put('host_eligibility','合作校正式提名、母校大學部或研究所仍在學；交換開始前完成至少一整個大學學年；GPA標準3.0/4.0或同等，協議另訂須遵守。',guide,'PDF p.8 Enrollment / Academic Requirements')
        put('host_language','RCJ：JLPT N1或EJU日語280且寫作35；IJL外校未設日語程度下限；RCE及IJL選英文專業課：iBT76（新量尺4.0）、IELTS Academic6、Cambridge170或Duolingo100，豁免須符合外校條件。淡江本輪立命館N1仍另須滿足。',guide,'PDF p.8 Language Requirements; p.19')
        put('campus','依track選衣笠（京都）、BKC（滋賀）或OIC（大阪）；IJL僅衣笠。需核對p.5–6可選院系表，不能任意跨校區。',guide,'PDF p.5–7 track / campus chart')
        put('host_nomination_deadline','2026/10/22 09:00 JST；母校承辦提名期間9/28起。','ritsumeikan-howto-2027','Nomination Period')
        put('host_calendar','2027春：4/1學期開始、4/7開課、7/31課程計畫結束、9/25學期結束；秋：9/26學期開始、9/27開課、2028/1/31計畫結束、3/31學期結束。實際抵達及orientation為3月上中旬，精確日期未載。',guide,'PDF p.2 Schedule')
        put('host_study_period','春季一學期或春秋兩學期；申請後不得延長；上課結束不等於學期結束或宿舍最後入住日。',guide,'PDF p.2–3')
        put('housing','申請SKP時填住宿意向；正式住宿申請於錄取後另寄給錄取生。I-House依校區安排且不保證房型／床位，住宿結果預計2月底。',guide,'PDF p.18 Housing Preference / Application Process')
        put('housing_application_deadline',None,guide,'PDF p.18 Housing Application Process',status='missing_in_source',reason='簡章明示錄取後另寄住宿申請說明；公開文件未載本期確切截止。')
        put('housing_costs','2026/3起可每學期變動的參考：衣笠Tokiwa租金39,000＋寢具2,000/月，Taishogun／Utano49,000＋2,000/月，含水電網路，入寮费一個月租金、清潔10,000及另列行政費；BKC月總48,900或55,900；OIC月總64,200。BKC/OIC另需一個月租金入寮費、清潔10,000、行政10,000及火災保險。2027實際宿舍帳單未核實。','ritsumeikan-kinugasa-housing','Fee Tables; BKC/OIC separate official tables',status='reference_only',reason='表頭限定2026/3起且註明每學期可能變動；不能當作2027確定價格。')
        f['housing_costs'].evidence += [host_fact('',s,'Fee Table (Ritsumeikan Students)').evidence[0] for s in ['ritsumeikan-bkc-housing','ritsumeikan-oic-housing']]
        put('living_costs','一般SKP頁估一學期798,000／兩學期1,582,000日圓，含住宿、食物、交通、手機、休閒及保險；該預算表保險項目與2027新增支援費包含項目可能重複，年度亦未明示，須確認後才可合計。','ritsumeikan-fees','Estimated Living Expenses',status='needs_confirmation',reason='一般預算表未明示年度，academic/liability insurance與2027支援費內容可能重複；不產出確定總預算。')
        put('insurance','50,000日圓SKP支援費包含Gakkensai／Gakkenbai及COE行政服務；不含國民健康保險與個人選擇保險，後者入境後另辦另付。',guide,'PDF p.4 support fee inclusions/exclusions')
        put('arrival_preparation','COE申請程序為11月上旬至12月上旬，早於12月下旬錄取結果；依行政書士另通知送件，不能等錄取才辦。COE核發文件預計2月中寄出；3月上中旬抵達／orientation。錄取後全體填健康資訊（1月中暫定），患病／用藥或需學習調整者另附指定證明；住宿結果預計2月底。',guide,'PDF p.2, p.20–22')
        put('arrival_date',None,guide,'PDF p.2 Arrival / Orientation (Early to Mid-March)',status='missing_in_source',reason='只載區間，精確抵達日待錄取生通知，不能自行建立航班日期。')
        put('course_restrictions','每週至少7堂95分鐘課、上限20學分；依track／校區核對可選院系及歷年課表，2027課程可能變動；大學部只選大學部課，研究生可選兩層級但SKP不提供研究指導；跨校區需許可，Design and Art不開放。',guide,'PDF p.5–8')
        put('course_schedule_2027',None,guide,'PDF p.5 and p.8 Course Lists From Previous Semesters',status='not_verified_new',reason='簡章要求核對歷年課表，公開2027實際課表未核實；不是官方明示尚未公告。')
        put('latest_forms','2027簡章文件清單已核實；SKP申請網址／帳號提名核准後寄送。COE程序11月上旬至12月上旬（錄取前），行政書士另提供指定網路表；健康表錄取後另提供。實際表單內容尚未取得。','ritsumeikan-howto-2027','Application Process Step 2; guide p.2/p.20–21',status='needs_confirmation',reason='當期清單／提供方式已核實，但未取得提名後SKP網路表、錄取前COE表及錄取後健康表內容，不能稱全部表單已驗證。')
        put('transport','衣笠各宿舍官方一般估步行／單車約10–30分鐘；OIC宿舍步行約18分鐘。實際校區依提名及track，跨校區通學需另計。','ritsumeikan-kinugasa-housing','Access to campus for Taishogun/Tokiwa/Utano',status='reference_only',reason='一般宿舍交通估計，住宿分配與2027路線尚未確定。')
        record.conflicts.append('ritsumeikan-budget-insurance')
    elif slug=='nagasaki':
        notice='nagasaki-nics-2027'
        put('website','https://www.nagasaki-gaigo.ac.jp/studying-abroad/receiving_program/nics_program/',notice,'2027年度春学期 NICS heading; partner directory Taiwan Tamkang')
        f['website'].evidence.append(host_fact('','nagasaki-partners','Taiwan / 2004年5月17日 淡江大学').evidence[0])
        put('host_programme_mapping','官方合作名單列淡江（2004/5/17）；2027春NICS按交流協議收交換生且以日語授課，與淡江本輪時點相符。但淡江表未寫NICS，最終提名track須承辦確認；以下為NICS條件。',notice,'募集要項 opening / 出願資格',status='needs_confirmation',reason='雙方合作關係已核實；本輪淡江提名是否指定NICS及碩士課程安排未明示，不能僅以合作名單判定。')
        f['host_programme_mapping'].evidence.append(f['website'].evidence[-1])
        put('host_eligibility','NICS：非日本國籍；日語能聽課且由合作母校負責推薦；2027/3前在母校在學至少一年（含預計）；交換結束前保持母校學籍。',notice,'出願資格1–3')
        put('host_language','NICS外校未列JLPT級數，要求可用日語聽課並獲母校推薦；淡江日語二甄大學部N2／研究所N1仍適用。',notice,'出願資格1')
        put('host_deadline','2027春NICS：2026/10/31消印有效；未載時刻。適用已獲淡江推薦且確認NICS者。',notice,'出願締切',quote='2026年10月31日（土）（消印有効）')
        put('host_nomination_deadline',None,notice,'出願資格 / 出願締切',status='missing_in_source',reason='母校推薦為必須，但公開NICS公告未另列提名截止。')
        put('host_study_period','NICS／2027 Form A及誓約書：半年2027/3–8；一年2027/3–2028/2；入境後不能由半年延長至一年。與淡江表2027/4–2028/3範圍不同，實際交換及返校期間須確認。','nagasaki-pledge','PDF p.1 Intended Term(s)',status='needs_confirmation',reason='本期誓約書及Form A有明確3月至次年2月，與淡江名額表範圍不同。')
        put('host_calendar',None,'nagasaki-calendar','2026年度 heading',status='not_verified_new',reason='官方calendar入口目前展示2026年度；2027課程／考試精確日期尚未核實，未見官方明示尚未公告。')
        put('campus','NICS學校地址長崎市横尾3-15-1；Ampelos寮為時津町元村郷1222-21、校園鄰接。',notice,'住居（寮）／問い合わせ先')
        put('housing','NICS短期交換／一般留學生均由校方準備房間，第一學期原則全體入住Ampelos；房型／室友不保證符合偏好。一年生可第二學期自行外租，已付第二學期寮費依日退回。',notice,'住居（寮）; pledge p.1 items 1/3')
        put('housing_application_deadline',None,notice,'住居（寮）／納入金',status='missing_in_source',reason='公告表示安排房間，未另載住宿申請截止及房型選擇截止。')
        put('costs','2027春NICS交換生外校學費0；實驗實習／課外活動費半年50,000、一年53,100（含指定A/B保險）；行政費15,000／20,000（含機場接送）。住宿／餐費另計，非交換一般生270,000／540,000學費不套用。',notice,'2027年度（春学期）の納入金内訳表①–③')
        put('housing_costs','NICS北側雙人：一次入寮20,000、月租21,000加零星日數；南側單人：30,000、42,000/月加零星日數。餐費30,000/月×3個月加零星日數，至6月底早餐／晚餐必訂；7月起可自炊。納入期限1月下旬另告知，未載確切日。',notice,'納入金内訳表④–⑥／上記納入金について')
        put('living_costs','2027春NICS公告直接引用的Form C要求支弁學費以外住宿、食物、交通、水電每月60,000日圓以上。這是本期財務證明下限，不是完整實支預算或保證足夠金額；依房型及其他支出另準備。','nagasaki-form-c','PDF p.2 Financial Support Details; 2027 NICS notice 提出書類5',reason='表單本身無學年度；適用本期的依據是2027春NICS公告直接連結。僅核實支弁基準，非實際總費用。',quote='more than 60,000 JPY will be needed per month')
        f['living_costs'].evidence.append(host_fact('',notice,'提出書類5 経費支弁書 Form C').evidence[0])
        put('insurance','NICS必保A學生教育研究災害傷害及B外國留學生生活綜合保險（均含實習費），C國民健康保險約2,000日圓/月另繳，入境後本人赴役所登記；另強烈建議母國海外旅行保險。',notice,'保険 A/B/C')
        put('arrival_preparation','NICS預計1月下旬發入學許可及COE、2月下旬申請簽證、3月中旬抵達；校方在福岡機場接送，原則專車至校／寮，包含在行政費；不使用不退費。',notice,'出願後の流れについて／空港から大学まで')
        put('arrival_date',None,notice,'3月中旬 渡航・来日',status='missing_in_source',reason='只載3月中旬，實際接機日期／集合方式須錄取通知，不能自行指定。')
        put('course_restrictions','NICS每學期至少12、至多25學分，可把英語JASIN課計入12；可選部分一般大學部課，部分不開放。研究所認列及本輪指定track須淡江系所確認。',notice,'カリキュラム')
        put('course_schedule_2027',None,'nagasaki-courses','開講科目一覧',status='not_verified_new',reason='目前是一般開講科目列表，未核實2027實際課表／時段，不是官方明示未公告。')
        put('latest_forms','2027春公開Form A已開啟；本期誓約書內文寫2027，其餘B/C/D/E表單無學年度，但由2027春公告直接連結，已讀PDF/DOCX；照片2／3張及Form B日英文字數差異待確認。',notice,'提出書類1–11',status='needs_confirmation',reason='表單可開啟且當期公告明確引用；附件與公告的照片數量、日英內容有矛盾。')
        put('transport','2027 NICS抵達日福岡機場有校方專車；Ampelos寮鄰接校園。其他日常交通費公告未列。',notice,'空港から大学まで／住居（寮）')
        record.conflicts += ['nagasaki-photo-count','nagasaki-essay-translation','nagasaki-study-period','nagasaki-programme-mapping']
    elif slug=='seikei':
        sheet='seikei-2027-sheet'
        put('host_programme_mapping','2027春交換生information sheet；由母校提名／送外校，名單頁亦列淡江。',sheet,'PDF p.1–2; p.6 Partners')
        put('host_eligibility','外校GPA2.5/4.0以上，提名前母校在學至少一學期；日語學習一年或300小時，N5等同且目標N4。淡江本輪日語資格另需滿足。',sheet,'PDF p.1 Admission Requirements')
        put('host_language','外校要求一年或300小時日語學習（N5等同並目標N4）；專業大學部課需N1；淡江大學部N2／研究所N1不能被外校較低最低日語要求取代。',sheet,'PDF p.1 Admission / p.2 Courses')
        put('host_nomination_deadline','Spring2027提名10/1；未載時刻，須母校承辦提名。',sheet,'PDF p.1 Application Deadline')
        put('host_study_period','2027交換計畫接受一學期或一學年；淡江本輪仍列一學年，不能自行縮短。外校春季住宿約3月中旬至8月初、秋季9月初至次年2月初；精確calendar及指定抵達日仍未核實，分列待確認。',sheet,'PDF p.1 Duration of Study / Semester Schedule',reason='此欄僅核實外校接受的學期數；不以近似schedule推定精確日期。',quote='One semester / One academic year')
        put('host_calendar','Spring2027 sheet：3月中旬入住、3月下旬orientation、4月初至7月下旬上課及7月底考試、8月初退宿；秋季9月初入住、9月中orientation、9月下旬至1月下旬上課／考試、2月初退宿。精確2027日期未核實。',sheet,'PDF p.1 Academic Calendar / Semester Schedule',status='needs_confirmation',reason='該sheet的calendar連結標AY2026；僅近似schedule可用，不能套2026確切日。')
        put('campus','東京武藏野市吉祥寺北町；專業課依指導教師同意，無法保證選上。',sheet,'PDF p.1 Contact / p.2 Course Information')
        put('housing_application_deadline',None,sheet,'PDF p.3–4 Accommodation',status='missing_in_source',reason='住宿資料已核實，公開sheet未列住宿表截止；取得方式與期限須承辦確認。')
        put('housing_costs',str(f['costs'].value),sheet,'PDF p.3–4 Fees')
        put('living_costs','2027 sheet另估手機3,000–5,000/月、其他個人支出20,000–50,000/月；國際會館另估水電8,000–10,000/月、食物25,000–30,000/月。Dormy及MICHI有不同餐費包含範圍，不能把全部項目重複加總。',sheet,'PDF p.4–5 Fees / Living Costs')
        put('insurance','國民健康保險官方sheet估約10,000日圓/年；實際保費需依自治體及個人情況，與宿舍費不同。',sheet,'PDF p.5 Living Costs')
        put('arrival_preparation','春季約3月中旬入住、3月下旬orientation；先由母校提名，COE線上表及財力證明等細節提供給提名學生。2027/9起原校安排住宿者搬入MICHI，需預留搬遷安排。',sheet,'PDF p.1–4')
        put('arrival_date',None,sheet,'PDF p.1 arrival / orientation schedule',status='missing_in_source',reason='只載mid/late-March，未載2027指定抵達日期或接機服務。')
        put('course_schedule_2027',None,'seikei-host','Incoming Students / Syllabus links',status='not_verified_new',reason='2027當期課表未核實；incoming頁現有歷年syllabus僅供參考。')
        put('latest_forms','2027 sheet p.2清單已讀；官網Program段指定向母校交換承辦索取申請材料。已查incoming頁未列這些空白表下載，內容尚未取得核實；不能推定所有表單只限提名後或非公開。COE細節p.2明示另提供提名學生。',sheet,'PDF p.1–2 Application Procedures；incoming頁Program段',status='needs_confirmation',reason='當期清單、承辦索取途徑及COE提名後通知已核實；一般申請原表仍未取得，沒有逐表非公開證據。')
        f['latest_forms'].evidence.append(host_fact('','seikei-host','Program: contact home university coordinator for application details and materials').evidence[0])
        put('transport','2027/8前Dormy：井之頭公園站步行12分、吉祥寺站15分、校園單車12分（2.9km）；國際交流會館：吉祥寺站步行20分、校園1分。2027/9起MICHI至校園步行5分。sheet未載接機服務或交通票價；床位與實際路線依外校安排。',sheet,'PDF p.3–4 Accommodation <Access>',reason='已核實本期住宿通勤；接機及票價仍未知，不能把通勤資料解讀為有機場接送。',quote='12-minute bicycle ride from Seikei University (2.9km)')
        put('scholarships','成蹊40,000日圓/月（每年60人）或深谷60,000/月（每學期1人），至多10月，均非保證。成蹊獎要求其他非貸款獎助低於60,000/月；深谷不得有其他獎助，活動參與等條件見sheet；與交換申請同時申請。',sheet,'PDF p.5 Scholarships')
    else:
        app='uec-application-recheck'
        f['host_programme_mapping']=TKUFact(value='淡江2027–2028日語二甄名額表row4明載參加JUSST program。僅核實本梯計畫名稱；外校2027專屬規則、學制及表單仍各自待核實，不能由名稱推定。',status='verified',reason='當期母校直接明示JUSST；外校一般規則適用年度與本欄分開。',evidence=[f['school_name'].evidence[0].model_copy(update={'locator':'PDF p.1 row4 注意事項1', 'quote':'JUSST program'})])
        put('host_eligibility','JUSST一般：合作校正規全職資訊／科學／工程學生，入學時大學部三四年級或研究生；畢業年级須交換结束后仍保持母校學籍。學業達80%或GPA2.3/3、3/4、5.5/7其一；淡江本輪80及GPA3仍另列。',app,'Eligible Applicants / Student Status / Academic Conditions',status='reference_only',reason='外校一般規則，2027專屬未核實；不能覆蓋母校当期較嚴條件。')
        put('host_language','JUSST一般以英語授課：iBT67、CEFR B2、IELTS6、Duolingo95等同擇一，無入學日語門檻；不等於免修日語課。淡江表寫iBT67及IELTS6，連接詞差異待確認。',app,'English Proficiency',status='needs_confirmation',reason='外校一般頁等同擇一、淡江本期表用「及」；母校實際送件要求須確認。')
        put('host_nomination_deadline',None,app,'Application procedure / Schedule',status='not_verified_new',reason='由母校IAO直接送件，未核實2027獨立提名截止，無法沿用別校。')
        put('host_study_period','一般JUSST一年兩學期，4月或10月入學；部分可一學期，最終依申請與錄取。淡江本轮表為2027/4–2028/3。','uec-program','JUSST Program / Enrollments paragraph',status='reference_only',reason='一般方案未核實2027個別錄取期間。')
        put('host_calendar',None,'uec-courses','2026 Spring / Fall time tables',status='not_verified_new',reason='官方course入口最新列2026課表；2027開課／orientation精確日尚未核實，不宣稱官方尚未公告。')
        put('campus','JUSST位於東京調布校區；淡江電機／資工學生「優先」，不是排除其他科系。','uec-program','Contact / programme description',status='reference_only',reason='一般校址，2027研究室及課程安排另依外校。')
        put('housing_application_deadline',None,'uec-costs','Living and Housing Information',status='not_verified_new',reason='一般住宿資訊未列2027申請窗口、床位及正式入住日。')
        put('housing_costs',str(f['housing'].value),'uec-costs','Living and Housing Information',status='reference_only',reason='25,000日圓原文未明示計費單位，不補猜月租；2027費率未核實。')
        put('living_costs',None,'uec-costs','Living and Housing Information',status='not_verified_new',reason='住宿金額單位不明，沒有足夠2027生活費項目，不猜總額。')
        put('insurance','JUSST一般頁指定保險約26,000日圓（年度可變動，正文未明示計費單位）並另須國民健康保險；國保需赴居住地役所登記。一般生活頁包含2009保費表，不當作當期價目。','uec-costs','Student Administration Fee and Insurance',status='reference_only',reason='2027價格未核實；舊保費表與JUSST一般估算分開。')
        f['insurance'].evidence += [host_fact('',s,'Enrollment procedures / body explicitly dated fee table').evidence[0] for s in ['uec-national-insurance','uec-private-insurance']]
        put('arrival_preparation','一般Form A：春季COE約2–3月送母校、4月首個平日抵達及首週orientation；2027確切日尚未核實。核准後自費者立即提供財力文件；TB檢查僅指定國籍等適用者，不套用所有臺灣學生。','uec-jusst_form_A-rev9-pdf','PDF p.9 Spring Semester Entry Process; application webpage item16–17',status='reference_only',reason='Form A©2023為一般年度程序；2027行前通知尚未取得。')
        put('arrival_date',None,app,'Schedule / JUSST Form A p.9',status='not_verified_new',reason='只有每年4月首個平日的一般規則，未核實2027指定日期／接機安排。')
        put('course_restrictions','JUSST一般：學士每學期3門日語、3門科學工程、3門技能及Individual Study；研究生日語第一學期3門、科學工程每年3門、技能3門及Independent Research。無日語入學門檻仍須修日語；課程可能與舊表不同。','uec-program','Course Requirements / Undergraduate and Graduate rows',status='reference_only',reason='一般課程要求，2027課程清單未核實。')
        put('course_schedule_2027',None,'uec-courses','time table links 2026 Spring/Fall',status='not_verified_new',reason='2027課表尚未核實，不能將2026課表放當期申請文件。')
        put('latest_forms','一般JUSST A/H/SP/RP及JASSO表共9個PDF/DOCX版本已實際下載讀內容；Form A©2023，版本ver22/ver23不當作年度；2027專屬版尚未核實，全部放一般參考文件。',app,'Application Forms and Documents',status='reference_only',reason='目前官方一般頁提供的表單，未核實2027指定版本；不宣稱官方尚未公告。')
        put('transport',None,app,'General application / no transfer policy',status='not_verified_new',reason='未核實2027接機或通勤費，須依錄取行前指示。')
        # This is an opportunity in the CURRENT home list, not a guaranteed award.
        f['scholarships']=f['quota'].model_copy(deep=True)
        f['scholarships'].value='淡江2027–2028日語二甄名額表row4：有機會申請JASSO獎學金；不是保證獲獎。一般JUSST的JASSO在籍證明由母校授權人填写，2027資助名額／金額尚未核實。'
        f['scholarships'].evidence[0].locator='PDF p.1 row 4 remark 4'
        f['scholarships'].evidence[0].quote='有機會申請JASSO獎學金。'
        record.conflicts.append('uec-form-a-fall-label')
    specs=host_documents(slug)
    source_id=specs[0]['evidence']['source_id']
    put('host_documents','；'.join(item['name']+'〔'+item['condition']+'；'+item['phase']+'〕' for item in specs),
        source_id,specs[0]['evidence']['locator'],status='reference_only' if slug=='uec' else 'needs_confirmation' if slug=='nagasaki' else 'verified',
        reason='清單與條件及階段已分開；非公開表／2027未核實版或公告附件矛盾另見latest_forms。')
    return record


def host_documents(slug):
    """Named items preserve conditions, phase, version and public-form access."""
    rows=[]
    def doc(key,name,source,locator,*,phase=4,condition='所有申請人',form=None,status='verified',copy_type='unspecified',signatures=None,access=None,stage=None,timing=None):
        s=source_map()[source]
        form_source=source_map().get(form) if form else None
        rows.append(dict(key=key,name=name,phase='外校申請' if phase==4 else '行前',step_order=phase,
            condition=condition,status=status,applicable_year=s['applicable_year'],checked_at=CHECKED_AT.isoformat(),
            stage=stage or ('student_application' if phase==4 else 'post_offer'), timing=timing,
            evidence=host_fact('',source,locator).evidence[0].model_dump(mode='json'),
            form_source_id=form,official_form_url=form_source['source_url'] if form_source else None,
            form_access=access or ('verified_public' if form_source else 'own_document'),
            form_version=form_source['applicable_year'] if form_source else None,
            copy_type=copy_type,signatures=signatures or []))
    if slug=='ritsumeikan':
        s='ritsumeikan-2027-guide'
        doc('skp-online','SKP線上申請：track／校區、日語學習背景、財務／獎助與住宿意向',s,'PDF p.14–18',access='nomination_then_account_by_email')
        doc('enrollment','目前大學官方在學證明（英文或附英文／日文譯本）',s,'PDF p.19')
        doc('graduation','官方畢業證明',s,'PDF p.19',condition='已取得學位者')
        doc('transcript','最近官方成績單，附評分制度、全部課程及學分',s,'PDF p.19')
        doc('undergraduate-transcript','大學部成績單',s,'PDF p.19',condition='研究所一年級')
        doc('language','語言成績證明：RCJ N1／EJU；RCE及選英文課IJL按外校標準',s,'PDF p.19',condition='依track及英文豁免規則；淡江N1資格另適用')
        doc('statement','個人聲明PDF：日文500–700字或英文500–700 words',s,'PDF p.16–17; p.19')
        doc('passport','護照姓名／國籍／照片等相關頁；曾入境日本者併入出境章頁PDF',s,'PDF p.18–19',copy_type='copy')
        doc('residence-card','有效在留卡正面影本，My Number背面不得提交',s,'PDF p.19–20',condition='持有效日本在留卡者',copy_type='copy')
        doc('coe','指定行政書士COE網路表，另依通知補件',s,'PDF p.2 Schedule／p.20 COE',phase=5,condition='非日本籍且無有效在留卡者；有在留卡者由外校判斷',access='separately_sent_to_applicant',stage='after_application',timing='11月上旬至12月上旬，早於12月下旬錄取結果；行政書士另通知，未載確切截止，不能等offer。')
        doc('health','Health Information Registration Form',s,'PDF p.21',phase=5,access='after_admission_separately_provided')
        doc('medical','指定診斷證明及處方',s,'PDF p.21–22',phase=5,condition='治療／服藥／定期觀察或需醫療支持者',access='after_admission_separately_provided')
        doc('accommodation-support','診斷證明及母校學習調整證明；預期困難聲明可選',s,'PDF p.21–22',phase=5,condition='申請合理學習調整者；困難聲明選附',access='after_admission_separately_provided')
        doc('housing','錄取後正式住宿申請',s,'PDF p.18',phase=5,condition='申請I-House者，公開本期截止未載',access='after_admission_separately_provided')
        doc('japanese-id','戶籍謄本抄本及學生證照片',s,'PDF p.20',phase=5,condition='日本國籍者（含雙重國籍）；不與COE必繳並列')
    elif slug=='nagasaki':
        s='nagasaki-nics-2027'
        doc('form-a','2027春Form A線上表（出願指南不用提交）',s,'提出書類1',form='nagasaki-form-a-online')
        doc('pledge','2027春誓約書：閱讀住宿規則後簽名',s,'提出書類2',form='nagasaki-pledge',signatures=['申請人'])
        doc('photos','4×3cm近3月彩照；公告3張／指南2張差異待確認，上傳照片可免附',s,'提出書類3; Form A guide PDF p.1',condition='未上傳照片資料者需紙本；張數待外校確認',status='needs_confirmation')
        doc('essay','Form B日文志望理由：日文500–1,000字；英譯words／語言內容不同待確認',s,'提出書類4; Form B DOCX essay instructions',form='nagasaki-form-b',status='needs_confirmation')
        doc('finance','Form C經費支弁書',s,'提出書類5; Form C PDF p.1–2',form='nagasaki-form-c',signatures=['經費支弁者'])
        doc('recommendation','Form D推薦書；非日文須日文譯本，英文原本免譯',s,'提出書類6',form='nagasaki-form-d',signatures=['推薦教師'])
        doc('health-student','Form E①本人健康申告',s,'提出書類7',form='nagasaki-form-e1')
        doc('health-physician','Form E②醫師診斷與胸部X光報告／未X光者結核皮膚測試結果',s,'提出書類8; Form E2 PDF p.1',form='nagasaki-form-e2',signatures=['醫師'])
        doc('transcript','母校英文成績單正本',s,'提出書類9',copy_type='original')
        doc('bank','英文銀行餘額證明：交換半年500,000／一年1,000,000日圓，姓名須與Form C支弁者一致',s,'提出書類10; Form C PDF p.1')
        doc('passport','護照所有個人／國籍／發照資訊頁A4影本；尚無護照可暫以官方身分證件代替',s,'提出書類11',copy_type='copy')
    elif slug=='seikei':
        s='seikei-2027-sheet'
        specs=[('application','Exchange Student Application','所有申請人'),('japanese-background','Japanese Language Study Background','所有申請人'),('health','Health Certificate','所有申請人'),('scholarship-intention','Declaration of intention for applying scholarships','申請清單列載全體；實際填寫意向依表'),('financial-statement','Statement of financial situation','僅獎學金申請人'),('medical','Medical declaration form','所有申請人'),('transcript','英文官方Academic Transcript','所有申請人'),('passport','有效護照照片頁影本','所有申請人'),('photo','ID照片資料4×3cm','所有申請人'),('coe','線上COE申請及財力證明','提名後依外校COE指示；適用者須辦')]
        for key,name,condition in specs:doc(key,name,s,'PDF p.2 Application Procedures',condition=condition,access='provided_to_nominated_students' if key=='coe' else 'contact_home_coordinator' if key not in ['transcript','passport','photo'] else 'own_document',copy_type='copy' if key=='passport' else 'unspecified')
    else:
        s='uec-application-recheck';kw={'status':'reference_only'}
        doc('form-a','JUSST Form A（PDF可編輯）：列印親簽與母校推薦欄',s,'Application Forms item1; Form A PDF p.1/8/9',form='uec-jusst_form_A-rev9-pdf',signatures=['申請人','母校授權推薦人'],**kw)
        doc('photos','3×4cm照片貼Form A及另附一張；Form A要求送件前30日内',s,'Application Forms item2–3; Form A PDF p.1',**kw)
        doc('health','Form H健康申告：本人及母校國際處／授權人確認，錄取後參加UEC健康檢查',s,'Application Forms item4; Form H PDF p.1–2',form='uec-uec_form_H-new-pdf',signatures=['申請人','母校國際處／授權人'],**kw)
        doc('jasso','JASSO在籍證明（母校授權人填寫）',s,'Application Forms item5',form='uec-jasso_form-rev1-pdf',condition='全年交換申請人依一般清單；2027資格及資助須確認',signatures=['母校授權人'],**kw)
        doc('english','官方英文能力證明',s,'Application Forms item6',condition='第一語言非英語者',**kw)
        doc('transcript-current','目前學位課程官方成績單正本（發出1個月內）',s,'Application Forms item7',copy_type='original',**kw)
        doc('transcript-prior','先前已取得學位官方成績單正本',s,'Application Forms item8',condition='已取得其他學位者',copy_type='original',**kw)
        doc('study-proposal','Form SP Study Proposal',s,'Application Forms item9',form='uec-uec_form_SP-ver22-pdf',**kw)
        doc('research-ug','Form RP-U Individual Study Proposal',s,'Application Forms item10',form='uec-uec_form_RP-ver23-U-2-pdf',condition='大學部學生',**kw)
        doc('research-grad','Form RP-G Independent Research Proposal',s,'Application Forms item10',form='uec-uec_form_RP-ver23-G-2-pdf',condition='研究所學生',**kw)
        doc('passport','經認證護照影本',s,'Application Forms item11',copy_type='copy',**kw)
        doc('student-id','經認證母校學生證影本',s,'Application Forms item12',copy_type='copy',**kw)
        doc('video-1','3分鐘影片1：學習背景及在UEC學習計畫',s,'Application Forms item13',**kw)
        doc('video-2','3分鐘影片2：JUSST動機、未來／研究規劃',s,'Application Forms item14',**kw)
        doc('supporting','其他支持文件',s,'Application Forms item15',condition='必要時／外校要求時',**kw)
        doc('funding','經費支持證明：獎學金證明或本人／支弁者銀行存款',s,'Application Forms item16',phase=5,condition='自費申請人，錄取後立即提供',**kw)
        doc('tb','Pre-Entry TB Screening clearance',s,'Application Forms item17',phase=5,condition='僅JPETS指定國籍等適用者；不套所有臺灣学生',**kw)
    return rows


def document_requirement(item):
    conditional=item['condition']!='所有申請人'
    name=item['name']+(f"（條件：{item['condition']}）" if conditional else '')
    if item['status']=='reference_only':name='一般參考／2027版未核實：'+name
    urls=[item['evidence']['source_url']]
    if item['official_form_url']:urls.append(item['official_form_url'])
    form_source=source_map().get(item['form_source_id'])
    # Public availability is distinct from the student's programme/year eligibility.
    form_verified=bool(form_source and form_source.get('open_status')=='verified_open'
        and form_source.get('http_status')==200 and form_source.get('sha256'))
    access_labels={
        'verified_public':'已核實公開原檔／官方表單入口',
        'own_document':'自行取得的證明文件',
        'nomination_then_account_by_email':'提名核准後由外校寄送申請帳號',
        'separately_sent_to_applicant':'外校另寄申請人',
        'after_admission_separately_provided':'錄取後由外校另提供；不得推定已取得表單內容',
        'provided_to_nominated_students':'外校明示提供已提名學生',
        'contact_home_coordinator':'官網指定向母校承辦索取；原表尚未取得，非公開限制未核實',
    }
    mapping_note='長崎NICS與淡江本輪／研究生對應仍待確認；此項不代表所有淡江提名者適用。' if item['evidence']['source_id'].startswith('nagasaki-') else ''
    return dict(name=name,copy_type=item['copy_type'],signatures=item['signatures'],
        official_form_url=item['official_form_url'],source_urls=list(dict.fromkeys(urls)),
        needs_confirmation=item['status']!='verified',
        stage=item['stage'],
        conditional=conditional,condition=item['condition'],official_form_verified=form_verified,
        applicability_status='reference_only' if item['status']=='reference_only' else 'needs_confirmation' if item['status']!='verified' or mapping_note else 'verified_current',
        applicability_year=item['applicable_year'],
        applicability_note=f"外校incoming，僅已獲母校推薦者；{item['evidence']['locator']}；{access_labels[item['form_access']]}。{item['timing'] or ''}{mapping_note}")
