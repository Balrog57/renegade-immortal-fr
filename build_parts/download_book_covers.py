#!/usr/bin/env python3
"""
download_book_covers.py — Download 13 Book N.jpg from Fandom + convert to WebP.

Usage: python download_book_covers.py
"""
import urllib.request, urllib.parse, json, os
from pathlib import Path
from PIL import Image
from io import BytesIO

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

ROOT = Path(__file__).parent.parent
IMG_DIR = ROOT / 'wiki' / 'images'
IMG_DIR.mkdir(parents=True, exist_ok=True)

api = 'https://xian-ni.fandom.com/api.php'
downloaded = 0
for book_n in range(1, 14):
    target = IMG_DIR / f'Book {book_n}.webp'
    if target.exists() and target.stat().st_size > 0:
        print(f'  Book {book_n}: already exists')
        continue
    # Try multiple filename variants
    for fname in [f'Book {book_n}.jpg', f'Book {book_n}.jpeg', f'Book {book_n}.png']:
        params = {
            'action': 'query', 'titles': f'File:{fname}',
            'prop': 'imageinfo', 'iiprop': 'url', 'format': 'json',
        }
        url = api + '?' + urllib.parse.urlencode(params)
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode('utf-8'))
            for p in data.get('query', {}).get('pages', {}).values():
                infos = p.get('imageinfo', [])
                if infos:
                    img_url = infos[0]['url']
                    print(f'  Book {book_n}: downloading {img_url[:80]}...')
                    req2 = urllib.request.Request(img_url, headers={'User-Agent': UA})
                    with urllib.request.urlopen(req2, timeout=30) as r2:
                        img = Image.open(BytesIO(r2.read()))
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img.save(target, 'WEBP', quality=85, method=6)
                        else:
                            img = img.convert('RGB')
                            img.save(target, 'WEBP', quality=85, method=6)
                    print(f'    ✓ {target.stat().st_size:,} B')
                    downloaded += 1
                    break
            else:
                continue
            break
        except Exception as e:
            print(f'  Book {book_n} {fname}: ERR {e}')

# Generate placeholders for missing (Book 12, 13)
for book_n in [12, 13]:
    target = IMG_DIR / f'Book {book_n}.webp'
    if target.exists() and target.stat().st_size > 0:
        continue
    print(f'  Book {book_n}: generating placeholder')
    W, H = 540, 720
    img = Image.new('RGB', (W, H), color=(7, 6, 10))
    draw = __import__('PIL.ImageDraw', fromlist=['ImageDraw']).ImageDraw.Draw(img)
    # Gradient bg
    for y in range(H):
        t = y / H
        r = int(40 * (1 - t) + 7 * t)
        g = int(15 * (1 - t) + 6 * t)
        b = int(35 * (1 - t) + 10 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    draw.rectangle([(20, 20), (W-20, 30)], fill=(200, 164, 74))
    draw.rectangle([(20, H-30), (W-20, H-20)], fill=(200, 164, 74))
    font = None
    for fp in [r'C:\Windows\Fonts\Cinzel-Bold.ttf', r'C:\Windows\Fonts\segoeuib.ttf']:
        if os.path.exists(fp):
            font = __import__('PIL.ImageFont', fromlist=['ImageFont']).ImageFont.truetype(fp, 56)
            break
    if font:
        sub = __import__('PIL.ImageFont', fromlist=['ImageFont']).ImageFont.truetype(r'C:\Windows\Fonts\segoeuib.ttf' if os.path.exists(r'C:\Windows\Fonts\segoeuib.ttf') else fp, 24)
        sub_text = f'Tome {book_n}'
        bbox = draw.textbbox((0, 0), sub_text, font=sub)
        sw = bbox[2] - bbox[0]
        draw.text(((W - sw) / 2, H/2 - 60), sub_text, fill=(200, 164, 74), font=sub)
        num = f'{book_n}'
        bbox = draw.textbbox((0, 0), num, font=font)
        nw = bbox[2] - bbox[0]
        nh = bbox[3] - bbox[1]
        draw.text(((W - nw) / 2, H/2 - nh/2), num, fill=(243, 231, 200), font=font)
        ri_text = 'Renegade Immortal'
        bbox = draw.textbbox((0, 0), ri_text, font=sub)
        rw = bbox[2] - bbox[0]
        draw.text(((W - rw) / 2, H - 80), ri_text, fill=(184, 184, 184), font=sub)
    else:
        draw.text((W/2 - 50, H/2 - 30), f'Tome {book_n}', fill=(200, 164, 74))
    img.save(target, 'WEBP', quality=90, method=6)
    print(f'    ✓ {target.stat().st_size:,} B')

print(f'\nDone. {downloaded} covers downloaded.')
