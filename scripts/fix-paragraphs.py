#!/usr/bin/env python3
"""
Correction des paragraphes fusionnés — V3.
Approche robuste : divise le texte FR en phrases, puis regroupe en N paragraphes
(où N = nombre de paragraphes dans la source EN), en utilisant des heuristiques
de coupure (dialogues, changements de lieu/personnage, phrases longues).

Usage: python scripts/fix-paragraphs.py [--dry-run] [--chapter N] [--all]
"""

import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = PROJECT_ROOT / "src" / "content" / "chapters"
WUXIA_DIR = Path(r"C:\Users\Marc\Downloads\Renegade Immortal\wuxiaworld")
SCORES_PATH = PROJECT_ROOT / "reports" / "chapter-scores-full.json"


def read_file_raw(path):
    if not path or not os.path.exists(path):
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def read_body(path):
    if not path or not os.path.exists(path):
        return "", ""
    content = read_file_raw(path)
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            return parts[1].strip(), parts[2].strip()
    return "", content.strip()


def get_paragraphs(text):
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    paras = [p for p in paras if not re.match(r'^(Chapter|Chapitre)\s+\d+', p, re.IGNORECASE)]
    return paras


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


def split_into_sentences(text):
    """Split French text into sentences."""
    # Split on sentence-ending punctuation followed by space and capital letter
    # Handle: . ! ? » followed by space and uppercase or «
    sentences = re.split(r'(?<=[.!?\xbb])\s+(?=[\xab"\u201c]*(?:[A-Z\u00c0\u00c2\u00c4\u00c9\u00c8\u00ca\u00cb\u00ce\u00cf\u00d4\u00d6\u00d9\u00db\u00dc\u00c7]|\d+|—|\xab))', text)
    # Merge back small fragments
    merged = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if merged and len(s) < 30 and not s[0].isupper():
            merged[-1] += ' ' + s
        else:
            merged.append(s)
    return merged


def score_break_point(sentences, i):
    """
    Score how good a paragraph break would be after sentence i.
    Higher score = better break point.
    """
    if i >= len(sentences) - 1:
        return 0
    
    score = 0
    current = sentences[i]
    next_s = sentences[i + 1] if i + 1 < len(sentences) else ""
    
    # 1. Dialogue markers: « or » at end of sentence = strong break
    if current.rstrip().endswith('»'):
        score += 30
    if next_s.lstrip().startswith('«'):
        score += 30
    
    # 2. Scene change indicators
    scene_words = ['pendant ce temps', 'au même moment', 'ailleurs', 'soudain',
                   'à cet instant', 'le lendemain', 'plus tard', 'ce jour-là',
                   'la nuit', 'le jour', 'quelques jours', 'plusieurs jours']
    for word in scene_words:
        if word in next_s.lower()[:80]:
            score += 20
            break
    
    # 3. Subject change: different proper noun at start
    current_names = set(re.findall(r'\b[A-Z][a-zàâäéèêëîïôöùûüç]{2,}\b', current[-100:]))
    next_names = set(re.findall(r'\b[A-Z][a-zàâäéèêëîïôöùûüç]{2,}\b', next_s[:100]))
    if current_names and next_names and not (current_names & next_names):
        score += 15
    
    # 4. Long sentence = good break point
    if len(current) > 200:
        score += 10
    
    # 5. Short next sentence starting with dialogue
    if len(next_s) < 60 and ('«' in next_s or '"' in next_s):
        score += 10
    
    return score


def regroup_sentences(sentences, target_paragraphs):
    """
    Regroup sentences into approximately target_paragraphs paragraphs.
    Uses scoring to find best break points.
    """
    if len(sentences) <= target_paragraphs:
        return sentences  # Can't split further
    
    # We need (target_paragraphs - 1) break points
    num_breaks = target_paragraphs - 1
    
    # Score all possible break points
    break_scores = []
    for i in range(len(sentences) - 1):
        score = score_break_point(sentences, i)
        break_scores.append((i, score))
    
    # Sort by score descending
    break_scores.sort(key=lambda x: -x[1])
    
    # Take top N break points, but ensure they're spread out
    # Minimum distance between breaks: total_sentences / (num_breaks * 2)
    min_distance = max(1, len(sentences) // (num_breaks * 3))
    
    selected_breaks = []
    for idx, score in break_scores:
        if len(selected_breaks) >= num_breaks:
            break
        # Check distance from existing breaks
        too_close = any(abs(idx - b) < min_distance for b in selected_breaks)
        if not too_close and score > 0:
            selected_breaks.append(idx)
    
    # If we don't have enough good breaks, add evenly-spaced ones
    if len(selected_breaks) < num_breaks:
        step = len(sentences) // (num_breaks + 1)
        for j in range(1, num_breaks + 1):
            pos = j * step
            if pos < len(sentences) and pos not in selected_breaks:
                selected_breaks.append(pos)
    
    selected_breaks = sorted(selected_breaks)[:num_breaks]
    
    # Build paragraphs
    paragraphs = []
    start = 0
    for bp in selected_breaks:
        para = ' '.join(sentences[start:bp+1]).strip()
        if para:
            paragraphs.append(para)
        start = bp + 1
    
    # Last paragraph
    para = ' '.join(sentences[start:]).strip()
    if para:
        paragraphs.append(para)
    
    return paragraphs


def fix_chapter(ch_num, site_path, wuxia_path, dry_run=False):
    """Fix paragraph splitting."""
    site_fm, site_body = read_body(site_path)
    _, en_body = read_body(wuxia_path)
    
    if not site_body:
        return False, "Site chapter empty", None
    if not en_body:
        return False, "EN source not available", None
    
    site_paras = get_paragraphs(site_body)
    en_paras = get_paragraphs(en_body)
    
    target_count = len(en_paras)
    current_count = len(site_paras)
    para_ratio = current_count / target_count if target_count else 1
    
    if para_ratio >= 0.80:
        return True, f"Déjà bon ({current_count}/{target_count} paras, ratio {para_ratio:.2f})", None
    
    # Split into sentences and regroup
    sentences = split_into_sentences(site_body)
    
    if len(sentences) < target_count:
        return False, f"Pas assez de phrases ({len(sentences)}) pour {target_count} paragraphes", None
    
    new_paras = regroup_sentences(sentences, target_count)
    new_body = '\n\n'.join(new_paras)
    new_count = len(new_paras)
    new_ratio = new_count / target_count if target_count else 1
    
    if new_count <= current_count + 1:
        return False, f"Pas d'amélioration significative ({current_count}→{new_count} paras)", None
    
    if dry_run:
        return True, f"Simulation: {current_count}→{new_count} paras (ratio {para_ratio:.2f}→{new_ratio:.2f})", new_body
    
    # Write back
    new_content = f"---\n{site_fm}\n---\n\n{new_body}\n"
    with open(site_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True, f"Corrigé: {current_count}→{new_count} paras (ratio {para_ratio:.2f}→{new_ratio:.2f})", new_body


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Correction des paragraphes fusionnés V3')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--chapter', type=int, default=0)
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()
    
    wuxia_map = build_wuxia_map()
    site_map = build_site_map()
    
    if args.chapter > 0:
        ch = args.chapter
        success, msg, new_body = fix_chapter(ch, site_map.get(ch), wuxia_map.get(ch), args.dry_run)
        print(f"Chapitre {ch}: {msg}")
        if args.dry_run and new_body:
            # Show first 3 paragraphs
            paras = new_body.split('\n\n')
            for i, p in enumerate(paras[:3]):
                print(f"\n  [Para {i+1}] {p[:150]}...")
        return
    
    if args.all:
        with open(SCORES_PATH, 'r', encoding='utf-8') as f:
            scores_data = json.load(f)
        
        to_fix = [r for r in scores_data['needs_review'] if r['quality_score'] < 70]
        print(f"Chapitres à corriger: {len(to_fix)}")
        
        fixed = 0
        skipped = 0
        failed = 0
        
        for ch_data in to_fix:
            ch_num = ch_data['chapter']
            success, msg, _ = fix_chapter(ch_num, site_map.get(ch_num), wuxia_map.get(ch_num), args.dry_run)
            
            if success and "Déjà bon" in msg:
                skipped += 1
            elif success:
                fixed += 1
            else:
                failed += 1
            print(f"  ch{ch_num:04d}: {msg}")
        
        print(f"\n=== RÉSUMÉ ===")
        print(f"Corrigés: {fixed} | Déjà bons: {skipped} | Échecs: {failed}")
        if args.dry_run:
            print("(Mode simulation)")
    else:
        print("Usage: --chapter N ou --all")


if __name__ == '__main__':
    main()
