# 中央116-1來源查核與平台接入（進行中）

基底為合併PR #1後的`f6ad1b8`，已確認包含臺大六項修正`daad399`。獨立worktree `/workspace/abroad-ncu`、分支`data/ncu-exchange-20261008`；已推送checkpoint `dc126d2`、`95c883a`、`2865413`、`6f2f9d1`、`dd06632`、`0d91d46`、`5b0df5a`、`7b381ae`、`9d44a4e`、`7f0e1cc`、`a9c6fd0`、`a199426`、`719d523`、`fc876ca`、`0b10d31`、`1bddf5a`、`ded2ed1`、`eb0b610`（只補ded2ed1原始證據）、`9671a106`、`eeade3d`（只補9671a106證據），draft [PR #4](https://github.com/blizzard-new/abroad/pull/4)。原工作目錄、中正及淡江分支未改動。本文件不宣稱中央全部外校資料完備。

## 適用年度與實際覆蓋

2026/10/8中央交換計畫首頁已提供[116-1甄選簡章](https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangenotice.pdf)，名額表預定2026/10/12公布（第2頁）。當日首頁仍連[115年度表](https://oia.ncu.edu.tw/static/file/26/1026/img/272/115exchangeschoolist-20251127.pdf)，所以**所有116名額均為null、待確認**。未知不等於0名額或未開放。

115表216列完整保留；靜岡、南洋理工重複列保留成兩個program options，其餘含北海道院／校級及自費方案，不相加名額。目錄214項不是214所當期已開放學校。

| 指標 | 2026/10/8實際結果 |
| --- | ---: |
| 115 PDF原始列 | 216 |
| 平台目錄／pending流程／生活資料項 | 各214 |
| 公開Drive遞迴資料夾 | 173 |
| 公開附件下載成功 | 459，下載錯誤0 |
| 至少一頁有可讀文字／全頁有文字 | 454／423；文字抽取不等於人工已讀 |
| 完全無文字的附件 | 5份，33頁（URCA、Bolton、UOS、重慶、HUST） |
| 有明確SHA與逐頁紀錄的全文已讀／視覺文件 | Drive附件19／4；UOS舊影像版11頁、SUFE與SHU各8頁、廣西16頁逐頁視覺讀完；OCR僅UOS舊版 |
| 部分或全部無文字頁／字型問題 | 36份含100頁、2份字型缺字 |
| 另查公開host／home網頁 | 740筆公開頁／文件讀取紀錄（含browser失敗／選定摘錄）；97筆目前讀取錯誤分列 |
| 有外校來源的目錄項 | 211（210項有文字）；214項有任意參考來源，另3項只有其他母校官方轉載、不可冒充host官網 |
| 人工整理的host紀錄 | 62（全部partial）；152項尚未逐欄整理 |
| 全部17欄完成116當期核准 | **0** |

附件取得／文字抽取不是逐欄當期查核完成。其他資料仍可繼續查；未查完的欄位不稱「官方未公告」。

[逐校逐欄CSV](../src/exchange_info/official_data/ncu/field-coverage.csv)與[完整證據／缺口JSON](../src/exchange_info/official_data/ncu/field-audit.json)包含17欄：城市／校區、抵達／日常交通、名額、學制／校區／track、語言、home文件、host文件、home截止、host截止、交換期間、課程、學費、生活費、住宿、保險、簽證、到校。JSON保留來源URL、PDF頁碼、原文、適用年份及查核日期。CSV與JSON不是全綠即完成的數字展示。

## 已確認母校規則

線上2026/11/16 09:00–12/4 12:00；學生紙本12/11 17:00交系所；系所12/18 17:00送國際處，全部臺灣時間。校內錄取公告2027/1/11 09:00。

大學部平均60、研究生70；在職專班可申請但無研修獎學金，目前大五／大六不可申請。未知學制、成績或大學部年級不回傳通過；不將GPA換算百分制。仍須系所與導師／指導教授同意、一學年成績及全程學籍，境外生／國籍限制分列。

七項home必繳文件及簽章分列於home step；外校文件放入另一host step。正式語檢影本必繳、不限級數，英檢兩年有效，不能截圖或補繳。外校語檢是另一規則；第4頁補件說明與第7頁提名前具備要求的差異保留，不取消較早的準備義務。第4頁TOEFL ITP與第6頁PBT差異亦保留。

首頁仍下載forms-2022.pdf：個資同意第1頁、家長同意第2頁、109年度範例第3頁。只使用現行表格連結，不將範例舊日期當116截止。行前兩週程序、回國一週程序、WORD心得800–1500字及至少四照片接入流程。課程兩門且一門專業課與學則兩門或六學分分別列出，採認由系所審定。

## 人工外校整理與具體缺口

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

- 太歷國立大學：現行OIAL下載入口明載2024/9/24生效，三份SF06／08／11 DOCX全讀；PHS六正本、指印、成績與出生認證、相片及保險均保留一般外國生適用限制。exchange入口正文不足，不把一般入學表套成中央host必繳。菲律賓政府SSP／9F、CGAF、條件附件、2024線上公告與ECC已讀；費表明載2014、Children表URL2025但Effective2024，年例／舊版與當期分開。
- 胡志明市科師大：官方現稱Technology and Engineering，保留115原列Education名稱並核對身份。inbound／outbound雙欄程序已讀，CV／英文面試、faculty審查、入境住宿支援及到校生活安排均列參考；國際處索引多為outgoing，不能移植其截止。沒有完整incoming包，host文件清單仍空。

- 首爾市立：舊Drive影像PDF11頁與官網新版11頁均逐頁視覺閱讀；舊版2023／2022費用與新版2025房價另列，原始空頁／不可見舊字層不覆寫。官方AY2027秋季期限、校曆、六頁FAQ、課程限制、住宿MMR／TB、現連DOCX與16頁dorm guide、機場6002及臺北韓國代表部文件已讀。GPA minimum與FAQ preferred例外衝突、TOPIK4課程範圍、Spring2028／全套WISE申請包未取得，不能稱完整116核准。MMR與健康表是錄取後住宿條件文件，新增獨立行前步驟，不放進初次host申請必繳清單。
- 華中科技：2026Fall臺灣track DOCX及HKBU官方轉載的HUST2027–28港澳臺九頁簡章已讀；2027/5/5與11/3來源、普通話「最好」建議、四人住宿500–700／學期、全期自購保險與母校統一送件分列。2026計算機／集成電路暫不開放與2027版本未述不同，不推定重開；新文件的2027–28日期仍聲明參照舊校曆。健康檢查明載錄取後才交，已移至獨立行前文件步驟。轉載來源不冒充外校官網authority，中央116協議、表格及最新校曆仍待核對。
- 胡志明市國際：官方2018 F-IEX1兩頁印刷111／112由browser核對本科／研究所欄、英語證明選項、最少12最多24學分、提名／英文成績／英文證明／護照附件及申請人簽名日期。local下載回cookie challenge或403，原PDF未取得，獨立browser摘錄明載selected excerpt而非完整當期包。五項host歷史文件已接流程，全部2018參考待確認；新版門檻、期限、住宿費及2025 brochure仍未核實，不稱官方未公告。
- 上海財經：中央Drive八頁逐頁視覺閱讀，持港澳臺證件／中國護照track與non-Chinese international分開；四項host材料及成績管理部門公章、提名後另發申請模板、無host總學分下限、通常27號樓／地鐵18號線、生活1000–1500／月與保險「建議」分列。封面2026–27、封底2025–26衝突保留；官網現連高清PDFSHA不同，不能沿用Drive視覺紀錄，已另外視覺核對高清原第1、8頁，亦見相同封底衝突；其餘六頁不宣稱已沿用查核。2026截止／Spring2027不能當116秋春期限，住宿價目與最新模板仍待查。
- 上海大學：港澳臺八頁全視覺閱讀，原第5–6頁是一般英文介紹、第8頁2020地鐵圖、第3–4頁2023–24校曆；空文字頁保留、另附選定原文。三學期正文與秋冬春夏校曆差異、部分線下選課／無線上完整大綱、3–4人房10／天、水電實際與餐費1000／月接生活頁；一卡通四欄與20元是到校文件，不能充作完整host清單。2019港澳臺PDF及入口local proxy400、國際圖片指南不等於臺灣track，最新接收包／期限／保險簽證仍待查。

- 日惹UNY：現行國際處首頁、Programs、Study／Current兩個正文不足入口及Visitor404，另逐頁讀PMB2021一般degree頁。中央網路學習科技dual-degree不是semester exchange，degree年齡、USD4000財力、使館推薦、2021學費／期限全部不建立為交換必繳或當期費用；14個host欄保留實際已查來源與具體缺口。住宿／簽證標籤沒有正文，未知不等於無要求或官方未公告。

- 迪波內哥羅UNDIP：官網2026 guideline標籤內的2027三頁表／Spring2027海報與未標年38頁booklet已讀，四個空白／相片頁另視覺確認；第2頁另核對Spring提名2026/11/10早於中央116，Fall2027五月／六月確切日官方此表待公布，Spring2028新版尚未找到。UG敘述與Master／Doctor課單、生活補助多零、Fall2026提名Excel、USD1500外校財力與另一政府E30B類別分開。十項host文件分Online／Visa兩類，因表第3頁稱兩類都上傳portal，不一律移Visa至錄取後。兩Word空白表與提名Excel非空行全讀；直接2025模板URL403另保存。秋139頁／春146頁課冊仍2026，只第1–4頁人工讀，其餘281頁未宣稱逐課已查；政府E30F正文Data Belum Tersedia、Mamikos外部JS房源不是宿舍保證，不能抵扣未核准補助。

- 大連理工：雲科官方Spring2025臺灣兩頁／Word空白表全讀，七件彩掃、母校及本人簽名、四人宿舍400–600／學期、全期自購保險與指定日免費接機；官網2022國際UG／PG、HSK／英語、十件文件、年例期限、X簽證及月租另讀，不套臺灣。2022交通含三校區，FAQ甚至引用北京居留交通，範圍及錯址保留，116新包未取得。
- 天津：新增銘傳公開Spring2027臺灣兩頁及申請DOC，舊雲科2025臺灣／HKU2027港澳分開。初次七件與到校後保單分兩階段；2026/11/15與「秋季」標題／春季日期矛盾保留。DOC轉為DOCX逐欄讀並綁定兩SHA、本人簽名日期可見；四至六人600／學期及接機旅費自付是2027春臺灣參考，不是116價格／宿位保證。
- 西安交通：雲科2025港澳臺須知、申請／推薦Word及單工作表Excel全讀；GPA>2.8/4.3保持嚴格大於、9學分或4課原文不改判。五學生件合一PDF、母校另Excel、申請人與派出承辦手寫簽名；統一住宿無價格，未知不填0。官方入口proxy403不當登入，116新包未取得。
- Warmadewa：官方國際教育概述及校曆browser選定摘錄，local403另保存，沒有原HTML SHA；最新索引2025–26、明細附件未取得。商業WIP方案不是中央雙邊交換，host文件仍空，印尼政府E30F／E30B与交換範圍分開。
- ITERA：官方宿舍／設施／合作正文已讀相关段落；2020／2021–22國內新生200.000／2000.000／150.000每月價格矛盾與10月預付不能套116。DIM／BPJS及照片清單不建立成交換必繳，2019BRT／內部校車不能當2027班次；國際入口proxy403不當登入。OAIL實為天文台，未冒充國際處。
- HCMUS：清華公開未標年兩頁交換空白表全讀，母校承辦與本人均需手寫簽名日期；只有一份待確認表，不虛構完整附件／緊急聯絡件。現行官方browser組織頁Campus1／2行政區不同於舊表；兩校區地址不是交換教學／住宿保證，outgoing期限與費用未移植。
- 東北林業：官網未標年交換頁与舊life指南全讀；後續local重讀200的成功與首次proxy403分開保存。外國護照／JW／X簽證、七件國際生申請與500／1000月租、400／800保險不自動套臺灣track。2021表格下載兩筆雖200卻非原件，host臺灣結構清單保持空，116包待查。
- 武漢：澳科大官方轉載接收港澳一頁PDF全讀，九類含選填、兩推薦信／心理健康、online加紙本、境內門診住院意外保險及延畢成績延後均明列參考。港澳標題与registerHMTStudent路徑不證明臺灣適用，host清單不硬填；當期臺灣新包、住房課程費用及政府程序仍待查。
- 長安：雲科2023秋四份空白附件全讀，六件初次合一PDF、母校公章／負責人簽名、母校一份13欄Excel、行前接機表與到校紙本分三阶段。Excel兩工作表（其一空白）逐欄讀，原XLS／轉檔SHA保留；接機2023/8/28卻含2020/8/20回傳矛盾，未改造日期，116新包未取得。

- 南京信息工程：新增銘傳公開2027春港澳臺八頁全影像簡章，逐頁視覺讀取、原始空文字頁保留，選定1／6／7／8頁原文另列。七項學生初次文件與母校另匯總表共八項，兩份空白DOCX逐欄讀；在學證明需三月內開立，學校購買醫療保險不列初次學生保單。2027/2/22–7/9與2026/11/10、四人750／學期、膳食1500／月只是此春track，不能當116核准。舊中英文一般國際生年房價2500–3000／2000–2500與博士限制另列；五筆local403留audit，成功browser摘錄優先進索引。報到交通圖未讀，當期房價／全生活費／保額與住房期限仍缺。
- 鄭州：靜宜官方轉載51頁PDF只讀臺灣簡章1–6及校區11，其餘44頁未全部讀；第6頁2026/7批文與1100／人年另視覺核對。有效協議／臺灣籍UG或PG、50專業及按通知報到分列；6/30／12/31是Offer日，不作申請截止。申請段未列完整附件或表格，host清單仍空。
- 貴州：舊OIR國際生全所得正文及2011行前／交通索引、2025國際學院概述分讀；國際自費／CSC與臺灣交換不能混。舊X／F與旅遊簽轉學習簽文字整段從問答索引隔離，原文保留稽核，不當現行政府指引。當期臺灣包、費用／宿舍／保險與最新表仍需續查。
- 濟南：山東UJN五頁嶺南香港交換表全讀，不能套廣州暨南JNU；header2024、2025秋／2026春與2024/10／2025/4截止矛盾保留。香港版4人400–800／學期、不住國際宿舍、到後意外醫療保險；2025國際生X1／X2報到、床品自備、2024交通另查而不套臺灣。臺灣116接收清單仍空。

- 同濟：銘傳2027春臺灣三頁全所得正文已讀，與雲科2026春兩頁分列；新版七件加入通行證、移除舊學習計畫，母校系統提名後才收到申請mail。2027研究生經管沒有舊版英授工商，建築／規劃／景觀上限不是中央配額；不跨校區選課、住宿統配但價格未知。新空白申請／住宿表未取得、未登入portal，116待查。
- 南京：2027春臺灣28頁簡章、日程、空白申請／體檢及三張Excel工作表全所得正文已讀；7／9／10／18頁及日程另視覺核對。首批七項與第二批三項分開，第二批11/20早於邀請12/10，不放錄取後行前；推薦Excel檔名2027春、表頭2026秋，臺灣版仍港澳證件名稱，材料10/20／11/20、心得1000–1500／1500以上、WiFi10／20元矛盾均保留。2027春保證宿位無須申請／2/22最早入住不延伸116；簡章和空白表院系範圍也不同，未硬判。銘傳配額不當中央名額。
- 復旦：政大傳播院2026秋五頁與六附件已取得；簡章、空白表、两張提名Excel、短指南全所得正文已讀。五電子件一zip、两纸本件及學習計畫單獨附頁、保單初次交、母校另提名明列；新聞院紙本收件管道不套中央校級協議。6／8人套間是2人一房、800／學期、水電網路另計；院系限制只保留參考不建自動通過。所附平台兩頁仍2022，逐頁視覺核對、從問答索引隔離；318頁2025–26舊課冊只讀1–2，其餘316頁未讀，不當116。
- 吉林：高醫舊公告轉載一頁清單未標年，九件紙本與原件／影印／推薦人欄位已讀；最新金門2026頁及附件實讀404，搜尋標題不作取得原件。重試附件URL與既有URL相同，以previous_attempts保存、未新增重複來源。116完整新表、電子／紙本階段、語言／課程／住房／預算／到校仍待續查，不稱未公告或登入限定。

## 尚未完成的來源工作

目前155項尚無初步人工欄位整理；已整理59項也全部partial，**214項沒有任何一項完成116當期全欄核准**。不能以中央提名步驟當host文件清單完成。211項有外校附件／網頁不表示211項全部17欄已核對。3項仍無外校來源映射；另1項只有影像、尚無可讀文字，具體項目见下列清單及CSV「其中外校來源數=0」；多數仍可繼續做官方host來源搜尋／身份與track核對，**尚非證實登入限定或官方未公告**。已取得的大陸international資料若排除Chinese nationals，另列臺灣track缺口，不能硬配。

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

Chromium中央／臺大10項通過，實際檢查390與1440寬的摘要、原文、home／host文件、生活頁、成績尺度／年級／正式語檢表單。六份截圖在`/tmp/ncu-audit/browser/`，本機已檢視中央手機生活頁。另追蹤三份公開頁面截圖：[來源](ncu-browser-evidence/source-390.png)、[流程](ncu-browser-evidence/workflow-390.png)、[生活](ncu-browser-evidence/life-390.png)。最新中央3項（含母校PDF原文展開）亦通過。API OpenAPI版本`2026-10-08.5`與快照一致（最新條件引擎修正）。

北大`test_runtime_includes_tracked_ntpu_public_baseline_with_isolated_private_data`的destination_profile_count=0失敗已在未修改基底f6ad1b8復現（1 failed, 3 passed），與此輪相同；没有隱藏或修改該失敗。第一輪12個NCU／CGU／NTPU／NTU／文件／流程／完整度／預算測試module：171 passed、4 skipped（51.97s）；本輪含新增三項來源／範例摘錄防漏測試為174 passed、4 skipped（110.55s）。新增來源測試曾因禁止原始PDF含NUL而失敗，已改為只禁止Word二進位誤解析並保留原始缺字、加上品質缺口。NCU／預算／完整度四module另62 passed；最後排除把法國政府標成外校authority後，NCU30項再通過且OpenAPI／JS檢查通過。不宣稱全套CI通過。

## 與並行分支合併點

淡江draft [PR #2](https://github.com/blizzard-new/abroad/pull/2)與中正draft [PR #3](https://github.com/blizzard-new/abroad/pull/3)存在。共用`university_registry.py`、`storage.py`、`api.py`、`models.py`、`application_documents.py`、`application_rules.py`、`advisor.py`、`cost_estimates.py`、`school_completeness.py`、`static/app.js`、`static/index.html`與`docs/api/openapi.json`可能同時變動。合併時保留各校分支及校別判斷，重建OpenAPI與校數測試；不要以整檔覆蓋。NCU專屬資料與腳本可獨立核對。

`uv lock --check`在未修改main基底亦失敗：lock仍列pyproject已無的pytesseract。此分支只用離線重建移除三處殘留項，未升級其他依賴；重新check通過。

來源字型缺口：上海財經26–27手冊第1、8頁及上海大學申請指南第2頁含NUL，原始缺字仍保留；三頁已視覺核對，摘錄與原始抽取分開。36份共100個無抽取文字頁包括封面／圖片，尚未全部視覺核對。下載成功不代表全文內容核對完成。

## 尚無外校官網來源映射的3項

其中西安交通、武漢及長安已有其他母校官方轉載，來源authority保留home_university，不能用轉載填補host官網計量。其餘仍需公開host／官方轉載搜尋，不稱官方未公告或登入限定。

- ncu-178：西安交通大學 Xian Jiaotong University。具體已查來源、HTTP失敗、年度／track與未解欄位見field-audit。
- ncu-182：武漢大學 Wuhan University。具體已查來源、HTTP失敗、年度／track與未解欄位見field-audit。
- ncu-183：長安大學 Changan University。具體已查來源、HTTP失敗、年度／track與未解欄位見field-audit。
## 表格視覺及原件摘錄證據

[Turku評量第1頁](ncu-source-evidence/language-assessment.png)、[第2頁](ncu-source-evidence/language-assessment-p2.png)為DOC轉檔頁，原件無固定PDF頁碼。[TUAF factsheet原PDF第2頁](ncu-source-evidence/ncu-tuaf-2026-factsheet-p2.png)顯示費用分類。視覺紀錄保存原件與截圖SHA；原件變更即不套舊視覺確認。已填範例摘錄同樣依SHA確認，原件變更／摘錄遺失即保留空頁與具體錯誤，不輸出學生填答。

本輪Chromium新增Turku／TUAF兩項手機檢查通過，驗證實際host文件、保險、住宿期限、24 working hours及範例摘錄提示。既有390寬測試首次因啟動遮罩攔截選單點擊逾時失敗，未到中央內容；獨立重跑同項通過（40.78s），原先失敗仍記錄。首次共4 passed、1 failed，重跑1 passed；沒有修改啟動遮罩或測試等待條件掩蓋問題。

## 2865413複核後修正

曾以單欄unresolved為空將釜慶courses、Strasbourg arrival標available，忽略整筆年份／track限制。現在所有host參考欄均needs_confirmation，另記reference_status與current_applicability_status；兩個home欄才計本期已核實，NCU分數只算2/17，不給待確認加權。前端改顯示「項本期已核實」，其他學校用「項已提供資料」，不再寫「資料完整」。城市與交通納入17欄，沒有官方核實內容仍保留未知與具體缺口。

下載、any_text、all_pages_have_text、all_pages_read、visual_reviewed和OCR狀態分開。all_pages_read／visual只計原件SHA相符的明確逐頁紀錄，不能以pages陣列存在或可抽取文字推定人工已讀。五份全影像與部分影像均有回歸測試。來源UI顯示文字／視覺頁數與缺口，不將11個空段落稱已讀原文。

補做Turku／TUAF生活指南展開及可見文字檢查，2 passed（66.50s）。曾因Turku全文長頁截圖30秒逾時失敗，內容断言已過；改在已可見的保險文字位置截取實際viewport，重跑通過，未修改內容或隱藏原失敗。

完整度、來源計量及城市／交通修正後，NCU與school_completeness兩個module為44 passed（43.99s）；390px Chromium實際內容檢查1 passed（102.55s），另驗證2/17本期已核實與城市／交通缺口。OpenAPI快照、JS syntax及git diff --check通過。這些新檢查不替代前述基底失敗紀錄或全部CI。

## 視覺證據與條件文件新增驗證

離線builder現在逐來源合併同SHA sidecar，包含TUAF factsheet第2頁；source-evidence與field-audit均顯示原件2頁、1頁已視覺核對。SHA不同即清除舊視覺紀錄與摘錄，無效頁碼不計視覺頁數。原始抽取不替換為人工轉錄。UOS舊影像版、UOS新版、上海兩校都有原件／轉圖SHA與逐頁閱讀紀錄；正文摘錄只標selected passages。

本輪NCU與school_completeness為47 passed（73.64s）；新增UOS／HUST／HCM年度、範圍、条件文件與SHA回歸通過。Chromium首爾市立390px實際頁面1 passed（69.18s），可見2027秋季期限、舊11頁視覺摘錄、獨立MMR／Health Form及6002生活內容，截圖在`/tmp/ncu-audit/browser/ncu-uos-*.png`。一度因錯用pytest --browser參數及缺Playwright對應Chromium未啟動，已依既有fixture及本機工具路徑安裝恢復；未把環境錯誤算內容通過。TUAF sidecar／Shanghai視覺版本新增兩項回歸通過（2 passed，12.22s）；包含新回歸的兩個module最後49 passed（191.37s），OpenAPI、JS及diff checks通過。TUAF手機來源摘要已確認1頁視覺查核。上海兩項首次在末尾未定義errors變數而失敗，原内容斷言已過；補上pageerror紀錄後SHU通過，SUFE一度在中央切換前被原有boot-splash攔截逾時，獨立重跑SUFE通過（1 passed，43.69s），SHU同輪1 passed。未強制點擊、移除遮罩或修改產品啟動流程。

本轮公開視覺證據：[UOS舊第3頁](ncu-source-evidence/uos-old-2023-p3.png)、[UOS新版第3頁](ncu-source-evidence/uos-current-p3.png)、[新版第4頁](ncu-source-evidence/uos-current-p4.png)、[新版第7頁](ncu-source-evidence/uos-current-p7.png)、[SUFE Drive封面](ncu-source-evidence/sufe-p1.png)、[Drive封底](ncu-source-evidence/sufe-p8.png)、[SUFE官網高清封面](ncu-source-evidence/sufe-primary-p1.png)、[高清封底](ncu-source-evidence/sufe-primary-p8.png)、[SHU第2頁](ncu-source-evidence/shu-p2.png)、[SHU第8頁](ncu-source-evidence/shu-p8.png)。學生頁截图已追蹤於docs/ncu-browser-evidence/ncu-uos-*、ncu-sufe-*與ncu-shu-*；只展示來源、流程及生活資訊，沒有學生個資。

最新跨校與共用接口回歸：school_content、NTPU support、NTU audit／integration、application_rules、document_catalog及documents_api七個module共97 passed（32.51s）。前述NTPU bundled destination基底已知失敗仍單獨列出；不宣稱全部CI通過。

首爾市立政府表格補查：臺北韓國代表部2025/8/8現連Visa Application Form原PDF5頁均讀，韓／英大寫、35×45mm近6月照、五年旅行史、USD費用／付款者及第5頁姓名／日期／親筆簽名分列；未滿17歲另有父母／監護簽名。政府來源不標為host authority，不放入UOS初次交換申請必繳清單；本表不是入境後居留登錄表，個人條件及2027行前更新仍須查。新增UNY／政府表及離線重建兩項回歸2 passed（11.72s）。

## UOS問答索引隔離與本輪續查

已確認UOS新版第3／6／7頁含不可見舊字層。以前ProcessedPage把raw與正確摘錄並列，造成索引污染風險；尚未證實發生使用者錯答。本輪以來源SHA與明確頁碼隔離：同SHA、同頁已核對摘錄替代問答索引中的該頁，原始破損文字仍完整留於source-evidence／audit。SHA變更或該頁未列視覺閱讀時先隔離，不能套舊修正版；不是用價格regex清洗。住宿764,000／382,000保留2025參考與2027–2028價格未核實，實際build_document_chunks／local index／search回歸通過。

HUST申請前3–6門課學習計畫已進結構化文件，附2027–28簡章第7頁。UOS住宿健康文件與HUST錄取後健康文件的正式啟用條件仍待實作；目前models沒有住宿選擇／錄取狀態判斷，不能宣稱已完成條件引擎。具體邏輯與相容性要求見[可審閱啟用前設計](ncu-conditional-documents-design.md)，三項缺口亦在實際學生field-audit。所有214流程仍未發布，沒有精確host提醒。

來源計量改分任意參考來源與外校来源；Warmadewa／ITERA只有印尼政府來源仍列host缺口。CSV不再把附件取得稱「已讀host」。文字／視覺頁数及原始空頁繼續分開。新增[UNDIP第2頁原圖](ncu-source-evidence/undip-factsheet-2027-p2.png)與[Spring2027海報](ncu-source-evidence/undip-poster-spring2027.jpg)。本輪UNY／韓國政府表／UNDIP版本及離線重建，含新增UOS索引檢索四項先通過（4 passed，17.97s）；NCU／完整度52項通過，通用RAG6項通過另1項失敗；該503預期／422實際差異已在未修改f6ad1b8復現（1 failed，10.33s）。跨校與文件七module97項通過（37.91s）；UI靜態4項、JS／OpenAPI檢查通過。手機實測UOS簽證原文、UNY適用範圍、UNDIP未定期限與十文件各1項通過，另臺大瀏覽與切回長庚2項通過（67.46s）。UNDIP實測發現摘要十項截斷，已增中央專用其餘說明展開；畫面選擇器亦已修正，未隱藏boot狀態或強制點擊。追蹤[UOS簽證原文](ncu-browser-evidence/ncu-uos-visa-form-390.png)、[UNY生活](ncu-browser-evidence/ncu-uny-life-390.png)、[UNDIP原文](ncu-browser-evidence/ncu-undip-source-390.png)、[UNDIP生活](ncu-browser-evidence/ncu-undip-life-390.png)。這批27校驗證後仍持續下一批天津／HCMUS／ITERA／Warmadewa來源查核，後續變更須再重建與複驗。

## 長庚範圍逐項驗收與36筆續查

新增[長庚對照驗收表](ncu-cgu-acceptance-20261008.md)，逐項對照實際models／loader／API／文件中心／流程與生活頁；含資格、語言、名額、內外截止、所有文件階段、課程採認、住房、費用、保險簽證、城市交通、到校與返國。表格明確分介面接通與內容未完成，0項目全17欄当期核实，178項可續查而非外部阻擋。

新增天津手机流程、轉檔原文1 passed（52.09s）；首次49.31s於中央切換前被既有boot-splash攔截，未到內容，原失敗保留。檢視截圖後發現原測試只檢查折疊內DOM文字，補上實際展開申請與抵達後步驟、可見文字斷言，再1 passed（46.64s）；[抵達後保險](ncu-browser-evidence/ncu-tju-arrival-390.png)及[轉檔原文](ncu-browser-evidence/ncu-tju-source-390.png)已檢視，無學生個資。沒有移除遮罩或強制點擊。

舊Word／Excel轉檔必須SHA相符，原件變更即不使用既有轉檔；原始解析失敗仍保存，不對OLE二進位做文字解碼。Excel逐工作表確認，不能以所有page=None就算全工作表已讀。HTTP200但回HTML而非PDF／Word分為回應已取得、原件未取得，不能計原件下載完成。

## 文件中心真實API缺口修正及40筆續查

新增隔離資料目录的中央文件catalog測試曾得到空清單：流程API可讀repo baseline，但catalog只讀隔離目录且context保留NCU alias。當時63 passed、1 failed（112.84s）；已修正中央catalog使用同校治理／baseline loader並正規化中央校名，沒有改其他母校catalog路徑、登入／安全或資料發布界線。天津初次七件、抵達後保險、home文件在實際API及UI均待確認，沒有正式下載。

修正後NCU／來源collector／完整度、CGU／NTPU／NTU／規則／文件API及前端契約11個module為207 passed、8 failed（155.02s）。八項皆前端契約既有失敗，已在未修改f6ad1b8逐項復現（8 failed，46 deselected，1.80s），涉及社群舊文案／fetch名、通知字串、舊app版本、資格元件及學校計畫文案；未隱藏或篡改結果，不能稱全套CI通過。

長安空工作表與天津文件中心真實手機測試1 passed（73.73s）。[長安空白工作表](ncu-browser-evidence/ncu-chd-workbook-390.png)與[天津抵達後catalog](ncu-browser-evidence/ncu-tju-catalog-390.png)已檢視：實際展開sheet2、原文空白說明與待確認保險，並非只檢查折疊DOM。新增鄭州[第6頁原图](ncu-source-evidence/zzu-taiwan-reference-p6.png)已視覺確認，原件及轉圖SHA附sidecar；整份51頁不計全文已讀。

最新main再fetch仍為f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59。中央40筆仍全部partial、174筆可做公開來源工作未整理；新增四校來源不使任何項目達到當期全欄核實。南京信息工程五筆local403與五筆browser選定摘錄分開保存，原HTML SHA未知／圖片未讀；來源計量211 host映射不是211全包完成。貴州舊國際生簽證正文只在問答索引隔離，來源原文及人工閱讀證據仍保留。

最新40筆資料的NCU／collector／完整度三module共71 passed（125.04s）。新增四校第一輪聚焦測試6 passed、2 failed（17.67s），兩項是測試對報到圖字樣與錯用processed_pages loader路徑的斷言問題，已依實際audit及pages.jsonl修正後完整三module通過。未改來源內容或降低年度／範圍封鎖。

南京信息工程與濟南兩項手機內容2 passed（81.67s），實際展開原文及官方生活段；[南京中英文房價及資格差異](ncu-browser-evidence/ncu-nuist-versions-390.png)、[濟南香港宿舍範圍](ncu-browser-evidence/ncu-ujn-hk-scope-390.png)已檢視。濟南宿舍頁只讀圖標題，已改不計整頁內容已讀；現連REGISTRATION NOTICE PDF亦補試，200非PDF原件的43rd讀取缺口保留，不當登入限制。這兩筆最後來源狀態修正另跑聚焦來源、重建及API複驗。JS、diff與OpenAPI快照檢查通過。

最後補查濟南PDF時，builder曾因失敗來源沒有原文頁而StopIteration，聚焦回歸2 failed、2 passed（13.59s）；已修正只將成功頁附為original_evidence，失敗URL仍在欄位source_urls及unretrieved_sources。新測試確認200非PDF不計下載、不附虛構原文，之後完整NCU／collector／完整度再71 passed（89.76s）。貴州隔離頁的索引提示另明確標過時簽證，不錯稱原件文字破損，原始內容不變。

OpenAPI版本2026-10-08.4再次與snapshot一致，JavaScript syntax及git diff --check通過。uv第一次因預設/home/agent cache唯讀未能開始；改用/tmp/ncu-uv-cache後uv lock --check通過（87 packages，16ms），沒有新增依賴或修改lock。沒有環境斷線。

最後索引提示／來源狀態／離線重建聚焦4 passed（16.04s），git diff --check通過。2026-10-08 10:06:05 UTC收到環境斷線通知後，在原/workspace/abroad-ncu執行date、pwd、git rev-parse及讀catalog的唯讀命令均exit0；git ls-remote亦exit0，main仍f6ad1b8、當時遠端中央checkpoint仍dd06632f871d6c38313aa32520837161446cf43d。40筆／241來源及CGU驗收表、UOS索引sidecar已保存；通知未形成實際環境阻塞，未換環境或建立重複工作。

## 44筆續查、第二批交件與來源截取修正

本輪新增21筆公開文件／頁面並補記銘傳官方入口鏈，總263筆、44筆讀取失敗；44人工partial、170項尚未整理、0項17欄116核實。原main與遠端checkpoint在2026-10-08 10:39:45 UTC唯讀ls-remote均exit0，main仍f6ad1b8、上一checkpoint 0d91d46f53f64943f6e6d9fd576af792175ef402，原worktree正常。

NCU builder新增第二批host申請步驟，仍使用既有「合作校申請」phase，與初次、錄取後行前、抵達後分開，文件catalog也可見三件第二批。南京來源第10頁11/20、日程邀請12/10，不能將這三件歸為錄取後。所有流程仍pending、所有文件needs_confirmation，不提供正式下載、精確提醒或提交。

初次聚焦5項為3 passed、2 failed（11.20s）：南京Excel年度矛盾只在未解欄，已補到摘要可見points；復旦隔離提示明確補「已隔離」。完整三module為75 passed、1 failed（148.40s），抓到Excel示例多行沒有整筆移除。修正後聚焦6 passed、1 failed（15.04s）又抓到另一南京快照未同步截取；已改離線builder也強制套同SHA public-excerpt，原件改變即清空正文／保留錯誤，不能重新帶入示例。两Excel均保留空白欄與工作表身份、移除完整示例行；collector與builder共用相同public_pages格式。這些失敗與修正均保留，不稱第一輪全通過。

新增三校Chromium實際原文／生活／流程3 passed（130.43s）；[同濟新版七件](ncu-browser-evidence/ncu-tongji-new-list-390.png)、[復旦初次保單](ncu-browser-evidence/ncu-fudan-initial-insurance-390.png)已檢視。南京原截圖停在步驟標題，另補可見保單與體檢及捲動截圖檢查；沒有強制點擊或移除boot遮罩。首次browser命令帶此環境不支援的--tracing，未開始測試；改成既有fixture後三項通過。一次中文-k未匹配escaped參數而17 deselected／exit5，沒有當成通過。

跨校及共享document/rules六module92 passed（38.51s）、school_content 5 passed（4.44s），合計97；未改他校資料或規則。OpenAPI2026-10-08.4、JavaScript syntax、diff及uv lock check通過，新增第二批內容未改API模型。完整最新複驗結果另補於下方。

最新完整NCU／collector／completeness三module **77 passed（104.05s）**；最後南京可見第二批保單／體檢与捲動截圖 **1 passed（48.05s）**，[南京第二批文件](ncu-browser-evidence/ncu-nju-second-batch-390.png)已檢視。此輪沒有新跨校失敗，既有main前端契約／NTPU／RAG差異仍照前述紀錄保留，不稱全套CI通過。

## 276來源、NUIST去重及四校2027春補查

2026-10-08 11:17 UTC在同一worktree唯讀ls-remote exit0：main仍f6ad1b8，上一已推checkpoint5b0df5a。新增銘傳官方2027春分校文件13份，現276筆公開來源、44筆錯誤，44筆partial／170筆未整理／0筆116全欄核實。銘傳母校配額不移植中央。

南京信息工程八頁影像PDF逐頁視覺核對，原始空文字頁保留，1／6／7／8頁選定原文與八份圖片SHA另存；兩DOCX空白表全文正文已讀。NUIST七項學生文件加一份母校匯總表、在學證明三月內、四人750／學期、學校購買保險、膳食1500／月逐項接流程／生活。舊一般國際生中英房價及博士限制仍屬不同track，不把2027春轉成116門檻。

NUIST成功browser摘錄先列、同URL失敗local後列曾使pages.jsonl五頁空白。builder現在先排除失敗及只有空頁標記的來源，URL去重優先非空正文且穩定選擇可用內容；失敗仍留source-evidence、field-audit及未取得清單。兩種來源順序與最後輸出去重均測試，實際中文／英文費用頁各建本機索引並取回費用原文；不接正式DB。初次聚焦2 passed／3 failed（8.26s）中，實際檢索測試把數字與CNY連成單一關鍵字，另兩項是保險用字及phase型別錯誤；修正測試後4 passed／1 failed（7.55s），膳食費用字亦已對齊原始資料。沒有為測試改共享RAG規則。

西安交通新增2027春兩頁、申請／推薦DOC與母校Excel；GPA嚴格大於2.8／4.3、五項合一PDF、10/30、表頭2027卻仍2025日期範例、最低學分或門數原文均保留。DOC轉DOCX兩SHA綁定、母校Excel整筆示例移除。華中科技臺灣2027春仍計算機／集成電路暫不開放、11/3、3–6課計畫；健康報告錄取後、保單兩交件選項分開。所附2024八頁影像宣傳冊於7b381ae checkpoint尚未視覺讀；其後9d44a4e已完成同SHA八頁視覺核對，2／3／7／8頁選定摘錄另存，仍是2024歷史參考而非116接收包。天津2027春臺灣PDF與DOC確認七初次件、到校後保單、11/15與秋季標題矛盾；原先2025／港澳參考仍另存。

完整NCU／collector／completeness為80 passed、1 failed（92.67s）：HUST來源排序已因2027春新文件改變，原斷言只准第一URL是舊PDF第7頁；改驗證新來源優先且舊第7頁仍保留。修正後六項聚焦全部通過（16.10s），包含來源正反排序、實際NUIST檢索、新包及UNDIP既有條件。OpenAPI2026-10-08.4、JS syntax及diff檢查通過；既有main失敗仍按前述紀錄保留。

Chromium天津階段／文件中心2 passed、新NUIST首次因來源標題選擇器錯誤1 failed（合計78.53s）；修正為原文件實際標題後NUIST1 passed（44.86s）。[八項NUIST文件](ncu-browser-evidence/ncu-nuist-2027-documents-390.png)、[第7頁視覺摘錄](ncu-browser-evidence/ncu-nuist-2027-source-390.png)、[學校購買保險](ncu-browser-evidence/ncu-nuist-2027-life-390.png)及[天津到校後保單](ncu-browser-evidence/ncu-tju-arrival-390.png)已逐圖檢視。不是只查校數或折疊DOM。

住宿／錄取條件引擎仍是內部待實作工作，不是學校未公告或登入限制；後續實作要保持未發布流程與版本查核狀態。此checkpoint不表示完成214校全包，也不授權部署。

## 條件引擎實作與年度封鎖（OpenAPI .5）

UOS兩份住宿健康文件與HUST一份錄取後健康報告已實作四態条件，按學校／年度／梯次／學期保存明確錄取、住宿選擇；文件catalog、個人計畫與統一任務使用同一policy。未知不一律必繳或免交，延後／不適用／未知文件不列當前「要準備」；依然顯示條件與來源，符合條件也只標參考範圍，116來源未核實、不可正式下載、沒有host精確提醒。現有工作區JSON可存新狀態，不需migration，未套用正式DB。完整規則見[已實作條件文件](ncu-conditional-documents-design.md)。

25項條件組合最先通過（21.36s）。完整NCU／collector／completeness／新條件四module106 passed（137.74s）。共享九module首次118 passed、2 failed（49.97s），都是固定851流程數；更新成851既有＋214中央後22 passed、1 failed（30.99s）揭露中央未發布流程仍被跨年度reference fallback借用。已加中央專用未發布阻擋，48項條件／工作區／任務全過（51.49s），最新九module120 passed（53.93s）；保持其他學校原有估計行為，沒有把中央pending稱已發布。851份CGU／NTPU／NTU workflow content hash逐份與未修改f6ad1b8比較完全相同。

真實手機測試曾1 failed（68.53s）發現同步整理函式遺漏新狀態；已補必要值、每期間快照及跨裝置不同鍵合併。另兩次1 failed（48.07s／53.71s）是在boot仍載入時以select_option直接操作後被初始化覆寫；測試改等待既有boot自然消失，沒有移除遮罩或force。新catalog請求另按相關條件快照防止舊回應覆蓋新選擇。文件目錄、四態、遠端JSON確實保存、重載及切學期後未知、HUST延後健康已1 passed（61.06s）。

補讀HUST所附2024八頁全影像宣傳冊：逐頁視覺核對，原空文字頁保持，2／3／7／8頁少量選定內容及八張圖片SHA可審阅；第3頁三校區、第7頁Junshan仍「upcoming」、第8頁含outgoing／international，不能補成116臺灣接收包。聚焦新條件／NUIST檢索／來源順序／原件年度／離線重建30 passed（25.60s）。sourcecoverage仍276／44錯誤、44partial／170未整理／0全116核實；閱讀一份宣傳冊不增加完成校數。

追加統一任務的真實操作時1 failed（88.66s）：其既有選單只列availability=open，使中央pending資料不可選，先前只驗證catalog不足以發現此點。已僅為中央加入本期名額待公告候選標籤；零名額／封鎖校不進候選，其他母校篩選規則保持。完整任務畫面複驗及最新SHA在後續紀錄。

已唯讀fetch遠端CCU4db9cd3／TKU61659fe並列[共享檔交集](ncu-shared-merge-points-20261008.json)：中正13項、淡江14項。API校別loader／models新欄位／文件中心／registry／前端條件選單與來源／OpenAPI及851＋214校數契約須逐段保留各校變更後重建，不以整檔覆蓋。沒有切換、提交、推送或合併它們的分支。

最新手機完整四態／保存與重載／學期隔離／統一任務內容 **1 passed（63.78s）**；臺大手機瀏覽 **1 passed（73.52s）**，長庚工作區單獨複驗 **1 passed（45.70s）**。先前同時啟動三個browser process曾使中央boot等待69.15s、長庚遮罩攔截53.06s各失敗，現按既有fixture順序執行，不移除遮罩或force。三張[UOS校外住宿](ncu-browser-evidence/ncu-uos-off-campus-390.png)、[HUST錄取後目錄](ncu-browser-evidence/ncu-hust-deferred-health-390.png)、[HUST統一任務](ncu-browser-evidence/ncu-hust-deferred-task-390.png)已逐圖檢視。

條件來源新增逐原件SHA版本綁定；原件改變／錯誤／URL或版本缺失不能沿用已讀政策，四種失效情況連同條件、來源與離線重建 **34 passed（46.48s）**。JavaScript syntax、diff及uv lock check通過。第一次OpenAPI check省略PYTHONPATH，載入另一未修改/workspace/abroad的安裝路徑而報drift；已用兩個實際import __file__命令確認，改用本worktree的PYTHONPATH=src核對，沒有以重產快照掩蓋差異。

本worktree OpenAPI .5快照檢查已成功（exit0），2026-10-08 11:49:55 UTC唯讀healthcheck與ls-remote也成功；main仍f6ad1b8、當時中央遠端7b381ae，沒有卡住或換環境。

## XJTU母校提名與HUST擇一保單接線修正

XJTU五項學生合一PDF維持獨立；另將已取得的2027春母校提名Excel接入母校負責步驟與document_requirements、catalog、個人／統一任務，不要求學生自行代填整校名單或代母校寄送。HUST保單另列一件行前文件：出境前購買涵蓋全期的醫療／意外／急難救援保險，電子版寄送或到校繳交擇一，不建兩件必繳、不移初次host包；HKBU原保險文字在第7頁。健康錄取後條件仍獨立。两件都保留Spring2027參考、116待查／未發布／無正式下載與host精確提醒。

HUST applicability已同步為同SHA八頁逐頁視覺已讀、2／3／7／8選定原文另存；2024歷史、Junshan upcoming及116未核實界線保留，沒有用閱讀完成當當期核准。gh更新PR說明曾401 Bad credentials，保存說明稿後以既有GitHub連接器更新成功並確認draft／未合併／head9d44a4e；未修改憑證。2026-10-08 12:00:04 UTC shell與ls-remote exit0，main仍f6ad1b8。

两项修正後API／任務／年度／條件及離線重建聚焦 **34 passed（29.69s）**；新手機實際目錄 **2 passed（74.13s）**，已展開母校提名及行前保單條目，明列母校負責／擇一提交與待確認，未啟用正式下載。完整module複驗續行。

最終本輪四module **111 passed（154.93s）**；OpenAPI .5與snapshot一致、diff check通過。兩張新增[XJTU母校匯總表](ncu-browser-evidence/ncu-xjtu-mother-nomination-390.png)、[HUST擇一保單](ncu-browser-evidence/ncu-hust-insurance-alternatives-390.png)已逐圖檢視。摘要／workflow／destination／field-audit四份實際產物均查無舊flyer未讀文字且仍含2024；sourcecoverage保持276／44 errors、44 partial／170未整理／0全116核實。


## 301來源、四校分階段文件與政府臺灣證件

2026-10-08 13:50:14 UTC在原worktree唯讀date／HEAD／ls-remote均exit0；main仍f6ad1b8，當時本地及遠端中央head7f0e1cc，沒有未返回的長時間工具。來源增加25筆：銘傳官方2027春公開分校附件18份、浙江官網4筆、政府3筆。301筆／44 errors，48校全部partial、166未整理、0校116全欄核准。新增三校廈門、西南、華中師範的七份原件暫存在/tmp，尚未計入301或48。

- 北京師範：AY2026–27三投影片依presentation manifest原序保留slide而非偽造PDF頁碼；GPA2.5/4.0無比較符號、非最後年級、臺港澳語言「無」與外籍HSK5分軌。六初次學生件、母校統一送件與JPEG另件；照片>300px／240×320及表格48×33mm矛盾保留。住宿60–80 RMB／日／人、統一安排及床具；不提供接機、北京前買全期醫療意外是義務，未杜撰host保單提交件。學费、完整預算與116接收版本仍待查。
- 東南：七原件均未標年度；銘傳2027春資料夾及母校10/15不等於host適用年／截止。三初次件、母校蓋章名單獨立；已填示例整段移除、不把GPA2.9等範例當門檻。體檢兩校對等互免尚未核定，宿舍表明許不填，兩件加入institutional confirmation、所有錄取／住房狀態都維持待確認。接機提前10工作日，不接也勾否及簽名退回；報到帶保單或到校自費買保險擇一。交換免400申請費及年度學費，宿舍四人900–1200／學期／床、雙人2400–4500／學期／床、床具自備；一般學位年限／學費不套交換，校園網敘述矛盾保留。
- 浙江：臺灣SpringSummer2027三頁、表格DOC及本科／研究生Excel逐頁／表讀；七初次件、母校名單擇一、保單可收到入學通知後補亦可先備，不能把保單當初次必缺。11/20/2026；本科交換時大二／三、限制院系與研究生醫學／管理不開分列。臺灣2–6月與通用表2–7月、1280／1600 RMB／年及可能跨校區保留。一般國際8頁另軌，Hangzhou11/10、Haining/Yiwu10/23、HSK／English及X簽證不套臺灣；當期課程分享回應Invalid share，首頁明示密碼由母校提供，沒有宣稱讀到內容；官網校曆仍春夏2026待更新。
- 重慶：十頁原字層及全頁視覺、2027參考校曆一頁、空白DOC、名單XLSX三表（兩空）逐一讀。九學生初次件、母校匯總独立，教師推薦1–2封沒有硬判copies=1；健康和醫療意外最晚報到，可提早，行前段兩件分開。10/30/2026、11–12月錄取及12月底通知；宿舍800–1200 RMB／學年、虎溪不保證宿位。40元平安保險選交不能代替醫療意外；2025專業代碼／2024課表UI不當2027課單。校曆2/20報到、6/21–27考試、6/28–7/11短周不是所有交換生統一離校期限。

三政府來源與host authority分開：NIA臺灣通行證公開指南、司法部法規PDF11頁全文、2025首次證件費豁免公告。親友家住宿24小時（農村72）与學校／飯店辦登記不同責任；五年多次／三月單次及續換分列，不套外國人X簽證。「不足六個月」是可換證條件，不判每次入境最低剩餘六個月。首次證件費豁免只2025/7/1–2027/12/31，不延到2028或免全部代理／補換費。指南原文舊200／40及46口岸保留audit、索引另隔離，不作現行費用回答。四校visa／cost／arrival与個人住宿登記流程已顯示實際產物；個別地方渠道／住宿校區和116更新仍具體待核對。

Office及PDF轉檔／視覺摘錄均SHA綁定；RTF偽.doc明確標轉檔、不杜撰頁碼。PPTX三slide順序、XLSX空表、同SHA sidecar及變更SHA拒用都有回歸。共享文件中心僅NCU：有該文件來源時不再混入整個步驟的所有URL，浙江兩種表的參考連結因此只顯示對應兩份；其他母校既有來源聯集保留。沒有新增API模型，OpenAPI .5快照一致。

本輪聚焦四校與原件／政府5 passed（71.34s）；SEU九組條件9 passed。最初API5 failed源自測試用錯workflow query與文字斷言，修正後重跑全過。Chromium四校原文／流程／生活首次3 passed、BNU切校逾時；BNU單獨第二次被boot splash攔截，補明確等待載入後1 passed（126.76s），沒有force或隱藏畫面。SEU／ZJU文件中心2 passed（161.67s含BNU失敗）；NCU文件来源收斂後ZJU1 passed（95.06s）。以下六張真實390px截圖逐圖檢視：

[北師申請](ncu-browser-evidence/ncu-bnu-slides-workflow-390.png)、[東南體檢流程](ncu-browser-evidence/ncu-seu-reciprocal-health-390.png)、[浙江保單階段](ncu-browser-evidence/ncu-zju-insurance-later-390.png)、[重慶最晚報到文件](ncu-browser-evidence/ncu-cqu-latest-registration-390.png)、[東南條件文件](ncu-browser-evidence/ncu-seu-health-condition-catalog-390.png)、[浙江表格擇一連結](ncu-browser-evidence/ncu-zju-form-alternatives-catalog-390.png)。


全四module最新125 passed／3 failed（455.41s），三項同因：浙江PDF原文含Unicode line separator，JSONL被Python splitlines拆成半筆，導致/documents及兩項檢索失敗。NCU builder只在JSON序列化跳脫U+0085/U+2028/U+2029；decode後原文不變、raw audit未改。重新build後原三項＋離線重建4 passed（88.89s）；同次新增保真測試因漏填ProcessedPage必填模型欄位失敗，改用實際合法模型後1 passed（5.65s）。所有JSONL產物與離線重建已通過，沒有略過原失敗API。診斷曾嘗試uvx py-spy，但tool directory預設唯讀而失敗，未安裝、未改權限；測試自行完成並非環境中斷。

共享跨校九module113 passed／6 skipped（162.55s），包含CGU bundled、NTPU support、NTU integration、application rules／workflow／context／task documents／document API／school content；skipped為原測試條件，不稱所有CI通過。另從未修改main實際runtime重新匯出851份流程，用相同當前模型驗證並逐份比較含重複的完整序列值：CGU154／NTPU409／NTU288，差異0，[比較證據](ncu-cross-school-parity-20261008.json)。舊hash檔未記序列化方法，直接套不同格式曾全部不符；本輪以同schema原始值比較，沒有拿hash格式差異當資料改動。

2026/10/8最新CCU遠端15270145ea93fab2c4d72a7112fe72cdcff5c6a3、TKU61659fe12cf5bb5f3fed2502f112039c7f8abd92；已唯讀fetch並重算13／14共享交集，[合併點清單](ncu-shared-merge-points-20261008.json)已更新，未合併或覆蓋。CGU手機工作區首次83.92s被boot-splash攔截；共享E2E helper原只等network idle，現在額外等真實boot overlay hidden 60秒後才操作，不force／移除遮罩。CGU同一手機工作區複驗1 passed（179.58s）：保留問題草稿、選校、資格、文件／舊路由流程實際操作過；測試有真實loader等待，不以移除遮罩掩蓋。


## 335來源、廈門／西南／華中師範與圖片、舊課表原件

本輪新增34筆來源：7份銘傳公開2027春附件、host主要頁／表8筆、額外官方文字9筆、廈門2027學位專業原圖6張、2025–26原生XLS課表1份、華中師範舊頁1筆及兩份公開browser選定摘錄。335來源／51讀取錯誤、51校全部partial／163未整理／0全116核准。臺灣證件政府三來源範圍已接入三校；全部214校116名額仍null、pending。

- 廈門：官網2026/3/3港澳臺規則与銘傳2027春須知分讀；初次四件為有效證件、蓋章成績、800字以上計畫、自簽健康聲明，母校提名表由母校負責。下載標籤寫PDF但健康原件實為DOCX，保留原始格式及SHA，沒有偽造PDF頁碼；到校保險另為報到證明，健康確認不是初次完整體檢。六張2027學位專業PNG均逐圖讀取，中文／英文本科80／4、碩158／16、博187／34列只摘錄必要欄，學位年限／MBBS／設計和漳州第三校區不能推定交換开放；港澳臺正文只列兩校區的差異保留。2025–26課表原始BIFF讀出兩工作表8,298列含兩表頭，只選讀表頭及首段，英中欄多處錯配，整份從問答索引隔離，原文仍可稽核。2021體檢PDF下載200卻是驗證碼HTML，明確未取得；不是已讀表或登入限制。住宿本科400–600／碩400–800每學期為對等自付參考、博士價未知，伙食1000–1500每月不是完整預算；宿位、住宿期限、2027春語言／課程適用及116新版仍待核對。
- 西南：2027春11頁簡章全文與逐頁視覺、兩頁空白申請、DOC體檢逐欄讀。2027/3–7及2026/11/30僅此春參考；母校統一送六類初次件，作品集只相關藝術專業，與接收單位確認後才能決定適用，錄取／住房選擇不會自行把它改為必繳或免交。本科二三／研究生二年級為優先，其他所列年級可在不延畢前提下申請，未硬排除。申請表第2頁推薦簽章與簡章「第三頁」矛盾保留；host審核簽章不要求學生先取得。新版初次體檢不沿用舊2026可抵達後補交。全部交換生有宿位、四至六人500–600每學期與申請表約600差異，研究生兩人房價格未知，床具自備、到校分配、住宿期限未列。醫療保險證明另為時間待確認的行前件，沒有杜撰初次或報到截止；音樂主副修額外教師費金額未知、四門課與院系預選範圍分開，完整課表／語言／116接收仍待核對。
- 華中師範：2027春22頁全文、低文字第5頁視覺及DOC表全讀；2027/2/21–7/10、2026/11/2，母校統一電子八類初次件，照片小二寸白底JPEG、表內含計畫及住宿選項，沒有再附舊2016獨立計畫／住宿表或兩張紙本照。保險涵蓋意外、急難救援及住院，證明到校後繳為獨立抵達階段。新版接機費校方付，未找到航班表及其期限；西區四種住宿600／750／900／1200每月、水電床具另計、選填不保證床位，1000–1500生活估計包含住宿與否未知。四官網索引local403如實保存；browser公開流程／2016頁只選定摘錄、沒有原始HTML SHA或全文已讀宣稱。未標年春申請11/1–12/15與新版11/2衝突、舊流程與表格不同階段均保留。返校後一月寄成績是未標年參考；全課表、116語言／費用／宿舍期限仍缺。

圖片與PDF分開：來源卡明列「原文圖片1／無PDF頁碼」及已視覺查核圖片張數；圖片本身不算HTML／PDF文字抽取或全文摘錄。原始XLS可讀內容與人工整表已讀分開記錄，SHA變更即拒用sidecar。host文件階段接到實際catalog／workflow／行前／抵達、student_summary和生活頁。條件政策在所有產物寫出前核對學校、步驟、文件及原件SHA；不匹配會保留前版bundle並報具體錯誤。

新增來源／條件／三校API首跑13 passed、3 failed；失敗為測試誤讀workflow API envelope，改為實際直返模型後3 passed（25.18s）。四個手機案例首跑3 passed、廈門首頁切換30秒逾時；正常等待延長60秒後廈門1 passed（93.94s），沒有force或隱藏遮罩。五張390px實際畫面已逐圖檢查：廈門2027圖片、健康DOCX、西南初次／作品集條件、華中師範抵達保單；後续完整回歸與共享合併點另補。

北京郵電2026春、廣西未標年交換附件已定位；華南理工來源短鏈與三校最新表／host索引正在查。這三校尚未計入51，不能以目錄或他校名額替代中央116核准。其他163項及51校各自未解欄位仍須續查，非全部官方未公告。

最新完整中央四module **149 passed（403.39s）**，包括逐欄完整度、三校API／年度封鎖、來源原件／XLS／圖片、作品集九種條件及無效政策不覆寫既有bundle。西南文件中心普通文字更新後實際手機 **1 passed（99.66s）**，已重新檢視截圖。OpenAPI .5 check、JavaScript syntax、git diff check、uv lock check通過；uv最初使用唯讀預設cache失敗，改用/tmp可寫cache即成功，未變更lock或依賴。851份既有CGU154／NTPU409／NTU288流程再次同schema比對差異0。共享九module複驗續行。

手機證據：[廈門2027圖片原文](ncu-browser-evidence/ncu-xmu-2027-image-390.png)、[廈門健康DOCX](ncu-browser-evidence/ncu-xmu-health-docx-390.png)、[西南作品集初次文件](ncu-browser-evidence/ncu-swu-major-portfolio-390.png)、[西南作品集條件目錄](ncu-browser-evidence/ncu-swu-portfolio-condition-catalog-390.png)、[華中師範抵達保單](ncu-browser-evidence/ncu-ccnu-arrival-insurance-390.png)。本輪未部署、未套正式DB、未改credentials/security、未對外聯絡學校。

共享九module本輪 **113 passed／6 skipped（84.33s）**；沒有新失敗，skip為原測試條件。


## 357來源、北郵／華南／廣西舊與現連版本差異

前一輪已推送a199426、PR4仍open draft、未合併。新增22筆來源後357／59 errors；人工54全部partial、160未整理、214名額null、0全116核准。公開Drive仍459份，明確全文已讀5份、視覺4份，新增北郵7頁正文與廣西16頁原件逐頁視覺；非把所有抽取得到的454份稱已讀。

- 北郵：中央2026春7頁、靜宜2026/5/15截止4頁及當日現連5頁全部正文已讀。六初次類含手寫不得空項、成績（碩博另最後學歷學位證）、計畫、健康、二寸电子照及居民證／通行證影本。白底與當日現連藍底差異保留；新版刪截止，沒有推當年或每年10/31／5/15。舊本科／碩／博／中外合辦／海南與新本科目錄／院系名稱差異，不能自動全開或排除研究所；紙本郵寄加掃描zip、host通知寄母校，沒有寄信或填表。四／六人房獨立衛生間不帶淋浴，價與全生活費、保險、宿位期限及116全套空白表仍缺；官網412不寫登入限定。
- 華南：靜宜當日現連3頁全文未標適用年、沒有deadline或其所稱附表；五電子件僅按此清單、空白申請表未取得，不從舊版480×640／WORD格式補成新版。院系最後審核、本科／碩最後一年排除、研究生與靜宜目錄博士禁申差異，中央可否博士需核；兩校協議免host學費但未核中央有效合約。五山／大學城交換分配與全校廣州國際三校區分開，600–1500 RMB／生／學期不含水電當年通知準。官方下載入口全讀，七頁全影像2018手冊逐頁看完是華南outgoing赴港澳臺，兩書頁一PDF頁、不借其臺灣入臺證／保險／GPA／獎助／返校表。整件從問答索引隔離，原七圖與查核保留。CCU短鏈200回轉址失敗明列未取得，不用CCU名額／停招判中央。
- 廣西：中央未標年16頁全部可讀正文與逐頁視覺核對，13頁多照片／英文介紹，空字層不覆寫、不依照片推當期房型。第2頁春「每年3月至次年7月」與「1學期」矛盾保留、未修成同年。六初次類由母校統一送，跨院可在計畫述理由不硬禁。公費／自費均依協議，不把詞意當免學費；東校園國際學院住宿約4000／學期、伙食300–500／月、其他2000／月是未標年參考，不能合成精確總價。入學後指定300／學期意外醫療保險不賠一般疾病，為抵達义務、原件未列保單提交件不杜撰host文件。現行官網港澳臺索引只有2026學測學位，下載中心2021免試入學Word與2023外国人體檢表不替代交換表；舊show-539失效、新交換表未找到與官方未公告分清。browser五選定摘錄不偽造HTML SHA或全文已讀，local403另保存。

三校政府證件、費用豁免期限與實際住處登記沿用已讀政府原件、並標116出發須再核。三校API首輪3 passed；同次來源測試1 failed（合計57.95s），發現舊outgoing指南封面轉錄仍會優先進索引；已取消公開轉錄保留原圖與稽核說明，整七頁確實隔離。來源複驗與逐檔離線重建2 passed（20.88s）。三校390px真實畫面3 passed（174.05s），依次展開原文、生活、申請內容，三張均已逐圖檢視：[北郵照片底色差異](ncu-browser-evidence/ncu-bupt-photo-conflict-390.png)、[華南空白附表缺口](ncu-browser-evidence/ncu-scut-missing-blank-form-390.png)、[廣西抵達後意外醫療保險](ncu-browser-evidence/ncu-gxu-local-accident-insurance-390.png)。完整四module續行；無新增共享實作變更。

2026-10-08 16:06:35 UTC shell健康、pytest實際CPU執行及遠端核對成功；main仍f6ad1b8，中正已c6d86bc、淡江61659fe，13／14共享交集已重新計算保存，未覆寫其分支。廣島已開始下一批：公開2027校曆、2027春時程及現連空白表／政府攜藥原件暫存在/tmp，尚未计入357／54，未以取得原件當116全部核准。

本批完整中央四module **153 passed（294.75s）**。前一a199426共享九module113 passed／6 skipped及851流程差異0仍是共享實作的最新複驗；此22來源批只增加NCU資料、來源與測試，未改共用實作。OpenAPI .5快照及diff檢查另核對；不宣稱既有main全部CI通過。


## 廣島：406來源、現連表格與日本行前／離校資料

前一批已推送719d523、PR4仍open draft；本批增加49筆原件／正文／讀取失敗紀錄，406來源／66目前error、55人工整理全部partial、159未整理。Drive459份不變，全文明確已讀增至7份（新增廣島2024三頁及未標年兩頁）；214個116名額均null，0項全116核准。東京科學大學來源仍暫存/tmp，不計入這些數字。

- HUSA現行頁實列2026秋與2027春：2027春提名2026/8/15、申請9/20在查核日已過；年例不能推成2027秋或2028春。官方2027校曆已公告並核對原1頁，不將「未找到交換申請新梯次」寫成「校曆尚未公告」。中央115表限大學部與host HUSA可接研究生分開；NCU是否屬可春季交換的部分伙伴仍未知。
- 初次八類、錄取後COE銀行存款（一學期480000／一年960000JPY）、臺灣護照持有人COE簽證五類及離校退居屆分階段。初次申請／checklist PDF與Word、課程加頁、語言證明現連原件全所得正文已讀；學生／母校承辦雙方簽名、推薦人必須教過學術課程、非六學分而是七堂／小時標示差異均保留。網頁above與語言表61+等門檻矛盾不硬改判；native English仍需表單證明，不能免中央正式語檢。
- 官方宿舍房型、日常交通及退宿頁逐正文核对：Ikenoue男A/B/C、女D且國際女生可C；住宿承诺版本不同，無116宿位或價格保證。現連2025手冊403保留失敗，另從現行官方入口取得2023版33頁，仅讀1–4、29–33共9頁；其餘24頁未全讀，全文從問答索引隔離。退居屆原1頁全讀，至少一月前交、先確定點檢再約清潔、10–17千清潔費及現金結清只作未標年參考。
- 日本臺灣交流協會2026/7/1費表正文幣別JPY與臺幣原圖分開；原圖完整視覺核對，臺灣一般單次3120TWD、印度欄180不套臺灣。簽證空白表兩份各兩頁全讀；單面規則在文件頁與表格頁不同仍保留。原圖無PDF頁碼，用image:1及SHA／轉錄sidecar，不虛構原第1頁。
- JASSO現行NHI、MOFA學生簽證、MHLW攜藥頁及10頁QA已讀；攜藥QA第8–10頁2020範例／劑量從問答索引隔離，並非處方建議。HUSA舊一年藥品／抗生素與不完整再入境文字同樣隔離；ISA四筆403沒有改稱登入限定。政府居留／再入境完整適用範圍仍缺，不給個人入境核准。

流程增加明確的before_home_return插入位置，使抵達後保險、交換期間旅行及離校退宿放在抵達後、中央返校前，沒有改其他學校的workflow。研究生研究時數申請、臨時旅行與池之上退居條件依原件SHA綁定，全部要求實際接收／宿舍單位確認；錄取或選校內住宿不會自動變成普遍必繳。旅行與研究申請空白缺口、未標年費用與宿位、116新梯次及中央春季資格仍具體列在17欄audit。

本批四個NCU／條件／來源／completeness完整module **164 passed（290.70s）**；廣島手機案例 **1 passed（121.01s）**，三張原圖／COE／退宿截圖逐張檢視並追蹤於docs/ncu-browser-evidence。共享實作未變，前批共享113 passed／6 skipped、CGU154／NTPU409／NTU288共851流程與main同schema差異0仍是最新共享複驗。2026-10-08遠端再次唯讀核對main f6ad1b8、CCUc6d86bc、TKU61659fe，13／14共享交集不變。OpenAPI .5快照及git diff --check通過。首次手機內容核對已看到原圖、生活頁3120TWD、八件初次文件與COE階段，最後提示文案斷言不符合真實workflow generic「待官方確認」，已改核對實際提示及個人住處仍需核文字。第二次在切換母校後DOM等待逾時、未到內容，保留失敗紀錄；未移除啟動遮罩或強制點擊。


## 東京科學：438來源、ACAP／YSEP提名前置與2027 TIEC新費率

廣島檢查點fc876ca已推送，PR4仍open draft、未合併。本批新增32筆來源，438筆／68目前讀取error；56人工整理全部partial、158未整理、0項116全17欄核准，214名額仍null。Drive459份取得不變，明確全文已讀10份／視覺4份：新增2024兩頁比較、2025十二頁簡報及未標年一頁介紹的全部原生正文。三份舊附件均從問答索引隔離；不是把454份有字抽取當全文已讀。

- 中央115表僅限115-2、歷史3名；host理工ACAP／YSEP接受學制各別，不替中央核准116。現連官方網站聲明合併後資訊仍有效，鈴懸台校區已於2026/4/1更名橫濱。全校醫牙健康校區與理工課名含Medicine不是相同接收範圍，不用regex封鎖課名。
- ACAP提名時母校提交個人課程計畫、校方指定教授；YSEP非建築申請前取得教授同意，建築由校方安排。兩track共用八類初次件含COE Excel，另按track／年級／系所準備語檢、CV／作品，不移植廣島錄取後COE或銀行480000。推薦為母校副教授以上學術教師、非語言教師；現連在學Word須Signature and Stamp。語言未列通用英語數值；非母語MOI例外僅指定母校所在地，臺灣不在列，不免中央home正式語檢。
- 現連COE2026-v3五sheet全原生正文逐欄讀，但含預填範例，公開只有必要欄位摘錄；範例姓名、每月120000、收入8000000及研究室不進問答或填答預設。ACAP課表表頭2026／2027、檔名fy2025-2026、選單仍2026且Sept與網頁Oct不同，第三sheet承辦模板不是學生附件。2026秋五頁課單已讀，400+未在名單者即使教師同意亦不能選；每課先修與核工輻射工作者資格仍要個別核實。ACAP每週六堂600分鐘與YSEP研究／發表、可選授課差異分開。
- 新2026/10健康Part I／II各兩頁與2025 TB國別一頁均原生及逐頁視覺核對，五張原圖及SHA保存。網頁Part I風險群與英文表All students IGRA矛盾未裁決；臺灣不在國別圖不等於免交。Part II抗體或疫苗可部分合併、破傷風與醫學例外分列，沒有要求兩套皆做。至少三月的新國際生健康是入學前另階段，晚到依個人與接收期限核對，不塞初次八件。
- ACAP／YSEP在online申請表勾住房需求，不另交一般Dorm申請、不保證宿位。一般Dorm預告2027/1中後招租非兩track住房截止；南行德已2026/9關閉、長津田可能2027秋結束。TIEC理工研究生級住宿四表與身份件另分階段：Form1／3只讀公開空白第一sheet，第二張記入例未讀；Form14一sheet與校方誓約兩頁已读。新渡日者在留卡、海外新人指導教師代簽及C／D家人文件須實際住房確認，不由錄取或住宿選項自動決定。
- JASSO已公告2027/3/1新入住TIEC月租A48000／B60000／C86000／D100000JPY，入館費另一月，水電另計。既住戶過渡到2029/3/31與重新入館／換棟例外、2031另價分開；不套school頁旧35000等價作116预算。現行學生指南72567字只讀1.1–1.5、3.1、4.1–4.5、10.2指定章節，未宣稱整本已讀。理工交換一年事故／責任1340JPY為必須；非正規學生僅東急通學票、無JR學生折扣票。暫離日本non-regular理工指定Microsoft Form不同於degree／medical流程，未登入或送件。

NCU builder新增before_host_application插入點，把提名課表／教授同意／track件放初次八件前；健康、條件TIEC、另要求財力、COE後五類臺灣簽證与抵達保險／交換旅行按各原件分階段。16條條件政策綁實際workflow ID及各文件精確來源SHA，九組狀態均待機構確認。第一次build被不匹配的步驟／來源版本擋下，修正後才寫產物，沒有以無效政策覆寫前版。

本批完整四module **175 passed（319.75s）**；新增兩API／九組條件聚焦先 **11 passed（27.20s）**。390px手機 **1 passed（86.55s）**，實際展開初次COE八件、健康矛盾與TIEC2027費用，三張已逐圖核對：[初次COE](ncu-browser-evidence/ncu-science-initial-coe-390.png)、[健康適用差異](ncu-browser-evidence/ncu-science-health-scope-390.png)、[2027 TIEC費率](ncu-browser-evidence/ncu-science-tiec2027-fee-390.png)。OpenAPI .5實際快照check exit0、git diff check通過；首次誤帶未支援--version參數的命令失敗已更正，未重產快照。共享runtime未變，前批共享113 passed／6 skipped及851份CGU／NTPU／NTU流程與main差異0仍是最新共享複驗。

最新唯讀遠端main f6ad1b8、CCU4a299f5、TKU61659fe；共享合併點再次列出，未切換、合併或覆寫其他分支。Science公开搜索用JSON已另外定位中央伙伴列，暫存/tmp待下一批接入，不計438／56；伙伴身份不證明116名額或semester。千葉新版2026–27手冊原站與其他大學官方轉載空白表正在查，亦不計本批數字。158項與56校116各欄缺口仍須續查；未查完不寫成官方尚未公告。


## 千葉：497來源、初次健康表、語言分流與宿舍／保險版本

前批東京科學已推送`0b10d31`，PR4保持open draft。本批新增58筆千葉／日本政府及一筆Science伙伴JSON，497來源／71讀取錯誤、57人工partial／157未整理、0全116核准。Drive459份不變，明確全文已讀12份：新讀千葉2025/1/10五頁factsheet與未標年一頁介紹；舊2025–26 36頁outline僅12頁選讀並隔離全文索引。中央115千葉第5頁歷史4名（上2／下2）、限UG，116仍null，不當零名額／未開放。

千葉官網2026–27新J-PAC 33頁全原生正文已讀，CAU官方轉載同SHA；2026/1/14五頁factsheet的UGM／CAU兩份轉載亦同SHA。J-PAC只UG、申請時二年級以上、日語已學50小時並滿足英語B2/iBT72/IELTS5.5或日語N2/B2其中一類。Faculty Direct的UG／grad、研究生先讀一學期及各學院程序另列，不以申請書Graduate checkbox或UGM自己的文章覆蓋J-PAC範圍。新版英文第7頁仍殘留舊兩course稱呼、日文第22頁沒有，不生成舊雙track選單；官網alternate檔正文其實2024–25，只讀封面。現連2025–26舊course list只選讀表頭；2026信息提到新版附表但未取得，推測URL404不能寫成官方尚未公告。

七份Word空白表、checklist、deadline、course information逐件原生全文已讀，沒有虛構固定PDF頁碼。語言原圖第16／31頁均已視覺核對並追蹤PNG，YES/NO圖頁扁平文字不直接交regex/RAG判分流。英語native/semi-native勾申請書；非母語有test交score、無則母校英語教師指定表；日語有N1/N2交結果成績、無則日語教師表。英或日擇一、機構學日語另交教師證明；over B2與B2以上／英語大學與母語範圍差異保留。日語教師表須日文及教師簽名；host JLPT證书未到可網站暫代與中央正式語檢不接受截圖分開。

初次共用八件是app／plan／reference／英文成績與評分／emergency／health／passport／貼表photo；健康在初次即交，醫師胸X光及簽日期、沒寫統一三月內檢查，不套東京科學入學前健康或廣島錄取後程序。申請書本人簽日期及Katakana；計畫約一頁、日語N2/B2以上用日文；推薦教師認識至少一年、confidential直接交母校，不同語言教師僅preferable。緊急表本人同意、母校人士及親屬兩個必填，日本聯絡人如有；不捏造三位皆必填或聯絡人簽名。checklist不用提交、每學生一資料夾，不加UGM自己的CV／動機／在學／三照片到host或home必繳。

2026–27母校提名2/13及8/28、email申請2/27及9/11全過期；UGM自己的2/1／8/14／9/2和Fall2023殘句不是千葉／中央期限。最新nomination sheet、116日期與受邀系統仍未取得。COE錄取後依母校收到指示另準備；新空白表、bank清單／金額未知，不套Science初次五sheet或廣島480000。三program期Oct–Aug／Oct–Feb／Apr–Aug，舊中央MAR–AUG另隔離；每非春假Term6週7堂、每semester兩連續term共10credit，不變成每term10或週7credit；Japanese5xx以下每term一英語／雙語，未保證新課全開或中央採認。

International House已2025/9關閉、舊218宿位與9–17入住仍留原頁但不提供舊宿舍申請。J-PAC校方另安排附近公寓，只住program期、不因實習延住；租50000–80000JPY已含在每月約100000伙食水電電話總估，教材休閒另計，不重複加租。自行租屋初期至少5倍租只是未標年概估、實際契約／家具／退租一月及清潔結算別核。使用校方機關保證才另需JEES租屋保障與指導教師簽名加章的Apartment Residence Guarantee Request，最新blank須ISD提供，不能因校內／校外住宿選項自動要求。

現連保險15頁原图全視覺已讀且逐頁PNG/SHA追蹤，原native空頁保留，未OCR／未稱原生文字全文。它標AY2025及2024/7、11製作：A一年1860JPY不含醫療，B11500、醫療需NHI及至少4月，不能把手冊1860說成包含傷病費；四月A1030/B6330、六月A1310/B8060僅舊年參考。晚繳次日才開始；疾病／牙科／精神／孕產等除外、救援事件條件另列，不提供全包醫療承諾或個人方案推薦。三保險必需與母校海外全期／入日前旅保分開，沒有杜撰初次host保單上傳。千葉市2026/6/25新證件頁取代舊hokensho當場／掛號親收說法：MyNumber或資格確認書，資格資訊通知書單獨不看診，僅千葉市適用；不推2027郵寄日。

政府年金原頁逐件核：20–59依法定資格、FY2026月17920JPY不是2027新價；nondegree exchange使用一般免除／猶予申請並獲批准，不能自動用degree學生納付特例或預設零支出。到校2026.10市役所協助手紙、三頁辦完程序、四頁2024到校程序、六頁疫苗建議與一頁self-check已原生全文讀；self-check不用提交。住址市區按實際住所、passport／在留卡／日文住址，銀行app無passbook且provider審查，不保證入境即開。J-PAC迎新直接由program通知，不用一般MEXT場次。最終退租結帳、確定自扣完才關銀行及NHI／年金／住址程序另段；暫離先告學院，政府ISA原頁403，完整再入境例外未讀，不捏造登入限定或个人入境核准。

Science Tokyo公開原JSON262列中只選讀唯一中央列：type01校級、exchange02學生交流／exchange03互免學費均t，另讀官方JS及HTML控制對應；原JSON格式校驗與公開摘錄SHA綁定，變更原件立即拒絕沿用摘錄。只稱中央1列及對應控制已核，不說262伙伴都逐列讀。移除「尚未核中央列」缺口，116協議續效／名額／semester與個人接收仍未核。

2026-10-08約17:45 UTC環境短暫回到starting；立即回報並在17:45:57最小healthcheck確認shell/date/Git與/tmp千葉JSON／保險PNG保留，HEAD仍0b10d31，沒有資料遺失。第一次build因舊五頁課表引用page=None被攔，改實際PDF第1頁後原子重建成功。新增JSONcollector二例2 passed；初次聚焦13 passed／9 failed是新增千葉測試誤放東京科學三條斷言，已移回原Science案例，完整回歸結果續記。2025生活指南92頁目前只讀8頁，剩餘84頁公開可續查，不以此當官方阻塞；各校當期未核欄位與157未整理仍需持續查。

完整中央／條件／來源／completeness四module **188 passed（234.36s）**，包含新增JSON原件變更兩例、千葉初次健康／語言分流／COE／閉宿與三保險資料、九組錄取與住宿狀態。OpenAPI .5快照check與diff檢查通過。最新唯讀main f6ad1b8、CCU0e70dbf、TKU61659fe，共享13／14檔交集已更新；只更新遠端追蹤參照及合併點檔，沒有切換或更動其他工作分支。手機內容結果續記。

390px真實Chromium初次 **1 passed（62.94s）**；逐圖發現confidential應為「保密」而非密封、off-white應為「乳白」，僅修精準譯名與学生文字後API/source **2 passed（10.05s）**。第二次手機在來源非同步載入前的5s等待失敗，未到內容，保留53.37s失敗紀錄；等實際workflow載入並給來源60s後 **1 passed（71.64s）**，未強制點擊或改遮罩。新版三張畫面全逐圖核對並追蹤：[初次醫師健康表](ncu-browser-evidence/ncu-chiba-initial-health-390.png)、[保險原圖閱讀狀態](ncu-browser-evidence/ncu-chiba-insurance-visual-390.png)、[AY2025 A/B保障及費率](ncu-browser-evidence/ncu-chiba-insurance-plan-390.png)。同樣實際展開語言三條件件、COE錄取後、關閉宿舍與健康Word原文，頁面無JS error及390px溢出。當前CGU154／NTPU409／NTU288共851流程再與未修改main匯出、同schema含重複multiset逐值比對 **差異0**。

後續閱讀2025生活手冊原PDF54–63頁十頁（支援／學生分類／移民程序），與原8頁共18/92、剩74頁。舊school40h工時／6000費與延居所需hokensho不当116新規；全92頁仍隔離问答。PDF60頁另連政府special-reentry930002122.pdf，web與本地原件皆403，已新增獨立失敗紀錄；總497來源／71錯誤、57partial／157未整理與0全116不變。先前188完整module為496資料／8頁紀錄時通過，這筆原件失敗与閱讀範圍補充後僅再跑必要API/source案例，結果續記，不冒稱全部公開指南已讀。

補充後API/source **2 passed（9.80s）**；續接tool回Unknown process id後，18:46:17 UTC立即最小healthcheck確認pwd/date/Git、HEAD0b10d31、變更與落盤測試日誌完整。屬工具無法續接已完成程序，未證明環境重啟；沒有遺失資料或重跑已通過重型測試。OpenAPI及diff結果另讀落盤／退出狀態確認。


## 大阪公立OMU公開表格、日語B2與故障來源批（531筆、58 partial）

新增34筆來源，使公開host／home讀取紀錄531、錯誤78；人工逐欄58全部partial，156尚未整理、0項116完整核准。Drive下載數仍459，2027春EN／JA四頁及未標年一頁增完整原生已讀至15；2025秋只讀1–3頁，第4頁字型錯亂未完整視覺讀，未稱四頁全讀。這不是完整中央資料交付；仍需持續研究其餘156項與58項具體未解欄位。

OMU2027春中日／英四頁與中央Drive副本逐頁原生讀，兩語host與NCU各相同SHA。官方簡章明示的公開SharePoint資料夾含10檔：兩語簡章、checklist、誓約DOCX、履修XLSX、配慮XLSX、碩士研究計畫DOCX、大學部志望理由XLSX、指定在籍XLSX及日語教師XLSX。以該匿名公開分享建立唯讀context，只讀該資料夾明列文件，無登入／OAuth、無其他目錄或cookie保存；各原件另用collector實際重讀，同SHA與真實回應Content-Type保存。Chromium在公開分享入口ERR_CERT_AUTHORITY_INVALID，未忽略TLS／修改安全設定／認定登入限制；requests預設TLS驗證取得全部原件。文件／大小／SHA與公開資料夾核對紀錄在[公開資料夾紀錄](../sources/ncu/2026-10-08/host-omu-public-folder-review.json)。

checklist一頁全原圖視覺讀；[原圖](ncu-source-evidence/host-omu-checklist2027-p1.png)及同SHA視覺紀錄保留。英文能力證明是「持有才交」，配慮僅希望／需要者；UG志望理由和碩士研究計畫擇身分、不兩件必繳。初次八類分學生五類與母校三類：近三月JPG彩色脫帽照、不同於護照照片；護照直向A4彩掃PDF非JPG／PNG；履修XLSX藍欄／個資勾選；日語JLPT/JTEST/JLT或指定教師證明；本人簽日期誓約；承辦另OMU英文在籍確認、英文在學、英文成績PDF。指定確認日文是全交换期母校學籍、英譯卻寫host university，差異保留，沒有強制承辦簽章的未明示欄位。表格部分格式列PDF與總則不轉Word／Excel矛盾另核，不一律合成PDF／zip。履修表第二張填寫示例已移除公開值，第三張住宿仍37800／80k／旧保費与2027簡章46000矛盾，僅保留第一張空白公開摘錄，三張原生閱讀範圍另明示。

2027春只UG／碩士，不擴博士。UG森之宮基幹教育、原則不能專業；碩士研究科及工學／情報校區由host決定、情報多線上；創藥科學明列可接收，不因藥／醫療課名一律禁。母校兩門且一專業與UG限制實際衝突，採認／例外待兩校核定，不作regex通過或不合格。日語CEFR B2強制，部分英語碩士課不免日語。JLPT官方新制從2025/12起：需全分項合格，N2 90–111為B1／112+ B2，N1 100–141 B2／142+ C1；只涵蓋讀聽及知識、不等於口寫互動或OMU准入。舊2010–2025/7成績仍有效但接受由機關決定，中央home正式語檢另必要。2026課表XLSX361行全原生讀，有文學專業／外語母語不得修／申請後分班／遠距期末實體等，不套2027。故障後2026教務日程一頁全原生讀，不當116新課曆；臨時新syllabus入口空JS框架尚無課目正文。

2027春一semester4/1–9/23，一年4/1/27–3/31/28；不可改期，結束前返國，考試後可早返不代表可延住。提名10/1已過、10/10申請10/8尚未到，但不是中央116出發期，全部提醒保持封鎖。公開program／住房／access／研究所課表五原URL均HTTP200轉官方臨時故障站，collector以明示URL範圍保留實際body／final_url並列error，不計原頁下載／正文／全讀。原syllabus503、ISA照片規格403另保存，不稱登入限定或尚未公告。10/8mail通知只校內恢復、外部收信預計當日／對外寄信約10/13；臨時在校生摘要仍停用，來日交換10/10未找到展延公告，不能用在校生10/14選課改期推交換期限。

I-wing住位不保證，LOA一起通知、不要自行申請；健康診斷書只實際申請I-wing的錄取後住房程序，新blank／效期／回覆期限未取得，不放八件初次。月46000＝34000＋12000含水電，初67000–68000＝押金46000＋清掃17000＋依期保險4000–5000；押金無欠費抵最後月，不能重算。通勤到森之宮約一小時、12000／16000–18000月參考且無學生通學定期。I-Dorm預計2027/4開館；營運商136室與一般一年契約月館費／管理費／水電網及190000入館費已讀，沒有把它當交换半年度分配／價。食物／電話／教材／全期預算、OMU當期學費互免條款與保險保障仍具體缺口。

COE接收後另寄母校清單，日本籍含雙重不申COE；新版財力／空白包未取得，不套Science初次Excel／廣島480000。日本簽證LOA／COE與臺灣官方文件參考分开，簽證後再買票。堺市2026/3英國保含舊hokensho，2026/9/28日頁已核資格確認書／MyNumber、資格資訊通知書單獨不能就醫；只真實住所堺市適用，不按教學校區或套大阪市。大阪市2026/5日文海外轉入passport／在留卡及無入境戳證據、英頁Special Permanent Resident Certificate差異保留，不強制普通交換生日本戶籍／特別永住件。20–59年金一般免除／猶予需申請批准，不套degree學生特例；government再入境原頁／PDF403未取得完整例外。入境迎新與交換結束／退宿／完整成績送母校程序各接流程，一年期不發半年度正式證明；離校表／退宿提前通知月數未取得，不套其他校表。

另修正51筆已有明示kind卻未轉為authority_kind的來源標籤（29host、16其他母校、6政府），尊重已人工標定發佈者；仍有其他未明示kind的舊紀錄未逐筆發佈者重核，沒有宣稱全531筆發佈者完備。新日語檢定來源為official_language_test_provider、Dormy為official_housing_provider，不按來源ID／校名regex推發佈者。collector新增公開context、預期Office容器與官方故障轉址檢查測試24 passed（2.55s）。建置曾因一筆簽證PDF以page=null引用失敗，已改1–2頁，原bundle原子建置未覆寫，修正後完整建置成功；不是空值自動補造頁碼。

大阪公立首次完整四module207 passed／1 failed（306.66s），實際發現初次照片`photo_specs`不是共享ApplicationDocumentRequirement支援欄位，API忽略。全量人工文件掃描另有14處notes及12處copies_required：照片規格改放正式name與流程details、份數改copies、適用備註改欄位points／流程details，原件與條件SHA不變。曼尼托巴研究生、信州if available與新版Sheet、芝浦track限定均保留；沒有改共享模型或猜份數。builder新增共享model_fields嚴格檢查所有初次／提名／補件／行前／抵達／保險文件及自訂stage，未知key在任何輸出前拒絕，不再靜默刪欄位。

第二次完整四module214 passed／1 failed（285.75s）；失敗是新增備註測試把ncu-101曼尼托巴誤當奧胡斯，資料與API中的曼尼托巴備註已存在，更正學校並以大小寫無關方式選取芝浦。此前聚焦7 passed／1 failed的照片名稱比對也已改為實際官方簽證件名稱。中文整理由簡體轉繁體時，建置的條件名稱綁定先正確拒絕不同名，更新同來源的明示綁定後成功；原bundle沒有被無效建置覆寫。後續複驗與手機畫面結果續記。


## 新潟：562來源、IEC與研究科分流、2027春空白表與行前生活

新增31筆公開host／政府來源後562筆、79讀取錯誤；59人工紀錄全部partial，155未逐欄整理、0項116全17欄核准。Drive459份取得不變，明確全文原生已讀增至17份；新增兩份中央舊新潟附件全讀，2024／2025／2026文字矛盾原樣保留並隔離問答索引，不能覆蓋新版。OMU補正後完整四module230 passed（303.48s），但在後述TIEC範圍、新潟及共用結構化修正之前，不標為最後候選SHA結果。

新潟官方2026/10現連2027春英／日簡章各六頁、IEC申請／推薦／研究科基本資訊／健康／COE／財力／grade formula各空白原件及研究科分類三頁，全部指定原生正文已讀。2027校曆一頁已下載、逐圖核對，原SHA與[日程圖](ncu-source-evidence/host-niigata-calendar2027-p1.png)另記。2026春與秋課冊各三頁、JASSO2026秋22頁與startup兩頁均讀全部原生文字，但舊年資料隔離索引，不宣稱22頁皆視覺讀。官方日文交換頁與政府JPETS頁僅選讀指定段落，未稱全文；2023國保手引19頁未讀，僅讀官方landing。

- 2027春提名及申請2026/11/1–10 JST，由母校承辦送；11/1才開IEC入口，未登入。這不是中央116出發期。秋2027官方現頁明示to be announced，不能推為固定5/10；Spring2028新版未取得不同於未公告。當期名額null、全部提醒封鎖。
- IEC No.1本科／No.2研究生與No.3–11研究科分流：後者初次只母校email基本資訊Word，表明非入學申請書；研究科後續整套文件尚未取得。No.2一般不能研究科授课、無academic advisor；被研究科拒絕不能同一期改IEC。醫牙健康No.11宜提前一年聯絡是建議，不自動變每人固定截止；本輪未聯絡學校。
- IEC初次學生六類各1份，健康及胸X光在初次即繳，效期為入學前半年、醫師簽日期；COE初次Excel三張不貼照片。母校另合一推薦XLSX，母校簽名或公印擇一，不加本人或強制雙方皆簽章。財力本人支應只本人銀行1份、他人支應四份各1；89000JPY為每月平均經費能力，不是總存款89000或別校480000。非英日翻譯可本人打字，不杜撰全件公證。
- IEC網站失敗才改備用申請XLSX、由母校email，不把備用檔當全員另必繳。原件4工作表已讀3、第四2026秋承辦表未讀／未發布；公開只第一張空白。移除預填六年級／0、推薦表示例姓名，保留原件SHA與公開摘錄SHA，不把預填值作學生條件。COE示例中的支應者金額／機場與舊住房數字也從索引隔離。
- 19份條件文件按IEC、研究科、財力、網站失败、住房及政府個人適用各分階段，全部需要實際機構確認；頂層共用host清單空，不套IEC六件到所有研究生。母校提名／備用／研究科基本資訊有明示email；IEC入口有明示online URL；其他未明示送法保持unknown。
- 一semester2027/4/1–8/31、兩semester2027/4/1–2028/2/29，抵達晚三月等通知；每週7堂90分鐘不是7學分。JASSO另外10學分／學期與JP目安差異保留，2026秋課程／mandatory10/1不套2027。2027日語課預告三月、新外語課仍準備中；capacity／lottery／prerequisites及研究科課限制須逐課核，學期後只寄PASS成績且無提前證明。
- IEC學費14800／credit只有有效互免協議及母校提名減免才免，研究科29700／月不同；中央116互免有效性未核。宿舍IEC強制生協單人房、不保證校舍／家人同住；2024一般FAQ的家人／改房例外不能覆蓋新版IEC。MEXT／JICA International House22000與degree優先Rikka13000不是普通IEC保證。
- 生協一般初期67500＝8500責任／10000租保／44000清掃／5000出資，NU付押金仲介但學生付月租水電；月租Ikarashi25000–45000、Asahimachi35000–55000。約80000月總估已含房租／伙食／水電，不與89000財力能力或房租重複加總；到校200000–250000現金為未標年host估。一般住房預約時點明載as ofFeb2023與至少抵達14日前，不當2027確認截止。簽約取消／三月費及90天差額依實際契約，不套到入學取消懲罰。
- 交換頁學研災／學研賠一年1340必須與一般保險頁鼓勵措辭差異保留，Futai為另外建議非千葉三保險全必需；國保新MyNumber／資格確認書，不用舊hokensho保證領卡。2026年金17920不是2027新費率，非學位一般免除需申請批准，不自動學生特例或零費用。2026startup的MFA／ANPIC與銀行活動日期不套2027；影片未觀看、指定帳密guidebook401是真實登入限制，未嘗試登入。
- 政府JPETS現頁2026/9/25新增印尼，預定2026/11/2開始指定檢查、2027/1/4開始COE證明；host新春簡章僅列菲／尼／越，適用差異具體保留。依真實國籍／所在居住地證明／COE時點及豁免核定，不以臺灣母校猜全員臺灣籍，不將一般胸X光替代Panel Clinic證明。舊host郵寄COE與新版email不同、政府ISA403完整再入境例外仍缺；入學許可不等於visa或住房日期確定，未作個人入境核准。

新潟API初次2 failed：實際發現共用workflow structuring從「簽名或公印」自行添加「本人」及XLSX預填六年級仍公開。前者改為NCU只保留明示送法／梯次／份數／文件形式／簽章，其他学校舊行為保留；後者改空白公開摘錄並重建。全214流程原始文件與API的名稱／copies／copy_type／signatures／stamps／official_form_url及送法／梯次逐值守恆，聚焦3 passed（10.84s）；另6既有workflow structuring案例通過。新的19份測試原先誤寫20已更正，未刪文件湊數。

另發現東京科學TIEC Form1／3原2工作表只讀第1張，摘錄處理過去以公開1張誤計all_parts_read；現在原件工作表數、已讀工作表與SHA另綁定，這兩份不計全讀，OMU原3張全讀仍正確。collector與OMU source聚焦28 passed（4.94s），新增3原始範圍測試；不改原始附件或未讀示例。

## 真實選校驗收、畫面發現與同SHA重驗要求

[候選驗收門檻](ncu-acceptance-20261008.md)列手機／桌面、配對、收藏比較、母校切換、文件中心、條件文件、儲存重載、來源及共檔檢查。資料門檻仍未過，不能用通過的UI測試宣稱完成。首次兩組選校測試已收藏卻未按独立比較checkbox，2 failed；改為真實勾比較後2 passed（190.10s）。逐圖發現桌面「我的志願」sticky遮比較表，NCU workspace加母校標記與專用static定位。第二輪合併跑2 passed／2 failed（272.89s），新潟已看到分流但測試誤用簽名而真實標籤為簽署；修正後新潟2 failed（94.68s）在末段把住房費用與訂房期限當同一段，兩段各自驗證後續跑。

實際配對後計畫卡未顯示已輸入IELTS7：NCU沒有统一母校英語分數門檻，顯示誤依門檻是否存在丟失檢定名稱。改保留NCU學生實際填入測驗／分數，仍不宣稱外校合格；API與判分未放寬。新增立即與切回母校後IELTS7可見斷言，重驗中。原文audit現在實際顯示公開摘錄隱私說明與閱讀範圍，包括新潟原4張／讀3張，避免只有JSON保留。

2026-10-08 20:44:46 UTC遇exec-server transport disconnected，立即最小healthcheck確認工作樹、HEAD1bddf5a及測試日誌保留、shell恢復。未知／中斷測試不算通過。同候選SHA廣泛單元、OpenAPI、851跨校流程、既有main失敗、手機桌面與CI結果仍待重新確認；前述230項及其他歷史結果不冒稱此候選全部通過。main仍f6ad1b8、CCU0e70dbf、TKU61659fe；未合併／部署／正式DB／credentials或security變更，未外聯。

第三輪配對／收藏／文書／儲存重載手機桌面2 passed，已確認立即與切回後IELTS7顯示；同輪新潟2 failed（共200.65s）發現JPETS印尼啟動日期雖在流程／來源卻漏入生活摘要。重新讀政府現頁Q6及與host簡章比較，已補日期及差異到visa生活段，重建資料仍562／59。訂房費用／2023期限、研究科一份、IEC六份及財力一／四份斷言在兩寬均已到達，最後生活段重驗中。

新潟生活頁日期補正後手機／桌面2 passed（104.16s）。逐圖又發現生活每點重複整段年度警語、研究科一步仍重複IEC初次六件的通用說明。已改NCU生活資料保留完整section.summary／coverage_note一次，具體points不再逐項重複同一警語；學生摘要與原始audit年度仍保留。新潟14個自訂stage各給明確details，不將IEC六件或財力包說明塞入研究科基本表步驟；其他未設定details的本校既有步驟保持舊值。新潟browser增加研究科步驟不含IEC六件、生活費用無重複警語、原件4／讀3說明真實可見斷言與位置截圖，重验中。沒有改其他校資料或共用API schema。

生活與stage細分後新潟手機／桌面2 passed（88.26s）；來源說明避免重複後再2 passed（87.41s），兩張原件4／讀3說明均實際可見，六張原文／研究科／住房與六張匹配／比較／日期欄截圖已逐圖檢視並追蹤。完整同SHA四module、跨校共用與50項browser仍待候選檢查點執行，不把這些preview數字冒稱全部驗收。最新唯讀fetch main f6ad1b8、CCU0e70dbf、TKU61659fe，各14共享交集。九州工業下一批18來源暫存/tmp並正在讀，不計本輪562／59。


## 九州工業與冷啟動效能修正（新候選驗證中）

新增85筆來源後公開host／home紀錄647、讀取錯誤92；人工60筆全部partial、154項未逐欄整理、0項116全17欄核准。Drive459取得不變，新增九工大未標年一頁原生全文已讀至18；舊JLPT N1／N2 level及只有Space Systems碩士英授說法隔離，未核116統一門檻。

逐讀九工大2026留學生手冊66頁原生全文，另視覺核PDF12、13、34、35、52、54、56、58、63。三校區／學制分開；[2026工學府手冊](https://www.tobata.kyutech.ac.jp/wp-content/uploads/2026/03/binran2026.pdf)170頁只讀145–148交流規則，飯塚UG274頁只讀242–245、Grad150頁只讀117–120，範圍／未讀頁明示在UI來源詳情。未將學位30學分、正規生年級、短期十四天或一般出國程序當中央交換門檻。

交流規則第11條初次指定願書／成績（影本可）／母校校長或學部長推薦三類；短期訪問可省成績，不能套一學期。第12條錄取後誓約書另段。到校五類護照／在留卡／保險資格確認書／存摺／連絡票與僅Special Auditing Students的履修票分開，承辦留影本不推學生各一份。八個流程stage與13項明示文件條件已接文件中心；所有身分、當期空白表及適用仍待兩校確認，錄取／住校狀態不自动判適用。home七項與generic host空清單保持分開。

2026工學府後期六頁課表及SEIC一頁原生全文、第一頁原圖核授課支援Level0–6，並非CEFR或語檢最低分；非SEIC Advanced Ceramics亦Level5。PBL／RSM、先備／抽籤、教師／協議修課權分開。公開syllabus匿名正常TLS搜尋26470831的一門結果原生全文已讀，單門完整syllabus未讀；browser憑證錯誤未解除。六頁指南全部原生／視覺讀，但2025範例截圖不當2027课單。若松local406與web工具可讀的選定原文分列，沒有原件SHA或完整視覺表格就不称全表核完。

2026秋GCC兩頁與一檔兩表Word已讀；7/31 16:00日本時間截止已過，住宿一年／degree年級／六次共同學習與短期客廳臨時床分开，不保證中央有個人房。手冊與網頁交流會館新舊、校區租價矛盾保留；7000是有條件住房減免額，不是全體租金。第17條交流身分免検定／入學費與外國大學學費依協議免除分開，中央校名「國立」不當日本國立豁免。

保險2026七頁全視覺核摘要，沒有假稱原生契約全文或完整Disclosure Statement已取得；Type D期間與保費、國保／學研災先決、正規新生Futai強制範圍分列，未套全部非學位生。北九州10/6國保正文保留MyNumber可選／資格確認書與單張資格資訊通知不能就醫；飯塚舊四機場段隔離，現行ISA403沒有冒充新版。FY2026年金17920與手冊FY2025 17510分开，一般免除須申請批准。到校／14日住址登記／交通折扣身分／退租至少一月參考／離境與成績報告均接生活及流程；2027个人接收、COE財力、期限／空白包仍是具體未取得項。

原候選`ded2ed1a`的236中央、158共用pass／2skip、已知10fail與browser49／50（新潟390預設5秒未完成）原始manifest、JUnit、完整失敗log、開始／結束SHA與乾淨工作樹及76張截圖已用證據專用`eb0b610`公開保存：[同SHA原始證據](https://github.com/blizzard-new/abroad/tree/eb0b610604499da9ca29884830fa0c85522aab33/docs/ncu-test-evidence/ded2ed1)。這不是在eb0b610重測的結果。獨立乾淨ded2ed1三轮冷啟動保留原5秒测试全部通過；流程後端0.81–1.30秒、發請求到DOM完成1.95–3.39秒，原首次失敗沒有timing，不能斷言唯一因果。

另重現三個併發冷啟動請求把同一1065筆流程快取各建一次，耗10–11秒；修正後同簽章只建一次、初測2.8秒，原5秒斷言保留。新候選還须在相同SHA再量測／完整必要回歸／實際browser，沒有只拉長timeout冒稱效能修好。不同簽章、各校override、資料更新及解析失敗後重讀保持原語義。最新唯讀main f6ad1b8、CCU0e70dbf、TKU61659fe，兩分支各14共檔整合點，沒有覆寫／合併他校。

這批目前是工作樹資料與適配；必要新候選檢查、CI狀態與提交SHA另以原始證據報告。其他154項仍可查，並非外部阻塞；不得用這次推送代稱完整中央交付，也不授權merge／deploy／正式DB。

工作樹預驗：九工大12項API／來源／九組條件12 passed（15.99s）、共用目錄快取6 passed（8.80s）、手機390／桌面1440九工大2 passed（108.04s）；六張內容截圖已逐圖檢視。這些不是後述新候選SHA完整結果。舊ded2ed1對同併發測試確實讀12次／預期4次，log與JUnit保留；為避免與browser搶資源停止該額外程序，process exit130另列，不能當完整測試執行。最後候選全部必要回歸依序執行，原新潟預設5秒不變。


## 北海道兩協議候選映射（仍partial，待同SHA必要驗證）

新增93筆公開來源紀錄；最新總數740／97目前讀取錯誤，Drive19份有SHA相符全文閱讀紀錄。院級與校級兩筆已人工映射，但都不是116當期核准，總數62 partial／214，152項尚可續查，0 full116。

- 院級：2026/9/1北海道協議PDF7列中央工／理學院與北大相應單位、A／S／I、2018/2/5。Polar Institute對Arctic Research Center的2024協議僅A，不能當同一交換名額。校級列表另列NCU2025/8/8及學生交換標記；兩種協議／中央舊quota不合併。
- HUSTEP只全日制UG、到校前兩年及GPA3/4同等，TOEFL79／IELTS6.5、CEFR C1可能接受，January2028採4.5為host原文政策，未硬換算。JLCSP只校級日語／文化主修UG非大一，申請N3同等；MEXT N2／年齡是獎學金條件。SA UG／Grad專業課與SRS Grad研究無學分分開。
- 院級9 stages／17條件文件；校級13 stages／35條件文件。HUSTEP學生6／母校4、JLCSP學生5／母校3、SA／SRS一般7、PSS獨立6項（含一般可選推薦及條件獎學金）、母校提名、另email COE、個人JPETS、宿舍／保險／到校／離校各自獨立。未核當期仍全部needs_confirmation、正式下載封鎖；錄取／住校不自動判全必繳。
- SA／SRS最新2026/8版2027春提名9/25已過、申請11/13；HUSTEP／JLCSP春10/23，JLCSP明示JST，未造23:59。全部是舊／相鄰年度，不建立116提醒；2027秋／2028春包未取得與官方尚未公告分開。
- 已讀2026宿舍日英兩工作表與2026/7寢具5頁：押金50000、季節能源／清掃另付、房型及性別範圍；北23短日額JA806／EN807、寢具處理費日中含稅4000／EN4000＋稅矛盾保留。私人保證／火災與賠償保險另核；一般mid-Jan／mid-Jul不是programdeadline。
- 國保資格確認書／MyNumber、HUSTEP三保險mandatory與一般生活頁recommended分开；FY2026年金17920仅當年參考，20–59及減免需核准。2025到校銀行指南北洋>6月、郵局app剩餘>3月／16歲／無存摺与紙本窗口不同；不排除全部五個月交換。2021郵局保費、2019舊卡制、一般degree學費不当交換116報價。
- 原件視覺25頁已保存[SHA／頁碼對照](ncu-source-evidence/hokkaido-review-manifest.json)。JLCSP在學PDF只有影像，原生空頁保留且選定欄位人工轉錄，不稱OCR全文。JLCSP guide11頁、銀行／區役所文件及兩個Study Plan原生實讀；PSS資訊科学院Word已讀，但部局與交換適用須核。
- PSS公開指引有交換選項，限實際支援部局；HTTP入口只unsupported browser錯誤且錯置京都信箱、ChromiumTLS失敗，沒有繞過或登入。ISA正常HTTP403與HU舊年金404保留，年金另循政府現行頁取得。不能把故障或403稱登入限定／官方未公告。
- 仍可獨立查：HUSTEP83頁syllabus只讀PDF1–4，其餘79頁未詳讀；協議16頁只讀PDF7、其餘15頁未讀。原文與閱讀範圍在實際來源稽核顯示，未讀頁隔離問答索引。最新接收包、宿舍時限、互免條款與個人居留／JPETS為具體待取得項，不代稱全部外部阻塞。

前一實作SHA `9671a106`已完成248 NCU pass、164 shared pass／2skip、52 browser pass與三輪原5秒冷測；證據專用`eeade3d1`保存[原始manifest／JUnit／cold reports](ncu-test-evidence/9671a106/README.md)。必要舊10 fail、quality failure／0jobs與資料門檻保留；CI runner.temp語法由淡江任務最小修正，NCU沒有重複改共用workflow。這些測試不能改標本次北海道新候選SHA；提交後另做固定SHA必要驗證。

北海道預驗紀錄：新23項API／來源／18組身分與住房條件第一版19 passed／4 failed（測試誤把既有agreement_only寫needs_confirmation及生活摘要當完整guide），修正檢查實際API後23 passed；browser初版2 passed／2 failed發現流程只有名稱／簽章而漏表格連結。已限NCU補官方參考表格連結，當期適用警語及正式下載封鎖不變，第二版4 passed（144.78s）。兩次原始失敗未抹除。畫面另顯示生活每欄重複全校93來源，改NCU builder依逐欄refs供連結，到校段亦只列arrival已查來源；全部原件仍保留在來源稽核。最後版本提交後以新SHA再跑，不將preview改標提交結果。

2026-10-08 23:18 UTC唯讀fetch：main `f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59`、CCU `0e70dbf29d0830ed3733c46090d5b7126689b958`、TKU `61659fe12cf5bb5f3fed2502f112039c7f8abd92`。新增NCU builder是獨立檔；共用app.js的表格參考連結只對NCU workflow啟用，其餘母校渲染不加連結。仍須按兩分支最新14共檔逐段整合；沒有合併、覆蓋或重複改TKU正在處理的CI workflow。
