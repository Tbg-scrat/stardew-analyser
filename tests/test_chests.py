# tests/test_chests.py

import xml.etree.ElementTree as ET
from src.modules.chests import parse_chests


def test_chest_capacity_and_material_aggregation():
    root = ET.fromstring("""
    <SaveGame>
        <locations>
            <GameLocation>
                <name>Farm</name>
                <objects>
                    <item>
                        <value>
                            <Object>
                                <name>Chest</name>
                                <QualifiedItemId>(BC)130</QualifiedItemId>
                                <items>
                                    <Item xsi:type="Object" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                                        <itemId>388</itemId>
                                        <QualifiedItemId>(O)388</QualifiedItemId>
                                        <name>Wood</name>
                                        <Stack>150</Stack>
                                    </Item>
                                </items>
                            </Object>
                        </value>
                    </item>
                </objects>
            </GameLocation>
        </locations>
    </SaveGame>
    """)

    result = parse_chests(root)
    assert result["total_chests"] == 1
    assert result["total_items"] == 150
    assert len(result["chests"][0]["chest_items"]) == 36
    wood_material = next(m for m in result["material_totals"] if m["name"] == "Wood")
    assert wood_material["count"] == 150
