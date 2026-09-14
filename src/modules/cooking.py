# -*- coding: utf-8 -*-
"""
Cooking module for Stardew Valley save file parsing.
Extracts cooked recipe counts keyed by item ID string from <recipesCooked>.
"""

def parse_cooking(player):
    """
    Parses <recipesCooked> from the player node or any sub-tree.

    :param player: xml.etree.ElementTree Element representing <player>
    :return: dict mapping item IDs (e.g. "194", "253") to cooked counts
    """
    if player is None:
        return {}

    cooked_counts = {}

    recipes_cooked_node = player.find("recipesCooked") or player.find(".//recipesCooked")

    if recipes_cooked_node is not None:
        for item in recipes_cooked_node.findall("item"):
            key_node = item.find("key")
            val_node = item.find("value")

            if key_node is not None:
                raw_key = "".join(key_node.itertext()).strip().replace("(O)", "")

                count = 0
                if val_node is not None:
                    val_text = "".join(val_node.itertext()).strip()
                    try:
                        count = int(val_text)
                    except ValueError:
                        count = 0

                if raw_key:
                    cooked_counts[raw_key] = count

    return cooked_counts
    