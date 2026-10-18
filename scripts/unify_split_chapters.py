#!/usr/bin/env python3
"""
Script pour consolider et fusionner les 60 chapitres divisés en (上) et (下).
Supprime également les reliquats obsolètes (0902_下, 1019_, 1269_combiné).
Résultat attendu : EXACTEMENT 2088 fichiers chinois pour 2088 chapitres traduits (stricte bijection 1:1).
"""

import collections
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
ZH_DIRS = [
    REPO_ROOT / "tmp" / "zh_extract" / "chapters",
    pathlib.Path(r"C:\Users\Marc\Downloads\renegade\chapitres_zh"),
]


def clean_obsolete_files():
    print("[1] Suppression des fichiers obsolètes et orphelins...")
    for d in ZH_DIRS:
        if not d.exists():
            continue
        obsoletes = [
            "0902_了却因果（下）.txt",
            "1019_.txt",
            "1269_、第1270章 没有了家.txt",
        ]
        for name in obsoletes:
            f = d / name
            if f.exists():
                f.unlink()
                print(f"    [-] Supprimé dans {d.name} : {name}")


def merge_split_chapters():
    print("\n[2] Fusion des chapitres scindés (上 / 下)...")
    for d in ZH_DIRS:
        if not d.exists():
            continue
        print(f"  -> Traitement du dossier : {d}")

        # Indexer par numéro de chapitre
        by_num = collections.defaultdict(list)
        for f in d.glob("*.txt"):
            m = re.match(r"^(\d{1,4})", f.name)
            if m:
                by_num[int(m.group(1))].append(f)

        merged_count = 0
        for num, files in sorted(by_num.items()):
            if len(files) <= 1:
                continue

            # Trouver le fichier (上) et (下)
            f_up = None
            f_down = None
            for f in files:
                if "（上）" in f.name or "(上)" in f.name:
                    f_up = f
                elif "（下）" in f.name or "(下)" in f.name:
                    f_down = f

            if f_up and f_down and len(files) == 2:
                # Extraire le titre de base
                base_title = re.sub(r"^[0-9]+_", "", f_up.stem)
                base_title = re.sub(r"[（\(][上下][）\)]", "", base_title).strip()

                t_up = f_up.read_text(encoding="utf-8").strip()
                t_down = f_down.read_text(encoding="utf-8").strip()

                lines_up = [l for l in t_up.splitlines() if l.strip()]
                if lines_up and re.match(r"^第?\s*\d+.*章?", lines_up[0]):
                    lines_up = lines_up[1:]

                lines_down = [l for l in t_down.splitlines() if l.strip()]
                if lines_down and re.match(r"^第?\s*\d+.*章?", lines_down[0]):
                    lines_down = lines_down[1:]

                unified_content = f"第{num}章 {base_title}\n\n" + "\n\n".join(lines_up) + "\n\n" + "\n\n".join(lines_down)

                new_fname = f"{num:04d}_{base_title}.txt"
                new_file = d / new_fname
                new_file.write_text(unified_content.strip() + "\n", encoding="utf-8")

                f_up.unlink()
                f_down.unlink()
                merged_count += 1
            else:
                print(f"    [!] Multiples non standard pour {num}: {[f.name for f in files]}")

        print(f"    [+] {merged_count} paires (上/下) fusionnées en chapitres uniques complets.")


def audit_final():
    print("\n[3] Vérification finale de bijection 1:1...")
    for d in ZH_DIRS:
        if not d.exists():
            continue
        files = list(d.glob("*.txt"))
        nums = {int(m.group(1)) for f in files if (m := re.match(r"^(\d{1,4})", f.name))}
        missing = sorted(set(range(1, 2089)) - nums)

        print(f"  Dossier : {d}")
        print(f"    Nombre exact de fichiers .txt : {len(files)}")
        print(f"    Numéros uniques de 1 à 2088   : {len(nums)} / 2088")
        print(f"    Chapitres manquants           : {len(missing)}")
        if len(files) == 2088 and len(nums) == 2088:
            print("    [V] SUCCÈS : Exactement 2088 fichiers pour 2088 chapitres (BIJECTION 1:1 PARFAITE) !")
        else:
            print(f"    [!] Anomalie : écart de {len(files) - 2088} fichiers.")


def update_alignment_index():
    print("\n[4] Mise à jour de l'index d'alignement tmp/alignment_zh_en_fr.json...")
    repo_zh = REPO_ROOT / "tmp" / "zh_extract" / "chapters"
    repo_en = REPO_ROOT / "tmp" / "en"
    repo_fr = REPO_ROOT / "src" / "content" / "chapters"

    zh_map = {}
    for f in repo_zh.glob("*.txt"):
        m = re.match(r"^(\d{1,4})", f.name)
        if m:
            zh_map[int(m.group(1))] = f

    en_map = {}
    for f in repo_en.rglob("*.txt"):
        m = re.match(r"^(\d{1,4})", f.name)
        if m:
            en_map.setdefault(int(m.group(1)), []).append(f)

    fr_map = {}
    for f in repo_fr.rglob("*.md"):
        m = re.match(r"^(\d{1,4})", f.name)
        if m:
            fr_map[int(m.group(1))] = f

    records = []
    for num in range(1, 2089):
        zf = zh_map.get(num)
        efs = en_map.get(num, [])
        ff = fr_map.get(num)

        z_text = zf.read_text(encoding="utf-8") if zf else ""
        z_title = z_text.splitlines()[0] if z_text else ""

        e_texts = [ef.read_text(encoding="utf-8", errors="ignore") for ef in efs]
        e_titles = [et.splitlines()[0] for et in e_texts if et]

        f_text = ff.read_text(encoding="utf-8") if ff else ""
        f_title_match = re.search(r"^title:\s*[\"']?(.*?)[\"']?$", f_text, re.MULTILINE)
        f_title = f_title_match.group(1) if f_title_match else ""

        records.append({
            "chapter": num,
            "zh": {
                "file": zf.name if zf else None,
                "title": z_title,
                "chars": len(z_text),
            },
            "en": {
                "files": [ef.name for ef in efs],
                "titles": e_titles,
                "words": sum(len(et.split()) for et in e_texts),
            },
            "fr": {
                "file": ff.name if ff else None,
                "title": f_title,
                "words": len(f_text.split()),
            },
        })

    out_file = REPO_ROOT / "tmp" / "alignment_zh_en_fr.json"
    out_file.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    Index sauvegardé : {out_file} (2088 entrées)")


if __name__ == "__main__":
    clean_obsolete_files()
    merge_split_chapters()
    audit_final()
    update_alignment_index()
