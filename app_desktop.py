import os
import sys
import tempfile
import traceback
from pathlib import Path
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


def create_error_html(output_path: str, message: str, detail: str = ""):
    """Write a fallback HTML page so pywebview always has a valid file to render."""
    error_content = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: sans-serif; background: #2c2c2c; color: #fff; padding: 40px; text-align: center; }}
        .card {{ background: #3a3a3a; padding: 20px; border-radius: 8px; max-width: 600px; margin: 0 auto; }}
        h1 {{ color: #e74c3c; }}
        pre {{ text-align: left; background: #1e1e1e; padding: 15px; border-radius: 4px; overflow-x: auto; color: #ff8b8b; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Stardew Save Analyzer</h1>
        <p><strong>{message}</strong></p>
        {f'<pre>{detail}</pre>' if detail else ''}
    </div>
</body>
</html>"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(error_content)


def build_app() -> str:
    """Parse saves and generate temporary HTML output, returning a valid file:// URI."""
    base_dir = get_base_dir()

    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    save_dir = get_default_save_dir()
    output_html = os.path.join(tempfile.gettempdir(), "stardew_analyzer_index.html")

    try:
        from parse import analyze_save
        analyze_save(save_dir=save_dir, output_path=output_html)
        
        # Verify the file was actually written by parse
        if not os.path.exists(output_html):
            create_error_html(
                output_html, 
                "No save file analyzed", 
                f"No valid Stardew Valley save files were found in:\n{save_dir}"
            )
    except Exception as e:
        err_msg = traceback.format_exc()
        create_error_html(output_html, f"An error occurred during save parsing: {e}", err_msg)

    return Path(output_html).as_uri()


def main():
    file_url = build_app()

    webview.create_window(
        title="Stardew Valley Save Analyzer",
        url=file_url,
        width=1280,
        height=800,
        resizable=True,
        min_size=(800, 600),
    )

    webview.start(private_mode=False)


if __name__ == "__main__":
    main()
