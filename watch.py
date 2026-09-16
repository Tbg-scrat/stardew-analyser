import os
import subprocess
import time
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

SAVE_DIR = Path(os.getenv("SAVE_DIR", "/saves"))


class SaveHandler(FileSystemEventHandler):

  def __init__(self):
    self.last_trigger = 0

  def trigger_rebuild(self, event_type, path):
    now = time.time()
    # Debounce: max 1 parse every 1.5 seconds
    if now - self.last_trigger > 1.5:
      self.last_trigger = now
      print(
          f"[WATCHER] Save change detected ({event_type}: {path}). Rebuilding"
          " index.html..."
      )
      subprocess.run(["python3", "parse.py"], check=False)

  def on_deleted(self, event):
    # Always trigger on folder or file deletion unless it's hidden (starts with .)
    filename = Path(event.src_path).name
    if not filename.startswith("."):
      self.trigger_rebuild("deleted", event.src_path)

  def on_created(self, event):
    filename = Path(event.src_path).name
    if not event.is_directory and not filename.startswith("."):
      self.trigger_rebuild("created", event.src_path)

  def on_modified(self, event):
    filename = Path(event.src_path).name
    if not event.is_directory and not filename.startswith("."):
      self.trigger_rebuild("modified", event.src_path)


if __name__ == "__main__":
  print("[WATCHER] Running initial parse...")
  subprocess.run(["python3", "parse.py"], check=False)

  print(f"[WATCHER] Monitoring {SAVE_DIR.resolve()} for save changes...")
  observer = Observer()
  observer.schedule(SaveHandler(), path=str(SAVE_DIR), recursive=True)
  observer.start()

  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    observer.stop()
  observer.join()
  