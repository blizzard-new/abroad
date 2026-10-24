# UniWay Android preview — 2026-10-24

The 2.1.3 implementation below was merged in PR #121. The subsequent 2.1.4 UI
redesign and validation are documented in `android-ui-redesign-20261024.md`;
user-facing installation instructions are in `android-2.1.4-release-notes.md`.

Production API: https://app.uniway-tw.com/ (Jerry's Windows host).
Branch: `codex/android-synced-preview`, based on `abroad/main` at
`0a790fc8c0d00ca891b63419b665540dd140a87f`. No university factual review or official-data edits.

## Delivered implementation

- Android 2.1.3 (17), package `tw.uniway.app`, Android API 24+, universal APK
  for arm64-v8a / armeabi-v7a / x86_64. Stable RSA 3072 preview certificate;
  signing passwords and keystore are outside Git. Release refuses debug signing.
- Student journey, schools, application preparation, forum and account navigation;
  restrained glass navigation with reduced-effects/high-contrast fallback.
- Google browser handoff with a 2-minute single-use PKCE-bound code, same account
  repository and separate mobile session; credentials use Android secure storage.
- Account/server/university-scoped cache, optimistic-revision workspace sync,
  offline retry, unrelated-field merge and explicit same-field conflict choices.
- Shared favorites, selection profile, document readiness, selections, budgets
  and saved calendar dates. Existing Web-only fields survive edits.
- Encrypted form drafts use the existing Web draft API. Known non-sensitive scalar
  fields survive offline restart in Android secure storage, incomplete forms can
  be saved, and conflicts use the version actually displayed when editing began.
  Existing vault references are preserved; expired references are removed.
- Android local reminders, permission/test control, notification center;
  responsive 140dp/280dp widget with cached next action, tasks and update date.
  Standalone calendar routes include a header/back button; the next-deadline card
  grows with the text instead of clipping on a narrow screen or larger font.
- Optional FCM FID registration, account-guarded data-only messages, generic
  lock-screen copy, logout unregister, durable Postgres claims/retries and
  internal scheduled dispatch entrypoint. Firebase is not configured yet.
- Foreground release checks with a direct APK-download prompt, manual check,
  six-hour success throttle, fifteen-minute failure backoff and 24-hour snooze.
  Uses public GitHub Android releases, including previews; no account data is sent.
- Native forum uses the existing board/feed/detail/comment APIs, with search,
  cursor pagination, nested replies, anonymous account-linked writing, own-content
  deletion and reporting. Server permissions are honored; account changes clear
  stale feed/detail/composer state and late identity creation cannot restore logout state.

## Evidence

- Flutter unit/widget tests: 96 passed, including 360px five-tab navigation at 1.4x text,
  offline restart, 409 revision races, same-field conflict and account isolation.
- 2.1.3 Android emulator integration passed: real native forum composer and reply
  write to an isolated backend, independent API client reads the same content,
  PackageInfo reads 2.1.3/17, and a simulated future-version dialog passes the exact
  APK URL to the browser launcher callback. No fake future Release was published.
  The initial test's numeric timestamp triggered the existing contact-data guard;
  its fixture title was corrected. Backend validation was preserved.
- Production read-only forum smoke returned 200 for boards/feed; guests see two
  readable public boards and have no posting permission. No production test posts.
- Android system-UI tap acceptance passed: background the real app, tap its local
  notification, assert the calendar page/header, then tap an other-account payload
  and assert no unauthorized page opens. This test initially exposed the calendar's
  embedded-only layout and fixed-height overflow; both were corrected and rerun.
- Android emulator integration: local notification permission, active delivery,
  scheduling, cancellation, widget storage and qualified receiver update passed.
- Android emulator + isolated loopback Python backend: PKCE exchange, restored
  account identity, favorite write/read through REST, Web-client JPY budget and
  document-readiness updates, Web-to-mobile-to-Web form draft edits, preservation
  and secure draft cache deletion on logout passed.
  The fixture uses synthetic data and bypasses Google's external approval page;
  it is not evidence of production Google login or two physical devices.
- Python authentication/workspace/notification tests: 67 distinct tests passed
  across the suite and focused rerun. An existing changes test assumed the inbox
  had only one notification; it now filters content_update before asserting
  ownership and scope, preserving those checks when a catalogue notice exists.
- Flutter analyze: no errors or warnings; four existing interpolation style infos.
- OpenAPI exported and --check passed; uv lock updated and --check passed.
- All 41 SQL migrations parsed, including PL/pgSQL bodies. Docker runtime database
  execution was unavailable locally and remains a deployment check.
- Python dependency audit: no known vulnerabilities found at this run.
- Signed release APK installed and launched on Android API 36.1 emulator.
  apksigner verified APK Signature Scheme v2; minSdk=24, targetSdk=36.
- 2.1.3 release: 80,384,008 bytes; SHA-256
  `810b17124e4788910cf6b4ef46e1a9efe24a081f6e99539ad2c3f03cd50a8f32`.
  Installed the signed 2.1.2 APK and then `adb install -r` of 2.1.3; both succeeded.
  Release 2.1.3 launched and its five-tab forum guest view was visually inspected.
  The signer SHA-256 remains
  `a837f361a4dae7f1892985aeca7fb9fd8e580ac7697e2b98ae044b3d132ba2f2`.

## Outstanding external acceptance

- Production backend deployment is now reported successful by the operator.
  The deployment script pinned commit 5f2a0f181322b30a1c0d1cbd5bc484a10cd313f4;
  the operator reported all smoke checks passed and all five services healthy.
  At 2026-10-24 06:38 UTC independent external checks confirmed HTTPS /health 200,
  /auth/mobile/config 200 with enabled=true and S256, Google provider enabled,
  and invalid mobile exchange codes rejected with 401. See
  android-production-deployment-20261024.json for the external receipt.
- Real Google login and production multi-device sync still need physical-phone
  acceptance. Firebase remains unconfigured; remote delivery is not yet verified.
- No physical phone was attached. Notification tap and widget size behavior can
  vary by launcher/device and should be checked on the user's phone.
- Sensitive form fields and newly selected raw attachments remain only in the
  current process. Explicit private-file consent, upload/download, and PDF export
  using existing vault attachments remain in the Web workbench. Native draft saves
  preserve existing vault references and display their filenames; native PDF export
  requires selecting those files again. General scalar answers now synchronize.
- Draft persistence requires pressing Save draft; unsaved typing is not autosaved.
  Selected common-field device memory remains a separate opt-in setting.
- Widget data is a cached snapshot refreshed when the app synchronizes, not a
  background cloud connection. iOS has not been built or tested.

See [Jerry and Firebase setup](android-jerry-setup.md) for installation, deployment,
configuration, manual acceptance and signing backup instructions.

## Release receipt

Public distribution is available at https://github.com/blizzard-new/abroad/releases.
The first published prerelease is android-v2.1.2-preview, targeting the APK source
commit 5f2a0f181322b30a1c0d1cbd5bc484a10cd313f4. Anonymous full-APK download passed
with the expected size and SHA-256 on 2026-10-24. See android-distribution.md for
installation/version-publishing instructions and android-public-download-20261024.json
for the verification receipt. Publishing does not establish physical-phone acceptance.

Final APK SHA-256: `e5daf1e03daea52d0196aa18f51d17d88712a0b1b24d8c856bccf0e45941214f`.
Certificate SHA-256: `a837f361a4dae7f1892985aeca7fb9fd8e580ac7697e2b98ae044b3d132ba2f2`.
Release-to-release `adb install -r` succeeded with this stable certificate.
Release UI loads the existing production school list. Home-screen widget pinning,
signed-out content and tap back to the journey tab were manually verified.
The Pixel emulator launcher was resized from 4x2 to 2x2: the signed-out title
remains fully readable, and tapping the small widget selects the journey tab.
Physical-device launchers and cold-process notification taps remain acceptance checks.
During the final release screenshot check, the Windows QEMU host process crashed
with an access violation. Its cause was not established. Restarting the same AVD
with 2 GB RAM allowed the signed 2.1.2 APK to install, launch and display the full
calendar route correctly; the release screenshot was inspected after recovery.

## Re-running native notification tap acceptance

The opt-in test uses the real app, a loopback fixture backend, and Android's own
notification shade. It is skipped by default because it requires system-UI input.
It never signs into a production account.

1. Start `tests/fixtures/mobile_preview_server.py` with `PYTHONPATH=src`, using the
   project Python environment. It binds to `127.0.0.1:18765` and synthetic data.
2. Run `adb -s emulator-5554 reverse tcp:18765 tcp:18765`.
3. From an English-path copy of `mobile_flutter`, run:

   ```powershell
   flutter test --no-pub integration_test/notification_tap_test.dart -d emulator-5554 --dart-define=NATIVE_TAP_ACCEPTANCE=true --dart-define=API_BASE_URL=http://127.0.0.1:18765/
   ```

4. Allow notifications. Wait for `SYSTEM_TAP_READY`, put the app in the background,
   open the Android notification shade and tap `UniWay 通知已開啟`.
5. The test asserts the real calendar page and its header are present. At the next
   `SYSTEM_TAP_READY`, tap `UniWay 帳號隔離測試`; it must not open another account's page.
6. Check for `All tests passed!`; marker messages alone are not a successful test.
   Stop the fixture server, remove the reverse mapping, and reinstall the signed
   preview APK afterward. Test builds use a different signing key and synthetic state.

## Goal completion audit

| Requirement | Current evidence | Remaining acceptance |
| --- | --- | --- |
| Installable Android APK | Signed universal APK, API 24+, emulator installation and launch | Install on the user's own phone |
| Same account as desktop | Isolated PKCE/account tests; production mobile endpoints and Google provider enabled after deployment | Real Google sign-in on a physical phone |
| Shared data | REST workspace and encrypted form-draft round trips; offline/conflict/account-isolation tests | Production desktop-to-phone acceptance |
| Notifications | Native permission, display, scheduling, cancellation and actual notification-shade taps | Firebase project/client configuration and backend credentials; real remote delivery |
| Home-screen widget | Native cache updates, launcher pinning, 4x2 to 2x2 resize and return-to-journey tap | User's launcher/device behavior |
| Glass interface | Rendered four-tab app, translucent floating navigation and accessibility fallback | User visual feedback |
| No new university factual audit | No official-data changes in this delivery | None |

Implementation and local acceptance have progressed; the goal is not claimed fully
complete while real-device production login/sync and remote delivery remain
unverified. The user executed deployment through the existing remote desktop;
independent external endpoint checks passed. Firebase has not yet been created.
