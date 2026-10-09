# CCU 複合摘要的逐來源顯示修正

原本describe_field與enrich_documents取evidence[0]，把新API／影像主張的摘要尾註綁到舊factsheet頁碼與2026-10-08。現在摘要逐份列來源的年度、形式、原文位置與實際日期；流程及生活來源連結標示相同內容。UNINTER48筆題目metadata的來源為正常TLS公開題目API、2026-10-09，舊factsheet第5頁保留初次文件清單與2026-10-08。Mapúa精確第三／四季日期指向正常TLS校曆影像與2026-10-09，舊factsheet第2頁只承接2–7月／quarter概述與2026-10-08。

11個API／影像／HTML evidence映射的抽取段落索引清除為無PDF頁碼；source JSON、原始payload、ledger的抽取文字索引、來源方法、hash及時間均未改，實體PDF頁碼保留。原始application_workflows／destination_profiles重建。新增兩項原始產物／實際API回歸與390／1440、UNINTER／Mapúa四個實際UI案例，核對新來源link／日期、舊PDF頁碼／日期及複合摘要，沒有靠改日期掩蓋來源差異。
