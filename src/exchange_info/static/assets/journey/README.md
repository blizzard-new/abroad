# UniWay travel journal assets

Created for the user-selected travel illustration reference on 2026-09-27 using the built-in image generation tool. The PNG originals are retained alongside optimized WebP delivery assets. These are decorative illustrations, not photos or claims about actual partner universities.

| Asset | Use | Delivery transformation |
| --- | --- | --- |
| `hero-travel` | Earlier framed hero, retained as source history; no longer rendered | WebP at original 1942 × 809 |
| `explorer` | Search and guide header: traveler using a camera | Transparent WebP, 900 × 600 |
| `paper-texture` | Quiet ivory background | WebP, 640 × 640 tile |
| `marker-underline` | Yellow brush underline under display headings | Transparent WebP, trimmed to 1993 × 132 |
| `home-canvas` | Full viewport homepage scenery, with quiet text area | WebP, 1513 × 1040 |
| `journal-canvas` | Shared all-page paper and travel collage backdrop | WebP, 1513 × 1040 |
| `home-canvas-mobile` | Portrait home backdrop with complete traveler | WebP, 923 × 1704 |
| `home-canvas-scenery` | Current homepage backdrop with the character removed | WebP, 1512 × 1040 |
| `home-canvas-mobile-scenery` | Current portrait homepage backdrop with the character removed | WebP, 923 × 1704 |
| `journal-canvas-mobile` | Portrait paper backdrop with narrow illustrated margins | WebP, 923 × 1704 |
| `washi-tape` | Small torn-paper tape accents on content sheets | Transparent WebP, trimmed/resized to 573 × 200 |

Prompts are saved in `output/journey-style/{hero,explorer,paper,underline}-prompt.txt`. Encoding, resizing and transparent-margin trimming used Sharp; artwork was not redrawn in code. Runtime URLs are same-origin. The reference image itself is not bundled into the product.

Full-canvas revision prompts are in `output/journey-canvas/`. These five new images also used the built-in image generator; Pillow was used only for WebP delivery encoding and trimming/resizing the transparent tape. Original PNGs remain unchanged. No generated campus or testimonial is substituted into school data.

The 2026-09-29 scenery revision used the built-in image generator to remove only the home character and reconstruct the obscured scenery. Original home canvases remain as source history. Its edit prompts are in `output/journey-scenery/edit-prompts.txt`; Pillow was used only to encode the edited PNGs as WebP.

The neighboring `fonts/iansui/iansui-display.woff2` is a subset of the upstream Iansui Regular font. Its subset includes the current home/search/guide/favorites display strings and the small English travel tagline. New display copy may require regenerating the subset; missing characters fall back to the normal UI font. The OFL license is retained. See `manifest.json` for source URLs and SHA-256 hashes.
