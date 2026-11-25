# 2026-11-25 每日雙篇驗收

Asia/Taipei 2026-11-25，隔離分支 `codex/seo-daily-20261125`，base main `21c9dde902506e79ac2da99b3d33d0838ae3cd0b`。兩篇完整原創繁體中文圖文文章完成本地驗收，將放入本日同一個新待審PR，未合併或部署。

| 題目／候選方向 | slug | 獨立用途 |
| --- | --- | --- |
| 德國交換生垃圾分類怎麼做？柏林垃圾桶、玻璃與退瓶指南（6） | `germany-berlin-waste-sorting` | 柏林材質與物品條件分類、包裝玻璃分色、押金分流、六件物品卡及住宿詢問。 |
| 用 AI 練英文圖表描述：趨勢、百分比與數據核對 Prompt（17） | `ai-english-chart-description` | 自讀資料、逐句證據核對、數量與單位、三輪Prompt、原創前後稿與百分點換題。 |

## 避重與實作範圍

初始UTC11/25 00:00:44＝台北08:00:44。環境初為starting，持續等待同一readiness呼叫並獨立查GitHub與來源；ready後才執行shell。讀最新workflow／backlog、63篇庫存及抵達第一週、住房清單、AI講稿、英文改寫、英文訂正相關全文。上層及tracked main無AGENTS。#78／#92已合併祖先驗證，無基礎相依；同日本地／遠端分支與PR原不存在，提交前重查main、五個open heads與最近100個全狀態PR。

五批待審：#401（11/20，`26bbdb21387b554ab2b42c5bbd48f66f8ef4f0f9`）成績單／多益連接結構；#402（11/21，`2d1c9a4aa2eecc0c048166568fc69f2d1392c866`）MOI／AI電話；#403（11/22，`9290f5d7e33d6e8e9efc933d9794af0d0a383337`）期間證明／主被動；#404（11/23，`40759bc03a0c046d302836ba3d453020173254a3`）考試登記／關係子句；#405（11/24，`acefe901b8e591e8e5b5275e84e3b21e1ac35049`）德國廣播費／比較句。五份完整PR說明、各30檔及十篇JSON分工查核，十題已選且排除，未匯入。test merge SHA不是完成合併。原63篇JSON位元、URL、published／modified不變，本分支63＋2＝65，不含十篇待審文章。

柏林分類是特定所在地抵達生活任務；住房總表只概述契約／入住及垃圾規則確認，抵達指南為行政總覽，廣播費為住所帳號計費，均無本文分類／退瓶完整流程。AI篇處理圖表值、基期、單位、整體與中間趨勢；和講稿的提案／投影片／時間、改寫的散文命題、文法訂正有獨立練習目標。選題為編輯判斷，無Search Console、搜尋量、排名或流量證據。10/30study-plan `97de3fda`未重做，無三品牌實測不造比較。

兩篇有直接回答、三點摘要、H1/H2／目錄、實用表格與清單、五步HTML圖解、文中攝影、六題FAQ、官方來源與2026適用範圍、四篇相關文及母校／目的地／工具連結。沿用canonical、Article／Breadcrumb JSON-LD、社群標記、Sitemap、手機橫捲表格、原生FAQ與無JavaScript閱讀；renderer／CSS／JS未改。

## 一手來源、原創教材與界線

十一個引用一手頁均HTTP200且實讀正文；來源紀錄保存請求／實際網址、標題、原始大小、SHA256、版本、實讀範圍與限制。沒有獨立修訂日的頁面只標查核日，不以搜尋摘要、留言或頁尾版權反推更新日。

柏林BSR材料、紙、Biogut、玻璃與Restabfall五頁核對接受與排除類別。Bioplastik／塑膠袋不進Biogut；塑膠金屬複合包裝及部分日用品進Wertstoffe，紙玻璃電池電器排除。包裝玻璃與飲水杯／陶瓷／鏡窗／燈泡分開，依實際標示分色；不推定每棟宿舍都有同樣容器。未引用歷史用紙量、碳排、柴油、車輛、桶容量、費用、清運日、罰款或法律PDF，也未認定Biogut桶色。

DPG完整FAQ含div答案已讀，核對適用一次性DPG標誌、0.25歐元返還、材質類型及小店品牌限制，和Mehrweg分開；不是所有瓶子都25分、任何門市收全部。2022果汁過渡條款明確排除，©2025不是修訂日；沒有容積／商品種類法律清單、退瓶機實測或收入保證。六件假設物品、條件／理由、五步分流與未寄出詢問稿均自寫，非真實宿舍觀察。

AI篇實讀British Council Describing charts正文／Tips，採圖意、總覽、關鍵趨勢、時態與任務原則；原頁統計為練習未必準確，不引用其手機數據／圖／原稿或互動題。ONS完整百分比／百分點教學與國會圖書館2026-03-17指南核對公式；國會頁一處「25%of20＝5%」單位誤植未沿用，只使用可獨立驗算的一般公式。沒有原頁統計或例題改寫。

OpenAI兩篇help正文核對清楚背景、逐輪修訂及錯誤／自信誤答；更新只顯示last month，不反推日期。先讀既有AI指南再查官方來源。以手動貼表的文字工作流程教學，未假設讀圖、上傳、語音、付費分析或地區可用性，無帳號／模型／方案／品牌比較實測。三輪Prompt、輸入、刻意錯誤回饋、前後稿及人工清單都是原創假設教材，非真實模型輸出、學生表現或官方程度／成績。課堂使用依教師規定，真實資料另核對分享權限。

資料A四週12／18／15／21報名人次允許跨週重複：首末＋9、以12為基期＋75%、中間下降3、合計66人次，沒有出席、不同人數或原因。原稿四錯為steadily、attendance、advertising caused、66different students；75%算式本身正確。資料B獨立兩期各40份，正面10／16份＝25%／40%，差15百分點，相對＋60%。八筆Decimal逐項核對；基期0不硬除，資料不證明同一群人或因果。Prompt依序觀察對證據、最小修訂、新資料先自己寫再回饋，層次屬編輯設計，不換算CEFR或固定進步幅度。

## 圖片、閱讀與套件驗收

Polina Tankilevitch／Pexels3735218（玻璃瓶布袋）及Yan Krukau／Pexels7698711（紙本圖表、筆電、手持鉛筆）在main與五個待審攝影紀錄未用。來源頁ImageObject、作者、原JPEG及完整Pexels License實讀；網站使用與修改允許、署名可選，仍保留不當描繪、背書、原樣轉售、素材再分發及商標限制。圖說明示素材情境，不是柏林回收站／校園／真實申請者或模型成果，照片數據不是本文資料。

成品1536×1024 WebP為52,310／126,380bytes，低於450KB。EXIF方向、RGB、LANCZOSfit中心(0.5,0.5)、quality83／method6；無生成、改色或重繪。有alt／尺寸／lazyloading／圖說／署名來源。原圖與15張驗收圖全部目視：桌面1440、手機320、兩照片／兩圖解、八個關鍵段落與3:2／2:1裁切；瓶袋、圖表／手／鉛筆／筆電保留，中英文與德文、算式、Prompt及前後稿可讀。手機表格實際橫捲，頁面無橫溢。長區塊截圖暫隱固定頁首與裝飾線以免拼接遮字，產品、全頁截圖與斷言未改。

| 檢查 | 實際結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 65篇，0 errors |
| 六模組SEO單元／整合／release gate | 193 passed（103.9秒） |
| 三模組桌面／手機E2E | 76 passed（237.25秒） |
| 兩篇×320／390／1440，JavaScript關閉 | 六組通過：目錄、FAQ、圖片／credit、表格橫捲、相關導航、母校／目的地／工具、canonical／JSON-LD |
| Wheel重建／checkout外匯入 | 65 JSON／65 WebP、全部59 CSS、481字型目錄檔與閱讀資產，共671唯一檔位元一致；外部載入65篇與兩個新slug |

各產品檢查一次完整通過，測前固定2JSON／2WebP／59CSS，最終雜湊一致。新隔離venv在checkoutready後frozen同步一次成功，未動共用venv。Wheel 2,529,742,289bytes存taskcache，核對後移除本次build暫存。為空間只移除自己11/20乾淨且完整推送的checkout：本地／遠端HEAD匹配、未提交空、ignored僅Python／測試快取，未force，保留分支／歷史／PR401（仍OPEN未合併）／已提交證據／來源快取。另移除自己11/24可重建Wheel快取2,529,670,756bytes；其他四個待審checkout、原root與共用venv保留。Reflink試探不支援、僅刪探測暫存；一次過長shell參數在文章寫入前遭拒，改apply_patch後成功，均在產品測試前處理。

本地驗收不等於正式上線、Google收錄、排名或真實Core Web Vitals；未合併、部署Windows正式機、寄信、操作私人帳號或提交索引。

- [來源／版本](seo-editorial-sources-2026-11-25.json)、[教材／試算](seo-editorial-exercises-2026-11-25.json)、[攝影授權](seo-editorial-photography-2026-11-25.json)
- [原63篇雜湊](seo-editorial-inventory-2026-11-25.json)、[PR查核](seo-editorial-pr-audit-2026-11-25.json)、[Gate](seo-editorial-checks-2026-11-25.json)
- [命令與結果](seo-editorial-tests-2026-11-25.txt)、[套件逐檔](seo-editorial-package-2026-11-25.json)、[瀏覽器與15圖](seo-editorial-browser-2026-11-25.json)
- [桌面](seo-previews-2026-11-25/desktop-1440.jpg)、[手機](seo-previews-2026-11-25/mobile-320.jpg)、[裁切](seo-previews-2026-11-25/photography-crops.jpg)

待審PR：[ #406 ](https://github.com/blizzard-new/abroad/pull/406)，OPEN／非draft／未合併，GitHub確認mergeable。建立時head `5386fd03622e5d5964299319f00c48a6da41b1b0`，30檔包含兩篇JSON、兩張WebP與15張驗收圖。兩個image CI仍in_progress，Supabase Preview skipped，不宣稱遠端全部通過。已呼叫attach_artifact但40秒未回傳，list_artifacts亦10秒未回傳，故任務附件未確認；PR建立與內容另外查核成功。建立後只回填本段、PR audit及本日選題紀錄，產品與測前雜湊一致，未重新產文或發布。
