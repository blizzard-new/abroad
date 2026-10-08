# 中正與他校分支衝突／驗收矩陣（2026-10-08）

77dfd84本地选定gate已完成：452回归passed／7skip，102浏览器passed。完整原始证据与精确tested_program_sha见 [验收矩阵](ccu-validation-2026-10-08/77dfd84-final/README.md)；本文件后续证据修订不继承测试SHA。远端最新heads与本矩阵一致，NTU2/NCU13/TKU9共享重叠；仍未合并。


最新只讀遠端／fetch核對：main `f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59`。只在中正獨立clone與分支工作，没有合併其他分支或修改他校目錄。機器記錄見 [逐檔hash與hunk](ccu-integration-risk-2026-10-08.json)。

|分支|最新SHA|共享重疊|合併驗收狀態|
|---|---|---:|---|
|origin/codex/add-ntu-third-university|`daad399fd3cadf2ba9414fd85d0d3b76154bbbf6`|0|已在main基準|
|origin/codex/ntu-photos-globe-life|`b8833a6a6ffc8236276fa7870e4c1ff541c34117`|2|未合併／未執行跨分支隔離驗收|
|origin/data/ncu-exchange-20261008|`eb0b610604499da9ca29884830fa0c85522aab33`|13|未合併／未執行跨分支隔離驗收|
|origin/data/tku-exchange-20261008|`89217e19d55f3ff615964594e5f83eeb6156ba85`|9|未合併／未執行跨分支隔離驗收|

中正17個共用路徑＝14 code＋pyproject/OpenAPI/uv.lock。新修正仍在既有api.py/app.js/index.html，没有增加CI共用修改。API以各母校自己的guide计coverage，并禁止显式home回传他校guide；正式校名须先由registry解析，保持NTU等别名相容。App加入school epoch、各loader request ID、固定target/workflow/life context；排队草稿保留原home与account，旧response不解除新loading或覆写新目标。不能用整份app/API/model覆蓋他校成果。

NCU最新eb0b610增加Niigata/OMU条件文件与source scope，以及app.js/workflow_structuring.py；TKU最新89217e1增加学制、文件/PDF字体、models/application_documents/pyproject/OpenAPI与切换adapter。统一整合须逐hunk处理school dispatch、附条件文件schema、qualification、内容hash、script版本和请求context helper，重新export OpenAPI。

|验收项目|本中正候选／已观察结果|统一合并后要求|
|---|---|---|
|基底官方资料|46份main原档／77CGU published hash未变；956先前CCU raw来源＋131 host附件byte不变|对固定main与各分支来源重测|
|NTPU guide覆盖率|真实0/206误计已修；回归测试不再失败|确认六校API/UI均使用正确母校profile|
|延迟与草稿|53e88e7的102浏览器全通過，含8个390/1440延迟／排队保存case|在合并后的同SHA重跑，不能继承单分支结论|
|home别名|53e88e7唯一回归失败为NTU alias；本轮已补修与8个四校别名测试，77dfd84完整gate已通过，原53失敗保留|保留Latin/中文alias并禁止跨校fallback|
|远端CI|53e88e7 failure/0jobs；job.env中runner context非法，唯读诊断与副本patch可审查|统一套用CI修正后实际跑；0jobs不可记为通过|
|外部模板|Jena DOC浏览器TLS失败；正常TLS HTTP200且保存hash相同，无绕过|实际外部浏览器成功或保留阻礙|
|资料完整度|935海外欄306当期/331待核/206缺/20参考/71冲突/1明示未公告；0完整17栏与0完整host文件集合|继续逐校正文和新版查核，不能宣称资料已完成|

[逐校正文清册](ccu-body-review-triage-2026-10-08.md)、[CI唯读诊断](ccu-validation-2026-10-08/ci-readonly/README.md)、[53e88e7失败原始证据](ccu-validation-2026-10-08/53e88e7-failed/README.md)均保留。新候选完整结果会另建证据目录，以tested_program_sha关联，后续证据commit不继承测试SHA。未执行他校隔离合并、全部其余repo测试、Supabase parse/runtime、依赖漏洞审计或部署。
