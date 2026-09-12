#!/usr/bin/env python3
"""
Audit approfondi de la fidélité de traduction et détection des scories anglaises
sur les 2 088 chapitres de src/content/chapters/.
"""

import pathlib
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')

CHAPTERS_DIR = pathlib.Path("src/content/chapters")

# Liste de termes anglais fréquents qui auraient dû être traduits
ANGLICISMS = [
    (r"\bCloud Sky Sect\b", "Secte Ciel Nuageux"),
    (r"\bcloud sky sect\b", "secte Ciel Nuageux"),
    (r"\bHou Fen\b", "Huo Fen"),
    (r"\bWar Shrine\b", "Sanctuaire de Guerre"),
    (r"\bFighting Evil Sect\b", "Secte Dou Xie"),
    (r"\bSoul Refining Sect\b", "Secte du Raffinement de l'Âme"),
    (r"\bCorpse Yin Sect\b", "Secte Yin des Cadavres"),
    (r"\bPurple Cloud Sect\b", "Secte du Nuage Pourpre"),
    (r"\bFour Sect Alliance\b", "Alliance des Quatre Sectes"),
    (r"\bPill King Sect\b", "Secte du Roi de la Pilule"),
    (r"\bSky Boundary Sect\b", "Secte Tian Dao"),
    (r"\bHeng Yue Sect\b", "Secte Heng Yue"),
    (r"\bRed Butterfly\b", "Hongdie (Papillon Rouge)"),
    (r"\bFlying Sword\b", "Épée Volante"),
    (r"\bflying sword\b", "épée volante"),
    (r"\bflying swords\b", "épées volantes"),
    (r"\bSpiritual Energy\b", "Énergie Spirituelle"),
    (r"\bspiritual energy\b", "énergie spirituelle"),
    (r"\bDivine Sense\b", "Sens Divin"),
    (r"\bdivine sense\b", "sens divin"),
    (r"\bNascent Soul\b", "Âme Naissante"),
    (r"\bnascent soul\b", "âme naissante"),
    (r"\bCore Formation\b", "Formation du Noyau"),
    (r"\bcore formation\b", "formation du noyau"),
    (r"\bFoundation Establishment\b", "Établissement des Fondations"),
    (r"\bfoundation establishment\b", "établissement des fondations"),
    (r"\bQi Condensation\b", "Condensation du Qi"),
    (r"\bqi condensation\b", "condensation du qi"),
    (r"\bSoul Transformation\b", "Transformation de l'Âme"),
    (r"\bsoul transformation\b", "transformation de l'âme"),
    (r"\bSpirit Severing\b", "Séparation Spirituelle"),
    (r"\bspirit severing\b", "séparation spirituelle"),
    (r"\bHeaven Defying Bead\b", "Perle Défiant les Cieux"),
    (r"\bheaven defying bead\b", "perle défiant les cieux"),
    (r"\bRestriction Flag\b", "Bannière de Restrictions"),
    (r"\brestriction flag\b", "bannière de restrictions"),
    (r"\bBag of Holding\b", "Sac de Rangement"),
    (r"\bbag of holding\b", "sac de rangement"),
    (r"\bStorage Bag\b", "Sac de Rangement"),
    (r"\bstorage bag\b", "sac de rangement"),
    (r"\bKilling Move\b", "Technique Mortelle"),
    (r"\bkilling move\b", "technique mortelle"),
    (r"\bOrigin Energy\b", "Énergie Originelle"),
    (r"\borigin energy\b", "énergie originelle"),
    (r"\bJoss Flame\b", "Flamme Joss"),
    (r"\bjoss flame\b", "flamme joss"),
    (r"\bNirvana Scryer\b", "Scruteur du Nirvana"),
    (r"\bnirvana scryer\b", "scruteur du nirvana"),
    (r"\bNirvana Cleanser\b", "Purificateur du Nirvana"),
    (r"\bnirvana cleanser\b", "purificateur du nirvana"),
    (r"\bNirvana Shatterer\b", "Briseur du Nirvana"),
    (r"\bnirvana shatterer\b", "briseur du nirvana"),
    (r"\bHeaven's Blight\b", "Fléau Céleste"),
    (r"\bheaven's blight\b", "fléau céleste"),
    (r"\bAncient God\b", "Dieu Antique"),
    (r"\bancient god\b", "dieu antique"),
    (r"\bAncient Demon\b", "Démon Antique"),
    (r"\bancient demon\b", "démon antique"),
    (r"\bAncient Monster\b", "Monstre Antique"),
    (r"\bancient monster\b", "monstre antique"),
    (r"\bSea of Devils\b", "Mer des Démons"),
    (r"\bsea of devils\b", "mer des démons"),
    (r"\bPlanet Suzaku\b", "Planète Suzaku"),
    (r"\bplanet Suzaku\b", "planète Suzaku"),
    (r"\bPlanet Tian Yun\b", "Planète Tian Yun"),
    (r"\bplanet Tian Yun\b", "planète Tian Yun"),
    (r"\bCloud Sea\b", "Mer de Nuages"),
    (r"\bcloud sea\b", "mer de nuages"),
    (r"\bAllheaven\b", "Tout-Céleste (Allheaven)"),
    (r"\bBrilliant Void\b", "Vide Brillant"),
    (r"\bInner Realm\b", "Royaume Intérieur"),
    (r"\binner realm\b", "royaume intérieur"),
    (r"\bOuter Realm\b", "Royaume Extérieur"),
    (r"\bouter realm\b", "royaume extérieur"),
]

hits = defaultdict(list)
files = list(CHAPTERS_DIR.rglob("*.md"))
print(f"Audit de {len(files)} fichiers markdown...")

for f in files:
    txt = f.read_text(encoding="utf-8", errors="replace")
    # check body only (after frontmatter)
    parts = txt.split("---", 2)
    body = parts[2] if len(parts) >= 3 else txt
    for pat, rep in ANGLICISMS:
        matches = re.findall(pat, body)
        if matches:
            hits[rep].append((f.name, len(matches)))

print(f"\n=== TERMES ANGLAIS DÉTECTÉS DANS LE CORPUS FR ===")
for rep, occurrences in sorted(hits.items(), key=lambda x: -sum(cnt for _, cnt in x[1])):
    total_count = sum(cnt for _, cnt in occurrences)
    files_count = len(occurrences)
    print(f"  - '{rep}' : {total_count} occurrences dans {files_count} chapitres (ex: {occurrences[0][0]})")
