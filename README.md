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

## Crédits

- **Œuvre originale** : *Renegade Immortal* (Xian Ni / 仙逆) par **Er Gen** (耳根)
- **Traduction française v4** : traducteurs anonymes de la communauté FR
- **Wiki & images personnages** : [Xian Ni Fandom Wiki](https://xian-ni.fandom.com/wiki/Xian_Ni_Wikia) — CC BY-SA
- **OST instrumentale** : [ANimeMuzic sur YouTube](https://www.youtube.com/watch?v=bXJKwYzz5mw)

## Licence

Le **code** de ce site est sous licence MIT.
Le **contenu textuel** (chapitres, wiki) appartient à ses auteurs respectifs — voir les crédits ci-dessus.
