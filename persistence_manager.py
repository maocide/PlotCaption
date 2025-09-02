import json
from pathlib import Path
import appdirs
from vlm_profiles import VLM_PROFILES

# Define the application name for the settings folder
APP_NAME = "PlotCaption"
APP_AUTHOR = "User"  # Can be generic

# Find the user's config directory in a cross-platform way
config_dir = Path(appdirs.user_config_dir(APP_NAME, APP_AUTHOR))
config_dir.mkdir(parents=True, exist_ok=True)


class PersistenceManager:
    """
    Manages loading and saving of application settings to a single JSON file.
    """

    def __init__(self, settings_file="app_settings.json"):
        """
        Initializes the PersistenceManager.

        Args:
            settings_file (str): The name of the settings file.
        """
        self.settings_file_path = config_dir / settings_file
        self.defaults = {
            "api_key": "",
            "base_url": "",
            "model_name": "",
            "last_card_template": "NSFW",
            "last_sd_template": "NSFW",
            "temperature": 0.7,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            # Get the first available VLM profile as the default
            "last_used_vlm": next(iter(VLM_PROFILES), None)
        }

    def load_settings(self) -> dict:
        """
        Loads settings from the JSON file.

        If the file doesn't exist, is empty, or is corrupted, it returns
        a dictionary with default values. It also ensures that all keys
        from the defaults are present in the loaded settings.

        Returns:
            dict: A dictionary containing the application settings.
        """
        if not self.settings_file_path.exists():
            return self.defaults.copy()

        try:
            with open(self.settings_file_path, 'r') as f:
                # Handle empty file case
                content = f.read()
                if not content:
                    return self.defaults.copy()
                loaded_settings = json.loads(content)
        except (json.JSONDecodeError, IOError):
            return self.defaults.copy()

        # Ensure all default keys are present in the loaded settings
        final_settings = self.defaults.copy()
        final_settings.update(loaded_settings)

        return final_settings

    def save_settings(self, settings_data: dict):
        """
        Saves the provided settings dictionary to the JSON file.

        Args:
            settings_data (dict): The dictionary of settings to save.

        Returns:
            bool: True if saving was successful, False otherwise.
        """
        try:
            with open(self.settings_file_path, 'w') as f:
                json.dump(settings_data, f, indent=4)
            print(f"Settings successfully saved to {self.settings_file_path}")
            return True
        except IOError as e:
            print(f"Error saving settings: {e}")
            return False
