# -*- coding: utf-8 -*-
# tests/modules/test_weather.py

import xml.etree.ElementTree as ET
from src.modules.weather import parse_weather


def test_parse_weather_none():
    """Verifies fallback when SaveGame root is None."""
    result = parse_weather(None)
    assert result["today"]["id"] == "Unknown"
    assert result["valley"]["id"] == "Unknown"
    assert result["island"] is None


def test_parse_weather_today_conditions():
    """Verifies live today weather condition priority (Lightning > Rain > Snow > Wind > Sun)."""
    # Storm / Lightning
    storm_xml = ET.fromstring("<SaveGame><isLightning>true</isLightning></SaveGame>")
    assert parse_weather(storm_xml)["today"]["id"] == "Storm"

    # Rain
    rain_xml = ET.fromstring("<SaveGame><isRaining>true</isRaining></SaveGame>")
    assert parse_weather(rain_xml)["today"]["id"] == "Rain"

    # Snow
    snow_xml = ET.fromstring("<SaveGame><isSnowing>true</isSnowing></SaveGame>")
    assert parse_weather(snow_xml)["today"]["id"] == "Snow"

    # Wind / Debris Weather
    wind_xml = ET.fromstring("<SaveGame><isDebrisWeather>true</isDebrisWeather></SaveGame>")
    assert parse_weather(wind_xml)["today"]["id"] == "Wind"

    # Default / Sun
    sun_xml = ET.fromstring("<SaveGame></SaveGame>")
    assert parse_weather(sun_xml)["today"]["id"] == "Sun"


def test_parse_weather_valley_and_island_forecast():
    """Verifies tomorrow's Valley forecast and Ginger Island location weather parsing."""
    xml_data = """
    <SaveGame>
        <weatherForTomorrow>Storm</weatherForTomorrow>
        <locationWeather>
            <item>
                <key><string>Farm</string></key>
            </item>
            <item>
                <key><string>Island</string></key>
                <value>
                    <LocationWeather>
                        <weatherForTomorrow>Rain</weatherForTomorrow>
                    </LocationWeather>
                </value>
            </item>
        </locationWeather>
    </SaveGame>
    """
    root = ET.fromstring(xml_data)
    result = parse_weather(root)

    assert result["valley"]["id"] == "Storm"
    assert result["valley"]["name"] == "Stormy"

    assert result["island"] is not None
    assert result["island"]["id"] == "Rain"
    assert result["island"]["name"] == "Rainy"
