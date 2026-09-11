def parse_player(player_node):
    """Extract basic farmer and farm statistics."""
    name = player_node.findtext("name", "Unknown")
    farm_name = player_node.findtext("farmName", "Unknown")
    money = player_node.findtext("money", "0")
    
    total_earned = player_node.findtext("totalMoneyEarned")
    if not total_earned or total_earned == "0":
        stats = player_node.find("stats")
        if stats is not None:
            total_earned = stats.findtext("totalMoneyEarned", "0")

    return {
        "farmer": name,
        "farm": farm_name,
        "money": int(money),
        "total_earned": int(total_earned or 0),
    }
