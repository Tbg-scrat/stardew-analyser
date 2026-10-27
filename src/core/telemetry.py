"""
Privacy-First Telemetry Module

This script sends a minimal, anonymous 'ping' to help count how many active 
installations exist and which versions are being used. 

PRIVACY GUARANTEE:
1. Strictly Opt-In: This script does absolutely nothing unless you explicitly 
   add TELEMETRY_ENABLED=true to your Docker environment variables.
2. Fully Anonymous: It only generates a random string of characters (an ID) 
   to count the installation, and checks the app version.
3. No Personal Data: It does NOT read your savegames, user data, local files, 
   hostnames, or IP addresses.
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

# The Cloudflare edge worker that receives the anonymous ping
TELEMETRY_URL = "https://round-darkness-4f79.tbg-scrat.workers.dev/"

def ping():
    logger.info("Initializing anonymous telemetry sequence.")

    # 1. OPT-IN CHECK
    # If the user did not explicitly set TELEMETRY_ENABLED=true, stop immediately.
    # No data is gathered and nothing is sent.
    if os.getenv("TELEMETRY_ENABLED", "false").lower() != "true":
        logger.info("Telemetry is disabled via TELEMETRY_ENABLED environment variable. Halting.")
        return
        
    logger.debug("Telemetry is enabled. Proceeding with ID generation/retrieval.")

    # 2. ANONYMOUS ID GENERATION
    # We need a way to count "1 installation" without knowing who you are.
    # We generate a completely random string (UUID) and save it to the cache folder.
    cache_dir = "/cache/telemetry"
    id_file = os.path.join(cache_dir, "instance_id")
    
    try:
        logger.debug(f"Checking cache directory: {cache_dir}")
        os.makedirs(cache_dir, exist_ok=True)
        
        # If an ID already exists from a previous run, read it
        if os.path.exists(id_file):
            logger.debug(f"Found existing ID file at {id_file}.")
            with open(id_file, "r") as f:
                instance_id = f.read().strip()
            logger.debug(f"Retrieved existing anonymous ID: {instance_id}")
            
        # If this is the first run, generate a new random ID and save it
        else:
            logger.debug("No existing ID found. Generating a new random UUID.")
            instance_id = str(uuid.uuid4())
            with open(id_file, "w") as f:
                f.write(instance_id)
            logger.debug("Successfully saved new random UUID to cache.")
            
    except Exception as e:
        # Fallback in case the folder has permission issues (still random and anonymous)
        instance_id = str(uuid.uuid4())
        logger.warning(f"Could not access cache volume, using temporary random UUID. Error: {e}")

    # 3. THE DATA PAYLOAD (THIS IS THE ONLY DATA SENT)
    # We construct a simple dictionary containing only the random ID and the app version.
    # We explicitly do not include any other information.
    app_version = os.getenv("APP_VERSION", "unknown")
    payload = {
        "id": instance_id,
        "version": app_version
    }
    
    logger.debug(f"Constructed anonymous payload: {payload}")

    # 4. SEND THE PING (FIRE AND FORGET)
    logger.info("Sending anonymous installation ping to edge server...")
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            TELEMETRY_URL, 
            data=data, 
            headers={
                "Content-Type": "application/json",
                "User-Agent": "stardew-analyser/1.0"  # Bypasses Cloudflare's default Python block
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
    # If run standalone, configure basic logging to see output
    from src.core.logger import setup_logging
    setup_logging("telemetry_standalone")
    ping()
    