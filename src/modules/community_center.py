# src/modules/community_center.py
# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger("community_center")

# Mapping of Community Center Room IDs and Names
ROOM_NAMES = {
    0: "Pantry",
    1: "Crafts Room",
    2: "Fish Tank",
    3: "Boiler Room",
    4: "Vault",
    5: "Bulletin Board",
    6: "Abandoned JojaMart",
}

# Mapping of Room IDs to Bundle IDs
ROOM_BUNDLES = {
    0: [0, 1, 2, 3, 4, 5],            # Pantry
    1: [13, 14, 15, 16, 17, 19],       # Crafts Room
    2: [6, 7, 8, 9, 10, 11],          # Fish Tank
    3: [20, 21, 22],                  # Boiler Room
    4: [23, 24, 25, 26],              # Vault
    5: [31, 32, 33, 34, 35],          # Bulletin Board
    6: [36],                          # Abandoned JojaMart
}

# Standard Junimo Bundle Definitions: (Room ID, Bundle Name, Color Sprite)
BUNDLE_METADATA = {
    # Pantry (Room 0)
    0: {"room_id": 0, "name": "Spring Crops", "color": "green"},
    1: {"room_id": 0, "name": "Summer Crops", "color": "yellow"},
    2: {"room_id": 0, "name": "Fall Crops", "color": "orange"},
    3: {"room_id": 0, "name": "Quality Crops", "color": "teal"},
    4: {"room_id": 0, "name": "Animal", "color": "red"},
    5: {"room_id": 0, "name": "Artisan", "color": "purple"},
    # Crafts Room (Room 1)
    13: {"room_id": 1, "name": "Spring Foraging", "color": "green"},
    14: {"room_id": 1, "name": "Summer Foraging", "color": "yellow"},
    15: {"room_id": 1, "name": "Fall Foraging", "color": "orange"},
    16: {"room_id": 1, "name": "Winter Foraging", "color": "cyan"},
    17: {"room_id": 1, "name": "Construction", "color": "red"},
    19: {"room_id": 1, "name": "Exotic Foraging", "color": "purple"},
    # Fish Tank (Room 2)
    6: {"room_id": 2, "name": "River Fish", "color": "teal"},
    7: {"room_id": 2, "name": "Lake Fish", "color": "green"},
    8: {"room_id": 2, "name": "Ocean Fish", "color": "blue"},
    9: {"room_id": 2, "name": "Night Fishing", "color": "purple"},
    10: {"room_id": 2, "name": "Specialty Fish", "color": "red"},
    11: {"room_id": 2, "name": "Crab Pot", "color": "yellow"},
    # Boiler Room (Room 3)
    20: {"room_id": 3, "name": "Blacksmith's", "color": "orange"},
    21: {"room_id": 3, "name": "Geologist's", "color": "purple"},
    22: {"room_id": 3, "name": "Adventurer's", "color": "red"},
    # Vault (Room 4)
    23: {"room_id": 4, "name": "2,500 Vault", "color": "yellow"},
    24: {"room_id": 4, "name": "5,000 Vault", "color": "orange"},
    25: {"room_id": 4, "name": "10,000 Vault", "color": "red"},
    26: {"room_id": 4, "name": "25,000 Vault", "color": "purple"},
    # Bulletin Board (Room 5)
    31: {"room_id": 5, "name": "Chef's", "color": "red"},
    32: {"room_id": 5, "name": "Dye", "color": "purple"},
    33: {"room_id": 5, "name": "Field Research", "color": "blue"},
    34: {"room_id": 5, "name": "Fodder", "color": "yellow"},
    35: {"room_id": 5, "name": "Enchanter's", "color": "teal"},
    # Abandoned JojaMart (Room 6)
    36: {"room_id": 6, "name": "The Missing Bundle", "color": "purple"},
}

JOJA_PROJECTS = [
    {"id": "jojaGreenhouse", "name": "Greenhouse", "cost": 35000},
    {"id": "jojaMinecart", "name": "Minecart Repair", "cost": 15000},
    {"id": "jojaBridge", "name": "Bridge Repair", "cost": 25000},
    {"id": "jojaPaniere", "name": "Bus Repair", "cost": 40000},
    {"id": "jojaBoulder", "name": "Panning / Glittering Boulder", "cost": 20000},
    {"id": "jojaCinema", "name": "Movie Theater", "cost": 500000},
]


def parse_community_center_data(root, player):
    """
    Parses Community Center or Joja Warehouse progress from save root and player nodes.
    Returns structured details on bundles, rooms, completion percentages, and routes.
    """
    if root is None or player is None:
        return _empty_cc_summary()

    mail_received = {m.text for m in player.findall(".//mailReceived/string") if m.text}
    is_joja = "JojaMember" in mail_received or "jojaMember" in mail_received

    if is_joja:
        return _parse_joja_route(root, player, mail_received)

    return _parse_junimo_route(root, player, mail_received)


def _parse_junimo_route(root, player, mail_received):
    cc_node = root.find(".//locations/GameLocation[@xsi:type='CommunityCenter']", namespaces={"xsi": "http://www.w3.org/2001/XMLSchema-instance"})
    
    if cc_node is None:
        cc_node = root.find(".//GameLocation[name='CommunityCenter']")

    bundle_states = {}
    room_completed_flags = {}

    if cc_node is not None:
        # Extract active bundle status from <bundles>
        bundles_container = cc_node.find("bundles")
        if bundles_container is not None:
            for item in bundles_container.findall("item"):
                key_node = item.find("key/int")
                booleans = [b.text.lower() == "true" for b in item.findall("value/ArrayOfBool/boolean")]
                
                if key_node is not None and key_node.text:
                    try:
                        bundle_id = int(key_node.text)
                        is_complete = len(booleans) > 0 and all(booleans)
                        filled_slots = sum(1 for b in booleans if b)
                        total_slots = len(booleans)
                        bundle_states[bundle_id] = {
                            "is_complete": is_complete,
                            "filled_slots": filled_slots,
                            "total_slots": total_slots,
                        }
                    except ValueError:
                        pass

        # Extract room completion flags (<areasComplete>)
        areas_node = cc_node.find("areasComplete")
        if areas_node is not None:
            for idx, boolean_node in enumerate(areas_node.findall("boolean")):
                room_completed_flags[idx] = boolean_node.text.lower() == "true"

    # Main CC (Rooms 0-5) completion flag
    main_cc_complete = "ccIsComplete" in mail_received or all(
        room_completed_flags.get(r_id, False) for r_id in range(6)
    )

    # Movie theater / Missing Bundle (Room 6) completion flag
    movie_theater_complete = "ccMovieTheater" in mail_received or bundle_states.get(36, {}).get("is_complete", False)

    rooms_dict = {}
    total_bundles = 0
    completed_bundles = 0

    for bundle_id, meta in BUNDLE_METADATA.items():
        room_id = meta["room_id"]
        
        # Room 6 (Abandoned JojaMart) uses movie_theater_complete; Rooms 0-5 use main_cc_complete
        if room_id == 6:
            room_done = room_completed_flags.get(6, False) or movie_theater_complete
        else:
            room_done = room_completed_flags.get(room_id, False) or main_cc_complete

        if room_id not in rooms_dict:
            rooms_dict[room_id] = {
                "id": room_id,
                "name": ROOM_NAMES.get(room_id, "Unknown Room"),
                "is_complete": room_done,
                "bundles": [],
            }

        if room_done:
            is_complete = True
            filled_slots = None
            total_slots = None
        elif bundle_id in bundle_states:
            st = bundle_states[bundle_id]
            is_complete = st["is_complete"]
            filled_slots = st["filled_slots"]
            total_slots = st["total_slots"]
        else:
            # Check if any bundle in this room is active in <bundles>
            room_bundle_ids = ROOM_BUNDLES.get(room_id, [])
            has_active_bundles_in_room = any(b_id in bundle_states for b_id in room_bundle_ids)

            if has_active_bundles_in_room:
                # Active room: missing bundle was completed and purged
                is_complete = True
                filled_slots = None
                total_slots = None
            else:
                # Room is locked, unstarted, or Missing Bundle not triggered yet
                is_complete = False
                filled_slots = 0
                total_slots = 0

        total_bundles += 1
        if is_complete:
            completed_bundles += 1

        rooms_dict[room_id]["bundles"].append({
            "id": bundle_id,
            "name": meta["name"],
            "color": meta["color"],
            "is_complete": is_complete,
            "filled_slots": filled_slots,
            "total_slots": total_slots,
        })

    logger.debug(f"Parsed Junimo CC: {completed_bundles}/{total_bundles} bundles complete.")

    return {
        "route": "junimo",
        "route_label": "Community Center (Junimo)",
        "is_complete": main_cc_complete,
        "movie_theater": movie_theater_complete,
        "completed_bundles": completed_bundles,
        "total_bundles": total_bundles,
        "rooms": list(rooms_dict.values()),
    }


def _parse_joja_route(root, player, mail_received):
    projects = []
    completed_count = 0

    for proj in JOJA_PROJECTS:
        p_id = proj["id"]
        is_done = p_id in mail_received or (p_id == "jojaCinema" and "ccMovieTheater" in mail_received)
        if is_done:
            completed_count += 1

        projects.append({
            "id": p_id,
            "name": proj["name"],
            "cost": proj["cost"],
            "is_complete": is_done,
        })

    is_all_complete = completed_count >= len(projects)

    logger.debug(f"Parsed Joja Route: {completed_count}/{len(projects)} projects complete.")

    return {
        "route": "joja",
        "route_label": "Joja Co. Warehouse",
        "is_complete": is_all_complete,
        "movie_theater": "ccMovieTheater" in mail_received,
        "completed_bundles": completed_count,
        "total_bundles": len(projects),
        "projects": projects,
        "rooms": [],
    }


def _empty_cc_summary():
    return {
        "route": "junimo",
        "route_label": "Community Center (Junimo)",
        "is_complete": False,
        "movie_theater": False,
        "completed_bundles": 0,
        "total_bundles": 31,
        "rooms": [],
    }
    