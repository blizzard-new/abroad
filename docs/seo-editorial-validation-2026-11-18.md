# 2026-11-18 每日雙篇驗收

Asia/Taipei 批次，隔離分支 `codex/seo-daily-20261118`，base main `cf3d5e6b8423c9cae171603c37525a7b8d9110fb`。兩篇完整原創繁體中文圖文文章及配圖完成，待同一個新 PR 審閱；未合併、部署或要求索引。

| 文章／候選方向 | slug | 獨立搜尋意圖 |
| --- | --- | --- |
| 德國交換生住址登記怎麼辦？柏林 Anmeldung、房東確認書與文件清單（6：抵達與行政） | `germany-residence-registration` | 德國 BMG 短住例外、住宿提供者確認及柏林臨櫃／線上條件、缺件／預約與完成證明。 |
| 多益 Part 5 代名詞怎麼選？主受格、所有格與反身代名詞原創題解析（20：多益準備） | `toeic-part-five-pronouns` | 子句角色、歸屬與指涉、反身／獨力／強調；六題原創四選一、歧義及換句訂正。 |

以實際時鐘換算批次：開始為 2026-11-17 23:58:01 UTC，即 11/18 07:58:01 台北，不將 UTC 11/17 當作昨日重試。昨日 #372 已合併，課綱評量及 AI 小組討論兩篇已在 main，排除重做；merge commit 祖先已驗證。#78／#92 也在 main，無未合併基礎相依。讀最新 workflow、backlog、59 篇庫存與相關正文；祖先及 tracked tree 均無 AGENTS。只有 open #397，已讀完整說明與 53 個變更檔案，為 Web／Flutter 流程與 CI，無 editorial 或閱讀 renderer 重疊。開始前無同日分支／PR，提交前再查 main、open heads、最近 100 個全狀態 PR，未變且無本日批次。10/30 study-plan `97de3fda` 未重做，無三品牌實測就不捏造比較。

選題為編輯判斷，沒有使用者 Search Console、搜尋量、排名或成效資料。柏林篇與抵達總覽、德國費用及日本新宿區規則區隔：BMG 第 27 條、Wohnungsgeberbestätigung、線上身分資格與 eAT 排除有各自一手依據，非替換國名；代名詞篇處理既有詞性字族與時態時間線沒有涵蓋的角色、指涉與反身。原 59 篇 JSON、URL、published／modified 完全不變，共 61 篇。兩篇均有直接回答、摘要、H1/H2、目錄、表格／清單、原創 HTML 五步圖、FAQ、官方來源／日期、相關文章及母校／目的地／選校工具連結，沿用 canonical、Article／Breadcrumb、社群與 Sitemap。

## 一手來源與教材範圍

11 個文章引用頁面均為 HTTP 200，實讀對應正文。柏林服務頁核對入住後 14 日、原住國外且最長三個月等例外、文件清單、租約不可取代入住確認、線上條件與免費登記；無獨立更新日期則記本次查核日。BMG 德文第 17／19／27 條逐條核對，另讀總法頁版本：最後由 2026-07-22 法第 10 條修正（BGBl. 2026 I Nr. 222），不使用未核對的舊英文譯本。

原住國外、首次移入且已計畫住超過三個月的虛構五個月情境，按柏林通常 14 日流程安排；不把第 27 條短住例外寫成每個人都可先等三個月。原短住後延長、多住所或特殊住宿須問機關，不自行算個案期限；未把三個月換成 90 天。入住、預約、完成登記及居留許可分開；eAT／BundID 不代表符合線上登記。住宿提供者與所有權人有別，缺確認書須立即告知機關，不接受無實住地址。所有欄位表、紀錄範本、五個月情境及未寄送德文詢問均自寫；表單只指向官方服務頁入口，未聲稱下載或填完官方 PDF。

Welcome Centre 頁面標示 2026-01-06，預約指引與預約確認用途按柏林範圍記載，未解讀成全德國逾期免責；其短住措辭與服務頁在邊界有差異，以本篇引用的服務頁「最長三個月」說明，個案仍問主管機關。沒有引用未核對的簽證、其他費用、翻譯、獎學金或處理時間。

臺灣多益官方確認 TOEIC Listening & Reading Part 5 為 30 題及四選一 directions，與 Speaking／Writing 分開。British Council 正文核對主受格、所有限定詞／所有代名詞、反身、by oneself、強調與位置／陪同介系詞限制；不依留言立論或將留言日期當版本，也不複製教材題目、官方題幹或選項。

六題與 24 選項、情境、解析、歧義與換句全為 UniWay 原創；答案依序 B、D、A、C、B、D。第 5 題未把可有「另一人」解釋的 her 列為錯項；另說明 her 語意可能不同。第 6 題為 by themselves 獨力結構，不泛化為所有介系詞後一律受格。Mina／Sara 歸屬不足的句子不硬選唯一答案；換句同時調整名詞與謂語數。沒有真實考生、專家審核、模型輸出／錄音或成效測試，也不以六題估分。除題數／選項數及原始法定單位外無費用或分數試算；六乘四等於 24，沒有官方統計與假設試算混用。

三個探索網址 404：猜測的 Berlin `/en/`、TOEIC `/sample-question/` 與 TU Berlin 頁。全部排除，改以可讀的德文服務頁及官方 sample05；未冒用不可查的存檔。詳細 HTTP、解析後 URL、原文雜湊、版本與限制均保留。

## 攝影與閱讀畫面

兩張新真實攝影：Miroslaw LT／Pexels 柏林住宅外牆（37174430）、Tima Miroshnichenko／Pexels 鉛筆書寫（5303510），來源 ID 不在既有庫存與紀錄。核對頁面 ImageObject、創作者、原 JPEG 及 Pexels License，允許網站使用與修改，禁止冒稱背書、素材原樣轉售或不當描繪等限制已讀。1536×1024 WebP 為 221,566／36,464 bytes，均低於 450 KB；EXIF 方向、RGB／LANCZOS 中心裁切、quality83／method6，無生成、重繪或變色。alt 與裁切後畫面相符，圖說明示不是合作宿舍、機關、實際申請者、正式多益題本或成績。

全部 15 張最終畫面已目視：桌面 1440、手機 320、兩張文中照片、兩張圖解、八段重點內容、3:2／2:1 裁切。住宅窗戶／陽台雕飾與書寫手／鉛筆／筆記本保留，中德英文與表格、原創題目／解析、辦理與訂正步驟可讀。390px 表格實際左右捲動，頁面無溢出。長區塊截圖暫隱固定頁首與裝飾線以免拼接遮字；產品頁、完整截圖及測量斷言未改。

## 驗證與已修復問題

| 檢查 | 最終結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 61 篇、0 errors |
| 六模組 SEO 單元／整合／release gate | 188 passed（89.12 秒） |
| 三模組桌面／手機 E2E | 71 passed（220.84 秒） |
| 兩篇 × 320／390／1440，JavaScript 關閉 | 六組通過：目錄、原生 FAQ、圖片／credit、實際橫捲、相關及母校／目的地／工具、canonical／JSON-LD |
| 重建 wheel、逐檔與 checkout 外匯入 | 61 JSON、61 WebP、全部 59 CSS、481 字型目錄檔及閱讀資產，共 663 唯一檔一致；外部匯入 61 篇及兩個新 slug |

初跑 188 SEO／71 E2E 已通過，但額外 320px 無 JavaScript 檢查實際失敗（頁寬 327 > 320）：官方長字 Wohnungsgeberbestätigung 在文章導言摘要及重點清單缺換行。兩次診斷定位 lead／takeaways；只為這兩個選擇器加入 `overflow-wrap: anywhere`，保留原文而非截字／隱藏溢出。CSS 修正後完整重跑 SEO、E2E、六組額外瀏覽器與 wheel，以上均為最終結果；原始失敗與兩次診斷、前後測試輸出保留，未把首次失敗寫成首次全過。JSON／照片跨跑次不變，最終 CSS／文章／圖片雜湊再核對。

採最新 main 的 uv.lock 建隔離 venv，`uv sync --frozen --extra dev` 完成，Python 3.12.14、soupsieve 4.1.1，共用 venv 未改。Wheel 2,529,142,221 bytes 留 cache；移除自己已完成且乾淨的 11/13 checkout、可重建的昨日及修正前 wheel／本批 build，以留建置空間，保留 Git 歷史／PR／證據，未動他人的未提交變更。本地驗收不等於正式部署、已收錄、搜尋成效或真實 Core Web Vitals。

- [來源版本／正文／HTTP 與限制](seo-editorial-sources-2026-11-18.json)、[原創題／法規條件檢核](seo-editorial-exercises-2026-11-18.json)
- [攝影來源與授權](seo-editorial-photography-2026-11-18.json)、[59 篇原文雜湊](seo-editorial-inventory-2026-11-18.json)、[PR／日期查核](seo-editorial-pr-audit-2026-11-18.json)
- [完整 gate](seo-editorial-checks-2026-11-18.json)、[命令與前後輸出](seo-editorial-tests-2026-11-18.txt)、[套件逐檔](seo-editorial-package-2026-11-18.json)
- [瀏覽器／15 圖雜湊](seo-editorial-browser-2026-11-18.json)、[桌面](seo-previews-2026-11-18/desktop-1440.jpg)、[手機](seo-previews-2026-11-18/mobile-320.jpg)、[裁切](seo-previews-2026-11-18/photography-crops.jpg)

[PR #398](https://github.com/blizzard-new/abroad/pull/398) 已建立，OPEN、非 draft、MERGEABLE。完整內容 head `22975fd3a70c68e53794c9df043dad3f1b41fed9`；建立後只回填這份驗收、PR audit 與 backlog，文章／圖片／CSS 雜湊不變。此內容 head 的兩個 TLS trust regression image 檢查仍進行中，Supabase Preview skipped，遠端 CI 未宣稱全部通過，以 PR 最新狀態為準。

任務附加 `codex_app.attach_artifact` 等待 40 秒無回覆，`list_artifacts` 等待 10 秒也無回覆，因此附加狀態未確認；實際 PR URL、head 與待審狀態已另行驗證。不要求使用者重複批准，也不宣稱附件成功。未合併、部署或要求索引。
