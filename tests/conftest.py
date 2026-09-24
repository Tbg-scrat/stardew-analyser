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
