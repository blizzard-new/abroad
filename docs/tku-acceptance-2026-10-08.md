# TKU 使用者驗收候選與重現方式

本文件取代第四批文件的「最新交接」說法；第四批及更早測試數字是歷史結果。最終完整測試的 SHA、實際通過／失敗／跳過數、遠端推送與 CI 結果，在同一 [draft PR #2](https://github.com/blizzard-new/abroad/pull/2) 交付。不能把先前 c602ec3 runner 的退出碼 0 當作整套通過。

## 可開始驗收的範圍

128 個計畫列中，當期可核實名單只有 **2027–2028 日語第二次甄選 4 校、7 名**；校內 2026/9/30 12:00 臺北時間已截止，**0 個可新申請選項**。124 個英歐／中文舊列仍是參考，新版為「尚未核實」，沒有任何官方「尚未公告」宣稱。四校 152 格只有 85 格 verified（55.9%），67 格保留原缺口狀態及來源。不能以此宣稱全學校／全年度申請可用。

驗收可涵蓋瀏覽、篩選、比較、條件與收藏保存、既有提名者文件查核及兩種準備稿。已截止選項不進入新申請志願，沒有正式期限提醒。流程未發布，當期公開表格可開啟不等於資格或流程已審查。兩份 PDF 是平台準備稿，沒有冒充官方格式。

## 人工驗收清單

使用隔離本機測試帳號，在 390px 與 1280px 各走一次：

- [ ] TKU → 臺北大學 → 長庚 → 臺大 → TKU：標題、名單、原生年度、目標文件與來源各自正確。
- [ ] 從 `?home=淡江大學` 的文件中心網址進入，改選臺北大學後導航及重載仍為臺北大學；返回 TKU 後 query 與文件中心也跟著更新，不被舊分享網址切回。
- [ ] 名單 4 校；只選開放時 0 校。日本／東亞／名稱篩選、收藏 2 校、比較名額及重載保存。
- [ ] 九學院、44 學籍單位可選；學籍目錄來源可開啟，但不當作交換資格白名單。學業條件與科系重載保存，沒有閉期推薦。
- [ ] 四校文件清單分別 23／19／18／25 項；條件、年度、待確認／參考狀態及原檔／來源連結可見。
- [ ] 立命館 COE 是「外校申請後」，**11 月上旬至 12 月上旬、早於 12 月下旬 offer**；行政書士另通知，沒有虛構確切截止。官方 2027 春簡章 PDF p.2／p.20；實際 workflow 與目錄一致。
- [ ] 成蹊一般表格寫聯絡母校承辦，只有 COE 依官方 p.2 明示向 nominated students 另通知。長崎 NICS／研究生對應仍待確認；UEC 表格為一般參考、2027 版未核實。
- [ ] 六組校對 A→B→A、取消、延遲舊回應、未知年度清空，均不殘留前校文件。既有準備目標重載保存；閉期正式計畫預覽停用。
- [ ] 自傳及研習計畫各填 `chinese_text`／`japanese_text`，重載保存後下載；PDF 母校、準備稿標示、中日文內容、字型與頁面均可讀。省略日文時 manifest 確實列缺值。
- [ ] 四校詳頁的 workflow、14 個生活區塊、38 個完整度欄及來源連結可查；沒有 page error 或橫向溢出。

## 這次補正與保障

COE 原本因粗粒度「行前」分組被誤投影成 post_offer，已改 explicit after_application，保留 approximate range／通知方式，不製造時間戳。外校收件与母校甄選維持分開。

新增文件 metadata 曾改變三個原母校 851 筆內容雜湊。空預設 metadata 現在沿用舊序列化；有效 TKU metadata 仍加入內容雜湊。完整比對器讀未改 main f6ad 的 851 個實際雜湊，記錄差異，不只比較資料檔名或數量。

PDF 實際渲染發現既有外部 CJK CMap 字型路徑在本機只顯示表格，文字擷取卻能成功。TKU 準備稿改用內嵌 Noto Sans CJK TC 完整中日文字形字型；只作用於 TKU，CGU／NTPU／NTU 仍走原字型路徑。[原字型版本、來源雜湊、衍生方法](../src/exchange_info/official_data/tku/fonts/provenance.json) 與 OFL 授權隨校別資產保存；不是交換附件。兩個模板 × 兩個寬度都驗證實際內容、內嵌字型、render stderr、頁數及深色字形像素，避免表格框線造成假通過。

Runner 現在任何子檢查非零就非零退出；SHA 不符或工作樹變動會中止後續項目。四個隔離 Git repository 測試確實造成子程序失敗、dirty、clean commit 變動與錯誤起始 SHA，確認不能報綠。

最新 CCU 差異的 `?home=` 修正提示另一條路徑：本候選 a6035e3 曾實際重現從 TKU 分享網址改選臺北大學後，hash 導航又被舊 query 切回 TKU。登入帳號還原亦會覆寫已選分享網址，兩個新案例實際重現此 reload 問題。因此獨立補正 explicit school choice 的網址同步，以及 account restore 對有效公開校目錄選校的保留；帳號學校身分與後端授權未修改。增加兩個真 UI 案例，没有合併 CCU 分支。先前不帶 home query 的切換通過，不等於這條路徑已覆蓋。此補正後須用新 SHA 重新完整驗證。

## 最終完整測試與誠實限制

固定乾淨候選 HEAD 後，一次 pytest 跑全部頂層 unit 檔（只有既有缺失 pyc wrapper 另試）、七個相關 E2E 檔與 CGU PDF node。再依序跑跨校／詳頁 switching、OpenAPI、兩個 JavaScript 語法、diff、wrapper collection、uv lock。每步前後核對同 SHA／乾淨工作樹，證據出到 `/tmp`。

未改 main f6ad 完整 unit 基準實際 **1348 passed、39 failed、8 skipped**。已有 39 項失敗不能算本分支通過；最後結果逐 case ID 比較新增／消除失敗。root conftest 的「Phase C data reviewed」跳過與 Docker opt-in 跳過均保留原因。缺失 pyc wrapper 的 collection error 獨立列為 error。未選的其他 E2E、Ollama 整合沒有執行，不能宣稱全專案瀏覽器驗收。

`uv lock --check` 在本分支與基準已實際指出 lockfile 需更新；不改 uv.lock 掩蓋問題。UV cache 使用 `/tmp`，避免唯讀 home cache 錯誤干擾診斷。先前遠端 quality run failure／jobs 0、Supabase Preview skipped 不是 CI 通過；最終 SHA 會另核對。

```bash
PLAYWRIGHT_BROWSERS_PATH=/tmp/tku-browsers .venv/bin/python scripts/run_tku_acceptance_suite.py \
  --candidate-sha "$(git rev-parse HEAD)" --output /tmp/tku-final-candidate
PYTHONPATH=src .venv/bin/python scripts/report_tku_acceptance.py \
  --output /tmp/tku-final-candidate \
  --baseline-suite /tmp/tku-acceptance-baseline-f6ad/suite.xml \
  --baseline-hashes /tmp/tku-acceptance-baseline-f6ad/workflow-hashes.json \
  --baseline-commit f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59
```

## 資料與合併阻礙

缺口包括英歐／中文新版、系所較早截止、長崎 NICS／研究生映射、UEC 2027 專屬文件、13 組來源矛盾及 JLPT 專用 UI 自動比對。系所轉知頁只核到標題，內文 HTTP 502，未提升成當期適用證據。逐欄／逐文件原文與狀態在 [acceptance_gap_audit.json](../src/exchange_info/official_data/tku/acceptance_gap_audit.json)。

CGU 對照讀實際 77 校流程，不用 E2E 替身 20 校或舊摘要冒充全目錄；見 [實際對照 JSON](tku-cgu-acceptance-comparison-2026-10-08.json)。NCU／CCU 只讀差異，沒有合併新分支；共用 14 檔重疊與處理原則見 [整合風險 JSON](tku-shared-integration-risks-2026-10-08.json)。其中 registry/API/storage dispatch、文件 metadata／public-form 例外、年度／梯次與 UI handlers 必須各校保留；完整合併後重產 OpenAPI。

可開始有限 TKU UI／證據人工驗收；完整當期申請與整體 release ready 仍受上述資料、既有測試與 CI 阻礙。本分支維持 draft，沒有合併 main 或部署。
