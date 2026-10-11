# 中斷後第四續作：KTU、明治、5處位置及校區保留優先序

基於 `e25ff02a1ebc69ea126a814d105e88b272539351`，同一 Draft PR11 安全續作。193／214具授權照片（190不同SHA）不變，合作位置181→186，中央母校另計。仍缺21圖、28點；214項名額null／agreement_only、流程pending_review、host提醒封鎖，當期完整核准仍0。原任務第五輪未提交工作未轉移，未假裝取得。

人工參考紀錄116→118，665完成來源、261段閱讀、51原生PDF全文及3份原生＋視覺全文；成功公开未讀候選317→314。新13份原件完整保存在 `sources/ncu/2026-10-11/resume-ktu-meiji-original-responses.json.gz`。原3筆landing其中Meiji兩筆同SHA，逐筆保留，不將重複計成不同內容；314待讀仍是後續公開補查工作，不是外部阻礙。嚴格當期欄位缺口3264→3259，只減5個已核位置，未用歷史內容消除當期限制。

## 官方116名額實際發布狀態

2026-10-11 **14:57 UTC／22:57 Asia/Taipei** 重新HTTP200取得同一[官方交換入口](https://oia.ncu.edu.tw/p/412-1026-1872.php?Lang=zh-tw)及[116公告PDF](https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangenotice.pdf)。入口仍連115歷史名單與116公告，尚無116名額表。不是僅沿用repo說法。[原件與HTTP/SHA](home-original-responses.json.gz)、[入口連結與公告第1／2／6頁原文](home-publication-recheck.json)一併保存。

- 公告第1頁：116學年度（AY2027–2028）第一梯次。
- 第2頁原文：「115 年 10 月 12 日(一) 公告姐妹校名額」；第6頁再引用同日姊妹校交換名額一覽表。
- 第6頁三期間：2027年9月～2028年2月一學期；2027年9月～2028年6月一學年；2028年2月～6月一學期。實際期間依姐妹校校曆。
- 本次查核時臺灣尚未10/12。若持續執行跨過臺灣午夜，須再查同入口實際換表情況，不建立新排程、不提前把214筆升為当期。

## 來源及適用範圍

KTU：2021交換規則4頁、2025/26 factsheet9頁（8頁原生空白，9頁全看且視覺摘錄與原始文字分開）、2026/27校曆、general relocation、舊Word LA皆保留原年。B2／IELTS5.5／舊TOEFL70及母校證明不能取代中央語檢；18–33ECTS及一faculty原則。4初次文件＋條件thesis form，後者原件仍缺。期限、不同來源宿租區間及calendar考期矛盾並列；degree新生TRP不套全部exchange。費用只有非協議／超名額例外，未自行推中央免學費。

明治：AY2027 factsheet4張PNG表及9頁申請指南全文，另health／photo兩份1頁PDF、UG／PG×日／英4份Word主文。春2027期限不是116；秋2027期限仍須中央校別核准。TOEFL2026/1/21前後各school不同門檻原表第5頁分列，未自行換算或通套。11份初次文件包含選語／學制的互斥條件，不說人人交11份。CoE財力2項是申請後仍不等錄取，Spring2027財力、2025所得版本另列。宿舍四租金區間與先付完整5個月、不可拒換、非保證床位、每月15萬日圓、校健保與國保並存；不以一般degree學費推交換收費。4campus包含Kanagawa川崎Ikuta，非全部東京都。

每一欄均有來源ID／完整URL／SHA／頁碼或HTML圖表位置／原文／閱讀日期／原版年與當期缺值理由，見 `reviewed-host-records.json`、`host-web-evidence.json.gz`、`document-conditions.json`。Word只稱主文已讀，不稱整個附件视觉全文。官方文件為查核原件，未假稱具圖片再授權；本批沒有新增照片授權。

## 校區位置及整合者必讀

新增HM Munich **Lothstraße**、Monaco **Le Stella新址**、Minho **Gualtar Braga官方GPS**、東北林業 **Harbin和興路26**、HCMUTE **VoVanNgan1**。後兩項採地址連結的總部P159座標限定詞，不從多個校址任挑P625。原始官方頁／Wikidata聲明、座標推導與canonical來源列保存在 `resume-fourth-location-review.json`、`resume-fourth-location-sourcepack.json.gz`。都是核實代表校區，不能推116交換分配。

**Hiroshima明示needs_review優先於共用verified fallback。** 官方access有Higashi-Hiroshima／Kasumi／Higashi-Senda，現有共用點未對應具名校區。修正只限NCU `campus_location` 及NCU盤點程式：有明示NCU紀錄一律優先，未核紀錄隱去lat/lon；無NCU紀錄才用共用fallback。共用matcher未改。新增2項API測試模擬整合分支較新共用verified點，驗證Hiroshima與Mons保留阻擋不消失。

**Chuo保留第三續作已核Tokyo Bunkyo Korakuen／Kasuga1-13-27**，不可寫成Tama Hachioji或Myogadani，更不是116分配保證。整合者請保留這些NCU逐校核對及待確認狀態，勿以共用fallback覆蓋。

## 驗證與剩餘工作

405項NCU／來源／API／位置／六校記憶體回歸通過。KTU／Meiji各390與1280四browser驗收通過，檢查5／11初次文件、2件CoE階段、費用及租金矛盾、無overflow／JS錯誤。地球另1項通過、10個歷次案例deselected；實際看到中央標記和186定位，選單187含母校。完整命令、截圖SHA及人工視讀範圍見[validation](validation.json)。本批沒有重跑舊8照片／2EIVP browser案例，不與第三批11項相加冒充同次全跑。

未合併、部署、改正式DB、安全設定、Quality、憑證或權限。仍須繼續21張照片／28點及314公開待讀來源；逐校歷史內容與當期未知並存，不能把階段提交視為全任務完成。
