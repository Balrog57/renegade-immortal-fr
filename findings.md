# Findings

## Structure du projet

```
renegade-immortal-fr/
├── src/
│   ├── components/       # Nav.astro, Footer.astro, LoreEntry.astro, LoreSection.astro
│   ├── content/          # Collections Astro
│   │   ├── chapters/     # ~2 088 fichiers .md (13 tomes)
│   │   ├── books/        # 13 fichiers .md (1 par tome)
│   │   ├── wiki/         # 4 fichiers .md (personnage, cultivation, secte, lieu)
│   │   └── site/         # Page d'accueil (home.md)
│   ├── layouts/          # Base.astro, Reader.astro
│   ├── lib/              # data.ts, book-summaries.ts
│   ├── pages/            # Routes Astro (index, chapitres/, lecture/, livres/, etc.)
│   └── styles/           # global.css (Tailwind @import + design tokens)
├── public/wiki/images/   # Images copiées par prebuild
├── wiki/images/          # Source originale des images (617 webp)
├── dist/                 # Build output (déjà existant)
├── .pages.yml            # Pages CMS config
├── astro.config.mjs      # Config Astro
├── package.json          # Astro 5.15, TailwindCSS 4.1
└── .github/workflows/deploy.yml  # GitHub Actions
```

## Config critique

### astro.config.mjs (À CORRIGER)
```js
site: 'https://marc-github.example',     // ← PLACEHOLDER, doit être 'https://balrog57.github.io'
base: '/renegade-immortal-fr',            // ✅ correct pour GitHub Pages subpath
trailingSlash: 'always',                  // ✅
build: { format: 'directory' },           // ✅
```

### deploy.yml (GitHub Actions)
- Build sur ubuntu-latest avec Node 20
- `npm ci` → `npm run build` → upload `dist/` → deploy-pages
- Cible GitHub Pages avec `actions/upload-pages-artifact@v3` et `actions/deploy-pages@v4`
- Source Pages doit être réglée sur "GitHub Actions" (Settings → Pages)

## Contenu

| Collection | Fichiers | Statut |
|------------|----------|--------|
| chapters   | ~2 088   | ✅ Complet (13 tomes) |
| books      | 13       | ✅ Complet |
| wiki       | 4        | ⚠️ Seulement 4 pages (ancien site en avait 2 285) |
| site       | 1        | ✅ home.md |

## Images
- Source : `wiki/images/` — 617 fichiers
- Copiées vers `public/wiki/images/` via `scripts/copy-images.mjs` (prebuild)
- 624 fichiers dans le public (copie récente)

## Dépendances
- astro ^5.15.0
- @astrojs/check ^0.9.4
- @tailwindcss/vite ^4.1.0
- tailwindcss ^4.1.0
- typescript ^5.6.0
