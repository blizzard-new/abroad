# UniWay mascot

`suitcase.webp` is the mascot's body only (a blue 3D suitcase, 384 x 460 px, transparent background, about 25 KB).
The eyes are not in the picture: `mascot.css` draws them, so they can blink, look around and wink.

Made from the supplied 640 x 640, 149-frame animated WebP:

1. Frame 0 (eyes open, looking ahead) was kept; the two eye blobs were found as the dark connected components in the
   upper body band and fitted with ellipses (OpenCV `fitEllipse`).
2. The eyes were painted out with `cv2.inpaint` (Telea, radius 9) plus a little matching grain, then the body was cropped
   to its outline with a 14 px margin and resized to 384 px wide (lossy WebP, quality 90, alpha quality 100).
3. The ellipses were converted to percentages of the cropped picture and written into `mascot.css`:

   | eye   | left    | top     | width  | height  | tilt (clockwise) | colour    |
   |-------|---------|---------|--------|---------|------------------|-----------|
   | left  | 37.011% | 46.830% | 8.538% | 12.351% | 9.2 deg          | `#2c2c2f` |
   | right | 61.052% | 48.873% | 8.565% | 12.455% | 9.2 deg          | `#2c2c2f` |

   Across the original animation the eyes only drift about 2% of the width sideways and blink once; the body barely
   moves. `mascot.css` reproduces both, so a rendering of the CSS eyes over this picture matches frame 0 of the original.

To change the mascot's look, redo these steps with the new animation and update the numbers above and in `mascot.css`.
The 4 MB original animation is deliberately not shipped: it would be larger than the whole first page.
