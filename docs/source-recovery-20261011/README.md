# 四校隔離候選：記憶體修復驗收進行中

目前 [候選5e7114182093fa77203ee946a4f86a88d3b10345](https://github.com/blizzard-new/abroad/commit/5e7114182093fa77203ee946a4f86a88d3b10345)，tree `d6029a2dcf6c8a03b7b5ed217769e874b68a17ab`；[Draft PR12](https://github.com/blizzard-new/abroad/pull/12)。本任務只正常推隔離分支與證據，沒有merge main、production DB或部署，沒有修改Quality停用、Render autoDeploy、保護、憑證或帳務。

固定資料仍為CCU `52ed6370c63f053da445a9aff6eb9e2a3d2ad6c8`、NCU `a2df55b16f72455f7154d7afff44934fc8dbf99d`、NTU `c7357f974faaec8e60ef19698d4d21633c322dc8`、TKU `93cbd9dfee3af95f9ecc89cceb1ccd0e100778af`。相對main59 migration增量0；CGU154／NTPU409／NTU288原workflow逐byte不變。資料來源與全部既有測試函式不受本次記憶體修復改寫。

父指示排隊的新輸入：NCU先前 `48fcc27446f8cadb19f45cae415852af67f76a1e`，19:25只讀核到遠端新head `084f500f091838afe09ddf4f716bffd5ace9b906`，已核實僅11個測試的暫存輸出改動，資料／應用程式不變、所有assert／wait AST相同；NTU `23757a06778f7569716a19987dd1d39effce13f2`。目前只讀盤點固定差異，尚未合入；先完成當前乾淨SHA重驗，再逐hunk接入，並重跑最終完整組合／記憶體／DB，不將來源分支結果當組合驗收。

| 目前5e711418門檻 | 狀態 |
|---|---|
| targeted regression | PASSED：61 cases，含25新增JSON／並行／完整來源失敗不發布快取案例；原NTU/CCU/TKU生命資料完整性與withdrawn圖檢查保留。 |
| contracts／delivery／NCU stream parity | PASSED：原workflow、35SQL／Actions／uv不變，OpenAPI／JS／compile，NTU1373觀察與TKU4529pack成員、NCU214+2177記錄完整核驗。 |
| 完整cache內容 | PASSED：TKU287校13,024,247 bytes→2,148,697無損cache；CCU104校9,310,485→1,123,661；每校canonical bytes／全部公開映射相等、原來源驗證全部執行。 |
| 同175步cold／warm，460MiB門檻 | cold／warm PASSED：175步各完整完成，峰值437.215／447.801MiB，無defer-budget、server log均0bytes。原assert/wait不放寬，僅已授權TKU inventory期望由264圖260點更新為262圖264點，差異receipt保存。 |
| 完整pytest套件 | RUNNING；原四shard最多2組同時，新增25回歸案例，最終以實際collection／四shard聯集為分母。 |
| 本SHA完整Supabase runtime／wheel fresh install | PASSED：35SQL／真Storage／2PostgREST／17治理檢查；wheel6955檔逐hash／CRC，fresh target六校API、原workflow及兩撤回圖切換前後404。此SHA wheel SHA256 `a035d5a3039444fc4bd6914d61f01c21e1fddc2ec266c80b77d0034ab0fa6a7d`。 |

程式修復：TKU與CCU先逐校讀取，再保留無損壓縮不可變快取，按請求還原完整紀錄；不刪來源、欄位或接受條件。TKU首次並行讀取只建一次完整snapshot；截斷JSON／最後一校來源失敗都不能留下部分成功快取。另修正TKU照片撤回工具CLI／package雙匯入。NCU4個測試截圖OUT改至獨立目錄，不改test function AST／assert／wait，已回報父協調源分支同步。

| 保留的歷史原始結果 | 固定SHA範圍，不能混用 |
|---|---|
| 160aeacd | 2919 unique＝2906passed／13skipped；完整runtime／wheel／175冷暖低於460MiB，屬較早資料批次。 |
| 4a011fab | 2970 unique＝2956passed／13skipped／1setup error；另一次單案pass不替代完整失敗。 |
| dbc4afd6 | 2985 unique＝2803passed／43failed／126setup errors／13skipped，0漏列。126 setup的test body未執行；另有Storage ENOSPC，完整runtime未通過。 |
| ca194735 | 完整suite CANCELLED；3085 collected，觀察118 call passed、2967未完成／未執行；4新增NCU模組寫tracked截圖，保存原log與截圖後修復輸出位置。 |
| 7a7c7e35 | contracts、完整35SQL真Storage runtime、wheel與隔離安裝PASSED；cold第8／175取樣472.656MiB FAILED，167步notrun。另跑完整175步diagnostic功能通過但峰值472.055MiB，最終exit1。full pytest未跑。 |
| a731aa07 | 54passed／1failed：照片政策獨立import缺tku_capture_io；保留原log/XML，2d0修復。 |
| 2d0e1a3b | 55focused／contracts／來源核驗passed；cold第107／175步461.191MiB FAILED，68步notrun；其他最終gates未跑。 |
| 80b09999 | 55focused／contracts／來源核驗passed；cold第121／175步460.238MiB FAILED，54步notrun；未放寬門檻，其他最終gates未跑。 |

TKU兩拒用圖：Sunderland錯校圖、UAEMEX授權人／署名鏈未核實圖已移至 `sources/tku/withdrawn-campus-assets/`。7a7的1149應用image hash掃描、最終wheel所有6955檔hash／CRC、六校dashboard前後原URL404均通過。wheel SHA256 `b3e3dfe6c560dfd02c85bb4a89a246b914ff35774d2fe7bcdd596c47a6728953`，現已無損封存成可完整還原的ZIP byte-range recipe，全bytes重新還原hash核驗後才回收重複wheel；原始測試／截圖證據沒有刪除。新候選仍需新wheel與同樣公開路徑檢查。

獨立來源核對：CCU全部21欄差異，19新補欄；離線两輪145資料檔完全一致，保留先前10項體檢、可選換宿與105.40/16日修正。NCU全部26新定位名稱與原數值、兩張照片及18校中文資料變更核對，保留圖爾庫原文件／簽章與明治五個月修正；214代表點／202照片（199唯一），不代表116指定校區或當期開放。NTU全部673新增中文說明、1228原件版本／42ZIP及611引用核驗；原46校獨立接待網域生活來源缺39，全288同標準缺44，任一生活內容缺16。TKU全部320新增M3–M6中文值、108來源／387引用核對，4529pack檔、45分片、262圖片hash與拍攝期檢查通過。原文為風險抽查，不宣稱獨立全文重讀全部作者501組或全網資料。

檢視 [原始run-index](run-index.json)、[完整runtime歷史原始摘要](integration-final4-full-runtime-summary.json)、[發布與回滾計畫](RELEASE-PLAN.md)、[2d0保存點](checkpoint-2d0-55ee3669.md)、[7a7保存點](checkpoint-7a7-a20abe6c.md)。未merge／部署；本地任一通過也不代表正式DB已同步或上線成功。
