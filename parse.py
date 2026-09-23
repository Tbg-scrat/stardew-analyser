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
from src.modules.fishing import parse_fishing
from src.modules.museum import parse_museum
from src.modules.cooking import parse_cooking
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


def format_wiki_filename(name):
    """Clean item names into Stardew Valley Wiki image file conventions."""
    return name.replace(" ", "_").replace("'", "%27")


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
    raw_fish = parse_fishing(player)
    fish_save_map = {str(k).replace("(O)", ""): v for k, v in raw_fish.items()}

    fish_mapped = []
    for item_id, catalog_item in FISH_CATALOG.items():
        stats = fish_save_map.get(item_id)
        is_caught = stats is not None
        fish_mapped.append(
            {
                "id": item_id,
                "name": catalog_item.get("name", f"Fish {item_id}"),
                "count": stats["count"] if is_caught else 0,
                "length": stats["length"] if is_caught else 0,
                "status": "caught" if is_caught else "not_caught",
                "is_unlocked": is_caught,
                "image": catalog_item.get("image", ""),
                "wiki_icon": format_wiki_filename(catalog_item.get("name", "")),
            }
        )
    data["fish_caught"] = sorted(fish_mapped, key=lambda x: x["name"])

    # 3. MUSEUM CATALOG MERGING
    raw_museum = parse_museum(root)
    donated_set = {str(item_id).replace("(O)", "") for item_id in raw_museum}

    museum_mapped = []
    for item_id, catalog_item in MUSEUM_CATALOG.items():
        is_donated = item_id in donated_set
        museum_mapped.append(
            {
                "id": item_id,
                "name": catalog_item.get("name", f"Artifact/Mineral {item_id}"),
                "type": catalog_item.get("type", "Artifact"),
                "status": "found" if is_donated else "not_found",
                "is_unlocked": is_donated,
                "image": catalog_item.get("image", ""),
                "wiki_icon": format_wiki_filename(catalog_item.get("name", "")),
            }
        )
    data["museum_pieces"] = sorted(museum_mapped, key=lambda x: x["name"])

    # 4. COOKING CATALOG MERGING
    raw_cooking = parse_cooking(player)
    cooking_save_map = {str(k).replace("(O)", ""): v for k, v in raw_cooking.items()}

    cooking_mapped = []
    for item_id, catalog_item in COOKING_CATALOG.items():
        count = cooking_save_map.get(str(item_id), 0)
        is_cooked = count > 0
        cooking_mapped.append(
            {
                "id": item_id,
                "name": catalog_item.get("name", f"Recipe {item_id}"),
                "count": count,
                "status": "cooked" if is_cooked else "not_cooked",
                "is_unlocked": is_cooked,
                "image": catalog_item.get("image", ""),
                "wiki_icon": catalog_item.get(
                    "wiki_icon", format_wiki_filename(catalog_item.get("name", ""))
                ),
            }
        )
    data["recipes_cooked"] = sorted(cooking_mapped, key=lambda x: x["name"])

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
        