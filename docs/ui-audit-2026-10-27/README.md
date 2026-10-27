# UI/UX audit and search-first redesign, 2026-10-27

Front-end only change (11 files under `src/exchange_info/static`, plus one contract-test assertion). No Python, data,
migration, route or SEO-rendering change. Not deployed. Pull request: `blizzard-new/abroad#149`.

Every number below was measured in headless Chromium (Playwright) against a local copy of the app, at 1440×900 and
390×844, with the saved school 長庚大學 unless noted. "Before" is `main` at `42f0eff3`.

## What was measured

| Check | Before | After |
|---|---|---|
| Desktop layout shift (CLS) on first load | 0.971 | 0 |
| Mobile layout shift (CLS) | 0.0003 | 0 |
| Document-check title contrast (white on photo) | 1.03:1 | 15.9:1 |
| Impeccable low-contrast findings: application center / documents / home | 22 / 1 / 1 | 0 / 0 / 0 |
| "Added to list" notice moves the page title | 48 px | 0 px (fixed toast) |
| Home: search action in the first screen | below the fold (search box at y 2,206 desktop, 3,462 mobile) | button at y 328 desktop, 517 mobile |
| Mobile search: first result card | y 797 | y 653 |
| Mobile map view: map visible in the first screen | 104 px | 360 px |
| Desktop map view: visible map height | 467 px of 600 | 441 px of 600, with a school list beside it |
| Tool pages exposing a level-1 heading | 2 of 9 | 9 of 9 |

## Acceptance results

**Keyboard** (desktop and mobile). Tab order on the home search desk is school, destination, term, language, 找學校,
then the country shortcuts. Each stop shows a visible focus ring and stays in view. Pressing Enter in the destination
box goes to `/?view=list&q=日本#partners` and shows 7 schools. On the search page, starting in the search box, Tab
reaches term, language, the search button and the three sort tabs on desktop; on a phone it reaches the search button,
the three sort tabs, 篩選 and 我的條件. Every stop had a focus ring and was in view.

**Filtering** (desktop and mobile). 77 schools; typing 法國 gives 15; adding the autumn term gives "15 (13 known to
match)" with an applied-filter chip; typing a string with no match shows the empty state with 清除所有條件; the button
restores all 77 (30 shown on desktop, 20 on a phone) and empties the box and the term.

**Forms.** With no school saved the home desk's 找學校 opens the school picker and keeps the typed destination. The
number on the desk and the number on the results page matched in the case tried (5 and 5).

**Reduced motion** (`prefers-reduced-motion: reduce`). Home, search and map have 0 running animations. In normal mode
home keeps 6 looping animations that were already there (switcher ring, mascot, supported-schools marquee). The map's
motion button is disabled. Not observed directly: the camera jumping instead of flying on selection (no test hook in
the page); the existing end-to-end test for exactly that (`test_selection_motion_pauses_without_moving_camera_and_respects_preferences`) passes.

**Dark theme.** Home and search were captured at desktop 1440 before and after (see the images). Contrast in dark mode
was not measured separately; the two dark tokens that changed (`--ink-faint`) were checked by eye only.

## Test comparison with `main`

| Suite | Result on this branch | Same tests on `main` |
|---|---|---|
| Contract / routing / caching / discovery (193 tests) | 4 fail | the same 4 fail |
| End-to-end, 19 files around home, navigation, layout, search, map, picker, SEO, photos | 192 passed, 20 failed, 2 skipped | the same 20 tests fail; where the two runs were compared line by line (responsive audit, picker, navigation, travel theme) the failing line and message match |

Three contract tests failed because of this change at first (a stylesheet version pin, an asset-version pairing and an
exact-markup assertion on the application-center title); they were fixed in the code, and only the title assertion was
loosened (it now allows the `role` and `aria-level` attributes). No test was skipped or disabled.

The failures that were already there on `main`: the home page title expectation (`首頁 | UniWay`), the editorial card
count, the Czech school name spacing, the visually-hidden step notes and the discovery labels flagged by the responsive
audit, the react-aria picker count assertions, back-button clicks blocked by the rail's brand mark (navigation, system
motion and travel-theme tests), two content-admin flows and the NTU photo credit test. Their causes were not
investigated beyond showing they are not caused by this change.

## Not verified

- A real GPU, a physical phone (touch gestures, scroll feel) and screen readers. Only headless Chromium was used.
- Safari and Firefox.
- The backend suite and the roughly 100 end-to-end files outside the 19 above. Nothing in the backend changed.
- First-load weight is unchanged: 250 requests on a cold visit, 159 of them CJK font shards, and `school-images.json`
  at 2.4 MB uncompressed. Repeat visits are served from cache (246 of 250). Splitting it touches card thumbnails and the
  reviewed-photo tests, so it needs its own change.

## Left as it was, on purpose

- Two school controls on home (the top pill and the desk's first field). Tests encode the pill's size and an earlier
  request that it be hard to miss.
- Sort-tab ARIA (a test asserts `aria-selected`).
- The country facet lists only the 8 largest countries (56 of 77 schools). The rest are reachable by typing a country
  name; a "more" control is a follow-up.

## Images

Before and after pairs have the same file name in `before/` and `after/`.

| Screen | Desktop 1440 | Mobile 390 |
|---|---|---|
| Home, school saved | `desktop-1440-home-school-chosen` | `mobile-390-home-school-chosen` |
| Home, no school | `desktop-1440-home-no-school` | `mobile-390-home-no-school` |
| Search | `desktop-1440-search` | `mobile-390-search` |
| Search, no result | `desktop-1440-search-empty` | `mobile-390-search-empty` |
| Map | `desktop-1440-map` | `mobile-390-map` |
| Added-to-list notice | `desktop-1440-toast` | `mobile-390-toast` |
| Document check | `desktop-1440-doc-check` | not captured |
| Dark theme | `desktop-1440-home-dark`, `desktop-1440-search-dark` | not captured in the "before" set |

After only: `desktop-1440-map-list-beside-map`, `mobile-390-search-filter-drawer`, `mobile-390-search-compare-tray`.
