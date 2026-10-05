# -*- coding: utf-8 -*-
# tests/modules/test_luck.py

import xml.etree.ElementTree as ET
from src.modules.luck import parse_luck


def test_parse_luck_none():
    """Verifies default fallback structure when SaveGame root is None."""
    result = parse_luck(None)
    assert result == {
        "value": 0.0,
        "label": "Neutral",
        "icon": "\U0001F610",
        "css_class": "luck-neutral",
    }


def test_parse_luck_invalid_or_missing_node():
    """Verifies handling of missing dailyLuck node or non-float text values."""
    empty_root = ET.fromstring("<SaveGame></SaveGame>")
    assert parse_luck(empty_root)["css_class"] == "luck-neutral"

    invalid_root = ET.fromstring("<SaveGame><dailyLuck>invalid_float</dailyLuck></SaveGame>")
    assert parse_luck(invalid_root)["css_class"] == "luck-neutral"


def test_parse_luck_thresholds():
    """Verifies all 5 daily luck categories based on Welwick's Oracle TV Channel thresholds."""
    # 1. Best Luck (>= 0.07)
    best_root = ET.fromstring("<SaveGame><dailyLuck>0.08</dailyLuck></SaveGame>")
    best_res = parse_luck(best_root)
    assert best_res["css_class"] == "luck-best"
    assert best_res["label"] == "Stardew Spirits Are Very Happy"
    assert best_res["value"] == 0.08

    # 2. Good Luck (> 0.02)
    good_root = ET.fromstring("<SaveGame><dailyLuck>0.05</dailyLuck></SaveGame>")
    good_res = parse_luck(good_root)
    assert good_res["css_class"] == "luck-good"
    assert good_res["label"] == "Spirits Are In Good Humor"

    # 3. Neutral Luck (-0.02 to 0.02)
    neutral_root = ET.fromstring("<SaveGame><dailyLuck>0.0</dailyLuck></SaveGame>")
    neutral_res = parse_luck(neutral_root)
    assert neutral_res["css_class"] == "luck-neutral"
    assert neutral_res["label"] == "Spirits Feel Neutral"

    # 4. Bad Luck (> -0.07)
    bad_root = ET.fromstring("<SaveGame><dailyLuck>-0.05</dailyLuck></SaveGame>")
    bad_res = parse_luck(bad_root)
    assert bad_res["css_class"] == "luck-bad"
    assert bad_res["label"] == "Spirits Are Somewhat Annoyed"

    # 5. Worst Luck (<= -0.07)
    worst_root = ET.fromstring("<SaveGame><dailyLuck>-0.10</dailyLuck></SaveGame>")
    worst_res = parse_luck(worst_root)
    assert worst_res["css_class"] == "luck-worst"
    assert worst_res["label"] == "Spirits Are Very Displeased"
    