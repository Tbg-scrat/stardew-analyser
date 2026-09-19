# src/modules/chests_processor.py


def process_chest_data(raw_chest_data):
  total_materials = {}
  chests_summary = raw_chest_data.get("chests", [])

  for chest in chests_summary:
    for item in chest.get("chest_items", []):  # <-- Updated key here
      name = item["name"]
      stack = item["stack"]
      total_materials[name] = total_materials.get(name, 0) + stack

  return {
      "total_chests": raw_chest_data.get("total_chests", 0),
      "total_items": raw_chest_data.get("total_items", 0),
      "chests": chests_summary,
      "material_totals": total_materials,
  }
  