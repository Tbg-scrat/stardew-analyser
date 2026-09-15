#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration sanity check for src/modules/achievements.py and parse.py wiring.
"""

import sys
import os
import xml.etree.ElementTree as ET

# Ensure parent path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.data_loader import ACHIEVEMENTS_CATALOG
from src.modules.achievements import parse_achievements

def run_integration_test():
    print("🧪 Running Achievements Parser Integration Check...\n")

    # 1. Create a mock XML <player> node with specific unlocked achievement IDs
    # Mocking unlocked: Greenhorn (0), Millionaire (3), Gourmet Chef (14), Full Shipment (29)
    mock_unlocked_ids = [0, 3, 14, 29]
    
    xml_data = f"""
    <player>
        <name>TestFarmer</name>
        <achievements>
            {''.join(f'<int>{aid}</int>' for aid in mock_unlocked_ids)}
        </achievements>
    </player>
    """
    
    player_elem = ET.fromstring(xml_data)

    # 2. Run module function
    result = parse_achievements(player_elem, ACHIEVEMENTS_CATALOG)

    # 3. Validation checks
    errors = 0

    # Test overall counts
    expected_unlocked = len(mock_unlocked_ids)
    expected_total = len(ACHIEVEMENTS_CATALOG)
    expected_pct = round((expected_unlocked / expected_total) * 100, 1)

    if result["unlocked_count"] != expected_unlocked:
        print(f"❌ Mismatch in unlocked_count: got {result['unlocked_count']}, expected {expected_unlocked}")
        errors += 1

    if result["total_count"] != expected_total:
        print(f"❌ Mismatch in total_count: got {result['total_count']}, expected {expected_total}")
        errors += 1

    if result["percentage"] != expected_pct:
        print(f"❌ Mismatch in percentage: got {result['percentage']}%, expected {expected_pct}%")
        errors += 1

    # Verify unlocked states on individual items
    items_by_id = {item["id"]: item for item in result["items"]}

    for aid in mock_unlocked_ids:
        item = items_by_id.get(aid)
        if not item or not item["unlocked"]:
            print(f"❌ Achievement ID {aid} should be UNLOCKED, but parser reported locked.")
            errors += 1

    # Verify locked states on unearned achievements
    locked_sample_id = 1  # Cowpoke
    locked_item = items_by_id.get(locked_sample_id)
    if not locked_item or locked_item["unlocked"]:
        print(f"❌ Achievement ID {locked_sample_id} should be LOCKED, but parser reported unlocked.")
        errors += 1

    # Output results
    if errors == 0:
        print(f"✅ Integration Check PASSED!")
        print(f"   - Total Catalog Items: {result['total_count']}")
        print(f"   - Unlocked Count:      {result['unlocked_count']}")
        print(f"   - Progress Percentage: {result['percentage']}%")
        print(f"   - Sample Unlocked Item: {items_by_id[0]['name']} (Status: Unlocked)")
        print(f"   - Sample Locked Item:   {items_by_id[1]['name']} (Status: Locked)")
    else:
        print(f"\n❌ Integration Check FAILED with {errors} issue(s)")

if __name__ == "__main__":
    run_integration_test()
    