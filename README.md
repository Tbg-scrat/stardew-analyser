# Stardew Valley Save Analyzer

A self-hosted web dashboard that watches Stardew Valley save files in real time and tracks farm progress across achievements, collections, skills, and daily intel. Built for **Stardew Valley 1.6+**.

![Stardew Valley 1.6+](https://img.shields.io/badge/Stardew%20Valley-1.6%2B-blue?style=flat-square)
![Status](https://img.shields.io/badge/Status-Self--Hosted-green?style=flat-square)

---

## Features

### Dashboard modules

| Module | What it tracks |
|---|---|
| **Daily Intel** | Tomorrow’s weather (valley + Ginger Island), daily luck / fortune-teller tier, upcoming birthdays (≤7 days), and a 34-villager social radar with hearts, gift limits, and loved gifts |
| **Skills & Mastery** | Farming, Fishing, Foraging, Mining, Combat levels with exact XP bars, active professions, and 1.6 Mastery Cave progress (points, shrines, unlock status) |
| **Abilities & Mastery** | Flat XP view of the five main skills plus MasteryExp (sourced from `experiencePoints` / `MasteryExp`, not the unused `<abilities>` XML) |
| **Polyculture** | All 28 seasonal crops for *Ship 15 of each crop*, with per-crop remaining counts and seasonal filters |
| **Fish Collection** | Master Angler checklist (69 entries) with seasons, weather, location, and time |
| **Museum** | Donated artifacts & minerals vs the archaeology house |
| **Full Shipment** | Full shipping collection progress |

### Platform

- **Multi-farm tabs** — discovers every unique save under the saves directory; newest farm highlighted; last-selected farm persisted in `localStorage`
- **Real-time watching** — `watchdog` observes save changes with a 2s debounce so half-written files are not parsed
- **Offline-first sprites** — downloads object ID / sprite mappings from GitHub once into `data/objects_cache.json`; later runs need no network
- **Docker + Nginx** — Python watcher regenerates static HTML; Nginx serves it on port 8080

---

## Polyculture crops (28)

Verified against the official Stardew Valley Wiki — ship **15 of each**:

| Season | Crops |
|---|---|
| **Spring (9)** | Cauliflower, Coffee Bean, Garlic, Green Bean, Kale, Parsnip, Potato, Rhubarb, Strawberry |
| **Summer (10)** | Blueberry, Corn, Hops, Hot Pepper, Melon, Radish, Red Cabbage, Starfruit, Tomato, Wheat |
| **Fall (9)** | Amaranth, Artichoke, Beet, Bok Choy, Cranberries, Eggplant, Grape, Pumpkin, Yam |

---

## Quick start (Docker Compose)

1. Point the compose volume at your Stardew saves (default mounts `./Saves`), or set `SAVES_PATH`:
   - **Windows**: `%APPDATA%\StardewValley\Saves`
   - **Linux / macOS**: `~/.config/StardewValley/Saves`
2. Launch:
   ```bash
   docker compose up -d
   ```
3. Open [http://localhost:8080](http://localhost:8080).

---

## Running locally (without Docker)

```bash
pip install -r requirements.txt
```

| Command | Purpose |
|---|---|
| `python parser.py ./Saves` | Parse saves and print a summary to the terminal |
| `python renderer.py ./Saves` | Generate `./web/index.html` once |
| `python watcher.py` | Watch saves and regenerate the dashboard on change |
| `python test_analyser.py` | Run the fixture-based test suite (uses `./Saves`) |

Open `./web/index.html` in a browser after rendering.

---

## Architecture

```
Save change → watcher (debounce) → parser (XML → farm dicts)
                                 → renderer (Jinja2) → web/index.html
                                 → nginx (:8080)
```

| Environment variable | Default | Description |
|---|---|---|
| `SAVES_DIR` | `/saves` or `./Saves` | Directory containing farm save folders |
| `OUTPUT_FILE` | `/app/web/index.html` or `./web/index.html` | Generated dashboard path |
| `TEMPLATES_DIR` | `/app/templates` or `./templates` | Jinja2 templates |
| `DATA_DIR` / `CACHE_FILE` | `./data` / `objects_cache.json` | Offline object ID & sprite cache |
| `DEBOUNCE_SECONDS` | `2.0` (`0.5` if `DEV_MODE` is set) | Quiet period after a save write before re-parse |

### Project layout

```
stardew-analyser/
├── data/
│   └── objects_cache.json      # Cached object IDs & base64 sprites
├── templates/
│   └── index.html              # Dashboard template (CSS + JS + modules)
├── web/
│   └── index.html              # Generated static site (Nginx root)
├── Saves/                      # Local / test save files (mount or copy)
├── parser.py                   # XML parser: polyculture, intel, collections, skills
├── renderer.py                 # Jinja2 render helper
├── watcher.py                  # Debounced filesystem watcher
├── test_analyser.py            # Automated tests against fixture saves
├── docker-compose.yml          # watcher + nginx:alpine
├── Dockerfile                  # Python 3.11 watcher image
├── requirements.txt            # watchdog, jinja2, …
└── deploy/                     # Optional host deploy copies (stack + bind-mount data)
```

---

## Tests

```bash
python test_analyser.py
```

Covers the 28-crop list, object cache/sprites, multi-farm discovery, daily intel, collections, skills/mastery XP (`ability_xp`), and HTML rendering.
