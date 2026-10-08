# f41e6ab 既有三個module修正後同SHA檢查

固定實作SHA `f41e6abb7f77283aa942cd6c9b80cd4d2991c735` 的原始manifest／JUnit／完整log：65 passed，0 fail／skip，起訖工作樹乾淨。這只是三module檢查，不等同新的完整候選驗證或CI通過。

NTPU coverage兩處白名單漏列修正，destination狀態與查核時間和實際API同值。AI consent程式未改：測試未同意422、明確同意且runtime paused503，確認外部AI請求0。八個前端斷言按現行community reader／通知逐項變更／文件缺口／版本化asset／系所選擇／驗證按鈕／availability blocker更新，沒有回改舊文案或把功能安全檢查刪掉。

首次工作樹預驗64 pass／1 fail（後續同測試舊filter字串）；修正為按partnerAvailabilityMeta.blocked篩選後65 pass。兩次工作樹結果另標，不能當乾淨SHA結果。fff2760仍保留原55 pass／10 fail，未回改歷史結果。

資料仍62 partial／214、0 full116、152項可續查。完整NCU／shared／56 browser／851 parity集合須在下一資料候選新SHA重跑。沒有merge、deploy、DB或credentials/security程式變更。
