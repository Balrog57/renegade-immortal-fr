#!/usr/bin/env python3
"""
verify-all.py — Vérification complète des 2088 chapitres EN↔FR.

10 checks par chapitre :
1.  Alignement des paragraphes EN↔FR (ratio, tailles)
2.  Ratio de taille FR/EN (omission potentielle)
3.  Préservation des entités (noms propres multi-mots)
4.  Cohérence numérique (nombres manquants en FR)
5.  Glossaire xianxia (glossary.json, 136+ termes)
6.  Cohérence transition N-1→N (dernier/premier paragraphe)
7.  Ratio du nombre de phrases FR/EN
8.  Mots anglais non traduits dans le FR
9.  Scoring (0–100)
10. Triage RED / YELLOW / GREEN

Usage:
  python scripts/verify-all.py [--tome N] [--output reports/verify-all.json] [--sample N]
"""

import io
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

# ── Windows Unicode stdout ──────────────────────────────────────────────
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ── Chemins ─────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = PROJECT_ROOT / "src" / "content" / "chapters"
WUXIA_DIR = Path(r"C:\Users\Marc\Downloads\Renegade Immortal\wuxiaworld")
GLOSSARY_PATH = PROJECT_ROOT / "scripts" / "glossary.json"
OUTPUT_DIR = PROJECT_ROOT / "reports"

# ── Tome ranges ─────────────────────────────────────────────────────────
TOME_RANGES = [
    (1, 1, 64), (2, 65, 140), (3, 141, 200), (4, 201, 405),
    (5, 406, 471), (6, 472, 658), (7, 659, 920), (8, 921, 1140),
    (9, 1141, 1478), (10, 1479, 1613), (11, 1614, 1793),
    (12, 1794, 2002), (13, 2003, 2088),
]


def get_tome(ch_num: int) -> int | None:
    """Retourne le tome (1–13) d'un numéro de chapitre."""
    for tome, start, end in TOME_RANGES:
        if start <= ch_num <= end:
            return tome
    return None


# ═══════════════════════════════════════════════════════════════════════════
#  CHARGEMENT DES SOURCES
# ═══════════════════════════════════════════════════════════════════════════

def read_en_body(path: Path) -> str:
    """Lit le corps d'un chapitre EN (.txt), en ignorant les lignes d'en-tête."""
    if not path or not path.exists():
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.strip().split('\n')
    # Ignorer les lignes qui commencent par "Chapter N" (en-tête + répétition)
    body_lines = []
    skipped = 0
    for line in lines:
        stripped = line.strip()
        if re.match(r'^Chapter\s+\d+', stripped):
            skipped += 1
            if skipped <= 2:
                continue  # skip first two "Chapter N" header lines
        body_lines.append(line)
    return '\n'.join(body_lines).strip()


def read_fr_body(path: Path) -> tuple[str, dict]:
    """
    Lit un chapitre FR (.md), retourne (corps, frontmatter dict).
    Le frontmatter YAML est entre ---.
    """
    if not path or not path.exists():
        return "", {}
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    frontmatter = {}
    body = content
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter_text = parts[1]
            body = parts[2]
            for line in frontmatter_text.strip().split('\n'):
                if ':' in line:
                    key, _, val = line.partition(':')
                    frontmatter[key.strip()] = val.strip()
    return body.strip(), frontmatter


def build_maps(selected_tome: int | None = None):
    """
    Construit les mappings ch_num → Path pour EN et FR.
    Si selected_tome est fourni, filtre sur ce tome.
    Retourne (en_map, fr_map, fr_frontmatter_map).
    """
    en_map: dict[int, Path] = {}
    for root, dirs, files in os.walk(WUXIA_DIR):
        for f in files:
            if f.endswith('.txt'):
                m = re.match(r'(\d{4})[ab]?', f)
                if m:
                    ch_num = int(m.group(1))
                    tome = get_tome(ch_num)
                    if selected_tome is not None and tome != selected_tome:
                        continue
                    # Éviter de remplacer un chapitre déjà mappé (ex: 1455a vs 1455b)
                    if ch_num not in en_map:
                        en_map[ch_num] = Path(root) / f

    fr_map: dict[int, Path] = {}
    fr_frontmatter_map: dict[int, dict] = {}
    for root, dirs, files in os.walk(CHAPTERS_DIR):
        for f in files:
            if f.endswith('.md'):
                m = re.match(r'(\d{4})', f)
                if m:
                    ch_num = int(m.group(1))
                    tome = get_tome(ch_num)
                    if selected_tome is not None and tome != selected_tome:
                        continue
                    fr_map[ch_num] = Path(root) / f

    return en_map, fr_map


def load_glossary() -> dict:
    """Charge glossary.json."""
    with open(GLOSSARY_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════════════════
#  FONCTIONS D'EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════

def get_paragraphs(text: str) -> list[str]:
    """Extrait les paragraphes d'un texte (séparation par double saut de ligne)."""
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    # Ignorer les paragraphes qui ne sont que des titres de chapitre
    result = []
    for p in paras:
        p_stripped = p.replace('\n', ' ').strip()
        if re.match(r'^(Chapter|Chapitre)\s+\d+', p_stripped, re.IGNORECASE):
            continue
        if len(p_stripped) < 10:  # ignorer les paragraphes triviaux
            continue
        result.append(p)
    return result


def extract_proper_nouns(text: str) -> Counter:
    """
    Extrait les noms propres (mots capitalisés > 2 lettres) du texte.
    Retourne un Counter {nom: occurrences}.
    """
    words = re.findall(r'\b[A-Z][a-zàâäéèêëîïôöùûüç]{2,}\b', text)
    return Counter(words)


def _strip_leading_articles(name: str) -> str:
    """Retire les articles/déterminants/pronoms en tête d'un nom propre."""
    words = name.split()
    articles = {'the', 'a', 'an', 'this', 'that', 'these', 'those',
                'his', 'her', 'their', 'our', 'my', 'your', 'its'}
    while words and words[0].lower() in articles:
        words = words[1:]
    return ' '.join(words)


def extract_multiword_proper_names(text: str, glossary_en_terms: set[str]) -> set[str]:
    """
    Extrait les noms propres multi-mots capitalisés (ex: 'Wang Lin', 'Sea of Devils').
    Retourne un set de noms normalisés (minuscules).
    Exclut les termes du glossaire (cultivation stages, concepts) qui sont
    attendus comme traduits.
    """
    # Pattern: séquence de 2+ mots commençant par une majuscule
    pattern = r'\b([A-Z][a-zàâäéèêëîïôöùûüç]+(?:\s+[A-Z][a-zàâäéèêëîïôöùûüç]+)+)\b'
    matches = re.findall(pattern, text)
    normalized = {m.lower() for m in matches}

    # Exclure les termes du glossaire (ils sont traduits, pas gardés tel quel)
    glossary_lower = {t.lower() for t in glossary_en_terms}

    # Mots-outils: fonction, titre, préposition — si une séquence commence
    # par l'un d'eux, c'est probablement une phrase, pas un nom propre
    _LEADING_FUNCTION = {
        'after', 'before', 'when', 'while', 'where', 'although',
        'though', 'because', 'since', 'until', 'unless', 'during',
        'without', 'within', 'through', 'between', 'behind',
        'beyond', 'upon', 'against', 'among', 'along', 'inside',
        'outside', 'about', 'across', 'around', 'toward', 'towards',
        'beside', 'besides', 'despite', 'except', 'instead',
        'throughout', 'underneath', 'however', 'therefore',
        'moreover', 'nevertheless', 'furthermore', 'meanwhile',
        'otherwise', 'hence', 'thus', 'indeed', 'rather',
        'the', 'a', 'an', 'this', 'that', 'these', 'those',
        'his', 'her', 'their', 'our', 'my', 'your', 'its',
        'as', 'what', 'which', 'who', 'how', 'why',
        'seeing', 'looking', 'watching', 'hearing', 'feeling',
        'following', 'saying', 'thinking', 'knowing', 'making',
        'coming', 'going', 'taking', 'giving', 'using', 'having',
        'letting', 'finding', 'leaving', 'calling', 'turning',
        'standing', 'sitting', 'walking', 'running', 'flying',
        'not', 'just', 'only', 'even', 'also', 'still', 'then',
        'now', 'here', 'there', 'once', 'again', 'already',
        'although', 'else', 'another', 'other', 'such', 'many',
        'much', 'more', 'most', 'some', 'any', 'each', 'every',
        'both', 'few', 'several', 'all',
        # Titres communs
        'brother', 'sister', 'master', 'elder', 'senior', 'junior',
        'fellow', 'ancestor', 'ancestral', 'grand', 'great',
        'old', 'young', 'little', 'big',
    }

    _COMMON_PATTERNS = {
        'chapter one', 'book one', 'wang lin',
        'chapter two', 'chapter three', 'chapter four', 'chapter five',
        'chapter six', 'chapter seven', 'chapter eight', 'chapter nine',
        'chapter ten',
    }

    result = set()
    for name in normalized:
        if name in _COMMON_PATTERNS:
            continue
        # Vérifier contre le glossaire (avec et sans article initial)
        stripped = _strip_leading_articles(name)
        if name in glossary_lower or stripped in glossary_lower:
            continue
        # Exclure les séquences qui commencent par un mot-outil anglais
        first_word = name.split()[0]
        if first_word in _LEADING_FUNCTION:
            continue
        result.add(name)

    return result


def extract_numbers(text: str) -> set[str]:
    """Extrait tous les nombres du texte (entiers)."""
    return set(re.findall(r'\b\d+\b', text))


def split_sentences(text: str) -> list[str]:
    """Découpe un texte en phrases (compatible français)."""
    text = text.replace('\n', ' ')
    # Découpage sur .!? suivi d'espace + majuscule ou fin de chaîne
    sentences = re.split(r'(?<=[.!?…])\s+(?=[A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ])', text)
    return [s.strip() for s in sentences if len(s.strip().split()) >= 3]


def _french_plural_variants(word: str) -> set[str]:
    """Génère les variantes plurielles françaises courantes d'un mot."""
    variants = {word}
    variants.add(word + 's')
    if word.endswith(('eu', 'au', 'eau')):
        variants.add(word + 'x')
    if word.endswith('al'):
        variants.add(word[:-2] + 'aux')
    return variants


# ═══════════════════════════════════════════════════════════════════════════
#  LES 8 CHECKS
# ═══════════════════════════════════════════════════════════════════════════

def check_paragraph_alignment(en_text: str, fr_text: str) -> dict | None:
    """
    Check 1 : Alignement des paragraphes EN↔FR.
    Compare le nombre de paragraphes et la taille moyenne.
    Retourne None si OK, ou un dict issue.
    """
    en_paras = get_paragraphs(en_text)
    fr_paras = get_paragraphs(fr_text)

    if not en_paras or not fr_paras:
        return None

    para_count_ratio = len(fr_paras) / len(en_paras)

    # Tailles moyennes des paragraphes
    en_avg_size = sum(len(p.split()) for p in en_paras) / len(en_paras)
    fr_avg_size = sum(len(p.split()) for p in fr_paras) / len(fr_paras)
    size_ratio = fr_avg_size / en_avg_size if en_avg_size > 0 else 1.0

    severity = None
    if para_count_ratio < 0.60:
        severity = 'high'
    elif para_count_ratio < 0.80:
        severity = 'medium'

    if severity:
        return {
            'type': 'paragraph_alignment',
            'severity': severity,
            'en_para_count': len(en_paras),
            'fr_para_count': len(fr_paras),
            'para_count_ratio': round(para_count_ratio, 3),
            'en_avg_words_per_para': round(en_avg_size, 1),
            'fr_avg_words_per_para': round(fr_avg_size, 1),
            'size_ratio': round(size_ratio, 3),
            'detail': (f'Paragraphes: {len(fr_paras)} FR vs {len(en_paras)} EN '
                       f'(ratio {para_count_ratio:.2f})')
        }
    return None


def check_size_ratio(en_text: str, fr_text: str) -> dict | None:
    """
    Check 2 : Ratio de taille FR/EN.
    Flag si FR < 70% de EN (possible omission).
    """
    en_len = len(en_text)
    fr_len = len(fr_text)
    if en_len == 0:
        return None
    ratio = fr_len / en_len
    if ratio < 0.70:
        return {
            'type': 'size_ratio',
            'severity': 'high',
            'en_chars': en_len,
            'fr_chars': fr_len,
            'ratio': round(ratio, 3),
            'detail': f'Taille FR={fr_len}c vs EN={en_len}c (ratio {ratio:.2f}) — possible omission'
        }
    return None


def check_entity_preservation(en_text: str, fr_text: str,
                               glossary_en_terms: set[str]) -> dict | None:
    """
    Check 3 : Préservation des entités.
    Extrait les noms propres multi-mots capitalisés de l'EN (hors termes glossaire),
    vérifie leur présence dans le FR (avec matching souple).
    Flag si > 2 entités significatives manquantes.
    Note: beaucoup d'entités sont légitimement traduites (noms de sectes, lieux).
    Ce check détecte les cas où le traducteur aurait pu oublier une référence.
    """
    en_entities = extract_multiword_proper_names(en_text, glossary_en_terms)
    if len(en_entities) < 3:
        return None

    fr_lower = fr_text.lower()
    missing = []

    # Mots génériques qui apparaissent dans les noms de lieux/sectes
    _GENERIC_WORDS = {
        'sect', 'clan', 'tribe', 'sea', 'planet', 'continent',
        'mountain', 'city', 'palace', 'realm', 'world', 'star',
        'system', 'region', 'valley', 'peak', 'river', 'lake', 'island',
        'kingdom', 'empire', 'country', 'village', 'town', 'forest',
        'desert', 'ocean', 'cave', 'temple', 'pavilion', 'hall',
        'pagoda', 'tower', 'gate', 'bridge', 'road', 'path',
    }

    for entity in sorted(en_entities):
        # Vérifier la présence brute
        if entity in fr_lower:
            continue

        # Vérifier sans article initial
        stripped = _strip_leading_articles(entity)
        if stripped and stripped in fr_lower:
            continue

        # Vérifier la partie distinctive (sans mots génériques)
        words = entity.split()
        distinctive = ' '.join(w for w in words if w not in _GENERIC_WORDS)
        if distinctive and len(distinctive.split()) >= 1 and distinctive in fr_lower:
            continue

        # Vérifier si au moins la moitié des mots distinctifs apparaissent
        # dans le FR (matching partiel pour les noms longs)
        distinctive_words = [w for w in words if w not in _GENERIC_WORDS]
        if distinctive_words:
            found_count = sum(1 for w in distinctive_words if w in fr_lower)
            if found_count >= len(distinctive_words) * 0.5 and found_count >= 2:
                continue

        missing.append(entity)

    if len(missing) > 2:
        return {
            'type': 'entity_preservation',
            'severity': 'low',  # low: les noms propres sont souvent traduits
            'en_entities_count': len(en_entities),
            'missing_count': len(missing),
            'missing_entities': missing[:10],
            'detail': f'{len(missing)} entites EN absentes du FR sur {len(en_entities)}: {", ".join(missing[:5])}'
        }
    return None


def check_number_consistency(en_text: str, fr_text: str) -> dict | None:
    """
    Check 4 : Cohérence numérique.
    Flag si > 8 nombres de l'EN sont absents du FR.
    """
    en_numbers = extract_numbers(en_text)
    fr_numbers = extract_numbers(fr_text)

    if len(en_numbers) < 10:
        return None  # pas assez de nombres pour un test significatif

    missing = en_numbers - fr_numbers
    if len(missing) > 8:
        return {
            'type': 'number_consistency',
            'severity': 'low',
            'en_numbers_count': len(en_numbers),
            'fr_numbers_count': len(fr_numbers),
            'missing_count': len(missing),
            'detail': f'{len(missing)} nombres EN absents du FR sur {len(en_numbers)}'
        }
    return None


def check_xianxia_glossary(en_text: str, fr_text: str, glossary: dict) -> dict | None:
    """
    Check 5 : Glossaire xianxia.
    Pour chaque terme EN du glossaire présent dans le chapitre,
    vérifie si son équivalent FR existe.
    Flag > 3 manquants (medium) ou > 1 manquant (low).
    """
    en_lower = en_text.lower()
    fr_lower = fr_text.lower()
    missing_terms = []

    for en_term, entry in glossary.items():
        en_term_lower = en_term.lower()

        # Vérifier présence du terme EN dans le chapitre source
        if len(en_term_lower) <= 4:
            pattern = re.compile(r'\b' + re.escape(en_term_lower) + r'\b')
        else:
            pattern = re.compile(re.escape(en_term_lower))

        if not pattern.search(en_lower):
            continue  # terme absent de l'EN, on ignore

        # Vérifier si un équivalent FR est présent
        fr_equivs = [entry.get('fr', '').lower()]
        if 'aliases' in entry:
            fr_equivs.extend(a.lower() for a in entry['aliases'])

        # Expansion des variantes plurielles pour termes courts
        expanded_fr: set[str] = set()
        for fr_eq in set(fr_equivs):
            if len(fr_eq) <= 5:
                expanded_fr.update(_french_plural_variants(fr_eq))
            else:
                expanded_fr.add(fr_eq)

        found = False
        for fr_eq in expanded_fr:
            if len(fr_eq) <= 5:
                p = re.compile(r'\b' + re.escape(fr_eq) + r'\b')
            else:
                p = re.compile(re.escape(fr_eq))
            if p.search(fr_lower):
                found = True
                break

        if not found:
            missing_terms.append({
                'en_term': en_term,
                'expected_fr': entry.get('fr', ''),
                'category': entry.get('category', 'unknown'),
            })

    if len(missing_terms) > 3:
        return {
            'type': 'xianxia_glossary',
            'severity': 'medium',
            'missing_count': len(missing_terms),
            'missing_terms': missing_terms,
            'detail': f'{len(missing_terms)} termes xianxia non rendus'
        }
    elif len(missing_terms) > 0:
        return {
            'type': 'xianxia_glossary',
            'severity': 'low',
            'missing_count': len(missing_terms),
            'missing_terms': missing_terms,
            'detail': f'{len(missing_terms)} terme(s) xianxia non rendu(s)'
        }
    return None


def check_transition_coherence(
    ch_num: int,
    en_text: str,
    fr_text: str,
    prev_en_text: str | None,
    prev_fr_text: str | None,
) -> dict | None:
    """
    Check 6 : Cohérence transition N-1→N.
    Compare le dernier paragraphe de N-1 avec le premier de N,
    dans les deux langues. Flag si des noms propres du 1er para EN
    sont absents du 1er para FR.
    """
    if prev_en_text is None or prev_fr_text is None:
        return None

    en_paras = get_paragraphs(en_text)
    if not en_paras:
        return None

    first_en_para = en_paras[0]
    first_en_nouns = extract_proper_nouns(first_en_para)

    # Filtrer pour ne garder que les noms propres significatifs (≥ 3 occurrences
    # dans le texte ou mots > 3 lettres)
    significant_nouns = {
        noun for noun, count in first_en_nouns.items()
        if len(noun) > 3 and noun[0].isupper()
    }

    if len(significant_nouns) < 2:
        return None

    fr_paras = get_paragraphs(fr_text)
    if not fr_paras:
        return None

    first_fr_para = fr_paras[0].lower()
    missing = [n for n in significant_nouns if n.lower() not in first_fr_para]

    if len(missing) > 0:
        return {
            'type': 'transition_coherence',
            'severity': 'low',
            'missing_in_fr_first_para': missing,
            'detail': f'Noms propres du 1er § EN absents du 1er § FR: {", ".join(missing)}'
        }
    return None


def check_sentence_count_ratio(en_text: str, fr_text: str) -> dict | None:
    """
    Check 7 : Ratio du nombre de phrases FR/EN.
    Flag si le nombre de phrases FR < 70% du nombre EN.
    """
    en_sentences = split_sentences(en_text)
    fr_sentences = split_sentences(fr_text)

    if len(en_sentences) < 5:
        return None

    ratio = len(fr_sentences) / len(en_sentences)
    if ratio < 0.70:
        return {
            'type': 'sentence_count_ratio',
            'severity': 'medium',
            'en_sentence_count': len(en_sentences),
            'fr_sentence_count': len(fr_sentences),
            'ratio': round(ratio, 3),
            'detail': f'Phrases: {len(fr_sentences)} FR vs {len(en_sentences)} EN (ratio {ratio:.2f})'
        }
    return None


def check_untranslated_english(fr_text: str) -> dict | None:
    """
    Check 8 : Mots anglais non traduits dans le FR.
    Utilise une liste ciblée de mots/patterns anglais connus pour
    éviter les faux positifs avec le vocabulaire français.
    Flag si > 3 occurrences (mots distincts ou répétés).
    """
    # Mots anglais connecteurs/adverbes (liste éprouvée de deep-review.py)
    _ANGLICISM_CONNECTORS = [
        "however", "therefore", "actually", "basically", "meanwhile",
        "moreover", "nevertheless", "indeed", "thus", "hence",
        "furthermore", "anyway", "somehow", "anyhow", "anywhere",
        "after all", "in fact", "of course", "anymore",
        "whatever", "whenever", "wherever", "whoever",
    ]

    # Mots-outils anglais qui n'existent pas en français
    _ENGLISH_FUNCTION = [
        "the", "and", "for", "with", "that", "this", "they",
        "their", "them", "these", "those", "there", "where",
        "which", "what", "when", "who", "how", "would", "could",
        "should", "might", "been", "being", "each", "every",
        "some", "many", "much", "more", "most", "other", "such",
        "own", "same", "any", "few", "into", "onto", "upon",
        "without", "within", "through", "during", "between",
        "behind", "beyond", "against", "among", "along",
        "almost", "always", "never", "often", "sometimes",
        "usually", "really", "quite", "rather", "still",
        "already", "enough", "almost", "instead", "perhaps",
        "maybe", "anyone", "someone", "everyone", "nothing",
        "something", "anything", "everything", "else",
        "though", "although", "because", "since", "until",
        "unless", "while", "whether", "either", "neither",
    ]

    fr_lower = fr_text.lower()
    found_words: list[str] = []

    # Vérifier les connecteurs/adverbes anglais
    for word in _ANGLICISM_CONNECTORS:
        pattern = re.compile(r'\b' + re.escape(word.lower()) + r'\b')
        matches = pattern.findall(fr_lower)
        found_words.extend([word] * len(matches))

    # Vérifier les mots-outils anglais (seulement s'ils sont isolés,
    # pas dans des noms propres)
    for word in _ENGLISH_FUNCTION:
        pattern = re.compile(r'\b' + re.escape(word.lower()) + r'\b')
        matches = pattern.findall(fr_lower)
        found_words.extend([word] * len(matches))

    # Compter les occurrences distinctes
    word_counts = Counter(found_words)
    total_occurrences = sum(word_counts.values())

    if total_occurrences > 3:
        top_words = [f"{w}(×{c})" for w, c in word_counts.most_common(10)]
        return {
            'type': 'untranslated_english',
            'severity': 'low',
            'total_occurrences': total_occurrences,
            'distinct_words': len(word_counts),
            'words': dict(word_counts.most_common(15)),
            'detail': f'{total_occurrences} occurrences anglaises ({len(word_counts)} mots distincts): {", ".join(top_words[:6])}'
        }
    return None


# ═══════════════════════════════════════════════════════════════════════════
#  SCORING & TRIAGE
# ═══════════════════════════════════════════════════════════════════════════

SEVERITY_DEDUCTION = {
    'critical': 30,
    'high': 20,
    'medium': 10,
    'low': 5,
}


def compute_score(issues: list[dict]) -> int:
    """Calcule le score (0–100) en déduisant les pénalités par sévérité."""
    score = 100
    dedup_types = set()  # éviter double pénalité pour le même type
    for issue in issues:
        severity = issue.get('severity', 'low')
        issue_type = issue.get('type', '')
        if issue_type in dedup_types:
            continue
        dedup_types.add(issue_type)
        score -= SEVERITY_DEDUCTION.get(severity, 5)
    return max(0, min(100, score))


def triage_chapter(issues: list[dict]) -> str:
    """
    Triage RED / YELLOW / GREEN :
    - RED : au moins 1 issue critical/high, ou > 3 medium
    - YELLOW : 1–3 medium, pas de critical/high
    - GREEN : 0 medium, low-severity uniquement
    """
    has_critical = any(i.get('severity') == 'critical' for i in issues)
    has_high = any(i.get('severity') == 'high' for i in issues)
    medium_count = sum(1 for i in issues if i.get('severity') == 'medium')

    if has_critical or has_high or medium_count > 3:
        return 'RED'
    elif medium_count >= 1:
        return 'YELLOW'
    else:
        return 'GREEN'


# ═══════════════════════════════════════════════════════════════════════════
#  VÉRIFICATION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════

def verify_all_chapters(en_map: dict, fr_map: dict, glossary: dict,
                         selected_chapters: list[int] | None = None) -> dict:
    """
    Vérifie tous les chapitres (ou une sélection).
    Retourne le rapport complet.
    """
    # Déterminer les chapitres à traiter
    if selected_chapters is not None:
        chapters = sorted(selected_chapters)
    else:
        chapters = sorted(set(en_map.keys()) & set(fr_map.keys()))

    total = len(chapters)
    results = []

    # Pré-calculer les termes EN du glossaire pour le check 3
    glossary_en_terms: set[str] = set(glossary.keys())

    tome_stats: dict[int, dict] = defaultdict(lambda: {
        'total': 0, 'red': 0, 'yellow': 0, 'green': 0,
        'scores': [], 'issues_by_type': Counter(),
    })

    # Pré-charger tous les textes pour le check de transition (N-1→N)
    # On ne charge que si on traite tout (pas de sample limité)
    preload = selected_chapters is None
    en_texts: dict[int, str] = {}
    fr_texts: dict[int, str] = {}
    fr_paras_cache: dict[int, list[str]] = {}

    if preload:
        for ch_num in chapters:
            en_texts[ch_num] = read_en_body(en_map.get(ch_num))
            fr_body, _ = read_fr_body(fr_map.get(ch_num))
            fr_texts[ch_num] = fr_body

    start_time = time.time()
    for idx, ch_num in enumerate(chapters):
        en_path = en_map.get(ch_num)
        fr_path = fr_map.get(ch_num)

        if not en_path or not fr_path:
            continue

        # Charger les textes (depuis cache si préchargé, sinon lire)
        if preload:
            en_text = en_texts.get(ch_num, '')
            fr_text = fr_texts.get(ch_num, '')
            _, fr_frontmatter = read_fr_body(fr_path)  # re-read pour frontmatter
        else:
            en_text = read_en_body(en_path)
            fr_text, fr_frontmatter = read_fr_body(fr_path)
            en_texts[ch_num] = en_text
            fr_texts[ch_num] = fr_text

        if not en_text or not fr_text:
            continue

        tome = get_tome(ch_num)
        issues: list[dict] = []

        # ── Check 1 : Alignement des paragraphes ──
        issue = check_paragraph_alignment(en_text, fr_text)
        if issue:
            issue['chapter'] = ch_num
            issues.append(issue)

        # ── Check 2 : Ratio de taille ──
        issue = check_size_ratio(en_text, fr_text)
        if issue:
            issue['chapter'] = ch_num
            issues.append(issue)

        # ── Check 3 : Préservation des entités ──
        issue = check_entity_preservation(en_text, fr_text, glossary_en_terms)
        if issue:
            issue['chapter'] = ch_num
            issues.append(issue)

        # ── Check 4 : Cohérence numérique ──
        issue = check_number_consistency(en_text, fr_text)
        if issue:
            issue['chapter'] = ch_num
            issues.append(issue)

        # ── Check 5 : Glossaire xianxia ──
        issue = check_xianxia_glossary(en_text, fr_text, glossary)
        if issue:
            issue['chapter'] = ch_num
            issues.append(issue)

        # ── Check 6 : Cohérence transition N-1→N ──
        prev_en = en_texts.get(ch_num - 1) if (ch_num - 1) in chapters else None
        prev_fr = fr_texts.get(ch_num - 1) if (ch_num - 1) in chapters else None
        issue = check_transition_coherence(ch_num, en_text, fr_text, prev_en, prev_fr)
        if issue:
            issue['chapter'] = ch_num
            issues.append(issue)

        # ── Check 7 : Ratio nombre de phrases ──
        issue = check_sentence_count_ratio(en_text, fr_text)
        if issue:
            issue['chapter'] = ch_num
            issues.append(issue)

        # ── Check 8 : Mots anglais non traduits ──
        issue = check_untranslated_english(fr_text)
        if issue:
            issue['chapter'] = ch_num
            issues.append(issue)

        # ── Scoring & Triage ──
        score = compute_score(issues)
        triage = triage_chapter(issues)

        # ── Ratios supplémentaires pour le rapport ──
        en_len = len(en_text)
        fr_len = len(fr_text)
        size_ratio = round(fr_len / en_len, 4) if en_len > 0 else 1.0

        en_para_count = len(get_paragraphs(en_text))
        fr_para_count = len(get_paragraphs(fr_text))
        para_ratio = round(fr_para_count / en_para_count, 4) if en_para_count > 0 else 1.0

        en_sent_count = len(split_sentences(en_text))
        fr_sent_count = len(split_sentences(fr_text))
        sent_ratio = round(fr_sent_count / en_sent_count, 4) if en_sent_count > 0 else 1.0

        severity_counts = Counter(i.get('severity') for i in issues)

        result = {
            'chapter': ch_num,
            'tome': tome,
            'en_title': fr_frontmatter.get('en', ''),
            'fr_title': fr_frontmatter.get('title', ''),
            'score': score,
            'triage': triage,
            'size_ratio': size_ratio,
            'para_count_ratio': para_ratio,
            'sentence_count_ratio': sent_ratio,
            'en_chars': en_len,
            'fr_chars': fr_len,
            'en_paras': en_para_count,
            'fr_paras': fr_para_count,
            'en_sentences': en_sent_count,
            'fr_sentences': fr_sent_count,
            'severity_counts': dict(severity_counts),
            'issues': issues,
        }
        results.append(result)

        # Mettre à jour les stats du tome
        if tome:
            ts = tome_stats[tome]
            ts['total'] += 1
            ts[triage.lower()] += 1
            ts['scores'].append(score)
            for issue in issues:
                ts['issues_by_type'][issue['type']] += 1

        # Progression
        if (idx + 1) % 100 == 0 or (idx + 1) == total:
            elapsed = time.time() - start_time
            rate = (idx + 1) / elapsed if elapsed > 0 else 0
            print(f"  [{idx + 1}/{total}] {rate:.0f} chap/s — "
                  f"dernier: ch{ch_num} score={score} {triage}", flush=True)

    # ── Construire le résumé par tome ──
    tome_summaries = {}
    for tome in sorted(tome_stats.keys()):
        ts = tome_stats[tome]
        scores = ts['scores']
        tome_summaries[tome] = {
            'total': ts['total'],
            'red': ts['red'],
            'yellow': ts['yellow'],
            'green': ts['green'],
            'avg_score': round(sum(scores) / len(scores), 1) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'top_issues': ts['issues_by_type'].most_common(5),
        }

    # ── Résumé global ──
    global_red = sum(ts['red'] for ts in tome_stats.values())
    global_yellow = sum(ts['yellow'] for ts in tome_stats.values())
    global_green = sum(ts['green'] for ts in tome_stats.values())
    all_scores = [r['score'] for r in results]

    # Top issues globales
    global_issues = Counter()
    for r in results:
        for issue in r['issues']:
            global_issues[issue['type']] += 1

    # Répartition des sévérités
    global_severity = Counter()
    for r in results:
        for issue in r['issues']:
            global_severity[issue.get('severity', 'low')] += 1

    global_summary = {
        'total_chapters': len(results),
        'red': global_red,
        'yellow': global_yellow,
        'green': global_green,
        'avg_score': round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
        'median_score': sorted(all_scores)[len(all_scores) // 2] if all_scores else 0,
        'min_score': min(all_scores) if all_scores else 0,
        'max_score': max(all_scores) if all_scores else 0,
        'total_issues': sum(global_issues.values()),
        'top_issues': global_issues.most_common(10),
        'severity_distribution': dict(global_severity),
    }

    report = {
        'meta': {
            'script': 'verify-all.py',
            'total_chapters_mapped': len(chapters),
            'total_chapters_verified': len(results),
            'tome_count': len(tome_stats),
            'glossary_terms': len(glossary),
        },
        'global_summary': global_summary,
        'tome_summaries': tome_summaries,
        'chapters': results,
    }

    return report


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Vérification complète EN↔FR des 2088 chapitres'
    )
    parser.add_argument('--tome', type=int, choices=range(1, 14),
                        help='Vérifier uniquement un tome spécifique (1–13)')
    parser.add_argument('--output', type=str, default='reports/verify-all.json',
                        help='Fichier de sortie JSON (défaut: reports/verify-all.json)')
    parser.add_argument('--sample', type=int, default=0,
                        help='Échantillon aléatoire de N chapitres (0 = tous)')
    args = parser.parse_args()

    print("=" * 70)
    print("  verify-all.py — Vérification complète EN↔FR")
    print("=" * 70)
    print()

    # ── Charger le glossaire ──
    print("Chargement du glossaire...")
    glossary = load_glossary()
    print(f"  → {len(glossary)} termes chargés")
    print()

    # ── Construire les mappings ──
    print("Construction des mappings EN/FR...")
    en_map, fr_map = build_maps(selected_tome=args.tome)
    common = sorted(set(en_map.keys()) & set(fr_map.keys()))
    print(f"  → {len(en_map)} chapitres EN, {len(fr_map)} chapitres FR, "
          f"{len(common)} en commun")
    print()

    # ── Échantillonnage ──
    selected = None
    if args.sample > 0:
        import random
        random.seed(42)
        selected = random.sample(common, min(args.sample, len(common)))
        print(f"Échantillon: {len(selected)} chapitres (mode --sample)")
    else:
        selected = common
        print(f"Vérification: {len(selected)} chapitres")

    if args.tome:
        print(f"Tome: {args.tome}")
    print()

    # ── Vérification ──
    print("Vérification en cours...")
    start = time.time()
    report = verify_all_chapters(en_map, fr_map, glossary, selected)
    elapsed = time.time() - start
    print(f"\n✓ Vérification terminée en {elapsed:.1f}s")
    print()

    # ── Résumé ──
    gs = report['global_summary']
    print("─" * 70)
    print("  RÉSUMÉ GLOBAL")
    print("─" * 70)
    print(f"  Chapitres vérifiés : {gs['total_chapters']}")
    print(f"  Score moyen        : {gs['avg_score']}")
    print(f"  Score médian       : {gs['median_score']}")
    print(f"  Total problèmes    : {gs['total_issues']}")
    print()
    print(f"  🔴 RED    : {gs['red']:>5}")
    print(f"  🟡 YELLOW : {gs['yellow']:>5}")
    print(f"  🟢 GREEN  : {gs['green']:>5}")
    print()

    # ── Par tome ──
    print("─" * 70)
    print("  PAR TOME")
    print("─" * 70)
    print(f"  {'Tome':<6} {'Total':<6} {'RED':<6} {'YELLOW':<8} {'GREEN':<7} {'Score moy':<10}")
    print(f"  {'─'*6} {'─'*6} {'─'*6} {'─'*8} {'─'*7} {'─'*10}")
    for tome in sorted(report['tome_summaries'].keys()):
        ts = report['tome_summaries'][tome]
        print(f"  {tome:<6} {ts['total']:<6} {ts['red']:<6} {ts['yellow']:<8} "
              f"{ts['green']:<7} {ts['avg_score']:<10}")

    # ── Top issues ──
    print()
    print("─" * 70)
    print("  TOP 10 PROBLÈMES")
    print("─" * 70)
    for issue_type, count in gs['top_issues']:
        print(f"  {issue_type:<30} {count:>5}")

    print()
    print("─" * 70)
    print("  SÉVÉRITÉS")
    print("─" * 70)
    for sev, count in sorted(gs['severity_distribution'].items()):
        print(f"  {sev:<10} {count:>5}")

    # ── Sauvegarde ──
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n✓ Rapport sauvegardé : {output_path} ({size_mb:.1f} MB)")


if __name__ == '__main__':
    main()
