#!/usr/bin/env python3
# scripts/download_missing_chest_sprites.py

import json
import urllib.parse
import urllib.request
from pathlib import Path

OUTPUT_DIR = Path("static/img/items")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}

# Explicit mapping: (Sprite Key -> Wiki File Title)
MISSING_CHEST_ITEMS = {
    # Artisan Machines & Furniture (Big Craftables)
    "BC_10": "Mayonnaise_Machine",
    "BC_12": "Seed_Maker",
    "BC_15": "Preserves_Jar",
    "BC_16": "Cheese_Press",
    "BC_17": "Loom",
    "BC_19": "Oil_Maker",
    "BC_20": "Recycling_Machine",
    "BC_24": "Cask",
    "BC_101": "Incubator",
    "BC_108": "Slime_Egg-Press",
    "BC_158": "Deconstructor",
    "BC_231": "Solar_Panel",
    "BC_254": "Heavy_Tapper",
    # Specific Crops / Forage / 1.6 Items
    "O_251": "Tea_Leaves",
    "O_815": "Roe",
    "O_447": "Aged_Roe",
    "O_812": "Squid_Ink",
    "O_340": "Honey",
    "O_342": "Pickles",
    "O_344": "Jelly",
    "O_348": "Wine",
    "O_350": "Juice",
}


def get_wiki_image_url(wiki_title):
  api_url = (
      "https://stardewvalleywiki.com/mediawiki/api.php?"
      + urllib.parse.urlencode({
          "action": "query",
          "titles": f"File:{wiki_title}.png",
          "prop": "imageinfo",
          "iiprop": "url",
          "format": "json",
      })
  )

  req = urllib.request.Request(api_url, headers=HEADERS)
  try:
    with urllib.request.urlopen(req, timeout=5) as response:
      data = json.loads(response.read().decode("utf-8"))
      pages = data.get("query", {}).get("pages", {})
      for _, page in pages.items():
        imageinfo = page.get("imageinfo", [])
        if imageinfo:
          return imageinfo[0].get("url")
  except Exception:
    pass
  return None


def download_file(url, save_path):
  req = urllib.request.Request(url, headers=HEADERS)
  try:
    with urllib.request.urlopen(req, timeout=5) as resp:
      with open(save_path, "wb") as f:
        f.write(resp.read())
      return True
  except Exception:
    pass
  return False


def main():
  print(f"[INFO] Fetching {len(MISSING_CHEST_ITEMS)} missing chest items...")
  for sprite_key, wiki_title in MISSING_CHEST_ITEMS.items():
    save_path = OUTPUT_DIR / f"{sprite_key}.png"
    if save_path.exists():
      continue

    url = get_wiki_image_url(wiki_title)
    if not url:
      url = f"https://stardewvalleywiki.com/Special:Redirect/file/{wiki_title}.png"

    if download_file(url, save_path):
      print(f"[OK] Saved {sprite_key}.png ({wiki_title})")
    else:
      print(f"[WARN] Failed to download {wiki_title}")


if __name__ == "__main__":
  main()
