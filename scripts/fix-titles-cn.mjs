/**
 * Corrige les titres FR des chapitres qui ne correspondent pas au titre
 * chinois officiel de Qidian. Ne touche PAS au contenu (body).
 *
 * Source de vérité : catalog Qidian (book 1264634) — 仙逆 par 耳根.
 */
import { readFile, writeFile, readdir, stat } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const CHAPTERS = join(ROOT, 'src', 'content', 'chapters');

// Corrections prioritaires (issues du rapport de comparaison CN/FR)
// Format: [n, newTitle, newEn (optional)]
// On ne touche QUE les titres (frontmatter `title:` et `en:`).
// Le contenu (body) reste intact.
const FIXES = [
  // Chapitres "更" — marqueurs de publication, pas des titres
  [1056, 'Première mise à jour (I)', 'First Update (I)'],
  [1057, 'Deuxième mise à jour (II)', 'Second Update (II)'],
  [1058, 'Troisième mise à jour (III)', 'Third Update (III)'],
  [1059, 'Quatrième mise à jour (IV)', 'Fourth Update (IV)'],
  [1060, 'Cinquième mise à jour (V)', 'Fifth Update (V)'],
  [1061, 'Sixième mise à jour (VI)', 'Sixth Update (VI)'],
  [1066, 'Septième mise à jour (VII)', 'Seventh Update (VII)'],
  [1067, 'Huitième mise à jour (VIII)', 'Eighth Update (VIII)'],
  [1068, 'Neuvième mise à jour (IX)', 'Ninth Update (IX)'],
  [1069, 'Dixième mise à jour (X)', 'Tenth Update (X)'],
  [1070, 'Onzième mise à jour (XI)', 'Eleventh Update (XI)'],
  [1082, 'Douzième mise à jour (XII)', 'Twelfth Update (XII)'],
  [1101, 'Treizième mise à jour (XIII)', 'Thirteenth Update (XIII)'],
  [1102, 'Quatorzième mise à jour (XIV)', 'Fourteenth Update (XIV)'],
  [1113, 'Quinzième mise à jour (XV)', 'Fifteenth Update (XV)'],
  [1114, 'Seizième mise à jour (XVI)', 'Sixteenth Update (XVI)'],
  [1115, 'Dix-septième mise à jour (XVII)', 'Seventeenth Update (XVII)'],
  [1116, 'Dix-huitième mise à jour (XVIII)', 'Eighteenth Update (XVIII)'],
  [1117, 'Dix-neuvième mise à jour (XIX)', 'Nineteenth Update (XIX)'],
  [1131, 'Vingtième mise à jour (XX)', 'Twentieth Update (XX)'],

  // Traductions sémantiquement erronées (priorité haute)
  [7,    'La lettre laissée', 'The Letter Left Behind'],
  [17,   'La voie des immortels', 'The Path of Immortals'],
  [21,   'La saisie de l\'esprit', 'Seizing the Spirit'],
  [24,   'L\'entraînement', 'The Training'],
  [33,   'L\'incantation', 'The Incantation'],
  [51,   'Quatorzième niveau de condensation du Qi ?', 'Fourteenth Level of Qi Condensation?'],
  [75,   'Retrouvailles avec un vieil ami', 'Reunited with an Old Friend'],
  [149,  'Formation du Noyau (Finale)', 'Core Formation (Finale)'],
  [171,  'Le jade laissé par Li Muwan', 'The Jade Slip Left by Li Muwan'],
  [228,  'La capture d\'une bête de compagnie', 'Capturing a Spirit Pet'],
  [434,  'Le veux-tu ?', 'Will You?'],
  [642,  'La sagesse de Wang Lin', 'Wang Lin\'s Wisdom'],
  [789,  'Passer à l\'action', 'Strike'],
  [823,  'Yao Changkong', 'Yao Changkong'],
  [1127, 'La mort de l\'avatar', 'The Death of the Avatar'],
  [1264, 'Un changement saisissant !', 'A Startling Change!'],
  [1322, 'Les flammes d\'encens des disciples', 'The Disciples\' Incense Flames'],
  [1455, 'La main géante réapparaît !', 'The Giant Hand Returns!'],
  [1530, 'L\'arc de Li Guang', 'Li Guang\'s Bow'],
  [1740, 'Frère aîné Ma !', 'Senior Brother Ma!'],
  [1827, 'Quatre mots !', 'Four Words!'],
  [2054, 'Trois pertes, deux calamités', 'Three Losses, Two Calamities'],
];

let fixed = 0;
let notFound = 0;

async function processDir(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = join(dir, e.name);
    if (e.isDirectory()) {
      await processDir(full);
    } else if (e.name.endsWith('.md')) {
      const content = await readFile(full, 'utf-8');
      const m = content.match(/^n:\s*(\d+)/m);
      if (!m) continue;
      const n = parseInt(m[1], 10);
      const fix = FIXES.find(f => f[0] === n);
      if (!fix) continue;
      const [, newTitle, newEn] = fix;
      let updated = content;
      updated = updated.replace(/^title:.*$/m, `title: ${newTitle}`);
      if (newEn) {
        updated = updated.replace(/^en:.*$/m, `en: ${newEn}`);
      }
      await writeFile(full, updated, 'utf-8');
      console.log(`  n=${n}: -> "${newTitle}"`);
      fixed++;
    }
  }
}

await processDir(CHAPTERS);
console.log(`\nFixed: ${fixed} | Not found in FIXES: 0 (we only process what's in the list)`);
