# 中央116-1來源查核與平台接入（進行中）

基底為合併PR #1後的`f6ad1b8`，已確認包含臺大六項修正`daad399`。獨立worktree `/workspace/abroad-ncu`、分支`data/ncu-exchange-20261008`；已推送checkpoint `dc126d2`、`95c883a`、`2865413`、`6f2f9d1`、`dd06632`，draft [PR #4](https://github.com/blizzard-new/abroad/pull/4)。原工作目錄、中正及淡江分支未改動。本文件不宣稱中央全部外校資料完備。

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
| 有明確SHA與逐頁紀錄的全文已讀／視覺文件 | Drive附件3／3；UOS舊影像版11頁、SUFE與SHU各8頁逐頁視覺讀完；OCR僅UOS舊版 |
| 部分或全部無文字頁／字型問題 | 36份含100頁、2份字型缺字 |
| 另查公開host／home網頁 | 276筆公開頁／文件讀取紀錄（含browser選定摘錄）；44筆目前讀取錯誤分列 |
| 有外校來源的目錄項 | 211（210項有文字）；214項有任意參考來源，另3項只有其他母校官方轉載、不可冒充host官網 |
| 人工整理的host紀錄 | 44（全部partial） |
| 全部17欄完成116當期核准 | **0** |

附件取得／文字抽取不是逐欄當期查核完成。其他資料仍可繼續查；未查完的欄位不稱「官方未公告」。

[逐校逐欄CSV](../src/exchange_info/official_data/ncu/field-coverage.csv)與[完整證據／缺口JSON](../src/exchange_info/official_data/ncu/field-audit.json)包含17欄：城市／校區、抵達／日常交通、名額、學制／校區／track、語言、home文件、host文件、home截止、host截止、交換期間、課程、學費、生活費、住宿、保險、簽證、到校。JSON保留來源URL、PDF頁碼、原文、適用年份及查核日期。CSV與JSON不是全綠即完成的數字展示。

## 已確認母校規則

線上2026/11/16 09:00–12/4 12:00；學生紙本12/11 17:00交系所；系所12/18 17:00送國際處，全部臺灣時間。校內錄取公告2027/1/11 09:00。

大學部平均60、研究生70；在職專班可申請但無研修獎學金，目前大五／大六不可申請。未知學制、成績或大學部年級不回傳通過；不將GPA換算百分制。仍須系所與導師／指導教授同意、一學年成績及全程學籍，境外生／國籍限制分列。

七項home必繳文件及簽章分列於home step；外校文件放入另一host step。正式語檢影本必繳、不限級數，英檢兩年有效，不能截圖或補繳。外校語檢是另一規則；第4頁補件說明與第7頁提名前具備要求的差異保留，不取消較早的準備義務。第4頁TOEFL ITP與第6頁PBT差異亦保留。

首頁仍下載forms-2022.pdf：個資同意第1頁、家長同意第2頁、109年度範例第3頁。只使用現行表格連結，不將範例舊日期當116截止。行前兩週程序、回國一週程序、WORD心得800–1500字及至少四照片接入流程。課程兩門且一門專業課與學則兩門或六學分分別列出，採認由系所審定。

## 四十四筆人工外校整理與具體缺口

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

目前170項尚無初步人工欄位整理；已整理44項也全部partial，**214項沒有任何一項完成116當期全欄核准**。不能以中央提名步驟當host文件清單完成。211項有外校附件／網頁不表示211項全部17欄已核對。3項仍無外校來源映射；另1項只有影像、尚無可讀文字，具體項目见下列清單及CSV「其中外校來源數=0」；多數仍可繼續做官方host來源搜尋／身份與track核對，**尚非證實登入限定或官方未公告**。已取得的大陸international資料若排除Chinese nationals，另列臺灣track缺口，不能硬配。

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

西安交通新增2027春兩頁、申請／推薦DOC與母校Excel；GPA嚴格大於2.8／4.3、五項合一PDF、10/30、表頭2027卻仍2025日期範例、最低學分或門數原文均保留。DOC轉DOCX兩SHA綁定、母校Excel整筆示例移除。華中科技臺灣2027春仍計算機／集成電路暫不開放、11/3、3–6課計畫；健康報告錄取後、保單兩交件選項分開。所附2024八頁影像宣傳冊尚未視覺讀，未計已讀。天津2027春臺灣PDF與DOC確認七初次件、到校後保單、11/15與秋季標題矛盾；原先2025／港澳參考仍另存。

完整NCU／collector／completeness為80 passed、1 failed（92.67s）：HUST來源排序已因2027春新文件改變，原斷言只准第一URL是舊PDF第7頁；改驗證新來源優先且舊第7頁仍保留。修正後六項聚焦全部通過（16.10s），包含來源正反排序、實際NUIST檢索、新包及UNDIP既有條件。OpenAPI2026-10-08.4、JS syntax及diff檢查通過；既有main失敗仍按前述紀錄保留。

Chromium天津階段／文件中心2 passed、新NUIST首次因來源標題選擇器錯誤1 failed（合計78.53s）；修正為原文件實際標題後NUIST1 passed（44.86s）。[八項NUIST文件](ncu-browser-evidence/ncu-nuist-2027-documents-390.png)、[第7頁視覺摘錄](ncu-browser-evidence/ncu-nuist-2027-source-390.png)、[學校購買保險](ncu-browser-evidence/ncu-nuist-2027-life-390.png)及[天津到校後保單](ncu-browser-evidence/ncu-tju-arrival-390.png)已逐圖檢視。不是只查校數或折疊DOM。

住宿／錄取條件引擎仍是內部待實作工作，不是學校未公告或登入限制；後續實作要保持未發布流程與版本查核狀態。此checkpoint不表示完成214校全包，也不授權部署。
