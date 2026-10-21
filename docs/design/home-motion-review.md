# UniWay 首頁動態預覽

這一版讓首頁隨閱讀逐步展開，保留既有配色、內容、學校資料與功能路由。

## Calendly 研究與採用方式

研究來源：[Calendly 首頁](https://calendly.com/)、頁面公開載入的 [元件 bundle](https://calendly.com/_astro/src.BcPAE6wV.js)、
[REA 官方專案](https://github.com/morluto/rea)。網站可能依版本與實驗顯示不同主視覺。

| 可核實的參考站做法 | UniWay 的對應設計 |
| --- | --- |
| 公開元件以 `whileInView` 將 opacity 與 y 位移帶回正常位置，搭配進場時間及延遲 | 指南卡、功能卡與論壇卡進入畫面時依閱讀順序淡入上移，每張只播放一次 |
| 產品介紹以展開寬度與透明度切換閱讀焦點 | 申請指南改為逐步聚焦的縱向卡片，保留完整文字與可用連結 |
| 主視覺使用漸層、浮層與互動產品展示 | 延續 UniWay 現有地球與行李箱，增加計畫卡輕微傾角與捲動位移 |
| 按鈕／圖示有小幅 hover 位移與顏色變化 | 指南卡與工具卡輕微上浮，連結箭頭短距離位移 |
| 公開程式具有減少動態效果分支 | 即時尊重系統設定，取消進場及捲動效果，內容保持可讀 |

左側固定路線卡、右側申請步驟是為 UniWay 設計的延伸，不宣稱與 Calendly 內部實作相同。沒有複製其素材、文案或前端程式。

REA CLI 6.7.0 已安裝在隔離研究目錄 `/workspace/scratch/rea-tools`，未加入產品依賴。
本環境的 REA JavaScript 分析 worker 回報 `execution_failure`，僅產生部分檔案盤點，不能視為完整 AST 分析成功。
動態觀察由雲端瀏覽器完成，元件實作另直接查閱公開 JS 確認。

## 實作

- `home-motion.js`：首頁專用 IntersectionObserver、Web Animations API 與單一 requestAnimationFrame 捲動排程。沒有攔截滾輪、修改捲動速度或持續跑計時器。
- `home-motion.css`：只作用於 `#home-landing`。桌面使用固定路線卡；手機採自然縱向時間軸，避免佔滿畫面。
- 地圖航線隨捲動描繪，地圖重建／切換學校後會重新套用。
- 路線圖只表示目前閱讀段落，不會改變帳號、收藏、資格、文件或真實申請進度。
- 內容預設可見。腳本失敗時保留完整文字和原有功能入口；鍵盤聚焦會取消該卡片尚未完成的進場。
- 切換頁面、分頁隱藏或離開頁面會取消動畫；恢復頁面會依當前位置同步。系統減少動態效果設定可即時切換。

## 驗證

以系統 Chromium 執行以下選定的首頁與共用動態測試：

```sh
.venv/bin/python /workspace/.abroad-cloud/system-browser-pytest.py \
  tests/e2e/test_home_motion.py \
  tests/e2e/test_platform_redesign.py \
  tests/e2e/test_system_motion.py \
  -k 'home or reduced_motion_live_change' -q --tb=short
```

結果：**15 passed，27 deselected，106.23 秒**。涵蓋 360、393、834、1440px，明暗模式，前後捲動、固定位置、路由返回、原有搜尋、名單跑馬燈、地球、即時減少動態效果與腳本失敗降級。另通過 JS 語法與 `git diff --check`。

實際預覽錄製沒有 JavaScript 錯誤；393px 淺色與 1440px 深色的截圖檢查沒有水平溢出。這次未進行完整全站測試，也未做真實手機效能量測。

## 預覽成果

錄製於本機隔離的開發資料服務，檔案在 `/workspace/artifacts/uniway-home-motion/`：

錄影環境使用 SwiftShader 軟體繪圖，既有地球元件因此回報 `data-state="fallback"`、`data-reason="software:ANGLE … SwiftShader …"`，在影片中顯示平面備援地圖。影片未呈現原本的 3D 旋轉地球；本次沒有修改地球元件、COBE 或其硬體／效能判定。不能把這段影片當成完整的 3D 地球預覽。

- `homepage-preview.mp4`：完整捲動操作影片。
- `journey-preview.gif`：申請路線的動態片段。
- `desktop-hero.png`、`desktop-features.png`、`desktop-map.png`、`desktop-journey.png`：桌面截圖。
- `mobile-light-journey.png`、`desktop-dark-journey.png`：手機及深色模式截圖。

這些預覽檔保存在研究工作區，未加入產品靜態資源；正式網站需透過既有的合併與部署流程更新。
