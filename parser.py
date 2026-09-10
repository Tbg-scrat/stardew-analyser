"""
parser.py - Stardew Valley Save File Parser for Polyculture Achievement

Extracts player stats and matches shipped crops from <player><basicShipped>
against the canonical 28 Polyculture crops from the official Stardew Valley Wiki.
Caches object ID mappings and sprites locally so network access is only needed on initial startup.
"""

import json
import logging
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("stardew-parser")

GITHUB_OBJECTS_URL = "https://raw.githubusercontent.com/MateusAquino/stardewids/main/dist/objects.json"
DEFAULT_CACHE_DIR = Path(
    os.getenv(
        "DATA_DIR",
        "/srv/docker/data/sv-analyzer/data"
        if Path("/srv/docker/data/sv-analyzer/data").exists()
        else (Path(__file__).resolve().parent / "data"),
    )
)
DEFAULT_CACHE_FILE = Path(os.getenv("CACHE_FILE", DEFAULT_CACHE_DIR / "objects_cache.json")).resolve()

# Canonical 28 Polyculture crops verified from official Stardew Valley Wiki:
# "Ship 15 of each crop"
POLYCULTURE_CROPS: List[Dict[str, str]] = [
    # Spring (9)
    {"name": "Cauliflower", "season": "Spring"},
    {"name": "Coffee Bean", "season": "Spring"},
    {"name": "Garlic", "season": "Spring"},
    {"name": "Green Bean", "season": "Spring"},
    {"name": "Kale", "season": "Spring"},
    {"name": "Parsnip", "season": "Spring"},
    {"name": "Potato", "season": "Spring"},
    {"name": "Rhubarb", "season": "Spring"},
    {"name": "Strawberry", "season": "Spring"},
    # Summer (10)
    {"name": "Blueberry", "season": "Summer"},
    {"name": "Corn", "season": "Summer"},
    {"name": "Hops", "season": "Summer"},
    {"name": "Hot Pepper", "season": "Summer"},
    {"name": "Melon", "season": "Summer"},
    {"name": "Radish", "season": "Summer"},
    {"name": "Red Cabbage", "season": "Summer"},
    {"name": "Starfruit", "season": "Summer"},
    {"name": "Tomato", "season": "Summer"},
    {"name": "Wheat", "season": "Summer"},
    # Fall (9)
    {"name": "Amaranth", "season": "Fall"},
    {"name": "Artichoke", "season": "Fall"},
    {"name": "Beet", "season": "Fall"},
    {"name": "Bok Choy", "season": "Fall"},
    {"name": "Cranberries", "season": "Fall"},
    {"name": "Eggplant", "season": "Fall"},
    {"name": "Grape", "season": "Fall"},
    {"name": "Pumpkin", "season": "Fall"},
    {"name": "Yam", "season": "Fall"},
]

# Fallback IDs in case first startup is completely offline before cache can be created
FALLBACK_CROP_IDS: Dict[str, str] = {
    "cauliflower": "190",
    "coffee bean": "433",
    "garlic": "248",
    "green bean": "188",
    "kale": "250",
    "parsnip": "24",
    "potato": "192",
    "rhubarb": "252",
    "strawberry": "400",
    "blueberry": "258",
    "corn": "270",
    "hops": "304",
    "hot pepper": "260",
    "melon": "254",
    "radish": "264",
    "red cabbage": "266",
    "starfruit": "268",
    "tomato": "256",
    "wheat": "262",
    "amaranth": "300",
    "artichoke": "274",
    "beet": "284",
    "bok choy": "278",
    "cranberries": "282",
    "eggplant": "272",
    "grape": "398",
    "pumpkin": "276",
    "yam": "280",
}

# Weather code lookups for 1.5 & 1.6
WEATHER_MAPPINGS: Dict[str, Dict[str, str]] = {
    "Sun": {"name": "Sunny", "icon": "☀️", "color": "#facc15", "desc": "Clear skies and sunshine."},
    "0": {"name": "Sunny", "icon": "☀️", "color": "#facc15", "desc": "Clear skies and sunshine."},
    "Rain": {"name": "Rainy", "icon": "🌧️", "color": "#60a5fa", "desc": "Rain all day. Crops will be watered!"},
    "1": {"name": "Rainy", "icon": "🌧️", "color": "#60a5fa", "desc": "Rain all day. Crops will be watered!"},
    "Debris": {"name": "Windy / Debris", "icon": "🍃", "color": "#34d399", "desc": "Breezy conditions with debris in the air."},
    "2": {"name": "Windy / Debris", "icon": "🍃", "color": "#34d399", "desc": "Breezy conditions with debris in the air."},
    "Lightning": {"name": "Stormy", "icon": "⚡", "color": "#c084fc", "desc": "Thunderstorms! Lightning strikes and heavy rain."},
    "3": {"name": "Stormy", "icon": "⚡", "color": "#c084fc", "desc": "Thunderstorms! Lightning strikes and heavy rain."},
    "Festival": {"name": "Festival", "icon": "🎪", "color": "#f472b6", "desc": "A festive gathering will take place today."},
    "4": {"name": "Festival", "icon": "🎪", "color": "#f472b6", "desc": "A festive gathering will take place today."},
    "Snow": {"name": "Snowy", "icon": "❄️", "color": "#bae6fd", "desc": "Gentle snowfall covering the valley."},
    "5": {"name": "Snowy", "icon": "❄️", "color": "#bae6fd", "desc": "Gentle snowfall covering the valley."},
    "Wedding": {"name": "Wedding", "icon": "💍", "color": "#fb7185", "desc": "A joyous wedding day!"},
    "6": {"name": "Wedding", "icon": "💍", "color": "#fb7185", "desc": "A joyous wedding day!"},
    "GreenRain": {"name": "Green Rain", "icon": "🟩🌧️", "color": "#4ade80", "desc": "A strange green rain event! Wild moss and giant weeds flourish."},
}

# Canonical 34 Villagers: Season, Day, Datable, and Curated Loved Gifts
VILLAGER_DATA: Dict[str, Dict[str, Any]] = {
    "Abigail": {"season": "Fall", "day": 13, "datable": True, "loved": ["Amethyst", "Pumpkin", "Chocolate Cake", "Spicy Eel", "Blackberry Cobbler"]},
    "Alex": {"season": "Summer", "day": 13, "datable": True, "loved": ["Complete Breakfast", "Salmon Dinner"]},
    "Caroline": {"season": "Winter", "day": 7, "datable": False, "loved": ["Fish Taco", "Green Tea", "Summer Spangle", "Tropical Curry"]},
    "Clint": {"season": "Winter", "day": 26, "datable": False, "loved": ["Amethyst", "Aquamarine", "Emerald", "Gold Bar", "Iridium Bar", "Jade", "Ruby", "Topaz", "Omni Geode"]},
    "Demetrius": {"season": "Summer", "day": 19, "datable": False, "loved": ["Bean Hotpot", "Ice Cream", "Rice Pudding", "Strawberry"]},
    "Dwarf": {"season": "Summer", "day": 22, "datable": False, "loved": ["Amethyst", "Aquamarine", "Emerald", "Jade", "Ruby", "Topaz", "Omni Geode", "Lemon Stone"]},
    "Elliott": {"season": "Fall", "day": 5, "datable": True, "loved": ["Crab Cakes", "Duck Feather", "Lobster", "Pomegranate", "Squid Ink"]},
    "Emily": {"season": "Spring", "day": 27, "datable": True, "loved": ["Amethyst", "Aquamarine", "Cloth", "Emerald", "Jade", "Ruby", "Survival Burger", "Topaz", "Wool"]},
    "Evelyn": {"season": "Winter", "day": 20, "datable": False, "loved": ["Beet", "Chocolate Cake", "Diamond", "Fairy Rose", "Stuffing", "Tulip"]},
    "George": {"season": "Fall", "day": 24, "datable": False, "loved": ["Fried Mushroom", "Leek"]},
    "Gus": {"season": "Summer", "day": 8, "datable": False, "loved": ["Diamond", "Escargot", "Fish Taco", "Orange", "Tropical Curry"]},
    "Haley": {"season": "Spring", "day": 14, "datable": True, "loved": ["Coconut", "Fruit Salad", "Pink Cake", "Sunflower"]},
    "Harvey": {"season": "Winter", "day": 14, "datable": True, "loved": ["Coffee", "Pickles", "Super Meal", "Truffle Oil", "Wine"]},
    "Jas": {"season": "Summer", "day": 4, "datable": False, "loved": ["Fairy Rose", "Pink Cake", "Plum Pudding"]},
    "Jodi": {"season": "Fall", "day": 11, "datable": False, "loved": ["Chocolate Cake", "Crispy Bass", "Diamond", "Eggplant Parmesan", "Fried Eel", "Pancakes", "Rhubarb Pie", "Vegetable Medley"]},
    "Kent": {"season": "Spring", "day": 4, "datable": False, "loved": ["Fiddlehead Risotto", "Roasted Hazelnuts"]},
    "Krobus": {"season": "Winter", "day": 1, "datable": False, "loved": ["Diamond", "Iridium Bar", "Pumpkin", "Void Egg", "Void Mayonnaise", "Wild Horseradish"]},
    "Leah": {"season": "Winter", "day": 23, "datable": True, "loved": ["Goat Cheese", "Poppyseed Muffin", "Salad", "Stir Fry", "Truffle", "Vegetable Medley", "Wine"]},
    "Leo": {"season": "Summer", "day": 26, "datable": False, "loved": ["Duck Feather", "Mango", "Ostrich Egg", "Poi"]},
    "Lewis": {"season": "Spring", "day": 7, "datable": False, "loved": ["Autumn's Bounty", "Glazed Yams", "Green Tea", "Hot Pepper", "Vegetable Medley"]},
    "Linus": {"season": "Winter", "day": 3, "datable": False, "loved": ["Blueberry Tart", "Cactus Fruit", "Coconut", "Dish O' The Sea", "Yam"]},
    "Marnie": {"season": "Fall", "day": 18, "datable": False, "loved": ["Diamond", "Farmer's Lunch", "Pink Cake", "Pumpkin Pie"]},
    "Maru": {"season": "Summer", "day": 10, "datable": True, "loved": ["Battery Pack", "Cauliflower", "Cheese Cauliflower", "Diamond", "Gold Bar", "Iridium Bar", "Miner's Treat", "Pepper Poppers", "Rhubarb Pie", "Strawberry"]},
    "Pam": {"season": "Spring", "day": 18, "datable": False, "loved": ["Beer", "Cactus Fruit", "Glazed Yams", "Mead", "Pale Ale", "Parsnip", "Parsnip Soup", "Piña Colada"]},
    "Penny": {"season": "Fall", "day": 2, "datable": True, "loved": ["Diamond", "Emerald", "Melon", "Poppy", "Poppyseed Muffin", "Red Plate", "Roots Platter", "Sandfish", "Tom Kha Soup"]},
    "Pierre": {"season": "Spring", "day": 26, "datable": False, "loved": ["Fried Calamari"]},
    "Robin": {"season": "Fall", "day": 21, "datable": False, "loved": ["Goat Cheese", "Peach", "Spaghetti"]},
    "Sam": {"season": "Summer", "day": 17, "datable": True, "loved": ["Cactus Fruit", "Maple Bar", "Pizza", "Tigerseye"]},
    "Sandy": {"season": "Fall", "day": 15, "datable": False, "loved": ["Crocus", "Daffodil", "Mango Sticky Rice", "Sweet Pea"]},
    "Sebastian": {"season": "Winter", "day": 10, "datable": True, "loved": ["Frozen Tear", "Obsidian", "Pumpkin Soup", "Sashimi", "Void Egg"]},
    "Shane": {"season": "Spring", "day": 20, "datable": True, "loved": ["Beer", "Hot Pepper", "Pepper Poppers", "Pizza"]},
    "Vincent": {"season": "Spring", "day": 10, "datable": False, "loved": ["Cranberry Candy", "Ginger Ale", "Grape", "Pink Cake", "Snail"]},
    "Willy": {"season": "Summer", "day": 24, "datable": False, "loved": ["Catfish", "Diamond", "Iridium Bar", "Mead", "Octopus", "Pumpkin", "Sea Cucumber", "Sturgeon"]},
    "Wizard": {"season": "Winter", "day": 17, "datable": False, "loved": ["Purple Mushroom", "Solar Essence", "Super Cucumber", "Void Essence"]},
}

# Canonical 69 Fish collection items (including 68 catchable + crab pot / algae)
FISH_METADATA: List[Tuple[str, str, str, str, str, str]] = [
    # (id, name, seasons, weather, location, time)
    ("128", "Pufferfish", "Summer", "Sun", "Ocean", "12pm - 4pm"),
    ("129", "Anchovy", "Spring / Fall", "Any", "Ocean", "Anytime"),
    ("130", "Tuna", "Summer / Winter", "Any", "Ocean", "6am - 7pm"),
    ("131", "Sardine", "Spring / Fall / Winter", "Any", "Ocean", "6am - 7pm"),
    ("132", "Bream", "All Seasons", "Any", "River", "6pm - 2am"),
    ("136", "Largemouth Bass", "All Seasons", "Any", "Mountain Lake", "6am - 7pm"),
    ("137", "Smallmouth Bass", "Spring / Fall", "Any", "River / Pond", "Anytime"),
    ("138", "Rainbow Trout", "Summer", "Sun", "River / Lake", "6am - 7pm"),
    ("139", "Salmon", "Fall", "Any", "River", "6am - 7pm"),
    ("140", "Walleye", "Fall / Winter", "Rain", "River / Lake / Pond", "12pm - 2am"),
    ("141", "Perch", "Winter", "Any", "River / Lake / Pond", "Anytime"),
    ("142", "Carp", "All Seasons", "Any", "Mountain Lake / Pond / Sewers", "Anytime"),
    ("143", "Catfish", "Spring / Fall", "Rain", "River / Secret Woods", "6am - 12am"),
    ("144", "Pike", "Summer / Winter", "Any", "River / Pond", "Anytime"),
    ("145", "Sunfish", "Spring / Summer", "Sun", "River", "6am - 7pm"),
    ("146", "Red Mullet", "Summer / Winter", "Any", "Ocean", "6am - 7pm"),
    ("147", "Herring", "Spring / Winter", "Any", "Ocean", "Anytime"),
    ("148", "Eel", "Spring / Fall", "Rain", "Ocean", "4pm - 2am"),
    ("149", "Octopus", "Summer", "Any", "Ocean", "6am - 1pm"),
    ("150", "Red Snapper", "Summer / Fall", "Rain", "Ocean", "6am - 7pm"),
    ("151", "Squid", "Winter", "Any", "Ocean", "6pm - 2am"),
    ("154", "Sea Cucumber", "Fall / Winter", "Any", "Ocean", "6am - 7pm"),
    ("155", "Super Cucumber", "Summer / Fall", "Any", "Ocean", "6pm - 2am"),
    ("156", "Ghostfish", "All Seasons", "Any", "Mines 20/60", "Anytime"),
    ("158", "Stonefish", "All Seasons", "Any", "Mines 20", "Anytime"),
    ("161", "Ice Pip", "All Seasons", "Any", "Mines 60", "Anytime"),
    ("162", "Lava Eel", "All Seasons", "Any", "Mines 100 / Volcano", "Anytime"),
    ("164", "Sandfish", "All Seasons", "Any", "Calico Desert", "6am - 8pm"),
    ("165", "Scorpion Carp", "All Seasons", "Any", "Calico Desert", "6am - 8pm"),
    ("267", "Flounder", "Spring / Summer", "Any", "Ocean", "6am - 8pm"),
    ("269", "Midnight Carp", "Fall / Winter", "Any", "Mountain Lake / Pond", "10pm - 2am"),
    ("698", "Sturgeon", "Summer / Winter", "Any", "Mountain Lake", "6am - 7pm"),
    ("699", "Tiger Trout", "Fall / Winter", "Any", "River", "6am - 7pm"),
    ("700", "Bullhead", "All Seasons", "Any", "Mountain Lake", "Anytime"),
    ("701", "Tilapia", "Summer / Fall", "Any", "Ocean", "6am - 2pm"),
    ("702", "Chub", "All Seasons", "Any", "River / Mountain Lake", "Anytime"),
    ("704", "Dorado", "Summer", "Any", "Forest River", "6am - 7pm"),
    ("705", "Albacore", "Fall / Winter", "Any", "Ocean", "6am - 11am & 6pm - 2am"),
    ("706", "Shad", "Spring / Summer / Fall", "Rain", "River", "9am - 2am"),
    ("707", "Lingcod", "Winter", "Any", "River / Mountain Lake", "Anytime"),
    ("708", "Halibut", "Spring / Summer / Winter", "Any", "Ocean", "6am - 11am & 7pm - 2am"),
    ("734", "Woodskip", "All Seasons", "Any", "Secret Woods", "Anytime"),
    ("795", "Void Salmon", "All Seasons", "Any", "Witch's Swamp", "Anytime"),
    ("796", "Slimejack", "All Seasons", "Any", "Mutant Bug Lair", "Anytime"),
    ("798", "Midnight Squid", "Winter (15-17)", "Any", "Night Market Submarine", "5pm - 2am"),
    ("799", "Spook Fish", "Winter (15-17)", "Any", "Night Market Submarine", "5pm - 2am"),
    ("800", "Blobfish", "Winter (15-17)", "Any", "Night Market Submarine", "5pm - 2am"),
    ("836", "Stingray", "All Seasons", "Any", "Pirate Cove (Island)", "Anytime"),
    ("837", "Lionfish", "All Seasons", "Any", "Ocean (Island)", "Anytime"),
    ("838", "Blue Discus", "All Seasons", "Any", "River / Pond (Island)", "Anytime"),
    ("Goby", "Goby", "All Seasons", "Any", "Waterfalls", "Anytime"),
    # Legendary Fish
    ("159", "Crimsonfish", "Summer", "Any", "East Pier (Ocean)", "Anytime"),
    ("160", "Angler", "Fall", "Any", "North of JojaMart (River)", "Anytime"),
    ("163", "Legend", "Spring", "Rain", "Mountain Lake", "Anytime"),
    ("676", "Glacierfish", "Winter", "Any", "Arrowhead Island (Forest)", "6am - 8pm"),
    ("682", "Mutant Carp", "All Seasons", "Any", "The Sewers", "Anytime"),
    # Crab Pot & Foraged Fish
    ("715", "Lobster", "All Seasons", "Crab Pot", "Ocean", "Crab Pot"),
    ("716", "Crayfish", "All Seasons", "Crab Pot", "Freshwater", "Crab Pot"),
    ("717", "Crab", "All Seasons", "Crab Pot", "Ocean", "Crab Pot"),
    ("718", "Cockle", "All Seasons", "Crab Pot", "Ocean / Beach", "Crab Pot"),
    ("719", "Mussel", "All Seasons", "Crab Pot", "Ocean / Beach", "Crab Pot"),
    ("720", "Shrimp", "All Seasons", "Crab Pot", "Ocean", "Crab Pot"),
    ("721", "Snail", "All Seasons", "Crab Pot", "Freshwater", "Crab Pot"),
    ("722", "Periwinkle", "All Seasons", "Crab Pot", "Freshwater", "Crab Pot"),
    ("723", "Oyster", "All Seasons", "Crab Pot", "Ocean / Beach", "Crab Pot"),
    ("372", "Clam", "All Seasons", "Crab Pot", "Ocean / Beach", "Crab Pot"),
    # Algae & Seaweed
    ("152", "Seaweed", "All Seasons", "Any", "Ocean", "Anytime"),
    ("153", "Green Algae", "All Seasons", "Any", "Freshwater", "Anytime"),
    ("157", "White Algae", "All Seasons", "Any", "Mines / Sewers", "Anytime"),
]

# Canonical 152 Shipping Collection Items
SHIPPING_ITEMS_DEF: List[Tuple[str, str]] = [
    ("16", "Wild Horseradish"), ("18", "Daffodil"), ("20", "Leek"), ("22", "Dandelion"),
    ("24", "Parsnip"), ("88", "Coconut"), ("90", "Cactus Fruit"), ("91", "Banana"),
    ("92", "Sap"), ("388", "Wood"), ("390", "Stone"), ("392", "Nautilus Shell"),
    ("393", "Coral"), ("394", "Rainbow Shell"), ("396", "Spice Berry"), ("397", "Sea Urchin"),
    ("398", "Grape"), ("399", "Spring Onion"), ("400", "Strawberry"), ("402", "Sweet Pea"),
    ("404", "Common Mushroom"), ("406", "Wild Plum"), ("408", "Hazelnut"), ("410", "Blackberry"),
    ("412", "Winter Root"), ("414", "Crystal Fruit"), ("416", "Snow Yam"), ("417", "Sweet Gem Berry"),
    ("418", "Crocus"), ("420", "Red Mushroom"), ("421", "Sunflower"), ("422", "Purple Mushroom"),
    ("424", "Cheese"), ("426", "Goat Cheese"), ("428", "Cloth"), ("430", "Truffle"),
    ("432", "Truffle Oil"), ("433", "Coffee Bean"), ("436", "Goat Milk"), ("438", "L. Goat Milk"),
    ("440", "Wool"), ("442", "Duck Egg"), ("444", "Duck Feather"), ("446", "Rabbit's Foot"),
    ("454", "Ancient Fruit"), ("459", "Mead"), ("174", "Large Egg"), ("176", "Egg"),
    ("180", "Egg"), ("182", "Large Egg"), ("184", "Milk"), ("186", "Large Milk"),
    ("188", "Green Bean"), ("190", "Cauliflower"), ("192", "Potato"), ("248", "Garlic"),
    ("250", "Kale"), ("252", "Rhubarb"), ("254", "Melon"), ("256", "Tomato"),
    ("257", "Morel"), ("258", "Blueberry"), ("259", "Fiddlehead Fern"), ("260", "Hot Pepper"),
    ("262", "Wheat"), ("264", "Radish"), ("266", "Red Cabbage"), ("268", "Starfruit"),
    ("270", "Corn"), ("272", "Eggplant"), ("274", "Artichoke"), ("276", "Pumpkin"),
    ("278", "Bok Choy"), ("280", "Yam"), ("281", "Chanterelle"), ("282", "Cranberries"),
    ("284", "Beet"), ("300", "Amaranth"), ("303", "Pale Ale"), ("304", "Hops"),
    ("305", "Void Egg"), ("306", "Mayonnaise"), ("307", "Duck Mayonnaise"), ("308", "Void Mayonnaise"),
    ("340", "Honey"), ("342", "Pickles"), ("344", "Jelly"), ("346", "Beer"),
    ("348", "Wine"), ("376", "Poppy"), ("378", "Copper Ore"), ("380", "Iron Ore"),
    ("382", "Coal"), ("384", "Gold Ore"), ("386", "Iridium Ore"), ("334", "Copper Bar"),
    ("335", "Iron Bar"), ("336", "Gold Bar"), ("337", "Iridium Bar"), ("338", "Refined Quartz"),
    ("787", "Battery Pack"), ("80", "Quartz"), ("82", "Fire Quartz"), ("84", "Frozen Tear"),
    ("86", "Earth Crystal"), ("591", "Fairy Rose"), ("593", "Summer Spangle"), ("595", "Poppy"),
    ("597", "Tulip"), ("613", "Apple"), ("634", "Apricot"), ("635", "Orange"),
    ("636", "Peach"), ("637", "Pomegranate"), ("638", "Cherry"), ("684", "Bug Meat"),
    ("709", "Hardwood"), ("724", "Maple Syrup"), ("725", "Oak Resin"), ("726", "Pine Tar"),
    ("745", "Strawberry"), ("447", "Slime"), ("766", "Slime"), ("767", "Bat Wing"),
    ("768", "Solar Essence"), ("769", "Void Essence"), ("771", "Fiber"), ("812", "Roe"),
    ("814", "Squid Ink"), ("815", "Tea Leaves"), ("829", "Ginger"), ("830", "Taro Root"),
    ("832", "Pineapple"), ("834", "Mango"), ("848", "Cinder Shard"), ("851", "Magma Cap"),
    ("852", "Bone Fragment"), ("856", "Curry"), ("889", "Qi Fruit"), ("910", "Radioactive Bar"),
    ("909", "Radioactive Ore"), ("807", "Dinosaur Mayonnaise"), ("Caviar", "Caviar"),
    ("Carrot", "Carrot"), ("SummerSquash", "Summer Squash"), ("Broccoli", "Broccoli"),
    ("Powdermelon", "Powdermelon"), ("Moss", "Moss"), ("MysticSyrup", "Mystic Syrup"),
    ("Raisins", "Raisins"), ("DriedFruit", "Dried Fruit"), ("DriedMushrooms", "Dried Mushrooms"),
    ("SmokedFish", "Smoked Fish"),
]

SEASONS_ORDER = ["spring", "summer", "fall", "winter"]


def evaluate_luck(daily_luck: float) -> Dict[str, Any]:
    """Classifies daily luck into Welwick TV Fortune Teller categories."""
    if daily_luck > 0.07:
        return {
            "value": round(daily_luck, 4),
            "tier": "Very Happy",
            "icon": "🌟",
            "color": "#4ade80",
            "fortune": "The spirits are very happy today! They will do their best to shower everyone with good fortune.",
        }
    elif daily_luck > 0.02:
        return {
            "value": round(daily_luck, 4),
            "tier": "Good Humor",
            "icon": "🔺",
            "color": "#a3e635",
            "fortune": "The spirits are in good humor today. I think you'll have a little extra luck.",
        }
    elif daily_luck >= -0.02:
        return {
            "value": round(daily_luck, 4),
            "tier": "Neutral",
            "icon": "⚖️",
            "color": "#facc15",
            "fortune": "The spirits feel neutral today. The day is in your hands.",
        }
    elif daily_luck >= -0.07:
        return {
            "value": round(daily_luck, 4),
            "tier": "Somewhat Displeased",
            "icon": "🦇",
            "color": "#fb923c",
            "fortune": "This is not a rare occurrence, but the spirits feel somewhat displeased today.",
        }
    else:
        return {
            "value": round(daily_luck, 4),
            "tier": "Very Displeased",
            "icon": "💀",
            "color": "#f87171",
            "fortune": "The spirits are very displeased today. They will do their best to make your life difficult.",
        }


def load_object_mappings(
    cache_path: Optional[Path] = None,
    force_refresh: bool = False,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Loads object ID-to-name and ID-to-image mappings.
    Uses local cache (`objects_cache.json`) without remote GitHub fetches.
    Returns: (name_to_id, id_to_image)
    """
    cache_file = cache_path or DEFAULT_CACHE_FILE
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    objects_data = None

    if cache_file.exists():
        try:
            logger.info(f"Loading objects mapping from local cache: {cache_file}")
            with open(cache_file, "r", encoding="utf-8") as f:
                objects_data = json.load(f)
            logger.info(f"Loaded {len(objects_data)} objects from cache")
        except Exception as e:
            logger.error(f"Error reading local cache {cache_file}: {e}")
    else:
        logger.warning(f"Local cache file not found: {cache_file}")

    # Build lowercase name -> ID mapping and ID -> base64 image mapping
    name_to_id: Dict[str, str] = dict(FALLBACK_CROP_IDS)
    id_to_image: Dict[str, str] = {}

    if objects_data and isinstance(objects_data, list):
        for item in objects_data:
            obj_id = str(item.get("id"))
            img_b64 = item.get("image", "")
            if img_b64:
                if not img_b64.startswith("data:image/"):
                    img_b64 = f"data:image/png;base64,{img_b64}"
                id_to_image[obj_id] = img_b64

            names = item.get("names", {})
            en_name = names.get("data-en-US")
            if en_name:
                name_to_id[en_name.strip().lower()] = obj_id

    return name_to_id, id_to_image


def find_all_saves(saves_dir: str | Path) -> List[Path]:
    """
    Discovers all unique Stardew Valley saves in saves_dir.
    Groups saves by farm folder, picks the primary save file for each farm,
    ignores backup files (*_old, *_SVBAK, *_SVEMERG, EMERGENCY_SAVE),
    and returns them sorted by last modified time (most recent first).
    """
    base_dir = Path(saves_dir)
    if not base_dir.exists():
        logger.warning(f"Saves directory does not exist: {base_dir}")
        return []

    ignored_patterns = ("_old", "_svbak", "_svemerg", "emergency_save", ".tmp")
    farms_map: Dict[str, Path] = {}

    # Check immediate entries in saves_dir
    try:
        entries = list(base_dir.iterdir())
    except OSError as e:
        logger.error(f"Error reading saves directory {base_dir}: {e}")
        return []

    for item in entries:
        if item.is_dir():
            d_name = item.name.lower()
            if any(d_name.endswith(pat) for pat in ignored_patterns) or d_name.startswith("."):
                continue

            # In the farm directory, locate valid save candidates
            candidates: List[Path] = []
            try:
                for f in item.iterdir():
                    if f.is_file():
                        f_name = f.name.lower()
                        if any(f_name.endswith(pat) or f_name == pat for pat in ignored_patterns):
                            continue
                        if f_name.startswith("."):
                            continue
                        if f.stat().st_size > 100:
                            candidates.append(f)
            except OSError:
                continue

            if candidates:
                # Prefer primary file matching directory name, then SaveGameInfo, then latest modified
                primary = next((c for c in candidates if c.name == item.name), None)
                if not primary:
                    primary = next((c for c in candidates if c.name == "SaveGameInfo"), None)
                if not primary:
                    primary = max(candidates, key=lambda p: p.stat().st_mtime)
                farms_map[item.name] = primary

        elif item.is_file():
            # Root-level save file
            f_name = item.name.lower()
            if not any(f_name.endswith(pat) or f_name == pat for pat in ignored_patterns):
                if not f_name.startswith(".") and item.stat().st_size > 100:
                    farms_map[item.stem] = item

    # Sort discovered saves by modification time descending (most recent first)
    sorted_saves = sorted(farms_map.values(), key=lambda p: p.stat().st_mtime, reverse=True)
    logger.info(f"Discovered {len(sorted_saves)} unique save(s) in {base_dir}")
    return sorted_saves


def find_newest_save(saves_dir: str | Path) -> Optional[Path]:
    """
    Finds the most recently modified valid Stardew Valley save file in saves_dir.
    """
    saves = find_all_saves(saves_dir)
    return saves[0] if saves else None


def extract_daily_intel(
    root: ET.Element,
    player: Optional[ET.Element],
    current_season: str,
    day_of_month: int,
    year: int,
    name_to_id: Dict[str, str],
    id_to_image: Dict[str, str],
) -> Dict[str, Any]:
    """Extracts Daily Farm Intel: Weather, Daily Luck, Birthdays, and Town Social Radar."""
    daily_luck_val = float(root.findtext("dailyLuck") or 0.0)
    luck_info = evaluate_luck(daily_luck_val)

    # Weather
    w_tomorrow_code = root.findtext("weatherForTomorrow") or "Sun"
    weather_tomorrow = WEATHER_MAPPINGS.get(
        w_tomorrow_code,
        {"name": w_tomorrow_code, "icon": "🌤️", "color": "#facc15", "desc": "Unknown weather conditions."},
    )

    # Ginger Island Weather if unlocked
    island_tomorrow = None
    loc_contexts = root.find("locationContexts")
    if loc_contexts is not None:
        for item in loc_contexts.findall("item"):
            if item.findtext("key/string") == "Island":
                isl_code = item.findtext("value/LocationWeather/weatherForTomorrow")
                if isl_code:
                    island_tomorrow = WEATHER_MAPPINGS.get(
                        isl_code,
                        {"name": isl_code, "icon": "🏝️", "color": "#38bdf8", "desc": "Island weather."},
                    )

    # Friendships from player
    friendships: Dict[str, Dict[str, Any]] = {}
    if player is not None and player.find("friendshipData") is not None:
        for item in player.find("friendshipData").findall("item"):
            vname = item.findtext("key/string")
            f_node = item.find("value/Friendship")
            if vname and f_node is not None:
                pts = int(f_node.findtext("Points") or 0)
                gifts_w = int(f_node.findtext("GiftsThisWeek") or 0)
                gifts_t = int(f_node.findtext("GiftsToday") or 0)
                talked = (f_node.findtext("TalkedToToday") or "false").lower() == "true"
                status = f_node.findtext("Status") or "Friendly"
                friendships[vname] = {
                    "points": pts,
                    "hearts": pts // 250,
                    "heart_pct": round(((pts % 250) / 250) * 100, 1),
                    "gifts_this_week": gifts_w,
                    "gifts_today": gifts_t,
                    "talked_today": talked,
                    "status": status,
                }

    # Calculate Season & Day of Year for Birthday Radar
    curr_season_lower = current_season.lower()
    curr_season_idx = SEASONS_ORDER.index(curr_season_lower) if curr_season_lower in SEASONS_ORDER else 0
    curr_day_of_year = curr_season_idx * 28 + day_of_month

    social_radar: List[Dict[str, Any]] = []
    upcoming_birthdays: List[Dict[str, Any]] = []

    for vname, vdata in VILLAGER_DATA.items():
        b_season = vdata["season"]
        b_day = vdata["day"]
        b_season_lower = b_season.lower()
        b_season_idx = SEASONS_ORDER.index(b_season_lower) if b_season_lower in SEASONS_ORDER else 0
        b_day_of_year = b_season_idx * 28 + b_day
        days_away = (b_day_of_year - curr_day_of_year) % 112

        f_info = friendships.get(
            vname,
            {
                "points": 0,
                "hearts": 0,
                "heart_pct": 0,
                "gifts_this_week": 0,
                "gifts_today": 0,
                "talked_today": False,
                "status": "Friendly",
            },
        )

        # Max hearts: 8 for unmarried datables, 14 for spouse, 10 for normal
        if f_info["status"] == "Married":
            max_hearts = 14
        elif vdata["datable"] and f_info["status"] != "Dating":
            max_hearts = 8
        else:
            max_hearts = 10

        # Resolve loved gift sprites
        loved_items = []
        for g_name in vdata["loved"]:
            gid = name_to_id.get(g_name.strip().lower(), "")
            img = id_to_image.get(gid, "")
            loved_items.append({"name": g_name, "id": gid, "image": img})

        entry = {
            "name": vname,
            "season": b_season,
            "day": b_day,
            "days_away": days_away,
            "datable": vdata["datable"],
            "max_hearts": max_hearts,
            "friendship": f_info,
            "loved_gifts": loved_items,
        }
        social_radar.append(entry)

        if days_away <= 7:
            badge_text = "TODAY! 🎂" if days_away == 0 else ("Tomorrow! 🎈" if days_away == 1 else f"In {days_away} days")
            upcoming_birthdays.append({**entry, "badge_text": badge_text})

    # Sort social radar: highest hearts first, then alphabetically
    social_radar.sort(key=lambda x: (-x["friendship"]["points"], x["name"]))
    upcoming_birthdays.sort(key=lambda x: x["days_away"])

    return {
        "weather": {
            "tomorrow": weather_tomorrow,
            "island_tomorrow": island_tomorrow,
        },
        "luck": luck_info,
        "birthdays_alert": upcoming_birthdays,
        "social_radar": social_radar,
    }


def extract_collections(
    root: ET.Element,
    player: Optional[ET.Element],
    id_to_image: Dict[str, str],
    shipped_items: Dict[str, int],
) -> Dict[str, Any]:
    """Extracts interactive Collections: Fish (Master Angler), Museum (Artifacts & Minerals), and Shipping."""
    # 1. Fish Collection
    fish_caught_map: Dict[str, int] = {}
    if player is not None and player.find("fishCaught") is not None:
        for item in player.find("fishCaught").findall("item"):
            key = item.findtext("key/string") or item.findtext("key/int")
            if key:
                clean_id = key.replace("(O)", "").strip()
                counts = [int(x.text) for x in item.findall("value/ArrayOfInt/int")]
                fish_caught_map[clean_id] = counts[0] if counts else 1

    fish_list: List[Dict[str, Any]] = []
    caught_fish_count = 0
    for fid, fname, seasons, weather, location, time_range in FISH_METADATA:
        clean_id = fid.replace("(O)", "").strip()
        count = fish_caught_map.get(clean_id, fish_caught_map.get(f"(O){clean_id}", 0))
        if count == 0 and clean_id.lower() in [k.lower() for k in fish_caught_map]:
            for k, v in fish_caught_map.items():
                if k.lower() == clean_id.lower():
                    count = v
                    break

        is_caught = count > 0
        if is_caught:
            caught_fish_count += 1

        img_b64 = id_to_image.get(clean_id, "")
        fish_list.append({
            "id": clean_id,
            "name": fname,
            "image": img_b64,
            "is_caught": is_caught,
            "count": count,
            "seasons": seasons,
            "weather": weather,
            "location": location,
            "time": time_range,
        })

    fish_total = len(FISH_METADATA)
    fish_pct = round((caught_fish_count / fish_total) * 100, 1) if fish_total else 0.0

    # 2. Museum Collection
    museum_pieces: set = set()
    for loc in root.findall(".//GameLocation"):
        loc_name = loc.findtext("name")
        if loc_name == "ArchaeologyHouse" or loc.get("{http://www.w3.org/2001/XMLSchema-instance}type") == "LibraryMuseum":
            pieces = loc.find("museumPieces")
            if pieces is not None:
                for p in pieces.findall("item"):
                    val = p.findtext("value/int") or p.findtext("value/string")
                    if val:
                        museum_pieces.add(val.replace("(O)", "").strip())

    museum_items: List[Dict[str, Any]] = []
    donated_count = 0
    cache_file = DEFAULT_CACHE_FILE
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            for item in c_data:
                ot = item.get("objectType")
                if ot in ("Arch", "Minerals"):
                    iid = str(item.get("id"))
                    name = item.get("names", {}).get("data-en-US", "")
                    cat = "Artifact" if ot == "Arch" else "Mineral"
                    is_donated = iid in museum_pieces or f"(O){iid}" in museum_pieces
                    if is_donated:
                        donated_count += 1
                    img_raw = item.get("image", "")
                    if img_raw and not img_raw.startswith("data:image/"):
                        img_raw = f"data:image/png;base64,{img_raw}"
                    museum_items.append({
                        "id": iid,
                        "name": name,
                        "category": cat,
                        "image": img_raw,
                        "is_donated": is_donated,
                    })
        except Exception as e:
            logger.error(f"Error building museum collection: {e}")

    museum_items.sort(key=lambda x: (x["category"], x["name"]))
    museum_total = len(museum_items) or 95
    museum_pct = round((donated_count / museum_total) * 100, 1) if museum_total else 0.0

    # 3. Shipping Collection
    shipping_items: List[Dict[str, Any]] = []
    shipped_count = 0
    for sid, sname in SHIPPING_ITEMS_DEF:
        clean_id = sid.replace("(O)", "").strip()
        count = shipped_items.get(clean_id, shipped_items.get(f"(O){clean_id}", 0))
        if count == 0:
            for k, v in shipped_items.items():
                if k.lower() == clean_id.lower():
                    count = v
                    break

        is_shipped = count > 0
        if is_shipped:
            shipped_count += 1

        img_b64 = id_to_image.get(clean_id, "")
        shipping_items.append({
            "id": clean_id,
            "name": sname,
            "image": img_b64,
            "is_shipped": is_shipped,
            "count": count,
        })

    shipping_total = len(SHIPPING_ITEMS_DEF)
    shipping_pct = round((shipped_count / shipping_total) * 100, 1) if shipping_total else 0.0

    return {
        "fish": {
            "caught_count": caught_fish_count,
            "total_count": fish_total,
            "percent": fish_pct,
            "items": fish_list,
            "fish_list": fish_list,
        },
        "museum": {
            "donated_count": donated_count,
            "total_count": museum_total,
            "percent": museum_pct,
            "items": museum_items,
            "item_list": museum_items,
        },
        "shipping": {
            "shipped_count": shipped_count,
            "total_count": shipping_total,
            "percent": shipping_pct,
            "items": shipping_items,
            "item_list": shipping_items,
        },
    }


# ==============================================================================
# CANONICAL SKILLS, PROFESSIONS & 1.6 MASTERY SYSTEM
# ==============================================================================

SKILL_XP_THRESHOLDS: List[int] = [0, 100, 380, 770, 1300, 2150, 3300, 4800, 6900, 10000, 15000]
MASTERY_THRESHOLDS: List[int] = [10000, 25000, 45000, 70000, 100000]

PROFESSIONS_DATA: Dict[int, Dict[str, Any]] = {
    # Farming
    0: {"name": "Rancher", "skill": "farming", "tier": 5, "desc": "Animal products worth 20% more."},
    1: {"name": "Tiller", "skill": "farming", "tier": 5, "desc": "Crops worth 10% more."},
    2: {"name": "Coopmaster", "skill": "farming", "tier": 10, "parent": 0, "desc": "Befriend coop animals faster. Incubation time cut in half."},
    3: {"name": "Shepherd", "skill": "farming", "tier": 10, "parent": 0, "desc": "Befriend barn animals faster. Sheep produce wool faster."},
    4: {"name": "Artisan", "skill": "farming", "tier": 10, "parent": 1, "desc": "Artisan Goods (wine, cheese, oil, etc.) worth 40% more."},
    5: {"name": "Agriculturist", "skill": "farming", "tier": 10, "parent": 1, "desc": "All crops grow 10% faster."},
    # Fishing
    6: {"name": "Fisher", "skill": "fishing", "tier": 5, "desc": "Fish worth 25% more."},
    7: {"name": "Trapper", "skill": "fishing", "tier": 5, "desc": "Resources required to craft crab pots reduced."},
    8: {"name": "Angler", "skill": "fishing", "tier": 10, "parent": 6, "desc": "Fish worth 50% more."},
    9: {"name": "Pirate", "skill": "fishing", "tier": 10, "parent": 6, "desc": "Chance to find treasure doubled."},
    10: {"name": "Mariner", "skill": "fishing", "tier": 10, "parent": 7, "desc": "Crab pots never produce junk items."},
    11: {"name": "Luremaster", "skill": "fishing", "tier": 10, "parent": 7, "desc": "Crab pots no longer require bait."},
    # Foraging
    12: {"name": "Forester", "skill": "foraging", "tier": 5, "desc": "Wood worth 50% more."},
    13: {"name": "Gatherer", "skill": "foraging", "tier": 5, "desc": "Chance for double harvest of foraged items."},
    14: {"name": "Lumberjack", "skill": "foraging", "tier": 10, "parent": 12, "desc": "All trees have a chance to drop hardwood."},
    15: {"name": "Tapper", "skill": "foraging", "tier": 10, "parent": 12, "desc": "Syrups sell for 25% more."},
    16: {"name": "Botanist", "skill": "foraging", "tier": 10, "parent": 13, "desc": "Foraged items are always of highest (iridium) quality."},
    17: {"name": "Tracker", "skill": "foraging", "tier": 10, "parent": 13, "desc": "Locations of foragable items are revealed."},
    # Mining
    18: {"name": "Miner", "skill": "mining", "tier": 5, "desc": "+1 ore per vein."},
    19: {"name": "Geologist", "skill": "mining", "tier": 5, "desc": "Chance for gems to appear in pairs."},
    20: {"name": "Blacksmith", "skill": "mining", "tier": 10, "parent": 18, "desc": "Metal bars worth 50% more."},
    21: {"name": "Prospector", "skill": "mining", "tier": 10, "parent": 18, "desc": "Chance to find coal doubled."},
    22: {"name": "Excavator", "skill": "mining", "tier": 10, "parent": 19, "desc": "Chance to find geodes doubled."},
    23: {"name": "Gemologist", "skill": "mining", "tier": 10, "parent": 19, "desc": "Gems worth 30% more."},
    # Combat
    24: {"name": "Fighter", "skill": "combat", "tier": 5, "desc": "All attacks deal 10% more damage. +15 max HP."},
    25: {"name": "Scout", "skill": "combat", "tier": 5, "desc": "Critical strike chance increased by 50%."},
    26: {"name": "Brute", "skill": "combat", "tier": 10, "parent": 24, "desc": "Deal 15% more damage."},
    27: {"name": "Defender", "skill": "combat", "tier": 10, "parent": 24, "desc": "+25 max HP."},
    28: {"name": "Acrobat", "skill": "combat", "tier": 10, "parent": 25, "desc": "Cooldown on special moves cut in half."},
    29: {"name": "Desperado", "skill": "combat", "tier": 10, "parent": 25, "desc": "Critical strikes are deadlier."},
}

MASTERY_SHRINES: List[Dict[str, Any]] = [
    {
        "id": 0,
        "name": "Farming Mastery",
        "icon": "🌾",
        "stat_key": "Mastery_0",
        "rewards": ["Iridium Scythe", "Mystic Tree Seed recipe", "Farmland Golden Mystery Boxes"],
        "desc": "Gain the power of Iridium farming and rapid scythe harvesting for all crops.",
    },
    {
        "id": 1,
        "name": "Fishing Mastery",
        "icon": "🎣",
        "stat_key": "Mastery_1",
        "rewards": ["Advanced Iridium Rod", "Challenge Bait recipe", "Golden Mystery Boxes from fishing"],
        "desc": "Equip two bobbers simultaneously and catch legendary yields.",
    },
    {
        "id": 2,
        "name": "Foraging Mastery",
        "icon": "🪓",
        "stat_key": "Mastery_2",
        "rewards": ["Treasure Totem recipe", "Mystic Tree Seed recipe", "Mystic Syrup & Golden Boxes"],
        "desc": "Summon rich treasure spots and harness mystical trees for rare syrup.",
    },
    {
        "id": 3,
        "name": "Mining Mastery",
        "icon": "⛏️",
        "stat_key": "Mastery_3",
        "rewards": ["Statue of Blessings recipe", "Heavy Furnace recipe", "Double gem node yield"],
        "desc": "Smelt bars with industrial speed and receive a powerful daily blessing statue.",
    },
    {
        "id": 4,
        "name": "Combat Mastery",
        "icon": "⚔️",
        "stat_key": "Mastery_4",
        "rewards": ["Trinkets Equipment Slot", "Anvil recipe", "Mini-Forge recipe"],
        "desc": "Unlock powerful combat trinkets and portable equipment reforging anywhere.",
    },
]


def extract_skills_and_mastery(
    player: ET.Element,
    root: ET.Element,
) -> Dict[str, Any]:
    """
    Extracts skill levels, exact experience points, active professions,
    and 1.6 Mastery Cave progression from player save data.
    """
    # 1. Experience points array in <player><experiencePoints>
    # Stardew Valley order: [0: Farming, 1: Fishing, 2: Foraging, 3: Mining, 4: Combat, 5: Luck]
    xp_elems = player.find("experiencePoints")
    xp_vals = [0] * 6
    if xp_elems is not None:
        for idx, el in enumerate(xp_elems.findall("int")[:6]):
            try:
                xp_vals[idx] = int(el.text.strip())
            except (ValueError, AttributeError):
                xp_vals[idx] = 0

    # Skill levels
    levels = {
        "farming": int(player.findtext("farmingLevel", "0")),
        "fishing": int(player.findtext("fishingLevel", "0")),
        "foraging": int(player.findtext("foragingLevel", "0")),
        "mining": int(player.findtext("miningLevel", "0")),
        "combat": int(player.findtext("combatLevel", "0")),
        "luck": int(player.findtext("luckLevel", "0")),
    }

    # Active professions
    prof_elem = player.find("professions")
    active_prof_ids = set()
    if prof_elem is not None:
        for el in prof_elem.findall("int"):
            try:
                active_prof_ids.add(int(el.text.strip()))
            except (ValueError, AttributeError):
                pass

    # Build 5 core skills
    skill_definitions = [
        ("farming", "Farming", "🌾", xp_vals[0]),
        ("mining", "Mining", "⛏️", xp_vals[3]),
        ("foraging", "Foraging", "🪓", xp_vals[2]),
        ("fishing", "Fishing", "🎣", xp_vals[1]),
        ("combat", "Combat", "⚔️", xp_vals[4]),
    ]

    skills_list: List[Dict[str, Any]] = []
    total_skill_levels = 0

    for key, label, icon, current_xp in skill_definitions:
        lvl = levels.get(key, 0)
        total_skill_levels += min(10, lvl)

        is_max = lvl >= 10
        cur_thresh = SKILL_XP_THRESHOLDS[min(10, lvl)]
        next_thresh = SKILL_XP_THRESHOLDS[min(10, lvl + 1)] if lvl < 10 else cur_thresh
        xp_into_level = max(0, current_xp - cur_thresh)
        xp_needed = max(0, next_thresh - current_xp) if lvl < 10 else 0
        level_span = max(1, next_thresh - cur_thresh) if lvl < 10 else 1
        pct = 100.0 if is_max else min(100.0, round((xp_into_level / level_span) * 100, 1))

        # Active and available professions for this skill
        active_profs: List[Dict[str, Any]] = []
        all_profs_for_skill: List[Dict[str, Any]] = []

        for pid, pdata in PROFESSIONS_DATA.items():
            if pdata["skill"] == key:
                is_active = pid in active_prof_ids
                prof_entry = {
                    "id": pid,
                    "name": pdata["name"],
                    "tier": pdata["tier"],
                    "desc": pdata["desc"],
                    "parent": pdata.get("parent"),
                    "is_active": is_active,
                }
                all_profs_for_skill.append(prof_entry)
                if is_active:
                    active_profs.append(prof_entry)

        # Sort active professions: Tier 5 first, Tier 10 second
        active_profs.sort(key=lambda p: p["tier"])

        skills_list.append({
            "key": key,
            "name": label,
            "icon": icon,
            "level": lvl,
            "is_max": is_max,
            "current_xp": current_xp,
            "current_xp_formatted": f"{current_xp:,}",
            "current_threshold": cur_thresh,
            "next_threshold": next_thresh,
            "xp_into_level": xp_into_level,
            "xp_needed": xp_needed,
            "xp_needed_formatted": f"{xp_needed:,}",
            "percent": pct,
            "active_professions": active_profs,
            "all_professions": all_profs_for_skill,
        })

    # 1.6 Mastery System
    is_mastery_unlocked = total_skill_levels >= 50
    missing_skill_levels = max(0, 50 - total_skill_levels)

    mastery_exp = 0
    mastery_levels_spent = 0
    shrine_claims: Dict[str, bool] = {}

    stats_elem = player.find("stats")
    if stats_elem is not None:
        vals_elem = stats_elem.find("Values")
        if vals_elem is not None:
            for item in vals_elem.findall("item"):
                k = item.findtext("key/string")
                if not k:
                    continue
                v_el = item.find("value")
                v_val = 0
                if v_el is not None:
                    try:
                        v_val = int(v_el.findtext("unsignedInt") or v_el.findtext("int") or v_el.text or "0")
                    except ValueError:
                        v_val = 0

                if k == "MasteryExp":
                    mastery_exp = v_val
                elif k == "MasteryLevelsSpent":
                    mastery_levels_spent = v_val
                elif k.startswith("Mastery_"):
                    shrine_claims[k] = v_val > 0

    # Calculate points earned (0 to 5)
    points_earned = 0
    for thresh in MASTERY_THRESHOLDS:
        if mastery_exp >= thresh:
            points_earned += 1
        else:
            break

    points_available = max(0, points_earned - mastery_levels_spent)
    is_all_mastered = points_earned >= 5

    # Progress to next mastery point
    if points_earned >= 5:
        next_mastery_threshold = MASTERY_THRESHOLDS[-1]
        mastery_pct = 100.0
        mastery_xp_needed = 0
    else:
        prev_thresh = MASTERY_THRESHOLDS[points_earned - 1] if points_earned > 0 else 0
        next_thresh = MASTERY_THRESHOLDS[points_earned]
        next_mastery_threshold = next_thresh
        span = max(1, next_thresh - prev_thresh)
        into_point = max(0, mastery_exp - prev_thresh)
        mastery_pct = min(100.0, round((into_point / span) * 100, 1))
        mastery_xp_needed = max(0, next_thresh - mastery_exp)

    # Shrines metadata
    shrines_result: List[Dict[str, Any]] = []
    for s in MASTERY_SHRINES:
        claimed = shrine_claims.get(s["stat_key"], False)
        shrines_result.append({
            "id": s["id"],
            "name": s["name"],
            "icon": s["icon"],
            "claimed": claimed,
            "rewards": s["rewards"],
            "desc": s["desc"],
        })

    # Summary text
    if not is_mastery_unlocked:
        needed_list = [f"{s['name']} (L{s['level']})" for s in skills_list if not s["is_max"]]
        status_text = f"Mastery Cave Locked: Reach Level 10 in {', '.join(needed_list)} ({total_skill_levels}/50 levels achieved)"
    elif points_available > 0:
        status_text = f"Mastery Cave Open: {points_available} Mastery Point{'s' if points_available > 1 else ''} available to spend!"
    elif is_all_mastered:
        status_text = "Mastery Cave Fully Mastered! All 5 shrines claimed."
    else:
        status_text = f"Next Mastery Point in {mastery_xp_needed:,} XP ({mastery_pct}%)"

    return {
        "total_skill_levels": total_skill_levels,
        "max_skill_levels": 50,
        "total_skills_percent": round((total_skill_levels / 50) * 100, 1),
        "luck_level": levels.get("luck", 0),
        "skills": skills_list,
        "mastery": {
            "is_unlocked": is_mastery_unlocked,
            "missing_levels": missing_skill_levels,
            "mastery_exp": mastery_exp,
            "mastery_exp_formatted": f"{mastery_exp:,}",
            "points_earned": points_earned,
            "points_spent": mastery_levels_spent,
            "points_available": points_available,
            "is_all_mastered": is_all_mastered,
            "next_threshold": next_mastery_threshold,
            "next_threshold_formatted": f"{next_mastery_threshold:,}",
            "xp_needed": mastery_xp_needed,
            "xp_needed_formatted": f"{mastery_xp_needed:,}",
            "percent": mastery_pct,
            "status_text": status_text,
            "shrines": shrines_result,
        },
    }


def build_ability_xp(skills_and_mastery: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Builds a flat XP map for the five main skills plus Mastery Cave progress.

    Skill XP comes from <player><experiencePoints> (via extract_skills_and_mastery).
    Mastery XP comes from stats Values MasteryExp. The save's optional <abilities>
    element is unrelated and is intentionally not used here.
    """
    ability_xp: Dict[str, Dict[str, Any]] = {}

    for skill in skills_and_mastery.get("skills", []):
        ability_xp[f"skill_{skill['key']}"] = {
            "name": skill["name"],
            "icon": skill["icon"],
            "xp": skill["current_xp"],
            "xp_formatted": skill["current_xp_formatted"],
            "level": skill["level"],
            "is_max": skill["is_max"],
            "progress": skill["percent"],
            "next_level_xp": skill["xp_needed"],
            "next_level_xp_formatted": skill.get("xp_needed_formatted", f"{skill['xp_needed']:,}"),
        }

    mastery = skills_and_mastery.get("mastery", {})
    ability_xp["mastery"] = {
        "name": "Mastery",
        "icon": "⭐",
        "xp": mastery.get("mastery_exp", 0),
        "xp_formatted": mastery.get("mastery_exp_formatted", "0"),
        "level": mastery.get("points_earned", 0),
        "is_max": mastery.get("is_all_mastered", False),
        "progress": mastery.get("percent", 0.0),
        "next_level_xp": mastery.get("xp_needed", 0),
        "next_level_xp_formatted": mastery.get("xp_needed_formatted", "0"),
        "is_unlocked": mastery.get("is_unlocked", False),
        "points_available": mastery.get("points_available", 0),
        "status_text": mastery.get("status_text", ""),
    }

    return ability_xp


def parse_save(
    save_path: str | Path,
    mappings: Optional[Tuple[Dict[str, str], Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Parses a Stardew Valley save file and returns player info and Polyculture achievement progress.
    Supports both full SaveGame files and SaveGameInfo files.
    """
    save_file = Path(save_path)
    if not save_file.exists():
        raise FileNotFoundError(f"Save file not found: {save_file}")

    if mappings is None:
        name_to_id, id_to_image = load_object_mappings()
    else:
        name_to_id, id_to_image = mappings

    logger.info(f"Parsing save file: {save_file.name}")
    tree = ET.parse(save_file)
    root = tree.getroot()

    # In full save files, root is <SaveGame> and player is under <player>.
    # In SaveGameInfo, root is <Farmer> directly.
    if root.tag == "SaveGame":
        player = root.find("player")
        game_elem = root
    elif root.tag == "Farmer":
        player = root
        game_elem = root
    else:
        player = root.find("player") or root
        game_elem = root

    if player is None:
        raise ValueError(f"Could not locate player element in XML: {save_file}")

    farmer_name = player.findtext("name", "Unknown Farmer").strip()
    farm_name = player.findtext("farmName", "Unknown Farm").strip()
    raw_money = player.findtext("totalMoneyEarned", "0").strip()
    try:
        total_money = int(raw_money)
    except ValueError:
        total_money = 0

    # Ingame date if present
    raw_season = game_elem.findtext("currentSeason", "spring").strip()
    current_season = raw_season.capitalize() if raw_season else "Spring"
    raw_day = game_elem.findtext("dayOfMonth", "1").strip()
    day_num = int(raw_day) if raw_day.isdigit() else 1
    raw_year = game_elem.findtext("year", "1").strip()
    year_num = int(raw_year) if raw_year.isdigit() else 1
    date_str = f"Year {year_num}, {current_season} {day_num}"

    # Parse shipped items dictionary from <basicShipped>
    basic_shipped = player.find("basicShipped")
    shipped_items: Dict[str, int] = {}

    if basic_shipped is not None:
        for item in basic_shipped.findall("item"):
            key_elem = item.find("key")
            val_elem = item.find("value")
            if key_elem is not None and val_elem is not None:
                raw_k = key_elem.findtext("string") or key_elem.findtext("int") or key_elem.text
                raw_v = val_elem.findtext("int") or val_elem.findtext("string") or val_elem.text
                if raw_k is not None and raw_v is not None:
                    k_str = str(raw_k).strip()
                    try:
                        count = int(raw_v)
                    except ValueError:
                        count = 0
                    shipped_items[k_str] = count
                    # Normalize (O) prefix from 1.6+ (e.g. '(O)24' -> '24')
                    if k_str.startswith("(O)"):
                        shipped_items[k_str[3:]] = count

    # Evaluate 28 Polyculture crops
    crops_result: List[Dict[str, Any]] = []
    completed_count = 0
    TARGET_SHIPPED = 15

    for crop_def in POLYCULTURE_CROPS:
        name = crop_def["name"]
        season = crop_def["season"]
        obj_id = name_to_id.get(name.lower(), FALLBACK_CROP_IDS.get(name.lower(), ""))
        image_b64 = id_to_image.get(obj_id, "")

        # Shipped count lookup by ID or (O)ID
        shipped = shipped_items.get(obj_id, 0)
        if shipped == 0 and f"(O){obj_id}" in shipped_items:
            shipped = shipped_items[f"(O){obj_id}"]

        is_completed = shipped >= TARGET_SHIPPED
        remaining = max(0, TARGET_SHIPPED - shipped)
        if is_completed:
            completed_count += 1

        crops_result.append({
            "name": name,
            "season": season,
            "id": obj_id,
            "image": image_b64,
            "shipped": shipped,
            "target": TARGET_SHIPPED,
            "remaining": remaining,
            "is_completed": is_completed,
            "status_text": "[✓ Done]" if is_completed else f"[Need {remaining} more]",
        })

    total_crops = len(POLYCULTURE_CROPS)
    progress_pct = round((completed_count / total_crops) * 100, 1)

    mtime = save_file.stat().st_mtime
    last_mod_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
    # Clean farm identifier for UI tabs & URL anchors
    farm_id = save_file.parent.name if save_file.parent.name != save_file.name else save_file.stem
    if not farm_id or farm_id.lower() in ("saves", "sv-analyzer", "data"):
        farm_id = f"{farm_name}_{save_file.stem}"

    # Extract Daily Intel and Collections
    daily_intel = extract_daily_intel(
        root=game_elem,
        player=player,
        current_season=current_season,
        day_of_month=day_num,
        year=year_num,
        name_to_id=name_to_id,
        id_to_image=id_to_image,
    )
    collections = extract_collections(
        root=game_elem,
        player=player,
        id_to_image=id_to_image,
        shipped_items=shipped_items,
    )
    skills_and_mastery = extract_skills_and_mastery(
        player=player,
        root=game_elem,
    )
    # Main skill XP (farming/fishing/foraging/mining/combat) + MasteryExp
    ability_xp = build_ability_xp(skills_and_mastery)

    return {
        "farm_id": farm_id,
        "save_file": str(save_file),
        "ability_xp": ability_xp,
        "save_filename": save_file.name,
        "last_modified": mtime,
        "last_modified_str": last_mod_str,
        "farmer_name": farmer_name,
        "farm_name": farm_name,
        "total_money": total_money,
        "total_money_formatted": f"{total_money:,}g",
        "date_str": date_str,
        "date_details": {
            "season": current_season,
            "day": day_num,
            "year": year_num,
        },
        "completed_count": completed_count,
        "total_crops": total_crops,
        "progress_percent": progress_pct,
        "is_all_completed": completed_count == total_crops,
        "crops": crops_result,
        "polyculture": {
            "completed_count": completed_count,
            "total_count": total_crops,
            "percent": progress_pct,
            "crops": crops_result,
        },
        "daily_intel": daily_intel,
        "collections": collections,
        "skills_and_mastery": skills_and_mastery,
    }


def parse_all_saves(
    saves_dir: str | Path,
    mappings: Optional[Tuple[Dict[str, str], Dict[str, str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Finds and parses all unique Stardew Valley saves in saves_dir.
    Returns a list of parsed farm objects sorted by last modified (newest first).
    """
    save_files = find_all_saves(saves_dir)
    if not save_files:
        return []

    if mappings is None:
        mappings = load_object_mappings()

    farms_data: List[Dict[str, Any]] = []
    for sf in save_files:
        try:
            data = parse_save(sf, mappings=mappings)
            farms_data.append(data)
        except Exception as e:
            logger.error(f"Error parsing save file {sf}: {e}", exc_info=True)

    if farms_data:
        for f in farms_data:
            f["is_newest"] = False

    return farms_data


if __name__ == "__main__":
    import sys

    default_saves = os.getenv(
        "SAVES_DIR",
        "/srv/docker/data/sv-analyzer/saves"
        if Path("/srv/docker/data/sv-analyzer/saves").exists()
        else ("/saves" if Path("/saves").exists() else "./Saves"),
    )
    saves_path = sys.argv[1] if len(sys.argv) > 1 else default_saves
    logger.info(f"Running parser standalone against: {saves_path}")

    target_path = Path(saves_path)
    if target_path.is_dir():
        all_farms = parse_all_saves(target_path)
        if not all_farms:
            logger.error(f"No valid saves found in {target_path}")
            sys.exit(1)
        print(f"\nDiscovered and parsed {len(all_farms)} farm(s):")
        for idx, f in enumerate(all_farms, 1):
            star = " (Latest)" if f.get("is_newest") else ""
            print(f"[{idx}] {f['farm_name']} Farm (Farmer: {f['farmer_name']}) - {f['date_str']}{star}")
            print(f"    Earnings: {f['total_money_formatted']} | Polyculture: {f['completed_count']}/{f['total_crops']} ({f['progress_percent']}%)")
            print(f"    File: {f['save_file']}")
    else:
        result = parse_save(target_path)
        print("\n" + "=" * 50)
        print(f" Farmer: {result['farmer_name']}")
        print(f" Farm: {result['farm_name']} Farm")
        print(f" Total Earnings: {result['total_money_formatted']}")
        print(f" Date: {result['date_str']}")
        print(f" Polyculture Progress: {result['completed_count']} / {result['total_crops']} Crops Completed ({result['progress_percent']}%)")
        print("=" * 50)
