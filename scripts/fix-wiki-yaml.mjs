import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const wikiDir = join(ROOT, 'src', 'content', 'wiki');

let fixed = 0;
let checked = 0;

async function processDir(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      await processDir(full);
    } else if (entry.name.endsWith('.md')) {
      checked++;
      let content = await readFile(full, 'utf-8');
      const m = content.match(/^---\n([\s\S]*?)\n---/);
      if (!m) continue;
      let fm = m[1];
      let changed = false;

      if (/^sections: \[\]$/m.test(fm)) {
        fm = fm.replace(/^sections: \[\]\n?/m, '');
        changed = true;
      } else if (/^sections: \[\n/m.test(fm)) {
        fm = fm.replace(/^sections: \[\n(  - .*\n)*\]\n?/m, '');
        changed = true;
      }

      if (changed) {
        content = '---\n' + fm + '\n---' + content.slice(m[0].length);
        await writeFile(full, content, 'utf-8');
        fixed++;
      }
    }
  }
}

await processDir(wikiDir);
console.log(`Checked: ${checked}, Fixed: ${fixed}`);
