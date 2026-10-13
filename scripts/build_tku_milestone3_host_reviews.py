"""Content-reviewed TKU host references; no home quota or workflow promotion."""
import gzip
import json
from bs4 import BeautifulSoup
from tku_capture_io import BUNDLE, read_bytes


def source(key):
    return json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(key+'.json.gz'))))


def fact(s, value, needle, year, page=None, verified=False, role='host_incoming', note=''):
    if page is None and s.get('pages'):
        matched=[p['page'] for p in s['pages'] if needle in p['text']]
        assert len(matched)==1,(s['id'],needle,matched)
        page=matched[0]
    text=s['pages'][page-1]['text'] if page else s['text']
    assert s.get('http_status')==200 and not s.get('error') and needle in text, (s['id'],needle)
    start=text.index(needle)
    return dict(value=value,status='reference_only',source_period_verified=verified,
        review_scope='content_reviewed_host_reference; TKU nomination, agreement track and current quota unverified',
        reason='已讀接待校官方正文；'+note+'淡江本期提名、院系協議與母校申請流程未核實，不能轉成開放名額、母校資格或申請中心文件。',
        evidence=[dict(source_id=s['id'],source_url=s['source_url'],checked_at=s['checked_at'],
            content_sha256=s['sha256'],applicable_year=year,application_round='Host programme only; TKU cycle mapping unverified',
            locator=f'PDF p.{page}' if page else 'Actual HTML/DOCX body; exact retained quotation',
            quote=text[start:start+850],role=role)])


def main():
    rows=[]
    def add(n,fields):rows.append(dict(id='tku-sister-'+str(n),fields=fields))
    u=source('cf48d77d5a265b7e96e6cceb');assert len(u['pages'])==8 and 'Fact Sheet 2026/27' in u['pages'][0]['text'] and 'July 2026' in u['pages'][0]['text']
    uy='2026/27 host incoming Fact Sheet, updated July 2026; not TKU 116 quota'
    def uf(value,needle,page,note=''):
        # Cover is physical p.1; body footer numbering starts at 1 on p.2.
        matched=[p['page'] for p in u['pages'] if needle in p['text']]
        assert len(matched)==1,(needle,matched)
        return fact(u,value,needle,uy,matched[0],True,note=note)
    add(329,dict(
        study_period=uf('2026/27：第一學期2026/9/7–2027/1/29，第二學期2027/2/1–6/25；各院系精確日期可能不同。不能當作2027秋交換行事曆。','7 September 2026',2),
        host_deadline=uf('p.2「Erasmus+ Programme」表列一般第一學期／全年2/15–5/15、第二學期9/15–11/15；醫學／護理所有期別須第一時段2/15–5/15申請，Massana須2/15–4/20。TKU非Erasmus雙邊track是否沿用此表尚待核對，不視為淡江本期截止日。','NOMINATION & APPLICATION DEADLINES',2,'表頭明示Erasmus+，TKU track對應未核實。'),
        host_nomination_deadline=uf('Erasmus+表列第一學期／全年母校提名2/15–5/1，第二學期9/15–11/1；醫學及Massana即使第二學期亦須第一期提名。雙邊TKU適用表尚未確認。','First semester or whole year',2,'Erasmus+截止表範圍保留。'),
        host_eligibility=uf('須母校正式提名，只接受協議指定學科，並須母校相近學科在籍及相應背景。博士／實習不可走此提名表。','An official nomination',3),
        latest_forms=uf('母校以接待校寄給partner的線上表提名；學生收到通知後於sia.uab.es Incoming exchange students申請。現有簡章不等於已取得TKU提名登入權限，未加入母校申請文件catalog。','Nominations must be done',3),
        host_language=uf('主要加泰隆尼亞語／西班牙語、部分英語；每院系另有NEW LANGUAGE REQUIREMENTS，不能推定統一B2或IELTS分數。考試語言依課程及教師同意。','Lectures are mainly taught',4),
        department_scope=uf('至少50%學分在協議指定接待院系，其餘跨院須有餘額及限制；碩士課須協議涵蓋碩士層級且碩士主任最後批准。','Minimum 50%',5),
        course_restrictions=uf('碩士交換最高30 ECTS；多數院系不接受純論文研究，須另洽；博士／實習須直接與接待部門協議。並非全部課程對交換開放。',"Admission to master's level subjects",5),
        insurance=uf('須自備涵蓋疾病、意外及遣返醫療險；補充意外／責任險費€4.02明示僅2025–26歷史價格，不作2026–27或2027固定費用。','Complementary insurance',5),
        housing=uf('校內Vila Universitària與校外房源分開向住宿服務申請；簡章沒有每位床位保證或當期價格。','UAB offers on-campus accommodation',7)))
    saar=source('9749a94a28c96debba93661f');assert len(saar['pages'])==2 and 'Fact sheet 2027/28' in saar['pages'][0]['text']
    sy='2027/28 Overseas exchange host Fact Sheet; TKU nomination unverified'
    def sf(value,needle,page=1):return fact(saar,value,needle,sy,page,True)
    web=source('8796d981bc8207e920488d85')
    saarfacts=dict(
        host_deadline=sf('海外交換申請冬學期6/1、夏學期12/1；為接待校期限，沒有核實淡江母校仍收新申請。','01 June'),
        host_eligibility=sf('海外交換要求母校大二至大四，需足夠德語或英語；不把Erasmus、freemover或degree申請混入Weltweit。','2nd to 4th year students'),
        host_language=sf('多數德語課B1，心理學德語C1；英語課B1。另短期德語密集班最低A2.1且不收初學者，與一般課語言門檻分開。','Language of instruction',2),
        department_scope=sf('一般大學部開放；醫學與資訊可能須系所批准，由Welcome Center申請後代洽。碩士課僅對母校碩士生開放。','Disciplines open to exchange students',2),
        study_period=sf('2027/28冬迎新2027/10/6、上課10/18–2028/2/11；2028夏迎新4/3、上課4/10–7/21。','Academic Calendar 2027/28'),
        course_schedule=sf('下期課程每年7月與2月發布，申請前舊學期課只能參考，不保證同課再開。','Course schedules',2),
        costs=sf('沒有學費；註冊費€122.60僅明示截至2026冬的參考，含Germany交通票，不把舊價格當2027確定費。','122,60 EUR'),
        insurance=sf('註冊須足額醫療險：德國制度約€130/月或足額私人保險；費用是估計非固定帳單。','Sufficient health insurance'),
        housing=sf('海外學期交換可保證住宿，實習可能不同；仍須按時另填住房申請，未填不能保證。','Housing is guaranteed',2),
        housing_deadline=fact(web,'Weltweit宿舍申請冬學期7/15、夏學期12/31；網頁未載獨立年度，與2027/28簡章住宿保證及接待校6/1、12/1學籍申請分開。','Die Fristen für die Wohnheim-Bewerbung','undated Weltweit housing rule, checked 2026-10-11; year not independently stated'),
        living_costs=sf('接待校2027/28估每月€992，包含租金、食物、保險、休閒，個人支出可能不同。','992 EUR',2),
        latest_forms=fact(web,'提名後收到Zulassungsantrag連結；另交母校成績單、在籍證明、課程清單、護照及選用德語密集班表。課程表與德語表本次可開啟並讀正文；模板依2027/28連結頁使用。課程表的2025/26與2024/25課表及€180短期語言班費僅舊例，不當2027價格；不作淡江申請表。','Notenübersicht','2027/28 linked portal context; course template has 2025/26 historical examples',verified=True))
    for sid,needle,year in [('9d4432fb44b4f878461db0eb','Winter term 2025/26','2025/26 and2024/25 historical course examples in portal-linked preliminary template'),('b431e8bdb16ab542060c675f','For Visiting Students ONLY','undated optional course template linked from Weltweit 2027/28 portal')]:
        saarfacts['latest_forms']['evidence']+=fact(source(sid),'',needle,year,verified=True)['evidence']
    add(284,saarfacts)
    n=source('ab238e54713add021ae723c4');assert n['title'].startswith('2027年度春学期')
    ny='2027 Spring NICS semester/year incoming; TKU nomination unverified'
    def nf(value,needle):return fact(n,value,needle,ny,verified=True)
    nfacts=dict(
        host_eligibility=nf('非日本國籍；母校可責任推薦、有足夠日語聽課能力；至2027/3至少母校在籍一年（含預期），交換結束前保有母校學籍。','日本国籍を有しない者'),
        host_language=nf('要求可無礙修日語授課課程的能力；正文未列統一JLPT分數，不能補猜N2或N3。NICS與以英語授課、面向北美歐洲的JASIN分開。','日本語による授業を受ける'),
        host_deadline=nf('接待校2027春NICS出願2026/10/31郵戳有效；超額會調整接待人数，不能轉成淡江可申請名額或母校截止日。','2026年10月31日'),
        latest_forms=nf('FormA線上申請、簽名誓約書、照片、FormB日文動機書、FormC財力支弁、FormD推薦、FormE學生及醫師健康表、英文原始成績單、英文銀行證明與護照影本。8份公開表／指南皆HTTP200並實讀；舊檔名不代表過期，依2027春頁明示使用。FormB日文500–1000字與英譯500–1000words/English-or-Japanese矛盾、正文照片3張與指南不可上傳時2張矛盾，待接待校確認。','提出書類の内容'),
        study_period=nf('2027/3中旬抵達，選半年或一年；抵達後不能由半年延一年。誓約書明載半年2027/3–8、一年2027/3–2028/2；JASIN Early Assessment至12月不能套用NICS。','半年から１年に延長することはできません'),
        costs=nf('交換身分學費免除，一般留學生另付學費，不混用。實習／課外活動費半年JPY50,000、一年53,100；行政半年15,000、一年20,000；另加入寮、寮費、餐費。繳款期限官方明示1月下旬另通知，已付款原則不退。','2027年度（春学期）の納入金内訳表'),
        housing=nf('第一學期原則全員住校方安排アンペロス；一年學生第二學期可自找房並依日退已付第二學期寮費。房型不保證照願望，316室是全寮房數而非淡江名額。','原則として最初の1学期は全員'),
        housing_costs=nf('北側雙人JPY21,000/月、入寮20,000；南側單人42,000/月、入寮30,000，首末按日；餐費30,000/月，入住至6月底必須早晚兩餐，7月起可自炊。不能只列房租當完整住宿總費。','（21,000／月 × 滞在月数）'),
        insurance=nf('須三種保險：學研災及留學生生活綜合險含在實習費；日本國民健康險抵日另辦、估JPY2,000/月另繳。海外旅行險是強烈建議而非第四項明示必繳。','次の3つの保険'),
        transport=nf('指定到達日於福岡機場接機、原則專車至學校／寮，包含行政費；不使用不退，並非自由日期保證接機。','福岡空港'),
        course_restrictions=nf('NICS每學期至少12學分，可含JASIN英語課並選部分一般部課；合計不超過25，有部分科目不可修。','1学期に12単位以上'),
        living_costs=nf('交換財力證明半年至少JPY500,000、一年至少1,000,000；一般留學生70萬／140萬不同。FormC另列生活每月至少60,000，這是財力支弁資料而非現行全費用估計。','交換留学生の場合500,000円'))
    attachment_ids=[]
    index=json.loads((BUNDLE/'host_census_capture_index.json').read_text())
    for r in index:
        if r['id']!='tku-sister-34':continue
        for m in r['sources']:
            if 'Sample_' not in m['source_url'] and any(k in m['source_url'] for k in ['FormA_guide','written_pledge','FormB_Essay','FormC_Financial','FormD_Recommendation','FormE1_Healthform','FormE2_Healthform','/form/intl_application/']):
                a=source(m['id']);assert a['http_status']==200 and not a.get('error')
                attachment_ids.append(dict(source_id=a['id'],source_url=a['source_url'],http_status=a['http_status'],local_file=a.get('local_file'),sha256=a['sha256'],checked_at=a['checked_at'],content_reviewed=True,applicable_year='2027Spring linked portal; FormA and pledge explicitly print Spring2027; remaining templates are intrinsically undated'))
                if 'written_pledge' in a['source_url']:key,needle='study_period','March ～ August, 2027'
                elif 'FormB_Essay' in a['source_url']:key,needle='latest_forms','500 – 1,000 words'
                elif 'FormA_guide' in a['source_url']:key,needle='latest_forms','NICS'
                elif 'FormC_Financial' in a['source_url']:key,needle='living_costs','60,000 JPY'
                elif 'FormD_Recommendation' in a['source_url']:key,needle='latest_forms','academic advisor'
                elif 'FormE1_Healthform' in a['source_url']:key,needle='latest_forms','For the student'
                elif 'FormE2_Healthform' in a['source_url']:key,needle='latest_forms','Tuberculin Skin Test'
                elif '/form/intl_application/' in a['source_url']:key,needle='latest_forms','Application Form for Spring 2027'
                else:continue
                nfacts[key]['evidence']+=fact(a,'',needle,'2027Spring portal-linked template; body undated except pledge',verified=True)['evidence']
    assert len(attachment_ids)==8
    nfacts['latest_forms']['attachment_checks']=attachment_ids
    add(34,nfacts)
    vel=source('3d847b66bfd4fbaba9db511e');vy='undated incoming exchange FAQ; checked 2026-10-11; 2027 degree-admission footer excluded'
    def vf(value,needle):return fact(vel,value,needle,vy,note='FAQ本身未載年度，費額有效期未知。')
    add(212,dict(host_eligibility=vf('只透過母校國際處辦理交換申請；收到接待通知不代表淡江當期新甄選開放。','processed only through'),latest_forms=vf('可online或offline申請；online列印由母校國際處簽署，申請及佐證以母校承辦email軟本送出、免紙本。公開表模板尚未核實，不能套用degree表。','Soft copy of Application'),department_scope=vf('僅分配一系修課／project，可按主修選偏好，不能自動跨多系。','any one department'),costs=vf('協議交換免接待學費，住宿餐費自付；除先行明確確認外無stipend／scholarship。','need not pay any Tuition Fee'),housing=vf('FAQ稱到達前分配校內住房，房型價格為未載年度參考，仍待接待校確認個人安排。','Will be allocated before your arrival'),housing_costs=vf('雙人共用AC房每月€150、獨立AC房€250，含接機、印度餐食、WiFi、gym及校舍與住宿交通；到校以INR付，不自行換算即時匯率。','150 Euros/Month'),transport=vf('應至少7個工作日前提供航班抵達資訊；接機承辦資訊預計出發前至少2天提供。','at-least 7 working days'),insurance=vf('校內可處理輕症／急救，重大醫療費須學生保險或自行負擔；FAQ未提供統一保險保額。','Medical expenses must be taken care')))
    han=source('158b1402f74820abd3e6da1c');hy='undated general hostel webpage; checked 2026-10-11; prices subject to change, exchange allocation unknown'
    add(48,dict(housing=fact(han,'兩個公寓Suasana Lumayan與Anggun Lumayan距校步行7／5分鐘；一般校方住宿介紹，未確認TKU交換是否可分配。','SUASANA LUMAYAN CONDOMINIUM',hy,role='host_general_housing'),housing_costs=fact(han,'每學期RM計價，不是每月。Suasana單人風扇1680／AC2000、雙人1520／1800、suite2200、quad1640；AnggunAC雙人2200、suite2800、四人2000；水電另付。頁面房人數敘述與quad列表不一致，待確認；價格會變動、沒有獨立年度。','RM 1,680',hy,role='host_general_housing'),transport=fact(han,'Suasana步行約7分钟、Anggun約5分鐘；此為住宿與校舍一般步行參考，不是交換校區配對確認。','within 7 minutes',hy,role='host_general_housing')))
    brandon=source('e825a19a51d231f33f0991a2');english=source('2d540f33ab11529f6f895bd2');by='undated host exchange/general admission policy; explicit TOEFL Jan2026 change kept separately; TKU cycle unverified'
    add(8,dict(host_eligibility=fact(brandon,'協議／認可交換計畫在籍、累積GPA至少2.00或同等、符合接待英語要求且母校推薦。Visiting Letter of Permission與正式exchange推薦信分開。','minimum cumulative GPA of 2.00',by),latest_forms=fact(brandon,'正式交換申請須母校recommendation and approval for exchange；一般訪問生Letter of Permission不能取代交換批准。未核實當期TKU專用表。','letter of recommendation and approval for exchange',by),host_language=fact(english,'接待校一般英語要求由exchange頁明示引用：IELTSAcademic6.5且各6.0，DET120各105；TOEFL至2026/1/20舊制86各20，1/21起新量尺4.5各4.0，成績送件時兩年內。豁免有12類須按原文核對；EAP官方明示不收2027秋／2028冬，不能用EAP當可申請備援。母校語言門檻另行核實。','tests taken until January 20, 2026:',by)))
    lmu=source('aafab80d1f7c870e127dd9a4');lh=source('2ce5a9733f65ff27a39ae896');lc=source('405a34c8fa4a042f97ba5638');ly='undated Erasmus/UK/SEMP/LMUexchange host rules checked 2026-10-11; 2026 courses only examples'
    def lf(value,needle,s=lmu):return fact(s,value,needle,ly)
    add(18,dict(host_eligibility=lf('須LMU協議母校正式提名後收申請資訊；不接受freemover。院系協議及TKU提名未核實。','your university must be an LMU partner'),host_deadline=lf('接待online冬學期5/15、夏學期11/15，網頁未列獨立年份；不能轉為淡江母校期限。','15 May'),latest_forms=lf('online申請、成績單、母校與學生簽署LA、語言證明、非EU護照個資頁、簽署同意表。Erasmus須OLA；LMUexchange可用母校或LMU紙式LA，上傳PDF後接待系所再簽。模板連結另查；未列入TKU母校申請catalog。','Completed online application form'),host_language=lf('一般申請B1、開始修課B2；英語only不須德語證明。北美研究／英語語文及政治碩士英語C1，醫／獸醫臨床德語C1與授課B2分開；證明兩年內。TOEFL頁列4(72+)/5(95+)但未載切換考日，不自行推定；IELTSB2為5.5、C1為7.0。','By the time you'),department_scope=lf('LMUexchange至少60%課在母校major/minor；其餘最多兩學科、合計最多3領域。未有先修只可入門課，大學部原則不可碩士課。','LMUexchange students',lc),course_restrictions=lf('30 ECTS為正常學生學期負擔，交換不強制；LA只是意向，課程待學期開始與系協調，不等於已註冊。','this is not compulsory for exchange'),course_schedule=lf('夏課約2月底／3初、冬課7月底／8初發布；交換確切課表申請截止時不可得，2026夏及2026/27冬英語課僅示例不保證下一期。','will not be available by the application deadline',lc),housing=lf('床位有限，正文約半數有房；須在交換online申請勾選住房，不能直接向Student Union申請，逾申請截止不受理。','approximately half of the students',lh),housing_costs=lf('平均每月€400–600依房型地點，通常最多一學期；冬租9月–2月底、夏3月–7月底，接受房需先付3月租及押金，精確金額依offer。網頁未載价格年度。','between 400 € and 600 €',lh)))
    mur=source('e35a25e9994bee0361e469ab')
    add(187,dict(housing=fact(mur,'官方SIU Bolsa de Alojamiento提供经审阅的租屋广告与公告栏；屬一般私人租屋資訊服務，沒有核實交換宿舍保證、租金或TKU分配。','se incorporan a la bolsa de alojamiento','undated general SIU accommodation service checked 2026-10-11',role='host_general_housing')))
    # Campus identities come from retained official geography HTML, not map viewport coordinates.
    geo=json.loads((BUNDLE/'official_geography_checks.json').read_text())
    hz=[g for g in geo if g['institution_id']=='tku-sister-322' and g.get('http_status')==200 and any(k in g['source_url'] for k in ['edisonweg','het-groene-woud'])]
    if hz:
        evidence=[]
        for g in hz:
            raw=json.loads(gzip.decompress(read_bytes(BUNDLE/g['capture_file'])));soup=BeautifulSoup(raw['response_text'],'html.parser');text=(soup.find('main') or soup).get_text(' ',strip=True)
            needle='A 10-minute walk' if 'edisonweg' in g['source_url'] else 'Within walking distance';assert needle in text;start=text.index(needle)
            evidence.append(dict(source_url=g['source_url'],capture_file=g['capture_file'],checked_at=g['checked_at'],content_sha256=g['sha256'],locator='Official named campus main body, exact location/department paragraph',quote=text[start:start+1200],applicable_year='undated general campus identity checked 2026-10-11',role='host_campus_identity'))
        fields={k:dict(value=v,status='reference_only',source_period_verified=False,reason='實讀官方分校頁；教學配置是一般參考，未核實淡江當期提名課系或校區。',evidence=evidence) for k,v in [('campus','HZ有Vlissingen Edisonweg及Middelburg Het Groene Woud兩校區；不能以任一市中心或網頁map viewport取代校區。'),('department_scope','Edisonweg官方分校頁明示經濟學科、Logistics Engineering及Maritime Officer；Middelburg為部分技術學科，該頁未完整逐列所有課系，不能補猜。須與TKU協議及修課確認。'),('transport','Edisonweg距NS鐵路站步行10分鐘；Het Groene Woud與NS站及市中心可步行到達，正文未給分鐘數，保留缺值。')]}
        add(322,fields)
    bel=source('6df503c703770318b30f7d1c');bely='undated incoming PEAL/PALAS semester programme; TKU track and current year unverified'
    def bf(value,needle):return fact(bel,value,needle,bely)
    add(313,dict(study_period=bf('PEAL與PALAS均15週，春約3月初–6月中、秋約7月底–11月初；網頁未載具體年度，不能套入2027確切日期。','15-week upper division program'),host_language=bf('PEAL全西班牙語，PALAS除語言課外英語；頁面沒有統一語言考試門檻，不补猜IELTS／DELE。','are conducted in English'),course_restrictions=bf('全時至少4課，每課60小時；每課至少6學生才開課，6是開課門檻不是TKU交換名額。','A minimum of six students'),department_scope=bf('Latin American Studies證書另須5課300小時及10–15頁研究報告；證書、一般PEAL/PALAS、Immersion與短期add-on為不同方案，不把選修證書當所有交換義務。','five courses (300 academic hours)')))
    ku=source('38ee6b5fdbf490279be523fa');ky='undated fee-paying Visiting Student KUSEP track; TKU bilateral fee waiver and programme mapping unverified'
    def kf(value,needle):return fact(ku,value,needle,ky,note='KUSEP為付費Visiting Student track，未核實TKU雙邊是否適用。')
    add(239,dict(host_eligibility=kf('KUSEP要求母校全時在籍，錄取後為Visiting Student；不能把此付費方案當淡江雙邊免學費交換。','enrolled as full-time students'),host_language=kf('KUSEP須大學程度英語，可以IELTS或同等測驗、或協議母校提名信中的評估證明；正文未載統一IELTS分數。','partner institution’s nomination letter'),costs=kf('KUSEP學費／校費THB60,000每學期，不含住宿、生活、制服、visa、保險。這是接待付費訪問方案，TKU雙邊是否免學費與當期價格未核實；不得套用此數值到所有TKU交換。','60,000 THB / semester'),course_restrictions=kf('KUSEP大學部3–7課、9–21 KU credits且Thai Conversation in Everyday Life I必修；非所有KU交換計畫共通規則。','9 KU credits'),department_scope=kf('正文先稱5個international programs，後稱6 faculties且列6，來源數量矛盾保留；須選1接待院與主修，未核實TKU可選學科。','five identified international programs')))
    tur=source('bb574a69fa578ee4155449f2');th=source('8c924385e55503733f008b80');ty='undated incoming exchange FAQ/health rules checked 2026-10-11; precise academic year and TKU nomination unverified'
    def tf(value,needle,s=tur):return fact(s,value,needle,ty)
    add(201,dict(host_eligibility=tf('須母校是partner／同網絡並完成母校內選後SoleMove提名；到UTU交換開始應已修滿2年、升大三，申請時大二尚未完成可。不是淡江本期校內资格。','When starting your exchange'),host_language=tf('語言證明送件時不超過2年；可由母校出具至少B2英語的蓋章簽名評估，C1但逾2年仍不可。頁面未列統一IELTS分數。','English level as at least B2'),latest_forms=tf('非EU Erasmus+ ICM須LA；非EU雙邊協議LA自願、依母校要求；EU/EEA OLA在UTU審完申請後，不能一律套用。語言Assessment Sheet模板的當期內容仍待核實。','For non-EU students coming through bilateral agreements'),department_scope=tf('醫學與Turku School of Economics須相關主修且協議涵蓋该院；法律／教育跨院要餘額與先修，大多數課應本主修，Any Field表選項不代表院系無限制。','can only accept exchange students, who are majoring'),course_restrictions=tf('UTU沒有交換最低ECTS，建議每學期30／全年60；母校／獎學金可另定最低。修滿2年的大學部可選部分碩士課，仍有先修；當期課表約5／6月更新。','we do not have a minimum ECTS'),insurance=tf('非EU居留申請須保險，UTU本身不替交換生投保；交換生不可用Finnish Student Health Services，可按住址使用Turku／Pori health stations。未自行擴充官方保額或醫療法律規範。','Insurance is obligatory for any non-EU citizen',th),housing=tf('TYS住房申請已開但錄取信未到可先申請、之後補信；FAQ沒有床位保證、租金或確切住房截止。','You may enclose the Letter of Admission later'),study_period=tf('FAQ一般秋迎新8月底、春1月初，上課隔週；秋至聖誕前、春5月中／底依課程。正文無精確年度，不能当2027確切日期。','usually organised at the end of August')))
    apply=source('4929af9e27decc32f8238f4d');turfields=rows[-1]['fields']
    def taf(value,needle):return fact(apply,value,needle,ty)
    turfields['host_deadline']=taf('接待一般秋／全年非EU/EEA為3/15–4/15、EU/EEA至4/30；春所有申請者9/1–10/15，皆Finnish time23:59。頁面沒有独立學年度，須先母校提名取得SoleMove指示；不能當作2026/10/15仍可新申請淡江母校。','15 March - 15 April')
    turfields['host_language']=taf('B2英語、證明兩年內；可母校評估並師生簽名及校章。IELTS6.0、PTE Academic62，IELTS one-skill retake限原測60日內；不收OLS／TOEIC／Duolingo。TOEFL標題寫ITP而內容寫iBT，另載Jan26,2026前72及各項分數、之後4及各項4，型別與切換日表述待接待校確認，不自行改成別校Jan21。','Language Certificate')
    turfields['host_language']['evidence']+=taf('','ITP taken before Jan 26 2026:')['evidence']
    turfields['latest_forms']=taf('須英文正式成績單、語言證明、護照／official ID，依母校及track另附LA。公開Language Assessment DOC及非Erasmus、ICM兩種DOCX已下載實讀；DOC以停用巨集與外連更新離線轉文字／2頁PDF並檢視評估表，正文無年度。雙邊LA模板Academic year空白、ICM正文KA171，不能由2025檔名推定交換年度。原始未解析DOC保留。這些是接待模板，不加入淡江母校申請文件catalog。','Application enclosures')
    templates=[('b0e98d5a81aafaaea61b56c0','Language Assessment Sheet','undated exchange Language Assessment Sheet; actual two-page offline rendering',1),('ee6ffc54d2e87404a8488adf','Academic year 20___','undated non-Erasmus Learning Agreement; academic year blank in body',None),('8d37c3475103b15048cffb35','International Mobility (KA171)','undated Erasmus+ KA171 Learning Agreement; 2025 filename not body academic year',None)]
    turfields['latest_forms']['attachment_checks']=[]
    for sid,needle,year,page in templates:
        a=source(sid);turfields['latest_forms']['evidence']+=fact(a,'',needle,year,page)['evidence']
        turfields['latest_forms']['attachment_checks'].append(dict(source_id=sid,source_url=a['source_url'],http_status=a['http_status'],local_file=a['local_file'],sha256=a['sha256'],checked_at=a['checked_at'],applicable_year=year,content_reviewed=True,original_capture_id=a.get('original_capture_id'),parser=a.get('parser'),rendered_file=a.get('rendered_file'),rendered_sha256=a.get('rendered_sha256'),rendered_pages=len(a.get('pages',[])),visual_review='Both rendered pages and A1–C2 assessment matrix inspected' if a.get('rendered_file') else None))
    turfields['course_restrictions']=taf('UTU無交換最低ECTS，建議30／60；最多半數語言中心課、至少半數課在UTU，Åbo Akademi課可部分選。碩士課申請頁要求母校碩士或學士最後一年，而FAQ寫修滿兩年可，文字差異待接待校確認，不擴大學士修課資格。','The recommended work')
    turfields['course_restrictions']['evidence']+=taf('','If you wish to complete Master')['evidence']+tf('','If you are a Bachelor-level student and you have studied 2 years')['evidence']
    turfields['course_schedule']=taf('一般秋課5/15、春課11/15才確認，可能晚於接待申請期；舊年度課供規劃參考，非保證同課重開。LA需course code且仍須正式選課。','teaching is generally confirmed by')
    hac=source('c2be64fd8b2142ae12755c9c');hy='undated Hacettepe bilateral visiting semester exchange rules checked 2026-10-11; TKU cycle unverified'
    def hf(value,needle):return fact(hac,value,needle,hy)
    add(219,dict(host_eligibility=hf('正式雙邊學期visiting international students須由母校國際處代申請，經接待相關學術單位審議批准後由外部關係處發錄取信。官方未給統一GPA或語言分數，不補猜。','Prospective visiting international'),latest_forms=hf('母校將申請交接待Office of External Relations；每學期申請期間由該處訂定公布，但此頁沒有實際日期、當期表格清單或明示尚未公告。新版期限／表格仍未核實。','application periods'),housing=hf('接待外部關係處可以預訂學生宿舍／residence halls；can be reserved不等於每位保證床位。沒有當期租金、住房期限或TKU校區分配。','Accommodation for visiting students')))
    skp=source('806dd7e12db3b3a2f79c2cf7');sp=source('f494e276173b3e9d3266502a');sl=source('bc23bb0562f3951e6c51c6bf')
    assert len(skp['pages'])==22 and '2027 Spring Semester Application Guidelines' in skp['pages'][0]['text']
    sky='2027 Spring SKP official semester application guidelines; TKU nomination/track/quota unverified'
    def rf(value,needle,page):return fact(skp,value,needle,sky,page,True)
    skpf=dict(
        host_eligibility=rf('母校須有有效交換協議並正式提名；在籍大學部／研究所，開始交換前須修滿至少一完整大學部學年。一般GPA3.0/4.0或B平均，協議另定者須符合協議。接待校標準不能取代淡江本期母校資格。','The standard required GPA is 3.0',8),
        host_language=rf('RCJ須JLPTN1或EJU日語讀聽合計280且寫作35；IJL不要求先有日語，零基礎須基本英語，選英語課另須RCE門檻。RCE為TOEFLiBT76／新制4.0、IELTSAcademic6.0、CambridgeB2/C1170、DET100或明示豁免。拒收HomeEdition、Essentials、MyBest、IELTSOnline及OneSkillRetake、TOEICIP；新語言文件明載TOEFL新制2026/1/21生效，不能套用別校規則。','Language  \nof Instruction',8),
        host_deadline=rf('2027春接待申請2026/10/2 10:00開始、11/2 09:00截止，全部JST；先提名才收到帳號。不是淡江母校新申請期限。','Monday, November 2, 2026',2),
        host_nomination_deadline=fact(sp,'接待提名2026/9/28開始、10/22 09:00 JST截止；細節寄partner coordinator，TKU當期是否提名此校與track未核實。','Thursday, October 22, 2026',sky,verified=True),
        campus=rf('IJL在京都衣笠；RCJ／RCE依學科可在衣笠、大阪茨木OIC或滋賀BKC。圖列校區不可任選互換，TKU提名實際校區仍未知。','In SKP Program, applicants must select a study track and campus',5),
        department_scope=rf('只能選指定track／校區的SKP課表，非一般學生全部課；不提供研究指導。大學部不可選研究所SKP課，研究生可兩層級；Design and Art暫未對SKP開放。OIC行政登錄Business Administration不等於僅可修該院課。','SKP students can select courses only',7),
        course_restrictions=rf('每週至少7節95分鐘課、每學期最多20學分含日語；限額課抽籤不保證。跨校區須餘額且預留約1.5小時交通，母校區優先；IJL最多再選2門英語課且須申請時語言證明。','at least 7 class sessions per week',7),
        course_schedule=rf('春課表3月、秋9月定案；過去課表僅參考，課程與餘額會變動，不保证同課重開。','course lists for the Spring Semester will be finalized in March',8),
        study_period=rf('2027春預計3月初／中抵達迎新，4/1學期開始、4/7上課、7/31program ends、9/25學期結束。全年次學期9/26開始、2028/1/31program ends；申請後不可半年延全年或連續另申下一學期。','Program Ends July 31',2),
        costs=rf('所有SKP學生須一次付JPY50,000 Student Support Fee，包含指定學研災／責任險、COE行政與活動；一般國民健康險／自行加購不含。自費partner學生另付學費，不能未查協議就給所有TKU交換同一學費。RUSSES自2027春停止，JASSO可能無補助，不能把JPY80,000/月當保證收入。','SKP Student Support Fee',4),
        latest_forms=rf('接待申請全線上，日／英文件PDF或JPG；所需在籍／適用畢業證、最新含評分尺度成績單、依track語言證、日文500–700字或英文500–700words動機、護照、適用居留卡。COE另由指定行政書士通知web form；健康表錄取後另通知，暫定1月中。沒有以舊COE表取代新版程序，未加入淡江文件catalog。','Required Application Documents',19),
        housing=rf('先填I-House偏好，錄取後才送正式住宿申請，依衣笠／OIC／BKC分開，未核實保證床位、當期租金或TKU分配。','official housing application must be submitted after',18),
        insurance=rf('JPY50,000 Support Fee含指定Gakkensai與Gakkenbai及醫療支援；國民健康險及自行選購保險需另繳，不把support fee当完整保費。','Gakkensai',4))
    skpf['host_language']['evidence']+=fact(sl,'','effective January 21, 2026',sky,1,True)['evidence']
    skpf['department_scope']['evidence']+=rf('','On OIC campus, applicants may only select',15)['evidence']
    skpf['study_period']['evidence']+=rf('','Extension of the study period after application',3)['evidence']
    skpf['latest_forms']['evidence']+=rf('','statement of purpose in Japanese is between 500 and 700',16)['evidence']+rf('','Starting from Spring 2027',4)['evidence']+rf('','Submission deadline: Mid-January',21)['evidence']
    skpf['costs']['evidence']+=rf('','will not be offered from the Spring 2027',4)['evidence']
    add(111,skpf)
    vub=source('a2292ebfc5e9736ff72395ce');vp=source('8420fd719590b4cd5f6a35ad');vy='undated VUB incoming exchange website; TKU nomination and specific academic year unverified';vpy='2026/27 autumn incoming exchange orientation; actual PDF p50 year/calendar, not2027/28'
    def vf(value,needle):return fact(vub,value,needle,vy)
    add(7,dict(host_eligibility=vf('學期study exchange須雙邊協議並母校內選批准，接待仍會審查不保證錄取；traineeship無協議亦可洽，但不是同一交換方案。','You need an agreement'),host_deadline=vf('一般接待秋6/1、春11/1截止，EU及非EU皆同、逾期不完整不受理；網頁未載独立年度，不作TKU母校期限。','Application to VUB before 1 June'),host_nomination_deadline=vf('一般母校提名秋5/1前、春10/1前；非EU同期限，無獨立年份，TKU提名狀態未知。','Nomination to VUB by your home university before'),department_scope=vf('一般只能本學科課，由院系exchange coordinator核對；課表逐院含Bachelor／Master／ad hoc不同，不等於全部接待科系可供TKU交換。','you can only pick courses from your study field'),campus=vf('法律等課在Main Campus，Medicine and Pharmacy在Jette Health Campus；實際TKU科系、校區與協議範圍仍待確認。','VUB Health Campus in Jette'),study_period=fact(vp,'2026/27秋簡報實載2026/9/21開課（Bruface例外），2027/1/4–31考試，交換結束為個人最後考試日；不是2027/28行事曆。','Start of classes: 21/09/2026',vpy,50,True),course_restrictions=fact(vp,'2026秋LA修改截止2026/10/8、需雙方coordinator審查；院系依LA代登課，不需學生自行註冊，非LA草稿自动確定學分。這是已錄取在校選課期限，不是接待申請期限。','Deadline: 8 October 2026',vpy,16,True),latest_forms=fact(vp,'抵離校證明須以Mobility Online證據處理，簡報明示不簽母校證明模板；此為2026秋抵離手續，不是TKU當期校內申請表。','HOME',vpy,15,True)))
    tsuda=source('ffd732abc29a88e27e8f8b8f');ts=source('66f499849563194c80dbabf0');tsy='undated Tsuda incoming exchange/general support webpages checked2026-10-11; TKU nomination and semester year unverified'
    def tdf(value,needle,s=tsuda):return fact(s,value,needle,tsy)
    add(28,dict(study_period=tdf('交換可一年4月–1月或9月–7月，或春／秋一學期；頁面無独立年份或精確日期，不套用2027，亦不改寫TKU名額。','We accept international exchange students'),housing=tdf('CIE協助安排campus accommodation；沒有在此頁核實床位保證、當期價格或房型，不能以helps assign推定住宿保證。','helps assign campus accommodations'),insurance=tdf('入學時校方說明日本國民健康險登錄及繳費程序；此一般支援頁沒有提供交換當期保費金額。','procedures for enrolling in National Health Insurance',ts),transport=tdf('交換生各有兩位Big Sisters協助抵達後認識校園、生活與住宿規則；不是保證機場接送或交通費用，宿舍迎接協助只限同住Big Sisters。','Each international exchange student has two',ts)))
    ta=source('40d4a6ea64a9917872aab3d6');tl=source('13f48e9e5ca29c85ba64ee5f');tb=source('21d1aedbbf5ab7be6989bc96');tsh=source('bef9eab6b6f56af563b8f4de');tsp=source('7dbedf532b3b5cfd7f00151f');tsfields=rows[-1]['fields']
    assert len(tl['pages'])==1 and len(tb['pages'])==5
    tsfields['host_eligibility']=fact(ta,'須為協議母校學生並由母校提名，CIE partner頁確列Tamkang University；協議存在不能作當期TKU開放名額或性別／學制資格核實。','students must be nominated by a home university',tsy)
    tsfields['host_eligibility']['evidence']+=fact(tsp,'','Tamkang University',tsy)['evidence']
    tsfields['host_deadline']=fact(ta,'接待頁要求向母校國際處確認流程、指定表與截止，沒有在正文給當期日期或明示尚未公告；TKU當期及接待精確截止皆未核實。','Please ask them for the application procedure',tsy)
    tsfields['latest_forms']=fact(tl,'已讀1頁交換文件清單：online登録、指定Excel交換／COE表、JPEG證件照、財力及佐證、成績單、1封教師推薦、適用日語證明與護照。Excel原格式提交，不收手寫、PDF或Numbers轉格式。清單與5頁brochure可開啟，PDF無模板超連結，指定模板／online form須由母校取得；不宣稱已讀未提供的表。正文無年度，brochure2023課表只供歷史參考，不混入當期母校文件。','Exchange Application Form',tsy,1)
    tsfields['latest_forms']['evidence']+=fact(tl,'','Please fill in the Excel form and submit it as it is',tsy,1)['evidence']
    tsfields['latest_forms']['attachment_checks']=[dict(source_id=s['id'],source_url=s['source_url'],http_status=s['http_status'],local_file=s['local_file'],sha256=s['sha256'],checked_at=s['checked_at'],applicable_year=y,content_reviewed=True,pages=len(s['pages'])) for s,y in [(tl,'undated1-page exchange document checklist; no embedded public template links'),(tb,'undated5-page brochure; p3 explicit2023 course examples historical only')]]
    tsfields['host_language']=fact(tl,'不接受零日語；一般須出願前報名TUFS on-demand日語課、附報名證明、費JPY18,000自付且先會讀平／片假名。已有大學等日語學習史或達JLPTN5可豁免課程；JLPT成績或校方指定教師獨立評估為替代證據，不把N5誤設成全員統一入學門檻。無法報名或取得證據須截止前洽校，年份仍未核實。','Note that Tsuda does not accept zero-level Japanese learners',tsy,1)
    tsfields['host_language']['evidence']+=fact(tl,'','those who have Japanese language learning',tsy,1)['evidence']
    tsfields['housing']=fact(tsh,'小平Shiraumeryo59間雙人、118全寮容量不是TKU名額；有家具共廚、不附餐、假期部分閉寮。此未載年度頁沒有每位床位保證、租金或TKU分配。','capacity for 118 residents',tsy)
    tsfields['course_restrictions']=fact(tb,'歷史brochure列交換日語4門加Japanese Studies1門、依能力；同頁明載2023課程示例，不能推為2027開課或當期強制負擔。英文課與一般院系課另列，需用當期syllabus及接待指示核實。','Here is a list of some of the courses offered in 2023','2023 historical course examples explicitly printed in undated brochure p3',3)
    knu=source('b223e72ecbc57fded7d40718');kny='undated general international-student housing page checked2026-10-11; current price year and TKU exchange allocation unverified'
    add(70,dict(housing=fact(knu,'一般國際生向36Vasylkivska辦公室房委會申請，核准後至25Litnya第22宿舍簽住宿契約。依空床分配、無位須waitlist，不保證TKU交換床位；沒有當期年份或住房截止。','Accommodation is subject to availability',kny,role='host_general_housing'),housing_costs=fact(knu,'官方未載年度的一般宿舍參考：prospective student UAH1,438/月、student UAH1,296/月，類別不同；不轉匯率、不宣稱2027交換價格。','Monthly dormitory fee:',kny,role='host_general_housing')))
    bh=source('a10e4e5c4919f44d4d66e4b5');bhy='2026 Spring/Fall historical international General Scholar/Exchange page; TKU mainland programme route and2027 mapping unverified'
    def bhf(value,needle):return fact(bh,value,needle,bhy,verified=True,note='來源為普通進修／交換General Scholar國際學生方案，TKU陸港澳金門是否走同一route未核實；明載2026期限僅歷史參考。')
    add(134,dict(
        host_eligibility=bhf('國際学院General Scholar／Exchange頁要求已修滿2年大學部、相關領域、一般35歲以下及足夠英語或中文；對TKU台灣學生是否適用此外国學生route未核實，不能當母校資格。','complete at least two years undergraduate study'),
        host_language=bhf('依授課須能英語或中文聽課；教育語言不是英／中者交TOEFL、IELTS、HSK或英／中能力證明，但該頁沒有統一分數，不能補猜IELTS／HSK門檻。','The results of TOEFL, IELTS or HSK'),
        department_scope=bhf('頁面逐學科以符號區分中文●、英文▲、法文◆、德文☐、俄文△；院系與語言不可當全校統一，TKU陸港澳金門的學制、院系及track對應未知。','Note: ● 中文授课'),
        host_deadline=bhf('歷史2026春接待申請2025/12/30、2026秋2026/6/30；現在均已截止。2027新期限未核實，不稱官方尚未公告，也不是TKU母校期限。','December 30, 2025'),
        study_period=bhf('頁面歷史2026春3月／秋9月入學，General Scholar可半年／一年，沒有核實2027時程或TKU交換期。','March, 2026'),
        latest_forms=bhf('General Scholar申請書、護照、最高學歷或預期畢業證、公證成績單、至少500words研修計畫、2封教授／學術專家推薦、体檢表與驗血報告、適用語言證明。文件須英／中或譯文；公開常用下載另查，沒有將此國際進修清單加入TKU母校catalog。','Application Form for General Scholar Program'),
        costs=bhf('國際普通進修頁列申請費RMB400、學費RMB13,000／半年；此2026歷史方案收費，TKU雙邊免學費／適用track未核實，不把13,000套給全部淡江交換。','13,000 Yuan/Half a year'),
        insurance=bhf('General Scholar表列保險RMB400／半年，與首頁政府獎學金生每年800及返還是不同對象；未核實2027價格或TKU適用。','400 Yuan/Half a year'),
        housing=bhf('表列Student Dormitory雙人房、按床按日，不等於保證床位或TKU實際分配校區；一般公寓頁另有沙河及學院路，不自行對應任一校區。','Double Room'),
        housing_costs=bhf('頁面歷史方案雙人RMB30／日／床，水電不含且費用可能調整；未核實當期交換價格，不算固定全年房租。','30 Yuan/Day, per bed')))
    bhforms=rows[-1]['fields']['latest_forms']
    bhforms['value']='General Scholar文件清單的申請書與外国人体檢表已可開啟並實讀：普通進修Form004為2頁、含Agreement Institution及研修／財力欄，原始DOC以停用巨集及外連更新離線轉2頁PDF；體檢PDF2頁含醫師簽名章與附件報告。模板正文學年空白，僅2026歷史portal上下文，不當2027新版。實讀並排除Senior Scholar Form005、Chinese Language Form006及四年本科財力表（10萬／12萬RMB），不能混進TKU學期交換。2推薦、500words研修計畫等清單仍只屬此國際進修route，未加入TKU母校catalog。'
    bhforms['attachment_checks']=[]
    for sid,needle,page in [('9d90ee5fd05be71cd0090e91','General Scholar',1),('1c166f394bc38069c5b3adeb','FOREIGNER PHYSICAL EXAMINATION FORM',1)]:
        a=source(sid);year='Undated body; year/enrolment blanks; linked from generic downloads and2026 General Scholar portal context only'
        bhforms['evidence']+=fact(a,'',needle,year,page)['evidence']
        bhforms['attachment_checks'].append(dict(source_id=sid,source_url=a['source_url'],http_status=a['http_status'],local_file=a['local_file'],sha256=a['sha256'],checked_at=a['checked_at'],applicable_year=year,content_reviewed=True,pages=len(a['pages']),original_capture_id=a.get('original_capture_id'),parser=a.get('parser'),rendered_file=a.get('rendered_file'),rendered_sha256=a.get('rendered_sha256')))
    (BUNDLE/'milestone3_reviewed_host_facts.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(additional_reviewed_institutions=len(rows),additional_fields=sum(len(r['fields']) for r in rows))))


if __name__=='__main__':main()
