# -*- coding: utf-8 -*-
# tests/modules/test_shipping.py

import xml.etree.ElementTree as ET
from src.modules.shipping import (
    format_wiki_filename,
    get_formatted_shipping,
    parse_shipping,
)


def test_format_wiki_filename():
    """Verifies item name formatting for wiki icon URLs."""
    assert format_wiki_filename("") == ""
    assert format_wiki_filename("Sweet Gem Berry") == "Sweet_Gem_Berry"


def test_parse_shipping_none_and_empty():
    """Verifies fallback when player or basicShipped node is missing."""
    assert parse_shipping(None) == {}

    empty_player = ET.fromstring("<player></player>")
    assert parse_shipping(empty_player) == {}


def test_parse_shipping_valid_and_invalid_counts():
    """Verifies parsing of shipped item quantities and non-integer fallbacks."""
    xml_data = """
    <player>
        <basicShipped>
            <item>
                <key><string>(O)24</string></key>
                <value><int>15</int></value>
            </item>
            <item>
                <key><string>190</string></key>
                <value><int>bad_int</int></value>
            </item>
        </basicShipped>
    </player>
    """
    player = ET.fromstring(xml_data)
    shipped = parse_shipping(player)

    assert shipped.get("(O)24") == 15
    assert shipped.get("190") == 0


def test_get_formatted_shipping_catalog_merge():
    """Verifies catalog enrichment, polyculture/monoculture flags, and status flags."""
    xml_data = """
    <player>
        <basicShipped>
            <item>
                <key><string>24</string></key>
                <value><int>15</int></value>
            </item>
        </basicShipped>
    </player>
    """
    player = ET.fromstring(xml_data)
    custom_catalog = {
        "24": {
            "name": "Parsnip",
            "achievement_required": True,
            "is_polyculture": True,
            "is_monoculture": True,
        },
        "190": {
            "name": "Cauliflower",
            "achievement_required": True,
            "is_polyculture": True,
            "is_monoculture": False,
        },
        "corrupted_item": 12345,
    }

    results = get_formatted_shipping(player, catalog=custom_catalog)

    assert len(results) == 2

    parsnip = next(item for item in results if item["id"] == "24")
    assert parsnip["count"] == 15
    assert parsnip["is_unlocked"] is True
    assert parsnip["status"] == "shipped"
    assert parsnip["is_polyculture"] is True
    assert parsnip["is_monoculture"] is True

    cauliflower = next(item for item in results if item["id"] == "190")
    assert cauliflower["count"] == 0
    assert cauliflower["is_unlocked"] is False
    assert cauliflower["status"] == "not_shipped"
    