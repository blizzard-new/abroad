# SEO 第二階段：品質稽核與內容更新

本次採用內部 A／B／C 編輯分級，不是 Google 評分，也不是收錄預測。預設僅輸出報告，**不會依分數大量 noindex、移除 sitemap 或改寫 canonical**。母校與合作校的條件不同時，保留各自的標準網址。參考資料、未公布名額與尚未取得本期查核證據，不等於沒有搜尋價值。

## 規則與驗收

- A：母校官方網域來源、至少四類具體申請資訊、至少兩個有母校來源的本期已查核欄位。
- B：母校官方網域來源、至少兩類具體申請資訊；可能是有價值的歷史／參考內容。
- C：來源網域需核對或具體資訊不足，優先人工檢查與補強。官方來源可能使用另一個網域，因此 C 不是錯誤判決。
- 比對去除學校名稱、來源網址後的申請條件指紋，列出完全相同的內容候選；同一母校的共同規定可能合理，不自動合併。
- 不用文字長度、名額、查核日期或 AI 分數單獨決定索引。下一輪需結合 Google 排除原因和實際內容審閱。

```sh
python scripts/audit_seo.py --output /tmp/seo-quality.json
python scripts/check_seo.py --base-url https://app.uniway-tw.com
```

第一個命令讀取隨版本發布的官方資料快照；不讀私人帳戶、不套用尚未發布的草稿，也不包含正式站額外的研究覆寫。第二個命令檢查正式輸出，包括 canonical、noindex、sitemap 格式、重複網址與未來／無效 lastmod。

2026-10-19 基線：3,540 頁；A 53、B 2,835、C 652。10 組內容相同候選涵蓋 386 頁，需要辨認共同校規與低價值重複內容。逐頁清單見 `seo-quality-baseline-2026-10-19.csv`。目前索引決策全部維持原狀，品質分級不對使用者顯示。

## lastmod 的依據與保存

`seo_changes.ContentChanges` 在每次公開校庫快取更新時比較實質欄位指紋，包含資格、學制、語言、名額、期限、來源、證據狀態與方案。排除擷取／查核時間、來源探測紀錄、圖片與排序變化。第一次只建立基線，不輸出 lastmod；之後內容改變才記錄觀測時間。這是「系統發現內容變更的時間」，不是官方文件發布時間，也不假裝知道第一次匯入前的修改日期。

目前 lastmod 適用合作校頁面；其他頁面無可靠修改紀錄時仍省略。重新抓取相同資料、重啟 app、重新部署相同內容都不更新日期。實質狀態如受理截止變動會更新日期。資料庫不可寫時記錄警告並省略日期，網站仍可用。

Docker 新增獨立的 `uniway_seo_state` volume，僅保存公開內容指紋與修改時間，容器 UID 10001 可寫入。沿用僅重建 app 的部署流程，沒有業務資料庫 migration；不要刪除此 volume。一般部署用 `EXCHANGE_SEO_STATE_DIR` 指定持久化目錄，預設為既有 data 目錄下的 `seo-state`。丟失紀錄時安全回到無 lastmod 的基線，不補寫今天。

索引政策依據：[Google sitemap 指南](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)、[重複網址與 canonical](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)、[大量內容濫用政策](https://developers.google.com/search/docs/essentials/spam-policies#scaled-content)。
