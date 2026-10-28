# Application progress heading, 2026-10-27

Front-end only: `application-workspace.js`, `application-workspace.css`, the two asset versions in `index.html`, and
tests. No Python, data, route, SEO or `app.js` change. Not deployed. Pull request: `blizzard-new/abroad#150`.

Measured in headless Chromium (Playwright) at 1440×900 and 390×844 with the saved school 長庚大學. "Before" is `main` at
`42f0eff3`. "Target chosen" means a verified account whose conditions were filled and a target school was picked through
the page, with nothing scheduled or drafted yet.

## What changed

The heading of 我的申請 used one component for two things: the step the student is looking at and the step they should do
next. A page on step 3 could sit above a card that said step 1.

- The circle on a step says how far it is (done, next, not started). The card says which step is on screen
  ("你在這裡"); the recommended one is flagged "下一步" (flags show from 901px wide; below that the cards are too narrow and the
  next-action card says the same in words).
- The next-action card says "你在第 3 步 · 建議下一步在第 1 步「選校與確認」" when it points to another step and is then a
  secondary button; on its own step it says "第 1 步「選校與確認」· 現在先做這件事" with the primary button.
- Steps show what has really been done, from the same state `planningNextAction()` judges by: conditions / target /
  eligibility comparison (`n / 3`), scheduled preparation tasks (`已排 n 項`), drafts filled and checked (`n / m 份`). The
  heading says `已完成 n / 3 步`. With nothing done there is no figure; the plain hints stay.
- A step that finishes while the student is on the page gets one 360 ms check pop and a live-region announcement. Under
  `prefers-reduced-motion` the movement is dropped and the announcement stays. A step already shown as done on this device
  (per account, school and target) is not celebrated again after a reload: the account and plan arrive in pieces while
  the page loads, and an earlier version of this change celebrated that loading (found by a test, fixed).
- Shorter: the kicker "我的申請 · 共 3 步" is gone, the school name is not repeated under the switcher, and a pointer to
  another step drops its detail line.

## Measured

| Page (heading height, then where the page's own content starts) | Desktop 1440 | Phone 390 |
|---|---|---|
| Step 1, nothing done | 366 → 310 px, content at y 488 → 432 | 531 → 373 px, y 705 → 547 |
| Step 2 (準備與時程), nothing done | 266 → 241 px, y 384 → 359 | 355 → 271 px, y 531 → 447 |
| Step 3 (申請文件), nothing done | 356 → 289 px, y 690 → 623 | 481 → 301 px, y 974 → 794 |
| Step 1, target chosen | 356 → 311 px, y 478 → 433 | 505 → 340 px, y 679 → 514 |
| Step 2, target chosen | 266 → 241 px, y 384 → 359 | 355 → 310 px, y 531 → 486 |
| Step 3, target chosen | 356 → 311 px, y 690 → 645 | 505 → 340 px, y 997 → 833 |
| Calendar page after a login, where the month starts | y 685 → 679 | y 965 → 961 |

No page scrolls sideways in any of these. Text contrast of every new or changed string was measured on real pixels
(glyphs hidden, the worst background pixel against the text colour): at least 4.5:1 in light and dark theme at both
widths (lowest 4.78:1, the plain step hint). Tab order in the heading is the same as on `main` (three steps, the next-
action button, 本階段其他頁面, then the page); every stop has a focus ring and stays in view, and the tool menu keeps its
44 px touch height.

## Tests

- New in `tests/e2e/test_application_stage_guide.py` (6, with the 4 existing: 10 pass): where you are apart from what is
  next; no figure for an account with nothing done; figures match what has really been done and the count equals the
  number of steps marked done; a finished step is announced once and stays quiet after a reload; no movement under
  reduced motion.
- Contract / routing / caching / discovery: 189 passed, 4 failed; the same 4 fail on `main`.
- Application, planning, glass-theme, writing-guidance e2e files on the final state: 46 passed, 4 failed. The 4 failures
  (`test_calendar_appears_first_and_tools_still_work`, `test_each_long_field_shows_a_live_count_and_opens_plain_language_guidance`,
  two sizes each) also fail on `main`, at the same assertion; the calendar one fails by a smaller margin here than on `main`
  (month top 960.6 px against 964.6 px on a phone, 678.6 against 685.0 on a desktop).

- Responsive layout audit (`test_responsive_layout.py`): fails at the same 5 sizes as on `main`, and on the final state it
  reports exactly the same 28 problems as `main` (compared line by line, none only here). Comparing them found one that
  was this change's: at 768 px the step flag left a plain hint 58 px wide; flags are now hidden below 900 px.
- Motion, platform redesign, planning, multi-plan, application periods, student journey and workload journey e2e files:
  64 passed, 1 failed (`test_all_routes_share_motion_and_back_retains_working_history`, which fails on `main` the same
  way: the rail's brand mark blocks the back button).

## Found on the way, not changed

In dark theme the page header of 申請文件 shows a pale-grey title on a light gradient and is nearly unreadable; it does
the same on `main`. Filed as a separate task. See the dark images.

## Not verified

A real GPU or phone, a screen reader, Safari and Firefox; the roughly 100 e2e files outside the ones named above.
Nothing in the backend changed.

## Images

Same file name in `before/` and `after/`.

| Screen | Desktop 1440 | Phone 390 |
|---|---|---|
| Step 1, nothing done | `desktop-1440-step-1-nothing-done` | `mobile-390-step-1-nothing-done` |
| Step 3, nothing done | `desktop-1440-step-3-nothing-done` | `mobile-390-step-3-nothing-done` |
| Step 3, target chosen | `desktop-1440-step-3-after-target-chosen` | `mobile-390-step-3-after-target-chosen` |
| Step 2, target chosen | `desktop-1440-step-2-after-target-chosen` | `mobile-390-step-2-after-target-chosen` |
| Step 3, target chosen, dark | `desktop-1440-step-3-after-target-chosen-dark` | `mobile-390-step-3-after-target-chosen-dark` |
