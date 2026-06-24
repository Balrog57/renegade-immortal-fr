#!/usr/bin/env node
/**
 * Conversion unique des sources (traduction/ + wiki/) vers src/content/ Markdown.
 *
 * Sources :
 *   build_parts/chapters-data.json  -> 2 084 chapitres
 *   build_parts/wiki-data.json      -> 2 285 fiches wiki
 *   build_parts/data.json           -> 3 personnages principaux (Wang Lin, Situ Nan, Li Muwan)
 *   traduction/Book N - Title/NNNN - Chapter N - Title.txt  -> texte chapitres
 *   wiki/<name>.json                -> contenu complet des fiches
 *   wiki/images/                    -> images locales associées
 *
 * Sorties :
 *   src/content/chapters/<book>/<NNNN>-<slug>.md
 *   src/content/books/<book>-<slug>.md            (13 tomes)
 *   src/content/wiki/<type>/<slug>.md             (par catégorie)
 *   src/content/site/home.md, stats.md
 */

import { readFile, writeFile, mkdir, readdir, stat, copyFile, access } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, join, basename, extname, sep, posix } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// ---------------------------------------------------------------------------
// Utils
// ---------------------------------------------------------------------------

const reEscapeRE = /[.*+?^${}()|[\]\\]/g;
function reEscape(s) { return String(s).replace(reEscapeRE, '\\$&'); }

function slugify(s, maxlen = 80) {
  s = String(s ?? '').normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '') // accents off
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
  if (s.length > maxlen) s = s.slice(0, maxlen).replace(/-[^-]*$/, '');
  return s || 'x';
}

function yamlScalar(v) {
  if (v == null) return '""';
  if (typeof v === 'boolean' || typeof v === 'number') return String(v);
  let s = String(v);
  if (/[:#\[\]{}&'*!|>"'%@`]/.test(s) || /^\s|\s$/.test(s) || /\n/.test(s)) {
    return JSON.stringify(s);
  }
  return s;
}

// Préserve les valeurs "natives" (chaînes, nombres) dans les tableaux.
function yamlList(arr) {
  if (!Array.isArray(arr) || arr.length === 0) return '[]';
  if (arr.every(x => typeof x !== 'string' || !/[:#\[\]{}&'*!|>"'%@`\n]/.test(x))) {
    return '[' + arr.map(x => JSON.stringify(String(x))).join(', ') + ']';
  }
  return '[\n' + arr.map(x => '  - ' + JSON.stringify(String(x))).join('\n') + '\n]';
}

function frontmatter(obj) {
  const lines = ['---'];
  for (const [k, v] of Object.entries(obj)) {
    if (v == null) continue;
    if (Array.isArray(v)) {
      if (v.length === 0) continue;
      if (v.every(x => typeof x === 'object' && x !== null)) {
        // nested arrays of objects: skip / fallback to string
        lines.push(`${k}: ${yamlList(v.map(x => JSON.stringify(x)))}`);
      } else {
        lines.push(`${k}: ${yamlList(v)}`);
      }
    } else if (typeof v === 'object') {
      lines.push(`${k}: ${JSON.stringify(JSON.stringify(v))}`);
    } else {
      lines.push(`${k}: ${yamlScalar(v)}`);
    }
  }
  lines.push('---', '');
  return lines.join('\n');
}

async function readJSON(p) {
  try {
    return JSON.parse(await readFile(p, 'utf-8'));
  } catch (e) {
    console.warn(`  ! impossible de lire ${p} : ${e.message}`);
    return null;
  }
}

async function ensureDir(p) { await mkdir(p, { recursive: true }); }

async function writeText(p, content) {
  await ensureDir(dirname(p));
  // Windows safe long path
  let pp = p;
  if (process.platform === 'win32' && pp.length > 240 && !pp.startsWith('\\\\?\\')) {
    pp = '\\\\?\\' + pp;
  }
  await writeFile(pp, content, 'utf-8');
}

// ---------------------------------------------------------------------------
// Wiki categorization (mirror of build.py logic)
// ---------------------------------------------------------------------------

const MAIN_PERSOS = new Set([
  'Wang Lin', 'Situ Nan', 'Li Muwan', 'Li MuWan', 'Tuo Sen', 'All Seer', 'All-Seer',
  'Sima Mo', 'Master Devil God', 'Zhou Yi', 'Wang Ping', 'Han Pao',
  'Blood Ancestor', 'Soap', 'Ancient God'
]);

function categorizeOne(name, cats) {
  const lc = new Set((cats || []).map(c => c.toLowerCase()));
  if (MAIN_PERSOS.has(name) || lc.has('characters')) return 'personnage';
  if (lc.has('locations') || lc.has('planets') || lc.has('continents') || lc.has('star system')) return 'lieu';
  if (lc.has('sects') || lc.has('clan') || lc.has('organisations')) return 'secte';
  if (lc.has('cultivation') || lc.has('realms') || lc.has('techniques') || lc.has('spells')) return 'cultivation';
  return 'personnage'; // défaut : on classe les fiches non catégorisées en personnages
}

// ---------------------------------------------------------------------------
// Image lookup
// ---------------------------------------------------------------------------

let imageIndex = null;

async function buildImageIndex() {
  const dir = join(ROOT, 'wiki', 'images');
  if (!existsSync(dir)) { imageIndex = []; return; }
  const files = await readdir(dir);
  imageIndex = files.map(f => ({ name: f, stem: f.replace(/\.[^.]+$/, '') }));
}

function findImageForPage(pageName) {
  if (!imageIndex) return '';
  const nl = pageName.toLowerCase();
  // exact stem match, prefer .webp
  let cands = imageIndex.filter(f => f.stem.toLowerCase() === nl);
  let pick = cands.find(f => /\.webp$/i.test(f.name)) || cands[0];
  if (pick) return `/renegade-immortal-fr/wiki/images/${pick.name}`;
  // partial
  cands = imageIndex.filter(f => f.stem.toLowerCase().includes(nl) || nl.includes(f.stem.toLowerCase()));
  pick = cands.find(f => /\.webp$/i.test(f.name)) || cands[0];
  if (pick) return `/renegade-immortal-fr/wiki/images/${pick.name}`;
  return '';
}

// ---------------------------------------------------------------------------
// Wiki section parser (mirror of build.py:parse_wiki_sections)
// ---------------------------------------------------------------------------

const KNOWN_TITLES = new Set([
  'Overview','Personality','Background','History','Appearance','Manhua','Trivia',
  'Links and References','Cultivation','Techniques','Items','Relationships','Fights',
  'Quotes','Image Gallery','Description','Legacy','Abilities','Powers and Abilities',
  'Equipment','Weaknesses','Gallery','Quote'
]);

function isTitleBlock(b) {
  if (KNOWN_TITLES.has(b)) return true;
  if (/^Book \d+/.test(b)) return true;
  if (/^Chapter \d+\b/.test(b)) return true;
  if (b.length > 80) return false;
  if (/[.!?,;]$/.test(b)) return false;
  if (!b[0] || !/[A-ZÀ-Ý]/.test(b[0])) return false;
  if (/:/.test(b)) return false;
  if (/^\d+(\.\d+)*$/.test(b)) return false;
  if (/^\[\d+\]$/.test(b)) return false;
  if (/[.!?,;]/.test(b)) return false;
  return true;
}

function parseWikiSections(content) {
  const ovs = [...content.matchAll(/^Overview$/gm)];
  let bodyStart = 0;
  if (ovs.length >= 2) bodyStart = ovs[1].index;
  else if (ovs.length === 1) bodyStart = ovs[0].index;
  let body = content.slice(bodyStart).replace(/\[\s*\n\s*\]/g, '');
  // Split on blank lines, then re-aggregate blocks
  const rawBlocks = body.split(/\n\n+/).map(b => b.replace(/\n/g, ' ').trim()).filter(Boolean);
  const sections = [];
  let current = null;
  let buf = [];
  for (const b of rawBlocks) {
    if (b === 'Overview' || isTitleBlock(b)) {
      if (current && buf.length) sections.push([current, buf]);
      current = b;
      buf = [];
    } else {
      const cleaned = b.replace(/\[\d+\]/g, '').replace(/\s+/g, ' ').trim();
      if (cleaned.length > 40) buf.push(cleaned);
    }
  }
  if (current && buf.length) sections.push([current, buf]);
  return sections;
}

// ---------------------------------------------------------------------------
// Main conversions
// ---------------------------------------------------------------------------

async function convertChapters() {
  console.log('\n=== Conversion chapitres ===');
  const data = await readJSON(join(ROOT, 'build_parts', 'chapters-data.json'));
  if (!data) return { count: 0, byBook: {} };
  let written = 0, skipped = 0;
  const byBook = {};
  for (const c of data) {
    byBook[c.book] ||= { title: c.bookTitle, count: 0, firstN: c.n, lastN: c.n };
    byBook[c.book].count++;
    if (c.n < byBook[c.book].firstN) byBook[c.book].firstN = c.n;
    if (c.n > byBook[c.book].lastN) byBook[c.book].lastN = c.n;

    const srcRel = c.file; // "traduction/Book N - Title/NNNN - Chapter ...txt"
    const srcAbs = join(ROOT, srcRel);
    let text = '';
    if (existsSync(srcAbs)) {
      let raw = await readFile(srcAbs, 'utf-8');
      raw = raw.replace(/^\ufeff/, '').replace(/^\s+/, '');
      const firstLineEnd = raw.indexOf('\n');
      if (firstLineEnd > 0 && !/[.!?]$/.test(raw.slice(0, firstLineEnd).trim())) {
        raw = raw.slice(firstLineEnd + 1);
      }
      text = raw.trim();
    }
    if (!text) { skipped++; continue; }

    // Paragraphes -> Markdown : on garde les sauts de ligne simples comme paragraphes
    const mdBody = text.split(/\n+/).map(p => p.trim()).filter(p => p).join('\n\n');
    const cleanTitle = String(c.title).replace(/^Chapitre\s+\d+\s*[-—:]\s*/, '').trim() || c.title;
    const slug = slugify(cleanTitle);
    const fname = `${String(c.n).padStart(4, '0')}-${slug}.md`;
    const outDir = join(ROOT, 'src', 'content', 'chapters', `tome-${c.book}`);
    const fm = frontmatter({
      n: c.n,
      title: cleanTitle,
      book: c.book,
      bookTitle: c.bookTitle,
      en: c.en || undefined,
      slug,
    });
    await writeText(join(outDir, fname), fm + mdBody + '\n');
    written++;
  }
  console.log(`  ✓ ${written} chapitres écrits (${skipped} ignorés)`);
  return { count: written, skipped, byBook };
}

async function convertBooks(byBook) {
  console.log('\n=== Conversion livres ===');
  let written = 0;
  // Cover images naming convention: "Book N.webp"
  for (const [bookStr, info] of Object.entries(byBook)) {
    const book = Number(bookStr);
    const title = info.title;
    const slug = slugify(title);
    const fname = `tome-${book}-${slug}.md`;
    const outDir = join(ROOT, 'src', 'content', 'books');
    const cover = existsSync(join(ROOT, 'wiki', 'images', `Book ${book}.webp`))
      ? `/renegade-immortal-fr/wiki/images/Book ${book}.webp`
      : '';
    const fm = frontmatter({
      book,
      title,
      cover: cover || undefined,
      chaptersCount: info.count,
      rangeStart: info.firstN,
      rangeEnd: info.lastN,
    });
    // Body volontairement minimal : on enrichira via Pages CMS plus tard.
    await writeText(join(outDir, fname), fm + `\n_Tome ${book} — ${title}. ${info.count} chapitres (n° ${info.firstN} à ${info.lastN})._\n`);
    written++;
  }
  console.log(`  ✓ ${written} livres écrits`);
  return written;
}

async function convertWiki() {
  console.log('\n=== Conversion wiki ===');
  const data = await readJSON(join(ROOT, 'build_parts', 'wiki-data.json'));
  if (!data) return { count: 0, byType: {} };
  let written = 0, skipped = 0;
  const byType = { personnage: 0, lieu: 0, secte: 0, cultivation: 0 };
  const seenSlugs = new Set();

  for (const p of data) {
    const type = categorizeOne(p.name, p.categories);
    // Charger le contenu complet depuis wiki/<name>.json
    const wikiFile = join(ROOT, 'wiki', `${p.name}.json`);
    let pageData = null;
    if (existsSync(wikiFile)) {
      pageData = await readJSON(wikiFile);
    }
    if (!pageData && p.sub) {
      // Sous-pages : on cherche par stem
      const dir = join(ROOT, 'wiki');
      for (const f of (await readdir(dir))) {
        if (f.replace(/\.[^.]+$/, '') === p.name) {
          pageData = await readJSON(join(dir, f));
          if (pageData) break;
        }
      }
    }
    const content = (pageData && pageData.content) || '';
    const sections = parseWikiSections(content || '');

    let baseSlug = slugify(p.name);
    let slug = baseSlug;
    let suffix = 2;
    while (seenSlugs.has(`${type}/${slug}`)) {
      slug = `${baseSlug}-${suffix++}`;
    }
    seenSlugs.add(`${type}/${slug}`);

    const image = findImageForPage(p.name);
    const fm = frontmatter({
      name: p.name,
      title: p.title || p.name,
      type,
      categories: (p.categories || []).slice(0, 12),
      image: image || undefined,
      url: p.url || undefined,
      sections: sections.map(([h, paragraphs]) => ({ heading: h, body: paragraphs.join('\n\n') })),
    });

    // Corps Markdown : on restitue les sections en headings Markdown
    let body = '';
    if (image) body += `![${p.title || p.name}](${image})\n\n`;
    if (p.url) body += `> Source : [Fandom Wiki](${p.url}) (CC BY-SA)\n\n`;
    body += `**Catégories :** ${(p.categories || []).join(', ') || '—'}\n\n`;
    if (sections.length === 0 && p.preview) {
      body += `${p.preview}\n`;
    } else {
      sections.forEach(([h, paragraphs], i) => {
        body += `${i === 0 ? '## ' : '### '}${h}\n\n${paragraphs.join('\n\n')}\n\n`;
      });
    }

    const outDir = join(ROOT, 'src', 'content', 'wiki', type);
    const fname = `${slug}.md`;
    await writeText(join(outDir, fname), fm + body);
    byType[type]++;
    written++;
  }
  console.log(`  ✓ ${written} fiches wiki écrites (perso:${byType.personnage} lieu:${byType.lieu} secte:${byType.secte} cult:${byType.cultivation})`);
  return { count: written, byType };
}

async function convertSite(stats) {
  console.log('\n=== Conversion site/home ===');
  const outDir = join(ROOT, 'src', 'content', 'site');

  const homeFm = frontmatter({
    title: 'Renegade Immortal FR',
    section: 'home',
    order: 0,
  });
  const homeBody = `# Renegade Immortal — 仙逆 — Xian Ni

L'odyssée d'un jeune orphelin devenu démon, forgeant son destin entre ciel et terre, là où les mortels défient l'ordre des Immortels.

## Synopsis

Sorti de son village avec rien d'autre qu'un héritage brisé et une volonté de fer, **Wang Lin** s'élève à travers les royaumes de cultivation — disciple méprisé, traître présumé, vagabond solitaire — jusqu'à devenir l'une des figures les plus redoutables du cosmos.

Parmi les sectes qui s'effondrent, les clans ancestraux et les guerres entre Immortels, sa route n'est jamais droite. Il tue pour protéger ce qu'il aime. Il trahit pour survivre. Il attend, pendant des siècles, ce que d'autres ont oublié.

*Renegade Immortal* (仙逆) est l'un des monuments du xianxia moderne : une fresque de ${stats.chapters} chapitres où chaque transgression a un prix, et où la vraie immortalité n'est jamais celle qu'on croit.

## Chiffres clés

- **${stats.chapters}** chapitres
- **${stats.books}** tomes
- **${stats.personnages}** personnages
- **${stats.lieux}** lieux
- **${stats.sectes}** sectes & clans
`;
  await writeText(join(outDir, 'home.md'), homeFm + homeBody);
  console.log('  ✓ site/home.md');
}

// ---------------------------------------------------------------------------
// Copy public assets (wiki/images -> public/wiki/images)
// ---------------------------------------------------------------------------

async function copyWikiImages() {
  console.log('\n=== Copie images wiki -> public/wiki/images ===');
  const srcDir = join(ROOT, 'wiki', 'images');
  const dstDir = join(ROOT, 'public', 'wiki', 'images');
  if (!existsSync(srcDir)) { console.log('  ! aucun dossier wiki/images'); return 0; }
  await ensureDir(dstDir);
  const files = await readdir(srcDir);
  let n = 0;
  for (const f of files) {
    const src = join(srcDir, f);
    const dst = join(dstDir, f);
    try {
      const st = await stat(src);
      if (!st.isFile()) continue;
      await copyFile(src, dst);
      n++;
    } catch (e) {
      // ignore individual errors (some filenames may have invalid chars)
    }
  }
  console.log(`  ✓ ${n} images copiées`);
  return n;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  console.log('Renegade Immortal FR — conversion Markdown');
  console.log(`ROOT = ${ROOT}`);
  await buildImageIndex();

  const { byBook } = await convertChapters();
  const booksCount = Object.keys(byBook).length;
  await convertBooks(byBook);
  const { byType } = await convertWiki();
  await convertSite({
    chapters: 2084,
    books: booksCount,
    personnages: byType.personnage,
    lieux: byType.lieu,
    sectes: byType.secte,
  });
  await copyWikiImages();

  console.log('\n✓ Conversion terminée.');
  console.log('  Prochaine étape : npm install && npm run build');
}

main().catch(e => {
  console.error('Erreur fatale :', e);
  process.exit(1);
});