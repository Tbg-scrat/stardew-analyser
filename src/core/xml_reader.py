# src/core/xml_reader.py
import time
import xml.etree.ElementTree as ET


def get_player_node(file_path, retries=3, delay=0.5):
    """
    Parses save XML with retries to gracefully handle temporary file locks
    or mid-write zeroes during sync jobs.
    """
    for attempt in range(retries):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            player = root.find("player")
            if root is not None and player is not None:
                return root, player
            raise ET.ParseError("Incomplete XML structure: missing root or player node")
        except (ET.ParseError, PermissionError, OSError):
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise


def get_key_value(item_node):
    """
    Extracts key identifier and value node from a Stardew XML dictionary <item> element.
    <item>
        <key><string>24</string></key>
        <value><int>10</int></value>
    </item>
    """
    if item_node is None:
        return None, None

    key_node = item_node.find("key")
    val_node = item_node.find("value")

    if key_node is None:
        return None, val_node

    child = key_node.find("*")
    if child is not None and child.text is not None:
        return child.text, val_node

    return key_node.text, val_node
    