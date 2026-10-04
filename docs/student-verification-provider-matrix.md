# 學生身分驗證 Provider Matrix

最後查核：2026-08-21

本文件定義長庚大學與國立臺北大學的在學驗證方式。「有學校帳號」不必然代表「目前在學」；只有校方帳號、校方 claim 或學生證能實際證明的資訊，才能標示為已驗證。

## 產品狀態

| 學校 | 方式 | 目前狀態 | 產品決策 |
| --- | --- | --- | --- |
| 長庚大學 | 學生證正反面 | 可用 | 一次性辨識；不保存原圖、OCR 全文、姓名或學號。 |
| 長庚大學 | Microsoft 365 / Entra | 待校方合作 | 官方說明學生與畢業校友皆可使用 `@cgu.edu.tw`；只驗證 tenant 與網域不足以證明目前在學，需校方提供可驗簽的在學 claim。 |
| 長庚大學 | Google Workspace | 待校方合作 | 官方資料可確認 `@gap.cgu.edu.tw` 服務存在，但未找到能供第三方確認當下在學的 claim。 |
| 長庚大學 | 校方 Email OTP | 僅輔助證明 | 長庚學生畢業後仍可保留帳號，所以收到 OTP 不單獨授予在學權限。 |
| 長庚大學 | 校方 SSO | 待校方合作 | 需校方登記 redirect URI，並提供在學狀態 claim。 |
| 國立臺北大學 | 學生證正反面 | 可用 | 一次性辨識；不保存原圖、OCR 全文、姓名或學號。 |
| 國立臺北大學 | Microsoft 365 / Entra | 程式已預留，平台設定中 | 只接受校方 tenant 正式 redirect 回傳，並要求 `s+學號@ms.ntpu.edu.tw` 格式與網域白名單。未設定 tenant App 前固定停用。 |
| 國立臺北大學 | Google Workspace | 待校方合作 | 學生信箱有明確生命週期，但畢業後仍保留部分 G Suite 服務；`hd` 只能證明組織帳號，不能單獨證明目前在學。 |
| 國立臺北大學 | 校方 Email OTP | 待生命週期與可達性確認 | 預留 `s+學號@gm.ntpu.edu.tw` 與 `s+學號@webmail.ntpu.edu.tw`；正式開放前需與校方確認在學、休學、畢業的信箱狀態。 |
| 國立臺北大學 | 校方 SSO | 待校方合作 | 需校方登記 redirect URI 與在學狀態 claim。 |

## 安全邊界

- 本平台絕對不收集校務系統、Microsoft、Google 或校方 SSO 密碼。
- OAuth / OIDC 必須離開本站前往校方或官方 identity provider，只由後端接收 authorization code。
- start 端點只對已登入帳號開放。`state` 為高強度一次性隨機值，後端只保存 SHA-256 指紋，10 分鐘到期；同一來源 10 分鐘最多 20 次，每類最多保存 2,048 個有效 state。production 的 state、限流與容量共用 Supabase TTL store，來源只保存 HMAC client fingerprint，不保存原始 IP。
- Authorization Code 流程同時使用 PKCE S256；callback 必須與原發起帳號、原登入 session ID／token 指紋、provider 與 redirect URI 完全相符。錯帳號或錯 session 會在呼叫 provider 前拒絕且不消耗 state，讓真正發起者仍可完成；真正發起者進入終止 callback 後會先原子消耗 state，再處理取消、參數格式、provider 錯誤或成功，因此 malformed callback 也不能重播。
- provider 回傳成功後，提交驗證結果前仍會在同一把帳號鎖內重新讀取帳號與原 session；帳號已刪除、session 已撤銷／過期或學生狀態已由其他流程完成時都 fail closed，不會復活帳號或覆寫另一個結果。
- Microsoft 使用固定 tenant authority，不使用 `common`；Google 必須檢查 `email_verified` 與 `hd`，不只比對 Email 文字後綴。
- callback 不保存校方 Email、OIDC `sub`、authorization code、access token 或 provider 原始 claims。帳號只留下已驗證學校、可證明系所、驗證方式、狀態與時間。
- 刪除帳號時，尚未完成的學生證 token 與 OAuth state 會同時失效。
- 這些流程與 AI 無關，不會呼叫任何雲端 AI API。

OAuth state、學生證一次性 token、rate limit、容量、同 session 替換與 consume 已移到共享 TTL store，並以資料庫交易鎖原子處理；兩個 App instance 之間的成功 callback／confirm、wrong identity 不耗用與 replay 都有測試。尚未完成的是 OAuth 成功後的帳號建立／連結，以及「帳號存在、session 有效、尚未驗證、條件式更新」的共享資料庫 transaction／CAS；目前 `auth_lock` 仍是 process-local，因此整體 production 在完成這一層前仍維持單一 Uvicorn worker。

## 臺北大學 Entra 後端設定

只在校方或受權管理者完成 Entra App Registration 後設定：

```powershell
$env:EXCHANGE_NTPU_STUDENT_ENTRA_CLIENT_ID='Entra App client id'
$env:EXCHANGE_NTPU_STUDENT_ENTRA_CLIENT_SECRET='Entra App server-side secret'
$env:EXCHANGE_NTPU_STUDENT_ENTRA_TENANT_ID='Entra tenant id'
$env:EXCHANGE_PUBLIC_BASE_URL='https://your-production-domain.example'
```

正式 redirect URI：

```text
https://your-production-domain.example/auth/student-verification/oauth/ntpu-entra/callback
```

Client secret 只能存在 FastAPI 後端 secrets，不得放入 Web、Flutter、Git 或截圖。未同時設定 client id、secret 與 tenant id 時，API 回傳停用狀態，start 端點以 503 拒絕，不會退回自建密碼表單。

## 官方查核來源

- [長庚大學 Microsoft 365 服務登入說明](https://www.cgu.edu.tw/faq/Contents?nodeId=18826)
- [長庚大學電子郵件信箱使用管理辦法](https://www.cgu.edu.tw/regulation/ServerFile/Get/6731e095-b2f1-4564-b74b-e72deab39cd9)
- [長庚大學 Google Workspace 服務異動說明](https://www.cgu.edu.tw/ic/Subject/Detail/35050?nodeId=11240)
- [國立臺北大學 Microsoft 365 學生帳號使用說明](https://m365.ntpu.edu.tw/en/guide)
- [國立臺北大學 Google Apps for Education 服務使用管理辦法](https://cms-carrier.ntpu.edu.tw/uploads/Google_Apps_for_Education_G_Suite_49d2ee084e.pdf)
- [Microsoft identity platform OIDC endpoints](https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc)
- [Google OpenID Connect `hd` 驗證要求](https://developers.google.com/identity/openid-connect/openid-connect)
- [Google OAuth `state` 安全建議](https://developers.google.com/identity/protocols/oauth2/resources/best-practices)
