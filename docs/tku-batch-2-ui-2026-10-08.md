# TKU 第二批：已查內容的詳頁顯示修正

第一批推送不代表全部交換生資料整理完成。2026-10-08 繼續在原分支補齊資料。

`tku_student_view.py` 原本只填 raw eligibility/application_info/tuition_info，前端讀取的 `student_summary_zh` 為空。本批新增直接由已審查欄位生成的母校／外校摘要，保留 JLPT N2/N1、學制、總平均與前40%矛盾、系所推薦、校內已截止、文件步驟、淡江全額學雜費及外校費用，附適用年度與頁碼提示。未把已截止改成可申請。

實際驗證：13 個 TKU 測試通過；Chromium 逐一點開四校詳頁，確認母校語言、申請步驟、學費文字均可見，page errors 0，桌面及手機篩選仍正確。`scripts/check_tku_browser.py` 已保存此逐校檢查。

CI 狀態：`92fc2fedc80db36993a5f20dc5aceeff728c1b3c` 的 [quality run 37719707403](https://github.com/blizzard-new/abroad/actions/runs/37719707403) 為 completed/failure；jobs 與 check-runs 皆空，取得 log 回傳 `failed to get run log: log not found`。不能把沒有 PR checks 說成 CI 通過。
本地 `scripts/export_openapi.py --check` 明確發現 contract drift。新增的 availability enum 必須同步凍結契約；已重新匯出 `docs/api/openapi.json`，此檔是第九個共用整合點，後續多校整合需一起整理。沒有改 CI workflow、憑證或權限設定。

長崎的 2027 Spring NICS 與合作校目錄已找到，正在逐份讀附件；此批先修顯示，尚未宣稱該校內容全部核實。下一批會分開校內／外校文件、conditionality 與來源，建立逐校逐欄矩陣。
