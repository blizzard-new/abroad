# UniWay 文章與平台整合驗收

文章使用獨立綠色文字頁，且主平台只有頁尾連結，讓讀者難以發現內容並感覺離開 UniWay。此變更統一公共閱讀頁與平台的品牌外觀，並補上主要入口。

- 平台與公共頁共用 `brand-tokens.css`、既有 Logo 和自架字體；文章以閱讀版型呈現，保留目錄、表格、插圖、來源與相關文章。
- 平台主選單、手機頁首、首頁首屏與精選文章區均可開啟 `/guides`；文章頁可返回首頁或開啟選校工具。
- 手機頁首使用兩列導覽，減少重複的完整標題麵包屑；正文與所有網址仍完整存在於 HTML，無 JavaScript 也能閱讀與導覽。
- 公共頁讀取相同的 `exchange-guide-theme` 偏好；主題切換可保存，儲存空間被封鎖時仍可使用。
- 原文章 JSON、canonical、Article 結構化資料與內容修改日期沒有改動。驗收工具將 Git JSON 與模型預設欄位正規化後比較，避免把缺省欄位當成內容改寫。

## 驗證

本機 SEO／跨校頁測試 71 項、編輯日期驗收測試 2 項通過。瀏覽器共 31 項不同測試通過（其中 3 項在最後的圖片與小螢幕調整後再次通過）：

- 320、390、1440 px 的平台 → 指南 → 文章 → 選校 → 指南流程。
- 主平台與公共頁實際計算出的品牌色及字體一致。
- 首頁三張精選文章圖片實際載入；10 篇文章的正文插圖皆載入。
- 手機閱讀無橫向整頁溢出；表格可橫向捲動。
- 無 JavaScript 的學校頁、文章、國家專區與編輯政策可用。
- 深色、淺色、跟隨系統，以及 localStorage 被封鎖情境。
- 手機選單焦點、Escape、登入入口，以及桌面導覽列展開後無重疊。

`scripts/check_editorial.py --base-ref origin/main`：10 篇文章通過；`git diff --check` 通過。

遠端 `Web quality` 工作流程仍為 `disabled_manually`。上述結果是本機執行，不代表遠端 CI 或正式部署。

## 預覽

截圖使用隔離測試環境，學校數字與資料僅供測試。

- [手機文章](seo-brand-previews/article-mobile.png)
- [桌面文章](seo-brand-previews/article-desktop.png)
- [深色閱讀](seo-brand-previews/article-dark.png)
- [手機首頁文章入口](seo-brand-previews/home-mobile.png)
- [桌面首頁文章入口](seo-brand-previews/home-desktop.png)

合併後仍需更新 Windows Docker 的 app 容器才會反映在正式站。
