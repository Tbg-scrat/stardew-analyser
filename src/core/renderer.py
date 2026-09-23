# src/core/renderer.py

import time
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

OUTPUT_HTML = Path("index.html")


def generate_dashboard_html(all_saves_data, output_path=OUTPUT_HTML):
    """
    Renders Jinja2 HTML dashboard from parsed save data dictionaries.
    """
    env = Environment(loader=FileSystemLoader("templates", encoding="utf-8"))
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

    print(
        f"[OK] Generated static dashboard for {len(all_saves_data)} save game(s)"
        f" -> {Path(output_path).resolve()}"
    )
    