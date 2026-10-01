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
    """Find the most recently modified main Stardew Valley save file within the saves directory."""
    if not os.path.exists(saves_dir):
        return ""

    if os.path.isfile(saves_dir):
        return saves_dir

    candidate_files = []

    for root, _, files in os.walk(saves_dir):
        for file in files:
            # Stardew Valley save files usually match their parent folder name and have no extension.
            # Skip known non-save files, backups, and metadata.
            if (
                file.endswith("_SaveGameInfo")
                or file.endswith(".old")
                or file.endswith(".bak")
                or file.endswith(".tmp")
                or file.endswith(".vdf")
                or file.endswith(".png")
                or file.startswith(".")
            ):
                continue

            full_path = os.path.join(root, file)
            try:
                if os.path.isfile(full_path) and os.path.getsize(full_path) > 0:
                    candidate_files.append((full_path, os.path.getmtime(full_path)))
            except Exception:
                continue

    if not candidate_files:
        return ""

    # Sort by last modified timestamp descending
    candidate_files.sort(key=lambda x: x[1], reverse=True)
    return candidate_files[0][0]


def create_error_html(output_path: str, message: str, detail: str = ""):
    """Write a fallback HTML page so pywebview always has a valid file to render."""
    error_content = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: sans-serif; background: #2c2c2c; color: #fff; padding: 40px; text-align: center; }}
        .card {{ background: #3a3a3a; padding: 25px; border-radius: 8px; max-width: 700px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
        h1 {{ color: #e74c3c; margin-top: 0; }}
        p {{ line-height: 1.5; color: #ddd; }}
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
            "Kein Spielstand gefunden",
            f"Es konnte keine gültige Stardew Valley Speicherdatei in folgendem Ordner gefunden werden:\n{saves_root}\n\nBitte stelle sicher, dass mindestens ein Spielstand existiert."
        )
        return Path(output_html).as_uri()

    try:
        from parse import analyze_save
        
        # Versuche zuerst die konkrete Speicherdatei zu übergeben
        try:
            result = analyze_save(save_file)
        except Exception:
            # Fallback: Falls parse.py den Ordner statt der Datei erwartet
            result = analyze_save(saves_root)

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
                "Analyse fehlgeschlagen",
                f"Die Analyse für die Datei '{save_file}' konnte keine HTML-Ausgabe erzeugen."
            )
    except Exception as e:
        err_msg = traceback.format_exc()
        create_error_html(output_html, f"Fehler beim Parsen des Spielstands: {e}", err_msg)

    return Path(output_html).as_uri()


def main():
    try:
        file_url = build_app()
    except Exception as e:
        output_html = os.path.join(tempfile.gettempdir(), "stardew_analyzer_index.html")
        create_error_html(output_html, "Startfehler", traceback.format_exc())
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
