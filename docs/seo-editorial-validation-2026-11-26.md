# 2026-11-26 每日雙篇驗收

Asia/Taipei 2026-11-26，隔離分支 `codex/seo-daily-20261126`，base main `21c9dde902506e79ac2da99b3d33d0838ae3cd0b`。兩篇完整原創繁體中文圖文文章完成本地驗收，將同屬本日一個新待審PR，未合併或部署。

| 題目／候選方向 | slug | 獨立用途 |
| --- | --- | --- |
| 日本交換生手機怎麼辦？eSIM、電話號碼與整期通訊費檢查表（6） | `japan-exchange-mobile-plan` | 數據／語音／SMS／原門號、裝置相容性、分線、有效期、整期成本與結約。 |
| 多益 Part 5 條件句怎麼判斷？if、unless 與原創題解析（20） | `toeic-part-five-conditionals` | 條件與結果的時間／語氣、六題24選項、unless否定、間接if及混合結果時間。 |

## 避重與範圍

初始UTC11/26 00:01:11＝台北08:01:11。環境初為starting，持續等待同一readiness呼叫，同時用連接工具查main／來源並準備教材；ready後才執行shell。讀最新workflow／backlog、63篇庫存與相關完整抵達、返國、日本費用、Part5時態／詞性指南。上層及tracked main無AGENTS；#78／#92已合併祖先驗證，無基礎相依。原先沒有同日本地／遠端分支或PR；提交前再次核對main、七個open heads及最近100個全狀態PR。

六批SEO待審：#401（11/20）成績單／連接結構；#402（11/21）MOI／AI電話；#403（11/22）期間證明／主被動；#404（11/23）考試登記／關係子句；#405（11/24）德國廣播費／比較句；#406（11/25）柏林分類／AI英文圖表。七份完整PR說明與6×30＋1檔名查核，十二篇JSON題目／章節分工比對；十二題已選且排除，未匯入。#407僅marketing/agent-office/openbot/SETUP_ZH_TW.md，無editorial重疊。各head與完整清單存audit；test merge SHA不是完成合併。

手機篇將抵達總覽中的通訊提示深入為日本服務／裝置／契約決策，不重寫抵達日程或日本生活總預算。條件句聚焦條件—結果語氣及時間，時態篇是事件參照／完成、僅一題once未來時間；詞性、連接結構、語態、關係子句、比較句也各有分工。兩個獨立搜尋問題屬候選6／20，編輯判斷，無Search Console／搜尋量／排名／流量證據。10/30study-plan `97de3fda`未重做，無三品牌實測不造比較。

原63篇JSON位元、URL、published／modified不變，本分支63＋2＝65，不含十二篇待審。兩篇具直接回答、三點摘要、H1/H2／目錄、表格／清單、原創五步HTML圖解、文中攝影、六題FAQ、官方來源與2026適用範圍、相關文及母校／目的地／工具連結。沿用canonical、Article／Breadcrumb JSON-LD、社群、Sitemap、原生FAQ與手機橫捲表；renderer／CSS／JS未改。

## 來源與教材核對

十二個引用官方／一手頁均實際讀取，最終HTTP200，記錄請求／實際網址、標題、原始大小與SHA256、版本、引用範圍及限制。Apple三頁工作區初始預設User-Agent回429，但官網閱讀工具可讀正文；改一般瀏覽器User-Agent逐頁重新下載200，版本日期一致。初始429HTML／meta與閱讀器文字快照保留taskcache，不冒稱官方存檔，也不把失敗下載說成成功。沒有無法查證主張保留。

東京大學電話頁只引簽約先核對方案與純數據一般無電話／緊急電話功能；未推定所有銀行、宿舍或學校要求日本門號。離日前清單只引手機結約及最後帳單所需付款安排，不引用居留、稅務、保險、證件、關戶期限或個案結果。未打緊急電話、登入、寄送或測試私人帳號。

Apple旅行／雙SIM頁Published Date皆2026-10-22，移除eSIM頁2026-09-17；核對型號／地區／電信條件、鎖機檢查路徑、原門號可能漫遊費、標籤／預設號碼／數據線路分工，以及刪eSIM與向電信商取消服務分開。未把iPhone菜單套Android，未列所有型號／國家、iOS26自動切換保證或實測相容性，未保證任一data-only方案有語音／SMS。SoftBank公開頁只作純數據無語音的例子及2025-02-18停止500MB加購公告；殘留舊價表、31日、容量、2018促銷、舊APN畫面、3G頻段、30分鐘、文件／年齡規定不當2026現行推薦或全日本要求。

原創六期假設日圓試算以Decimal驗算：1,800×6＝10,800；3,000＋10,800＝13,800；2,300×6＝13,800；A加過渡1,000與假設結約2,000＝16,800；B加過渡1,000＝14,800；差2,000。全是假設，不是電信報價、平均或優惠；先比較相同期間與必要功能，通話／額外用量／原門號／部分月／退款／匯率等另查加入，不視為免費。六計費月不等同180日。功能表、檢查表與未寄送詢問稿自寫，無實際SIM、訊號、費率或學生結果。

多益官方內容與Part5 directions核對TOEIC Listening & Reading、30題與四選一最佳答案，和口說寫作分開。British Council四篇教學正文實讀：zero／first／second、third／mixed、future與hypotheses、Other ways of asking questions。只取一般規則，沒有翻寫原頁人物／咖啡／天氣／花園／登山／東京工作等例句、互動題或留言，頁面等級不是本文讀者或題目校準。

六題答案B／C／B／D／A／C：單數remains的普通未來條件；結果主句will dispatch；目前沒有scanner的had假設；昨天錯過的would have accepted過去結果；明示只有陪同可進入的unless；I wonder後if問是否、可接will。各題逐項排除其他選項，六題24選項全原創，非正式題庫／必考比例／成績預測。unless→if not改寫保留主句否定；had ordered＋would have one now的have是主要動詞，和would have connected yesterday的完成組合分開。was／were無上下文不硬製唯一題，缺背景片段改討論，could／would／might不任意互換。例句、設備、期限與錯答皆假設，不是校務規定或真實考生。

## 圖片、閱讀與套件

Ketut Subiyanto／Pexels4881138（背包旅人查看手機），cottonbro studio／Pexels5124877（筆、筆記本、週計畫與手），main與六個待審攝影紀錄均未用。來源頁ImageObject、作者、原JPEG及完整Pexels License實讀；可網站使用／修改、署名可選，保留不當描繪／背書／原樣轉售／素材再分發／商標限制。圖說明示素材，不是日本合作校、真實交換學生、訊號測試、官方多益題或作答結果。

兩張1536×1024 WebP為117,292／111,178bytes，低於450KB。EXIF方向、RGB、LANCZOSfit中心(0.5,0.5)、quality83／method6；無生成、改色或重繪。alt／尺寸／lazyloading／圖說／作者來源完整。原圖與15張最終驗收圖逐張目視：桌面1440、手機320、兩照片／兩圖解、八個關鍵段落與3:2／2:1裁切；人物／背包／手機、筆記本／計畫／筆／手保留。中英文與長設定路徑、算式、六題角色、unless／if／混合結果可讀；手機表格實際橫捲，頁面無溢出。長區塊截圖暫隱固定頁首／裝飾線免拼接遮字，產品、全頁圖與斷言未改。

| 檢查 | 實際結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 65篇，0 errors |
| 六模組SEO單元／整合／release gate | 193 passed（93.65秒） |
| 三模組桌面／手機E2E | 76 passed（215.9秒） |
| 兩篇×320／390／1440，無JavaScript | 六組通過：目錄／FAQ／圖片及credit／橫捲／相關導航／母校目的地工具／canonical及JSON-LD |
| Wheel重建及checkout外匯入 | 65 JSON／65 WebP、全部59 CSS、481字型目錄檔及閱讀資產，共671唯一檔位元一致；外部載入65篇與兩新slug |

產品檢查各一次完整通過，測前固定2JSON／2WebP／59CSS，最終雜湊一致。本批新venv在checkoutready後frozen同步一次成功，未動共用venv；首個來源保存命令誤用無requests的systempython，連線前退出，改本批venv後成功，與產品檢查跑次分開記錄。Wheel 2,529,792,163bytes存taskcache，比對後移除本批build暫存。為空間只移除自己11/21乾淨且完整推送的checkout：本地／遠端HEAD匹配、未提交空、ignored僅Python／測試快取，未force，保留分支／歷史／PR402（仍OPEN未合併）／已提交證據／來源快取。另移除自己11/25可重建Wheel快取2,529,742,290bytes；其他四個待審checkout、root及共用venv保留。

本地驗收不等於正式上線、Google收錄、排名或真實Core Web Vitals。未合併、部署Windows正式機、寄信、致電／登入私人帳號或提交索引。

- [來源／版本](seo-editorial-sources-2026-11-26.json)、[原創教材／試算](seo-editorial-exercises-2026-11-26.json)、[攝影授權](seo-editorial-photography-2026-11-26.json)
- [原63篇雜湊](seo-editorial-inventory-2026-11-26.json)、[PR查核](seo-editorial-pr-audit-2026-11-26.json)、[Gate](seo-editorial-checks-2026-11-26.json)
- [命令與結果](seo-editorial-tests-2026-11-26.txt)、[套件逐檔](seo-editorial-package-2026-11-26.json)、[瀏覽器與15圖](seo-editorial-browser-2026-11-26.json)
- [桌面](seo-previews-2026-11-26/desktop-1440.jpg)、[手機](seo-previews-2026-11-26/mobile-320.jpg)、[裁切](seo-previews-2026-11-26/photography-crops.jpg)

待審PR：[ #408 ](https://github.com/blizzard-new/abroad/pull/408)，OPEN／非draft／未合併，GitHub確認mergeable。建立時head `0e06416d5101ea9d650f1045ba367ee6da46553b`，30檔包括兩篇JSON、兩張WebP及15張驗收圖。兩個image CI仍in_progress，Supabase Preview skipped，不宣稱遠端全部通過。已呼叫attach_artifact但40秒未回傳，list_artifacts亦10秒未回傳，因此任務附件未確認；PR建立、狀態及內容另外查核成功。此後只回填本段、PR audit與本日選題紀錄，產品與測前固定雜湊一致，未重新產文或發布。
