# src/modules/player.py

import logging

logger = logging.getLogger(__name__)


def parse_player(player_node):
    """Extract basic farmer and farm statistics."""
    if player_node is None:
        logger.warning("Player node is None. Defaulting player statistics.")
        return {
            "farmer": "Unknown",
            "farm": "Unknown",
            "money": 0,
            "total_earned": 0,
        }

    name = player_node.findtext("name", "Unknown")
    farm_name = player_node.findtext("farmName", "Unknown")
    money = player_node.findtext("money", "0")
    
    total_earned = player_node.findtext("totalMoneyEarned")
    if not total_earned or total_earned == "0":
        stats = player_node.find("stats")
        if stats is not None:
            total_earned = stats.findtext("totalMoneyEarned", "0")

    try:
        money_int = int(money)
    except ValueError:
        money_int = 0

    try:
        earned_int = int(total_earned or 0)
    except ValueError:
        earned_int = 0

    logger.debug(f"Parsed farmer details: '{name}' on '{farm_name}' Farm (Current: {money_int}g, Total Earned: {earned_int}g)")

    return {
        "farmer": name,
        "farm": farm_name,
        "money": money_int,
        "total_earned": earned_int,
    }
    