# -*- coding: utf-8 -*-
"""
Festivals module for Stardew Valley save file parsing.
Determines the current date and calculates upcoming seasonal festivals.
"""

FESTIVAL_CALENDAR = {
    "spring": [
        {"day": 13, "name": "Egg Festival", "location": "Pelican Town", "icon": "\U0001F95A"},
        {"day": 24, "name": "Flower Dance", "location": "Cindersap Forest", "icon": "\U0001F338"},
    ],
    "summer": [
        {"day": 11, "name": "Luau", "location": "The Beach", "icon": "\U0001F372"},
        {"day": 20, "name": "Trout Derby (Day 1)", "location": "Cindersap Forest", "icon": "\U0001F801"},
        {"day": 21, "name": "Trout Derby (Day 2)", "location": "Cindersap Forest", "icon": "\U0001F801"},
        {"day": 28, "name": "Dance of the Moonlight Jellies", "location": "The Beach", "icon": "\U0001F988"},
    ],
    "fall": [
        {"day": 16, "name": "Stardew Valley Fair", "location": "Pelican Town", "icon": "\U0001F3AA"},
        {"day": 27, "name": "Spirits' Eve", "location": "Pelican Town", "icon": "\U0001F383"},
    ],
    "winter": [
        {"day": 8, "name": "Festival of Ice", "location": "Cindersap Forest", "icon": "\U0001F9CA"},
        {"day": 12, "name": "SquidFest (Day 1)", "location": "The Beach", "icon": "\U0001F991"},
        {"day": 13, "name": "SquidFest (Day 2)", "location": "The Beach", "icon": "\U0001F991"},
        {"day": 15, "name": "Night Market (Day 1)", "location": "The Beach", "icon": "\U0001F3D5\ufe0f"},
        {"day": 16, "name": "Night Market (Day 2)", "location": "The Beach", "icon": "\U0001F3D5\ufe0f"},
        {"day": 17, "name": "Night Market (Day 3)", "location": "The Beach", "icon": "\U0001F3D5\ufe0f"},
        {"day": 25, "name": "Feast of the Winter Star", "location": "Pelican Town", "icon": "\U0001F384"},
    ]
}

def parse_festivals(root):
    """
    Parses current date and identifies the next upcoming festival in the season.

    :param root: xml.etree.ElementTree Element representing <SaveGame>
    :return: dict containing current date info and next festival details
    """
    if root is None:
        return {"current_day": 1, "season": "spring", "next_festival": None}

    season_node = root.find("currentSeason")
    day_node = root.find("dayOfMonth")

    season = season_node.text.lower() if season_node is not None and season_node.text else "spring"
    try:
        day = int(day_node.text) if day_node is not None and day_node.text else 1
    except ValueError:
        day = 1

    seasonal_festivals = FESTIVAL_CALENDAR.get(season, [])
    
    # Find next festival today or later in current season
    upcoming = [f for f in seasonal_festivals if f["day"] >= day]

    if upcoming:
        next_event = upcoming[0]
        days_away = next_event["day"] - day
        status_text = "Today!" if days_away == 0 else f"In {days_away} day{'s' if days_away > 1 else ''} (Day {next_event['day']})"
    else:
        next_event = None
        status_text = "None remaining this season"

    return {
        "season": season.capitalize(),
        "day": day,
        "next_festival": next_event,
        "status_text": status_text
    }
