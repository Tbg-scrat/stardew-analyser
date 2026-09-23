# src/modules/fishing.py

from src.core.xml_reader import get_key_value


def format_wiki_filename(name):
    """Clean item names into Stardew Valley Wiki image file conventions."""
    if not name:
        return ""
    return name.replace(" ", "_").replace("'", "%27")


def parse_fishing(player_node):
    """Extract fishCaught records with quantity and max length."""
    fish_caught = {}
    fish_node = player_node.find("fishCaught")
    if fish_node is not None:
        for item in fish_node.findall("item"):
            item_id, val_node = get_key_value(item)
            if item_id and val_node is not None:
                count, length = 0, 0

                array_node = val_node.find("ArrayOfInt")
                if array_node is None:
                    array_node = val_node.find("ArrayOfint")

                if array_node is not None:
                    ints = array_node.findall("int")
                    if len(ints) > 0 and ints[0].text:
                        count = int(ints[0].text)
                    if len(ints) > 1 and ints[1].text:
                        length = int(ints[1].text)
                else:
                    int_val = val_node.findtext("int")
                    if int_val:
                        count = int(int_val)

                fish_caught[str(item_id)] = {"count": count, "length": length}
    return fish_caught


def get_formatted_fishing(player_node, catalog):
    """
    Parses fishing save data and merges it against FISH_CATALOG,
    returning a sorted list of fish item dictionaries ready for the UI.
    """
    raw_fish = parse_fishing(player_node)
    fish_save_map = {str(k).replace("(O)", ""): v for k, v in raw_fish.items()}

    fish_mapped = []
    catalog_items = catalog.items() if isinstance(catalog, dict) else []

    for item_id, catalog_item in catalog_items:
        if not isinstance(catalog_item, dict):
            continue

        stats = fish_save_map.get(str(item_id))
        is_caught = stats is not None
        item_name = catalog_item.get("name", f"Fish {item_id}")

        fish_mapped.append({
            "id": item_id,
            "name": item_name,
            "count": stats["count"] if is_caught else 0,
            "length": stats["length"] if is_caught else 0,
            "status": "caught" if is_caught else "not_caught",
            "is_unlocked": is_caught,
            "image": catalog_item.get("image", ""),
            "wiki_icon": format_wiki_filename(item_name),
        })

    return sorted(fish_mapped, key=lambda x: x["name"])
    