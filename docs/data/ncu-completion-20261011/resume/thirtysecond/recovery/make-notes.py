import json
from pathlib import Path
W=Path('/workspace/ncu-resume-work/thirtysecond');p=W/'reading-notes.json';notes=json.load(open(p));assert len(notes)==2
rows=[('18V9vNjSgs4HCh9YSLlzmQYs_qXvLn9yK','f7f73710088d8e7e65fb232c74c684266d19eb25f36f4ece807cf9b9ccc4ecf1','大阪公立大學Fall2025；不替代已核Spring2027',[
'2025秋UG/MA、N2相當；UG只有基幹教育，MA專業、情報基本線上，排除醫護獸復健，無日本語學系或論文指導，學校決定配屬。森之宮於2025秋開校屬該版規劃，不推現況。交換9/24/25–3/31/26或9/23/26，不延期。提名4/1、申請4/10，母校承辦送件，不是116。',
'課程連2024Fall是舊表。9/20/25搬入、9/26上課、1/20–2/2/26考試。I-wing錄取後才申、宿位有限可別宿、不自申，校外通知校方但無協助。中百舌鳥至森之宮約一小時，Metro340/12000月、另路500/16000–18000；不享學生通學定期。英文成績PDF送母校，一年期無半年度正式成績。COE另寄母校、政府不保證核發、日本籍含雙重無COE。',
'LOA錄取決定後PDF，虛假資料得撤；不受理個人查詢選考狀態。簽證以LOA/COE依領館辦、必要預約、visa後才購票。迎新說明市役所、校園、學生證；宿舍與日語另限適用者，問題經母校代表。',
'實看日英清單：JPEG三月內彩色脫帽清晰且不同護照照片；護照直向A4彩色PDF不用JPEG/PNG，未有告知預計取得日。履修願Excel填藍；UG志望理由列Excel/PDF，MA研究計畫Word/PDF。日語JLPT/JTEST/JLT或母校日語教師指定表；英語證明有才交。指定英文在籍確認由母校承辦填，最新英文在學及成績皆PDF。配慮表僅需要者、學生/承辦/教師可填、Excel/PDF。總則母校email/cloud，不收個人、不需原件，不把Word/Excel轉PDF，和表格部分PDF選項落差保留。照片尺寸外鏈未讀。本頁日文字型抽取亂碼已原圖讀，不等原生文字可靠。'
]),('host-chuo-next-02','f41e1f28e004c7d790c127db4b302398e4466c0d0557a370018e327307486a67','Chuo交換協議名單截至July2026；不是116名額表',[
'標頭asofJuly2026、workingstudentexchange。先院級法/經濟/理工/文/政策，法學臺大、台北大是院級，曁南人文也是院級；不要把中央的條目套院級。未列者聯絡國際處。接著UniversityWide由澳洲、比利時、加拿大、柬埔寨、中國開始。',
'全校協議清單接中國至義大利；各國欄與校名視覺對齊。不是接收學院/課程清單，沒有名額、成績或期限。',
'全校協議清單韓國至土耳其，Taiwan欄NationalCentralUniversity國立中央大學確實列於UniversityWide。NTU/TaipeiLaw於p1不能混入這列。荷蘭Erasmus及新加坡NTU仍列具學部名稱，不自行抹掉限制。',
'全校清單UK/Uruguay/USA/Vietnam至末頁。無額外交換名額、2027–28收件、住房或保證錄取條款；只證2026/7協議列名。'
]),('1AML0E9CXUoPyoVyhc05Wpj653l1mrkfT','ce66394275f4c8062833bf689a14bb704bcaa54ad52fc69a9656f92d1a351b3e','UniversityofManitobaCanada2027/28，2026/9修订；非Neubrandenburg',[
'校名/WinnipegCanada/UMSU541國際處明確。線上提名不email，之後學生+承辦收指引。秋27/冬28主輪3/15提名4/15申，冬28次輪8/1、9/1；夏27提名3/15申3/31。GAC2/5、2/26不同且參與可能變更，不套臺灣必適用。住宿4/1秋、5/1冬是開放，不是截止。此頁summer8week。',
'精確2027/28日期未定，秋9–12、冬1–4。此頁summerfourweek與前頁8week衝突。母校提名後給入口。UG母校良好學業+語言、faculty決定；PG競爭，4年學士、最近兩完整學年GPA3/B，3年學士只能本科1000–4000不能PG。英文成績/正式翻譯PDF+抬頭grading scale、portal詳細studyplan、1–2頁DOC個人目標。',
'EnglishproofPDF依UG/PG連結及例外，不在本頁給分數。PG加本科成績與母校研究所在學acceptanceletter，抬頭+學程結構焦點、承辦或導師寫。校級IC可農食、Art、Arts、環地、Kinesiology、Music、Science，Law/SocialWorklimited；法建議高年級背景。Architecture/Education/Engineering/Health/Asper不開放；UGCS1000–4000及Psych/EnglishHonours排除，不套全部學校交換協議。',
'學費免但學生組織約$150/term、書100–200/course及可能lab/fieldtrip。原頁只$未標CAD，既有他源幣別不得冒本頁明示。住房stronglyrecommended不mandatory/guarantee，含餐單房與不含餐套房分開。移民只連結不本頁簽證全讀；從母國購travelhealth，供應商自選。健康/障礙支援、buddy可抵達前聯繫、迎新社交，過往excursions不是承諾當期活動。Cannabis泛稱Canada19歲不能當全加拿大現行法律，未採為法律建議。',
'InterculturalLeaders秋冬各8sessions，LanguageExchange每週語伴、自願。運動中心、200+社團及學術/無障礙/誠信支援連結，旅遊例子不是學分課或包含费用。末行LastrevisedSeptember2026。未新讀所有外鏈。'
])]
for sid,sha,scope,ps in rows:
 notes.append({'source_id':sid,'sha256':sha,'document_year_scope':scope,'native_pages_read':list(range(1,len(ps)+1)),'visual_pages_read':list(range(1,len(ps)+1)),'page_notes':list(enumerate(ps,1))})
p.write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n')
