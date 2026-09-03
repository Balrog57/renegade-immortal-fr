#!/usr/bin/env python3
"""Corrections systématiques FR à partir des 700 paires Qidian alignées.

- Remplacements lexicaux sûrs (rangs, noms anglais résiduels).
- Conversion 丈/里 → mètres/km lorsque le même nombre apparaît en FR (pieds/km).
- Journal interne (peut contenir du chinois) : tmp/zh_extract/fix_log.md
"""
from __future__ import annotations

import json
import pathlib
import re
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
ALIGNED = ROOT / "tmp" / "zh_extract" / "aligned.json"
ZH_DIR = ROOT / "tmp" / "zh_extract" / "chapters"
FR_DIR = ROOT / "src" / "content" / "chapters"
LOG_PATH = ROOT / "tmp" / "zh_extract" / "fix_log.md"

CN_DIGITS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}

FR_CARDINALS = {
    "un": 1,
    "une": 1,
    "deux": 2,
    "trois": 3,
    "quatre": 4,
    "cinq": 5,
    "six": 6,
    "sept": 7,
    "huit": 8,
    "neuf": 9,
    "dix": 10,
    "onze": 11,
    "douze": 12,
    "treize": 13,
    "quatorze": 14,
    "quinze": 15,
    "seize": 16,
    "vingt": 20,
    "trente": 30,
    "quarante": 40,
    "cinquante": 50,
    "soixante": 60,
    "cent": 100,
    "cents": 100,
    "mille": 1000,
}

# Lexical replacements applied to all French chapter markdown (and later wiki).
LEXICAL: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"Séparation de l['’]Esprit"), "Formation de l'Âme"),
    (re.compile(r"Séparation de l['’]esprit"), "Formation de l'Âme"),
    (re.compile(r"Formation de l['’]Esprit"), "Formation de l'Âme"),
    (re.compile(r"Formation d['’]Esprit"), "Formation de l'Âme"),
    (re.compile(r"Transformation Spirituelle"), "Formation de l'Âme"),
    (re.compile(r"\bQin Lin\b"), "Qing Lin"),
    (re.compile(r"\bRed Butterfly\b"), "Papillon Rouge"),
    (re.compile(r"\bTeng Hauyaun\b"), "Teng Huayuan"),
    (re.compile(r"l['’]All-Seer"), "l'Omniscient"),
    (re.compile(r"L['’]All-Seer"), "L'Omniscient"),
    (re.compile(r"\bAll-Seer\b"), "Omniscient"),
    (re.compile(r"l['’]honorable Très-Sage"), "l'honorable Omniscient"),
    (re.compile(r"le Très-Sage"), "l'Omniscient"),
    (re.compile(r"Le Très-Sage"), "L'Omniscient"),
    (re.compile(r"\bTrès-Sage\b"), "Omniscient"),
    (re.compile(r"le Tout-voyant"), "l'Omniscient"),
    (re.compile(r"Le Tout-voyant"), "L'Omniscient"),
    (re.compile(r"au Tout-voyant"), "à l'Omniscient"),
    (re.compile(r"du Tout-voyant"), "de l'Omniscient"),
    (re.compile(r"\bTout-voyant\b"), "Omniscient"),
    (re.compile(r"\bThousand Fantasy Ruthless\b"), "Mille Illusions Impitoyables"),
]

ZHANG_RE = re.compile(
    r"(?:(?P<shu>数)|(?P<shang>上))?(?P<num>[\d零一二两三四五六七八九十百千万]+)?多?余?丈"
)
LI_RE = re.compile(
    r"(?:(?P<shu>数)|(?P<shang>上))?(?P<num>[\d零一二两三四五六七八九十百千万]+)?多?余?里"
)


def parse_cn_int(s: str) -> int | None:
    if not s:
        return None
    if s.isdigit():
        return int(s)
    n = 0
    i = 0
    chars = list(s)
    while i < len(chars):
        c = chars[i]
        if c == "万":
            n = (n or 1) * 10000
            i += 1
            continue
        if c == "千":
            prev = CN_DIGITS.get(chars[i - 1], None) if i else None
            if prev is None:
                n += 1000
            i += 1
            continue
        if c == "百":
            prev = CN_DIGITS.get(chars[i - 1], None) if i else None
            if prev is None:
                n += 100
            i += 1
            continue
        if c == "十":
            prev = CN_DIGITS.get(chars[i - 1], None) if i else None
            if prev is None or (i and chars[i - 1] in "万千百"):
                n += 10
            i += 1
            continue
        d = CN_DIGITS.get(c)
        if d is None:
            return None
        # lookahead unit
        if i + 1 < len(chars) and chars[i + 1] == "千":
            n += d * 1000
            i += 2
            continue
        if i + 1 < len(chars) and chars[i + 1] == "百":
            n += d * 100
            i += 2
            continue
        if i + 1 < len(chars) and chars[i + 1] == "十":
            n += d * 10
            i += 2
            continue
        if i + 1 < len(chars) and chars[i + 1] == "万":
            n += d * 10000
            i += 2
            continue
        n += d
        i += 1
    return n or None


def fr_num_word(n: int) -> list[str]:
    """French spellings likely used in the corpus for n."""
    table = {
        1: ["un", "une"],
        2: ["deux"],
        3: ["trois"],
        4: ["quatre"],
        5: ["cinq"],
        6: ["six"],
        7: ["sept"],
        8: ["huit"],
        9: ["neuf"],
        10: ["dix"],
        20: ["vingt"],
        30: ["trente"],
        40: ["quarante"],
        50: ["cinquante"],
        60: ["soixante"],
        100: ["cent", "cents"],
        1000: ["mille"],
    }
    out = table.get(n, [])
    out.append(str(n))
    out.append(f"{n:,}".replace(",", " "))
    out.append(f"{n:,}".replace(",", "\u00a0"))
    return out


def meters_from_zhang(n: int) -> str:
    m = int(round(n * 3.3))
    if m >= 1000:
        km = m / 1000
        if km == int(km):
            return f"{int(km)} kilomètres"
        return f"{km:.1f} kilomètres".replace(".", ",")
    return f"{m} mètres"


def km_from_li(n: int) -> str:
    km = n * 0.5
    if km == int(km):
        val = int(km)
        return f"{val} kilomètre" + ("s" if val != 1 else "")
    return f"{km:.1f} kilomètres".replace(".", ",")


def apply_lexical(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    for pat, repl in LEXICAL:
        text, n = pat.subn(repl, text)
        if n:
            notes.append(f"{pat.pattern} → {repl} ({n})")
    return text, notes


def find_fr_file(n: int) -> pathlib.Path | None:
    prefix = f"{n:04d}-"
    matches = list(FR_DIR.rglob(f"{prefix}*.md"))
    return matches[0] if matches else None


def find_zh_files(n: int) -> list[pathlib.Path]:
    prefix = f"{n:04d}_"
    return sorted(ZH_DIR.glob(f"{prefix}*.txt"))


def convert_units(zh: str, fr: str, chapter: int) -> tuple[str, list[str], list[str]]:
    applied: list[str] = []
    skipped: list[str] = []
    # Collect 丈 values
    zhang_vals: list[tuple[int | None, str]] = []
    for m in ZHANG_RE.finditer(zh):
        raw = m.group(0)
        if m.group("shu"):
            zhang_vals.append((None, "shu:" + raw))
            continue
        num = parse_cn_int(m.group("num") or "")
        if num:
            zhang_vals.append((num, raw))
        else:
            skipped.append(f"ch.{chapter} 丈 non parsé : {raw}")

    li_vals: list[tuple[int | None, str]] = []
    for m in LI_RE.finditer(zh):
        raw = m.group(0)
        if m.group("shu"):
            li_vals.append((None, "shu:" + raw))
            continue
        num = parse_cn_int(m.group("num") or "")
        if num:
            li_vals.append((num, raw))
        else:
            skipped.append(f"ch.{chapter} 里 non parsé : {raw}")

    # Unique numeric zhang
    seen_z: set[int] = set()
    for num, raw in zhang_vals:
        if num is None:
            # 数十丈 / 上百丈
            if raw.startswith("shu:数十") or "数十丈" in raw:
                new_fr, c = re.subn(
                    r"des dizaines de pieds",
                    "une centaine de mètres",
                    fr,
                    count=1,
                )
                if c:
                    fr = new_fr
                    applied.append(f"ch.{chapter} 数十丈 → une centaine de mètres")
                else:
                    skipped.append(f"ch.{chapter} 数十丈 sans « dizaines de pieds »")
            elif "上百丈" in raw or raw.endswith("百丈"):
                new_fr, c = re.subn(
                    r"(?:plus de |plus d['’])?cent pieds",
                    "plus de trois cents mètres",
                    fr,
                    count=1,
                )
                if c:
                    fr = new_fr
                    applied.append(f"ch.{chapter} 上百丈 → plus de trois cents mètres")
            continue
        if num in seen_z:
            continue
        seen_z.add(num)
        meters = meters_from_zhang(num)
        replaced = False
        for word in fr_num_word(num):
            # N pieds
            pat = re.compile(
                rf"\b{re.escape(word)}\s+pieds\b",
                re.IGNORECASE,
            )
            if pat.search(fr):
                fr, c = pat.subn(meters, fr, count=1)
                if c:
                    applied.append(f"ch.{chapter} {raw} / {word} pieds → {meters}")
                    replaced = True
                    break
        if not replaced:
            skipped.append(f"ch.{chapter} {raw} ({num}) : pas de « N pieds » correspondant")

    seen_l: set[int] = set()
    for num, raw in li_vals:
        if num is None:
            continue
        if num in seen_l:
            continue
        seen_l.add(num)
        km = km_from_li(num)
        replaced = False
        for word in fr_num_word(num):
            for unit in ("pieds", "kilomètres", "kilomètre", "km"):
                pat = re.compile(
                    rf"\b{re.escape(word)}\s+{unit}\b",
                    re.IGNORECASE,
                )
                if pat.search(fr):
                    # If already correct km (num*0.5), skip
                    if unit.startswith("kilo") or unit == "km":
                        # only rewrite if FR used 里 as km 1:1 (same number)
                        target_val = num * 0.5
                        if word.replace("\u00a0", " ").replace(" ", "").isdigit() or word.isdigit():
                            try:
                                shown = int(re.sub(r"\s", "", word))
                            except ValueError:
                                shown = None
                        else:
                            shown = FR_CARDINALS.get(word.lower())
                        if shown is not None and abs(shown - target_val) < 0.01:
                            skipped.append(f"ch.{chapter} {raw} déjà en km corrects")
                            replaced = True
                            break
                    fr, c = pat.subn(km, fr, count=1)
                    if c:
                        applied.append(f"ch.{chapter} {raw} / {word} {unit} → {km}")
                        replaced = True
                        break
            if replaced:
                break
        if not replaced:
            skipped.append(f"ch.{chapter} {raw} ({num}) : pas de distance FR correspondante")

    return fr, applied, skipped


def safe_write(path: pathlib.Path, text: str) -> None:
    import time

    for attempt in range(5):
        try:
            path.write_text(text, encoding="utf-8")
            return
        except OSError:
            time.sleep(0.15 * (attempt + 1))
    path.write_text(text, encoding="utf-8")


def main() -> None:
    aligned = json.loads(ALIGNED.read_text(encoding="utf-8"))
    aligned_ns = {int(item["n"]) for item in aligned}
    lexical_notes: dict[str, list[str]] = {}
    unit_applied: list[str] = []
    unit_skipped: list[str] = []
    changed_files = 0

    # Pass 1: lexical on every French chapter (not only the 700).
    for fr_path in FR_DIR.rglob("*.md"):
        original = fr_path.read_text(encoding="utf-8")
        text, notes = apply_lexical(original)
        if notes:
            lexical_notes[str(fr_path.relative_to(ROOT))] = notes
        if text != original:
            safe_write(fr_path, text)
            changed_files += 1

    # Pass 2: unit conversion on aligned pairs only.
    for n in sorted(aligned_ns):
        fr_path = find_fr_file(n)
        zh_paths = find_zh_files(n)
        if not fr_path or not zh_paths:
            continue
        original = fr_path.read_text(encoding="utf-8")
        zh = "\n".join(p.read_text(encoding="utf-8") for p in zh_paths)
        text, applied, skipped = convert_units(zh, original, n)
        unit_applied.extend(applied)
        unit_skipped.extend(skipped)
        if text != original:
            safe_write(fr_path, text)
            changed_files += 1

    lines = [
        "# Journal des corrections alignées ZH→FR",
        "",
        f"Fichiers FR modifiés : {changed_files}",
        f"Fichiers avec remplacements lexicaux : {len(lexical_notes)}",
        f"Conversions d'unités appliquées : {len(unit_applied)}",
        f"Conversions d'unités refusées : {len(unit_skipped)}",
        "",
        "## Lexical",
        "",
    ]
    for key in sorted(lexical_notes):
        lines.append(f"- {key}: " + "; ".join(lexical_notes[key]))
    lines += ["", "## Unités appliquées", ""]
    lines += [f"- {x}" for x in unit_applied[:400]]
    if len(unit_applied) > 400:
        lines.append(f"- … {len(unit_applied) - 400} de plus")
    lines += ["", "## Unités refusées (échantillon)", ""]
    # collapse similar
    sample = unit_skipped[:200]
    lines += [f"- {x}" for x in sample]
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"changed={changed_files} lexical={len(lexical_notes)} units={len(unit_applied)} skipped={len(unit_skipped)}")
    print(f"log={LOG_PATH}")


if __name__ == "__main__":
    main()
