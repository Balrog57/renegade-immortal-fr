import sharp from 'sharp';
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

async function svgToPng(svgPath, pngPath) {
  const svg = await readFile(svgPath);
  const png = await sharp(svg, { density: 300 })
    .png({ quality: 95 })
    .toBuffer();
  await writeFile(pngPath, png);
  console.log(`  -> ${pngPath}`);
}

const targets = [
  { svg: 'public/wiki/images/Book 12.svg', png: 'public/wiki/images/Book 12.png' },
  { svg: 'public/wiki/images/Book 13.svg', png: 'public/wiki/images/Book 13.png' },
];

for (const t of targets) {
  const svgPath = join(ROOT, t.svg);
  const pngPath = join(ROOT, t.png);
  await svgToPng(svgPath, pngPath);
}

console.log('Done.');
