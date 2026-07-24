# Design QA

## Visual sources

- Reference: `C:\Users\User\AppData\Local\Temp\codex-clipboard-f0448563-dec9-4a44-9b0d-8251d7c90565.png`
- Desktop implementation: `docs/design/web-life-cards-after.png`
- Desktop community: `docs/design/web-community-after.png`
- Mobile life information: `docs/design/web-life-mobile.png`
- Mobile community: `docs/design/web-community-mobile.png`

## Viewports

- Desktop: 874 x 836
- Mobile: 390 x 844

## Checks

- Source-backed life information is ordered before categories without verified sources.
- Generic phrases such as `來源談到` and `來源提到` are absent from rendered key points.
- Concrete life-information points are displayed as scannable bullets with official/source links retained.
- Posts, public chat, and invite-only private messages are visible as three distinct community modes.
- Desktop and mobile layouts have no horizontal overflow.
- All visible mobile buttons meet the 44 px minimum touch target.
- Button labels do not overflow their containers.
- The 821-960 px layout removes the narrow desktop sidebar so content cards remain readable.

## Fixes applied after comparison

- Replaced vague source descriptions with concrete extracted points.
- Added an explicit pending-summary state for source-backed categories that still need extraction.
- Reordered verified, source-backed cards ahead of incomplete categories.
- Added responsive social controls and mobile stacking.
- Removed the desktop progress sidebar at intermediate widths to prevent compressed cards.

Result: passed

## Flutter Liquid Glass navigation update

### Source and implementation

- Source visual truth: `C:\Users\User\OneDrive\文件\留學\.codex-remote-attachments\019f420a-e102-7482-bc5e-0be0c3e330ae\1caf1516-b1bc-447d-992b-364794e37e31\1-Photo-1.jpg`
- Full implementation screenshot: `mobile_flutter\artifacts\flutter-liquid-glass-selected.png`
- Focused side-by-side comparison: `mobile_flutter\artifacts\liquid-glass-nav-comparison.png`
- Viewport: 1280 x 2856 Android emulator capture
- State: school search tab selected, light mode

### Fidelity checks

- Fonts and typography: the center destination keeps the existing product typeface and weight so it remains consistent with the app; the label fits without clipping.
- Spacing and layout: four circular destinations and one wider center capsule follow the reference proportions, remain inside the safe area, and preserve at least 48 px interaction targets.
- Colors and materials: individual low-opacity white surfaces, 30 px dynamic backdrop blur, a three-stop cool refraction tint, top specular highlights, restrained teal selection glow, and soft external shadows create a clearly visible Liquid Glass treatment.
- Image and icon fidelity: the reference contains standard navigation icons only; the implementation uses the platform Material icon set rather than custom drawings.
- Copy and content: the reference search action is adapted to the product's primary task as `找學校`; the other destinations retain the existing app functions.
- Interaction: all five destinations switch to the correct screen, expose selected semantics, and provide splash, highlight, hover, tooltip, and animated selection feedback.
- Responsive safety: no horizontal overflow, clipped icons, clipped center text, or incoherent overlap was found at the tested phone viewport.

### Comparison history

- First comparison: the original implementation matched the shape but read as opaque frosted white rather than Liquid Glass.
- Fix applied: reduced surface opacity, increased background blur, moved shadows outside the clipped glass, and added refractive highlight and selection layers.
- Post-fix comparison: no P0, P1, or P2 mismatch remains. The wider center capsule is intentional because `找學校` is the app's primary student task and needs a readable 48 px-plus target.
- Remaining P3: physical blur intensity can vary slightly by Android device and GPU.

final result: passed

## Flutter Android and iOS migration

### Implementation evidence

- Home dashboard: `docs/design/flutter-home.png`
- School list: `docs/design/flutter-schools.png`
- School detail: `docs/design/flutter-detail.png`
- Concrete life information: `docs/design/flutter-tabs.png`
- Deadlines: `docs/design/flutter-deadlines.png`
- Root community: `docs/design/flutter-community-root.png`

### Device

- Android emulator: API 36
- Screenshot size: 1080 x 2400
- Override density: 320 dpi

### Checks

- The shared Flutter project contains both `android/` and `ios/` runners.
- FastAPI data loads successfully from the Android emulator.
- Home, school search, school detail, workflow, life, deadline, and community navigation are functional.
- Life cards show concrete key points first and explicitly mark incomplete source summaries.
- Anonymous posts, public chat, invite-only messages, block, and report actions are wired to the existing API.
- Students can copy their anonymous ID and invite a post author directly.
- Visible controls use 44 px or 48 px minimum interaction sizes.
- No visible horizontal overflow, clipped button text, or incoherent content overlap was found.
- `flutter analyze` reports no issues and Flutter model tests pass.
- Android debug APK builds and runs; the release APK passes AOT compilation and APK signature verification.
- The release artifact is a locally signed testing build. Store distribution still requires production signing.

final result: passed

## Flutter photo-led school discovery and app-wide Liquid Glass

### Source and implementation

- Source visual truth: `C:\Users\User\OneDrive\文件\留學\.codex-remote-attachments\019f420a-e102-7482-bc5e-0be0c3e330ae\947b671f-cf3b-4a5c-858c-ab9ec279e715\1-Photo-1.jpg`
- School list implementation: `mobile_flutter\artifacts\flutter-photo-schools-final.png`
- School detail implementation: `mobile_flutter\artifacts\flutter-photo-detail-final.png`
- Focused before/after comparison: `mobile_flutter\artifacts\school-card-before-after-comparison.png`
- Viewport: Android emulator capture at 1280 x 2856; focused comparison normalizes the differing source capture height around the school-card region.
- State: all schools, no favorites, light mode; Lincoln University detail opened for disclosure verification.

### Findings and fixes

- [P1 fixed] School cards were dominated by eligibility and language text. The list now removes that paragraph entirely and retains only country, program, study period, quota, and deadline status.
- [P1 fixed] Schools had no visual identity in the list. Every card now has a stable photo region, dark readability overlay, country badge, bookmark action, and matching photo hero on the detail screen.
- [P2 fixed] New Zealand initially inherited the Sydney destination image. It now uses the neutral student-campus fallback; Australia alone uses the Sydney image.
- [P2 fixed] Cards, inputs, icon buttons, filled buttons, outlined buttons, text buttons, and chips used mixed opaque materials. Shared theme and card components now use translucent surfaces, cool refraction tint, white specular borders, and restrained shadows.

### Fidelity surfaces

- Fonts and typography: school names are limited to two lines over the image; supporting copy is one line and eligibility text is deferred to detail.
- Spacing and layout: cards use a fixed 184 px image region, compact fact row, 14 px list rhythm, and a two-column tablet breakpoint without horizontal overflow.
- Colors and materials: all shared controls use the same light Liquid Glass palette while retaining teal semantic emphasis and readable contrast.
- Images and icons: existing licensed web imagery is reused by destination with per-school crop variation; an optional API `image_url` field is supported for future official school imagery. Material icons identify country, period, quota, deadline, bookmark, and navigation actions.
- Copy and content: the list is intentionally concise; full qualification, language, workflow, life, stories, and community information remains available after opening a school.
- Interaction and accessibility: cards remain tappable, bookmarks have independent 44 px-plus targets, Hero transitions connect list and detail imagery, and selected/filter semantics remain intact.

### Comparison history

- First implementation comparison found the incorrect New Zealand/Sydney association and retained it as a P2 blocker.
- The country mapping and fallback test were corrected, the app was rebuilt, and the final screenshot confirms a neutral fallback for Lincoln University.
- No actionable P0, P1, or P2 issue remains. P3: several schools currently share destination imagery until official image metadata is collected.

final result: passed
