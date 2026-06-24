import sharp from 'sharp';
import { readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const ROOT = process.cwd();
const targets = [
  { src: 'wiki/images/Book 8.webp', dst: 'public/wiki/images/Book 8.webp', w: 303, h: 438 },
  { src: 'wiki/images/Book 9.webp', dst: 'public/wiki/images/Book 9.webp', w: 303, h: 438 },
  { src: 'wiki/images/Book 10.webp', dst: 'public/wiki/images/Book 10.webp', w: 303, h: 438 },
  { src: 'wiki/images/Book 11.webp', dst: 'public/wiki/images/Book 11.webp', w: 303, h: 438 },
];

for (const t of targets) {
  const buf = await readFile(join(ROOT, t.src));
  const resized = await sharp(buf)
    .resize(t.w, t.h, { fit: 'cover' })
    .webp({ quality: 90 })
    .toBuffer();
  await writeFile(join(ROOT, t.src), resized);
  await writeFile(join(ROOT, t.dst), resized);
  console.log(`  -> ${t.src} & ${t.dst} (${t.w}x${t.h})`);
}
console.log('Done.');
