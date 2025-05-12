import json
import os

# Configuration directory & file
CONFIG_DIR  = os.path.join(os.path.expanduser("~"), ".nac")
CONFIG_FILE = os.path.join(CONFIG_DIR, "profiles.json")

def _ensure_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"default": {}, "profiles": {}}, f, indent=2)

def load_all() -> dict:
    """Load the entire configuration."""
    _ensure_config()
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_all(cfg: dict):
    """Save the entire configuration."""
    _ensure_config()
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def get_profile(name: str) -> dict:
    """
    Return the settings for a given profile.
    Falls back to the 'default' profile if name not found.
    """
    cfg = load_all()
    return cfg["profiles"].get(name, cfg["default"])

def list_profiles() -> list:
    """Return a list of saved profile names."""
    cfg = load_all()
    return list(cfg["profiles"].keys())

def add_or_update_profile(name: str, settings: dict):
    """Create or update a profile with the given settings."""
    cfg = load_all()
    cfg["profiles"][name] = settings
    save_all(cfg)

def set_default_profile(name: str):
    """Set which profile to load by default at startup."""
    cfg = load_all()
    if name in cfg["profiles"]:
        cfg["default"] = cfg["profiles"][name]
        save_all(cfg)
    else:
        raise KeyError(f"No profile named '{name}'")
