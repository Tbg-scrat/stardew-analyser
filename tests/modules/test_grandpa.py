# tests/test_grandpa.py
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import pytest
from src.modules.grandpa import parse_grandpa_data, _calculate_candles


def _build_mock_xml(
    earned=0,
    skills=(0, 0, 0, 0, 0),
    house_level=0,
    spouse="",
    pet_pts=0,
    keys=False,
    mail=None,
):
    mail = mail or []
    root = ET.Element("SaveGame")
    
    # Pet location setup
    loc = ET.SubElement(root, "locations")
    gloc = ET.SubElement(loc, "GameLocation")
    chars = ET.SubElement(gloc, "characters")
    pet = ET.SubElement(chars, "NPC")
    pet.set("{http://www.w3.org/2001/XMLSchema-instance}type", "Cat")
    ET.SubElement(pet, "friendshipTowardFarmer").text = str(pet_pts)

    player = ET.Element("player")
    ET.SubElement(player, "totalMoneyEarned").text = str(earned)
    ET.SubElement(player, "farmingLevel").text = str(skills[0])
    ET.SubElement(player, "miningLevel").text = str(skills[1])
    ET.SubElement(player, "combatLevel").text = str(skills[2])
    ET.SubElement(player, "foragingLevel").text = str(skills[3])
    ET.SubElement(player, "fishingLevel").text = str(skills[4])
    ET.SubElement(player, "houseUpgradeLevel").text = str(house_level)
    ET.SubElement(player, "spouse").text = spouse
    ET.SubElement(player, "hasRustyKey").text = "true" if keys else "false"
    ET.SubElement(player, "hasSkullKey").text = "true" if keys else "false"

    mail_node = ET.SubElement(player, "mailReceived")
    for m in mail:
        ET.SubElement(mail_node, "string").text = m

    return root, player


def test_candle_scoring_thresholds():
    assert _calculate_candles(0) == 1
    assert _calculate_candles(3) == 1
    assert _calculate_candles(4) == 2
    assert _calculate_candles(7) == 2
    assert _calculate_candles(8) == 3
    assert _calculate_candles(11) == 3
    assert _calculate_candles(12) == 4
    assert _calculate_candles(21) == 4


def test_grandpa_data_minimum_score():
    root, player = _build_mock_xml()
    res = parse_grandpa_data(root, player)

    assert res["total_score"] == 0
    assert res["candles"] == 1
    assert res["statue_unlocked"] is False
    assert len(res["categories"]) == 5


def test_grandpa_data_max_earnings_and_skills():
    root, player = _build_mock_xml(earned=1_500_000, skills=(10, 10, 10, 10, 10))
    res = parse_grandpa_data(root, player)

    earnings_cat = next(c for c in res["categories"] if c["id"] == "earnings")
    skills_cat = next(c for c in res["categories"] if c["id"] == "skills")

    assert earnings_cat["score"] == 7
    assert skills_cat["score"] == 2
    assert res["total_score"] == 9
    assert res["candles"] == 3


def test_grandpa_statue_unlocked_threshold():
    # 7 earnings + 2 skills + 2 keys + 1 pet = 12 pts (4 candles)
    root, player = _build_mock_xml(
        earned=1_000_000,
        skills=(10, 10, 10, 10, 10),
        pet_pts=1000,
        keys=True,
    )
    res = parse_grandpa_data(root, player)

    assert res["total_score"] == 12
    assert res["candles"] == 4
    assert res["statue_unlocked"] is True


def test_grandpa_none_handling():
    res = parse_grandpa_data(None, None)
    assert res["total_score"] == 0
    assert res["candles"] == 1
    assert res["statue_unlocked"] is False
    