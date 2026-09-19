#!/usr/bin/env python3
# scripts/download_sprites.py

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Bootstrap project root for module imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
  sys.path.insert(0, str(PROJECT_ROOT))

from data.data_loader import (
    ACHIEVEMENTS_CATALOG,
    COOKING_CATALOG,
    FISH_CATALOG,
    MUSEUM_CATALOG,
    SHIPPING_CATALOG,
)
from src.core.reference_data import load_object_map

OUTPUT_DIR = Path("static/img/items")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}


def sanitize_wiki_filename(name):
  """Clean item names into Stardew Valley Wiki image conventions."""
  return name.replace(" ", "_").replace("'", "%27")


def get_qualified_sprite_key(item_id, item_type="O"):
  """Creates a filesystem-safe sprite key (e.g., O_382 or BC_130)."""
  raw_id = str(item_id).replace("(O)", "").replace("(BC)", "")
  prefix = "BC" if "(BC)" in str(item_id) else item_type
  return f"{prefix}_{raw_id}"


def batch_resolve_wiki_urls(names_list):
  """Queries MediaWiki API via POST in chunks of 20 to avoid URL length & 404 issues."""
  file_urls = {}
  chunk_size = 20

  for i in range(0, len(names_list), chunk_size):
    chunk = names_list[i : i + chunk_size]
    titles = "|".join([f"File:{sanitize_wiki_filename(name)}.png" for name in chunk])

    post_data = urllib.parse.urlencode({
        "action": "query",
        "titles": titles,
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json",
    }).encode("utf-8")

    api_url = "https://stardewvalleywiki.com/mediawiki/api.php"
    req = urllib.request.Request(api_url, data=post_data, headers=HEADERS)

    try:
      with urllib.request.urlopen(req, timeout=10) as response:
        if response.status == 200:
          data = json.loads(response.read().decode("utf-8"))
          pages = data.get("query", {}).get("pages", {})
          for _, page_info in pages.items():
            title = page_info.get("title", "").replace("File:", "").replace(".png", "")
            imageinfo = page_info.get("imageinfo", [])
            if imageinfo:
              file_urls[title] = imageinfo[0].get("url")
    except Exception as e:
      print(f"  └─ [WARN] Batch query failed for chunk {i//chunk_size + 1}: {e}")

    time.sleep(0.5)

  return file_urls


def download_file(url, save_path):
  """Downloads a direct image file to disk."""
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


def process_catalogs():
  """Collects item keys, batch-resolves URLs, and downloads missing sprites to static/img/items."""
  items_to_download = {}

  print("[INFO] Processing object map...")
  object_map = load_object_map()
  for item_id, details in object_map.items():
    name = details.get("name") if isinstance(details, dict) else str(details)
    if not name or name == "Unknown Item":
      continue
    sprite_key = get_qualified_sprite_key(item_id)
    items_to_download[sprite_key] = name

  print("[INFO] Processing static catalogs...")
  all_catalogs = [
      SHIPPING_CATALOG,
      FISH_CATALOG,
      MUSEUM_CATALOG,
      COOKING_CATALOG,
      ACHIEVEMENTS_CATALOG,
  ]

  for catalog in all_catalogs:
    if isinstance(catalog, list):
      for entry in catalog:
        if isinstance(entry, dict):
          item_id = entry.get("id") or entry.get("item_id") or entry.get("name")
          name = entry.get("name")
          if name and item_id:
            sprite_key = get_qualified_sprite_key(item_id)
            items_to_download[sprite_key] = name
    elif isinstance(catalog, dict):
      for item_id, info in catalog.items():
        name = info.get("name") if isinstance(info, dict) else str(info)
        if name:
          sprite_key = get_qualified_sprite_key(item_id)
          items_to_download[sprite_key] = name

  total_count = len(items_to_download)
  print(f"[INFO] Target Directory: {OUTPUT_DIR.resolve()}")
  print(f"[INFO] Total unique items queued: {total_count}")

  # Filter items that need downloading
  pending_items = {
      key: name
      for key, name in items_to_download.items()
      if not (OUTPUT_DIR / f"{key}.png").exists()
  }

  print(f"[INFO] Items remaining to download: {len(pending_items)}")

  if pending_items:
    unique_names = list({name for name in pending_items.values()})
    print(f"[INFO] Resolving image URLs for {len(unique_names)} unique items via API...")
    resolved_urls = batch_resolve_wiki_urls(unique_names)

    downloaded = 0
    failed = 0
    total_pending = len(pending_items)

    for idx, (sprite_key, name) in enumerate(pending_items.items(), 1):
      save_path = OUTPUT_DIR / f"{sprite_key}.png"
      wiki_clean_name = sanitize_wiki_filename(name)
      url = resolved_urls.get(wiki_clean_name) or resolved_urls.get(name)

      if not url:
        url = f"https://stardewvalleywiki.com/Special:Redirect/file/{wiki_clean_name}.png"

      print(f"[{idx}/{total_pending}] Downloading {name} -> {sprite_key}.png...")
      if download_file(url, save_path):
        downloaded += 1
        time.sleep(1.0)  # 1-second delay between file downloads
      else:
        print(f"  └─ [WARN] Skipping {name} (File not found or blocked)")
        failed += 1

    print(f"\n[SUCCESS] Completed! Downloaded: {downloaded}, Failed: {failed}")
  else:
    print("\n[SUCCESS] All sprites already exist in static/img/items/!")


if __name__ == "__main__":
  process_catalogs()
  