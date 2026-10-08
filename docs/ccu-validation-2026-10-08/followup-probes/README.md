# 修正前後工作目錄探查（不是乾淨SHA最終gate）

這些檔案是後續修正過程的原始證據；它們在有未提交改動的工作目錄執行，**不宣稱屬於e838307或後續任一乾淨SHA完整結果**。最终固定SHA驗收另附。

NTPU問題是`/coverage`僅採用CGU/NTU guide狀態，其他已載入母校資料仍not_collected；實際NTPU206個guide但計數0，CCU55個但計數0。修正採各母校自己guide，explicit-home不回傳其他學校guide。真實bundle四校重新查API：CGU77、NTPU206、NTU288、CCU55，計數不代表全部当期完整。Coverage可採既有audit優先，因此coverage status分布與raw guide不同，沒有改原NTPU/CGU附件或來源。第一次probe誤用destination-profiles的school參數後已另存不作有效驗證；此處after proof使用正確home_school參數。

`race-before`重現舊A回應在新A仍pending時解除loading；`queued-before`重現切母校前排隊的650ms自動儲存遺失。修正後`race-stable`8項通過（390／1440各4）：只延遲實際API bytes送達，保留HTTP/body hash；草稿case控制browser clock，不替換application state或政策response。新detail測試最初誤期待program_scope為「法學」，實際官方欄位為NUPACE／National Chung Cheng University；修正測試與實際來源一致，未改官方資料迎合測試。

`followup-data`10項通過＝既有NTPU4項＋新增coverage/isolation3項＋新增來源/分類3項。Focus結果不能替代後續full gate，遠端CI仍未執行。
