# watch.py

import logging
import os
import sys
import time
from pathlib import Path

from src.core.logger import setup_logging

setup_logging("watcher")
logger = logging.getLogger(__name__)

SAVE_DIR = Path(os.getenv("SAVE_DIR", "/saves"))


def main():
    logger.info(f"Monitoring {SAVE_DIR.resolve()} for save changes...")
    logger.info("Running initial parse...")

    # Execute main parse loop
    from parse import run_pipeline

    run_pipeline()

    last_mtime = 0
    while True:
        try:
            current_mtime = max(
                [f.stat().st_mtime for f in SAVE_DIR.glob("**/*") if f.is_file()],
                default=0,
            )
            if current_mtime > last_mtime and last_mtime != 0:
                logger.info("Save directory modified. Triggering re-parse...")
                run_pipeline()
                last_mtime = current_mtime
            elif last_mtime == 0:
                last_mtime = current_mtime

            time.sleep(2)
        except KeyboardInterrupt:
            logger.info("Watcher stopped by user.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error in watcher loop: {e}", exc_info=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
    