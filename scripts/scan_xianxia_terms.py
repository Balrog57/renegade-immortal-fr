#!/usr/bin/env python3
"""
Scanner complet des résidus anglais bruts et anglicismes récurrents.
"""

import pathlib
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')

CHAPTERS_DIR = pathlib.Path("src/content/chapters")

TERMS = [
    r"\bCloud Sky\b",
    r"\bWar Shrine\b",
    r"\bFighting Evil\b",
    r"\bSoul Refining\b",
    r"\bCorpse Yin\b",
    r"\bPurple Cloud\b",
    r"\bPill King\b",
    r"\bSky Boundary\b",
    r"\bKilling Move\b",
    r"\bStorage Bag\b",
    r"\bBag of Holding\b",
    r"\bRestriction Flag\b",
    r"\bFlying Sword\b",
    r"\bDivine Sense\b",
    r"\bNascent Soul\b",
    r"\bCore Formation\b",
    r"\bFoundation Establishment\b",
    r"\bQi Condensation\b",
    r"\bNirvana Scryer\b",
    r"\bNirvana Cleanser\b",
    r"\bNirvana Shatterer\b",
    r"\bHeaven's Blight\b",
    r"\bAncient God\b",
    r"\bAncient Demon\b",
    r"\bAncient Monster\b",
    r"\bSea of Devils\b",
    r"\bPlanet Suzaku\b",
    r"\bPlanet Tian Yun\b",
    r"\bHou Fen\b",
    r"\bBrilliant Void\b",
    r"\bCloud Sea\b",
    r"\bInner Realm\b",
    r"\bOuter Realm\b",
    r"\bSpirit Severing\b",
    r"\bSoul Transformation\b",
    r"\bCorporeal Yang\b",
    r"\bIllusionary Yin\b",
    r"\bAscendant\b",
    r"\bGolden Exalt\b",
    r"\bEmpyrean Exalt\b",
    r"\bGrand Empyrean\b",
    r"\bHeaven Trampler\b",
    r"\bHeaven Defying Bead\b",
    r"\bBlood Ancestor\b",
    r"\bAll-Seer\b",
    r"\bDaoist Water\b",
    r"\bMaster Simo\b",
    r"\bMaster Hong Shan\b",
    r"\bOld Ghost Zhan\b",
    r"\bRed Butterfly\b",
]

hits = defaultdict(list)
files = list(CHAPTERS_DIR.rglob("*.md"))

for f in files:
    txt = f.read_text(encoding="utf-8", errors="replace")
    parts = txt.split("---", 2)
    body = parts[2] if len(parts) >= 3 else txt
    for pat in TERMS:
        matches = re.findall(pat, body, re.IGNORECASE)
        if matches:
            clean_name = pat.replace(r"\b", "")
            hits[clean_name].append((f.name, len(matches)))

print(f"=== RESULTATS DU SCAN DES TERMES ANGLAIS DANS SRC (SUR {len(files)} CHAPITRES) ===")
for term, occs in sorted(hits.items(), key=lambda x: -sum(cnt for _, cnt in x[1])):
    tot = sum(cnt for _, cnt in occs)
    print(f"{term:30s} : {tot:4d} occ dans {len(occs):3d} fichiers (ex: {occs[0][0]})")
