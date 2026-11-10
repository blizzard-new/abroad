# UniWay Web design

UniWay helps students reduce uncertainty, compare exchange options and see the next useful application step. The current refinement follows the owner's **交換平台 UI/UX 優化** principles: reduce information anxiety, establish trust and simplify complex decisions.

## Scope

The owner approved a partial upgrade, based on PR #299:

| Surface | Design |
| --- | --- |
| School search (`#partners`, `#search`) and school details | Refined metro section |
| 我的申請 and its qualification, document, calendar, deadline, budget, scholarship, saved-school, writing and guide tools | Refined metro section |
| Desktop navigation, above 900px | Shared top bar |
| Home, forum, school boards, feedback, profile | Existing live appearance |
| Server-rendered `/guides`, `/schools`, `/partners`, `/privacy`, `/terms` | Existing live appearance |
| Mobile header and drawer on classic pages | Existing live appearance |

`syncSkin()` in `app.js` sets `html[data-skin="metro"]` from the **visible page**, including school detail and fallback routes. Every content rule in `metro.css` must use that attribute. Only the desktop top bar and its existing centering rules are shared. Mobile's primary link is **找學校** within the upgraded sections; it returns to the original **交換指南** link on classic pages.

The full-site metro homepage proposal is archived in Git history at `bff878ea`; it is not the selected production direction. Do not reinstate it or restyle classic pages as part of this refinement.

## Tokens and hierarchy

`metro.css` owns the scoped tokens and maps legacy `--uw-*` / `--glass-*` names only on upgraded pages. Edit the existing definitions rather than appending another stylesheet.

| Role | Light | Dark |
| --- | --- | --- |
| Page / card | `#ffffff` | `#11151c` |
| Subtle surface | `#f3f4f6` | `#1a2029` |
| Primary text | `#1a1d23` | `#eef0f4` |
| Secondary text | `#2b303a` | `#b9c0cc` |
| Divider | `#d6dae1` | `#2f3846` |
| Input boundary | `#8d95a3` | `#5d6879` |
| Primary action | `#165cb4`, white text | `#8bbcff`, `#11151c` text |

Keep the existing region colours on the globe and school marks, plus a restrained 3px navigation band. Region colours must not compete with the primary action or imply eligibility.

- Fonts: self-hosted Poppins for Latin and GenJyuu Gothic for Chinese, with the existing fallbacks.
- Use the available 400, 500 and 700 weights. Page headings are 700, `clamp(28px, 2.5vw, 36px)`, line-height 1.3.
- Each visible top-level page has a level-one heading. Section headings are subordinate.
- Body and editable controls use 16px or larger. Labels use 13px or larger where space allows. Long descriptions use line-height 1.75.
- Upgraded content shares a 1280px maximum width, 24px side gutters, and 16px gutters on phones. Nested tools fill their parent rather than introducing another page margin.
- Use 1px dividers and 12px control corners. Stronger boundaries belong to inputs and focus, not every panel.
- Primary controls are at least 48px high. Keyboard focus remains a visible 3px outline. Native checkbox/radio semantics must be preserved.
- Search has one clear primary action. Labels and controls stay grouped; secondary sorting and view controls are quieter.
- Hide the redundant Back control only on the top-level search and 我的申請 screens. School detail and nested tools retain a return route.

## Trust and states

A matching preference, a checked source or an available guide is **not** a passed qualification requirement. Never derive a qualification fraction from `match.reasons.length`.

School details distinguish:

| State | Display |
| --- | --- |
| No student conditions | Neutral invitation to fill conditions; browsing remains available |
| Known conditions match | 已知條件初步相符, with the school's final decision boundary |
| Missing or uncertain information | 資格待確認, with a specific missing fact |
| Known mismatch | 目前條件不符, with the mismatch reason |
| Availability blocks applying | The catalogue's actual availability label and reason |

Availability takes precedence over matching. Preserve the catalogue wording: a zero quota, an expired round and reference-only data are different facts. The UI continues to use the existing matching and availability functions; it does not replace the policy engine or establish official admission eligibility.

Do not invent ratings, deadlines, admission outcomes or confirmation of unpublished requirements. Personal preparation progress is not school acceptance. Keep official-source links and uncertainty explanations visible.

## Verification

Check desktop and mobile, light and dark, signed out and a synthetic signed-in account. Exercise school search, details, saved schools, 我的申請, tasks and history navigation. Confirm classic content keeps its own skin after returning from an upgraded page.

Browser tests await `appReady`, the real bootstrap promise, instead of global network idleness. Campus images, maps and periodic requests can continue after the application is usable. A boot rejection remains a test failure.

Keep the existing static-asset version checks: any changed versioned CSS or JavaScript needs a new `?v=` and an updated `tests/static_asset_versions.json`.

The repository still loads legacy stylesheets for classic pages. This scoped refinement does not claim to have removed that legacy dependency.
