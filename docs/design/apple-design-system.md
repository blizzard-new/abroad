# Exchange Guide Design System

Version 1.0 | iOS 17+ and responsive web | First deployment: Chang Gung University

## Product principles

1. **Answer first.** Show the deadline, eligibility result, required action, or funding limit before supporting text.
2. **Official evidence stays visible.** Every rule, workflow step, document, and deadline keeps its source and checked date.
3. **Progressive disclosure.** Mobile shows summaries first; desktop may expose comparison details in parallel.
4. **Platform-native behavior.** Web follows pointer, keyboard, and responsive conventions. iOS uses SwiftUI, SF Symbols, Dynamic Type, sheets, swipe actions, and native navigation.
5. **Calm, not decorative.** Glass is limited to navigation and elevated overlays. Color communicates action or state, not decoration.

## Semantic color system

Never reference raw colors in components. Components consume the semantic token names below.

| Token | Light | Dark | Use |
|---|---:|---:|---|
| `background.primary` | `#F5F5F7` | `#080A0D` | App canvas |
| `background.secondary` | `#FFFFFF` | `#0F1217` | Main content surface |
| `background.tertiary` | `#EEF0F3` | `#171B22` | Inputs, grouped rows |
| `background.elevated` | `#FFFFFFE8` | `#171B22E8` | Menus, sheets, glass bars |
| `background.selected` | `#E6F4FF` | `#102C3B` | Selected navigation/filter |
| `label.primary` | `#15171A` | `#F5F7FA` | Primary copy |
| `label.secondary` | `#5C6470` | `#A7AFBB` | Supporting copy |
| `label.tertiary` | `#7C8591` | `#747E8B` | Metadata/placeholder |
| `label.quaternary` | `#A7AFB8` | `#505965` | Disabled decorative copy |
| `separator.opaque` | `#D8DCE2` | `#2A3039` | Structural dividers |
| `separator.translucent` | `#1D1D1F1F` | `#FFFFFF1F` | Glass separators |
| `fill.primary` | `#1D1D1F14` | `#FFFFFF18` | Controls and hover |
| `fill.secondary` | `#1D1D1F0A` | `#FFFFFF0D` | Quiet grouping |
| `accent.primary` | `#007AFF` | `#64D2FF` | Primary action and focus |
| `accent.primaryPressed` | `#005FCC` | `#30B8EE` | Pressed action |
| `accent.green` | `#248A3D` | `#30D158` | Verified, eligible |
| `accent.orange` | `#C65D00` | `#FF9F0A` | Deadlines and review |
| `accent.red` | `#D70015` | `#FF453A` | Error and destructive |
| `accent.yellow` | `#A05A00` | `#FFD60A` | Highlighted key fact |
| `accent.indigo` | `#4F46A5` | `#7D7AFF` | Documents/reference |
| `link.primary` | `#0066CC` | `#64D2FF` | External and internal links |
| `focus.ring` | `#007AFF59` | `#64D2FF66` | Keyboard focus |
| `scrim` | `#00000052` | `#000000A3` | Modal backdrop |

Contrast targets: body text and controls meet WCAG 2.2 AA at 4.5:1; large text and non-text controls meet 3:1. Status never relies on color alone: pair color with an icon and label.

## Dynamic typography

Web uses `-apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang TC"`. iOS uses semantic SwiftUI text styles so every role scales with Dynamic Type.

| Role | Web default | iOS style | Weight | Line height | Usage |
|---|---:|---|---:|---:|---|
| `largeTitle` | 40px | `.largeTitle` | 700 | 1.15 | Product/task headline only |
| `title1` | 32px | `.title` | 700 | 1.2 | Primary screen title |
| `title2` | 26px | `.title2` | 700 | 1.25 | Major section |
| `title3` | 21px | `.title3` | 650 | 1.35 | Card/sheet heading |
| `headline` | 17px | `.headline` | 600 | 1.4 | Row title and command |
| `body` | 17px | `.body` | 400 | 1.6 | Main reading text |
| `callout` | 16px | `.callout` | 500 | 1.5 | Compact explanation |
| `subheadline` | 15px | `.subheadline` | 500 | 1.45 | Metadata and labels |
| `footnote` | 13px | `.footnote` | 500 | 1.4 | Source and checked date |
| `caption1` | 12px | `.caption` | 600 | 1.35 | Badge and field label |
| `caption2` | 11px | `.caption2` | 600 | 1.3 | Dense table metadata |

Rules: never scale type from viewport width; allow wrapping; do not truncate eligibility or deadline values that change decisions; support iOS accessibility sizes through AX5 without clipped controls.

## Grid and responsive layout

### Web 12-column grid

| Breakpoint | Container | Columns | Gutter | Outer margin |
|---|---:|---:|---:|---:|
| 1440+ | 1440px max | 12 | 24px | 40px minimum |
| 1024–1439 | Fluid | 12 | 20px | 32px |
| 768–1023 | Fluid | 8 logical / 12 tokens | 16px | 24px |
| 320–767 | Fluid | 4 logical / 12 tokens | 16px | 16px |

Primary content uses columns 1–8; contextual details use columns 9–12. Tables may span all 12. Never nest a 12-column grid inside a card.

### iOS adaptive grid

- iPhone compact: 4 logical columns, each equal to three 12-grid units; 16px side inset.
- iPhone landscape/iPad split: 8 logical columns; 20–24px inset.
- iPad full width: all 12 columns; 24px gutter and maximum readable text width of 680px.
- Respect safe areas and keyboard; bottom actions stay above the home indicator.

### Shared native mobile dock

- Android and iOS compact layouts use the same five-control floating dock: Home, Deadlines, an elongated Search/Schools capsule, Support/Documents, and Profile/Eligibility.
- The four outer controls are circular and icon-only; the center Search control is the sole dock item with visible text. Accessibility labels and selected state remain mandatory for every item.
- Support/Documents may show one compact green update badge. The badge communicates attention, not the total document count.
- Dense secondary content stays out of the first viewport. Use a disclosure for quick context and a separate screen for multi-step tasks, long rules, school details, or source-backed documents.
- Home task entry points use icons plus one short title. Longer outcome text is available to assistive technology and on the destination screen.

## 8px spacing and geometry

| Token | Value | Use |
|---|---:|---|
| `space.0_5` | 4px | Icon-to-label optical correction only |
| `space.1` | 8px | Tight inline gap |
| `space.1_5` | 12px | Row internals |
| `space.2` | 16px | Standard control/card padding |
| `space.3` | 24px | Section inner gap |
| `space.4` | 32px | Section rhythm |
| `space.5` | 40px | Large region separation |
| `space.6` | 48px | Desktop section boundary |
| `space.8` | 64px | Page-level separation |

Geometry: 44px minimum target; 48px standard input; 52px primary button; 10px control radius; 8px card radius; 20px sheet radius; 999px only for pills. Use 1px separators and 0.5px iOS hairlines where supported.

## Elevation and material

- `level0`: canvas, no shadow.
- `level1`: card, `0 1px 2px rgba(0,0,0,.18)` plus semantic border.
- `level2`: hover/popover, `0 10px 30px rgba(0,0,0,.22)`.
- `level3`: modal/sheet, `0 24px 72px rgba(0,0,0,.34)`.
- Liquid Glass appears only on navigation, toolbars, tab bars, sidebars, menus, and important controls. On iOS 26 use native system APIs instead of hard-coding blur values; on iOS 17-25 use standard material as a fallback. Provide an opaque semantic surface when reduced transparency is enabled.

## Motion

- Hover: 160ms ease-out, maximum `translateY(-2px)`.
- Press: 90ms ease-out, scale `0.98`; never move layout.
- Sheet/navigation: native spring, response 0.32, damping 0.86.
- Skeleton shimmer: 1.25s linear; stop when Reduce Motion is enabled.
- Loading longer than 300ms shows progress; asynchronous refresh preserves existing content when possible.

## Native component catalogue

All components below define Normal, Hover, Pressed, Disabled, and accessibility behavior. Hover applies to web, iPad pointer, and macOS Catalyst only; iPhone skips directly from Normal to Pressed.

| # | Component and anatomy | Normal | Hover | Pressed | Disabled | Accessibility |
|---:|---|---|---|---|---|---|
| 1 | **Primary Button**: label + optional leading SF Symbol | Accent fill, high-contrast label, 52px | Brighter fill, level1 shadow | Accent pressed, scale .98 | 35% opacity, no shadow | Button trait; label starts with a verb; 44px min |
| 2 | **Secondary Button**: icon/label + border | Elevated surface, semantic border | `fill.primary` | `fill.secondary`, scale .98 | Quaternary label | Expose action, not visual style |
| 3 | **Tertiary Button**: label only | Link color, transparent | Primary fill | Secondary fill | Quaternary label | Do not use for destructive action |
| 4 | **Icon Button**: SF Symbol in 44px square | Transparent/quiet fill | Primary fill | Accent tint + scale .96 | 30% opacity | Requires localized accessibility label and tooltip on web |
| 5 | **Destructive Button**: icon + verb | Red label or red fill | Stronger red | Darker red | 35% opacity | Confirm irreversible actions; announce consequence |
| 6 | **Link**: text + optional external icon | Link color, no underline | Underline | Lower opacity | Tertiary label | External links announce “opens official website” |
| 7 | **Navigation Bar**: title, context, trailing actions | Glass material, hairline | Actions respond individually | Native button press | N/A | Landmarks; title is current screen heading |
| 8 | **Sidebar Navigation Item**: icon, label, selection indicator | Secondary label | Quiet fill | Pressed fill | Quaternary | `aria-current`/selected trait; keyboard arrow support |
| 9 | **Floating Dock Item**: circle icon or center Search capsule | Elevated glass/material | Pointer tint | Native tab press | Quaternary | Selected trait; icon-only items expose localized labels |
| 10 | **Breadcrumb**: hierarchy links + current label | Tertiary/primary | Link underline | Reduced opacity | Quaternary | Ordered navigation; current item not linked |
| 11 | **Search Field**: search icon, input, clear | Tertiary surface | Stronger border | Focus ring | Lower fill | Native search role; clear button named; supports dictation |
| 12 | **Text Field**: label, input, assist/error | Tertiary surface | Border emphasis | Accent focus ring | 45% opacity | Persistent visible label; errors associated programmatically |
| 13 | **Secure Field**: text field + reveal control | Same as field | Reveal button hover | Reveal button press | 45% opacity | Reveal control announces state; never copy secrets by default |
| 14 | **Text Area**: label, counter, multiline input | Tertiary surface | Border emphasis | Accent focus ring | 45% opacity | No fixed height at Dynamic Type; announce remaining count |
| 15 | **Select/Menu**: value + chevron | Tertiary surface | Primary fill | Menu opens | Quaternary | Native menu semantics; selected option announced |
| 16 | **Filter Chip**: concise label + optional count | Secondary fill | Primary fill | Accent selected/scale .98 | Quaternary | Toggle/button pressed state; never color-only |
| 17 | **Segmented Control**: 2–4 options | Native grouped fill | Segment hover | Selected segment | Whole/segment disabled | Radiogroup semantics; labels under 12 characters |
| 18 | **Toggle**: label + system switch | Native state | Pointer halo | Native thumb motion | Dimmed | Switch role, current state announced; 44px row target |
| 19 | **Checkbox**: square + label | Empty/checked | Quiet fill | Accent flash | Quaternary | Checkbox role, mixed state supported |
| 20 | **Radio Row**: circle + label + detail | Unselected/selected | Quiet fill | Accent flash | Quaternary | Radio group with one selected value |
| 21 | **Stepper**: minus, value, plus | Elevated controls | Button hover | Native press | Limit action disabled | Value and min/max announced; direct text entry optional |
| 22 | **Slider**: track, thumb, min/max | Accent progress | Thumb halo | Dragging thumb | Quaternary | Adjustable trait; keyboard arrows; value label |
| 23 | **Date Picker**: field + calendar sheet | Form surface | Border emphasis | Opens native picker | Quaternary | Locale/calendar aware; deadline timezone visible |
| 24 | **University Row**: country, school, eligibility, chevron | Grouped row | Quiet fill | Pressed surface | N/A | Entire row one target; concise combined label |
| 25 | **University Card**: school, country, key threshold, deadline | Level1 surface | Level2 + -2px | Scale .99 | N/A | Heading order; no duplicate nested links |
| 26 | **Deadline Row**: date block, title, status | Orange when near | Level1 | Row press | Past items remain readable | Exact date in accessible name; urgency also stated in text |
| 27 | **Scholarship Row**: name, amount/eligibility, source | Indigo accent | Level1 | Row press | Closed status visible | Amount read with currency; status announced |
| 28 | **Document Row**: file icon, title, summary, source | Tertiary surface | Level1 | Row press | Unavailable action disabled | File type/size and official-source context announced |
| 29 | **Workflow Step**: number, owner, title, deadline, disclosure | First open on mobile | Summary fill | Toggle disclosure | N/A | Native disclosure; sequence position “step x of y” |
| 30 | **Eligibility Result**: outcome, checks, next action | Green/review surface | N/A | Action responds | N/A | Status live region, does not claim official admission |
| 31 | **Status Pill**: icon + label | Semantic tinted fill | Slight fill | Optional filter press | Quaternary | Text duplicates status meaning; 24px visual, 44px target if interactive |
| 32 | **Badge/Count**: compact number/label | Neutral or semantic fill | N/A | N/A | Quaternary | Hidden when redundant; pluralized accessible label |
| 33 | **Progress Indicator**: determinate/indeterminate | Accent track | N/A | N/A | Tertiary | Progress value announced; indeterminate says what is loading |
| 34 | **Skeleton**: content-shaped placeholders | Tertiary shimmer | N/A | N/A | N/A | `aria-hidden`; parent exposes one loading status |
| 35 | **Inline Banner**: icon, title, message, action | Semantic tint + edge accent | Action hover | Action press | Action disabled only | Alert/status role based on urgency; dismiss named |
| 36 | **Toast/Snackbar**: icon, short status, optional undo | Elevated surface | Pause timeout | Undo press | N/A | Live region; 5s minimum; persistent for errors |
| 37 | **Empty State**: SF Symbol, title, next action | Unframed centered content | Action hover | Action press | N/A | Explains cause and recovery; decorative icon hidden |
| 38 | **Error State**: message, recovery action, source context | Red edge accent | Action hover | Retry press | Retry may show progress | Alert role; preserve entered data |
| 39 | **Sheet**: grabber, title, content, close | Native material | Pointer actions | Drag/close | N/A | Focus trapped on web; VoiceOver starts at title |
| 40 | **Dialog**: title, explanation, actions | Level3 + scrim | Actions respond | Action press | Per action | `aria-modal`; Escape/cancel; return focus to invoker |
| 41 | **Context Menu**: icon, command, shortcut | Elevated material | Row highlight | Command press | Quaternary | Native menu roles; destructive items identified |
| 42 | **Tooltip**: short label | Appears after 500ms | Stays open | N/A | N/A | Supplements, never replaces accessible name |
| 43 | **Table**: sticky header, sortable columns, rows | Hairline grid | Row highlight | Selected row | Disabled action only | Real table semantics; sort state announced |
| 44 | **Pagination/Load More**: progress + command | Secondary button | Level1 | Pressed | Loading/last page disabled | Announces newly loaded count; focus remains stable |
| 45 | **Source Link Group**: official links + checked date | Unframed list | Underline | Reduced opacity | Unavailable source labelled | Domain is visible; external behavior announced |
| 46 | **Student Experience Card**: medium, theme, summary, source | Level1 surface | Level2 | Row press | N/A | Distinguishes personal experience from official rules |
| 47 | **Snapshot Rail**: value + short label + separators | Horizontally scrollable content surface | Pointer scroll | Native horizontal drag | N/A | Each value-label pair is combined; scrolling is intentional |
| 48 | **Information Summary Grid**: up to four label/value/icon cells | 2 x 2 on compact, one row on regular width | Level1 | Read-only unless the whole card navigates | N/A | Each cell is one combined fact; icon is decorative |

### Dense information pattern

- Use the Snapshot Rail only for three to five comparable facts that can be understood without paragraphs, such as country, program, quota, deadline status, post count, or reply count.
- Use the Information Summary Grid for up to four decision-supporting facts. The value is visually stronger than its label, and the icon repeats meaning without replacing text.
- On compact width the grid is always two columns. Long eligibility rules, application instructions, official-source notes, post bodies, comments, and chat messages never enter the grid; they use disclosures or a separate reading view.
- School detail and community post cards share this hierarchy on Android and iOS, while retaining native icons, typography, accessibility behavior, and platform-specific interaction feedback.

## Component state rules

- Disabled state is never the only explanation. Place a short reason adjacent or expose it through accessible help.
- Hover is enhancement only; all information and actions work by touch and keyboard.
- Pressed state begins within 50ms and does not alter surrounding geometry.
- Focus order follows visual reading order. Modal focus is contained and returns to the trigger.
- Loading preserves layout dimensions and prevents duplicate submission without blocking navigation.

## Content and data formatting

- Dates: `2026/09/30` in dense tables; `2026 年 9 月 30 日` in reading views.
- Relative urgency is supplementary: “剩 12 天” never replaces the exact date.
- Academic scores keep the test name and scale together: `IELTS 6.0（單科 5.5）`.
- Money includes currency: `NT$75,000`, `NZ$1,200`.
- Official rules use declarative language; student experiences use attributed, non-authoritative language.
- Every summarized rule includes an official source and last checked timestamp.

## Accessibility acceptance criteria

1. Web keyboard operation covers navigation, filters, table links, disclosures, dialog, theme toggle, and form submission.
2. iOS supports VoiceOver, Dynamic Type through accessibility sizes, Reduce Motion, Increase Contrast, Differentiate Without Color, and Reduce Transparency.
3. Minimum target is 44×44pt/px. Adjacent targets have at least 8px separation.
4. No horizontal scrolling at 320px except intentionally scrollable data tables with an accessible alternative card view.
5. Dark and light themes pass automated contrast checks plus manual review for translucent materials.
6. Text remains readable at 200% web zoom and iOS AX5 without clipping or overlapping.

## Handoff checklist

- Tokens exist in web CSS and SwiftUI with the same semantic names.
- Each visible state has a component example or production usage.
- All icons use Lucide on web and SF Symbols on iOS; icon-only commands have labels.
- API loading, empty, error, stale, and refreshed states are represented.
- Screens are validated at 16:9 desktop, 390×844 iPhone, and light/dark mode.
- Native app production builds use HTTPS; local HTTP is development-only.
