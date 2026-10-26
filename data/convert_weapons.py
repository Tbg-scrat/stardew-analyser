# convert_weapons.py

import json
from pathlib import Path


def slim_down_weapons(input_path="Weapons.json", output_path="data/weapons.json"):
    src_file = Path(input_path)
    if not src_file.exists():
        print(f"Fehler: {input_path} wurde nicht gefunden.")
        return

    with open(src_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    slimmed_data = {}

    for item_id, data in raw_data.items():
        name = data.get("Name", "Unknown Weapon")
        sprite_index = data.get("SpriteIndex", int(item_id))

        slimmed_data[item_id] = {
            "name": name,
            "sprite_index": sprite_index,
            "sprite_key": f"W_{sprite_index}",
        }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(slimmed_data, f, indent=2, ensure_ascii=False)

    print(f"Erfolgreich {len(slimmed_data)} Waffen nach {output_path} konvertiert!")


if __name__ == "__main__":
    slim_down_weapons()
