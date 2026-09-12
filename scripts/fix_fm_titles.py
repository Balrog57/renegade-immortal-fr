import pathlib
import re

src_dir = pathlib.Path("src/content/chapters")
files = list(src_dir.rglob("*.md"))

fixed_titles = 0
for f in files:
    txt = f.read_text(encoding="utf-8", errors="replace")
    parts = txt.split("---", 2)
    if len(parts) >= 3:
        fm = parts[1]
        body = parts[2]
        new_fm = fm
        # check title
        new_fm = re.sub(r"\bdu Secte\b", "de la Secte", new_fm)
        new_fm = re.sub(r"\bau Secte\b", "à la Secte", new_fm)
        new_fm = re.sub(r"\ble Secte\b", "la Secte", new_fm)
        new_fm = re.sub(r"\bSect\b", "Secte", new_fm)
        new_fm = re.sub(r"\bHou Fen\b", "Huo Fen", new_fm)
        new_fm = re.sub(r"\bCloud Sky\b", "Ciel Nuageux", new_fm)
        new_fm = re.sub(r"\bGrand Empyrean\b", "Grand Empyrée", new_fm)
        new_fm = re.sub(r"\bEmpyrean Exalt\b", "Exalté Empyréen", new_fm)
        if new_fm != fm:
            f.write_text(f"---{new_fm}---{body}", encoding="utf-8")
            fixed_titles += 1

print(f"Titres et métadonnées frontmatter corrigés dans {fixed_titles} fichiers.")
