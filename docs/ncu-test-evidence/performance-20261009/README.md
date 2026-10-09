# 中央效能有界診斷的原始證據

這是62 partial／214的效能階段，不是65項Japan3候選驗證，也不代表資料驗收或CI通過。沒有放寬原測試timeout／斷言、沒有無限重試。

| 目錄 | 固定實作SHA／結果 | 解讀界線 |
| --- | --- | --- |
| baseline-9bf90c8 | 9bf90c8748fd33747c625e1f5154f6838540d64a；一次原四失敗案例4 passed／200.41秒 | 沒有重現原失敗；與原56個52 passed／4 failed的歷史證據分開 |
| bounded-b29e28f | b29e28f00c6118eb9925b9bc72ad6ce4782dd043；一次四案例4 passed／129.28秒 | 可觀察重複首讀消除，不是四種原始timeout的唯一根因證明 |
| candidate-b29e28f-stopped | 279 NCU；191 shared passed／1 failed／2 skipped；65 gate | 包裝漏保留cache_clear造成新回歸；browser啟動後停止，未完成部分不標通過。3張中止前截圖另留 |
| candidate-3b14037 | 3b1403701edc957bba1796f30dae1a6bc0bf4712；279 NCU、193 shared／2 skip、65 gate；原browser55 passed／1 failed | 原GPA重載值5秒仍空白的失敗保留；固定起迄SHA／clean proof、94張browser及failure截圖另列；necessary_local_tests_passed=false |
| supplemental-ntu-restore-3b14037 | 同3b，一次原單案例1 passed | 只定位函式時間／還原順序；不能覆蓋前次失敗或稱根因關閉 |
| supplemental-boot-v4-3b14037 | 同3b，一次新Python程序原新潟5秒斷言passed，boot-ready10.021秒 | v3三輪boot-ready欄缺值未改；v4修正timer處理splash移除。100毫秒取樣；published建置包含bundled |

JSON大檔以確定性gzip保存原bytes；原始log／JUnit／profiles未修改。`checksum-manifest.json`逐檔記錄原始及儲存SHA，圖像ZIP列每張PNG SHA。Playwright原trace ZIP留/tmp，因可能帶隔離測試session headers；公開事件JSON不含header值／response body。這不改動正式credentials／security。

原始`baseline-9bf90c8/bundled-cold-profile.txt`有1處、`candidate-3b14037/browser_ncu_ntu.xml`有2處原生尾端空白；不清洗原始證據。diff-check僅豁免這兩個精確檔案，其餘已提交檔案照常檢查。

`scripts`是本輪實際外部計時插件與執行命令，並非正式測試的timeout替代。`preview`保留未提交時39項預驗及cache介面補回後22項預驗，不把預驗當固定提交結果。`supplemental-driver-proof`保留兩項補測完成、Japan3尚未完成時的原始driver manifest，具起迄SHA和原工作樹狀態。

214份完整source-audit的canonical SHA為d1ad9dad458c83b0fa66f433ba5412b06607c9e62b0fff51ca5efdae57e5a0fb；3292筆有效翻譯為b10197e4cbab0c802b308712e0837e9570fc6f7752fc60a862605287ff3c6b43，前後值不變。原audit-endpoint量測v1因學校名未含「(校級)」而StopIteration，失敗script/log也保留；修正名稱後八個API回應SHA相同。原整體資料缺口、四個未重現timeout及新GPA失敗均仍開放。

3b CI：quality37869693722 failure／0 jobs，Supabase113624678250 skipped，combined pending；不是完整CI通過。遠端main仍f6ad1b8，CCU5eadeb5／TKU3ccbf7c共享交集15／20見同目錄精確merge points。不merge、部署、套正式DB或聯絡學校。
