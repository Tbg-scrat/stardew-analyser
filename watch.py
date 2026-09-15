import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SaveHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # Ignore directory modifications or hidden temporary files
        if not event.is_directory and not event.src_path.split("/")[-1].startswith("."):
            print(f"[WATCHER] Change detected in {event.src_path}. Rebuilding dashboard...")
            subprocess.run(["python", "parse.py"])

if __name__ == "__main__":
    path = "/saves"  # Must match your container's volume mount
    print(f"[WATCHER] Starting observer on {path}...")
    
    # Run once on startup
    subprocess.run(["python", "parse.py"])
    
    observer = Observer()
    observer.schedule(SaveHandler(), path=path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    