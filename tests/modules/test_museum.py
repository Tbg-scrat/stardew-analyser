# -*- coding: utf-8 -*-
# tests/modules/test_museum.py

import xml.etree.ElementTree as ET
from src.modules.museum import (
    format_wiki_filename,
    get_formatted_museum,
    parse_museum,
)


def test_format_wiki_filename():
    """Verifies image filename string formatting for museum items."""
    assert format_wiki_filename("") == ""
    assert format_wiki_filename("Prehistoric Scapula") == "Prehistoric_Scapula"


def test_parse_museum_none_and_empty():
    """Verifies return values when SaveGame root or locations node is missing."""
    assert parse_museum(None) == []

    empty_root = ET.fromstring("<SaveGame></SaveGame>")
    assert parse_museum(empty_root) == []

    no_museum_root = ET.fromstring(
        "<SaveGame><locations><GameLocation><name>Farm</name></GameLocation></locations></SaveGame>"
    )
    assert parse_museum(no_museum_root) == []


def test_parse_museum_donations():
    """Verifies extraction of donated artifact/mineral IDs from museumPieces nodes."""
    xml_data = """
    <SaveGame>
        <locations>
            <GameLocation>
                <name>Town</name>
            </GameLocation>
            <GameLocation>
                <name>LibraryMuseum</name>
                <museumPieces>
                    <item>
                        <key><Vector2><X>1</X><Y>2</Y></Vector2></key>
                        <value><string>579</string></value>
                    </item>
                    <item>
                        <key><Vector2><X>3</X><Y>4</Y></Vector2></key>
                        <value><int>580</int></value>
                    </item>
                    <item>
                        <key><Vector2><X>5</X><Y>6</Y></Vector2></key>
                        <value></value>
                    </item>
                </museumPieces>
            </GameLocation>
        </locations>
    </SaveGame>
    """
    root = ET.fromstring(xml_data)
    donated = parse_museum(root)

    assert "579" in donated
    assert "580" in donated
    assert len(donated) == 2


def test_get_formatted_museum_catalog_merge():
    """Verifies museum donation status mapping against catalog metadata."""
    xml_data = """
    <SaveGame>
        <locations>
            <GameLocation>
                <museumPieces>
                    <item>
                        <value><string>579</string></value>
                    </item>
                </museumPieces>
            </GameLocation>
        </locations>
    </SaveGame>
    """
    root = ET.fromstring(xml_data)
    custom_catalog = {
        "579": {"name": "Prehistoric Scapula", "type": "Artifact"},
        "580": {"name": "Prehistoric Tibia", "type": "Artifact"},
        "bad_entry": None,
    }

    results = get_formatted_museum(root, catalog=custom_catalog)

    assert len(results) == 2
    scapula = next(item for item in results if item["id"] == "579")
    assert scapula["is_unlocked"] is True
    assert scapula["status"] == "found"

    tibia = next(item for item in results if item["id"] == "580")
    assert tibia["is_unlocked"] is False
    assert tibia["status"] == "not_found"
