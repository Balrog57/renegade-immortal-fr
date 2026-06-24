import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';

// Wiki type enum: ce qui définit une fiche lore (personnage / lieu / secte / cultivation)
const wikiType = z.enum(['personnage', 'lieu', 'secte', 'cultivation']);

const chapters = defineCollection({
  loader: glob({
    pattern: '**/*.md',
    base: './src/content/chapters',
    generateId: ({ entry }) => entry.replace(/\.md$/, ''),
  }),
  schema: z.object({
    n: z.number(),
    title: z.string(),
    book: z.number(),
    bookTitle: z.string(),
    en: z.string().optional(),
  })
});

const books = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/books' }),
  schema: z.object({
    book: z.number(),
    title: z.string(),
    cover: z.string().optional(),
    chaptersCount: z.number().optional(),
    rangeStart: z.number().optional(),
    rangeEnd: z.number().optional(),
    summary: z.string().optional(),
    majorEvents: z.array(z.string()).optional(),
    introducedCharacters: z.array(z.string()).optional(),
  })
});

const wiki = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/wiki' }),
  schema: z.object({
    name: z.string(),
    title: z.string(),
    type: wikiType,
    categories: z.array(z.string()).default([]),
    image: z.string().optional(),
    url: z.string().optional(),
  })
});

const site = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/site' }),
  schema: z.object({
    title: z.string(),
    section: z.string(),
    order: z.number().default(0),
  })
});

export const collections = { chapters, books, wiki, site };