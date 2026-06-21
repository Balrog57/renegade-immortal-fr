# Renegade Immortal FR

Site web **Single-Page Application** dédié à la traduction française et au wiki du web novel **Renegade Immortal (Xian Ni / 仙逆)** écrit par Er Gen.

🌐 **Site en ligne** : https://balrog57.github.io/renegade-immortal-fr/

## Contenu

- **2,084 chapitres** de la traduction française (Books 1 à 13)
- **2,285 pages** du wiki Fandom officiel (Xian Ni Wikia)
- **3 personnages** détaillés (Wang Lin, Situ Nan, Li Muwan)
- **Univers** : système de cultivation, géographie, Perle défiant les Cieux
- **Musique d'ambiance** : OST Xian Ni instrumentale via YouTube IFrame API
- **Recherche live** dans les chapitres et le wiki
- **Filtres** par tome (13 Books) et par catégorie wiki

## Structure du repo

```
.
├── README.md                    # ce fichier
├── index.html                   # redirect → SPA
├── renegade-immortal-fr.html    # SPA complète (1.7 MB, tout inliné)
├── .nojekyll                    # désactive Jekyll (pour les noms avec _)
├── assets/                      # index JSON (chargés à l'ouverture)
│   ├── data.json                #   données persos Fandom
│   ├── chapters.json            #   index 2,084 chapitres
│   └── wiki.json                #   index 2,285 pages wiki
├── traduction/                  # 13 Books (sous-dossiers) — traduction FR
│   ├── Book 1 - The Mediocre Youth/
│   ├── Book 2 - The Bloody Image of Cultivation/
│   ├── ...
│   └── Book 13 - Light of the coming end/
└── wiki/                        # 2,349 pages wiki Fandom (JSON par page)
    ├── Wang Lin.json
    ├── Situ Nan.json
    ├── ...
    └── (autres pages)
```

## Stack

- **HTML / CSS / JavaScript vanilla** (aucune dépendance runtime, sauf Google Fonts)
- Polices : Cinzel, Cormorant Garamond, Noto Serif (Google Fonts)
- Images personnages : [Xian Ni Fandom Wiki](https://xian-ni.fandom.com/) (CC BY-SA)
- Musique : [ANimeMuzic — Renegade Immortal Xian Ni 仙逆 All Instrument OST](https://www.youtube.com/watch?v=bXJKwYzz5mw)

## Crédits et licences

### Œuvre originale
**Renegade Immortal (Xian Ni / 仙逆)** — © Er Gen (耳根). Tous droits réservés à l'auteur et à ses ayants droit.

### Traduction française
**© 2024–2026 Balrog57**. La traduction française de l'œuvre en dossier `traduction/` est mon travail personnel (Balrog57 = auteur du repo). Licence : **CC BY-NC-SA 4.0** — partage autorisé avec attribution et même licence, usage commercial interdit. Pour toute republication ou usage commercial, contactez-moi.

### Wiki et images
Contenu des pages et images de `wiki/` issues du [Xian Ni Fandom Wiki](https://xian-ni.fandom.com/wiki/Xian_Ni_Wikia) — **CC BY-SA** (avec attribution aux contributeurs Fandom). Chaque page wiki a un lien `Voir sur Fandom Wiki →` pointant vers sa source.

### Code
Le code source du site (`renegade-immortal-fr.html`, `index.html`, scripts) est sous licence **MIT** — libre d'usage, modification, redistribution avec mention de l'auteur original.

## 🚀 Déploiement

Le site est hébergé sur **GitHub Pages** à l'adresse :

🌐 **https://balrog57.github.io/renegade-immortal-fr/**

### Mises à jour automatiques

À chaque `git push` sur la branche `main`, GitHub Pages redéploie automatiquement en 20-60 secondes.

### Setup initial (déjà fait)

1. Repo : https://github.com/Balrog57/renegade-immortal-fr (public)
2. Settings → Pages → Source : `Deploy from a branch` → `main` / `/` (root)
3. Le fichier `.nojekyll` à la racine désactive Jekyll (nécessaire car certains fichiers contiennent des `_`)
4. URL par défaut : `https://balrog57.github.io/renegade-immortal-fr/`

### Domaine custom (optionnel)

Settings → Pages → Custom domain → ajouter un domaine. Si le domaine est chez un registrar externe, ajouter un CNAME `balrog57.github.io` ou un A record vers les IPs GitHub Pages.

## ✏️ Corriger une traduction

### Option A — Directement sur github.com (le plus rapide)

1. Ouvrir https://github.com/Balrog57/renegade-immortal-fr
2. Naviguer vers le chapitre : `traduction/Book X - .../NNNN - Chapter ...txt`
3. Clic ✏️ (Edit this file)
4. Corriger
5. **Commit changes** → message clair → **Commit directly to the main branch**
6. GitHub Pages redéploie automatiquement en 20-60 secondes

### Option B — Pull Request (traçabilité)

1. Fork du repo
2. Modifier sur la fork
3. Ouvrir une PR contre `Balrog57/renegade-immortal-fr:main`
4. Review + merge → redéploiement auto

### Workflow local

```bash
git clone https://github.com/Balrog57/renegade-immortal-fr.git
cd renegade-immortal-fr
# Lancer un serveur local (requis pour les fetches chapitres/wiki)
python -m http.server 8000
# Éditer un fichier .txt dans traduction/...
# Reload http://localhost:8000/renegade-immortal-fr.html
git add . && git commit -m "fix(ch.123): correction typo"
git push origin main
# → GitHub Pages redéploie en 20-60s
```

> Le double-clic direct sur le HTML fonctionne pour la navigation, mais le chargement à la demande des chapitres et des pages wiki nécessite un serveur HTTP (les navigateurs bloquent `fetch()` sur `file://`).
