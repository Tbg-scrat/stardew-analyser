"""
test_analyser.py - Automated tests for Stardew Valley Save File Analyzer
"""

import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from parser import POLYCULTURE_CROPS, load_object_mappings, find_newest_save, parse_save
from renderer import render_dashboard


def test_crops_count():
    assert len(POLYCULTURE_CROPS) == 28, f"Expected 28 crops, found {len(POLYCULTURE_CROPS)}"
    seasons = [c["season"] for c in POLYCULTURE_CROPS]
    assert seasons.count("Spring") == 9
    assert seasons.count("Summer") == 10
    assert seasons.count("Fall") == 9
    print("✓ Polyculture canonical 28-crop list passed (Spring: 9, Summer: 10, Fall: 9)")


def test_cache_loading():
    name_to_id, id_to_image = load_object_mappings()
    assert len(name_to_id) >= 28, "Missing crop IDs"
    for crop in POLYCULTURE_CROPS:
        cid = name_to_id.get(crop["name"].lower())
        assert cid is not None, f"Missing ID for crop {crop['name']}"
        assert cid in id_to_image, f"Missing image for crop {crop['name']}"
    print("✓ Object mappings and sprite icons loaded from local cache successfully")


def test_save_parsing():
    save1 = Path("./Saves/Friisen_433608217/Friisen_433608217")
    data1 = parse_save(save1)
    assert data1["farmer_name"] == "Nils"
    assert data1["farm_name"] == "Friisen"
    assert data1["total_money"] == 2006369
    assert data1["completed_count"] == 22
    assert data1["total_crops"] == 28
    print(f"✓ Save 1 parsed: {data1['farmer_name']} ({data1['completed_count']}/28 completed, {data1['total_money_formatted']})")

    save2 = Path("./Saves/Friisen_442850859/Friisen_442850859")
    data2 = parse_save(save2)
    assert data2["farmer_name"] == "Nils"
    assert data2["farm_name"] == "Friisen-"
    print(f"✓ Save 2 parsed: {data2['farmer_name']} ({data2['completed_count']}/28 completed, {data2['total_money_formatted']})")


def test_dashboard_rendering():
    save1 = Path("./Saves/Friisen_433608217/Friisen_433608217")
    data1 = parse_save(save1)
    out_file = Path("./web/index.html")
    res = render_dashboard(data1, output_file=out_file)
    assert res.exists()
    content = res.read_text(encoding="utf-8")
    assert "Friisen Farm" in content
    assert "Nils" in content
    assert "2,006,369" in content
    assert "Cauliflower" in content
    assert "✓ Done" in content
    assert "Need" in content
    print("✓ Dashboard HTML rendering verified")


def test_multi_save_parsing():
    from parser import find_all_saves, parse_all_saves
    saves = find_all_saves("./Saves")
    assert len(saves) >= 2, f"Expected at least 2 saves, found {len(saves)}"

    farms = parse_all_saves("./Saves")
    assert len(farms) >= 2, f"Expected at least 2 parsed farms, found {len(farms)}"
    # assert farms[0].get("is_newest") is True, "First farm should be marked is_newest"
    assert farms[0]["farm_id"] != farms[1]["farm_id"], "Each farm must have a unique farm_id"

    # Test multi-farm rendering
    out_file = Path("./web/index.html")
    res = render_dashboard(farms, output_file=out_file)
    content = res.read_text(encoding="utf-8")
    assert f"tab-btn-{farms[0]['farm_id']}" in content
    assert f"tab-btn-{farms[1]['farm_id']}" in content
    assert f"farm-panel-{farms[0]['farm_id']}" in content
    assert f"farm-panel-{farms[1]['farm_id']}" in content
    assert "selectFarm" in content
    assert "localStorage" in content
    print(f"✓ Multi-save test passed ({len(farms)} farms parsed with interactive tabs & persistence)")


def test_daily_intel():
    from parser import parse_save
    save1 = Path("./Saves/Friisen_433608217/Friisen_433608217")
    data1 = parse_save(save1)
    intel = data1.get("daily_intel", {})
    assert "weather" in intel
    assert intel["weather"]["tomorrow"]["name"] == "Sunny"
    assert "luck" in intel
    assert intel["luck"]["tier"] == "Very Displeased"
    assert len(intel["birthdays_alert"]) >= 1
    assert any(b["name"] == "Leo" for b in intel["birthdays_alert"])
    assert len(intel["social_radar"]) == 34
    print("✓ Daily Intel test passed (Weather, Luck Oracle, Birthday Radar, 34 Villagers)")


def test_collections():
    from parser import parse_save
    save1 = Path("./Saves/Friisen_433608217/Friisen_433608217")
    data1 = parse_save(save1)
    cols = data1.get("collections", {})
    assert "fish" in cols
    assert cols["fish"]["caught_count"] == 39
    assert cols["fish"]["total_count"] == 69
    assert "museum" in cols
    assert cols["museum"]["donated_count"] == 60
    assert cols["museum"]["total_count"] == 95
    assert "shipping" in cols
    assert cols["shipping"]["shipped_count"] == 91
    assert cols["shipping"]["total_count"] == 153
    print("✓ Collections test passed (Fish: 39/69, Museum: 60/95, Shipping: 91/153)")


def test_skills_and_mastery():
    from parser import parse_save
    # --- Save 1: Advanced farm (49/50 levels) ---
    save1 = Path("./Saves/Friisen_433608217/Friisen_433608217")
    data1 = parse_save(save1)
    sm1 = data1.get("skills_and_mastery", {})

    # Structure checks
    assert "skills" in sm1 and "mastery" in sm1
    assert sm1["total_skill_levels"] == 49
    assert sm1["max_skill_levels"] == 50
    assert sm1["total_skills_percent"] == 98.0

    # 5 skills present
    skill_keys = [s["key"] for s in sm1["skills"]]
    assert set(skill_keys) == {"farming", "mining", "foraging", "fishing", "combat"}

    # Farming: L10, maxed
    farming = next(s for s in sm1["skills"] if s["key"] == "farming")
    assert farming["level"] == 10
    assert farming["is_max"] is True
    assert farming["current_xp"] == 109671
    assert farming["xp_needed"] == 0
    assert farming["percent"] == 100.0

    # Combat: L9, NOT maxed, needs 1067 XP
    combat = next(s for s in sm1["skills"] if s["key"] == "combat")
    assert combat["level"] == 9
    assert combat["is_max"] is False
    assert combat["current_xp"] == 13933
    assert combat["xp_needed"] == 1067
    assert combat["percent"] == 78.7

    # Professions: Fighter (24) active for Combat
    combat_profs = [p["id"] for p in combat["active_professions"]]
    assert 24 in combat_profs  # Fighter

    # Mastery: locked (49/50 levels)
    mastery1 = sm1["mastery"]
    assert mastery1["is_unlocked"] is False
    assert mastery1["missing_levels"] == 1
    assert mastery1["mastery_exp"] == 0
    assert mastery1["points_earned"] == 0
    assert mastery1["points_available"] == 0
    assert len(mastery1["shrines"]) == 5

    # ability_xp: flat view of main skill XP + mastery (not the unused <abilities> XML)
    axp1 = data1.get("ability_xp", {})
    assert set(axp1.keys()) == {
        "skill_farming", "skill_mining", "skill_foraging", "skill_fishing", "skill_combat", "mastery"
    }
    assert axp1["skill_farming"]["xp"] == 109671
    assert axp1["skill_farming"]["level"] == 10
    assert axp1["skill_farming"]["is_max"] is True
    assert axp1["skill_combat"]["xp"] == 13933
    assert axp1["skill_combat"]["level"] == 9
    assert axp1["skill_combat"]["next_level_xp"] == 1067
    assert axp1["skill_foraging"]["xp"] == 31080
    assert axp1["mastery"]["xp"] == 0
    assert axp1["mastery"]["is_unlocked"] is False
    print(f"✓ Skills & Mastery test passed (Save 1: 49/50 levels, Combat L9, {combat['xp_needed_formatted']} XP to max)")

    # --- Save 2: Early game (7/50 levels) ---
    save2 = Path("./Saves/Friisen_442850859/Friisen_442850859")
    data2 = parse_save(save2)
    sm2 = data2.get("skills_and_mastery", {})
    assert sm2["total_skill_levels"] == 7
    assert sm2["mastery"]["is_unlocked"] is False
    farming2 = next(s for s in sm2["skills"] if s["key"] == "farming")
    assert farming2["level"] == 2
    assert farming2["is_max"] is False
    assert len(farming2["active_professions"]) == 0
    print(f"✓ Skills & Mastery test passed (Save 2: 7/50 levels, no professions)")


if __name__ == "__main__":
    test_crops_count()
    test_cache_loading()
    test_save_parsing()
    test_daily_intel()
    test_collections()
    test_skills_and_mastery()
    test_dashboard_rendering()
    test_multi_save_parsing()
    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY! 🎉")
