# 中正與長庚實際 API／逐校功能對照（第二十三輪，2026-10-08）

由 `scripts/build_ccu_functional_parity.py` 逐校讀取公開 API；完整原文、URL、實體頁、年度、日期及 hash 保存在 `official_data/ccu/functional-parity.json`。非空值只表示可呈現，不等於當期規定完整。

最新 main 為 `f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59`。長庚原始154流程分為77筆115年published與77筆116年legacy；無年度API選取116 legacy，指定115才取得77 published。中正55筆均legacy／official_partial。

| API功能 | 長庚無年度 | 中正 |
| --- | ---: | ---: |
| Dashboard條目 | 77 | 104 |
| 目的地指南 | 77 | 55 |
| 指南：city | 77 | 55 |
| 指南：housing_summary | 77 | 55 |
| 指南：cost_summary | 77 | 55 |
| 指南：transport_summary | 77 | 53 |
| 指南：campus_life_summary | 77 | 55 |
| 指南：guide_photos | 0 | 0 |
| 指南：first_72_hours | 0 | 0 |
| 指南：packing_from_taiwan | 0 | 0 |
| 指南：buy_after_arrival | 0 | 0 |
| 合作校：website | 77 | 55 |
| 合作校：location | 77 | 55 |
| 合作校：colleges | 77 | 23 |
| 合作校：degree_levels | 77 | 29 |
| 合作校：location_with_city | 47 | 55 |
| 合作校：location_with_source | 47 | 55 |
| 可確定資格：colleges | 77 | 3 |
| 可確定資格：degree_levels | 77 | 10 |
| 流程文件：requirements | 1469 | 1172 |
| 流程文件：requirements_with_form | 77 | 140 |
| 流程文件：schools_with_requirements | 77 | 55 |
| 流程文件：schools_with_signature_detail | 3 | 55 |

長庚115 published另有1238項文件、0 form URL及3校簽章細節；不得混用116 legacy基準。中正1172項包含母校通用準備，不等於32校237項外校實讀要求；237項均partial_not_exhaustive，57附條件，28個已取得且hash核實的官方文件直連包含指引，並非全是空白表。慶熙新增7個到校後ARC項目，政府整合表2022.4.12修訂不是2027交換初次申請表。57條件項不能一律套所有人。

中正55筆網站／校址有來源、53筆交通和55筆生活有呈現；年度、身分與校區核實狀態另列，座標均pending。學制29筆非空、可確定10；學院23筆非空、可確定3，待核資料不加符合分或硬性排除。名古屋教育／法學學制必須配對，法學限碩士。兩校照片、72小時、行李與抵達採購均0，不列成中正單方缺口。

| 55×17＝935海外欄位 | 數量 |
| --- | ---: |
| 核 | 304 |
| 待 | 331 |
| 舊 | 20 |
| 缺 | 208 |
| 矛 | 71 |
| 未公告 | 1 |

39校至少一項當期外校事實，0校17欄全當期、0校完整host文件集合；`functional_parity_complete=false`。只有HUFS到校前TB窗口是官方明示未公告；其他未查得新版保留尚未核實。

| 7類基本資料 | 核 | 待 | 舊 | 缺 |
| --- | ---: | ---: | ---: | ---: |
| city | 38 | 14 | 3 | 0 |
| location | 38 | 14 | 3 | 0 |
| website | 55 | 0 | 0 | 0 |
| degree_levels | 9 | 19 | 0 | 27 |
| colleges | 3 | 20 | 0 | 32 |
| transport | 17 | 30 | 6 | 2 |
| campus_life | 18 | 29 | 8 | 0 |

| 中正PDF頁 | 學校／計畫 | 海外核／待／缺／矛／舊 | 城市／交通／生活 | 個別host文件／階段 |
| ---: | --- | --- | --- | --- |
| 10 | Beijing Normal University 北京師範大學 | 12/1/4/0/0 | 核/舊/舊 | 6／{"student_application": 6} |
| 16 | Chongqing University 重慶大學 | 0/9/7/0/1 | 核/舊/舊 | 0／{} |
| 23 | Xiamen University 廈門大學 | 0/13/4/0/0 | 核/待/待 | 4／{"conditional_program": 4} |
| 24 | Tianjin University 天津大學 | 8/1/6/2/0 | 核/核/舊 | 8／{"student_application": 7, "post_offer": 1} |
| 26 | Northeast Normal University 東北師範大學 | 0/15/2/0/0 | 待/待/待 | 0／{} |
| 27 | University of Electronic Science and Technology of China 電子科技大學 | 9/2/5/1/0 | 核/舊/待 | 8／{"student_application": 7, "post_offer": 1} |
| 29 | Central China Normal University 華中師範大學 | 11/2/4/0/0 | 核/核/核 | 8／{"student_application": 8} |
| 32 | Ryukoku University 龍谷大學 | 10/1/1/5/0 | 核/核/核 | 12／{"student_application": 10, "after_dorm_assignment": 2} |
| 33 | Chiba University of Commerce 千葉商科大學 | 0/11/4/2/0 | 核/待/待 | 0／{} |
| 34 | Nagoya University 名古屋大學 | 14/1/0/2/0 | 待/核/待 | 10／{"student_application": 10} |
| 35 | Tohoku University 東北大學 | 4/9/2/1/1 | 待/待/待 | 0／{} |
| 37 | Hokkaido University 北海道大學 | 12/3/0/2/0 | 核/核/待 | 9／{"conditional_program": 9} |
| 39 | Tokiwa University 常磐大學 | 0/3/4/0/10 | 舊/待/舊 | 0／{} |
| 42 | Dong-A University 東亞大學 | 0/5/9/2/1 | 核/舊/待 | 0／{} |
| 43 | Pusan National University 釜山國立大學 | 14/1/2/0/0 | 核/核/核 | 8／{"student_application": 7, "post_offer": 1} |
| 45 | Kyung Hee University 慶熙大學 | 10/4/0/3/0 | 核/核/核 | 21／{"student_application": 9, "second_submission": 3, "after_dorm_assignment": 2, "post_offer": 7} |
| 47 | Hankuk University of Foreign Studies 韓國外國語大學 | 11/3/0/2/0 | 核/待/核 | 12／{"student_application": 9, "after_dorm_assignment": 1, "after_application": 2} |
| 48 | Seoul National University of Science and Technology 國立首爾科技大學 | 13/2/1/1/0 | 待/待/核 | 12／{"student_application": 7, "second_submission": 3, "conditional_program": 2} |
| 49 | Sungshin Women's University 誠信女子大學 | 12/0/2/3/0 | 核/核/核 | 9／{"student_application": 9} |
| 50 | Chung Ang University 中央大學 | 0/17/0/0/0 | 待/待/待 | 0／{} |
| 52 | Gachon University 嘉泉大學 | 3/11/1/2/0 | 待/待/待 | 0／{} |
| 53 | ChungNam National University 忠南大學 | 13/3/0/1/0 | 待/待/待 | 9／{"student_application": 4, "after_application": 2, "post_offer": 3} |
| 54 | Kyungsung University 慶星大學 | 8/2/5/2/0 | 核/核/核 | 0／{} |
| 58 | Thammasat University 國立法政大學 | 0/14/2/1/0 | 待/待/待 | 0／{} |
| 61 | King Mongkut’s University of Technology Thonburi 蒙庫國王科技大學 | 0/13/2/2/0 | 待/待/待 | 0／{} |
| 65 | Universitas Bunda MuliaUK 慈育大學 | 0/11/6/0/0 | 核/待/待 | 0／{} |
| 67 | Ho Chi Minh City University of Technology HCMUT胡志明市國家大學所屬百科大學 | 14/1/2/0/0 | 核/核/核 | 9／{"student_application": 7, "nomination": 1, "post_offer": 1} |
| 68 | Ho Chi Minh City University of Technology and Engineering HCMUTE胡志明科技工程大學 | 11/1/4/1/0 | 核/待/舊 | 7／{"nomination": 7} |
| 71 | Dong Nai Technology University (DNTU) 同奈科技大學 | 0/0/17/0/0 | 待/缺/待 | 0／{} |
| 73 | Chitkara University 吉特卡拉大學 | 4/5/7/1/0 | 核/核/待 | 0／{} |
| 74 | Saintigits Group of Institutions 聖基茲工學院 | 0/1/16/0/0 | 核/待/待 | 0／{} |
| 77 | Vel Tech Rangarajan Dr.Sagunthala R&D Institute of Science andTechnology 維爾特克科技大學 | 0/13/2/2/0 | 核/待/待 | 0／{} |
| 80 | Presidency University 總統大學 | 1/9/2/1/4 | 核/待/待 | 6／{"student_application": 6} |
| 83 | Mapua University 瑪普爾大學 | 7/2/6/2/0 | 核/核/核 | 7／{"student_application": 7} |
| 85 | Bordeaux Montaigne University 蒙田波爾多大學 | 3/9/3/2/0 | 核/待/待 | 0／{} |
| 86 | EPITA (School of engineering & computer science) 法國高等工程技術學院 | 9/4/2/2/0 | 核/核/核 | 9／{"student_application": 8, "post_offer": 1} |
| 87 | University of Strasbourg 史特拉斯堡大學 | 2/10/4/1/0 | 待/待/待 | 0／{} |
| 88 | Faculty of Management, Economics & Sciences (FGES) –Catholic University of Lille 法國里爾天主教大學(管理、經濟及科學學院) | 10/1/6/0/0 | 核/核/核 | 1／{"student_application": 1} |
| 89 | University of Southern Denmark 南丹麥大學 | 0/12/4/1/0 | 核/待/待 | 1／{"after_dorm_assignment": 1} |
| 95 | Adam Mickiewicz University, Poznan 亞當密砍凱維奇大學 | 2/7/5/0/3 | 核/舊/舊 | 0／{} |
| 98 | Ludwigshafen University of Business and Society 路德維希港社會應用科技大學 | 6/2/9/0/0 | 核/核/核 | 5／{"student_application": 5} |
| 99 | Friedrich Schiller Universität Jena 耶拿大學 | 9/5/0/3/0 | 舊/待/舊 | 3／{"post_offer": 3} |
| 100 | Ostfalia University of Applied Sciences 奧斯特法利亞應用科技大學 | 1/13/3/0/0 | 核/待/待 | 0／{} |
| 101 | Deggendorf Institute of Technology 德根多夫應用科技大學 | 0/12/1/4/0 | 核/待/待 | 7／{"student_application": 6, "post_offer": 1} |
| 102 | Augsburg University of Applied Sciences 奧格斯堡應用科技大學 | 7/8/2/0/0 | 核/核/核 | 10／{"student_application": 10} |
| 103 | ZHAW Zurich University of Applied Sciences-SoE 蘇黎世應用科技大學-工學院 | 0/11/4/2/0 | 核/待/待 | 0／{} |
| 104 | University of Applied Sciences and Arts Northwestern Switzerland – School of Business Fachhoschule Nordwestschweiz (FHNW) - Hochschule für Wirtschaft 西北應用科技與藝術大學 | 3/10/2/2/0 | 待/待/待 | 3／{"post_offer": 1, "student_application": 2} |
| 105 | Ankara Social Science University 土耳其安卡拉社會科技大學 | 1/11/3/2/0 | 舊/舊/舊 | 0／{} |
| 106 | Ç ukurova University 土耳其丘庫羅瓦大學 | 10/0/6/1/0 | 核/待/核 | 8／{"student_application": 8} |
| 107 | University of Pardubice 捷克巴爾杜比彩大學 | 13/0/3/1/0 | 待/待/待 | 4／{"student_application": 3, "post_offer": 1} |
| 108 | Tomas Bata University in Zlí n 托馬斯拔佳大學 | 8/3/4/2/0 | 核/待/核 | 6／{"student_application": 4, "conditional_program": 2} |
| 109 | University of West Bohemia 西波希米亞大學 | 2/12/3/0/0 | 待/待/待 | 2／{"student_application": 1, "post_offer": 1} |
| 111 | SILESIAN UNIVERSITY IN OPAVA (School of Business Administration in Karvina) 奧帕瓦西里西亞大學(管理學院) | 6/3/5/3/0 | 核/核/核 | 0／{} |
| 114 | Ø stfold University of Applied Sciences 厄斯特福德應用科學大學 | 5/7/4/1/0 | 核/待/待 | 5／{"student_application": 5} |
| 119 | Universidad Internacional 墨西哥國際大學 | 6/2/6/3/0 | 核/缺/核 | 8／{"student_application": 6, "post_offer": 2} |
