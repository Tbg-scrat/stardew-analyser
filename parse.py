# parse.py
# -*- coding: utf-8 -*-

import logging
import os
import time
from pathlib import Path

from src.core.logger import setup_logging

# Initialize central logging configuration
setup_logging()
logger = logging.getLogger(__name__)

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
from src.modules.crops import parse_all_crops_from_save
from src.modules.tools import parse_tools
from src.modules.hay import parse_hay_data
from src.modules.grandpa import parse_grandpa_data
from src.modules.community_center import parse_community_center_data

SAVE_DIR = Path(os.getenv("SAVE_DIR", "/saves"))


def find_all_saves(saves_dir):
    saves_dir = Path(saves_dir)
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


def _evaluate_watering_can_rain_opportunity(data):
    """
    Evaluates if tomorrow is rainy/stormy and the watering can is ready to upgrade today with sufficient funds and materials.
    Also detects Clint's festival pickup closures.
    """
    today_day = data.get("day_of_month", 1)
    today_season = (data.get("season") or "spring").lower()

    # Weather check
    weather_valley = data.get("weather", {}).get("valley", {})
    weather_id = weather_valley.get("id", "")
    weather_name = weather_valley.get("name", "")
    is_rainy_tomorrow = weather_id in ("Rain", "Storm") or weather_name in ("Rainy", "Stormy")

    # Watering can check
    tools_info = data.get("tools", {})
    watering_can = tools_info.get("watering_can")
    if not watering_can and "upgradeable" in tools_info:
        watering_can = next((t for t in tools_info["upgradeable"] if t.get("key") == "WateringCan"), None)

    if not watering_can:
        return {"active": False}

    is_ready = watering_can.get("status") == "ready"
    next_tier = watering_can.get("next_tier") or {}
    can_upgrade = next_tier.get("can_upgrade", False)

    if is_rainy_tomorrow and is_ready and can_upgrade:
        pickup_day = today_day + 2
        pickup_season = today_season
        if pickup_day > 28:
            pickup_day -= 28
            seasons_order = ["spring", "summer", "fall", "winter"]
            next_idx = (seasons_order.index(today_season) + 1) % 4
            pickup_season = seasons_order[next_idx]

        festivals_shop_closed = {
            ("spring", 13),  # Egg Festival
            ("spring", 24),  # Flower Dance
            ("summer", 11),  # Luau
            ("fall", 16),    # Stardew Valley Fair
            ("winter", 8),   # Festival of Ice
            ("winter", 25),  # Feast of the Winter Star
        }

        has_festival_delay = (pickup_season, pickup_day) in festivals_shop_closed

        logger.debug(
            f"Watering Can Rain Opportunity active: {next_tier.get('name')} | "
            f"Rain forecast tomorrow | Festival delay on pickup ({pickup_season.capitalize()} {pickup_day}): {has_festival_delay}"
        )

        return {
            "active": True,
            "next_tier_name": next_tier.get("name", "Watering Can Upgrade"),
            "gold_cost": next_tier.get("gold_cost", 0),
            "materials_text": next_tier.get("materials_text") or next_tier.get("materials") or "",
            "has_festival_delay": has_festival_delay,
            "pickup_day": pickup_day,
            "pickup_season": pickup_season.capitalize(),
        }

    return {"active": False}


def analyze_save(file_path):
    # Milestone 1: XML Ingestion
    t_xml_start = time.perf_counter()
    root, player = get_player_node(file_path)
    xml_duration_ms = (time.perf_counter() - t_xml_start) * 1000
    logger.info(f"XML ingestion completed in {xml_duration_ms:.2f}ms")

    # Milestone 2: Feature Module Parsing
    t_modules_start = time.perf_counter()

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

    # Crops Module
    crops_summary = parse_all_crops_from_save(root, current_day=data["day_of_month"])
    data["crops"] = crops_summary

    # Tools Module (passes player funds and chest material stock)
    tools_summary = parse_tools(
        root,
        player_money=data.get("money", 0),
        material_totals=chest_summary.get("material_totals", []),
    )
    data["tools"] = tools_summary

    # Evaluate Watering Can Rain Opportunity
    data["watering_can_opportunity"] = _evaluate_watering_can_rain_opportunity(data)

    # Hay Tracker Module
    hay_summary = parse_hay_data(root)
    data["hay"] = hay_summary

    # Grandpa's Evaluation Module
    grandpa_summary = parse_grandpa_data(
        root,
        player,
        shipped_items=data["shipped_items"],
        fish_caught=data["fish_caught"],
        museum_pieces=data["museum_pieces"],
        friendships=data["friendships"],
    )
    data["grandpa"] = grandpa_summary

    # Community Center / Joja Module
    cc_summary = parse_community_center_data(root, player)
    data["community_center"] = cc_summary

    modules_duration_ms = (time.perf_counter() - t_modules_start) * 1000
    logger.info(f"All 15 feature modules parsed in {modules_duration_ms:.2f}ms")

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

    cooking_unlocked = len([r for r in data.get("recipes_cooked", []) if r.get("is_unlocked")])
    cooking_total = len(data.get("recipes_cooked", []))

    social_count = len(data.get("friendships", []))

    artisan_machines = data.get("artisan", {}).get("summary", {}).get("total_machines", 0)
    chests_count = data.get("chests", {}).get("total_chests", 0)

    crops_total = data.get("crops", {}).get("summary", {}).get("total_crops", 0)
    crops_ready = data.get("crops", {}).get("summary", {}).get("ready_today", 0)

    tools_maxed = sum(1 for t in data.get("tools", {}).get("upgradeable", []) if t.get("is_max"))
    tools_total = len(data.get("tools", {}).get("upgradeable", []))
    upgrading_tools = [t for t in data.get("tools", {}).get("upgradeable", []) if t.get("status") == "upgrading"]
    ready_tools_count = sum(
        1 for t in data.get("tools", {}).get("upgradeable", [])
        if (t.get("next_tier") or {}).get("can_upgrade")
    )
    scythe_name = data.get("tools", {}).get("scythe", {}).get("current_stage", {}).get("name", "Scythe")

    if upgrading_tools:
        upg = upgrading_tools[0]
        upg_detail = f"{upg.get('display_name', 'Tool')} at Clint's, {upg.get('days_left', 0)}d left | {scythe_name}"
    elif ready_tools_count > 0:
        upg_detail = f"{ready_tools_count} Ready to Upgrade | {scythe_name}"
    else:
        upg_detail = scythe_name

    hay_current = data.get("hay", {}).get("current_hay", 0)
    hay_max = data.get("hay", {}).get("max_capacity", 0)
    hay_animals = data.get("hay", {}).get("total_animals", 0)

    grandpa_score = data.get("grandpa", {}).get("total_score", 0)
    grandpa_max = data.get("grandpa", {}).get("max_score", 21)
    grandpa_candles = data.get("grandpa", {}).get("candles", 1)

    cc_bundles = data.get("community_center", {}).get("completed_bundles", 0)
    cc_total = data.get("community_center", {}).get("total_bundles", 30)
    cc_route = data.get("community_center", {}).get("route_label", "Community Center")

    logger.info(
        f"Parsed '{save_id}' ({farmer} @ {farm} Farm | Y{year} {season} {day}) -> "
        f"Achievements: {ach_unlocked}/{ach_total} | "
        f"Shipped: {shipped_unlocked}/{shipped_total} | "
        f"Fish: {fish_unlocked}/{fish_total} | "
        f"Museum: {museum_unlocked}/{museum_total} | "
        f"Cooking: {cooking_unlocked}/{cooking_total} | "
        f"Social: {social_count} NPCs | "
        f"Artisan: {artisan_machines} machines | "
        f"Chests: {chests_count} | "
        f"Crops: {crops_total} total ({crops_ready} ready) | "
        f"Tools: {tools_maxed}/{tools_total} Maxed ({upg_detail}) | "
        f"Hay: {hay_current}/{hay_max} ({hay_animals} animals) | "
        f"Grandpa: {grandpa_score}/{grandpa_max} pts ({grandpa_candles} Candles) | "
        f"CC: {cc_bundles}/{cc_total} Bundles ({cc_route})"
    )


def run_pipeline(save_dir=None, output_path=None):
    """
    Executes the full parsing pipeline for a given save directory (or default SAVE_DIR),
    parsing all discovered farms and rendering the multi-farm dashboard HTML.
    """
    pipeline_start = time.perf_counter()

    target_dir = Path(save_dir) if save_dir else SAVE_DIR
    logger.info(f"Scanning directory: {target_dir.resolve()}")

    saves = find_all_saves(target_dir)
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
        try:
            t_render_start = time.perf_counter()
            result = generate_dashboard_html(all_saves_data, output_path=output_path)
            render_duration_ms = (time.perf_counter() - t_render_start) * 1000
            logger.info(f"Dashboard rendered in {render_duration_ms:.2f}ms")
        except TypeError:
            # Fallback if generate_dashboard_html does not accept output_path kwarg
            t_render_start = time.perf_counter()
            result = generate_dashboard_html(all_saves_data)
            render_duration_ms = (time.perf_counter() - t_render_start) * 1000
            logger.info(f"Dashboard rendered in {render_duration_ms:.2f}ms")

        total_duration_ms = (time.perf_counter() - pipeline_start) * 1000
        logger.info(f"Pipeline completed in {total_duration_ms:.2f}ms")
        return result
    else:
        logger.warning(f"No valid save games were parsed in {target_dir.resolve()}")
        return None


if __name__ == "__main__":
    run_pipeline()
    