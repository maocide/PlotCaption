import json
import os
from config import MODEL_HISTORY_FILE, DEFAULT_MODEL

class HistoryManager:
    """
    Manages the model history, loading from and saving to a JSON file.
    """
    def __init__(self):
        """
        Initializes the HistoryManager and loads the model history.
        """
        self.history_file = MODEL_HISTORY_FILE
        self.model_history = self._load_model_history()

    def _load_model_history(self):
        """
        Loads the model history from the JSON file.

        If the file doesn't exist or is corrupted, it returns a list
        containing the default model.

        Returns:
            list: A list of previously used model names.
        """
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return [DEFAULT_MODEL]  # Return default if file is corrupted
        else:
            return [DEFAULT_MODEL]

    def _save_model_history(self):
        """Saves the current model history list to the JSON file."""
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.model_history, f, indent=4)
        except IOError as e:
            print(f"Error saving model history: {e}")  # Log to console

    def add_model_to_history(self, model_name):
        """
        Adds a new model name to the history if it's not already present.

        Args:
            model_name (str): The name of the model to add.
        """
        if model_name not in self.model_history:
            self.model_history.append(model_name)

    def get_history(self):
        """
        Returns the list of model names in the history.

        Returns:
            list: The model history.
        """
        return self.model_history

    def save_on_exit(self):
        """
        Saves the model history to the file.
        """
        self._save_model_history()
