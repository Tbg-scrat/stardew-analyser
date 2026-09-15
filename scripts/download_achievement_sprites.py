#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility script to fetch all 30 Stardew Valley achievement icons 
from the official wiki and save them locally to static/img/achievements/.
"""

import os
import re
import urllib.request

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "img", "achievements")
WIKI_URL = "https://stardewvalleywiki.com/Achievements"

def download_sprites():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"📁 Target directory: {os.path.abspath(OUTPUT_DIR)}")
    
    req = urllib.request.Request(WIKI_URL, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print(f"❌ Failed to fetch wiki page: {e}")
        return

    # Extract image URLs from wiki HTML
    # Matches images inside achievement table rows
    img_matches = re.findall(r'src="(/mediawiki/images/[^"]+/(Achievement_[^"]+\.png))"', html)

    # Deduplicate matches while preserving order
    unique_images = {}
    for rel_path, filename in img_matches:
        if filename not in unique_images:
            unique_images[filename] = rel_path

    downloaded_count = 0

    for filename, rel_path in unique_images.items():
        full_url = f"https://stardewvalleywiki.com{rel_path}"
        target_file_path = os.path.join(OUTPUT_DIR, filename)
        
        if os.path.exists(target_file_path):
            print(f"⏭️ Skipping {filename} (already exists)")
            continue

        try:
            print(f"⬇️ Downloading {filename}...")
            img_req = urllib.request.Request(full_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(img_req) as img_resp, open(target_file_path, "wb") as out_file:
                out_file.write(img_resp.read())
            downloaded_count += 1
        except Exception as e:
            print(f"❌ Error downloading {filename}: {e}")

    print(f"\n✅ Finished! Downloaded {downloaded_count} icons into {os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    download_sprites()
    