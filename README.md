# Renegade Immortal FR

Site web **Single-Page Application** dédié à la traduction française et au wiki du web novel **Renegade Immortal (Xian Ni / 仙逆)** écrit par Er Gen.

🌐 **Site en ligne** : https://balrog57.github.io/renegade-immortal-fr/

## Contenu

- **2,084 chapitres** de la traduction française v4 (Books 1 à 13)
- **2,285 pages** du wiki Fandom officiel (Xian Ni Wikia)
- **3 personnages** détaillés (Wang Lin, Situ Nan, Li Muwan)
- **Univers** : système de cultivation, géographie, Perle défiant les Cieux
- **Musique d'ambiance** : OST Xian Ni instrumentale via YouTube IFrame API
- **Recherche live** dans les chapitres et le wiki
- **Filtres** par tome (13 Books) et par catégorie wiki

## Stack

- HTML / CSS / JavaScript **vanilla** (aucune dépendance runtime)
- Polices : Cinzel, Cormorant Garamond, Noto Serif (Google Fonts)
- Images personnages : [Xian Ni Fandom Wiki](https://xian-ni.fandom.com/) (CC BY-SA)
- Musique : [ANimeMuzic — Renegade Immortal Xian Ni 仙逆 All Instrument OST](https://www.youtube.com/watch?v=bXJKwYzz5mw)

## Lancer en local

```bash
# Clone
git clone https://github.com/Balrog57/renegade-immortal-fr.git
cd renegade-immortal-fr

# Lancer un mini serveur (requis pour les fetches chapitres/wiki)
python -m http.server 8000

# Ouvrir dans le navigateur
open http://localhost:8000/renegade-immortal-fr.html
```

> Le double-clic direct sur le HTML fonctionne pour la navigation, mais le chargement à la demande des chapitres et des pages wiki nécessite un serveur HTTP (les navigateurs bloquent `fetch()` sur `file://`).

## 🚀 Déploiement sur Cloudflare Pages (gratuit, repo privé OK)

GitHub Free ne permet pas Pages sur un repo privé. Ce repo utilise donc **Cloudflare Pages** comme hébergement public, qui accepte les repos privés gratuitement et illimité.

### Setup initial (une seule fois)

1. Aller sur https://dash.cloudflare.com/ → Sign up (gratuit, email + mdp)
2. Une fois connecté, menu latéral → **Workers & Pages** → **Pages** → **Create application** → **Pages** → **Connect to Git**
3. Autoriser Cloudflare à accéder au repo `Balrog57/renegade-immortal-fr`
4. Sélectionner le repo, branche `main`
5. **Build settings** :
   - **Framework preset** : *None*
   - **Build command** : (laisser vide)
   - **Build output directory** : `/`
6. **Save and Deploy** → 1er build prend ~1 min, ensuite l'URL `https://renegade-immortal-fr.pages.dev` est active

### Mises à jour automatiques

À chaque `git push` sur `main`, Cloudflare redéploie automatiquement en 30-60 secondes.

### Domaine custom (optionnel)

Dans Cloudflare Pages → Custom domains → ajouter `renegade-immortal.fr` (ou autre). DNS auto-géré si le domaine est sur Cloudflare.

## ✏️ Corriger une traduction

Deux options :

### Option A — Directement sur github.com (le plus rapide)

1. Ouvrir https://github.com/Balrog57/renegade-immortal-fr
2. Naviguer vers le chapitre à corriger : `traduction/v4/Book X - .../NNNN - Chapter ...txt`
3. Cliquer sur l'icône ✏️ (Edit this file)
4. Faire les corrections
5. **Commit changes** → message + **Commit directly to the main branch**
6. Cloudflare redéploie automatiquement en 30-60s

### Option B — Pull Request (pour traçabilité)

1. Fork du repo
2. Modifier sur la fork
3. Ouvrir une PR contre `Balrog57/renegade-immortal-fr:main`
4. Review + merge → redéploiement auto

### Workflow de test local avant de pusher

```bash
git clone https://github.com/Balrog57/renegade-immortal-fr.git
cd renegade-immortal-fr
# Lancer un serveur local
python -m http.server 8000
# Éditer un fichier .txt dans traduction/v4/...
# Reload http://localhost:8000/renegade-immortal-fr.html pour voir le résultat
git add . && git commit -m "fix(ch.123): correction typo"
git push origin main
# → Cloudflare redéploie en 30-60s
```

## Crédits

- **Œuvre originale** : *Renegade Immortal* (Xian Ni / 仙逆) par **Er Gen** (耳根)
- **Traduction française v4** : traducteurs anonymes de la communauté FR
- **Wiki & images personnages** : [Xian Ni Fandom Wiki](https://xian-ni.fandom.com/wiki/Xian_Ni_Wikia) — CC BY-SA
- **OST instrumentale** : [ANimeMuzic sur YouTube](https://www.youtube.com/watch?v=bXJKwYzz5mw)

## Licence

Le **code** de ce site est sous licence MIT.
Le **contenu textuel** (chapitres, wiki) appartient à ses auteurs respectifs — voir les crédits ci-dessus.
