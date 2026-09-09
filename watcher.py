"""
watcher.py - Stardew Valley Save File Watcher

Monitors the saves directory for file creation and modification events using watchdog.
Implements a 2-second debounce timer to prevent duplicate parsing while save files are actively writing.
Parses the newest save file immediately on startup and regenerates the HTML dashboard.
"""

import logging
import os
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from parser import find_all_saves, find_newest_save, load_object_mappings, parse_all_saves, parse_save
from renderer import render_dashboard

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("stardew-watcher")

# Configuration via environment variables (with fallbacks to Ubuntu bind mounts, container mounts, and local dev)
DEFAULT_SAVES = (
    "/srv/docker/data/sv-analyzer/saves"
    if Path("/srv/docker/data/sv-analyzer/saves").exists()
    else ("/saves" if Path("/saves").exists() else "./Saves")
)
SAVES_DIR = Path(os.getenv("SAVES_DIR", DEFAULT_SAVES)).resolve()

DEFAULT_OUTPUT = (
    "/srv/docker/data/sv-analyzer/web/index.html"
    if Path("/srv/docker/data/sv-analyzer/web").exists()
    else ("/app/web/index.html" if Path("/app/web").exists() else "./web/index.html")
)
OUTPUT_FILE = Path(os.getenv("OUTPUT_FILE", os.getenv("OUTPUT_PATH", DEFAULT_OUTPUT))).resolve()
DEFAULT_TEMPLATES = (
    "/srv/docker/data/sv-analyzer/templates"
    if Path("/srv/docker/data/sv-analyzer/templates").exists()
    else ("/app/templates" if Path("/app/templates").exists() else "./templates")
)
TEMPLATES_DIR = Path(os.getenv("TEMPLATES_DIR", DEFAULT_TEMPLATES)).resolve()
DEBOUNCE_SECONDS = float(os.getenv("DEBOUNCE_SECONDS", "0.5" if os.getenv("DEV_MODE") else "2.0"))


class SaveFileHandler(FileSystemEventHandler):
    """
    Watchdog event handler with a debounce timer.
    """

    def __init__(self, watcher: "SaveWatcher"):
        super().__init__()
        self.watcher = watcher

    def on_any_event(self, event: FileSystemEvent):
        # Ignore directory events directly, wait for files inside
        if event.is_directory:
            return

        src = Path(event.src_path)
        name = src.name.lower()

        # Ignore known temporary or backup files
        ignored_patterns = ("_old", "_svbak", "_svemerg", "emergency_save", ".tmp")
        if any(name.endswith(pat) or name == pat for pat in ignored_patterns):
            return
        if name.startswith("."):
            return

        logger.debug(f"Detected event [{event.event_type}] on {event.src_path}")
        self.watcher.trigger_debounce()


class SaveWatcher:
    """
    Coordinates file observation, debouncing, and dashboard regeneration.
    """

    def __init__(
        self,
        saves_dir: Path = SAVES_DIR,
        output_file: Path = OUTPUT_FILE,
        templates_dir: Path = TEMPLATES_DIR,
        debounce_seconds: float = DEBOUNCE_SECONDS,
    ):
        self.saves_dir = saves_dir
        self.output_file = output_file
        self.templates_dir = templates_dir
        self.debounce_seconds = debounce_seconds

        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
        self._running = False
        self._mappings = None

    def trigger_debounce(self):
        """
        Resets the debounce timer. Processing will only occur after
        the directory has been quiet for `debounce_seconds`.
        """
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self.debounce_seconds, self._on_debounce_expired)
            self._timer.daemon = True
            self._timer.start()
            logger.info(f"Save change detected. Debouncing for {self.debounce_seconds}s...")

    def _on_debounce_expired(self):
        with self._lock:
            self._timer = None
        self.process_latest_save()

    def process_saves(self) -> bool:
        """
        Discovers all save files, parses them, and regenerates the multi-farm dashboard.
        """
        logger.info(f"Scanning for saves in: {self.saves_dir}")
        try:
            if self._mappings is None:
                logger.info("Initializing object mappings...")
                self._mappings = load_object_mappings()

            farms = parse_all_saves(self.saves_dir, mappings=self._mappings)
            if not farms:
                logger.warning(f"No valid saves found in {self.saves_dir}")
                return False

            render_dashboard(
                player_data=farms,
                output_file=self.output_file,
                templates_dir=self.templates_dir,
            )
            latest = farms[0]
            logger.info(
                f"Dashboard updated for {len(farms)} farm(s). Active/Latest: '{latest['farm_name']} Farm' "
                f"({latest['completed_count']}/{latest['total_crops']} Polyculture crops completed)"
            )
            return True
        except Exception as e:
            logger.error(f"Error updating saves: {e}", exc_info=True)
            return False

    process_latest_save = process_saves  # Backwards-compatible alias

    def start(self):
        """
        Starts immediate initial parse and the watchdog observer.
        """
        self._running = True
        logger.info("=" * 60)
        logger.info("Starting Stardew Valley Save File Watcher")
        logger.info(f"  Saves Directory : {self.saves_dir}")
        logger.info(f"  Output File     : {self.output_file}")
        logger.info(f"  Templates Dir   : {self.templates_dir}")
        logger.info(f"  Debounce Window : {self.debounce_seconds}s")
        logger.info("=" * 60)

        # 1. Ensure saves directory exists
        self.saves_dir.mkdir(parents=True, exist_ok=True)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # 2. Initial processing of newest save on startup
        logger.info("Running initial save check on startup...")
        self.process_latest_save()

        # 3. Setup watchdog observer
        event_handler = SaveFileHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.saves_dir), recursive=True)
        observer.start()
        logger.info(f"Watchdog observer active on: {self.saves_dir}")

        try:
            while self._running:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutdown signal received.")
        finally:
            observer.stop()
            observer.join()
            with self._lock:
                if self._timer is not None:
                    self._timer.cancel()
            logger.info("Watcher stopped cleanly.")

    def stop(self):
        self._running = False


def handle_signals(signum, frame):
    logger.info(f"Received signal {signum}. Stopping...")
    if watcher_instance:
        watcher_instance.stop()


watcher_instance: Optional[SaveWatcher] = None

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_signals)
    signal.signal(signal.SIGTERM, handle_signals)

    watcher_instance = SaveWatcher()
    watcher_instance.start()
