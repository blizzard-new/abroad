# UniWay 中英文字體

Web 使用源柔黑體（GenJyuu Gothic）搭配 Poppins，套用首頁、搜尋、學校介紹、申請工具、表單及內部 Web 工具。這次只調整字型，不更動配色、版型、資料或原生 App。

- 中文：GenJyuuGothic，Regular 400、Medium 500、Bold 700。
- 英文與數字：Poppins，Regular 400、Medium 500、Bold 700。
- `typography.css` 定義 `--uw-font-ui`，Poppins 放在前面，漢字交由 GenJyuuGothic 呈現。既有字級、行高與字重階層保留。
- 共用字體樣式最後載入，涵蓋深淺色模式、下拉選項、輸入提示及檔案選擇按鈕。攻略、收藏與旅行標題也使用這組字體，移除先前「UniWay Journal」手寫字體覆蓋。
- 個別源柔未收錄的漢字（包含「啟、夠、查、值、踩」）會使用繁體中文系統備援字型，確保文字完整；不修改原文來遷就字集。
- 程式碼區塊保留等寬字型，登入供應商標誌保持原有字形。
- 使用者參考圖的中文「源柔黑體」與英文「GenYoGothic」不一致；GenYo 是源樣黑體。本次依照中文名稱與圓潤風格採用 GenJyuu。

全部字型從同一網站載入，符合既有 `font-src 'self'`。源柔使用上游 Unicode 分段 WOFF2，按畫面上的字載入；Poppins 使用原始 TTF。`font-display: swap` 讓慢速網路先顯示備援文字。授權與來源雜湊位於 `static/assets/fonts/`，不需要使用者安裝字型。

地球的英文國名與群組數字使用獨立的 `Poppins Medium` SDF 字形，範圍 0–255。由同一份 Poppins Medium TTF 經 MapLibre font-maker 產生，放在 `static/assets/partner-map/fonts/Poppins Medium/`。其餘 HTML 地圖標籤、預覽卡與提示框沿用中英文字型組合。

上游來源：

- [GenJyuu Gothic web subsets](https://github.com/shogo82148/genjyuugothic-subsets/releases/tag/2022-06-16)
- [Poppins](https://github.com/google/fonts/tree/main/ofl/poppins)
- [GenYo 名稱說明](https://github.com/ButTaiwan/genyog-font)
- [MapLibre font-maker](https://github.com/maplibre/font-maker)
