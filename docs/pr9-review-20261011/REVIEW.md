# PR #9 首批唯讀審查與 PR #8 整合面 — 2026-10-11

審查固定 NTU head `4566f7f2b51b3b5c188f5394a56d7b5df190d1c5`（Draft PR #9），PR #8 head `9927ec1d8765a9772671bbaa68e7f920995f1258`，共同 base `59a20f27fcee00fb597abc79e75ec11778317422`。未套用兩分支合併，未建立任何合成 commit，未修改候選來源、main、正式 DB、部署或外部設定。審查期間沒有 push 或 PR comment；其後依父端明確指示，僅將本報告與診斷封存到既有純證據分支。

## 結論

這一批的直接記錄改動可與 PR #8 協調，但不能據此批准最終整合／發布。13 個作者報稱 baseline failures 並非在所有 main 環境固定失敗：根因是測試依賴 CGU 即時 Google Sheets，來源失敗後名冊為空。已用獨立正常 main、PR #8、來源故障注入、離線保存名冊四組證據定位。資料不足仍如作者所列：9 張照片、18 組座標、147 校獨立官方生活來源；130 筆接待校参考不表示本期規定完整。

## 發現 1：13 個失敗是外部 CGU 名冊依賴，不能作 baseline waiver

作者原日誌：[baseline-same-failures.log](pr9/docs/ntu-completion-20261011/validation/baseline-same-failures.log)、[full-regression.log](pr9/docs/ntu-completion-20261011/validation/full-regression.log)。

| 獨立診斷 | 原始結果 | 證據 |
| --- | --- | --- |
| 精確 main59 原始碼＋原始測試，在本環境正常來源 | 13 passed，58.08s | [stdout](baseline-13-complete-tests/stdout.log)、[metadata](baseline-13-complete-tests/metadata.json) |
| PR #8 固定 head，相同 13 個 test IDs | 13 passed，77.94s | [stdout](pr8-13-independent/stdout.log) |
| main59；僅對兩個 CGU Google Sheets GVIZ 讀取注入 RequestException | 13 failed，12.22s；test IDs 與作者完全相同 | [stdout](baseline-controlled-cgu-outage/stdout.log)、[review-only plugin](cgu_source_unavailable.py) |
| main59；使用前輪獨立保存的 CGU77 名冊作離線 fixture | 13 passed，21.29s | [stdout](baseline-offline-recorded-cgu/stdout.log)、[review-only plugin](cgu_recorded_catalogue.py) |

失敗分群為 10 個 workflow/issue-report 測試在取「林肯大學 Lincoln University」時先 404；2 個 experience-digest 測試找不到「北京清華大學 Tsinghua University」，出現 404／沒有 sources；1 個 request-origin 測試因 CGU 名冊沒有照片而找不到 localhost 圖片 URL。前兩群多未走到要驗證的治理／心得斷言。

程式鏈：`student_view._fetch_sheet_rows()` 直接讀 Google Sheets，遇 `RequestException/ValueError/JSONDecodeError` 回 `[]`；`fetch_partner_universities()` 合併兩份來源；`api.partners_for_university()` 把結果（包括空集合）寫入 app 的 partner cache；`partner_context_for_school()` 只能从該名冊匹配目標，故後續回404。這個外部依賴在 main 與兩 PR 間未變。本環境普通 main 可以通過，來源故障可精確重現全部13項；沒有證據把失敗歸咎 PR #9 的 NTU 資料。

原作者日誌沒有保存這兩個上游請求的 status/body/parse error，因此不能進一步斷言當時為503、TLS、Google封鎖或解析格式改動。可確定的是 CGU 外部名冊缺失這條失敗機制，以及原測試沒有固定此 fixture。生產冷啟動若遇同樣狀況也可能把空名冊留在 app cache，這是既有可用性風險，不是本輪已修復項目。

下一步：把這13項業務驗收改為明確的離線名冊 fixture，另立來源取得失敗／恢復的測試，再重跑治理／删除／匯出流程。不能把原始13 failed改寫成已通過。此次只是證明原因，沒有替任何分支改測試或改 production fallback。

最初節錄 baseline 測試時漏了一個被 import 的測試 helper，造成 collection error；已保留 [初始失敗](baseline-13-independent/stdout.log)，補上完整原版 tests/*.py 後才得到上述正式獨立結果。

## 發現 2：原始已採用來源未隨 Git／ZIP 交付

60 個 `public_source_reviews` 都能連到 host-access 收據；其中59有 body hash，1筆明示 `primary_web_tool_cached_read`，沒有把此快取讀取算成取得原始正文。

然而這些收據所指的 `sources/<id>.html/.pdf/.txt` 不在 PR 的 Git tree，也不在12檔的可回填ZIP。ZIP只有表格、報告、結構化整理、收據與驗證摘要；13張圖片在 Git 中，但 ZIP 亦不是可直接部署的完整 asset package。詳見 [逐來源交付核對](reviewed-source-delivery.json)。

這不證明130項中文整理錯誤，但目前無法在不重新連線的情況下逐筆核對正文／PDF頁碼／日期與翻譯。79段生活內容是附日期與scope的中文整理，`original_excerpt=false`、`original_text`空白；它們不是79段逐字原文。建議原任務補交已採用的59份原始來源及可定位文字、或等效可重現取證；快取讀取那筆保留限制。不要把另外2772次訪問紀錄或成功1466次當作1466項已核實規定。

## PR #8 / #9 整合面

1. **直接共用修改僅1個檔案**：`src/exchange_info/official_data/university_locations.jsonl`。PR #8新增四校母校點；PR #9只將 ENS Ulm 一筆合作校座標從 needs_review 改為 verified。是不同 record，不需覆蓋整份檔案；最後必須同時保留四校母校、ENS 校區限定與其他原有點。
2. **共用照片有跨校效果**：PR #9 更新13個既有 manifest keys，新增13個檔案。用 PR #8 的視覺索引作唯讀投影，除 NTU13筆，CCU與NCU的馬來亞大學各一筆會由 needs_review 轉為可顯示相同新照片。[完整投影](pr8-matcher-pr9-asset-impact.json)。這是新來源可被共用的正常結果，但需納入兩校手機／桌面／來源及授權顯示回歸；「其他校目錄未改」不等於「其他校展示完全不變」。
3. **建置順序**：NTU destination builder 先重放舊288校 snapshot（照片、座標、生活），再套 completion。它以各校名字鍵寫共用清冊，可能覆蓋其他資料分支後來對同校資產的修訂。應先在各自固定來源下產出結果，再在合成候選逐 record/hunk 協調；合成完後不可無審查重跑單校全量 builder。這次沒有實際跑合成 builder。
4. **版本與驗收**：最終素材集合確定後按 PR #8 規格協調清冊與前端資源版本。現有 `fetchJson` 預設 `cache:no-store`，不能把未改清冊 URL 直接報成已證實的圖片快取 bug。實際合成後仍需完整瀏覽器、所有可靠點、缺漏狀態、授權 credit、mobile/desktop、跨校帳號／文件／論壇及512MiB回歸。
5. **沒有 DB 順序相依**：PR #9沒有 migration、依賴、workflow設定或共用 app.js 修改；無理由為審查先動正式DB。main仍由父端控制，且四校資料還在追加，不固定最終合成SHA。

## 已獨立核對與尚未核對

[獨立檢查JSON](independent-review-checks.json)、[snapshot validate輸出](validate-snapshot.log)、[13張照片檔案與來源metadata](asset-review/photo-source-proof.json)、[共用記錄差異](shared-record-changes.json)。

- 13張新圖片的 Git blob SHA-256全部等於 completion 與 manifest 的宣告；作者、CC授權、URL及具名校區欄位存在。只抽看了馬來亞與聖安德魯斯圖片，未把 metadata 驗證冒充13張逐一獨立授權／校區現況重認證。
- 288校的 eligibility/quota/application_deadline/availability_status/source_url/country/school_name與main逐值相同；NTU workflow檔案逐位元相同。
- PR #9 snapshot `validate()` 通過（使用未改的 model/schema依賴，只讀讀取抽出的PR #9資料；沒有執行apply_completion或合成build）。
- 130筆期間分類核對為86無年度參考、33明列目標年度事實、7舊年參考、3版本矛盾、1明示待公告。全部保留 `selection_rule_confirmed=false`；不把33筆當臺大甄選已確認。
- ENS點的來源記錄明示45 rue d’Ulm、object location、非photographer position、`assigned_exchange_campus_confirmed=false`；仍需最終整合時保留此範圍。
- 照片品質建議：聖安德魯斯的已授權影像是 JF Allen 圖書館內門，來源校区有記錄，但作學校縮圖辨識度低，可由原資料任務繼續尋找更清楚的代表校舍。不是據此認定授權或校名錯誤。

**Not run**：PR8+PR9合成後E2E／記憶體、全repository重新回歸、130筆參考的全文獨立語義複核、四校最終合成、正式發布／正式DB。作者原36 focused／13 browser／2163 passed 13 failed 13 skipped仍僅列為作者交付原始結果，沒有標成本轮全部獨立重跑。

原始本地證據保留在 `/workspace/pr9-review-20261011`，本交付副本僅位於 `artifacts/globe-coverage-20261011` 純證據分支，未寫入任何 PR 來源分支。下一步先回原 NTU 任務補來源交付與可重現fixture，再等待其新的固定SHA和其餘三校交付。
