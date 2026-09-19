#!/usr/bin/env python3
# scripts/download_category3_sprites.py

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR = Path("static/img/items")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}

# Explicit mapping: (Sprite Key -> Wiki File Title)
CATEGORY_3_MAPPINGS = {
    # Special Quest / Unique Items
    "O_71": "Trimmed_Lucky_Purple_Shorts",
    "O_742": "Haley%27s_Lost_Bracelet",
    "O_788": "Lost_Axe",
    "O_789": "Lucky_Purple_Shorts",
    "O_790": "Berry_Basket",
    "O_870": "Pirate%27s_Locket",
    "O_897": "Pierre%27s_Missing_Stocklist",
    
    # 1.6 Artisan & Processed Goods
    "O_DriedFruit": "Dried_Fruit",
    "O_DriedMushrooms": "Dried_Mushrooms",
    "O_SmokedFish": "Smoked_Fish",
    "O_GoldCoin": "Gold_Coin",
    
    # 1.6 Skill Books & Literature
    "O_SkillBook_2": "Woodcutter%27s_Weekly",
    "O_Book_Crabbing": "The_Art_O%27_Crabbing",
    "O_Book_WildSeeds": "Raccoon_Journal",
    "O_Book_Woodcutting": "Woody%27s_Secret",
    "O_Book_Horse": "Horse_The_Book",
    "O_Book_Grass": "Ol%27_Slitherlegs",
    "O_PetLicense": "Pet_License",
    
    # Special Totems & Utility
    "O_261": "Warp_Totem_Desert",
    "O_688": "Warp_Totem_Farm",
    "O_689": "Warp_Totem_Mountains",
    "O_690": "Warp_Totem_Beach",
    "O_886": "Warp_Totem_Island",
}

def get_direct_wiki_url(wiki_title):
    """Query MediaWiki API for the direct image file URL."""
    api_url = "https://stardewvalleywiki.com/mediawiki/api.php?" + urllib.parse.urlencode({
        "action": "query",
        "titles": f"File:{wiki_title}.png",
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json",
    })
    
    req = urllib.request.Request(api_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})
                for _, page in pages.items():
                    imageinfo = page.get("imageinfo", [])
                    if imageinfo:
                        return imageinfo[0].get("url")
    except Exception as e:
        print(f"  └─ [API ERROR] {e}")
    return None

def download_image(url, save_path):
    """Download image to disk."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            if response.status == 200:
                with open(save_path, "wb") as f:
                    f.write(response.read())
                return True
    except Exception:
        pass
    return False

def main():
    print(f"[INFO] Processing {len(CATEGORY_3_MAPPINGS)} Category 3 items...")
    downloaded = 0
    skipped = 0
    failed = 0

    for sprite_key, wiki_title in CATEGORY_3_MAPPINGS.items():
        save_path = OUTPUT_DIR / f"{sprite_key}.png"
        
        if save_path.exists():
            skipped += 1
            continue

        print(f"Fetching {sprite_key}.png ({wiki_title})...")
        direct_url = get_direct_wiki_url(wiki_title)
        
        if direct_url and download_image(direct_url, save_path):
            print(f"  └─ [OK] Saved -> {save_path.name}")
            downloaded += 1
            time.sleep(1.0) # 1s delay
        else:
            print(f"  └─ [WARN] Failed to fetch {wiki_title}")
            failed += 1

    print(f"\n[SUCCESS] Summary: Downloaded {downloaded}, Skipped {skipped}, Failed {failed}")

if __name__ == "__main__":
    main()
