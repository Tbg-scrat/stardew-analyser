# -*- coding: utf-8 -*-
# tests/core/test_xml_reader.py

import xml.etree.ElementTree as ET
import pytest
from src.core.xml_reader import get_key_value, get_player_node


def test_get_key_value_none():
    """Verifies get_key_value when item_node is None."""
    key, val = get_key_value(None)
    assert key is None
    assert val is None


def test_get_key_value_no_key_node():
    """Verifies get_key_value when <key> node is omitted."""
    item = ET.fromstring("<item><value><int>10</int></value></item>")
    key, val = get_key_value(item)
    assert key is None
    assert val is not None
    assert val.findtext("int") == "10"


def test_get_key_value_typed_child_key():
    """Verifies key extraction from nested child elements (e.g. <key><string>24</string></key>)."""
    item = ET.fromstring("<item><key><string>24</string></key><value><int>10</int></value></item>")
    key, val = get_key_value(item)
    assert key == "24"
    assert val is not None


def test_get_key_value_raw_text_key():
    """Verifies key extraction from raw text inside <key> nodes without child elements."""
    item = ET.fromstring("<item><key>24</key><value><int>10</int></value></item>")
    key, val = get_key_value(item)
    assert key == "24"


def test_get_key_value_empty_key_nodes():
    """Verifies fallback when <key> or child text is empty."""
    item_empty = ET.fromstring("<item><key></key><value><int>10</int></value></item>")
    key, _ = get_key_value(item_empty)
    assert key is None

    item_empty_child = ET.fromstring("<item><key><string></string></key><value><int>10</int></value></item>")
    key_child, _ = get_key_value(item_empty_child)
    assert key_child is None


def test_get_player_node_valid(tmp_path):
    """Verifies successful parsing of standard XML with root <player> child."""
    save_file = tmp_path / "SaveGame.xml"
    save_file.write_text("<SaveGame><player><name>Bob</name></player></SaveGame>")

    root, player = get_player_node(save_file, retries=1)
    assert root.tag == "SaveGame"
    assert player.findtext("name") == "Bob"


def test_get_player_node_nested_fallback(tmp_path):
    """Verifies recursive fallback (.//player) when <player> is nested deep inside the tree."""
    save_file = tmp_path / "NestedSave.xml"
    save_file.write_text("<SaveGame><wrapper><player><name>Alice</name></player></wrapper></SaveGame>")

    root, player = get_player_node(save_file, retries=1)
    assert root.tag == "SaveGame"
    assert player.findtext("name") == "Alice"


def test_get_player_node_missing_player(tmp_path):
    """Verifies ParseError exception and retry exhaustion when <player> is missing."""
    save_file = tmp_path / "InvalidSave.xml"
    save_file.write_text("<SaveGame><world></world></SaveGame>")

    with pytest.raises(ET.ParseError, match="missing <player> node"):
        get_player_node(save_file, retries=2, delay=0.001)


def test_get_player_node_malformed_xml(tmp_path):
    """Verifies retry exhaustion when XML syntax is malformed."""
    save_file = tmp_path / "Corrupted.xml"
    save_file.write_text("<SaveGame><player>")

    with pytest.raises(ET.ParseError):
        get_player_node(save_file, retries=2, delay=0.001)


def test_get_player_node_nonexistent_file(tmp_path):
    """Verifies OSError handling when file does not exist."""
    nonexistent = tmp_path / "Does_Not_Exist.xml"

    with pytest.raises(OSError):
        get_player_node(nonexistent, retries=2, delay=0.001)
