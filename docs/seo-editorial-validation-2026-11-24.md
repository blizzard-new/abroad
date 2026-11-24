# 2026-11-24 每日雙篇驗收

Asia/Taipei 2026-11-24，分支 `codex/seo-daily-20261124`，base main `21c9dde902506e79ac2da99b3d33d0838ae3cd0b`。兩篇完整原創繁體中文圖文文章完成驗收，待本日同一新PR審閱，未合併或部署。

| 題目／候選方向 | slug | 獨立用途 |
| --- | --- | --- |
| 德國交換生廣播費要繳嗎？Rundfunkbeitrag、宿舍與 WG 分攤指南（6／10） | `germany-broadcasting-fee` | 計費住所與戶型、同戶帳號與來信、月費率／付款週期、私人分攤、減免查核及離境交接。 |
| 多益 Part 5 比較級與最高級怎麼選？than、as…as 與原創題解析（20） | `toeic-part-five-comparisons` | 比較對象／集合、特性、方向、形容詞／副詞與程度，六題24選項逐項解析及換句。 |

## 避重與工作範圍

開始時鐘UTC11/24 00:00:13＝台北08:00:13。環境初為starting，持續等待同一readiness呼叫，同時獨立查GitHub與來源；ready後才執行shell。最新workflow／backlog、63篇庫存及相關全文已讀：德國費用、住宿總表、柏林住址登記、Part5詞性與各篇分工已比對。上層及tracked main無AGENTS；#78／#92已合併祖先驗證，無基礎相依。同日PR與本地／遠端分支原不存在，提交前再次核對main、四個open heads、最近100個全狀態PR。

待審#401（11/20，head `26bbdb21387b554ab2b42c5bbd48f66f8ef4f0f9`）成績單／多益連接結構；#402（11/21，`2d1c9a4aa2eecc0c048166568fc69f2d1392c866`）英語授課證明／AI電話；#403（11/22，`9290f5d7e33d6e8e9efc933d9794af0d0a383337`）期間證明／多益主被動；#404（11/23，`40759bc03a0c046d302836ba3d453020173254a3`）考試登記／多益關係子句。四份完整PR說明、各30檔及八篇JSON分工均查核，八題已選且排除，未匯入本分支；待審test merge不是完成合併。原63篇JSON、URL、published／modified位元相同，本分支63＋2＝65，不含八篇待審內容。

廣播費是特定德國住所與帳號行政問題，既有德國費用篇不含此流程，住宿總表處理契約／入住退房，柏林住址篇處理Bürgeramt，皆未重寫。比較句聚焦範圍／方向／程度，與字族、時態、人稱代名詞、連接結構、語態及關係子句分工。選題為編輯判斷，沒有Search Console、搜尋量、排名、流量或「最好學校」實證。10/30study-plan `97de3fda`未重做，沒有三品牌實測不造比較。

兩篇有直接回答、三點摘要、清楚H1/H2／目錄、表格／清單、原創五步HTML圖解、文中攝影、FAQ、來源與年度、相關文章、母校／目的地／工具連結。沿用canonical、Article／Breadcrumb JSON-LD、社群標記、Sitemap、原生FAQ與手機表格橫捲；renderer／CSS／JS未改。

## 來源、試算與原創教材

十個引用一手來源均HTTP200且實讀正文；各記錄請求／實際網址、標題、原始大小與SHA256、查核日、引用範圍與限制。未見獨立修訂日的頁面明記2026-11-24版本，不把留言日、搜尋摘要或導覽頁當更新證據。

直接閱讀Beitragsservice的英文總覽、Students and Apprentices、德文付款、Auslandsaufenthalt及註銷公開入口。確認成年住戶、一住所一份、不依媒體使用、WG與公共走廊宿舍／共同前門分流、同戶帳號回覆、交換／獎學金不自動免繳；付款頁月費18.36歐元與三個月55.08及其他預付安排分開。減免需正式資格與結果，不替臺灣學生判定；不轉載財力／居留要求、罰款或申訴法律期限。

離境僅按官方「永久搬出國且完全放棄德國住所」與遷出證明、留下住戶另登記等條件說明，不把機票、學期末或短暫離境當自動註銷。Wohnung abmelden可讀公開body說需條件／帳號／附件，但互動表單另行載入；沒有填送、上傳、登入或個人帳號實測，也未承諾生效、退款或處理天數。TU Dortmund探索頁導覽可讀，但細節webopen兩次逾時，因此未引用，改直接核對主管服務來源，無無法查證主張保留。詢問稿原創且未寄送。

四筆假設試算以Decimal核對：18.36÷4＝4.59、18.36×4＝73.44、18.36×3＝55.08、55.08÷4＝13.77歐元。前提是四成年、同一已確認住所或四個獨立計費房、無減免、完整月份且戶況／費率不變；私人平均分攤不是官方優惠，也不把同一筆55.08再次算新增成本。未按半月、追溯、換人或退款推算實際帳單。

多益臺灣官方內容及directions核對TOEIC Listening & Reading、Part5句子填空30題及四選一最佳答案。British Council形容詞比較、副詞比較、Modifying comparatives三篇教學正文均讀，未用留言／互動測驗／促銷或原頁人物、國家、旅館、襪子、家庭例句。六題新寫，答案C／D／A／C／C／B，分別為shorter、全五條路線中的shortest、as durable as、much quieter、修飾processed的more accurately、less confusing than；逐項解釋干擾選項。材料不代表實際產品測試或路線研究。

not as long as改寫為反向longer than，保留對象、特性及方向；the revised checklist不是最高級，than可由已知語境省略，僅知三方案可行不足以排名。6×4＝24選項與官方30題分開；沒有官方題庫、占比、難度、量尺估分、真實學生／AI成果或專家審核。

## 攝影與驗收

SHVETS production／Pexels8036579（手持鑰匙、門邊）及Mizuno K／Pexels12911699（持紙筆對照筆電）未在main或四個待審攝影紀錄使用。實讀來源頁ImageObject、作者、原JPEG與完整Pexels License：可用於網站與修改、署名可選，保留不得不當描繪、背書、原樣轉售、素材再分發、商標等限制。有alt／圖說／署名與來源，非德國校園／宿舍認定／實際交換學生或官方多益教材。

成品1536×1024 WebP為45,402／62,202bytes，均低於450KB；EXIF方向、RGB、LANCZOSfit，中心點(0.5,0.5)／(0.5,0.3)，quality83／method6，無生成、重繪或改色。原圖及15張最終驗收圖已逐張目視：桌面1440、手機320、兩照片／圖說、兩圖解、八個關鍵段落及3:2／2:1裁切。鑰匙／手／門、紙筆／手／筆電保留，中英文及長德文字可讀，月費／分攤／離境條件及六題解釋未遮蓋。手機表格實際橫捲，頁面無溢出。長區塊截圖暫隱固定頁首與裝飾線避免拼接遮字，產品、完整截圖與斷言未改。

| 檢查 | 實際結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 65篇、0 errors |
| 六模組SEO單元／整合／release gate | 193 passed（82.04秒） |
| 三模組桌面／手機E2E | 76 passed（216.05秒） |
| 兩篇×320／390／1440，JavaScript關閉 | 六組通過：目錄、FAQ、圖片／credit、橫捲、相關導航、母校／目的地／工具、canonical／JSON-LD |
| 重建Wheel與checkout外匯入 | 65 JSON／65 WebP、全部59 CSS、481字型目錄檔及閱讀資產，共671唯一檔位元一致；外部載入65篇及新slug |

各產品檢查一次完整通過，測前固定，最終雜湊相同。使用本批隔離venv與最新main frozen lock，未動共用venv。首次環境同步在checkout尚未完成時遇缺lock而退出，完成checkout後以frozen重試成功，產品測試前已處理；沒有宣稱首次安裝成功。Wheel 2,529,670,755bytes留task cache，核對後移除本次build暫存。為預留空間，自己的11/19checkout經分支／乾淨狀態／合併祖先／兩篇JSON與main相同查核後才移除；另只移除自己11/23可重建Wheel快取（2,529,939,462bytes），保留Git分支／歷史／PR／證據及四個待審checkout。最初較廣的本次checkout再縮為前批相同sparse範圍，未刪他人資料或覆寫未提交變更。

本地驗收不等於正式上線、Google收錄、排名或真實Core Web Vitals；未合併、部署Windows正式機、寄信、操作銀行／校務／廣播費私人帳號或要求索引。

- [來源與版本](seo-editorial-sources-2026-11-24.json)、[試算及原創題核對](seo-editorial-exercises-2026-11-24.json)
- [攝影授權](seo-editorial-photography-2026-11-24.json)、[原63篇雜湊](seo-editorial-inventory-2026-11-24.json)、[PR日期查核](seo-editorial-pr-audit-2026-11-24.json)
- [Gate](seo-editorial-checks-2026-11-24.json)、[命令與輸出](seo-editorial-tests-2026-11-24.txt)、[套件逐檔](seo-editorial-package-2026-11-24.json)
- [瀏覽器與15圖](seo-editorial-browser-2026-11-24.json)、[桌面](seo-previews-2026-11-24/desktop-1440.jpg)、[手機](seo-previews-2026-11-24/mobile-320.jpg)、[裁切](seo-previews-2026-11-24/photography-crops.jpg)

待審PR：[ #405 ](https://github.com/blizzard-new/abroad/pull/405)，OPEN／非draft／未合併，GitHub確認mergeable。建立時head `e28610e0bb39b4a2f4e1df51ef14d62cbd6c29c5`，30檔包括兩篇JSON、兩張WebP及15張驗收圖。兩個image CI仍in_progress，Supabase Preview skipped，不宣稱遠端全部通過。已呼叫attach_artifact但40秒未回傳，list_artifacts亦10秒未回傳，因此任務附件未確認；PR建立與內容另已核對成功。之後僅回填本段、PR audit與本日選題紀錄，產品與測前固定雜湊一致，未重新產文或發布。
