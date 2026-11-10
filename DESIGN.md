---
name: UniWay
description: A metro route map for exchange study. White ground, one ink, five region lines, station-board controls.
colors:
  ground: "#ffffff"
  concourse: "#f3f4f6"
  ink: "#1a1d23"
  ink-2: "#454c5a"
  ink-3: "#6a7282"
  rule: "#d6dae1"
  rule-strong: "#8d95a3"
  board: "#1a1d23"
  on-board: "#ffffff"
  on-board-2: "#c7cdd8"
  line-red: "#d9262c"
  line-orange: "#f2a81d"
  line-blue: "#1f6fd1"
  line-green: "#0c7d56"
  line-brown: "#8c5a2e"
  red-text: "#b81c22"
  blue-text: "#165cb4"
  focus: "#1f6fd1"
typography:
  display:
    fontFamily: "Poppins, GenJyuuGothic, UniWay Sign, Noto Sans TC, PingFang TC, Microsoft JhengHei, system-ui, sans-serif"
    fontSize: "clamp(28px, 4.05cqi, 58px)"
    fontWeight: 900
    lineHeight: 1.12
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Poppins, GenJyuuGothic, UniWay Sign, Noto Sans TC, PingFang TC, Microsoft JhengHei, system-ui, sans-serif"
    fontSize: "clamp(26px, 3cqi, 42px)"
    fontWeight: 900
    lineHeight: 1.18
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Poppins, GenJyuuGothic, UniWay Sign, Noto Sans TC, PingFang TC, Microsoft JhengHei, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 800
    lineHeight: 1.3
    letterSpacing: "0em"
  body:
    fontFamily: "Poppins, GenJyuuGothic, UniWay Sign, Noto Sans TC, PingFang TC, Microsoft JhengHei, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.75
  label:
    fontFamily: "Poppins, GenJyuuGothic, UniWay Sign, Noto Sans TC, PingFang TC, Microsoft JhengHei, system-ui, sans-serif"
    fontSize: "11.5px"
    fontWeight: 700
    letterSpacing: "0.1em"
rounded:
  sm: "8px"
  button: "10px"
  lg: "12px"
  rail: "14px"
  pill: "999px"
  station: "50%"
spacing:
  board-cell-x: "18px"
  board-cell-y: "12px"
  grid-gap: "20px"
  section-gap: "clamp(56px, 7cqi, 104px)"
components:
  board:
    backgroundColor: "{colors.board}"
    textColor: "{colors.on-board}"
    rounded: "0px"
  board-cell:
    textColor: "{colors.on-board}"
    padding: "12px 18px 10px"
    height: "72px"
  board-go:
    backgroundColor: "{colors.line-orange}"
    textColor: "{colors.ink}"
    rounded: "0px"
    padding: "0 28px"
    width: "150px"
  board-go-hover:
    backgroundColor: "#ffc24d"
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.ground}"
    rounded: "{rounded.button}"
  button-primary-hover:
    backgroundColor: "{colors.ink-2}"
  line-tag:
    backgroundColor: "{colors.line-red}"
    textColor: "{colors.ground}"
    rounded: "{rounded.sm}"
    padding: "6px 12px 7px 11px"
  station:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    rounded: "{rounded.station}"
    size: "20px"
  origin-label:
    backgroundColor: "{colors.board}"
    textColor: "{colors.on-board}"
    rounded: "{rounded.sm}"
    padding: "8px 10px 9px"
    width: "150px"
  card-ruled:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
  nav-rail:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    rounded: "{rounded.rail}"
  nav-item-active:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.ground}"
    rounded: "{rounded.button}"
---

# Design System: UniWay

## Overview

**Creative North Star: "The Route Map From Your Own Campus"**

The home is drawn like a Taipei metro diagram. The student's school is the origin station, each region of the world is a coloured line, each partner country is a station, and the state of a station is drawn rather than implied. The system is one white ground, one near-black ink, and five saturated line colours used at full strength. There are no gradients, no glass and no blur. Depth comes from 2px ink outlines, flat fills and rules.

The `--mt-*` custom properties in `src/exchange_info/static/metro.css` are the source of truth. The older stylesheets (glass-theme, midnight-theme, product-v2, platform-redesign) still load and still read `--uw-*` and `--glass-*` names. metro.css loads last and re-points those names to the `--mt-*` values, so legacy pages inherit the world without being rewritten (see Colors, Legacy token remap). A light "day service" and a night variant are selected by `html[data-theme="light" | "dark"]`; the night variant keeps the same roles and brightens the line colours.

Only the home page was designed as a surface. Other routes (search and map, school detail, community, account, the server-rendered reading pages) inherit through tokens plus override blocks in metro.css. They are in the world but not individually composed.

**Key Characteristics:**
- White ground, ink #1a1d23, five region line colours, no gradients, glass or blur.
- Station-board controls: black bars with a 6px line-coloured top rule per cell and one orange action.
- Heavy gothic (weight 700, the heaviest cut of both faces) for every name and heading: Poppins for Latin letters and digits, 源柔黑體 (GenJyuu Gothic) for Chinese, both self-hosted (`typography.css`). Noto Sans TC ("UniWay Sign") is only the fallback for glyphs 源柔黑體 lacks.
- Ruled 2px ink outlines for containers; flat, no resting shadow.
- A five-colour band, 6px tall, fixed at the top of every page.

## Colors

One white ground and one ink, with colour reserved for meaning: the five lines are regions, not decoration.

### Primary
- **Platform Ink** (`ink`, #1a1d23): text, 2px outlines, station rings, the primary button, the active nav item, the board and origin label fill (via `board`).

### Line colours (region meaning)
- **East Asia Red** (`line-red`, #d9262c): East Asia line; the "you are here" origin dot, the current plan step, the reading position in the journey, the text caret. Text-sized red uses `red-text` (#b81c22) for contrast.
- **Southeast and South Asia Orange** (`line-orange`, #f2a81d): Southeast and South Asia line, and also the one primary search action (board "go" button), the "next stop" label, the supported-schools label, and the journey index numeral. Always paired with ink text (`--mt-on-orange` is #1a1d23).
- **Europe Blue** (`line-blue`, #1f6fd1): Europe line; focus ring, links (text-sized links use `blue-text` #165cb4), completed plan steps, the open-this-cycle legend key, the vertical journey line.
- **Americas Green** (`line-green`, #0c7d56): Americas line; the fit-tool chip.
- **Oceania, Africa and West Asia Brown** (`line-brown`, #8c5a2e): the fifth line. As built it also colours the budget tool chip and the `pr-chip-amber` chip, so it is not exclusive to that line (see Don'ts).

### Neutral
- **Ground** (`ground`, #ffffff): page and card fill.
- **Concourse** (`concourse`, #f3f4f6): hover fills, inset footers, map land on the day variant.
- **Ink 2 / Ink 3** (`ink-2` #454c5a, `ink-3` #6a7282): secondary text; `ink-3` only for small labels.
- **Rule / Rule Strong** (`rule` #d6dae1, `rule-strong` #8d95a3): hairlines, inactive plan bars, scrollbars.
- **Board** (`board`, #1a1d23 by day, #000 at night) with `on-board` #ffffff and `on-board-2` #c7cdd8: the dark station-board surfaces.

### Night variant
Set by `html[data-theme="dark"]`. Ground #11151c, concourse #1a2029, ink #eef0f4, ink-2 #b9c0cc, ink-3 #8f98a8, rule #2f3846, board #000. Lines brighten: red #ff5a60, orange #ffbf47, blue #5aa2ff, green #38d69b, brown #d2a074. `--mt-on-red`, `--mt-on-blue`, `--mt-on-green` flip to dark text. Full values are in the sidecar.

### Band token
`--mt-band` is an inline SVG image (five equal rects: red, orange, blue, green, brown) with a night twin using the brightened lines. It paints the 6px band fixed at the top of every unified-shell and reading-shell page (z-index 70). It is an image token, not a colour, so it is not in the frontmatter.

### Legacy token remap
metro.css re-points these so unmigrated stylesheets render in the world: `--uw-page`, `--uw-surface`, `--uw-surface-soft`, `--uw-navy`, `--uw-text`, `--uw-muted`, `--uw-accent` (to ink), `--uw-on-accent`, `--uw-blue`, `--uw-blue-strong`, `--uw-line`, `--uw-line-strong`, `--uw-hairline`, `--uw-radius`, `--uw-font-ui`, `--uw-page-bg`, `--ink-soft`, and `--glass-surface`, `--glass-strong`, `--glass-edge`, `--glass-hi` (transparent), `--glass-coral`, `--glass-coral-strong`. Some legacy tints stay as literal values, not `--mt-*` references: `--uw-blue-soft`/`--glass-blue` (#e8f1fc day, #1c2b44 night), `--uw-amber-soft`, `--uw-amber-ink`, `--glass-peach`, `--uw-ph-a/b`. The names `--uw-shadow` and `--uw-shadow-soft` and `--uw-radius-lg` (16px) are also still set. Write new rules against `--mt-*`, never the legacy names.

### Named Rules
**The Colour-Means-Region Rule.** A line colour on a map, chip or tile identifies a region or a tool category. Do not use a line colour as decoration.
**The One Action Rule.** Orange with ink text is the primary search action and the "next stop" announcement. Every other button is ink.
**The Ink-On-Orange Rule.** Orange never carries white text; `--mt-on-orange` is ink in both themes.

## Typography

**Display Font:** Poppins (Latin, 400/500/700 TTF from `assets/fonts/poppins/`) with 源柔黑體 / GenJyuu Gothic (Chinese, Regular/Medium/Bold WOFF2 slices loaded by unicode-range from `assets/fonts/genjyuu/`), then UniWay Sign (Noto Sans TC) for missing glyphs, then PingFang TC, Microsoft JhengHei, system-ui.
**Body Font:** the same family; one family for the whole site (`--mt-font`, applied to body, buttons and form controls).
**Label/Mono Font:** none. Numerals use `font-variant-numeric: tabular-nums`.

**Character:** A heavy signage gothic. Weight does the work: names and headings sit at 800-900, secondary information at 600-700.

### Hierarchy
- **Display** (900, clamp(28px, 4.05cqi, 58px), 1.12, -0.02em): the home H1, with one underline in line red under the span. Max width 22em, balanced wrap.
- **Headline** (900, clamp(26px, 3cqi, 42px), 1.18, -0.02em): home section h2s; reading-page headings are 900 at -0.01em.
- **Title** (800-900, 15-26px): board values 800 at 17px/1.3; station names 800 at 16px; line names 900 at 15px (17px on the narrow route sheet); card h3 900; stage h3 clamp(20px, 2.1cqi, 26px); journey sign title 22px; next-stop date 26px 900.
- **Body** (400-600, 16px, 1.75): section intro text in `ink-2`. Route note 13px/1.7.
- **Label** (700-800, 11-13px, 0.04-0.1em tracking): board cell captions 11.5px at 0.1em, station sub-labels 13px, line meta 12px. The floor is 11px (rail labels and origin captions); nothing is set smaller.

### Named Rules
**The Heavy Name Rule.** Names, headings and values are 800 or 900. Do not set a heading in a light or regular weight.
**The Signage Floor Rule.** Text is 11px or larger. Small captions stay in `ink-2` or `on-board-2`, never lighter.
**The No Helper Line Rule.** A heading is not followed by a grey sentence that restates it. Small text is kept only when it is a value, a label, a status the student must act on, or a disclosure the law or the data's honesty requires (the footer's source and analytics notice, 不代表校方受理, 待確認 reasons). `ink-2` is `#2b303a` and `ink-3` `#4a5160` so what remains is not grey.

## Layout

The home hero is a single-column grid with four stacked areas: sky, route (map), plan (four steps) and cue. The whole home page is one night (`#0b1220`, in the light and the dark theme alike: the night tokens apply to the home through `html:has(#home-landing:not([hidden]))`); the **sky** is transparent and holds one centred sentence, the station board and the Earth, so the planet rises out of the page, not out of a box, and its lower edge dissolves through a mask. The sentence is the H1, "世界這麼大，別讓資訊限制你的選擇。", set at `clamp(30px, 7.2cqi, 96px)` in 900 weight with a red underline under the second line; it is a block so it balances into two lines on a phone and never strands a character. The two official social accounts sit in the corner of the band as white pills, with no caption. Under the board the **Earth** rises as a horizon: a circle `min(1760px, 130cqi)` wide, clipped to `clamp(112px, 20svh, 220px)`, textured with the NASA Blue Marble (`earth-equirect.jpg`) and rim-lit. The texture strip opens over Asia and turns once in seven minutes (transform only; it holds still under reduced motion). Below the band the route map carries the visible H2 "你能去哪些交換學校，一次看清楚。", centred. Gaps use `clamp(26px, 4.4svh, 48px)` vertically. The map stage is capped at 1180px, centred, and is a container (`mtstage`) so the map reflows by container width, not viewport.

Country names on the globe are Traditional Chinese (`country-names-zh.json`, Natural Earth NAME_ZHT with the platform's own wording) drawn from the page's own face. The explore globe is a toy, not a photograph (it was NASA's Blue Marble until the search page went soft): flat pastel countries, each in the tone `countries.geojson` gives it (seven tones, so neighbours differ), on a light-blue sea (`#bfe4ff`; night `#2b3f73` with deeper tones), white round-joined borders, a white graticule, plum labels on a white halo, no atmosphere glow, and a soft blue shadow under the canvas so it floats. School markers are coral (`#ff6f91`) discs ringed in white. Its window has no colour of its own: it is the page's white (`--mt-ground`). The school card beside it is a fixed-content card (about 450 px, 330 px on a phone): place, Chinese name over English name, availability chip, a ruled grid of up to five figures (名額, 研修期間, 語言門檻, 申請截止, 費用), a single line naming what is still unpublished, one line of student experience, and 查看完整資料. It never scrolls; each value clamps at two lines.

The route map draws on a 1000 by 500 unit canvas. The origin sits at (96, 250); lines leave on a shared trunk to x=150, bend at 45 degrees to their lane, then run horizontal at 78-unit station spacing up to x=780. Lines are bundled 11 units apart at the origin. Stations and tags are positioned as percentages of the canvas. Lines show as many countries as fit; the tag states how many more ("前 N / M 國").

Responsive behaviour is container-driven. Below 1060px the board becomes a two-column grid (school and destination span the row, the go button spans the row at 56px min height). Below 719px stage width the diagram becomes a vertical route sheet: line tags turn into full-width accordion rows with "+"/"–", countries list down a vertical line bar with station dots on its edge, and the first line is open by default. Below 640px the four plan steps become a 2-column grid. Below 700px viewport width the supported-schools row stays one line and the Earth band is 96px tall. The old half-globe inset in the route map is gone; the Earth in the sky replaces it.

Sections below the hero are spaced by `clamp(56px, 7cqi, 104px)`. Card grids use 20px gaps. Reading pages are server-rendered, outside the single-page app, and carry the same band, header rule and ruled cards.

## Elevation & Depth

Flat. Depth comes from 2px ink outlines, the dark board surfaces against white, and hover tints (concourse, or a lighter ink). There is no blur, no glass and no gradient; buttons have `background-image: none` enforced. Resting surfaces have no shadow. The only shadows left are on floating UI: the select menu (`0 6px 18px #1a1d2326`), the map preview popup (`0 8px 22px #1a1d2326`), and the legacy `--uw-shadow*` values that old stylesheets still read.

### Named Rules
**The Flat-On-The-Ground Rule.** Containers sit on the ground with an outline, not a shadow. A shadow appears only on something that floats over content (menu, map popup).

## Shapes

Geometry is circles, bars and short-radius rectangles. Stations are circles with a 4px ink ring (20px; the origin ring is 68px with an 8px ring and a red core). Line paths are 9px strokes with round caps and joins, at 45 and 90 degrees only. Containers use 8px (chips, tags, line tags, mini inputs), 10px (buttons, nav items, popovers), 12px (ruled cards, bands), 14px (the nav rail); pills (999px) are used for small tags and the "edit" affordance. The station board itself, its cells and its go button are square (0px radius) to read as a hardware sign. Outlines are 2px ink; hairlines are 1px `rule`.

Station state is drawn: every partner school open this cycle is a solid station (filled with the line colour), some open is a white station with a line-colour inner dot, none open is hollow white. Text under each station repeats the same counts.

## Components

### Station board (search)
Black bar (`board`) of cells, square corners. Each cell has a 6px line-colour top rule (red school, orange destination, blue term, green language), a 11.5px caption at 0.1em tracking in `on-board-2`, and an 800 17px value in white. Cells divide by 1px `#ffffff33` rules and hover to `#ffffff14`. Focus is a 3px white inset outline. Selects drop their chevron to a small white SVG. The explore page uses the same board with three cells (orange, blue, green rules).
- **Go button:** orange (`line-orange`) fill, ink text, 900 19px, 150px minimum width, 28px side padding, square; hover #ffc24d.

### Buttons
- **Shape:** 10px radius, 2px ink border.
- **Primary:** ink fill, ground text, weight 800. Hover goes to `ink-2` fill and border.
- **Secondary:** ground fill, ink text, 2px ink border (map actions).
- **Back and icon buttons:** ground fill; 2px `rule` border on back, 2px ink on rail icons. Hover is a concourse fill.
- **Focus (all interactive):** 3px outline in `focus`, 2px offset; on dark board surfaces, a 3px white outline.

### Chips and tags
8px radius, ink fill by default. Colour variants carry meaning only: blue, green, red, orange, brown. Status tags are 6px radius: ok is blue, warn is concourse with a 2px inset ink outline. Pill badges are ink with ground text.

### Cards / Containers
Ruled card: 12px radius, 2px ink border, ground fill, no shadow, hover shows a heading underline (2px, offset 4px) or a concourse fill. Used for guide cards, tool tiles (a coloured icon chip beside its h3), forum boards, the social banner and reading-page article blocks. The real-world map band is a ruled card with a plain concourse land fill and no arcs or halos.

### Inputs / Fields
Inside the board, inputs are transparent with white text and placeholder #aab2c0 at weight 600. Outside the board, mini inputs are 8px radius, 2px ink border. Checkboxes are 4px radius with 2px ink border, and checked state fills blue.

### Navigation
The left rail is ground with a 2px ink border and 14px radius; items are 800 weight, 10px radius, `ink-2` text, 11px labels. Hover is concourse. The active item is ink fill with ground text. A 2px `rule` divides the actions group. The mobile header is a 2px ink bottom rule. The school switcher is a 10px ground pill with a 2px ink border and a round ink icon. The reading-page header is ground with a 2px ink bottom rule, ink-filled active link.

### Route map (signature)
Origin roundel (68px, ink ring, red core) with the suitcase mascot standing on it and an ink name label below. Each line has a coloured tag (8px radius, name 900 15px, English and counts below), a 9px path, and station buttons whose labels alternate above and below. Pressing a tag focuses that line and drops the others to 0.18-0.25 opacity (transition .25s, off under reduced motion). The map is drawn from the loaded catalogue by `metro-route.js`; nothing is sample data.

### Next stop and plan line
The next stop is a board-coloured strip with an orange "next" label, a 26px 900 tabular date and text; it appears only when a real deadline exists. The four-step plan is one line of 30px station rings joined by 8px bars: done is blue, now is red, to-do is hollow.

### Supported-school ticker
Board-coloured strip with an orange label cell at its left and school names in white. Scrolls as a marquee with a pause toggle; with reduced motion it becomes one horizontally scrollable row.

### Journey sign
A board-coloured sign with an orange "01 — 04" position index (30px 900), a 22px title and a red progress meter; below it, four stages sit as ring stations on one vertical blue line, the reading stage turning red.

## Do's and Don'ts

### Do:
- **Do** keep one ground and one ink; draw containers with 2px `ink` outlines and no resting shadow.
- **Do** use a line colour only for its region, or for the tool category it already marks, and pair it with its `--mt-on-*` text colour.
- **Do** make the primary search action orange with ink text; make every other primary button ink.
- **Do** set names and headings at weight 800-900 in Poppins and 源柔黑體 (weights 800-900 resolve to their Bold cut), 11px minimum anywhere.
- **Do** draw state: solid for open, dot for some, hollow for none, and state the same fact in text.
- **Do** reference `--mt-*` tokens in new rules and test both `data-theme` values.
- **Do** keep the 3px `focus` outline on every interactive element.

### Don't:
- **Don't** use gradients, glass, blur or backdrop-filter; they were removed deliberately and `background-image: none` is enforced on buttons.
- **Don't** put a line colour behind white text if it fails contrast: orange takes ink text; use `red-text` and `blue-text` for small red or blue text.
- **Don't** add new line colours or recolour a region; an extra hue breaks the map's meaning.
- **Don't** write new rules against `--uw-*` or `--glass-*`; they exist only for old stylesheets.
- **Don't** put a label above a heading. Kicker and eyebrow elements are hidden by the build; do not reintroduce them.
- **Don't** add pastel fills, shadowed floating cards or arcs and halos to maps.

### Known gaps (the build carries these; they are not rules)
- The supported-school ticker is plain scrolling text on the board strip. The dot-matrix destination ticker named in the direction contract was not built.
- The icon-card grids below the fold (5 tool tiles, 3 community cards) are still same-size cards in the ink-outline style, with a small icon chip beside the heading. They are not route-map or station-board forms.
- The journey sign keeps a sticky "01 — 04" position index. The index is orange numerals on the board, kept for orientation; it is a carry-over, not a pattern for new surfaces.
- Brown is used on the budget tool chip and the amber chip as well as the fifth line, so it is not exclusive to its region.
- Only the home was designed as a surface. Other routes inherit through tokens and the override blocks for the search page, shell and reading pages in metro.css; they are quieter and not individually composed.
- The Flutter app is unchanged and has its own system; this document covers the Web front end only.

## Later additions
- **Search dropdowns**: the highlighted row is a 12% tint of ink with a 2px ink outline, never a solid bar the colour of its text (it was, in both themes).
- **School marks**: every school has its own hue (`SCHOOL_BADGES` presets, then a wheel in `app.js` that never repeats between neighbours); light and night variants in `metro.css` section 17.
- **我的申請 今天**: boxes are sized to their contents and laid side by side (focus card + deadline card in one row, next tasks as cards in a grid, the to-do form on one line). The "synced" line is not shown; a sentence that restates its heading or the obvious is not written.
- **Cache versions**: `tests/static_asset_versions.json` records the `?v=` tag and content hash of every versioned static file; `scripts/update_static_versions.py` refuses a file whose content changed under the same tag. Static files with a `?v=` are cached for a year as immutable, so a forgotten bump serves visitors the old file.
- **Fonts**: the type system is the platform's own, Poppins for Latin and 源柔黑體 for Chinese. The Noto Sans TC stack the metro redesign introduced is only a fallback. 源柔黑體 is built from the Japanese cut of Source Han Sans, so a few Han characters take their Japanese glyph shapes.
- **Navigation**: one bar across the top on screens wider than 900px (logo, links, then theme, refresh, notifications, sync and account at the right); below that the drawer and bottom bar are unchanged. Pages are centred across the full width, 32px from each edge.
- **The home has no route map**: the first screen is the sentence, the search board and the Earth; the sections below it start with the supported schools.
- **The logo is always on screen**: the bar is fixed to the top and shows the mark *and* the "UniWay" wordmark at all times (the old rail's hover-only wordmark is overridden in `metro.css` section 19); phones keep their sticky header; the server-rendered pages (guides, schools, partners, privacy, terms) have a sticky header or `legal-bar` for the same reason (section 20). The account name beside its avatar shows from 1101px up.
- **The Earth turns**: one revolution takes 90 seconds (about 40 px a second on a wide screen; it was 420 s, too slow to be seen). (Superseded below: it also turns under `prefers-reduced-motion`, at a third of the speed, and has a pause button.)
- **The search page is soft and round** (`metro.css` section 21): the board is a warm tray holding round bubbles and a chunky pressable button; the small controls (filter, my conditions, recent, my schools, the view switch, the sort tabs, the globe's buttons and zoom) are tinted pills with no ink outline; the globe's window is rounded with a pastel sky and at least 700px tall (the viewport height minus the top bar on a desktop). The globe is sized to fill that window (`globalCamera` in `partner-map.js`), and the buttons over it keep 20px from its right edge so none is clipped. The tints are mixed from the metro tokens, so night mode follows. The home board keeps the square station-sign look.
- **The home board's button** fills the search page's own term and language-test fields and opens `#partners` with the typed place (`syncBoard` and the `mt-board` submit handler in `platform-home.js`). That wiring once lived in the deleted route-map script and was lost with it; `test_round_two.py` now covers it.
- **The Earth turns for everyone, and can be paused**: the system's "reduce motion" setting does not stop it (it runs at 270 s a turn instead of 90 s; `motion.css` switches every animation off with `!important` in that case, so `metro.css` has to say it again, as strongly), and a round button at the right of the Earth (`#mt-earth-toggle`) pauses and resumes it for anyone. The map's own "動態效果" button stays disabled under that setting.
- **The home board is soft and round too** (`metro.css` section 22): a cream tray on the night sky, white bubbles with dark text and tinted captions, the same chunky button as the school search. Its colours are fixed rather than tokens, because the home is always night while the bubbles are always light.
