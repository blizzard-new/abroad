# 中正候選版與其他學校分支整合風險

2026-10-08 重新 fetch，`main` 仍為 `f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59`。只讀取其他分支的 commit 與 diff，未合併、checkout 他校或寫入其他 session。精確逐檔 SHA-256 與 diff hunk 見 [機器紀錄](ccu-integration-risk-2026-10-08.json)。中正新增資料在 `official_data/ccu/`；本輪校別 adapter 為 `ccu_overseas.py`、`ccu_profile.py`，學制篩選分類在 `ccu-academic-units.js`。

| 分支／已觀察 SHA | 與中正重疊 | 必須協調的內容 |
| --- | ---: | --- |
| NTU 原第三校 `daad399fd3cadf2ba9414fd85d0d3b76154bbbf6` | 0 | 原第三校已在本次 main 基準，不再重複合入。 |
| NTU photos/globe/life `b8833a6a6ffc8236276fa7870e4c1ff541c34117` | 2 | `api.py`、`static/app.js`：目的地生活 dispatch、照片／地圖呈現及中正欄位 renderer；不能以一校檔案覆蓋另一校修改。 |
| NCU `1bddf5a154e2283e17cbb5c1ab554089385e033c` | 12 | registry/API/storage/template 新增 school dispatch；models 條件文件欄位與中正 evidence 欄位；資格分支、計畫任務、共用 app/index、OpenAPI 及 package data。 |
| TKU `61659fe12cf5bb5f3fed2502f112039c7f8abd92` | 9 | registry/API/storage/templates/models 與 app/index；淡江加入目標／母校切換請求失效與 context key，中正未合入淡江檔案，本輪獨立修正並以8項手機／桌面測試覆蓋母校A→B→A、目標／detail晚回應及切校前排隊草稿；跨分支helper/context合併仍需隔離整合重測。 |

中正累計 14 個共用程式路徑，另有 `pyproject.toml`、`docs/api/openapi.json` 與 `uv.lock`，合計17個共用合併路徑。本輪在共用 `app.js` 修復母校切換空值報錯及分享URL舊home參數回切，同時增加校別篩選分類選項 hook，`index.html` 更新腳本版本；既有其餘共用修改清單見 [資料交接](ccu-exchange-audit-2026-10-08.md)。不能直接採用任何一個完整共用檔覆蓋其他分支；應逐個 school dispatch、schema 新欄位、來源狀態與前端生命週期合併，然後重新 export OpenAPI。

跨校最終驗收順序：在另行安排的隔離整合分支固定所有 heads，確認 main 基準與原始資料 hash；合併必要共用程式後，重新跑手機 390／桌面 1440 的真實选校、母校與目標校切換、兩種配對、收藏比較、當期／舊期官方表格、分階段／條件文件、計畫與草稿保存重載。須特別加入快速切換及延遲回應情境。此 session 的真實 API/UI 測試覆蓋本中正分支四校，不代表尚未執行的六校合併結果。

既有 NTPU `destination_profile_count` 預期1實際0為實際API邏輯問題；本輪修正各校自己guide計数，相關10項focused regression已通過，最終候選須另做完整同SHA驗證。GitHub 對上一個中正候選 `2528ede75412e1f353ce6466467cd02579fe6191` 的 quality run `37835187099` 結果為 failure，jobs 為 0：没有執行測試，不是 CI 通過；未更改 CI、憑證、權限或安全設定。最終候選另需核對遠端實際 run，不以本段代替。

資料完整度也有独立阻礙：55 校均仍為 `legacy/official_partial`、0 校具完整已核外校文件清單、0 校 17 欄全當期。缺值、未核新版與矛盾須依逐欄來源繼續確認，不可以 UI 能呈現當成 CGU 同等當期資料已完成。

本輪重新fetch後四個其他分支heads均維持表列SHA；未合併任何其他分支。共享路徑17個未新增；新增guard與coverage修正在同一API/app/index，逐hunk合併，不整份覆蓋。[CI唯讀診斷](ccu-validation-2026-10-08/ci-readonly/README.md) 已定位job.env使用runner context錯誤；提出副本驗證patch，正式workflow未修改。其他分支合併、遠端CI、Supabase及依賴稽核不在本輪已通過宣稱內。
