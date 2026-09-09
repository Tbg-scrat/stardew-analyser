"""
renderer.py - Dashboard renderer using Jinja2

Loads the HTML dashboard template and renders it with parsed save game data.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger("stardew-renderer")

DEFAULT_TEMPLATES = (
    "/srv/docker/data/sv-analyzer/templates"
    if Path("/srv/docker/data/sv-analyzer/templates").exists()
    else ("/app/templates" if Path("/app/templates").exists() else Path(__file__).resolve().parent / "templates")
)
DEFAULT_TEMPLATES_DIR = Path(os.getenv("TEMPLATES_DIR", DEFAULT_TEMPLATES)).resolve()
DEFAULT_OUTPUT_FILE = Path(
    os.getenv(
        "OUTPUT_FILE",
        "/srv/docker/data/sv-analyzer/web/index.html"
        if Path("/srv/docker/data/sv-analyzer/web").exists()
        else ("/app/web/index.html" if Path("/app/web").exists() else Path(__file__).resolve().parent / "web" / "index.html"),
    )
).resolve()


def render_dashboard(
    player_data: Dict[str, Any] | List[Dict[str, Any]],
    output_file: Optional[Path] = None,
    templates_dir: Optional[Path] = None,
) -> Path:
    """
    Renders player_data (single farm or list of farms) into an HTML dashboard using Jinja2.
    """
    tmpl_dir = templates_dir or DEFAULT_TEMPLATES_DIR
    out_path = output_file or DEFAULT_OUTPUT_FILE

    out_path.parent.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(tmpl_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    farms = player_data if isinstance(player_data, list) else [player_data]
    template = env.get_template("index.html")
    rendered_html = template.render(
        farms=farms,
        player=farms[0] if farms else {},
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    logger.info(f"Successfully generated dashboard for {len(farms)} farm(s) at: {out_path}")
    return out_path


if __name__ == "__main__":
    import sys
    from parser import find_all_saves, parse_all_saves, parse_save

    default_saves = os.getenv(
        "SAVES_DIR",
        "/srv/docker/data/sv-analyzer/saves"
        if Path("/srv/docker/data/sv-analyzer/saves").exists()
        else ("/saves" if Path("/saves").exists() else "./Saves"),
    )
    saves_dir = sys.argv[1] if len(sys.argv) > 1 else default_saves
    target = Path(saves_dir)
    if target.is_dir():
        farms = parse_all_saves(target)
        if not farms:
            print(f"No valid save file found in {target}")
            sys.exit(1)
        out = render_dashboard(farms)
    else:
        farm = parse_save(target)
        out = render_dashboard(farm)

    print(f"Generated dashboard: {out}")
