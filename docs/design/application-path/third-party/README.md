# React Bits Glide Select

`../glide-select.css` adapts the component CSS, and `../glide-select.js` ports its popover, gliding highlight and selection-label feedback to the existing native JavaScript preview. It does not install a React runtime or the upstream icon dependency.

- Component: https://reactbits.dev/micro/glide-select
- Official source registry: https://reactbits.dev/r/GlideSelect-JS-CSS.json
- Repository: https://github.com/DavidHDev/react-bits
- License: [full upstream MIT + Commons Clause text](react-bits-LICENSE.md), retrieved 2026-10-29 from https://raw.githubusercontent.com/DavidHDev/react-bits/main/LICENSE.md

UniWay adaptations: light brand colors, 48px touch rows, scrollable 12-stage list, native top-layer popover, keyboard navigation and typeahead, reduced-motion handling and an explicit animation toggle. Touch uses ordinary scrolling and tapping rather than drag-to-select, so the longer stage list remains usable.
