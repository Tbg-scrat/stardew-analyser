import xml.etree.ElementTree as ET

def get_player_node(file_path):
    """Parse save file and return root and player nodes."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    player = root.find("player")
    if player is None:
        raise ValueError("Invalid save file: <player> tag not found.")
    return root, player

def get_key_value(item_node):
    """Extract key/value pair from a Stardew XML dictionary item node."""
    key_node = item_node.find("key")
    val_node = item_node.find("value")
    if key_node is not None and val_node is not None:
        key = key_node.findtext("string") or key_node.findtext("int")
        return str(key) if key else None, val_node
    return None, None
