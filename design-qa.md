# Design QA: platform redesign (home, explore, school detail, guide, tracker, forum, profile)

## Comparison target

- Source visual truth: `design_handoff_uniway_redesign/designs/` from the 2026-10-15 request: `Home 1a Product Story`, `Explore Schools`, `School Detail`, `Application Guide`, `Application Tracker`, `Stories Forum` and `Profile Center`, rendered in a browser from their `.dc.html` files (React and Babel served locally), plus the handoff README.
- Implementation screenshots: `docs/platform-redesign-2026-10-15/<screen>-<theme>-<width>.webp`, full-page captures of the running app with a signed-in test account where the page needs one.
- Viewports and normalization: the design renders were taken at 1440 and 390 CSS px; the app was captured at 1440, 834 and 393 in light and dark. The designs do not draw an 834 layout, so 834 was checked for overflow and layout sanity only, not against a source image.
- State: Chinese UI, 長庚大學 as the home school, real catalogue data from the local dev server.

## Full-view comparison evidence

Each screen was compared against its design render side by side. Composition, section order, card structure, sort tabs, facet panel, docs three-column layout, tracker list/board/timeline views, masonry forum and settings rows follow the designs. Colours come from the existing glass-theme tokens, so dark mode needs no second palette; only the values the designs fix in both themes are written in `platform-redesign.css`.

## Focused region comparison evidence

Regions inspected at original resolution: the home hero collage and map card, a school card's photo/badge/heart/compare overlay, the detail booking card and facts strip, the guide table of contents with the plan link, the tracker stats strip and ring buttons, the forum header with its mode switch, and the profile switch, chip and theme-card rows.

## Required fidelity surfaces

- Fonts and typography: the existing Poppins / Noto Sans TC stack; heading sizes follow the designs' clamp() values.
- Spacing and layout rhythm: container queries (`cqi`) on each page root so layouts follow the page width, not the viewport; tablet and phone stack the home collage below 1180px.
- Colours and tokens: new tokens in `glass-theme.css` for both themes; pages that the designs draw flat (guide, tracker, profile) drop the gradient canvas.
- Image quality and asset fidelity: school photos reuse the existing reviewed images and credit lines. The home map is a static SVG outline derived from the Natural Earth data already in the repo; no new raster art.
- Copy and content: design copy is used except where the data cannot back it (see Findings).

## Findings

- No P0 or P1 visual mismatch is known for the seven screens at 1440 and 393.
- Deviations chosen on purpose, because the data does not exist: no monthly-cost or teaching-language facts (omitted, not invented); star ratings only when a post carries a 1–5 `rating`; the profile 語言 row is a disabled select because only Traditional Chinese exists.
- Behaviour changes: `#guide` is now the docs-style guide instead of redirecting to `#home`; `#profile` is a page and the old modal dialog is removed on every width; theme preference gains `system`.
- Not verified against a design: the 834 px layouts.
- Full end-to-end run on the final commit (`6a97d753`): 543 passed, 284 failed, 2 skipped. 278 of the failures also fail on `main` without this change, and they stop at the same test line on the same element on both sides (NCU school data and phone navigation-drawer cases). The other 6 failed only under load: they pass on `main` and pass alone on this branch.
- Still not verified: anything those 278 tests would do after the line where they stop, on either side.
- Non-end-to-end suite on the final commit: 2595 passed, 9 failed, and all 9 also fail on `main`.

## Open questions

- None that block review. The README says the profile dialog "can remain on mobile"; it was removed everywhere because one form cannot live in two places.

## Comparison history

- Home hero overflowed near 1100 px: the collage now stacks below 1180 px.
- Mobile home collage created an implicit second column: its cards are pinned to column 1.
- Explore facet panel was squashed by legacy list-mode rules: raised specificity under `#partners.pr-explore`.
- Detail photo credit stretched and the facts strip showed a grey empty cell: both fixed.
- Guide, tracker and profile kept the gradient canvas in dark mode: flat-background rule now matches the dark selector.
- Tracker ring buttons rendered as ovals and the workspace overflowed 85 px on phones: size reset, and the rail offset now applies only above 900 px.
- The forum hub appeared under every other page: its display rule no longer overrides the rules that hide it.
- Profile switch rows stacked their controls under the label: specificity fix.

## Primary interactions and runtime checks

- Home school buttons choose the school through the same path as the onboarding picker.
- Explore sort tabs, facets, compare tray (max 3) and the phone filter drawer work; tests open the drawer first.
- Profile: account button opens `#profile`; chips add and remove; saving sends the same PATCH fields as before; reload keeps the values; export downloads `/auth/me/export`; sign-out returns home; a signed-out deep link opens the sign-in dialog and lands on home; appearance cards switch light, dark and system, and system follows the device.
- `tests/e2e/test_platform_redesign.py` covers overflow at three widths in both themes and the flows above; 14 tests passed when last run.

## Implementation checklist

- [x] Home landing, explore, school detail, guide, tracker, forum and profile pages.
- [x] Light and dark themes through shared tokens.
- [x] Existing deep links (`#public-board`, `#board=…`, `#language-school-board`, `#following`) still open the forum.
- [x] Static asset versions bumped together.
- [x] Screenshots stored under `docs/platform-redesign-2026-10-15/`.
- [x] Full end-to-end re-run on the final commit (see Findings for what it does not cover).

## Follow-up polish

- Decide whether the 834 px layouts need a design.
- Optional: a real rating field would let the stars and sort-by-rating appear.

final result: passed with open items (see Findings)

---

# Design QA: reusable full-screen loading animation

## Comparison target

- Source visual truth: the second screenshot in the user's 2026-10-14 request, showing the UniWay suitcase on the blue-to-peach full-screen gradient with `正在載入中…`; the first screenshot in that request identifies the horizontal `正在取得最新整理資料…` banner that must be removed.
- Implementation screenshot: `output/loading-overlay/school-switch.png`.
- Viewport and normalization: source and implementation are both 1730 × 837 px at a 1730 × 837 CSS-pixel viewport and device scale factor 1. No resampling or crop normalization was required.
- State: light theme, school change from 長庚大學 to 國立臺北大學, with the replacement dashboard request intentionally held so the loading state can be inspected at full opacity.

## Full-view comparison evidence

The rendered school-switch state reproduces the selected target's full-screen composition: an opaque cool-blue/neutral/peach background, one centered suitcase mascot, its existing soft floor shadow, and the centered `正在載入中…` label. The former fixed horizontal status surface, spinner icon, border, and underlying interactive page are absent while data is loading. The implementation uses the same existing mascot image, animation layers, gradient tokens, and typography as the initial UniWay loading screen rather than creating a visually similar substitute.

The overlay remains above the complete page and intercepts pointer targeting until all school-switch operations have finished. It then uses the existing short fade-out and exposes the success message on the restored page.

## Focused region comparison evidence

The central mascot/title region was inspected at original resolution. Subject, transparent edges, blue surface shading, handle crop, eye placement, floor shadow, title weight, three animated dots, and center alignment match the existing target component because the runtime state clones that exact component. No additional focused crop was necessary: the rest of the target is deliberately empty gradient canvas, and the full-size capture clearly exposes its color and opacity.

## Required fidelity surfaces

- Fonts and typography: The existing Poppins/Traditional Chinese fallback stack, 19 px title size, 700 weight, line height, letter spacing, and animated ellipsis are reused unchanged.
- Spacing and layout rhythm: The mascot/title group stays centered with the same 18 px mascot bottom margin and 6 px grid gap. It remains within the viewport at desktop, tablet, mobile, and landscape sizes.
- Colors and visual tokens: The source loading gradient and dark-theme counterpart are shared directly. The runtime overlay is fully opaque at rest; only its 180 ms entry and 320 ms exit transitions change opacity.
- Image quality and asset fidelity: The implementation uses the existing 384 × 460 WebP suitcase asset at its authored aspect ratio. No generated image, CSS illustration, inline SVG, or placeholder was introduced.
- Copy and content: Visible copy remains exactly `正在載入中…`. The live region receives the more specific `正在切換至國立臺北大學的資料` label for assistive technology without adding visual text.

## Findings

- No actionable P0, P1, or P2 mismatch remains for the requested loading-state replacement.

## Open questions

- None. The user selected an already-existing application loading component, so its visual definition and motion behavior are unambiguous.

## Comparison history

- Initial capture was taken during the 180 ms entry transition and therefore showed the page beneath the partially opaque overlay. This was capture timing rather than a persistent implementation state; the browser test now waits for opacity 1 before recording evidence.
- Final 1730 × 837 comparison confirms the fully opaque state matches the selected loading screen and contains no horizontal loading banner.

## Primary interactions and runtime checks

- Held the new school's dashboard request and confirmed the overlay appears, blocks the page, keeps the specific accessible loading label, and contains no `.status-message.loading` element.
- Released the request and confirmed the overlay hides, the selected school updates, and the success state remains available.
- Existing browser coverage confirms the shared mascot state in dark mode, reduced-motion mode, 320/390/844/1280 px responsive viewports, slow requests, failed requests, and the 60-second fail-safe.
- Browser runs completed without page errors in the school-switch flow.

## Implementation checklist

- [x] Replace the horizontal loading banner with the existing suitcase loading scene.
- [x] Keep generic information, success, and error notices as non-spinning status messages.
- [x] Hold the overlay until the complete school-switch request group finishes.
- [x] Reuse the exact mascot asset, gradient, title, motion, dark mode, and reduced-motion behavior.
- [x] Preserve specific screen-reader loading context.
- [x] Verify entry, blocking, completion, error-safe boot behavior, and responsive states.

## Follow-up polish

- None required for this scoped change.

final result: passed

---

# Design QA: page-header school switcher

## Comparison target

- Source visual truth: the user's supplied 307 × 93 px crop of the existing school control and 1895 × 331 px desktop page-header screenshot, with the request to remove the control from the left rail and place it immediately to the right of the return button.
- Implementation screenshots: `output/navigation-guide/guide-1440.png`, `output/navigation-guide/guide-834.png`, and `output/navigation-guide/guide-393.png`.
- Viewports and density: 1440 × 900, 834 × 900, and 393 × 900 CSS px at device scale factor 1. Full-page implementation captures are 1440 × 1035, 834 × 1379, and 393 × 1662 px respectively. No density normalization was needed.
- State: light theme, 長庚大學 selected, application-guide home route; the school selector is closed and the route-back control is at its safe home boundary.

## Full-view comparison evidence

The supplied header reference and the browser-rendered captures were reviewed together. The left rail now contains only navigation and utility controls, while the school selector sits directly after the return control in the page header. The implementation preserves the user's existing pale glass visual system instead of introducing a foreign navigation style. At desktop, tablet, and mobile widths, the selector stays above the main page content and does not create horizontal overflow or push the guide cards out of alignment.

## Focused region comparison evidence

The header controls are legible in all three full-resolution captures, so a separate cropped capture was not necessary. The focused check confirmed the requested left-to-right order, a consistent 12 px desktop / 8 px mobile gap, visible graduation-cap and chevron affordances, the explicit “切換就讀學校” action label, and the current “長庚大學” value without clipping. On the 393 px viewport, both return and school controls remain on the same row and the school name remains readable.

## Required fidelity surfaces

- Fonts and typography: Existing UniWay Chinese UI typography, weight hierarchy, line height, and antialiasing are retained. The compact action label and stronger current-school value form a clear two-level hierarchy without truncation in the tested states.
- Spacing and layout rhythm: The selector is immediately to the right of the return button, aligned vertically, and uses the existing page gutter at each responsive breakpoint. Its 54 px touch height and compact mobile sizing preserve rhythm without crowding the header.
- Colors and visual tokens: Existing navy, blue-soft, glass-surface, glass-edge, and shadow tokens are reused. The stronger blue border and icon tile make the control discoverable while remaining consistent with nearby controls.
- Image quality and asset fidelity: No new raster imagery was introduced. The existing UniWay logo, suitcase art, and Lucide graduation-cap/chevron icons remain sharp and unchanged; no placeholder, emoji, CSS drawing, or replacement asset was used.
- Copy and content: “切換就讀學校” directly explains the action, while the live school value continues to be populated by the existing application state. The selector still opens the existing school-selection dialog.

## Findings

- No actionable P0, P1, or P2 visual mismatch remains for the requested relocation and prominence of the school selector.

## Open questions

- None. The requested placement and the existing control content were both explicit in the supplied screenshots.

## Comparison history

- Initial implementation comparison: the selector was removed from the left rail, placed after the return control, and given a visible action label plus stronger border/elevation. Browser captures at 1440, 834, and 393 px showed no actionable P0/P1/P2 issue, so no visual correction iteration was required.

## Primary interactions and runtime checks

- Verified the selector is absent from `#glass-navigation` and present inside `.page-back-bar`.
- Verified selector visibility, left-to-right geometry, school-dialog opening and closing, responsive menu behavior, light/dark theme switching, nested application tools, and no horizontal overflow.
- Browser console and uncaught page errors are asserted empty in the responsive test; the focused browser suite passed 10 tests.

## Implementation checklist

- [x] Remove the school selector from the left navigation rail.
- [x] Place it immediately to the right of the visible return button.
- [x] Add an explicit switching label while preserving the current-school value.
- [x] Preserve keyboard focus, dialog behavior, and existing application state.
- [x] Keep the header usable at desktop, tablet, and mobile widths.

## Follow-up polish

- None required for handoff.

final result: passed

---

# Design QA: overlaying expanded navigation rail

## Comparison target

- Source visual truth: the two screenshots in the user's 2026-10-14 request, showing the UniWay forum with the rail expanded and collapsed. The requested correction is behavioral and spatial: the collapsed rail may reserve its compact footprint, while the 240 px expanded surface should float over the page instead of permanently pushing the page to the right.
- Implementation screenshots: `output/sidebar-overlay/rail-collapsed-animated.png` and `output/sidebar-overlay/rail-overlay-expanded-animated.png`, with reduced-motion variants in the same directory.
- Source pixels: the supplied captures use two slightly different desktop crops. Implementation viewport: 1754 × 956 CSS px, device scale factor 1; full-page captures are 1754 × 1189 px. The comparison was normalized around the shared rail, return control, forum header, search panel, and right-side board cards rather than the differing bottom crop.
- State: light theme, guest session, 長庚大學 forum, compact resting rail and pointer-hover expanded rail.

## Full-view comparison evidence

The corrected resting state places the forum canvas at x = 217 px in the 1754 px viewport instead of reserving the expanded rail's previous x = 288 px gutter. This returns the main forum composition toward the viewport center and recovers horizontal space for the feed and board cards.

On hover, the rail grows from 76 px to 240 px as a fixed surface above the document. Browser geometry confirms the forum canvas remains at the same x-coordinate during the transition; at this viewport the rail overlaps the first 39 px of the page canvas. The title and search surface are therefore allowed to sit beneath the expanded navigation, matching the user's stated preference. Moving the pointer outside the overlay collapses it and restores access without moving or reflowing content.

## Focused region comparison evidence

- Collapsed rail: icons remain centered, the UniWay mark is unobstructed, and the main content begins after the compact navigation footprint rather than the expanded width.
- Expanded rail: the existing 240 px labelled surface, active route, school selector, theme, refresh, and account actions remain intact. The rail's opaque glass surface separates labels from the content it covers.
- Transition: screenshots before and after hover confirm the underlying forum title, cards, search input, and right column do not shift horizontally.

## Required fidelity surfaces

- Fonts and typography: Existing UniWay families, weights, Chinese labels, wrapping, and hierarchy are unchanged. Covered text belongs to the stationary page beneath the temporary overlay and is fully restored after pointer exit.
- Spacing and layout rhythm: Desktop page width now uses `calc(100% - 144px)` with a 112 px compact-rail offset. Wide-screen centering is calculated from that compact footprint, not the expanded 240 px surface. Mobile spacing is unchanged.
- Colors and visual tokens: Existing light/dark glass surfaces, active blue, borders, shadows, and focus tokens remain unchanged; only page geometry changes.
- Image quality and asset fidelity: No image or icon asset changed. The UniWay logo and existing Lucide icons retain their authored size and sharpness.
- Copy and content: No visible copy changed. Full route names remain available on hover and keyboard focus.
- Accessibility and responsiveness: `:focus-within` still expands the rail for keyboard users, reduced-motion removes the width animation, and widths at or below 900 px continue using the existing modal drawer instead of hover behavior.

## Findings

- No actionable P0, P1, or P2 mismatch remains for the requested overlay behavior.

## Open questions

- None. The user explicitly accepted temporary content coverage and rejected a permanently expanded gutter.

## Comparison history

- Previous implementation reserved 288 px for the 240 px expanded rail even while collapsed. This kept content stationary but made the entire page read too far to the right.
- Final implementation reserves only the compact 76 px rail plus spacing, keeps the canvas stationary, and layers the expanded rail above it. Desktop captures and browser geometry confirm the correction.

## Primary interactions and runtime checks

- Verified pointer expansion, pointer exit collapse, keyboard `focus-within` expansion, blur collapse, nested application popover, and click-away closure.
- Verified normal and reduced-motion modes, mobile drawer behavior, responsive guide navigation, light/dark theme switching, and absence of horizontal document overflow.
- Browser coverage: 18 passed. Frontend, notification, and next-phase contract coverage: 101 passed. JavaScript syntax, Python compilation, OpenAPI snapshot, and diff checks also passed.

## Implementation checklist

- [x] Remove the permanent 240 px page reservation.
- [x] Reserve only the compact desktop rail footprint.
- [x] Keep the page fixed while the expanded rail overlays it.
- [x] Preserve hover, keyboard, nested-menu, mobile, and reduced-motion behavior.
- [x] Verify collapsed and expanded screenshots against the supplied forum states.

## Follow-up polish

- None required for this scoped correction.

final result: passed

---

# Design QA: Supabase-style expanding navigation rail

## Comparison target

- Source visual truth: the user's latest two Supabase screenshots, showing the same project page with a 58 px icon-only rail and an approximately 260 px hover-expanded rail.
- Implementation screenshots: `output/expanding-rail/rail-collapsed-animated.png` and `output/expanding-rail/rail-expanded-animated.png`, plus the reduced-motion variants in the same directory.
- Primary viewport and density: 1754 × 956 CSS px at device scale factor 1; full-page captures are 1754 × 1189 px.
- State: light theme, guest session, 長庚大學 guide page. The rail was compared in its resting, pointer-hover, keyboard-focus, and nested application-menu states.

## Full-view comparison evidence

The Supabase reference keeps the page canvas fixed while the left navigation grows over the reserved gutter. The implementation follows that behavior: its resting rail is 76 px wide, its expanded rail is 240 px wide, and the guide content remains anchored at x = 288 px in both states. The compact state shows only the established UniWay and Lucide iconography; hover or keyboard focus reveals the full UniWay brand, route names, school selector, theme, refresh, notification, sync, and account labels without moving the page.

The reference's dark graphite palette was treated as interaction and proportion guidance rather than a replacement visual system. UniWay's existing translucent light/dark surfaces, type, active-state color, radii, and icon family are retained, so the new behavior reads as part of the existing product rather than a copied foreign shell.

## Focused region comparison evidence

- Collapsed state: all text is removed from visual flow with zero-width, hidden labels rather than clipped fragments. Every icon remains centered in the 76 px rail and retains its accessible name.
- Expanded state: route rows, utility actions, account identity, and status copy restore at consistent alignment inside the 240 px surface. Long supporting text is allowed to wrap vertically instead of overflowing horizontally.
- Layout stability: browser geometry confirms that the guide content's x-position does not change between collapsed and expanded states.
- Nested controls: the application selector still opens from the expanded rail and remains usable without collapsing its parent surface.

## Required fidelity surfaces

- Fonts and typography: Existing UniWay families, weights, line height, and Chinese labels are preserved. Labels reveal as complete words and remain optically aligned with their icons.
- Spacing and layout rhythm: 76/240 px rail widths reproduce the compact-to-full relationship in the reference while fitting UniWay's existing 16 px page inset. The page gutter is reserved, eliminating hover-induced content movement.
- Colors and visual tokens: Existing theme tokens remain intact in light and dark modes. Active, hover, danger-dot, muted status, border, and focus colors keep their established semantics.
- Image quality and asset fidelity: No new imagery was required. The existing UniWay logo and Lucide icons remain vector-sharp; no CSS art, replacement SVG, or placeholder asset was introduced.
- Copy and content: Full Chinese route and utility names are now available in the expanded state. The notification label integrates with the existing unread red dot and accessible unread count.
- Responsiveness: At tablet and mobile widths the existing drawer behavior remains in place, so the hover rail does not create an unusable touch-only interaction.

## Findings

- No actionable P0, P1, or P2 visual mismatch remains for the requested expanding-sidebar behavior.

## Open questions

- None. The reference clearly defines the collapsed and expanded behavior; UniWay's established palette and content provide the product-specific styling.

## Comparison history

- Initial implementation review: collapsed and expanded captures matched the reference's interaction hierarchy, but a browser integration check exposed an obsolete tooltip listener. The listener was removed before final capture.
- Final comparison: the rail expands cleanly, labels are complete, content remains stationary, nested menus work, and no clipping or horizontal overflow was observed.

## Primary interactions and runtime checks

- Verified pointer hover expansion and collapse, keyboard `focus-within` expansion, focus-retained open state, reduced-motion behavior, nested application menu, notification label/red-dot integration, and unchanged mobile drawer behavior.
- Verified light/dark theme switching and desktop, tablet, and mobile responsive states with browser error collection enabled.

## Implementation checklist

- [x] Default to a compact icon-only desktop rail.
- [x] Expand the complete rail and reveal full names on pointer hover.
- [x] Provide the same disclosure for keyboard focus.
- [x] Keep the page canvas fixed while the rail expands.
- [x] Preserve the notification indicator, application selector, account controls, and mobile drawer.
- [x] Honor reduced-motion preferences.

## Follow-up polish

- None required for this scoped change.

final result: passed

---

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
