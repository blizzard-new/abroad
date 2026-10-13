# 中正第二批補查實測

凍結資料／程式commit：`b786ec8d7a2efff3c294e23489a74637e1b3db45`。實測先後與修正保留於report.json；首批c18aebf全套報告不可替代本批實測。

- 104身份；點98、授權照片100、官方網站102；當期接待欄330/1768，缺690。新增3點/3照片/1網站；IIT Bombay官方2026–2027 PDF全5頁及11初申文件、到校後FRRO與無版本表分開。
- 452項選定回歸實際445通過、4略過、3失敗，無新增排除。照片措辭斷言與ASBU城市label已修正，相关4檔41項通過。Jena390官方連結hidden一次失敗，原樣独立重跑通過；未證明不穩定根因，不能改寫整批全綠。
- CCU completion手機/桌面6項通過，包含新IIT Bombay兩種寬度；母校未開放/名額null、17接待欄、期限、無版本表、住宿非保證均實測。
- 最終離線及wheel gate通過，3186個CCU package files逐byte一致，SHA204525fa114211c03d7014ae49326f11932a40a7fbe591d1edfdb04710aa2a8b。下一批原始來源另移到自己的artifact目錄，未混入凍結package。
- 只清理自身可再生成build與含未納入來源的draft wheel，移动自己的Playwright/UV cache保留；Docker vfs runtime重試仍failed to register layer:no space left on device。images/containers/volumes/cache全部0，自己的隔離project資源已清；未改Docker、安全、憑證或其他工作區。
- Ruff最初套件不存在、預設tools目錄唯讀、猜測bin路徑不存在，原錯誤留存；以命令局部UV目錄於自身workspace執行實際9項lint修正，最终通過。

表格及照片來源bytes已在CCU completion_sources中；附件能以一般PDF/DOC工具開啟。此資料仍有可公開查詢未完成項目與Gamma全量清單未取得，沒有冒稱已窮盡公開來源。
