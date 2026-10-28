"""
Privacy-First Telemetry Module

This script sends a minimal, anonymous 'ping' to help count how many active 
installations exist and which versions are being used in the wild. 

PRIVACY GUARANTEES FOR USERS:
1. Strictly Opt-In: This script does absolutely nothing unless you explicitly 
   add TELEMETRY_ENABLED=true to your Docker environment variables.
2. Fully Anonymous: It only generates a random string of characters (a UUID) 
   to count unique installations, and checks the app version.
3. Persistent Storage Required: Telemetry will automatically turn itself off if 
   the /cache folder is not mapped to a Docker volume or host folder. This prevents 
   creating duplicate 'fake' installation counts every time your container updates.
4. No Personal Data Ever: It does NOT read your savegames, farm names, player names, 
   user data, local files, hostnames, or IP addresses.
"""

import json
import logging
import os
import urllib.request
import uuid

from src.core.logger import is_module_debug_enabled

# Initialize the standard logger for this specific module
logger = logging.getLogger(__name__)

# If the user specifically allowed debug logging for 'telemetry' via the 
# DEBUG_MODULES environment variable, force this logger to capture DEBUG events.
if is_module_debug_enabled("telemetry"):
    logger.setLevel(logging.DEBUG)

# The Cloudflare edge worker domain that receives the anonymous ping
TELEMETRY_URL = "https://sv-telemetry.ms58.org"


def is_cache_mounted(cache_path: str = "/cache") -> bool:
    """
    Checks whether the /cache directory is attached to a real, persistent storage volume.
    
    Why this matters:
    Without a mounted volume, Docker deletes everything inside /cache every time 
    the container is updated or recreated. That would cause a brand-new random ID 
    to be generated on every single update, artificially inflating installation counts.
    """
    os.makedirs(cache_path, exist_ok=True)
    return os.path.ismount(cache_path)


def ping():
    logger.info("Initializing anonymous telemetry sequence.")

    # 1. OPT-IN CHECK
    # If the user did not explicitly set TELEMETRY_ENABLED=true in Docker, stop immediately.
    # No files are read or written, and no network connections are made.
    if os.getenv("TELEMETRY_ENABLED", "false").lower() != "true":
        logger.info("Telemetry is disabled via TELEMETRY_ENABLED environment variable. Halting.")
        return
        
    logger.debug("Telemetry is enabled. Checking storage persistence...")

    # 2. PERSISTENCE CHECK (PREVENT DUPLICATE PHANTOM IDs)
    # Check if /cache is mounted as a persistent Docker volume or host bind mount.
    # If it is not mounted, stop here to avoid generating disposable IDs on every container restart.
    cache_dir = "/cache"
    if not is_cache_mounted(cache_dir):
        logger.warning(
            f"Directory '{cache_dir}' is not mounted as a persistent volume or bind mount. "
            "Telemetry ping skipped to prevent generating duplicate installation IDs on container recreation."
        )
        return

    logger.debug("Persistent volume verified. Proceeding with ID generation/retrieval.")

    # 3. ANONYMOUS ID GENERATION & RETRIEVAL
    # We need a way to recognize '1 installation' over time without knowing who you are.
    # We generate a completely random string of numbers/letters (UUID) and save it to /cache/telemetry/instance_id.
    id_dir = os.path.join(cache_dir, "telemetry")
    id_file = os.path.join(id_dir, "instance_id")
    
    try:
        os.makedirs(id_dir, exist_ok=True)
        
        # If an ID already exists from a previous run, read and reuse it
        if os.path.exists(id_file):
            logger.debug(f"Found existing ID file at {id_file}.")
            with open(id_file, "r") as f:
                instance_id = f.read().strip()
            logger.debug(f"Retrieved existing anonymous ID: {instance_id}")
            
        # If this is the first run, generate a new random ID and save it to the persistent volume
        else:
            logger.debug("No existing ID found. Generating a new random UUID.")
            instance_id = str(uuid.uuid4())
            with open(id_file, "w") as f:
                f.write(instance_id)
            logger.debug("Successfully saved new random UUID to persistent cache.")
            
    except Exception as e:
        # If storing the ID fails due to folder permission issues, log a warning and stop
        logger.warning(f"Could not access cache directory for ID storage. Skipping ping. Error: {e}")
        return

    # 4. DATA PAYLOAD (THIS IS THE ONLY DATA SENT)
    # We construct a simple dictionary containing ONLY the random installation ID 
    # and the application version (e.g., v2.0.1). No other information is collected.
    app_version = os.getenv("APP_VERSION", "unknown")
    payload = {
        "id": instance_id,
        "version": app_version
    }
    
    logger.debug(f"Constructed anonymous payload: {payload}")

    # 5. SEND THE PING (FIRE AND FORGET)
    # We send the payload to our edge server. We set a short 3-second timeout so that 
    # if internet access is down or blocked, it fails silently and will NEVER freeze or crash the app.
    logger.info("Sending anonymous installation ping to edge server...")
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            TELEMETRY_URL, 
            data=data, 
            headers={
                "Content-Type": "application/json",
                "User-Agent": "stardew-analyser/1.0"  # Identifies the app to bypass Cloudflare automated bot blocking
            }, 
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            logger.debug(f"Ping successful. Edge server responded with HTTP {response.status}")
            logger.info("Anonymous telemetry ping completed successfully.")
            
    except urllib.error.HTTPError as e:
        logger.debug(f"Ping failed with HTTP Error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        logger.debug(f"Ping failed due to network error: {e.reason}")
    except Exception as e:
        logger.debug(f"Ping encountered an unexpected error: {e}")

if __name__ == "__main__":
    # If run standalone for testing, configure basic logging to output results directly
    from src.core.logger import setup_logging
    setup_logging("telemetry_standalone")
    ping()
    