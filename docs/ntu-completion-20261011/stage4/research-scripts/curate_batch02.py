from research_curator import Curator
c=Curator();f=c.fact;d=c.decision;b=c.body_review
sid='47e8fe28264291e8';quote='Students who wish to participate in the Kindai University Exchange Program must be nominated'
f('1187',sid,'eligibility','近畿交換流程要求母校coordinator先提名；提名時提供姓名、學業成績、語言能力、參加計畫與期間。未提名前不直接回答個人詢問，依母校窗口辦理；頁未標2027年度。','Kindai Exchange Program Flow官方連結試算表；未標年度',quote,locator='Row6 Nomination')
f('1187',sid,'documents','近畿列交換申請準備：在學證明、成績單、語言證明、計畫及期間、預選課、COE必要資訊、另行指定文件；個人申請方法提名截止後才通知。指定健康證明及抵日資料屬通過申請後，不混作首次申請文件。','Kindai Exchange Program Flow；申請vs錄取後程序；未標年度',quote,locator='Rows7 Application/8 Pre-arrival')
f('1187',sid,'deadlines','近畿公開流程僅稱春入學提名資訊8月寄合作校、秋入學1月寄；個人申請資訊提名截止後通知且逾期不受理。這不是精確提名／申請截止日，不能由月曆軸推定日期。','Kindai未標年度流程表；公開通知月份，截止細節須母校提名程序',quote,locator='Rows6/7: notification months and post-nomination instructions')
f('1187','9aacce63461a2efe','language','近畿Program A課程表明列TOEFL iBT3.5（61/120）、IELTS6.0、CEFR B2或同等；保留原寫法不自行換算。不能套所有交換計畫；同頁課程表依2025curriculum，不代表2027–28版本已定。','Kindai Program A List A；語言數值未標年度／課表基於2025curriculum','Program A',period='undated_public_reference',locator='Introduction row2 language, row3 curriculum notice')
for field in ['eligibility','language','deadlines','documents']:
 sids=[sid]+(['9aacce63461a2efe'] if field=='language' else ['3aaf2de384ec340d'] if field=='documents' else [])
 for source in sids:b('1187',source,[field],'全部可用正文已讀；提名、個人申請、錄取後程序分列。ProgramA數值不套其他計畫；Study at Kindai首頁僅索引。')
 d('1187',field,sids,'reviewed_reference_added_partial_scope','已讀本欄全部既有可讀候選；公開清單與流程可作原範圍參考，未核新期完整版；精確截止仍需正式提名通知。')
sid='c3666690cd8586cd';quote='Exchange Program Fact Sheet AY2025-2026'
f('24',sid,'documents','早稻田2025–26factsheet的首次申請文件與院系資格清單須另讀Application Guidelines及List of Schools，本PDF沒有完整清單；COE財力證明舊門檻為每月120,000日圓，且需由學校代申請COE後本人辦簽證，不能把COE文件當全部交換申請文件。','Waseda Exchange AY2025–26 p1/p3；一般申請與COE文件分開',quote,page=1,period='older_year_reference',locator='p1 Required Documents -> Application Guidelines; p3 Defraying Expenses')
f('24',sid,'cost','早稻田2025–26文件估新宿住宿每月80,000日圓，另生活費80,000日圓，依個人生活改變；每月120,000日圓為COE最低財力證明，不是合計實際費用。國保舊估通常2,000日圓/月以下，非2027正式收費。','Waseda AY2025–26 p3財力vs p4生活估算；原年度',quote,page=4,period='older_year_reference',theme='cost',locator='p3 COE funds; p4 Cost of Living/Health Insurance')
for field in ['eligibility','documents','cost']:
 b('24',sid,[field],'完整4頁factsheet已讀；2025–26舊版，院系資格及完整文件均指向Application Guidelines；生活估算與COE財力額度分開。')
 d('24',field,[sid],'reviewed_previous_cycle_reference','本候選全文已讀，為舊版及後續官方指南索引，不表示新期完整資格／文件或費率核實。')
for field in ['eligibility','deadlines','cost']:
 sources=['c3e67885ed504ff5']+(['80462584842a70ea'] if field=='eligibility' else [])
 for source in sources:b('1299',source,[field],'完整正文已讀；保險適用學分與UCAN學生雇員、Approved Sponsor分別有範圍，不是交換入學資格。Fall2026 waiver日期不是交換申請截止。incoming首頁僅一句提示。')
 d('1299',field,sources,'reviewed_reference_partial_scope' if field=='cost' else 'wrong_scope_no_exchange_field_detail','完整保險政策正文與本欄候選已讀；保險收費責任可參考但沒有金額，12/9/1學分是保險觸發，8/2–10/23是2026豁免窗口，均不能代替交換資格或截止。')
f('1299','c3e67885ed504ff5','cost','NJIT對F1/J1國際生通常自動加收校方保險費；非Approved Sponsor名單者不得豁免。UCAN費用補助僅符合規定的graduate employee，不自動適用一般交換生；此頁沒有2027–28保費金額。','NJIT保險政策；UCAN員工與一般F1/J1身分分開，未標新期費率','Student Health Insurance',locator='Automatic charges/UCAN eligibility/Waiver restrictions')
sid='82e61715a66fdb22';quote='Kumamoto University - Fact Sheet 2025/26'
f('1293',sid,'eligibility','熊本2025/26短期交換要求大二以上，開放文、法、教育、理、工；醫、藥及資訊學院不開放。官網更明示合作校全時外國學士學生、保留母校全時學籍；舊文件不提升為2027新期。','Kumamoto2025/26 factsheet p2，院系及學士短期交換限制',quote,page=2,period='older_year_reference',locator='p2 Grade Requirements/Faculties/Restrictions')
f('1293','c8985c9d9bfa6cba','language','熊本短期交換官網：E Course非英語母語者需TOEFL iBT61以上影本，亦接受IELTS但此頁無IELTS數字；不接受中國CET、印尼ELPT或教授證明信。J Course需JLPT N2同等以上，也不接受教授信替代。','Kumamoto本科Short-Term Exchange未標新期；E/J分開','A letter from a professor',locator='E/J Course Eligibility and proof restrictions')
f('1293',sid,'deadlines','熊本2025/26factsheet舊表列秋2025申請4/18、春2026提名2025/10/10、申請11/14；秋提名同一文字層呈3/7與3/14兩日期，未視覺核清修訂前不選其一。全為舊期，不能改標2027。','Kumamoto2025/26 factsheet p2；秋提名文字層疑修訂版本',quote,page=2,period='version_conflict',locator='p2 Nomination Deadlines/Application Deadlines')
f('1293',sid,'cost','熊本2025/26國際宿舍C/D棟單人房共用設施：17,000日圓/月房租、一次10,000日圓deposit；生活估宿舍80,000/月、外租100,000/月；國保舊估3,000/月。這些是原年度與住房型態估算，非2027收費。','Kumamoto2025/26 factsheet p2 housing/living/insurance；JPY與monthly明列',quote,page=2,period='older_year_reference',theme='cost',locator='p2 General Aspects fees and estimates')
f('1293','c8985c9d9bfa6cba','documents','熊本官網要求向母校outbound窗口取得申請文件，不收個別學生郵件；此頁沒有完整文件清單。語言證明條件有公開明文，不能將未見全清單當成全校未公告或任意改用教授信。','Kumamoto本科Short-Term Exchange Application Package；未標年度','A letter from a professor',locator='Application Package: institutional coordinator, no individual mails')
for field,sources in {'eligibility':[sid],'language':[sid,'c8985c9d9bfa6cba'],'deadlines':[sid],'documents':[sid,'c8985c9d9bfa6cba'],'cost':[sid,'851932ac2d062f5b','ff314d4846143eb8']}.items():
 for source in sources:b('1293',source,[field],'全部候選正文已讀；2025/26factsheet、未標年度E/J語言條件、住宿首頁索引及外租生活規範分開。宿舍首頁無可用租金表，需下一層連結；非全校未公告。')
 d('1293',field,sources,'reviewed_reference_added_partial_scope','本欄全部既有可讀候選正文已讀；保留舊版與官方常年範圍，需後續申請文件／最新宿舍費率連結，未核完整新期。')
c.save();print('observations',sum(len(s['observations']) for s in c.schools.values()))
