from src.core.xml_reader import get_key_value

def parse_shipping(player_node):
    """Extract basicShipped items register."""
    shipped_items = {}
    basic_shipped = player_node.find("basicShipped")
    if basic_shipped is not None:
        for item in basic_shipped.findall("item"):
            item_id, val_node = get_key_value(item)
            if item_id and val_node is not None:
                count = val_node.findtext("int", "0")
                shipped_items[item_id] = int(count)
    return shipped_items
