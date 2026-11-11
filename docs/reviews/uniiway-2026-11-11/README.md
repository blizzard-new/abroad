# 搜尋欄、地球配色與全站文字精簡

使用者要求把學校搜尋欄改成對話附圖的樣式、降低學校搜尋地球的亮度，並刪除全站多餘的小灰字與重複說明。接續已合併的 PR #299；本次只修改前端與對應的介面測試。

## 實際畫面

![搜尋欄](screenshots/search-bar.png)

- [桌機搜尋與地球](screenshots/search-1696-light.png)
- [手機淺色](screenshots/search-390-light.png)／[手機深色](screenshots/search-390-dark.png)
- [首頁](screenshots/home.png)／[論壇](screenshots/forum.png)／[個人設定](screenshots/profile.png)
- [我的申請](screenshots/application-today.png)／[準備工作台](screenshots/application-workspace.png)

截圖來自本機實際 Chromium 與 MapLibre，使用合成帳號及測試學校資料；學校數量與計畫內容不是正式站統計。首頁在測試環境使用既有的低動態地圖呈現，這次沒有修改首頁地球。

## 修改內容

1. 搜尋欄採奶油色外框、白色圓角欄位、紅／藍／綠欄位標籤，以及帶底部陰影的黃色搜尋按鈕。保留現有 1280px 內容寬度，依畫面縮放；手機的學期與語言仍收在「篩選」。
2. 地球的海洋改為灰藍色，陸地改為低彩度灰綠與灰褐色，淡化經緯線和外圍陰影。深色模式另有配色，學校位置與可點選標記仍清楚顯示。
3. 直接移除首頁卡片、流程介紹、論壇、個人設定、文件工具、準備工作台等區域的重複說明與裝飾性小標。沒有新增一條 CSS 把所有小字隱藏。
4. 縮短登入、提醒設定、文件保存、預算與頁尾文字。仍保留欄位名稱、資格原因、期限、來源、錯誤／空白狀態，以及涉及保存同意或刪除帳號的必要資訊。
5. 移除相應的動態重填文字與失效的 `aria-describedby`，更新所有受影響靜態檔案的快取版本。

[刪除文字清單](copy-removals.json)與[縮短前後對照](copy-shortened.json)記錄批次整理內容；另外手動清理的論壇說明、指南閱讀分鐘數、頁尾與動態填字可在程式 diff 檢視。

## 驗證範圍

- 靜態版本、快取、載入畫面：20 項通過，見 [static.log](verification/static.log)。
- 本機逐頁觀察搜尋、首頁、論壇、回饋、指南、資格、申請文件、行事曆、預算與登入後申請／設定頁；記錄中沒有 JavaScript 頁面錯誤。搜尋 1696px 桌機及 390px 手機深淺色均無水平溢出，見 [observations.json](observations.json)。
- 地球、搜尋控制項、跨頁標題／手機配置、資格狀態與首頁範圍：10 項瀏覽器案例通過，見 [browser.log](verification/browser.log)／[JUnit](verification/browser.xml)。首次跑次在等待啟動畫面時逾時，因此停止該跑次；將兩個舊測試改用專案既有、等待真實 `appReady` 的共用啟動程序後重跑。未放寬拖曳、縮放、篩選、跨頁清理或文字對比斷言。
- 最後另驗證論壇空白畫面：重複引導文已刪除，標題可見，訪客按「發表文章」仍開啟登入，且無頁面錯誤，見 [forum.json](verification/forum.json)。
- 只驗證這次受影響範圍；沒有把先前 PR 的通過數加進本次，也沒有重跑整個後端測試庫。

本次沒有部署或變更正式站資料。
