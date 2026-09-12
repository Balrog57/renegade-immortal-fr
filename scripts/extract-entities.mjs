import { readFile, writeFile, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, join, extname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const CH = join(ROOT, 'src/content/chapters');
const WIKI = join(ROOT, 'src/content/wiki');
const OUT = join(ROOT, 'glossaire-entites.md');

const esc = s => String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
// word-boundary, unicode-aware regex on lowercased text
function reCount(term) {
  const re = new RegExp('(?<!\\p{L})' + esc(term.toLowerCase()) + '(?!\\p{L})', 'giu');
  return re;
}

// ---------- 1. Read all chapters ----------
async function walk(dir) {
  const out = [];
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) out.push(...await walk(p));
    else if (extname(e.name).toLowerCase() === '.md') out.push(p);
  }
  return out;
}

const files = (await walk(CH)).sort();
const chapters = [];
let combined = '';
for (const f of files) {
  let raw = await readFile(f, 'utf8');
  // strip frontmatter
  raw = raw.replace(/^---[\s\S]*?---\s*/, '');
  chapters.push({ file: f.replace(/\\/g, '/'), body: raw });
  combined += '\n' + raw;
}
const totalChapters = chapters.length;
console.error(`chapters: ${totalChapters}`);

// ---------- 2. Load wiki entities ----------
const TYPES = ['personnage', 'secte', 'lieu', 'cultivation', 'auteur'];
function parseFront(raw) {
  const m = raw.match(/^---\s*([\s\S]*?)---/);
  if (!m) return {};
  const fm = {};
  for (const line of m[1].split(/\r?\n/)) {
    const mm = line.match(/^([\w-]+):\s*(.*)$/);
    if (mm) fm[mm[1]] = mm[2];
  }
  return fm;
}
function field(raw, label) {
  const re = new RegExp('[\\-\\|]\\s*\\*\\*' + esc(label) + '\\s*:\\*\\*\\s*(.+)', 'u');
  const m = raw.match(re);
  return m ? m[1].replace(/\*+/g, '').trim() : '';
}
function splitAliases(s) {
  if (!s) return [];
  return s.split(/[·,，;|\n]/).map(x => x.trim()).filter(Boolean);
}
function stripChinese(s) { // keep roman part, capture chinese inside (...)
  const m = s.match(/^([^(（]+)[(（]([^)）]+)[)）]?/);
  if (m) return { rom: m[1].trim(), zh: m[2].trim() };
  return { rom: s.replace(/[（(].*$/, '').trim(), zh: '' };
}

const wiki = [];
for (const t of TYPES) {
  const d = join(WIKI, t);
  if (!existsSync(d)) continue;
  for (const f of (await readdir(d)).filter(x => x.endsWith('.md'))) {
    const raw = await readFile(join(d, f), 'utf8');
    const fm = parseFront(raw);
    const name = (fm.name || '').trim();
    if (!name) continue;
    const pinyin = field(raw, 'Pinyin');
    const zh = field(raw, 'Nom chinois') || '';
    const aliasStr = field(raw, 'Alias');
    let aliases = splitAliases(aliasStr);
    // normalize aliases: drop trailing chinese parentheticals captured separately
    aliases = aliases.map(a => {
      const c = a.match(/[(（]([^)）]+)[)）]/);
      return a.replace(/[(（][^)）]+[)）]/g, '').trim();
    }).filter(Boolean);
    wiki.push({ type: t, name, pinyin, chinese: zh, aliases });
  }
}

// ---------- 3. Count occurrences in corpus ----------
function countAll(term) {
  const re = reCount(term);
  let occ = 0;
  const matches = combined.toLowerCase().match(re);
  occ = matches ? matches.length : 0;
  return occ;
}
function chapterHits(term) {
  const re = reCount(term);
  let n = 0;
  for (const c of chapters) if (re.test(c.body)) n++;
  return n;
}

// romanize aliases: terms to count for a wiki entity = name + non-empty roman aliases (no chinese)
function romanTerms(e) {
  const terms = new Set([e.name]);
  for (const a of e.aliases) {
    // skip pure chinese
    if (/[\u4e00-\u9fff]/.test(a)) continue;
    if (a) terms.add(a);
  }
  return [...terms];
}

for (const e of wiki) {
  const terms = romanTerms(e);
  let occ = 0, ch = 0;
  for (const t of terms) { occ += countAll(t); }
  ch = chapterHits(e.name) || chapterHits(terms[terms.length - 1]);
  e.occ = occ; e.chapters = ch;
}

// ---------- 4. Discovery passes ----------
const STOP = new Set([
  'Le','La','Les','Un','Une','Des','Du','De','Et','En','Dans','Sur','Pour','Par','Avec','Sans','Sous','Vers',
  'Mais','Ou','Or','Donc','Ni','Car','Que','Qui','Quand','Comment','Pourquoi','Où','Ce','Ces','Son','Sa','Ses',
  'Il','Elle','Ils','Elles','On','Nous','Vous','Je','Tu','Me','Te','Se','Mon','Ma','Mes','Ton','Ta','Tes',
  'Notre','Nos','Votre','Vos','Leur','Leurs','Tous','Tout','Toute','Toutes','Ne','Pas','Plus','Moins','Très',
  'Aussi','Encore','Puis','Alors','Apres','Après','Avant','Pendant','Depuis','Ici','Là','Loin','Près','Même',
  'Autre','Autres','Tel','Telle','Tels','Tel','Cet','Cette','Non','Oui','Bien','Mal','Toujours','Jamais',
  'Souvent','Parfois','Vite','Lent','Grand','Grande','Petit','Petite','Vieux','Vieille','Jeune','Beau','Belle',
  'Homme','Femme','Enfant','Garçon','Fille','Père','Mère','Frère','Sœur','Oncle','Tante','Roi','Seigneur',
  'Maître','Disciple','Ancêtre','Céleste','Immortel','Immortelle','Mortel','Mortelle','Ciel','Terre','Soleil',
  'Lune','Mer','Mont','Montagne','Chapitre','Tome','Livre','Note','Voir','Source','Image','Wang','Lin','Secte',
  'Clan','Tribu','Planète','Pays','Continent','Royaume','Système','Domaine','Mer','Forêt','Cité','Ville',
  'Qing','Suzaku','Tian','Yun','Lin','Mu','Sen','Nan','Dieu','Démon','Esprit','Âme','Sang','Feu','Eau','Vent',
  'Tonnerre','Glace','Pierre','Arbre','Porte','Pont','Tour','Palais','Pavillon','Grotte','Pic','Abîme','Vallée',
  'Nascent','Soul','Core','Foundation','Qi','Ascendant','Heaven','Void','Nirvana','Yang','Yin','Dao',
  'Chapter','Book','The','Of','And','To','In','On','At','For','With','A','An','It','He','She','They','His','Her',
  'Deux','Trois','Quatre','Cinq','Six','Sept','Huit','Neuf','Dix','Cent','Mille','Million','Milliard','Un','De',
]);

function uniqCounts(arr) {
  const m = new Map();
  for (const x of arr) m.set(x, (m.get(x) || 0) + 1);
  return m;
}

// 4a. Sects / Clans / Tribus — leading keyword
const sectRe = /\b((?:Secte|Clan|Tribu|Tribe|Faction|Ordre)\s+(?:(?:de\s+la\s+|de\s+l['’]\s*|du\s+|des\s+|de\s+)?\p{Lu}[\wà-ÿ'’-]+(?:\s+\p{Lu}[\wà-ÿ'’-]+){0,3}))/gu;
const sectHits = uniqCounts([...combined.matchAll(sectRe)].map(m => m[1].replace(/\s+/g, ' ').trim()));
// reverse: <Name> Sect/Clan (English)
const sectRe2 = /\b(\p{Lu}[\wà-ÿ'’-]+(?:\s+\p{Lu}[\wà-ÿ'’-]+){0,3})\s+(?:Sect|Clan|Tribe)\b/gu;
for (const m of combined.matchAll(sectRe2)) {
  const k = (m[1] + ' (anglais)').trim();
  sectHits.set(k, (sectHits.get(k) || 0) + 1);
}

// 4b. Lieux / Mondes / Royaumes — leading keyword
const lieuRe = /\b((?:Planète|Pays|Continent|Royaume|Système\s+stellaire|Mer|Montagne|Mont|Forêt|Lac|Vallée|Cité|Ville|Région|Gouffre|Grotte|Pic|Palais|Pavillon|Tour|Abîme|Domaine|Pont|Porte|Caverne|Désert|Océan|Fleuve|Rivière)\s+(?:(?:de\s+la\s+|de\s+l['’]\s*|du\s+|des\s+|de\s+)?\p{Lu}[\wà-ÿ'’-]+(?:\s+\p{Lu}[\wà-ÿ'’-]+){0,3}))/gu;
const lieuHits = uniqCounts([...combined.matchAll(lieuRe)].map(m => m[1].replace(/\s+/g, ' ').trim()));

// 4c. Personnages — two consecutive Capitalized words, frequency gated
const twoRe = /\b(\p{Lu}[a-zà-ÿ'’-]+(?:\s+\p{Lu}[a-zà-ÿ'’-]+){1,2})\b/gu;
const twoHits = new Map();
for (const m of combined.matchAll(twoRe)) {
  const phrase = m[1];
  const words = phrase.split(/\s+/);
  if (words.some(w => STOP.has(w))) continue;
  if (words.some(w => w.length < 3)) continue;
  if (/(?:^|\s)(?:[0-9]*ème|[0-9]*ère|[0-9]*ier|[0-9]*ième|ème|ère)\b/i.test(phrase)) continue;
  if (/^(?:[0-9]+|X+|I+|V+)\s/i.test(phrase)) continue;
  // require not sentence-initial noise: skip if a known cultivation/english realm word only
  twoHits.set(phrase, (twoHits.get(phrase) || 0) + 1);
}
const charHits = new Map([...twoHits].filter(([, c]) => c >= 10).sort((a, b) => b[1] - a[1]));

// 4d. Cultivation stages (realms) — canonical bilingual list, count French+English names
const REALMS = [
  ['Condensation du Qi','凝气','Ning Qi','Qi Condensation'],
  ['Établissement des Fondations','筑基','Zhu Ji','Foundation Establishment'],
  ['Formation du Noyau','结丹','Jie Dan','Core Formation'],
  ['Âme Naissante','元婴','Yuan Ying','Nascent Soul'],
  ["Formation de l'Âme",'化神','Hua Shen','Soul Formation'],
  ["Transformation de l'Âme",'婴变','Ying Bian','Soul Transformation'],
  ['Ascendant','问鼎','Wen Ding','Ascendant'],
  ['Yin Illusoire','阴虚','Yin Xu','Illusory Yin'],
  ['Yang Corporel','阳实','Yang Shi','Corporeal Yang'],
  ['Scruteur de Nirvana','窥涅','Kui Nie','Nirvana Scryer'],
  ['Purificateur de Nirvana','净涅','Jing Nie','Nirvana Cleanser'],
  ['Briseur de Nirvana','碎涅','Sui Nie','Nirvana Shatterer'],
  ["Désolation Céleste", "", "Heaven Blight", "Heaven's Blight"],
  ['Vide de Nirvana','空涅','Kong Nie','Nirvana Void'],
  ['Vide Spirituel','空灵','Kong Ling','Spirit Void'],
  ['Vide Arcane','空玄','Kong Xuan','Arcane Void'],
  ['Tribulation du Vide','空劫','Kong Jie','Void Tribulant'],
  ['Demi-Piétinement des Cieux','','Half Heaven Trampling','Half Heaven Trampling'],
  ['Piétinement des Cieux','踏天','Ta Tian','Heaven Trampling'],
  // Domaine Céleste alt
  ['Shang Xian','上仙','Shang Xian','Exalted Immortal'],
  ['Tian Xian','天仙','Tian Xian','Celestial Immortal'],
  ['Xian Wang','仙王','Xian Wang','Immortal King'],
  ['Xian Jun','仙君','Xian Jun','Immortal Lord'],
  ['Xian Di','仙帝','Xian Di','Immortal Emperor'],
  // royaumes spéciaux
  ['Shi Realm','极境','Shi Realm','Realm'],
  ['Ji Realm','极境','Ji Realm','Ji Realm'],
  ['Dao Realm','道境','Dao Realm','Dao Realm'],
];
const realmRows = [];
for (const [fr, zh, ...rest] of REALMS) {
  const terms = [fr, ...rest].filter(t => t && !/[\u4e00-\u9fff]/.test(t));
  let occ = 0;
  for (const t of terms) occ += countAll(t);
  realmRows.push({ fr, zh: zh || '', occ });
}

// ---------- 5. Assemble output ----------
const typeLabel = { personnage: 'Personnages', secte: 'Sectes & Clans', lieu: 'Royaumes, Lieux & Mondes', cultivation: 'Cultivation', auteur: 'Auteurs' };

// discovered sects not already a wiki sect
const wikiSectNames = new Set(wiki.filter(e => e.type === 'secte').flatMap(romanTerms).map(s => s.toLowerCase()));
const discSects = [...sectHits].filter(([k]) => !wikiSectNames.has(k.toLowerCase().replace(/\s+\(anglais\)$/, '').trim().toLowerCase()))
  .filter(([, c]) => c >= 5).sort((a, b) => b[1] - a[1]);

const wikiLieuNames = new Set(wiki.filter(e => e.type === 'lieu').flatMap(romanTerms).map(s => s.toLowerCase()));
const discLieux = [...lieuHits].filter(([k]) => !wikiLieuNames.has(k.toLowerCase()))
  .filter(([, c]) => c >= 5).sort((a, b) => b[1] - a[1]);

const wikiCharNames = new Set(wiki.flatMap(e => romanTerms(e)).map(s => s.toLowerCase()));
const discChars = [...charHits].filter(([k]) => !wikiCharNames.has(k.toLowerCase()))
  .sort((a, b) => b[1] - a[1]).slice(0, 220);

function mdEsc(s){ return String(s||'').replace(/\|/g,'\\|').replace(/\n/g,' '); }

let md = '';
md += `# Glossaire des entités — *Renegade Immortal*\n\n`;
md += `> Source : ${totalChapters} chapitres (` + `src/content/chapters` + `) + métadonnées wiki (` + `src/content/wiki` + `).\n`;
md += `> « Occ. » = nombre d'occurrences totales dans le corpus ; « Chap. » = nombre de chapitres distincts où l'entité apparaît.\n`;
md += `> Les entrées découvertes (hors wiki) sont déduites par motifs lexicaux et peuvent comporter du bruit.\n\n`;

// Personnages (wiki)
md += `## Personnages\n\n`;
md += `| Nom | Pinyin | Chinois | Alias | Occ. | Chap. |\n|---|---|---|---|---:|---:|\n`;
const chars = wiki.filter(e => e.type === 'personnage').sort((a, b) => b.occ - a.occ);
for (const e of chars) {
  md += `| **${mdEsc(e.name)}** | ${mdEsc(e.pinyin)} | ${mdEsc(e.chinese)} | ${mdEsc(e.aliases.filter(a=>!/[\u4e00-\u9fff]/.test(a)).join(' · '))} | ${e.occ} | ${e.chapters} |\n`;
}
md += `\n### Personnages découverts (hors wiki)\n\n`;
md += `| Nom | Occ. |\n|---|---:|\n`;
for (const [k, c] of discChars) md += `| ${mdEsc(k)} | ${c} |\n`;

// Sectes
md += `\n## Sectes & Clans\n\n`;
md += `| Nom | Pinyin | Chinois | Alias | Occ. | Chap. |\n|---|---|---|---|---:|---:|\n`;
const sects = wiki.filter(e => e.type === 'secte').sort((a, b) => b.occ - a.occ);
for (const e of sects) {
  md += `| **${mdEsc(e.name)}** | ${mdEsc(e.pinyin)} | ${mdEsc(e.chinese)} | ${mdEsc(e.aliases.filter(a=>!/[\u4e00-\u9fff]/.test(a)).join(' · '))} | ${e.occ} | ${e.chapters} |\n`;
}
md += `\n### Sectes & clans découverts (hors wiki)\n\n`;
md += `| Nom | Occ. |\n|---|---:|\n`;
for (const [k, c] of discSects) md += `| ${mdEsc(k)} | ${c} |\n`;

// Lieux / Royaumes
md += `\n## Royaumes, Lieux & Mondes\n\n`;
md += `| Nom | Pinyin | Chinois | Alias | Occ. | Chap. |\n|---|---|---|---|---:|---:|\n`;
const lieus = wiki.filter(e => e.type === 'lieu').sort((a, b) => b.occ - a.occ);
for (const e of lieus) {
  md += `| **${mdEsc(e.name)}** | ${mdEsc(e.pinyin)} | ${mdEsc(e.chinese)} | ${mdEsc(e.aliases.filter(a=>!/[\u4e00-\u9fff]/.test(a)).join(' · '))} | ${e.occ} | ${e.chapters} |\n`;
}
md += `\n### Lieux & mondes découverts (hors wiki)\n\n`;
md += `| Nom | Occ. |\n|---|---:|\n`;
for (const [k, c] of discLieux) md += `| ${mdEsc(k)} | ${c} |\n`;

// Cultivation realms
md += `\n## Stades de cultivation (Royaumes de cultivation)\n\n`;
md += `| Stade (FR) | Chinois | Occ. |\n|---|---|---:|\n`;
for (const r of realmRows.sort((a, b) => b.occ - a.occ)) {
  md += `| ${mdEsc(r.fr)} | ${mdEsc(r.zh)} | ${r.occ} |\n`;
}

// Auteurs
const auteurs = wiki.filter(e => e.type === 'auteur');
if (auteurs.length) {
  md += `\n## Auteurs\n\n`;
  for (const e of auteurs) md += `- **${mdEsc(e.name)}** — ${mdEsc(e.pinyin)}\n`;
}

md += `\n---\n\n_Généré par \`scripts/extract-entities.mjs\` le ${new Date().toISOString().slice(0,10)} — ${totalChapters} chapitres, ${wiki.length} entrées wiki._\n`;

await writeFile(OUT, md, 'utf8');
console.error(`written: ${OUT}`);
console.error(`wiki entities: ${wiki.length} | disc chars: ${discChars.length} | disc sects: ${discSects.length} | disc lieux: ${discLieux.length}`);
