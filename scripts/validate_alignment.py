import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")

data = json.loads(pathlib.Path("tmp/alignment_zh_en_fr.json").read_text(encoding="utf-8"))
by_num = {d["chapter"]: d for d in data}
sample_nums = [1, 52, 53, 70, 574, 575, 707, 708, 901, 902, 903, 1018, 1019, 1632, 2088]

print(f"Total entrées dans l'alignement : {len(data)}")
all_aligned = all(d["zh"]["file"] and d["en"]["files"] and d["fr"]["file"] for d in data)
print(f"Tous les 2088 chapitres ont un fichier ZH, EN et FR : {all_aligned}")
print("\nÉchantillons représentatifs :")
for n in sample_nums:
    d = by_num[n]
    print(f"\n--- Chapitre {n} ---")
    print(f"  ZH: {d['zh']['file']} | {d['zh']['title']} ({d['zh']['chars']} car.)")
    print(f"  EN: {d['en']['files']} | {d['en']['titles'][:1]} ({d['en']['words']} mots)")
    print(f"  FR: {d['fr']['file']} | {d['fr']['title']} ({d['fr']['words']} mots)")
