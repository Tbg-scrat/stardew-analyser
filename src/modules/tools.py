# src/modules/tools.py

import logging
import re
import time
from typing import Any

from src.core.reference_data import get_tools_catalog

logger = logging.getLogger(__name__)

DEFAULT_UPGRADEABLE_TOOLS: dict[str, Any] = {
    "Axe": {
        "name": "Axe",
        "tiers": [
            {
                "level": 0,
                "name": "Axe",
                "icon": "/cache/img/T/T_Axe.png",
                "gold_cost": 0,
                "materials": None,
                "perks": "Chops trees.",
            },
            {
                "level": 1,
                "name": "Copper Axe",
                "icon": "/cache/img/T/T_CopperAxe.png",
                "gold_cost": 2000,
                "materials": "5x Copper Bar",
                "perks": "Chops large stumps.",
            },
            {
                "level": 2,
                "name": "Steel Axe",
                "icon": "/cache/img/T/T_SteelAxe.png",
                "gold_cost": 5000,
                "materials": "5x Iron Bar",
                "perks": "Chops large logs.",
            },
            {
                "level": 3,
                "name": "Gold Axe",
                "icon": "/cache/img/T/T_GoldAxe.png",
                "gold_cost": 10000,
                "materials": "5x Gold Bar",
                "perks": "Chops trees quickly.",
            },
            {
                "level": 4,
                "name": "Iridium Axe",
                "icon": "/cache/img/T/T_IridiumAxe.png",
                "gold_cost": 25000,
                "materials": "5x Iridium Bar",
                "perks": "Maximum chopping efficiency.",
            },
        ],
    },
    "Pickaxe": {
        "name": "Pickaxe",
        "tiers": [
            {
                "level": 0,
                "name": "Pickaxe",
                "icon": "/cache/img/T/T_Pickaxe.png",
                "gold_cost": 0,
                "materials": None,
                "perks": "Breaks small rocks.",
            },
            {
                "level": 1,
                "name": "Copper Pickaxe",
                "icon": "/cache/img/T/T_CopperPickaxe.png",
                "gold_cost": 2000,
                "materials": "5x Copper Bar",
                "perks": "Breaks large rocks in mines.",
            },
            {
                "level": 2,
                "name": "Steel Pickaxe",
                "icon": "/cache/img/T/T_SteelPickaxe.png",
                "gold_cost": 5000,
                "materials": "5x Iron Bar",
                "perks": "Breaks boulders.",
            },
            {
                "level": 3,
                "name": "Gold Pickaxe",
                "icon": "/cache/img/T/T_GoldPickaxe.png",
                "gold_cost": 10000,
                "materials": "5x Gold Bar",
                "perks": "Breaks most rocks easily.",
            },
            {
                "level": 4,
                "name": "Iridium Pickaxe",
                "icon": "/cache/img/T/T_IridiumPickaxe.png",
                "gold_cost": 25000,
                "materials": "5x Iridium Bar",
                "perks": "Breaks any rock in 1-2 hits.",
            },
        ],
    },
    "Hoe": {
        "name": "Hoe",
        "tiers": [
            {
                "level": 0,
                "name": "Hoe",
                "icon": "/cache/img/T/T_Hoe.png",
                "gold_cost": 0,
                "materials": None,
                "perks": "Till 1 tile.",
            },
            {
                "level": 1,
                "name": "Copper Hoe",
                "icon": "/cache/img/T/T_CopperHoe.png",
                "gold_cost": 2000,
                "materials": "5x Copper Bar",
                "perks": "Till 3 tiles in a line.",
            },
            {
                "level": 2,
                "name": "Steel Hoe",
                "icon": "/cache/img/T/T_SteelHoe.png",
                "gold_cost": 5000,
                "materials": "5x Iron Bar",
                "perks": "Till 5 tiles in a line.",
            },
            {
                "level": 3,
                "name": "Gold Hoe",
                "icon": "/cache/img/T/T_GoldHoe.png",
                "gold_cost": 10000,
                "materials": "5x Gold Bar",
                "perks": "Till 3x3 area.",
            },
            {
                "level": 4,
                "name": "Iridium Hoe",
                "icon": "/cache/img/T/T_IridiumHoe.png",
                "gold_cost": 25000,
                "materials": "5x Iridium Bar",
                "perks": "Till 6x3 area.",
            },
        ],
    },
    "WateringCan": {
        "name": "Watering Can",
        "tiers": [
            {
                "level": 0,
                "name": "Watering Can",
                "icon": "/cache/img/T/T_WateringCan.png",
                "gold_cost": 0,
                "materials": None,
                "perks": "Water 1 tile.",
            },
            {
                "level": 1,
                "name": "Copper Watering Can",
                "icon": "/cache/img/T/T_CopperWateringCan.png",
                "gold_cost": 2000,
                "materials": "5x Copper Bar",
                "perks": "Water 3 tiles in a line.",
            },
            {
                "level": 2,
                "name": "Steel Watering Can",
                "icon": "/cache/img/T/T_SteelWateringCan.png",
                "gold_cost": 5000,
                "materials": "5x Iron Bar",
                "perks": "Water 5 tiles in a line.",
            },
            {
                "level": 3,
                "name": "Gold Watering Can",
                "icon": "/cache/img/T/T_GoldWateringCan.png",
                "gold_cost": 10000,
                "materials": "5x Gold Bar",
                "perks": "Water 3x3 area.",
            },
            {
                "level": 4,
                "name": "Iridium Watering Can",
                "icon": "/cache/img/T/T_IridiumWateringCan.png",
                "gold_cost": 25000,
                "materials": "5x Iridium Bar",
                "perks": "Water 6x3 area.",
            },
        ],
    },
    "TrashCan": {
        "name": "Trash Can",
        "tiers": [
            {
                "level": 0,
                "name": "Trash Can",
                "icon": "/cache/img/T/T_TrashCan.png",
                "gold_cost": 0,
                "materials": None,
                "perks": "Reclaims 0% item value.",
            },
            {
                "level": 1,
                "name": "Copper Trash Can",
                "icon": "/cache/img/T/T_CopperTrashCan.png",
                "gold_cost": 1000,
                "materials": "5x Copper Bar",
                "perks": "Reclaims 15% item value.",
            },
            {
                "level": 2,
                "name": "Steel Trash Can",
                "icon": "/cache/img/T/T_SteelTrashCan.png",
                "gold_cost": 2500,
                "materials": "5x Iron Bar",
                "perks": "Reclaims 30% item value.",
            },
            {
                "level": 3,
                "name": "Gold Trash Can",
                "icon": "/cache/img/T/T_GoldTrashCan.png",
                "gold_cost": 5000,
                "materials": "5x Gold Bar",
                "perks": "Reclaims 45% item value.",
            },
            {
                "level": 4,
                "name": "Iridium Trash Can",
                "icon": "/cache/img/T/T_IridiumTrashCan.png",
                "gold_cost": 12500,
                "materials": "5x Iridium Bar",
                "perks": "Reclaims 60% item value.",
            },
        ],
    },
}


def _parse_material_requirement(mat_str: str | None) -> tuple[int, str | None]:
    """Parses a material requirement string like "5x Copper Bar" into (count, item_name)."""
    if not mat_str:
        return 0, None

    match = re.match(r"^(\d+)\s*x\s*(.+)$", mat_str.strip(), re.IGNORECASE)
    if match:
        count = int(match.group(1))
        name = match.group(2).strip()
        return count, name

    return 0, mat_str.strip()


def parse_tools(
    xml_root: Any,
    player_money: int = 0,
    material_totals: list[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Parses tool upgrade levels and blacksmith processing status from XML."""
    start_time = time.perf_counter()

    if xml_root is None:
        logger.warning("xml_root is None. Returning default tools structure.")
        return {
            "upgradeable": [],
            "watering_can": None,
            "scythe": None,
        }

    catalog = get_tools_catalog()
    upgradeable_catalog = catalog.get("upgradeable_tools") or DEFAULT_UPGRADEABLE_TOOLS

    tool_levels = {tool_key: 0 for tool_key in upgradeable_catalog}

    chest_stock = {
        item["name"]: item["count"]
        for item in (material_totals or [])
        if "name" in item and "count" in item
    }

    player = xml_root.find("player") if hasattr(xml_root, "find") else None

    days_left = 0
    upgrading_tool_type = None

    if player is not None:
        days_elem = player.find("daysLeftForToolUpgrade")
        if days_elem is not None and days_elem.text:
            try:
                days_left = int(days_elem.text)
            except ValueError:
                days_left = 0

        tool_upgrading_node = player.find("toolBeingUpgraded")
        if tool_upgrading_node is not None:
            upgrading_item = tool_upgrading_node.find("Item")
            if upgrading_item is not None:
                item_type = (
                    upgrading_item.get("{http://www.w3.org/2001/XMLSchema-instance}type") or ""
                )
                item_name = upgrading_item.findtext("name") or ""
                upgrading_tool_type = item_type or item_name

        trash_lvl_elem = player.find("trashCanLevel")
        if trash_lvl_elem is not None and trash_lvl_elem.text:
            try:
                tool_levels["TrashCan"] = int(trash_lvl_elem.text)
            except (ValueError, KeyError):
                pass

    items = xml_root.findall(".//Item") if hasattr(xml_root, "findall") else []

    for item in items:
        if item.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true":
            continue

        item_type = item.get("{http://www.w3.org/2001/XMLSchema-instance}type") or ""
        item_name = item.findtext("name") or ""

        for tool_key, tool_info in upgradeable_catalog.items():
            is_tool_match = False
            if item_type == tool_key:
                is_tool_match = True
            elif item_type in ("Tool", "GenericTool", "SpecialItem"):
                valid_names = [tool_key, tool_info.get("name", "")] + [
                    t["name"]
                    for t in tool_info.get("tiers", [])
                    if isinstance(t, dict) and "name" in t
                ]
                if item_name in valid_names:
                    is_tool_match = True

            if is_tool_match:
                level_text = item.findtext("upgradeLevel")
                if level_text is not None:
                    try:
                        level = int(level_text)
                        tool_levels[tool_key] = max(tool_levels.get(tool_key, 0), level)
                    except ValueError:
                        pass

    tools_data: list[dict[str, Any]] = []

    for tool_key, tool_info in upgradeable_catalog.items():
        tiers = tool_info.get("tiers", []) if isinstance(tool_info, dict) else []
        if not tiers:
            continue

        current_lvl = tool_levels.get(tool_key, 0)
        max_lvl = tiers[-1]["level"] if tiers else 0
        current_lvl = min(current_lvl, max_lvl)

        current_tier_data = next(
            (t for t in tiers if t["level"] == current_lvl),
            tiers[0],
        )

        is_upgrading = (
            (days_left > 0)
            and (upgrading_tool_type is not None)
            and (tool_key in upgrading_tool_type)
        )
        is_max = current_lvl >= max_lvl

        status = "upgrading" if is_upgrading else ("maxed" if is_max else "ready")
        icon_file = current_tier_data.get("icon", "")

        next_tier_data = None
        if not is_max:
            raw_next = next((t for t in tiers if t["level"] == current_lvl + 1), None)
            if raw_next:
                gold_cost = raw_next.get("gold_cost", 0)
                has_enough_gold = player_money >= gold_cost
                mat_text = raw_next.get("materials")
                req_count, req_mat_name = _parse_material_requirement(mat_text)

                available_count = chest_stock.get(req_mat_name, 0) if req_mat_name else 0
                has_enough_materials = available_count >= req_count if req_mat_name else True
                can_upgrade = has_enough_gold and has_enough_materials

                next_icon_file = raw_next.get("icon", "")
                next_tier_data = {
                    "level": raw_next["level"],
                    "name": raw_next["name"],
                    "gold_cost": gold_cost,
                    "has_enough_gold": has_enough_gold,
                    "materials": mat_text,
                    "materials_text": mat_text,
                    "material_name": req_mat_name,
                    "required_count": req_count,
                    "available_count": available_count,
                    "has_enough_materials": has_enough_materials,
                    "can_upgrade": can_upgrade,
                    "icon_url": f"/{next_icon_file.lstrip('/')}" if next_icon_file else None,
                }

        tools_data.append(
            {
                "key": tool_key,
                "display_name": tool_info.get("name", tool_key)
                if isinstance(tool_info, dict)
                else tool_key,
                "current_level": current_lvl,
                "max_level": max_lvl,
                "status": status,
                "days_left": days_left if is_upgrading else 0,
                "is_max": is_max,
                "current_tier": {
                    "name": current_tier_data["name"],
                    "perks": current_tier_data.get("perks", ""),
                    "icon_url": f"/{icon_file.lstrip('/')}" if icon_file else None,
                },
                "next_tier": next_tier_data,
            }
        )

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(f"Parsed tools in {elapsed_ms:.2f}ms")

    return {
        "upgradeable": tools_data,
        "watering_can": next((t for t in tools_data if t["key"] == "WateringCan"), None),
        "scythe": None,
    }
    