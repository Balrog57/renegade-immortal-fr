#!/usr/bin/env python3
"""
Revue approfondie chapitre par chapitre - V5.
Détecte les VRAIS problèmes de traduction :
1. Omissions (paragraphes EN sans équivalent FR)
2. Contresens (noms propres mal traduits, chiffres différents)
3. Incohérences avec chapitres adjacents (termes qui changent brutalement)
4. Divergences site vs NF qui suggèrent une erreur

Nouveautés V5:
5. Termes xianxia non rendus (glossary.json, 136 termes)
6. Anglicismes résiduels (connecteurs/adverbes anglais)
7. Phrases-calques (phrases trop longues miroir de l'EN)
8. Variété poétique insuffisante (TTR, hapax ratio)
+ Vérification cohérence chapitres EN<->FR par tome
+ Flag fiabilité NF pour T7+
+ Triage automatique RED/YELLOW/GREEN

Usage: python scripts/deep-review.py [--sample N] [--full] [--output reports/semantic-review-full.json]
"""

import io, json, os, re, sys
from collections import Counter, defaultdict
from pathlib import Path

# Ensure stdout supports Unicode on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = PROJECT_ROOT / "src" / "content" / "chapters"
WUXIA_DIR = Path(r"C:\Users\Marc\Downloads\Renegade Immortal\wuxiaworld")
NF_DIR = PROJECT_ROOT / "novelfrance"
GLOSSARY_PATH = PROJECT_ROOT / "scripts" / "glossary.json"
OUTPUT_DIR = PROJECT_ROOT / "reports"

# Tome chapter ranges (tome_num, start_ch, end_ch)
TOME_RANGES = [
    (1, 1, 64),
    (2, 65, 140),
    (3, 141, 200),
    (4, 201, 405),
    (5, 406, 471),
    (6, 472, 658),
    (7, 659, 920),
    (8, 921, 1140),
    (9, 1141, 1478),
    (10, 1479, 1613),
    (11, 1614, 1793),
    (12, 1794, 2002),
    (13, 2003, 2088),
]

# English connectives/adverbs to detect as residual anglicisms
ANGLICISM_WORDS = [
    "however", "therefore", "actually", "basically", "meanwhile",
    "moreover", "nevertheless", "indeed", "thus", "hence",
    "furthermore", "anyway", "somehow", "anyhow", "anywhere",
    "after all", "in fact", "of course", "anymore",
    "whatever", "whenever", "wherever", "whoever",
]


def get_tome(ch_num):
    """Map a chapter number to its tome (1-13)."""
    for tome, start, end in TOME_RANGES:
        if start <= ch_num <= end:
            return tome
    return None


def read_body(path):
    """Read chapter body text, stripping YAML frontmatter from .md files."""
    if not path or not os.path.exists(str(path)):
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if str(path).endswith('.md') and content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]
    return content.strip()


def get_paras(text):
    """Extract paragraphs, filtering out chapter title lines."""
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    return [p for p in paras if not re.match(r'^(Chapter|Chapitre)\s+\d+', p, re.IGNORECASE)]


def extract_proper_nouns(text):
    """Extract capitalized words that are likely proper nouns."""
    words = re.findall(r'\b[A-Z][a-zàâäéèêëîïôöùûüç]{2,}\b', text)
    return Counter(words)


def extract_numbers(text):
    """Extract all numbers from text."""
    return set(re.findall(r'\b\d+\b', text))


def split_sentences(text):
    """Split text into sentences (French-aware)."""
    text = text.replace('\n', ' ')
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip().split()) >= 3]


def compute_lexical_diversity(text):
    """Compute TTR (Type-Token Ratio) and hapax ratio."""
    words = re.findall(r'\b[a-zàâäéèêëîïôöùûüç]+\b', text.lower())
    if not words:
        return 0.0, 0.0
    total = len(words)
    unique = len(set(words))
    ttr = unique / total
    word_counts = Counter(words)
    hapax_count = sum(1 for c in word_counts.values() if c == 1)
    hapax_ratio = hapax_count / total
    return ttr, hapax_ratio


def load_glossary():
    """Load glossary.json."""
    with open(GLOSSARY_PATH, 'r', encoding='utf-8') as f:
        glossary = json.load(f)
    return glossary


def build_maps():
    """Build chapter maps for all three sources + tome mapping."""
    wuxia_map = {}
    for root, dirs, files in os.walk(WUXIA_DIR):
        for f in files:
            if f.endswith('.txt'):
                m = re.match(r'(\d{4})', f)
                if m:
                    wuxia_map[int(m.group(1))] = Path(root) / f

    site_map = {}
    site_tome_map = {}
    for root, dirs, files in os.walk(CHAPTERS_DIR):
        tome_match = re.search(r'tome-(\d+)', str(root))
        tome = int(tome_match.group(1)) if tome_match else None
        for f in files:
            if f.endswith('.md'):
                m = re.match(r'(\d{4})', f)
                if m:
                    ch_num = int(m.group(1))
                    site_map[ch_num] = Path(root) / f
                    if tome:
                        site_tome_map[ch_num] = tome

    nf_map = {}
    if NF_DIR.exists():
        for f in os.listdir(NF_DIR):
            if f.endswith('.md'):
                m = re.match(r'ch(\d{4})', f)
                if m:
                    nf_map[int(m.group(1))] = NF_DIR / f

    return wuxia_map, site_map, nf_map, site_tome_map


def check_chapter_consistency(wuxia_map, site_map):
    """Verify EN files per tome match FR files per tome."""
    issues = []

    for tome, start, end in TOME_RANGES:
        en_chapters = set(c for c in wuxia_map if start <= c <= end)
        fr_chapters = set(c for c in site_map if start <= c <= end)

        missing_in_fr = en_chapters - fr_chapters
        extra_in_fr = fr_chapters - en_chapters

        if missing_in_fr or extra_in_fr:
            detail_parts = []
            if missing_in_fr:
                detail_parts.append(f"{len(missing_in_fr)} chapitres EN manquants en FR: {sorted(missing_in_fr)[:10]}")
            if extra_in_fr:
                detail_parts.append(f"{len(extra_in_fr)} chapitres FR sans source EN: {sorted(extra_in_fr)[:10]}")

            issues.append({
                'chapter': 0,
                'severity': 'critical',
                'type': 'chapter_count_mismatch',
                'tome': tome,
                'en_count': len(en_chapters),
                'fr_count': len(fr_chapters),
                'detail': ' | '.join(detail_parts),
                'missing_in_fr': sorted(missing_in_fr),
                'extra_in_fr': sorted(extra_in_fr),
            })

    return issues


def _french_plural_variants(word):
    """Generate common French plural variants of a word for matching."""
    variants = {word}
    variants.add(word + 's')
    if word.endswith(('eu', 'au', 'eau')):
        variants.add(word + 'x')
    if word.endswith('al'):
        variants.add(word[:-2] + 'aux')
    return variants


def check_xianxia_terms(en_text, fr_text, glossary):
    """Check if xianxia glossary terms present in EN are rendered in FR."""
    en_lower = en_text.lower()
    fr_lower = fr_text.lower()
    missing_terms = []

    for en_term, entry in glossary.items():
        en_term_lower = en_term.lower()

        # Use word-boundary match for short terms to avoid false positives
        if len(en_term_lower) <= 4:
            pattern = re.compile(r'\b' + re.escape(en_term_lower) + r'\b')
        else:
            pattern = re.compile(re.escape(en_term_lower))

        if not pattern.search(en_lower):
            continue  # Term not present in EN source, skip

        # Check if any FR equivalent appears in FR text
        fr_equivs = [entry['fr'].lower()]
        if 'aliases' in entry:
            fr_equivs.extend(a.lower() for a in entry['aliases'])

        # Expand with French plural variants for short terms
        expanded_fr = set()
        for fr_eq in set(fr_equivs):  # dedup
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
                'expected_fr': entry['fr'],
                'category': entry.get('category', 'unknown'),
            })

    return missing_terms


def check_anglicisms(text):
    """Detect residual English connectives/adverbs in FR text."""
    text_lower = text.lower()
    found = []

    for word in ANGLICISM_WORDS:
        pattern = re.compile(r'\b' + re.escape(word.lower()) + r'\b')
        matches = pattern.findall(text_lower)
        if matches:
            found.append({'word': word, 'count': len(matches)})

    return found


def check_calque_sentences(en_text, fr_text):
    """Check for calque sentences (too-long, mirroring EN structure)."""
    en_sentences = split_sentences(en_text)
    fr_sentences = split_sentences(fr_text)

    en_avg = sum(len(s.split()) for s in en_sentences) / len(en_sentences) if en_sentences else 0
    fr_avg = sum(len(s.split()) for s in fr_sentences) / len(fr_sentences) if fr_sentences else 0

    ratio = fr_avg / en_avg if en_avg > 0 else 0

    long_fr_sentences = [
        {'length': len(s.split()), 'text': s[:200] + '...' if len(s) > 200 else s}
        for s in fr_sentences if len(s.split()) > 60
    ]

    calque_detected = fr_avg > 30 and ratio > 0.9

    return {
        'en_avg_sentence_len': round(en_avg, 1),
        'fr_avg_sentence_len': round(fr_avg, 1),
        'ratio': round(ratio, 3),
        'calque_detected': calque_detected,
        'long_sentences_count': len(long_fr_sentences),
        'long_sentences': long_fr_sentences[:5],
    }


def review_chapter(ch_num, site_path, wuxia_path, nf_path, prev_site_text, next_site_text, glossary):
    """
    Deep review of a single chapter.
    Returns (issues, calque_info) tuple.
    """
    site_text = read_body(site_path)
    en_text = read_body(wuxia_path)
    nf_text = read_body(nf_path)

    if not site_text or not en_text:
        return [{'chapter': ch_num, 'severity': 'critical', 'type': 'empty_source',
                 'detail': 'Chapitre vide ou source EN manquante'}], None

    site_paras = get_paras(site_text)
    en_paras = get_paras(en_text)
    nf_paras = get_paras(nf_text) if nf_text else []
    site_nouns = extract_proper_nouns(site_text)

    issues = []

    # === 1. Omission check: significant size difference ===
    ratio = len(site_text) / len(en_text) if len(en_text) > 0 else 1
    if ratio < 0.80:
        issues.append({
            'chapter': ch_num,
            'severity': 'high',
            'type': 'omission',
            'detail': f'Chapitre FR significativement plus court que EN (ratio {ratio:.2f}, {len(site_text)}c vs {len(en_text)}c)'
        })

    # === 2. Paragraph count anomaly ===
    para_ratio = len(site_paras) / len(en_paras) if en_paras else 1
    if para_ratio < 0.60:
        issues.append({
            'chapter': ch_num,
            'severity': 'medium',
            'type': 'merged_paragraphs',
            'detail': f'Paragraphes très fusionnés: {len(site_paras)} vs {len(en_paras)} EN'
        })

    # === 3. Number consistency with EN ===
    en_numbers = extract_numbers(en_text)
    site_numbers = extract_numbers(site_text)
    missing_numbers = en_numbers - site_numbers
    if len(missing_numbers) > 5 and len(en_numbers) > 10:
        issues.append({
            'chapter': ch_num,
            'severity': 'low',
            'type': 'missing_numbers',
            'detail': f'{len(missing_numbers)} nombres EN absents du FR (sur {len(en_numbers)})'
        })

    # === 4. Cross-reference with NF ===
    if nf_text:
        nf_nouns = extract_proper_nouns(nf_text)
        site_nouns_set = set(site_nouns.keys())
        nf_nouns_set = set(nf_nouns.keys())
        en_nouns = extract_proper_nouns(en_text)
        # Filter out common English sentence-start words that aren't real proper nouns
        _ENGLISH_COMMON = {'After', 'They', 'This', 'That', 'These', 'Those', 'There', 'Here',
            'When', 'Where', 'While', 'Although', 'Though', 'However', 'Because',
            'Since', 'Before', 'Until', 'Unless', 'During', 'Without', 'Within',
            'Then', 'Now', 'But', 'And', 'Not', 'Also', 'Even', 'Only', 'Just',
            'Still', 'Yet', 'Each', 'Every', 'Both', 'Some', 'Many', 'Much',
            'More', 'Most', 'Other', 'Such', 'Into', 'Like', 'Over', 'Under',
            'Above', 'Below', 'Between', 'Through', 'Behind', 'Beyond',
            'Upon', 'Against', 'Among', 'Along', 'Inside', 'Outside',
            'About', 'Across', 'Around', 'Away', 'Down', 'Back', 'Off',
            'Already', 'Always', 'Never', 'Ever', 'Often', 'Once', 'Again',
            'First', 'Next', 'Last', 'Might', 'Could', 'Would', 'Should',
            'Must', 'Shall', 'Will', 'Can', 'May', 'Did', 'Was', 'Were',
            'Has', 'Had', 'Have', 'Does', 'Said', 'One', 'Two', 'Three',
            'Very', 'Too', 'Well', 'Almost', 'Rather', 'Quite', 'Really',
            'Something', 'Anything', 'Nothing', 'Everything', 'Someone',
            'Anyone', 'Everyone', 'Nobody', 'Somehow', 'Anyhow', 'Else',
            'His', 'Her', 'Its', 'Their', 'Your', 'Our', 'Myself', 'Himself',
            'Itself', 'Ourselves', 'Themselves', 'Yourself', 'Perhaps',
            'Maybe', 'Indeed', 'Thus', 'Hence', 'Therefore',
            'Meanwhile', 'Moreover', 'Nevertheless', 'Furthermore', 'Instead',
            'Otherwise', 'Besides', 'Except', 'Despite', 'Throughout'}
        en_only = set(en_nouns.keys()) - site_nouns_set - nf_nouns_set
        significant_en_only = {n for n in en_only if en_nouns[n] >= 3 and len(n) > 3 and n not in _ENGLISH_COMMON}
        if len(significant_en_only) >= 3:
            issues.append({
                'chapter': ch_num,
                'severity': 'low',
                'type': 'names_missing_in_both_fr',
                'detail': f'Noms EN absents des deux FR: {", ".join(sorted(significant_en_only)[:5])}'
            })

    # === 5. Check for untranslated English words ===
    fr_words = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'est', 'en', 'au', 'aux',
                'ce', 'il', 'elle', 'ils', 'elles', 'que', 'qui', 'dans', 'sur', 'pas', 'ne', 'se',
                'son', 'sa', 'ses', 'leur', 'leurs', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes',
                'nous', 'vous', 'je', 'tu', 'a', 'ont', 'sont',
                'plus', 'mais', 'ou', 'donc', 'car', 'ni', 'or', 'si', 'très', 'tout', 'tous',
                'avec', 'sans', 'pour', 'par', 'sur', 'sous', 'entre', 'vers', 'chez',
                'bien', 'mal', 'peu', 'trop', 'assez', 'déjà', 'encore', 'toujours', 'jamais',
                'aussi', 'ainsi', 'alors', 'après', 'avant', 'pendant', 'depuis', 'selon',
                'Wang', 'Lin', 'Tie', 'Zhu', 'Dao', 'Yun', 'Tian', 'Fen', 'Hou',
                'Joss', 'Yang', 'Yin', 'Nirvana', 'Karma', 'Samsara', 'Ji', 'Qi',
                'All', 'Seer', 'Situ', 'Nan', 'Liu', 'Mei', 'Qing', 'Shui', 'Yi',
                'Sun', 'Dazhu', 'Teng', 'Huayuan', 'Tuo', 'Sen', 'Hao', 'Ping', 'Zhuo',
                'Zhang', 'Hu', 'Zhou', 'Ru', 'Rui', 'Qian', 'Mei', 'Lian', 'Daozhen', 'Su',
                'Hongdie', 'Muwan', 'Xuan', 'Luo', 'Yao', 'Ling', 'Dong',
                'Suzaku', 'Vermillon', 'Bird', 'Azure', 'Dragon', 'White', 'Tiger', 'Black', 'Tortoise'}

    en_words_in_fr = re.findall(r'\b[A-Za-z]+\b', site_text)
    potential_untranslated = []
    for word in en_words_in_fr:
        if len(word) >= 4 and word.lower() not in fr_words and word[0].isupper():
            if word not in site_nouns:
                potential_untranslated.append(word)

    if len(potential_untranslated) > 5:
        issues.append({
            'chapter': ch_num,
            'severity': 'low',
            'type': 'possible_untranslated',
            'detail': f'Mots potentiellement non traduits: {", ".join(potential_untranslated[:8])}'
        })

    # === NEW: 6. Xianxia terms not rendered ===
    missing_terms = check_xianxia_terms(en_text, site_text, glossary)
    if len(missing_terms) > 3:
        issues.append({
            'chapter': ch_num,
            'severity': 'medium',
            'type': 'xianxia_terms_missing',
            'detail': f'{len(missing_terms)} termes xianxia non rendus sur {len(glossary)}',
            'missing_terms': missing_terms,
        })
    elif len(missing_terms) > 0:
        issues.append({
            'chapter': ch_num,
            'severity': 'low',
            'type': 'xianxia_terms_missing',
            'detail': f'{len(missing_terms)} termes xianxia non rendus',
            'missing_terms': missing_terms,
        })

    # === NEW: 7. Residual anglicisms ===
    anglicisms = check_anglicisms(site_text)
    total_anglicism_hits = sum(a['count'] for a in anglicisms)
    if total_anglicism_hits > 2:
        issues.append({
            'chapter': ch_num,
            'severity': 'medium',
            'type': 'anglicisms',
            'detail': f'{total_anglicism_hits} occurrences d\'anglicismes: {", ".join(a["word"] for a in anglicisms)}',
            'anglicisms': anglicisms,
        })
    elif total_anglicism_hits > 0:
        issues.append({
            'chapter': ch_num,
            'severity': 'low',
            'type': 'anglicisms',
            'detail': f'{total_anglicism_hits} anglicisme(s): {", ".join(a["word"] for a in anglicisms)}',
            'anglicisms': anglicisms,
        })

    # === NEW: 8. Calque sentences ===
    calque_info = check_calque_sentences(en_text, site_text)
    if calque_info['calque_detected']:
        issues.append({
            'chapter': ch_num,
            'severity': 'medium',
            'type': 'calque_sentences',
            'detail': f'FR avg {calque_info["fr_avg_sentence_len"]} mots/phrase, EN avg {calque_info["en_avg_sentence_len"]} (ratio {calque_info["ratio"]:.2f})',
            'calque_info': calque_info,
        })
    if calque_info['long_sentences_count'] > 0:
        issues.append({
            'chapter': ch_num,
            'severity': 'low',
            'type': 'long_sentences',
            'detail': f'{calque_info["long_sentences_count"]} phrases > 60 mots',
            'calque_info': calque_info,
        })

    # === NEW: 9. Poetic variety ===
    site_words = re.findall(r'\b[a-zàâäéèêëîïôöùûüç]+\b', site_text.lower())
    words_count = len(site_words)
    if words_count > 500:
        ttr, hapax = compute_lexical_diversity(site_text)
        variety_info = {'ttr': round(ttr, 4), 'hapax_ratio': round(hapax, 4), 'word_count': words_count}
        if ttr < 0.35:
            issues.append({
                'chapter': ch_num,
                'severity': 'low',
                'type': 'poetic_variety_low',
                'detail': f'TTR={ttr:.3f}, hapax={hapax:.3f} (vocabulaire répétitif)',
                'variety_info': variety_info,
            })

    return issues, calque_info


def triage_chapter(issues):
    """Assign triage level based on issues found.
    - RED: any critical/high severity, OR >3 medium issues
    - YELLOW: 1-3 medium issues, no critical/high
    - GREEN: no issues or only low-severity
    """
    if not issues:
        return 'GREEN'

    severities = Counter(i.get('severity', 'low') for i in issues)

    if severities.get('critical', 0) > 0 or severities.get('high', 0) > 0:
        return 'RED'
    if severities.get('medium', 0) > 3:
        return 'RED'

    if severities.get('medium', 0) > 0:
        return 'YELLOW'

    return 'GREEN'


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample', type=int, default=0)
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--output', type=str, default=None)
    args = parser.parse_args()

    print("Construction des index...")
    wuxia_map, site_map, nf_map, site_tome_map = build_maps()
    print(f"  Wuxia: {len(wuxia_map)} | Site: {len(site_map)} | NF: {len(nf_map)}")

    print("Chargement du glossaire...")
    glossary = load_glossary()
    print(f"  {len(glossary)} termes xianxia chargés")

    # === Chapter count consistency check ===
    print("\n=== VERIFICATION COHERENCE CHAPITRES EN<->FR ===")
    consistency_issues = check_chapter_consistency(wuxia_map, site_map)
    if consistency_issues:
        for ci in consistency_issues:
            print(f"  !! Tome {ci['tome']}: EN={ci['en_count']} FR={ci['fr_count']} - {ci['detail']}")
    else:
        print("  [OK] Coherence parfaite EN<->FR")

    all_chapters = sorted(set(site_map.keys()) & set(wuxia_map.keys()))

    if args.sample > 0:
        import random; random.seed(42)
        all_chapters = sorted(random.sample(all_chapters, min(args.sample, len(all_chapters))))
    elif not args.full:
        import random; random.seed(42)
        all_chapters = sorted(random.sample(all_chapters, min(500, len(all_chapters))))

    print(f"\nRevue de {len(all_chapters)} chapitres...")

    all_issues = []
    chapter_results = {}
    prev_site_text = None

    for i, ch_num in enumerate(all_chapters):
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(all_chapters)}...")

        next_ch = ch_num + 1
        next_site_text = read_body(site_map.get(next_ch)) if next_ch in site_map else None

        issues, calque_info = review_chapter(
            ch_num,
            site_map.get(ch_num),
            wuxia_map.get(ch_num),
            nf_map.get(ch_num),
            prev_site_text,
            next_site_text,
            glossary
        )

        all_issues.extend(issues)
        tome = site_tome_map.get(ch_num, get_tome(ch_num))
        triage = triage_chapter(issues)
        nf_available = ch_num in nf_map
        nf_reliable = not (tome and tome >= 7)  # NF unreliable for T7+

        chapter_results[str(ch_num)] = {
            'tome': tome,
            'triage': triage,
            'issue_count': len(issues),
            'severity_counts': dict(Counter(i.get('severity', 'low') for i in issues)),
            'nf_available': nf_available,
            'nf_reliable': nf_reliable,
            'issues': issues,
        }

        prev_site_text = read_body(site_map.get(ch_num))

    # === Summarize ===
    by_severity = Counter(i.get('severity', 'low') for i in all_issues)
    by_type = Counter(i.get('type', 'unknown') for i in all_issues)
    chapters_affected = len(set(i['chapter'] for i in all_issues))

    print(f"\n=== RÉSULTATS ===")
    print(f"Chapitres revus: {len(all_chapters)}")
    print(f"Chapitres avec problèmes: {chapters_affected}")
    print(f"Total problèmes: {len(all_issues)}")
    print(f"\nPar sévérité:")
    for sev in ['critical', 'high', 'medium', 'low']:
        print(f"  {sev}: {by_severity.get(sev, 0)}")
    print(f"\nPar type:")
    for typ, count in by_type.most_common():
        print(f"  {typ}: {count}")

    # Triage summary
    triage_counts = Counter(r['triage'] for r in chapter_results.values())
    print(f"\n=== TRIAGE ===")
    print(f"  RED:    {triage_counts.get('RED', 0)}")
    print(f"  YELLOW: {triage_counts.get('YELLOW', 0)}")
    print(f"  GREEN:  {triage_counts.get('GREEN', 0)}")

    # Triage per tome
    print(f"\n=== TRIAGE PAR TOME ===")
    tome_triage = defaultdict(lambda: Counter())
    for r in chapter_results.values():
        if r['tome']:
            tome_triage[r['tome']][r['triage']] += 1
    for tome in sorted(tome_triage.keys()):
        tc = tome_triage[tome]
        total = sum(tc.values())
        print(f"  Tome {tome:2d}: RED={tc.get('RED',0):4d} | YELLOW={tc.get('YELLOW',0):4d} | GREEN={tc.get('GREEN',0):4d} | Total={total:4d}")

    # Show critical/high issues
    critical_high = [i for i in all_issues if i.get('severity') in ('critical', 'high')]
    if critical_high:
        print(f"\n=== PROBLÈMES CRITIQUES/HAUTS ({len(critical_high)}) ===")
        for issue in sorted(critical_high, key=lambda x: x['chapter'])[:30]:
            print(f"  ch{issue['chapter']:04d} [{issue['severity']}] {issue['type']}: {issue['detail']}")

    # Save output
    output = {
        'total_reviewed': len(all_chapters),
        'chapters_affected': chapters_affected,
        'total_issues': len(all_issues),
        'by_severity': dict(by_severity),
        'by_type': dict(by_type),
        'triage_summary': dict(triage_counts),
        'triage_per_tome': {str(k): dict(v) for k, v in sorted(tome_triage.items())},
        'consistency_issues': consistency_issues,
        'chapter_results': chapter_results,
        'issues': sorted(all_issues, key=lambda x: (x.get('severity', 'low'), x['chapter'])),
    }

    output_path = args.output or str(OUTPUT_DIR / 'semantic-review-full.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nRapport: {output_path}")


if __name__ == '__main__':
    main()
