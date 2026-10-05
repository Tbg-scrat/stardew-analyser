# -*- coding: utf-8 -*-
# tests/modules/test_artisan_machines.py

import xml.etree.ElementTree as ET
from src.modules.artisan import parse_all_artisan_goods
from src.modules.artisan.bee_houses import parse_all_bee_houses_from_save
from src.modules.artisan.casks import parse_all_casks_from_save, parse_casks, resolve_item_icon
from src.modules.artisan.dehydrators import parse_all_dehydrators_from_save
from src.modules.artisan.jars import parse_all_jars_from_save
from src.modules.artisan.kegs import parse_all_kegs_from_save


def test_resolve_item_icon_mapping_and_fallback():
    """Verifies item icon resolution for color-mapped goods and standard wiki string fallbacks."""
    # Unmapped items fallback to Wiki filename conventions
    assert resolve_item_icon("Unmapped Test Item") == "Unmapped_Test_Item"
    assert resolve_item_icon("Governor's Reserve") == "Governor%27s_Reserve"


def test_casks_edge_cases_and_parsing():
    """Verifies cellar level requirements, missing nodes, quality math, and cask parsing."""
    player_lvl2 = ET.fromstring("<player><houseUpgradeLevel>2</houseUpgradeLevel></player>")
    empty_root = ET.fromstring("<SaveGame></SaveGame>")
    res_no_cellar = parse_all_casks_from_save(empty_root, player_lvl2)
    assert res_no_cellar["total_casks"] == 0

    no_objects_loc = ET.fromstring("<GameLocation><name>Cellar</name></GameLocation>")
    assert parse_casks(no_objects_loc) is None

    non_cask_loc = ET.fromstring(
        "<GameLocation><objects><item><value><Object><parentSheetIndex>99</parentSheetIndex></Object></value></item></objects></GameLocation>"
    )
    assert parse_casks(non_cask_loc) is None

    player_lvl3 = ET.fromstring("<player><houseUpgradeLevel>3</houseUpgradeLevel></player>")
    cellar_xml = """
    <SaveGame>
        <locations>
            <GameLocation xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="Cellar">
                <name>Cellar</name>
                <objects>
                    <item>
                        <value>
                            <Object xsi:type="Cask">
                                <heldObject xsi:nil="true" />
                            </Object>
                        </value>
                    </item>
                    <item>
                        <value>
                            <Object xsi:type="Cask">
                                <heldObject>
                                    <displayName>Starfruit Wine</displayName>
                                    <quality>invalid_qual</quality>
                                </heldObject>
                                <daysToMature>14.2</daysToMature>
                            </Object>
                        </value>
                    </item>
                    <item>
                        <value>
                            <Object xsi:type="Cask">
                                <heldObject>
                                    <displayName>Pale Ale</displayName>
                                    <quality>1</quality>
                                </heldObject>
                                <daysToMature>1.0</daysToMature>
                            </Object>
                        </value>
                    </item>
                    <item>
                        <value>
                            <Object>
                                <bigCraftable>true</bigCraftable>
                                <parentSheetIndex>163</parentSheetIndex>
                                <heldObject>
                                    <displayName>Goat Cheese</displayName>
                                    <quality>4</quality>
                                </heldObject>
                                <daysToMature>bad_float</daysToMature>
                            </Object>
                        </value>
                    </item>
                </objects>
            </GameLocation>
        </locations>
    </SaveGame>
    """
    root_cellar = ET.fromstring(cellar_xml)
    res_casks = parse_all_casks_from_save(root_cellar, player_lvl3)

    assert res_casks["total_casks"] == 4
    assert res_casks["empty_casks"] == 1
    assert res_casks["ready_today"] == 1
    assert res_casks["ready_tomorrow"] == 1
    assert res_casks["aging_count"] == 2
    assert len(res_casks["batches"]) == 3


def test_kegs_furnace_exclusion_and_building_interiors():
    """Verifies keg parsing, furnace exclusion, and recursive building interior scanning."""
    keg_xml = """
    <SaveGame xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <locations>
            <GameLocation>
                <name>Farm</name>
                <objects>
                    <item>
                        <value>
                            <Object>
                                <name>Keg</name>
                                <heldObject xsi:nil="true"/>
                            </Object>
                        </value>
                    </item>
                    <item>
                        <value>
                            <Object>
                                <name>Furnace</name>
                                <QualifiedItemId>(BC)13</QualifiedItemId>
                            </Object>
                        </value>
                    </item>
                </objects>
                <buildings>
                    <Building>
                        <buildingType>Shed</buildingType>
                        <indoors>
                            <name>Big Shed</name>
                            <objects>
                                <item>
                                    <value>
                                        <Object>
                                            <name>Keg</name>
                                            <heldObject>
                                                <displayName>Ancient Fruit Wine</displayName>
                                                <quality>0</quality>
                                            </heldObject>
                                            <minutesUntilReady>10000</minutesUntilReady>
                                        </Object>
                                    </value>
                                </item>
                                <item>
                                    <value>
                                        <Object>
                                            <bigCraftable>true</bigCraftable>
                                            <parentSheetIndex>12</parentSheetIndex>
                                            <heldObject>
                                                <displayName>Hops Pale Ale</displayName>
                                                <quality>0</quality>
                                            </heldObject>
                                            <minutesUntilReady>1600</minutesUntilReady>
                                        </Object>
                                    </value>
                                </item>
                            </objects>
                        </indoors>
                    </Building>
                </buildings>
            </GameLocation>
        </locations>
    </SaveGame>
    """
    root_kegs = ET.fromstring(keg_xml)
    res_kegs = parse_all_kegs_from_save(root_kegs)

    assert res_kegs["total"] == 3
    assert res_kegs["idle"] == 1
    assert res_kegs["ready_tomorrow"] == 1
    assert res_kegs["processing"] == 1
    assert res_kegs["idle_locations"].get("Farm") == 1


def test_jars_and_dehydrators_parsing():
    """Verifies preserves jars and dehydrators parsing in indoor building structures."""
    xml_data = """
    <SaveGame xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <locations>
            <GameLocation>
                <name>Farm</name>
                <buildings>
                    <Building>
                        <buildingType>Shed</buildingType>
                        <indoors>
                            <name>Shed #1</name>
                            <objects>
                                <item>
                                    <value>
                                        <Object>
                                            <name>Preserves Jar</name>
                                            <heldObject xsi:nil="true"/>
                                        </Object>
                                    </value>
                                </item>
                                <item>
                                    <value>
                                        <Object>
                                            <bigCraftable>true</bigCraftable>
                                            <parentSheetIndex>15</parentSheetIndex>
                                            <readyForHarvest>true</readyForHarvest>
                                            <heldObject>
                                                <displayName>Pickles</displayName>
                                                <quality>0</quality>
                                            </heldObject>
                                            <minutesUntilReady>0</minutesUntilReady>
                                        </Object>
                                    </value>
                                </item>
                                <item>
                                    <value>
                                        <Object>
                                            <name>Dehydrator</name>
                                            <heldObject xsi:nil="true"/>
                                        </Object>
                                    </value>
                                </item>
                                <item>
                                    <value>
                                        <Object>
                                            <bigCraftable>true</bigCraftable>
                                            <parentSheetIndex>272</parentSheetIndex>
                                            <readyForHarvest>true</readyForHarvest>
                                            <heldObject>
                                                <displayName>Raisins</displayName>
                                                <quality>0</quality>
                                            </heldObject>
                                        </Object>
                                    </value>
                                </item>
                            </objects>
                        </indoors>
                    </Building>
                </buildings>
            </GameLocation>
        </locations>
    </SaveGame>
    """
    root = ET.fromstring(xml_data)

    res_jars = parse_all_jars_from_save(root)
    assert res_jars["total"] == 2
    assert res_jars["idle"] == 1
    assert res_jars["ready_today"] == 1
    assert res_jars["idle_locations"].get("Shed #1") == 1

    res_dehydrators = parse_all_dehydrators_from_save(root)
    assert res_dehydrators["total"] == 2
    assert res_dehydrators["idle"] == 1
    assert res_dehydrators["ready_today"] == 1
    assert res_dehydrators["idle_locations"].get("Shed #1") == 1


def test_bee_houses_winter_hibernation_and_ginger_island():
    """Verifies outdoor winter hibernation rules for farm bee houses vs year-round Ginger Island production."""
    xml_data = """
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
                            </Object>
                        </value>
                    </item>
                </objects>
            </GameLocation>
            <GameLocation>
                <name>IslandWest</name>
                <isOutdoors>true</isOutdoors>
                <objects>
                    <item>
                        <value>
                            <Object>
                                <name>Bee House</name>
                                <readyForHarvest>true</readyForHarvest>
                                <heldObject>
                                    <displayName>Fairy Rose Honey</displayName>
                                    <quality>0</quality>
                                </heldObject>
                            </Object>
                        </value>
                    </item>
                </objects>
            </GameLocation>
        </locations>
    </SaveGame>
    """
    root = ET.fromstring(xml_data)
    res_bees = parse_all_bee_houses_from_save(root)

    assert res_bees["total"] == 2
    assert res_bees["hibernating"] == 1
    assert res_bees["ready_today"] == 1


def test_artisan_aggregator_and_idle_summary():
    """Verifies parse_all_artisan_goods consolidation and global idle_summary breakdown."""
    xml_data = """
    <SaveGame xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <currentSeason>spring</currentSeason>
        <locations>
            <GameLocation>
                <name>Farm</name>
                <objects>
                    <item>
                        <value>
                            <Object>
                                <name>Keg</name>
                                <heldObject xsi:nil="true"/>
                            </Object>
                        </value>
                    </item>
                </objects>
            </GameLocation>
        </locations>
    </SaveGame>
    """
    root = ET.fromstring(xml_data)
    player = ET.fromstring("<player><houseUpgradeLevel>3</houseUpgradeLevel></player>")

    agg = parse_all_artisan_goods(root, player)
    summary = agg["summary"]

    assert summary["total_machines"] == 1
    assert summary["idle_machines"] == 1
    assert agg["idle_summary"] == {"Farm": {"kegs": 1}}
    