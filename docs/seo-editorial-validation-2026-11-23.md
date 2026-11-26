# 2026-11-23 每日雙篇驗收

Asia/Taipei 2026-11-23，隔離分支 `codex/seo-daily-20261123`，base main `21c9dde902506e79ac2da99b3d33d0838ae3cd0b`。兩篇完整原創繁體中文圖文文章完成驗收，待同一個當日新 PR 審閱；未合併或部署。

| 題目／候選方向 | slug | 獨立用途 |
| --- | --- | --- |
| 交換考試要另外報名嗎？以 TUM 為例，核對報考、取消與完成紀錄（8） | `exchange-exam-registration` | 課位／報考分開、學院與語言中心手動／自動例外、正確項目／狀態、取消、三門假設課程與詢問欄位。 |
| 多益 Part 5 關係子句怎麼選？who、which、whose、where 與原創題解析（20） | `toeic-part-five-relative-clauses` | 先行詞與子句角色、場所受詞與地點關係、所有關係、逗號與省略、六題二十四選項逐項解析。 |

## 日期、庫存與避重

開始時鐘 UTC 11/23 00:05:06＝台北 08:05:06。環境初為 starting，持續等待同一 readiness 呼叫，同時獨立讀取 GitHub／官方來源；ready 後才執行 shell。已讀最新 workflow／backlog、63 篇庫存與相關全文／分工；上層及 tracked main 無 AGENTS。#78／#92 已合併祖先驗證，無未合併基礎相依。同日 PR、本地／遠端分支原不存在；提交前 main、所有 open heads、最近100個全狀態PR再次核對。

三個待審批次完整說明與各30檔已查：#401（11/20，head `26bbdb21387b554ab2b42c5bbd48f66f8ef4f0f9`）成績單／多益連接結構；#402（11/21，head `2d1c9a4aa2eecc0c048166568fc69f2d1392c866`）英語授課證明／AI電話；#403（11/22，head `9290f5d7e33d6e8e9efc933d9794af0d0a383337`）研修期間證明／多益主被動。六題已選且全部排除，不因未在main而重做，未匯入本分支。API待審test merge不是已合併。原63篇JSON、網址、published／modified全部位元相同；本分支63＋2＝65，不含六篇待審文章。10/30study-plan `97de3fda` 未重做，不造品牌比較。

交換篇和既有換課／衝堂、課綱評量、返國清單及待審成績單／MOI／期間證明分工，專門處理「哪一項考試是否登記」。關係子句篇與人稱／反身代名詞、詞性、時態及待審連接結構／主被動分工，專門處理先行詞與子句缺口。選題是核對庫存後的編輯判斷，無使用者Search Console、搜尋量、排名或流量資料。

兩篇均有直接回答、三點摘要、H1/H2與目錄、實用表格／清單、五步原創HTML圖解、FAQ、官方來源及查核年度、相關文章、母校／目的地／選校工具連結。沿用canonical、Article／Breadcrumb JSON-LD、社群標記、Sitemap、原生FAQ及手機橫捲；renderer／CSS／JS未改。

## 來源及教材

十個引用一手來源均HTTP200且實讀相關正文，來源記錄含要求／解析後網址、查核日、頁面標題、原始位元大小與SHA256、主張及限制。各頁未主張獨立修訂日期，明記2026-11-23查核日版本；無無法核對而保留的主張。

TUM中央報考／取消入口、CIT Examination Matters報考段落、CIT Incoming Informatics考試與重考、LanguageCenter考試／登記／取消與短版報考指引均實讀。CIT課程不等於考試登記、每次含重考分開處理、回查My studies／Exams清單、系統provisional標記、部分附加現場程序分別核對。語言中心確認課位自動登記與缺漏處理、應選正確考官／場次、學生自行取消、不能代取消／逾期取消與兩種紀錄差異明確限定，未寫成所有TUM或所有德國大學通則。沒有登入TUMonline、私有表件或進行報考／取消實測；不捏造按鈕、個人資格、費用、期限或補登結果。A／B／C三門課為原創假設，無真實課號或日程；詢問稿未寄出。

多益臺灣現行內容與Part5範例directions實讀，核對TOEIC Listening & Reading、句子填空30題及四選項最佳答案。British Council限定、非限定、Relative pronouns參考三篇教學正文已讀；未引用留言／互動題，未翻寫來源人物、故事或例句。六題答案B／C／C／D／A／C，分別檢查人作主詞、物作受詞、supplier的invoice、完整核心加地點、leased缺場所受詞、逗號補充句which主詞；逐項排除干擾，承認限定句that或受詞省略等選項外改寫。自寫sensors省略／多餘them、technician主詞不能直接刪與screens逗號意思比較，沒有強迫唯一英文寫法。6×4＝24選項與官方Part5共30題分開，無難度占比、校準成績、實際學生／AI成效或滿分保證。

## 攝影、閱讀與套件

Yan Krukau／Pexels8199167（教室使用筆電）與 Gül Işık／Pexels6747749（手翻書、筆電）兩張ID未在main或三個待審批次攝影紀錄使用。實讀來源頁ImageObject／作者／原JPEG／完整Pexels License：網站使用與修改、署名可選，並保留不得不當描繪／背書／原樣轉售／素材再分發／商標等限制。顯示alt、圖說與作者來源；素材並非實際TUM校園／帳號／交換申請者或官方多益教材。

1536×1024 WebP各114,280／262,504bytes，均低於450KB；EXIF方向、RGB、LANCZOSfit，quality83／method6；中心點分別(0.5,0.45)／(0.5,0.48)，無生成、重繪或改色。原圖及15張最終驗收圖逐張目視：桌面1440、手機320、兩文中攝影、兩HTML圖解、八個程序／案例／文法解析段落、3:2及2:1裁切。人臉／手／筆電、翻書手／書／筆電保留，2:1帽頂略裁但主體完整；原圖盆栽不在成品，alt已在正式測試前修正。中英文、provisional、三課案例、各題角色與省略說明可讀；手機表格實際橫捲，頁面無溢出。長區塊截圖暫隱固定頁首／裝飾線避免拼接遮字，產品、完整截圖與斷言未改。

| 檢查 | 實際結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 65篇，0 errors |
| 六模組SEO單元／整合／release gate | 193 passed（83.19秒） |
| 三模組桌面／手機E2E | 76 passed（211.16秒） |
| 兩篇×320／390／1440，JavaScript關閉 | 六組通過；目錄、FAQ、圖片／credit、實際橫捲、相關導航、母校／目的地／工具、canonical／JSON-LD |
| 重建wheel、逐檔及checkout外匯入 | 65 JSON／65 WebP、全部59 CSS、481字型目錄檔及閱讀資產，共671唯一檔位元相同；外部載入65篇與新slug |

單元、E2E、六組閱讀與wheel各一次完整通過；初次gate通過後修正裁切alt，再固定產品並執行最終gate與其他檢查，最終雜湊不變。使用本批隔離venv及最新main frozen lock，未改共用venv。Wheel 2,529,939,461bytes留task cache，成功核對後移除本次build暫存。預留空間時先確認自己11/18checkout分支、乾淨狀態、HEAD已合併祖先、兩篇在main位元相同才移除checkout；只另移除自己11/22可重建wheel（2,529,848,505bytes），保留Git分支／歷史／PR／來源證據及待審#401／#402／#403 checkout。未覆寫他人未提交變更。

本地驗收不是正式部署、Google收錄、搜尋成效或真實Core Web Vitals；未寄信、操作私人校務、部署Windows正式機或要求Google索引。

- [來源／HTTP／版本](seo-editorial-sources-2026-11-23.json)、[原創案例及題目核對](seo-editorial-exercises-2026-11-23.json)
- [攝影授權](seo-editorial-photography-2026-11-23.json)、[原63篇雜湊](seo-editorial-inventory-2026-11-23.json)、[PR日期查核](seo-editorial-pr-audit-2026-11-23.json)
- [Gate](seo-editorial-checks-2026-11-23.json)、[命令與輸出](seo-editorial-tests-2026-11-23.txt)、[套件逐檔](seo-editorial-package-2026-11-23.json)
- [瀏覽器與15圖雜湊](seo-editorial-browser-2026-11-23.json)、[桌面](seo-previews-2026-11-23/desktop-1440.jpg)、[手機](seo-previews-2026-11-23/mobile-320.jpg)、[裁切](seo-previews-2026-11-23/photography-crops.jpg)

待審 PR：[ #404 ](https://github.com/blizzard-new/abroad/pull/404)，OPEN／非draft／未合併，GitHub確認mergeable。建立時head `429247ef5a9613ce9330a071369a1ddfa1cbfcad`，30檔包括兩篇JSON、兩張WebP及15張驗收圖。兩個image CI仍in_progress，Supabase Preview skipped；不宣稱遠端全部通過。已呼叫任務attach_artifact但40秒未回傳，list_artifacts亦10秒未回傳，故附件狀態未確認，PR建立本身已核對成功。此後僅回填本段、PR audit及本日選題紀錄，產品與測前固定雜湊一致，未重新產文或發布。
