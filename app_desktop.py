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
    try:
        appdata = os.getenv("APPDATA")
        if appdata:
            stardew_path = os.path.join(appdata, "StardewValley", "Saves")
            if os.path.exists(stardew_path):
                return stardew_path
    except Exception:
        pass

    base_dir = get_base_dir()
    local_saves = os.path.join(base_dir, "saves")
    os.makedirs(local_saves, exist_ok=True)
    return local_saves


def find_latest_save_file(saves_dir: str) -> str:
    """Find the most recently modified valid Stardew Valley save file within the saves directory."""
    if not os.path.exists(saves_dir):
        return ""

    if os.path.isfile(saves_dir):
        return saves_dir

    candidate_files = []

    # Iterate over subdirectories inside the Saves folder
    try:
        for entry in os.scandir(saves_dir):
            if entry.is_dir():
                folder_name = entry.name
                # The main Stardew Valley save file has the same name as its parent folder
                save_file_path = os.path.join(entry.path, folder_name)

                if os.path.isfile(save_file_path) and os.path.getsize(save_file_path) > 0:
                    candidate_files.append((save_file_path, os.path.getmtime(save_file_path)))
    except Exception as e:
        print(f"[WARN] Error scanning save directories: {e}")

    # Fallback to general search if no exact match folder/filename match was found
    if not candidate_files:
        for root, _, files in os.walk(saves_dir):
            for file in files:
                if (
                    file.endswith("_SaveGameInfo")
                    or file.endswith(".old")
                    or file.endswith(".bak")
                    or file.endswith(".tmp")
                    or file.startswith(".")
                    or file.endswith(".vdf")
                ):
                    continue

                full_path = os.path.join(root, file)
                if os.path.isfile(full_path) and os.path.getsize(full_path) > 0:
                    candidate_files.append((full_path, os.path.getmtime(full_path)))

    if not candidate_files:
        return ""

    # Sort by last modified timestamp descending to pick the latest save
    candidate_files.sort(key=lambda x: x[1], reverse=True)
    return candidate_files[0][0]


def create_error_html(output_path: str, message: str, detail: str = ""):
    """Write a fallback HTML page so pywebview always has a valid file to render."""
    error_content = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: sans-serif; background: #2c2c2c; color: #fff; padding: 40px; text-align: center; }}
        .card {{ background: #3a3a3a; padding: 20px; border-radius: 8px; max-width: 700px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
        h1 {{ color: #e74c3c; }}
        pre {{ text-align: left; background: #1e1e1e; padding: 15px; border-radius: 4px; overflow-x: auto; color: #ff8b8b; font-size: 13px; }}
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

    saves_root = get_default_save_dir()
    save_file = find_latest_save_file(saves_root)

    temp_dir = tempfile.gettempdir()
    output_html = os.path.join(temp_dir, "stardew_analyzer_index.html")

    if not save_file:
        create_error_html(
            output_html,
            "No Save File Found",
            f"Could not locate a valid Stardew Valley save file inside:\n{saves_root}\n\nPlease ensure you have at least one saved game."
        )
        return Path(output_html).as_uri()

    try:
        from parse import analyze_save
        result = analyze_save(save_file)

        if isinstance(result, str) and os.path.exists(result):
            output_html = result
        elif isinstance(result, str) and result.strip().startswith("<"):
            with open(output_html, "w", encoding="utf-8") as f:
                f.write(result)

        if not os.path.exists(output_html):
            default_index = os.path.join(os.getcwd(), "stardew_analyzer_index.html")
            if os.path.exists(default_index):
                output_html = default_index

        if not os.path.exists(output_html):
            create_error_html(
                output_html,
                "No save file analyzed",
                f"No valid Stardew Valley XML save files were found in:\n{saves_root}"
            )
    except Exception as e:
        err_msg = traceback.format_exc()
        create_error_html(output_html, f"An error occurred during save parsing: {e}", err_msg)

    return Path(output_html).as_uri()


def main():
    try:
        file_url = build_app()
    except Exception as e:
        output_html = os.path.join(tempfile.gettempdir(), "stardew_analyzer_index.html")
        create_error_html(output_html, "Startup Error", traceback.format_exc())
        file_url = Path(output_html).as_uri()

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
