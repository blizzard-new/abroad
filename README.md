# 台灣大學生交換申請資訊整理系統 MVP

目前 Web 版支援長庚大學與國立臺北大學。長庚資料入口為國際事務處公開網站；臺北大學版接入 115 學年度赴外交換簡章與英語、日語、中文三組官方名額表，並補上現行合作資料庫中具交換合約、但尚未列入 115 學年度名額表的 48 所合作校。畫面會區分「本期開放」與「合作備查」，不會把合作合約誤當成當期可申請名額：

https://www.cgu.edu.tw/oia-ch

https://new.ntpu.edu.tw/oia

這個 MVP 會抓公開頁面，整理成 JSONL 與 FastAPI API，供未來 APP 查詢來源索引、摘要、附件與結構化交換資訊。爬蟲不登入任何系統、不蒐集公開頁面中的個資，也不把整篇原文設計成前端回傳格式。申請文件工作台只處理學生主動輸入的資料，產生 PDF 後不會替學生送件。

目前採 Web-first 開發流程：先在網頁版確認資訊架構、內容與操作，再由使用者明確確認後同步到 Flutter 的 iOS 與 Android 版本。國立臺北大學這一輪只加入 Web 與共用 API，尚未同步到原生 App。

## 專案結構

```text
src/exchange_info/
  crawler.py       # requests/BeautifulSoup crawler, optional Playwright rendering
  cleaner.py       # 去選單、頁尾、重複文字
  classifier.py    # rule-based 分類
  extractor.py     # rule-based 結構化欄位抽取
  student_view.py  # 學生查詢 dashboard 與補助要點整理
  ntpu_student_view.py # 臺北大學官方名額表解析與學生版資訊
  university_registry.py # 支援學校與別名、視覺、驗證訊號設定
  experience_collector.py # 公開學生心得與影片搜尋、去重、主題整理
  content_summary.py # 實際讀取來源正文、產生中文摘要與清理模型格式文字
  application_workflow_collector.py # 合作校官方申請流程查核與步驟整理
  partner_research.py # 合作校官網辨識與官方生活資訊查核
  application_documents.py # 個人化文件清單、欄位驗證與列印 PDF 產生器
  models.py        # pydantic schema
  api.py           # FastAPI app
  cli.py           # CLI
data/
  raw/pages.jsonl          # 原始頁面資料
  raw_files/               # PDF/doc/docx/ppt/pptx 附件與官方規章 PDF
  processed/pages.jsonl    # 清洗與分類後頁面
  processed/exchange_info.json
  processed/student_experiences.jsonl
  processed/application_workflows.jsonl
  processed/partner_research.jsonl
  processed/destination_profiles.jsonl
  processed/collection_audits.jsonl
  processed/community_questions.jsonl
  processed/community_answers.jsonl
  processed/experience_submissions.jsonl
  processed/user_accounts.jsonl
  processed/account_sessions.jsonl
tests/
ios/ExchangeGuide/       # 原生 SwiftUI iOS App 與 XcodeGen 專案設定
docs/design/
  apple-design-system.md # Web/iOS 共用設計 token、46 個元件與無障礙規格
```

## 安裝

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

如果要啟用 Playwright 動態渲染 fallback，再安裝 Chromium：

```powershell
python -m playwright install chromium
```

## 執行爬蟲

預設從長庚國際處首頁開始，只保留 `cgu.edu.tw` 網域內、與國際處/交換/出國/研修/補助/心得/FAQ/可申請學校/說明會/申請公告相關的頁面。

```powershell
exchange-info crawl --max-pages 60 --rate-limit 1.5
```

使用 Playwright：

```powershell
exchange-info crawl --max-pages 60 --rate-limit 1.5 --use-playwright
```

重新用既有 raw data 建立 processed data：

```powershell
exchange-info build-index
```

`crawl` 與 `build-index` 也會增量更新 `structured_sources.jsonl` 與 RAG 文件分段索引。若已設定 AI 金鑰，新增或變更的內容會使用 Structured Outputs 與 embedding；相同 `content_hash` 會沿用既有向量，避免重複付費。只想執行規則式整理時加上 `--rules-only`。也可單獨重建 AI 索引：

```powershell
exchange-info build-ai-index
```

蒐集合作學校的公開學生心得、社群討論與影片：

```powershell
exchange-info collect-experiences --school "林肯大學 Lincoln University" --max-sources 12 --school-delay 1.5
```

省略 `--school` 時會依合作學校清單增量蒐集，已完成或已確認無可靠結果的學校會自動略過；可用 `--max-schools` 控制批次大小、`--school-delay` 控制校際等待時間，或用 `--refresh` 重新查核。蒐集器只保存標題、短摘要、主題、來源類型、公開 URL、查核時間、雜湊，以及來源平台有提供時的公開作者／頻道名稱；不保存私人聯絡資料、不下載影片，也不大量複製文章原文。每次結果會寫入 `collection_audits.jsonl`，區分已找到、已搜尋但無結果與搜尋失敗。

查核合作學校的詳細官方申請流程：

```powershell
exchange-info collect-workflows --school "林肯大學 Lincoln University" --school-delay 1.5
```

流程蒐集只接受所選母校國際處與合作校官方網域，整理校內申請、提名、合作校線上申請、必要文件、錄取、選課、簽證、保險、住宿及返國結案。每所學校的結果會依「母校＋合作校」個別快取，避免長庚與臺北大學流程互相覆蓋。官方頁未公開、無法讀取或日期互相衝突時，系統會標示「需確認」，不自行補造規定。

完整執行臺北大學合作校的可續跑查核批次：

```powershell
exchange-info research-partners --home-school "國立臺北大學" --max-schools 5 --max-sources 12 --school-delay 1.5
```

每校會依序查核官方網域、校園照片、母校與合作校申請流程、官方住宿／生活費／交通／校園生活頁，以及公開學生心得。找到連結後會實際讀取頁面正文，為每個來源產生學生可直接閱讀的中文摘要；無法取得全文時只保留來源並明確標示，不把搜尋片段冒充摘要。省略 `--school` 時會從尚未完成五個階段的學校繼續；`--refresh` 可重新查核。校園照片必須通過來源與影像驗證才計入完成，官網低信心候選會保留為 `needs_review`，搜尋過但沒有可靠結果會記為 `not_found`。

臺北大學 203 所合作校的完整資料會匯出到 `src/exchange_info/official_data/ntpu/`，並與已驗證校園圖片一起納入 Git 版本控制。因此從 GitHub 複製到另一臺 Windows 或 Mac 後，即使當地尚未建立 `data/processed/`，API 仍會自動讀取這份基準資料。重新查核及匯出時使用：

```powershell
$env:PYTHONPATH='src'
python scripts/refresh_ntpu_catalog.py --workers 6 --max-pages 3 --timeout 12
python scripts/refresh_ntpu_images.py
python scripts/export_ntpu_catalog.py
```

`export_ntpu_catalog.py` 會同時產生 `catalog-completeness.json`。交付前應確認合作校、官網、必要詳細欄位、圖片、申請流程與目的地資料的數量全部都是 203。

在 Mac 更新專案時，先執行 `git pull --ff-only`；完成開發並通過測試後，再依序執行 `git add`、`git commit` 與 `git push`。不要把同一份專案放在 OneDrive、iCloud Drive 等同步資料夾內，以免建置產物造成路徑過長或檔案同步衝突。

## 啟動 API

```powershell
uvicorn exchange_info.api:app --reload
```

預設服務位置：

```text
http://127.0.0.1:8000
```

前端頁面：

- `http://127.0.0.1:8000/`

前端會依裝置切換操作方式：桌面版使用固定側邊導覽、多欄摘要與合作學校表格；手機版使用底部導覽、44px 以上觸控區及漸進式揭露。首次進入可選擇目前就讀學校，也可略過後先看長庚資料。首頁以找學校、截止日期、補助與資格初判為主要任務，並提供最近三個可辨識期限、依學生資料計算的基本篩選結果、可勾選的文件準備清單、收藏、比較與本機申請進度。官方文件預設只顯示摘要，展開後才顯示完整重點與來源連結。

「我的計畫」會依學生填寫的學院、學制、語言成績、目標學期、偏好國家與預算，排序合作校並列出推薦理由及待確認風險。獨立的交換預算頁可估算學費、住宿、生活費、交通、保險與簽證，並保留官方生活費來源；文件庫可逐項標記為待準備、準備中或已完成，補助頁則會依個人條件標示優先查看項目。

登入後可在申請日曆啟用私人訂閱網址，讓 Google Calendar、Apple Calendar 或 Outlook 訂閱系統中的申請期限與自訂任務。這是由系統單向同步至第三方日曆的訂閱機制；正式部署需把 `EXCHANGE_PUBLIC_BASE_URL` 設為可由外部日曆服務讀取的公開 HTTPS 網址，本機 `127.0.0.1` 僅供介面與流程預覽。

點擊合作學校會進入完整頁面，查看限制條件、語言門檻、名額、學費、截止日、逐步申請流程、官方住宿與生活費參考，以及公開學生文章、影片、社群討論與跨來源優缺點。官方表格的 69 筆合作紀錄會合併成 62 間不重複學校；同校的交換、雙學位或不同學院方案會在校內分開顯示。桌面版預設展開前兩個流程步驟，手機版展開第一步，其餘保留可掃描的步驟標題。資格初判僅依公開的校內基本門檻提供篩選結果，不代表正式錄取或校方認定。

網頁另有跨學校的留學社群，以及每間合作校的校別討論。學生登入後可用公開暱稱發布貼文、留言、使用公開聊天室，或從公開內容發送私訊邀請；只有收件者接受後才能繼續私訊。貼文可依申請、獎學金、住宿、簽證、花費、課業、生活與避雷分類，並標註學校、國家、學年度及申請階段。API 會拒絕 Email、電話與常見社群帳號格式，並提供檢舉與封鎖。原有公開問答與交換經驗投稿仍保留，投稿內容先進入審核。

網頁預設使用淺色 Apple 風格語義色彩、圖片導向的首頁與半透明玻璃材質，可由頂部按鈕切換深色模式。完整跨平台設計規格位於 `docs/design/apple-design-system.md`，包含深淺色 token、Dynamic Type、12 欄網格、8px 間距、互動狀態與 46 個原生元件的 accessibility 規格。

本次首頁與社群照片來源及授權連結整理在 `docs/image-credits.md`。

### 申請文件工作台

網頁的「申請文件」是一個獨立工作區。學生先選擇交換計畫、目標學校、學年度、學期及補助等條件，再建立一次共用個人資料；系統只顯示該身分需要的文件，重複欄位會自動帶入。每份文件都有獨立填寫頁，支援必填、Email、數字、日期先後、附件與照片數量檢查，也會列出預設列印份數、送件單位、親簽及核章對象。

目前涵蓋校內申請資料、家長同意書、讀書計畫（中文與選填英文版）、初審同意聲明、課程預選及學分規劃、雙聯學籍、出國切結、役男文件、出國前通知、補助收據、行政契約、抵達報到、海外學期報告、返國成果及學分採認。境外短期學分課程的 `2B0001001` 至 `2B0001004` 會優先套入長庚公開的正式 DOCX 版面；校方尚未公開正式檔案的項目會清楚標示為「資料整理列印版」，不可冒充正式表格。

產生「整包 PDF」時，封面會列出每份文件的份數、交件位置、簽名及核章要求，後續頁面依設定重複排入。學生自行列印與送件，系統不會連線至校方申請系統，也不會自動送出。附件中的 PDF 會接在對應文件後方；成果照片會排入報告。每份文件可追蹤「待列印、待簽名、待系所核章、待送件、已完成」，並提示下一位應聯絡或簽核的人。

個人資料與表單草稿目前只保留在瀏覽器分頁的工作階段，附件只留在記憶體；後端在請求期間於記憶體產生 PDF，回傳後不保存。正式 SaaS 上線前仍須使用 HTTPS、登入授權、加密資料庫、保留期限與刪除機制，並由校方確認每份正式表格的最新版本。Windows 有 Microsoft Word 時可將官方 DOCX 精準轉成 PDF；Linux 正式環境應另配置 LibreOffice 或文件轉檔服務。

## 帳號與第三方登入

Email 建立帳號與登入可直接使用。密碼只在後端以 PBKDF2 雜湊儲存，登入狀態同時支援 HttpOnly Cookie 與 API Bearer Token；公開社群只顯示學生設定的暱稱，不顯示 Email。

Google 與 Facebook 登入按鈕已完成 OAuth 流程，但需要先在各平台建立應用程式並設定環境變數；未設定時按鈕會顯示為暫不可用：

```powershell
$env:EXCHANGE_PUBLIC_BASE_URL='http://127.0.0.1:8000'
$env:GOOGLE_OAUTH_CLIENT_ID='你的 Google Client ID'
$env:GOOGLE_OAUTH_CLIENT_SECRET='你的 Google Client Secret'
$env:FACEBOOK_APP_ID='你的 Facebook App ID'
$env:FACEBOOK_APP_SECRET='你的 Facebook App Secret'
uvicorn exchange_info.api:app --reload
```

開發環境的 callback URL 分別是 `http://127.0.0.1:8000/auth/oauth/google/callback` 與 `http://127.0.0.1:8000/auth/oauth/facebook/callback`。正式部署必須改用 HTTPS，並設定 `EXCHANGE_AUTH_SECURE_COOKIE=true`。Apple 登入會等 App 上架需要時再接 Apple Developer 設定。

## 啟動原生 iOS App

iOS 端使用 SwiftUI，最低支援 iOS 17。請在安裝 Xcode 26 與 XcodeGen 的 macOS 執行：

```bash
cd ios/ExchangeGuide
xcodegen generate
open ExchangeGuide.xcodeproj
```

iOS Simulator 預設讀取 `http://127.0.0.1:8000`。實機測試時，在 Xcode Scheme 的 Launch Environment Variables 設定 `EXCHANGE_API_BASE_URL` 為執行 FastAPI 的 Mac 區網網址；正式上架必須改用 HTTPS。App 已實作淺色玻璃感首頁、圓形資料圖、找學校、學校限制、詳細流程、具體生活情報、公開學生心得、匿名社群、截止日、補助文件摘要與資格初判，並依裝置寬度在 iPhone Tab Bar 與 iPad Sidebar 間切換。iOS 26 使用原生 Liquid Glass；iOS 17-25 使用系統材質 fallback。

## 啟動原生 Android App

Android 端使用 Kotlin、Jetpack Compose 與 Material 3。用 Android Studio 開啟 `android/ExchangeGuideAndroid`，啟動本機 FastAPI 後即可執行 `app`。Android 模擬器預設透過 `http://10.0.2.2:8000` 連線到後端；實機測試需將 `app/build.gradle.kts` 的 `API_BASE_URL` 改為同一個 Wi-Fi 內的電腦 IP，正式版本則必須使用 HTTPS。

Android App 保留 iOS 版的核心資訊與社群流程，並依平台改用手機 Bottom Navigation、平板 Navigation Rail、淺色磨砂卡片與 48dp 最小觸控區。完整執行與建置說明位於 `android/ExchangeGuideAndroid/README.md`。

API:

- `GET /health`
- `GET /sources`
- `GET /exchange-info?school=長庚大學`
- `GET /student-dashboard?school=長庚大學`
- `GET /advisor/status`
- `GET /ai/status`
- `POST /advisor/plan`
- `POST /advisor/ask`
- `POST /ai/chat`
- `GET /ai/structured-sources`
- `POST /document-check`
- `POST /ai/review-document`
- `POST /ai/rewrite-document`
- `GET /student-experiences?school=林肯大學%20Lincoln%20University`
- `POST /student-experiences/refresh?school=林肯大學%20Lincoln%20University`
- `GET /application-workflow?school=林肯大學%20Lincoln%20University`
- `POST /application-workflow/refresh?school=林肯大學%20Lincoln%20University`
- `GET /application-center/templates?program_type=exchange&flags=subsidy`
- `POST /application-center/manifest`
- `POST /application-center/pdf`
- `GET /destination-profile?school=林肯大學%20Lincoln%20University`
- `POST /destination-profile/refresh?school=林肯大學%20Lincoln%20University`
- `GET /destination-profiles`
- `GET /coverage`
- `GET /community/questions?school=林肯大學%20Lincoln%20University`
- `GET /community/posts?topic=scholarship&q=補助`
- `POST /community/questions`
- `POST /community/questions/{question_id}/answers`
- `POST /experience-submissions`
- `GET /deadlines`
- `GET /documents`
- `GET /search?q=交換學生`
- `GET /auth/providers`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `PATCH /auth/me`
- `POST /auth/logout`

`/student-dashboard` 是學生前端主要使用的整理後資料，包含申請期間、申請資格、語言門檻、官方文件摘要、補助要點解讀，以及可申請學校清單。官方文件會把公開規章 PDF 或表單連結整理成 `document_explanations`，例如「領航者補助作業要點」、「學海惜珠補助要點」、境外交流作業要點、短期學分補助要點，以及申請表、同意書、計畫書、報告、聲明書等文件。學生預設先看摘要與重點；需要完整版本時，再點官方完整文件連結。`/sources` 與 `/search` 只回傳摘要、片段與來源 URL，不回傳整篇內文，避免把原站文章大量複製到前端。

## 資料儲存位置

- `data/raw/pages.jsonl`: 每筆原始頁面包含 `source_url`, `crawled_at`, `content_hash`, `attachments`
- `data/raw_files`: 下載的 PDF、docx、pptx 等附件，包含官方規章 PDF 與表單文件
- `data/processed/pages.jsonl`: 清洗後頁面，含 rule-based category
- `data/processed/exchange_info.json`: 給 APP 使用的結構化欄位
- `data/processed/structured_sources.jsonl`: 每份公告的計畫、年度、學期、期限、資格、語言、文件與補助欄位，並標示規則式或 AI 抽取及是否待複核
- `data/processed/document_chunks.jsonl`: RAG 使用的短段落、來源、發布日期、最後查核時間、內容雜湊與選配 embedding
- `data/processed/student_experiences.jsonl`: 各合作學校的公開學生心得與影片索引、短摘要、主題及來源 URL
- `data/processed/application_workflows.jsonl`: 各合作學校的官方申請步驟、負責單位、期限、文件、來源與最後查核時間
- `data/processed/partner_research.jsonl`: 依母校隔離的合作校官方網域、信心狀態、發現來源與查核時間
- `data/processed/destination_profiles.jsonl`: 已查核的城市、住宿、生活費、交通與官方來源
- `data/processed/collection_audits.jsonl`: 依母校記錄每間合作校的官網、心得、流程與生活資訊查核狀態，包含零結果與失敗紀錄
- `data/processed/community_posts.jsonl`、`community_post_comments.jsonl`: 匿名公開貼文與留言
- `data/processed/public_chat_messages.jsonl`: 各合作校公開聊天室訊息
- `data/processed/private_conversations.jsonl`、`private_messages.jsonl`: 邀請制私訊與對話
- `data/processed/community_blocks.jsonl`、`community_reports.jsonl`: 封鎖與檢舉紀錄
- `data/processed/user_accounts.jsonl`: 帳號資料與密碼雜湊；正式 SaaS 應遷移至受控資料庫
- `data/processed/account_sessions.jsonl`: 登入工作階段；正式環境應改用可撤銷的資料庫或快取儲存
- `data/processed/community_questions.jsonl`: 待審核或已核准的公開問題
- `data/processed/community_answers.jsonl`: 待審核或已核准的公開回答
- `data/processed/experience_submissions.jsonl`: 學生投稿的交換經驗與原始公開連結

所有頁面與結構化資訊都保留來源 URL，因為交換申請資訊可能會異動。

申請文件的個人資料、答案與附件不寫入上述 `data/processed` 檔案；目前只用於當次 PDF 產生流程。

## 測試

```powershell
pytest
```

## OpenAI 摘要、問答與文件檢查

申請顧問與文件檢查已可執行。沒有設定 OpenAI 金鑰時，系統仍會用已查核來源與規則完成選校排序、資格缺口、待辦、來源檢索與基本文件檢查；設定金鑰後，問答與使用者主動勾選的文件檢查會增加 AI 深度整理。

PowerShell 設定方式：

```powershell
$env:OPENAI_API_KEY="你的金鑰"
$env:OPENAI_FAST_MODEL="gpt-5-mini"
$env:OPENAI_ADVANCED_MODEL="gpt-5-mini"
$env:OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
uvicorn exchange_info.api:app --reload
```

- 後端透過 `LLMProvider` 介面呼叫模型；目前提供 OpenAI 實作，應用程式本身不直接綁死請求細節。
- 問答採 RAG：公告先切成短段落，再用 embedding 與關鍵字混合檢索，只把最相關的官方片段交給模型。
- 每個回答保留來源 URL、公告日期與最後查核時間；沒有足夠來源時不使用模型記憶猜答案。
- AI 使用 Structured Outputs；Responses API 請求設定 `store: false`。
- 日期、成績與語言門檻仍由程式比對；AI 只整理依據與解釋結果。選校顯示的是公開條件「符合度」，不是錄取機率。
- 上傳文件預設只做本機記憶體檢查、不保存原檔；只有使用者勾選「使用 AI 深度檢查」時才傳送抽取文字，不傳送原始檔案。
- 文件改寫支援正式語氣、英文翻譯、壓縮字數與文法修正；輸出固定標示為 AI 建議稿，模型不得補寫原文沒有的經歷、數字或規定。
- 正式環境應把金鑰放在受控的 secrets manager，不要寫進 repo 或前端程式碼。

### 選配 Supabase PostgreSQL + pgvector

本機 MVP 不設定雲端服務也能運作。要改用 Supabase 向量搜尋時，先在 Supabase 執行 `supabase/migrations/202607190001_ai_rag.sql`，再只於 FastAPI 執行環境設定：

```powershell
$env:SUPABASE_URL="https://你的專案.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY="後端專用金鑰"
exchange-info build-ai-index
```

`SUPABASE_SERVICE_ROLE_KEY` 不可放進網頁或 Flutter。預設 SQL 向量維度對應 `text-embedding-3-small`；更換不同維度模型時，需同步修改 migration。

官方文件：

- OpenAI API quickstart: https://developers.openai.com/api/docs/quickstart
- Responses API overview: https://developers.openai.com/api/reference/responses/overview/
- Embedding model: https://developers.openai.com/api/docs/models/text-embedding-3-small

## Flutter 手機 App（目前主要版本）

Android 與 iOS 手機端已整合到 `mobile_flutter/`，共用同一套 Dart 程式碼。現有 `android/ExchangeGuideAndroid/` 與 `ios/ExchangeGuide/` 暫時保留作為功能與版面對照，不再作為後續功能的主要實作位置。

Flutter 版包含獨立的公共留學首頁與長庚大學板、個人交換計畫、條件式學校推薦、三段文件進度、交換預算、可寫入第三方日曆的申請時程、合作校搜尋與收藏、官方文件摘要、詳細流程、生活情報、學生心得、全校結構化留學社群、校別聊天室、邀請制私訊，以及 Android／iOS 桌面與鎖定畫面 Widget。App 字型與文字大小跟隨手機系統設定。

Windows 可執行 Android 分析、測試與 APK 建置；iOS 原始專案也會同步生成，但最後的 iPhone 測試、簽署與 App Store 上架仍需要 macOS 與 Xcode。完整指令請參考 `mobile_flutter/README.md`。
