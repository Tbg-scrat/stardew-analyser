# parse.py
# -*- coding: utf-8 -*-

import logging
import os
from pathlib import Path

from src.core.logger import setup_logging

# Initialize central logging configuration
setup_logging()
logger = logging.getLogger("parse")

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
        logger.warning(f"Save directory '{saves_dir.resolve()}' does not exist.")
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

    # Extract calendar date from root save node
    try:
        data["day_of_month"] = int(root.findtext("dayOfMonth", "1"))
    except ValueError:
        data["day_of_month"] = 1

    data["season"] = root.findtext("currentSeason", "spring")

    try:
        data["year"] = int(root.findtext("year", "1"))
    except ValueError:
        data["year"] = 1

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

    # Artisan Module
    artisan_data = parse_all_artisan_goods(root, player)
    data["artisan"] = artisan_data
    data["casks"] = artisan_data["casks"]

    # Chests Module
    chest_summary = parse_chests(root)
    data["chests"] = chest_summary

    return data



def log_save_summary(save_id, data):
    """Logs a single-line INFO summary confirming successful extraction across all modules."""
    farmer = data.get("farmer", "Farmer")
    farm = data.get("farm", "Farm")
    day = data.get("day_of_month", 1)
    season = (data.get("season") or "spring").capitalize()
    year = data.get("year", 1)

    ach_unlocked = data.get("achievements", {}).get("unlocked_count", 0)
    ach_total = data.get("achievements", {}).get("total", 0)

    shipped_unlocked = len([i for i in data.get("shipped_items", []) if i.get("is_unlocked")])
    shipped_total = len(data.get("shipped_items", []))

    fish_unlocked = len([i for i in data.get("fish_caught", []) if i.get("is_unlocked")])
    fish_total = len(data.get("fish_caught", []))

    museum_unlocked = len([i for i in data.get("museum_pieces", []) if i.get("is_unlocked")])
    museum_total = len(data.get("museum_pieces", []))

    artisan_machines = data.get("artisan", {}).get("summary", {}).get("total_machines", 0)
    chests_count = data.get("chests", {}).get("total_chests", 0)

    logger.info(
        f"Parsed '{save_id}' ({farmer} @ {farm} Farm | Y{year} {season} {day}) -> "
        f"Achievements: {ach_unlocked}/{ach_total} | "
        f"Shipped: {shipped_unlocked}/{shipped_total} | "
        f"Fish: {fish_unlocked}/{fish_total} | "
        f"Museum: {museum_unlocked}/{museum_total} | "
        f"Artisan: {artisan_machines} machines | "
        f"Chests: {chests_count}"
    )


if __name__ == "__main__":
    logger.info(f"Scanning directory: {SAVE_DIR.resolve()}")
    saves = find_all_saves(SAVE_DIR)
    logger.info(f"Discovered {len(saves)} save candidate(s).")

    all_saves_data = {}
    for save_id, save_path in saves:
        try:
            data = analyze_save(save_path)
            all_saves_data[save_id] = data
            log_save_summary(save_id, data)
        except Exception as e:
            logger.exception(f"Error processing save '{save_id}': {e}")

    if all_saves_data:
        generate_dashboard_html(all_saves_data)
    else:
        logger.warning(f"No valid save games were parsed in {SAVE_DIR.resolve()}")
        