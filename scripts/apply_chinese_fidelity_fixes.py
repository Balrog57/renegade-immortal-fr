#!/usr/bin/env python3
"""
Application des corrections de fidélité par rapport aux originaux chinois :
- Correction des noms propres et sectes restés en anglais
- Harmonisation avec les sinogrammes canoniques (Huo Fen, Ciel Nuageux, Grand Empyrée, etc.)
"""

import pathlib
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

CHAPTERS_DIR = pathlib.Path("src/content/chapters")

# Remplacements ciblés avec préservation du sens et de la grammaire française
CORRECTIONS = [
    # Pays de Huo Fen (火焚国 - Huǒ Fén Guó)
    (r"\bdu pays de Hou Fen\b", "du pays de Huo Fen"),
    (r"\bLe pays de Hou Fen\b", "Le pays de Huo Fen"),
    (r"\ble pays de Hou Fen\b", "le pays de Huo Fen"),
    (r"\bAu pays de Hou Fen\b", "Au pays de Huo Fen"),
    (r"\bau pays de Hou Fen\b", "au pays de Huo Fen"),
    (r"\bce pays de Hou Fen\b", "ce pays de Huo Fen"),
    (r"\bde Hou Fen\b", "de Huo Fen"),
    (r"\bHou Fen\b", "Huo Fen"),

    # Secte Ciel Nuageux (云天宗 - Yún Tiān Zōng)
    (r"\bSecte Cloud Sky\b", "Secte Ciel Nuageux"),
    (r"\bsecte Cloud Sky\b", "secte Ciel Nuageux"),
    (r"\bCloud Sky Sect\b", "Secte Ciel Nuageux"),
    (r"\bcloud sky sect\b", "secte Ciel Nuageux"),
    (r"\bde Cloud Sky\b", "de la Secte Ciel Nuageux"),
    (r"\bCloud Sky\b", "Ciel Nuageux"),

    # Grands Empyrées (大天尊 - Dà Tiān Zūn)
    (r"\bCinq Grands Empyreans\b", "Cinq Grands Empyrées"),
    (r"\bcinq Grands Empyreans\b", "cinq Grands Empyrées"),
    (r"\bcinq grands Empyreans\b", "cinq grands Empyrées"),
    (r"\bGrands Empyreans\b", "Grands Empyrées"),
    (r"\bgrands Empyreans\b", "grands Empyrées"),
    (r"\bGrand Empyrean\b", "Grand Empyrée"),
    (r"\bgrand Empyrean\b", "grand Empyrée"),

    # Exaltés Empyréens / Célestes (天尊 - Tiān Zūn)
    (r"\bEmpyrean Exalts\b", "Exaltés Empyréens"),
    (r"\bempyrean exalts\b", "exaltés empyréens"),
    (r"\bEmpyrean Exalt\b", "Exalté Empyréen"),
    (r"\bempyrean exalt\b", "exalté empyréen"),

    # Taoïste de l'Eau / Shui Daozi (水道子 - Shuǐ Dào Zǐ)
    (r"\bDaoist Water\b", "Shui Daozi"),

    # Vieux Fantôme Zhan (战老鬼 / 詹老鬼)
    (r"\bOld Ghost Zhan\b", "Vieux Fantôme Zhan"),
    (r"\bold ghost Zhan\b", "vieux fantôme Zhan"),

    # Mer de Nuages (云海 - Yún Hǎi)
    (r"\bCloud Sea\b", "Mer de Nuages"),
    (r"\bcloud sea\b", "mer de nuages"),

    # Vide Brillant (昭河 / 召河)
    (r"\bBrilliant Void\b", "Vide Brillant"),
    (r"\bbrilliant void\b", "vide brillant"),

    # Secte Dou Xie / Fighting Evil (斗邪派)
    (r"\bFighting Evil Sect\b", "Secte Dou Xie"),
    (r"\bFighting Evil\b", "Dou Xie"),

    # Royaume Extérieur (界外 - Jiè Wài)
    (r"\bOuter Realm\b", "Royaume Extérieur"),
    (r"\bouter realm\b", "royaume extérieur"),

    # Nettoyage de résidus de ponctuation / espaces
    (r"[ \t]+", " "),
]

files = list(CHAPTERS_DIR.rglob("*.md"))
print(f"Application des corrections de fidélité sur {len(files)} chapitres...")

modified_files = 0
total_replacements = 0

for f in files:
    raw = f.read_text(encoding="utf-8", errors="replace")
    parts = raw.split("---", 2)
    if len(parts) >= 3:
        fm = f"---{parts[1]}---"
        body = parts[2]
    else:
        fm = ""
        body = raw

    new_body = body
    file_changes = 0
    for pat, rep in CORRECTIONS:
        new_body, count = re.subn(pat, rep, new_body)
        file_changes += count

    if file_changes > 0:
        new_content = (fm + new_body) if fm else new_body
        f.write_text(new_content, encoding="utf-8")
        modified_files += 1
        total_replacements += file_changes

print(f"Terminé : {modified_files} fichiers modifiés avec {total_replacements} corrections appliquées.")
