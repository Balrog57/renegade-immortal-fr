# Plan : Contrôle et Amélioration de la Traduction Xianxia

> **Pour Hermes :** Exécuter phase par phase. Chaque phase produit un livrable vérifiable.

**Objectif :** Utiliser Wuxiaworld (source anglaise) et NovelFrance (traduction fan FR indépendante) comme références croisées pour auditer et améliorer la traduction FR des 2088 chapitres sur le site `renegade-immortal-fr`.

**Architecture :** Approche en 4 phases — (1) normalisation terminologique globale, (2) audit chapitre par chapitre avec scoring, (3) correction des chapitres problématiques, (4) validation finale.

**Sources :**
- `C:\Users\Marc\Downloads\Renegade Immortal\wuxiaworld\` — 2093 .txt, source anglaise de référence
- `C:\Users\Marc\Documents\1G1R\_Programmation\renegade-immortal-fr\novelfrance\` — 2090 .md, traduction fan FR indépendante
- `C:\Users\Marc\Documents\1G1R\_Programmation\renegade-immortal-fr\src\content\chapters\` — 2088 .md, traduction actuelle du site

**Diagnostic initial :**
- Couverture complète (2088/2088), pas de chapitres tronqués
- Site et NovelFrance sont deux traductions **indépendantes** (similarité médiane 3.5%)
- Terminologie globalement cohérente mais variations mineures (Dao/DAO, Ancien/Antique, Démon/Démoniaque)
- Tailles cohérentes (médiane ~11 700 caractères)

---

## Phase 1 : Normalisation terminologique

**Objectif :** Établir et appliquer un glossaire de référence unifié sur l'ensemble des 2088 chapitres.

### Task 1.1 : Extraire le glossaire de référence

Créer `scripts/glossary.json` à partir de :
- `build_parts/wiki-data.json` (2285 entrées Fandom)
- Analyse des termes récurrents dans les chapitres site
- Comparaison avec NovelFrance pour les choix de traduction

**Fichier :** `scripts/glossary.json`

Format :
```json
{
  "term_en": {
    "fr": "traduction canonique",
    "aliases": ["variante1", "variante2"],
    "category": "cultivation|personnage|lieu|technique|concept"
  }
}
```

### Task 1.2 : Script d'audit terminologique

Créer `scripts/audit-terminology.py` qui :
- Parcourt tous les chapitres
- Détecte les termes hors-glossaire
- Produit un rapport `reports/terminology-issues.json`

### Task 1.3 : Script de correction terminologique

Créer `scripts/fix-terminology.py` qui :
- Applique les corrections du glossaire (remplacement des alias par le terme canonique)
- Respecte la casse (majuscule en début de phrase)
- Produit un diff pour revue humaine

### Task 1.4 : Appliquer la normalisation

Exécuter le script sur les 2088 chapitres, valider par échantillonnage.

---

## Phase 2 : Audit chapitre par chapitre

**Objectif :** Scorer chaque chapitre sur fidélité, qualité littéraire et cohérence.

### Task 2.1 : Script de scoring

Créer `scripts/score-chapters.py` qui pour chaque chapitre :
- Compare le contenu site vs wuxiaworld (fidélité : omissions, ajouts, contresens)
- Compare le contenu site vs NovelFrance (détection de divergences suspectes)
- Vérifie la cohérence terminologique interne
- Produit un score composite et un rapport

**Métriques :**
- `fidelity_score` (0-100) : alignement avec la source anglaise
- `quality_score` (0-100) : qualité du français, fluidité
- `terminology_score` (0-100) : respect du glossaire
- `completeness_score` (0-100) : ratio de contenu vs source

### Task 2.2 : Exécuter l'audit complet

Lancer le scoring sur les 2088 chapitres → `reports/chapter-scores.json`

### Task 2.3 : Prioriser les corrections

Identifier les chapitres à corriger en priorité :
- Score composite < 70
- fidelity_score < 60
- completeness_score < 80

---

## Phase 3 : Correction des chapitres problématiques

**Objectif :** Corriger les chapitres identifiés comme problématiques.

### Task 3.1 : Script de correction assistée

Créer `scripts/improve-chapter.py` qui pour un chapitre donné :
- Affiche côte à côte : EN (wuxiaworld), FR site, FR NovelFrance
- Propose des améliorations basées sur les deux sources
- Génère une version corrigée

### Task 3.2 : Corriger les chapitres prioritaires

Par lots de 50 chapitres, appliquer les corrections et valider.

### Task 3.3 : Vérification croisée

Pour chaque lot corrigé, vérifier que :
- Le score composite s'améliore
- Aucune régression sur les chapitres adjacents
- La cohérence inter-chapitres est préservée

---

## Phase 4 : Validation finale

### Task 4.1 : Build de test

Lancer `npm run build` pour vérifier que le site compile sans erreur.

### Task 4.2 : Rapport final

Générer `reports/quality-report.md` avec :
- Statistiques avant/après
- Liste des chapitres corrigés
- Terminologie unifiée
- Recommandations pour la maintenance continue

---

## Fichiers à créer

| Fichier | Phase |
|---------|-------|
| `scripts/glossary.json` | 1.1 |
| `scripts/audit-terminology.py` | 1.2 |
| `scripts/fix-terminology.py` | 1.3 |
| `scripts/score-chapters.py` | 2.1 |
| `scripts/improve-chapter.py` | 3.1 |
| `reports/terminology-issues.json` | 1.2 |
| `reports/chapter-scores.json` | 2.2 |
| `reports/quality-report.md` | 4.2 |

## Fichiers modifiés

| Fichier | Phase |
|---------|-------|
| `src/content/chapters/**/*.md` (2088 fichiers) | 1.4, 3.2 |

## Risques

- **Faux positifs** : le script de scoring peut mal évaluer des traductions créatives mais correctes → revue humaine par échantillonnage
- **Régression** : une correction peut casser la cohérence avec les chapitres adjacents → vérification par lots
- **Volume** : 2088 chapitres = traitement long → scripts optimisés, traitement par lots

## Validation

- [ ] Le glossaire couvre ≥ 95% des termes xianxia récurrents
- [ ] Le score composite médian passe au-dessus de 80
- [ ] Aucun chapitre n'a un fidelity_score < 50 après correction
- [ ] `npm run build` réussit
- [ ] 10 chapitres aléatoires vérifiés manuellement
