# UniWay travel journal Web style

The selected image is art direction for the existing product: warm paper, navy ink, sky blue, coral actions, illustrated travelers, yellow marker accents and destination stamps.

- Main surfaces: ivory `#faf8f2`, paper `#fffefa`, navy `#102956`, blue `#1263e6`, coral `#d93852`, yellow `#f5ce63`.
- Chinese body text remains GenJyuu Gothic; Latin body text remains Poppins. Iansui is limited to large travel headings and a short tagline.
- The full viewport is an illustrated travel canvas, including the margins and space behind navigation. The home introduction is unframed editable text over that canvas, with one real navigation link. The deleted origin/destination boarding-pass form remains absent.
- Search keeps one existing search/filter state and the real list/MapLibre globe. Desktop filters sit beside results; on small screens they become a collapsible section above results.
- School detail uses the existing official campus image, a paper caption, destination stamp and solid reading surfaces. School data, source links and AI-inference labels remain intact.
- Shared colors, surfaces, navigation and actions also cover guides, favorites and application tools. Existing interaction/motion behavior and reduced-motion preferences are preserved.
- Paper fibers, sky, cherry blossoms, postcards, passport and camera extend across the full background. Inset navigation, paper content surfaces, postcard borders and real raster washi tape tie every page into the same journal. Content remains on quiet paper areas. The mock's illustrated geographic map is not substituted for the functional globe.
- Mobile uses dedicated portrait backgrounds; tablet sizing keeps the traveler's face inside the viewport. Decorative layers are fixed, ignore pointer events, dim in dark mode and disappear in forced-colors mode.
- Desktop, tablet, mobile and dark-mode evidence plus known constraints are recorded in root `design-qa.md`.

Implementation: `src/exchange_info/static/journey.css` followed by `journey-canvas.css`, and small structural changes in `index.html`. The latter clears the old `.app-shell`/`.workspace` solid backgrounds that previously hid the page artwork. No backend schema, API or native app changes are part of this style pass.
