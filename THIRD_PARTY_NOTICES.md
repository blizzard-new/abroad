# Third-party notices

The Web interface redistributes the following pinned runtime assets.

## Web typography

- Iansui (芫荽), Regular: https://github.com/ButTaiwan/iansui . Copyright 2025 The Iansui Project Authors. SIL Open Font License 1.1, included at `src/exchange_info/static/assets/fonts/iansui/OFL.txt`. A locally generated WOFF2 subset, named `UniWay Journal` in CSS, supplies only decorative travel headings; body text continues to use GenJyuu Gothic and Poppins. Source and output hashes are recorded in `src/exchange_info/static/assets/journey/manifest.json`.
- GenJyuu Gothic (源柔黑體), Regular / Medium / Bold: unmodified WOFF2 subsets from `shogo82148/genjyuugothic-subsets`, release `2022-06-16`, https://github.com/shogo82148/genjyuugothic-subsets/releases/tag/2022-06-16 . Copyright 2014 自家製フォント工房 by MM; web subsets copyright 2021 Ichinose Shogo. SIL Open Font License 1.1; M+ derived glyphs also retain their upstream notice. License, upstream README and attribution in `src/exchange_info/static/assets/fonts/genjyuu/`.
- Poppins, Regular / Medium / Bold: https://github.com/google/fonts/tree/main/ofl/poppins . Copyright 2020 The Poppins Project Authors. Unmodified TTFs, SIL Open Font License 1.1 in `src/exchange_info/static/assets/fonts/poppins/OFL.txt`.
- Map label glyphs are generated from Poppins Medium with https://github.com/maplibre/font-maker (build-time only). Range 0–255 and its font license are in `src/exchange_info/static/assets/partner-map/fonts/Poppins Medium/`; output hashes are recorded in the partner-map manifest.
- Source URLs and downloaded asset SHA-256 hashes: `src/exchange_info/static/assets/fonts/sources.json`. All runtime font requests are same-origin. No external font CDN or system installation is required.

## Partner globe assets

- MapLibre GL JS 5.24.0: https://github.com/maplibre/maplibre-gl-js/tree/v5.24.0 . BSD-3-Clause, including upstream notices, in `src/exchange_info/static/vendor/maplibre/5.24.0/LICENSE.txt`. CSP bundle and same-origin worker; no blob worker or external CDN at runtime.
- Natural Earth 5.1.2, 1:50m countries, lakes and rivers: https://github.com/nvkelso/natural-earth-vector/tree/v5.1.2 . Public domain (https://www.naturalearthdata.com/about/terms-of-use/). Coordinates are rounded to four decimals; properties retain names, label coordinates, continents and cartographic color groups. Waterways are limited to scale rank 4 or lower.
- Home page map outline `src/exchange_info/static/assets/home/world-land.json`: derived from the Natural Earth 5.1.2 country shapes above (public domain), flattened and simplified into one SVG path in a Natural Earth projection by `scripts/build_home_world_map.py`. Antarctica and islands smaller than 0.9 square degrees are dropped, apart from the partner-school regions.
- Open Sans Semibold glyphs, range 0–255: https://demotiles.maplibre.org/font/Open%20Sans%20Semibold/0-255.pbf . Open Font License in `src/exchange_info/static/assets/partner-map/fonts/Open Sans Semibold/LICENSE.txt`.
- ROR institution identity/city metadata: CC0, https://ror.org/about/terms/ . Wikidata P625 institution coordinates: CC0, https://www.wikidata.org/wiki/Wikidata:Licensing . Each enriched record retains its ROR and Wikidata evidence URLs and retrieval timestamp. These are representative institution locations, not assigned exchange campuses.
- Reproducible map vendor retrieval: `scripts/prepare_partner_map_assets.py`; asset SHA-256 hashes: `src/exchange_info/static/assets/partner-map/manifest.json`.

## COBE 0.6.4 (home page globe)

- Project: https://github.com/shuding/cobe (with its dependency Phenomenon 1.6.0, https://github.com/vaneenige/phenomenon)
- Source: https://registry.npmjs.org/cobe/-/cobe-0.6.4.tgz
- License: MIT (both packages)
- Bundled into one classic script by `frontend/globe` as `src/exchange_info/static/vendor/cobe/0.6.4/cobe.min.js`; both licences are in `src/exchange_info/static/vendor/cobe/0.6.4/LICENSE.txt`. The land map COBE draws is its own embedded bitmap; no network request is made at runtime.

## Morphicons 1.7.0

- Project: https://www.morphicons.com/
- Source: https://github.com/guillermolg00/morphicons/tree/v1.7.0
- License: MIT
- Included license: `src/exchange_info/static/vendor/morphicons/1.7.0/LICENSE`

## Lucide 0.468.0

- Project: https://lucide.dev/
- Source: https://github.com/lucide-icons/lucide/tree/0.468.0
- License: ISC
- Included license: `src/exchange_info/static/vendor/lucide/0.468.0/LICENSE`

## Local AI runtime and operator-downloaded models

The following components are installed or downloaded into the local user profile for the approved development prototype. Model weights and Ollama binaries are not copied into or redistributed with this repository.

### Ollama 0.32.15

- Project: https://ollama.com/
- Source: https://github.com/ollama/ollama/tree/v0.32.15
- License: MIT
- Installation: user-level `Ollama.Ollama` winget package

### Gemma 4 12B for Ollama

- Model tag: `gemma4:12b`
- Manifest digest: `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`
- Source: https://ollama.com/library/gemma4
- License reported by `ollama show gemma4:12b --license`: Apache License 2.0
- Storage: current user's Ollama model store; not committed to the repository

### EmbeddingGemma for Ollama

- Model tag: `embeddinggemma:latest`
- Manifest digest: `85462619ee721b466c5927d109d4cb765861907d5417b9109caebc4e614679f1`
- Source: https://ollama.com/library/embeddinggemma
- License reported by `ollama show embeddinggemma --license`: Gemma Terms of Use, last modified March 24, 2025
- Storage: current user's Ollama model store; not committed to the repository

Gemma is provided under and subject to the Gemma Terms of Use found at ai.google.dev/gemma/terms.
