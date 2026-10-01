import os
import sys
import tempfile
import traceback
import time
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


def debug_find_save_file(saves_dir: str) -> tuple[str, list[str]]:
    """Scan directory and return selected save path alongside detailed scan logs."""
    logs = [f"Scanning root directory: {saves_dir}"]

    if not os.path.exists(saves_dir):
        logs.append("ERROR: Saves directory does not exist on disk!")
        return "", logs

    if os.path.isfile(saves_dir):
        logs.append(f"Target is a single file: {saves_dir}")
        return saves_dir, logs

    candidate_files = []

    try:
        entries = list(os.scandir(saves_dir))
        logs.append(f"Found {len(entries)} item(s) inside root folder:")

        for entry in entries:
            logs.append(f"  - [{ 'DIR' if entry.is_dir() else 'FILE' }] {entry.name}")

            if entry.is_dir():
                folder_path = entry.path
                expected_save = os.path.join(folder_path, entry.name)
                if os.path.isfile(expected_save):
                    mtime = os.path.getmtime(expected_save)
                    size = os.path.getsize(expected_save)
                    candidate_files.append((expected_save, mtime))
                    logs.append(f"    -> MATCHED SAVE FILE: {entry.name} ({size} bytes, mtime: {mtime})")
                else:
                    logs.append(f"    -> Expected save file missing: {expected_save}")
                    try:
                        sub_files = os.listdir(folder_path)
                        logs.append(f"       Subfolder contents: {sub_files}")
                    except Exception as sub_err:
                        logs.append(f"       Failed to read subfolder: {sub_err}")

    except Exception as e:
        logs.append(f"ERROR during folder scan: {e}\n{traceback.format_exc()}")

    if not candidate_files:
        logs.append("No matches found via folder name convention. Running fallback recursive walk...")
        for root, _, files in os.walk(saves_dir):
            for file in files:
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
                        logs.append(f"  -> Fallback matched file: {full_path}")
                except Exception:
                    continue

    if not candidate_files:
        logs.append("ERROR: Zero candidate files found after full scan.")
        return "", logs

    candidate_files.sort(key=lambda x: x[1], reverse=True)
    selected = candidate_files[0][0]
    logs.append(f"\nSELECTED LATEST SAVE: {selected}")
    return selected, logs


def create_error_html(output_path: str, title: str, message: str, logs: list[str] = None):
    """Render a detailed diagnostic HTML screen."""
    log_block = ""
    if logs:
        log_text = "\n".join(logs)
        log_block = f'<h3>Diagnostic Output Log:</h3><pre>{log_text}</pre>'

    error_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #111; color: #fff; padding: 30px; margin: 0; }}
        .card {{ background: #222; padding: 25px; border-radius: 8px; max-width: 950px; margin: 0 auto; border: 1px solid #333; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }}
        h1 {{ color: #e74c3c; margin-top: 0; font-size: 24px; }}
        h3 {{ color: #3498db; margin-bottom: 5px; }}
        p {{ line-height: 1.5; color: #ccc; }}
        pre {{ text-align: left; background: #000; padding: 15px; border-radius: 6px; overflow-x: auto; color: #00ff66; font-family: "Consolas", "Courier New", monospace; font-size: 13px; line-height: 1.4; white-space: pre-wrap; word-wrap: break-word; border: 1px solid #333; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>{title}</h1>
        <p><strong>{message}</strong></p>
        {log_block}
    </div>
</body>
</html>"""

    # Remove existing file to prevent stale cache reading
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception:
            pass

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(error_content)
        f.flush()


def build_app() -> str:
    """Parse saves and generate temporary HTML output, returning a valid file:// URI."""
    base_dir = get_base_dir()

    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    saves_root = get_default_save_dir()
    save_file, scan_logs = debug_find_save_file(saves_root)

    # Use a unique timestamped debug file path to bypass browser caching
    temp_dir = tempfile.gettempdir()
    output_html = os.path.join(temp_dir, f"stardew_diag_{int(time.time())}.html")

    if not save_file:
        create_error_html(
            output_html,
            "No Save File Identified",
            f"Directory inspected: {saves_root}",
            scan_logs,
        )
        return Path(output_html).as_uri()

    try:
        from parse import analyze_save

        scan_logs.append(f"Calling analyze_save('{save_file}')...")
        result = analyze_save(save_file)

        if isinstance(result, str) and os.path.exists(result):
            output_html = result
        elif isinstance(result, str) and result.strip().startswith("<"):
            with open(output_html, "w", encoding="utf-8") as f:
                f.write(result)

        if not os.path.exists(output_html):
            scan_logs.append("ERROR: parse.py ran but output HTML was not written to disk.")
            create_error_html(
                output_html,
                "Analysis Failed to Render Output",
                f"Target File: {save_file}",
                scan_logs,
            )
    except Exception as e:
        scan_logs.append(f"\nEXCEPTION DURING PARSING:\n{traceback.format_exc()}")
        create_error_html(
            output_html,
            f"Parsing Error: {e}",
            f"Target File: {save_file}",
            scan_logs,
        )

    return Path(output_html).as_uri()


def main():
    try:
        file_url = build_app()
    except Exception as e:
        output_html = os.path.join(tempfile.gettempdir(), f"stardew_diag_{int(time.time())}.html")
        create_error_html(output_html, "Startup Exception", str(e), [traceback.format_exc()])
        file_url = Path(output_html).as_uri()

    webview.create_window(
        title="Stardew Valley Save Analyzer - Diagnostics",
        url=file_url,
        width=1280,
        height=800,
        resizable=True,
        min_size=(800, 600),
    )

    webview.start(private_mode=False)


if __name__ == "__main__":
    main()
