# UniWay 交換申請全站實測

測試從學生選一所合作校開始，經過查看申請方式、收藏、建立個人計畫與整理文件，終點是學生能拿著正確文件自行進入校方的正式申請管道。使用隔離的開發環境、獨立測試帳號及合成檔案。官方網站用於查閱公開規定。

## 學生能走到哪一步

71 所母校各用一個獨立帳號，從選校、收藏及查看申請方式開始。60 所能建立計畫、連結文件、重新開啟並下載相同內容。這 60 校都實際開啟學生本人送件交接，其中 29 校為當期校方流程，31 校標明使用歷年資料；所有案例在學生登記或對外送出之前停止。其餘 11 所的全部合作項目在測試當下都受梯次、名額或資格狀態限制，學生能收藏並查看限制。逐校紀錄列出目標、可開始備件的方案數與停止位置。[71 校逐校操作結果](student-journeys.md) · [網頁逐案紀錄](student-journeys.jsonl) · [服務端逐案核對](student-files.jsonl)

長庚→林肯、臺北大學→關西學院大學另用六份測試 PDF 逐關操作。兩案皆完成保存，重開帳號後逐份核對版本與備妥狀態，並各下載一份與原檔逐位元比對。長庚學生也從文件工具實際產生可下載的 PDF。臺北城市科大與陽明交大兩案另驗證了歷年和當期文件的適用選擇。[文件、檔案與校方交接](document-journeys.md) · [桌面與手機導覽](navigation.md)

## 哪裡改了

| 學生遇到的問題 | 修正後的行為 |
| --- | --- |
| 長庚計畫使用的「116-1（2027 秋季出國）」和資料中的「秋季／全學年梯次」原先對不到。 | 以同母校、同學年的規則比對期別。長庚至林肯恢復 9 個步驟，保留校方尚待確認的事項；尚未公告的梯次會提供來源與可先準備的事項。 |
| 長庚 116-1 寫須交紙本，展示預檢也少了在學證明。 | 先填第一份表單，從信箱下載申請表及同意書各自完成簽名，再從第二份表單逐項上傳 PDF。校內六份必備文件含 iCGU 在學證明，兩份表單均須在 2026/12/21 17:00 前完成。 |
| 臺北大學部分校名的英文空格不同，已整理的生活指南無法顯示。 | 以該校名單內唯一的完整名稱配對，保留不同方案。漢堡商學院現在能讀到指南與兩個來源；同濟及烏迪內補上接待校實際公布的生活資訊。 |
| 文件關卡已保存附件，學生仍要離開關卡找檔案。部分送件任務也沒有官方入口。 | 從同一關卡下載已選取的檔案，能開啟官方公告核對送件方式。正式送件狀態由學生依實際情形註記。 |
| 有些學校只有往年文件，建立計畫後卻沒有可用的備件項目。 | 提供來源、適用年度及適用性選擇，學生可以先備檔，再依本期校方公告確認。 |
| 中央大學仍顯示名單預定 10 月公布，8 個新方案找不到。 | 依 11/17 校方名單補齊 214 個當期方案（內含 8 個自費）與各自名額、語言及備件來源。另保留 8 個本期未列方案。南洋理工的兩列分別呈現，一列只印有國家卻無校名的原始資料留待校方確認。 |
| 接待校網址缺漏，部分校方生活資料只有空白或來源狀態錯誤。 | 以機構名稱、所在國及可讀校方網頁補 77 筆接待校網址；臺北大學 58 筆新增校區或地址可逐列對照原文，中正大學 16 校補上可用的住宿／生活服務或聯絡窗口。 |
| 長庚部分目標把其他大學或不同交換方向的期限當成本案期限。 | 複核 13 條長庚接待校路徑，移除 6 個錯置的具體期限。另把中正 25 間合作校中能追到校方頁碼的學院及學制限制顯示在資格檢核。 |
| 從跨校選校目錄開慕尼黑工業大學、早稻田大學等目標時，詳情 API 回應 422。 | 恢復正確的跨校詳情入口。未登入就能查到慕尼黑工業大學的 4 所臺灣母校，以及早稻田大學的 18 所母校，並對到學生選的母校。 |
| 金門大學等校把學生繳交文件的校內關卡顯示成「儲存通知紀錄」。 | 依該關的負責人及交件動作區分學生送件與校方審查。8 校重驗到正確的校內交接位置；已有的備註仍可查閱，新的送件狀態須由學生確認。 |
| 母校選單筆數過時，部分校方入口已搬家。 | 納入實際名單的長庚 78 筆、臺北 206 筆、中正 104 筆與中央 222 筆，並同步修正首頁備援清單。逐校查閱 71 個官方入口，修正 13 個連結。 |

[長庚 116-1 官方公告](https://www.cgu.edu.tw/oia-ch/Subject/Detail/85785?nodeId=15817) · [長庚選送須知](https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656) · [71 校官方入口前後查驗](home-offices.csv)

長庚與德勒斯登工業大學的學碩 3+2 計畫另作查核。長庚雙聯名單的「名額」欄空白，且這張表沒有接待校截止日欄。平台現標明名額待確認，並提示學生先查系所與國際處。北大、長庚等校的讀書計畫指引也分別連回自己的要求與來源。[長庚雙聯名單](https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17533) · [逐校資料盤點](catalog.md)

[中央逐列名單與申請窗口](ncu-roster.md) · [11/17 中央大學官方表](https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangeschoollist-1117.pdf) · [原先缺申請核心欄位的 55 組來源查核](open-core-sources.md) · [接待校官網查核](partner-host-websites.csv) · [臺北校區／地址來源](ntpu-verified-cities.csv) · [中正生活服務來源](partner-ui-ccu-life.md)

## 修改前後畫面

各組左右是同一個學生操作位置。長庚林肯的「修正前」取自正式網站，以計畫實際產生的期別重現；「修正後」取自本 PR 的測試站。點圖可放大。

| 操作位置 | 修改前 | 修改後 |
| --- | --- | --- |
| 長庚 → 林肯 → 申請方式 | [![長庚流程空白](screenshots/cgu-lincoln-before.png)](screenshots/cgu-lincoln-before.png) | [![林肯九步驟](screenshots/cgu-lincoln-after.png)](screenshots/cgu-lincoln-after.png) |
| 長庚 116-1 校內文件清單（展示版） | [![原五項與紙本說明](screenshots/cgu-checklist-before.png)](screenshots/cgu-checklist-before.png) | [![六項及兩表單說明](screenshots/cgu-checklist-after.png)](screenshots/cgu-checklist-after.png) |
| 北大 → 漢堡商學院 → 生活情報 | [![原待補頁面](screenshots/ntpu-hamburg-before.png)](screenshots/ntpu-hamburg-before.png) | [![含兩個來源的指南](screenshots/ntpu-hamburg-after.png)](screenshots/ntpu-hamburg-after.png) |
| 中央 → 西雪梨大學 → 名額與受理狀態 | [![中央舊名單與待確認狀態](screenshots/ncu-western-sydney-before.png)](screenshots/ncu-western-sydney-before.png) | [![11/17 版名單所列的 2 個名額](screenshots/ncu-western-sydney-after.png)](screenshots/ncu-western-sydney-after.png) |
| 中正 → 印尼慈育大學 → 官方生活服務 | [![生活服務補查前](screenshots/partner-ui-ccu-life-before.png)](screenshots/partner-ui-ccu-life-before.png) | [![校方住宿設施及窗口](screenshots/partner-ui-ccu-life-after.png)](screenshots/partner-ui-ccu-life-after.png) |
| 淡江合作校公開頁的申請入口 | [![原方案資訊](screenshots/partner-ui-before.png)](screenshots/partner-ui-before.png) | [![可直達方案申請分頁](screenshots/partner-ui-after.png)](screenshots/partner-ui-after.png) |
| 我的申請 → 已保存的文件 | [![原附件畫面](screenshots/student-linked-document-before.png)](screenshots/student-linked-document-before.png) | [![可直接下載已連結文件](screenshots/student-linked-document-after.png)](screenshots/student-linked-document-after.png) |
| 中央 → 西雪梨大學 → 選校卡 | [![原備查卡片](screenshots/ncu-roster-before.png)](screenshots/ncu-roster-before.png) | [![中央受理中及2個名額](screenshots/ncu-roster-after.png)](screenshots/ncu-roster-after.png) |
| 金門 → 三重大學 → 學生送交校內申請表 | [![原本只可儲存通知](screenshots/nqu-application-handoff-before.png)](screenshots/nqu-application-handoff-before.png) | [![學生能核對公告與記錄送件](screenshots/nqu-application-handoff-after.png)](screenshots/nqu-application-handoff-after.png) |
| 我的申請 → 校內送件 | [![原送件備註](screenshots/student-official-handoff-before.png)](screenshots/student-official-handoff-before.png) | [![可核對官方入口的送件關卡](screenshots/student-official-handoff-after.png)](screenshots/student-official-handoff-after.png) |

## 如何解讀數字

10,965 是更新名單後的合作校或方案總數。一所海外大學可以和不同臺灣母校合作，也可能有多個方案。10,960 是按母校、合作校與國家彙整後的公開詳情頁數。逐筆結構盤點、頁面內容可讀、實際上傳下載與校方是否開放申請，各自有不同的測試依據。[名單與欄位盤點](catalog.md) · [逐頁與逐方案實測](partner-ui.md) · [公開網頁原始結果](partner-ui.csv.gz)

逐筆掃描 16 欄，925 個方案至少一欄無原始值。4,589 個名單狀態標為 `open` 的方案中，267 個至少一欄無值，253 個至少缺一項核心申請欄位（中央 198、中正 42、長庚 13）。例如中央校表即使公布名額，也未必另列學院或學制。備註已明載的 48 個院系／方案與 25 個學制／年級限制已寫入對應欄位；尚待確認的欄位保留原始依據及下一步。中央另為 50 個方案補上可核對的校區，仍有 30 個開放方案的城市待核。[全平台逐欄計數與學校來源](catalog.md)

每份文件以任務所屬階段與年度判斷。名單標示開放仍須交叉核對受理期限、學生資格和當期名額；歷年資料、提名後才會通知的規定、宿舍與費用預估都有自己的適用範圍。東海與開南的官方入口重試時回應 503，這兩筆保留原址並紀錄狀態。[來源入口](home-offices.csv)

## 少了幾步、花了多久

| 相同終點 | 只用官網 | 使用平台 | 本次觀察 |
| --- | --- | --- | --- |
| 北大查佐賀或山梨的甄選與接待條件 | 各開 3 份資料 | 各開 2 份 | 各少 1 份（33.3%）。自動查詢中位數由 4.889–5.322 秒降到 0.796–0.806 秒。 |
| 長庚整理六份已簽妥的 PDF、兩個官方入口與截止時刻 | 9 步 | 8 步 | 少 1 步（11.1%）。六輪配對產出的檔案與交接清單雜湊相同。本機自動重播中位數約 652／602 毫秒，兩邊時間範圍重疊。 |

計時範圍未涵蓋真人寫讀書計畫、等成績單、請師長簽名與校方審查。這些個案足以比較資料來源和操作步數，整份交換申請能為真人省幾小時仍待學生對照測量。[完整比較、假設及原始計時](benchmark.md)

## 驗證紀錄

- 71 校的瀏覽器與文件測試使用隔離服務及合成帳號。網站公開詳情以逐頁 HTTP 和 Chromium 解析驗證，10,965 個方案另以正式前端渲染函式逐筆檢查。原始表內每一列都有結果；逐校上傳測試從各母校選代表目標。[合作校檢查方法](partner-ui.md) · [逐校學生操作方法](student-journeys.md)
- 長庚展示、來源更新失敗復原、打包資料、文件關卡及中正生活資料的整合測試共 110 項通過、4 項略過。接待校研究整檔與行動版校目錄的一致性檢查共 33 項通過。申請關卡分類與既有帳號紀錄相容性測試 53 項通過。中央跨時窗、跨校目錄、顧問及 SEO 合計 36 項通過。中央名單更新另外抽出 45 個受影響的既有測試函式，含參數共 85 案，經修正與重播後逐案通過，包含桌面與手機。另驗證 OpenAPI 契約、JavaScript 語法及網站資產版本。
- 額外跑完整的 Web 介面字串比對、資產版本與 Flutter 原始碼比對三個測試檔，此分支 53 項通過、11 項失敗。以相同測試方式讀取基準版本 `af32b61d` 的檔案，該版本 50 項通過、13 項失敗。兩版共有 9 項舊版 Web 文案／結構斷言失敗。Flutter 另有 2 項仍引用已移除的檔案、舊版 API 或目錄數量；本次補驗 71 校離線資料與後端對齊。此次操作結果涵蓋手機瀏覽器，未建置 iOS 或 Android 安裝檔。
