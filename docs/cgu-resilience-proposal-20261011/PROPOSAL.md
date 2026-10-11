# CGU 來源中斷恢復：小範圍方案與隔離驗證

日期：2026-10-11。應用程式基準為 PR #8 `9927ec1d8765a9772671bbaa68e7f920995f1258`；main仍為`59a20f27`。本交付只包含方案、獨立原型與證據，**沒有把原型接入應用程式、修改候選來源分支、部署或寫正式DB**。

## 建議採用：一個CGU名冊供應器，共用完整的最後成功快照

可行，但不能只把 `fetch_partner_universities()` 的 `[]` 改成某個固定名單。現有CGU dashboard與workflow各自抓取／快取，必須讓兩者使用同一個具名冊版本與来源狀態的供應器，才不會出現列表與詳情不一致。範圍只限CGU；其他五校的名冊、年度、名額及既有guard不變。

現有兩個缺陷已用完全離線來源回放重現：

1. 冷啟動取得空名冊後，`partner_cache['cgu']` 一直保留空集合；來源恢復，workflow仍404且不再發起來源讀取。
2. dashboard已有77列，背景刷新遇來源失敗卻回傳有效的空dashboard，會把原本77列換成0；同時另一份workflow cache仍可能成功，造成頁面互相矛盾。

這是程式把「來源取得失敗」與「名冊沒有學校」混為一談，而非需要改CGU的年度、名額或workflow內容。

## 快照来源與可追溯性

Repository中的CGU bundle目前只有catalog-completeness、destination profiles、workflows，沒有正式的最後成功名冊snapshot。前輪77列API診斷快照雖有觀測時間，卻未保存兩份來源都成功的收據，而且夾帶視覺衍生欄位；不宜直接升格為production seed。

本輪只做兩次公開唯讀請求，取得目前程式使用的兩份CGU Google Sheets GVIZ來源，均HTTP200、必要欄位結構有效，原始列數64與18。用既有解析與合併邏輯得到77列，沒有另行改寫年度、名額或資格。

- 最後成功擷取：`2026-10-11T09:58:47.453586+00:00`。
- [兩份原始來源及收據](source-capture/receipts.json)，各附URL、HTTP結果、擷取時間、原始SHA-256與schema檢查。
- [提案用快照](source-capture/snapshot.json)：335,285 bytes，77列；記錄內容SHA-256 `afbd6356d0a46e1d593d04f3de5a47a4507c0f553bd3cd4a6e617cff689a3ade`。
- [擷取程式](capture_sources.py)與[原始輸出](source-capture.log)。此snapshot明示`proposal_and_tests_only_not_adopted_by_application`，尚未放入正式app bundle。

77是合併後顯示列數，不等於已確認當期可選校數。`fetched_at`只代表取得來源的時間，不是該頁所有規則已核實為當年度。保留每列原始`academic_year`、`quota`、`quota_status`、`availability_status`、deadline及program options；不得因來源今日取得就改成今日／本期已確認。

## 最小行為契約

| 取得情況 | 顯示與儲存行為 |
| --- | --- |
| 兩份來源成功、結構有效、有可解析名冊 | 原子保存完整新batch；更新來源取得時間；允許合法新增／移除校列，不寫死77 |
| 任一來源失敗、逾時、解析失敗或只取得一份 | 保留上一份完整batch，不混合一半新資料與一半舊資料；更新「最近嘗試失敗」資訊，不改最後成功時間 |
| HTTP200但空表／缺欄位 | `empty_source_needs_review`／`parse_error`；不得自動取代成功快照成0校；真實官方空名冊須另有核對依據 |
| 有已驗證快照、即時來源尚未確認或失敗 | 顯示`last_known_good`／参考狀態、最後成功時間和官方連結；原列值保持不變 |
| 無任何有效快照且來源失敗 | 顯示「名冊暫時無法載入」，數量用「—」；不能宣稱0所／無合作校；依賴CGU目標查找回可重試503，其他五校及六校選單仍可用 |
| 來源恢復 | 單一供應器更換名冊版本；列表、地球及workflow lookup在下一次讀取使用同一版本，清除失敗狀態 |

建議提示文字：「來源暫時無法取得，顯示 2026-10-11 09:58 UTC 最後成功擷取的名冊。年度、名額與申請條件仍以原資料及官方公告為準。」在CGU列表與詳情都可見；不以單純log或最後更新日期冒充已告知使用者。`fresh`也只指來源取得成功，不表示當期規則全部已確認。

### 持久化、快取與512MiB界線

- 載入有效runtime snapshot，無有效者用隨程式版本保存的已查核seed。Render目前沒有持久化磁碟保證，runtime檔案不足以解決重新部署／冷啟動；不申請磁碟、付費服務或新DB。
- 只存CGU partner records及來源metadata，不保存整份dashboard、workflow graph或照片內容。舊snapshot雜湊／schema／school／來源IDs不符就不採用；runtime檔案損壞可退回有效bundle。
- 採temp file＋atomic replace，失敗不清除舊檔。一次只准一個背景取得工作；重試有間隔，不讓每位訪客各打兩次外部來源。
- 使用現有單worker與背景warm-up機制。建議成功後沿用10分鐘刷新節奏；失敗後最多每60秒嘗試一次。讀取有效snapshot不等待外部來源。這是待實作的app內策略，不是新增平台排程。
- `partner_cache`和`dashboard_cache`不再各自保存CGU來源真相。dashboard可繼續快取較重的規章內容，但每次返回所用partner rows、snapshot ID與來源狀態必須一致；來源狀態變動不可被舊dashboard快取遮住。
- 來源新鮮度與資料適用年度分開。來源逾刷新時限即標待確認／参考，後台刷新失敗仍維持原始取得時間；不因例外把任何quota變0，不更改deadline eligibility或發布／治理狀態。

## 預計修改邊界與分工

1. 新增CGU snapshot/provider模組；在`student_view.py`加入結構化雙來源batch結果，讓呼叫者區分取得失敗、空表、有效資料。保留舊list函式的相容介面。
2. `api.py`只調整CGU的partner取用與dashboard建置入口；`build_student_dashboard`可接受已取得的rows，避免第二次独立抓取。CGU來源失敗不能升級成讓所有學校不可用的全域503。
3. 加入可選`catalogue_source`回應metadata與CGU提示UI，更新OpenAPI契約與資源版本；其他學校不填來源狀態，也不改其partner records。若查找目標不在「失效來源下的舊名冊」，不能聲稱已確認不在當期名單。
4. 加入已核實CGU seed及專用新測試（例如`test_cgu_catalogue_recovery.py`、`test_cgu_source_status.py`）。不改NTU接手的13項fixture檔案。

[範圍查核](scope-check.json)：依父端分工，NTU負責13項fixture與缺失原文；本方案處理CGU production取得／快取／回復及新測試。查核時只見PR8、PR9開啟，固定PR9沒有修改上述CGU取得／API／model或13項fixture檔案；其他三校仍做其校別資料。可見變更與父端分工沒有重複。未推送的工作無法從PR diff驗證，正式接線前以父端分工為準。本輪未動任何這些來源檔案。

## 已執行測試，與尚未完成的驗收

[最終原始輸出](isolated-tests-final/stdout.log)、[命令／SHA／時刻](isolated-tests-final/metadata.json)：**20 passed，包含18個獨立原型狀態實驗與2個現有程式缺陷特徵實驗**。後者的通過表示成功重現缺陷，絕不等於應用程式已修好。

18個狀態實驗涵蓋：帶日期的cold-start snapshot、失敗保留所有欄位與時間、HTTP錯誤、錯schema、部分來源、空來源、空records、雜湊不符、跨校snapshot拒絕、無snapshot明列unavailable、來源恢復與真實校列移除、間隔重試、讀者不能污染其他讀者資料、損壞runtime退回bundle、舊版本不能蓋新版本、8讀者single-flight，以及原子replace失敗保留舊檔。零名額、空白、未公告及歷史年度均保持輸入值。[原型](snapshot_prototype.py)只展示儲存與狀態判斷，尚未實作完整HTTP錯誤分類、app介面或UI。

**後續接線必測（本輪not run）**：

- 真正app遇雙來源／單來源故障、恢復及重啟，列表、地球、詳情、workflow、保存／文件流程使用同一snapshot；無snapshot時不能把暫不可用說成0校或不支援。
- 手機390／桌面1440的来源提示及retry；CGU stale來源切到其他五校不殘留警告／資料。
- 正常live資料、fallback資料除新metadata外保持值相同；年度／名額／提醒guard／權限不被來源新鮮度改寫。
- 配合NTU交付的13項固定fixture重跑治理流程，但不接手修改其測試。
- 打包後能讀bundle seed；新取得來源嚴格validation、損壞／寫入失敗及重啟恢復。
- PR6單worker512MiB暖機／並行、PR7年度邊界、全六校回歸、OpenAPI／語法。0.34MB快照本身不是已證明production記憶體安全，仍需量測。

沒有需要新增migration、憑證、權限、付費或修改Quality／Render設定。現在的交付是具體可審閱方案；app修復、最終合成與發布都尚未執行。
