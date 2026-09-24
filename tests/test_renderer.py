# -*- coding: utf-8 -*-
# tests/test_renderer.py

import pytest
from bs4 import BeautifulSoup
from src.core.renderer import generate_dashboard_html


@pytest.fixture
def sample_render_data():
    """Provides a realistic single save data dictionary for renderer tests."""
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
    }


def test_html_file_creation(tmp_path, sample_render_data):
    """Verifies that generate_dashboard_html writes output file to disk."""
    output_file = tmp_path / "index.html"
    generate_dashboard_html({"save1": sample_render_data}, output_path=str(output_file))

    assert output_file.exists(), "Rendered index.html file was not created on disk."
    assert output_file.stat().st_size > 0, "Rendered index.html file is empty."


def test_html_metadata_and_text_content(tmp_path, sample_render_data):
    """Verifies farmer, farm name, and core money/date values exist in rendered DOM."""
    output_file = tmp_path / "index.html"
    generate_dashboard_html({"save1": sample_render_data}, output_path=str(output_file))

    soup = BeautifulSoup(output_file.read_text(encoding="utf-8"), "html.parser")
    page_text = soup.get_text()

    assert "Nils" in page_text
    assert "Friisen" in page_text
    assert "1,138,180" in page_text or "1138180" in page_text
    assert "George" in page_text
    assert "Spirits' Eve" in page_text


def test_html_navigation_and_sections(tmp_path, sample_render_data):
    """Verifies navigation structural elements or section containers render in the HTML."""
    output_file = tmp_path / "index.html"
    generate_dashboard_html({"save1": sample_render_data}, output_path=str(output_file))

    soup = BeautifulSoup(output_file.read_text(encoding="utf-8"), "html.parser")

    assert soup.find("html") is not None
    assert soup.find("head") is not None
    assert soup.find("body") is not None

    all_text = soup.get_text().lower()
    for section_kw in ["achievements", "shipped", "fish", "artisan", "chests"]:
        assert section_kw in all_text, f"Expected '{section_kw}' content in rendered HTML"


def test_html_multi_save_rendering(tmp_path, sample_render_data):
    """Verifies that rendering multiple save profiles includes data from all farmers."""
    save_2 = dict(sample_render_data)
    save_2["farmer"] = "Amalia"
    save_2["farm"] = "Amali"

    saves_map = {
        "Friisen_12345": sample_render_data,
        "Amali_67890": save_2,
    }

    output_file = tmp_path / "index.html"
    generate_dashboard_html(saves_map, output_path=str(output_file))

    soup = BeautifulSoup(output_file.read_text(encoding="utf-8"), "html.parser")
    page_text = soup.get_text()

    assert "Nils" in page_text
    assert "Friisen" in page_text
    assert "Amalia" in page_text
    assert "Amali" in page_text
