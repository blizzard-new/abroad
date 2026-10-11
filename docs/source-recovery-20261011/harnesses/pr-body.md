長庚公開來源失敗時，原本的快取可能永久保留空名單；六校資料批次同時載入又會超過512MiB。本候選保留帶日期的完整來源快照、逐校照片／座標與原年度狀態，並透過串流驗證、有限快取及共用工作池降低記憶體。

已驗收固定檢查點：`0d3d671ef92344970e4de1797a81b050235eecbd`。固定輸入為main59a20f27、PR8 9927ec1d、NTU第二批b6607a0、CCU cf4d86f、NCU第三批06bfdfa、TKU f4819da；完整SHA及逐hunk決策在[證據報告](https://github.com/blizzard-new/abroad/blob/e368f907506f76614958237cdbf4f275fd9e4da8/docs/source-recovery-20261011/README.md)。保持Draft；沒有merge main、部署、正式DB、Quality、Render設定、branch protection、憑證或付費變更。

- 全套非E2E：2287 passed、12 skipped；重點瀏覽器：91 passed（手機／桌面、六校切換、帳號／條件保存、文件階段、跨校論壇與治理流程）。原始skip理由及全部失敗／重跑均保留。
- 同資料完整162步負載：修正前556.27MiB failed；最終暖啟動454.56MiB、冷啟動458.49MiB，均通過460MiB門檻，最低53.51MiB餘裕。
- 原CGU154／NTPU409／NTU288 workflow位元組及13個父擁有測試函數AST不变。中央214審核／1990來源完整payload等值；中正104及台大288生活索引保留完整資料且防止跨請求污染。
- 真實長庚雙來源HTTP200、77列；source狀態明示非當期核實。NTU217正文／191引用／59歷史正文及TKU13包2576成員已獨立核對。
- Wheel建置與5796套件檔案SHA／zip CRC通過（硬連結暫存；首次ENOSPC失敗也保留）；全部新增来源與照片均被打包。OpenAPI、JS、uv lock及35份migration本地語法通過。

每個固定輸入相對main的migration變更均0。[發布／回滾計畫](https://github.com/blizzard-new/abroad/blob/e368f907506f76614958237cdbf4f275fd9e4da8/docs/source-recovery-20261011/RELEASE-PLAN.md)要求父對話先核對production實際SHA、DB版本與備份，再協調單一已驗收候選更新main；Render會隨main commit自動部署，Actions帳務受阻不能當作DB已同步。沒有把mergeable或任務完成當作上線成功。

資料仍未全校完成：各校missing／pending／reference_only／zero保留。下一增量NTU第三批`ed7479073df36deb8fc0393e86fedb102e1cf2b7`的345正文／12ZIP／268引用已獨立核對，但尚未納入以上檢查點；將在下一固定SHA重新整合驗收。第三批16校無任一生活段落與38校缺獨立接待校生活來源是不同口徑。
