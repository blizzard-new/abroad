from pathlib import Path
import json,hashlib
W=Path('/workspace/ncu-resume-work/twentyfourth');notes=[]
def add(slug,rid,ext,scope,*pages):
 p=W/(slug+'.'+ext);m=json.load(open(p.with_suffix(p.suffix+'.source.json')))
 notes.append({'slug':slug,'row_id':rid,'filename':p.name,'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_url':m['url'],'document_year_scope':scope,'native_pages_read':list(range(1,len(pages)+1))if ext!='html'else[None],'visual_pages_read':list(range(1,len(pages)+1))if ext!='html'else[],'page_notes':[[i+1 if ext!='html'else None,t]for i,t in enumerate(pages)],'full_document_read':ext!='html','html_main_passages_read':ext=='html','converted_from_docx':ext=='docx','license_scope':'公開官方原件僅供查核，未取得頁內照片獨立開放授權；不重用為校景。'})
add('monaco-factsheet-2025-26','ncu-060','pdf','2025–2026 IUM author factsheet hosted by official partner Carleton',
'IUM紅校徽、LeStella14rueHubertClerissi98000PrincipalityMonaco，footer登記辦公室6rueAugustinVento不同用途。提名4/15、10/15，學生4/30、10/30。BBA秋2025/9/11–12/19春2026/1/22–6/26，秋考12/11–19春考5/4–12；UGremedial5/26–29是跨欄合併列，不自行分秋春。MSc秋9/4–12/19春1/7–6/26，秋考12/15–19春3/23–28+6/10–16；碩士補考秋2026/2/23–27春6/30–7/4超過正常學期。正式提名後收到網申連結。8附件：passportorID、passportphoto、resume、coverletter、ToR、healthandliabilityinsuranceACKNOWLEDGMENT(不是已繳保單)、languagelevelcertificate(母校非英授才要求)、LA。BBA/MSc英授，選program與specializationmodules按預設課組並由homecoordinator同選，不是自由全校選課。UScredit每1約15contacthours，每選項至少15US=30ECTS，不改ECTS15。',
'2025–26無校內住宿，學生自行找且付費，學服協助不是保證。平均單房600–800EUR、公寓800–1200EUR，原表沒寫每月/每學期，不能擅補計價週期或当完整生活費。學服連guide但未讀guide不可算全文。簽證依住法國/摩納哥區分，VLS-TSvisitor原文只是舊校方說明不當當期政府認定。需health/accident/liabilityinsurance，建議公司不等於校方保證全涵蓋；初申ack與最後保險保障不同。Nice機場到Monaco約30–45分(交通方式混列)，尼斯火車20分44班舊概述不當當期班表。學生社團每學期87.50EUR明寫ToBeConfirmed不是tuition或當期定價，折扣非免費。')
add('buem-incoming','ncu-061','html','官網校曆2026–2027，其餘程序段未另註年；Erasmus incoming範圍',
'官方BUEM/VSEM、SKBRATISL13、Furdekova16與既有照片座標吻合，不是EUBA。先確認bilateralagreement並母校提名。EWP/OLA路徑：onlineLA+申請表+CV+passportorID；非EWP/OLA改紙本LA加相同3件，共4類不是兩套要疊交。電腦填、列印由學生及母校coordinators簽。截止秋/年6月底春11月底，guide另具體6/30、11/30。接受後約4週回簽LA及LOA給母校，不能初申就要求接收方先錄取簽章。2026–27秋9/28–1/30、授課9/28–12/18、考1/4–30、intro9/28–10/2；春2/8–6/30、授課2/8–4/30、考5/3–6/30、intro2/8–12。不直接取消混校母校原件的問題，或當116雙邊適用已核。')
add('buem-studyguide','ncu-061','pdf','檔名2023，正文無新學年；舊一般incoming指南',
'同BUEM/VSEM、SKBRATISL13、Furdekova16校名地址，非EUBA。期限秋6/30春11/30，沒有2027/28年。',
'有自營宿舍，email住宿管理及公開forms入口詢問，非全體保證房；另hostel/私房。非EU簽證/居留及90天文件、到後登記3工作日等均舊校方法律說明，須當期政府核實，沒有轉成已核新法；行政居留健康文件非初申附件。',
'離境交還居留卡說明與官方自稱僅參考保留。全期健康/意外/責任險，EU/EHIC與nonEU不同。33000等保險上限原文approx33200、孕16600為示例保障不是保費或法定門檻；個人保單依契約。',
'舊公車日夜15/60/90票種、SMS1100與app資訊不當現期票價班表；買SMS先收到才上車。ISIC一般卡非感應卡、不能保證交通折扣；非全免費。',
'斯洛伐克歷史與首都地理旅遊說明，不用於交換资格或當期校曆；照片無開放校景授權。',
'旅遊概述含稅關、飲水、230V50Hz、語言與資訊服務；不採舊稅關敘述為當期法律規則。',
'生活禮俗、假日表及醫療電話為舊旅遊內容；不據此建立116休假／醫療建議。',
'郵局、觀光治安、料理、吸菸、COVID入境與EU簽證舊概述；不當現行法／醫療核實，沒有帶入學生規則。',
'換匯旅遊資訊與緊急電話表，舊夜車N31時間不當現行班次；只留完整核讀證據，不作116交通保證。')
add('buem-accommodation','ncu-061','pdf','檔名2023，正文未註當期年',
'BUEM宿舍Hlinicka1Rača約30分鐘距校；StudentHouseTomasikova34約20分、InchebaViedenska7約10分、私人房約15分是各類概覽，不是保證路程／房源。未列价格或床位，官網current價另讀；不開第三方付款或送申請。')
add('buem-dormitory','ncu-061','html','住宿價目含2026/9/1起長租及獨立3月交換方案；3月段未另註生效日',
'原頁正文全讀。BUEM用Hlinicka1職業學校宿舍3樓、非Furdekova16教學校區；距校9.2km。Comfort3床、DeLuxe2床；Comfort兩人要付第三床，不能套三人單價。2026/9/1起≥11月每人每月150/220/245EUR，9月或兩學期180/260/275；單列3月Erasmus/bilateral每人每月Comfort三人200/DeLuxe雙人300。交換3月不能自選長租150低價；未說當期116保證、押金期限未核。短住25EUR/night需特別批准。洗衣含費、wifi共享廚衛、兩付費車位需先約；附加費依rules未讀不假設全包。3號電車到PeknaCesta步行8分、校26分為概覽非當期班表。')
add('buem-courses','ncu-061','html','未註學年外語課單，UG/Graduate各秋春；未逐讀連外CourseDescription檔',
'主文從Subjects taught in foreign language至postgraduate空段全部讀完；分UG秋春、Graduate秋春，多英語部分英/俄。學士秋Accounting4、IntroBusinessAdmin5、law4、EconomicTheoryI5、entrepreneurship5、finance5、languageI/III4、HR5、IT I/III4、trade4、mgmtI5、marketing5、nationalpolicy4；春Finance5、EconII5、stories5、financeanalysis5、langII/IV4、ITII4及原錯INFORMATICS VI/codeIV4、law4、marketingservices4、mgmtII5、project4、risk5、social4、tax4。碩士秋corporateecon5/crisis6/projects4/entrepreneurship4/EUpolicy4/financialanalysis6/intlrelations4/marketingstrategy5/quality6；春risk5/environment4/financiallaw4/financialmgmt5/intercultural4/intlmgmt6/investment4/labour4/strategy5/tradebarriers4。原頁未宣称全課當期開放，沒入學B2新門檻，不用course語言取代母校條件。部分標題/代碼錯誤保留，未把空postgraduate當博士名額。')
add('buem-application','ncu-061','docx','官網現行連結的DOCX表內仍ACADEMICYEAR2022/2023；本地LibreOffice呈3頁',
'官方DOCX原文OOXML加本地轉PDF核讀；2022/2023明顯舊年不可直接當2026/27新表。photo一欄，原模板多處預選男/曾實習等是表格預設不是申請資格，不能帶入使用者身份。電腦填列印簽名，母校系所/校級窗口及個資、BUEM地址。',
'期間、預計ECTS、動機、母語/授課語言與其他語言能力自評、既往學制/交換與相關工作經驗。自評欄不等於免語證或最低A1/B2核准。',
'學生、母校系所與校級協調人簽章；接收校acknowledgereceipt含provisionallyaccepted預選，不能当真錄取或在申請前先須收到校方錄取。附件另列CoverLetter、LA、EuropeanCV、EnglishToR；與网页僅4類清單差異，CoverLetter與EnglishToR為舊表追加待確認，不靜默取消或改成當期必繳。')
add('buem-learning','ncu-061','docx','未註年Erasmus LA範本，AcademicYear20…/20…；本地轉PDF4頁',
'OOXML原文加LibreOffice轉PDF/原生頁字讀，收校BUEM同碼地址。Before TableA接收課程與TableB母校抵免；A1至母語checkbox無預定最低值，不能當語門檻；學年空白不是2027。',
'Before承諾學生/派出/接收三方，官網接收後回簽LA故不要求先拿接收錄取簽章再申請。During TableA2變課需三方email或簽、B2母校認列變更需學生母校；After TableC外校成績、TableD母校抵免不列為初申附件。',
'只有TableD跨頁續欄及總學分空格，非新的文件需求，頁面實看含大量空白。',
'腳註12項定義，responsibleperson名稱email僅異於contactperson時填；更課原因：課未開/語言不同/撞期/其他與替換/延長/其他。不用模板學制博士選項擴NCU名額。原生OOXML主文未含footnotes，另以轉PDF原生p4全文核讀；非OCR。')
assert len(notes)==8 and sum(len(n['visual_pages_read'])for n in notes)==19
(W/'reading-notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n')
print('8 source originals: 3 PDF + 2 DOCX / 19 pages fully read, 3 official HTML main passages read.')
