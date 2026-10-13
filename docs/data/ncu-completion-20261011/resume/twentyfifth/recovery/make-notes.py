from pathlib import Path
import json,hashlib
W=Path('/workspace/ncu-resume-work/twentyfifth');notes=[]
def add(slug,rid,ext,scope,*pages):
 p=W/(slug+'.'+ext);m=json.load(open(p.with_suffix(p.suffix+'.source.json')))
 notes.append({'slug':slug,'row_id':rid,'filename':p.name,'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_url':m['url'],'document_year_scope':scope,'native_pages_read':list(range(1,len(pages)+1))if ext!='html'else[None],'visual_pages_read':list(range(1,len(pages)+1))if ext!='html'else[],'page_notes':[[i+1 if ext!='html'else None,t]for i,t in enumerate(pages)],'full_document_read':ext!='html','html_main_passages_read':ext=='html','converted_from_word':ext=='doc','license_scope':'公開官方原件僅供查核；未取得頁內照片獨立開放授權，不當授權校景。'})
old=[
'封面校名與校徽對應Altinbas，無獨立照片授權。',
'印刷2/3頁目錄與校景，僅目錄不是交換開放學科佐證。',
'印刷4/5歡迎incoming、國際處MahmutbeyDilmenler26，伊斯坦堡旅遊文字不作資格。',
'印刷6/7建校2008Kemerburgaz、2017更名；排行與學生心得是舊宣傳資料，不當當期表現。',
'印刷8/9三校區、兩醫院、400人guesthouse等校級統計；不是中央名額或保證交換床位，90%獎學金不適用為中央交換補助。',
'印刷10/11Erasmus/ICM/GlobalBilateral/Summer一學期或全年；舊提名/申請秋6月中至7月中、春10月底至11月底。各學院programme列表不代表全部對中央開放。',
'印刷12/13學士與研究所列表，多處**無圖例，不自行把星號解為土/英語或開放限制。',
'印刷14/15Gayrettepe管理經濟社科藝術法律應用社科研究所；Mahmutbey外語工程理科研究所職業；Bakirkoy醫藥牙健康。舊免費跨校區接駁，15分鐘機場/45分鐘Edirne是宣傳不當交通保證。',
'印刷16/17交換導師、24/7圖書館、社團、健康中心英語醫師預約。Mahmutbey宿舍保證有申請且按時付費者，另有COVID限制；不是無條件116保證。',
'印刷18/19預算每月私房350EUR明確不含學生宿舍，交通5EUR、一般食物社交150EUR分别列；350不是全月總額也不是宿舍費。免費跨校區接駁和市區學生折扣卡不同。迎新在開課前一週為旧指南說明。',
'印刷20/21Buddy抵達前註冊申請、心理輔導、基礎土耳其語可參加但未寫免費；短語表和學生心得不當要求。',
'封底明寫13.03.2023；三校址MahmutbeyDilmenler26、GayrettepeEsentepeBuyukdere147、BakirkoyKartaltepeIncirli11，沒有照片獨立授權。']
add('altinbas-handbook','ncu-093','pdf','原件頁尾13.03.2023；12實體PDF頁，2–11多為跨印刷雙頁',*old)
new=list(old);new[5]='印刷10/11提名/申請改秋6月初至7月初、春10月初至11月初；不是舊版中旬/月底期限。校级programme列表不等於中央當期逐科開放。';new[8]='印刷16/17重排版移除COVID句，仍寫Mahmutbey宿舍申請且按時繳費有保證；與官網有限床位不同，不當116保證。導師、圖書館、社團與健康中心內容保留。';new[11]='封底明寫20.09.2023，不因2024/02網址變成2024學年。三校址同舊版。'
add('altinbas-handbook-2024-link','ncu-093','pdf','網址2024/02，但原件頁尾20.09.2023；非2024或116學年',*new)
notes[-1]['pixel_identical_review_inherited_pages']=[1,10,11];notes[-1]['comparison_note']='逐頁native比較，僅6/9/12文字變動；原生新段已完整讀。頁1/10/11與已實看舊版像素逐位相同，其他9頁新版另逐頁view_image實看，比較檔保留。'
add('altinbas-incoming','ncu-093','html','網頁更新2024-11-05，程序與截止未註學年',
'GlobalExchange雙邊：須母校提名，免接收學費無方案獎學金。泛述每學期2全年4但另要求依各協議部門名額，不當中央名額。秋/全年6/1–7/1春10/1–11/1。UG至少1年GPA2.20/4，PG至少1學期2.50/4。B2或TOEFLPBT550/CBT213/iBT80兩年內；英語母語或已在英語國家讀高教可免考，母校英授需正式英語能力信，不是免所有證明。提名後寄網申，完整附件清單未列；LOA後寄非初申已錄取。平均5課20AU=30ECTS，交換無固定下限但建議至少3課，母校決定負荷。開課單學期初提供，LA協調人簽；可能先修/容量不足、跨領域要母校核准，加退結束不能改。到後居留三種住宿證明不是初申，舊法指引非政府當期規則。住宿限量。Buddy每生配對與舊PDF需先註冊分開；迎新未列日。EWI/UZEM用途與協調人註冊。離校checkout、還物/罰款，成績等齊最晚考後一月加寄送數週，不是初申文件。全文主體至contact讀完，導航不當實質規則。')
add('bingol-student-documents','ncu-094','html','未註年Gelen-Giden文件索引；方向須以原表正文核對',
'主表左Gelen入境右Giden出境，study與traineeship分開。左列申請media25135、LA37755、attendance25128；右申請25134不同id同檔名。左申請下載正文卻OUTGOING，不能以索引標題蓋過內文。LA接收Bingol/TRBINGOL01可確認；出席函是到/離境且措辭yourinstitution有出境方向疑點。不能把三個連結合成三項已核初申必繳。')
add('bingol-application','ncu-094','doc','未註學年Word；本地2頁；入境索引錯向連到OUTGOING',
'Bingol校徽卻標ApplicationFormforOUTGOINGStudents，Turkish國籍預填、身分學制/交換/障礙/動機欄；錯向表保留稽核但排除中央初申，不當只收土耳其人。',
'出境目的校Preference1/2/3，英法德自評與學生簽署聲明；不能當來賓格爾語言要求或初申表。頁碼為LibreOffice本地呈現，不是原生固定PDF頁。')
add('bingol-learning','ncu-094','doc','未年LA、AcademicYear20../20..空白；本地3頁，檔案metadata不是學年',
'接收校BingolUniversity/TRBINGOL01，Selahaddin-iEyyubiAydinlikCadNo1zip12000；BeforeA外校課、B母校認列，A1至母語checkbox沒有一律最低值，不能取消母校B2。',
'Before承諾學生/派出/接收三方；DuringA2三方email/簽章，B2學生母校；AfterC成績、D回校認列不能列成初申已完成附件。預勾刪加課示例不是個人實際變更。',
'TableD續欄及12腳註，responsibleperson異於contact時才填。更課原因與EQF學制說明不是中央博士名額或語言豁免。本地3頁原生文字與逐頁圖均讀。')
add('bingol-attendance','ncu-094','doc','未年到離境證明，本地1頁；方向措辭仍疑為本校出境',
'校IO致DearColleague，在yourinstitution當Erasmusstudent措辭指向出境，不能靜默改成incoming必繳。到達日學生+facultycoordinator、離開日學生+erasmuscoordinator；是交換期間到離境佐證，不是初申附件。舊UniversiteCadNo1地址不據此更換既有位置。')
add('bingol-course-catalogue','ncu-094','html','未註學年院系課程索引，未逐讀連外單科課綱',
'主文院系列表全讀：經管business/econ/politicaladmin；文理philosophy/EnglishLit/molbio/Psych/socialwork/sociology/history/TurkishLit/Englishtranslation；工程computer/electric/civil/architecture/mech；theology；healthnursing/nutrition/occupationalhealth；agrihorticulture/fieldcrop/plantprotection；vet；sporttraining/PE/recreation/mgmt。只有目錄，未驗各科ECTS/授課語言/當期開課或中央開放，不能按系名當全英語。')
assert len(notes)==8 and sum(len(n['visual_pages_read'])for n in notes)==30
(W/'reading-notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n')
