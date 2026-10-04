# Design QA — UniWay full-page travel journal

Final result: passed

## Scope and visual truth

- Date: 2026-09-27. This revision addresses the user's correction that the entire background must adopt the selected style, beyond isolated illustrations.
- Selected source: C:/Users/User/AppData/Local/Temp/codex-clipboard-fa4c83a7-9c21-4798-ad8f-8c2d51dcbaac.png (1122 × 1402, three-screen concept board, no specified CSS viewport).
- Preview: http://127.0.0.1:8767/#home
- Previous report: output/journey-canvas/before/design-qa.md.
- Web only. Existing APIs, real content, school photos, geographic map, motion behavior and native applications are preserved. The previously removed boarding-pass search form remains absent.
- This is an original implementation of the reference's art direction, not a pixel-exact copy of its illustrated institutions or mock content.

## Evidence and comparison setup

All current screenshots are under output/journey-canvas/.

| Evidence | Requested CSS viewport | Stored capture | State |
| --- | --- | --- | --- |
| home-desktop.png | 1440 × 1000 | 1425 × 990 | Light home, full scene and paper discussion cards |
| search-desktop.png | 1440 × 1000 | 1425 × 990 | Japan map, expanded filters, shared collage margins |
| guide-desktop.png | 1440 × 1000 | 1425 × 990 | Guide stages on taped paper |
| school-desktop.png | 1440 × 1000 | 1425 × 990 | Tohoku University, real campus photography |
| budget-desktop.png | 1440 × 1000 | 1425 × 990 | Existing budget form on the shared paper canvas |
| home-tablet.png | 834 × 1000 | 819 × 982 | Full face, complete heading, unobstructed CTA |
| home-mobile.png | 393 × 852 | 378 × 820 | Dedicated portrait home illustration |
| guide-mobile.png | 393 × 852 | 378 × 820 | Stacked guide cards and portrait collage margins |
| school-mobile.png | 393 × 852 | 378 × 820 | Campus photo, caption and single-column facts |
| school-mobile-dark.png | 393 × 852 | 378 × 820 | Dimmed background and legible dark paper surfaces |
| home-dark.png | 1440 × 1000 | 1425 × 990 | Dark home with separate readable copy surface |

The in-app browser capture surface omits the scrollbar and slightly normalizes output size; desktop DPR is approximately 1. Compare original image proportions and visible detail rather than treating the concept board as a one-to-one pixel target. Temporary viewport overrides are reset after review.

The source, implemented desktop home, guide and tablet were viewed together. A focused full-resolution comparison uses reference-background-detail.png and implemented-background-detail.png (280 × 580 each): passport, camera, postcards, paper texture and the transition into the working UI. Initial iterations are retained as home-desktop-first.png, search-desktop-first.png, guide-desktop-first.png and home-mobile-first.png.

## Findings and fixes

No actionable P0/P1/P2 remains in this background pass.

1. **[P1, fixed] The old application surface concealed the page background.** Made the main app and workspace transparent and added a fixed viewport-wide raster canvas. Shared collage margins remain visible on search, guide, school and budget screens.
2. **[P1, fixed] The home illustration read as an image inside the old interface.** Removed the isolated hero image and card frame. Live HTML copy and the functional CTA now sit over an open paper-and-sky scene extending to the viewport edges.
3. **[P2, fixed] Navigation covered the aircraft.** Positioned the home scene below the inset paper navigation and used a second shared background behind the top strip. The final desktop screenshot shows the airplane and continuous page texture.
4. **[P2, fixed] Tablet cover cropping removed part of the traveler's face.** Changed tablet background sizing and placement. Increased text inset and reduced the tablet heading to 40px so it stays on quiet paper. The final 834px screenshot confirms a complete face and readable heading.
5. **[P2, fixed] Desktop artwork did not fit a narrow screen.** Added dedicated portrait home and shared canvases and explicitly reset the mobile background sizing. Text occupies the quiet upper area; artwork continues below. No document-level horizontal overflow was observed.

## Required fidelity surfaces

- **Typography:** preserved Poppins and GenJyuu Gothic body fonts and the previously verified Iansui display face. Responsive headline sizes are 38px on mobile, 40px on tablet and up to 64px on desktop. Real text remains selectable and accessible.
- **Layout and spacing:** inset paper navigation, open homepage hero, visible collage margins and paper content surfaces form one continuous scene. Search retains its working map/sidebar hierarchy. School content, guides and tools use the same paper treatment. Decorations do not intercept pointer input.
- **Colors and materials:** cream paper, navy ink, blue sky, coral controls and yellow tape follow the selected reference. Cards use a supplied raster paper texture and subtle shadows instead of floating glass panels. Existing contrast-aware button and text tokens remain in use. Dark mode uses dark solid reading surfaces with dimmed artwork; forced colors hides decorative backgrounds.
- **Images and assets:** five generated raster assets provide desktop/portrait page scenes and transparent washi tape. Original PNGs, delivery WebPs, prompts, dimensions and SHA-256 manifest are saved. Pillow was used only for delivery encoding and tape trim/resize. Real campus photographs and the functioning geographic globe remain the factual content sources.
- **Copy and content:** no new explanatory paragraphs, student posts or school facts were added. Existing content, source links, empty states and inference labels are preserved. The deleted ticket/search section was not reintroduced.

## Verification

- **76 passed:** frontend contracts, independent page routing, UI contracts, navigation/guide E2E and system-motion E2E. Report: output/journey-canvas/verification.xml.
- **4 passed:** travel-theme E2E. Report: output/journey-canvas/travel-verification.xml.
- **80 total passed.** Two existing external HTTPS warnings were reported by pytest. No test failed in this revision.
- The last tablet typography/background adjustments were then checked visually in the browser.
- Manual browser review covered home, keyword search, map/list switching, school detail, guide, budget, mobile layouts and light/dark themes. Console error query returned an empty array after these flows. Main app/workspace computed backgrounds are transparent, the old hero image is absent, and shared pages select the correct canvas.
- Scoped git diff --check passed; only the repository's LF/CRLF warning was emitted.
- No backend, database, native app or production deployment changes belong to this revision.

Final result: passed
