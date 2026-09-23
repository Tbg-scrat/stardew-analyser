# -*- coding: utf-8 -*-

import traceback
import os
import time
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from src.core.xml_reader import get_player_node
from src.core.reference_data import load_object_map
from data.data_loader import (
    FISH_CATALOG,
    MUSEUM_CATALOG,
    SHIPPING_CATALOG,
    COOKING_CATALOG,
    ACHIEVEMENTS_CATALOG,
)

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
from src.modules.artisan.casks import parse_all_casks_from_save
from src.modules.chests import parse_chests

SAVE_DIR = Path(os.getenv("SAVE_DIR", "/saves"))
OUTPUT_HTML = Path("index.html")


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


def analyze_save(file_path, object_map):
    root, player = get_player_node(file_path)

    data = parse_player(player)

    # Base overview modules
    data["weather"] = parse_weather(root)
    data["daily_luck"] = parse_luck(root)
    data["festivals"] = parse_festivals(root)
    data["birthdays"] = parse_birthdays(root)

    # 1. SHIPPING CATALOG MERGING
    data["shipped_items"] = get_formatted_shipping(player, SHIPPING_CATALOG)

    # 2. FISHING CATALOG MERGING
    data["fish_caught"] = get_formatted_fishing(player, FISH_CATALOG)

    # 3. MUSEUM CATALOG MERGING
    data["museum_pieces"] = get_formatted_museum(root, MUSEUM_CATALOG)

    # 4. COOKING CATALOG MERGING
    data["recipes_cooked"] = get_formatted_cooking(player, COOKING_CATALOG)

    # 5. ACHIEVEMENTS MODULE MERGING
    data["achievements"] = parse_achievements(
        player, ACHIEVEMENTS_CATALOG, shipped_items=data["shipped_items"]
    )

    data["friendships"] = parse_social(player)
    data["daily_intel"] = None

    # 6. CASKS MODULE
    cask_data = parse_all_casks_from_save(root, player)
    print(
        f"[DEBUG parse.py] Casks parsed: {cask_data['total_casks']} total "
        f"({cask_data['ready_today']} ready today, {cask_data['ready_tomorrow']} ready tomorrow)"
    )
    data["casks"] = cask_data

    # 7. CHESTS MODULE
    chest_summary = parse_chests(root, object_map)
    print(f"[DEBUG parse.py] Material types aggregated: {len(chest_summary['material_totals'])}")
    data["chests"] = chest_summary

    return data


def generate_dashboard_html(all_saves_data):
    env = Environment(loader=FileSystemLoader("templates", encoding="utf-8"))
    template = env.get_template("index.html")

    farms_context = []
    for save_id, data in all_saves_data.items():
        data["farm_id"] = save_id
        data["farmer_name"] = data.get("farmer", "Farmer")
        data["farm_name"] = data.get("farm", "Farm")
        farms_context.append(data)

    build_time = int(time.time())

    rendered_html = template.render(
        farms=farms_context, build_timestamp=build_time
    )

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    print(
        f"[OK] Generated static dashboard for {len(all_saves_data)} save game(s)"
        f" -> {OUTPUT_HTML.resolve()}"
    )


if __name__ == "__main__":
    print("[INFO] Loading game item reference map...")
    object_map = load_object_map()

    print(f"[INFO] Scanning directory: {SAVE_DIR.resolve()}")
    saves = find_all_saves(SAVE_DIR)
    print(f"[INFO] Discovered {len(saves)} save candidate(s).")

    all_saves_data = {}
    for save_id, save_path in saves:
        try:
            print(f"[INFO] Processing save file: {save_id}")
            all_saves_data[save_id] = analyze_save(save_path, object_map)
        except Exception as e:
            print(f"[ERROR] Detailed traceback for save '{save_id}':")
            traceback.print_exc()

    if all_saves_data:
        generate_dashboard_html(all_saves_data)
    else:
        print(f"[WARN] No valid save games were parsed in {SAVE_DIR.resolve()}")
        