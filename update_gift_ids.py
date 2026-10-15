import argparse
import json
import pathlib
import sys


def build_name_to_id_map(objects_path: pathlib.Path) -> dict:
    """Build a normalized mapping from item display names to O_<Key> identifiers."""
    if not objects_path.exists():
        print(f"[ERROR] {objects_path} does not exist!")
        sys.exit(1)

    objects_data = json.loads(objects_path.read_text(encoding="utf-8"))
    name_map = {}

    for key, details in objects_data.items():
        if isinstance(details, dict):
            item_name = details.get("Name")
            if item_name:
                oid = key if key.startswith("O_") else f"O_{key}"
                name_map[item_name.lower().strip()] = (oid, item_name)

    return name_map


def main():
    parser = argparse.ArgumentParser(
        description="Map villager gift names in villagers.json to exact O_IDs from objects.json"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write updated IDs to data/villagers.json (defaults to dry-run preview)",
    )
    args = parser.parse_args()

    dry_run = not args.apply
    objects_path = pathlib.Path("data/objects.json")
    villagers_path = pathlib.Path("data/villagers.json")

    if not villagers_path.exists():
        print(f"[ERROR] {villagers_path} does not exist!")
        sys.exit(1)

    name_to_id = build_name_to_id_map(objects_path)
    villagers_data = json.loads(villagers_path.read_text(encoding="utf-8"))

    unmatched = []
    updated_count = 0

    mode_label = "DRY RUN (Preview Only)" if dry_run else "APPLYING CHANGES"
    print(f"=== {mode_label} ===\n")

    villagers = villagers_data.get("villagers", {})
    for villager_name, v_data in villagers.items():
        gifts = v_data.get("loved_gifts", [])
        updated_gifts = []

        for gift in gifts:
            if isinstance(gift, dict):
                gift_name = gift.get("name", "")
                current_id = gift.get("id", "N/A")
            else:
                gift_name = str(gift)
                current_id = "N/A"

            norm_name = gift_name.lower().strip()

            if norm_name in name_to_id:
                target_oid, canonical_name = name_to_id[norm_name]
                updated_gift = {"id": target_oid, "name": canonical_name}

                if current_id != target_oid:
                    print(f"[{villager_name}] '{gift_name}': {current_id} -> {target_oid}")
                    updated_count += 1

                updated_gifts.append(updated_gift)
            else:
                print(f"[WARNING] [{villager_name}] Gift '{gift_name}' NOT FOUND in objects.json!")
                unmatched.append((villager_name, gift_name))
                updated_gifts.append(gift)

        v_data["loved_gifts"] = updated_gifts

    print(f"\n--- Summary ---")
    print(f"Total IDs mapped/updated: {updated_count}")
    print(f"Total gifts unmatched:    {len(unmatched)}")

    if not dry_run:
        villagers_path.write_text(json.dumps(villagers_data, indent=2), encoding="utf-8")
        print(f"\n[SUCCESS] Wrote changes to {villagers_path}")
    else:
        print(f"\n[INFO] Dry run complete. Run with '--apply' to write changes.")


if __name__ == "__main__":
    main()
