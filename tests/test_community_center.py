# tests/test_community_center.py
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import pytest
from src.modules.community_center import parse_community_center_data, BUNDLE_METADATA


def _build_cc_mock_xml(is_joja=False, completed_bundles=None, mail=None):
    mail = mail or []
    if is_joja:
        mail.append("JojaMember")

    root = ET.Element("SaveGame")
    locs = ET.SubElement(root, "locations")
    cc = ET.SubElement(locs, "GameLocation")
    cc.set("{http://www.w3.org/2001/XMLSchema-instance}type", "CommunityCenter")
    ET.SubElement(cc, "name").text = "CommunityCenter"

    bundles_node = ET.SubElement(cc, "bundles")

    completed_bundles = set(completed_bundles or [])

    # In actual SDV saves, uncompleted bundles remain in <bundles> as false booleans,
    # while completed bundles are purged from <bundles> by the game engine.
    for b_id in BUNDLE_METADATA.keys():
        if b_id in completed_bundles:
            continue  # Purged upon completion

        item = ET.SubElement(bundles_node, "item")
        key = ET.SubElement(item, "key")
        ET.SubElement(key, "int").text = str(b_id)
        
        val = ET.SubElement(item, "value")
        arr = ET.SubElement(val, "ArrayOfBool")
        ET.SubElement(arr, "boolean").text = "false"

    player = ET.Element("player")
    mail_node = ET.SubElement(player, "mailReceived")
    for m in mail:
        ET.SubElement(mail_node, "string").text = m

    return root, player


def test_cc_none_handling():
    res = parse_community_center_data(None, None)
    assert res["route"] == "junimo"
    assert res["completed_bundles"] == 0
    assert res["is_complete"] is False


def test_cc_junimo_partial_progress():
    # Complete Spring Crops (0) and Spring Foraging (13)
    root, player = _build_cc_mock_xml(completed_bundles=[0, 13])
    res = parse_community_center_data(root, player)

    assert res["route"] == "junimo"
    assert res["completed_bundles"] == 2
    assert res["is_complete"] is False
    assert len(res["rooms"]) > 0

    pantry = next(r for r in res["rooms"] if r["name"] == "Pantry")
    spring_crop = next(b for b in pantry["bundles"] if b["id"] == 0)
    assert spring_crop["is_complete"] is True


def test_cc_joja_route():
    root, player = _build_cc_mock_xml(is_joja=True, mail=["jojaGreenhouse", "jojaBridge"])
    res = parse_community_center_data(root, player)

    assert res["route"] == "joja"
    assert res["route_label"] == "Joja Co. Warehouse"
    assert res["completed_bundles"] == 2
    assert len(res["projects"]) == 6
    