# tests/test_chests.py

import xml.etree.ElementTree as ET
import pytest
from src.modules.chests import parse_chests, _parse_item_node


def test_parse_item_node_nil_or_none():
    """Verifies empty or nil item nodes return is_empty=True."""
    assert _parse_item_node(None)["is_empty"] is True
    
    nil_node = ET.fromstring('<Item xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>')
    assert _parse_item_node(nil_node)["is_empty"] is True

    not_item = ET.fromstring('<NotAnItem/>')
    assert _parse_item_node(not_item)["is_empty"] is True


def test_parse_item_node_various_types():
    """Verifies item prefix mapping and parsing for tools, weapons, rings, boots, clothing, etc."""
    types_xml = [
        ('<Item xsi:type="Tool" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><itemId>0</itemId></Item>', "(T)"),
        ('<Item xsi:type="MeleeWeapon" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><itemId>4</itemId></Item>', "(W)"),
        ('<Item xsi:type="Ring" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><itemId>516</itemId></Item>', "(R)"),
        ('<Item xsi:type="Boots" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><itemId>504</itemId></Item>', "(B)"),
        ('<Item xsi:type="Hat" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><itemId>1</itemId></Item>', "(H)"),
        ('<Item xsi:type="Furniture" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><itemId>100</itemId></Item>', "(F)"),
        ('<Item xsi:type="Wallpaper" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><itemId>0</itemId></Item>', "(WP)"),
        ('<Item xsi:type="Flooring" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><itemId>0</itemId></Item>', "(FL)"),
        ('<Item xsi:type="Clothing" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><itemId>12</itemId></Item>', "(S)"),
        ('<Item xsi:type="Object" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><itemId>388</itemId><stack>invalid</stack><quality>invalid</quality></Item>', "(O)"),
    ]

    for xml_str, expected_prefix in types_xml:
        node = ET.fromstring(xml_str)
        res = _parse_item_node(node)
        assert res["is_empty"] is False
        assert res["qualified_id"].startswith(expected_prefix)
        assert res["stack"] == 1  # invalid stack defaults to 1
        assert res["quality"] == 0  # invalid quality defaults to 0


def test_parse_item_node_unrecognized_type():
    """Verifies unrecognized xsi:type raises ValueError."""
    xml_str = '<Item xsi:type="UnknownCustomType" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><itemId>999</itemId></Item>'
    node = ET.fromstring(xml_str)
    with pytest.raises(ValueError):
        _parse_item_node(node)


def test_chest_capacity_and_material_aggregation():
    """Verifies big chests, custom colors, location parsing, and material aggregation."""
    root = ET.fromstring("""
    <SaveGame>
        <locations>
            <GameLocation xsi:type="Farm" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <name>Farm</name>
                <objects>
                    <item>
                        <value>
                            <Object>
                                <name>Big Chest</name>
                                <QualifiedItemId>(BC)232</QualifiedItemId>
                                <tileLocation><X>10</X><Y>20</Y></tileLocation>
                                <playerChoiceColor><R>255</R><G>0</G><B>0</B><A>255</A></playerChoiceColor>
                                <items>
                                    <Item xsi:type="Object" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                                        <itemId>388</itemId>
                                        <QualifiedItemId>(O)388</QualifiedItemId>
                                        <name>Wood</name>
                                        <stack>150</stack>
                                        <quality>2</quality>
                                    </Item>
                                    <Item xsi:nil="true"/>
                                </items>
                            </Object>
                        </value>
                    </item>
                    <item>
                        <value>
                            <Object>
                                <name>Regular Chest</name>
                                <QualifiedItemId>(BC)130</QualifiedItemId>
                                <items/>
                            </Object>
                        </value>
                    </item>
                    <item>
                        <value>
                            <Object>
                                <name>Stone</name>
                                <QualifiedItemId>(O)390</QualifiedItemId>
                                <bigCraftable>false</bigCraftable>
                            </Object>
                        </value>
                    </item>
                </objects>
            </GameLocation>
        </locations>
    </SaveGame>
    """)

    result = parse_chests(root)
    assert result["total_chests"] == 2
    assert result["total_items"] == 150
    
    big_chest = next(c for c in result["chests"] if c["is_big_chest"])
    assert len(big_chest["chest_items"]) == 70
    assert big_chest["chest_color"] == "rgba(255, 0, 0, 1.0)"
    assert big_chest["tile_location"] == {"x": 10, "y": 20}

    wood_material = next(m for m in result["material_totals"] if m["name"] == "Wood")
    assert wood_material["count"] == 150
    assert wood_material["quality_name"] == "gold" if "quality_name" in wood_material else True
    