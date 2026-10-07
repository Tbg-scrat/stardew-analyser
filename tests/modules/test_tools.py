# tests/test_tools.py

from unittest.mock import patch
import xml.etree.ElementTree as ET
from src.modules.tools import parse_tools


MOCK_TOOLS_CATALOG = {
    "upgradeable_tools": {
        "Axe": {
            "name": "Axe",
            "tiers": [
                {"level": 0, "name": "Axe", "icon": "/cache/img/items/T_105.png", "gold_cost": 0, "materials": None, "perks": "Chops trees."},
                {"level": 1, "name": "Copper Axe", "icon": "/cache/img/items/T_111.png", "gold_cost": 2000, "materials": "5x Copper Bar", "perks": "Chops stumps."},
                {"level": 2, "name": "Steel Axe", "icon": "/cache/img/items/T_117.png", "gold_cost": 5000, "materials": "5x Iron Bar", "perks": "Chops logs."},
                {"level": 3, "name": "Gold Axe", "icon": "/cache/img/items/T_126.png", "gold_cost": 10000, "materials": "5x Gold Bar", "perks": "Chops faster."},
                {"level": 4, "name": "Iridium Axe", "icon": "/cache/img/items/T_132.png", "gold_cost": 25000, "materials": "5x Iridium Bar", "perks": "Max efficiency."}
            ]
        },
        "Pickaxe": {
            "name": "Pickaxe",
            "tiers": [
                {"level": 0, "name": "Pickaxe", "icon": "pickaxe.png", "gold_cost": 0, "materials": None, "perks": "Breaks small rocks."},
                {"level": 1, "name": "Copper Pickaxe", "icon": "copper_pickaxe.png", "gold_cost": 2000, "materials": "5x Copper Bar", "perks": "Breaks mine rocks."}
            ]
        }
    },
    "special_tools": {
        "Scythe": {
            "name": "Scythe",
            "stages": [
                {"id": "Scythe", "name": "Basic Scythe", "icon": "scythe.png", "tier": 0, "hint": "Starter tool."},
                {"id": "Golden Scythe", "name": "Golden Scythe", "icon": "golden_scythe.png", "tier": 1, "hint": "Found in Quarry Mine."},
                {"id": "Iridium Scythe", "name": "Iridium Scythe", "icon": "iridium_scythe.png", "tier": 2, "hint": "Unlocked in Mastery Cave."}
            ]
        }
    }
}


def test_parse_tools_inventory_levels():
    """Verifies that tool upgrade levels are correctly extracted from player inventory."""
    xml_data = """
    <SaveGame>
        <player>
            <items>
                <Item xsi:type="Axe" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <upgradeLevel>2</upgradeLevel>
                </Item>
            </items>
        </player>
    </SaveGame>
    """
    root = ET.fromstring(xml_data.strip())

    with patch("src.modules.tools.get_tools_catalog", return_value=MOCK_TOOLS_CATALOG):
        result = parse_tools(root)

    axe = next(t for t in result["upgradeable"] if t["key"] == "Axe")
    assert axe["current_level"] == 2
    assert axe["status"] == "ready"
    assert axe["current_tier"]["name"] == "Steel Axe"
    assert axe["next_tier"]["name"] == "Gold Axe"
    assert axe["next_tier"]["gold_cost"] == 10000
    assert axe["next_tier"]["materials"] == "5x Gold Bar"
    assert axe["next_tier"]["icon_url"] == "cache/img/items/T_126.png"


def test_parse_tools_upgrading_at_blacksmith():
    """Verifies that tools being processed at Clint's shop reflect the upgrading status and days left."""
    xml_data = """
    <SaveGame>
        <player>
            <daysLeftForToolUpgrade>2</daysLeftForToolUpgrade>
            <toolBeingUpgraded>
                <Item xsi:type="Pickaxe" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <upgradeLevel>0</upgradeLevel>
                </Item>
            </toolBeingUpgraded>
        </player>
    </SaveGame>
    """
    root = ET.fromstring(xml_data.strip())

    with patch("src.modules.tools.get_tools_catalog", return_value=MOCK_TOOLS_CATALOG):
        result = parse_tools(root)

    pickaxe = next(t for t in result["upgradeable"] if t["key"] == "Pickaxe")
    assert pickaxe["status"] == "upgrading"
    assert pickaxe["days_left"] == 2


def test_parse_tools_scythe_progression():
    """Verifies scythe detection and progression hinting (Basic -> Golden -> Iridium)."""
    xml_data = """
    <SaveGame>
        <player>
            <items>
                <Item xsi:type="MeleeWeapon" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <name>Golden Scythe</name>
                </Item>
            </items>
        </player>
    </SaveGame>
    """
    root = ET.fromstring(xml_data.strip())

    with patch("src.modules.tools.get_tools_catalog", return_value=MOCK_TOOLS_CATALOG):
        result = parse_tools(root)

    scythe = result["scythe"]
    assert scythe["current_stage"]["name"] == "Golden Scythe"
    assert scythe["is_max"] is False
    assert scythe["next_stage"]["name"] == "Iridium Scythe"
    assert "Mastery Cave" in scythe["next_stage"]["hint"]


def test_parse_tools_max_level():
    """Verifies that max-level tools do not populate next_tier and set status to maxed."""
    xml_data = """
    <SaveGame>
        <player>
            <items>
                <Item xsi:type="Axe" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <upgradeLevel>4</upgradeLevel>
                </Item>
            </items>
        </player>
    </SaveGame>
    """
    root = ET.fromstring(xml_data.strip())

    with patch("src.modules.tools.get_tools_catalog", return_value=MOCK_TOOLS_CATALOG):
        result = parse_tools(root)

    axe = next(t for t in result["upgradeable"] if t["key"] == "Axe")
    assert axe["current_level"] == 4
    assert axe["is_max"] is True
    assert axe["status"] == "maxed"
    assert axe["next_tier"] is None
    