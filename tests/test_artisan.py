# tests/test_artisan.py

import xml.etree.ElementTree as ET
from src.modules.artisan.casks import parse_all_casks_from_save
from src.modules.artisan.bee_houses import parse_all_bee_houses_from_save


def test_casks_ignored_when_house_upgrade_under_level_3():
    root = ET.fromstring("<SaveGame><locations></locations></SaveGame>")
    player = ET.fromstring("<player><houseUpgradeLevel>2</houseUpgradeLevel></player>")

    result = parse_all_casks_from_save(root, player)
    assert result["total_casks"] == 0


def test_bee_houses_hibernate_in_winter_outdoors():
    root_winter = ET.fromstring("""
    <SaveGame>
        <currentSeason>winter</currentSeason>
        <locations>
            <GameLocation>
                <name>Farm</name>
                <isOutdoors>true</isOutdoors>
                <objects>
                    <item>
                        <value>
                            <Object>
                                <name>Bee House</name>
                                <bigCraftable>true</bigCraftable>
                                <parentSheetIndex>10</parentSheetIndex>
                            </Object>
                        </value>
                    </item>
                </objects>
            </GameLocation>
        </locations>
    </SaveGame>
    """)
    result = parse_all_bee_houses_from_save(root_winter)
    assert result["total"] == 1
    assert result["hibernating"] == 1
    assert result["idle"] == 0
