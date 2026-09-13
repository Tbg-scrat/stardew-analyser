# -*- coding: utf-8 -*-
"""
Weather module for Stardew Valley save file parsing.
Extracts tomorrow's weather forecast for Pelican Town and Ginger Island.
"""

WEATHER_MAP = {
    "Sun": {"name": "Sunny", "icon": "\u2600\ufe0f", "css_class": "weather-sunny"},
    "Rain": {"name": "Rainy", "icon": "\U0001F327\ufe0f", "css_class": "weather-rainy"},
    "Wind": {"name": "Windy", "icon": "\U0001F343", "css_class": "weather-windy"},
    "Storm": {"name": "Stormy", "icon": "\u26C8\ufe0f", "css_class": "weather-stormy"},
    "Festival": {"name": "Festival", "icon": "\U0001F38F", "css_class": "weather-festival"},
    "Snow": {"name": "Snowy", "icon": "\u2744\ufe0f", "css_class": "weather-snowy"},
}

def parse_weather(root):
    """
    Parses tomorrow's weather forecast from the save XML root.

    :param root: xml.etree.ElementTree Element representing <SaveGame>
    :return: dict containing valley weather and optional island weather forecast
    """
    if root is None:
        return {
            "valley": {"id": "Unknown", "name": "Unknown", "icon": "\u2753", "css_class": "weather-unknown"},
            "island": None
        }

    # 1. Main Valley Weather Forecast
    weather_node = root.find("weatherForTomorrow")
    weather_id = weather_node.text if weather_node is not None and weather_node.text else "Sun"

    valley_data = WEATHER_MAP.get(
        weather_id, 
        {"name": "Unknown", "icon": "\u2753", "css_class": "weather-unknown"}
    )

    # 2. Ginger Island Weather Forecast (if unlocked)
    island_weather_id = None
    location_contexts = root.find("locationWeather")
    if location_contexts is not None:
        for item in location_contexts.findall("item"):
            key = item.find("key/string")
            if key is not None and key.text == "Island":
                weather_for_tomorrow = item.find("value/LocationWeather/weatherForTomorrow")
                if weather_for_tomorrow is not None and weather_for_tomorrow.text:
                    island_weather_id = weather_for_tomorrow.text
                break

    island_data = None
    if island_weather_id:
        mapped_island = WEATHER_MAP.get(
            island_weather_id, 
            {"name": "Unknown", "icon": "\u2753", "css_class": "weather-unknown"}
        )
        island_data = {
            "id": island_weather_id,
            "name": mapped_island["name"],
            "icon": mapped_island["icon"],
            "css_class": mapped_island["css_class"]
        }

    return {
        "valley": {
            "id": weather_id,
            "name": valley_data["name"],
            "icon": valley_data["icon"],
            "css_class": valley_data["css_class"]
        },
        "island": island_data
    }
