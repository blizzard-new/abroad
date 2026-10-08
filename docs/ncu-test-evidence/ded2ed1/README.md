# ded2ed1 原始測試證據（不是驗收通過）

測試 SHA：`ded2ed1a79a5f3cb009655790eb560816a7af61a`。此目錄是測試結束後的 evidence-only 保存；保存此目錄的後續 commit 沒有被這批測試覆蓋，不可改標。

原始 run：2026-10-08 21:00:12–21:30:29 UTC。起訖 HEAD 都是上述 SHA、工作樹乾淨；runner 每階段前亦檢查。`manifest.json` 未修改，原來 /tmp 路徑由同目錄檔名與 `browser-artifact-map.json` 對應。`freeze-and-results.json` 分列原始 runner 核對、事後獨立 healthcheck 與後續同 SHA 重跑。

- 中央236通過；共用158通過／2跳過。
- 50項 browser：49通過／1失敗，完整 `browser_ncu_ntu.xml` 和 `.log` 保留。新潟390手機在流程 API 尚載入時，5秒文字等待失敗；未判定為功能或效能根因。
- 同一 SHA／原始5秒測試連續手機重跑2次通過，JUnit和log各自保存；這不抹除第一次失敗，不代表50項全綠。
- 既有3 module55通過／10失敗；未改main同名10項重現，仍是未通過，不能作上線豁免。
- OpenAPI、JS、lock／diff、851份同schema流程multiset語義差異0。
- GitHub quality實際failure且0 jobs，Supabase Preview skipped；根因未取得。完整CI集合尚未本地执行。資料59 partial／214、155未整理、0 full116，資料門檻仍失敗。

`browser-captures.zip` 保存實際同 SHA 原始通過案例截圖；phone-repeat-2的三張圖是另次同 SHA 重跑，沒有替換失敗回合。未採強制點擊／隱藏overlay；全用隔離本地 API／資料，沒有正式DB、合併、部署或對外聯絡。API及繪製時間將另外量測，單純放寬timeout不是效能修正。
