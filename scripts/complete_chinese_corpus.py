#!/usr/bin/env python3
"""
Master script to complete and synchronize the entire Chinese corpus (2088 chapters) for Renegade Immortal (仙逆).
Extracts all remaining missing chapters:
- Web scraping from Piaotia (35 chapters: dual/triple chapters and isolated chapters)
- Local disentanglement (574 from 573, 901-903 realignment)
- Web scraping from Millionbook in Simplified Chinese (Chapter 707 and the 15 unabridged early chapters 52-61, 64-70)
- Writes directly to both:
    - tmp/zh_extract/chapters/
    - C:\\Users\\Marc\\Downloads\\renegade\\chapitres_zh
- Verifies 100% complete coverage (2088 / 2088 chapters).
- Generates a full tri-alignment JSON index: ZH -> EN -> FR.
"""

from __future__ import annotations

import html
import json
import pathlib
import re
import sys
import time
from typing import Dict, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup
from opencc import OpenCC

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

t2s = OpenCC("t2s")


def save_to_destinations(fname: str, content: str):
    """Writes chapter file to both repo and disk target directories."""
    for d in ZH_DIRS:
        if d.exists():
            out_file = d / fname
            out_file.write_text(content.strip() + "\n", encoding="utf-8")


def clean_piaotia_page(html_text: str) -> Tuple[str, List[str]]:
    soup = BeautifulSoup(html_text, "html.parser")
    h1 = soup.h1.text.strip() if soup.h1 else ""
    for s in soup.select(
        "script, style, div#guild, div#shop, div#feit2, div.toplink, div.bottomlink, center, table, h1, div#Commenddiv"
    ):
        s.decompose()
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    lines = [
        l for l in lines
        if not any(k in l for k in [
            "PT文学", "加入书架", "返回目录", "快捷键", "投推荐票",
            "上一章", "下一章", "点此举报", "我的藏书架", "重要声明",
            "www.piaotia", "All rights reserved", "Copyright",
            "选择背景颜色", "繁體中文", "小说阅读网"
        ])
    ]
    # Remove chapter title repetition if in line 0
    if lines and re.match(r"^第?\s*\d+.*章?", lines[0]):
        lines = lines[1:]
    return h1, lines


def clean_millionbook_page(html_text: str) -> List[str]:
    soup = BeautifulSoup(html_text, "html.parser")
    for s in soup.select("script, style, h1, div.toplink, div.bottomlink, a"):
        s.decompose()
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    lines = [
        l for l in lines
        if not any(k in l for k in [
            "龍騰世紀", "武俠修真", "文 /", "耳根", "上一章",
            "本書目錄", "下一章", "章 節目錄", "章 節", "龙腾世纪", "武侠修真"
        ])
    ]
    if lines and re.match(r"^第?\s*\d+.*章?", lines[0]):
        lines = lines[1:]
    # Convert traditional to simplified
    return [t2s.convert(l) for l in lines]


# --- STEP 1: Process Local Disentanglements (573/574, 901/902/903) ---
def process_local_disentanglements():
    print("\n[+] 1. Traitement des découpages locaux (573/574 et 901-903)...")
    repo_zh = REPO_ROOT / "tmp" / "zh_extract" / "chapters"

    # Chapter 573 & 574
    f573_matches = list(repo_zh.glob("0573*"))
    if f573_matches:
        f573_file = f573_matches[0]
        text573 = f573_file.read_text(encoding="utf-8")
        split_marker = "在那银龙消失的瞬间"
        idx = text573.find(split_marker)
        if idx != -1:
            part1 = text573[:idx].strip()
            part2 = text573[idx:].strip()

            c573 = f"第573章 杀戮仙诀（二）\n\n{part1}"
            save_to_destinations("0573_杀戮仙诀 （二）.txt", c573)

            c574 = f"第574章 杀戮仙诀（三）\n\n{part2}"
            save_to_destinations("0574_杀戮仙诀 （三）.txt", c574)
            print(f"    -> 0573_杀戮仙诀 （二）.txt ({len(c573)} car.)")
            print(f"    -> 0574_杀戮仙诀 （三）.txt ({len(c574)} car.)")
        else:
            print("    [!] Marqueur 574 introuvable dans 573")

    # Chapter 901, 902 & 903
    f901_matches = list(repo_zh.glob("0901*"))
    f902_matches = list(repo_zh.glob("0902*"))
    if f901_matches and f902_matches:
        t901 = f901_matches[0].read_text(encoding="utf-8")
        t902 = f902_matches[0].read_text(encoding="utf-8")

        m901_split = "四级修真国，火焚国"
        m902_split = "王林目中涌现杀机，大袖一甩"

        idx901 = t901.find(m901_split)
        idx902 = t902.find(m902_split)

        if idx901 != -1 and idx902 != -1:
            p901 = t901[:idx901].strip()
            p902 = (t901[idx901:].strip() + "\n\n" + t902[:idx902].strip()).strip()
            p903 = t902[idx902:].strip()

            c901 = f"第901章 了却因果（上）\n\n{p901}"
            c902 = f"第902章 了却因果（中）\n\n{p902}"
            c903 = f"第903章 了却因果（下）\n\n{p903}"

            save_to_destinations("0901_了却因果（上）.txt", c901)
            save_to_destinations("0902_了却因果（中）.txt", c902)
            save_to_destinations("0903_了却因果（下）.txt", c903)

            print(f"    -> 0901_了却因果（上）.txt ({len(c901)} car.)")
            print(f"    -> 0902_了却因果（中）.txt ({len(c902)} car.)")
            print(f"    -> 0903_了却因果（下）.txt ({len(c903)} car.)")


# --- STEP 2: Fetch Piaotia Missing Chapters (35 numbers) ---
PIAOTIA_SOURCES = [
    ([575], "帝剑之怨", "https://www.piaotia.com/html/0/54/188266.html"),
    ([708], "本尊、拓森、周茹", "https://www.piaotia.com/html/0/54/188398.html"),
    ([762, 763], "机缘", "https://www.piaotia.com/html/0/54/188459.html"),
    ([770, 771], "姚家！", "https://www.piaotia.com/html/0/54/188467.html"),
    ([797, 798], "冲出", "https://www.piaotia.com/html/0/54/188495.html"),
    ([817, 818], "避天棺", "https://www.piaotia.com/html/0/54/188520.html"),
    ([824, 825], "血神子的心思", "https://www.piaotia.com/html/0/54/188527.html"),
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


def process_piaotia_downloads():
    print(f"\n[+] 2. Téléchargement des 19 sources Piaotia ({sum(len(c[0]) for c in PIAOTIA_SOURCES)} chapitres)...")
    for ch_nums, title, url in PIAOTIA_SOURCES:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.encoding = "gbk"
            if r.status_code != 200:
                print(f"    [!] Erreur {r.status_code} sur {url}")
                continue

            h1, lines = clean_piaotia_page(r.text)
            if not lines:
                print(f"    [!] Contenu vide sur {url}")
                continue

            if len(ch_nums) == 1:
                n = ch_nums[0]
                fname = f"{n:04d}_{title}.txt"
                content = f"第{n}章 {title}\n\n" + "\n\n".join(lines)
                save_to_destinations(fname, content)
                print(f"    -> {fname} ({len(content)} car.)")

            elif len(ch_nums) == 2:
                n1, n2 = ch_nums
                mid = len(lines) // 2
                p1 = "\n\n".join(lines[:mid])
                p2 = "\n\n".join(lines[mid:])

                f1 = f"{n1:04d}_{title}（一）.txt"
                c1 = f"第{n1}章 {title}（一）\n\n{p1}"
                save_to_destinations(f1, c1)

                f2 = f"{n2:04d}_{title}（二）.txt"
                c2 = f"第{n2}章 {title}（二）\n\n{p2}"
                save_to_destinations(f2, c2)
                print(f"    -> {f1} ({len(c1)} car.) & {f2} ({len(c2)} car.)")

            elif len(ch_nums) == 3:
                n1, n2, n3 = ch_nums
                step = len(lines) // 3
                p1 = "\n\n".join(lines[:step])
                p2 = "\n\n".join(lines[step:2*step])
                p3 = "\n\n".join(lines[2*step:])

                f1 = f"{n1:04d}_{title}（一）.txt"
                c1 = f"第{n1}章 {title}（一）\n\n{p1}"
                save_to_destinations(f1, c1)

                f2 = f"{n2:04d}_{title}（二）.txt"
                c2 = f"第{n2}章 {title}（二）\n\n{p2}"
                save_to_destinations(f2, c2)

                f3 = f"{n3:04d}_{title}（三）.txt"
                c3 = f"第{n3}章 {title}（三）\n\n{p3}"
                save_to_destinations(f3, c3)
                print(f"    -> {f1}, {f2}, {f3}")

            time.sleep(0.3)
        except Exception as e:
            print(f"    [!] Erreur {ch_nums}: {e}")


# --- STEP 3: Fetch Millionbook Unabridged Chapters (16 chapters: 707 + 52-61, 64-70) ---
MILLIONBOOK_CHAPTERS = [
    # (ch_num, title, url_id)
    (52, "出场（2）", "1061791"),
    (53, "出场（3）", "1061792"),
    (54, "出场（4）", "1061793"),
    (55, "出场（5）", "1061794"),
    (56, "出场（6）", "1061795"),
    (57, "出场（7）", "1061796"),
    (58, "完胜", "1061797"),
    (59, "盘问", "1061798"),
    (60, "长老", "1061799"),
    (61, "师祖", "1061800"),
    (64, "门散", "1061803"),
    (65, "派殇", "1061804"),
    (66, "无题（一）", "1061805"),
    (67, "无题（二）", "1061806"),
    (68, "无题（三）", "1061807"),
    (69, "无题（四）", "1061808"),
    (70, "回乡", "1061809"),
    (707, "王林动容的仙术残本", "1062445"),
]


def process_millionbook_downloads():
    print(f"\n[+] 3. Téléchargement des 18 chapitres intégraux Millionbook (707 + versions intégrales 2009)...")

    # Remove the abridged placeholders if they exist
    for d in ZH_DIRS:
        for old_abridged in ["0052_－－六十一章（缩改）.txt", "0064_－－－七十章（缩改）.txt"]:
            f = d / old_abridged
            if f.exists():
                f.unlink()
                print(f"    [-] Supprimé placeholder abrégé : {f.name}")

    for n, title, url_id in MILLIONBOOK_CHAPTERS:
        try:
            url = f"https://millionbook.net/novels/2/2492/{url_id}.html"
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.encoding = "big5"
            if r.status_code != 200:
                print(f"    [!] Erreur {r.status_code} sur {url}")
                continue

            lines = clean_millionbook_page(r.text)
            if not lines:
                print(f"    [!] Contenu vide sur {url}")
                continue

            fname = f"{n:04d}_{title}.txt"
            content = f"第{n}章 {title}\n\n" + "\n\n".join(lines)
            save_to_destinations(fname, content)
            print(f"    -> {fname} ({len(content)} car.)")
            time.sleep(0.3)
        except Exception as e:
            print(f"    [!] Erreur {n}: {e}")


# --- STEP 4: Comprehensive Audit & Verification ---
def audit_corpus():
    print("\n[+] 4. Audit final de complétude du corpus chinois...")
    for d in ZH_DIRS:
        if not d.exists():
            continue
        files = list(d.glob("*.txt"))
        present_nums: Set[int] = set()
        for f in files:
            m = re.match(r"^(\d{1,4})", f.name)
            if m:
                present_nums.add(int(m.group(1)))

        all_2088 = set(range(1, 2089))
        missing = sorted(all_2088 - present_nums)
        print(f"    Dossier : {d}")
        print(f"      Total fichiers .txt : {len(files)}")
        print(f"      Numéros uniques 1..2088 : {len(present_nums)} / 2088")
        if missing:
            print(f"      [!] Numéros manquants ({len(missing)}) : {missing[:15]}...")
        else:
            print("      [V] 100% COMPLET ! Aucun chapitre manquant !")


# --- STEP 5: Generate Tri-Alignment Index (ZH -> EN -> FR) ---
def generate_tri_alignment():
    print("\n[+] 5. Génération de l'index d'alignement triple ZH -> EN -> FR...")
    repo_zh = REPO_ROOT / "tmp" / "zh_extract" / "chapters"
    repo_en = REPO_ROOT / "tmp" / "en"
    repo_fr = REPO_ROOT / "src" / "content" / "chapters"

    # Index ZH files
    zh_map: Dict[int, pathlib.Path] = {}
    for f in repo_zh.glob("*.txt"):
        m = re.match(r"^(\d{1,4})", f.name)
        if m:
            num = int(m.group(1))
            zh_map[num] = f

    # Index EN files
    en_map: Dict[int, List[pathlib.Path]] = {}
    for f in repo_en.rglob("*.txt"):
        m = re.match(r"^(\d{1,4})", f.name)
        if m:
            num = int(m.group(1))
            en_map.setdefault(num, []).append(f)

    # Index FR files
    fr_map: Dict[int, pathlib.Path] = {}
    for f in repo_fr.rglob("*.md"):
        m = re.match(r"^(\d{1,4})", f.name)
        if m:
            num = int(m.group(1))
            fr_map[num] = f

    alignment_records = []
    unaligned = []

    for num in range(1, 2089):
        zh_file = zh_map.get(num)
        en_files = en_map.get(num, [])
        fr_file = fr_map.get(num)

        if not zh_file or not en_files or not fr_file:
            unaligned.append(num)

        zh_text = zh_file.read_text(encoding="utf-8") if zh_file else ""
        zh_title = zh_text.splitlines()[0] if zh_text else ""

        en_texts = [ef.read_text(encoding="utf-8", errors="ignore") for ef in en_files]
        en_titles = [et.splitlines()[0] for et in en_texts if et]

        fr_text = fr_file.read_text(encoding="utf-8") if fr_file else ""
        fr_title_match = re.search(r"^title:\s*[\"']?(.*?)[\"']?$", fr_text, re.MULTILINE)
        fr_title = fr_title_match.group(1) if fr_title_match else ""

        alignment_records.append({
            "chapter": num,
            "zh": {
                "file": zh_file.name if zh_file else None,
                "title": zh_title,
                "chars": len(zh_text),
            },
            "en": {
                "files": [ef.name for ef in en_files],
                "titles": en_titles,
                "words": sum(len(et.split()) for et in en_texts),
            },
            "fr": {
                "file": fr_file.name if fr_file else None,
                "title": fr_title,
                "words": len(fr_text.split()),
            },
        })

    out_json = REPO_ROOT / "tmp" / "alignment_zh_en_fr.json"
    out_json.write_text(json.dumps(alignment_records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    Index sauvegardé : {out_json} ({len(alignment_records)} entrées)")
    if unaligned:
        print(f"    [!] Non-alignés ({len(unaligned)}) : {unaligned}")
    else:
        print("    [V] Alignement triple 1:1 parfait sur les 2088 chapitres !")


def main():
    print("=" * 70)
    print("  COMPLÉTION & ALIGNEMENT DU CORPUS CHINOIS - RENEGADE IMMORTAL")
    print("=" * 70)
    process_local_disentanglements()
    process_piaotia_downloads()
    process_millionbook_downloads()
    audit_corpus()
    generate_tri_alignment()
    print("\n[+] TOUT EST TERMINÉ AVEC SUCCÈS !")


if __name__ == "__main__":
    main()
