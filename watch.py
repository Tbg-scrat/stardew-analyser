# watch.py
import os
import subprocess
import time
from pathlib import Path
from threading import Timer
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

SAVE_DIR = Path(os.getenv("SAVE_DIR", "/saves"))


class SaveHandler(FileSystemEventHandler):

    def __init__(self, debounce_seconds=2.0):
        self.debounce_seconds = debounce_seconds
        self.timer = None

    def schedule_rebuild(self, event_type, path):
        # Reset timer on every event to wait for file operations to complete
        if self.timer is not None:
            self.timer.cancel()

        self.timer = Timer(self.debounce_seconds, self._run_rebuild, [event_type, path])
        self.timer.start()

    def _run_rebuild(self, event_type, path):
        print(f"[WATCHER] Settled save change detected ({event_type}: {path}). Rebuilding index.html...")
        subprocess.run(["python3", "parse.py"], check=False)

    def on_deleted(self, event):
        filename = Path(event.src_path).name
        if not filename.startswith("."):
            self.schedule_rebuild("deleted", event.src_path)

    def on_created(self, event):
        filename = Path(event.src_path).name
        if not event.is_directory and not filename.startswith("."):
            self.schedule_rebuild("created", event.src_path)

    def on_modified(self, event):
        filename = Path(event.src_path).name
        if not event.is_directory and not filename.startswith("."):
            self.schedule_rebuild("modified", event.src_path)


if __name__ == "__main__":
    print("[WATCHER] Running initial parse...")
    subprocess.run(["python3", "parse.py"], check=False)

    print(f"[WATCHER] Monitoring {SAVE_DIR.resolve()} for save changes...")
    observer = Observer()
    observer.schedule(SaveHandler(debounce_seconds=2.0), path=str(SAVE_DIR), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    