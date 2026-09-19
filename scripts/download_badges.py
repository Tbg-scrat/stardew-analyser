#!/usr/bin/env python3
# scripts/download_badges.py

import json
import urllib.parse
import urllib.request
from pathlib import Path

OUTPUT_DIR = Path("static/img/badges")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}

BADGE_MAPPINGS = {
    "silver_star.png": "Silver_Quality",
    "gold_star.png": "Gold_Quality",
    "iridium_star.png": "Iridium_Quality",
}


def download_badge(filename, wiki_title):
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
    with urllib.request.urlopen(req, timeout=5) as resp:
      data = json.loads(resp.read().decode("utf-8"))
      pages = data.get("query", {}).get("pages", {})
      for _, page in pages.items():
        imageinfo = page.get("imageinfo", [])
        if imageinfo:
          direct_url = imageinfo[0].get("url")
          save_path = OUTPUT_DIR / filename
          img_req = urllib.request.Request(direct_url, headers=HEADERS)
          with urllib.request.urlopen(img_req, timeout=5) as img_resp:
            with open(save_path, "wb") as f:
              f.write(img_resp.read())
          print(f"[OK] Downloaded badge -> static/img/badges/{filename}")
          return True
  except Exception as e:
    print(f"[WARN] Failed to download {wiki_title}: {e}")
  return False


if __name__ == "__main__":
  print("[INFO] Downloading quality star badges...")
  for fn, title in BADGE_MAPPINGS.items():
    download_badge(fn, title)
