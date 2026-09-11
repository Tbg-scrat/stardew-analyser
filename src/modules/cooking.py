from src.core.xml_reader import get_key_value

def parse_cooking(player_node):
    """Extract recipesCooked dictionary."""
    recipes_cooked = {}
    recipes_node = player_node.find("recipesCooked")
    if recipes_node is not None:
        for item in recipes_node.findall("item"):
            item_id, val_node = get_key_value(item)
            if item_id and val_node is not None:
                count = val_node.findtext("int", "0")
                recipes_cooked[item_id] = int(count)
    return recipes_cooked
