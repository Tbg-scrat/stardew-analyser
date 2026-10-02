import logging
import os
import sys
import tempfile
import traceback
from pathlib import Path
import webview

# Configure persistent file logging for desktop executable diagnostics
log_dir = os.path.join(os.getenv("APPDATA", "."), "StardewSaveAnalyzer")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "desktop.log")

logging.basicConfig(
    filename=log_file,
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("desktop")


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
            logger.info(f"Detected default Windows save directory: {stardew_path}")
            return stardew_path

    base_dir = get_base_dir()
    local_saves = os.path.join(base_dir, "saves")
    os.makedirs(local_saves, exist_ok=True)
    logger.warning(f"Default save dir not found, falling back to local: {local_saves}")
    return local_saves


def build_app() -> str:
    """Parse saves and generate temporary HTML output for PyWebView."""
    base_dir = get_base_dir()

    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    save_dir = get_default_save_dir()
    output_html = os.path.join(tempfile.gettempdir(), "stardew_analyzer_index.html")

    logger.info(f"Starting desktop build. Save Dir: {save_dir} | Output HTML: {output_html}")

    try:
        from parse import run_pipeline
        result = run_pipeline(save_dir=save_dir, output_path=output_html)
        logger.info(f"run_pipeline execution completed. Result: {result}")
    except Exception as e:
        logger.error(f"Error during run_pipeline execution: {e}")
        logger.error(traceback.format_exc())

    if not os.path.exists(output_html):
        logger.error(f"HTML output file was not generated at {output_html}")

    return Path(output_html).as_uri()


def main():
    logger.info("Initializing Stardew Valley Save Analyzer Desktop Window...")
    file_uri = build_app()
    logger.info(f"Loading webview URL: {file_uri}")

    webview.create_window(
        title="Stardew Valley Save Analyzer",
        url=file_uri,
        width=1280,
        height=800,
        resizable=True,
        min_size=(800, 600),
    )

    webview.start(private_mode=False)


if __name__ == "__main__":
    main()
    