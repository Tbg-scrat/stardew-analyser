# src/modules/player.py

import logging
import time

logger = logging.getLogger(__name__)


def parse_player(player_node):
    """Extract basic farmer and farm statistics."""
    start_time = time.perf_counter()

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
            logger.debug("Extracted totalMoneyEarned via <stats> fallback container")

    try:
        money_int = int(money)
    except ValueError:
        logger.debug(f"Invalid non-integer money value '{money}'; defaulting to 0")
        money_int = 0

    try:
        earned_int = int(total_earned or 0)
    except ValueError:
        logger.debug(
            f"Invalid non-integer totalMoneyEarned value '{total_earned}'; defaulting to 0"
        )
        earned_int = 0

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(
        f"Parsed farmer details: '{name}' on '{farm_name}' Farm "
        f"(Current: {money_int}g, Total Earned: {earned_int}g) in {elapsed_ms:.2f}ms"
    )

    return {
        "farmer": name,
        "farm": farm_name,
        "money": money_int,
        "total_earned": earned_int,
    }
