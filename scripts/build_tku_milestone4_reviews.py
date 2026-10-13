"""Record all 69 fixed candidates and carefully scoped host references.

The human assessments below follow full available-body review, not keyword/year
inference. Four HTTP200 bodies are partial shells; one candidate is HTTP404.
No home eligibility, quota, document catalog or current-school list is changed.
"""
import json
from collections import Counter
from build_tku_milestone3_host_reviews import source, fact
from tku_capture_io import BUNDLE


# Ordinals are the frozen M3 remaining-candidate list, including URL variants.
ASSESSMENTS = [
('unrelated_training','2019/20 historical; finalized','World Bank officials/data training, finalized100%; not semester exchange'),
('institution_activity','2025 activities and2022 testimonial','UADE COIL/seminars/summer activities; no semester application rules'),
('partial_body_unavailable','not established','Suda summer-school page retains only title/navigation; no substantive programme body'),
('different_programme','2026 title; old listing dates','Chinese Teacher Scholarship, not semester exchange; followed actual2026 rules'),
('institution_project','2018–2022 historical','PSU FRIENDS capacity/virtual-mobility project'),
('institution_project','2016 historical','PSU SIMPLE labour/curriculum project'),
('different_programme','2016 historical; actual announcement21July2016','EU-only credit conversion×1.67; PSU outbound Erasmus funding separate from TKU incoming'),
('manual_reference_only','undated; historical2016 event also on page','Exchange-student Poitiers station welcome; no2027 guarantee'),
('institution_project','2021–2027 charter, not application cycle','Poitiers Erasmus institutional charter'),
('institution_project','2015–2028 mixed project periods','KA131/KA171 institutional/outbound project countries; not TKU application'),
('manual_reference_only','undated office directory','SURIEE incoming support contact; office address not allocated campus'),
('different_programme','2026–27 ambassador call','EC2U ambassador recruitment, not semester admission'),
('event','October2026','Paris Cité CircleU event'),
('event','October2026','Paris Cité escape game/food event'),
('event','October2026','Paris Cité theatre event'),
('host_outbound_event','October2026','Paris Cité outgoing internship webinar'),
('host_outbound_event','October2026;13vs15 event-date inconsistency','Paris Cité outgoing mobility stand; event dates not admission deadline'),
('manual_reference_only','undated brochure;2018 statistics; historical general reference','GZU mixed degree/nondegree brochure: general housing/costs only; degree HSK not exchange threshold'),
('partial_body_unavailable','2025 Spring title; published2024-10-23','GZU title-only language-programme page; empty image src, no actual brochure body'),
('different_programme','published2019-04-04; brochure intrinsically undated','GZU8day/2week/3week cultural group programme; not semester exchange'),
('manual_reference_only','published2019-03-01; brochure intrinsically undated with2018 statistics','GZU English mixed brochure: historical general housing/costs only'),
('partial_body_unavailable','2025 cultural-festival title; published2025-10-10','Festival title/navigation only; not semester application'),
('event','September2026','UNA Abriendo fronteras student-experience event'),
('partial_js_shell_certificate_error','not established','UNA public agreements table absent from HTTP200 shell; Chromium certificate validation failed, no bypass'),
('institution_project','2026/27 Erasmus and2023–28 research projects','UNA EU programmes/research, not TKU semester route'),
('research_event','October2026','UNA food-research conference'),
('institution_news','mixed2026 news','UNA research/event news, Taiwan studies not incoming admission'),
('full_degree','curriculum, not academic application period','JNU International Studies MA/PhD course/faculty catalogue'),
('http404_unavailable','not established; filename not evidence','JNU PDF returned404; original body/year not reviewed'),
('full_degree','mixed curriculum/history/news; period not established','NUM International Relations department BA/MA/PhD site, not incoming mobility'),
('institution_directory','undated; modified2025 not academic year','UTP DRI intro/menu'),
('institution_directory','undated','UTP director greetings/link directory'),
('institution_directory','undated; modified2026 not academic year','UTP DRI mission/staff'),
('restricted_republication_directory','undated; updated2026-10-07 not document year','UTP manuals expressly prohibit reproducing/sharing without written permission; HTML consulted, manual PDFs not downloaded/reposted'),
('programme_directory','undated directory; followed2027 actual incoming page','UTP incoming/outgoing routes kept separate; actual incoming programme followed'),
('full_degree','2027 actual degree-admission form','HIU handwritten400Japanese-character degree-admission motivation; not exchange form'),
('alumni','undated','HIU alumni homepage'),
('alumni_duplicate','undated','HIU same alumni body URL variant; no duplicate facts'),
('research_institute','published2023-11-07','Wuhan maritime research centre, not incoming application'),
('research_institute','published2023-11-07','Wuhan materials lab'),
('research_institute','2017 approval;2023 page','Wuhan materials lab, research agreement not semester opening'),
('research_institute','published2023-11-07','Wuhan ecological-building lab'),
('teaching_book','2007 actual copyright','Aoyama SEEDBOOK1 textbook, not language certificate/form'),
('teaching_book','2008 actual copyright','Aoyama SEEDBOOK2 textbook'),
('teaching_book','2009 actual copyright','Aoyama SEEDBOOK3 textbook'),
('teaching_book','2010 actual copyright','Aoyama SEEDBOOK4 textbook'),
('teaching_book','2007 actual copyright','Aoyama SEEDBOOK5 textbook'),
('full_degree','not established in body; URL year not sufficient','PKU Chinese full-time foreign-languages degree majors'),
('full_degree','not established in body','PKU Chinese full-time International Relations degree majors'),
('full_degree','not established in body','PKU doctoral degree majors'),
('full_degree','not established in body','PKU master degree majors'),
('full_degree','not established in body','PKU English full-time International Relations degree majors'),
('research_institute','mixed research periods','Lyon EDIEC research/conferences'),
('full_degree_catalogue','updated2018; not current exchange catalogue','Lyon International Intercultural degree/course catalogue'),
('research_staff_mobility','updated2024-07-16; not application year','Lyon research/staff/doctoral internships, not incoming semester scheme'),
('programme_directory','undated; updated2026-05-12','Lyon DEUF/SELF distinguished from full master/double degrees; actual programmes followed'),
('institution_project','updated2025-10-24; not application year','Lyon partnerships/double-degree networks'),
('institution_strategy','2030 strategy; not application period','Bonn German institutional international profile'),
('programme_directory','mixed2026 news; actual programme followed','Bonn international directory → International Students → Global Exchange'),
('office_directory','undated office hours;2025–26 closure historical','Bonn International Office contact; historical closure not current closure'),
('institution_strategy','undated statistics','Bonn English international profile; student counts not exchange quotas'),
('manual_reference_only','undated; modified2026-07-06 not academic cycle','Stockholm says most exchanges conducted by departments; not TKU agreement allocation'),
('manual_reference_only','undated','UMLP DREIF incoming support; former Franche-Comté agreement/scope mapping unverified'),
('full_degree_catalogue','undated','UMLP full-degree/short-course catalogue; not approved TKU exchange courses'),
('event','September2026','Reitaku RIFA first meeting; followed general RIFA support page'),
('event','September2026','Reitaku21 visitors/9partners are current visitors, not TKU quota'),
('full_degree_testimonial','four-year degree examples, not exchange period','Reitaku JIC degree testimonials; weekly classes not exchange requirement'),
('manual_reference_only','undated','Reitaku general Japanese-language support, not admission test threshold or guaranteed exchange access'),
('manual_reference_duplicate','undated','Same Reitaku Japanese centre body URL variant; facts deduplicated'),
]


def main():
    checks=json.loads((BUNDLE/'milestone4_candidate_capture_checks.json').read_text())
    assert len(checks)==len(ASSESSMENTS)==69
    reviews=[]
    for c,(status,year,assessment) in zip(checks,ASSESSMENTS,strict=True):
        s=source(c['source_id']); text=s.get('text') or ''
        failed=status=='http404_unavailable'; partial=status.startswith('partial_')
        reviews.append(dict(**{k:v for k,v in c.items() if k!="content_sha256"},status=status,assessment=assessment,applicable_year=year,
            body_review_status='not_obtained' if failed else 'all_available_shell_or_title_text_reviewed_substantive_content_missing' if partial else 'all_available_extracted_body_reviewed',
            complete_programme_content_reviewed=not(failed or partial),
            exclude_from_semester_reference_index=True,
            promotion='explicit_manual_reference_overlay_only' if status.startswith('manual_reference') else 'no_automatic_rule_promotion',
            locator=f"PDF physical pages1–{len(s['pages'])}; all extracted text" if s.get('pages') else 'All available HTML extracted body; substantive limitations retained',
            quote=text[:1200] if not failed else '',content_sha256=s['sha256']))
    (BUNDLE/'milestone4_candidate_content_reviews.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2)+'\n')
    followups=[]
    for filename in ['milestone4_followup_capture_checks.json','milestone4_document_capture_checks.json','milestone4_programme_capture_checks.json']:
        for c in json.loads((BUNDLE/filename).read_text()):
            s=source(c['source_id'])
            followups.append(dict(source_id=s['id'],source_url=s['source_url'],checked_at=s['checked_at'],
                content_sha256=s.get('sha256'),http_status=s.get('http_status'),error=s.get('error'),
                status='human_overlay_only_mixed_programme_or_directory',exclude_from_semester_reference_index=True,
                locator='Actual retained HTML/PDF/DOCX body; relevant rules individually quoted in reviewed facts',
                quote=(s.get('text') or '')[:1000],applicable_year='See individually reviewed field; URL, update and template filename never establish academic year',
                assessment='Non-exchange French full-degree language page excluded; scholarship, short culture programme and directories not promoted. Accepted programme rules are explicit curated fields only.'))
    (BUNDLE/'milestone4_followup_scope_reviews.json').write_text(json.dumps(followups,ensure_ascii=False,indent=2)+'\n')
    rows=[]
    def add(n,fields):rows.append(dict(id=f'tku-sister-{n}',fields=fields))
    u=source('2be33d4a336fb42979b89441');p=source('600dbb2503a9659985cd1675')
    uy='2027 incoming academic semester webpage; TKU nomination/track/quota unverified'
    py='2026–2027 actual host Fact Sheet; not TKU current application verification'
    def uf(value,needle):return fact(u,value,needle,uy,verified=True)
    def pf(value,needle,page):return fact(p,value,needle,py,page,True)
    ufields=dict(
        host_deadline=uf('接待校2027第一學期（3–7月）申請2026/9/1–2027/1/14；第二學期（8–12月）2027/4/1–2027/7/1。PDF2026–27列10–1月／4–6月概略窗口，與網頁不同；保留矛盾，以網頁精確日期向接待校核對。研究實習全年開放屬另一方案。不是淡江母校截止。','Periodos de aplicación 2027'),
        host_eligibility=uf('由母校國際處以每人一份PDF提名；UTP仍審查後才發接受函，尚未核實淡江本期協議track或提名資格。','La oficina de asuntos internacionales de la universidad origen'),
        host_language=uf('非西語母語者需中級B1–B2西語證明，母校如開西語課可出證；大多西語授課，僅regular plan內明示英文課例外。研究實習导师另定與一般學期交換分開。','El certificado de idioma español aplica'),
        study_period=uf('學期交換1或2學期：2027年3–7月／8–12月。研究及專業實習3–6月屬另外方案，不用同一交換期限。','Intercambio académico de 1 o 2 semestres.'),
        department_scope=uf('單一學院，最多三個學位計畫且限二年級以上課；母校提名的學院／VLS或七regional校區未核實，不能任選全部校區。','(3.) El estudiante puede seleccionar'),
        course_restrictions=uf('最多5門、單一學院、最多3個degree plans；不能選EE/OP選修，畢業專題須另審；課須對應第一／第二學期。時段由院系安排，可早、午、晚，課表不是選中即保證。','(1.) Las asignaturas deben ser'),
        course_schedule=uf('2027第一學期：二年級課查2025/2026版plan，三年級查2025，四／五年級查2024。官方明示舊plan版本與2027交換期分開，不能因plan年份判為舊申請。','Consideraciones Importantes sobre los Planes de Estudio 2027'),
        latest_forms=uf('母校以單一PDF提交內部交換表、提名信、成績單、西語CV、證件／護照、西語證明、西語至少1頁動機；SMILE/PAME表僅適用該track。錄取後需國際醫療險。23頁PDF與2份DOCX已開啟讀正文：PDF實載2026–2027；DOCX學年度留白、courselist有Ejemplo，並非當期保證課。這些接待表未加入淡江母校文件catalog。','Lista de documentos para semestre académico'),
        costs=uf('交換頁明示免matrícula；PDF航空programme另有費用，不將一般免註冊费套到全部航空課。當期淡江雙邊條件未核實。','Exoneración del costo de matrícula.'),
        housing=pf('由UTP community提供近主校區個人／共用房或公寓，聯繫國際處；沒有床位保證、價格或淡江校區分配。','ACCOMMODATION',23),
        living_costs=pf('2026–27接待校主校區餐廳參考：學生餐USD1，一般USD2–4。未核實2027全部生活費，不換匯或當固定全年預算。','Student menu at $1.00.',23),
        insurance=pf('incoming students須自行購買涵蓋期間的國際health insurance；未核實金額。','must purchase international health insurance',23),
        student_support=pf('有線上行前induction、第一上課週現場welcome及Panabuddy志工支援；不保證個人配對或接機。','PANABUDDY',22))
    ufields['host_deadline']['evidence']+=pf('','To apply for the first semester',17)['evidence']
    docs=[source('12661070e4502c2061531474'),source('77baebf42badca87b186a9b1')]
    for d in docs:
        ufields['latest_forms']['evidence']+=fact(d,'', 'Año' if 'Año' in d['text'] else 'Ejemplo', 'Intrinsically undated DOCX template linked from2027 incoming page; year blank, examples not guaranteed courses')['evidence']
    ufields['latest_forms']['attachment_checks']=[dict(source_id=d['id'],source_url=d['source_url'],http_status=d['http_status'],local_file=d['local_file'],sha256=d['sha256'],checked_at=d['checked_at'],content_reviewed=True,applicable_year=py if d==p else 'undated template linked from2027 page; not assumed2027 revised form',pages=len(d.get('pages',[]))) for d in [p,*docs]]
    ufields['latest_forms']['reason']+=' PDF主任Clemente與表／網頁Karla不同；表的西語Traducción oficial及英語Original transcript翻譯差異仍待確認，不猜接受語言。'
    add(54,ufields)
    b=source('cd85aa1bcfd490bc145242d6');bw=source('56bb8e68c0a8b83607b81647')
    by='2026/27 actual Global Exchange partner Fact Sheet; TKU absent from website partner list; applicability unverified'
    def bf(v,n,p):return fact(b,v,n,by,p,True,note='Global Exchange網頁臺灣partner只列臺大與政大、未列淡江；淡江名錄不證明同一接待計畫適用。')
    bfields=dict(host_eligibility=bf('GPA一般3.0/4.0，母校coordinator可依潛力彈性；網頁Bachelor須完成一年。Global Exchange公開臺灣名單只有臺大、政大，未列淡江；不能據此判TKU適用或全校無協議。','At least 3.0 out of 4.0',4),host_language=bf('2026/27英語B2（偏好C1，無正式證書要求）或德語課B2；本科英文課有限。只屬Global Exchange，淡江route未核實。','English B2/C1:',4),host_nomination_deadline=bf('2026/27接待表：冬3/1–4/14、夏9/1–10/14提名；沒有核實淡江有此programme提名權或2027/28新規。','Nomination Winter semester:',4),host_deadline=bf('2026/27接待申請冬4/1–5/31、夏10/1–11/30；2027/28新版未核實，不稱官方尚未公告。','Application Winter semester:',4),study_period=bf('2026/27上課冬2026/10/12–2027/2/5、夏2027/4/5–7/16，考試可能在課後數週。不是2027秋行事曆。','Winter semester 2026/27:',3),department_scope=bf('醫學院不開放；網頁另明示medicine及dentistry不收，不能當全部科系開放。TKU院系協議未知。','All fac u lties',5),housing=bf('可經Mobility-Online申請Studierendenwerk住房，約抵達6週前簽約；沒有床位保證，搬入／出只限週一至五。','Student dormitories',6),housing_costs=bf('2026/27住宿€300–560/月、可選starter kit€60；取消可能收最高三月租金。2027/28新價格未核實。','Monthly rent €300–€560',6),living_costs=bf('2026/27估月總約€1,000，私人房€300–650、餐€200、醫保€135–150；只是接待參考估算。','€1,000',8),insurance=bf('註冊须全期間足額醫保；私人保险需德國公保機構認可，不足可另購；30歲以上私人險。€135–150/月為2026/27參考。','Health insurance',7),latest_forms=bf('Mobility-Online需英語成績單、護照及動機；登入連結先發partner提名coord，未核實TKU取得此route權限。未加入母校文件catalog。','Admission documents',4),course_restrictions=bf('依語言／背景與課程個別條件選課；建議每週12–18contacthours、約30ECTS，非強制統一最低。','Standard full',5))
    bfields['host_eligibility']['evidence']+=fact(bw,'','Taiwan\nNational Chengchi University\nNational Taiwan University','Undated actual Global Exchange website partner list; absence is programme-list observation, not proof of no institutional agreement')['evidence']
    add(19,bfields)
    l=source('a7eb5c49635078d36d6e4617');ld=source('29798ec5051d4d30df947ddf');ll=source('b8831cd166411bcc4f5bc0c8');steps=source('352c64471597c13698483f0f')
    ly='2026/27 SELF host semester calendar; other general programme rules undated; TKU route unverified'
    def lf(v,n,known=False):return fact(l,v,n,ly,verified=known)
    lfields=dict(host_eligibility=lf('SELF本科高年級、至少完成兩年大學，非degree programme；DEUF另可本科／碩士。淡江本期採哪個track未知。','at least two years of university studies'),host_language=lf('SELF頁（2026/10/6更新）TOEFLiBT新制4.5/6且各4/6、ITP560各50；獨立交換語言頁（4/14）仍列iBT80各20、ITP87各25，來源矛盾未擅自換算。IELTS6.5各6、DET125；證明於提名提供且2年內。SELF法語≤A2（最多B1）；DEUF通常B1、法政哲B2、傳播C1。待接待校確認所用版本。','Level of English:'),study_period=lf('SELF2026/27秋抵達8/24–26、迎新8/27–9/4、12/18結束；春2027/1/4–6抵達、迎新1/7–15、4/30結束。DEUF2027春精確日期正文明示「à venir」，與SELF已列春日期分開。DEUF秋頁「Réouverture4janvier2026」年份矛盾不補猜。','Fall Semester 2026/2027:',True),course_restrictions=lf('SELF全時、不能併其他programme，FLE與法國文化必修+最多4門內容課，full-time31credits；各班35–45人、最少15人才開課，均非TKU名額。DEUF學期文憑26credits（8必修+18選修），LA經母校核准；課程不全校任選。','It is a full time program and cannot be combined'),campus=lf('SELF所有課在Manufacture Campus（6coursAlbertThomas）；DEUF只列Lyon，淡江實際track／校區仍未核實。','The SELF classes all take place'),costs=lf('exchange免enrolment fees；SELF自費€3,500/學期正文明載2025/26，DEUF自費€3,000/學期是另一對象。自費截止6/1、11/1不能當交換申請期限，亦不當2027價格。','Exchange students\nare exempted'),host_deadline=fact(steps,'交換先由母校選派；接受函一般秋5月／春10月底，註冊秋6月／春10月底，這是行政階段而非申請截止。SELF/DEUF自費截止不適用交換；本期交換截止尚未核實。','Étape 1 : Sélection','Undated exchange steps; linked2025/26 guide/calendar historical, not2027/28'),latest_forms=lf('交換生正文要求向母校確認程序；此頁公開application form專供non-exchange/fee-paying/free-movers，未作交換或淡江申請表。','Exchange students:\nplease revert to your home University'))
    lfields['host_language']['evidence']+=fact(ll,'','TOEFL IBT:','Undated exchange-language rules; page updated2026-04-14; contradictory SELF2026-10-06 version')['evidence']
    for key,needle in [('study_period','Dates semestre de printemps'),('course_restrictions','26 crédits par semestre'),('costs','3000 € par semestre')]:lfields[key]['evidence']+=fact(ld,'',needle,'2026 Fall DEUF calendar;2027Spring dates explicitly à venir; other programme rules undated')['evidence']
    add(16,lfields)
    g=source('af08924ac1aa8bf0bd7674ed');gy='Intrinsically undated GZU brochure;2018 statistics; official link published2019-03-01; historical general reference, not2027 prices'
    def gf(v,n,p):return fact(g,v,n,gy,p,False,role='host_general_historical',note='混合degree/nondegree舊brochure；未核實淡江route、2027費額／條件。')
    add(211,dict(housing=gf('舊一般國際生宿舍有浴室、冰箱、暖氣及公共洗衣；未核實交換床位保證或2027安排。','Accommodation',7),housing_costs=gf('歷史未載學年度：三人房共浴RMB350、雙人套房共浴500、單人獨浴800／人／月；官方連結頁2019、正文2018統計，不是2027報價。','RMB 350',7),costs=gf('舊General Visiting Student文14000／理15500RMB年；Advanced18000／20000。一般registration500；交換協議免除與TKU適用未核實，不能向TKU一律收此費。','General Visiting Student',4),insurance=gf('舊一般新生保險800RMB年／400學期；scholarship及self-sponsored不同，不是2027交換保費。','RMB800 per year',4),living_costs=gf('舊brochure校內餐約RMB10／餐；不当2027固定價格或完整預算。','about RMB10',7),department_scope=gf('舊Visiting Student可非degree修部分本科／碩／博課；degreeHSK4/5與degree／語言班6/30、11/30期限不混入TKU交換門檻或截止。','Visiting Student Program',3)))
    po=source('640d4fc27ebf84e6b704f5d5');pc=source('873dc037bfcda3f466d4cb57')
    add(215,dict(transport=fact(po,'一般交換學生可有Poitiers火車站welcome；未載年度、預約／班次／2027保證未核實。','accueil à la gare de Poitiers','Undated exchange welcome;2016 event elsewhere excluded'),student_support=fact(pc,'SURIEE有國際生接待職務，官方辦公室15rueHôtelDieu；這是office，不是交換授課或住宿校區。','Accueil des étudiants internationaux','Undated SURIEE office directory')))
    r=source('de7883ddcf7e133d302c9a79');j=source('8f3f0d3b83acf5b886233c5d')
    add(24,dict(student_support=fact(r,'RIFA可安排partner每月互動2–3次及生活協助；2025參加135人是活動統計，不是2027交換名額或配對保證。','Partners meet two or three times','Undated RIFA service;FY2025 participation statistics historical'),course_restrictions=fact(j,'一般日語centre提供academicJapanese與JLPT/BJT準備；first-year本科課介紹不能當交換最低JLPT或每週必修要求。TKU交換修課權／2027開課待確認。','Preparation for various exams','Undated general Japanese-language support; exchange course access not verified')))
    st=source('260f27782ff6a95cdfd216ac')
    needle=next(line for line in st['text'].splitlines() if 'department' in line.lower() and 'exchange' in line.lower() and ('most' in line.lower() or 'conduct' in line.lower()))
    add(64,dict(department_scope=fact(st,'官方指出多數exchange由departments執行；全校與department agreements要分開。此機構策略頁没有確認TKU院系範圍、名額或本期選項。',needle,'Undated international strategy;2026-07-06 update not academic period')))
    m=source('c1e5671d3e4477e58fa26726')
    add(15,dict(student_support=fact(m,'現UMLP DREIF接待國際生，PlaceSaint-Jacques/MSHE辦公室，週一至四9–12、14–17，週五關。與淡江名錄舊Franche-Comté的協議承繼／校區仍待確認；不推定outgoing補助適用incoming。','Elle accueille et accompagne','Undated UMLP office; former Franche-Comté TKU agreement continuation unverified')))
    assert len(rows)==8 and len({r['id'] for r in rows})==8
    (BUNDLE/'milestone4_reviewed_host_facts.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(candidates=69,body_review=Counter(r['body_review_status'] for r in reviews),additional_reference_institutions=len(rows),additional_fields=sum(len(r['fields']) for r in rows))))


if __name__=='__main__':main()
