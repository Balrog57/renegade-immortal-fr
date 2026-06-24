/**
 * Fusionne les sous-chapitres a/b/.1 dans le fichier principal du chapitre.
 * - 0717a + 0717b -> 0717 (nouveau)
 * - 0975a + 0975b -> 0975 (nouveau)
 * - 1022.1 -> ajoute a la fin de 1022
 * - 1455a + 1455b -> 1455 (nouveau)
 * - 1740a + 1740b -> 1740 (nouveau)
 *
 * Met aussi a jour build_parts/chapters-data.json pour les nouvelles entrees.
 */
import { readFile, writeFile, readdir, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const TRAD = join(ROOT, 'traduction');

async function readChapterBody(file) {
  const content = await readFile(file, 'utf-8');
  // Saute la 1re ligne (titre) et la 2e (vide)
  const lines = content.split('\n');
  return lines.slice(2).join('\n').trim();
}

async function readTitle(file) {
  const content = await readFile(file, 'utf-8');
  return content.split('\n')[0].trim();
}

async function mergePair(fileA, fileB, outFile, outTitle) {
  const bodyA = await readChapterBody(fileA);
  const bodyB = await readChapterBody(fileB);
  const text = `${outTitle}\n\n${bodyA}\n\n${bodyB}\n`;
  await writeFile(outFile, text, 'utf-8');
  console.log(`  -> ${outFile}`);
}

async function appendToFile(targetFile, sourceFile, separator = '\n\n') {
  const body = await readChapterBody(sourceFile);
  const existing = await readFile(targetFile, 'utf-8');
  // Enlever le titre de la 2e source et concatener
  const text = existing.trimEnd() + separator + body + '\n';
  await writeFile(targetFile, text, 'utf-8');
  console.log(`  -> ${targetFile} (appended)`);
}

async function main() {
  console.log('=== Fusion des sous-chapitres a/b/.1 ===\n');

  const merges = [
    {
      n: 717,
      book: 7,
      bookTitle: 'Fame Shakes Allheaven Star System',
      a: 'Book 7 - Fame Shakes Allheaven Star System/0717a - Chapter 717 - Escaping alive (1).txt',
      b: 'Book 7 - Fame Shakes Allheaven Star System/0717b - Chapter 717 (2) - Thunder Prison.txt',
      out: 'Book 7 - Fame Shakes Allheaven Star System/0717 - Chapter 717 - Escaping alive.txt',
      title: 'Chapitre 717 - S\'echapper vivant',
      en: 'Chapter 717 - Escaping alive',
    },
    {
      n: 975,
      book: 8,
      bookTitle: 'Alliance\'s Secret',
      a: 'Book 8 - Alliance\'s Secret/0975a - Chapter 975 - Frightened Spirit.txt',
      b: 'Book 8 - Alliance\'s Secret/0975b - Chapter 975.1 - Heaven Defying Bead Opens Once More (1).txt',
      out: 'Book 8 - Alliance\'s Secret/0975 - Chapter 975 - Frightened Spirit.txt',
      title: 'Chapitre 975 - Esprit effraye',
      en: 'Chapter 975 - Frightened Spirit',
    },
    {
      n: 1455,
      book: 9,
      bookTitle: 'Peak of the Cloud Sea',
      a: 'Book 9 - Peak of the Cloud Sea/1455a - Chapter 1455 - Killing Move!.txt',
      b: 'Book 9 - Peak of the Cloud Sea/1455b - Chapter 1455 - Giant Hand Appears Once More.txt',
      out: 'Book 9 - Peak of the Cloud Sea/1455 - Chapter 1455 - Killing Move!.txt',
      title: 'Chapitre 1455 - Coup fatal',
      en: 'Chapter 1455 - Killing Move!',
    },
    {
      n: 1740,
      book: 11,
      bookTitle: 'Mysteries of the Ancient Era',
      a: 'Book 11 - Mysteries of the Ancient Era/1740a - Chapter 1740 - Double Elements Armor (1).txt',
      b: 'Book 11 - Mysteries of the Ancient Era/1740b - Chapter 1740 (2) - Double Elements Armor (2).txt',
      out: 'Book 11 - Mysteries of the Ancient Era/1740 - Chapter 1740 - Double Elements Armor.txt',
      title: 'Chapitre 1740 - Armure aux doubles elements',
      en: 'Chapter 1740 - Double Elements Armor',
    },
  ];

  for (const m of merges) {
    const fileA = join(TRAD, m.a);
    const fileB = join(TRAD, m.b);
    const outFile = join(TRAD, m.out);
    if (!existsSync(fileA) || !existsSync(fileB)) {
      console.log(`  ! skip ${m.n}: fichiers manquants`);
      continue;
    }
    await mergePair(fileA, fileB, outFile, m.title);
  }

  // 1022.1 -> append to 1022
  const file1022 = join(TRAD, "Book 8 - Alliance's Secret/1022 - Chapter 1022 - Break (1).txt");
  const file10221 = join(TRAD, "Book 8 - Alliance's Secret/1022.1 - Chapter 1022.1 - Break (2).txt");
  if (existsSync(file1022) && existsSync(file10221)) {
    await appendToFile(file1022, file10221);
  }

  console.log('\n=== Mise a jour de chapters-data.json ===\n');

  const jsonPath = join(ROOT, 'build_parts', 'chapters-data.json');
  const data = JSON.parse(await readFile(jsonPath, 'utf-8'));

  for (const m of merges) {
    const newEntry = {
      n: m.n,
      title: m.title.replace(/^Chapitre \d+ - /, '').replace(/^Chapitre \d+ \(2\) - /, ''),
      book: m.book,
      bookTitle: m.bookTitle,
      en: m.en,
      file: 'traduction/' + m.out.replace(/\\/g, '/'),
    };
    // Chercher si une entree avec le meme n existe deja, sinon l'ajouter
    const existing = data.findIndex(d => d.n === m.n);
    if (existing >= 0) {
      console.log(`  ~ n=${m.n} existe deja (remplace)`);
      data[existing] = newEntry;
    } else {
      console.log(`  + n=${m.n} ajoute (book ${m.book})`);
      // Inserer en ordre de n
      const idx = data.findIndex(d => d.n > m.n);
      if (idx >= 0) data.splice(idx, 0, newEntry);
      else data.push(newEntry);
    }
  }

  await writeFile(jsonPath, JSON.stringify(data, null, 2), 'utf-8');
  console.log(`\n  Total dans JSON: ${data.length}`);
  console.log('\n=== Termine ===');
}

main().catch(e => { console.error(e); process.exit(1); });
