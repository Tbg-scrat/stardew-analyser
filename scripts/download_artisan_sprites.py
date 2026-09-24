#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Target directory for items
OUTPUT_DIR = Path("static/img/items")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Color variants matching Stardew Valley artisan color palettes
COLORS = [
    "Blue",
    "Brown",
    "Dark_Blue",
    "Dark_Pink",
    "Dark_Purple",
    "Green",
    "Light_Blue",
    "Orange",
    "Pink",
    "Purple",
    "Red",
    "White",
    "Yellow",
]

# Generate list of target filenames
TARGET_FILES = []

# 1. Colored Jellies & Dried Fruit
for color in COLORS:
    TARGET_FILES.append(f"{color}_Jelly.png")
    TARGET_FILES.append(f"{color}_Dried_Fruit.png")

# 2. Generic & Standard Artisan Items
TARGET_FILES.extend([
    "Jelly.png",
    "Dried_Fruit.png",
    "Dried_Mushrooms.png",
    "Raisins.png",
    "Pickles.png",
    "Juice.png",
    "Honey.png",
    "Beer.png",
    "Pale_Ale.png",
    "Mead.png",
    "Aged_Roe.png",
    "Caviar.png",
    "Cheese.png",
    "Goat_Cheese.png",
])

# Remove duplicates while preserving order
TARGET_FILES = sorted(list(set(TARGET_FILES)))

# Correct MediaWiki API endpoint
API_URL = "https://stardewvalleywiki.com/mediawiki/api.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def fetch_image_urls(filenames):
    """
    Batch queries the MediaWiki API for up to 50 file titles at once to resolve direct image URLs.
    """
    titles = [f"File:{filename}" for filename in filenames]
    titles_param = "|".join(titles)

    params = {
        "action": "query",
        "titles": titles_param,
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json",
    }

    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=HEADERS)

    url_mapping = {}
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})

            for _, page_info in pages.items():
                # Title returned is e.g. "File:Light Blue Jelly.png" or "File:Light_Blue_Jelly.png"
                raw_title = page_info.get("title", "").replace("File:", "").strip()
                normalized_title = raw_title.replace(" ", "_")

                imageinfo = page_info.get("imageinfo")
                if imageinfo and len(imageinfo) > 0:
                    img_url = imageinfo[0].get("url")
                    url_mapping[normalized_title] = img_url
                    url_mapping[raw_title] = img_url
    except Exception as e:
        print(f"[ERROR] Failed API request: {e}")

    return url_mapping


def download_file(url, target_path):
    """
    Downloads a single image file from a URL to target_path.
    """
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as resp, open(target_path, "wb") as f:
            f.write(resp.read())
        return True
    except Exception as e:
        print(f"[ERROR] Failed downloading {url}: {e}")
        return False


def main():
    print(f"[INFO] Checking {len(TARGET_FILES)} artisan sprite candidates...")

    # Filter out files that already exist locally
    to_download = [f for f in TARGET_FILES if not (OUTPUT_DIR / f).exists()]

    if not to_download:
        print(f"[INFO] All {len(TARGET_FILES)} artisan sprites are already downloaded in {OUTPUT_DIR.resolve()}")
        return

    print(f"[INFO] Need to download {len(to_download)} missing sprite(s). Querying Wiki API...")

    # Query API in chunks of 50
    CHUNK_SIZE = 50
    url_map = {}

    for i in range(0, len(to_download), CHUNK_SIZE):
        chunk = to_download[i : i + CHUNK_SIZE]
        fetched = fetch_image_urls(chunk)
        url_map.update(fetched)
        time.sleep(0.5)

    downloaded_count = 0
    for filename in to_download:
        img_url = url_map.get(filename) or url_map.get(filename.replace("_", " "))
        if not img_url:
            print(f"[WARN] No URL found on Wiki for: {filename}")
            continue

        target_file = OUTPUT_DIR / filename
        print(f"[DOWNLOADING] {filename} -> {target_file}")

        if download_file(img_url, target_file):
            downloaded_count += 1
            time.sleep(0.2)

    print(f"[SUCCESS] Downloaded {downloaded_count} new artisan sprites to {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
    