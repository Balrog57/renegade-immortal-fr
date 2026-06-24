import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const contentDir = join(ROOT, 'src', 'content');
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

      // Fix any field using broken "field: [\n  - \"...\"\n  - \"...\"\n]" pattern
      // Convert to proper flow: field: ["...", "..."]
      fm = fm.replace(
        /^(\w+): \[\n((?:  - ".*"\n)+)\]/gm,
        (_, key, items) => {
          const vals = [...items.matchAll(/  - (".*")/g)].map(x => x[1]);
          changed = true;
          return `${key}: [${vals.join(', ')}]`;
        }
      );

      if (changed) {
        content = '---\n' + fm + '\n---' + content.slice(m[0].length);
        let pp = full;
        if (process.platform === 'win32' && pp.length > 240 && !pp.startsWith('\\\\?\\')) {
          pp = '\\\\?\\' + pp;
        }
        await writeFile(pp, content, 'utf-8');
        fixed++;
      }
    }
  }
}

await processDir(contentDir);
console.log(`Checked: ${checked}, Fixed: ${fixed}`);
