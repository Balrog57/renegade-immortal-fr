#!/usr/bin/env python3
"""
convert_to_webp.py — Convert all wiki/images/* from JPG/PNG to WebP.

Reduces site size by ~22 MB (561 images converted, ~66 MB JPG/PNG -> ~44 MB WebP).

Usage: python convert_to_webp.py
"""
import os
from pathlib import Path
from PIL import Image
import time

ROOT = Path(__file__).parent.parent
IMG_DIR = ROOT / 'wiki' / 'images'

if not IMG_DIR.exists():
    print(f'No {IMG_DIR}')
    exit(1)

files = [f for f in IMG_DIR.iterdir() if f.is_file()]
print(f'Files to convert: {len(files)}')

t0 = time.time()
converted = 0
skipped = 0
errors = 0
saved_bytes = 0

for i, f in enumerate(files):
    ext = f.suffix.lower()
    if ext in ('.webp', '.gif'):  # already webp or animated
        skipped += 1
        continue
    try:
        webp_path = f.with_suffix('.webp')
        if webp_path.exists() and webp_path.stat().st_size > 0:
            skipped += 1
            continue
        img = Image.open(f)
        if img.mode in ('RGBA', 'LA', 'P'):
            img.save(webp_path, 'WEBP', quality=85, method=6, lossless=False)
        else:
            img = img.convert('RGB')
            img.save(webp_path, 'WEBP', quality=85, method=6)
        saved_bytes += f.stat().st_size - webp_path.stat().st_size
        converted += 1
    except Exception as e:
        errors += 1
        print(f'  ERR {f.name}: {e}')

    if (i + 1) % 50 == 0:
        dt = time.time() - t0
        rate = (i+1) / dt
        remaining = (len(files) - i - 1) / max(rate, 0.1)
        print(f'  {i+1}/{len(files)}  converted={converted}  skipped={skipped}  errors={errors}  saved={saved_bytes/1024/1024:.1f}MB  ETA={remaining:.0f}s')

# Delete originals
deleted = 0
for f in IMG_DIR.iterdir():
    if f.suffix.lower() in ('.jpg', '.jpeg', '.png'):
        webp = f.with_suffix('.webp')
        if webp.exists():
            f.unlink()
            deleted += 1

print(f'\n=== DONE in {time.time()-t0:.1f}s ===')
print(f'  Converted: {converted}')
print(f'  Skipped  : {skipped}')
print(f'  Errors   : {errors}')
print(f'  Originals deleted: {deleted}')
print(f'  Saved: {saved_bytes/1024/1024:.1f} MB')
print(f'  Final size: {sum(f.stat().st_size for f in IMG_DIR.iterdir())/1024/1024:.1f} MB')
