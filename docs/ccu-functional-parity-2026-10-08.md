# 中正與長庚實際 API／逐校功能對照（2026-10-08）

由 `scripts/build_ccu_functional_parity.py` 逐校讀取公開 API。完整原文、URL、PDF物理頁碼、年度、查核時間、hash、條件及文件階段保存在 `official_data/ccu/functional-parity.json`。非空值不代表當期完整申請規定。

## 實際基準

最新 main `f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59` 的長庚原始154流程＝77筆115年published＋77筆116年legacy。未指定年度API回傳77筆legacy；指定 `academic_year=115` 回傳77筆published，已以獨立main解包API重現。中正55筆維持legacy／official_partial。

| 功能／欄位 | 長庚未指定年度 API | 中正 API |
| --- | ---: | ---: |
| Dashboard條目 | 77 | 104 |
| 目的地指南 | 77 | 55 |
| city | 77 | 55 |
| transport_summary | 77 | 53 |
| campus_life_summary | 77 | 55 |
| guide_photos | 0 | 0 |
| first_72_hours | 0 | 0 |
| packing_from_taiwan | 0 | 0 |
| buy_after_arrival | 0 | 0 |
| website | 77 | 55 |
| location_with_city | 47 | 55 |
| location_with_source | 47 | 55 |
| 可確定的學術篩選：colleges | 77 | 3 |
| 可確定的學術篩選：degree_levels | 77 | 10 |
| 流程文件：requirements | 1469 | 1151 |
| 流程文件：requirements_with_form | 77 | 136 |
| 流程文件：schools_with_requirements | 77 | 55 |
| 流程文件：schools_with_signature_detail | 3 | 55 |

長庚指定115已發布基準有1238項文件、0項form URL及3校簽章細節；未指定年度116 legacy則1469項文件、77項form URL及3校簽章細節。兩個年度不得混用。中正1151項含母校通用及逐校準備要求，不可與216項已逐份實讀的host清單等同。

城市／校址55筆有來源；未標年或交換校區仍待確認；地圖經緯度全部pending。55個網站核實身分入口，不保證全站2027規定已核實。照片、抵達72小時、行李及到校採購兩校均為0。

母校第一階9類準備文件、37筆當期逐校第二階要求、29校216項外校文件分開。216項均partial_not_exhaustive；38項附條件，25個已取得且hash核實的官方文件連結可開啟，含申請指引，不全部是空白表。55流程中52筆7步驟，忠南／HUFS／首爾科技三筆8步驟。忠南／HUFS的after_application表示補件不等錄取；首爾科技三項改為中性second_submission，逐項顯示時點待確認。其他26校沒有製造完整外校清單。

待確認學院／學制的API及前端均不加符合分、不硬性排除。名古屋教育／法學以學院學制配對篩選；法學限碩士。ZHAW工學院改由母校當期p103核實。可確定學院是3筆。

HCMUT當期公開公告及Updated August 2026 factsheet一致：2026-09-30提名、2026-10-15申請；2027-01-08 orientation、01-11至06-07課程及考試。新學生申請與母校提名範本內容已讀；提名信須負責人簽名及Seal，保險copy到校前一週送。個人線上表HTTP401未讀，不冒稱文件集合完整。March版舊截止日保留參考；兩版PDF抽取出的隱藏Kyoto／CoE文字經實際p4畫面排除，不能当作官方簽證政策。

首爾科技新版p3／p7：非OECD在學／成績須依國別認證；銀行列本人名下USD6000一期／12000一年及非OECD正本，未列銀行認證。住宿條件、第一次與第二次送件分開。

## 欄位核實狀態

| 17類海外接收欄位（55×17＝935） | 數量 |
| --- | ---: |
| 核 | 310 |
| 缺 | 212 |
| 待 | 327 |
| 舊 | 20 |
| 矛 | 65 |
| 未公告 | 1 |

39校至少一項當期外校事實已核實；0校17項全核實、0校完整外校文件集合，`functional_parity_complete=false`。僅HUFS到校前TB窗口是官方明示尚未公告。

| 7類基本資料 | 當期／身分已核實 | 年度或條件待確認 | 舊參考 | 未載 |
| --- | ---: | ---: | ---: | ---: |
| city | 38 | 14 | 3 | 0 |
| location | 38 | 14 | 3 | 0 |
| website | 55 | 0 | 0 | 0 |
| degree_levels | 9 | 19 | 0 | 27 |
| colleges | 3 | 19 | 0 | 33 |
| transport | 17 | 30 | 6 | 2 |
| campus_life | 18 | 29 | 8 | 0 |

## 55筆逐校核對

核／待／舊／缺／矛分別表示verified_current／needs_confirmation／reference_only／missing／conflict。所有母校當期收件已截止；3筆名額空白仍待確認。PDF頁是中正2026.09.17學校資訊的物理頁；host附件頁另存證據。

| 中正PDF頁 | 合作校／計畫 | 外校17項核／待／缺／矛／舊 | 城市／交通／生活 | 外校個別文件數／階段 |
| ---: | --- | --- | --- | --- |
| 10 | Beijing Normal University 北京師範大學 | 12/1/4/0/0 | 核/舊/舊 | 6／student_application:6 |
| 16 | Chongqing University 重慶大學 | 0/9/7/0/1 | 核/舊/舊 | 0／未建個別外校清單 |
| 23 | Xiamen University 廈門大學 | 0/13/4/0/0 | 核/待/待 | 4／conditional_program:4 |
| 24 | Tianjin University 天津大學 | 8/1/6/2/0 | 核/核/舊 | 8／student_application:7、post_offer:1 |
| 26 | Northeast Normal University 東北師範大學 | 0/15/2/0/0 | 待/待/待 | 0／未建個別外校清單 |
| 27 | University of Electronic Science and Technology of China 電子科技大學 | 9/2/5/1/0 | 核/舊/待 | 8／student_application:7、post_offer:1 |
| 29 | Central China Normal University 華中師範大學 | 11/2/4/0/0 | 核/核/核 | 8／student_application:8 |
| 32 | Ryukoku University 龍谷大學 | 11/1/1/4/0 | 核/核/核 | 10／student_application:10 |
| 33 | Chiba University of Commerce 千葉商科大學 | 0/11/4/2/0 | 核/待/待 | 0／未建個別外校清單 |
| 34 | Nagoya University 名古屋大學 | 14/1/0/2/0 | 待/核/待 | 10／student_application:10 |
| 35 | Tohoku University 東北大學 | 4/9/2/1/1 | 待/待/待 | 0／未建個別外校清單 |
| 37 | Hokkaido University 北海道大學 | 12/3/0/2/0 | 核/核/待 | 9／conditional_program:9 |
| 39 | Tokiwa University 常磐大學 | 0/3/4/0/10 | 舊/待/舊 | 0／未建個別外校清單 |
| 42 | Dong-A University 東亞大學 | 0/5/9/2/1 | 核/舊/待 | 0／未建個別外校清單 |
| 43 | Pusan National University 釜山國立大學 | 14/1/2/0/0 | 核/核/核 | 8／student_application:7、post_offer:1 |
| 45 | Kyung Hee University 慶熙大學 | 14/2/1/0/0 | 核/核/核 | 11／student_application:9、post_offer:2 |
| 47 | Hankuk University of Foreign Studies 韓國外國語大學 | 11/3/0/2/0 | 核/待/核 | 12／student_application:9、after_dorm_assignment:1、after_application:2 |
| 48 | Seoul National University of Science and Technology 國立首爾科技大學 | 13/2/1/1/0 | 待/待/核 | 12／student_application:7、second_submission:3、conditional_program:2 |
| 49 | Sungshin Women's University 誠信女子大學 | 12/0/2/3/0 | 核/核/核 | 9／student_application:9 |
| 50 | Chung Ang University 中央大學 | 0/17/0/0/0 | 待/待/待 | 0／未建個別外校清單 |
| 52 | Gachon University 嘉泉大學 | 3/11/1/2/0 | 待/待/待 | 0／未建個別外校清單 |
| 53 | ChungNam National University 忠南大學 | 13/3/0/1/0 | 待/待/待 | 9／student_application:4、after_application:2、post_offer:3 |
| 54 | Kyungsung University 慶星大學 | 8/2/5/2/0 | 核/核/核 | 0／未建個別外校清單 |
| 58 | Thammasat University 國立法政大學 | 0/14/2/1/0 | 待/待/待 | 0／未建個別外校清單 |
| 61 | King Mongkut’s University of Technology Thonburi 蒙庫國王科技大學 | 0/13/2/2/0 | 待/待/待 | 0／未建個別外校清單 |
| 65 | Universitas Bunda MuliaUK 慈育大學 | 0/11/6/0/0 | 核/待/待 | 0／未建個別外校清單 |
| 67 | Ho Chi Minh City University of Technology HCMUT胡志明市國家大學所屬百科大學 | 14/1/2/0/0 | 核/核/核 | 9／student_application:7、nomination:1、post_offer:1 |
| 68 | Ho Chi Minh City University of Technology and Engineering HCMUTE胡志明科技工程大學 | 11/1/4/1/0 | 核/待/舊 | 7／nomination:7 |
| 71 | Dong Nai Technology University (DNTU) 同奈科技大學 | 0/0/17/0/0 | 待/缺/待 | 0／未建個別外校清單 |
| 73 | Chitkara University 吉特卡拉大學 | 4/5/7/1/0 | 核/核/待 | 0／未建個別外校清單 |
| 74 | Saintigits Group of Institutions 聖基茲工學院 | 0/1/16/0/0 | 核/待/待 | 0／未建個別外校清單 |
| 77 | Vel Tech Rangarajan Dr.Sagunthala R&D Institute of Science andTechnology 維爾特克科技大學 | 0/13/2/2/0 | 核/待/待 | 0／未建個別外校清單 |
| 80 | Presidency University 總統大學 | 1/9/2/1/4 | 核/待/待 | 6／student_application:6 |
| 83 | Mapua University 瑪普爾大學 | 7/2/6/2/0 | 核/核/核 | 7／student_application:7 |
| 85 | Bordeaux Montaigne University 蒙田波爾多大學 | 3/9/3/2/0 | 核/待/待 | 0／未建個別外校清單 |
| 86 | EPITA (School of engineering & computer science) 法國高等工程技術學院 | 10/3/3/1/0 | 核/核/核 | 7／student_application:7 |
| 87 | University of Strasbourg 史特拉斯堡大學 | 2/10/4/1/0 | 待/待/待 | 0／未建個別外校清單 |
| 88 | Faculty of Management, Economics & Sciences (FGES) –Catholic University of Lille 法國里爾天主教大學(管理、經濟及科學學院) | 10/1/6/0/0 | 核/核/核 | 1／student_application:1 |
| 89 | University of Southern Denmark 南丹麥大學 | 0/12/4/1/0 | 核/待/待 | 0／未建個別外校清單 |
| 95 | Adam Mickiewicz University, Poznan 亞當密砍凱維奇大學 | 2/6/6/0/3 | 核/舊/舊 | 0／未建個別外校清單 |
| 98 | Ludwigshafen University of Business and Society 路德維希港社會應用科技大學 | 6/2/9/0/0 | 核/核/核 | 5／student_application:5 |
| 99 | Friedrich Schiller Universität Jena 耶拿大學 | 9/5/0/3/0 | 舊/待/舊 | 0／未建個別外校清單 |
| 100 | Ostfalia University of Applied Sciences 奧斯特法利亞應用科技大學 | 1/13/3/0/0 | 核/待/待 | 0／未建個別外校清單 |
| 101 | Deggendorf Institute of Technology 德根多夫應用科技大學 | 0/13/1/3/0 | 核/待/待 | 7／student_application:6、post_offer:1 |
| 102 | Augsburg University of Applied Sciences 奧格斯堡應用科技大學 | 7/8/2/0/0 | 核/核/核 | 10／student_application:10 |
| 103 | ZHAW Zurich University of Applied Sciences-SoE 蘇黎世應用科技大學-工學院 | 0/10/5/2/0 | 核/待/待 | 0／未建個別外校清單 |
| 104 | University of Applied Sciences and Arts Northwestern Switzerland – School of Business Fachhoschule Nordwestschweiz (FHNW) - Hochschule für Wirtschaft 西北應用科技與藝術大學 | 3/10/2/2/0 | 待/待/待 | 0／未建個別外校清單 |
| 105 | Ankara Social Science University 土耳其安卡拉社會科技大學 | 1/11/3/2/0 | 舊/舊/舊 | 0／未建個別外校清單 |
| 106 | Ç ukurova University 土耳其丘庫羅瓦大學 | 10/0/6/1/0 | 核/待/核 | 8／student_application:8 |
| 107 | University of Pardubice 捷克巴爾杜比彩大學 | 13/0/3/1/0 | 待/待/待 | 4／student_application:3、post_offer:1 |
| 108 | Tomas Bata University in Zlí n 托馬斯拔佳大學 | 8/3/4/2/0 | 核/待/核 | 6／student_application:4、conditional_program:2 |
| 109 | University of West Bohemia 西波希米亞大學 | 2/12/3/0/0 | 待/待/待 | 2／student_application:1、post_offer:1 |
| 111 | SILESIAN UNIVERSITY IN OPAVA (School of Business Administration in Karvina) 奧帕瓦西里西亞大學(管理學院) | 6/3/5/3/0 | 核/核/核 | 0／未建個別外校清單 |
| 114 | Ø stfold University of Applied Sciences 厄斯特福德應用科學大學 | 5/7/4/1/0 | 核/待/待 | 5／student_application:5 |
| 119 | Universidad Internacional 墨西哥國際大學 | 6/2/6/3/0 | 核/缺/核 | 8／student_application:6、post_offer:2 |

## 第十七輪適配與逐校缺口

Augsburg 10項、Ludwigshafen 5項與廈門台港澳4項各自保留適用年度；Ludwigshafen當期母校p98證件照／護照與未標年程序分開。未標年可讀清單可查，完整度仍partial。Augsburg LA正文可讀，原檔重試429，顯示待核實來源、不假稱下載成功。Ludwigshafen LA／住宿表原檔可開，模板的2027適用與完整個人online欄位仍待確認。

HCMUTE2027 factsheet五mandatory／兩optional均由母校整包彙整email提名；文件階段移至nomination。CS1停車／公車鼓勵僅一般通勤，不變成機場接送。DNTU由乾淨獨立官方圖書館列一般服務及先訓練啟用；2027交換生資格未知。2026-01-19生效正文08:00–17:00與頁尾07:30–17:00差異另記，不把頁尾当確定開館時間。

逐校學院／學制／文件／交通／生活缺口、已查來源URL及實際HTTP／內容狀態、未映射附件和未請求的實際href見[缺口清冊](ccu-remaining-gaps-2026-10-08.md)及official_data/ccu/remaining-gaps.json。候選href沒有宣称已驗證可開啟，所有校public_sources_exhausted=false。

## 尚待補查與實際限制

公開查核缺口：交通2校（DNTU、UNINTER）、生活0校未載；學制32校、學院40校未載；其餘無年份／跨校區來源仍待確認適用性。未把公開缺值歸為只能聯絡學校。

697個唯一來源對應697請求（本輪16次網路候選取得＋2份既有母校PDF重新實讀紀錄），89個可解析合作校附件；81筆fetch_failed，另7challenge、7空回應、2captcha及10不相關內容異常不採作政策。UNINTER前輪指南及本輪三個替代官方入口／指南皆503、HCMUT個人表兩次401；匿名瀏覽器遇憑證錯誤，改讀可匿名且正常TLS驗證的官方公開JSON，未登入或關閉憑證驗證。

最新測試及套件證據見ccu-validation-2026-10-08/seventeenth-*。保留第十六輪來源與測試歷史；本輪新增名古屋配對篩選及未標年表格警示，下載回放使用保存的真實官方檔案，另保存匿名來源HTTP／hash，不宣稱回放是即時外網下載。

中正母校與平台適配可用；外校完整度仍有上述缺口。未登入學校系統、提交資料、聯絡承辦、merge main或部署。

第十八輪修正真實條件表單：新增碩士／博士選項；舊研究所值可由年級細分，法學研究所未細分時保持待確認。HCMUTE第4／5步明確為母校email，不以否定句推斷online。西波希米亞路線補Florenc轉巴士／B轉C到中央車站轉火車，年度仍待確認。

第十九輪：77新來源、11新host要求、19項原文／物理頁修正。名古屋10項改為實際PDF第15頁並保留語言免附及JASSO財力適用條件；Sungshin在學證明／天津CV不捏造英文。Presidency使用3頁Inbound表而非8頁Outbound表；Pardubice住宿意向書與Pusan宿舍TB列錄取後條件。UTB四院2026/27課表中AE8SV不開、1PE3E僅Master，15是課程容量。一般目錄、2025/26手冊、2019／2022住宿指南均不升級當期申請表。

API比對更正：獨立latest-main匯入確認110端點與既有schema必填欄位相同，但6個既有schema有optional欄位／enum變更，另新增4個CCU component；完整OpenAPI不相同。以nineteenth-api-hash-proof.json取代先前完整snapshot相同的說法。

第二十輪：125份匿名取得結果，95份必要正文來源保留；27份導覽／其他範圍排除，2份實際final URL＋相同文字複查、1份同批原檔＋文字重複。109次欄位補充，HUFS兩既有宿舍文件接入實開1頁模板、學生／clinician簽日期與未年版本註記；另新增Intensive Korean申請後確認GoogleForm及DIT手冊exam grade sheet兩項条件／年度待核。宿舍表可下載不代表2027空白版已核。

HUFS一般頁的宿舍分配約1月／2月及Global付款方式差異保留conflict；未年CreditInfo的研究生12學分仍不覆蓋2027 factsheet20。DIT 09.2026手冊exchange段與既有流程單文件不同，regular degree的deadline／500EUR service fee不當交換要求；fee頁只明示交換免service，60EUR application是否免仍待核。UPCE Transport推薦四門與FEI至少80%分開，Østfold Fredrikstad／Halden、Autumn2027 elective／Spring版本分開；ZHAW Engineering本科B2／碩士C1未年要求仍待核。

本輪沒有修改共用核心、API、UI或校別adapter程式；110路徑及OpenAPI與第十九輪分支相同。對main的6個既有schema optional／enum變更及4新component仍保留於合併清冊；完整OpenAPI不相同。第二十一輪83份精確官方候選已取得並持續正文查核，不能把本輪checkpoint視為資料完整或所有來源查盡。
