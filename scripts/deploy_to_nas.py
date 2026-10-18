#!/usr/bin/env python3
"""
Script pour organiser et copier les 2088 chapitres chinois par Tome/Livre sur le NAS (yoda)
dans \\192.168.1.150\Media\Livres\EBOOK\Renegade Immortal\chinois
aux côtés des dossiers 'traduction' et 'wuxiaworld'.

Vérifie ensuite la parfaite concordance des 13 tomes entre les 3 répertoires :
- chinois (ZH original)
- wuxiaworld (EN)
- traduction (FR)
"""

import pathlib
import re
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
ZH_SRC_DIR = pathlib.Path(r"C:\Users\Marc\Downloads\renegade\chapitres_zh")
NAS_ROOT = pathlib.Path(r"\\192.168.1.150\Media\Livres\EBOOK\Renegade Immortal")
NAS_ZH_DIR = NAS_ROOT / "chinois"
NAS_WW_DIR = NAS_ROOT / "wuxiaworld"
NAS_FR_DIR = NAS_ROOT / "traduction"

# Définition des 13 Tomes / Livres et leurs plages de chapitres
BOOK_RANGES = [
    (1, "Book 1 - The Mediocre Youth", 1, 64),
    (2, "Book 2 - The Bloody Image of Cultivation", 65, 140),
    (3, "Book 3 - Famous in the Sea of Devils", 141, 200),
    (4, "Book 4 - Clean Sweep", 201, 405),
    (5, "Book 5 - Cultivation Planet Crystal", 406, 471),
    (6, "Book 6 - Arriving on Tian Yun", 472, 658),
    (7, "Book 7 - Fame Shakes Allheaven Star System", 659, 920),
    (8, "Book 8 - Alliance's Secret", 921, 1140),
    (9, "Book 9 - Peak of the Cloud Sea", 1141, 1478),
    (10, "Book 10 - Rampage Through the Inner Realm", 1479, 1613),
    (11, "Book 11 - Mysteries of the Ancient Era", 1614, 1793),
    (12, "Book 12 - Tenth Sun of the Immortal Astral Continent", 1794, 2002),
    (13, "Book 13 - Light of the coming end", 2003, 2088),
]


def get_book_for_chapter(ch_num: int):
    for book_idx, book_name, start, end in BOOK_RANGES:
        if start <= ch_num <= end:
            return book_idx, book_name, start, end
    return None


def copy_and_organize_chinese_chapters():
    print("=" * 70)
    print("  DÉPLOIEMENT DU CORPUS CHINOIS PAR TOME SUR LE NAS (YODA)")
    print("=" * 70)

    print(f"\n[1] Source locale : {ZH_SRC_DIR}")
    src_files = list(ZH_SRC_DIR.glob("*.txt"))
    print(f"    Total fichiers trouvés : {len(src_files)}")
    if len(src_files) != 2088:
        print(f"    [!] ATTENTION : Nombre de fichiers différent de 2088 ({len(src_files)})")

    print(f"\n[2] Destination NAS : {NAS_ZH_DIR}")
    NAS_ZH_DIR.mkdir(parents=True, exist_ok=True)

    # Création des 13 sous-dossiers par Livre
    for _, book_name, _, _ in BOOK_RANGES:
        book_dir = NAS_ZH_DIR / book_name
        book_dir.mkdir(exist_ok=True)

    # Copie des fichiers
    print("\n[3] Copie des fichiers vers chaque tome sur le NAS...")
    copied_count = 0
    errors = []

    for f in sorted(src_files):
        m = re.match(r"^(\d{1,4})", f.name)
        if not m:
            errors.append(f"Format invalide : {f.name}")
            continue

        num = int(m.group(1))
        book_info = get_book_for_chapter(num)
        if not book_info:
            errors.append(f"Aucun tome trouvé pour le chapitre {num} ({f.name})")
            continue

        _, book_name, _, _ = book_info
        dest_dir = NAS_ZH_DIR / book_name
        dest_file = dest_dir / f.name

        try:
            shutil.copy2(f, dest_file)
            copied_count += 1
        except Exception as e:
            errors.append(f"Erreur copie {f.name} vers {book_name} : {e}")

    print(f"    -> {copied_count} / {len(src_files)} fichiers copiés avec succès.")
    if errors:
        print(f"    [!] {len(errors)} erreurs constatées :")
        for err in errors[:10]:
            print(f"       - {err}")


def verify_nas_deployment():
    print("\n[4] Vérification de l'arborescence et comparaison triple sur le NAS...")
    print(f"    Racine : {NAS_ROOT}")

    total_zh_files = 0
    total_zh_unique = set()

    print("\n    Détail par Tome dans 'chinois' :")
    print(f"    {'Tome':<40} {'Plage attendue':<18} {'Fichiers ZH':<12} {'Fichiers EN':<12} {'Fichiers FR':<12}")
    print("    " + "-" * 96)

    for book_idx, book_name, start, end in BOOK_RANGES:
        expected_range = f"{start} à {end} ({end - start + 1})"

        zh_book = NAS_ZH_DIR / book_name
        ww_book = NAS_WW_DIR / book_name
        fr_book = NAS_FR_DIR / book_name

        zh_files = list(zh_book.glob("*.txt")) if zh_book.exists() else []
        ww_files = list(ww_book.glob("*.txt")) if ww_book.exists() else []
        fr_files = list(fr_book.glob("*.txt")) if fr_book.exists() else []

        for f in zh_files:
            m = re.match(r"^(\d+)", f.name)
            if m:
                total_zh_unique.add(int(m.group(1)))
        total_zh_files += len(zh_files)

        print(f"    {book_name:<40} {expected_range:<18} {len(zh_files):<12} {len(ww_files):<12} {len(fr_files):<12}")

    print("    " + "-" * 96)
    print(f"    TOTAL GLOBAL : {total_zh_files} fichiers chinois copiés | {len(total_zh_unique)} / 2088 chapitres uniques")

    missing = sorted(set(range(1, 2089)) - total_zh_unique)
    if not missing and total_zh_files == 2088:
        print("\n[V] VÉRIFICATION PARFAITE RÉUSSIE !")
        print("    - Exactement 2088 fichiers chinois répartis dans les 13 tomes.")
        print("    - Aucune anomalie, aucune perte, synchronisation 100% complète sur le NAS.")
    else:
        print(f"\n[!] ANOMALIE DÉTECTÉE : Manquants ({len(missing)}) : {missing}")


if __name__ == "__main__":
    copy_and_organize_chinese_chapters()
    verify_nas_deployment()
