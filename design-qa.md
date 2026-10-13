# Design QA: source notifications and notification management

## Comparison target

- Source visual truth: chat attachments `codex-clipboard-6588886a-1984-4ea8-8b86-f473fa238855.png` (101 × 838 px navigation rail) and `codex-clipboard-7e6e7d2f-237d-4c81-9df5-e7af6b7416e8.png` (1802 × 861 px guide page), plus the user's focused bell-tooltip crop in the follow-up request.
- Implementation screenshots: `output/notification-center/notification-red-dot-1280.png`, `output/notification-center/notification-center-1280.png`, `output/notification-center/notification-center-390.png`, `output/cgu-source-recovery/outage-saved-1440.png`, and `output/cgu-source-recovery/outage-saved-390.png`.
- Viewports and density: 1280 × 900 and 390 × 844 CSS px for the notification flow, plus 1440 × 950 and 390 × 950 CSS px for source-recovery states; device scale factor 1 throughout. Full-page notification captures are 1280 × 1072 and 390 × 1699 px. No density resampling was needed.
- State: light theme, authenticated 長庚大學 account, two unread notifications, notification dialog open; source-recovery captures cover saved-reference, unavailable, and recovered catalogue states. The visual target and rendered captures were reviewed together in the same light-theme guide context.

## Full-view comparison evidence

The source guide screenshot shows the three-line 長庚 catalogue-source message above the hero and the notification entry in the left rail. In the rendered guide and recovery captures, that top-left message is absent, so the hero begins without the extra provenance block and the rest of the supplied page composition remains intact. The authenticated rail retains the same bell location and gains a compact red unread dot without changing the rail width or icon geometry.

The open notification-center captures show the former source title, retrieval time, verification disclaimer, destination link, and official-source link as a first-class notification. At desktop width the dialog remains visually centered and separated from the page by the existing blur treatment. At 390 px it becomes a single-column sheet; its header actions, notification copy, and item actions wrap without overlap or horizontal overflow.

## Focused region comparison evidence

- Rail bell: browser geometry confirms a 10 × 10 px red dot anchored within the existing bell button. The dot carries no duplicate spoken text; the button's accessible label exposes the unread count.
- Notification actions: `全部已讀` and red-semantic `全部刪除` remain 44 px-high controls. Each row provides a Lucide trash icon with a text label and notification-specific accessible name. Mobile captures confirm that the controls remain separate and tappable.
- Source-message destination: browser recovery captures and DOM checks confirm there is no `#catalogue-source-status` banner. Source-unavailable guidance remains in the catalogue list/map, while account-specific source events appear in the notification center.

## Required fidelity surfaces

- Fonts and typography: Existing UI families and optical weights are preserved. Notification title, metadata, body, and actions maintain the established hierarchy and wrap cleanly at 390 px.
- Spacing and layout rhythm: Desktop dialog alignment, 16–17 px item padding, 44 px action targets, separators, and mobile single-column flow remain consistent with the product shell. No viewport overflow was detected.
- Colors and visual tokens: The unread dot and destructive actions use the existing danger red; unread rows retain the existing blue wash, and disabled controls retain the existing muted state.
- Image quality and asset fidelity: The supplied UniWay logo and suitcase artwork remain unchanged. All new functional icons use the existing Lucide set; no image or custom SVG substitute was introduced.
- Copy and content: The source acquisition title, timestamp, and official-verification disclaimer are preserved in the new destination. Action labels match the requested `全部已讀` and `全部刪除`; destructive bulk deletion explicitly warns that it cannot be undone.

## Findings

- No actionable P0, P1, or P2 mismatch remains for the requested notification-center change.

## Open questions

- The supplied visual target does not depict an open notification-center design, so the dialog was evaluated against the existing product design system and the user's explicit functional copy rather than against a new pixel-specific mockup.

## Comparison history

- Initial rendered pass: no P0/P1/P2 issue was found. Desktop and mobile captures showed readable hierarchy, intact source content, correct destructive emphasis, and no clipping, so no visual correction iteration was required.

## Primary interactions and runtime checks

- Verified unread-dot visibility, notification-dialog opening, individual deletion, mark-all-read, bulk-delete confirmation, empty state, source-notification deduplication, deletion persistence, and future-source recovery behavior.
- Verified 1280 px desktop and 390 px mobile widths with no horizontal overflow, and checked page-error collection during catalogue recovery.
- Browser coverage: the focused notification flow and four source-recovery variants passed.

## Implementation checklist

- [x] Remove the catalogue-source banner from the page upper-left.
- [x] Create deduplicated web notifications for meaningful catalogue-source states.
- [x] Show a red dot whenever unread notifications exist.
- [x] Add all-read, delete-all, and per-notification delete controls.
- [x] Prevent deleted generated notifications from reappearing on the next refresh.
- [x] Verify desktop, mobile, empty, unavailable, saved-reference, and recovered states.

## Follow-up polish

- None required for this scoped change.

final result: passed

---

# Design QA: page-level return control

## Comparison target

- Source visual truth: chat attachments `codex-clipboard-6588886a-1984-4ea8-8b86-f473fa238855.png` (101 × 838 px navigation rail) and `codex-clipboard-7e6e7d2f-237d-4c81-9df5-e7af6b7416e8.png` (1802 × 861 px guide page).
- Implementation screenshots: `output/navigation-guide/guide-1440.png`, `output/navigation-guide/guide-834.png`, and `output/navigation-guide/guide-393.png`.
- Primary comparison viewport: 1440 × 900 CSS px, device scale factor 1. The full-page implementation capture is 1440 × 1146 px. Supporting responsive captures use 834 × 900 and 393 × 900 CSS px and produce 834 × 1506 and 393 × 1840 full-page images.
- State: light theme, `#home` guide page, 長庚大學 selected, return control at the initial-history boundary. The source and implementation use the same guide content and navigation state; dynamic source-acquisition timestamps differ and are not part of the requested UI change.
- Density normalization: all implementation captures are 1× CSS-pixel screenshots. The source attachments were assessed at their supplied 1× pixel dimensions; no resampling was needed for the scoped placement comparison.

## Full-view comparison evidence

The two source attachments and the rendered 1440 px implementation were reviewed together. The source shows the return arrow inside the compact left rail while the guide page itself starts with the provenance notice. The implementation removes that control from the rail and places a single return button above the provenance notice, aligned to the guide page's left content edge. The rail, provenance notice, hero, mascot, four stage cards, typography, and background treatment otherwise retain the source composition.

At 834 px and 393 px, the return button remains in document flow under the mobile header and above the provenance notice. It does not overlap the menu, banner, hero, or cards, and there is no horizontal overflow.

## Focused region comparison evidence

The focused region is the upper-left navigation area because that is the only requested visual change. In the source rail, the arrow sits between the school selector and the lower rail actions. In the implementation, that rail position is removed; the button begins on the same x-coordinate as the guide/provenance content (112 px at the 1440 px viewport) and appears above it. Its existing Lucide arrow, label, disabled state, focus outline, and history behavior are preserved. No other focused crop was needed because the request did not alter imagery, card styling, or lower-page layout.

## Required fidelity surfaces

- Fonts and typography: Existing UI font family, weights, line height, and copy wrapping are unchanged. The visible `返回` label uses the existing navigation control typography.
- Spacing and layout rhythm: The control is in its own page header row with 20 px desktop and 14 px mobile top spacing. Its left edge matches the responsive content grid, and it precedes rather than overlays the provenance notice.
- Colors and visual tokens: The button uses the existing glass surface, edge, shadow, navy text, hover, focus, and disabled tokens. No new palette values were introduced.
- Image quality and asset fidelity: The supplied UniWay logo and suitcase mascot remain unchanged, sharp, and correctly scaled. No visible asset was replaced or approximated.
- Copy and content: Existing guide, provenance, and action copy are unchanged. The established `返回` label and route-specific accessible labels remain intact.

## Findings

- No actionable P0, P1, or P2 mismatch remains for the requested placement change.

## Open questions

- None. The requested placement is unambiguous in the supplied screenshots.

## Comparison history

- Initial implementation pass: no P0/P1/P2 issue was found. Browser captures at 1440, 834, and 393 px confirmed the new position and responsive flow, so no visual correction iteration was required.

## Primary interactions and runtime checks

- Verified previous-page return, direct-entry fallback to `#home`, school-detail return with filters and scroll restoration, forward navigation, keyboard focus, menu open/close, and light/dark theme behavior.
- Browser run completed with no JavaScript page errors or console errors in the guide navigation flow.
- Relevant browser suite: 12 passed.

## Implementation checklist

- [x] Remove the return control from the left rail.
- [x] Place the shared route-specific return controls at the page's upper-left edge.
- [x] Align the control with desktop, tablet, and mobile content grids.
- [x] Preserve history, direct-entry, focus, disabled, and route-specific behavior.
- [x] Verify light/dark and responsive layouts.

## Follow-up polish

- None required for this scoped change.

final result: passed

---

# Prior Design QA — UniWay full-page travel journal

Final result: passed

## Scope and visual truth

- Date: 2026-09-27. This revision addresses the user's correction that the entire background must adopt the selected style, beyond isolated illustrations.
- Selected source: C:/Users/User/AppData/Local/Temp/codex-clipboard-fa4c83a7-9c21-4798-ad8f-8c2d51dcbaac.png (1122 × 1402, three-screen concept board, no specified CSS viewport).
- Preview: http://127.0.0.1:8767/#home
- Previous report: output/journey-canvas/before/design-qa.md.
- Web only. Existing APIs, real content, school photos, geographic map, motion behavior and native applications are preserved. The previously removed boarding-pass search form remains absent.
- This is an original implementation of the reference's art direction, not a pixel-exact copy of its illustrated institutions or mock content.

## Evidence and comparison setup

All current screenshots are under output/journey-canvas/.

| Evidence | Requested CSS viewport | Stored capture | State |
| --- | --- | --- | --- |
| home-desktop.png | 1440 × 1000 | 1425 × 990 | Light home, full scene and paper discussion cards |
| search-desktop.png | 1440 × 1000 | 1425 × 990 | Japan map, expanded filters, shared collage margins |
| guide-desktop.png | 1440 × 1000 | 1425 × 990 | Guide stages on taped paper |
| school-desktop.png | 1440 × 1000 | 1425 × 990 | Tohoku University, real campus photography |
| budget-desktop.png | 1440 × 1000 | 1425 × 990 | Existing budget form on the shared paper canvas |
| home-tablet.png | 834 × 1000 | 819 × 982 | Full face, complete heading, unobstructed CTA |
| home-mobile.png | 393 × 852 | 378 × 820 | Dedicated portrait home illustration |
| guide-mobile.png | 393 × 852 | 378 × 820 | Stacked guide cards and portrait collage margins |
| school-mobile.png | 393 × 852 | 378 × 820 | Campus photo, caption and single-column facts |
| school-mobile-dark.png | 393 × 852 | 378 × 820 | Dimmed background and legible dark paper surfaces |
| home-dark.png | 1440 × 1000 | 1425 × 990 | Dark home with separate readable copy surface |

The in-app browser capture surface omits the scrollbar and slightly normalizes output size; desktop DPR is approximately 1. Compare original image proportions and visible detail rather than treating the concept board as a one-to-one pixel target. Temporary viewport overrides are reset after review.

The source, implemented desktop home, guide and tablet were viewed together. A focused full-resolution comparison uses reference-background-detail.png and implemented-background-detail.png (280 × 580 each): passport, camera, postcards, paper texture and the transition into the working UI. Initial iterations are retained as home-desktop-first.png, search-desktop-first.png, guide-desktop-first.png and home-mobile-first.png.

## Findings and fixes

No actionable P0/P1/P2 remains in this background pass.

1. **[P1, fixed] The old application surface concealed the page background.** Made the main app and workspace transparent and added a fixed viewport-wide raster canvas. Shared collage margins remain visible on search, guide, school and budget screens.
2. **[P1, fixed] The home illustration read as an image inside the old interface.** Removed the isolated hero image and card frame. Live HTML copy and the functional CTA now sit over an open paper-and-sky scene extending to the viewport edges.
3. **[P2, fixed] Navigation covered the aircraft.** Positioned the home scene below the inset paper navigation and used a second shared background behind the top strip. The final desktop screenshot shows the airplane and continuous page texture.
4. **[P2, fixed] Tablet cover cropping removed part of the traveler's face.** Changed tablet background sizing and placement. Increased text inset and reduced the tablet heading to 40px so it stays on quiet paper. The final 834px screenshot confirms a complete face and readable heading.
5. **[P2, fixed] Desktop artwork did not fit a narrow screen.** Added dedicated portrait home and shared canvases and explicitly reset the mobile background sizing. Text occupies the quiet upper area; artwork continues below. No document-level horizontal overflow was observed.

## Required fidelity surfaces

- **Typography:** preserved Poppins and GenJyuu Gothic body fonts and the previously verified Iansui display face. Responsive headline sizes are 38px on mobile, 40px on tablet and up to 64px on desktop. Real text remains selectable and accessible.
- **Layout and spacing:** inset paper navigation, open homepage hero, visible collage margins and paper content surfaces form one continuous scene. Search retains its working map/sidebar hierarchy. School content, guides and tools use the same paper treatment. Decorations do not intercept pointer input.
- **Colors and materials:** cream paper, navy ink, blue sky, coral controls and yellow tape follow the selected reference. Cards use a supplied raster paper texture and subtle shadows instead of floating glass panels. Existing contrast-aware button and text tokens remain in use. Dark mode uses dark solid reading surfaces with dimmed artwork; forced colors hides decorative backgrounds.
- **Images and assets:** five generated raster assets provide desktop/portrait page scenes and transparent washi tape. Original PNGs, delivery WebPs, prompts, dimensions and SHA-256 manifest are saved. Pillow was used only for delivery encoding and tape trim/resize. Real campus photographs and the functioning geographic globe remain the factual content sources.
- **Copy and content:** no new explanatory paragraphs, student posts or school facts were added. Existing content, source links, empty states and inference labels are preserved. The deleted ticket/search section was not reintroduced.

## Verification

- **76 passed:** frontend contracts, independent page routing, UI contracts, navigation/guide E2E and system-motion E2E. Report: output/journey-canvas/verification.xml.
- **4 passed:** travel-theme E2E. Report: output/journey-canvas/travel-verification.xml.
- **80 total passed.** Two existing external HTTPS warnings were reported by pytest. No test failed in this revision.
- The last tablet typography/background adjustments were then checked visually in the browser.
- Manual browser review covered home, keyword search, map/list switching, school detail, guide, budget, mobile layouts and light/dark themes. Console error query returned an empty array after these flows. Main app/workspace computed backgrounds are transparent, the old hero image is absent, and shared pages select the correct canvas.
- Scoped git diff --check passed; only the repository's LF/CRLF warning was emitted.
- No backend, database, native app or production deployment changes belong to this revision.

Final result: passed
