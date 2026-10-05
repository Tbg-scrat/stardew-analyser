# src/modules/tools.py
import logging
import re
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

from src.core.reference_data import get_tools_catalog

logger = logging.getLogger(__name__)


def _parse_material_requirement(mat_str: Optional[str]) -> Tuple[int, Optional[str]]:
    """
    Parses a material requirement string like "5x Copper Bar" into (count, item_name).
    Returns (0, None) if mat_str is None or empty.
    """
    if not mat_str:
        return 0, None

    match = re.match(r"^(\d+)\s*x\s*(.+)$", mat_str.strip(), re.IGNORECASE)
    if match:
        count = int(match.group(1))
        name = match.group(2).strip()
        return count, name

    return 0, mat_str.strip()


def parse_tools(
    xml_root: ET.Element,
    player_money: int = 0,
    material_totals: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Parses tool upgrade levels, blacksmith processing status, and scythe discovery
    from the save file XML root, verifying upgrade gold and chest material requirements.
    """
    start_time = time.perf_counter()

    if xml_root is None:
        logger.warning("xml_root is None. Returning default tools structure.")
        return {
            "upgradeable": [],
            "scythe": {
                "name": "Scythe",
                "current_stage": {
                    "name": "Basic Scythe",
                    "tier": 0,
                    "icon_url": "static/img/tools/scythe.png",
                    "hint": "Starter tool.",
                },
                "is_max": False,
                "next_stage": None,
            },
        }

    catalog = get_tools_catalog()
    upgradeable_catalog = catalog.get("upgradeable_tools", {})
    special_catalog = catalog.get("special_tools", {})

    # Build chest material stock lookup dictionary
    chest_stock = {
        item["name"]: item["count"]
        for item in (material_totals or [])
        if "name" in item and "count" in item
    }
    logger.debug(
        f"Evaluating tool upgrades against {player_money:,}g funds and {len(chest_stock)} chest material types"
    )

    player = xml_root.find("player")

    # 1. Check Clint's blacksmith upgrade status
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
                item_type = upgrading_item.get("{http://www.w3.org/2001/XMLSchema-instance}type") or ""
                item_name = upgrading_item.findtext("name") or ""
                upgrading_tool_type = item_type or item_name

        if days_left > 0 and upgrading_tool_type:
            logger.debug(
                f"Active blacksmith upgrade detected at Clint's: {upgrading_tool_type} ({days_left}d remaining)"
            )
    else:
        logger.debug("No <player> node found under save XML root")

    # 2. Track tool levels and scythe stages across inventory, chests, and blacksmith
    tool_levels = {tool_key: 0 for tool_key in upgradeable_catalog}
    scythe_tier_found = 0  # 0: Basic, 1: Golden, 2: Iridium

    items = xml_root.findall(".//Item")
    scanned_items_count = len(items)
    matched_tools_count = 0

    for item in items:
        if item.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true":
            continue

        item_type = item.get("{http://www.w3.org/2001/XMLSchema-instance}type") or ""
        item_name = item.findtext("name") or ""

        # Precise matching for upgradeable tools
        for tool_key, tool_info in upgradeable_catalog.items():
            is_tool_match = False

            if item_type == tool_key:
                is_tool_match = True
            elif item_type in ("Tool", "GenericTool", "SpecialItem"):
                valid_names = [tool_key, tool_info.get("name", "")] + [
                    t["name"] for t in tool_info.get("tiers", [])
                ]
                if item_name in valid_names:
                    is_tool_match = True

            if is_tool_match:
                matched_tools_count += 1
                level_text = item.findtext("upgradeLevel")
                if level_text is not None:
                    try:
                        level = int(level_text)
                        if level > tool_levels[tool_key]:
                            tool_levels[tool_key] = level
                    except ValueError:
                        pass

        # Check Scythes
        if "Iridium Scythe" in item_name:
            scythe_tier_found = max(scythe_tier_found, 2)
        elif "Golden Scythe" in item_name:
            scythe_tier_found = max(scythe_tier_found, 1)
        elif "Scythe" in item_name or "Scythe" in item_type:
            scythe_tier_found = max(scythe_tier_found, 0)

    logger.debug(
        f"Evaluated {scanned_items_count} <Item> nodes across save: {matched_tools_count} tool matches processed"
    )

    # 3. Build upgradeable tools data structure and check requirements
    tools_data: List[Dict[str, Any]] = []
    maxed_count = 0
    ready_to_upgrade_count = 0

    for tool_key, tool_info in upgradeable_catalog.items():
        current_lvl = tool_levels.get(tool_key, 0)
        tiers = tool_info.get("tiers", [])
        max_lvl = tiers[-1]["level"] if tiers else 0

        current_lvl = min(current_lvl, max_lvl)
        current_tier_data = next((t for t in tiers if t["level"] == current_lvl), tiers[0])

        is_upgrading = (days_left > 0) and (upgrading_tool_type is not None) and (tool_key in upgrading_tool_type)
        is_max = (current_lvl >= max_lvl)

        if is_max:
            maxed_count += 1

        if is_upgrading:
            status = "upgrading"
        elif is_max:
            status = "maxed"
        else:
            status = "ready"

        icon_file = current_tier_data.get("icon")
        icon_url = f"static/img/tools/{icon_file}" if icon_file else None

        next_tier_data = None
        if not is_max:
            raw_next = next((t for t in tiers if t["level"] == current_lvl + 1), None)
            if raw_next:
                gold_cost = raw_next.get("gold_cost", 0)
                has_enough_gold = player_money >= gold_cost
                mat_text = raw_next.get("materials")
                req_count, req_mat_name = _parse_material_requirement(mat_text)

                if req_mat_name:
                    available_count = chest_stock.get(req_mat_name, 0)
                    has_enough_materials = available_count >= req_count
                else:
                    available_count = 0
                    has_enough_materials = True

                can_upgrade = has_enough_gold and has_enough_materials
                if can_upgrade and status != "upgrading":
                    ready_to_upgrade_count += 1

                logger.debug(
                    f"Tool '{tool_key}' -> Next: {raw_next['name']} | Gold: {gold_cost:,}g "
                    f"({'OK' if has_enough_gold else 'NEEDS FUNDS'}) | Material: "
                    f"{req_count}x {req_mat_name or 'None'} (Chests: {available_count} | "
                    f"{'OK' if has_enough_materials else 'SHORT'}) -> Can Upgrade: {can_upgrade}"
                )

                next_icon_file = raw_next.get("icon")
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
                    "icon_url": f"static/img/tools/{next_icon_file}" if next_icon_file else None,
                }

        tools_data.append({
            "key": tool_key,
            "display_name": tool_info.get("name", tool_key),
            "current_level": current_lvl,
            "max_level": max_lvl,
            "status": status,
            "days_left": days_left if is_upgrading else 0,
            "is_max": is_max,
            "current_tier": {
                "name": current_tier_data["name"],
                "perks": current_tier_data["perks"],
                "icon_url": icon_url,
            },
            "next_tier": next_tier_data,
        })

    logger.debug(
        f"Tool evaluation completed: {maxed_count}/{len(upgradeable_catalog)} maxed, "
        f"{ready_to_upgrade_count} ready to upgrade at Clint's"
    )

    # 4. Build Scythe progression structure
    scythe_info = special_catalog.get("Scythe", {})
    stages = scythe_info.get("stages", [])
    current_scythe_stage = stages[min(scythe_tier_found, len(stages) - 1)]
    next_scythe_stage = stages[scythe_tier_found + 1] if scythe_tier_found + 1 < len(stages) else None

    scythe_data = {
        "name": scythe_info.get("name", "Scythe"),
        "current_stage": {
            "name": current_scythe_stage["name"],
            "tier": current_scythe_stage["tier"],
            "icon_url": f"static/img/tools/{current_scythe_stage['icon']}" if current_scythe_stage.get("icon") else None,
            "hint": current_scythe_stage["hint"],
        },
        "is_max": (scythe_tier_found >= len(stages) - 1),
        "next_stage": {
            "name": next_scythe_stage["name"],
            "icon_url": f"static/img/tools/{next_scythe_stage['icon']}" if next_scythe_stage.get("icon") else None,
            "hint": next_scythe_stage["hint"],
        } if next_scythe_stage else None,
    }

    logger.debug(f"Resolved Scythe progression stage: {current_scythe_stage['name']} (Tier {scythe_tier_found})")

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(f"Parsed tools module in {elapsed_ms:.2f}ms")

    return {
        "upgradeable": tools_data,
        "scythe": scythe_data,
    }
    