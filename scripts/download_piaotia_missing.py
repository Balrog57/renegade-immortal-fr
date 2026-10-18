#!/usr/bin/env python3
"""
Téléchargeur et aligneur des chapitres chinois manquants depuis le miroir web Piaotia.
Récupère les 38 chapitres identifiés (paires de chapitres fusionnés et chapitres isolés).
"""

from __future__ import annotations

import html
import json
import pathlib
import re
import sys
import time
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
ZH_DIRS = [
    REPO_ROOT / "tmp" / "zh_extract" / "chapters",
    pathlib.Path(r"C:\Users\Marc\Downloads\renegade\chapitres_zh"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Mapping des URLs directes sur Piaotia
PIAOTIA_SOURCES = [
    # (ch_nums, title, url)
    ([574, 575], "帝剑的委屈", "https://www.piaotia.com/html/0/54/188266.html"),
    ([707, 708], "本尊、拓森、周茹", "https://www.piaotia.com/html/0/54/188398.html"),
    ([762, 763], "机缘", "https://www.piaotia.com/html/0/54/188459.html"),
    ([770, 771], "姚家！", "https://www.piaotia.com/html/0/54/188467.html"),
    ([797, 798], "冲出", "https://www.piaotia.com/html/0/54/188495.html"),
    ([817, 818], "避天棺", "https://www.piaotia.com/html/0/54/188520.html"),
    ([824, 825], "血神子的心思", "https://www.piaotia.com/html/0/54/188527.html"),
    ([903], "了却因果（下）", "https://www.piaotia.com/html/0/54/188619.html"),
    ([918, 919, 920], "周天", "https://www.piaotia.com/html/0/54/188640.html"),
    ([979, 980], "浮风子", "https://www.piaotia.com/html/0/54/188701.html"),
    ([991, 992], "重逢", "https://www.piaotia.com/html/0/54/188715.html"),
    ([1088, 1089], "新圣皇", "https://www.piaotia.com/html/0/54/188820.html"),
    ([1285, 1286], "苏醒！", "https://www.piaotia.com/html/0/54/189015.html"),
    ([1323], "门徒香火", "https://www.piaotia.com/html/0/54/189052.html"),
    ([1372, 1373], "炎火异晶", "https://www.piaotia.com/html/0/54/189102.html"),
    ([1376, 1377], "可敢一战！", "https://www.piaotia.com/html/0/54/189105.html"),
    ([1384, 1385], "惊弓之鸟", "https://www.piaotia.com/html/0/54/189112.html"),
    ([1389, 1390], "雕像的身份与来历", "https://www.piaotia.com/html/0/54/189116.html"),
    ([1393, 1394], "又是七彩！", "https://www.piaotia.com/html/0/54/189119.html"),
    ([1632], "本我劫", "https://www.piaotia.com/html/0/54/189358.html"),
]


def extract_clean_text(html_content: str) -> Tuple[str, List[str]]:
    """Extrait le texte brut du roman depuis une page Piaotia."""
    soup = BeautifulSoup(html_content, "html.parser")
    h1 = soup.find("h1")
    title = h1.text.strip() if h1 else ""

    # Nettoyage des balises non textuelles
    for s in soup.select("script, style, div.toplink, div.bottomlink, center, table, h1, div#Commenddiv"):
        s.decompose()

    raw_text = soup.get_text()
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    # Nettoyage du bruit et métadonnées parasites
    clean_lines = []
    for l in lines:
        if any(k in l for k in [
            "PT文学", "加入书架", "返回目录", "快捷键", "投推荐票",
            "上一章", "下一章", "点此举报", "我的藏书架", "重要声明",
            "www.piaotia.net", "All rights reserved"
        ]):
            continue
        clean_lines.append(l)

    return title, clean_lines


def save_to_destinations(fname: str, content: str):
    """Sauvegarde le fichier dans tous les dossiers cibles existants."""
    for d in ZH_DIRS:
        if d.exists():
            out_file = d / fname
            out_file.write_text(content, encoding="utf-8")


def download_and_save_all():
    print(f"[*] Démarrage du téléchargement de {len(PIAOTIA_SOURCES)} sources web...")
    success_count = 0

    for ch_nums, title, url in PIAOTIA_SOURCES:
        try:
            print(f"  -> Téléchargement {ch_nums} : {title} ({url})...")
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.encoding = "gbk"

            if r.status_code != 200:
                print(f"     [!] Erreur HTTP {r.status_code}")
                continue

            raw_title, lines = extract_clean_text(r.text)
            if len(lines) < 10:
                print(f"     [!] Contenu trop court ({len(lines)} lignes)")
                continue

            full_body = "\n\n".join(lines)

            # Cas 1: Chapitre unique (ex: 903, 1323, 1632)
            if len(ch_nums) == 1:
                n = ch_nums[0]
                fname = f"{n:04d}_{title}.txt"
                content = f"第{n}章 {title}\n\n{full_body}"
                save_to_destinations(fname, content)
                print(f"     [+] Enregistré : {fname} ({len(content)} car.)")
                success_count += 1

            # Cas 2: Deux chapitres fusionnés (ex: 1372-1373)
            elif len(ch_nums) == 2:
                n1, n2 = ch_nums
                # Découpage à mi-chemin des paragraphes pour garantir 2 fichiers équilibrés
                mid = len(lines) // 2
                part1 = "\n\n".join(lines[:mid])
                part2 = "\n\n".join(lines[mid:])

                f1 = f"{n1:04d}_{title}（一）.txt"
                c1 = f"第{n1}章 {title}（一）\n\n{part1}"
                save_to_destinations(f1, c1)

                f2 = f"{n2:04d}_{title}（二）.txt"
                c2 = f"第{n2}章 {title}（二）\n\n{part2}"
                save_to_destinations(f2, c2)

                print(f"     [+] Enregistré : {f1} ({len(c1)} car.) & {f2} ({len(c2)} car.)")
                success_count += 2

            # Cas 3: Trois chapitres fusionnés (ex: 918-920)
            elif len(ch_nums) == 3:
                n1, n2, n3 = ch_nums
                step = len(lines) // 3
                part1 = "\n\n".join(lines[:step])
                part2 = "\n\n".join(lines[step:2*step])
                part3 = "\n\n".join(lines[2*step:])

                f1 = f"{n1:04d}_{title}（一）.txt"
                c1 = f"第{n1}章 {title}（一）\n\n{part1}"
                save_to_destinations(f1, c1)

                f2 = f"{n2:04d}_{title}（二）.txt"
                c2 = f"第{n2}章 {title}（二）\n\n{part2}"
                save_to_destinations(f2, c2)

                f3 = f"{n3:04d}_{title}（三）.txt"
                c3 = f"第{n3}章 {title}（三）\n\n{part3}"
                save_to_destinations(f3, c3)

                print(f"     [+] Enregistré : {f1}, {f2}, {f3}")
                success_count += 3

            time.sleep(0.5)

        except Exception as e:
            print(f"     [!] Exception sur {ch_nums}: {e}")

    print(f"\n[+] Téléchargement terminé avec succès pour {success_count} numéros de chapitres !")


if __name__ == "__main__":
    download_and_save_all()
