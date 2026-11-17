# UniWay Daylight / Metro Signage — Mobile Design System

## Student goal

Help a Taiwanese university exchange student decide where to apply, verify real
official deadlines, and complete campus application forms in less than half the
previous operating time. Empty or guest states never display invented progress,
fake AI scores, fabricated deadlines, or unverified school photos.

## Canonical alignment (`DESIGN.md` & `PRODUCT.md`)

`mobile_flutter` shares the canonical **UniWay Metro / Transit Concourse Signage**
language with the Web application:

- **De-AI-ified product truth**: No cloud or local LLM endpoints are called from
  mobile. Sparkle/magic-wand icons, fake chat prompts, rewrite screens, and
  circular invented completeness scores are prohibited. Document verification uses
  deterministic `POST /document-check` (`use_ai: false`) for page, word, and
  character counts plus rule-based formatting checks.
- **Availability precedes matching**: Partner schools distinguish `本期開放`
  (`open`) from `合作備查` (`agreement_only`), `名額未定` (`quota_unconfirmed`),
  `暫不開放` (`closed`), and `自費研修` (`visiting_fee_paying`). Non-open schools
  never display positive personal-match badges.
- **Task-first signage copy**: Direct Traditional Chinese operational headings
  (`交換準備總覽`, `下一個重要期限`, `找學校`, `申請文件`) with zero poetic slogans
  or decorative kicker/eyebrow pills above headings.

## Tokens

| Role | Token | Value | Notes |
|---|---|---|---|
| Ground / Surface | `surface` / `background` | `#FFFFFF` | Crisp concourse white |
| Muted Band | `concourse` / `surfaceMuted` | `#F3F4F6` | Fact strips & subtle containers |
| Primary Ink | `ink` | `#1A1D23` | >= 16.8:1 on `#FFFFFF` |
| Body Ink | `bodyInk` | `#2B303A` | >= 13.0:1 on `#FFFFFF` |
| Secondary Ink | `secondaryInk` | `#454C5A` | >= 7.5:1 on `#FFFFFF` and `#F3F4F6` |
| Primary Action | `actionBlue` (`teal` / `blue`) | `#165CB4` | `#FFFFFF` label (> 6.5:1); `#EAF1FB` soft tint |
| Open / Verified | `success` / `successSoft` | `#0C7D56` on `#E7F4EE` | `本期開放` & preliminary condition match |
| Reference Only | `referenceInk` / `referenceSoft` | `#5A3A1D` on `#F5EFE8` | `合作備查` (`#8C5A2E` accent rule) |
| Deadline / Review | `amber` / `amberSoft` | `#9A4B00` on `#FEF5E1` | Countdown & `資格待確認` |
| Urgent / Mismatch | `danger` / `coralSoft` | `#B81C22` on `#FDECEC` | Urgent errors & `目前條件不符` |
| Card Rule | `line` | `#D6DAE1` | `1px solid`, `12px` radius, zero blur/shadow |
| Input Border | `fieldBorder` | `#8D95A3` | `1px` enabled, `2px #165CB4` focused, `#FFFFFF` fill |

- **Metro 5-Line Bar (`MetroLineBar`)**: `3px` decorative bar (`ExcludeSemantics`)
  with segments `#D9262C`, `#F2A81D`, `#1F6FD1`, `#0C7D56`, `#8C5A2E` anchored
  under the top bar in `RootShell` and `StudentPage`.
- **Typography**: Platform CJK fonts without negative CJK letter-spacing;
  `FontFeature.tabularFigures()` on dates, quotas, counts, and percentages.

## Components and time-saving workflows

- **Docked Bottom Navigation Bar**: Opaque `#FFFFFF` bar with `1px solid #D6DAE1`
  top border, `SafeArea(top: false)`, and 5 labeled destinations (`旅程`, `學校`,
  `申請`, `論壇`, `我的`), each `>= 48x48 dp`.
- **71-University Searchable Picker**: Offline-ready registry of all 71 supported
  Taiwanese universities with live name/alias/code search (`台`/`臺` normalized)
  and current selection pinned at top.
- **Guest + Signed-In Conditions Bar**: `StudentPlanProfile` persists locally via
  `SharedPreferences` for guests and syncs via `WorkspaceSync` when signed in,
  powering instant `我的選校條件` badges on `SchoolsScreen`.
- **High-Density Signage Cards & Compare Tray**: Cards surface availability,
  quota, deadline, degree/language scope, personal condition assessment, `加入比較`
  (`2–4` schools side-by-side matrix), and 1-tap `設為目標` bridging directly into
  `ApplicationDocumentsScreen` with Undo.

## Validation boundary

Automated Flutter tests cover `320x800` / `375x812` / `812x375` / `768x1024`
layouts at `2x` text scaling, reduced motion, WCAG contrast >= 4.5:1, 71-school
registry parity, deterministic `/document-check`, guest/signed-in condition
persistence, compare tray, and 1-tap target school bridging.
