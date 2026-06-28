# Plan de Révision — 2088 Chapitres

> **Objectif :** Vérifier chaque chapitre sur 6 critères structurels + 4 critères sémantiques, en croisant EN (Wuxiaworld), NF (NovelFrance), Site, et chapitres adjacents.

---

## 1. CE QUI EST FAIT ✅

### 1.1 Revue structurelle (G, O, C, T, X, F) — 2088/2088 = 100%

| Critère | Description | Statut |
|---------|-------------|--------|
| **G** Grammaire | Accords, conjugaison, guillemets équilibrés | ✅ 2088/2088 |
| **O** Orthographe | Accents, fautes de frappe, homophones | ✅ 2088/2088 |
| **C** Cohérence | Noms propres, continuité N-1/N+1 | ✅ 2088/2088 |
| **T** Traduction | Ratio taille FR/EN, paragraphes | ✅ 2088/2088 |
| **X** Terminologie | Glossaire xianxia 136 termes | ✅ 2088/2088 |
| **F** Formatage | Paragraphes, ponctuation française | ✅ 2088/2088 |

**Corrections appliquées :** 670 (58 accents, 35 paragraphes fusionnés, 12 guillemets, 564 espaces ponctuation, 1 typo)

### 1.2 Revue sémantique (fidélité, qualité, style, vs NF) — 39/2088 = 1.9%

| Tome | Échantillon | Fidélité EN | Qualité FR | Style Xianxia | vs NF |
|------|------------|:-----------:|:----------:|:-------------:|:-----:|
| T1 (1-64) | ch1, ch32, ch64 | 10.0 | 10.0 | 8.3 | FR > NF |
| T2 (65-140) | ch65, ch100, ch140 | 10.0 | 10.0 | 8.3 | FR > NF |
| T3 (141-200) | ch141, ch170, ch200 | 10.0 | 10.0 | 8.3 | FR > NF |
| T4 (201-405) | ch201, ch300, ch405 | 10.0 | 10.0 | 8.3 | FR > NF |
| T5 (406-471) | ch406, ch440, ch471 | 10.0 | 10.0 | 8.3 | FR > NF |
| T6 (472-658) | ch472, ch565, ch658 | 10.0 | 10.0 | 8.3 | FR > NF |
| T7 (659-920) | ch659, ch790, ch920 | 10.0 | 10.0 | 8.3 | FR > NF |
| T8 (921-1140) | ch921, ch1030, ch1140 | 7.7 | 9.2 | 8.1 | FR > NF |
| T9 (1141-1478) | ch1141, ch1310, ch1478 | 7.2 | 8.9 | 7.5 | FR > NF |
| T10 (1479-1613) | ch1479, ch1545, ch1613 | 7.6 | 9.1 | 7.8 | FR > NF |
| T11 (1614-1793) | ch1614, ch1700, ch1793 | 7.8 | 9.1 | 7.8 | FR > NF |
| T12 (1794-2002) | ch1794, ch1900, ch2002 | 7.4 | 9.1 | 8.4 | FR > NF |
| T13 (2003-2088) | ch2003, ch2045, ch2088 | 7.3 | 9.4 | 8.1 | FR > NF |
| **MOYENNE** | | **8.8** | **9.6** | **8.2** | **FR toujours > NF** |

### 1.3 Outils créés

| Script | Rôle |
|--------|------|
| `scripts/review-all.py` | Revue automatique 6 critères (G,O,C,T,X,F) |
| `scripts/fix-orthographe.py` | Correction accents |
| `scripts/fix-paragraphs.py` | Correction paragraphes fusionnés |
| `scripts/fix-espaces-ponctuation.py` | Correction espaces avant ! ? ; : |
| `scripts/glossary.json` | Glossaire xianxia 136 termes |
| `scripts/audit-terminology.py` | Audit terminologique |
| `scripts/score-chapters.py` | Scoring fidélité/qualité |
| `scripts/deep-review.py` | Détection problèmes traduction |

---

## 2. CE QUI RESTE À FAIRE 🔄

### 2.1 Revue sémantique — 2049 chapitres restants

**Méthode par chapitre :**
1. Lire EN (Wuxiaworld), FR site (lecture/), FR NF (novelfrance/)
2. Comparer 3 passages : ouverture, milieu (conflit/action), fin (cliffhanger)
3. Vérifier : omissions, contresens, noms propres, termes xianxia, ton
4. Noter /10 : fidélité EN, qualité FR, style xianxia
5. Comparer avec NF : quelle version est meilleure et pourquoi
6. Corriger si nécessaire

**Priorité par tome (du plus urgent au moins urgent) :**

| Priorité | Tome | Chapitres | Fidélité actuelle | Raison |
|:--------:|------|:---------:|:-----------------:|--------|
| **P1** | T9 (1141-1478) | 338 | 7.2/10 | Fidélité la plus basse |
| **P2** | T13 (2003-2088) | 86 | 7.3/10 | Dernier tome, conclusion |
| **P3** | T12 (1794-2002) | 209 | 7.4/10 | Avant-dernier tome |
| **P4** | T10 (1479-1613) | 135 | 7.6/10 | Milieu de saga |
| **P5** | T8 (921-1140) | 220 | 7.7/10 | Transition |
| **P6** | T11 (1614-1793) | 180 | 7.8/10 | Bonne base |
| **P7** | T1-T7 (1-920) | 920 | 10.0/10 | Déjà excellents |

### 2.2 Améliorations ciblées (issues de la revue sémantique)

| Problème | Impact | Tome concerné | Action |
|----------|--------|---------------|--------|
| Termes xianxia non rendus (« ancient god » → « dieu ancien ») | Moyen | T8-T13 | Script de détection + correction |
| Anglicismes résiduels (« however », « therefore ») | Faible | T8-T13 | Script de détection |
| Phrases-calques trop longues | Faible | T9-T10 | Relecture humaine |
| Variété poétique insuffisante | Faible | T9 | Enrichissement lexical |

### 2.3 Validation finale

- [ ] Revue sémantique complète (2049 chapitres)
- [ ] Corrections des problèmes détectés
- [ ] Re-build et test
- [ ] Commit final

---

## 3. PROGRESSION DÉTAILLÉE

| Tome | Chapitres | Structure (G,O,C,T,X,F) | Sémantique | Restant sémantique |
|------|:---------:|:----------------------:|:----------:|:------------------:|
| Tome 1 | 64 | ✅ 100% | 3/64 | 61 |
| Tome 2 | 76 | ✅ 100% | 3/76 | 73 |
| Tome 3 | 60 | ✅ 100% | 3/60 | 57 |
| Tome 4 | 205 | ✅ 100% | 3/205 | 202 |
| Tome 5 | 66 | ✅ 100% | 3/66 | 63 |
| Tome 6 | 187 | ✅ 100% | 3/187 | 184 |
| Tome 7 | 262 | ✅ 100% | 3/262 | 259 |
| Tome 8 | 220 | ✅ 100% | 3/220 | 217 |
| Tome 9 | 338 | ✅ 100% | 3/338 | **335** ⬅ P1 |
| Tome 10 | 135 | ✅ 100% | 3/135 | 132 |
| Tome 11 | 180 | ✅ 100% | 3/180 | 177 |
| Tome 12 | 209 | ✅ 100% | 3/209 | 206 |
| Tome 13 | 86 | ✅ 100% | 3/86 | **83** ⬅ P2 |
| **Total** | **2088** | **✅ 100%** | **39/2088** | **2049** |

---

## 4. PROCHAINES ACTIONS (dans l'ordre)

1. **Tome 9** (P1) — 335 chapitres, fidélité 7.2 → cible 8.5+
2. **Tome 13** (P2) — 83 chapitres, conclusion de la saga
3. **Tome 12** (P3) — 206 chapitres
4. **Tome 10** (P4) — 132 chapitres
5. **Tome 8** (P5) — 217 chapitres
6. **Tome 11** (P6) — 177 chapitres
7. **Tomes 1-7** (P7) — 920 chapitres (déjà excellents, vérification rapide)
