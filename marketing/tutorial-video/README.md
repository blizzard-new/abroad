# UniWay 教學影片：登入與學校搜尋

| 成品 | 規格 |
|------|------|
| [`build/uniway-tutorial-school-search.mp4`](build/uniway-tutorial-school-search.mp4) | 1920×1080、30 fps，輕配樂＋點擊音效 |

從首頁登入開始，進入「學校搜尋」，把頁面上每個功能都操作一次。示範帳號是「示範同學」（@cgu.edu.tw），就讀學校自動帶入**長庚大學**（77 所合作校）。畫面都是真的網站，由瀏覽器實際點擊錄下來，不是截圖拼貼。

## 分段

| 步驟 | 內容 |
|------|------|
| 片頭 | UniWay 使用教學：登入 → 學校搜尋 → 篩選與排序 → 我的選校 |
| 1 從首頁登入 | 點左下角人像圖示 → 勾選同意條款 → 「使用 Google 繼續」→ 回到首頁，就讀學校自動帶入長庚大學 |
| 2 進入學校搜尋 | 左側選單展開，點「學校搜尋」；共 77 所，先顯示 30 所 |
| 3 關鍵字搜尋 | 輸入「日本」→ 搜尋學校 → 剩 7 所；出發學期、語言檢定兩個欄位 |
| 4 卡片／地圖 | 切到地圖看合作校分布，用「定位學校」跳到一所並預覽；再切回卡片 |
| 5 三種排序 | 截止最近、名額最多、最符合條件 |
| 6 左側篩選 | 國家（法國 15 所）、交換名額 2 名以上、更多條件（名額狀態、地區、國家、學院、學制）、清除全部 |
| 7 我的條件 | IELTS 6.5、大學部 → 套用條件 → 「最符合條件」顯示 11 間符合 |
| 8 學校詳情與最近看過 | 點學校名稱看詳情 → 返回 → 「最近看過」 |
| 9 比較與我的選校 | 勾「加入比較」兩所、愛心收藏一所 → 並排比較 → 我的選校 |
| 片尾 | 開始找你的交換學校吧！app.uniway-tw.com |

## 登入那一段怎麼錄的

正式網站只開放 Google 登入。錄影時 `demo_server.py` 啟動的就是正式的程式，只差兩點：

- 帳號、收藏與條件寫進一次性的暫存資料夾，不會動到 `data/`。
- 不連 Google：取 token 與讀個人資料這兩個呼叫，直接回一位假的學生（示範同學，已驗證的 @cgu.edu.tw 信箱）。UniWay 自己這一側的流程全部照跑：條款勾選檢查、state cookie、callback、依信箱網域帶入學校。

Google 自己的帳號選擇畫面不屬於 UniWay，影片裡不模仿它，改用一張說明卡（「接下來會開啟 Google 登入……教學影片略過 Google 的帳號選擇畫面」）帶過；登入後頁面重新載入的那幾秒以 2 倍速播放。

## 重新錄製

需要專案的 Python 環境（`uv sync --frozen --extra dev`，內含 Playwright）、Chromium、ffmpeg，以及有 NumPy 的 Python 3（配樂用）。在專案根目錄：

```bash
.venv/bin/python marketing/tutorial-video/demo_server.py &     # 正式網站，port 8771，資料放暫存資料夾
.venv/bin/python marketing/tutorial-video/record.py            # 約 20 分鐘：慢動作操作一遍，再輸出 build/uniway-tutorial-school-search.mp4
.venv/bin/python marketing/tutorial-video/record.py --stills   # 只在每一步結束存一張 PNG（build/stills/），快速檢查版面
```

沒有 GPU 的環境裡，Chromium 每秒只畫得出 8 張左右 1080p 畫面，直接錄會一格一格的。所以整段操作以 4 倍慢動作進行（`--slow 4`）：滑鼠、停留、網頁的計時器與 CSS 動畫一起放慢，最後再加速回正常速度，每秒影片約有 30 張實際畫面。有 GPU 的電腦可以用 `--slow 1` 直接即時錄。

每次重錄前請重開 `demo_server.py`（或給新的 `--data-dir`），讓示範帳號從空白開始；不然上一次的收藏與條件會留在帳號裡。

找不到 Chromium 時可以用 `CHROMIUM_PATH` 指定；配樂用的 Python 可以用 `MUSIC_PYTHON` 指定（預設 `python3`）。`--no-music` 輸出無聲版本，`--keep-frames` 保留 `build/frames/` 的原始畫格。

## 檔案

| 檔案 | 用途 |
|------|------|
| `demo_server.py` | 錄影用的網站：正式程式＋暫存資料＋代替 Google 回應 |
| `record.py` | 分鏡腳本：每一步的滑鼠移動、點擊、字幕與停留秒數；Chromium screencast 收畫格，ffmpeg 合成 |
| `overlay.js` | 疊在網站上的滑鼠游標、點擊波紋、框選提示、字幕與片頭片尾卡（不攔截任何點擊），以及慢動作用的網頁時鐘與平滑捲動 |
| `music.py` | 合成配樂與點擊音效（依 `build/timeline.json` 的長度與點擊時間），沒有版權問題 |

## 之後要更新

- **改字幕或順序**：都在 `record.py` 的 `storyboard()`；字幕裡 `<em>` 會變成紅色強調字。
- **網站改版**：選擇器寫在 `storyboard()` 裡（例如 `#partner-search`、`[data-partner-sort=deadline]`、`.pr-compare`）。先跑 `--stills` 看每一步的畫面，再錄正式版。
- **換示範學校**：改 `demo_server.py` 的 `DEMO_USER["email"]` 網域（例如 `@gm.ntpu.edu.tw`），並同步修改字幕裡的校名與數字（77 所、法國 15 所、日本 7 所、11 間符合）。
