import logging
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List

from src.core.reference_data import get_tools_catalog

logger = logging.getLogger(__name__)


def parse_tools(xml_root: ET.Element) -> Dict[str, Any]:
    """
    Parses tool upgrade levels, blacksmith processing status, and scythe discovery
    from the save file XML root.
    """
    start_time = time.perf_counter()
    catalog = get_tools_catalog()

    upgradeable_catalog = catalog.get("upgradeable_tools", {})
    special_catalog = catalog.get("special_tools", {})

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

    # 2. Track tool levels and scythe stages across inventory, chests, and blacksmith
    tool_levels = {tool_key: 0 for tool_key in upgradeable_catalog}
    scythe_tier_found = 0  # 0: Basic, 1: Golden, 2: Iridium

    for item in xml_root.findall(".//Item"):
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
                valid_names = [tool_key, tool_info.get("name", "")] + [t["name"] for t in tool_info.get("tiers", [])]
                if item_name in valid_names:
                    is_tool_match = True

            if is_tool_match:
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

    # 3. Build upgradeable tools data structure
    tools_data: List[Dict[str, Any]] = []

    for tool_key, tool_info in upgradeable_catalog.items():
        current_lvl = tool_levels.get(tool_key, 0)
        tiers = tool_info.get("tiers", [])
        max_lvl = tiers[-1]["level"] if tiers else 0

        current_lvl = min(current_lvl, max_lvl)
        current_tier_data = next((t for t in tiers if t["level"] == current_lvl), tiers[0])

        is_upgrading = (days_left > 0) and (upgrading_tool_type is not None) and (tool_key in upgrading_tool_type)
        is_max = (current_lvl >= max_lvl)

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
                next_icon_file = raw_next.get("icon")
                next_tier_data = {
                    "level": raw_next["level"],
                    "name": raw_next["name"],
                    "gold_cost": raw_next["gold_cost"],
                    "materials": raw_next["materials"],
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

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.debug("Parsed tools in %.2fms", elapsed_ms)

    return {
        "upgradeable": tools_data,
        "scythe": scythe_data,
    }
    