# src/core/xml_reader.py
import logging
import os
import time
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


def get_player_node(file_path, retries=3, delay=0.5):
    """
    Parses save XML with retries to gracefully handle temporary file locks
    or mid-write zeroes during sync jobs. Logs detailed DEBUG info on XML structure.
    """
    start_time = time.perf_counter()
    file_path_str = str(file_path)

    # Determine file size for context logging
    file_size_bytes = 0
    if os.path.exists(file_path_str):
        file_size_bytes = os.path.getsize(file_path_str)

    logger.debug(
        f"Attempting XML parse for '{file_path_str}' "
        f"(Size: {file_size_bytes / (1024 * 1024):.2f} MB, Max retries: {retries})"
    )

    for attempt in range(retries):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            if root is None:
                logger.warning(
                    f"Root node is None on attempt {attempt + 1}/{retries} for file '{file_path_str}'"
                )
                raise ET.ParseError("XML root element is None")

            logger.debug(f"XML root element found: <{root.tag}>")

            player = root.find("player")
            if player is None:
                # Attempt fallback check for alternative player location (e.g., direct child vs subnode)
                player = root.find(".//player")
                if player is not None:
                    logger.debug(
                        "Located <player> via deep recursive lookup (.//player)"
                    )

            if player is None:
                logger.warning(
                    f"Missing <player> node in XML root <{root.tag}> on attempt {attempt + 1}/{retries}"
                )
                raise ET.ParseError("Incomplete XML structure: missing <player> node")

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                f"Successfully parsed XML root <{root.tag}> and <player> node from '{file_path_str}' "
                f"in {elapsed_ms:.2f}ms"
            )
            return root, player

        except (ET.ParseError, PermissionError, OSError) as e:
            if attempt < retries - 1:
                logger.debug(
                    f"Attempt {attempt + 1}/{retries} failed for '{file_path_str}' ({type(e).__name__}: {e}). "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
            else:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.error(
                    f"Failed to parse XML from '{file_path_str}' after {retries} attempts "
                    f"({elapsed_ms:.2f}ms elapsed): {e}"
                )
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
        logger.debug("get_key_value called with None item_node")
        return None, None

    key_node = item_node.find("key")
    val_node = item_node.find("value")

    if key_node is None:
        logger.debug(
            f"No <key> node found inside <item> element (Tag: {item_node.tag})"
        )
        return None, val_node

    child = key_node.find("*")
    if child is not None and child.text is not None:
        key_val = child.text.strip()
        logger.debug(f"Extracted typed key '{key_val}' from <key><{child.tag}>")
        return key_val, val_node

    raw_key = key_node.text.strip() if key_node.text else None
    logger.debug(f"Extracted raw key text '{raw_key}' from <key>")
    return raw_key, val_node
