# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Taiwanese university students (undergraduate and graduate) preparing an exchange-program application. They arrive with one job: decide which partner school to apply to, know the next document and the next deadline, and ask other students who have been through it. Confirmed by the owner.

Other audiences exist in the codebase (administrators reviewing content, feedback and error reports; the analytics dashboard) but are not primary users and were not part of this brief.

## Product Purpose

UniWay (`src/exchange_info`) collects public exchange-program information from university offices and partner schools, structures it, and turns it into a student's path: choose a school, see eligibility, get a personalised document checklist with progress, track deadlines, and read or post in a student community. Success is a student who knows what to do next and trusts that the information behind it is real.

## Positioning

Only officially verified information is presented. What is not confirmed is labelled as not confirmed ("待確認", "依官方公告"), and the interface never invents progress, deadlines, quotas, or recommendations. A neighbouring product that fills gaps with plausible-looking data could not truthfully make this claim. Confirmed by the owner.

## Operating Context

- Students use it on phones and laptops, in bursts between classes and at deadline time; the application workspace ("我的申請") is revisited over weeks.
- Content is Traditional Chinese (`zh-Hant`) first; school names, programmes, and requirements are Taiwan-specific.
- The product distinguishes "本期開放" (open this cycle) from "合作備查" (partnership on file, no current quota). A cooperation agreement must never read as an open place.
- The application workspace only handles data the student types in and produces a PDF; it does not submit anything for the student.

## Capabilities and Constraints

- Supports 66 universities (`SUPPORTED_UNIVERSITIES` in `src/exchange_info/university_registry.py`).
- Web front end is vanilla HTML/CSS/JS served by FastAPI from `src/exchange_info/static/` (about 100 files; 25+ stacked stylesheets from earlier redesigns such as glass-theme, midnight-theme, product-v2, platform-redesign). A React Aria school picker and a globe are separate bundles built from `frontend/`.
- Main surfaces: home (search desk), explore/search, partner map and globe, school detail, application workspace and document workbench, deadlines and calendar, destination tips, community forum and chat, account/profile, plus admin pages (content review, feedback admin, analytics dashboard, API contract) and legal pages.
- A Flutter iOS/Android app exists in `mobile_flutter/` with its own "UniWay Daylight" design system (`design-system/uniway-daylight/MASTER.md`). The project works Web-first; Flutter is synchronised only after the owner explicitly confirms the Web result. **This redesign is Web only.**
- **Front-end only.** Routes, SEO output, DOM ids and roles, content, data, and behaviour stay as they are. About 130 e2e tests and many contract tests depend on them. (Inferred from the owner's scope choice and the prior UI audit in `design-qa.md`; confirm if a DOM change is ever needed.)
- No cloud AI API is wired in; advisor and AI surfaces must not imply capabilities that do not exist.
- Decision on release readiness is still "NOT READY" per README; verified/unverified states must keep showing honestly.

## Brand Commitments

- The name **UniWay** and the current logo (`src/exchange_info/static/assets/brand/`: `uniway-logo.webp`, `uniway-logo-glow.webp`, `uniway-mark.webp`, favicons, updated 2026-10-04).
- The suitcase mascot and the advisor character (`assets/mascot/`, `advisor-mascot.css`, `mascot.js`).
- Not binding, free to be re-decided by the redesign: the current midnight-blue primary (`#23324a`), glass and midnight themes, the existing type, layout, and component language. (The Flutter app uses teal `#006C67`; the two are currently inconsistent.)

## Evidence on Hand

- Verified structured data and official sources under `data/`, `sources/`, and the `DATA_*` reports; real school imagery with verified metadata (`assets/*-campus.*`, `ncu-school-images.json`). School photos come only from that verified metadata.
- Prior UI audit and before/after captures: `design-qa.md`, `docs/ui-audit-2026-10-27/`, `docs/ui-progress-2026-10-27/`.
- Absent, must not be fabricated: testimonials, user counts, success rates, ratings, quotas not on an official page, student-activity figures, and progress for empty accounts.

## Product Principles

1. **Verified or labelled.** Every fact is either from an official source or visibly marked as unconfirmed; the interface never fills gaps.
2. **Next step first.** A student always sees the one thing to do next and the real date it matters, before anything decorative.
3. **Conditions before catalogue.** Choosing a school starts from the student's conditions (school, destination, term, language), not a browse of 66 universities.
4. **Honest empty states.** An account with nothing done shows zero, not encouragement.
5. **Peers over polish.** Other students' answers are a first-class part of the journey, not a footer link.

## Accessibility & Inclusion

Held to WCAG AA contrast, keyboard operation with visible focus, `prefers-reduced-motion` support, 2× text scaling, and phone-first layouts (verified in the earlier audit; see `design-qa.md`). Human screen-reader and physical-device testing have not been done and must not be claimed. Traditional Chinese typography must stay legible at small sizes.
