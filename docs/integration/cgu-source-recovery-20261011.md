# CGU 來源恢復與本輪隔離整合

此分支僅供隔離驗收，從 PR #8 `9927ec1d8765a9772671bbaa68e7f920995f1258` 開始。main 基線 `59a20f27fcee00fb597abc79e75ec11778317422`。尚未 merge main、部署或修改正式 DB；Quality 停用、Render autoDeploy、branch protection、憑證及付費均未改動。

## CGU 小範圍修復

- API 的 dashboard 與合作校／流程查找共用 CGU provider；基礎 dashboard 不再獨立下載及永久快取空名冊。
- 兩份公開表格均 HTTP 200、必要欄位 schema 有效、有可解析學校，且完整批次驗證成功，才原子替换整批。任一來源失敗、空白、結構不符、較舊時間或磁碟寫入失敗，保留前一完整批次。
- 成功批次更新間隔 600 秒，失敗重試至少 60 秒；背景更新 single flight，請求直接讀已存資料。runtime JSON 以同目錄 temporary file、fsync、os.replace 寫入，無額外 DB migration。
- 隨程式交付 2026-10-11 09:58:47 UTC 的 77 筆顯示列及兩份原始公開 GVIZ 內容／SHA256 收據，供暫時性檔案系統的冷啟動備援。records SHA256 `afbd6356d0a46e1d593d04f3de5a47a4507c0f553bd3cd4a6e617cff689a3ade`。77 是顯示列，不是當期可申請學校總數。
- 年度、名額、空白／零值、可申請與發布狀態皆保持來源原值。來源取得成功不等於當期資料已核實，`current_cycle_verified=false`。
- 新增可選 `catalogue_source` API 欄位，區分 `retrieved`、`saved_reference`、`unavailable`，分列上次成功／本次嘗試時間與失敗原因。其他校省略此欄，保持既有 bundle 序列化格式。
- 清單、地圖與詳細頁顯示來源時間／參考性；完全沒有有效備援時顯示暫不可用和「—」，CGU 相依查找回 503 + Retry-After 60。其餘五校及選校入口繼續使用。

既有 API fixture 改為明確注入 `create_cgu_catalogue`，資料與斷言不變；不以測試中的成功冒充 live。NTU 任務負責的原 13 個 live 來源依賴測試修復與 PR #9 原文缺件仍單獨追蹤。

## 第一個實作檢查點（完整整合驗收尚在進行）

- 初輪來源/API/快取/學生 dashboard：46 passed。
- 新來源測試補強必要欄位 schema 與 zero/missing/pending 保留，結果將在最終證據記錄。
- 手機390與桌面1440，錄製来源故障/恢復 browser：4 passed。最初2 failed為測試使用不存在函式，其後1 failed為未展開手機卡片；均已修正测试操作並保留原始 logs。
- 單獨真实公開來源 GET：兩份200，77列，2026-10-11 10:31:30 UTC；與備援 records hash 相同。此為 live 擷取，與上述 fixture 測試分開。
- OpenAPI snapshot、JS syntax、git diff --check 通過。
- 全量 unit/integration suite、六校瀏覽器、512 MiB單worker：本檢查點尚未完成。不得把此檢查點當成上線驗收。

## 固定資料候選及交集

| PR | 固定 SHA | 審查重點／狀態 |
|---|---|---|
| #8 | 9927ec1d8765a9772671bbaa68e7f920995f1258 | 本分支基底；共用視覺身份匹配／六校地球回歸保留 |
| #9 NTU | 4566f7f2b51b3b5c188f5394a56d7b5df190d1c5 | 無 api.py 改動；共用位置檔 ENS Ulm 與 #8 的母校點分別合併。60來源原文交付缺件未解，等待修正固定 SHA |
| #10 CCU | c18aebfceeedf8fceba5e4b24bbdf9dbebf0af18 | 照片／coverage／三處位置投影，需保留共用 matcher 與本機 operator 判定；部分補完 |
| #11 NCU | 5a3b690bff21e28ca85b438d285deb9236e706b9 | 照片／位置／JS sidecar 與共用 hunk 整合；部分補完，仍為 agreement_only，不升級為116當期資料 |
| TKU | 尚待本輪完成固定 SHA | 不重做收集者工作、不宣稱完成 |

## 發布與回滾邊界

本輪 CGU 修复以及上述 #9/#10/#11 相對 main 的 migration 變更為 0。新增來源狀態是 API additive 欄位；舊程式可忽略 runtime source_cache，舊前端可忽略此欄。回滾候選程式不需刪除 DB 或來源證據。

後續父對話決定正式順序前，必須先核對當時 main、每PR固定head、正式DB已套用migration清單與備份／還原證據。Render main commit 自動部署已開啟，而 Supabase Actions 受帳務阻擋，不能假設 main push 會同步 DB。若未來批次帶migration，應先完成隔離升級／舊程式相容性驗證，再依父對話批准執行「可前向相容DB -> 程式 -> 真實健康與功能驗收」；破壞性資料變更另需精確批准。程式退版與DB還原必須分別規劃，不自動下 destructive down migration。此分支沒有執行任何上述正式步驟。

## 固定批次整合檢查點

已在隔離分支依序納入 #9 `4566f7f`、#10 `c18aebf`、#11 `5a3b690`。尚未纳入任何 TKU 本輪新資料，NTU 原文缺件仍未解。

逐 hunk 處理：

- NTU ENS Ulm 更新保留 PR8 四個母校點，未整檔覆蓋共用位置。
- CCU 的照片與 coverage 使用同份校別 sidecar，其他校保留 PR8 VisualRecordIndex；三個位置入口傳本機資料目錄。
- NCU 照片不回落至未複核共用舊圖，95/97的CCU座標／照片與43/125的NCU座標／照片使用不同分母和校別。CCU／NCU 前端均使用對應已複核圖片及署名，不以共用別名圖片搭配不同作者授權。
- NCU 新增本機 operator verified/pending/needs_review/invalid 優先於 sidecar 的回歸；dashboard和生活頁一致。原始學校身份判斷未改動。
- 新 `catalogue_source` 未提供時省略，保持其他五校既有 bundle 序列化格式；NCU離線重建已重驗。
- 一致更新app／community-reader入口版本，保留CGU來源提示、地球及手機導航修正。

PR8+CGU固定 `985224fd`：65 tests passed（含六校真實API/地球與390/1440 browser）；單worker初輪12樣本最大RSS338.027MiB，未逾512MiB。此為加入三校新批次**之前**的基線，不代替整合後驗收。

整合初輪88案例：83 passed、5 failed；4為新增測試假定life回應含location物件（實際契約是location_note），1為NCU舊base預期10點（PR8+新批次實為43）。保留原始紀錄，修正測試對齊已驗證契約及合併分母後相關6案例全過。完整整合suite、擴充browser、暖機512MiB尚待最終證據。

原始CCU公開來源與CSV保留其CRLF／尾端空白，以維持原件SHA；全檔 `git diff --check` 會報原件空白，沒有改寫證據消除訊息。程式／測試檔的diff檢查另行通過。


## 2026-10-11 後續固定批次與記憶體修復

本節取代上文初期檢查點的待辦狀態。固定輸入：NTU #9 `b6607a0ee5d01e23878950d556f9540aa25aeaf2`、CCU #10 `cf4d86f22d89ee698315d46177daf00b49dd8706`、NCU #11 `5a3b690bff21e28ca85b438d285deb9236e706b9`、TKU #13 `f4819dab2db22507ad8978800aeabbcb9f598294`。資料仍不完整，不含研究者之後未固定的增量。

NTU217份當批正文／6 ZIP、191筆引文及頁碼、第一批59份正文已逐一hash驗證；舊缺件可關閉。保留282未公告名額與6明示零。19新增照片hash與授權核對：7份隨附Commons正文，12份透過網頁工具核對（獨立HTTP讀取403另留收據，不冒充live正文）。UC3M Commons描述Colmenarejo、分類Leganés仍有校區名稱矛盾，待研究者確認。前端額外顯示metadata作者，避免有授權連結但note漏署名。TKU287機構與153含歷史計畫分開，4本輪已截止／149協議參考／134歷史參考；13照片、3座標。13原文分片2576成員hash全核對，並補上套件選入規則。

完整整合於3a4977c9：2250 passed／1 failed／12 skipped；失敗為NCU覆蓋舊斷言43，NTU第二批為同一馬來亞機構新增1個共用校區點後應為44，唯一差異有逐列紀錄。擴充browser76 passed／2 failed，兩失敗為新增測試用字串wait_for_function違反既有CSP，改為函式而未放寬CSP。相關修復後8 targeted cases通過，包含19照片手機桌面實際解碼及可見署名；完整最終重跑另見證據分支。

512MiB原壓測高水位525.89MiB而失敗。配置診斷保持同資料／API／前端功能，4工作執行緒與單一大型回應完整123樣本通過，高水位438.97MiB。此限制已納入應用lifespan，結束時還原thread limiter；健康／認證／靜態路由不佔大型回應槽。增加來源審核場景又發現NCU整包解壓造成613.37MiB峰值，因此改為逐列串流，僅快取該校所引用的完整來源，快取8MiB且16項上限。所有214校審核列與1882來源列的完整canonical hash符合原本全量json解碼，四校（含最大紀錄）回應逐欄完全相同。相同短負載改善至421.87MiB高水位，135相關測試通過。最終冷／暖完整六校切換、各校生活頁、來源審核與併發仍需跑完；不能以診斷或短測試當最終發布通過。

正式發布仍由父對話協調；相對main59 migration變更0，Quality維持停用，main更新會觸發Render且Actions DB同步不可假定成功。不得把此候選完成／mergeable視作正式上線。

### 第二次記憶體修正與中央第三輪固定輸入

`eb4a5cdd` 的全套非E2E為2264 passed、12 skipped；78個重點瀏覽器案例全部通過。擴充壓測加上六校生活頁與中央來源稽核後仍失敗：暖啟動519.65 MiB、冷啟動521.72 MiB；不得將先前短流程約410 MiB稱為完整通過。

保留上述固定結果後合入中央第三輪 `06bfdfa15e9f773533d3f82e1a136faa99f68104`。共用application_rules的變更僅對中央關閉會混淆院系／自費track的寬鬆校名匹配；其他校沿用原規則。仍有277個成功取得候選待人工查，214合作項目不能視作全校資料完成。

記憶體修正保留全部API、模型欄位及來源證據：中央審核串流與8MiB／16筆快取不變；中正生活欄位按校串流並保留原來源hash／摘錄驗證，僅留四筆序列化記錄；中正104校completion及台大288校生活參考改存序列化內容，使用時回傳獨立完整物件。來源PDF與gzip正文SHA-256改分塊讀取，不保留整份48MB PDF。同步worker上限為2、共用catalogue同時展開1份，health仍可用；partner-source-audit也受相同背壓保護。全套相同負載及460MiB保留52MiB餘裕的門檻以最終固定SHA外部原始紀錄為準，本文不預先宣告通過。

`1a3181fa` 冷啟動完整162步峰值452.54MiB通過；暖啟動在第99步到461.02MiB，仍判失敗。後續將預熱改為lifespan管理的async task：保留15秒健康檢查緩衝，逐步使用既有2個worker與同一catalogue slot，步驟間讓出名額，關閉時取消預熱；不再額外開暖機執行緒。保留預熱預先建立dashboard、失敗步驟不阻止後續步驟及health可用的行為測試；另驗證延遲／進行中的預熱不阻塞health及不超出lifespan。最終驗收在下一固定SHA重跑。

### 臺大第三批固定增量

先封存並推送已通過的 `0d3d671ef92344970e4de1797a81b050235eecbd`：完整非E2E 2287 passed／12 skipped，重點browser 91 passed；同一162步負載修正前556.27MiB，修正後暖454.56／冷458.49MiB，均低於460MiB驗收門檻。實體wheel的5796份內容與來源逐檔hash相同，完整原始結果保存在證據commit `e368f907506f76614958237cdbf4f275fd9e4da8`。UC3M校區名稱已透過校方Colmenarejo照片相簿與官方地圖獨立交叉確認；參考照片未更換，也未將額外查閱的非商用圖片加入產品。

其後僅整合父對話提供的NTU #9第三批 `ed7479073df36deb8fc0393e86fedb102e1cf2b7`，不追浮動head或尚未提供的第四批。新增資料不修改Python runtime或前端邏輯；前述記憶體修復全部保留。獨立核對345份來源正文／12 ZIP、268筆外校引用及178筆人工語義紀錄；原217份正文不變。433筆觀察涵蓋175校，生活evidence共1913筆、272校有任一參考／16校無生活證據；38校缺獨立接待校生活来源屬另一分母。939欄位仍有已取得但未讀正文，3照片及3座標仍缺，不能宣稱全校或當期資料完整。原129候選已做初次分類，也不能繼續一律列作未讀。

中央新browser截圖改遵循VISUAL_EVIDENCE_DIR，保留全部斷言及行為。此第三批合併後的全套非E2E、六校browser、冷暖162步記憶體與套件檢查將使用下一固定SHA重新驗收；上列0d結果只屬前一檢查點。正式邊界與migration=0不變。

### 中央第四輪與淡江第二批

臺大第三批候選8e65c47d完整非E2E2293 passed／12 skipped、browser91 passed；另補跑隔離Docker PostgreSQL2 passed。冷暖各162步456.80／457.52MiB通過460門檻，wheel逐檔hash通過。以上完成並保存後，再整合中央 `358a72e7302476ba8dd19c47c35fc398fc205a47` 與淡江 `88bd00531d9a77fb98ba54dbfd8786cbde18db96`，不採用浮動head。

中央646新增來源、237段落閱讀、45完整原生PDF及2完整圖文PDF；本輪另以公開GET獨立重核47份PDF全部原件SHA相同。115／214為人工參考，319成功候選尚待讀，當期完整批准仍0。淡江264照片（54沿用固定base）、260點（255代表點、5校園點）、139校官方內容；18分片3616成員全部hash核對，原2576不變。264照片全量解碼／hash／校別列對應、207份Commons封存署名授權、54份固定base署名授權與3份原始網頁另核對，六張聯絡表已檢視。未知名額283、照片缺23、位置缺27；校園照片、代表點與當期分配校區維持分開。

共用tku_assets保留本機operator pending／needs_review／verified／invalid優先，再納入照片与地圖不同校區提示；沒有改共用identity或其他五校資料。新增的NCU／NTU截圖輸出改遵循本次run的VISUAL_EVIDENCE_DIR，測試斷言不變。下一候選壓測擴充為175步（原162步全部保留，另加TKU摘要、三份完整原始校別證據、3批8併發與6輪全264照片／260點）；460MiB門檻不變。最終結果以固定SHA外部證據為準，本文不預先宣告通過。

175步初測在59aa522a全部跑完，冷470.74／暖463.55MiB，兩者均未達460MiB門檻。後續將淡江287校完整census存為序列化索引，摘要與單校查詢各自展開完整結果，照片／coverage只取校別ID，避免為取得ID展開全部來源欄位。完整匯出介面仍保留；原別名覆寫順序、欄位內容、來源與照片／位置審核狀態不改。287校與全部別名逐項等值、回傳物件防污染、來源替換失效及既有TKU／跨校案例44 passed；全冷暖與最終功能驗收尚待固定SHA重跑。


共用未核實狀態文案修正：人工驗收在7cb20ff3發現quota=null仍被前台寫成「本期名額待公告」，非規劃列亦寫成「本期沒開放名額」。選校卡片、時程預覽、多計畫、探索條件與advisor改為待核實／待確認，不推定官方未公告或確定無名額。保留零名額、舊期參考、官方明示未公告、pending/blocked行為與所有來源欄位。新增Node語意回歸覆蓋規劃開關、null/zero/reference及日期待確認，61個針對案例通過；完整固定SHA驗收另列證據分支。
