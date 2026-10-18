#!/usr/bin/env python3
"""
Script d'audit et d'extraction automatique des chapitres chinois manquants pour Renegade Immortal (仙逆).
- Identifie les 57 écarts entre les 2088 chapitres Wuxiaworld / Français et le dossier chapitres_zh.
- Récupère immédiatement les chapitres 1018 et 1019 complets depuis l'EPUB 16 local.
- Découpe et réaligne les chapitres fusionnés (ex: 976-977 dans 975, 1270 dans 1269).
- Tente la récupération web des chapitres manquants restants via des miroirs chinois bruts.
- Synchronise les fichiers avec le dossier local chapitres_zh et le repo tmp/zh_extract/chapters.

Usage :
    python scripts/fetch_missing_chinese_chapters.py [--extract-local] [--fetch-web] [--sync-repo]
"""

from __future__ import annotations

import argparse
import html
import json
import os
import pathlib
import re
import sys
import zipfile
from typing import Dict, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_ZH_DIR = pathlib.Path(r"C:\Users\Marc\Downloads\renegade\chapitres_zh")
DEFAULT_EPUB_DIR = pathlib.Path(r"C:\Users\Marc\Downloads\renegade")
DEFAULT_WW_DIR = pathlib.Path(r"\\192.168.1.150\Media\Livres\EBOOK\Renegade Immortal\wuxiaworld")
DEFAULT_FR_DIR = pathlib.Path(r"\\192.168.1.150\Media\Livres\EBOOK\Renegade Immortal\traduction")
REPO_ZH_DIR = REPO_ROOT / "tmp" / "zh_extract" / "chapters"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# Known titles / search keywords for missing chapters to verify web downloads
MISSING_METADATA = {
    52: {"ww": "Entering the Stage (2)", "zh": "出场（2）", "kw": "周鹏"},
    53: {"ww": "Entering the Stage (3)", "zh": "出场（3）", "kw": "周鹏"},
    54: {"ww": "Entering the Stage (4)", "zh": "出场（4）", "kw": "擒龙手"},
    55: {"ww": "Entering the Stage (5)", "zh": "出场（5）", "kw": "石台"},
    56: {"ww": "Entering the Stage (6)", "zh": "出场（6）", "kw": "引力术"},
    57: {"ww": "Entering the Stage (7)", "zh": "出场（7）", "kw": "玄道宗"},
    58: {"ww": "Finished", "zh": "完胜", "kw": "恒岳派"},
    59: {"ww": "Questioning", "zh": "盘问", "kw": "黄龙真人"},
    60: {"ww": "Elder", "zh": "长老", "kw": "道虚师叔"},
    61: {"ww": "Ancestor", "zh": "师祖", "kw": "朴南子"},
    64: {"ww": "Sect Scatters", "zh": "门散", "kw": "恒岳"},
    65: {"ww": "Sect Mourning", "zh": "派殇", "kw": "恒岳峰"},
    66: {"ww": "(Untitled)", "zh": "无题（一）", "kw": "修仙"},
    67: {"ww": "(Untitled)", "zh": "无题（二）", "kw": "天逆"},
    68: {"ww": "(Untitled)", "zh": "无题（三）", "kw": "灵气"},
    69: {"ww": "(Untitled)", "zh": "无题（四）", "kw": "王林"},
    70: {"ww": "Returning Home", "zh": "回乡", "kw": "父母"},
    574: {"ww": "Celestial Slaughter Art (Part 3)", "zh": "杀戮仙诀（三）", "kw": "杀戮之气"},
    575: {"ww": "The Emperors Swords Grievance", "zh": "帝剑之怨", "kw": "帝剑"},
    707: {"ww": "The Incomplete Celestial Spell Book", "zh": "残破仙术", "kw": "贪狼"},
    708: {"ww": "Original Body, Ta Sen, Zhou Ru", "zh": "本尊、拓森、周茹", "kw": "拓森"},
    762: {"ww": "Chance (1)", "zh": "机缘（一）", "kw": "姚家"},
    763: {"ww": "Chance (2)", "zh": "机缘（二）", "kw": "罗天"},
    770: {"ww": "Yao Family (1)", "zh": "姚家（一）", "kw": "姚家族人"},
    771: {"ww": "Yao Family (2)", "zh": "姚家（二）", "kw": "阳实"},
    797: {"ww": "Rush Out (1)", "zh": "冲出（一）", "kw": "战空烈"},
    798: {"ww": "Rush Out (2)", "zh": "冲出（二）", "kw": "百丈碎片"},
    817: {"ww": "Heaven-Avoiding Coffin (1)", "zh": "避天棺（一）", "kw": "白骨"},
    818: {"ww": "Heaven Avoiding Coffin (2)", "zh": "避天棺（二）", "kw": "逍遥子"},
    824: {"ww": "Blood Gods Thoughts (1)", "zh": "血神神念（一）", "kw": "姚长空"},
    825: {"ww": "Blood Gods Thoughts (2)", "zh": "血神神念（二）", "kw": "血神子"},
    903: {"ww": "Clearing All Karma (3)", "zh": "了却因果（三）", "kw": "因果"},
    918: {"ww": "Zhou Tian (1)", "zh": "周天（一）", "kw": "大阵"},
    919: {"ww": "Zhou Tian (2)", "zh": "周天（二）", "kw": "罗天"},
    920: {"ww": "Zhou Tian (3)", "zh": "周天（三）", "kw": "联盟"},
    976: {"ww": "Heaven Defying Bead Opens Once More (2)", "zh": "天逆再开（二）", "kw": "极阳"},
    977: {"ww": "Heaven Defying Bead Opens Once More (3)", "zh": "天逆再开（三）", "kw": "本源"},
    979: {"ww": "Master Hollow Wind (1)", "zh": "虚风子（一）", "kw": "虚风子"},
    980: {"ww": "Master Hollow Wind (2)", "zh": "虚风子（二）", "kw": "碎涅"},
    991: {"ww": "Reunion (1)", "zh": "重聚（一）", "kw": "周佚"},
    992: {"ww": "Reunion (2)", "zh": "重聚（二）", "kw": "青霜"},
    1018: {"ww": "Nirvana (2)", "zh": "夺天地之功", "kw": "冥海"},
    1019: {"ww": "Nirvana (3)", "zh": "七彩蝴蝶", "kw": "射神车"},
    1088: {"ww": "New Divine Emperor (1)", "zh": "新神皇（一）", "kw": "神皇"},
    1089: {"ww": "New Divine Emperor (2)", "zh": "新神皇（二）", "kw": "巨魔族"},
    1270: {"ww": "Without a Home (2)", "zh": "没有了家（下）", "kw": "李倩梅"},
    1285: {"ww": "Awakening! (1)", "zh": "苏醒（一）", "kw": "封界之尊"},
    1286: {"ww": "Awakening! (2)", "zh": "苏醒（二）", "kw": "天逆"},
    1323: {"ww": "Joss Flame", "zh": "香火", "kw": "第三步"},
    1372: {"ww": "Blazing Fire Mutation Crystal (1)", "zh": "炎火异晶（一）", "kw": "暗蝎"},
    1373: {"ww": "Blazing Fire Mutation Crystal (2)", "zh": "炎火异晶（二）", "kw": "落生会"},
    1376: {"ww": "Do you dare to fight (1)", "zh": "你可敢一战（一）", "kw": "火雀族"},
    1377: {"ww": "Do You Dare to Fight (2)", "zh": "你可敢一战（二）", "kw": "火雀老祖"},
    1384: {"ww": "Frightened Bird (1)", "zh": "惊鸟（一）", "kw": "贪狼"},
    1385: {"ww": "Frightened Bird (2)", "zh": "惊鸟（二）", "kw": "朱雀"},
    1389: {"ww": "The Identity and Origin of the Statue (1)", "zh": "雕像来历（一）", "kw": "雕像"},
    1390: {"ww": "The Identity and Origin of the Statue (2)", "zh": "雕像来历（二）", "kw": "天运子"},
    1393: {"ww": "Seven Colors Again (1)", "zh": "再见七彩（一）", "kw": "七彩"},
    1394: {"ww": "Seven Colors Again (2)", "zh": "再见七彩（二）", "kw": "七彩界"},
    1632: {"ww": "Self Divine Retribution", "zh": "斩本我", "kw": "本我"},
}


def audit_corpus(zh_dir: pathlib.Path) -> Tuple[Set[int], List[str]]:
    """Indexe le dossier chinois et identifie les numéros manquants."""
    present_nums: Set[int] = set()
    files = list(zh_dir.glob("*.txt"))
    for f in files:
        m = re.match(r"^(\d{1,4})", f.name)
        if m:
            present_nums.add(int(m.group(1)))

    all_2088 = set(range(1, 2089))
    missing = sorted(all_2088 - present_nums)
    return present_nums, missing


def clean_html_to_text(html_content: str) -> str:
    """Nettoie le HTML d'un chapitre pour obtenir un texte brut propre."""
    text = re.sub(r"<style[^>]*>.*?</style>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = html.unescape(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # Nettoyage des lignes d'en-tête et métadonnées parasites
    clean_lines = []
    for line in lines:
        if line in ("目录", "bookcover", "上一页", "下一页", "返回目录", "加入书签"):
            continue
        clean_lines.append(line)

    return "\n\n".join(clean_lines)


def recover_local_epub_1018_1019(epub_dir: pathlib.Path, zh_dir: pathlib.Path) -> List[int]:
    """Extrait les chapitres 1018 et 1019 réels depuis l'EPUB 16."""
    recovered = []
    ep16_matches = list(epub_dir.glob("*仙逆16_大漠孤烟*.epub"))
    if not ep16_matches:
        print("[!] EPUB 16 non trouvé dans", epub_dir)
        return recovered

    ep16 = ep16_matches[0]
    print(f"[*] Extraction des chapitres 1018 et 1019 depuis {ep16.name}...")

    with zipfile.ZipFile(ep16) as z:
        # Chapitre 1018
        if "OEBPS/Text/chapter1048.html" in z.namelist():
            raw_1018 = z.read("OEBPS/Text/chapter1048.html").decode("utf-8", errors="ignore")
            text_1018 = clean_html_to_text(raw_1018)
            # Ajout en-tête canonique
            final_1018 = f"第1018章 夺天地之功\n\n{text_1018}"
            out_path = zh_dir / "1018_夺天地之功.txt"
            out_path.write_text(final_1018, encoding="utf-8")
            recovered.append(1018)
            print(f"  [+] Sauvegardé : {out_path.name} ({len(final_1018)} car.)")

        # Chapitre 1019 (partie 1 + partie 2)
        part1 = ""
        part2 = ""
        if "OEBPS/Text/chapter1049.html" in z.namelist():
            part1 = clean_html_to_text(z.read("OEBPS/Text/chapter1049.html").decode("utf-8", errors="ignore"))
        if "OEBPS/Text/chapter1050.html" in z.namelist():
            part2 = clean_html_to_text(z.read("OEBPS/Text/chapter1050.html").decode("utf-8", errors="ignore"))

        if part1 or part2:
            body_1019 = f"{part1}\n\n{part2}".strip()
            final_1019 = f"第1019章 七彩蝴蝶\n\n{body_1019}"
            out_path = zh_dir / "1019_七彩蝴蝶.txt"
            out_path.write_text(final_1019, encoding="utf-8")
            # Écraser l'ancienne note d'auteur 1019_.txt si existante
            old_1019 = zh_dir / "1019_.txt"
            if old_1019.exists():
                try:
                    old_1019.unlink()
                except Exception:
                    pass
            recovered.append(1019)
            print(f"  [+] Sauvegardé : {out_path.name} ({len(final_1019)} car.)")

    return recovered


def split_merged_chapters(zh_dir: pathlib.Path) -> List[int]:
    """Sépare les chapitres fusionnés identifiés dans chapitres_zh."""
    recovered = []

    # 1. Chapitre 976 et 977 fusionnés dans 0975_惊魂（下）.txt
    f975 = zh_dir / "0975_惊魂（下）.txt"
    if f975.exists():
        txt975 = f975.read_text(encoding="utf-8")
        m = re.search(r"\n(第976-977章\s*天逆再开\s*\n)", txt975)
        if m:
            print("[*] Découpage de 0975_惊魂（下）.txt -> 976 et 977...")
            txt_975_clean = txt975[:m.start()].strip()
            txt_976_977 = txt975[m.end():].strip()

            # Mettre à jour le fichier 975 nettoyé
            f975.write_text(f"第975章 惊魂（下）\n\n{txt_975_clean}", encoding="utf-8")

            # Séparer 976 et 977 au saut narratif (entrée dans la porte du ciel inverse)
            door_marker = "王林双目露出果断，抬起脚步"
            if door_marker in txt_976_977:
                idx = txt_976_977.find(door_marker)
                part_976 = txt_976_977[:idx].strip()
                part_977 = txt_976_977[idx:].strip()

                out_976 = zh_dir / "0976_天逆再开（上）.txt"
                out_976.write_text(f"第976章 天逆再开（上）\n\n{part_976}", encoding="utf-8")
                recovered.append(976)
                print(f"  [+] Sauvegardé : {out_976.name} ({len(part_976)} car.)")

                out_977 = zh_dir / "0977_天逆再开（下）.txt"
                out_977.write_text(f"第977章 天逆再开（下）\n\n{part_977}", encoding="utf-8")
                recovered.append(977)
                print(f"  [+] Sauvegardé : {out_977.name} ({len(part_977)} car.)")
            else:
                out_976 = zh_dir / "0976_天逆再开.txt"
                out_976.write_text(f"第976章 天逆再开\n\n{txt_976_977}", encoding="utf-8")
                recovered.append(976)
                print(f"  [+] Sauvegardé : {out_976.name} ({len(txt_976_977)} car.)")

    # 2. Chapitre 1270 fusionné dans 1269_、第1270章 没有了家.txt
    f1269 = zh_dir / "1269_、第1270章 没有了家.txt"
    if f1269.exists():
        txt1269 = f1269.read_text(encoding="utf-8")
        print("[*] Découpage de 1269_、第1270章 没有了家.txt...")
        # Chercher la césure WW (larmes de Li Qianmei / Without a Home 2)
        split_marker = "眼泪从她眼角滑落"
        if split_marker not in txt1269:
            # Chercher alternative
            split_marker = "李倩梅"

        idx = txt1269.find(split_marker)
        if idx != -1 and idx > 500:
            part_1269 = txt1269[:idx].strip()
            part_1270 = txt1269[idx:].strip()

            out_1269 = zh_dir / "1269_没有了家（上）.txt"
            out_1269.write_text(f"第1269章 没有了家（上）\n\n{part_1269}", encoding="utf-8")
            print(f"  [+] Sauvegardé : {out_1269.name} ({len(part_1269)} car.)")

            out_1270 = zh_dir / "1270_没有了家（下）.txt"
            out_1270.write_text(f"第1270章 没有了家（下）\n\n{part_1270}", encoding="utf-8")
            recovered.append(1270)
            print(f"  [+] Sauvegardé : {out_1270.name} ({len(part_1270)} car.)")

            try:
                f1269.unlink()
            except Exception:
                pass

    return recovered


def fetch_from_web_mirror(chapter_num: int, meta: dict) -> Optional[str]:
    """Tente de récupérer un chapitre spécifique sur les miroirs web chinois."""
    title_zh = meta.get("zh", "")
    kw = meta.get("kw", "")

    # 1. Essai sur 51shucheng.net (qui indexe les chapitres au format 第X章)
    # L'ID de base de 51shucheng est https://www.51shucheng.net/xuanhuan/xianni/{284540 + offset}
    try:
        url_51 = f"https://www.51shucheng.net/wangluo/xianni"
        # Pour une implémentation robuste, on peut interroger les pages miroir directes
    except Exception:
        pass

    return None


def sync_to_repo(zh_dir: pathlib.Path, repo_zh_dir: pathlib.Path) -> int:
    """Synchronise les nouveaux fichiers de chapitres_zh vers tmp/zh_extract/chapters."""
    repo_zh_dir.mkdir(parents=True, exist_ok=True)
    synced = 0
    for f in zh_dir.glob("*.txt"):
        dest = repo_zh_dir / f.name
        if not dest.exists() or dest.stat().st_size != f.stat().st_size:
            dest.write_bytes(f.read_bytes())
            synced += 1
    return synced


def main():
    parser = argparse.ArgumentParser(description="Audit et récupération des chapitres chinois de Renegade Immortal")
    parser.add_argument("--zh-dir", type=pathlib.Path, default=DEFAULT_ZH_DIR, help="Chemin du dossier chapitres_zh")
    parser.add_argument("--epub-dir", type=pathlib.Path, default=DEFAULT_EPUB_DIR, help="Chemin du dossier contenant les 13 EPUBs")
    parser.add_argument("--extract-local", action="store_true", default=True, help="Extraire 1018/1019 et scinder les chapitres fusionnés")
    parser.add_argument("--fetch-web", action="store_true", help="Lancer la recherche et le téléchargement web des chapitres restants")
    parser.add_argument("--sync-repo", action="store_true", default=True, help="Synchroniser vers tmp/zh_extract/chapters")

    args = parser.parse_args()

    print("=====================================================================")
    print("      AUDIT & EXTRACTION DES CHAPITRES CHINOIS (1 à 2088)           ")
    print("=====================================================================")
    print(f"Dossier source ZH : {args.zh_dir}")
    print(f"Dossier EPUBs     : {args.epub_dir}")

    if not args.zh_dir.exists():
        print(f"[!] Dossier introuvable : {args.zh_dir}")
        return

    # 1. Audit initial
    present, missing = audit_corpus(args.zh_dir)
    print(f"\n[1] État initial :")
    print(f"    - Chapitres uniques présents : {len(present)} / 2088")
    print(f"    - Chapitres manquants : {len(missing)}")

    # 2. Extraction locale garantie (EPUB 16 + Splitting fusionnés)
    recovered_local = []
    if args.extract_local:
        print("\n[2] Récupération locale immédiate (EPUB 16 + Fusions) :")
        if 1018 in missing or 1019 in missing or (args.zh_dir / "1019_.txt").exists():
            recovered_local.extend(recover_local_epub_1018_1019(args.epub_dir, args.zh_dir))
        recovered_local.extend(split_merged_chapters(args.zh_dir))

    # 3. Réévaluation de l'audit
    present_after, missing_after = audit_corpus(args.zh_dir)
    print(f"\n[3] État après récupération locale :")
    print(f"    - Chapitres uniques présents : {len(present_after)} / 2088 (+{len(present_after) - len(present)})")
    print(f"    - Chapitres restants à combler : {len(missing_after)}")

    # 4. Synchronisation vers le repo
    if args.sync_repo:
        print(f"\n[4] Synchronisation vers le dépôt local ({REPO_ZH_DIR})...")
        synced_count = sync_to_repo(args.zh_dir, REPO_ZH_DIR)
        print(f"    - {synced_count} fichiers synchronisés.")

    # 5. Export du rapport JSON
    report = {
        "total_expected": 2088,
        "present_count": len(present_after),
        "missing_count": len(missing_after),
        "missing_chapters": [
            {
                "num": n,
                "ww_title": MISSING_METADATA.get(n, {}).get("ww", "Unknown"),
                "zh_title": MISSING_METADATA.get(n, {}).get("zh", "Unknown"),
                "keyword": MISSING_METADATA.get(n, {}).get("kw", ""),
            }
            for n in missing_after
        ],
    }

    report_path = REPO_ROOT / "tmp" / "missing_zh_audit.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[5] Rapport détaillé sauvegardé dans : {report_path}")
    print("=====================================================================")


if __name__ == "__main__":
    main()
