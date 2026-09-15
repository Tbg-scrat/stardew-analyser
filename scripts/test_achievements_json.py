#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sanity check script for data/achievements.json.
Validates structure, checks local sprite existence, and verifies names against the official wiki.
"""

import html
import json
import os
import re
import urllib.request

JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "achievements.json")
IMG_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "img", "achievements")
WIKI_URL = "https://stardewvalleywiki.com/Achievements"

REQUIRED_KEYS = {"id", "key", "name", "description", "category", "icon", "target", "tip"}

def run_sanity_checks():
    print("🔍 Starting JSON Sanity Check...\n")
    
    if not os.path.exists(JSON_PATH):
        print(f"❌ File not found: {JSON_PATH}")
        return
        
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📦 Total achievements in JSON: {len(data)}")

    # 1. Internal Schema & File Check
    seen_ids = set()
    errors = 0

    for idx, item in enumerate(data):
        missing_keys = REQUIRED_KEYS - item.keys()
        if missing_keys:
            print(f"❌ Item index {idx} ({item.get('name', 'UNKNOWN')}) missing keys: {missing_keys}")
            errors += 1

        item_id = item.get("id")
        if item_id in seen_ids:
            print(f"❌ Duplicate ID detected: {item_id}")
            errors += 1
        seen_ids.add(item_id)

        icon_name = item.get("icon")
        if icon_name:
            icon_path = os.path.join(IMG_DIR, icon_name)
            if not os.path.exists(icon_path):
                print(f"⚠️ Missing sprite asset: {icon_name} for '{item.get('name')}'")
                errors += 1

    if errors == 0:
        print("✅ Internal Schema & Sprite File Check: PASSED")
    else:
        print(f"❌ Internal Schema Check: FAILED with {errors} issue(s)\n")

    # 2. Live Wiki Match Check
    print("\n🌐 Cross-matching against Stardew Valley Wiki...")
    req = urllib.request.Request(WIKI_URL, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        with urllib.request.urlopen(req) as response:
            raw_html = response.read().decode('utf-8')
            # Unescape entities (e.g., convert &#39; to ')
            decoded_html = html.unescape(raw_html)

        unmatched_wiki = 0
        for item in data:
            name = item["name"]
            # Check for exact string or normalized alphanumeric match
            if name not in decoded_html:
                clean_name = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
                clean_html = re.sub(r'[^a-zA-Z0-9]', '', decoded_html).lower()
                if clean_name not in clean_html:
                    print(f"⚠️ Warning: Could not find exact Wiki match for '{name}'")
                    unmatched_wiki += 1

        if unmatched_wiki == 0:
            print("✅ Wiki Cross-Match Check: PASSED (100% names verified on Wiki)")
        else:
            print(f"⚠️ Wiki Cross-Match Check: Finished with {unmatched_wiki} warning(s)")

    except Exception as e:
        print(f"❌ Failed to query wiki: {e}")

if __name__ == "__main__":
    run_sanity_checks()
    