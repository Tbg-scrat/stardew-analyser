# -*- coding: utf-8 -*-
"""
Gift preferences reference data for Stardew Valley villagers.
Contains item names and wiki icon mappings for loved gifts loaded from catalog.
"""

from data.data_loader import VILLAGERS_CATALOG


def format_wiki_filename(name):
    return name.replace(" ", "_").replace("'", "%27")


def get_loved_gifts(villager_name):
    """Returns a list of dicts containing name and wiki_icon for a villager's loved gifts."""
    villagers_map = VILLAGERS_CATALOG.get("villagers", {})
    villager_data = villagers_map.get(villager_name, {})
    gifts = villager_data.get("loved_gifts", [])
    return [{"name": name, "wiki_icon": format_wiki_filename(name)} for name in gifts]
    