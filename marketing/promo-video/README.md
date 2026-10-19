# UniWay 推廣影片

| 版本 | 成品 | 規格 | 原始檔 |
|------|------|------|--------|
| 橫版 | [`build/uniway-promo-1080p.mp4`](build/uniway-promo-1080p.mp4) | 1920×1080、30 fps、65 秒 | `index.html` |
| 直式（IG Reels） | [`build/uniway-reels-1080x1920.mp4`](build/uniway-reels-1080x1920.mp4) | 1080×1920、30 fps、36 秒 | `reels.html`，文案在 [`reels-caption.md`](reels-caption.md) |

兩支都有配樂，吉祥物小藍行李箱貫穿全片，**片尾都不列任何校名**。

## 橫版分鏡

| 時間 | 段落 | 畫面重點 |
|------|------|----------|
| 0–6 秒 | 痛點 | 簡章、名額表、語檢門檻等 30 個分頁散落；吉祥物小藍行李箱探頭：「到底要先看哪一份……」 |
| 6–10 秒 | 品牌 | 所有分頁被收進行李箱，UniWay 標誌登場：「交換申請，一站搞定。」 |
| 10–17 秒 | 01 找交換學校 | 合作校搜尋與篩選（國家、學期、語言檢定、名額），每校附官方網站 |
| 17–23 秒 | 合作校地圖 | 從臺灣出發的世界地圖，支援大學數與合作校資料筆數 |
| 23–29 秒 | 02 期限與提醒 | 一鍵匯入 Google／Apple 行事曆、T-14～T-1 倒數提醒、讀書計畫字數規定 |
| 29–36 秒 | 03 申請工作台 | 資格初判、志願排序、多志願排程，文件「填寫 → 檢查 → 下載列印」 |
| 36–42 秒 | 04 預算與補助 | 同一幣別估算總成本、官方生活費來源、獎學金與補助 |
| 42–48 秒 | 05 學長姐心得 | 心得、公共留學板與各校看板 |
| 48–53 秒 | 資料可信 | 官方 HTTPS 來源、最後查核日、規定更新提醒 |
| 53–58 秒 | 支援大學 | 目前支援的大學名單＋「更多大學陸續加入」 |
| 58–65 秒 | 片尾 | UniWay 標誌、「你的交換旅程，從這裡出發。」、app.uniway-tw.com；**片尾不列任何校名** |

畫面中的平台截圖都是 2026-10-19 版本的實際網站（以國立政治大學為母校示範）。

## 直式（Reels）分鏡

畫面是網站手機版（393×852、3 倍）的實際截圖，放在手機框裡捲動、點按。重要文字都放在 Reels 不會蓋到的區域（上 200 px、下 470 px、右側按鈕列以外）。

| 時間 | 段落 | 畫面重點 |
|------|------|----------|
| 0–3.5 秒 | 痛點 | 「準備交換，還在翻 30 個 PDF？」，檔案滿天飛，吉祥物發抖：「到底先看哪一份……」 |
| 3.5–5.6 秒 | 品牌 | 檔案被收進行李箱，UniWay 登場：「交換申請，一站搞定。」 |
| 5.6–11.8 秒 | 01 找交換學校 | 首頁 → 找交換學校：點「搜尋學校」，滑過合作校卡片 |
| 11.6–17.2 秒 | 02 期限與提醒 | 點「一鍵匯入 Apple／Google 行事曆」、倒數提醒、讀書計畫字數規定 |
| 17–22.7 秒 | 03 申請工作台 | 申請文件四步驟 → 交換預算 |
| 22.5–27.2 秒 | 04 學長姐心得 | 心得、看板、熱門學校 |
| 27–31 秒 | 數字 | 22 所大學、4,152 筆合作校資料、逐筆附官方來源、更多大學陸續加入 |
| 31–36 秒 | 片尾 | UniWay、「你的交換旅程，從這裡出發。」、app.uniway-tw.com |

## 之後要更新

- **新增大學**：改 `index.html` 最上方的 `SCHOOLS` 陣列（數字會自動跟著變）與 `STATS.partners`（合作校資料筆數，看首頁「已整理 N 間合作校資料」）；`reels.html` 改 `SCHOOL_COUNT`、`PARTNER_COUNT`，`reels-caption.md` 的數字也一起改，再重新輸出。片尾本來就不寫校名，不用改。
- **Reels 手機畫面**：`assets/mobile/*.jpg` 是手機版整頁截圖（寬 1179 px）；捲動位置、點按位置寫在 `reels.html` 的 `FEATURES[].shots`（以截圖像素為單位）。
- **換截圖**：`assets/` 裡的整頁 `*.jpg` 是 1920×1200 的網站截圖（1600×1000 視窗、1.2 倍），`crop-*.jpg` 是從截圖裁下的卡片；換掉同名檔即可。框選重點的位置在 `FEATURES[].focus`（以截圖像素為單位）。
- **改台詞**：吉祥物說的話在 `LINES`；改了時間記得同步 `music.py` 對應版本（`PRESETS`）的 `pops`。

## 重新輸出

需要 Node.js、Playwright（含 Chromium）、Python 3 + NumPy、ffmpeg。在專案根目錄：

```bash
python3 -m http.server 8770 --bind 127.0.0.1 &        # 讓頁面讀得到 src/ 裡的字型
python3 marketing/promo-video/music.py marketing/promo-video/build/music.wav
node marketing/promo-video/render.mjs                  # 產生 build/uniway-promo-1080p.mp4
node marketing/promo-video/render.mjs --frames 12,30   # 只輸出指定秒數的靜態畫面，方便檢查版面

python3 marketing/promo-video/music.py marketing/promo-video/build/music-reels.wav reels
node marketing/promo-video/render.mjs --video reels    # 產生 build/uniway-reels-1080x1920.mp4
```

用瀏覽器開 `http://127.0.0.1:8770/marketing/promo-video/index.html`（或 `reels.html`）可即時預覽（點一下畫面會從頭播放並放音樂）。

配樂與音效全部由 `music.py` 合成，沒有版權問題；字型使用專案內的源柔ゴシック（GenJyuu Gothic，SIL OFL）與 Poppins（SIL OFL）。
