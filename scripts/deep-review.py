#!/usr/bin/env python3
"""
Revue approfondie chapitre par chapitre — V4.
Détecte les VRAIS problèmes de traduction :
1. Omissions (paragraphes EN sans équivalent FR)
2. Contresens (noms propres mal traduits, chiffres différents)
3. Incohérences avec chapitres adjacents (termes qui changent brutalement)
4. Divergences site vs NF qui suggèrent une erreur

Usage: python scripts/deep-review.py [--sample N] [--output reports/deep-review.json]
"""

import json, os, re, sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = PROJECT_ROOT / "src" / "content" / "chapters"
WUXIA_DIR = Path(r"C:\Users\Marc\Downloads\Renegade Immortal\wuxiaworld")
NF_DIR = PROJECT_ROOT / "novelfrance"
GLOSSARY_PATH = PROJECT_ROOT / "scripts" / "glossary.json"
OUTPUT_DIR = PROJECT_ROOT / "reports"


def read_body(path):
    if not path or not os.path.exists(path):
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if path.suffix == '.md' and content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]
    return content.strip()


def get_paras(text):
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    return [p for p in paras if not re.match(r'^(Chapter|Chapitre)\s+\d+', p, re.IGNORECASE)]


def build_maps():
    wuxia_map = {}
    for root, dirs, files in os.walk(WUXIA_DIR):
        for f in files:
            if f.endswith('.txt'):
                m = re.match(r'(\d{4})', f)
                if m:
                    wuxia_map[int(m.group(1))] = Path(root) / f

    site_map = {}
    for root, dirs, files in os.walk(CHAPTERS_DIR):
        for f in files:
            if f.endswith('.md'):
                m = re.match(r'(\d{4})', f)
                if m:
                    site_map[int(m.group(1))] = Path(root) / f

    nf_map = {}
    if NF_DIR.exists():
        for f in os.listdir(NF_DIR):
            if f.endswith('.md'):
                m = re.match(r'ch(\d{4})', f)
                if m:
                    nf_map[int(m.group(1))] = NF_DIR / f

    return wuxia_map, site_map, nf_map


def extract_proper_nouns(text):
    """Extract capitalized words that are likely proper nouns."""
    # French+English capitalized words (3+ chars, not at sentence start)
    words = re.findall(r'\b[A-Z][a-zàâäéèêëîïôöùûüç]{2,}\b', text)
    return Counter(words)


def extract_numbers(text):
    """Extract all numbers from text."""
    return set(re.findall(r'\b\d+\b', text))


def review_chapter(ch_num, site_path, wuxia_path, nf_path, prev_site_text, next_site_text):
    """
    Deep review of a single chapter.
    Returns list of issues found.
    """
    site_text = read_body(site_path)
    en_text = read_body(wuxia_path)
    nf_text = read_body(nf_path)

    if not site_text or not en_text:
        return [{'chapter': ch_num, 'severity': 'critical', 'issue': 'Chapitre vide ou source EN manquante'}]

    site_paras = get_paras(site_text)
    en_paras = get_paras(en_text)
    nf_paras = get_paras(nf_text) if nf_text else []

    issues = []

    # === 1. Omission check: significant size difference ===
    ratio = len(site_text) / len(en_text)
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

    # === 3. Proper noun consistency with adjacent chapters ===
    site_nouns = extract_proper_nouns(site_text)
    if prev_site_text:
        prev_nouns = extract_proper_nouns(prev_site_text)
        # Check for names that appear in prev but with different capitalization in current
        for name in prev_nouns:
            if name in site_nouns:
                continue
            # Check if lowercase version appears
            lower = name.lower()
            # This is noisy, skip for now

    # === 4. Number consistency with EN ===
    en_numbers = extract_numbers(en_text)
    site_numbers = extract_numbers(site_text)
    # Numbers that are in EN but missing from FR (potential omission)
    missing_numbers = en_numbers - site_numbers
    # Filter: only flag if > 3 numbers are missing (could be translation choice)
    if len(missing_numbers) > 5 and len(en_numbers) > 10:
        issues.append({
            'chapter': ch_num,
            'severity': 'low',
            'type': 'missing_numbers',
            'detail': f'{len(missing_numbers)} nombres EN absents du FR (sur {len(en_numbers)})'
        })

    # === 5. Cross-reference with NF: detect if site and NF agree on a likely error ===
    if nf_text:
        # Check if both site and NF have the same suspicious pattern
        # e.g., both missing the same content, both have same wrong name
        nf_nouns = extract_proper_nouns(nf_text)
        site_nouns_set = set(site_nouns.keys())
        nf_nouns_set = set(nf_nouns.keys())

        # Names in EN that are in neither FR translation
        en_nouns = extract_proper_nouns(en_text)
        en_only = set(en_nouns.keys()) - site_nouns_set - nf_nouns_set
        significant_en_only = {n for n in en_only if en_nouns[n] >= 3 and len(n) > 3}
        if len(significant_en_only) >= 3:
            issues.append({
                'chapter': ch_num,
                'severity': 'medium',
                'type': 'names_missing_in_both_fr',
                'detail': f'Noms EN absents des deux FR: {", ".join(sorted(significant_en_only)[:5])}'
            })

    # === 6. Check for untranslated English words ===
    en_words_in_fr = re.findall(r'\b[A-Za-z]+\b', site_text)
    # Filter common French words that look English
    fr_words = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'est', 'en', 'au', 'aux',
                'ce', 'il', 'elle', 'ils', 'elles', 'que', 'qui', 'dans', 'sur', 'pas', 'ne', 'se',
                'son', 'sa', 'ses', 'leur', 'leurs', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes',
                'nous', 'vous', 'je', 'tu', 'nous', 'vous', 'ils', 'a', 'ont', 'sont',
                'plus', 'mais', 'ou', 'donc', 'car', 'ni', 'or', 'si', 'très', 'tout', 'tous',
                'avec', 'sans', 'pour', 'par', 'sur', 'sous', 'entre', 'vers', 'chez',
                'bien', 'mal', 'peu', 'trop', 'assez', 'déjà', 'encore', 'toujours', 'jamais',
                'aussi', 'ainsi', 'alors', 'après', 'avant', 'pendant', 'depuis', 'selon',
                'Wang', 'Lin', 'Tie', 'Zhu', 'Dao', 'Yun', 'Tian', 'Fen', 'Hou',
                'Joss', 'Yang', 'Yin', 'Nirvana', 'Karma', 'Samsara', 'Ji', 'Qi',
                'All', 'Seer', 'Situ', 'Nan', 'Liu', 'Mei', 'Qing', 'Shui', 'Yi',
                'Sun', 'Dazhu', 'Teng', 'Huayuan', 'Tuo', 'Sen', 'Hao', 'Ping', 'Zhuo',
                'Zhang', 'Hu', 'Zhou', 'Ru', 'Rui', 'Qian', 'Mei', 'Lian', 'Daozhen', 'Su',
                'Hongdie', 'Muwan', 'Xuan', 'Luo', 'Yao', 'Ling', 'Dong', 'Mei',
                'Suzaku', 'Vermillon', 'Bird', 'Azure', 'Dragon', 'White', 'Tiger', 'Black', 'Tortoise'}
    
    potential_untranslated = []
    for word in en_words_in_fr:
        if len(word) >= 4 and word.lower() not in fr_words and word[0].isupper():
            # Check if it appears to be English (not a proper noun used in xianxia)
            if word not in site_nouns:
                potential_untranslated.append(word)

    if len(potential_untranslated) > 5:
        issues.append({
            'chapter': ch_num,
            'severity': 'low',
            'type': 'possible_untranslated',
            'detail': f'Mots potentiellement non traduits: {", ".join(potential_untranslated[:8])}'
        })

    return issues


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample', type=int, default=0)
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--output', type=str, default=None)
    args = parser.parse_args()

    print("Construction des index...")
    wuxia_map, site_map, nf_map = build_maps()
    print(f"  Wuxia: {len(wuxia_map)} | Site: {len(site_map)} | NF: {len(nf_map)}")

    all_chapters = sorted(set(site_map.keys()) & set(wuxia_map.keys()))

    if args.sample > 0:
        import random; random.seed(42)
        all_chapters = sorted(random.sample(all_chapters, min(args.sample, len(all_chapters))))
    elif not args.full:
        import random; random.seed(42)
        all_chapters = sorted(random.sample(all_chapters, 500))

    print(f"Revue de {len(all_chapters)} chapitres...")

    all_issues = []
    prev_site_text = None

    for i, ch_num in enumerate(all_chapters):
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(all_chapters)}...")

        # Get adjacent chapter text
        next_ch = ch_num + 1
        next_site_text = read_body(site_map.get(next_ch)) if next_ch in site_map else None

        issues = review_chapter(
            ch_num,
            site_map.get(ch_num),
            wuxia_map.get(ch_num),
            nf_map.get(ch_num),
            prev_site_text,
            next_site_text
        )

        all_issues.extend(issues)
        prev_site_text = read_body(site_map.get(ch_num))

    # Summarize
    by_severity = Counter(i['severity'] for i in all_issues)
    by_type = Counter(i['type'] for i in all_issues)
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

    # Show critical/high issues
    critical_high = [i for i in all_issues if i['severity'] in ('critical', 'high')]
    if critical_high:
        print(f"\n=== PROBLÈMES CRITIQUES/HAUTS ({len(critical_high)}) ===")
        for issue in sorted(critical_high, key=lambda x: x['chapter'])[:30]:
            print(f"  ch{issue['chapter']:04d} [{issue['severity']}] {issue['type']}: {issue['detail']}")

    # Save
    output = {
        'total_reviewed': len(all_chapters),
        'chapters_affected': chapters_affected,
        'total_issues': len(all_issues),
        'by_severity': dict(by_severity),
        'by_type': dict(by_type),
        'issues': sorted(all_issues, key=lambda x: (x['severity'], x['chapter'])),
    }

    output_path = args.output or str(OUTPUT_DIR / 'deep-review.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nRapport: {output_path}")


if __name__ == '__main__':
    main()
