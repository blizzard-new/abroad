本分支恢復CGU公開名冊來源，整合六校資料及照片／地球識別，保留未知、待審、歷史參考與明示零。最新已推送檢查點為 `8e65c47d1d42bd0d065ff53c8d6572d0be994bf2`，包含NTU第三批ed747907、NCU第三批06bfdfa、CCU cf4d86f、TKU第一批f4819dab與PR8。

驗證：完整非E2E2293 passed／12 skipped，重點browser91 passed；另隔離PostgreSQL2 passed。冷暖各162步，HWM456.80／457.52MiB低於460MiB門檻。wheel逐檔hash、原workflow154/409/288、OpenAPI及35份migration語法通過。

[固定原始證據](https://github.com/blizzard-new/abroad/blob/985b72be0c02968cbd9c7ff0e8d3c9ba280e5466/docs/source-recovery-20261011/checkpoint-8e65c47d.md)。沒有merge main、正式DB或部署，也未改Quality、Render、保護設定、憑證或付費。資料仍未全校完成。

後續NCU第四輪358a72e7與TKU第二批88bd0053正在隔離工作樹驗收，尚未推入此PR。新增資料175步冷470.74／暖463.55MiB失敗已保存，正在修復並重跑完整流程，不能沿用本檢查點通過結果。正式發布仍由父對話核對production SHA／DB版本／備份後協調。