#!/usr/bin/env python3
"""
fix-paragraph-alignment.py — Divise les paragraphes FR fusionnés pour les aligner
avec la structure de paragraphes EN.

Lit reports/verify-all.json, identifie les chapitres avec des problèmes de
paragraph_alignment, et divise les longs paragraphes FR aux frontières de
phrases pour ramener le ratio de paragraphes >= 0.80 × le compte EN.

Usage:
  python scripts/fix-paragraph-alignment.py --dry-run
  python scripts/fix-paragraph-alignment.py
  python scripts/fix-paragraph-alignment.py --chapter 225
"""

import io
import json
import os
import re
import sys
from collections import Counter
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
VERIFY_PATH = PROJECT_ROOT / "reports" / "verify-all.json"


# ═══════════════════════════════════════════════════════════════════════════
#  LECTURE DES SOURCES
# ═══════════════════════════════════════════════════════════════════════════

def read_en_body(path: Path) -> str:
    """Lit le corps d'un chapitre EN (.txt), en ignorant les lignes d'en-tête."""
    if not path or not path.exists():
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.strip().split('\n')
    body_lines = []
    skipped = 0
    for line in lines:
        stripped = line.strip()
        if re.match(r'^Chapter\s+\d+', stripped):
            skipped += 1
            if skipped <= 2:
                continue
        body_lines.append(line)
    return '\n'.join(body_lines).strip()


def read_fr_file(path: Path) -> tuple[str, str, str]:
    """
    Lit un chapitre FR (.md).
    Retourne (contenu_complet, frontmatter, corps).
    Gère les fichiers avec BOM UTF-8 en début de fichier.
    """
    with open(path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    frontmatter = ""
    body = content
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            body = parts[2]
    return content, frontmatter.strip(), body.strip()


# ═══════════════════════════════════════════════════════════════════════════
#  EXTRACTION DE PARAGRAPHES
# ═══════════════════════════════════════════════════════════════════════════

def get_paragraphs(text: str) -> list[str]:
    """
    Extrait les paragraphes du texte (séparés par double saut de ligne).
    Ignore les titres de chapitre et les paragraphes triviaux (< 10 caractères).
    """
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    result = []
    for p in paras:
        p_stripped = p.replace('\n', ' ').strip()
        if re.match(r'^(Chapter|Chapitre)\s+\d+', p_stripped, re.IGNORECASE):
            continue
        if len(p_stripped) < 10:
            continue
        result.append(p)
    return result


def split_sentences(text: str) -> list[str]:
    """
    Découpe un texte en phrases (compatible français).
    Découpage sur .!?…» suivi d'espace + majuscule.
    """
    text = text.replace('\n', ' ')
    sentences = re.split(r'(?<=[.!?…»])\s+(?=[A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ])', text)
    return [s.strip() for s in sentences if len(s.strip().split()) >= 3]


# ═══════════════════════════════════════════════════════════════════════════
#  ALGORITHME DE SPLIT
# ═══════════════════════════════════════════════════════════════════════════

def _count_words(text: str) -> int:
    """Compte les mots dans un texte."""
    return len(text.split())


def _find_sentence_split_positions(para_text: str) -> list[int]:
    """
    Trouve les positions des frontières de phrases dans un paragraphe.
    Retourne une liste de positions d'index (fin de phrase + espace).
    Chaque position pointe juste après `. `, `! `, `? `, `» `.
    """
    positions = []
    for m in re.finditer(r'[.!?…»]\s+(?=[A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ])', para_text):
        # Position après le caractère de ponctuation + l'espace
        pos = m.end()
        positions.append(pos)
    return positions


def _split_raw_paragraph(raw_para: str, target_sub_count: int) -> list[str]:
    """
    Divise un paragraphe brut en target_sub_count sous-paragraphes
    aux frontières de phrases.

    Retourne une liste de textes de sous-paragraphes.
    Si la division est impossible, retourne [raw_para].
    """
    if target_sub_count <= 1:
        return [raw_para]

    positions = _find_sentence_split_positions(raw_para)
    if not positions:
        return [raw_para]

    total_len = len(raw_para)
    # On veut target_sub_count parties de taille à peu près égale
    target_size = total_len / target_sub_count

    # Choisir les positions de split les plus proches des tailles cibles
    chosen = []
    for i in range(1, target_sub_count):
        ideal = int(i * target_size)
        # Trouver la position de split la plus proche de `ideal`
        best_pos = None
        best_dist = float('inf')
        for pos in positions:
            if pos in chosen:
                continue
            dist = abs(pos - ideal)
            if dist < best_dist:
                best_dist = dist
                best_pos = pos

        if best_pos is not None:
            chosen.append(best_pos)

    if not chosen:
        return [raw_para]

    chosen.sort()

    # Construire les sous-paragraphes
    sub_paras = []
    start = 0
    for pos in chosen:
        sub = raw_para[start:pos].strip()
        if sub:
            sub_paras.append(sub)
        start = pos

    # Dernière partie
    last = raw_para[start:].strip()
    if last:
        sub_paras.append(last)

    # Filtrer les sous-paragraphes trop courts (< 50 caractères)
    result = []
    for sp in sub_paras:
        if len(sp) < 50 and result:
            # Fusionner avec le précédent
            result[-1] = result[-1] + ' ' + sp
        else:
            result.append(sp)

    if len(result) <= 1:
        return [raw_para]

    return result


def fix_paragraphs_in_body(fr_body: str, avg_en_sent_per_para: float,
                           needed_new_paras: int) -> tuple[str, int]:
    """
    Divise les paragraphes surdimensionnés dans le corps FR.

    Approche gloutonne itérative :
    1. À chaque itération, trouver le paragraphe avec le plus de phrases
    2. Si ce paragraphe a un ratio phrases/§ ≥ 1.5× la moyenne EN, le diviser
    3. Répéter jusqu'à atteindre la cible ou qu'il n'y ait plus de candidats

    Args:
        fr_body: Le texte du corps FR (sans frontmatter).
        avg_en_sent_per_para: Nombre moyen de phrases par paragraphe EN.
        needed_new_paras: Nombre de nouveaux paragraphes à créer.

    Returns:
        (nouveau_corps, nombre_de_paragraphes_ajoutés)
    """
    raw_blocks = fr_body.split('\n\n')
    if len(raw_blocks) <= 1:
        return fr_body, 0

    avg_sent = max(avg_en_sent_per_para, 0.5)
    # Seuil : un paragraphe FR est considéré « fusionné » s'il a au moins
    # 1.3× le nombre moyen de phrases d'un paragraphe EN (minimum 2 phrases)
    threshold = max(2.0, 1.3 * avg_sent)

    blocks = list(raw_blocks)
    splits_made = 0

    for _ in range(needed_new_paras * 2):  # sécurité anti-boucle infinie
        if splits_made >= needed_new_paras:
            break

        # Trouver le bloc avec le plus de phrases ET au-dessus du seuil
        best_idx = -1
        best_sents = 0
        for idx, block in enumerate(blocks):
            stripped = block.strip()
            if len(stripped) < 10:
                continue
            sents = len(split_sentences(stripped))
            if sents >= threshold and sents > best_sents:
                best_sents = sents
                best_idx = idx

        if best_idx < 0:
            # Si aucun bloc n'atteint le seuil, réduire progressivement
            threshold = max(1.5, threshold - 0.3)
            # Réessayer avec le seuil réduit
            for idx, block in enumerate(blocks):
                stripped = block.strip()
                if len(stripped) < 10:
                    continue
                sents = len(split_sentences(stripped))
                if sents >= threshold and sents > best_sents:
                    best_sents = sents
                    best_idx = idx

        if best_idx < 0:
            break  # plus de candidats

        block = blocks[best_idx]
        # Diviser en 2 au milieu
        sub_paras = _split_raw_paragraph(block, 2)

        if len(sub_paras) > 1:
            blocks[best_idx:best_idx + 1] = sub_paras
            splits_made += len(sub_paras) - 1
        else:
            # Forcer le split en utilisant plus de points
            sub_paras = _split_raw_paragraph(block, 3)
            if len(sub_paras) > 1:
                blocks[best_idx:best_idx + 1] = sub_paras
                splits_made += len(sub_paras) - 1
            else:
                # Vraiment impossible de diviser ce bloc — le marquer comme traité
                # en réduisant le seuil pour qu'il ne bloque pas la boucle
                threshold = best_sents + 1

    if splits_made == 0:
        return fr_body, 0

    return '\n\n'.join(blocks), splits_made


# ═══════════════════════════════════════════════════════════════════════════
#  MAPPINGS
# ═══════════════════════════════════════════════════════════════════════════

def build_maps():
    """Construit les mappings ch_num → Path pour EN et FR."""
    en_map: dict[int, Path] = {}
    for root, dirs, files in os.walk(WUXIA_DIR):
        for f in files:
            if f.endswith('.txt'):
                m = re.match(r'(\d{4})[ab]?', f)
                if m:
                    ch_num = int(m.group(1))
                    if ch_num not in en_map:
                        en_map[ch_num] = Path(root) / f

    fr_map: dict[int, Path] = {}
    for root, dirs, files in os.walk(CHAPTERS_DIR):
        for f in files:
            if f.endswith('.md'):
                m = re.match(r'(\d{4})', f)
                if m:
                    ch_num = int(m.group(1))
                    fr_map[ch_num] = Path(root) / f

    return en_map, fr_map


# ═══════════════════════════════════════════════════════════════════════════
#  FONCTION PRINCIPALE DE CORRECTION
# ═══════════════════════════════════════════════════════════════════════════

def fix_chapter(ch_num: int, en_map: dict, fr_map: dict,
                dry_run: bool = False) -> dict:
    """
    Corrige l'alignement des paragraphes pour un chapitre.

    Returns:
        dict avec les clés: fixed, new_paras, detail, ratio_before, ratio_after
    """
    en_path = en_map.get(ch_num)
    fr_path = fr_map.get(ch_num)

    result = {
        'fixed': False,
        'new_paras': 0,
        'detail': '',
        'ratio_before': 0.0,
        'ratio_after': 0.0,
        'en_paras': 0,
        'fr_paras_before': 0,
        'fr_paras_after': 0,
    }

    if not en_path or not fr_path:
        result['detail'] = "Fichier EN ou FR manquant"
        return result

    # ── Lire EN ──
    en_text = read_en_body(en_path)
    en_paras = get_paragraphs(en_text)
    if not en_paras:
        result['detail'] = "Aucun paragraphe EN"
        return result

    # ── Lire FR ──
    full_content, frontmatter, fr_body = read_fr_file(fr_path)
    fr_paras = get_paragraphs(fr_body)
    if not fr_paras:
        result['detail'] = "Aucun paragraphe FR"
        return result

    n_en = len(en_paras)
    n_fr = len(fr_paras)
    result['en_paras'] = n_en
    result['fr_paras_before'] = n_fr
    result['ratio_before'] = round(n_fr / n_en, 4) if n_en > 0 else 1.0

    # Objectif : ratio >= 0.80 (arrondi au supérieur)
    target_ratio = 0.80
    target_fr = max(n_fr, int(n_en * target_ratio + 0.999))
    if n_fr >= target_fr:
        result['detail'] = f"Déjà OK : {n_fr} FR >= {target_fr} (cible {target_ratio}×{n_en})"
        result['fr_paras_after'] = n_fr
        result['ratio_after'] = result['ratio_before']
        return result

    needed_new = target_fr - n_fr

    # ── Calculer les phrases par paragraphe EN ──
    en_total_sentences = 0
    for p in en_paras:
        en_total_sentences += len(split_sentences(p))
    avg_en_sent = en_total_sentences / n_en if n_en > 0 else 1.0

    # ── Diviser les paragraphes FR surdimensionnés ──
    new_body, splits_made = fix_paragraphs_in_body(
        fr_body, avg_en_sent, needed_new
    )

    if splits_made == 0:
        result['detail'] = (f"Division impossible : aucun point de split trouvé "
                            f"(n_en={n_en}, n_fr={n_fr}, "
                            f"avg_en_sent={avg_en_sent:.1f})")
        result['fr_paras_after'] = n_fr
        result['ratio_after'] = result['ratio_before']
        return result

    # ── Vérifier le nouveau ratio ──
    new_fr_paras = get_paragraphs(new_body)
    new_n_fr = len(new_fr_paras)
    new_ratio = round(new_n_fr / n_en, 4) if n_en > 0 else 1.0
    result['fr_paras_after'] = new_n_fr
    result['ratio_after'] = new_ratio

    if dry_run:
        result['fixed'] = True
        result['new_paras'] = splits_made
        result['detail'] = (f"[DRY RUN] Ajout de {splits_made} § "
                            f"({n_fr}→{new_n_fr}, ratio {result['ratio_before']:.3f}→{new_ratio:.3f})")
        return result

    # ── Écrire le fichier ──
    # Format: ---\n{frontmatter}\n---\n{body}\n
    # Le frontmatter original a déjÃ  le slug en dernière ligne,
    # et il est suivi de --- puis d'une ligne vide.
    new_content = f"---\n{frontmatter}\n---\n{new_body}\n"
    with open(fr_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    result['fixed'] = True
    result['new_paras'] = splits_made
    result['detail'] = (f"✓ Ajout de {splits_made} § "
                        f"({n_fr}→{new_n_fr}, ratio {result['ratio_before']:.3f}→{new_ratio:.3f})")
    return result


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Corrige l\'alignement des paragraphes FR↔EN'
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Prévisualiser les changements sans écrire')
    parser.add_argument('--chapter', type=int,
                        help='Corriger un seul chapitre (ex: 225)')
    parser.add_argument('--output', type=str,
                        default='reports/paragraph-fix-report.json',
                        help='Fichier de rapport JSON')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Afficher tous les détails')
    args = parser.parse_args()

    print("=" * 70)
    print("  fix-paragraph-alignment.py — Alignement des paragraphes FR↔EN")
    print("=" * 70)
    if args.dry_run:
        print("  MODE: --dry-run (aucune modification écrite)")
    print()

    # ── Charger les données verify ──
    print("Chargement des données verify-all.json...")
    with open(VERIFY_PATH, 'r', encoding='utf-8') as f:
        verify_data = json.load(f)

    pa_chapters = []
    for c in verify_data['chapters']:
        for issue in c.get('issues', []):
            if issue.get('type') == 'paragraph_alignment':
                pa_chapters.append(c)
                break

    print(f"  → {len(pa_chapters)} chapitres avec paragraph_alignment")
    print()

    # ── Filtrer si --chapter ──
    if args.chapter:
        pa_chapters = [c for c in pa_chapters if c['chapter'] == args.chapter]
        if not pa_chapters:
            print(f"Chapitre {args.chapter} introuvable dans la liste paragraph_alignment")
            return

    # ── Construire les mappings ──
    print("Construction des mappings EN/FR...")
    en_map, fr_map = build_maps()
    print(f"  → {len(en_map)} chapitres EN, {len(fr_map)} chapitres FR")
    print()

    # ── Traiter les chapitres (du pire au meilleur ratio) ──
    pa_chapters.sort(key=lambda c: c['para_count_ratio'])

    results = []
    fixed_count = 0
    total_new_paras = 0
    failed_count = 0

    for c in pa_chapters:
        ch_num = c['chapter']
        tome = c['tome']
        ratio_before = c['para_count_ratio']

        result = fix_chapter(ch_num, en_map, fr_map, dry_run=args.dry_run)

        if result['fixed']:
            fixed_count += 1
            total_new_paras += result['new_paras']
            status = "✓"
        else:
            failed_count += 1
            status = "✗"

        if args.verbose or not result['fixed']:
            print(f"  {status} ch{ch_num:<5} T{tome:<2}  "
                  f"ratio={ratio_before:.3f}→{result['ratio_after']:.3f}  "
                  f"{result['detail']}")

        results.append({
            'chapter': ch_num,
            'tome': tome,
            'en_title': c.get('en_title', ''),
            'fr_title': c.get('fr_title', ''),
            'ratio_before': ratio_before,
            'ratio_after': result['ratio_after'],
            'en_paras': result['en_paras'],
            'fr_paras_before': result['fr_paras_before'],
            'fr_paras_after': result['fr_paras_after'],
            'fixed': result['fixed'],
            'new_paras': result['new_paras'],
            'detail': result['detail'],
        })

    # ── Résumé ──
    print()
    print("─" * 70)
    print("  RÉSUMÉ")
    print("─" * 70)
    print(f"  Chapitres traités   : {len(pa_chapters)}")
    print(f"  Corrigés            : {fixed_count}")
    print(f"  Non corrigés        : {failed_count}")
    print(f"  Nouveaux paragraphes: {total_new_paras}")
    print()

    # Par tome
    tome_stats = Counter()
    tome_fixed = Counter()
    for r in results:
        t = r['tome']
        tome_stats[t] += 1
        if r['fixed']:
            tome_fixed[t] += 1

    if tome_stats:
        print(f"  {'Tome':<6} {'Total':<7} {'Corrigés':<10} {'Nouveaux §':<12}")
        print(f"  {'─'*6} {'─'*7} {'─'*10} {'─'*12}")
        for t in sorted(tome_stats):
            count = tome_stats[t]
            fixed = tome_fixed[t]
            new_paras = sum(r['new_paras'] for r in results if r['tome'] == t)
            print(f"  {t:<6} {count:<7} {fixed:<10} {new_paras:<12}")

    print()

    # ── Sauvegarder le rapport ──
    report = {
        'script': 'fix-paragraph-alignment.py',
        'dry_run': args.dry_run,
        'total_with_issues': len(pa_chapters),
        'total_fixed': fixed_count,
        'total_failed': failed_count,
        'total_new_paragraphs': total_new_paras,
        'results': results,
    }

    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Rapport sauvegardé : {output_path}")

    if args.dry_run:
        print()
        print("⚠ Mode dry-run : aucun fichier modifié.")
        print("  Pour appliquer les changements, relancez sans --dry-run.")


if __name__ == '__main__':
    main()
