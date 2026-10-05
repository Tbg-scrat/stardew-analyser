# -*- coding: utf-8 -*-
# tests/modules/test_social.py

import xml.etree.ElementTree as ET
from data.data_loader import VILLAGERS_CATALOG
from src.modules.social import format_wiki_filename, get_loved_gifts, parse_social


def test_format_wiki_filename():
    """Verifies image URL formatting for Stardew Wiki conventions."""
    assert format_wiki_filename("Abigail") == "Abigail"
    assert format_wiki_filename("Axe Master") == "Axe_Master"
    assert format_wiki_filename("Governor's Feast") == "Governor%27s_Feast"


def test_get_loved_gifts():
    """Verifies loved gifts retrieval for known and unknown villagers."""
    gifts = get_loved_gifts("Abigail")
    assert isinstance(gifts, list)

    unknown_gifts = get_loved_gifts("NonExistentNPC")
    assert unknown_gifts == []


def test_parse_social_none_and_missing_nodes():
    """Verifies edge cases when player node or friendshipData node is missing."""
    assert parse_social(None) == []

    empty_player = ET.fromstring("<player></player>")
    assert parse_social(empty_player) == []


def test_parse_social_filtering_and_sorting():
    """Verifies internal NPC filtering, sorting by points, and heart capping logic."""
    ignored_list = VILLAGERS_CATALOG.get("ignored_npcs", [])
    ignored_npc = ignored_list[0] if ignored_list else "Gunther"

    xml_data = f"""
    <player>
        <friendshipData>
            <item>
                <key><string>Abigail</string></key>
                <value>
                    <Friendship>
                        <Points>2500</Points>
                        <TalkedToToday>true</TalkedToToday>
                        <GiftsThisWeek>2</GiftsThisWeek>
                        <Status>Dating</Status>
                    </Friendship>
                </value>
            </item>
            <item>
                <key><string>Haley</string></key>
                <value>
                    <Friendship>
                        <Points>2500</Points>
                        <TalkedToToday>false</TalkedToToday>
                        <GiftsThisWeek>0</GiftsThisWeek>
                        <Status>Friendly</Status>
                    </Friendship>
                </value>
            </item>
            <item>
                <key><string>George</string></key>
                <value>
                    <Friendship>
                        <Points>3500</Points>
                        <TalkedToToday>true</TalkedToToday>
                        <GiftsThisWeek>1</GiftsThisWeek>
                        <Status>Married</Status>
                    </Friendship>
                </value>
            </item>
            <item>
                <key><string>Linus</string></key>
                <value>
                    <Friendship>
                        <Points></Points>
                    </Friendship>
                </value>
            </item>
            <item>
                <key><string>{ignored_npc}</string></key>
                <value><Friendship><Points>500</Points></Friendship></value>
            </item>
            <item>
                <key><string>Henchman_Guard</string></key>
                <value><Friendship><Points>500</Points></Friendship></value>
            </item>
            <item>
                <key><string>Granter_Quest</string></key>
                <value><Friendship><Points>500</Points></Friendship></value>
            </item>
            <item>
                <key><string></string></key>
                <value><Friendship><Points>500</Points></Friendship></value>
            </item>
        </friendshipData>
    </player>
    """
    player = ET.fromstring(xml_data)
    results = parse_social(player)

    npc_names = [r["name"] for r in results]
    assert ignored_npc not in npc_names
    assert "Henchman_Guard" not in npc_names
    assert "Granter_Quest" not in npc_names
    assert len(results) == 4

    # Verify descending point sorting (George 3500 -> Abigail 2500 -> Haley 2500 -> Linus 0)
    assert results[0]["name"] == "George"
    assert results[0]["status"] == "Spouse"
    assert results[0]["hearts"] == 14
    assert results[0]["max_hearts"] == 14
    assert results[0]["is_spouse"] is True

    # Abigail (Datable + Dating): 2500 points = 10 hearts (max 10)
    abigail = next(r for r in results if r["name"] == "Abigail")
    assert abigail["status"] == "Datable"
    assert abigail["hearts"] == 10
    assert abigail["max_hearts"] == 10
    assert abigail["talked_today"] is True
    assert abigail["gifts_this_week"] == 2

    # Haley (Datable + Not Dating): 2500 points capped at 8 hearts (max 8)
    haley = next(r for r in results if r["name"] == "Haley")
    assert haley["status"] == "Datable"
    assert haley["hearts"] == 8
    assert haley["max_hearts"] == 8
    assert haley["talked_today"] is False

    # Linus (Non-datable, missing/empty points text defaults to 0)
    linus = next(r for r in results if r["name"] == "Linus")
    assert linus["points"] == 0
    assert linus["hearts"] == 0
    assert linus["max_hearts"] == 10
    assert linus["status"] == "Normal"
    