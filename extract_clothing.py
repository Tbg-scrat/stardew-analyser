# scripts/extract_clothing.py
import json
import os

SOURCE_DIR = "/srv/docker/data/sv-analyzer/Content (unpacked)/Data"
OUTPUT_DIR = "data"

TARGETS = {
    "Pants.json": "pants.json",
    "Shirts.json": "shirts.json",
    "Boots.json": "boots.json",
}


def parse_entry(key, raw_value):
    name = f"Item {key}"
    description = ""

    if isinstance(raw_value, dict):
        name = raw_value.get("Name", raw_value.get("name", name))
        description = raw_value.get("Description", raw_value.get("description", ""))
    elif isinstance(raw_value, str):
        parts = raw_value.split("/")
        if len(parts) >= 1 and parts[0]:
            name = parts[0]
        if len(parts) >= 2 and parts[1]:
            description = parts[1]

    # Clean up localization tokens like "[LocalizedText ...]"
    if description.startswith("[") and "]" in description:
        description = ""

    return {"name": name, "description": description}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for src_filename, out_filename in TARGETS.items():
        src_path = os.path.join(SOURCE_DIR, src_filename)
        out_path = os.path.join(OUTPUT_DIR, out_filename)

        if not os.path.exists(src_path):
            print(f"[WARNING] Source file not found: {src_path}. Skipping.")
            continue

        try:
            with open(src_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            catalog = {}
            if isinstance(raw_data, dict):
                for k, v in raw_data.items():
                    catalog[str(k)] = parse_entry(k, v)
            elif isinstance(raw_data, list):
                for k, v in enumerate(raw_data):
                    catalog[str(k)] = parse_entry(k, v)

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(catalog, f, indent=2)

            print(
                f"[SUCCESS] Extracted {len(catalog)} items from {src_filename} -> {out_filename}"
            )

        except Exception as e:
            print(f"[ERROR] Failed to process {src_filename}: {e}")


if __name__ == "__main__":
    main()
    