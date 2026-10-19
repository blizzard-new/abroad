# SEO photography replacement — 2026-10-20

All ten guides now use licensed real photographs instead of the launch illustrations. This includes homepage guide cards, the guide index, related-article cards, article figures, Open Graph images and Article image URLs. New `-photo.webp` filenames avoid reusing cached illustration URLs. The superseded illustration files are removed.

Each article has an alt description matching the photo, a contextual caption, and a linked photographer credit. The editorial policy and recurring editorial workflow now describe the photography direction. Publication dates, official-source check dates and article prose are preserved; the image revision is dated 2026-10-20 in Asia/Taipei.

## Photo inventory and provenance

The [photography manifest](seo-editorial-photography-2026-10-20.json) records the source page, photographer, Pexels asset ID, license, downloaded crop URL, original dimensions, available camera metadata, final byte size and SHA-256 for every image. All ten source pages and their credit/license metadata were checked, and every selected image was visually inspected. Photos illustrate the topics; subjects are not presented as actual applicants or staff. The shared-room image is explicitly identified as a hostel room, rather than a partner-university dormitory.

| Guide | Photo subject | Photographer |
| --- | --- | --- |
| Application | Reading documents beside a laptop | Mikhail Nilov |
| Eligibility | Books, notes and laptop at a study table | Yan Krukau |
| Study plan | Writing notes beside a laptop | PNW Production |
| Budget | Calculator and handwritten calculations | Towfiqu barbhuiya |
| Scholarships | Two students using a tablet and notes | RDNE Stock project |
| Housing | Daylit shared hostel room with bunk beds | cottonbro studio |
| Credit transfer | Shared reading in a library | Ludovic Delot |
| Japan costs | Japanese neighborhood shopping street | Huy Phan |
| Korea costs | Seoul neighborhood and city skyline | Dasha Klimova |
| Germany costs | Heidelberg square and castle | Tobias Waibl |

All files are local 1536×1024 WebP, 43,106–386,812 bytes each, below the existing 450 KB budget. Combined size decreased from 2,543,616 to 1,634,538 bytes (35.7%). The mobile homepage retains its 2:1 crop, with the application photo anchored at the top to retain the subject's face and documents; other layouts retain their 3:2 presentation.

## Validation

- `python scripts/check_editorial.py --base-ref origin/main`: passes for all ten articles, including image dimensions, file budgets and modification dates.
- `pytest -q tests/test_seo_articles.py tests/test_editorial_release_gate.py tests/test_seo.py tests/test_seo_content.py tests/test_seo_quality.py tests/test_seo_reporting.py`: **76 passed**. Includes every article's caption, credit link, metadata, sitemap and delivered photo, plus rejection of unsafe credit URLs.
- `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium pytest -q tests/e2e/test_seo_articles.py tests/e2e/test_editorial_brand_journey.py`: **19 passed**, including every article on mobile, the journey with JavaScript disabled, and homepage/article navigation at 320, 390 and 1440 px.
- After the mobile crop adjustment, reran `tests/e2e/test_editorial_brand_journey.py::test_platform_to_article_and_back`: **3 passed**. The homepage stylesheet version was bumped so the adjustment reaches cached clients.
- Visually reviewed the homepage at 390, 618 and 1440 px, guide cards at 1440 px, and inline photography with credits at 390 and 1440 px. These views have no horizontal overflow. The 618 px view matches the width of the user's marked browser view.
- Built a wheel with `uv build --wheel` and inspected its image/article entries: all ten current photos and JSON files match source bytes/hashes, and no superseded illustrations are included. Temporary build output is excluded from the change.
- `git diff --check`: passes. No production deployment or merge was performed.

## Browser previews

Desktop homepage:

![Desktop homepage guide cards](seo-photography-previews/home-1440.jpg)

618 px homepage:

![Homepage at the marked browser width](seo-photography-previews/home-618.jpg)

Guide cards:

![Guide index with real photographs](seo-photography-previews/guide-index-1440.jpg)

Mobile inline photograph and credit:

![Mobile article photograph and linked credit](seo-photography-previews/article-390.jpg)

Additional captures: [390 px homepage](seo-photography-previews/home-390.jpg), [1440 px inline photo](seo-photography-previews/article-1440.jpg).
