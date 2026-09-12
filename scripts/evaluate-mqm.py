#!/usr/bin/env python3
"""
Evaluateur universel de qualité de traduction MQM.
Compatible romans, light novels, webnovels (EN->FR, ZH->FR, DE->FR, etc.)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Heuristiques résiduelles (sans faux amis français comme 'disciple')
RESIDUAL_ENGLISH_STRONG = re.compile(
    r"\b(had|was|were|said|asked|thought|looked|smiled|nodded|could|would|"
    r"cultivation|elder|sect|immortal|flying sword|spiritual energy|"
    r"suddenly|however|meanwhile|stared|frowned|murmured)\b",
    re.I,
)
RESIDUAL_ENGLISH_COMMON = re.compile(
    r"\b(the|this|that|these|those|and|but|with|from|into|about|after|before|"
    r"his|her|their|our|my|your|him|them|you|they|she|he|it|is|are|been|have|has)\b",
    re.I,
)

AI_ARTIFACTS = re.compile(
    r"(?:texte (?:fourni|que vous m'avez fourni) est déjà en français|"
    r"veuillez (?:me )?(?:fournir|transmettre) le texte|"
    r"il n[’']y a (?:donc )?rien à traduire|"
    r"je ne peux pas (?:traduire|effectuer)|"
    r"en tant qu['’]IA|modèle de langue|assistant IA|"
    r"voici la traduction|traduction du texte ci-dessous|"
    r"<<<\s*\d+\s*>>>|\[\[\[\s*\d+\s*\]\]\]|<chunk_\d+>|```)",
    re.I,
)


def extract_chapter_number(filename: str) -> int:
    m = re.search(r"(?:chapter|chapitre|de-|fr-|^|\b)(\d+)\b", filename, re.I)
    return int(m.group(1)) if m else 0


def load_glossary(path: Path | None) -> set[str]:
    glossary = set()
    if path and path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                glossary.add(line)
    return glossary


def strip_frontmatter(text: str) -> str:
    m = re.match(r"^\ufeff?---\s*\n.*?\n---\s*\n(.*)$", text, re.DOTALL)
    return m.group(1) if m else text


def evaluate_text_pair(
    num: int,
    fr_text: str,
    src_text: str,
    file_rel_path: str,
) -> dict:
    # Retirer le frontmatter pour n'évaluer que le corps narratif
    clean_fr = strip_frontmatter(fr_text)

    fr_paras = [p.strip() for p in re.split(r"\n\s*\n", clean_fr) if p.strip() and not p.startswith("#")]
    src_paras = [p.strip() for p in re.split(r"\n\s*\n", src_text) if p.strip() and not p.startswith("#")]

    fr_chars = len(clean_fr)
    src_chars = len(src_text)
    ratio = fr_chars / max(1, src_chars) if src_chars > 0 else 1.0

    errors = []
    penalties = 0.0

    # 1. Détection d'artefacts IA
    if AI_ARTIFACTS.search(clean_fr):
        errors.append("Accuracy/AiArtifactsOrPromptLeak")
        penalties += 15.0

    # 2. Ratio de longueur / Omissions
    if src_chars > 0:
        if ratio < 0.75:
            errors.append(f"Accuracy/SevereOmissionRatio:{ratio:.2f}")
            penalties += 25.0
        elif ratio < 0.88:
            errors.append(f"Accuracy/PossibleOmissionRatio:{ratio:.2f}")
            penalties += 8.0
        elif ratio > 1.40:
            errors.append(f"Accuracy/SevereExpansionRatio:{ratio:.2f}")
            penalties += 15.0
        elif ratio > 1.28:
            errors.append(f"Fluency/HighExpansionRatio:{ratio:.2f}")
            penalties += 5.0

    # 3. Texte source non traduit résiduel
    src_hits = 0
    for para in fr_paras:
        strong = RESIDUAL_ENGLISH_STRONG.findall(para)
        common = RESIDUAL_ENGLISH_COMMON.findall(para)
        words = para.split()
        if len(strong) >= 2 or (len(common) >= 5 and len(common) / max(1, len(words)) > 0.20):
            src_hits += 1

    if src_hits > 0:
        errors.append(f"Accuracy/UntranslatedSourceParagraphs:{src_hits}")
        penalties += min(30.0, src_hits * 10.0)

    # 4. Asymétrie de structure (seulement si le ratio de longueur est aussi suspect)
    if len(src_paras) > 0 and len(fr_paras) > 0:
        p_ratio = len(fr_paras) / len(src_paras)
        if (p_ratio < 0.50 or p_ratio > 1.80) and (ratio < 0.88 or ratio > 1.30):
            errors.append(f"Structure/ParagraphMismatch:SRC={len(src_paras)},FR={len(fr_paras)}")
            penalties += 6.0

    # 5. Typographie des dialogues
    straight_quotes = len(re.findall(r'"[^"\n]{2,200}"', clean_fr))
    french_quotes = len(re.findall(r"«[^»]{2,200}»", clean_fr))
    if straight_quotes > 20 and french_quotes == 0:
        errors.append("Fluency/EnglishStyleQuotes")
        penalties += 3.0

    # Score MQM final (0 - 100)
    score = max(0.0, min(100.0, 100.0 - penalties))

    if score >= 90.0 and not any(e.startswith("Accuracy/Severe") or e.startswith("Accuracy/Untranslated") for e in errors):
        rank = "A"
    elif score >= 75.0 and not any(e.startswith("Accuracy/Severe") for e in errors):
        rank = "B"
    else:
        rank = "C"

    return {
        "chapter": num,
        "path": file_rel_path,
        "rank": rank,
        "score": round(score, 1),
        "ratio": round(ratio, 3),
        "fr_chars": fr_chars,
        "src_chars": src_chars,
        "fr_paras": len(fr_paras),
        "src_paras": len(src_paras),
        "errors": errors,
    }


def scan_directory(source_dir: Path, target_dir: Path, glossary_path: Path | None, report_out: Path):
    glossary = load_glossary(glossary_path)

    # Indexation source (en concaténant les sous-parties du même chapitre si présentes)
    src_map: dict[int, list[Path]] = {}
    for p in source_dir.rglob("*.txt"):
        num = extract_chapter_number(p.name)
        if num > 0:
            src_map.setdefault(num, []).append(p)
    for p in source_dir.rglob("*.md"):
        num = extract_chapter_number(p.name)
        if num > 0:
            src_map.setdefault(num, []).append(p)

    # Indexation et audit cible
    results = []
    target_files = list(target_dir.rglob("*.txt")) + list(target_dir.rglob("*.md"))
    target_files.sort(key=lambda p: extract_chapter_number(p.name))

    for p in target_files:
        num = extract_chapter_number(p.name)
        if num == 0:
            continue
        fr_text = p.read_text(encoding="utf-8", errors="replace")

        # Concaténer les sous-parties sources si multiples
        src_files = src_map.get(num, [])
        src_files.sort(key=lambda x: x.name)
        src_text = ""
        for sf in src_files:
            st = sf.read_text(encoding="utf-8", errors="replace")
            src_text += ("\n\n" if src_text else "") + st

        rel_path = str(p.relative_to(target_dir))
        rec = evaluate_text_pair(num, fr_text, src_text, rel_path)
        results.append(rec)

    # Sauvegarde rapport JSON
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    # Synthèse
    total = len(results)
    rank_a = [r for r in results if r["rank"] == "A"]
    rank_b = [r for r in results if r["rank"] == "B"]
    rank_c = [r for r in results if r["rank"] == "C"]
    avg_score = sum(r["score"] for r in results) / max(1, total) if total > 0 else 0.0

    print("=" * 60)
    print(f"RAPPORT GLOBAL D'ÉVALUATION MQM ({total} chapitres)")
    print("=" * 60)
    if total > 0:
        print(f"Rang A (Excellence / Validé)  : {len(rank_a):>5} ({len(rank_a)/total*100:5.1f} %)")
        print(f"Rang B (Retouches mineures)   : {len(rank_b):>5} ({len(rank_b)/total*100:5.1f} %)")
        print(f"Rang C (Intervention Requise) : {len(rank_c):>5} ({len(rank_c)/total*100:5.1f} %)")
    print(f"Score MQM Moyen               : {avg_score:5.1f} / 100")
    print(f"Rapport détaillé sauvegardé   : {report_out}")
    print("=" * 60)

    if rank_c:
        print("\n[!] CHAPITRES RANG C (Nécessitent un sous-agent de correction) :")
        for r in rank_c[:15]:
            print(f"  - Ch. {r['chapter']:04d} [{r['score']}/100] ({r['path']}): {', '.join(r['errors'])}")
        if len(rank_c) > 15:
            print(f"  ... et {len(rank_c) - 15} autres.")


def main():
    parser = argparse.ArgumentParser(description="Audit et Scoring Qualité MQM pour traductions de romans")
    parser.add_argument("--source", type=Path, required=True, help="Dossier des textes originaux (Wuxiaworld, Raw)")
    parser.add_argument("--target", type=Path, required=True, help="Dossier des textes traduits en français")
    parser.add_argument("--glossary", type=Path, default=None, help="Fichier glossaire (termes canoniques)")
    parser.add_argument("--report", type=Path, default=Path("mqm-evaluation-report.json"), help="Fichier de sortie JSON")
    args = parser.parse_args()

    scan_directory(args.source, args.target, args.glossary, args.report)


if __name__ == "__main__":
    main()
