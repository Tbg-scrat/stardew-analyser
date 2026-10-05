# -*- coding: utf-8 -*-
# tests/renderer/test_alerts.py

from bs4 import BeautifulSoup
from src.core.renderer import generate_dashboard_html


def test_html_hay_warning_banners_rendering(tmp_path, sample_render_data):
    """Verifies that hay warning banners render conditionally in HTML DOM."""
    # 1. Deficit Warning active, Capacity Warning inactive
    sample_render_data["hay"]["has_deficit_warning"] = True
    sample_render_data["hay"]["has_capacity_warning"] = False

    output_file = tmp_path / "index_deficit.html"
    generate_dashboard_html({"save1": sample_render_data}, output_path=str(output_file))

    soup = BeautifulSoup(output_file.read_text(encoding="utf-8"), "html.parser")
    assert soup.find("div", class_="alert-warning") is not None
    assert soup.find("div", class_="alert-capacity") is None

    # 2. Capacity Warning active, Deficit Warning inactive
    sample_render_data["hay"]["has_deficit_warning"] = False
    sample_render_data["hay"]["has_capacity_warning"] = True

    output_file_cap = tmp_path / "index_capacity.html"
    generate_dashboard_html({"save1": sample_render_data}, output_path=str(output_file_cap))

    soup_cap = BeautifulSoup(output_file_cap.read_text(encoding="utf-8"), "html.parser")
    assert soup_cap.find("div", class_="alert-warning") is None
    assert soup_cap.find("div", class_="alert-capacity") is not None


def test_html_watering_can_opportunity_banner_rendering(tmp_path, sample_render_data):
    """Verifies that the Watering Can Rain Opportunity banner renders conditionally in HTML DOM."""
    # 1. Active Opportunity WITH Festival Pickup Delay
    sample_render_data["watering_can_opportunity"] = {
        "active": True,
        "next_tier_name": "Steel Watering Can",
        "gold_cost": 5000,
        "materials_text": "5x Iron Bar",
        "has_festival_delay": True,
        "pickup_season": "Spring",
        "pickup_day": 13,
    }

    output_file_active = tmp_path / "index_wc_active.html"
    generate_dashboard_html({"save1": sample_render_data}, output_path=str(output_file_active))

    soup_active = BeautifulSoup(output_file_active.read_text(encoding="utf-8"), "html.parser")
    banner = soup_active.find("div", class_="alert-opportunity")
    assert banner is not None, "Watering Can Rain Opportunity banner missing from DOM"

    page_text_active = soup_active.get_text()
    assert "Perfect Day for Watering Can Upgrade!" in page_text_active
    assert "5,000g" in page_text_active
    assert "5x Iron Bar" in page_text_active
    assert "Steel Watering Can" in page_text_active
    assert "Festival Delay:" in page_text_active
    assert "Spring 13" in page_text_active
    assert "Rain does not water crops inside the Greenhouse" in page_text_active

    # 2. Active Opportunity WITHOUT Festival Pickup Delay
    sample_render_data["watering_can_opportunity"]["has_festival_delay"] = False

    output_file_no_fest = tmp_path / "index_wc_no_fest.html"
    generate_dashboard_html({"save1": sample_render_data}, output_path=str(output_file_no_fest))

    soup_no_fest = BeautifulSoup(output_file_no_fest.read_text(encoding="utf-8"), "html.parser")
    page_text_no_fest = soup_no_fest.get_text()
    assert "Perfect Day for Watering Can Upgrade!" in page_text_no_fest
    assert "Festival Delay:" not in page_text_no_fest

    # 3. Inactive Opportunity
    sample_render_data["watering_can_opportunity"] = {"active": False}

    output_file_inactive = tmp_path / "index_wc_inactive.html"
    generate_dashboard_html({"save1": sample_render_data}, output_path=str(output_file_inactive))

    soup_inactive = BeautifulSoup(output_file_inactive.read_text(encoding="utf-8"), "html.parser")
    assert soup_inactive.find("div", class_="alert-opportunity") is None
    page_text_inactive = soup_inactive.get_text()
    assert "Perfect Day for Watering Can Upgrade!" not in page_text_inactive
