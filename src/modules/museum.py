def parse_museum(root_node):
    """Extract LibraryMuseum donated pieces."""
    museum_pieces = {}
    locations = root_node.find("locations")
    if locations is not None:
        for loc in locations.findall("GameLocation"):
            museum_node = loc.find("museumPieces")
            if museum_node is not None:
                for item in museum_node.findall("item"):
                    val_node = item.find("value")
                    if val_node is not None:
                        item_id = val_node.findtext("string") or val_node.findtext("int")
                        if item_id:
                            museum_pieces[str(item_id)] = True
    return list(museum_pieces.keys())
