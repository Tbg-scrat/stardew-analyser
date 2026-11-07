# src/core/renderer.py

import logging
import sys
import time
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

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
    with tracer.start_as_current_span("generate_dashboard_html") as span:
        saves_count = len(all_saves_data)
        span.set_attribute("dashboard.saves_count", saves_count)

        # 1. Template Setup Span
        with tracer.start_as_current_span("render.init_template") as template_span:
            templates_dir = get_resource_path("templates")
            logger.debug(f"Loading Jinja templates from: {templates_dir}")
            template_span.set_attribute("dashboard.templates_dir", str(templates_dir))

            env = Environment(loader=FileSystemLoader(templates_dir, encoding="utf-8"))
            template = env.get_template("index.html")

        # 2. Context Assembly Span
        with tracer.start_as_current_span("render.build_context") as context_span:
            farms_context = []
            for save_id, data in all_saves_data.items():
                data["farm_id"] = save_id
                data["farmer_name"] = data.get("farmer", "Farmer")
                data["farm_name"] = data.get("farm", "Farm")
                farms_context.append(data)

            build_time = int(time.time())
            context_span.set_attribute("dashboard.context_items", len(farms_context))

        # 3. Jinja Rendering Engine Span
        with tracer.start_as_current_span("render.jinja_template") as render_span:
            rendered_html = template.render(farms=farms_context, build_timestamp=build_time)
            render_span.set_attribute("dashboard.html_size_bytes", len(rendered_html.encode("utf-8")))

        # 4. File I/O Span
        with tracer.start_as_current_span("render.write_file") as io_span:
            resolved_output = Path(output_path).resolve()
            io_span.set_attribute("dashboard.output_path", str(resolved_output))
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered_html)

        logger.info(
            f"Generated static dashboard for {saves_count} save game(s)"
            f" -> {resolved_output}"
        )

        span.set_attribute("dashboard.output_path", str(resolved_output))
        return output_path
        