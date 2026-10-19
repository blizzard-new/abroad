# UniWay illustrated editorial workflow

The user requested ten complete Traditional Chinese SEO articles, then a batch of three articles every Monday with a review PR. Publishing cadence is a production workflow, not a promise of Google rankings. Do not auto-merge or deploy these batches.

## Content and routes

Articles live in `src/exchange_info/editorial/<slug>.json`. The Pydantic models in `seo_articles.py` validate the format. The article inventory drives `/guides`, individual routes, metadata, related links, and `/sitemaps/pages.xml`; no manual route list is needed. Existing `exchange-application`, `exchange-eligibility`, and `exchange-budget` URLs are retained.

Each article needs:

- One distinct student question and a unique title/description. Inspect existing articles and open PRs before selecting topics. Expand an existing article when intent overlaps substantially; do not create a second page just to change a keyword or year.
- Original, useful Traditional Chinese prose: a direct answer, three takeaways, a navigable outline, at least four substantive sections, a practical table/checklist, a meaningful diagram, two or more answered FAQs, and relevant next steps. The automated 1,500-character floor is a thin-content check, not a writing target; do not pad text to pass it.
- Specific primary sources, their dates/versions and scope. Read the source, not just search snippets. Separate official facts, historical statistics, editorial methods, and hypothetical worked examples. Verify arithmetic and units. Do not invent deadlines, costs, qualifications, testimonials, interviews or expert reviews. If a source is unavailable, use a verifiable archived official document with disclosed date or omit the unverified claim.
- At least one relevant original inline illustration placed inside the article, with descriptive alt text and an honest illustrative caption. Use image generation for new art, not unlicensed university/stock photographs. The launch palette is ivory, teal, mint, muted coral and ochre with paper/pencil texture; avoid words and fake logos within images.
- Local `1536×1024` WebP under `static/assets/editorial/`, below 450 KB. Encode/compress the original without changing the composition. Explicit image dimensions, lazy loading and CSS preserve layout stability. Add original accessible HTML diagrams in section `diagram` fields; their content must explain this article, not repeat generic filler. Shared artwork is acceptable only when genuinely relevant; don't present it as a real campus or student.
- Two to four related article slugs, and the applicable country when relevant. Link students to their own mother-school information and the planner. Do not scatter all articles across every partner page.
- `published` is the original publication date; `modified` changes only with meaningful content/source corrections, and `checked` records an actual source check. A source recheck alone does not bump sitemap `lastmod`. Use Asia/Taipei dates. Preserve original publication dates when revising.

All inputs are structured plain text. Do not insert raw HTML or tracking scripts into article data. The renderer provides Article/Breadcrumb JSON-LD, canonical, social image, visible authorship/source dates, accessible tables, native FAQ toggles and conversion links. Existing consent-based analytics remains disabled until a GA4 ID is configured; no new third-party scripts are required.

## Batch procedure

1. Fetch `blizzard-new/abroad` main and inspect current open editorial PRs. Work on an isolated branch/worktree. Do not reset or clean unrelated user changes. If the initial editorial implementation is still unmerged, prepare the next batch on a branch based on it with an explicit PR dependency; avoid recreating the publishing system.
2. Select three distinct useful topics, using Search Console evidence if the user has provided it; otherwise disclose that topic choice is editorial judgment. Review `docs/seo-editorial-backlog.md` and existing content first. Update the backlog to record the completed intentions.
3. Read and record official sources, write the full articles, create inline artwork and diagrams, and check every numeric example. Keep an evidence ledger with checked date, source version, claim supported and any access limitation. A functioning URL alone is not content verification.
4. Run the checks below; inspect desktop and phone screenshots. Confirm the deployed wheel includes JSON, stylesheet and images. A failed essential check must be fixed or prominently reported before delivery, never called passing.
5. Create one review PR containing the three articles, assets, any needed related-link updates and source/validation notes. Attach its URL to the task. Report three titles, changes, validations and any limitation. Do not merge, deploy, submit thousands of URLs to Search Console, or promise immediate indexing.

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

The recurring task produces three articles together on Monday morning in Asia/Taipei and creates a review PR. It does not rely on the Windows server being available to write content. GitHub access must remain connected; if a future run fails, report the actual blocker rather than claim a PR or publication succeeded.

The production server is maintained by the user. Their original `C:\uniway\app` has unrelated local work; the previous release used a separate checkout `C:\uniway\releases\seo-bd504845`, the original `.env`, and Compose project `uniway`. After PR review/merge, deploy a verified commit using a new isolated release checkout, preserve the running image as rollback, rebuild the app, and run the existing deployment SEO smoke test. Do not overwrite the original worktree or `.env`.

After deployment, verify `/guides`, one updated article, one new article, their image URLs and `/sitemaps/pages.xml`. Google can discover the new URLs through the existing submitted sitemap; repeat manual submission of every article is unnecessary. Use Search Console later to evaluate actual impressions, clicks and useful-page indexing.
