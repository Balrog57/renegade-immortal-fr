#!/usr/bin/env python3
"""
Comparaison MQM bilingue Chinois -> Français sur les chapitres disponibles.
Vérifie les ratios de longueur, les titres et la complétude.
"""

import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

CHAPTERS_DIR = pathlib.Path("src/content/chapters")

# Charger les chapitres chinois indexés
if not pathlib.Path("raw_chinese_index.json").exists():
    print("Erreur: raw_chinese_index.json introuvable.")
    sys.exit(1)

with open("raw_chinese_index.json", "r", encoding="utf-8") as f:
    zh_index = json.load(f)

# Indexer les chapitres français
fr_by_num = {}
for f in CHAPTERS_DIR.rglob("*.md"):
    m = re.match(r"^(\d+)", f.name)
    if m:
        num = int(m.group(1))
        txt = f.read_text(encoding="utf-8", errors="replace")
        parts = txt.split("---", 2)
        body = parts[2].strip() if len(parts) >= 3 else txt
        # get title from frontmatter
        title_m = re.search(r"^title:\s*(.+)$", parts[1], re.M) if len(parts) >= 3 else None
        title = title_m.group(1).strip().strip('"').strip("'") if title_m else ""
        fr_by_num[num] = {"path": f, "title": title, "body": body, "chars": len(body)}

print(f"Chapitres disponibles : {len(zh_index)} en chinois, {len(fr_by_num)} en français.")

results = []
omissions = []
expansions = []
ratios = []

for num_str, zh_info in sorted(zh_index.items(), key=lambda x: int(x[0])):
    num = int(num_str)
    if num not in fr_by_num:
        continue
    fr_info = fr_by_num[num]
    zh_len = zh_info["length"]
    fr_len = fr_info["chars"]
    ratio = fr_len / max(1, zh_len)
    ratios.append(ratio)

    entry = {
        "chapter": num,
        "zh_title": zh_info["title"],
        "fr_title": fr_info["title"],
        "zh_chars": zh_len,
        "fr_chars": fr_len,
        "ratio": round(ratio, 2),
        "source": zh_info["source"],
    }
    results.append(entry)

    if ratio < 1.70:
        omissions.append(entry)
    elif ratio > 4.20:
        expansions.append(entry)

avg_ratio = sum(ratios) / len(ratios) if ratios else 0
print(f"\n=== SYNTHÈSE MQM BILINGUE ZH -> FR ({len(results)} chapitres comparés) ===")
print(f"Ratio moyen (caractères FR / caractères ZH) : {avg_ratio:.2f}")
print(f"Plage nominale : 1.80 à 3.80")
print(f"Omissions suspectes (ratio < 1.70) : {len(omissions)}")
print(f"Sur-expansions suspectes (ratio > 4.20) : {len(expansions)}")

if omissions:
    print("\n[!] Chapitres avec ratio bas :")
    for o in omissions[:10]:
        print(f"  Ch. {o['chapter']} (Ratio {o['ratio']}) : ZH={o['zh_chars']} chars vs FR={o['fr_chars']} chars | {o['zh_title']} -> {o['fr_title']}")

if expansions:
    print("\n[!] Chapitres avec ratio élevé :")
    for e in expansions[:10]:
        print(f"  Ch. {e['chapter']} (Ratio {e['ratio']}) : ZH={e['zh_chars']} chars vs FR={e['fr_chars']} chars | {e['zh_title']} -> {e['fr_title']}")

# Sauvegarde du rapport
with open("mqm_bilingual_zh_fr_report.json", "w", encoding="utf-8") as f:
    json.dump({"summary": {"total": len(results), "avg_ratio": round(avg_ratio, 2), "omissions_count": len(omissions)}, "chapters": results}, f, ensure_ascii=False, indent=2)

print("\nRapport bilingue sauvegardé dans mqm_bilingual_zh_fr_report.json")
