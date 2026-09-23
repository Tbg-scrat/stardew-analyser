# src/modules/artisan/__init__.py

import logging
from src.modules.artisan.casks import parse_all_casks_from_save
from src.modules.artisan.kegs import parse_all_kegs_from_save
from src.modules.artisan.jars import parse_all_jars_from_save
from src.modules.artisan.dehydrators import parse_all_dehydrators_from_save
from src.modules.artisan.bee_houses import parse_all_bee_houses_from_save

logger = logging.getLogger(__name__)


def parse_all_artisan_goods(root, player=None):
    """
    Main aggregator for all multi-day artisan machines across the save.
    Orchestrates casks, kegs, jars, dehydrators, and bee houses into a 
    unified data contract.
    """
    # 1. Parse Cellar Casks
    casks_data = parse_all_casks_from_save(root, player)

    # 2. Parse Kegs
    kegs_data = parse_all_kegs_from_save(root)

    # 3. Parse Preserves Jars
    jars_data = parse_all_jars_from_save(root)

    # 4. Parse Dehydrators
    dehydrators_data = parse_all_dehydrators_from_save(root)

    # 5. Parse Bee Houses
    bee_houses_data = parse_all_bee_houses_from_save(root)

    # Aggregate Top-Level Statistics
    total_machines = (
        casks_data.get("total_casks", 0)
        + kegs_data["total"]
        + jars_data["total"]
        + dehydrators_data["total"]
        + bee_houses_data["total"]
    )

    total_ready_today = (
        casks_data.get("ready_today", 0)
        + kegs_data["ready_today"]
        + jars_data["ready_today"]
        + dehydrators_data["ready_today"]
        + bee_houses_data["ready_today"]
    )

    total_ready_tomorrow = (
        casks_data.get("ready_tomorrow", 0)
        + kegs_data["ready_tomorrow"]
        + jars_data["ready_tomorrow"]
        + dehydrators_data["ready_tomorrow"]
        + bee_houses_data["ready_tomorrow"]
    )

    total_idle = (
        casks_data.get("empty_casks", 0)
        + kegs_data["idle"]
        + jars_data["idle"]
        + dehydrators_data["idle"]
        + bee_houses_data["idle"]
    )

    total_hibernating = bee_houses_data.get("hibernating", 0)

    return {
        "summary": {
            "total_machines": total_machines,
            "ready_today": total_ready_today,
            "ready_tomorrow": total_ready_tomorrow,
            "idle_machines": total_idle,
            "hibernating_machines": total_hibernating,
        },
        "casks": casks_data,
        "kegs": kegs_data,
        "jars": jars_data,
        "dehydrators": dehydrators_data,
        "bee_houses": bee_houses_data,
    }
    