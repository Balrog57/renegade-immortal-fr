#!/usr/bin/env python3
"""
Correction automatique des chapitres 601-800 :
- Guillemets déséquilibrés (ajout de » manquants)
- Paragraphes fusionnés (regroup_sentences)
- Espaces avant ponctuation (! ? ; :)
"""
import os, re, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = PROJECT_ROOT / "src" / "content" / "chapters"
WUXIA_DIR = Path(r"C:\Users\Marc\Downloads\Renegade Immortal\wuxiaworld")

def read_body(path):
    """Lit un fichier .md et retourne (frontmatter, body)."""
    if not path or not os.path.exists(path):
        return "", ""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            return parts[1].strip(), parts[2].strip()
    return "", content.strip()

def read_body_txt(path):
    """Lit un fichier .txt et retourne le body."""
    if not path or not os.path.exists(path):
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def get_paragraphs(text):
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    return [p for p in paras if not re.match(r'^(Chapter|Chapitre)\s+\d+', p, re.IGNORECASE)]

def split_into_sentences(text):
    """Split French text into sentences."""
    sentences = re.split(r'(?<=[.!?\xbb])\s+(?=[\xab"\u201c]*(?:[A-Z\u00c0\u00c2\u00c4\u00c9\u00c8\u00ca\u00cb\u00ce\u00cf\u00d4\u00d6\u00d9\u00db\u00dc\u00c7]|\d+|—|\xab))', text)
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
    """Score how good a paragraph break would be after sentence i."""
    if i >= len(sentences) - 1:
        return 0
    score = 0
    current = sentences[i]
    next_s = sentences[i + 1] if i + 1 < len(sentences) else ""
    if current.rstrip().endswith('»'):
        score += 30
    if next_s.lstrip().startswith('«'):
        score += 30
    scene_words = ['pendant ce temps', 'au même moment', 'ailleurs', 'soudain',
                   'à cet instant', 'le lendemain', 'plus tard', 'ce jour-là',
                   'la nuit', 'le jour', 'quelques jours', 'plusieurs jours']
    for word in scene_words:
        if word in next_s.lower()[:80]:
            score += 20
            break
    current_names = set(re.findall(r'\b[A-Z][a-zàâäéèêëîïôöùûüç]{2,}\b', current[-100:]))
    next_names = set(re.findall(r'\b[A-Z][a-zàâäéèêëîïôöùûüç]{2,}\b', next_s[:100]))
    if current_names and next_names and not (current_names & next_names):
        score += 15
    if len(current) > 200:
        score += 10
    if len(next_s) < 60 and ('«' in next_s or '"' in next_s):
        score += 10
    return score

def regroup_sentences(sentences, target_paragraphs):
    """Regroup sentences into approximately target_paragraphs paragraphs."""
    if len(sentences) <= target_paragraphs:
        return sentences
    num_breaks = target_paragraphs - 1
    break_scores = []
    for i in range(len(sentences) - 1):
        score = score_break_point(sentences, i)
        break_scores.append((i, score))
    break_scores.sort(key=lambda x: -x[1])
    min_distance = max(1, len(sentences) // (num_breaks * 3))
    selected_breaks = []
    for idx, score in break_scores:
        if len(selected_breaks) >= num_breaks:
            break
        too_close = any(abs(idx - b) < min_distance for b in selected_breaks)
        if not too_close and score > 0:
            selected_breaks.append(idx)
    if len(selected_breaks) < num_breaks:
        step = len(sentences) // (num_breaks + 1)
        for j in range(1, num_breaks + 1):
            pos = j * step
            if pos < len(sentences) and pos not in selected_breaks:
                selected_breaks.append(pos)
    selected_breaks = sorted(selected_breaks)[:num_breaks]
    paragraphs = []
    start = 0
    for bp in selected_breaks:
        para = ' '.join(sentences[start:bp+1]).strip()
        if para:
            paragraphs.append(para)
        start = bp + 1
    para = ' '.join(sentences[start:]).strip()
    if para:
        paragraphs.append(para)
    return paragraphs

def fix_guillemets(text):
    """Ajoute les » manquants en fin de paragraphe."""
    lines = text.split('\n')
    fixed_lines = []
    for line in lines:
        ouvrants = line.count('«')
        fermants = line.count('»')
        if ouvrants > fermants:
            # Ajouter » manquants à la fin de la ligne
            missing = ouvrants - fermants
            line = line.rstrip() + '»' * missing
        fixed_lines.append(line)
    return '\n'.join(fixed_lines)

def fix_espaces_ponctuation(text):
    """Ajoute un espace avant ! ? ; : quand il manque."""
    # Espace avant !
    text = re.sub(r'([^\s])!', r'\1 !', text)
    # Espace avant ?
    text = re.sub(r'([^\s])\?', r'\1 ?', text)
    # Espace avant ;
    text = re.sub(r'([^\s]);', r'\1 ;', text)
    # Espace avant :
    text = re.sub(r'([^\s]):', r'\1 :', text)
    return text

def find_chapter_file(ch_num):
    """Trouve le fichier .md d'un chapitre dans la structure tome-*."""
    for root, dirs, files in os.walk(CHAPTERS_DIR):
        for f in files:
            if f.endswith('.md'):
                m = re.match(r'(\d{4})', f)
                if m and int(m.group(1)) == ch_num:
                    return Path(root) / f
    return None

def find_wuxia_file(ch_num):
    """Trouve le fichier .txt wuxia pour un chapitre."""
    for root, dirs, files in os.walk(WUXIA_DIR):
        for f in files:
            if f.endswith('.txt'):
                m = re.match(r'(\d{4})', f)
                if m and int(m.group(1)) == ch_num:
                    return Path(root) / f
    return None

def fix_chapter(ch_num):
    """Corrige tous les problèmes d'un chapitre."""
    site_path = find_chapter_file(ch_num)
    wuxia_path = find_wuxia_file(ch_num)
    
    if not site_path:
        return f"ch{ch_num:04d}: Fichier site non trouvé"
    
    fm, body = read_body(site_path)
    if not body:
        return f"ch{ch_num:04d}: Body vide"
    
    changes = []
    original_body = body
    
    # 1. Vérifier guillemets déséquilibrés
    ouvrants = body.count('«')
    fermants = body.count('»')
    if ouvrants != fermants:
        body = fix_guillemets(body)
        new_ouvrants = body.count('«')
        new_fermants = body.count('»')
        changes.append(f"Guillemets: {ouvrants}«/{fermants}» → {new_ouvrants}«/{new_fermants}»")
    
    # 2. Vérifier espaces avant ponctuation
    for punct in ['!', '?', ';', ':']:
        bad = re.findall(r'[^\s]' + re.escape(punct), body)
        if bad:
            body = fix_espaces_ponctuation(body)
            changes.append(f"Espaces avant {punct}: {len(bad)} corrigés")
            break
    
    # 3. Vérifier paragraphes fusionnés
    if wuxia_path and wuxia_path.exists():
        en_text = read_body_txt(wuxia_path)
        en_paras = get_paragraphs(en_text)
        site_paras = get_paragraphs(body)
        
        if en_paras and len(site_paras) > 0:
            para_ratio = len(site_paras) / len(en_paras) if en_paras else 1
            if para_ratio < 0.70:
                sentences = split_into_sentences(body)
                if len(sentences) >= len(en_paras):
                    new_paras = regroup_sentences(sentences, len(en_paras))
                    new_body = '\n\n'.join(new_paras)
                    new_count = len(new_paras)
                    if new_count > len(site_paras) + 1:
                        body = new_body
                        changes.append(f"Paragraphes: {len(site_paras)}→{new_count} (cible: {len(en_paras)})")
    
    if not changes:
        return f"ch{ch_num:04d}: Aucun changement nécessaire"
    
    # Écrire le fichier
    new_content = f"---\n{fm}\n---\n\n{body}\n"
    with open(site_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return f"ch{ch_num:04d}: {'; '.join(changes)}"

def main():
    # Chapitres avec problèmes
    problem_chapters = [606, 620, 626, 639, 642, 643, 667, 707, 709, 717, 758, 765, 771]
    
    print("=== Correction des chapitres 601-800 ===\n")
    
    for ch_num in problem_chapters:
        result = fix_chapter(ch_num)
        print(result)
    
    print("\n=== Vérification finale ===\n")
    
    # Re-vérifier tous les chapitres
    for ch_num in problem_chapters:
        site_path = find_chapter_file(ch_num)
        if not site_path:
            print(f"ch{ch_num:04d}: ❌ Fichier non trouvé")
            continue
        fm, body = read_body(site_path)
        if not body:
            print(f"ch{ch_num:04d}: ❌ Body vide")
            continue
        
        issues = []
        
        # Guillemets
        ouvrants = body.count('«')
        fermants = body.count('»')
        if ouvrants != fermants:
            issues.append(f"G:Guillemets ({ouvrants}«/{fermants}»)")
        
        # Espaces avant ponctuation
        for punct in ['!', '?', ';', ':']:
            bad = re.findall(r'[^\s]' + re.escape(punct), body)
            if bad:
                issues.append(f"G:Espace manquant avant {punct} ({len(bad)})")
        
        # Paragraphes
        wuxia_path = find_wuxia_file(ch_num)
        if wuxia_path:
            en_text = read_body_txt(wuxia_path)
            en_paras = get_paragraphs(en_text)
            site_paras = get_paragraphs(body)
            if en_paras:
                para_ratio = len(site_paras) / len(en_paras)
                if para_ratio < 0.70:
                    issues.append(f"F:Paragraphes fusionnés ({len(site_paras)}/{len(en_paras)})")
                elif para_ratio > 1.70:
                    issues.append(f"T:Long vs EN (ratio {para_ratio:.2f})")
        
        if issues:
            print(f"ch{ch_num:04d}: ⚠️ {'; '.join(issues)}")
        else:
            print(f"ch{ch_num:04d}: ✅ OK")

if __name__ == '__main__':
    main()
