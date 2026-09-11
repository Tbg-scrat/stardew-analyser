# 🌾 Stardew Valley Save Analyzer

A lightweight, local-first web dashboard for parsing Stardew Valley save files. Designed for self-hosted homelabs, it parses raw save XML and renders a dynamic Jinja2 dashboard for multi-farm progress monitoring.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- **Multi-Farm Support:** Automatically detects and indexes all farms in your `/saves` directory with top-level tab switching.
- **Collection Tracking:**
  - 📦 **Shipping:** Item counts and completion mapping.
  - 🐟 **Fishing:** Fish caught, record lengths, and counts.
  - 🏺 **Museum:** Donated artifacts and minerals.
  - 🍳 **Cooking:** Recipes unlocked and cooked counts.
- **Social Radar:** Track villager friendship heart levels, daily chat statuses, and weekly gift counts.
- **Dynamic Sprites:** Automatically maps internal item IDs to Stardew Valley Wiki icons with standard emoji fallbacks.
- **Lightweight & Fast:** Runs on a minimal Python + Nginx container stack.

---

## 🚀 Quickstart (Docker Compose)

The easiest way to run the Stardew Valley Save Analyzer is with `docker-compose`.

```yaml
version: "3.8"

services:
  stardew-analyzer:
    image: ghcr.io/tbg-scrat/stardew-analyser:latest
    container_name: stardew-analyzer
    restart: unless-stopped
    ports:
      - "9999:80"
    volumes:
      - /path/to/your/StardewValley/Saves:/saves:ro
```

Replace `/path/to/your/StardewValley/Saves` with the absolute path to your Stardew Valley save folder on your host machine.

### Default Save File Locations

- **Linux:** `~/.config/StardewValley/Saves`
- **Windows:** `%APPDATA%\StardewValley\Saves`
- **macOS:** `~/.config/StardewValley/Saves`

## 🛠️ Building Locally

```bash
# Clone the repository
git clone https://github.com/tbg-scrat/stardew-analyser.git
cd stardew-analyser

# Build and run with Docker Compose
docker compose up --build -d
```

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
