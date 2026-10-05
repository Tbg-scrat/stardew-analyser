# -*- coding: utf-8 -*-
# tests/renderer/test_modules.py

from bs4 import BeautifulSoup
from src.core.renderer import generate_dashboard_html


def test_html_crops_rendering(tmp_path, sample_render_data):
    """Verifies that Crop Tracker tab and crop entries render in HTML DOM."""
    output_file = tmp_path / "index_crops.html"
    generate_dashboard_html({"save1": sample_render_data}, output_path=str(output_file))

    soup = BeautifulSoup(output_file.read_text(encoding="utf-8"), "html.parser")
    page_text = soup.get_text()

    assert "Crop Tracker" in page_text or "Crops" in page_text
    assert "Powdermelon" in page_text
    assert "167x" in page_text


def test_html_tools_rendering(tmp_path, sample_render_data):
    """Verifies that Tools module pane and tool tier entries render cleanly in HTML DOM."""
    output_file = tmp_path / "index_tools.html"
    generate_dashboard_html({"save1": sample_render_data}, output_path=str(output_file))

    soup = BeautifulSoup(output_file.read_text(encoding="utf-8"), "html.parser")
    page_text = soup.get_text()

    assert "Tool Upgrades & Progression" in page_text or "Tools" in page_text
    assert "Steel Axe" in page_text
    assert "Gold Pickaxe" in page_text
    assert "At Clint's (1d left)" in page_text
    assert "Golden Scythe" in page_text
    assert "Iridium Scythe" in page_text


def test_html_grandpa_evaluation_rendering(tmp_path, sample_render_data):
    """Verifies that Grandpa's Evaluation banner and categories render cleanly in HTML DOM."""
    output_file = tmp_path / "index_grandpa.html"
    generate_dashboard_html({"save1": sample_render_data}, output_path=str(output_file))

    soup = BeautifulSoup(output_file.read_text(encoding="utf-8"), "html.parser")

    banner = soup.find("div", class_="grandpa-banner")
    assert banner is not None, "Grandpa banner container missing from DOM"
    assert "statue-unlocked" in banner.get("class", []), "Expected 'statue-unlocked' CSS class on banner"

    page_text = soup.get_text()
    assert "Grandpa's Evaluation" in page_text
    assert "Statue of Perfection Unlocked" in page_text
    assert "Farm Earnings" in page_text
    assert "Player Skills" in page_text


def test_html_community_center_rendering(tmp_path, sample_render_data):
    """Verifies that Community Center status and rooms render in HTML DOM."""
    output_file = tmp_path / "index_cc.html"
    generate_dashboard_html({"save1": sample_render_data}, output_path=str(output_file))

    soup = BeautifulSoup(output_file.read_text(encoding="utf-8"), "html.parser")
    page_text = soup.get_text()

    assert "Community Center (Junimo)" in page_text
    assert "Pantry" in page_text
    assert "Spring Crops" in page_text
