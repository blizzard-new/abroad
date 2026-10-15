# UniWay globe bundle

Bundles [COBE](https://github.com/shuding/cobe) 0.6.4 (MIT) and its only dependency, Phenomenon (MIT), into one
classic script for the home page's half-globe backdrop. The bundle sets `window.UniWayCobe` to COBE's
`createGlobe(canvas, options)`; `platform-globe.js` in the static folder drives it.

With Node.js 20 or newer, from this directory:

```sh
npm ci
npm run build
```

The output is `src/exchange_info/static/vendor/cobe/0.6.4/cobe.min.js` plus `LICENSE.txt` with both licences.
