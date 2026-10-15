import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { build } from 'esbuild';

const directory = '../../src/exchange_info/static/vendor/cobe/0.6.4';
await mkdir(directory, { recursive: true });
await build({
  entryPoints: ['globe-entry.js'],
  bundle: true,
  minify: true,
  format: 'iife',
  target: 'es2020',
  outfile: `${directory}/cobe.min.js`,
});
const cobe = JSON.parse(await readFile('node_modules/cobe/package.json', 'utf8'));
const phenomenon = JSON.parse(await readFile('node_modules/phenomenon/package.json', 'utf8'));
await writeFile(`${directory}/LICENSE.txt`,
  `COBE ${cobe.version} — MIT\n` + await readFile('node_modules/cobe/LICENSE', 'utf8') +
  `\nPhenomenon ${phenomenon.version} — MIT (bundled by COBE)\n` + await readFile('node_modules/phenomenon/LICENSE', 'utf8'));
