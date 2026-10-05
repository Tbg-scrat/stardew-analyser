# tests/test_hay.py

import xml.etree.ElementTree as ET
from src.modules.hay import parse_hay_data


def test_summer_hay_deficit_and_capacity_warning():
    """10 animals in Summer need 280 hay. With 1 Silo (240 capacity) & 100 hay, both warnings trigger."""
    xml_data = """
    <SaveGame>
        <currentSeason>summer</currentSeason>
        <dayOfMonth>10</dayOfMonth>
        <locations>
            <GameLocation>
                <name>Farm</name>
                <piecesOfHay>100</piecesOfHay>
                <buildings>
                    <Building>
                        <buildingType>Silo</buildingType>
                    </Building>
                </buildings>
                <buildings>
                    <Building>
                        <indoors>
                            <animals>
                                <item><value><FarmAnimal><name>Cow1</name></FarmAnimal></value></item>
                                <item><value><FarmAnimal><name>Cow2</name></FarmAnimal></value></item>
                                <item><value><FarmAnimal><name>Cow3</name></FarmAnimal></value></item>
                                <item><value><FarmAnimal><name>Cow4</name></FarmAnimal></value></item>
                                <item><value><FarmAnimal><name>Cow5</name></FarmAnimal></value></item>
                                <item><value><FarmAnimal><name>Chicken1</name></FarmAnimal></value></item>
                                <item><value><FarmAnimal><name>Chicken2</name></FarmAnimal></value></item>
                                <item><value><FarmAnimal><name>Chicken3</name></FarmAnimal></value></item>
                                <item><value><FarmAnimal><name>Chicken4</name></FarmAnimal></value></item>
                                <item><value><FarmAnimal><name>Chicken5</name></FarmAnimal></value></item>
                            </animals>
                        </indoors>
                    </Building>
                </buildings>
            </GameLocation>
        </locations>
    </SaveGame>
    """
    root = ET.fromstring(xml_data.strip())
    result = parse_hay_data(root)

    assert result["total_animals"] == 10
    assert result["silos_built"] == 1
    assert result["max_capacity"] == 240
    assert result["current_hay"] == 100
    assert result["required_winter_hay"] == 280
    assert result["deficit_amount"] == 180
    assert result["capacity_shortfall"] == 40
    assert result["has_deficit_warning"] is True
    assert result["has_capacity_warning"] is True


def test_winter_remaining_days_calculation():
    """On Winter 20, 5 animals need 9 days of feed (28 - 20 + 1 = 9 days * 5 = 45 hay)."""
    xml_data = """
    <SaveGame>
        <currentSeason>winter</currentSeason>
        <dayOfMonth>20</dayOfMonth>
        <locations>
            <GameLocation>
                <name>Farm</name>
                <piecesOfHay>50</piecesOfHay>
                <buildings>
                    <Building><buildingType>Silo</buildingType></Building>
                </buildings>
                <animals>
                    <item><value><FarmAnimal><name>Cow1</name></FarmAnimal></value></item>
                    <item><value><FarmAnimal><name>Cow2</name></FarmAnimal></value></item>
                    <item><value><FarmAnimal><name>Cow3</name></FarmAnimal></value></item>
                    <item><value><FarmAnimal><name>Cow4</name></FarmAnimal></value></item>
                    <item><value><FarmAnimal><name>Cow5</name></FarmAnimal></value></item>
                </animals>
            </GameLocation>
        </locations>
    </SaveGame>
    """
    root = ET.fromstring(xml_data.strip())
    result = parse_hay_data(root)

    assert result["required_winter_hay"] == 45
    assert result["deficit_amount"] == 0
    assert result["capacity_shortfall"] == 0
    assert result["has_deficit_warning"] is False
    assert result["has_capacity_warning"] is False


def test_zero_animals_no_warnings():
    """With zero animals, no warning flags should be raised."""
    xml_data = """
    <SaveGame>
        <currentSeason>spring</currentSeason>
        <dayOfMonth>1</dayOfMonth>
        <locations>
            <GameLocation>
                <name>Farm</name>
                <piecesOfHay>0</piecesOfHay>
            </GameLocation>
        </locations>
    </SaveGame>
    """
    root = ET.fromstring(xml_data.strip())
    result = parse_hay_data(root)

    assert result["total_animals"] == 0
    assert result["has_deficit_warning"] is False
    assert result["has_capacity_warning"] is False
