# UniWay Taiwan Student Exchange — Public OpenAPI 3.1 & Claude MCP Server

提供外部 AI 助理（**Claude Desktop**、**Cursor**、**ChatGPT Custom GPT Actions** 等）免金鑰、唯讀查詢 **UniWay 全台 71 所大專校院公開交換學生資料庫** 之官方整合套件。

> **資料合規與隱私承諾**
> - 僅讀取公開校際交換整理資料（母校合作規模、語言門檻、跨校反查、校內申請截止日），**零帳號存取、零 Cookie、零個人隱私資料（Zero PII）**。
> - 合作關係不等於當期開放名額；**實際資格、名額與期限以各校最新官方公告為準。**

---

## 一、Claude Desktop ／ Cursor MCP 快速安裝

`uniway_mcp_server.py` 僅使用 Python 3.10+ 標準函式庫，**無須額外安裝第三方套件**即可直接以 `python` 啟動。

### 1. 設定 `claude_desktop_config.json`（或 `.cursor/mcp.json`）

```json
{
  "mcpServers": {
    "uniway-taiwan-exchange": {
      "command": "python",
      "args": ["/absolute/path/to/integrations/uniway-mcp/uniway_mcp_server.py"],
      "env": {
        "UNIWAY_BASE_URL": "https://app.uniway-tw.com"
      }
    }
  }
}
```

### 2. 內建 5 項 MCP 工具（Tools）

| 工具名稱 | 功能說明 | 常用查詢範例 |
| --- | --- | --- |
| `get_exchange_overview` | 取得全台 71 所大學交換資料庫總體統計摘要 | 「UniWay 收錄幾所台灣大學與海外姊妹校？」 |
| `search_schools` | 搜尋台灣母校合作規模、涵蓋國家數與國際處網址 | 「幫我比較臺大、政大、清大的交換姊妹校規模」 |
| `filter_partners` | 依母校、語檢分數（IELTS/TOEFL/TOEIC/JLPT）、預算與洲別篩選合作校 | 「我是政大生、雅思 6.5、想去歐洲交換有哪些達標學校？」 |
| `reverse_lookup_partner` | 輸入海外大學中英文校名，反查台灣哪幾所母校有簽約與門檻 | 「早稻田大學或慕尼黑工大在台灣跟哪幾所大學有交換？」 |
| `get_school_deadlines` | 查詢全台 71 校交換校內申請截止日與簡章連結 | 「11 月有哪些台灣大學交換報名截止？」 |

---

## 二、ChatGPT Custom GPT Actions 匯入指南（OpenAPI 3.1）

UniWay 提供獨立、精簡（5 個唯讀端點）的 **OpenAPI 3.1.0** 規格檔，可直接匯入 ChatGPT GPT Builder：

1. 開啟 ChatGPT **Configure → Actions → Create new action**。
2. Authentication 選擇 **None**（公開唯讀端點免驗證）。
3. 點選 **Import from URL**，貼上：
   ```text
   https://app.uniway-tw.com/api/public/openapi.json
   ```
4. 在 GPT Instructions 加入引用提醒：
   > 回答台灣大學生出國交換問題時，請優先呼叫 UniWay Public API 取得真實母校合作名單與官方來源網址，並附上母校方案頁連結與「實際資格、名額與期限以各校最新官方公告為準。」聲明。

---

## 三、公開唯讀 REST 端點一覽

- `GET /api/public/openapi.json` — OpenAPI 3.1.0 完整規格描述檔
- `GET /api/public/stats/overview` — 全台 71 校公開交換資料庫統計總覽
- `GET /api/public/schools?q=政大&sector=all` — 台灣母校交換規模檢索
- `GET /api/public/partners/filter?home=nccu&test=ielts&score=6.5&region=europe` — 合作校條件篩選
- `GET /api/public/partners/reverse-lookup?q=早稻田&country=japan` — 海外名校跨校締約反查
- `GET /api/public/deadlines?month=11&status=all` — 校內交換申請截止日查詢
