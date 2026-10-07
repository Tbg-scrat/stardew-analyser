# tests/test_pipeline.py

from unittest.mock import patch
import xml.etree.ElementTree as ET
from parse import analyze_save, log_save_summary, run_pipeline


def test_analyze_save_schema_contract():
    """Verifies that analyze_save() returns all top-level keys required for UI rendering."""
    save_xml = """
    <SaveGame>
        <dayOfMonth>20</dayOfMonth>
        <currentSeason>fall</currentSeason>
        <year>3</year>
        <player>
            <name>Nils</name>
            <farmName>Friisen</farmName>
            <money>500000</money>
            <totalMoneyEarned>1200000</totalMoneyEarned>
            <houseUpgradeLevel>3</houseUpgradeLevel>
        </player>
        <locations></locations>
    </SaveGame>
    """
    root = ET.fromstring(save_xml.strip())
    player = root.find("player")

    with patch("parse.get_player_node", return_value=(root, player)):
        data = analyze_save("fake_save_path")

    expected_keys = [
        "farmer",
        "farm",
        "money",
        "total_earned",
        "day_of_month",
        "season",
        "year",
        "weather",
        "daily_luck",
        "festivals",
        "birthdays",
        "shipped_items",
        "fish_caught",
        "museum_pieces",
        "recipes_cooked",
        "achievements",
        "friendships",
        "artisan",
        "chests",
        "crops",
        "hay",
        "tools",
        "grandpa",
        "community_center",
    ]

    for key in expected_keys:
        assert key in data, f"Missing required top-level key '{key}' in analyze_save() output"


def test_log_save_summary_formatting(caplog):
    """Ensures log_save_summary formats cleanly without throwing KeyErrors or TypeErrors."""
    mock_data = {
        "farmer": "Nils",
        "farm": "Friisen",
        "day_of_month": 20,
        "season": "fall",
        "year": 3,
        "achievements": {"unlocked_count": 22, "total": 39},
        "shipped_items": [{"is_unlocked": True}] * 100 + [{"is_unlocked": False}] * 149,
        "fish_caught": [{"is_unlocked": True}] * 40,
        "museum_pieces": [{"is_unlocked": True}] * 60,
        "artisan": {"summary": {"total_machines": 150}},
        "chests": {"total_chests": 12},
        "crops": {"summary": {"total_crops": 384, "ready_today": 84}},
        "tools": {
            "upgradeable": [
                {"key": "Axe", "is_max": True},
                {"key": "Pickaxe", "is_max": False},
                {"key": "Hoe", "is_max": False},
                {"key": "WateringCan", "is_max": False},
                {"key": "TrashCan", "is_max": False},
                {"key": "Pan", "is_max": True},
            ],
            "scythe": {"current_stage": {"name": "Golden Scythe"}, "is_max": False}
        },
        "hay": {"current_hay": 350, "max_capacity": 480, "total_animals": 16},
        "grandpa": {"total_score": 14, "max_score": 21, "candles": 4},
        "community_center": {"completed_bundles": 28, "total_bundles": 30, "route_label": "Community Center (Junimo)"},
    }

    with caplog.at_level("INFO"):
        log_save_summary("Friisen_12345", mock_data)

    assert "Parsed 'Friisen_12345' (Nils @ Friisen Farm | Y3 Fall 20)" in caplog.text
    assert "Achievements: 22/39" in caplog.text
    assert "Crops: 384 total (84 ready)" in caplog.text
    assert "Grandpa: 14/21 pts (4 Candles)" in caplog.text
    assert "CC: 28/30 Bundles (Community Center (Junimo))" in caplog.text


def test_run_pipeline_asset_cache_verification(tmp_path, caplog):
    """Verifies that run_pipeline() asserts asset cache validity and logs status."""
    with patch("parse.is_cache_valid", return_value=True) as mock_cache_check:
        with caplog.at_level("INFO"):
            run_pipeline(save_dir=tmp_path)

        mock_cache_check.assert_called_once()
        assert "Asset cache verification: VALID" in caplog.text
        