# claude-seo 使用手冊

[claude-seo](https://github.com/AgriciDaniel/claude-seo)（MIT）是 Claude Code 外掛，用來審計「已上線的網址」並產生建議。它在開發者電腦上執行，**不進 repo、不進正式環境**，輸出只是建議，改動仍走一般 PR 與 CI。以下指令名稱取自它的 README；2026-10-29 撰寫時尚未在本專案實跑過，第一次執行請以實際輸出為準並回頭修正本文。

## 分工：哪些已有、哪些交給它

| 需求 | 本專案已有 | claude-seo 補的部分 |
| --- | --- | --- |
| robots、sitemap、canonical、metadata | `seo.py`、`scripts/check_seo.py`（部署後必跑） | 不需要，不重複 |
| Search Console 成效報告 | `seo_reporting.py`（唯讀） | 不需要 |
| 內容品質稽核 | `seo_quality.py`（不自動改索引） | 第三方角度的 E-E-A-T 評語 |
| AI 搜尋可見度（`llms.txt`、AI 爬蟲、可被引用的段落） | `/llms.txt`、robots 的 AI 爬蟲群組 | `/seo geo`、`/seo agentic` 查漏 |
| 結構化資料 | 首頁 `Organization`＋`WebSite`、內頁 `BreadcrumbList`、指南 `Article` | `/seo schema` 驗證與建議 |
| 部署前後的 title／canonical／schema 回歸 | 只有內容層的 `ContentChanges` | `/seo drift` |
| 新指南題目與大綱 | `docs/seo-editorial-backlog.md` 的候選清單 | `/seo content-brief`、`/seo cluster` |

`/seo local`、`/seo maps`、`/seo ecommerce` 不適用（沒有實體店面或商品）；`/seo hreflang` 在有英文版之前用不到。

## 安裝（在你的電腦上）

```text
/plugin marketplace add AgriciDaniel/claude-seo
/plugin install claude-seo@agricidaniel-claude-seo
/seo setup
/seo doctor
```

`/seo setup` 會建立 Python 環境並下載 Chromium。安裝前先讀過它的程式碼；不要把外掛寫進本專案的 `.claude/settings.json`，避免每個開啟此 repo 的人都被要求載入第三方程式。完整 `/seo audit` 會用到多個 Opus 子代理，額度消耗大，不要排進每日排程。

## 流程

1. **基準線（只做一次）**：`/seo audit https://app.uniway-tw.com`。把輸出存成 `docs/seo-audit-YYYY-MM-DD.md`，與 `check_seo.py` 的 JSON 並排比對；只有兩邊都能重現的問題才開修正 PR。
2. **AI 搜尋**：`/seo geo https://app.uniway-tw.com`、`/seo agentic https://app.uniway-tw.com`。對照 `https://app.uniway-tw.com/llms.txt` 與 `/robots.txt` 看有沒有遺漏的頁面或爬蟲。
3. **結構化資料**：`/seo schema https://app.uniway-tw.com`，再抽查一篇 `/guides/*` 與一個 `/schools/*/partners/*`。
4. **回歸監測**：每次部署前 `/seo drift baseline https://app.uniway-tw.com`；部署後先跑 `scripts/check_seo.py`，通過再 `/seo drift compare https://app.uniway-tw.com`。差異必須能對應到這次 PR，否則視為意外變更。
5. **新題目**：`/seo cluster <關鍵字>`、`/seo content-brief <題目>` 的結果只放進 `docs/seo-editorial-backlog.md` 的 *Candidate intentions*，仍照 `docs/seo-editorial-workflow.md` 的規則選題、查官方來源、做原創內容。需要行銷辦公室跟進時，在聊天裡把題目與依據交給 Ivy；不要改 `marketing/agent-office` 的程式去讀外掛輸出。

## 不採納的建議類型

- 用抓取時間（`checked_at`）充當 sitemap 的 `lastmod`：`seo-launch.md` 已說明不做。
- 為了關鍵字或 FAQ 寫出沒有官方來源的名額、資格或日期；合作關係不等於當期開放申請。
- 為了 `FAQPage` 補 FAQ：Google 對 FAQ 摘要的顯示範圍有限，有實際來源的問答再做，不為了版位而做。
- 大量送出網址（Search Console、IndexNow）：編輯流程明定不做。
- 把 Google 或其他服務的憑證放進 repo；Search Console 讀取沿用 `seo_reporting.py` 的唯讀權杖作法。

## AI 爬蟲政策

`robots.txt` 對下列爬蟲各有一個群組，並且各自重複私人路徑的 `Disallow`（具名群組會取代 `*` 群組）：

- 搜尋與使用者代為抓取（引用來源）：`OAI-SearchBot`、`ChatGPT-User`、`PerplexityBot`、`Perplexity-User`、`Claude-SearchBot`、`Claude-User`
- 訓練用：`GPTBot`、`ClaudeBot`、`Google-Extended`、`Applebot-Extended`、`CCBot`

預設 `EXCHANGE_AI_CRAWLERS=allow`，兩類都允許。想保留被 AI 搜尋引用、但不讓訓練爬蟲抓取時，設成 `search-only`；其他值會被忽略並改用 `allow`。`llms.txt` 對排名或引用率的實際影響尚無定論，把它當成低成本的導覽檔，不要當作成效承諾。
