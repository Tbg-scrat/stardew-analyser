# -*- coding: utf-8 -*-
"""
Gift preferences reference data for Stardew Valley villagers.
Contains item names and wiki icon mappings for loved gifts.
"""

def format_wiki_filename(name):
    return name.replace(" ", "_").replace("'", "%27")

# Map of villagers to their loved gifts
VILLAGER_LOVED_GIFTS = {
    "Abigail": ["Amethyst", "Banana Pudding", "Blackberry Cobbler", "Chocolate Cake", "Pufferfish", "Pumpkin", "Spicy Eel"],
    "Alex": ["Complete Breakfast", "Salmon Dinner"],
    "Caroline": ["Fish Tacos", "Green Tea", "Summer Spangle", "Tropical Curry"],
    "Clint": ["Amethyst", "Aquamarine", "Emerald", "Fiddlehead Risotto", "Gold Bar", "Iridium Bar", "Jade", "Omni Geode", "Ruby", "Topaz"],
    "Demetrius": ["Bean Hotpot", "Ice Cream", "Rice Pudding", "Strawberry"],
    "Elliott": ["Crab Cakes", "Duck Feather", "Lobster", "Pomegranate", "Squid Ink", "Tom Kha Soup"],
    "Emily": ["Amethyst", "Aquamarine", "Cloth", "Emerald", "Jade", "Ruby", "Survival Burger", "Topaz", "Wool"],
    "Evelyn": ["Beet", "Chocolate Cake", "Diamond", "Fairy Rose", "Stuffing", "Tulip"],
    "George": ["Fried Mushroom", "Leek"],
    "Gus": ["Diamond", "Escargot", "Fish Tacos", "Orange"],
    "Haley": ["Coconut", "Fruit Salad", "Pink Cake", "Sunflower"],
    "Harvey": ["Coffee", "Pickles", "Super Meal", "Truffle Oil", "Wine"],
    "Jas": ["Fairy Rose", "Pink Cake", "Plum Pudding"],
    "Jodi": ["Chocolate Cake", "Crispy Bass", "Eggplant Parmesan", "Fried Eel", "Pancakes", "Rhubarb Pie", "Vegetable Medley"],
    "Kent": ["Fiddlehead Risotto", "Roasted Hazelnuts"],
    "Krobus": ["Diamond", "Iridium Bar", "Monster Compendium", "Pumpkin", "Void Egg", "Void Mayonnaise", "Wild Horseradish"],
    "Leah": ["Goat Cheese", "Poppyseed Muffin", "Salad", "Stir Fry", "Truffle", "Vegetable Medley", "Wine"],
    "Leo": ["Duck Feather", "Mango", "Ostrich Egg", "Poi"],
    "Lewis": ["Autumn's Bounty", "Glazed Yams", "Green Tea", "Hot Pepper", "Vegetable Medley"],
    "Linus": ["Blueberry Tart", "Cactus Fruit", "Coconut", "Dish O' The Sea", "Yam"],
    "Marnie": ["Farmer's Lunch", "Pink Cake", "Pumpkin Pie", "Diamond"],
    "Maru": ["Battery Pack", "Cheese Cauliflower", "Diamond", "Gold Bar", "Iridium Bar", "Miner's Treat", "Pepper Poppers", "Radioactive Bar", "Rhubarb Pie", "Strawberry"],
    "Pam": ["Beer", "Cactus Fruit", "Glazed Yams", "Mead", "Pale Ale", "Parsnip", "Parsnip Soup"],
    "Penny": ["Diamond", "Emerald", "Melon", "Poppy", "Poppyseed Muffin", "Red Plate", "Roots Platter", "Sandfish", "Tom Kha Soup"],
    "Pierre": ["Fried Squid"],
    "Robin": ["Goat Cheese", "Peach", "Spaghetti"],
    "Sam": ["Cactus Fruit", "Maple Bar", "Pizza", "Tigerseye"],
    "Sandy": ["Cactus Fruit", "Daffodil", "Mango Sticky Rice", "Super Meal"],
    "Sebastian": ["Frozen Tear", "Obsidian", "Pumpkin Soup", "Sashimi", "Void Egg"],
    "Shane": ["Beer", "Hot Pepper", "Pepper Poppers", "Pizza"],
    "Vincent": ["Cranberry Candy", "Ginger Ale", "Pink Cake", "Snail"],
    "Willy": ["Catfish", "Diamond", "Iridium Bar", "Mead", "Octopus", "Pumpkin", "Sea Cucumber", "Sturgeon"],
    "Wizard": ["Book of Mysteries", "Ectoplasm", "Frozen Tear", "Purple Mushroom", "Super Cucumber"]
}

def get_loved_gifts(villager_name):
    """Returns a list of dicts containing name and wiki_icon for a villager's loved gifts."""
    gifts = VILLAGER_LOVED_GIFTS.get(villager_name, [])
    return [{"name": name, "wiki_icon": format_wiki_filename(name)} for name in gifts]
