import { getCollection, render, type CollectionEntry } from 'astro:content';

export const FEATURED_PERSONNAGES = [
  'wang-lin', 'situ-nan', 'li-muwan', 'tuo-sen', 'all-seer', 'sima-mo',
  'master-devil-god', 'zhou-yi', 'wang-ping', 'blood-ancestor', 'ancient-god',
];

export const FEATURED_LIEUX = [
  'sea-of-devils', 'planet-suzaku', 'chu-country', 'country-of-zhao',
  'tian-yun', 'sky-demon-country', 'outer-realm', 'foreign-battleground',
  'forest-ruins', 'ancient-demon-city', 'cloud-sea-star-system',
  'allheaven-star-system',
];

export interface LoreSection {
  type: 'personnage' | 'lieu' | 'secte' | 'cultivation';
  segment: string;
  label: string;
  singular: string;
  active: string;
}

export const LORE_SECTIONS: LoreSection[] = [
  { type: 'personnage', segment: 'personnages', label: 'Personnages', singular: 'Personnage', active: 'personnages' },
  { type: 'lieu', segment: 'lieux', label: 'Lieux', singular: 'Lieu', active: 'lieux' },
  { type: 'secte', segment: 'sectes-clans', label: 'Sectes & Clans', singular: 'Secte / Clan', active: 'sectes' },
  { type: 'cultivation', segment: 'cultivation', label: 'Cultivation', singular: 'Cultivation', active: 'cultivation' },
];

export function loreSectionByType(type: string): LoreSection | undefined {
  return LORE_SECTIONS.find(s => s.type === type);
}

export function chapterSlug(entry: CollectionEntry<'chapters'>): string {
  return entry.id.replace(/\.md$/, '').split('/').pop() as string;
}

export function wikiSlug(entry: CollectionEntry<'wiki'>): string {
  return entry.id.replace(/\.md$/, '').split('/').pop() as string;
}

export async function getChaptersSorted(): Promise<CollectionEntry<'chapters'>[]> {
  const all = await getCollection('chapters');
  return all.sort((a, b) => a.data.n - b.data.n);
}

export async function getBooksSorted(): Promise<CollectionEntry<'books'>[]> {
  const all = await getCollection('books');
  return all.sort((a, b) => a.data.book - b.data.book);
}

export async function getWikiByType(type: string): Promise<CollectionEntry<'wiki'>[]> {
  const all = await getCollection('wiki');
  return all
    .filter(e => e.data.type === type)
    .sort((a, b) => a.data.name.localeCompare(b.data.name, 'fr'));
}

export function featuredSlugs(type: string): string[] | null {
  if (type === 'personnage') return FEATURED_PERSONNAGES;
  if (type === 'lieu') return FEATURED_LIEUX;
  return null;
}

export async function getLoreEntries(type: string): Promise<CollectionEntry<'wiki'>[]> {
  const slugs = featuredSlugs(type);
  if (!slugs) return getWikiByType(type);
  const all = await getWikiByType(type);
  const ordered: CollectionEntry<'wiki'>[] = [];
  for (const s of slugs) {
    const found = all.find(e => wikiSlug(e) === s);
    if (found) ordered.push(found);
  }
  return ordered;
}

export interface ChapterMenuItem {
  n: number;
  slug: string;
  title: string;
  book: number;
  bookTitle: string;
}

export async function getChapterMenu(): Promise<ChapterMenuItem[]> {
  const all = await getChaptersSorted();
  return all.map(c => ({
    n: c.data.n,
    slug: chapterSlug(c),
    title: c.data.title,
    book: c.data.book,
    bookTitle: c.data.bookTitle,
  }));
}

export interface PreparedLore {
  slug: string;
  name: string;
  title: string;
  image: string | null;
  categories: string[];
  url: string | null;
  Content: any;
  headings: any[];
}

export async function prepareLore(entry: CollectionEntry<'wiki'>): Promise<PreparedLore> {
  const { Content, headings } = await render(entry);
  return {
    slug: wikiSlug(entry),
    name: entry.data.name,
    title: entry.data.title,
    image: entry.data.image || null,
    categories: entry.data.categories || [],
    url: entry.data.url || null,
    Content,
    headings,
  };
}
