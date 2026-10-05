# tests/test_crops.py

import xml.etree.ElementTree as ET
from src.modules.crops import parse_crop, parse_all_crops_from_save


def test_parse_crop_ready_today():
    xml_data = """
    <crop>
        <currentPhase>5</currentPhase>
        <dayOfCurrentPhase>1</dayOfCurrentPhase>
        <fullyGrown>false</fullyGrown>
        <regrowAfterHarvest>-1</regrowAfterHarvest>
        <indexOfHarvest>454</indexOfHarvest>
        <phaseDays><int>1</int><int>4</int><int>5</int><int>5</int><int>3</int><int>99999</int></phaseDays>
    </crop>
    """
    crop_elem = ET.fromstring(xml_data.strip())
    result = parse_crop(crop_elem)

    assert result["days_to_harvest"] == 0
    assert result["harvest_id"] == "454"
    assert result["is_recurring"] is False


def test_parse_crop_days_remaining_calculation():
    xml_data = """
    <crop>
        <currentPhase>4</currentPhase>
        <dayOfCurrentPhase>1</dayOfCurrentPhase>
        <fullyGrown>false</fullyGrown>
        <regrowAfterHarvest>-1</regrowAfterHarvest>
        <indexOfHarvest>Powdermelon</indexOfHarvest>
        <phaseDays><int>1</int><int>0</int><int>0</int><int>1</int><int>2</int><int>99999</int></phaseDays>
    </crop>
    """
    crop_elem = ET.fromstring(xml_data.strip())
    result = parse_crop(crop_elem)

    # current_phase = 4, phase_days[4] = 2, day_of_phase = 1 -> 1 day remaining
    assert result["days_to_harvest"] == 1
    assert result["harvest_id"] == "Powdermelon"


def test_season_wither_warning_on_main_farm():
    save_xml = """
    <SaveGame>
        <locations>
            <GameLocation xsi:type="Farm" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <name>Farm</name>
                <terrainFeatures>
                    <item>
                        <value>
                            <TerrainFeature xsi:type="HoeDirt">
                                <crop>
                                    <currentPhase>0</currentPhase>
                                    <dayOfCurrentPhase>0</dayOfCurrentPhase>
                                    <fullyGrown>false</fullyGrown>
                                    <regrowAfterHarvest>-1</regrowAfterHarvest>
                                    <indexOfHarvest>472</indexOfHarvest>
                                    <phaseDays><int>3</int><int>3</int><int>3</int><int>3</int><int>99999</int></phaseDays>
                                </crop>
                            </TerrainFeature>
                        </value>
                    </item>
                </terrainFeatures>
            </GameLocation>
        </locations>
    </SaveGame>
    """
    root = ET.fromstring(save_xml.strip())
    # Current day = 20, remaining season days = 8. Crop needs 12 days.
    result = parse_all_crops_from_save(root, current_day=20)

    farm_items = result["locations"]["farm"]["items"]
    assert len(farm_items) == 1
    assert farm_items[0]["will_wither"] is True
    