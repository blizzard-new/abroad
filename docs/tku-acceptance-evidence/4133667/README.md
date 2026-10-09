# TKU 4133667 完整原始驗收與交付證據

候選 `4133667cfede9f3be70216795c74051adb6f3a33`，程式分支 `data/tku-exchange-20261008`，[draft PR #2](https://github.com/blizzard-new/abroad/pull/2)。本分支只追加證據，artifact commit 沒有冒稱另跑程式驗收。最新 main 基準 f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59。

本機更正後固定SHA十步完整：1482 passed、24 failed、8 skipped；其他九步exit0。逐步起訖guard同SHA且乾淨，54相關browser通過，62既有TKU unit/runner與2新增pipe回歸通過。851 CGU/NTPU/NTU workflow hash與完整各校資料bundle無差異；沒有新增本機failure。另19隱私回歸/原HTTP、6/6探測、2JLPT及2原文來源browser保存實際JSONL/HTTP/JUnit/截圖，與主suite不重複計數。fresh wheel從獨立同413 checkout建置，1009 package來源逐檔相同；138MB wheel不加入archive，SHA與建置guard另存。

[PR run37876127808](https://github.com/blizzard-new/abroad/actions/runs/37876127808)及[push run37876122528](https://github.com/blizzard-new/abroad/actions/runs/37876122528)均已failure終態。每輪完整1764 nodes/182 files：1717 passed、31 failed、16 skipped。第0片1494/31/16（1541），其餘75/74/74全部pass。0漏跑、0重複、原1757 IDs全部保留、新增7回歸；skip集合16與原始完全一致。每片result實際pytest_exit1或0，沒有內部錯誤或logger中斷。PR synthetic merge a8c48c33426404f31b1d00cfeb78ba6abfa8c136與413同tree270e08671c467b0507044be676ffdafab29ba8fa，原commit metadata附檔。

原66失敗已解35（4PDF工具環境＋31共用browser）；剩31＝24nonbrowser＋7browser，0新增失敗、0尚未跑原失敗。完整remaining/resolved ID在remote/*-original-failure-triage.json。非browser仍含社群board政策/response、兩個source/localization契約、10個UI/router字串、私訊重試及4個缺治理API家族；browser仍有documents/進度選擇器、review頁404、兩個workspace隱藏控制、過期提示與422/403。早期選擇器或status斷言會阻止後續安全/保存斷言，不能稱整案例安全或豁免。

每輪62個同job/same runner main控制全部實跑：PR 1passed/61failed；push4passed/58failed。固定f6ad runtime及4e6原測試，同interpreter/packages/browser/Poppler，按候選partition指派；candidate gate仍失敗。main-control shell0只代表診斷證據產出成功；原pytest_exit1、完整JUnit/log與SHA均留，不宣稱基準全綠或候選可合併。

[remote/original-artifacts](remote/original-artifacts)保留8份原candidate suite.xml＋8份原main-control suite.xml、完整collect-nodeids/result/partition/log、原ZIP與完整解壓；remote另有兩輪完整原log archive/metadata/逐案例結果。全為本環境成功授權讀取且持有的原bytes，沒有重建或刪除failure。Reviewer環境下載引用403後停止該路徑，本環境最後一次沿既有成功介面正常取得；沒有繞過403、改權限或重新授權。提交到固定Git commit讓reviewer可讀原檔，不依賴短效下載引用。

首次413本機命令漏PLAYWRIGHT_BROWSERS_PATH，1428P/24F/8S/54 setup errors，另JLPT/source起始失敗，原bytes在operational/first-local-browser-path；更正既有/tmp/tku-browsers後才取得上述完整結果。報表工具原not_run仍誤寫七份selected：保留原報表並用acceptance-scope-correction.json列實際九份，未跑其他E2E不稱通過。診斷首次路徑錯誤亦保留並更正。runner-stress保留強制nonblocking/省略startup的負向terminal-error探測，以及實際startup後54案例正常exit1的對照，不混入正式統計。

資料128計畫列、119原文校名、unique IDs128；4當期2027–2028日語二甄/7公告名額、124舊期參考。校內9/30中午臺北截止已過，0個可新申請；不是所有姊妹校可選。89/152欄核實（58.6%），16missing_in_source/18needs_confirmation/18reference_only/11not_verified_new，63缺口、13矛盾組。53外校文件/28交換附件/1參考行事曆，4未發布流程/4official_partial目的地，9學院44科系僅名冊。官方URL/頁碼或原文/原生年度/角色/查核日逐欄保留，不把incoming/outbound、計畫、學制、校區或名額狀態合併。

10/9中央兩公告与19頁簡章/1頁名額表重新GET，內文年度與SHA同既有capture；只限這兩份，未宣稱全部host 2027表格已核實。尚未核實新版與官方尚未公告分開；系所期限不能自動延到中央延期。4個有直接來源的映射補正保留原10/8查核日，不借此把63缺口升verified。

歷史ce83 logger中斷、3cc中斷、4e6完整66失败及b455逾時/892資料均保持原固定commit，summary.json列history。manifest.json逐檔bytes/SHA256；acceptance-evidence.zip是可下載副本，不含自身/manifest/checksum。資料與全站驗收仍有上述實質阻礙；checksum或同main失敗不等於通過。未merge、部署、正式DB、憑證或權限變更。
