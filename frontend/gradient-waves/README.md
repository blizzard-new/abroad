# UniWay Gradient Waves background

`GradientWaves.jsx` and `GradientWaves.css` are unchanged files fetched from the
[React Bits JS-CSS registry](https://reactbits.dev/r/GradientWaves-JS-CSS.json)
on 2026-10-14. The registry lists `ogl@^1.0.11`. React and React DOM mount this
component as an isolated background inside the existing FastAPI/static frontend.
The remaining platform uses its existing JavaScript.

`platform-background.jsx` contains the requested ocean palette and all supplied
parameters. The host fills the viewport on every platform route, rather than a
600px demonstration block. Pointer coordinates reach the canvas without
intercepting foreground controls. The upstream component pauses when the page
is hidden; reduced motion, renderer errors and lost WebGL contexts show a static
gradient. Changing reduced-motion preferences removes or remounts the animation.
Glass surfaces and the home introduction preserve text contrast in both themes.

## Rebuild

From this directory, with Node.js 20 or newer:

```sh
npm ci
npm run build
```

Commit the lockfile and generated `src/exchange_info/static/gradient-waves.js`,
`gradient-waves.css` and `gradient-waves.js.LEGAL.txt` together with source changes.
Existing Python packaging includes these static assets, so serving the platform
does not require Node.js or a third-party CDN. The generated legal notice includes
React/React DOM and the React Bits MIT + Commons Clause license.
