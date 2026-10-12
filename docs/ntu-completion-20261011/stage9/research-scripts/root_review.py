from field_worker import Worker
w=Worker('root')
w.fact('1296','a06a135010405636','calendar','2026年正式行事曆列春季3月3日開課、6月16–22日期考；秋季9月1日開課、12月14–18日期考。交換共通頁春季3月2日是未標年概述，不能覆寫2026正式日期或推成2027。','KNU正式2026 calendar；Daegu/Sangju個人接收校區仍待指定；非2027–28','03.03(화)\nSemester Begins',period='older_year_reference')
w.fact('169','7315c11520a069b3','calendar','HKU2026/27秋季2026/9/1開課、12/7–23考試；春季2027/1/18開課、5/8–25考試。春季住宿1/8入住仍tentative、迎新TBC；這些2027春季日期屬2026/27，不改標2027/28。','HKU Academic Information明列Academic Year2026–27，主校通用；Law另有學院安排','September 1, 2026\nJanuary 18, 2027',period='older_year_reference')
w.fact('2','6c4af7d38430a1a0','calendar','September2025版本的2026–27要項列秋季2026/9/9開課、12/23結束；秋迎新/期考及Spring2027主要日期仍TBD。Calendar入口只列三版公布/生效月份，不能當已取得2027–28完整日程。','UVic ICS2026–27 fact sheet，September2025版本，第2實體頁；非2027–28','September 9th,\n2026',page=2,period='older_year_reference')
w.fact('872','c54177df7c8e2ccf','insurance_visa','2025–26交換要項要求加入醫療保險，但列出的USD1355秋季／1849春季明示依2024–25保費且可變動，不能當2027–28價格。其I-20文件與F-1 SEVIS費屬該舊版本程序，個人簽證類別及當期要求仍需錄取文件。','UofSC Columbia exchange factsheet2025–26第3實體頁；保費數值明示2024–25，不作臺灣個案法律或新年度保費裁定','USC students are required to enroll in health insurance.',page=3,period='older_year_reference',theme='safety')
# Each source reason below is specific to the assigned field, preserving identities and dates.
notes={
'1296':{
'calendar':('verified_scoped_reference','已核2026正式日程；2025/26要項及未標年交換概述不能提供2027–28精確迎新、開課及考試日。',['2027–28正式開課/期考/迎新日','個人接收Daegu或Sangju校區'],{'3f121c21dd3c4772':'未標年交換概述僅春3/2、秋9/1，無2027–28完整日程。','94b1fdb82d657e78':'與~eng交換頁同raw SHA，日期概述重用；無新年度完整日程。','a06a135010405636':'正式日曆明列2026；3/3與9/1開課及期考可採原年。','fc2aa4ef221bb72a':'與~eng calendar同raw SHA，為2026日曆，非2027。','e33b81bda85adf09':'2025/2026要項頁1–2為舊年semester/arrival概述，不作2027日程。'}),
'courses':('version_conflict','交換web研究生上限9學分、2025/26 PDF master上限10；本科18一致但最低6只見舊PDF。保留版本差別，英授課表於1/7月提供及需錄取後選課資訊。',['2027–28研課學分上限及本科最低課量','當期英授開課與錄取校區'],{'3f121c21dd3c4772':'交換web本科18/研9、英授1/7月提供；只連2026課表。','94b1fdb82d657e78':'同raw交換web別名，保留研9與舊PDF10差別。','e33b81bda85adf09':'2025/26頁1本科18最低6、master10，非可覆寫web的2027新規。','a06a135010405636':'2026 calendar只有選課日期，不提供exchange課目或學分限制。','fc2aa4ef221bb72a':'同2026 calendar raw別名；無exchange課目及先修/學分規定。'}),
'housing':('version_conflict','web稱自動雙人房，2025/26要項則要求另上網申寮並於申請後保障；一般宿舍房型頁未提供2027交換分配。保留申請程序差別及校區未知。',['2027–28申寮程序/截止/房價','Daegu或Sangju接收與實際房間'],{}),
'insurance_visa':('version_conflict','交換web NHIS71520/月與2025/26 PDF75490/月為不同版本估價；一般Student Health Insurance是校內給付，不能當NHIS替代。D-2/ARC舊程序不作個人當期裁定。',['2027–28NHIS適用費率/豁免條件','錄取文件/個人簽證與ARC材料'],{})},
'1306':{
'courses':('verified_scoped_reference','2027–28交換要項課量及Nursing不開已採。MSU incoming web另寫Media/Theater/Film/Photo通常不開，與新版有限選課須按科系核；一般住宿頁不是課目授權。',['2027秋/2028春實際課目、作品集/先修與空位','錄取後My Global Connection選課指示'],{}),
'housing':('verified_scoped_reference','2027–28交換要項只說usually able預留及非強制住校。一般degree admission保證/30學分規則與Bozeman租屋名單不構成交換2027個人床位保證。',['2027–28房價/截止與個人room offer','個人合約與入住日期'],{}),
'insurance_visa':('external_information_required','錄取後DS-2019/J-1或ISEP分支及MMR/TB程序已有來源；本批沒有2027–28保險條款/費率與臺灣個人簽證核准資料，需錄取文件與適用身分。',['2027–28保險方案/費率與豁免','錄取後DS-2019或ISEP文件、個人簽證材料'],{})},
'169':{
'calendar':('verified_scoped_reference','已核2026/27主要日程與TBC/tentative項。Law學院為2026/27課程/迎新概述，不能提供2027/28完整精確日程。',['2027–28精確開課/考試/迎新與入住日期'],{}),
'courses':('verified_scoped_reference','已採2026/27課量、50% host faculty及院系限制。Law頁混列2025/26 electives與2026/27指引，須分學院/協定，不保證2027/28課目。',['2027–28課目、院系協定涵蓋及先修空位'],{}),
'housing':('verified_scoped_reference','2026/27申寮可在初申取得10位refNo後開始且不保證。Law只導向CEDARS，Academic頁入住/搬出是舊學年且部分暫定。',['2027–28申期/房費/入住日','CEDARS個人room offer與接收期限'],{}),
'insurance_visa':('external_information_required','已核Notice後申visa及臺灣申請分支、Law8–10週與IAO至少10週估期差別。2023/24系統手冊不是新保險條款或個人visa裁定；需當期錄取及個人資料。',['2027–28保險要求/費用','录取Notice/個人身份及簽證材料'],{})},
'2':{
'calendar':('verified_scoped_reference','2026–27要項秋季日期已採、春季多項TBD。Calendar入口為刊行規則，ICS為未標年term概述，沒有2027–28精確日期。',['2027–28開课/期考/迎新日'],{}),
'courses':('verified_scoped_reference','2026–27要項舊課程限制可供參考；既有ICS未標年課量亦保留。當期可選課目、graduate審批與先修override需錄取後指示。',['2027–28實際課表/先修審批','母校認抵及錄取後選課指示'],{}),
'housing':('verified_scoped_reference','ICS一般住房及2026–27要項保留抽籤/候補、最低4.5units等限制。Continuing Studies頁屬ELC付費語言方案，不能當ICS住宿保障。',['2027–28房價/申期與個人room offer','入住/搬出及最低課量當期規則'],{}),
'insurance_visa':('external_information_required','ICS與2026–27要項GuardMe第一4月及估價已核；Continuing Studies屬另一programme。IRCC個人entry/study permit及當期保險費率不能由既有概述決定。',['2027–28GuardMe/BC MSP適用費率','依國籍/停留期/錄取文件的個人入境與study permit條件'],{})},
'872':{
'calendar':('verified_scoped_reference','Registrar2027–28正式開課/期考日已採，秋break仍tentative。2026–27、2028–29與2025–26來源維持各自年份；outgoing申請頁不是incoming迎新日。',['2027–28incoming orientation/arrival確認','tentative Fallbreak最後公告'],{}),
'courses':('verified_scoped_reference','incoming Columbia共通課量/先修/空位已有參考；此候選沒有2027–28實際授課清單或協定院系授權。',['2027–28交換可選課目/先修空位','DMSB或general協定與院系批准'],{}),
'housing':('verified_scoped_reference','2025–26交換要項住校/保證但不保偏好已採。一般housing首頁和hall目錄不確認交換2027分配；兩目錄URL同raw。',['2027–28交換申寮/費率/入住規則','個人實際房間与offer'],{}),
'insurance_visa':('external_information_required','舊要項明列保險義務，數值為2024–25；ISSS首頁只導引移民服務及政策通知，outgoing頁不可作incoming簽證/保險。需當期方案及錄取/個人簽證文件。',['2027–28保險方案/費率/豁免','錄取後I-20或DS-2019分支與個人官方入境要求'],{})}}
# SID-level topic contexts; combined with field-specific conclusion makes every rejection/adoption explicit.
contexts={
'256913ee310b0a2c':'一般Daegu/Sangju宿舍設施/房型，非exchange2027分配；沒有NHIS/visa規定。','505179bf3abeacfb':'與~eng宿舍頁同raw，只有一般房型容量；不作exchange保障或NHIS。','494c5f70aaa6cbc9':'一般校內Student Health Insurance給付，非NHIS交換費率；無申寮規則。','d47a9f2b36ce2755':'與life01同raw的一般校內健康給付，無交換申寮/visa或NHIS。',
'0ec4b764e9dee461':'MSU incoming course restrictions及term課表不保證；通常Media/Theater/Film/Photo不開，需與2027–28有限名額原文分開。','27766577529fcb47':'一般international degree admissions住房/本科保證與30學分規則，不能套非degree交換；不是可選課目。','d5fb82aee97b2949':'MSU交換要項明列2027–28，保留課量/院系限制與usually able住房、保險項原範圍。','fcd91787b6ac97b8':'未標年incoming申請與錄取後DS-2019/MMR/TB；非當期課表/住房offer/個人簽證核准。','e228afb8c1d18986':'Bozeman一般校外住房選項名單，未給2027 exchange床位或價格/申期保證。',
'7315c11520a069b3':'Academic Information明列2026/27日程/選課/入住，部分日期TBC/tentative；不當2027/28完整規則。','da046beaf1ebd796':'Law incoming學院限制/住房導鏈/簽證程序與估期；分別列2025/26electives與2026/27guidance，不代表全校新年度。','4f7a8732b0734225':'HKU2026/27 application，住房不保證/初申refNo及Notice後visa至少10週；不當2027/28申期或個人核准。','0f18929475fd076e':'2023/24exchange申請系統手冊，只能辨流程/身分，非2027/28保險、visa費率或法律決定。',
'08a49aa0f1ff0b82':'Calendar入口列May/Sept/Jan版公布生效規則；不含2027/28精確授課/考試日。','0d011084611eac6e':'UVic ICS未標年incoming共通programme/term/課量/住宿及移民導引，個別新年度/permit未定。','6c4af7d38430a1a0':'UVicICS2026–27要項September2025版，保留頁2日程TBD、頁3課程、舊GuardMe與housing條件；非2027/28。','56a8ba717772bda8':'一般housing/transport只說校寮空間有限應早申，無當期房間保證或insurance/visa要求。','c4f1b6a286f39b69':'Continuing Studies/ELC付費語言方案housing，不套ICS交換住宿。','26dee9a71a14db2e':'ContinuingStudies international programs屬付費語言/訪問programmes，非ICS exchange移民與保險規定。',
'2c8ca49935e3abd7':'教職員develop an exchange programme的agreement資訊，非incoming學生行事曆/個人住宿。','3f2c632bb76a0750':'UofSC outgoing exchange partner申請，方向錯配，不能採incoming行事曆/住房/visa。','3f801ed5fa557ac2':'UofSC outgoing International Business exchange，非incoming Columbia個人行事曆或visa。','3f6d61adc0e07225':'正式2028–29calendar，比目標晚一年；不覆寫已核2027–28。','c2191014c8e7cd87':'Registrar年份/校區/term入口索引；具體2027–28已從該年正式页核。','c0b196e44e13accb':'Columbia incoming共通exchange方向正確，但未列2027–28個人課表/住房offer/迎新或保險費率。','c54177df7c8e2ccf':'2025–26交換要項舊期；保險數值明示2024–25，住房條件及其他程序不升為2027–28。','c54a8701cb213c87':'Registrar2026–27正式calendar舊年，不能代2027–28。','fa50768d5e8d44aa':'Registrar2027–28正式Columbia完整semester日程已核，Fallbreak標tentative，無incoming orientation確日。','639b3fa2667fcd50':'一般first-year/continuing及LLC hall目錄，無交換個人床位/2027費率。','fcbb9dbcf7bd4536':'與residence-halls目錄同raw，非exchange2027房間offer。','6bde8cd9bda5a77f':'一般housing服務宣傳，25buildings与目錄28halls不是交換床位承諾，無當期交換申期/費率。','2123b6ba11113dde':'ISSS首頁服務/政策通知導引，無2027保險費率或個人簽證核准；政策摘要未取得實際政府文件，不作法律結論。'}
for pid,fields in notes.items():
 for field,(outcome,note,missing,specific) in fields.items():
  sids=w.rows[pid,field]['readable_candidate_source_ids'];sn={sid:specific.get(sid,contexts.get(sid,'既有'+field+'來源：'+note)) for sid in sids}
  # KNU same-source notes add both positive exchange context and correct generic page rejection.
  if pid=='1296':
   for sid in sids:
    if sid in ['3f121c21dd3c4772','94b1fdb82d657e78']:sn[sid]='未標年KNU incoming exchange共通頁；'+note
    if sid=='e33b81bda85adf09':sn[sid]='2025/26要項頁1–2，原年份及交換身分已核；'+note
  w.finish(pid,field,outcome,note,sn,missing_items=missing)
print('root',len(w.decisions),'facts',sum(o['observation_id'] not in w.base_ids for s in w.schools.values() for o in s['observations']))
