from src.core.xml_reader import get_key_value


def parse_shipping(player_node):
    """Extract basicShipped item counts from the player XML node."""
    shipped_items = {}
    basic_shipped = player_node.find("basicShipped")
    if basic_shipped is not None:
        for item in basic_shipped.findall("item"):
            item_id, val_node = get_key_value(item)
            if item_id and val_node is not None:
                count = val_node.findtext("int", "0")
                shipped_items[str(item_id)] = int(count)
    return shipped_items


def get_formatted_shipping(player_node, catalog):
    """Parses save data and maps it against shipping catalog metadata for the UI."""
    raw_shipped_data = parse_shipping(player_node)
    formatted_items = []

    # If catalog is a list, convert to dict keyed by ID or item name
    if isinstance(catalog, list):
        catalog_dict = {
            str(item.get("id")): item for item in catalog if isinstance(item, dict)
        }
    elif isinstance(catalog, dict):
        catalog_dict = catalog
    else:
        catalog_dict = {}

    for item_id, catalog_item in catalog_dict.items():
        if not isinstance(catalog_item, dict):
            continue

        shipped_count = raw_shipped_data.get(str(item_id), 0)
        status = "shipped" if shipped_count > 0 else "not_shipped"

        formatted_items.append({
            "id": item_id,
            "name": catalog_item.get("name", f"Item {item_id}"),
            "status": status,
            "count": shipped_count,
            "achievement_required": catalog_item.get(
                "achievement_required", False
            ),
            "is_polyculture": catalog_item.get("is_polyculture", False),
            "wiki_icon": catalog_item.get("icon", ""),
            "image": catalog_item.get("image", None),
        })

    return formatted_items
    