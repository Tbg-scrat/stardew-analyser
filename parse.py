# -*- coding: utf-8 -*-

import traceback
import os
from pathlib import Path

from src.core.xml_reader import get_player_node
from src.core.renderer import generate_dashboard_html

from src.modules.player import parse_player
from src.modules.shipping import get_formatted_shipping
from src.modules.fishing import get_formatted_fishing
from src.modules.museum import get_formatted_museum
from src.modules.cooking import get_formatted_cooking
from src.modules.social import parse_social
from src.modules.weather import parse_weather
from src.modules.luck import parse_luck
from src.modules.festivals import parse_festivals
from src.modules.birthdays import parse_birthdays
from src.modules.achievements import parse_achievements
from src.modules.artisan import parse_all_artisan_goods
from src.modules.chests import parse_chests

SAVE_DIR = Path(os.getenv("SAVE_DIR", "/saves"))


def find_all_saves(saves_dir):
    save_files = []
    if not saves_dir.exists():
        print(f"[WARN] Save directory '{saves_dir.resolve()}' does not exist.")
        return save_files

    for item in saves_dir.iterdir():
        if item.is_dir():
            target_file = item / item.name
            if target_file.exists() and not item.name.startswith("."):
                save_files.append((item.name, target_file))
    return sorted(save_files, key=lambda x: x[0])


def analyze_save(file_path):
    root, player = get_player_node(file_path)

    data = parse_player(player)

    # Base overview modules
    data["weather"] = parse_weather(root)
    data["daily_luck"] = parse_luck(root)
    data["festivals"] = parse_festivals(root)
    data["birthdays"] = parse_birthdays(root)

    # Catalog-backed feature modules
    data["shipped_items"] = get_formatted_shipping(player)
    data["fish_caught"] = get_formatted_fishing(player)
    data["museum_pieces"] = get_formatted_museum(root)
    data["recipes_cooked"] = get_formatted_cooking(player)

    # Achievements
    data["achievements"] = parse_achievements(
        player, shipped_items=data["shipped_items"]
    )

    data["friendships"] = parse_social(player)
    data["daily_intel"] = None

    # ARTISAN MODULE AGGREGATOR
    artisan_data = parse_all_artisan_goods(root, player)
    data["artisan"] = artisan_data
    # Backwards compatibility key for cellar cask overview
    data["casks"] = artisan_data["casks"]

    print(
        f"[DEBUG parse.py] Artisan machines parsed: {artisan_data['summary']['total_machines']} total "
        f"({artisan_data['summary']['ready_today']} ready today, "
        f"{artisan_data['summary']['ready_tomorrow']} ready tomorrow)"
    )

    # Chests Module
    chest_summary = parse_chests(root)
    print(f"[DEBUG parse.py] Material types aggregated: {len(chest_summary['material_totals'])}")
    data["chests"] = chest_summary

    return data


if __name__ == "__main__":
    print(f"[INFO] Scanning directory: {SAVE_DIR.resolve()}")
    saves = find_all_saves(SAVE_DIR)
    print(f"[INFO] Discovered {len(saves)} save candidate(s).")

    all_saves_data = {}
    for save_id, save_path in saves:
        try:
            print(f"[INFO] Processing save file: {save_id}")
            all_saves_data[save_id] = analyze_save(save_path)
        except Exception as e:
            print(f"[ERROR] Detailed traceback for save '{save_id}':")
            traceback.print_exc()

    if all_saves_data:
        generate_dashboard_html(all_saves_data)
    else:
        print(f"[WARN] No valid save games were parsed in {SAVE_DIR.resolve()}")
        