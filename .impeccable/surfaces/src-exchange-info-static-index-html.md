---
version: 1
slug: "src-exchange-info-static-index-html"
primary_target: "src/exchange_info/static/index.html"
related_targets: []
---

# Surface brief: UniWay home (#home-landing)

## Scope and visitor mode
Persuade. The home page of the Web front end (`src/exchange_info/static/index.html`, `#home-landing`). It sets the one visual world for the whole Web site; other routes inherit it through shared tokens and components, in Operate/Read mode (quieter, denser). Web only, front-end only; Flutter is out of scope until the owner confirms the Web result.

## Audience, job, action, proof, constraints
- Audience and job: a Taiwanese university student, usually on a phone, who wants to know where they can go on exchange from their own school and what to do next.
- Action: choose the home school if none is set, then start the search (destination, term, language) or pick a country/region. This must be a working control in the first viewport, not a link to elsewhere.
- Proof: real partner data for the chosen school (counts, open / pending / not open states, last-checked date). Nothing is invented; empty accounts show zero progress.
- Constraints: keep all DOM ids, roles, copy that tests assert (`#home-landing-title` containing 你能去哪些交換學校, `.pr-hero-socials`, `[data-home-globe]` and `[data-home-map="hero"] svg`, `.pr-supported` and `#home-supported-list` marquee with its toggle and reduced-motion behaviour, `#home-plan-steps`, `.pr-collage-mascot` with its 3D tilt), routes, SEO output, data. Blue suitcase mascot and the UniWay logo stay as they are.

## Chosen direction and memorable moment
Taipei-metro-style route map (the IMPECCABLE'S PICK card). The memorable moment: the student's own school is the origin station of a route map, each region is a coloured line, each partner country is a station, and the next real deadline reads like the next-stop announcement.

## Unresolved decisions
- Display face: a signage-style heavy gothic for Traditional Chinese, to be sourced and self-hosted (candidate: Noto Sans TC via @fontsource). Check payload against the existing self-hosted GenJyuu slices.
- Night variant of the world (existing theme toggle must keep working).
- Whether a signed-in student's saved schools should appear as interchange stations (not in the first build).

## Direction contract

THESIS: The home is a route map drawn from the student's own campus: their school is the origin station, each region is a coloured line, each partner country is a station, and the state of every station (本期開放, 合作備查, 待確認) is drawn, never implied. It refuses both today's pastel glass and globe-with-arcs hero and the category default of a headline over a search box over a row of photo cards.

OWN-WORLD: White ground and one ink (#1a1d23), with five saturated line colours (red, blue, green, orange, a dark brown or violet for the rest) used at full strength as thick 45 and 90 degree lines with rounded bends. Stations are black-ringed white circles, filled with the line colour when open this cycle and hollow when only on file or unconfirmed. Names sit on bilingual name tiles (Chinese heavy gothic over small English), the search is a dark platform-board bar with line-coloured tabs, and the supported-school marquee is a dot-matrix style destination ticker. No gradients, no glass, no blur; recognizable with all content removed as a transit diagram.

STORY: In five seconds a visitor understands that this map starts from their own school and shows where they can go. They believe it because every station says what is confirmed and what is not, with a last-checked date. They act by choosing their school and then a line or a country; a returning student sees their next real deadline as the next stop.

FIRST VIEWPORT: Desktop 1440x900, left rail as station-sign column. Heavy-gothic H1 (你能去哪些交換學校，一次看清楚。) top-left, about 56 to 64px, with the platform-board search bar directly under it: 從 [school] 出發, destination, term, language, and a clear 找學校 button. Right and below: the route diagram fills the viewport, origin roundel on the left carrying the suitcase mascot as 你在這裡, lines running right, stations as buttons. A small labelled real-geography inset (示意圖, 非實際位置) holds the existing map host. The four-step plan becomes one line of four stations under the diagram. The primary action is the search bar button. On a 390x844 phone the H1 and board come first, the diagram is a vertical route sheet below it.

FORM: Taipei-metro route map, position 1 on my grounded list, the IMPECCABLE'S PICK card, chosen by the user. seed:313019080de5f98e

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
