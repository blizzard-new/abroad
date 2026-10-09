# CCU 固定候選 SHA 的最終驗證證據

官方來源主要查核日為2026-10-08；本次完整gate於2026-10-09 00:05 UTC結束。

本目錄測試只屬 **`92e66f365d66c87889c8ddff82e9675327b66366`**。完成後的純文件證據 commit 不繼承測試 SHA；程式與資料未再修改。[原始 summary](final-validation-summary.json)、[實際選檔](test-selection.json)、[起始](git-boundary-start.json)與[結束](git-boundary-end.json)記錄同一 SHA 與空 porcelain stdout。

|實際檢查|結果|
|---|---|
|469 回歸|462 passed、7 skipped、0 failed、0 errors；JUnit 414.29s|
|102 瀏覽器|102 passed、0 skipped、0 failed、0 errors；兩組 JUnit 1169.00s，較長組 wall 673.74s|
|可重現產物|7 builders、1,184 CCU 檔逐 byte 相同；wheel 同 1,184 檔，SHA `62a1a365355a21f3873bfa400711ffc35146feb2aa6ba3aba307c2cdd3a440b3`|
|資料保留|原 1,091 來源／附件檔與77dfd84逐byte相同，46 main 官方資料與77 CGU published hash不變|
|父 session 舊證據|1959d16 所發布77dfd84目錄88檔逐byte不變，見[獨立保留證明](prior-77-evidence-preservation.json)|
|契約與語法|110 API paths與原有required保留；6既有schema有optional變更、4新增schema；OpenAPI、uv0.11.26 lock、Python、4JS、指定Ruff通過|

[regression log](regression.txt)／[XML](regression.xml)、[browser XML](browser.xml)、兩組[1 log](browser-group-1.txt)／[1 XML](browser-group-1.xml)、[2 log](browser-group-2.txt)／[2 XML](browser-group-2.xml)及[案例聯集](case-union.json)保留原始結果。7 skip為6既有Phase C及1 Docker opt-in，未放寬舊測試。[驗收矩陣](acceptance-results.json)列實際原因與未執行範圍。

正式四校bundle的4個390／1440真實UI/API案例沒有response/state mock；各母校實際回應筆數另見browser-evidence/real-dashboard-cold-loads.json。[8個延遲／排隊草稿案例](browser-evidence)只延遲實際API response送達或控制browser clock，涵蓋application workflow、資格/detail與完整度；不能宣稱life頁亦做獨立延遲。其他既有e2e fixture替換CGU partner list，與這4個獨立正式bundle案例分開。

本輪資料為104目錄（52曾列非零名額、3名額空白、不能視為零、49灰字參考），55工作流程／概要，966來源與33校250文件要求（185current、65pending、59conditional）。935海外欄307current／333pending／203missing／71conflict／20reference／1explicit_not_announced；0校17欄全current、清單仍部分，functional_parity_complete=false。母校2027春三梯截止於2026年8–9月，均已截止；2027秋新版尚未核實。

323筆原佇列149／149及174／174皆有原文、hash、年度、實際查核時間與限定處置：102指定映射、21相同正文、64參考、60排除、69索引、7受限。不是全來源全文或全部政策完成。Mapúa公開校曆影像及34頁手冊、UNINTER Spring2027的44題表已實際處理；讀到表單不代表所有附件齊全。來源記錄與[公開擷取實證](public-render-verification)記載標準ChromiumTLS錯誤、一般requests正常TLS成功及一次性診斷context；未改系統/repo信任設定、填寫或提交。

`6ea9368`完整驗證曾找到AMU博士生保險範圍錯誤並中止；[原失敗紀錄](../6ea9368-aborted/README.md)保留。`d3b97d9`恢復一般交換missing並保留龍谷當期校方核章要求，之後73cb7ca另發現DNTU摘要待核時段與九個HTML/JPEG未打包；保留第二次中止證據。0765054修正摘要及打包後，完整回歸仍有一般HCMUTE支援頁誤補arrival的1項失敗（461pass／7skip），原完整XML/log保留。92e66f3將該來源限定到program_scope研究註記並恢復arrival缺值後，重跑上述完整gate。舊77dfd84及其他歷史失敗均未覆寫。

[當前候選遠端CI](remote-ci-current-candidate.json)於2026-10-09 00:06 UTC實際觀察為 [run 37863065623](https://github.com/blizzard-new/abroad/actions/runs/37863065623) completed／failure／0 jobs、0 check runs，不能把本地gate算CI通過。既有workflow job.env的runner context語法錯誤診斷／可審查修正見[只讀CI證據](../ci-readonly/README.md)，正式workflow未改。[Jena實際外部browser結果](browser-evidence)與[正常TLS下載實證](jena-official-alternative-https.json)分開；該DOC是交換延長表，不是初次申請或2027新版。

[17共用檔與當時遠端heads](../../ccu-followup-integration-boundary-2026-10-08.json)及[本gate期間唯讀heads](integration-heads-observed.json)供統一整合。其他分支仍在更新，未合併或做跨分支延遲／runtime驗收；其餘repo全測試、Supabase、依賴漏洞審查與部署未執行。檔案manifest保存本目錄其他檔的SHA256，沒有修改logs/XML。

原始0765054失敗log/XML各有一行pytest錯誤輸出的尾端空白，保留原檔所以全diff --check為2；排除這兩個原始檔後為0，見[實際檢查收據](whitespace-check-proof.json)。
