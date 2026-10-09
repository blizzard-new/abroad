# 9bf90c8 北海道複核修正：同 SHA 原始證據（未驗收）

測試 SHA `9bf90c8748fd33747c625e1f5154f6838540d64a`，2026-10-09T00:04:19.801526+00:00 至 2026-10-09T00:34:21.483306+00:00。固定 detached 工作樹起訖乾淨，各階段前再驗 HEAD／工作樹。原始 manifest、JUnit 與所有命令日志保持原樣；後續保存證據 commit 未被此測試涵蓋。關西國際／駒澤／東北三校未提交研究不在此 SHA。

- 中央四 modules：274 passed；共享回歸164 passed／2 skipped；先前失敗的三 modules：65 passed／0 failed／0 skipped。
- 原56項手機／桌面browser：**52 passed／4 failed**。北海道院級／校級390與1440全部通過，原圖A／S／I中的I為Internship program；JLCSP禁修與其他program分流顯示。
- 四個原失敗：太原農林原文展開5秒仍為placeholder、復旦搜尋fill等待不可見、臺大保存條件頁及北大新版TOEFL頁goto等待load超30秒。原始错误保留在JUnit／log；根因尚未确认。後续四項诊断重跑另存，不能覆寫本次失敗。
- 92張原56案例輸出截圖於冷測前保存；未完成截圖的失敗不補稱原始已保存。zip另列第三次冷測3張，共95張，逐張SHA見artifact map。
- 三次新Python串行新潟390冷測均exit0，原始5秒斷言未改；HTTP／DOM、ASGI、LongTask與catalog build報告分列。這不是SLA或原ded2ed1失敗的豁免。
- OpenAPI snapshot、JS三檔、lock與diff通過；未改main的CGU154／NTPU409／NTU288共851份workflow同schema逐值multiset差異0。
- 實際GitHub quality [37862788170](https://github.com/blizzard-new/abroad/actions/runs/37862788170) failure／0 jobs；Supabase Preview skipped。根因未取得，CI未通過。沒有改quality.yml、執行Docker／正式migration或將本集合稱完整CI。
- 資料62 partial／214，152項尚可繼續查，0 full116；740筆公開host／home來源、97筆讀取錯誤。Drive459份中19份有同SHA逐頁閱讀紀錄，含原生文字或視覺核對，不全稱原生全文。116校別名額預定10/12公布。
- fresh fetch後main仍f6ad1b8；CCU、TKU SHA與各14條共用交集見shared merge points。尚須獨立整合後重驗，不覆寫別校分支。

沒有merge、deploy、正式DB、credentials變更或學校聯絡。資料、browser與CI門檻仍blocked。

同SHA四項後續診斷重跑：4 passed（119.92秒），未改production或原測試；只有/tmp額外插件記錄HTTP／toggle事件。太原原文API本次約3.70秒、復旦約3.28秒，頁面load本次完成；原四失敗根因仍未證實，不稱已修正或將原56全部改成通過。兩張本次補取的太原／復旦截圖在four-failure-followup獨立zip，不是原始92張。

原始pytest.log與JUnit保留pytest輸出的行尾空白。staged diff的空白檢查只排除此兩個原始失敗輸出檔，其他變更正常check；所有原始日志／JUnit均與/tmp原檔逐字節checksum核對，未裁改錯誤。
