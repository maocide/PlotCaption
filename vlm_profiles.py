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
        return {"output": raw_output}
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
    return {"output": raw_output}


# --- Create the Profile Database ---
# This is your central list of all supported models.
VLM_PROFILES = {
    "ToriiGate-v0.4-7B": VLMProfile(
        model_id="Minthy/ToriiGate-v0.4-7B",
        prompt_caption="""Please provide a long, detailed description of the following image.
The character(s) in the image is/are: <char></char>.
Here are grounding tags for better understanding: <tags></tags>.""",
        prompt_tags='Describe the picture in structured json-like format. Include a field called "suggested_booru_tags" and a "description".',
        output_parser=parse_toriigate_json
    ),
    "llama-joycaption-alpha-two-hf-llava": VLMProfile(
        model_id="fancyfeast/llama-joycaption-alpha-two-hf-llava",
        prompt_caption="Write a long detailed description for this image.", #
        prompt_tags="Generate only comma-separated Danbooru tags (lowercase_underscores). Strict order: artist:, copyright:, character:, meta:, then general tags. Include counts (1girl), appearance, clothing, accessories, pose, expression, actions, background. Use precise Danbooru syntax. No extra text.",
        output_parser=parse_simple_model_text
    )
    # Add new models here!
}