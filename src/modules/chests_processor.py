# src/modules/chests_processor.py


def process_chest_data(raw_chests):
  """Aggregates chest data and calculates total material quantities across all locations,

  skipping empty inventory slots (`is_empty: True`).
  """
  material_totals = {}

  if not raw_chests or "chests" not in raw_chests:
    return {
        "total_chests": 0,
        "total_items": 0,
        "chests": [],
        "material_totals": [],
    }

  for chest in raw_chests.get("chests", []):
    for item in chest.get("chest_items", []):
      # Skip empty slot placeholders
      if item.get("is_empty"):
        continue

      item_name = item.get("name", "Unknown Item")
      stack = item.get("stack", 1)
      sprite_key = item.get("sprite_key", "")

      if item_name not in material_totals:
        material_totals[item_name] = {
            "name": item_name,
            "count": 0,
            "sprite_key": sprite_key,
        }

      material_totals[item_name]["count"] += stack

  # Sort aggregated materials by highest total count
  sorted_materials = sorted(
      material_totals.values(), key=lambda x: x["count"], reverse=True
  )

  return {
      "total_chests": raw_chests.get("total_chests", 0),
      "total_items": raw_chests.get("total_items", 0),
      "chests": raw_chests.get("chests", []),
      "material_totals": sorted_materials,
  }
  