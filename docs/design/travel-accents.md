# UniWay Web travel accents

Saved-school tickets are the primary motif. Destination and completion stamps are small accents; standard actions retain the existing Lucide icons and UniWay navigation.

- Saved schools: a tinted ticket header, collection sequence number, dashed divider and edge notches. The number indicates collection display order, not preference rank. Notes, comparison, favorites and preference ordering retain their existing handlers and account scoping.
- School detail: a small stamp shows the record's country and optional `location.city`. Missing cities are omitted. No destination data is invented.
- Preparation: checked tasks show 「完成」. Only a newly checked task animates, for 180 ms; reduced-motion disables it. Unchecking removes the stamp. Existing account persistence and guest restrictions still apply, and keyboard focus stays on the checkbox.

`static/travel.css` owns the accent tokens and responsive rules. It builds on `--uw-*` colors, surfaces and shadows, uses a teal tint in light mode, and supplies dark-mode equivalents. Ticket edges must not clip controls or produce horizontal page overflow.

Validation: `tests/e2e/test_travel_theme.py` covers search/history, the shared school switcher, missing location data, numbered favorites, saved completion state, reduced motion and responsive screenshots. Existing discovery and navigation tests verify the preserved interactions. Test screenshots live in `output/travel-theme/`; their fixture school data is not production content.
