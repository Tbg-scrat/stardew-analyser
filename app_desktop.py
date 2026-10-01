import os
import sys
import tempfile
import webview


def get_base_dir() -> str:
    """Return base directory path, handling PyInstaller's sys._MEIPASS bundle directory."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_default_save_dir() -> str:
    """Detect the default Stardew Valley save directory on Windows."""
    appdata = os.getenv("APPDATA")
    if appdata:
        stardew_path = os.path.join(appdata, "StardewValley", "Saves")
        if os.path.exists(stardew_path):
            return stardew_path

    base_dir = get_base_dir()
    local_saves = os.path.join(base_dir, "saves")
    os.makedirs(local_saves, exist_ok=True)
    return local_saves


def build_app():
    """Parse saves and generate temporary HTML output for PyWebView."""
    base_dir = get_base_dir()

    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    save_dir = get_default_save_dir()
    output_html = os.path.join(tempfile.gettempdir(), "stardew_analyzer_index.html")

    try:
        from parse import run_pipeline
        run_pipeline(save_dir=save_dir, output_path=output_html)
    except Exception:
        from src.core.renderer import generate_dashboard_html
        from src.core.xml_reader import load_and_parse_save

        save_data = load_and_parse_save(save_dir)
        render_dashboard(save_data, output_path=output_html)

    return output_html


def main():
    html_path = build_app()

    webview.create_window(
        title="Stardew Valley Save Analyzer",
        url=html_path,
        width=1280,
        height=800,
        resizable=True,
        min_size=(800, 600),
    )

    webview.start(private_mode=False)


if __name__ == "__main__":
    main()
