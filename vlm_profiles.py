# vlm_profiles.py

from dataclasses import dataclass
from typing import Callable, Dict
import json

# This defines the structure for a model's "forensic file"
@dataclass
class VLMProfile:
    model_id: str
    prompt_caption: str
    prompt_tags: str
    # This stores a function that will parse the model's output!
    output_parser: Callable[[str], Dict[str, str]]

# --- Define Parser Functions ---
# Each model might have a different output format, so they get their own parser.

def parse_toriigate_json(raw_output: str) -> Dict[str, str]:
    """Parses the specific JSON output from ToriiGate."""
    try:
        data = json.loads(raw_output)
        # Assumes the JSON has a field called "suggested_booru_tags"
        tags = data.get("suggested_booru_tags", "Error: Tags not found in JSON.")
        # You would also extract the main description/caption here
        caption = data.get("description", "Error: Description not found in JSON.")
        return {"caption": caption, "tags": tags}
    except json.JSONDecodeError:
        return {"caption": raw_output, "tags": "Error: Failed to parse JSON output."}

def parse_simple_model_text(raw_output: str) -> Dict[str, str]:
    """Parses a simple model that just outputs a caption and nothing else."""
    return {"caption": raw_output, "tags": "N/A"}


# --- Create the Profile Database ---
# This is your central list of all supported models.
VLM_PROFILES = {
    "ToriiGate-v0.4-7B": VLMProfile(
        model_id="Minthy/ToriiGate-v0.4-7B",
        prompt_caption="Please provide a long, detailed description of the following image.",
        prompt_tags='Describe the picture in structured json-like format. Include a field called "suggested_booru_tags" and a "description".',
        output_parser=parse_toriigate_json
    ),
    "A-Different-VLM-3B": VLMProfile(
        model_id="somebody/a-different-vlm-3b",
        prompt_caption="Image:", # This model might use a simpler prompt!
        prompt_tags="Tags:",    # It might not even support tags!
        output_parser=parse_simple_model_text
    )
    # Add new models here!
}