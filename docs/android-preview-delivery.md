# UniWay Android preview — 2026-10-24

Production API: https://app.uniway-tw.com/ (Jerry's Windows host).
Branch: `codex/android-synced-preview`, based on `abroad/main` at
`0a790fc8c0d00ca891b63419b665540dd140a87f`. No university factual review or official-data edits.

## Delivered implementation

- Android 2.1.1 (15), package `tw.uniway.app`, Android API 24+, universal APK
  for arm64-v8a / armeabi-v7a / x86_64. Stable RSA 3072 preview certificate;
  signing passwords and keystore are outside Git. Release refuses debug signing.
- Student journey, schools, application preparation and account navigation;
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
- Optional FCM FID registration, account-guarded data-only messages, generic
  lock-screen copy, logout unregister, durable Postgres claims/retries and
  internal scheduled dispatch entrypoint. Firebase is not configured yet.

## Evidence

- Flutter unit/widget tests: 84 passed, including 360px navigation at 1.4x text,
  offline restart, 409 revision races, same-field conflict and account isolation.
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

## Outstanding external acceptance

- Production /auth/mobile/config returned HTTP 404 on 2026-10-24. Jerry must deploy
  this backend before this APK can sign in and sync with the production account.
- Real Google login, production multi-device sync and Firebase foreground/
  background delivery still need production configuration and user acceptance.
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

Final APK SHA-256: `6ab35d15a686ff59470bb0285285c8dea8254b0b7d57041fce0d252536ff62ac`.
Certificate SHA-256: `a837f361a4dae7f1892985aeca7fb9fd8e580ac7697e2b98ae044b3d132ba2f2`.
Release-to-release `adb install -r` succeeded with this stable certificate.
Release UI loads the existing production school list. Home-screen widget pinning,
signed-out content and tap back to the journey tab were manually verified.
Resizing to the narrow layout remains a physical-device/launcher acceptance item.
