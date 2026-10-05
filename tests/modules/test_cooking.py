# -*- coding: utf-8 -*-
# tests/modules/test_cooking.py

import xml.etree.ElementTree as ET
from src.modules.cooking import (
    format_wiki_filename,
    get_formatted_cooking,
    parse_cooking,
)


def test_format_wiki_filename():
    """Verifies string cleaning for Stardew Valley Wiki conventions."""
    assert format_wiki_filename("") == ""
    assert format_wiki_filename("Fried Egg") == "Fried_Egg"
    assert format_wiki_filename("Miner's Treat") == "Miner%27s_Treat"


def test_parse_cooking_none_and_empty():
    """Verifies fallback behavior when player or recipesCooked node is missing."""
    assert parse_cooking(None) == {}

    empty_player = ET.fromstring("<player></player>")
    assert parse_cooking(empty_player) == {}


def test_parse_cooking_valid_and_malformed_entries():
    """Verifies parsing of (O) prefixed keys, valid counts, and non-integer text fallbacks."""
    xml_data = """
    <player>
        <recipesCooked>
            <item>
                <key><string>(O)194</string></key>
                <value><int>5</int></value>
            </item>
            <item>
                <key><string>253</string></key>
                <value><int>invalid_count</int></value>
            </item>
            <item>
                <key></key>
                <value><int>10</int></value>
            </item>
        </recipesCooked>
    </player>
    """
    player = ET.fromstring(xml_data)
    cooked = parse_cooking(player)

    assert cooked.get("194") == 5
    assert cooked.get("253") == 0
    assert "" not in cooked


def test_get_formatted_cooking_catalog_merge():
    """Verifies catalog merging, unlock status determination, and list sorting by name."""
    xml_data = """
    <player>
        <recipesCooked>
            <item>
                <key><string>194</string></key>
                <value><int>3</int></value>
            </item>
        </recipesCooked>
    </player>
    """
    player = ET.fromstring(xml_data)
    custom_catalog = {
        "194": {"name": "Fried Egg", "image": "egg.png"},
        "253": {"name": "Triple Shot Espresso", "image": "espresso.png"},
        "invalid_key": "not_a_dict_catalog_item",
    }

    results = get_formatted_cooking(player, catalog=custom_catalog)

    assert len(results) == 2
    # Alphabetical sorting check: Fried Egg comes before Triple Shot Espresso
    assert results[0]["name"] == "Fried Egg"
    assert results[0]["count"] == 3
    assert results[0]["is_unlocked"] is True
    assert results[0]["status"] == "cooked"

    assert results[1]["name"] == "Triple Shot Espresso"
    assert results[1]["count"] == 0
    assert results[1]["is_unlocked"] is False
    assert results[1]["status"] == "not_cooked"
