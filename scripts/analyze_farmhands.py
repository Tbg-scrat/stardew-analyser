# scripts/analyze_farmhands.py
import os
import xml.etree.ElementTree as ET
from pathlib import Path

SAVE_DIR = Path(os.getenv("SAVE_DIR", "/saves"))
if not SAVE_DIR.exists():
    SAVE_DIR = Path("./saves")


def analyze_farmhands(save_path):
    print("=" * 75)
    print(f"SAVE: {save_path.parent.name}")
    print("=" * 75)

    try:
        tree = ET.parse(save_path)
        root = tree.getroot()
    except Exception as e:
        print(f"[ERROR] Failed to parse XML: {e}\n")
        return

    # 1. Primary Host Farmer
    host_player = root.find("player")
    host_name = host_player.findtext("name", "Unknown") if host_player is not None else "Unknown"
    host_house = host_player.findtext("houseUpgradeLevel", "0") if host_player is not None else "0"
    print(f"Host Farmer: {host_name} (House Upgrade Level: {host_house})")

    # 2. Root-level <farmhands> (SDV 1.6 Array)
    root_farmhands = []
    farmhands_node = root.find("farmhands")
    if farmhands_node is not None:
        for farmer in farmhands_node.findall("Farmer") + farmhands_node.findall("farmhand"):
            fh_name = (farmer.findtext("name") or "").strip()
            fh_id = farmer.findtext("uniqueMultiplayerID", "0")
            house_level = farmer.findtext("houseUpgradeLevel", "0")
            try:
                time_played = int(farmer.findtext("millisecondsPlayed", "0"))
            except ValueError:
                time_played = 0

            if fh_name or time_played > 0:
                root_farmhands.append({
                    "name": fh_name if fh_name else "(Unnamed)",
                    "id": fh_id,
                    "house_level": house_level,
                    "hours_played": round(time_played / 3600000, 1)
                })

    # 3. Scan Farm Buildings for Cabins
    cabins = []
    for building in root.findall(".//Building"):
        b_type = building.findtext("buildingType", "")
        indoors = building.find("indoors")
        indoors_type = indoors.get("{http://www.w3.org/2001/XMLSchema-instance}type", "") if indoors is not None else ""

        is_cabin = "cabin" in b_type.lower() or "cabin" in indoors_type.lower()
        if not is_cabin:
            continue

        # Check for farmhand data inside the cabin structure
        fh_node = building.find(".//farmhand")
        if fh_node is None and indoors is not None:
            fh_node = indoors.find("farmhand")

        fh_name = ""
        fh_house = "0"
        time_played = 0

        if fh_node is not None:
            fh_name = (fh_node.findtext("name") or "").strip()
            fh_house = fh_node.findtext("houseUpgradeLevel", "0")
            try:
                time_played = int(fh_node.findtext("millisecondsPlayed", "0"))
            except ValueError:
                time_played = 0

        is_claimed = bool(fh_name) and (time_played > 0 or fh_house != "0")

        cabins.append({
            "building_type": b_type if b_type else "Cabin",
            "occupant": fh_name if fh_name else "(Unclaimed)",
            "is_claimed": is_claimed,
            "house_level": fh_house,
            "hours_played": round(time_played / 3600000, 1)
        })

    print(f"\nRegistered Farmhands (Root Array): {len(root_farmhands)}")
    for fh in root_farmhands:
        print(f"  • {fh['name']} | House Level: {fh['house_level']} | Time Played: {fh['hours_played']}h (ID: {fh['id']})")

    print(f"\nFarm Cabins Detected: {len(cabins)}")
    for c in cabins:
        status_str = f"Occupant: {c['occupant']} (House Level: {c['house_level']})" if c['is_claimed'] else "Unclaimed / Vacant"
        print(f"  • [{c['building_type']}] -> {status_str}")

    if not root_farmhands and not cabins:
        print("  No cabins or farmhands found in this save file.")

    print("\n")


if __name__ == "__main__":
    if not SAVE_DIR.exists():
        print(f"[WARN] Save directory '{SAVE_DIR.resolve()}' does not exist.")
    else:
        saves = [
            item / item.name
            for item in sorted(SAVE_DIR.iterdir())
            if item.is_dir() and not item.name.startswith(".") and (item / item.name).exists()
        ]
        if not saves:
            print(f"[WARN] No valid save directories found in '{SAVE_DIR.resolve()}'.")
        else:
            for save_path in saves:
                analyze_farmhands(save_path)
                