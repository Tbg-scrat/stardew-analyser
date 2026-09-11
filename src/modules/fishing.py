from src.core.xml_reader import get_key_value

def parse_fishing(player_node):
    """Extract fishCaught records with quantity and max length."""
    fish_caught = {}
    fish_node = player_node.find("fishCaught")
    if fish_node is not None:
        for item in fish_node.findall("item"):
            item_id, val_node = get_key_value(item)
            if item_id and val_node is not None:
                count, length = 0, 0

                # Fixed DeprecationWarning by testing with 'is not None'
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

                fish_caught[item_id] = {"count": count, "length": length}
    return fish_caught
