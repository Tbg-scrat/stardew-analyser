# -*- coding: utf-8 -*-
# tests/modules/test_player.py

import xml.etree.ElementTree as ET
from src.modules.player import parse_player


def test_parse_player_none():
    """Verifies return value when player node is None."""
    data = parse_player(None)
    assert data == {
        "farmer": "Unknown",
        "farm": "Unknown",
        "money": 0,
        "total_earned": 0,
    }


def test_parse_player_basic_attributes():
    """Verifies extraction of farmer name, farm name, money, and skill levels."""
    xml_data = """
    <player>
        <name>Farmer Bob</name>
        <farmName>Sunnyside</farmName>
        <money>150000</money>
        <totalMoneyEarned>500000</totalMoneyEarned>
        <farmingLevel>10</farmingLevel>
        <miningLevel>8</miningLevel>
        <combatLevel>7</combatLevel>
        <foragingLevel>9</foragingLevel>
        <fishingLevel>6</fishingLevel>
    </player>
    """
    player = ET.fromstring(xml_data)
    data = parse_player(player)

    assert data.get("farmer") == "Farmer Bob"
    assert data.get("farm") == "Sunnyside"
    assert data.get("money") == 150000
    assert data.get("total_earned") == 500000
    