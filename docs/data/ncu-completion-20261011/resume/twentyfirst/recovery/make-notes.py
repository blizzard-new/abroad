from pathlib import Path
import json,hashlib
W=Path('/workspace/ncu-resume-work/twentyfirst'); notes=json.load(open(W/'temple-reading-notes.json'))['sources']
def add(sid,scope,*pages):
 notes.append({'source_id':sid,'document_year_scope':scope,'native_pages_read':list(range(1,len(pages)+1)),'visual_pages_read':list(range(1,len(pages)+1)),'page_notes':[[i+1,p]for i,p in enumerate(pages)]})
add('1ECGpDBzluK_H5EsPeU-yK4mkaV8X7dMR','檔名2026，正文未註年，Clermont School of Business',
'校徽ClermontSchoolBusiness、FCLERMON46與4boulevardTrudaine63037ClermontFerrandFrance，和母校舊ESC同址。英授大學1–3及研究所4–5秋春皆有；免費法語初中級全年、其他語言進階每學期。課單xlsx未另核。秋9月初–12月中，春1月初–5月底；每學期8至30ECTS。學生申請秋5/31春10/31，未列提名日。A–E有學分，FX/F無；成績單秋2月春6月中。',
'母校提名姓名/學制/creditseeking或dualdegree/郵箱/母校窗口，線上選partnerinstitution。初申4項照片、護照或ID、前年度成績或學位證明、授課語言證明。一般B2；表格degree-seeking英語正式考試ITP550/iBT80/IELTS6/TOEIC750/DET115/PTEgeneral3/academic58/ITEPacademic3.9/ISEII/CambridgeB2或C1，母語者例外；非學位交換可接受B1，不擴到全部方案或中央116。法語degree母語或B2。Moversia收費服務含接送與租務等，不免費或保證宿舍；私房/擔保選項。月生活700–800EUR含租食帳單，首月押金水電電話等另計。線上/實體迎新不寫強制；簽證保險標題下實際只列非EU逾3月簽證，未提供保險。',
'整頁實看僅頂部PARTNER INFORMATION SHEET小頁眉，其餘白頁，無額外規定；不能把空白页算缺失內容或未讀。')
add('1_21NXsggFlaHJ3UDg32CzPV6MDuM3Ee9','母校舊ESC簡介，語言格註2024更新',
'舊ESCClermont校徽、法國4BdTrudaine63037地址吻合；大學部/研究所。語言格為嵌圖，實讀2024更新B1可接受僅non-degree-seekingexchange，非所有degree門檻。秋9–12春1–5月。無法預訂hallofresidence，Moversia收費住房服務；不會法語及無擔保人找房困難是舊校方說法。生活610–1050EUR/月含租食帳單，首月額外押金等；與新件700–800不同不任選低值。頁內地圖未授權校景重用。')
add('1pqSP_a3saamO8OoJo21AI22MTr0TYuJi','2026–2027日內瓦交換資料表',
'UniversityofGeneva標誌與瑞士24rueduGeneralDufour1211Geneve4，AcademicExchangeOfficeUniDufour非所有教室。母校提名秋3/31春8/31、學生登錄秋4/10春9/10。提名須姓名/email/學期領域及特殊需求。初申6件動機信、成績、照片、護照、語言證明、studyplan；現就讀授課語言可免證明須條件。完整申請才可預期5/30或10/30接受信。秋2026/9/14–2027/2/12，春2/22–6/25，理學院到6/30；考試實體非遠端。迎新9/11及2/19。',
'課單夏季出，先用舊年規劃後調整。學期前核studyplan，抵達只可小改不能全換主學院；最多2院，本科不能碩士課。經管/法/英語文學/語言學須母校對應主修。標題recommended但正文requested英法B2；FrenchC1明確適用French及Englishliterature，不擅改英文C1。ELCF預備年B1、浸入年A2例外；考試或教授官方信，兩語課需兩份語言證明，p1現授課語豁免仍保留。法語線上測試CHF10非全體必繳；學前密集優惠非免費，學期內2門免費法語支持每週各3ECTS，報名後必到。良好成績min4是0–6校方scale非GPA4/4，A6至5.25/B5至4.75/C4.5/D4.25/E4/F<4。',
'非EU簽證校方建議提前3月詢瑞士館、30歲以上特許、抵達OCPM居留登記；非現行政府法規驗證。Cite一棟翻修減房，早提名先到先得；超過34歲不能申Cite非全市不能租。生活約CHF2000/月；財力文件為簽證居留，非初申第7件。健康意外必需，私人保單可申請認可非自動，瑞士學生保險from65CHF/月非全包固定價。成績評量後約6週，離校前提供母校國際處郵寄地址，屬後續步驟非初申。')
add('1nkS_ocMRsINB0luAkc4m-1VxfUpZz6Fn','未註年母校日內瓦介紹',
'同校名校徽瑞士日內瓦；大學/研究所，英B2 must、法B2且心理教育強制法B2，不能覆蓋新C1特例。秋9–2春2–6。月CHF2000；分項住房500餐基本600保險100只和1200不是完整2000分解，未列800不自行補。保險舊100與新from65差異不混成同年。校景圖未獨立開放授權。')
add('10uCIcGHCpV6nqVloAagGMONP8QL4Zazc','標題2026–2027；內文校曆2026、課單Fall2025，混合年度保留',
'Dongguk校徽首爾30Pildongro1gil Junggu04620；非慶州。提名秋5/15春11/15，申請秋5/30春11/30。無語言證書要求非無能力要求，GPA3/4.5，大學或碩士ONLY。名額依協議無數字。7附件申請表、中英成績、中英在學、中英推薦、護照、全停留保險、JPG頭照；母校國際處email一併送，拒個人，無紙本；保險可簽證後補。大學排藥學/未來融合/韓國音樂/戲劇/體育文化，研究所僅一般研究所不接受特殊專業所。生命科學生技全部一山校區，研究多韓語可選英授大學課。大學至少1課最高18學分，碩士至少2課最高9；底列泛1課18不能抹碩士限制。2026春3月初–6月中秋9月初–12月中，課單寫Fall2025非當期已核。',
'4.5評分表A+4.5至D0=1,F0，文字aboveD0但表D0給1，保留不要換算抵免。學期後一月內電子成績給學生。Buddy不保證1對1，無接機。校方D2-6錄取寄母校再印申簽，所需件另核領館。韓語班非學分無國際處正式成績，10週季課30%折後KRW1225000，schedule/fee可變；付款段版面截切不补缺字。宿舍不保證，入宿後另TB/MMR/保險，最多一學期含假期，年交換後段自找；原句後部截斷不自補確日。忠武校外3–6人可用厨房，南山校內雙人無厨房，160–170萬KRW/學期含水電一次繳；分配1或7月中。生活35–50萬/月不含自租40–60萬/月。',
'Both are required紅粗體：本國意外傷害/住院保險涵蓋全停留＋韓國NHIS不能二選一。居留卡後通知繳，約KRW80000/月以實單為準，校方舊週期说明非現行政府規則。')
add('1nHSbJlL0JoiIS46Jp9YxBo-24tGP8aQA','未註年母校東國介紹',
'校名logo首爾26Pildong3ga舊址吻合首爾校，地圖含其他校不重用。母校大二以上/研究所與新碩士only分列。英語不交測驗但須跟課，舊英授25%商英系50%非當期保證。秋8–1春2–6較新校曆不同。D2簽證與出國前全面保險紙本要求屬舊說法，新表免紙本且可簽證後補，不當116必繳硬要求。')
add('1BmTecGKmVudvDqU_dlMpcFfu0LWFFiEi','未註年母校布勞爪哇全校介紹',
'UB校徽印尼東爪哇MalangJalanVeteran65145，同校非其他印尼大學；全校地址非經管MT.Haryono165。UG/graduate。全英會計管理經濟，所有exchange須3學分印尼語文化且入成績；新FEB未確認不直接取消或全擴。舊ITP500/IELTS5.5/TOEICequivalent無數字不能推定。舊奇數9–2偶數3–8跟FEB不同；300USD/月未列完整細項。可宿舍或校外租非保證房源。')
add('1Q7NgoqWBefphbjBdkdhrkoKNx4rLgSiF','未註年FEB經濟商學院交換海報',
'UB校徽與FACULTYOFECONOMICSANDBUSINESS身份清楚，僅該院。初申10項成績CV學院聲明學生證推薦信意向信英證有效護照3x4白底照申請表，全上傳入口。7/1與12/1截止無年份，free tuition fee僅本方案外校學費，不免中央/生活住宿。海報照片沒有獨立重用授權。')
add('1QzL2RhXhbqKkiNsy_zl1H7IOn8qu22WG','未註年FEB UB國際生資料表；院級非全校方案',
'UB校徽經管院印尼Malang JalanMT.Haryono16565145，學院IRO/IUP與全校簽證窗口不同。學期I8–12月II2–6月；申請7/1、12/1、接受7/10、12/10無年。全英課；非英語母語原圖嚴格大於TOEFLITP525、IELTS5.5、Duolingo95（>非≥），不擅改門檻。10初申全部英文或官方英文翻譯：成績CV學院聲明學生證推薦意向英證有效護照3x4白底照申請表，附表格入口。',
'LoA後才收到課單與填選課表非初申。SKS寫170分鐘或45.3小時全時學習但未清楚週/學期跨度，不自行等同ECTS；成績A>80–100/B+>75–80/B>69–75/C+>60–69/C>55–60/D+>50–55/D>44–50/E0–44。成績I期1月II期7月寄。生活$120–200/月、宿舍$350/6月依房型、校外$150–250/月，$未明ISO幣種不能自動USD；母校舊300USD另列不合併。簽證只連外手冊待讀不推規則。抵達Juanda需接送先確認，97km/2hr概估不承諾免費或已訂。')
for n in notes:n['sha256']=hashlib.sha256((W/(n['source_id']+'.pdf')).read_bytes()).hexdigest()
assert len(notes)==11 and sum(len(n['native_pages_read'])for n in notes)==20
(W/'reading-notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n')
print('11 documents, 20 native and visual pages persisted')
