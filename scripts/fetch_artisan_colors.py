# scripts/fetch_artisan_colors.py
import os
import re
import json
import urllib.request
from pathlib import Path

OUTPUT_DIR = Path("static/img/items")
DATA_DIR = Path("data")
JSON_OUTPUT = DATA_DIR / "artisan_colors.json"

URL = "https://stardewvalleywiki.com/Fruits"
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}


def fetch_and_extract():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Fetching fruit data from {URL}...")
    req = urllib.request.Request(URL, headers=HEADERS)

    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print(f"[ERROR] Failed to fetch wiki page: {e}")
        return

    # Expanded match pattern to capture header rows (like Ancient Fruit) and standard rows
    row_matches = re.findall(
        r'<a[^>]*title="([^"]+)"[^>]*>.*?<img[^>]*src="([^"]*Wine[^"]*\.png)"',
        html,
        re.DOTALL | re.IGNORECASE
    )

    artisan_map = {}
    downloaded_files = set()

    print(f"[INFO] Discovered {len(row_matches)} candidate(s). Processing...")

    for fruit_name, img_path in row_matches:
        fruit_clean = fruit_name.strip().lower()

        # Filter out non-fruit wiki link titles
        if fruit_clean in ["skills", "fruit", "fruits", "farming", "artisan goods", "keg"]:
            continue

        filename_match = re.search(r'([A-Za-z_]+Wine\.png)', img_path)
        if not filename_match:
            continue

        filename = filename_match.group(1)
        target_path = OUTPUT_DIR / filename

        # Map fruit wine string to the color sprite filename
        artisan_map[f"{fruit_clean} wine"] = filename

        if filename not in downloaded_files:
            downloaded_files.add(filename)

            if img_path.startswith("//"):
                img_url = "https:" + img_path
            elif img_path.startswith("/"):
                img_url = "https://stardewvalleywiki.com" + img_path
            else:
                img_url = img_path

            # Remove thumbnail size prefix to download full resolution
            img_url = re.sub(r'/thumb(/.*)/[^/]+$', r'\1', img_url)

            print(f"  --> Downloading sprite: {filename}")
            try:
                img_req = urllib.request.Request(img_url, headers=HEADERS)
                with urllib.request.urlopen(img_req) as img_resp, open(target_path, 'wb') as out_file:
                    out_file.write(img_resp.read())
            except Exception as err:
                print(f"      [WARN] Failed to download {img_url}: {err}")

    # Explicit fallback for Ancient Fruit if wiki layout varies
    if "ancient fruit wine" not in artisan_map:
        artisan_map["ancient fruit wine"] = "Light_Blue_Wine.png"

    # Fallback mapping for generic wine
    artisan_map["wine"] = "Wine.png"

    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(artisan_map, f, indent=2)

    print("\n" + "=" * 60)
    print(f"[OK] Downloaded {len(downloaded_files)} unique wine sprite(s) to '{OUTPUT_DIR.resolve()}'")
    print(f"[OK] Generated color mapping JSON: '{JSON_OUTPUT.resolve()}'")
    print("=" * 60)


if __name__ == "__main__":
    fetch_and_extract()
    