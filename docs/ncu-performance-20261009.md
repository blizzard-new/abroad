# 中央瀏覽器超時與啟動成本：有界診斷（2026/10/9）

原始9bf90c8固定SHA的56個browser為52 passed／4 failed；同SHA一次四項重跑通過不能證明根因已修。本輪保留原測試、30秒page/load/search timeout及5秒來源內容斷言，新增一次四案例有界診斷（最多600秒，不重試），同SHA4 passed／200.41秒。診斷僅由/tmp插件記錄請求headers／完成／失敗、事件迴圈延遲、頁面路由與搜尋可見性、CPU及函式時間；沒有更改正式程式或測試等待。

| 原失敗 | 本輪觀察 | 結論與未解 |
| --- | --- | --- |
| 太原農林來源稽核5秒仍預設文字 | 來源HTTP、完整度及兩次欄位JSON讀取有顯著CPU成本；本輪內容完成且原斷言通過 | 有可修的重讀成本；原失敗時沒有事件紀錄，不能證明是唯一原因 |
| 復旦搜尋fill30秒因不可見 | 本輪搜尋在partners路由可見，到打開詳情才隱藏；原fill通過 | 原先路由／可見性問題未重現，未關閉根因 |
| 臺大advisor document load30秒 | 本輪DOMContentLoaded1.11秒、load1.25秒，原goto與保存／重載內容通過 | 本輪無同種失敗，不能用通過取代原失敗或證明已修 |
| 北大partners document load30秒 | 本輪DOMContentLoaded3.33秒、load3.92秒，原goto與新TOEFL警語通過 | 同上，原load卡住原因仍未證實 |

一次隔離cProfile的bundled工作流程冷建置1065份耗5.367秒wall／5.367秒CPU；其中structure3.190秒、JSON驗證／讀取2.131秒，熱讀0.000426秒且回傳独立list。這是帶剖析開銷的一次loader測量，不是整體Web啟動，也不能把新潟局部原5秒斷言當整體冷啟動門檻。既有9.88／6.18／18.64秒冷建置與本輪測量均保留，不以一次較快值抹除波動。

## 已證實的重複工作與修正

本輪首次四個public-translations請求同時錯過lru_cache，各執行同一3292筆有效離線翻譯的載入／驗證：各約7.52–7.57秒wall、1.84–1.86秒thread CPU，共7.44秒CPU。lru_cache允許並行miss重做，不是資料損壞。現在只把該離線bundle的快取查找與首次載入放在專用lock內；翻譯來源key、數字驗證、machine標籤、AI同意與服務開關沒有更動。並行六呼叫測試確認只讀／驗證一次，無效數字仍拒絕，讀取失敗後可重試。

中央field-audit約17.35 MB、source-evidence解壓約18.45 MB，完整度與稽核原先每次重解析。診斷四次ncu_field_audit共4.33秒CPU；八次隔離API測量第二輪仍各0.566–0.867秒。現在中央兩份immutable snapshot依路徑＋mtime_ns＋size保持最多兩筆快取、並行首讀互斥；只複製單校與所選來源回應，避免呼叫端改壞共享snapshot。檔案版本改變立即重新取得，未知校仍404；原文、URL／頁碼、年度、閱讀範圍與公開摘錄規則維持原值。

cache改动只针对離線共享翻譯與中央來源讀取；没有改流程實際條件、年度、提醒或發布狀態。API、public_translation與NCU adapter需要列入共享合併點；不覆蓋中正／淡江，也不處理淡江負責的CI workflow。

## 證據與驗證界線

39項預驗通過，包括新增7項並行／版本失效／失敗重試／防突變、既有翻譯、生活、工作流程快取回歸；預驗不是固定候選提交SHA結果。全部214份來源稽核回應及3292有效離線翻譯另以canonical JSON SHA核對，固定SHA測試、API前後數值與原browser結果續記。

基底診斷原始manifest／JUnit／事件JSON／cProfile與一次API測量位於/tmp/ncu-bounded-performance-9bf90c8，後續證據專用提交保存可公開的原始檔。Playwright trace只留本地/tmp，可能包含隔離測試session headers，不公開原trace。四項沒有重現的根因保持未解，不做無限重跑或純增加timeout。

資料不變：這個效能候選仍62 partial／214、152待整理、0全116核准。下一個可完成的資料批次是已在另一工作樹整理的關西國際／駒澤／東北三校，預驗33 passed，尚待六個實際手機桌面案例及候選SHA驗證；其後東京市／富山／福井已開始官方原件續查。沒有merge、部署、正式DB、credentials／security設定更改或聯絡學校。
