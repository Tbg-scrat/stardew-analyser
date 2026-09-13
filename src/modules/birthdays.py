# -*- coding: utf-8 -*-
"""
Birthdays module for Stardew Valley save file parsing.
Tracks villager birthdays and identifies the next upcoming birthday.
"""

VILLAGER_BIRTHDAYS = {
    "spring": [
        {"day": 4, "name": "Kent", "icon": "\U0001F382"},
        {"day": 7, "name": "Lewis", "icon": "\U0001F382"},
        {"day": 10, "name": "Vincent", "icon": "\U0001F382"},
        {"day": 14, "name": "Haley", "icon": "\U0001F382"},
        {"day": 18, "name": "Pam", "icon": "\U0001F382"},
        {"day": 20, "name": "Shane", "icon": "\U0001F382"},
        {"day": 26, "name": "Pierre", "icon": "\U0001F382"},
        {"day": 27, "name": "Emily", "icon": "\U0001F382"},
    ],
    "summer": [
        {"day": 4, "name": "Jas", "icon": "\U0001F382"},
        {"day": 8, "name": "Gus", "icon": "\U0001F382"},
        {"day": 10, "name": "Maru", "icon": "\U0001F382"},
        {"day": 13, "name": "Alex", "icon": "\U0001F382"},
        {"day": 17, "name": "Sam", "icon": "\U0001F382"},
        {"day": 19, "name": "Demetrius", "icon": "\U0001F382"},
        {"day": 24, "name": "Willy", "icon": "\U0001F382"},
        {"day": 26, "name": "Leo", "icon": "\U0001F382"},
    ],
    "fall": [
        {"day": 2, "name": "Penny", "icon": "\U0001F382"},
        {"day": 5, "name": "Elliott", "icon": "\U0001F382"},
        {"day": 11, "name": "Jodi", "icon": "\U0001F382"},
        {"day": 13, "name": "Abigail", "icon": "\U0001F382"},
        {"day": 15, "name": "Sandy", "icon": "\U0001F382"},
        {"day": 18, "name": "Marnie", "icon": "\U0001F382"},
        {"day": 21, "name": "Robin", "icon": "\U0001F382"},
        {"day": 24, "name": "George", "icon": "\U0001F382"},
    ],
    "winter": [
        {"day": 1, "name": "Krobus", "icon": "\U0001F382"},
        {"day": 3, "name": "Linus", "icon": "\U0001F382"},
        {"day": 7, "name": "Caroline", "icon": "\U0001F382"},
        {"day": 10, "name": "Sebastian", "icon": "\U0001F382"},
        {"day": 14, "name": "Harvey", "icon": "\U0001F382"},
        {"day": 17, "name": "Wizard", "icon": "\U0001F382"},
        {"day": 20, "name": "Evelyn", "icon": "\U0001F382"},
        {"day": 23, "name": "Leah", "icon": "\U0001F382"},
        {"day": 26, "name": "Clint", "icon": "\U0001F382"},
    ]
}

def parse_birthdays(root):
    """
    Parses current date and identifies the next upcoming birthday in the season.

    :param root: xml.etree.ElementTree Element representing <SaveGame>
    :return: dict containing next birthday details and status text
    """
    if root is None:
        return {"next_birthday": None, "status_text": "None"}

    season_node = root.find("currentSeason")
    day_node = root.find("dayOfMonth")

    season = season_node.text.lower() if season_node is not None and season_node.text else "spring"
    try:
        day = int(day_node.text) if day_node is not None and day_node.text else 1
    except ValueError:
        day = 1

    seasonal_birthdays = VILLAGER_BIRTHDAYS.get(season, [])
    upcoming = [b for b in seasonal_birthdays if b["day"] >= day]

    if upcoming:
        next_bday = upcoming[0]
        days_away = next_bday["day"] - day
        status_text = "Today!" if days_away == 0 else f"In {days_away} day{'s' if days_away > 1 else ''} (Day {next_bday['day']})"
    else:
        next_bday = None
        status_text = "None remaining this season"

    return {
        "next_birthday": next_bday,
        "status_text": status_text
    }
