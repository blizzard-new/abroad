# TKU 驗收與續查紀錄（2026-10-08）

本分支為 `data/tku-exchange-20261008`，基準 main `f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59`。使用獨立 worktree，未合併其他学校分支、未改 CGU／NTPU／NTU bundled 資料、未部署或修改正式資料庫。

## 原候選與原始證據保留

`89217e19d55f3ff615964594e5f83eeb6156ba85` 的完整執行為 **1424 passed、39 failed、8 skipped**；未改 main unit 基準為 **1348 passed、39 failed、8 skipped**。wrapper collection error、lock failure、CI failure／0 jobs 均是失敗，不能因與 main 相同而當作驗收通過。

[原證據資料夾（不可變 commit）](https://github.com/blizzard-new/abroad/tree/1159874b7a3d3f48299d18c810646f38396c6ad9/docs/tku-acceptance-evidence/89217e1) 保留原 JUnit、逐步 exit code、瀏覽器、PDF、ZIP 與雜湊。續查結果另綁新的固定 SHA，不覆寫此證據。

## 67 個缺口的逐項續查

[gap_triage.json](../src/exchange_info/official_data/tku/gap_triage.json) 保留原 SHA 的全部 67 個欄位與原文位置，逐項記錄初始分類、查核入口、適用年度、日期、補正後狀態及下一步。初始分類：47 項仍可查、14 項矛盾、2 項官方材料提供途徑、4 項未映射。新增 12 個全文快照並執行限定官方網域的搜尋後，補正 4 項映射；仍有 **45 項在列出的公開範圍內未取得足夠當期內容、18 項矛盾／更正後適用性待確認**。不以搜尋無結果推定「官方尚未公告」。

四項補正為成蹊本期住宿通勤（接機仍未知）、成蹊接受的學期數（精確日仍未知）、淡江當期表直接明示的 JUSST 名稱（2027 外校規則未核實）、2027 NICS 公告直接引用 Form C 的每月60,000日圓以上支弁下限（不是完整實支預算）。每項保留官方 URL、頁碼／原文與限定範圍。逐欄 **89／152 核實，58.6%**，不是完整當期申請就緒。

財金原公告重新開啟為 HTTP200，原502失敗作歷史保留。另讀資管、保險、人工智慧、資傳全文；各系原收件／轉送日期早於中央9/16更正。當期系所期限仍為 null／待確認，未把原公告日期套到更正後梯次。原表空白科系或學制仍為缺值，不改成全系可申請。

128 列（4 本梯名額列、124 舊期參考）、7 名額、本梯校內9/30中午已截止／0 可新申請；53 外校文件、28 原有交換附件與1另補2026參考行事曆。舊英歐／中文清單不是當期開放校名單；新版仍「尚未核實」。

## 平台適配與實際缺陷修復

新增獨立 JLPT N1–N5 欄位，與英語數值分開；API、按母校工作區保存與重載、行為查核一併處理。N1 強於 N2；立命館需N1、一般日語大學部N2、研究所N1；JUSST英語／80分／GPA與研究所豁免保持待確認。未核實年度不借用本梯規則，母校語言通過不能取消「校內已截止」。

`/coverage` 原先只將CGU／NTU既有生活資料納入統計。改以資料母校相符條件計入，修復 NTPU／TKU 已有資料卻報0的情況；保留各校原有資料狀態，不升級來源年份或完整度。

合成、隔離資料確認兩項實際隱私缺陷：證件型內容以201且approved進入訪客GET；刪帳後訪客GET仍保留本名及作者關聯。修復為送出前422阻擋、刪除所有連結身分前先去識別化／清除私人資料，失敗保留帳號可重試。自身POST回應移除author_id屬回應契約修復；原訪客GET已隱藏ID，不能把自身POST當作原訪客洩漏證據。

Supabase 沿用既有原子刪帳RPC；未帶重試header亦走RPC，未完成則503且不落回本機刪除。新增模擬路由與失敗測試；沒有查寫正式Supabase。原SQL去識別化以唯讀原碼與既有遷移測試核對，未把模擬測試宣稱正式DB驗證。

`/docs` 改為不依賴CSP阻擋的CDN資源之OpenAPI下載入口，`/redoc`轉向；補現有路由錯誤回應及已實作重試header的OpenAPI文件，明確同意欄位與AI暫緩標記。沒有把尚未實作的private重試／管理功能加成虛構API。

## wrapper、lock 與 CI

wrapper 原依賴未追蹤 pyc，main／可讀其他分支／歷史均找不到來源。恢復 tracked wrapper 中唯一可還原的RPC回歸為可讀原碼，納入主pytest；未知bytecode測試不能還原，不能宣稱已覆蓋。

uv.lock 只移除 pyproject 早已移除的 pytesseract 遺留套件與root兩項引用；其他套件版本未升級。`uv lock --check --offline`已實際exit0。環境代理只在DNS模擬單元測試內隔離，正式網路／安全設定未改。

quality.yml 的 `jobs.test.env` 使用不支援的runner context。官方文件及已驗release checksum的actionlint重現；改由step將RUNNER_TEMP寫入GITHUB_ENV後lint exit0。與[中正只讀診斷](https://github.com/blizzard-new/abroad/blob/1959d160d6abbce24226396e648777f2c2b55d0b/docs/ccu-validation-2026-10-08/ci-readonly/README.md)一致。permissions、secrets、action pins未動；不證明CI僅有此原因，遠端新SHA的jobs與實際失敗需另記錄。

## 固定 SHA 驗收與合併界線

所有頂層單元檔（含恢復wrapper）、七個相關E2E檔及CGU PDF node在一次pytest執行；逐步包含跨校／詳頁切換、OpenAPI、三個JavaScript、diff、wrapper collection、lock、actionlint。每步前後檢查同SHA與乾淨工作樹，實際exit code、失敗和skip輸出到獨立證據目錄。未選的其他E2E與Ollama整合不算通過。新固定候選結果與39案例逐項診斷由PR與新證據提交記錄。

```bash
PLAYWRIGHT_BROWSERS_PATH=/tmp/tku-browsers .venv/bin/python scripts/run_tku_acceptance_suite.py \
  --candidate-sha "$(git rev-parse HEAD)" --output /tmp/tku-final-candidate \
  --actionlint-binary /tmp/tku-continuation-20261008/actionlint/actionlint
PYTHONPATH=src .venv/bin/python scripts/report_tku_acceptance.py \
  --output /tmp/tku-final-candidate \
  --baseline-suite /tmp/tku-acceptance-baseline-f6ad/suite.xml \
  --baseline-hashes /tmp/tku-acceptance-baseline-f6ad/workflow-hashes.json \
  --baseline-commit f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59
```

[CGU實際比較](tku-cgu-acceptance-comparison-2026-10-08.json)讀77校實際資料，不用測試替身20校或舊摘要冒充完整。新版文件、系所更正時程、NICS／研究生、UEC2027、13組來源矛盾仍是資料阻礙。private重試與多項管理API在現行app未實作，既有看板政策／OpenAPI及UI字面契約未對齊亦需統一整合判定。不能以與main同失敗當作可接受，也不為變綠而擴權或刪除要求。

[共用變更與只讀分支比較](tku-shared-integration-risks-2026-10-08.json)列出registry/API/storage/templates、JLPT profile、UI hook、隱私cleanup、OpenAPI、workflow、lock及測試支架。逐段保留各校dispatch，合併後重產OpenAPI；未修改其他學校資料或worktree。維持draft，不merge main、不部署。
