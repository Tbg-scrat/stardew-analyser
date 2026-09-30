import os
import sys
import webview
from src.core.renderer import render_dashboard
from src.core.xml_reader import load_and_parse_save

APP_NAME = "Stardew Valley Save Analyzer"
DEFAULT_WINDOW_SIZE = (1280, 800)


def get_default_save_dir() -> str:
    """Detect the default Stardew Valley save directory on Windows."""
    appdata = os.getenv("APPDATA")
    if appdata:
        stardew_path = os.path.join(appdata, "StardewValley", "Saves")
        if os.path.exists(stardew_path):
            return stardew_path

    # Fallback to local saves directory if APPDATA isn't found
    local_saves = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")
    os.makedirs(local_saves, exist_ok=True)
    return local_saves


def build_app():
    """Parse saves and generate the temporary HTML output for PyWebView."""
    save_dir = get_default_save_dir()
    
    # Path to bundle assets when running frozen under PyInstaller
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    output_html = os.path.join(base_dir, "index.html")

    try:
        from parse import run_pipeline
        run_pipeline(save_dir=save_dir, output_path=output_html)
    except ImportError:
        save_data = load_and_parse_save(save_dir)
        render_dashboard(save_data, output_path=output_html)

    return output_html


def main():
    html_path = build_app()

    window = webview.create_window(
        title=APP_NAME,
        url=html_path,
        width=DEFAULT_WINDOW_SIZE[0],
        height=DEFAULT_WINDOW_SIZE[1],
        resizable=True,
        min_size=(800, 600),
    )

    webview.start(private_mode=False)


if __name__ == "__main__":
    main()
