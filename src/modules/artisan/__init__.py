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
    Consolidates casks, kegs, jars, dehydrators, and bee houses into a 
    standardized schema with aggregated summary metrics and idle alerts.
    """
    # 1. Parse Sub-modules
    casks_data = parse_all_casks_from_save(root, player) or {
        "total_casks": 0, "empty_casks": 0, "ready_today": 0, "ready_tomorrow": 0, "aging_count": 0, "batches": []
    }
    kegs_data = parse_all_kegs_from_save(root) or {
        "total": 0, "idle": 0, "ready_today": 0, "ready_tomorrow": 0, "processing": 0, "idle_locations": {}, "batches": []
    }
    jars_data = parse_all_jars_from_save(root) or {
        "total": 0, "idle": 0, "ready_today": 0, "ready_tomorrow": 0, "processing": 0, "idle_locations": {}, "batches": []
    }
    dehydrators_data = parse_all_dehydrators_from_save(root) or {
        "total": 0, "idle": 0, "ready_today": 0, "ready_tomorrow": 0, "processing": 0, "idle_locations": {}, "batches": []
    }
    bee_houses_data = parse_all_bee_houses_from_save(root) or {
        "total": 0, "idle": 0, "hibernating": 0, "ready_today": 0, "ready_tomorrow": 0, "processing": 0, "idle_locations": {}, "batches": []
    }

    # 2. Grand Totals Calculation
    total_casks = casks_data.get("total_casks", 0)
    total_kegs = kegs_data.get("total", 0)
    total_jars = jars_data.get("total", 0)
    total_dehydrators = dehydrators_data.get("total", 0)
    total_bee_houses = bee_houses_data.get("total", 0)

    total_machines = (
        total_casks
        + total_kegs
        + total_jars
        + total_dehydrators
        + total_bee_houses
    )

    total_ready_today = (
        casks_data.get("ready_today", 0)
        + kegs_data.get("ready_today", 0)
        + jars_data.get("ready_today", 0)
        + dehydrators_data.get("ready_today", 0)
        + bee_houses_data.get("ready_today", 0)
    )

    total_ready_tomorrow = (
        casks_data.get("ready_tomorrow", 0)
        + kegs_data.get("ready_tomorrow", 0)
        + jars_data.get("ready_tomorrow", 0)
        + dehydrators_data.get("ready_tomorrow", 0)
        + bee_houses_data.get("ready_tomorrow", 0)
    )

    total_processing = (
        casks_data.get("aging_count", 0)
        + kegs_data.get("processing", 0)
        + jars_data.get("processing", 0)
        + dehydrators_data.get("processing", 0)
        + bee_houses_data.get("processing", 0)
    )

    total_idle = (
        casks_data.get("empty_casks", 0)
        + kegs_data.get("idle", 0)
        + jars_data.get("idle", 0)
        + dehydrators_data.get("idle", 0)
        + bee_houses_data.get("idle", 0)
    )

    total_hibernating = bee_houses_data.get("hibernating", 0)

    # 3. Global Idle Summary Aggregation
    idle_summary = {}

    def _add_idle(location, machine_type, count):
        if count <= 0:
            return
        if location not in idle_summary:
            idle_summary[location] = {}
        idle_summary[location][machine_type] = count

    if casks_data.get("empty_casks", 0) > 0:
        _add_idle("Cellar", "casks", casks_data["empty_casks"])

    for loc, count in kegs_data.get("idle_locations", {}).items():
        _add_idle(loc, "kegs", count)

    for loc, count in jars_data.get("idle_locations", {}).items():
        _add_idle(loc, "jars", count)

    for loc, count in dehydrators_data.get("idle_locations", {}).items():
        _add_idle(loc, "dehydrators", count)

    for loc, count in bee_houses_data.get("idle_locations", {}).items():
        _add_idle(loc, "bee_houses", count)

    return {
        "summary": {
            "total_machines": total_machines,
            "ready_today": total_ready_today,
            "ready_tomorrow": total_ready_tomorrow,
            "processing_machines": total_processing,
            "idle_machines": total_idle,
            "hibernating_machines": total_hibernating,
            "breakdown": {
                "casks": total_casks,
                "kegs": total_kegs,
                "jars": total_jars,
                "dehydrators": total_dehydrators,
                "bee_houses": total_bee_houses,
            },
        },
        "casks": casks_data,
        "kegs": kegs_data,
        "jars": jars_data,
        "dehydrators": dehydrators_data,
        "bee_houses": bee_houses_data,
        "idle_summary": idle_summary,
    }
    