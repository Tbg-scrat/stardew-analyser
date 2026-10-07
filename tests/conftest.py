# tests/conftest.py

import os
import xml.etree.ElementTree as ET
import pytest


@pytest.fixture(autouse=True)
def reset_logging_env(monkeypatch):
    """Automatically resets DEBUG environment variable state before each test."""
    monkeypatch.delenv("DEBUG", raising=False)


@pytest.fixture
def sample_player_xml():
    """Minimal valid <player> XML snippet for module unit tests."""
    xml_data = """
    <player>
        <name>TestFarmer</name>
        <farmName>TestFarm</farmName>
        <money>1500</money>
        <totalMoneyEarned>5000</totalMoneyEarned>
        <houseUpgradeLevel>3</houseUpgradeLevel>
        <achievements>
            <int>0</int>
            <int>1</int>
        </achievements>
        <basicShipped>
            <item>
                <key><string>24</string></key>
                <value><int>10</int></value>
            </item>
        </basicShipped>
    </player>
    """
    return ET.fromstring(xml_data.strip())


@pytest.fixture
def sample_save_root_xml():
    """Minimal valid <SaveGame> XML snippet for module unit tests."""
    xml_data = """
    <SaveGame>
        <dayOfMonth>15</dayOfMonth>
        <currentSeason>summer</currentSeason>
        <year>2</year>
        <dailyLuck>0.05</dailyLuck>
        <isRaining>false</isRaining>
        <isSnowing>false</isSnowing>
        <isLightning>false</isLightning>
        <isDebrisWeather>false</isDebrisWeather>
        <weatherForTomorrow>Sun</weatherForTomorrow>
        <locations></locations>
    </SaveGame>
    """
    return ET.fromstring(xml_data.strip())


@pytest.fixture
def sample_render_data():
    """Provides a realistic single save data dictionary for all renderer test modules."""
    return {
        "farmer": "Nils",
        "farm": "Friisen",
        "money": 1138180,
        "total_earned": 2614655,
        "day_of_month": 24,
        "season": "fall",
        "year": 3,
        "weather": {
            "today": {"name": "Windy", "icon": "\U0001F343", "css_class": "weather-windy"},
            "valley": {"name": "Rainy", "icon": "\U0001F327\ufe0f", "css_class": "weather-rainy"},
            "island": None,
        },
        "daily_luck": {
            "value": -0.079,
            "label": "Spirits Are Very Displeased",
            "icon": "\U0001F480",
            "css_class": "luck-worst",
        },
        "festivals": {
            "season": "Fall",
            "day": 24,
            "next_festival": {"name": "Spirits' Eve", "day": 27},
            "status_text": "In 3 days (Day 27)",
        },
        "birthdays": {
            "next_birthday": {"name": "George", "day": 24},
            "status_text": "Today!",
        },
        "shipped_items": [
            {
                "id": "24",
                "name": "Parsnip",
                "count": 10,
                "status": "shipped",
                "is_unlocked": True,
            }
        ],
        "fish_caught": [
            {
                "id": "142",
                "name": "Carp",
                "count": 5,
                "length": 15,
                "status": "caught",
                "is_unlocked": True,
            }
        ],
        "museum_pieces": [
            {
                "id": "535",
                "name": "Geode",
                "type": "Mineral",
                "status": "found",
                "is_unlocked": True,
            }
        ],
        "recipes_cooked": [],
        "achievements": {
            "unlocked_count": 22,
            "total": 39,
            "list": [{"name": "Greenhorn", "unlocked": True}],
        },
        "friendships": [
            {
                "name": "Abigail",
                "points": 2500,
                "hearts": 10,
                "max_hearts": 10,
                "status": "Datable",
                "talked_today": True,
                "gifts_this_week": 1,
                "loved_gifts": ["Amethyst", "Pumpkin"],
            }
        ],
        "artisan": {
            "summary": {
                "total_machines": 207,
                "processing_machines": 190,
                "idle_machines": 9,
                "hibernating_machines": 0,
                "ready_today": 0,
                "ready_tomorrow": 8,
            }
        },
        "chests": {
            "total_chests": 15,
            "total_items": 16149,
            "material_totals": [{"name": "Wood", "count": 999}],
        },
        "crops": {
            "summary": {"total_crops": 384, "ready_today": 84},
            "locations": {
                "farm": {
                    "total_crops": 384,
                    "ready_today": 0,
                    "next_harvest_days": 1,
                    "items": [
                        {
                            "harvest_id": "Powdermelon",
                            "name": "Powdermelon",
                            "icon": "/cache/img/items/Powdermelon.png",
                            "price": 60,
                            "count": 167,
                            "days_to_harvest": 1,
                            "is_recurring": False,
                            "will_wither": False,
                            "total_value": 10020,
                        }
                    ],
                },
                "greenhouse": {"total_crops": 0, "ready_today": 0, "next_harvest_days": None, "items": []},
                "ginger_island": {"total_crops": 0, "ready_today": 0, "next_harvest_days": None, "items": []},
            },
        },
        "tools": {
            "upgradeable": [
                {
                    "key": "Axe",
                    "display_name": "Axe",
                    "current_level": 2,
                    "max_level": 4,
                    "status": "ready",
                    "days_left": 0,
                    "is_max": False,
                    "current_tier": {
                        "name": "Steel Axe",
                        "perks": "Can chop large logs (Secret Woods entry).",
                        "icon_url": "/cache/img/items/T_117.png",
                    },
                    "next_tier": {
                        "level": 3,
                        "name": "Gold Axe",
                        "gold_cost": 10000,
                        "materials": "5x Gold Bar",
                        "icon_url": "/cache/img/items/T_126.png",
                    },
                },
                {
                    "key": "Pickaxe",
                    "display_name": "Pickaxe",
                    "current_level": 3,
                    "max_level": 4,
                    "status": "upgrading",
                    "days_left": 1,
                    "is_max": False,
                    "current_tier": {
                        "name": "Gold Pickaxe",
                        "perks": "Breaks meteorites on the farm.",
                        "icon_url": "/cache/img/items/T_173.png",
                    },
                    "next_tier": {
                        "level": 4,
                        "name": "Iridium Pickaxe",
                        "gold_cost": 25000,
                        "materials": "5x Iridium Bar",
                        "icon_url": "/cache/img/items/T_180.png",
                    },
                },
                {
                    "key": "Hoe",
                    "display_name": "Hoe",
                    "current_level": 2,
                    "max_level": 4,
                    "status": "ready",
                    "days_left": 0,
                    "is_max": False,
                    "current_tier": {
                        "name": "Steel Hoe",
                        "perks": "Tills a 5x1 line when charged.",
                        "icon_url": "/cache/img/items/T_33.png",
                    },
                    "next_tier": {
                        "level": 3,
                        "name": "Gold Hoe",
                        "gold_cost": 10000,
                        "materials": "5x Gold Bar",
                        "icon_url": "/cache/img/items/T_42.png",
                    },
                },
                {
                    "key": "WateringCan",
                    "display_name": "Watering Can",
                    "current_level": 0,
                    "max_level": 4,
                    "status": "ready",
                    "days_left": 0,
                    "is_max": False,
                    "current_tier": {
                        "name": "Watering Can",
                        "perks": "Capacity: 40. Waters 1 tile.",
                        "icon_url": "/cache/img/items/T_147.png",
                    },
                    "next_tier": {
                        "level": 1,
                        "name": "Copper Watering Can",
                        "gold_cost": 2000,
                        "materials": "5x Copper Bar",
                        "icon_url": "/cache/img/items/T_153.png",
                    },
                },
                {
                    "key": "TrashCan",
                    "display_name": "Trash Can",
                    "current_level": 1,
                    "max_level": 4,
                    "status": "ready",
                    "days_left": 0,
                    "is_max": False,
                    "current_tier": {
                        "name": "Copper Trash Can",
                        "perks": "Reclaims 15% of discarded item value.",
                        "icon_url": "/cache/img/items/T_175.png",
                    },
                    "next_tier": {
                        "level": 2,
                        "name": "Steel Trash Can",
                        "gold_cost": 2500,
                        "materials": "5x Iron Bar",
                        "icon_url": "/cache/img/items/T_176.png",
                    },
                },
                {
                    "key": "Pan",
                    "display_name": "Pan",
                    "current_level": 3,
                    "max_level": 3,
                    "status": "maxed",
                    "days_left": 0,
                    "is_max": True,
                    "current_tier": {
                        "name": "Iridium Pan",
                        "perks": "Maximum panning yields and special rewards.",
                        "icon_url": "/cache/img/items/T_15.png",
                    },
                    "next_tier": None,
                },
            ],
            "scythe": {
                "name": "Scythe",
                "current_stage": {
                    "name": "Golden Scythe",
                    "tier": 1,
                    "icon_url": "/cache/img/items/T_252.png",
                    "hint": "Found at the end of the Quarry Mine statue.",
                },
                "is_max": False,
                "next_stage": {
                    "name": "Iridium Scythe",
                    "icon_url": "/cache/img/items/T_251.png",
                    "hint": "Unlocked in the Mastery Cave upon achieving Farming Mastery.",
                },
            },
        },
        "hay": {
            "current_hay": 350,
            "silos_built": 2,
            "max_capacity": 480,
            "total_animals": 16,
            "daily_consumption": 16,
            "required_winter_hay": 448,
            "deficit_amount": 98,
            "capacity_shortfall": 0,
            "days_of_feed_left": 21,
            "has_deficit_warning": True,
            "has_capacity_warning": False,
        },
        "grandpa": {
            "total_score": 14,
            "max_score": 21,
            "candles": 4,
            "statue_unlocked": True,
            "categories": [
                {
                    "id": "earnings",
                    "name": "Farm Earnings",
                    "score": 7,
                    "max_score": 7,
                    "items": [{"label": "1,000,000g Earned", "points": 1, "completed": True}],
                },
                {
                    "id": "skills",
                    "name": "Player Skills",
                    "score": 2,
                    "max_score": 2,
                    "items": [{"label": "Total Skill Levels = 50", "points": 1, "completed": True}],
                },
            ],
        },
        "community_center": {
            "route": "junimo",
            "route_label": "Community Center (Junimo)",
            "is_complete": False,
            "movie_theater": False,
            "completed_bundles": 2,
            "total_bundles": 30,
            "rooms": [
                {
                    "id": 0,
                    "name": "Pantry",
                    "is_complete": False,
                    "bundles": [
                        {
                            "id": 0,
                            "name": "Spring Crops",
                            "color": "green",
                            "is_complete": True,
                            "filled_slots": 4,
                            "total_slots": 4,
                        }
                    ],
                }
            ],
        },
    }
    