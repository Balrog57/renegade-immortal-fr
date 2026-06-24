import { copyFile, readdir, stat, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const src = join(ROOT, 'wiki', 'images');
const dst = join(ROOT, 'public', 'wiki', 'images');

if (!existsSync(src)) {
  console.log('[copy-images] wiki/images not found, skipping');
  process.exit(0);
}

await mkdir(dst, { recursive: true });
const files = await readdir(src);
let n = 0;
for (const f of files) {
  const s = join(src, f);
  if ((await stat(s)).isFile()) {
    await copyFile(s, join(dst, f));
    n++;
  }
}
console.log(`[copy-images] ${n} images copied to public/wiki/images`);
