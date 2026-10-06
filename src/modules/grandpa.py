# src/modules/grandpa.py

import logging
import time

from data.data_loader import GRANDPA_CATALOG

logger = logging.getLogger("grandpa")


def parse_grandpa_data(
    root,
    player,
    shipped_items=None,
    fish_caught=None,
    museum_pieces=None,
    friendships=None,
):
    """
    Calculates Grandpa's Evaluation score (max 21 points) and candles earned (1-4).
    Accepts pre-parsed catalog items and friendship records to avoid redundant XML parsing.
    """
    start_time = time.perf_counter()

    if root is None or player is None:
        logger.warning(
            "Root or player XML node is None. Returning default Grandpa evaluation."
        )
        return _empty_grandpa_summary()

    # Default fallbacks for pre-parsed data
    shipped_items = shipped_items or []
    fish_caught = fish_caught or []
    museum_pieces = museum_pieces or []
    friendships = friendships or []

    categories = []

    # 1. Total Farm Earnings (Max 7 points)
    try:
        total_earned = int(player.findtext("totalMoneyEarned", "0"))
    except ValueError:
        logger.debug("Invalid non-integer totalMoneyEarned text; defaulting to 0")
        total_earned = 0

    earnings_thresholds = GRANDPA_CATALOG.get("earnings_thresholds", [])
    earnings_items = []
    earnings_score = 0

    for item in earnings_thresholds:
        threshold = item.get("amount", 0)
        label = item.get("label", f"{threshold:,}g Earned")
        completed = total_earned >= threshold
        if completed:
            earnings_score += 1
        earnings_items.append({"label": label, "points": 1, "completed": completed})

    logger.debug(
        f"Grandpa Category 1 (Earnings): {earnings_score}/7 pts (Total Earned: {total_earned:,}g)"
    )

    categories.append(
        {
            "id": "earnings",
            "name": "Farm Earnings",
            "score": earnings_score,
            "max_score": len(earnings_thresholds),
            "items": earnings_items,
        }
    )

    # 2. Player Skills (Max 2 points)
    farming = _safe_int_child(player, "farmingLevel")
    mining = _safe_int_child(player, "miningLevel")
    combat = _safe_int_child(player, "combatLevel")
    foraging = _safe_int_child(player, "foragingLevel")
    fishing = _safe_int_child(player, "fishingLevel")
    total_skills = farming + mining + combat + foraging + fishing

    skills_thresholds = GRANDPA_CATALOG.get("skills_thresholds", [])
    skills_items = []
    skills_score = 0

    for item in skills_thresholds:
        min_lvl = item.get("min_level", 0)
        completed = total_skills >= min_lvl
        pts = item.get("points", 1)
        if completed:
            skills_score += pts
        skills_items.append(
            {"label": item.get("label", ""), "points": pts, "completed": completed}
        )

    logger.debug(
        f"Grandpa Category 2 (Skills): {skills_score}/2 pts (Total Level: {total_skills}/50)"
    )

    categories.append(
        {
            "id": "skills",
            "name": "Player Skills",
            "score": skills_score,
            "max_score": sum(i.get("points", 1) for i in skills_thresholds),
            "items": skills_items,
        }
    )

    # 3. Collections (Max 3 points)
    shipped_unlocked = len([i for i in shipped_items if i.get("is_unlocked")])
    shipped_total = len(shipped_items)
    full_shipment = shipped_unlocked > 0 and shipped_unlocked >= shipped_total

    fish_unlocked = len([i for i in fish_caught if i.get("is_unlocked")])
    fish_total = len(fish_caught)
    master_angler = fish_unlocked > 0 and fish_unlocked >= fish_total

    museum_unlocked = len([i for i in museum_pieces if i.get("is_unlocked")])
    museum_total = len(museum_pieces)
    complete_museum = museum_unlocked > 0 and museum_unlocked >= museum_total

    collections_status_map = {
        "complete_museum": complete_museum,
        "master_angler": master_angler,
        "full_shipment": full_shipment,
    }

    collections_catalog = GRANDPA_CATALOG.get("collections_items", [])
    collections_items = []
    collections_score = 0

    for item in collections_catalog:
        key = item.get("key")
        completed = collections_status_map.get(key, False)
        pts = item.get("points", 1)
        if completed:
            collections_score += pts
        collections_items.append(
            {"label": item.get("label", ""), "points": pts, "completed": completed}
        )

    logger.debug(
        f"Grandpa Category 3 (Collections): {collections_score}/3 pts "
        f"(Shipped: {full_shipment}, Fish: {master_angler}, Museum: {complete_museum})"
    )

    categories.append(
        {
            "id": "collections",
            "name": "Museum & Collections",
            "score": collections_score,
            "max_score": sum(i.get("points", 1) for i in collections_catalog),
            "items": collections_items,
        }
    )

    # 4. Social & Family (Max 4 points)
    house_upgrade_level = _safe_int_child(player, "houseUpgradeLevel")
    spouse_name = (player.findtext("spouse", "") or "").strip()
    is_married_and_upgraded = house_upgrade_level >= 2 and bool(spouse_name)

    villagers_8_plus = len([f for f in friendships if f.get("points", 0) >= 2000])
    pet_friendship = _extract_pet_friendship(root)

    social_catalog = GRANDPA_CATALOG.get("social_items", {})
    social_items = []
    social_score = 0

    # Marriage & House
    m_info = social_catalog.get("marriage_and_house", {})
    if is_married_and_upgraded:
        social_score += m_info.get("points", 1)
    social_items.append(
        {
            "label": m_info.get("label", "Married + House Upgraded (Nursery)"),
            "points": m_info.get("points", 1),
            "completed": is_married_and_upgraded,
        }
    )

    # 5 Villagers at 8+ Hearts
    v5_info = social_catalog.get("villagers_8_hearts_5", {})
    v5_completed = villagers_8_plus >= v5_info.get("min_count", 5)
    if v5_completed:
        social_score += v5_info.get("points", 1)
    social_items.append(
        {
            "label": v5_info.get("label", "5 Villagers at 8+ Hearts"),
            "points": v5_info.get("points", 1),
            "completed": v5_completed,
        }
    )

    # 10 Villagers at 8+ Hearts
    v10_info = social_catalog.get("villagers_8_hearts_10", {})
    v10_completed = villagers_8_plus >= v10_info.get("min_count", 10)
    if v10_completed:
        social_score += v10_info.get("points", 1)
    social_items.append(
        {
            "label": v10_info.get("label", "10 Villagers at 8+ Hearts"),
            "points": v10_info.get("points", 1),
            "completed": v10_completed,
        }
    )

    # Pet Friendship
    pet_info = social_catalog.get("pet_friendship", {})
    pet_loves_you = pet_friendship >= pet_info.get("min_points", 1000)
    if pet_loves_you:
        social_score += pet_info.get("points", 1)
    social_items.append(
        {
            "label": pet_info.get("label", "Pet Friendship >= 1,000 Points"),
            "points": pet_info.get("points", 1),
            "completed": pet_loves_you,
        }
    )

    logger.debug(
        f"Grandpa Category 4 (Social): {social_score}/4 pts "
        f"(House/Spouse: {is_married_and_upgraded}, 8-Heart Villagers: {villagers_8_plus}, Pet Friendship: {pet_friendship})"
    )

    categories.append(
        {
            "id": "social",
            "name": "Social & Relationships",
            "score": social_score,
            "max_score": 4,
            "items": social_items,
        }
    )

    # 5. Keys & Milestones (Max 5 points)
    has_rusty_key, has_skull_key = _check_keys_status(player)
    cc_complete, cc_ceremony = _check_community_center_progress(root, player)

    milestone_status_map = {
        "rusty_key": has_rusty_key,
        "skull_key": has_skull_key,
        "cc_complete": cc_complete,
        "cc_ceremony": cc_ceremony,
    }

    milestones_catalog = GRANDPA_CATALOG.get("milestones_items", {})
    milestones_items = []
    milestones_score = 0

    for key, meta in milestones_catalog.items():
        completed = milestone_status_map.get(key, False)
        pts = meta.get("points", 1)
        if completed:
            milestones_score += pts
        milestones_items.append(
            {"label": meta.get("label", ""), "points": pts, "completed": completed}
        )

    logger.debug(
        f"Grandpa Category 5 (Milestones): {milestones_score}/5 pts "
        f"(Rusty Key: {has_rusty_key}, Skull Key: {has_skull_key}, CC Complete: {cc_complete}, Ceremony: {cc_ceremony})"
    )

    categories.append(
        {
            "id": "milestones",
            "name": "Keys & Community Center",
            "score": milestones_score,
            "max_score": sum(m.get("points", 1) for m in milestones_catalog.values()),
            "items": milestones_items,
        }
    )

    total_score = sum(cat["score"] for cat in categories)
    max_possible = GRANDPA_CATALOG.get("max_score", 21)
    candles = _calculate_candles(total_score)
    statue_unlocked = candles >= 4

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(
        f"Calculated Grandpa Evaluation: {total_score}/{max_possible} points -> {candles} Candles "
        f"(Parsed in {elapsed_ms:.2f}ms)"
    )

    return {
        "total_score": total_score,
        "max_score": max_possible,
        "candles": candles,
        "statue_unlocked": statue_unlocked,
        "categories": categories,
    }


def _calculate_candles(score):
    thresholds = GRANDPA_CATALOG.get(
        "candle_thresholds",
        [
            {"min_score": 12, "candles": 4},
            {"min_score": 8, "candles": 3},
            {"min_score": 4, "candles": 2},
            {"min_score": 0, "candles": 1},
        ],
    )
    for item in thresholds:
        if score >= item.get("min_score", 0):
            return item.get("candles", 1)
    return 1


def _safe_int_child(element, child_name, default=0):
    node = element.find(child_name)
    if node is not None and node.text is not None:
        try:
            return int(node.text)
        except ValueError:
            logger.debug(f"Invalid integer string for '{child_name}': '{node.text}'")
    return default


def _extract_pet_friendship(root):
    """Locates pet NPC in NPC locations and returns friendship level."""
    for location in root.findall(".//GameLocation"):
        npcs = location.find("characters")
        if npcs is not None:
            for npc in npcs.findall("NPC"):
                npc_type = npc.get(
                    "{http://www.w3.org/2001/XMLSchema-instance}type", ""
                )
                if npc_type in ("Cat", "Dog", "Pet") or npc.tag in (
                    "Cat",
                    "Dog",
                    "Pet",
                ):
                    try:
                        val = int(npc.findtext("friendshipTowardFarmer", "0"))
                        logger.debug(
                            f"Found Pet ({npc_type or npc.tag}) friendship: {val}"
                        )
                        return val
                    except ValueError:
                        return 0
    logger.debug("No Pet NPC found in save file")
    return 0


def _check_keys_status(player):
    """
    Robust key lookup compatible with SDV 1.5 & 1.6+.
    Checks legacy boolean tags, 1.6 <stats> dictionary, mail flags, and events seen.
    """
    mail_received = {
        m.text.lower() for m in player.findall(".//mailReceived/string") if m.text
    }
    events_seen = {e.text for e in player.findall(".//eventsSeen/string") if e.text}
    for e in player.findall(".//eventsSeen/int"):
        if e.text:
            events_seen.add(e.text)

    # 1. Rusty Key Check
    rusty_node = (player.findtext("hasRustyKey") or "").lower() == "true"
    rusty_event = "67" in events_seen
    rusty_mail = any(
        k in mail_received for k in ["hasrustykey", "sewerkey", "gunthersewer"]
    )

    has_rusty_key = rusty_node or rusty_event or rusty_mail

    # 2. Skull Key Check
    skull_node = (player.findtext("hasSkullKey") or "").lower() == "true"
    skull_mail = any(
        k in mail_received for k in ["hasskullkey", "skullkey", "openedskullcavern"]
    )
    skull_event = bool({"901802", "120"} & events_seen)

    # Mine progression check (supporting SDV 1.6 <stats> dictionary)
    deepest_mine = 0
    mine_direct = player.findtext("deepestMineLevel")
    if mine_direct and mine_direct.isdigit():
        deepest_mine = int(mine_direct)

    # SDV 1.6 stores stats inside <stats><stat_dictionary>
    for item in player.findall(".//stats/stat_dictionary/item"):
        key_name = item.findtext("key/string", "")
        if key_name in ("deepestMineLevel", "minesExplored"):
            val = item.findtext("value/int", "0")
            if val.isdigit():
                deepest_mine = max(deepest_mine, int(val))

    skull_mine_progress = deepest_mine >= 120

    has_skull_key = skull_node or skull_mail or skull_event or skull_mine_progress
    logger.debug(
        f"Key status parsed -> Rusty Key: {has_rusty_key}, Skull Key: {has_skull_key} (Deepest Mine: {deepest_mine})"
    )

    return has_rusty_key, has_skull_key


def _check_community_center_progress(root, player):
    """Robust Community Center and ceremony lookup across all mail and event flags."""
    mail_received = {m.text for m in player.findall(".//mailReceived/string") if m.text}

    events_seen = set()
    for e in player.findall(".//eventsSeen/string"):
        if e.text:
            events_seen.add(e.text)
    for e in player.findall(".//eventsSeen/int"):
        if e.text:
            events_seen.add(e.text)

    # 1. Community Center completion check (all 6 areas complete or mail flag)
    areas_completed = False
    cc_node = root.find(
        ".//locations/GameLocation[@xsi:type='CommunityCenter']",
        namespaces={"xsi": "http://www.w3.org/2001/XMLSchema-instance"},
    )
    if cc_node is None:
        cc_node = root.find(".//GameLocation[name='CommunityCenter']")

    if cc_node is not None:
        areas_node = cc_node.find("areasComplete")
        if areas_node is not None:
            booleans = [b.text.lower() == "true" for b in areas_node.findall("boolean")]
            if len(booleans) >= 6 and all(booleans[:6]):
                areas_completed = True

    # 2. Joja Warehouse completion check (all 5 projects funded)
    joja_projects = {
        "jojaGreenhouse",
        "jojaMinecart",
        "jojaBridge",
        "jojaPaniere",
        "jojaBoulder",
    }
    is_joja_member = "JojaMember" in mail_received or "jojaMember" in mail_received
    joja_complete = is_joja_member and joja_projects.issubset(mail_received)

    cc_complete = (
        "ccIsComplete" in mail_received
        or "ccComplete" in mail_received
        or areas_completed
        or joja_complete
    )

    # 3. Re-opening ceremony cutscene check
    # Event 191393/191392 = Community Center Ceremony; Event 502261 = Joja Ceremony
    ceremony_events = {"191393", "191392", "502261"}
    ceremony_mail = {"ccGrandReopening", "ccCeremony", "jojaCeremony"}

    cc_ceremony = bool(
        (ceremony_mail & mail_received) or (ceremony_events & events_seen)
    )

    # Guard clause: Ceremony cannot have occurred if Community Center / Joja isn't completed yet
    if not cc_complete:
        cc_ceremony = False

    return cc_complete, cc_ceremony


def _empty_grandpa_summary():
    return {
        "total_score": 0,
        "max_score": 21,
        "candles": 1,
        "statue_unlocked": False,
        "categories": [],
    }
