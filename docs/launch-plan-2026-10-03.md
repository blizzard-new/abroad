# 先上線版（免費、網頁優先）— 做法與上線前清單

日期：2026-10-03（同日稍晚更新：學校板開放、走正式 Supabase、字樣改「免費」、加入使用統計）。這份記錄「現在系統怎麼運作」「上線前你要做的事」與「競品查核」。正式發布閘門（`docs/web-release-candidate.md`）仍是 `NOT READY`；先上線是產品負責人的決定，閘門與核准表沒有被改動，也沒有人代簽。

## 1. 系統現在的規則

| 對象 | 可以做 | 不能做 |
| --- | --- | --- |
| 沒登入的訪客 | 看長庚、臺北大學所有合作校資料、申請流程、文件清單、搜尋、比較、公開貼文 | 收藏、保存進度、發文留言 |
| 用 Google 登入的帳號 | 上面全部 ＋ 保存進度、申請計畫、提醒、在**所有討論板**（公共留學板、語言學校板、兩校板）發文、留言與按讚，署名為匿名或真實暱稱 | 用「某某大學學生」或系所署名；發問答、分享心得、校內即時聊天 |
| 驗證過在學身分的帳號 | 上面全部 ＋ 用「某某大學學生」署名、問答、分享心得、即時聊天 | — |

- 登入只有 Google（`EXCHANGE_AUTH_METHODS` 預設 `google`；Email 註冊與登入、Facebook 都是關的）。
- **學校怎麼來**：Google 回傳「已驗證」的信箱網域是 `cgu.edu.tw` 或 `ntpu.edu.tw`（含子網域，如 `gm.ntpu.edu.tw`）時，自動帶入該校；其他信箱登入後會請對方選學校，也可以先略過。
- 信箱網域只代表「這個地址屬於該校」，不代表目前在學（校友與教職員地址長得一樣）。畫面會寫「依校內信箱判斷（不代表目前在學）」；選的學校則寫「自行選擇，尚未驗證」。這兩種都不能在學校板發文，也不能用校名署名。
- **學校板已對所有 Google 帳號開放**（發文、留言、按讚），是你決定的。這等於任何人都能在長庚板或北大板發言，署名只能是匿名或真實暱稱；要用校名署名仍須學生證驗證，所以畫面上看到「長庚大學學生」就是真的驗證過。問答、分享心得、即時聊天仍限已驗證學生。這項改動包含 Supabase 的 `20261003100000_open_school_boards.sql`（只拿掉學校板的校籍檢查，其餘防護如限流、冪等、審核都原封不動）。
- 全站最下方有一行資料說明：「資料整理自各校官方公告，仍在逐筆人工核對」。

## 2. 上線前要你做的事（我不能代做）

1. **Google 登入金鑰**：Google Cloud Console 建立 OAuth 用戶端（網頁應用程式），授權的重新導向網址填 `https://你的網域/auth/oauth/google/callback`；伺服器設 `GOOGLE_OAUTH_CLIENT_ID`、`GOOGLE_OAUTH_CLIENT_SECRET`、`EXCHANGE_PUBLIC_BASE_URL`。同意畫面要有應用程式名稱、支援信箱；用的 scope 只有 `openid email profile`。
2. **先用兩所學校的真實信箱各試一次**：專案內的整理寫長庚 `@cgu.edu.tw` 是 Microsoft 365，Google Workspace 是 `@gap.cgu.edu.tw`；若你的 `b1128003@cgu.edu.tw` 不是 Google 帳號、或學校管理員擋第三方應用程式，就無法用它登入，只能用一般 Gmail 再選學校。這點只能實測。
3. **主機、網域（HTTPS）與正式 Supabase**（你選了正式 Supabase）：`EXCHANGE_ENVIRONMENT=production`，照 `docs/supabase-rollout-runbook.md` 建專案、依序套用 26 份 migration（含新增的兩份）、設定環境變數並逐項驗收；程式在 production 模式強制使用 Supabase，缺任何一個就拒絕啟動。隔離環境的完整驗證（`scripts/validate_supabase_runtime.py`）需要 Docker Desktop 與大型映像下載，我沒有執行，新增的兩份 migration 只通過語法解析。
4. **隱私權政策與服務條款**：專案裡的 `docs/closed-beta-privacy-notice.md` 只是空殼，Google 登入會取得姓名與信箱，上線前需要一份真正的說明（法律文字由你或專業人士決定，我沒有代寫）。
5. **誰來管留言**：公共板對所有 Google 帳號開放，要有人處理檢舉；管理員以 `EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS` 指定。
6. **全部免費**：`EXCHANGE_PRODUCT_RELEASE_MODE` 維持預設 `closed_beta`，登入帳號免費使用全部功能；畫面已改寫成「免費使用中：目前所有功能都免費開放，系統不會扣款」（不再出現「封閉測試」）。千萬不要設成 `public`：目前沒有付費機制，進階功能會變成無法使用。
7. **使用統計**：見 `docs/analytics.md`。要在 Supabase 套用 `20261003110000_analytics.sql`、指定管理員（`EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS` 或 `EXCHANGE_CONTENT_ADMIN_EMAILS`），並在隱私權政策寫明有蒐集匿名使用統計。

## 3. 資料狀況（2026-10-03）

- 長庚：合作校名單即時讀官方試算表，77 所；116 學年度秋季班流程 77 份依官網現行內容建立，截止日只寫「11/01–12/20」，因為官網沒有年度與時刻，沒有存成精確日期。
- 臺北大學：已換成 116 學年度，申請期間 2026-10-01 至 2026-10-23 17:00 有官方文字，已存成精確期限。
- 兩校 116 流程都**尚未人工核對**，不會發布也不會自動建立提醒。生活費、住宿等各校生活資訊沒有重新研究，缺口見 `docs/school-data-completeness-2026-10-02.md`。
- 長庚有 9 個合作校網頁失效（`docs/cgu-116-source-link-check-2026-10-03.csv`），需要人工找新網址。

## 4. 競品查核

方法與限制：用網頁搜尋（只能搜到被搜尋引擎收錄的公開網頁）加上直接讀幾個頁面。**沒有找到「跨校整合、針對台灣學生出國交換」的 App 或網站，但這不能證明不存在**：App Store／Google Play、Instagram、Threads、Facebook 社團、LINE 社群和 Notion 範本多半搜尋不到，需要你和女友實際到這些地方搜一輪。

| 類型 | 代表 | 它做得好的地方 | 它的限制 |
| --- | --- | --- | --- |
| 學校自己的出國平台 | [政大 outbound](https://outbound.nccu.edu.tw/)：746 所合作校、67 國，含線上申請與心得，申請要校內單一登入。[臺大合約一覽](https://oia.ntu.edu.tw/agreement/country)（216 項有效合約）、[清大海外交換學校一覽](https://oga.site.nthu.edu.tw/p/412-1524-18261.php?Lang=zh-tw)（可依地區、國家、校名搜尋）、[師大姊妹校查詢](https://bds.oia.ntnu.edu.tw/bds/web/partner-index)與心得查詢、[成大分區交換心得](https://oia.ncku.edu.tw/p/404-1032-252565.php?Lang=zh-tw)、[實踐大學交換學校列表](https://uscoia.usc.edu.tw/p/412-1049-1415.php?Lang=zh-tw) | 資料最權威、名額最新 | 只涵蓋自己學校，格式各校不同；不跨校比較；沒有個人化計畫與提醒 |
| 社群與個人整理 | [Dcard 留學板](https://www.dcard.tw/f/studyabroad/p/258653900)（交換心得、選校經驗）、PTT、各校 Facebook／LINE／IG 社團、個人部落格與 Notion（如[怎麼找最新交換資訊與學長姊心得](https://yunsdailyyyy.com/exchange-news/)） | 心得多、有人情味、更新快 | 零散難搜、沒有結構化的截止日與資格、時效與正確性無從核對 |
| 留學代辦與機構 | [IDP、EF、ed:m 等](https://tw.my-best.com/117097) | 有顧問、海外學位與遊學強 | 主力是海外申請與付費服務；校級交換是各校自己辦，幫助有限。代辦費用常見：校系排序確認約 4,000–8,000 元、多校申請約 40,000–80,000 元（見[TKB 整理](https://www.tkbgo.com.tw/zone/english/news/toNewsDetail?news_id=4857)） |
| 海外評論平台 | [Study Abroad 101](https://www.studyabroad101.com/countries/taiwan)、[Go Overseas](https://www.gooverseas.com/organization/asia-exchange-reviews) | 國際學生評價 | 站在「外國人來台灣」的角度，不是台灣學生出去 |

**你的位置**：把「各校官方資料整理成同一種格式」和「從查資料一路到追蹤申請進度」放在一起，這個組合我沒有在搜尋結果裡看到。

**要小心的地方**：
- 學校自己的平台資料最權威，也有申請系統；你的優勢是跨校與個人規劃，不是取代學校。
- Dcard 已經是學生找心得的習慣入口，剛上線時你的社群板是空的，需要先放內容或導流。
- 每多一所學校就多一份人工維護；資料出錯（尤其是期限）的代價是學生錯過申請，所以「尚未核對」的標示要一直清楚。
