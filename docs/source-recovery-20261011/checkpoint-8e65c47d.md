# NTU第三批完整隔離驗收檢查點

固定候選 `8e65c47d1d42bd0d065ff53c8d6572d0be994bf2`，臺大第三批 `ed7479073df36deb8fc0393e86fedb102e1cf2b7`，中央仍第三批06bfdfa，淡江仍第一批f4819dab。後續NCU358a72e7與TKU88bd0053僅完成輸入只讀核對，不包含於此候選。

- 完整非E2E2293 passed／12 skipped，原始結果[stdout](ntu3-full-unit/stdout.log)。
- 重點browser91 passed，[stdout](ntu3-browser/stdout.log)。
- 額外隔離Docker PostgreSQL2 passed，[stdout](ntu3-isolated-postgres-rpc/stdout.log)；補執行全套略過的RPC案例，數字不重複加總。未跑本機AI4項和Phase C7項。
- 冷暖各162步，HWM456.8008／457.5195MiB，460MiB門檻通過；[完整memory結果](ntu3-memory-results.json)。
- [wheel逐檔hash](ntu3-wheel-integrity.json)、OpenAPI／JS／uv lock／35SQL語法／原workflow／13原測試AST通過。
- [NTU345正文12ZIP與TKU2576成員驗證](ntu3-delivery-audit.json)；[NCU全payload等值](ntu3-ncu-streamed-payload-parity.json)；[真實CGU公開擷取](ntu3-live-source-acceptance/result.json)。

臺大仍939欄待讀，16校無任一生活evidence／38缺獨立host生活來源，照片／座標各缺3。資料未全校或當期完整。main、正式DB、部署及保護／帳務設定均未操作。正式runtime完整4容器驗收另行列明，不由單一RPC測試代替。
