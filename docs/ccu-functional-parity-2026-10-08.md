# 中正與長庚實際 API／逐校功能對照（2026-10-08）

此表由 `scripts/build_ccu_functional_parity.py` 讀取本機公開 API 產生。55 筆逐校欄位的原文、URL、PDF 頁碼、年度、查核時間、hash、條件與文件階段完整保存於 `official_data/ccu/functional-parity.json`。本表的非空值是功能呈現，不代表當期完整申請規定。

## 實際基準

最新 main `f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59` 的長庚原始流程 154 筆＝77 筆 115 年 published＋77 筆 116 年 legacy。實際未指定年度 API 回傳 77 筆 legacy，指定 `academic_year=115` 回傳 77 筆 published；以獨立 main 解包的 API 再次重現，見 `ccu-validation-2026-10-08/cgu-main-year-baseline-proof.json`。中正 55 筆維持 legacy／official_partial，未假冒發布。

| 實際功能／欄位 | 長庚 API | 中正 API |
| --- | ---: | ---: |
| Dashboard條目 | 77 | 104 |
| 目的地指南 | 77 | 55 |
| city | 77 | 54 |
| transport_summary | 77 | 45 |
| campus_life_summary | 77 | 48 |
| guide_photos | 0 | 0 |
| first_72_hours | 0 | 0 |
| packing_from_taiwan | 0 | 0 |
| buy_after_arrival | 0 | 0 |
| website | 77 | 55 |
| location_with_city | 47 | 54 |
| location_with_source | 47 | 54 |
| 可確定的學術filter：colleges | 77 | 2 |
| 可確定的學術filter：degree_levels | 77 | 8 |

城市／校址 54 筆有公開原文，1 筆未核實；55 個地圖定位物件包含 pending 缺值，沒有捏造經緯度。網站 55 筆核實身分入口，不代表全站 2027 接收規定已核實。長庚與中正的照片、抵達72小時、行李及到校採購欄均為0，不能把共同未建功能只算中正退步。

中正的母校第一階9類個別準備文件、37筆當期母校逐校第二階要求及23校175项獨立查核外校文件分開。175項均標 `partial_not_exhaustive`，包含 student_application、post_offer、conditional_program；簽章、份數、正本要求及可開啟模板只依原文設值。其他32校沒有製造外校逐項清單。

## 欄位核實狀態

| 17類海外接收欄位（55×17＝935） | 數量 |
| --- | ---: |
| 核 | 310 |
| 缺 | 229 |
| 待 | 314 |
| 舊 | 20 |
| 矛 | 61 |
| 未公告 | 1 |

39校至少一項當期外校事實已核實，0校17項全核實，0校完整外校申請文件清單；`functional_parity_complete=false`。一般無年份頁、舊指南、技術失敗、登入／提名後個人資料及實際矛盾分開。只有HUFS到校前TB檢查窗口一項是官方明示尚未公告。

| 7類基本資料 | 當期／當前身分已核實 | 年度或条件待確認 | 舊參考 | 未載 |
| --- | ---: | ---: | ---: | ---: |
| city | 38 | 13 | 3 | 1 |
| location | 38 | 13 | 3 | 1 |
| website | 55 | 0 | 0 | 0 |
| degree_levels | 7 | 14 | 0 | 34 |
| colleges | 1 | 10 | 0 | 44 |
| transport | 17 | 23 | 5 | 10 |
| campus_life | 17 | 26 | 5 | 7 |

## 55筆逐校核對

核＝verified_current；待＝needs_confirmation；舊＝reference_only；缺＝missing；矛＝conflict。城市／交通／生活欄以狀態呈現，不把非空當作核實。所有母校當期收件均已截止；3筆空白名額仍是待確認。PDF頁碼對應中正2026.09.17的121頁學校資訊，並非host附件頁碼。

| 中正PDF頁 | 合作校／計畫 | 外校17項核／待／缺／矛／舊 | 城市／交通／生活 | 外校個別文件數／階段 |
| ---: | --- | --- | --- | --- |
| 10 | Beijing Normal University 北京師範大學 | 12/1/4/0/0 | 核/舊/舊 | 6／student_application:6 |
| 16 | Chongqing University 重慶大學 | 0/9/7/0/1 | 核/舊/缺 | 0／未建個別外校清單 |
| 23 | Xiamen University 廈門大學 | 0/13/4/0/0 | 核/待/缺 | 0／未建個別外校清單 |
| 24 | Tianjin University 天津大學 | 8/1/6/2/0 | 核/核/缺 | 8／student_application:7, post_offer:1 |
| 26 | Northeast Normal University 東北師範大學 | 0/15/2/0/0 | 待/缺/缺 | 0／未建個別外校清單 |
| 27 | University of Electronic Science and Technology of China 電子科技大學 | 9/2/5/1/0 | 核/缺/待 | 8／student_application:7, post_offer:1 |
| 29 | Central China Normal University 華中師範大學 | 11/2/4/0/0 | 核/核/核 | 8／student_application:8 |
| 32 | Ryukoku University 龍谷大學 | 11/1/1/4/0 | 核/核/核 | 10／student_application:10 |
| 33 | Chiba University of Commerce 千葉商科大學 | 0/11/4/2/0 | 核/待/待 | 0／未建個別外校清單 |
| 34 | Nagoya University 名古屋大學 | 14/1/0/2/0 | 待/核/待 | 10／student_application:10 |
| 35 | Tohoku University 東北大學 | 4/9/2/1/1 | 待/待/待 | 0／未建個別外校清單 |
| 37 | Hokkaido University 北海道大學 | 12/3/0/2/0 | 核/核/待 | 9／conditional_program:9 |
| 39 | Tokiwa University 常磐大學 | 0/3/4/0/10 | 舊/待/舊 | 0／未建個別外校清單 |
| 42 | Dong-A University 東亞大學 | 0/5/9/2/1 | 核/舊/待 | 0／未建個別外校清單 |
| 43 | Pusan National University 釜山國立大學 | 14/1/2/0/0 | 核/核/核 | 7／student_application:7 |
| 45 | Kyung Hee University 慶熙大學 | 14/2/1/0/0 | 核/核/核 | 11／student_application:9, post_offer:2 |
| 47 | Hankuk University of Foreign Studies 韓國外國語大學 | 13/2/1/0/0 | 核/待/核 | 11／student_application:9, post_offer:2 |
| 48 | Seoul National University of Science and Technology 國立首爾科技大學 | 12/4/1/0/0 | 待/缺/核 | 10／student_application:6, post_offer:4 |
| 49 | Sungshin Women's University 誠信女子大學 | 12/0/2/3/0 | 核/核/核 | 9／student_application:9 |
| 50 | Chung Ang University 中央大學 | 0/17/0/0/0 | 待/待/待 | 0／未建個別外校清單 |
| 52 | Gachon University 嘉泉大學 | 3/11/1/2/0 | 待/待/待 | 0／未建個別外校清單 |
| 53 | ChungNam National University 忠南大學 | 13/3/0/1/0 | 待/待/待 | 9／student_application:4, post_offer:5 |
| 54 | Kyungsung University 慶星大學 | 8/2/5/2/0 | 核/核/核 | 0／未建個別外校清單 |
| 58 | Thammasat University 國立法政大學 | 0/14/2/1/0 | 待/待/待 | 0／未建個別外校清單 |
| 61 | King Mongkut’s University of Technology Thonburi 蒙庫國王科技大學 | 0/13/2/2/0 | 待/待/待 | 0／未建個別外校清單 |
| 65 | Universitas Bunda MuliaUK 慈育大學 | 0/11/6/0/0 | 核/待/待 | 0／未建個別外校清單 |
| 67 | Ho Chi Minh City University of Technology HCMUT胡志明市國家大學所屬百科大學 | 13/0/2/2/0 | 核/核/缺 | 8／student_application:8 |
| 68 | Ho Chi Minh City University of Technology and Engineering HCMUTE胡志明科技工程大學 | 11/1/4/1/0 | 核/缺/缺 | 7／student_application:7 |
| 71 | Dong Nai Technology University (DNTU) 同奈科技大學 | 0/0/17/0/0 | 缺/缺/缺 | 0／未建個別外校清單 |
| 73 | Chitkara University 吉特卡拉大學 | 4/5/7/1/0 | 核/核/待 | 0／未建個別外校清單 |
| 74 | Saintigits Group of Institutions 聖基茲工學院 | 0/1/16/0/0 | 核/待/待 | 0／未建個別外校清單 |
| 77 | Vel Tech Rangarajan Dr.Sagunthala R&D Institute of Science andTechnology 維爾特克科技大學 | 0/13/2/2/0 | 核/待/待 | 0／未建個別外校清單 |
| 80 | Presidency University 總統大學 | 1/9/2/1/4 | 核/待/待 | 0／未建個別外校清單 |
| 83 | Mapua University 瑪普爾大學 | 7/2/6/2/0 | 核/核/核 | 7／student_application:7 |
| 85 | Bordeaux Montaigne University 蒙田波爾多大學 | 3/9/3/2/0 | 核/待/待 | 0／未建個別外校清單 |
| 86 | EPITA (School of engineering & computer science) 法國高等工程技術學院 | 10/3/3/1/0 | 核/核/核 | 7／student_application:7 |
| 87 | University of Strasbourg 史特拉斯堡大學 | 2/10/4/1/0 | 待/待/待 | 0／未建個別外校清單 |
| 88 | Faculty of Management, Economics & Sciences (FGES) –Catholic University of Lille 法國里爾天主教大學(管理、經濟及科學學院) | 10/1/6/0/0 | 核/核/核 | 1／student_application:1 |
| 89 | University of Southern Denmark 南丹麥大學 | 0/11/5/1/0 | 核/待/待 | 0／未建個別外校清單 |
| 95 | Adam Mickiewicz University, Poznan 亞當密砍凱維奇大學 | 2/6/6/0/3 | 核/舊/舊 | 0／未建個別外校清單 |
| 98 | Ludwigshafen University of Business and Society 路德維希港社會應用科技大學 | 6/2/9/0/0 | 核/核/核 | 0／未建個別外校清單 |
| 99 | Friedrich Schiller Universität Jena 耶拿大學 | 9/5/0/3/0 | 舊/待/舊 | 0／未建個別外校清單 |
| 100 | Ostfalia University of Applied Sciences 奧斯特法利亞應用科技大學 | 1/12/4/0/0 | 核/缺/待 | 0／未建個別外校清單 |
| 101 | Deggendorf Institute of Technology 德根多夫應用科技大學 | 0/6/10/1/0 | 核/待/待 | 0／未建個別外校清單 |
| 102 | Augsburg University of Applied Sciences 奧格斯堡應用科技大學 | 7/8/2/0/0 | 核/核/核 | 0／未建個別外校清單 |
| 103 | ZHAW Zurich University of Applied Sciences-SoE 蘇黎世應用科技大學-工學院 | 0/9/6/2/0 | 核/待/待 | 0／未建個別外校清單 |
| 104 | University of Applied Sciences and Arts Northwestern Switzerland – School of Business Fachhoschule Nordwestschweiz (FHNW) - Hochschule für Wirtschaft 西北應用科技與藝術大學 | 3/10/2/2/0 | 待/待/待 | 0／未建個別外校清單 |
| 105 | Ankara Social Science University 土耳其安卡拉社會科技大學 | 1/11/3/2/0 | 舊/舊/舊 | 0／未建個別外校清單 |
| 106 | Ç ukurova University 土耳其丘庫羅瓦大學 | 10/0/6/1/0 | 核/缺/核 | 7／student_application:7 |
| 107 | University of Pardubice 捷克巴爾杜比彩大學 | 13/0/3/1/0 | 待/待/待 | 3／student_application:3 |
| 108 | Tomas Bata University in Zlí n 托馬斯拔佳大學 | 8/2/6/1/0 | 核/缺/核 | 6／student_application:4, conditional_program:2 |
| 109 | University of West Bohemia 西波希米亞大學 | 2/12/3/0/0 | 待/缺/待 | 0／未建個別外校清單 |
| 111 | SILESIAN UNIVERSITY IN OPAVA (School of Business Administration in Karvina) 奧帕瓦西里西亞大學(管理學院) | 6/3/5/3/0 | 核/核/核 | 0／未建個別外校清單 |
| 114 | Ø stfold University of Applied Sciences 厄斯特福德應用科學大學 | 5/5/6/1/0 | 核/待/待 | 5／student_application:5 |
| 119 | Universidad Internacional 墨西哥國際大學 | 6/2/6/3/0 | 核/缺/核 | 8／student_application:6, post_offer:2 |

## 尚待補查與實際限制

剩餘公開來源工作：交通10校、生活7校、學制34校、學院44校無可填值；其餘一般無年份／跨校區來源仍待確認適用性。這是公開查核缺口，並非都只能聯絡學校。已列逐校checklist及 `research-gap-audit.json`／`acquired-content-review.json`。

637個來源紀錄唯一且對應637請求；70筆fetch_failed，另有7個challenge、3個空回應、2個captcha、1個不相關內容異常。異常頁不當成官方政策或城市來源。20筆失敗followup分成14笔已重試及6筆首次失敗而未重試，不捏造重試結果。

中正母校流程與名額適配已可使用；外校規定仍有上述缺口，未宣稱與長庚資料完整度相同。未登入學校系統、提交資料、聯絡承辦、merge main或部署。
