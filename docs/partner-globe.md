# Partner globe

Current visual revision: at the user's request, the radial partnership lines, traveling highlights and connection checkbox have been removed. Color geography, country borders, rivers, graticules, university markers, clustering and school-selection breathing animation remain. Earlier connection descriptions below document the previous implementation.

## Repository analysis and scope

The Web app uses FastAPI, Pydantic and plain HTML/CSS/JavaScript; no React or build pipeline is needed. `static/index.html` owns `#partners`, `static/app.js` owns state, `filteredPartners()` and the desktop table/mobile cards. Search, country, availability, college and degree filters are shared. The optional eligibility profile sorts the same result by match score. There are no existing continent, semester or language filter controls to duplicate.

`GET /student-dashboard?school=…` provides `PartnerUniversity` records from official CGU sheets or the bundled NTPU catalog; `GET /destination-profiles` adds city and student-life information. `#school=<encoded name>` opens the existing detail page. `renderFavoriteButton()` and `toggleFavorite()` provide signed-in favorites and guest comparison. `activeHomeSchool()` derives the current school from the existing selected-school/account flow, with the existing default catalog for guests.

Public catalog storage is JSON/JSONL with bundled baselines and local overrides. Supabase/PostgreSQL is also available for accounts, workspaces, governance and RAG. Its `partner_universities` table is a relationship table, not the live map's catalog. Coordinates therefore belong in the existing public-file storage architecture, with a typed location model, rather than a new database service. No native mobile source is in scope.

## Technology

MapLibre GL JS 5.24.0 is vendored with its license, loaded only on demand. Globe projection, worker-based GeoJSON clustering and built-in touch/camera interaction fit the existing vanilla app. Natural Earth country geometry and local font glyphs provide a self-contained basemap: no commercial key, remote tiles, runtime geocoder, or visitor data sent to a map provider.

References: https://maplibre.org/maplibre-gl-js/docs/examples/display-a-globe-with-a-vector-map/ and https://maplibre.org/maplibre-gl-js/docs/examples/create-and-style-clusters/.

## Location provenance

`official_data/university_locations.jsonl` is a location enrichment catalog, never a replacement list of partnerships. Only names returned by the existing dashboard are rendered. Missing or ambiguous coordinates remain pending. Local reviewed overrides live in `data/processed/university_locations.jsonl`; the API exposes only verified coordinate pairs. Each record includes country, city, coordinates, timestamp, status, precision and source URLs. Coordinates represent an institution's representative campus, not a guarantee of the student's assigned campus.

The offline maintenance process checks organization identity, country and coordinate evidence before publishing any point. No geocoding runs from the browser or the API.

## Implemented

- Text-labelled List / 3D Map segmented controls, without a page reload or another dashboard request.
- Shared search, country, availability, college, degree and eligibility-score ordering. Cities are searchable through the same predicate.
- `?view=map` opens `#partners` directly. `view`, `q`, `country`, `availability`, `college`, `degree` and selected `home` persist in URL queries. Browser back/forward and refresh restore them.
- Existing desktop table and mobile cards remain. Expanded mobile cards survive background enrichment and view switches.
- Rotatable WebGL globe, touch drag/pinch, worker clustering, hover labels, school preview, existing detail-page navigation, favorites and guest comparison.
- Distinct, dynamically selected CGU/NTPU home marker. Unselected guests see the current catalog's origin described as a browsing context.
- Optional thin great-circle connections across the globe, capped at 80 currently visible, filtered destinations.
- Country/search camera framing, moderate school zoom, date-line-aware bounds, retained camera on card close and view return. Camera framing accounts for the mobile bottom sheet even with reduced motion.
- Desktop side card, mobile bottom sheet, keyboard school selector, focus return and focus preservation after saving/comparing. Nearby coincident points offer individual school choices.
- Empty catalog, no search results, partial/missing coordinates, API failure, module/engine/worker/basemap failures, timeouts and WebGL context loss have recoverable states. Retrying a broken worker creates a fresh engine instance; it does not retain a failed worker pool.

## Architecture and database changes

`app.js` retains ownership of all filters and selected home university. `partnerMapSnapshot()` passes `filteredPartners()` into the lazy module. No filters, catalog requests, account writes or new detail router exist inside the map. The map controller is retained when hidden, stops movement while hidden, and resizes on return. Retrying explicitly disposes its observers, events, markers and WebGL resources.

`PartnerUniversity.location` and `SupportedUniversity.location` are additive, optional fields. `GET /student-dashboard` and `GET /universities` enrich their existing responses from `UniversityLocation` records. The existing partnership source and all existing fields are preserved.

**No SQL migration or remote database operation is needed.** This feature follows the application's public JSONL catalog architecture. The existing Supabase relationship table and account storage are unchanged. `UniversityLocation` validates finite, bounded coordinate pairs and requires a source and timestamp for verified records. Pending/review candidates never expose coordinates. Bad rows are isolated; invalid local overrides invalidate their own identity rather than falling back silently to an older verified coordinate.

## Coordinate maintenance

1. Start the existing Web app locally.
2. Export its actual public partnership identities:

   ```powershell
   .venv/Scripts/python.exe scripts/export_university_location_input.py output/partner-globe/location-input.json --base-url http://127.0.0.1:8767
   ```

3. Run the offline resolver into a review file:

   ```powershell
   .venv/Scripts/python.exe scripts/refresh_university_locations.py output/partner-globe/location-input.json output/partner-globe/location-review.jsonl
   ```

   It accepts either the exported array or a saved dashboard JSON response. The resolver is resumable, uses at most three network workers and supports `--retry-pending`. ROR candidate discovery must resolve to one active education institution with the matching official domain, country and a single registry location. A linked Wikidata record must have one non-deprecated Earth coordinate, within 100 km of the independently matched registry location. City centroids are never substituted for campus coordinates. Subunits, branches and ambiguous coordinates remain pending/review candidates. The registry's location is a representative institution point, not proof of a student's assigned campus.

4. Review the evidence and campus scope, then copy accepted/reviewed rows to `data/processed/university_locations.jsonl` for a local override or maintain the version-controlled baseline. The export/resolver does not publish to the live catalog automatically.

2026-09-23 baseline: **277 unique location identities, 168 verified (including both home universities)**. Shared schools and display-name variants account for differing record and partnership totals. The final conservative campus-scope pass leaves:

| Current catalog | Real partnerships | On map | Pending / campus review |
| --- | ---: | ---: | ---: |
| Chang Gung University | 77 | 44 | 33 |
| National Taipei University | 203 | 125 | 78 |

All pending schools remain browsable in List View. Every coordinate retains an evidence URL and timestamp. The home cities were also checked against the universities' official address pages: https://www.cgu.edu.tw/engineering/Contents?nodeId=469 and https://new.ntpu.edu.tw/about/map-directions .

## Performance

- MapLibre CSP engine (~972 KB), worker (~458 KB), detailed country geometry (~1.89 MB), lakes (~359 KB), rivers (~271 KB), glyphs (~78 KB), vendor CSS (~70 KB) and map module are requested only after opening Map View. These are raw file sizes, not measured compressed transfer sizes. The color/detail revision increases map-only geography assets by approximately 2.25 MB; List View still does not request them.
- Automated network assertions confirm List View loads no map engine, map module or country geometry, and view switches do not refetch `/student-dashboard`.
- Existing page JavaScript gains approximately 160 integration lines; the small scoped map/switcher stylesheet is included normally. No build system or framework is introduced.
- GeoJSON worker clustering uses radius 42 and max clustering zoom 9; points are WebGL layers, not thousands of DOM markers. Only the home point uses a DOM marker. Coincident locations remain individually selectable.
- Updates reuse the same engine/source, avoid unchanged school GeoJSON submissions, and cap arcs at 80 × 49 vertices. Up to 16 small route highlights animate at at most 15 updates/second. Animation pauses during camera motion, outside the viewport, in hidden tabs, in List View, with the motion control, and with reduced-motion preferences. The camera never rotates continuously on its own.
- MapLibre uses its CSP build with a same-origin worker. The existing `script-src 'self'` policy is unchanged. Runtime map requests remain local; no map key, external tile service, or client geocoder is involved.
- No numerical FCP/FPS claim is made; responsiveness and resource requests were exercised in Chromium.

## Testing and actual browser verification

Evidence is saved under `output/partner-globe/` (local artifacts, not application data):

- 92 related Python/model/API/frontend/routing tests passed (`unit-results.xml`).
- All 18 map Chromium scenarios passed together after the final refinements (`browser-results.xml`, 89.48 seconds). Earlier focused checks also verified the focus/camera/overlap refinements and basemap-error retry.
- Desktop 1440×1000, tablet 834×1112 and mobile 393×852: real marker clicks, preview, comparison, detail navigation/back, no horizontal overflow, card placement and camera continuity.
- Real touch events verified mobile drag and pinch zoom. Reduced-motion mode and keyboard selection/escape/focus were exercised.
- 1,000 synthetic points exist only in the isolated scale test; real MapLibre worker clustering and cluster expansion were tested, with arcs limited to 80. Production uses only the existing real catalogs.
- Error injection covers dashboard API, dynamic module, engine, worker and basemap, followed by successful retries without losing search state. Empty and missing-coordinate fixtures remain usable through List View.
- Actual local app also ran at `http://127.0.0.1:8767/`, with both real catalogs, a real Japan filter and current home markers. `globe-desktop.png` captures the real CGU catalog; its capture recorded no page errors. `preview-1440.png`, `preview-834.png`, `preview-393.png` are isolated browser-test captures.
- JavaScript syntax, Python compilation and the newly added lines' whitespace checks passed.

### Existing repository failures, verified against the pre-change files

The broader `tests/test_next_phase_contract.py` run reports **14 failures / 6 passes** concerning frozen OpenAPI drift and previously missing contract routes, headers and response metadata. The exact same 14 failed with the pre-change `api.py` and `models.py` loaded in a separate process (`baseline-contract-results.xml`, `check_baseline_contract.py`). No working files were reverted for that comparison. Those unrelated contracts were not rewritten to make this feature look globally green.

Two additional legacy browser checks produced one pass (partial destination-profile evidence) and one failure. The guest comparison/plan-login flow completed its functional assertions but failed its final zero-console-errors assertion because the existing `/community/boards` request returns 404. The same failure reproduced while serving the pre-change `app.js` and `index.html` in an isolated browser route (`baseline-legacy-browser-diagnostic.xml`, `check_legacy_browser.py`); no application file was reverted. The new map's functional checks do not claim that unrelated existing endpoints are error-free.

`git diff --check` also reports four pre-existing whitespace-only lines in `api.py` outside this change. A baseline-to-current patch check confirms zero newly introduced trailing-whitespace lines. `implementation.patch` isolates this task's changes to the previously modified files.

## Files changed

Existing files changed by this task:

- `src/exchange_info/static/app.js`: view lifecycle, shared URL state, preview bridge, expanded-card preservation.
- `src/exchange_info/static/index.html`: accessible switch and map region.
- `src/exchange_info/models.py`: optional location fields.
- `src/exchange_info/api.py`: location enrichment of two existing responses.
- `THIRD_PARTY_NOTICES.md`: map/data/font attribution.

New files:

- `src/exchange_info/static/partner-map.js`, `partner-map.css`.
- `src/exchange_info/university_locations.py`.
- `src/exchange_info/official_data/university_locations.jsonl`.
- `src/exchange_info/static/vendor/maplibre/5.24.0/{maplibre-gl-csp.js,maplibre-gl-csp-worker.js,maplibre-gl.css,LICENSE.txt}`.
- `src/exchange_info/static/assets/partner-map/{countries.geojson,lakes.geojson,rivers.geojson,manifest.json,fonts/Open Sans Semibold/0-255.pbf,fonts/Open Sans Semibold/LICENSE.txt}`.
- `scripts/{export_university_location_input.py,refresh_university_locations.py,prepare_partner_map_assets.py}`.
- `tests/{test_university_locations.py,test_partner_map_geometry.py,e2e/test_partner_globe.py}`.
- This document.

## 2026-09-23 color and motion refinement

The user's follow-up requested richer colors, finer globe detail and stronger animation. The map now uses Natural Earth 1:50m geography, with continent-based green, sand, coral and lavender country tones; deepened ocean blue; major lakes/rivers; subtle graticules; coastal edging; and a globe atmosphere using the pinned engine's [sky API](https://maplibre.org/maplibre-style-spec/sky/). Geographic colors are decorative regional distinctions, not application availability or eligibility signals. Hovering a country adds a subtle highlight. Selected schools have a restrained pulse, the home marker breathes, and the optional partnership connections use a warm-to-cool gradient with traveling highlights. Connections start enabled, with a separate accessible animation pause control. Reduced motion disables nonessential animation.

Light and dark map palettes, desktop/tablet/mobile interaction and animation lifecycle were checked. Local review captures: `color-desktop.png`, `color-dark.png`, `color-mobile.png` under `output/partner-globe/`. The real catalog capture recorded no page errors or horizontal overflow. Basemap assets can be regenerated independently with `scripts/prepare_partner_map_assets.py --basemap-only`.

Final refinement validation: **19 map Chromium scenarios passed** (`color-browser-results.xml`, 123.45 seconds) and **62 frontend/geometry/routing regression checks passed** (`color-regression-results.xml`). The added scenario verifies visible route-highlight movement, pause/resume without camera movement, List View suspension and live reduced-motion preference changes. JavaScript syntax and the asset script's Python compilation also passed. This follow-up changed only the map module/style, its HTML controls and asset-version references, basemap generation/assets, attribution, the map test and this report; APIs, location records and native applications were not changed.

## Remaining issues and future improvements

- 33 CGU and 78 NTPU partnerships need coordinate/campus review; no guessed point is substituted. Resolving these is a data-review task, not an additional client geocoder.
- The self-contained Natural Earth basemap is appropriate for global/regional exploration, not street-level campus navigation.
- Existing API-contract failures and the legacy `/community/boards` 404 listed above remain. This is a local Web implementation, not a production release or native-app port.
- Useful later additions, not implemented here: reviewed campus-specific coordinates, highlighting existing favorites or AI recommendations, and source-backed cost-of-living layers.
