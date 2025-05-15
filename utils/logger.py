import os
import json
import datetime

LOG_DIR  = os.path.join(os.path.expanduser("~"), ".nac", "logs")
LOG_FILE = os.path.join(LOG_DIR, "nac_events.log")

def _ensure_log():
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.isfile(LOG_FILE):
        open(LOG_FILE, "w").close()

def log_event(event_type: str, details: str):
    _ensure_log()
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "event": event_type,
        "details": details
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
