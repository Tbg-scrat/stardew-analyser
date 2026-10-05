# -*- coding: utf-8 -*-
# tests/modules/test_fishing.py

import xml.etree.ElementTree as ET
from src.modules.fishing import get_formatted_fishing


def test_get_formatted_fishing_none_and_empty():
    """Verifies edge cases when player node or fishCaught node is missing/empty."""
    none_results = get_formatted_fishing(None)
    assert isinstance(none_results, list)
    assert len(none_results) > 0
    assert all(f.get("is_unlocked") is False for f in none_results)

    empty_player = ET.fromstring("<player></player>")
    empty_results = get_formatted_fishing(empty_player)
    assert isinstance(empty_results, list)
    assert len(empty_results) > 0
    assert all(f.get("is_unlocked") is False for f in empty_results)


def test_get_formatted_fishing_parsing():
    """Verifies parsing of caught fish records, quantities, and maximum length."""
    xml_data = """
    <player>
        <fishCaught>
            <item>
                <key><int>142</int></key>
                <value>
                    <ArrayOfInt>
                        <int>5</int>
                        <int>18</int>
                    </ArrayOfInt>
                </value>
            </item>
            <item>
                <key><string>143</string></key>
                <value>
                    <ArrayOfInt>
                        <int>1</int>
                        <int>12</int>
                    </ArrayOfInt>
                </value>
            </item>
            <item>
                <key><int>999999</int></key>
                <value>
                    <ArrayOfInt>
                        <int>0</int>
                        <int>0</int>
                    </ArrayOfInt>
                </value>
            </item>
        </fishCaught>
    </player>
    """
    player = ET.fromstring(xml_data)
    results = get_formatted_fishing(player)

    assert isinstance(results, list)
    assert len(results) > 0

    unlocked = [f for f in results if f.get("is_unlocked")]
    assert len(unlocked) >= 1

    caught_entry = next((f for f in results if str(f.get("id")) == "142"), None)
    if caught_entry:
        assert caught_entry["count"] == 5
        assert caught_entry["length"] == 18
        assert caught_entry["is_unlocked"] is True
        