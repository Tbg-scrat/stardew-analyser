# scripts/debug_casks.py
import os
import xml.etree.ElementTree as ET
from pathlib import Path

SAVE_DIR = Path(os.getenv("SAVE_DIR", "/saves"))
if not SAVE_DIR.exists():
    SAVE_DIR = Path("./saves")


def check_active_farmhands(root):
    """
    Scans root <farmhands> and <Building> cabins to verify if any claimed farmhands exist.
    """
    active_farmhands = []

    # 1. Root <farmhands> array (SDV 1.6)
    farmhands_node = root.find("farmhands")
    if farmhands_node is not None:
        for farmer in farmhands_node.findall("Farmer") + farmhands_node.findall("farmhand"):
            name = (farmer.findtext("name") or "").strip()
            try:
                ms_played = int(farmer.findtext("millisecondsPlayed", "0"))
            except ValueError:
                ms_played = 0

            if name and ms_played > 0:
                active_farmhands.append(name)

    # 2. Building cabins
    for building in root.findall(".//Building"):
        b_type = building.findtext("buildingType", "")
        indoors = building.find("indoors")
        indoors_type = indoors.get("{http://www.w3.org/2001/XMLSchema-instance}type", "") if indoors is not None else ""

        if "cabin" in b_type.lower() or "cabin" in indoors_type.lower():
            fh_node = building.find(".//farmhand")
            if fh_node is None and indoors is not None:
                fh_node = indoors.find("farmhand")

            if fh_node is not None:
                name = (fh_node.findtext("name") or "").strip()
                try:
                    ms_played = int(fh_node.findtext("millisecondsPlayed", "0"))
                except ValueError:
                    ms_played = 0

                if name and ms_played > 0 and name not in active_farmhands:
                    active_farmhands.append(name)

    return active_farmhands


def inspect_save_casks(save_path):
    print("=" * 80)
    print(f"INSPECTING SAVE FILE: {save_path.parent.name} / {save_path.name}")
    print("=" * 80)

    try:
        tree = ET.parse(save_path)
        root = tree.getroot()
    except Exception as e:
        print(f"[ERROR] Failed to parse XML: {e}\n")
        return

    # Check Host Player Cellar status
    host_player = root.find("player")
    try:
        host_house_level = int(host_player.findtext("houseUpgradeLevel", "0")) if host_player is not None else 0
    except ValueError:
        host_house_level = 0

    host_cellar_unlocked = host_house_level >= 3
    print(f"Host House Upgrade Level: {host_house_level} (Cellar Unlocked: {host_cellar_unlocked})")

    # Check Farmhand status
    active_farmhands = check_active_farmhands(root)
    has_farmhands = len(active_farmhands) > 0
    print(f"Active Farmhands Found: {len(active_farmhands)} {active_farmhands if has_farmhands else ''}")
    print("-" * 80)

    all_locations = root.findall(".//GameLocation")
    valid_casks_count = 0
    ignored_casks_count = 0

    for idx, loc in enumerate(all_locations):
        loc_name = loc.findtext("name", "Unnamed")
        loc_type = loc.get("{http://www.w3.org/2001/XMLSchema-instance}type", "NoType")

        # Match primary Cellar or secondary CellarN locations
        is_primary_cellar = loc_name == "Cellar" and loc_type == "Cellar"
        is_secondary_cellar = loc_name.startswith("Cellar") and loc_name != "Cellar"

        if not is_primary_cellar and not is_secondary_cellar:
            continue

        objects_node = loc.find("objects")
        if objects_node is None:
            continue

        casks_in_loc = []
        for item in objects_node.findall("item"):
            val = item.find("value")
            if val is None:
                continue
            obj = val.find("Object")
            if obj is None:
                continue

            obj_type = obj.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
            is_big_craftable = obj.findtext("bigCraftable", "").lower() == "true"
            parent_index = obj.findtext("parentSheetIndex", "")

            # Filter for true aging Casks
            if obj_type == "Cask" or (is_big_craftable and parent_index == "163"):
                held = obj.find("heldObject")
                is_nil = held is not None and held.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true"
                held_info = "Empty"
                if held is not None and not is_nil:
                    held_name = held.findtext("displayName") or held.findtext("name") or "Unknown"
                    held_qual = held.findtext("quality", "0")
                    days_mature = obj.findtext("daysToMature", "0")
                    held_info = f"Holding: {held_name} (Qual: {held_qual}, DaysToMature: {days_mature})"

                casks_in_loc.append(held_info)

        if not casks_in_loc:
            continue

        count = len(casks_in_loc)

        # Evaluation Rules:
        # 1. Primary Cellar: Evaluated based on Host House Level >= 3.
        # 2. Secondary Cellars (Cellar2..8): Disregarded whether farmhands are present or not.
        if is_primary_cellar:
            if host_cellar_unlocked:
                valid_casks_count += count
                print(f"✅ [INCLUDED] Location '{loc_name}': {count} Casks (Host Cellar is unlocked)")
            else:
                ignored_casks_count += count
                print(f"🚫 [DISREGARDED] Location '{loc_name}': {count} Casks (Host Cellar not unlocked)")
        elif is_secondary_cellar:
            ignored_casks_count += count
            if not has_farmhands:
                reason = "No active farmhand attached (unbuilt template cellar)"
            else:
                reason = "Secondary farmhand cellar (multiplayer deferred to future milestone)"
            print(f"🚫 [DISREGARDED] Location '{loc_name}': {count} Casks ({reason})")

    print("-" * 80)
    print(f"SUMMARY: Valid Host Casks = {valid_casks_count} | Disregarded Template/Secondary Casks = {ignored_casks_count}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    if not SAVE_DIR.exists():
        print(f"[WARN] Save directory '{SAVE_DIR.resolve()}' does not exist.")
    else:
        saves = [
            item / item.name
            for item in sorted(SAVE_DIR.iterdir())
            if item.is_dir() and not item.name.startswith(".") and (item / item.name).exists()
        ]
        for save_path in saves:
            inspect_save_casks(save_path)
            