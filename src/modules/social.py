def parse_social(player_node):
    """Extract friendship levels, hearts, and gift statistics directly from XML."""
    friendships = {}
    friendship_data = player_node.find("friendshipData")
    
    if friendship_data is not None:
        for item in friendship_data.findall("item"):
            key_node = item.find("key")
            val_node = item.find("value")
            
            if key_node is not None and val_node is not None:
                npc_name = key_node.findtext("string")
                friendship_obj = val_node.find("Friendship")
                
                if npc_name and friendship_obj is not None:
                    points = int(friendship_obj.findtext("Points", "0"))
                    gifts_this_week = int(friendship_obj.findtext("GiftsThisWeek", "0"))
                    talked_today = friendship_obj.findtext("TalkedToToday", "false").lower() == "true"
                    status = friendship_obj.findtext("Status", "Friendly")
                    
                    # 1 Heart = 250 Points
                    hearts = points // 250
                    points_in_current_heart = points % 250
                    
                    # Cap display hearts at 14 for spouse, 10 for regular
                    max_hearts = 14 if status == "Married" else 10
                    
                    friendships[npc_name] = {
                        "points": points,
                        "hearts": hearts,
                        "points_in_heart": points_in_current_heart,
                        "max_hearts": max_hearts,
                        "gifts_this_week": gifts_this_week,
                        "talked_today": talked_today,
                        "status": status,
                    }
                    
    # Sort alphabetically by NPC name
    return dict(sorted(friendships.items()))
