# src/modules/grandpa.py
# -*- coding: utf-8 -*-

import logging
import time

logger = logging.getLogger("grandpa")


def parse_grandpa_data(root, player, shipped_items=None, fish_caught=None, museum_pieces=None, friendships=None):
    """
    Calculates Grandpa's Evaluation score (max 21 points) and candles earned (1-4).
    Accepts pre-parsed catalog items and friendship records to avoid redundant XML parsing.
    """
    start_time = time.perf_counter()

    if root is None or player is None:
        logger.warning("Root or player XML node is None. Returning default Grandpa evaluation.")
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

    earnings_thresholds = [
        (50_000, "50,000g Earned"),
        (100_000, "100,000g Earned"),
        (150_000, "150,000g Earned"),
        (200_000, "200,000g Earned"),
        (300_000, "300,000g Earned"),
        (500_000, "500,000g Earned"),
        (1_000_000, "1,000,000g Earned"),
    ]

    earnings_items = []
    earnings_score = 0
    for threshold, label in earnings_thresholds:
        completed = total_earned >= threshold
        if completed:
            earnings_score += 1
        earnings_items.append({"label": label, "points": 1, "completed": completed})

    logger.debug(f"Grandpa Category 1 (Earnings): {earnings_score}/7 pts (Total Earned: {total_earned:,}g)")

    categories.append({
        "id": "earnings",
        "name": "Farm Earnings",
        "score": earnings_score,
        "max_score": 7,
        "items": earnings_items,
    })

    # 2. Player Skills (Max 2 points)
    farming = _safe_int_child(player, "farmingLevel")
    mining = _safe_int_child(player, "miningLevel")
    combat = _safe_int_child(player, "combatLevel")
    foraging = _safe_int_child(player, "foragingLevel")
    fishing = _safe_int_child(player, "fishingLevel")
    total_skills = farming + mining + combat + foraging + fishing

    skill_30 = total_skills >= 30
    skill_50 = total_skills >= 50

    skills_score = (1 if skill_30 else 0) + (1 if skill_50 else 0)
    logger.debug(f"Grandpa Category 2 (Skills): {skills_score}/2 pts (Total Level: {total_skills}/50)")

    categories.append({
        "id": "skills",
        "name": "Player Skills",
        "score": skills_score,
        "max_score": 2,
        "items": [
            {"label": "Total Skill Levels >= 30", "points": 1, "completed": skill_30},
            {"label": "Total Skill Levels = 50 (All Maxed)", "points": 1, "completed": skill_50},
        ],
    })

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

    collections_score = (1 if complete_museum else 0) + (1 if master_angler else 0) + (1 if full_shipment else 0)
    logger.debug(
        f"Grandpa Category 3 (Collections): {collections_score}/3 pts "
        f"(Shipped: {full_shipment}, Fish: {master_angler}, Museum: {complete_museum})"
    )

    categories.append({
        "id": "collections",
        "name": "Museum & Collections",
        "score": collections_score,
        "max_score": 3,
        "items": [
            {"label": "Complete Museum Collection", "points": 1, "completed": complete_museum},
            {"label": "Catch Every Fish (Master Angler)", "points": 1, "completed": master_angler},
            {"label": "Ship Every Item (Full Shipment)", "points": 1, "completed": full_shipment},
        ],
    })

    # 4. Social & Family (Max 4 points)
    house_upgrade_level = _safe_int_child(player, "houseUpgradeLevel")
    spouse_name = (player.findtext("spouse", "") or "").strip()
    is_married_and_upgraded = house_upgrade_level >= 2 and bool(spouse_name)

    villagers_8_plus = len([f for f in friendships if f.get("points", 0) >= 2000])
    has_5_villagers_8_hearts = villagers_8_plus >= 5
    has_10_villagers_8_hearts = villagers_8_plus >= 10

    pet_friendship = _extract_pet_friendship(root)
    pet_loves_you = pet_friendship >= 1000

    social_score = (
        (1 if is_married_and_upgraded else 0)
        + (1 if has_5_villagers_8_hearts else 0)
        + (1 if has_10_villagers_8_hearts else 0)
        + (1 if pet_loves_you else 0)
    )

    logger.debug(
        f"Grandpa Category 4 (Social): {social_score}/4 pts "
        f"(House/Spouse: {is_married_and_upgraded}, 8-Heart Villagers: {villagers_8_plus}, Pet Friendship: {pet_friendship})"
    )

    categories.append({
        "id": "social",
        "name": "Social & Relationships",
        "score": social_score,
        "max_score": 4,
        "items": [
            {"label": "Married + House Upgraded (Nursery)", "points": 1, "completed": is_married_and_upgraded},
            {"label": "5 Villagers at 8+ Hearts", "points": 1, "completed": has_5_villagers_8_hearts},
            {"label": "10 Villagers at 8+ Hearts", "points": 1, "completed": has_10_villagers_8_hearts},
            {"label": "Pet Friendship >= 1,000 Points", "points": 1, "completed": pet_loves_you},
        ],
    })

    # 5. Keys & Milestones (Max 5 points)
    has_rusty_key, has_skull_key = _check_keys_status(player)
    cc_complete, cc_ceremony = _check_community_center_progress(root, player)

    milestones_score = (
        (1 if has_rusty_key else 0)
        + (1 if has_skull_key else 0)
        + (1 if cc_complete else 0)
        + (2 if cc_ceremony else 0)
    )

    logger.debug(
        f"Grandpa Category 5 (Milestones): {milestones_score}/5 pts "
        f"(Rusty Key: {has_rusty_key}, Skull Key: {has_skull_key}, CC Complete: {cc_complete}, Ceremony: {cc_ceremony})"
    )

    categories.append({
        "id": "milestones",
        "name": "Keys & Community Center",
        "score": milestones_score,
        "max_score": 5,
        "items": [
            {"label": "Obtain Rusty Key (Sewer)", "points": 1, "completed": has_rusty_key},
            {"label": "Obtain Skull Key (Mines)", "points": 1, "completed": has_skull_key},
            {"label": "Complete Community Center / Joja Warehouse", "points": 1, "completed": cc_complete},
            {"label": "Attend Community Center Re-opening Ceremony / Joja", "points": 2, "completed": cc_ceremony},
        ],
    })

    total_score = sum(cat["score"] for cat in categories)
    candles = _calculate_candles(total_score)
    statue_unlocked = candles >= 4

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(
        f"Calculated Grandpa Evaluation: {total_score}/21 points -> {candles} Candles "
        f"(Parsed in {elapsed_ms:.2f}ms)"
    )

    return {
        "total_score": total_score,
        "max_score": 21,
        "candles": candles,
        "statue_unlocked": statue_unlocked,
        "categories": categories,
    }


def _calculate_candles(score):
    if score >= 12:
        return 4
    if score >= 8:
        return 3
    if score >= 4:
        return 2
    return 1


def _safe_int_child(element, child_name, default=0):
    node = element.find(child_name)
    if node is not None and node.text is not None:
        try:
            return int(node.text)
        except ValueError:
            logger.debug(f"Invalid integer string for '{child_name}': '{node.text}'")
            pass
    return default


def _extract_pet_friendship(root):
    """Locates pet NPC in NPC locations and returns friendship level."""
    for location in root.findall(".//GameLocation"):
        npcs = location.find("characters")
        if npcs is not None:
            for npc in npcs.findall("NPC"):
                npc_type = npc.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
                if npc_type in ("Cat", "Dog", "Pet") or npc.tag in ("Cat", "Dog", "Pet"):
                    try:
                        val = int(npc.findtext("friendshipTowardFarmer", "0"))
                        logger.debug(f"Found Pet ({npc_type or npc.tag}) friendship: {val}")
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
    mail_received = {m.text.lower() for m in player.findall(".//mailReceived/string") if m.text}
    events_seen = {e.text for e in player.findall(".//eventsSeen/string") if e.text}
    for e in player.findall(".//eventsSeen/int"):
        if e.text:
            events_seen.add(e.text)

    # 1. Rusty Key Check
    rusty_node = (player.findtext("hasRustyKey") or "").lower() == "true"
    rusty_event = "67" in events_seen
    rusty_mail = any(k in mail_received for k in ["hasrustykey", "sewerkey", "gunthersewer"])

    has_rusty_key = rusty_node or rusty_event or rusty_mail

    # 2. Skull Key Check
    skull_node = (player.findtext("hasSkullKey") or "").lower() == "true"
    skull_mail = any(k in mail_received for k in ["hasskullkey", "skullkey", "openedskullcavern"])
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
    logger.debug(f"Key status parsed -> Rusty Key: {has_rusty_key}, Skull Key: {has_skull_key} (Deepest Mine: {deepest_mine})")

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
    cc_node = root.find(".//locations/GameLocation[@xsi:type='CommunityCenter']", namespaces={"xsi": "http://www.w3.org/2001/XMLSchema-instance"})
    if cc_node is None:
        cc_node = root.find(".//GameLocation[name='CommunityCenter']")

    if cc_node is not None:
        areas_node = cc_node.find("areasComplete")
        if areas_node is not None:
            booleans = [b.text.lower() == "true" for b in areas_node.findall("boolean")]
            if len(booleans) >= 6 and all(booleans[:6]):
                areas_completed = True

    # 2. Joja Warehouse completion check (all 5 projects funded)
    joja_projects = {"jojaGreenhouse", "jojaMinecart", "jojaBridge", "jojaPaniere", "jojaBoulder"}
    is_joja_member = "JojaMember" in mail_received or "jojaMember" in mail_received
    joja_complete = is_joja_member and joja_projects.issubset(mail_received)

    cc_complete = "ccIsComplete" in mail_received or "ccComplete" in mail_received or areas_completed or joja_complete

    # 3. Re-opening ceremony cutscene check
    # Event 191393/191392 = Community Center Ceremony; Event 502261 = Joja Ceremony
    ceremony_events = {"191393", "191392", "502261"}
    ceremony_mail = {"ccGrandReopening", "ccCeremony", "jojaCeremony"}

    cc_ceremony = bool((ceremony_mail & mail_received) or (ceremony_events & events_seen))

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
    