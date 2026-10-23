# UniWay 行銷辦公室

一間「看得見」的 AI 行銷辦公室：8 位 AI agent 各坐一張桌子、各用一台電腦，每天自動企劃、寫 Threads、做 IG 輪播與限動、剪 Reels／YouTube Shorts（週日再做一支長影片）、審稿查核、排程發佈、抓成效、擬留言回覆。你坐在最後一張桌子，所有草稿像登機證一樣送到你面前，核准後才會發出去。

![辦公室畫面](docs/office.jpg)

- 每位 agent 的螢幕顯示他現在正在做的事：Threads 小編的草稿會一個字一個字打出來、設計師的螢幕會長出輪播圖、剪輯師的螢幕有算圖進度條、發佈員的螢幕是 API 呼叫紀錄。
- 工作交接時，會有一張紙從一張桌子飛到下一張桌子（企劃 → 寫手 → 審稿 → 你 → 發佈）。
- 牆上的「今日發文時刻表」是機場出發看板：每則貼文是一班飛機，待審、準時、已起飛、延誤一目了然。
- 窗外是台北的天色（跟著台北時間變化），白板上是企劃寫的今日主軸。
- 網址加上 `?tv` 是全螢幕的電視模式，可以掛在實體辦公室的牆上當看板。

## 辦公室裡有誰

| 座位 | 角色 | 每天做什麼 |
|------|------|------------|
| Ivy | 企劃總監 | 讀平台數字（目前支援幾所大學、幾筆合作校）、`sources/audit/` 最新一天的已核實官方公告、上週成效，排出今天的內容；照 3:3:3:1 輪替 IG 內容支柱 |
| 阿脆 | Threads 小編 | 去商業化的真人口吻；第一行點名族群或痛點，用提問、二選一、清單、小編碎碎念、今日公告五種角度；主文不放網址，網址放第一則留言 |
| Mori | IG 設計師 | 6 張 4:5 輪播圖（封面鉤子 → 重點 → 收藏／分享／連結在主頁），再做一張提醒看新貼文的限動；hashtag 最多 5 個 |
| 阿剪 | 影片剪輯 | 30～45 秒直式腳本（前 3 秒鉤子、每個畫面都有大字幕），逐格算圖並配上合成音樂；同一支影片發 Reels 和 YouTube Shorts；週日做 2～4 分鐘橫式「本週交換情報懶人包」 |
| Kiki | 審稿查核 | 程式規則＋AI 審稿：字數、連結位置、hashtag 數、平台數字不能誇大、沒有官方來源不能寫日期、禁用「保證錄取／官方合作」等字眼；不合格退回作者改一次 |
| Pat | 發佈排程 | 到排定時間呼叫 Threads／Instagram／YouTube 官方 API；Threads 發完主文立刻在第一則留言補上連結 |
| Nana | 數據分析 | 每晚抓成效，把 Threads 上互動最好的題目交給企劃重製成 IG（Threads 測試題目、IG 放大轉換的雙平台閉環） |
| Momo | 社群互動 | 發文後 30 分鐘～3 小時去看留言、擬回覆；回覆陌生人一律等你核准 |
| 你 | 老闆 | 在「待你審核」核准、修改、立即發佈或退回 |

## 一天怎麼運作

```
07:30  開工：企劃讀資料、排內容 → 寫手、設計、剪輯同時產出 → 審稿 → 草稿送到你的審核匣
       （你可以在手機上打開辦公室網頁審核）
12:30  Threads 第 1 篇（主文 → 第一則留言放連結）
18:00  YouTube Shorts
19:30  Instagram 輪播或 Reels，19:45 限動
21:00  Threads 第 2 篇
發文後 30 分鐘  社群互動看留言、擬回覆給你核准
23:30  數據分析抓成效，明天企劃參考
週日   多一支 YouTube 長影片
```

時間都可以在 `.env` 改。沒核准的草稿不會發；核准時已經過了排定時間的，下一輪（30 秒內）就發。

## 快速開始：不用任何帳號，先看辦公室動起來

需要 [uv](https://docs.astral.sh/uv/)、ffmpeg，以及 Playwright 用的 Chromium。在這個資料夾：

```bash
cd marketing/agent-office
uv sync
uv run playwright install chromium     # 已經有 Chromium 的話可以改設 CHROMIUM_PATH
uv run office serve                    # 打開 http://127.0.0.1:8780
```

按右上角「開始今天的工作」就會開工。沒有設定任何金鑰時，寫手用內建的離線範本、發佈是「模擬發佈」：該送出的 API 請求只會寫進 `var/outbox/`，不會真的發文。圖片、影片在 `var/media/`。

不開網頁也可以：

```bash
uv run office run --force     # 立刻跑一天
uv run office list            # 看草稿
uv run office approve 3 --now # 核准 #3 並馬上發
uv run office facts           # 看平台數字與今天可引用的官方公告
```

## 上線步驟

建議依序做，每一步都確認沒問題再往下：

1. **離線試跑**：照上面的快速開始，看一天的草稿長什麼樣子。
2. **接上 Claude**：在 `.env` 放 `ANTHROPIC_API_KEY`。寫稿、企劃與 AI 審稿改由 Claude 做（預設 `claude-opus-5-5`，有安全拒答時會自動改用備援模型）。
3. **接上各平台帳號**（下一節），仍保持 `OFFICE_DRY_RUN=1`，到 `var/outbox/` 看會送出的內容。
4. **正式發佈**：改成 `OFFICE_DRY_RUN=0`，保持 `OFFICE_APPROVAL=manual`，每天花 5 分鐘審核。
5. 跑順幾週後，想放手再改 `OFFICE_APPROVAL=auto`（審稿通過就自動排程；留言回覆仍然要你核准）。

辦公室要一直開著才會自動開工與發文：放在一台不關機的電腦（例如實體辦公室裡的小主機，順便接一台電視顯示 `?tv`），或任何可以長時間跑 Python 的主機。

## 接上 Threads、Instagram、YouTube

複製 `.env.example` 成 `.env` 再填。所有權杖只放在 `.env` 和 `var/office.sqlite3`，兩者都不進 Git。

### Threads

1. 到 [Meta for Developers](https://developers.facebook.com/) 建立 App，加入 **Threads API** 使用案例，勾選 `threads_basic`、`threads_content_publish`、`threads_read_replies`、`threads_manage_replies`、`threads_manage_insights`。
2. 把要發文的 Threads 帳號加為這個 App 的測試人員，並在 Threads 裡接受邀請。只發自己的帳號時，用開發模式就可以，通常不用送 App 審查。
3. 用後台的權杖產生器取得短期權杖，再換成長期權杖（約 60 天，辦公室每週自動延長）：
   ```bash
   # .env 先填 THREADS_APP_SECRET
   uv run office auth threads --short-token <短期權杖>
   ```
4. `THREADS_USER_ID`：用權杖呼叫 `https://graph.threads.net/v1.0/me?fields=id,username` 取得 `id`。

### Instagram

1. IG 帳號要是**專業帳號**（商業或創作者）。
2. 同一個 Meta App 加入 **Instagram API with Instagram Login**，勾選 `instagram_business_basic`、`instagram_business_content_publish`、`instagram_business_manage_comments`、`instagram_business_manage_insights`，把帳號加入並產生權杖。
3. 後台產生的若已是長期權杖，直接填 `INSTAGRAM_ACCESS_TOKEN`；若是短期權杖，用 `uv run office auth instagram --short-token …` 換。
4. `INSTAGRAM_USER_ID`：呼叫 `https://graph.instagram.com/me?fields=user_id,username` 取得 `user_id`。
5. **圖片和影片必須有公開網址**（Instagram 與 Threads 是從網址抓檔，不收上傳），選一種：
   - `OFFICE_MEDIA_HOST=supabase`：在 Supabase 建一個 public bucket（預設名稱 `marketing-media`），填 `SUPABASE_URL` 與 `SUPABASE_SERVICE_ROLE_KEY`。service role key 權限很大，只能放在這台機器的 `.env`。
   - `OFFICE_MEDIA_HOST=static`：讓這台機器的 `/media/` 對外（例如用 tunnel），填 `OFFICE_PUBLIC_BASE_URL`。這時**一定要設 `OFFICE_ACCESS_TOKEN`**，否則任何人都能打開辦公室按核准。

### YouTube

1. 在 Google Cloud 建專案，啟用 **YouTube Data API v3**。
2. OAuth 同意畫面選「外部」，把自己加為測試使用者；**發布狀態改成「正式版」**（測試中的 App 拿到的 refresh token 7 天就失效）。
3. 建立 OAuth 用戶端，類型選「電腦版應用程式」，把 ID 與密鑰填進 `.env`，然後：
   ```bash
   uv run office auth youtube   # 依提示登入頻道，最後把 YOUTUBE_REFRESH_TOKEN 貼進 .env
   ```
4. Google 規定：API 專案沒通過 YouTube 稽核前，用 API 上傳的影片一律是「私人」。先設 `YOUTUBE_PRIVACY=private`，到 YouTube Studio 手動公開，或申請稽核。

## 策略對照：NotebookLM 的建議落在哪裡

| 行銷策略 | 辦公室怎麼做 |
|----------|--------------|
| Threads 創造話題、IG 展示與轉化 | 每天 2 篇 Threads ＋ 1 則 IG；數據分析把 Threads 爆文交給企劃重製成 IG |
| IG 內容 3:3:3:1（價值／引流／信任／品牌故事） | 企劃以 10 天為一輪：價值、信任各 3 天做輪播，引流 3 天做 Reels，1 天說品牌故事 |
| Threads 去商業化、真人口吻 | 寫手規範與 Claude 的品牌語氣；離線範本也有小編碎碎念角度 |
| 第一行點名族群或痛點、二選一、清單 | 五種 Threads 角度輪流用 |
| 主文不放連結，放第一則留言或主頁 | 審稿規則擋下主文網址；發佈時自動補第一則留言；IG 說明欄寫「連結在主頁」 |
| 黃金 30 分鐘 | 社群互動在發文後 30 分鐘開始看留言、擬回覆 |
| Reels 9:16、30～45 秒、前 3 秒鉤子、動態字幕 | 影片腳本與審稿規則都檢查；字幕放在 Reels 介面不會蓋到的位置 |
| 輪播以「被收藏」為目標 | 一張一件事，最後一張是收藏／分享／連結在主頁 |
| 限時動態每天經營 | 每則 IG 貼文後 15 分鐘發一張限動（見下方限制） |
| 數據回饋 | 每晚抓 Threads／IG／YouTube 成效 |

## 安全設計

- **預設不會發文**：`OFFICE_DRY_RUN` 只有明確寫 `0` 才會關掉模擬模式。
- **預設每則都要你核准**；留言回覆永遠要你核准。
- **事實只來自資料**：平台數字從 `src/exchange_info/university_registry.py` 即時計算（新增學校，貼文數字自動跟上）；公告只引用 `sources/audit/` 標記為 confirmed update 且附官方網址的條目。審稿會擋下超過平台實際數字的說法，以及沒有來源的日期。
- 審稿不過的草稿標成「需修改」，列出問題給你決定，不會自動發出。
- 權杖、金鑰只在 `.env` 與 `var/`，紀錄裡的權杖都遮成 `***`。

## 限制

- Instagram API 不能加限動互動貼紙（投票、問答、連結貼紙），也不能使用 App 內的熱門音樂；限動是純圖片，影片音樂是程式合成、沒有版權問題。需要貼紙的限動請手動發。
- Instagram 一篇最多 5 個 hashtag（2025 年底起的平台規定）；Threads 每篇一個主題標籤、主文 500 字。
- 影片是動態字幕＋吉祥物動畫，沒有旁白。
- Meta 的長期權杖約 60 天，辦公室每週自動延長；超過 60 天沒開機就要重新授權。

## 費用

Claude 每天約 12～16 次呼叫（企劃、寫稿、審稿、改稿），以 `claude-opus-5-5` 估計約 1～2 美元／天，實際依內容長度與思考量而定；`OFFICE_MODEL=claude-sonnet-5-5` 約可省一半。Threads、Instagram、YouTube API 本身免費（有每日發文上限，遠高於這裡的用量）。

## 設定一覽

見 [`.env.example`](.env.example)，每一行都有說明。

## 檔案

| 路徑 | 內容 |
|------|------|
| `office/agents/` | 8 位 agent，一人一個檔案 |
| `office/pipeline.py` | 一天的流程：企劃 → 產出 → 審稿 → 送審 |
| `office/scheduler.py` | 辦公室時鐘：開工、發文、看留言、抓數據、延長權杖 |
| `office/llm.py` | Claude 寫手（結構化輸出）與離線範本寫手 |
| `office/brand.py` | 品牌語氣、內容支柱、平台數字與今日公告 |
| `office/rules.py` | 審稿規則 |
| `office/render/` | 輪播／限動／影片的 HTML 版型、算圖與配樂 |
| `office/platforms/` | Threads、Instagram、YouTube、媒體網址 |
| `office/server.py`、`office/static/` | 辦公室網頁與即時事件 |
| `tests/` | `uv run pytest`（算圖測試需要 Chromium 與 ffmpeg） |

![輪播圖範例](docs/carousel-sample.jpg)
