# 中央116-1來源查核與平台接入（進行中）

基底為合併PR #1後的`f6ad1b8`，已確認包含臺大六項修正`daad399`。獨立worktree `/workspace/abroad-ncu`、分支`data/ncu-exchange-20261008`；已推送checkpoint `dc126d2`、`95c883a`，draft [PR #4](https://github.com/blizzard-new/abroad/pull/4)。原工作目錄、中正及淡江分支未改動。本文件不宣稱中央全部外校資料完備。

## 適用年度與實際覆蓋

2026/10/8中央交換計畫首頁已提供[116-1甄選簡章](https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangenotice.pdf)，名額表預定2026/10/12公布（第2頁）。當日首頁仍連[115年度表](https://oia.ncu.edu.tw/static/file/26/1026/img/272/115exchangeschoolist-20251127.pdf)，所以**所有116名額均為null、待確認**。未知不等於0名額或未開放。

115表216列完整保留；靜岡、南洋理工重複列保留成兩個program options，其餘含北海道院／校級及自費方案，不相加名額。目錄214項不是214所當期已開放學校。

| 指標 | 2026/10/8實際結果 |
| --- | ---: |
| 115 PDF原始列 | 216 |
| 平台目錄／pending流程／生活資料項 | 各214 |
| 公開Drive遞迴資料夾 | 173 |
| 公開附件下載／抽取紀錄 | 459，下載錯誤0；36份含100個無文字頁、2份字型缺字 |
| 另查公開host／home網頁 | 78筆公開頁／文件讀取紀錄（含一筆browser摘錄） |
| 有相關host原文的目錄項 | 194 |
| 人工整理的host紀錄 | 18（全部partial） |
| 全部15欄完成116當期核准 | **0** |

附件取得／文字抽取不是逐欄當期查核完成。其他資料仍可繼續查；未查完的欄位不稱「官方未公告」。

[逐校逐欄CSV](../src/exchange_info/official_data/ncu/field-coverage.csv)與[完整證據／缺口JSON](../src/exchange_info/official_data/ncu/field-audit.json)包含15欄：名額、學制／校區／track、語言、home文件、host文件、home截止、host截止、交換期間、課程、學費、生活費、住宿、保險、簽證、到校。JSON保留來源URL、PDF頁碼、原文、適用年份及查核日期。CSV與JSON不是全綠即完成的數字展示。

## 已確認母校規則

線上2026/11/16 09:00–12/4 12:00；學生紙本12/11 17:00交系所；系所12/18 17:00送國際處，全部臺灣時間。校內錄取公告2027/1/11 09:00。

大學部平均60、研究生70；在職專班可申請但無研修獎學金，目前大五／大六不可申請。未知學制、成績或大學部年級不回傳通過；不將GPA換算百分制。仍須系所與導師／指導教授同意、一學年成績及全程學籍，境外生／國籍限制分列。

七項home必繳文件及簽章分列於home step；外校文件放入另一host step。正式語檢影本必繳、不限級數，英檢兩年有效，不能截圖或補繳。外校語檢是另一規則；第4頁補件說明與第7頁提名前具備要求的差異保留，不取消較早的準備義務。第4頁TOEFL ITP與第6頁PBT差異亦保留。

首頁仍下載forms-2022.pdf：個資同意第1頁、家長同意第2頁、109年度範例第3頁。只使用現行表格連結，不將範例舊日期當116截止。行前兩週程序、回國一週程序、WORD心得800–1500字及至少四照片接入流程。課程兩門且一門專業課與學則兩門或六學分分別列出，採認由系所審定。

## 十八筆人工外校整理與具體缺口

- Manitoba：AY2027–28表（2026/9更新），提名／申請梯次分開、UG／grad文件不同、closed faculties與Computer Science限制、住宿開放、免學費及額外費用、保險及行前。精確校曆官方表稱未定；英文門檻專頁、當期房價／housing截止、個人移民文件仍待查。
- 信州：AY2027–28、Fall2027提名／申請／暫定到校日，Sheet清單、COE另系統、財力、課程、住宿、預算。英日版本暑假年份及coop保險金額互相矛盾；Spring2028期限、最新Sheet／COE包未取得。不可用Spring2027推算2028。
- Strasbourg：AY2027–28、主／春季補梯次、六項host文件、法文B1強制／B2建議及領域例外、learning agreement兩週變更。新版文件住宿價明載2025–26，不能當2027–28；最新住宿期限、學費／生活費、簽證仍未核對完整。
- 芝浦：2027變更說明，SDW與REP分开、教授同意及語言佐證差異、研究facility fee、每週600分鐘。這份附件不是完整申請包；TAO財力金額／時程、最新版program guide、宿舍與全套文件待查。
- 釜慶：2027只見檔名，內文無AY；UG限定、語言certificate非強制與中央home必繳分開。文件、臺灣enrollment公證、課程韓語為主、宿舍與保險衝突保留；新表／確切年度／公證及NHI條件待確認。NHIS英文頁仍含2019/2021規定，不以它單獨消除衝突。
- Aarhus：2026/8–9官網改版，faculty語言分項／新版TOEFL、home正式證明不接受receipt但host部分可補交，完整英文PDF成績／graduate附件、年例期限。中央舊表只列School of Engineering，不能套BSS或全faculty豁免；工程校區指引、2027課表與住宿價目／截止待查。
- 南洋理工：local成功取得15頁AY2026–27表，browser對附件403的回執與local成功分開保存。原PDF年份／學期及護照起算描述衝突，保留原文；CCDS限制、research不適用宿舍、文件簽章、費用、保險與STP都標舊年度。2027–28及兩項中央歷史方案適用性未完成，不用2026截止提醒。
- Murray：未標年官方exchange／visiting頁與checklist，文件、條件語言、財力、宿舍deposit、J-1包資料。中央115列自費，不能自動套exchange減免；2027費用與J-1/F-1適用、最新版forms仍待查。
- ALKU：已視覺核對六項checklist與簽署次序、未標年Word factsheet（非HTML）、年例截止、協助找房與保險／visa說明。Google Form local401未讀欄位，FAQ local timeout；校曆仍2025–26。Erasmus／KA171能否用於中央116、2027房价、保額／費用與協議需另核對。
- SDU：申請页重讀200，七項文件清單与到校正本；現連DOC、DOCX、XLSX全讀，但申請表2012、確認信2008–09、到校表2007–08。未標年頁12/30與2012表11/30差異保存；Learning Agreement多方簽章與學生證欄位分列。表格入口local500，官網索引工具可讀，不稱login限定。
- ENSEA：2026–27表、一般交換與FAME2027分開；現連application PDF第2–4頁簽章、相片、附件與KA171補助額外要求已讀。PDF截止6/30、11/1與factsheet非EU6/1、10/31不同。協議費用法文原表与英文誤譯保留；政府住房補助三種例外另查，中央協議、最新Study Plan、費用年與住宿期限仍待核對。
- IPSA：2026–27表及官網，巴黎／Toulouse、Aero3／4／5、一般exchange／EUR4500自費Study Abroad分開；B2是recommended，host可收母校函不替代中央正式語檢。Toulouse本科PDF與官網差異、官網仍2024–25 handbook／課單、2027費用住宿与完整最新包均待核對。
- Turku：2026–27表及官網／現連Language Assessment與LA，TOEIC不能當host證明、B2／兩年／豁免分列；PDF提名年與申請順序矛盾、TOEFL ITP／iBT名稱及1/26分界差異保留。不同faculty限制、Pori／Turku、half UTU／研究課業與Spring2027 orientation分開；現連DOC已轉檔兩頁逐頁視覺確認A1–C2六級及五技能、雙方簽名日期和教師章戳。另逐頁讀Migri五頁與TYS四頁，保留exchange joint account矛盾、D visa例外、保險120000／40000與300自負額、offer四天及鑰匙領取要求。政府／住房供應者不冒稱外校authority；個人資格、116價目／期限與2027政策仍待確認。
- Western Sydney：browser可讀、local406分列；頁內仍2024校曆／2025 draft。已核对三項申請附件，原文摘錄僅一段不宣稱整頁本地存檔成功。2027–28校曆、最新完整規則／費用／住宿仍可繼續查。

- 東華：2026 Fall C.E.P factsheet／課單PDF／Excel及簽證保險頁已讀，明載non-Chinese international；中央歷史列臺灣籍限定，不能把IELTS6／TOEFL80或HSK4／5當臺灣生門檻。16門課、至少8學分、先修、延安西路校區房型與外國人X1／X2分列；臺灣track申請包、116時程与住宿未取得，不建立必繳host清單。
- 上海交通：2026–27international資料及港澳臺入口／2026到校新聞分讀；non-Chinese國際交換GPA／語言、七附件、X簽證及PingAn不能套臺灣生。部門／Global College／SPEIT課程校曆與2020房價另標；臺灣接收包／116門檻與名額尚未取得，不建立必繳host清單。
- 西交利物浦：現行incoming與明列臺灣學生住宿頁已讀。SIP／太倉校區、10–25學分與40學分備選、課程限制及住宿最低租期分開；推薦邀請後表格未公開取得，home歷史列臺灣且不採認學分仍需116系所核對。不拿年租價當一學期，宿舍押金、水電與退約逐項保留。
- TUAF：現連2026–27新版40頁手冊（公開Google Drive確認下載）、2026 factsheet、2024–25表與2022範例均保留；申請／提名／acceptance及迎新晚於課始矛盾不修造。IELTS5.5是program learning outcome，非交換門檻；八項host文件全部待當期確認。現連DOCX是已填學生範例，只保存原件SHA與必要欄位摘錄，未複製個資，沒有宣稱空白當期表已取得。已視覺核对factsheet第2頁：Administration $70到校付、Visa $95／6月及$135／12月，文字抽取錯序仍保留。新版保險60／年不是每月、越南health insurance／home旅保差異、到校24 working hours和延簽提前30天接入生活及流程；116臺灣簽證政府文件與接收包仍需查。

## 尚未完成的來源工作

目前196項尚無初步人工欄位整理；已整理18項也全部partial，**214項沒有任何一項完成116當期全欄核准**。不能以中央提名步驟當host文件清單完成。194項有附件／網頁不表示194項全部15欄已核對。20項仍無可用相關host原文，具體項目见下列清單及CSV「已讀host來源數=0」；多數仍可繼續做官方host來源搜尋／身份與track核對，**尚非證實登入限定或官方未公告**。已取得的大陸international資料若排除Chinese nationals，另列臺灣track缺口，不能硬配。

本地HTTP讀取限制：Western Sydney兩頁406（browser其中一頁讀取成功）、SDU表格入口500（申請頁重讀200）、中央student portal503（browser先前502）、ALKU Form401／FAQ timeout、TUAF Form401。不把這些錯誤改寫成登入限定。南洋理工brochure頁200但只回導航文字，保留而不稱完整brochure已讀。

## 接入及保護界線

registry／loader／API／dashboard／student_summary_zh／cards／詳情／workflow／生活頁已接入；新增公開`/partner-source-audit`顯示每欄與原文頁。六項個人準備工具沒有CGU正式表格下載、章戳或份數宣稱。中央語檢日期有前後端實際日期限制；後端拒絕已過兩年英文及不適用測驗，但不拿第三外語硬套英檢效期。

流程全部pending review、published_at為null，不可啟用精確提醒或提交申請；115／116不混用。沒有merge、部署、正式DB、credentials或security設定修改，也没有對外聯絡學校。新學校論壇SQL／Email domain辨識未改動；若要正式接入該部分，需另準備可審閱migration，不以此資料PR當授權。

## 重建與驗證

```bash
PYTHONPATH=src python scripts/build_ncu_catalog.py --output-dir /tmp/ncu-rebuild
PYTHONPATH=src python -m pytest -q tests/test_ncu_integration.py
PYTHONPATH=src python scripts/export_openapi.py --check
```

重建只讀追蹤snapshot，不需網路或私有資料。`import-provenance.json`保存输入SHA-256，builder不以regex產生外校數字資格、名額或精確截止。`collect_ncu_sources.py --inventory`、`collect_ncu_drive.py --retry-errors`與`collect_ncu_host_web.py`只用公開URL；它們是2026/10/8快照工具，未假裝持續更新。

Chromium中央／臺大10項通過，實際檢查390與1440寬的摘要、原文、home／host文件、生活頁、成績尺度／年級／正式語檢表單。六份截圖在`/tmp/ncu-audit/browser/`，本機已檢視中央手機生活頁。另追蹤三份公開頁面截圖：[來源](ncu-browser-evidence/source-390.png)、[流程](ncu-browser-evidence/workflow-390.png)、[生活](ncu-browser-evidence/life-390.png)。最新中央3項（含母校PDF原文展開）亦通過。API OpenAPI版本`2026-10-08.4`與快照一致。

北大`test_runtime_includes_tracked_ntpu_public_baseline_with_isolated_private_data`的destination_profile_count=0失敗已在未修改基底f6ad1b8復現（1 failed, 3 passed），與此輪相同；没有隱藏或修改該失敗。第一輪12個NCU／CGU／NTPU／NTU／文件／流程／完整度／預算測試module：171 passed、4 skipped（51.97s）；本輪含新增三項來源／範例摘錄防漏測試為174 passed、4 skipped（110.55s）。新增來源測試曾因禁止原始PDF含NUL而失敗，已改為只禁止Word二進位誤解析並保留原始缺字、加上品質缺口。NCU／預算／完整度四module另62 passed；最後排除把法國政府標成外校authority後，NCU30項再通過且OpenAPI／JS檢查通過。不宣稱全套CI通過。

## 與並行分支合併點

淡江draft [PR #2](https://github.com/blizzard-new/abroad/pull/2)與中正draft [PR #3](https://github.com/blizzard-new/abroad/pull/3)存在。共用`university_registry.py`、`storage.py`、`api.py`、`models.py`、`application_documents.py`、`application_rules.py`、`advisor.py`、`cost_estimates.py`、`school_completeness.py`、`static/app.js`、`static/index.html`與`docs/api/openapi.json`可能同時變動。合併時保留各校分支及校別判斷，重建OpenAPI與校數測試；不要以整檔覆蓋。NCU專屬資料與腳本可獨立核對。

`uv lock --check`在未修改main基底亦失敗：lock仍列pyproject已無的pytesseract。此分支只用離線重建移除三處殘留項，未升級其他依賴；重新check通過。

來源字型缺口：上海財經26–27手冊第1、8頁及上海大學申請指南第2頁含NUL，未補造缺字；36份共100個無抽取文字頁包括封面／圖片，尚未全部視覺核對。下載成功不代表全文內容核對完成。

## 尚無可用相關host原文的20項

- ncu-173：大連理工大學 Dalian University of Technology（中國）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-174：天津大學 Tianjin University（中國）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-177：吉林大學 Jilin University（中國）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-178：西安交通大學 Xian Jiaotong University（中國）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-181：東北林業大學 NORTHEAST FORESTRY UNIVERSITY（中國）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-182：武漢大學 Wuhan University（中國）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-183：長安大學 Changan University（中國）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-186：南京信息工程大學 Nanjing University of Information Science and Technology（中國）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-191：華南理工大學 South China University of Technology（中國）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-194：鄭州大學 Zhengzhou University（中國）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-195：貴州大學 Guizhou University（中國）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-196：濟南大學 University of Jinan（中國）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-199：太歷國立大學 Tarlac State University（菲律賓）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-206：沃瑪德瓦大學 Universitas Warmadewa（印尼）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-208：日惹國立大學 Universitas Negeri Yogyakarta（印尼）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-209：迪波內戈羅大學 Universitas Diponegoro（印尼）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-211：蘇門答臘理工學院 Institut Teknologi Sumatera (ITERA)（印尼）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-214：胡志明市科技師範大學 Ho Chi Min City University of Technology and Education（越南）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-215：胡志明市國際大學 International University, Viet Nam National University（越南）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。
- ncu-216：胡志明市自然科學大學 VNUHCM-University of Science, Ho Chi Minh City (HCMUS)（越南）。已查來源與下一步見field-audit；未完成官方host搜尋／身份核對，不聲稱官方未公告。

## 表格視覺及原件摘錄證據

[Turku評量第1頁](ncu-source-evidence/language-assessment.png)、[第2頁](ncu-source-evidence/language-assessment-p2.png)為DOC轉檔頁，原件無固定PDF頁碼。[TUAF factsheet原PDF第2頁](ncu-source-evidence/ncu-tuaf-2026-factsheet-p2.png)顯示費用分類。視覺紀錄保存原件與截圖SHA；原件變更即不套舊視覺確認。已填範例摘錄同樣依SHA確認，原件變更／摘錄遺失即保留空頁與具體錯誤，不輸出學生填答。

本輪Chromium新增Turku／TUAF兩項手機檢查通過，驗證實際host文件、保險、住宿期限、24 working hours及範例摘錄提示。既有390寬測試首次因啟動遮罩攔截選單點擊逾時失敗，未到中央內容；獨立重跑同項通過（40.78s），原先失敗仍記錄。首次共4 passed、1 failed，重跑1 passed；沒有修改啟動遮罩或測試等待條件掩蓋問題。
