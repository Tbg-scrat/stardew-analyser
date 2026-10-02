# src/core/renderer.py

import logging
import sys
import time
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

OUTPUT_HTML = Path("index.html")


def get_resource_path(relative_path: str) -> Path:
    """Resolve resource path for both development and PyInstaller bundled environments."""
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        # Repo root is 2 levels up from src/core/renderer.py
        base_path = Path(__file__).resolve().parent.parent.parent
    return base_path / relative_path


def generate_dashboard_html(all_saves_data, output_path=OUTPUT_HTML):
    """
    Renders Jinja2 HTML dashboard from parsed save data dictionaries.
    """
    templates_dir = get_resource_path("templates")
    logger.debug(f"Loading Jinja templates from: {templates_dir}")

    env = Environment(loader=FileSystemLoader(templates_dir, encoding="utf-8"))
    template = env.get_template("index.html")

    farms_context = []
    for save_id, data in all_saves_data.items():
        data["farm_id"] = save_id
        data["farmer_name"] = data.get("farmer", "Farmer")
        data["farm_name"] = data.get("farm", "Farm")
        farms_context.append(data)

    build_time = int(time.time())

    rendered_html = template.render(
        farms=farms_context, build_timestamp=build_time
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    logger.info(
        f"Generated static dashboard for {len(all_saves_data)} save game(s)"
        f" -> {Path(output_path).resolve()}"
    )
    return output_path
    