# UniWay editorial workflow

The user requested ten initial Traditional Chinese SEO articles. On 2026-10-20, the recurring workflow changed to two complete articles per day, starting at 08:00 Asia/Taipei from 2026-10-21, with one new review PR containing that day's pair. Publishing cadence is a production workflow, not a promise of Google rankings. Do not auto-merge or deploy these batches.

## Content and routes

Articles live in `src/exchange_info/editorial/<slug>.json`. The Pydantic models in `seo_articles.py` validate the format. The article inventory drives `/guides`, individual routes, metadata, related links, and `/sitemaps/pages.xml`; no manual route list is needed. Existing `exchange-application`, `exchange-eligibility`, and `exchange-budget` URLs are retained.

Each article needs:

- One distinct student question and a unique title/description. Inspect existing articles and open PRs before selecting topics. Expand an existing article when intent overlaps substantially; do not create a second page just to change a keyword or year.
- Original, useful Traditional Chinese prose: a direct answer, three takeaways, a navigable outline, at least four substantive sections, a practical table/checklist, a meaningful diagram, two or more answered FAQs, and relevant next steps. The automated 1,500-character floor is a thin-content check, not a writing target; do not pad text to pass it.
- Specific primary sources, their dates/versions and scope. Read the source, not just search snippets. Separate official facts, historical statistics, editorial methods, and hypothetical worked examples. Verify arithmetic and units. Do not invent deadlines, costs, qualifications, testimonials, interviews or expert reviews. If a source is unavailable, use a verifiable archived official document with disclosed date or omit the unverified claim.
- At least one relevant inline photograph placed inside the article, with descriptive alt text, a topic-specific `image_caption`, and `image_credit` containing the photographer and HTTPS source URL. The user changed the visual direction on 2026-10-20: use licensed real photography, or clearly disclosed photorealistic generated imagery when needed; avoid drawings, paper-cut artwork, cartoons and 3D interior renders. Inspect the actual image, verify its source and usage license, and record provenance in a dated photography manifest. Do not label stock subjects as actual applicants, staff, partner campuses or guaranteed accommodation. If generated imagery is used in future, adapt its caption, credit presentation and the editorial policy honestly.
- Local `1536×1024` WebP under `static/assets/editorial/`, below 450 KB. Preserve natural colors and crop around the subject; inspect both the 3:2 article/list presentation and the 2:1 mobile homepage crop. Use a new filename when replacing an image so cached/social previews can discover the new asset. Explicit image dimensions, lazy loading and CSS preserve layout stability. Add original accessible HTML diagrams in section `diagram` fields; their content must explain this article, not repeat generic filler. See `docs/seo-editorial-photography-2026-10-20.json` for the current ten photos; the 2026-10-19 artwork manifest describes the superseded launch assets.
- Two to four related article slugs, and the applicable country when relevant. Link students to their own mother-school information and the planner. Do not scatter all articles across every partner page.
- `published` is the original publication date; `modified` changes only with meaningful content/source corrections, and `checked` records an actual source check. A source recheck alone does not bump sitemap `lastmod`. Use Asia/Taipei dates. Preserve original publication dates when revising.

All inputs are structured plain text. Do not insert raw HTML or tracking scripts into article data. The renderer provides Article/Breadcrumb JSON-LD, canonical, social image, visible authorship/source dates, accessible tables, native FAQ toggles and conversion links. Existing consent-based analytics remains disabled until a GA4 ID is configured; no new third-party scripts are required.

## Batch procedure

1. Fetch `blizzard-new/abroad` main and inspect current open editorial PRs. Work on an isolated branch/worktree. Do not reset or clean unrelated user changes. If the initial editorial implementation is still unmerged, prepare the next batch on a branch based on it with an explicit PR dependency; avoid recreating the publishing system.
2. Select two distinct useful topics from the approved 20-candidate pool (12 exchange-preparation topics plus eight AI/language/test-preparation topics), using Search Console evidence if the user has provided it; otherwise disclose that topic choice is editorial judgment. Review `docs/seo-editorial-backlog.md` and existing content first. Update the backlog to record each selected intention, Asia/Taipei batch date, slug, status and PR. Treat topics in pending PRs as selected; update overlapping existing guides rather than publishing near-duplicates, and select another independent candidate to complete the pair. If suitable candidates or verifiable sources are exhausted, report the limitation instead of inventing or padding articles.
3. Read and record official sources, write the full articles, prepare inline photography under the current image rules and original accessible diagrams, and check every numeric example. Keep an evidence ledger with checked date, source version, claim supported and any access limitation. A functioning URL alone is not content verification.
4. Run the checks below; inspect desktop and phone screenshots. Confirm the deployed wheel includes JSON, stylesheet and images. A failed essential check must be fixed or prominently reported before delivery, never called passing.
5. Create one new review PR for each day's batch containing the two articles, assets, any needed related-link updates and source/validation notes. Use a new isolated branch for each date; retrying the same batch should reuse its existing branch/PR to avoid duplicates. Attach its URL to the task. Report two titles, changes, validations and any limitation. Do not merge, deploy, submit thousands of URLs to Search Console, or promise immediate indexing.

## Local checks

```bash
.venv/bin/python scripts/check_editorial.py --base-ref origin/main
.venv/bin/pytest -q tests/test_seo_articles.py tests/test_seo.py tests/test_seo_content.py tests/test_seo_quality.py tests/test_seo_reporting.py
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium .venv/bin/pytest -q tests/e2e/test_seo_articles.py tests/e2e/test_seo_pages.py tests/e2e/test_seo_analytics.py
```

Browser tests use the repository's fixture, not pytest-playwright's `--browser`. In the managed cloud, local server/browser tests require network capability because sandbox socket operations are restricted. Preserve the configured proxy/CA settings. Use the installed Chromium path appropriate to the environment.

`check_editorial.py` validates the inventory, image budget, content floor and modification-date discipline against Git. Source veracity, originality and editorial usefulness still require review. A no-JavaScript phone test checks outline links, FAQs, image delivery, tables, related navigation and horizontal overflow. Browser measurements are lab checks, not field Core Web Vitals.

For a package check, build a wheel with `pip wheel --no-deps .`, inspect that `exchange_info/editorial/*.json`, `seo-articles.css` and `static/assets/editorial/*.webp` are included, then load from the extracted wheel outside the source checkout. No database migration is introduced.

## Schedule and production boundary

The existing recurring task starts at 08:00 every day, including weekends, in Asia/Taipei from 2026-10-21; it produces two complete articles together and creates one new review PR for that day's pair after validation. The start time is not a promise that the PR is ready at 08:00. This replaces the former Monday-only three-article schedule; do not create a second concurrent automation. While this workflow update is awaiting merge, the user's current daily/two-article instruction and the updated automation prompt take precedence over the old count and cadence on main. It does not rely on the Windows server being available to write content. GitHub access must remain connected; if a future run fails, report the actual blocker rather than claim a PR or publication succeeded.

The production server is maintained by the user. Their original `C:\uniway\app` has unrelated local work; the previous release used a separate checkout `C:\uniway\releases\seo-bd504845`, the original `.env`, and Compose project `uniway`. After PR review/merge, deploy a verified commit using a new isolated release checkout, preserve the running image as rollback, rebuild the app, and run the existing deployment SEO smoke test. Do not overwrite the original worktree or `.env`.

After deployment, verify `/guides`, one updated article, one new article, their image URLs and `/sitemaps/pages.xml`. Google can discover the new URLs through the existing submitted sitemap; repeat manual submission of every article is unnecessary. Use Search Console later to evaluate actual impressions, clicks and useful-page indexing.
