# src/modules/grandpa.py
# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger("grandpa")


def parse_grandpa_data(root, player, shipped_items=None, fish_caught=None, museum_pieces=None, friendships=None):
    """
    Calculates Grandpa's Evaluation score (max 21 points) and candles earned (1-4).
    Accepts pre-parsed catalog items and friendship records to avoid redundant XML parsing.
    """
    if root is None or player is None:
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
    spouse_name = player.findtext("spouse", "").strip()
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
    has_rusty_key = player.findtext("hasRustyKey", "false").lower() == "true"
    has_skull_key = player.findtext("hasSkullKey", "false").lower() == "true"

    cc_complete, cc_ceremony = _check_community_center_progress(root, player)

    milestones_score = (
        (1 if has_rusty_key else 0)
        + (1 if has_skull_key else 0)
        + (1 if cc_complete else 0)
        + (2 if cc_ceremony else 0)
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

    logger.debug(f"Calculated Grandpa Evaluation: {total_score}/21 points -> {candles} Candles")

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
                        return int(npc.findtext("friendshipTowardFarmer", "0"))
                    except ValueError:
                        return 0
    return 0


def _check_community_center_progress(root, player):
    """Checks completion of Community Center or Joja Warehouse milestones."""
    mail_received = {m.text for m in player.findall(".//mailReceived/string") if m.text}
    cc_is_complete = "ccIsComplete" in mail_received or "JojaMember" in mail_received
    cc_ceremony = "ccGrandReopening" in mail_received or "JojaMember" in mail_received

    return cc_is_complete, cc_ceremony


def _empty_grandpa_summary():
    return {
        "total_score": 0,
        "max_score": 21,
        "candles": 1,
        "statue_unlocked": False,
        "categories": [],
    }
