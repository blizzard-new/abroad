# DATA-010-BATCH-001：非 HTTPS 官方來源安全替代候選

- 建立日期：2026-08-12；整批內容基線：2026-08-13；兩筆傳輸阻擋候選的內容與傳輸最近查核：2026-08-30
- 範圍：長庚大學、國立臺北大學的 legacy 交換流程
- 盤點結果：9 筆流程、12 個去重後的非 HTTPS 官方網址
- 狀態：待兩位真人逐頁查核；未建立正式 revision、未核准、未發布
- 原則：本表只整理可供真人核對的候選頁，不代表自動認定內容等價，也不把 `http` 字串直接改成 `https`
- 機器可讀候選：`docs/review-batches/data-010-batch-001-source-candidates.json`；測試會要求它恰好涵蓋目前 official data 的 9 筆流程／12 個非 HTTPS 審查來源，且明示不發布、不建立核准

內容研究仍分為 7 個強候選與 5 個條件式候選；這個強度與傳輸安全是兩個不同維度。2026-08-30 以允許 redirect、驗證 TLS、只讀取 response headers 的方式重查 10 個去重後候選網址，其中 8 個最終維持 HTTPS、2 個（Lobachevsky、人民大學 SIS）會轉回 HTTP。兩個降級候選目前各有三筆最終 HTTPS 200 的官方脈絡頁，但六筆都沒有重現原 exchange 規定，因此只標成 `eligible_as_replacement=false` 的研究線索。連同 DATA-003 山東大學候選、全部輔助連結與研究線索，稽核共檢查 22 個去重網址：20 個最終維持 HTTPS、2 個轉回 HTTP。後兩者即使內容強度較高也一律禁止填入待審欄位；安全研究線索同樣不能直接套用。

可重跑命令：`python scripts/check_source_replacement_transports.py --check --timeout 30`。命令不讀取或保存頁面本文，不修改 manifest、revision、核准或公開資料；連線失敗一律視為未驗證並以非零結果拒絕通過。

## 1. 可供真人確認的替代候選

| 母校 | 合作校 | 目前受阻擋網址 | 候選處置 | 自動查核結果 | 真人仍須確認 |
| --- | --- | --- | --- | --- | --- |
| 國立臺北大學 | 下諾夫哥羅德羅巴切夫斯基國立大學 | `http://lobachevsky.university/` | 條件式候選 `https://eng.unn.ru/`，傳輸阻擋；不可替代研究線索為外校學生入口、Academic exchanges 頁及 UNN 國際事務聯絡頁 | 候選首頁與 semester exchange 精確路徑都會轉到 HTTP；外校學生入口仍把詳情連回不安全網域，Academic exchanges 與 2026 mobility 指南是 UNN 學生赴海外的 outbound 流程，聯絡頁只有承辦窗口。三筆都不能支援臺北大學學生申請 UNN 的當期 incoming 規定 | 由母校承辦確認正式網站身分，並找到最終仍為 HTTPS、內容等價的精確 incoming exchange 頁；不足時不得替換 |
| 國立臺北大學 | 中國人民大學 | `http://sis.ruc.edu.cn/en/internationalExchange/studentexchange/exchange_application/index.htm` | 內容強候選但傳輸阻擋；不可替代研究線索為一般國際學生申請系統、通用擔保書及人民大學商學院 incoming exchange 頁 | SIS 的 `index.htm`、目錄版及無尾斜線 HTTPS 都轉回 HTTP；一般申請系統與擔保書沒有重現 SIS 規定，商學院頁雖有 nomination、期限與文件，但承辦學院及日期都不同，不能跨學院替代 | 尋找最終仍為 HTTPS 且內容等價的正式頁，再確認 School of International Studies 規定適用臺北大學目前協議與梯次 |
| 國立臺北大學 | 北京科技大學 | `http://www.ustb.edu.cn` | 強候選 `https://oia.ustb.edu.cn/StudywithUs/ExchangeStudentPrograms/index.htm` | 國際處專用交換生頁涵蓋 nomination、申請步驟、文件、住宿與簽證，比首頁精確 | 確認當期適用性並逐條比對現有文件規定 |
| 國立臺北大學 | 梨花女子大學 | `http://oia.ewha.ac.kr/oia/1165/subview.do` | 強候選為 incoming notice `https://oia.ewha.ac.kr/oia/1148/subview.do`，另搭配 eligibility 與 Fall 2026 factsheet | 原 1165 頁實為 Ewha 本校生 outbound 概覽；incoming notice 已列 Fall 2026 nomination、application 與文件 | 逐條決定 notice、長期 eligibility 與 factsheet 分別支援哪些規定，不能再沿用 outbound 頁 |
| 國立臺北大學 | 紐芬蘭紀念大學 | `http://www.mun.ca/` | 強候選 `https://www.mun.ca/goabroad/visiting-students-inbound/` | 專用 inbound 頁涵蓋 exchange eligibility、nomination、application、housing、visa 與 academics | 確認臺北大學協議對應 campus、faculty 與當期 deadline |
| 國立臺北大學 | 華東政法大學 | `http://study.ecupl.edu.cn/` | 條件式候選 `https://study.ecupl.edu.cn/` | HTTPS 國際教育入口可用並有含 exchange program 選項的官方申請表；目前找到的 2026 招生頁主要屬學位生 | 找到校際交換精確頁、年度、梯次與文件，不能只確認入口安全 |
| 國立臺北大學 | 華東政法大學 | `http://www.ecupl.edu.cn/` | 條件式候選 `https://www.ecupl.edu.cn/` | 校級 HTTPS 是安全入口，但沒有證明支援交換規定 | 確認與國際教育入口的關係；只有中繼資料完全一致時才能合併 |
| 長庚大學 | 北京清華大學 | `http://intl-nondegree.tsinghua.edu.cn/b/yzlxs/yz_sys_xxfjb/download/file?id=392029` | 優先比較 `https://is.tsinghua.edu.cn/GettingStarted/adm/ns.htm` | 舊下載端點的 HTTPS 版本目前回傳錯誤；清華官方現行頁明列 Visiting/Exchange Programs 與承辦聯絡方式 | 確認現行頁能否支撐原本所有文件要求；不能只因同校就取代失效附件 |
| 長庚大學 | 日本立教大學商學院 | `http://cob.rikkyo.ac.jp/en/` | 條件式候選 `https://english.rikkyo.ac.jp/exchange/index.html` | 中央 Student Exchange Program 頁涵蓋 application、academics、housing 與承辦；但明示學部間協議須洽對應學部 | 先確認長庚合作屬校級或商學院學部級；若為學部級須取得商學院 factsheet／正式通知 |
| 長庚大學 | 泰國法政大學商學院 | `http://www.bba.tbs.tu.ac.th/` | 與下列兩筆一起候選合併到 `https://cia.tbs.tu.ac.th/exchange-program/incoming-exchange-program` | 現行 Center for International Affairs Incoming Exchange Program 可開啟，列有 admission、學期、課程、簽證及 AY 2026/2027 factsheet | 兩位真人確認三個舊入口確實由同一現行頁取代，並核對文件規定 |
| 長庚大學 | 泰國法政大學商學院 | `http://www.bba.tbs.tu.ac.th/index.php` | 同上 | 三筆本機來源的標題、角色、權威、優先級與內容雜湊一致，可使用工作台的明確合併流程 | 同上 |
| 長庚大學 | 泰國法政大學商學院 | `http://inter.tbs.tu.ac.th/` | 同上 | 現行 CIA 頁使用 `tbs.tu.ac.th` 官方網域並提供 incoming 聯絡方式 | 同上 |

## 2. 工作台處置步驟

1. 以內容管理者帳號從「含非 HTTPS 官方來源」篩選出目標流程，建立待審副本。
2. 親自開啟目前頁、候選 HTTPS 頁、母校公告及合作校當期資料，確認權威性與適用年度／梯次。
3. 工作台只允許最終維持 HTTPS 且 HTTP 2xx 的候選填入未儲存欄位；會轉回 HTTP 或未驗證的候選會顯示最終網址與查核結果，按鈕保持停用。「安全研究線索（不可直接替代）」另列名稱、關係、傳輸證據與不等價原因，不提供套用按鈕。真人另找到安全且內容等價的來源後，才能在「補正適用學年度與來源證據」中勾選已查核來源並填寫修正說明。
4. 系統只修改 pending revision，並同步替換流程來源、步驟、期限、官方表單、文件、送件入口及動作網址的相同引用；正式學生內容不變。
5. 多個舊入口只有在標題、角色、權威、優先級、內容雜湊及本次適用範圍都一致時才可合併；任何衝突都會被拒絕。
6. 儲存後重新載入版本對照。每條關鍵規定必須直接顯示對應 HTTPS 來源，兩位審查者再各自逐來源、逐規定核准。

## 3. 本批不代表

- 不代表上述 HTTPS 候選已由真人認定為正式等價來源。
- 不代表合作校規定、適用年度、梯次、文件或期限已完成雙審。
- 不會建立或使用 AI API、本地 AI、Flutter、SwiftUI 或 Kotlin 功能。
- Codex 不代替真人審查者留下核准紀錄。
