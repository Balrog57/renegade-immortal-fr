#!/usr/bin/env python3
"""
Générateur professionnel d'EPUB 3 / EPUB 2 pour Renegade Immortal (Xian Ni).
Génère l'intégrale complète (2 088 chapitres) ainsi que les tomes individuels (1 à 13).
"""

from __future__ import annotations

import argparse
import html
import io
import os
import pathlib
import re
import sys
import uuid
import zipfile
from datetime import datetime
from PIL import Image

BOOK_TITLES_FR = {
    1: "Le Jeune Homme Ordinaire",
    2: "L'Image Sanglante de la Cultivation",
    3: "Célèbre dans la Mer des Démons",
    4: "Balayage Net",
    5: "Transformation de l'Âme",
    6: "Arrivée sur Tian Yun",
    7: "La Renommée Ébranle le Système Stellaire Allheaven",
    8: "Le Secret de l'Alliance",
    9: "Le Sommet de la Mer de Nuages",
    10: "Déchaînement à travers le Royaume Intérieur",
    11: "Mystères de l'Ère Ancienne",
    12: "Le Dixième Soleil du Continent Astral Immortel",
    13: "La Lumière de la Fin Imminente",
}

CSS_STYLE = """\
@charset "utf-8";

body {
    margin: 5% 5% 5% 5%;
    padding: 0;
    font-family: serif;
    line-height: 1.65;
    text-align: justify;
    text-justify: inter-word;
    color: #1a1a1a;
}

h1.book-title {
    font-family: sans-serif;
    font-size: 2.2em;
    font-weight: bold;
    text-align: center;
    margin-top: 15%;
    margin-bottom: 0.3em;
    color: #7b1113;
    page-break-before: always;
}

h2.book-subtitle {
    font-family: sans-serif;
    font-size: 1.3em;
    font-weight: normal;
    text-align: center;
    color: #555;
    margin-bottom: 2em;
}

.tome-cover-img {
    display: block;
    max-width: 80%;
    max-height: 60vh;
    margin: 2em auto;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    border-radius: 4px;
}

h2.chap-title {
    font-family: sans-serif;
    font-size: 1.5em;
    font-weight: bold;
    text-align: center;
    margin-top: 1.5em;
    margin-bottom: 0.3em;
    color: #111;
    page-break-before: always;
}

p.chap-subtitle {
    font-family: sans-serif;
    font-size: 0.9em;
    text-align: center;
    color: #777;
    margin-bottom: 2em;
    font-style: italic;
}

p {
    margin: 0;
    text-indent: 1.5em;
    padding-bottom: 0.5em;
}

p.no-indent {
    text-indent: 0;
}

.ornament {
    text-align: center;
    margin: 1.5em 0;
    color: #7b1113;
    font-size: 1.2em;
}

/* Page de titre */
.titlepage {
    text-align: center;
    margin-top: 20%;
    page-break-before: always;
}

.titlepage h1 {
    font-size: 2.6em;
    margin-bottom: 0.2em;
    color: #7b1113;
}

.titlepage h2 {
    font-size: 1.4em;
    font-weight: normal;
    color: #444;
    margin-bottom: 2em;
}

.titlepage .author {
    font-size: 1.3em;
    font-weight: bold;
    margin-top: 3em;
}

.titlepage .meta {
    font-size: 0.95em;
    color: #666;
    margin-top: 1.5em;
}

/* Page Couverture */
.cover-wrapper {
    text-align: center;
    height: 100vh;
    margin: 0;
    padding: 0;
}

.cover-img {
    max-width: 100%;
    max-height: 100%;
    height: auto;
    width: auto;
}

/* Navigation Table of Contents */
nav#toc ol {
    list-style-type: none;
    padding-left: 1.2em;
}

nav#toc li {
    margin: 0.4em 0;
}

nav#toc a {
    text-decoration: none;
    color: inherit;
}
"""

def parse_frontmatter(content: str) -> tuple[dict, str]:
    fm = {}
    body = content
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if m:
        fm_text = m.group(1)
        body = m.group(2)
        for line in fm_text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k in ("n", "book"):
                    try:
                        v = int(v)
                    except ValueError:
                        pass
                fm[k] = v
    return fm, body.strip()

def text_to_xhtml_paragraphs(text: str) -> str:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    html_parts = []
    for p in paragraphs:
        # Échappement HTML sécurisé
        escaped = html.escape(p)
        # Formatage de dialogues ou citations en italique markdown si présents
        escaped = re.sub(r"\*(.*?)\*", r"<em>\1</em>", escaped)
        html_parts.append(f"<p>{escaped}</p>")
    return "\n".join(html_parts)

def convert_webp_to_jpeg_bytes(webp_path: pathlib.Path, max_dim: int = 1600) -> bytes:
    im = Image.open(webp_path)
    if im.mode in ("RGBA", "P"):
        im = im.convert("RGB")
    im.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=90, optimize=True)
    return buf.getvalue()

class EpubBuilder:
    def __init__(self, book_id: str, title: str, author: str = "Er Gen (耳根)", lang: str = "fr"):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.lang = lang
        self.manifest_items = []  # list of (id, href, media_type, properties)
        self.spine_items = []     # list of id
        self.toc_entries = []     # hierarchical list of dicts {title, href, children: []}
        self.files = {}           # path_in_epub -> bytes

    def add_file(self, path: str, data: bytes, media_type: str, item_id: str | None = None, is_linear: bool = True, properties: str = ""):
        self.files[path] = data
        if item_id:
            self.manifest_items.append((item_id, path.replace("OEBPS/", ""), media_type, properties))
            if is_linear:
                self.spine_items.append(item_id)

    def set_cover(self, jpeg_bytes: bytes):
        self.add_file("OEBPS/images/cover.jpg", jpeg_bytes, "image/jpeg", "cover-image", is_linear=False, properties="cover-image")
        cover_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{self.lang}">
<head>
    <title>Couverture</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body class="cover-wrapper">
    <img class="cover-img" src="images/cover.jpg" alt="Couverture de {html.escape(self.title)}"/>
</body>
</html>"""
        self.add_file("OEBPS/cover.xhtml", cover_xhtml.encode("utf-8"), "application/xhtml+xml", "cover-page", is_linear=True)

    def build_epub(self, output_path: pathlib.Path):
        # 1. Add CSS
        self.add_file("OEBPS/style.css", CSS_STYLE.encode("utf-8"), "text/css", "style-css", is_linear=False)

        # 2. Add EPUB 3 Navigation (nav.xhtml)
        def render_nav_ol(entries):
            out = ["<ol>"]
            for e in entries:
                out.append(f'<li><a href="{e["href"]}">{html.escape(e["title"])}</a>')
                if e.get("children"):
                    out.append(render_nav_ol(e["children"]))
                out.append("</li>")
            out.append("</ol>")
            return "\n".join(out)

        nav_content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{self.lang}">
<head>
    <title>Table des Matières</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1>Table des Matières</h1>
        {render_nav_ol(self.toc_entries)}
    </nav>
</body>
</html>"""
        self.add_file("OEBPS/nav.xhtml", nav_content.encode("utf-8"), "application/xhtml+xml", "nav-doc", is_linear=False, properties="nav")

        # 3. Add EPUB 2 NCX (toc.ncx)
        ncx_playorder = 1
        def render_ncx_navpoints(entries):
            nonlocal ncx_playorder
            out = []
            for e in entries:
                p_id = f"navpoint-{ncx_playorder}"
                out.append(f'<navPoint id="{p_id}" playOrder="{ncx_playorder}">')
                out.append(f'<navLabel><text>{html.escape(e["title"])}</text></navLabel>')
                out.append(f'<content src="{e["href"]}"/>')
                ncx_playorder += 1
                if e.get("children"):
                    out.append(render_ncx_navpoints(e["children"]))
                out.append('</navPoint>')
            return "\n".join(out)

        ncx_content = f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="{self.lang}">
<head>
    <meta name="dtb:uid" content="{self.book_id}"/>
    <meta name="dtb:depth" content="2"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
</head>
<docTitle><text>{html.escape(self.title)}</text></docTitle>
<docAuthor><text>{html.escape(self.author)}</text></docAuthor>
<navMap>
    {render_ncx_navpoints(self.toc_entries)}
</navMap>
</ncx>"""
        self.add_file("OEBPS/toc.ncx", ncx_content.encode("utf-8"), "application/x-dtbncx+xml", "ncx", is_linear=False)

        # 4. Add content.opf
        now_utc = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        manifest_xml = "\n".join(
            f'    <item id="{item_id}" href="{href}" media-type="{media_type}"'
            + (f' properties="{props}"' if props else '') + '/>'
            for item_id, href, media_type, props in self.manifest_items
        )
        spine_xml = "\n".join(
            f'    <itemref idref="{item_id}"/>'
            for item_id in self.spine_items
        )

        opf_content = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id" xml:lang="{self.lang}">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">{self.book_id}</dc:identifier>
    <dc:title>{html.escape(self.title)}</dc:title>
    <dc:creator>{html.escape(self.author)}</dc:creator>
    <dc:language>{self.lang}</dc:language>
    <dc:publisher>Renegade Immortal FR Community</dc:publisher>
    <meta property="dcterms:modified">{now_utc}</meta>
</metadata>
<manifest>
{manifest_xml}
</manifest>
<spine toc="ncx">
{spine_xml}
</spine>
</package>"""
        self.files["OEBPS/content.opf"] = opf_content.encode("utf-8")

        # 5. Add META-INF/container.xml
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>"""
        self.files["META-INF/container.xml"] = container_xml.encode("utf-8")

        # 6. Write ZIP
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            # First file must be mimetype and uncompressed
            z.writestr("mimetype", b"application/epub+zip", compress_type=zipfile.ZIP_STORED)
            for path, data in self.files.items():
                z.writestr(path, data)

        print(f"  [OK] EPUB généré avec succès : {output_path} ({output_path.stat().st_size / (1024*1024):.2f} Mo)")


def load_all_chapters(chapters_dir: pathlib.Path) -> list[dict]:
    all_files = list(chapters_dir.rglob("*.md"))
    chapters = []
    for f in all_files:
        raw = f.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_frontmatter(raw)
        n = fm.get("n")
        if n is None:
            continue
        book = fm.get("book", 1)
        title = fm.get("title", f"Chapitre {n}")
        en = fm.get("en", "")
        book_title = fm.get("bookTitle", f"Tome {book}")
        chapters.append({
            "n": int(n),
            "book": int(book),
            "title": title,
            "en": en,
            "bookTitle": book_title,
            "body": body,
            "path": f,
        })
    chapters.sort(key=lambda c: c["n"])
    return chapters


def generate_omnibus_epub(chapters: list[dict], images_dir: pathlib.Path, out_file: pathlib.Path):
    print(f"\n--- Génération de l'Intégrale EPUB ({len(chapters)} chapitres) ---")
    builder = EpubBuilder(
        book_id=f"urn:uuid:{uuid.uuid4()}",
        title="Renegade Immortal (仙逆) - Intégrale",
        author="Er Gen (耳根)",
        lang="fr",
    )

    # 1. Main Cover
    cover_img_path = images_dir / "Wang_Lin_Fandom.webp"
    if not cover_img_path.exists():
        cover_img_path = images_dir / "Raws-1.webp"
    if cover_img_path.exists():
        builder.set_cover(convert_webp_to_jpeg_bytes(cover_img_path))

    # 2. Title page
    title_html = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr">
<head>
    <title>Titre</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body class="titlepage">
    <h1>Renegade Immortal</h1>
    <h2>仙逆 (Xian Ni)</h2>
    <div class="ornament">❖ ❖ ❖</div>
    <div class="author">Auteur : Er Gen (耳根)</div>
    <div class="meta">
        <p class="no-indent"><strong>Traduction :</strong> Intégrale Française Validée MQM</p>
        <p class="no-indent"><strong>Nombre de Tomes :</strong> 13</p>
        <p class="no-indent"><strong>Nombre de Chapitres :</strong> {len(chapters)}</p>
        <p class="no-indent"><strong>Édition :</strong> 2026</p>
    </div>
</body>
</html>"""
    builder.add_file("OEBPS/titlepage.xhtml", title_html.encode("utf-8"), "application/xhtml+xml", "titlepage")

    # Group chapters by book
    by_book = {}
    for c in chapters:
        by_book.setdefault(c["book"], []).append(c)

    for b_num in sorted(by_book.keys()):
        b_chaps = by_book[b_num]
        b_title_fr = BOOK_TITLES_FR.get(b_num, f"Tome {b_num}")
        b_title_en = b_chaps[0].get("bookTitle", "")

        # Tome Cover Image if available
        tome_img_id = None
        tome_img_name = f"Book {b_num}.webp"
        tome_img_path = images_dir / tome_img_name
        if tome_img_path.exists():
            tome_img_id = f"img-tome-{b_num}"
            jpeg_data = convert_webp_to_jpeg_bytes(tome_img_path)
            builder.add_file(f"OEBPS/images/tome_{b_num}.jpg", jpeg_data, "image/jpeg", tome_img_id, is_linear=False)

        # Tome Intertitle Page
        tome_html_parts = [
            f'<h1 class="book-title">Tome {b_num}</h1>',
            f'<h2 class="book-subtitle">{html.escape(b_title_fr)}<br/><small style="font-size:0.7em; color:#888;">({html.escape(b_title_en)})</small></h2>',
        ]
        if tome_img_id:
            tome_html_parts.append(f'<img class="tome-cover-img" src="images/tome_{b_num}.jpg" alt="Tome {b_num}"/>')
        tome_html_parts.append(f'<p class="no-indent" style="text-align:center; color:#666; margin-top:2em;">Chapitres {b_chaps[0]["n"]} à {b_chaps[-1]["n"]}</p>')

        tome_page_html = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr">
<head>
    <title>Tome {b_num}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    {"".join(tome_html_parts)}
</body>
</html>"""
        tome_href = f"tome_{b_num}.xhtml"
        builder.add_file(f"OEBPS/{tome_href}", tome_page_html.encode("utf-8"), "application/xhtml+xml", f"tome-{b_num}")

        tome_toc_entry = {
            "title": f"Tome {b_num} : {b_title_fr} ({b_chaps[0]['n']}-{b_chaps[-1]['n']})",
            "href": tome_href,
            "children": [],
        }

        # Chapters
        for c in b_chaps:
            c_num = c["n"]
            c_title = c["title"]
            c_en = c.get("en", "")
            c_href = f"chap_{c_num:04d}.xhtml"

            body_html = text_to_xhtml_paragraphs(c["body"])

            chap_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr">
<head>
    <title>Chapitre {c_num} - {html.escape(c_title)}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <h2 class="chap-title">Chapitre {c_num} : {html.escape(c_title)}</h2>
    {f'<p class="chap-subtitle">{html.escape(c_en)}</p>' if c_en else ''}
    <div class="chapter-content">
        {body_html}
    </div>
</body>
</html>"""
            builder.add_file(f"OEBPS/{c_href}", chap_xhtml.encode("utf-8"), "application/xhtml+xml", f"chap-{c_num:04d}")
            tome_toc_entry["children"].append({
                "title": f"Ch. {c_num} : {c_title}",
                "href": c_href,
            })

        builder.toc_entries.append(tome_toc_entry)

    builder.build_epub(out_file)


def generate_single_tome_epub(tome_num: int, b_chaps: list[dict], images_dir: pathlib.Path, out_file: pathlib.Path):
    b_title_fr = BOOK_TITLES_FR.get(tome_num, f"Tome {tome_num}")
    b_title_en = b_chaps[0].get("bookTitle", "")

    builder = EpubBuilder(
        book_id=f"urn:uuid:{uuid.uuid4()}",
        title=f"Renegade Immortal - Tome {tome_num:02d} : {b_title_fr}",
        author="Er Gen (耳根)",
        lang="fr",
    )

    # Cover
    tome_img_name = f"Book {tome_num}.webp"
    tome_img_path = images_dir / tome_img_name
    if not tome_img_path.exists():
        tome_img_path = images_dir / "Wang_Lin_Fandom.webp"
    if tome_img_path.exists():
        builder.set_cover(convert_webp_to_jpeg_bytes(tome_img_path))

    # Title Page
    title_html = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr">
<head>
    <title>Titre</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body class="titlepage">
    <h1>Renegade Immortal</h1>
    <h2>Tome {tome_num} — {html.escape(b_title_fr)}</h2>
    <div class="ornament">❖ ❖ ❖</div>
    <div class="author">Auteur : Er Gen (耳根)</div>
    <div class="meta">
        <p class="no-indent"><strong>Titre original :</strong> 仙逆 (Xian Ni)</p>
        <p class="no-indent"><strong>Tome original :</strong> {html.escape(b_title_en)}</p>
        <p class="no-indent"><strong>Chapitres :</strong> {b_chaps[0]["n"]} à {b_chaps[-1]["n"]} ({len(b_chaps)} chapitres)</p>
    </div>
</body>
</html>"""
    builder.add_file("OEBPS/titlepage.xhtml", title_html.encode("utf-8"), "application/xhtml+xml", "titlepage")

    # Chapters
    for c in b_chaps:
        c_num = c["n"]
        c_title = c["title"]
        c_en = c.get("en", "")
        c_href = f"chap_{c_num:04d}.xhtml"

        body_html = text_to_xhtml_paragraphs(c["body"])

        chap_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr">
<head>
    <title>Chapitre {c_num} - {html.escape(c_title)}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <h2 class="chap-title">Chapitre {c_num} : {html.escape(c_title)}</h2>
    {f'<p class="chap-subtitle">{html.escape(c_en)}</p>' if c_en else ''}
    <div class="chapter-content">
        {body_html}
    </div>
</body>
</html>"""
        builder.add_file(f"OEBPS/{c_href}", chap_xhtml.encode("utf-8"), "application/xhtml+xml", f"chap-{c_num:04d}")
        builder.toc_entries.append({
            "title": f"Ch. {c_num} : {c_title}",
            "href": c_href,
        })

    builder.build_epub(out_file)


def main():
    parser = argparse.ArgumentParser(description="Générateur d'ePub haute qualité pour Renegade Immortal")
    parser.add_argument("--chapters", type=pathlib.Path, default=pathlib.Path("src/content/chapters"), help="Dossier des chapitres Markdown")
    parser.add_argument("--images", type=pathlib.Path, default=pathlib.Path("public/wiki/images"), help="Dossier des images")
    parser.add_argument("--outdir", type=pathlib.Path, default=pathlib.Path("dist_epub"), help="Dossier de sortie des EPUBs")
    parser.add_argument("--by-book", action="store_true", help="Générer également les 13 tomes individuels")
    args = parser.parse_args()

    print("Chargement des chapitres...")
    chapters = load_all_chapters(args.chapters)
    print(f"Total chargé : {len(chapters)} chapitres.")

    if not chapters:
        print("Erreur : aucun chapitre trouvé.")
        sys.exit(1)

    args.outdir.mkdir(parents=True, exist_ok=True)

    # 1. Génération de l'Intégrale
    omnibus_path = args.outdir / "Renegade_Immortal_Integral_FR.epub"
    generate_omnibus_epub(chapters, args.images, omnibus_path)

    # 2. Génération par tomes si demandé
    if args.by_book:
        print("\n--- Génération des 13 tomes individuels ---")
        by_book = {}
        for c in chapters:
            by_book.setdefault(c["book"], []).append(c)

        for b_num in sorted(by_book.keys()):
            tome_file = args.outdir / f"Renegade_Immortal_Tome_{b_num:02d}.epub"
            generate_single_tome_epub(b_num, by_book[b_num], args.images, tome_file)

    print("\n[OK] Toutes les operations de generation EPUB sont terminees !")

if __name__ == "__main__":
    main()
