import sys
import json
import xml.etree.ElementTree as ET

def parse_crop(crop_elem):
    """Extracts raw crop fields from a <crop> XML element."""
    def get_val(tag, default=0):
        node = crop_elem.find(tag)
        return int(node.text) if node is not None and node.text else default

    def get_bool(tag):
        node = crop_elem.find(tag)
        return node is not None and node.text.lower() == "true"

    current_phase = get_val("currentPhase")
    day_of_phase = get_val("dayOfCurrentPhase")
    fully_grown = get_bool("fullyGrown")
    regrow = get_val("regrowAfterHarvest", -1)
    harvest_id = crop_elem.findtext("indexOfHarvest", "Unknown")

    phase_days = []
    phase_node = crop_elem.find("phaseDays")
    if phase_node is not None:
        phase_days = [int(i.text) for i in phase_node.findall("int") if i.text]

    # Calculate Days Until Harvest
    days_remaining = 0
    if fully_grown or (phase_days and current_phase >= len(phase_days) - 1):
        days_remaining = 0  # Ready today
    elif regrow > 0 and current_phase >= len(phase_days) - 1:
        days_remaining = max(0, regrow - day_of_phase)
    else:
        if current_phase < len(phase_days):
            days_remaining += max(0, phase_days[current_phase] - day_of_phase)
            for p in range(current_phase + 1, len(phase_days) - 1):
                days_remaining += phase_days[p]

    return {
        "harvest_id": harvest_id,
        "current_phase": current_phase,
        "day_of_phase": day_of_phase,
        "fully_grown": fully_grown,
        "regrow_after_harvest": regrow,
        "phase_days": phase_days,
        "days_to_harvest": days_remaining
    }

def inspect_save(save_path):
    print(f"Parsing savegame: {save_path}\n")
    tree = ET.parse(save_path)
    root = tree.getroot()

    locations_to_check = {
        "Farm": "Farm",
        "Greenhouse": "Greenhouse",
        "Ginger Island": "IslandWest"
    }

    results = {}

    for label, loc_type in locations_to_check.items():
        all_crops = []
        
        # Search for locations matching the type attribute or name node
        for loc in root.findall(".//locations/GameLocation"):
            type_attr = loc.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
            name_node = loc.findtext("name", "")
            
            if type_attr == loc_type or name_node == loc_type:
                for tf in loc.findall(".//terrainFeatures/item"):
                    val = tf.find("value/TerrainFeature")
                    if val is not None and val.get("{http://www.w3.org/2001/XMLSchema-instance}type") == "HoeDirt":
                        crop = val.find("crop")
                        if crop is not None:
                            all_crops.append(parse_crop(crop))

        # Summarize crops by harvest_id & days_to_harvest
        summary = {}
        for crop in all_crops:
            key = f"{crop['harvest_id']}_days{crop['days_to_harvest']}"
            if key not in summary:
                summary[key] = {**crop, "total_count": 0}
            summary[key]["total_count"] += 1

        # Pick up to 3 sample groups for the location
        samples = list(summary.values())[:3]

        results[label] = {
            "total_crops_found": len(all_crops),
            "sample_crops": samples
        }

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 inspect_crops.py /path/to/SaveGameFile")
        sys.exit(1)
    inspect_save(sys.argv[1])
    