# 9671a106 同 SHA 測試與效能原始證據（仍未驗收）

測試 SHA：`9671a106822a3d11754ea42b3b89a079c881e1ad`。起訖 2026-10-08T22:23:30.250752+00:00 至 2026-10-08T22:46:25.208333+00:00 UTC；兩端及各階段前 HEAD 都固定、工作樹乾淨。`manifest.json` 是 runner 原始輸出，未改寫。此資料夾由後續 evidence-only commit 保存；保存 commit 沒有被這批測試涵蓋，不可冒稱同 SHA 全綠。

- 中央248 passed；共用164 passed／2 skipped。
- 實際52項桌機／手機 browser 結果見 `browser_ncu_ntu.xml`；截圖原件保存在 `browser-captures.zip`，以 SHA256 map 對照。79張來自52項原始run；新潟390的3張在後續冷測被覆寫，原始3張未保留，zip明確標為 `performance-cold-3`，不能冒稱原始52項截圖。原始52項結果仍以JUnit與log核對。
- 後續三個串行、全新 Python 冷啟動測量，直接呼叫未改的原始新潟390函式，維持預設5秒門檻；結果、ASGI／HTTP／body／DOM／LongTask／catalog build次數見 `performance/cold-*.json`。如失敗後繼續量測，只算 eventual observation，不豁免失敗。
- 原始 ded2ed1 的首次49／50失敗仍保留在相鄰目錄。三次獨立原始 SHA 冷測有通過，不能抹掉首次失敗。該首次失敗沒有HTTP timing，無法唯一證明當時原因；另已獨立重現及修復相同catalog key並行冷載入重複解析競態。詳見 `performance-diagnosis.json`，dirty中間測量與cancelled對照明確分列。
- 既有3 modules仍55 passed／10 failed；10個名稱與未改main `f6ad1b8` 完全相同，仍未通過，不能當上線豁免。
- OpenAPI、JS、lock、diff及CGU154／NTPU409／NTU288同schema流程multiset語義差異0。
- GitHub quality [37853183998](https://github.com/blizzard-new/abroad/actions/runs/37853183998) 實際failure、0 jobs；Supabase Preview skipped。根因未取得。Docker／migration／dependency完整CI集合尚未本地执行，這份局部驗證不等同完整CI。
- 資料60 partial／214、154尚可持續整理、0 full116；116母校校別名額預定10/12公告。北海道新查來源留在/tmp，未納入這個測試SHA或覆蓋率。

沒有merge、deploy、正式DB、credentials變更或對外聯絡。必要測試、CI與資料驗收門檻仍blocked。
