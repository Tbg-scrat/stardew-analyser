# src/modules/luck.py
# -*- coding: utf-8 -*-
"""
Luck module for Stardew Valley save file parsing.
Extracts today's daily luck modifier from the save XML root and returns formatted display metadata.
"""

import logging

logger = logging.getLogger(__name__)


def parse_luck(root):
    """
    Parses daily luck value from the save XML root.
    Daily luck ranges from -0.1 to +0.1 (modified by Special Charm to max ~0.125).

    :param root: xml.etree.ElementTree Element representing <SaveGame>
    :return: dict containing luck value, qualitative description, emoji icon, and status class
    """
    if root is None:
        logger.warning("SaveGame root is None. Defaulting daily luck to 0.0 (Neutral).")
        return {"value": 0.0, "label": "Neutral", "icon": "\U0001F610", "css_class": "luck-neutral"}

    luck_node = root.find("dailyLuck")
    try:
        luck_val = float(luck_node.text) if luck_node is not None and luck_node.text else 0.0
    except ValueError:
        luck_val = 0.0

    # Categorize luck thresholds based on Welwick's Oracle TV Channel
    if luck_val >= 0.07:
        label = "Stardew Spirits Are Very Happy"
        icon = "\U0001F31F"  # Star
        css_class = "luck-best"
    elif luck_val > 0.02:
        label = "Spirits Are In Good Humor"
        icon = "\U0001F604"  # Smile
        css_class = "luck-good"
    elif luck_val >= -0.02:
        label = "Spirits Feel Neutral"
        icon = "\U0001F610"  # Neutral face
        css_class = "luck-neutral"
    elif luck_val > -0.07:
        label = "Spirits Are Somewhat Annoyed"
        icon = "\U0001F61F"  # Concerned face
        css_class = "luck-bad"
    else:
        label = "Spirits Are Very Displeased"
        icon = "\U0001F480"  # Skull
        css_class = "luck-worst"

    logger.debug(f"Daily luck: {round(luck_val, 4)} ({label})")

    return {
        "value": round(luck_val, 4),
        "label": label,
        "icon": icon,
        "css_class": css_class
    }
    