# settings_manager.py
import json
from pathlib import Path
import appdirs

# Define the application name for the settings folder
APP_NAME = "PlotCaption"
APP_AUTHOR = "User" # Can be generic

# Find the user's config directory in a cross-platform way
config_dir = Path(appdirs.user_config_dir(APP_NAME, APP_AUTHOR))
config_dir.mkdir(parents=True, exist_ok=True)
config_file = config_dir / "api_settings.json"

def save_settings(**settings):
    """Saves settings to the user's config file."""
    try:
        # To be safe, load existing settings first and update them
        existing_settings = load_settings()
        existing_settings.update(settings)

        with open(config_file, 'w') as f:
            json.dump(existing_settings, f, indent=4)
        print(f"Settings saved to {config_file}")
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

def load_settings() -> dict:
    """Loads API settings from the user's config file."""
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {} # Return empty dict if file is corrupt
    return {} # Return empty dict if file doesn't exist
