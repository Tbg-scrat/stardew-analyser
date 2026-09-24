# tests/test_achievements.py

import xml.etree.ElementTree as ET
from src.modules.achievements import parse_achievements


def test_achievements_unlock_from_xml():
    player_xml = ET.fromstring("""
    <player>
        <achievements>
            <int>0</int>
            <int>5</int>
        </achievements>
    </player>
    """)
    result = parse_achievements(player_xml)
    assert result["unlocked_count"] >= 2
    unlocked_ids = [a["id"] for a in result["list"] if a["unlocked"]]
    assert 0 in unlocked_ids
    assert 5 in unlocked_ids


def test_monoculture_override_triggers_unlock():
    player_xml = ET.fromstring("<player><achievements></achievements></player>")
    shipped_mock = [
        {"name": "Cranberries", "count": 310, "is_monoculture": True}
    ]
    result = parse_achievements(player_xml, shipped_items=shipped_mock)
    monoculture = next(a for a in result["list"] if a["name"] == "Monoculture")
    assert monoculture["unlocked"] is True
    assert monoculture["progress_current"] == 300
