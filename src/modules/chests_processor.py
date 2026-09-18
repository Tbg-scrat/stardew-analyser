def process_chest_data(raw_chest_data):
    """
    Takes raw extracted chest data from parsers.chests and computes:
    - Global totals per item across all chests
    - Formatted chest summaries for dashboard display
    """
    total_materials = {}
    chests_summary = raw_chest_data.get("chests", [])

    for chest in chests_summary:
        for item in chest.get("items", []):
            name = item["name"]
            stack = item["stack"]
            
            # Aggregate total quantities across all chests
            total_materials[name] = total_materials.get(name, 0) + stack

    return {
        "total_chests": raw_chest_data.get("total_chests", 0),
        "total_items": raw_chest_data.get("total_items", 0),
        "chests": chests_summary,
        "material_totals": total_materials
    }
    