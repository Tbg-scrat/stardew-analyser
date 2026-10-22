# src/modules/artisan/utils.py

from src.core.reference_data import get_object_info

QUALITY_MAP = {0: "Normal", 1: "Silver", 2: "Gold", 4: "Iridium"}


def resolve_item_icon(qualified_id, fallback_name=None):
    """
    Resolves the absolute image path directly from reference_data.
    """
    if not qualified_id:
        return "/static/img/placeholder.svg"
        
    obj_info = get_object_info(qualified_id, fallback_name=fallback_name)
    icon_path = obj_info.get("icon")
    
    if not icon_path:
        return "/static/img/placeholder.svg"
        
    return icon_path if icon_path.startswith("/") else f"/{icon_path}"


def get_all_locations(root):
    """
    Recursively scans all GameLocations, including building interiors
    (Sheds, Barns, Coops, Cellar). Yields (loc_name, loc_elem, is_outdoor).
    """
    locations_node = root.find("locations")
    if locations_node is None:
        return

    def _traverse_location(loc_elem, default_name="Unknown", is_indoor=False):
        loc_name = loc_elem.findtext("name") or default_name
        is_outdoor = (
            loc_elem.findtext("isOutdoors", "false").lower() == "true" and not is_indoor
        )
        yield loc_name, loc_elem, is_outdoor

        buildings = loc_elem.find("buildings")
        if buildings is not None:
            for b_idx, building in enumerate(buildings.findall("Building")):
                b_type = building.findtext("buildingType") or "Building"
                indoors = building.find("indoors")
                if indoors is not None:
                    indoor_name = indoors.findtext("name") or f"{b_type} #{b_idx + 1}"
                    yield from _traverse_location(indoors, indoor_name, is_indoor=True)

    for loc in locations_node.findall("GameLocation"):
        yield from _traverse_location(loc)
        