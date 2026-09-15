#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.xml_reader import get_player_node
from parse import find_all_saves

PROJECT_ROOT = Path(__file__).parent.parent
LOCAL_SAVES_DIR = PROJECT_ROOT / "saves"

def debug_save_achievements():
    print(f"🔍 Checking local project saves in: {LOCAL_SAVES_DIR.resolve()}")
    saves = find_all_saves(LOCAL_SAVES_DIR)

    if not saves:
        print(f"❌ No saves found in {LOCAL_SAVES_DIR.resolve()}")
        return

    for save_id, save_path in saves:
        print(f"\n📂 Processing save: {save_id}")
        root, player = get_player_node(save_path)
        
        achievements_node = player.find("achievements")
        if achievements_node is not None:
            unlocked_ids = [
                int(node.text) 
                for node in achievements_node.findall("int") 
                if node.text and node.text.isdigit()
            ]
            print("  Raw unlocked IDs in XML:", sorted(unlocked_ids))
            print("  - ID 27 (Polyculture):", 27 in unlocked_ids)
            print("  - ID 28 (Monoculture):", 28 in unlocked_ids)
            print("  - ID 29 (Full Shipment):", 29 in unlocked_ids)
        else:
            print("  ❌ No <achievements> node found in <player>")

if __name__ == "__main__":
    debug_save_achievements()
    