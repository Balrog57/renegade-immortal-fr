#!/usr/bin/env python3
"""
Extracteur et aligneur des chapitres chinois depuis C:\\Users\\Marc\\Downloads\\renegade
Extrait le texte brut chinois des 11 EPUBs et 2 PDFs.
"""

import fitz
import json
import os
import pathlib
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8')

DOWNLOADS_DIR = pathlib.Path(r"C:\Users\Marc\Downloads\renegade")
OUT_DIR = pathlib.Path("raw_chinese")
OUT_DIR.mkdir(exist_ok=True)

chinese_chapters = {}  # int -> {"title": str, "text": str, "source": str}

# 1. Extraction des EPUBs
print("--- Extraction des EPUBs ---")
epub_files = sorted(DOWNLOADS_DIR.glob("*.epub"))
for ep in epub_files:
    z = zipfile.ZipFile(ep)
    for name in z.namelist():
        if name.endswith((".html", ".xhtml", ".htm")):
            content = z.read(name).decode("utf-8", errors="ignore")
            # match 第X章 title
            m = re.search(r"第\s*(\d+)\s*章\s*([^<\n\r]+)", content)
            if m:
                c_num = int(m.group(1))
                c_title = m.group(2).strip()
                # Clean html tags from content
                text = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL)
                text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
                text = re.sub(r"<[^>]+>", "\n", text)
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                # remove chapter header line if first
                body_lines = []
                for line in lines:
                    if re.match(r"^第\s*\d+\s*章", line):
                        continue
                    if line in ("目录", "bookcover"):
                        continue
                    body_lines.append(line)
                clean_body = "\n\n".join(body_lines)
                if len(clean_body) > 200:
                    chinese_chapters[c_num] = {
                        "title": c_title,
                        "text": clean_body,
                        "source": f"{ep.name}:{name}",
                    }

print(f"Total chapitres extraits des EPUBs: {len(chinese_chapters)}")

# Sauvegarde d'un index
with open("raw_chinese_index.json", "w", encoding="utf-8") as f:
    summary = {k: {"title": v["title"], "length": len(v["text"]), "source": v["source"]} for k, v in sorted(chinese_chapters.items())}
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"Index sauvegardé dans raw_chinese_index.json (couverture : chapitres {min(chinese_chapters.keys())} à {max(chinese_chapters.keys())})")
