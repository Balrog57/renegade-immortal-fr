#!/usr/bin/env python3
"""
Scoring de qualité V2 — focalisé sur les VRAIS problèmes :
1. Paragraphes excessivement fusionnés (lecture désagréable)
2. Contenu manquant (chapitres tronqués)
3. Divergence réelle vs source EN (pas juste la similarité cross-langue)

Usage: python scripts/score-chapters.py [--sample N] [--output reports/chapter-scores.json]
"""

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = PROJECT_ROOT / "src" / "content" / "chapters"
WUXIA_DIR = Path(r"C:\Users\Marc\Downloads\Renegade Immortal\wuxiaworld")
NF_DIR = PROJECT_ROOT / "novelfrance"
OUTPUT_DIR = PROJECT_ROOT / "reports"


def build_wuxia_map():
    wuxia_map = {}
    for root, dirs, files in os.walk(WUXIA_DIR):
        for f in files:
            if f.endswith('.txt'):
                m = re.match(r'(\d{4})', f)
                if m:
                    wuxia_map[int(m.group(1))] = Path(root) / f
    return wuxia_map


def build_site_map():
    site_map = {}
    for root, dirs, files in os.walk(CHAPTERS_DIR):
        for f in files:
            if f.endswith('.md'):
                m = re.match(r'(\d{4})', f)
                if m:
                    site_map[int(m.group(1))] = Path(root) / f
    return site_map


def build_nf_map():
    nf_map = {}
    if NF_DIR.exists():
        for f in os.listdir(NF_DIR):
            if f.endswith('.md'):
                m = re.match(r'ch(\d{4})', f)
                if m:
                    nf_map[int(m.group(1))] = NF_DIR / f
    return nf_map


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


def get_paragraphs(text):
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    paras = [p for p in paras if not re.match(r'^(Chapter|Chapitre)\s+\d+', p, re.IGNORECASE)]
    return paras


def score_chapter(ch_num, site_path, wuxia_path, nf_path):
    """
    Score basé sur des métriques actionnables.
    """
    site_text = read_body(site_path)
    wuxia_text = read_body(wuxia_path)
    nf_text = read_body(nf_path)

    if not site_text:
        return {'chapter': ch_num, 'error': 'EMPTY', 'quality_score': 0, 'needs_review': True}

    if not wuxia_text:
        return {'chapter': ch_num, 'error': 'NO_EN_SOURCE', 'quality_score': 50, 'needs_review': True}

    site_paras = get_paragraphs(site_text)
    wuxia_paras = get_paragraphs(wuxia_text)
    nf_paras = get_paragraphs(nf_text) if nf_text else []

    wuxia_len = len(wuxia_text)
    site_len = len(site_text)

    issues = []
    deductions = 0  # Start at 100, deduct for issues

    # === 1. Paragraph fusion check ===
    # If site has significantly fewer paragraphs but similar total chars,
    # paragraphs are being merged (formatting issue, not translation error)
    para_ratio = len(site_paras) / len(wuxia_paras) if wuxia_paras else 1
    avg_en_para = wuxia_len / len(wuxia_paras) if wuxia_paras else 0
    avg_site_para = site_len / len(site_paras) if site_paras else 0

    if para_ratio < 0.5:
        deductions += 25
        issues.append(f"Paragraphes très fusionnés: {len(site_paras)} vs {len(wuxia_paras)} EN (ratio {para_ratio:.2f})")
    elif para_ratio < 0.65:
        deductions += 15
        issues.append(f"Paragraphes fusionnés: {len(site_paras)} vs {len(wuxia_paras)} EN (ratio {para_ratio:.2f})")
    elif para_ratio < 0.80:
        deductions += 5
        issues.append(f"Paragraphes légèrement fusionnés: {len(site_paras)} vs {len(wuxia_paras)} EN (ratio {para_ratio:.2f})")

    # === 2. Content completeness ===
    ratio = site_len / wuxia_len if wuxia_len > 0 else 0
    if ratio < 0.85:
        deductions += 30
        issues.append(f"Contenu potentiellement tronqué (ratio {ratio:.2f})")
    elif ratio < 0.95:
        deductions += 10
        issues.append(f"Contenu légèrement court (ratio {ratio:.2f})")
    elif ratio > 1.60:
        deductions += 10
        issues.append(f"Contenu anormalement long (ratio {ratio:.2f})")

    # === 3. First/last paragraph alignment check ===
    # Only flag if the chapter appears to be completely wrong (different topic)
    # Check using key content words, not just proper names
    first_mismatch = False
    if wuxia_paras and site_paras:
        # Extract significant words (4+ chars) from first paragraph
        en_words = set(re.findall(r'\b[a-z]{4,}\b', wuxia_paras[0][:150].lower()))
        fr_words = set(re.findall(r'\b[a-zàâäéèêëîïôöùûüç]{4,}\b', site_paras[0][:150].lower()))
        # If there's almost no overlap in significant words, flag it
        if en_words and fr_words:
            overlap = en_words & fr_words
            # For EN→FR, we expect low overlap due to translation, but not zero
            # If < 2 words overlap out of many, something might be wrong
            if len(en_words) >= 5 and len(fr_words) >= 5 and len(overlap) <= 1:
                first_mismatch = True
                deductions += 20
                issues.append(f"Début de chapitre potentiellement décalé (peu de mots communs avec EN)")

    # === 4. NF cross-reference (if available) ===
    nf_issue = False
    if nf_text and nf_paras:
        # Check if NF and site have similar paragraph counts
        nf_para_ratio = len(nf_paras) / len(wuxia_paras) if wuxia_paras else 1
        # If NF has good paragraph ratio but site doesn't, NF can be used as reference
        if nf_para_ratio > 0.80 and para_ratio < 0.65:
            issues.append(f"NovelFrance a {len(nf_paras)} paragraphes (bon ratio {nf_para_ratio:.2f}) — utilisable comme référence")

    quality_score = max(0, 100 - deductions)
    needs_review = quality_score < 70

    return {
        'chapter': ch_num,
        'quality_score': quality_score,
        'needs_review': needs_review,
        'para_ratio': round(para_ratio, 2),
        'size_ratio': round(ratio, 2),
        'en_paras': len(wuxia_paras),
        'site_paras': len(site_paras),
        'nf_paras': len(nf_paras),
        'en_chars': wuxia_len,
        'site_chars': site_len,
        'nf_chars': len(nf_text),
        'avg_en_para_len': round(avg_en_para),
        'avg_site_para_len': round(avg_site_para),
        'issues': issues,
        'file': str(site_path.relative_to(PROJECT_ROOT)) if site_path else None,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scoring de qualité V2')
    parser.add_argument('--sample', type=int, default=0)
    parser.add_argument('--output', type=str, default=None)
    parser.add_argument('--min-score', type=int, default=0)
    parser.add_argument('--full', action='store_true', help='Scorer tous les 2088 chapitres')
    args = parser.parse_args()

    print("Construction des index...")
    wuxia_map = build_wuxia_map()
    site_map = build_site_map()
    nf_map = build_nf_map()
    print(f"  Wuxiaworld: {len(wuxia_map)} | Site: {len(site_map)} | NF: {len(nf_map)}")

    all_chapters = sorted(set(site_map.keys()) & set(wuxia_map.keys()))

    if args.sample > 0:
        import random
        random.seed(42)
        all_chapters = sorted(random.sample(all_chapters, min(args.sample, len(all_chapters))))
    elif not args.full:
        # Default: sample 200
        import random
        random.seed(42)
        all_chapters = sorted(random.sample(all_chapters, 200))

    print(f"Scoring {len(all_chapters)} chapitres...")

    results = []
    for i, ch_num in enumerate(all_chapters):
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(all_chapters)}...")
        result = score_chapter(ch_num, site_map.get(ch_num), wuxia_map.get(ch_num), nf_map.get(ch_num))
        results.append(result)

    # Stats
    scores = [r['quality_score'] for r in results]
    import statistics

    buckets = {'100': 0, '90-99': 0, '80-89': 0, '70-79': 0, '60-69': 0, '<60': 0}
    for s in scores:
        if s == 100: buckets['100'] += 1
        elif s >= 90: buckets['90-99'] += 1
        elif s >= 80: buckets['80-89'] += 1
        elif s >= 70: buckets['70-79'] += 1
        elif s >= 60: buckets['60-69'] += 1
        else: buckets['<60'] += 1

    needs_review = [r for r in results if r['needs_review']]

    output = {
        'stats': {
            'total_scored': len(all_chapters),
            'mean_score': round(statistics.mean(scores), 1),
            'median_score': round(statistics.median(scores), 1),
            'min_score': min(scores),
            'max_score': max(scores),
            'distribution': buckets,
            'needs_review_count': len(needs_review),
        },
        'needs_review': sorted(needs_review, key=lambda r: r['quality_score']),
        'all_chapters': sorted(results, key=lambda r: r['quality_score']),
    }

    output_path = args.output or str(OUTPUT_DIR / 'chapter-scores.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== RÉSULTATS ===")
    print(f"Chapitres scorés: {len(all_chapters)}")
    print(f"Score moyen: {output['stats']['mean_score']}")
    print(f"Score médian: {output['stats']['median_score']}")
    print(f"\nDistribution:")
    for bucket, count in buckets.items():
        bar = '█' * (count // max(1, len(all_chapters) // 40))
        print(f"  {bucket:>6s}: {count:4d} ({count/len(all_chapters)*100:5.1f}%) {bar}")

    print(f"\nChapitres nécessitant revue: {len(needs_review)}")
    if needs_review:
        print(f"\n=== TOP 15 À REVOIR ===")
        for r in needs_review[:15]:
            print(f"  ch{r['chapter']:04d}: score={r['quality_score']} | {', '.join(r['issues'])}")

    print(f"\nRapport: {output_path}")


if __name__ == '__main__':
    main()
