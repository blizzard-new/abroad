from research_curator import Curator,ROOT
import json
c=Curator();f=c.fact;b=c.body_review;d=c.decision;q=json.loads((ROOT/'priority-source-roster.json').read_text())
notes={'371':'原7正文全讀。FDFA簽證不是交換初申，HousingAnywhere外國平台手續費／市況非伯恩校方生活預算；官方寮頁明示不供校方寮不保證私人床位，跟讀healthinsurance/partner明細。', '366':'原5正文全讀。housing/insurance/courses與學術初申分開；NTU明列IAPGeneral伙伴而非Businessexchange，Business優先不能套全校交換。選課April/November不是exchange申請deadline，完整申請頁已跟讀。','361':'原9正文全讀。1165為梨花學生OUTGOING，不能把3.0/4.3、TOEFL72等套臺大incoming；1142接待male/female2.5/4.0才合scope。2024行事曆、visa到校／打工TOPIK非交換初申。'}
for pid,note in notes.items():
 for field,sids in q[pid]['fields'].items():
  for sid in sids:b(pid,sid,[field],note)
  d(pid,field,sids,'reviewed_original_body_identity_split_and_followups',note)
sid='1af3aacd606df1b1';quote='The University of Bern does not offer accommodation for students'
f('371',sid,'housing','伯恩校方明示不提供學生住宿、不保證私人學生寮。Studentlodge A較便宜但不能早於1/31或7/31契約末終止；B通常月底可終止，若booking選離開日仍不能早退，不確定者官網建議B且不先指定離開日。頁未提供實際租金。','伯恩incoming Accommodation-living未標年；校方與private provider分開',quote,theme='housing',locator='Student lodgings disclaimer / Contract A vs B')
sid='734ce858b80bc5b6';quote='Visa requirements for entry into Switzerland'
f('371',sid,'insurance_visa','瑞士FDFA2026/2/1頁区分Schengen C（90日／180）與超過90日National D，D須居住州移民機關授權；附件依居住國管轄不同，頁Taiwan入口未列具體整套學生文件。這是簽證流程非伯恩交換初申；不得假定台灣短免簽涵蓋整學期。','瑞士FDFA2026公告入口；一般簽證類型與Taiwan-specific待核',quote,locator='National visa >90 days / cantonal authority / country-specific docs')
sid='8e80590243b9f904';quote='Incoming Exchange Students'
f('366',sid,'eligibility','UW-Madison須正式協議母校提名，官方名單NTU屬IAP General Exchange；Business/Engineering/CALS是另協議辦公室，不能把WSB優先或非協議VISP收學費條件套臺大一般交換。現頁無GPA／語測門檻數字，須正式app條款。','UW-Madison incoming/IAPGeneral明列NTU；未標學年',quote,locator='Becoming an exchange student and partner lists')
sid='670862f9956753fd';quote='Exchange – Course Enrollment'
f('366',sid,'courses','UW-Madison一般交換專業學院醫／獸醫／藥／護理／法／教育幾乎不開、各課依先修餘額；商學由BusinessExchange優先，IAP不能預設可選。Engineering須app表明、CS另enrollmentrequest、Economics另form。全日制drop後本科至少12credit／研8；J1每學期僅一online課可算full-time要求，course fees／研究另核。','UW-Madison common CourseEnrollment未標年；IAP非Business优先',quote,theme='academics',locator='Course Restrictions / popular subject requests / online and minimum loads')
f('366',sid,'deadlines','UW-Madison CourseEnrollment秋課April／春課November邀請，錄取才寄時間；這是選課不是母校提名／exchange初申deadline，不能用其補空申請期限。','UW-Madison course registration timeline未標年度',quote,locator='Enrollment invitation issued after exchange acceptance')
sid='23ede4fe4c348d98';quote='Exchange – Housing'
f('366',sid,'housing','UW-Madison學生自行找房，校內稀少不保證且lottery非先到先得。Fall-only年約可提前終止但不退deposit；spring約一學期；Jan–Dec交換May退房Aug再入、夏不開給exchange。校外常年約需自行找到subletter，不套免費解約；宿舍要meal plan。','UW-Madison exchange housing共通未標年、契約時段與summer明示',quote,theme='housing',locator='Residence hall contracts / calendar-year gap / offcampus leases / meal plan')
sid='58da337efb706b2a';quote='Exchange – Insurance'
f('366',sid,'insurance_visa','UW-Madison國際exchange要SHIP，豁免按母校／組織整體審定非個人自有旅保即免；美國公民domestic special不能買該SHIP是另一身分。頁鏈當期SHIPcost未直接列金額，renterinsurance建議非強制。','UW-Madison incoming保险共通；SHIP当期费率另linkedofficial頁',quote,locator='SHIP mandatory and institutional waiver vs US citizen exception')
sid='9c179101a5632cb0';quote='International Exchange / Visiting Students'
f('361',sid,'eligibility','梨花incoming限認可大學全日制本科／研，male與female皆可、母校至少一學期、GPA2.5/4.0（75/100）；officialtranscript申請時要有，研另研級成績。須母校提名先於學生app，不把梨花OUTGOING3.0/4.3或「女子」校名套僅女性。','梨花OIA1142 Incoming common未標學年；與OIA1165OUTGOING区分',quote,locator='Eligibility / Nomination vs separate Fee-paying Visiting')
f('361',sid,'language','梨花incoming頁只說可用English或Korean修課的能力，未列考試最低數字；outgoing頁iBT72/IELTS6與2年/7月底規則是梨花學生出國，不当臺大入學門檻。','梨花OIA1142 Incoming vs 1165 outgoing language standard；未標學年',quote,locator='Incoming language ability, scope mismatch of outgoing standard')
sid='e90d5f64cefc60a0';quote='I-House'
f('361',sid,'housing','梨花I-House五棟約770人含exchange/語校/訪客，有健身／電腦／洗衣與每層kitchenette；770是總住宿容量非臺大甄選名額、無個人配房保证或當期費率。其他EHouse／法学院／醫學Magok寮不是人人可選。','梨花CampusLife Housing未標年度；I-House含exchange',quote,theme='housing',locator='I-House versus degree-specific other dormitory buildings')
c.save();print('observations',sum(len(s['observations']) for s in c.schools.values()))
