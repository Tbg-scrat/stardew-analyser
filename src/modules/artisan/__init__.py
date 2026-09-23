# src/modules/artisan/__init__.py

import logging
from src.modules.artisan.casks import parse_all_casks_from_save

logger = logging.getLogger(__name__)


def parse_all_artisan_goods(root, player=None):
    """
    Main aggregator for all multi-day artisan machines across the save.
    Orchestrates casks, kegs, jars, dehydrators, and bee houses into a 
    unified data contract.
    """
    # 1. Parse Cellar Casks
    casks_data = parse_all_casks_from_save(root, player)

    # Placeholders for upcoming sub-modules
    kegs_data = {"total": 0, "ready_today": 0, "ready_tomorrow": 0, "processing": 0, "idle": 0, "batches": []}
    jars_data = {"total": 0, "ready_today": 0, "ready_tomorrow": 0, "processing": 0, "idle": 0, "batches": []}
    dehydrators_data = {"total": 0, "ready_today": 0, "ready_tomorrow": 0, "processing": 0, "idle": 0, "batches": []}
    bee_houses_data = {"total": 0, "ready_today": 0, "ready_tomorrow": 0, "processing": 0, "idle": 0, "batches": []}

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

    return {
        "summary": {
            "total_machines": total_machines,
            "ready_today": total_ready_today,
            "ready_tomorrow": total_ready_tomorrow,
            "idle_machines": total_idle,
        },
        "casks": casks_data,
        "kegs": kegs_data,
        "jars": jars_data,
        "dehydrators": dehydrators_data,
        "bee_houses": bee_houses_data,
    }
    