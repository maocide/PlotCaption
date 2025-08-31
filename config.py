# --- Configuration ---
# Use a quantized model for lower VRAM usage, or the full model for better quality.
# Quantized model: "John6666/llama-joycaption-beta-one-hf-llava-nf4"
# Full model: "fancyfeast/llama-joycaption-alpha-two-hf-llava"

DEFAULT_MODELS = ["Minthy/ToriiGate-v0.4-7B", "fancyfeast/llama-joycaption-alpha-two-hf-llava"]
DEFAULT_PROMPT = """Please provide a long, detailed description of the following image.
The character(s) in the image is/are: <char></char>.
Here are grounding tags for better understanding: <tags></tags>."""
TAGS_PROMPT = """Describe the picture in structured json-like format. Include a field called "suggested_booru_tags" containing a string of relevant tags separated by commas."""
MAX_THUMBNAIL_SIZE = (400, 400)
MODEL_HISTORY_FILE = "model_history.json"

COPY_IMAGE_FILE = "assets/copy_image.png"
COPY_IMAGE_HOVER_FILE = "assets/copy_image_hover.png"

DARK_COLOR = "#2E2E2E"
INACTIVE_TAB_COLOR = "#303030"
FIELD_BORDER_AREA_COLOR = "#4A4A4A"
FIELD_BACK_COLOR = "#3C3C3C"
FIELD_FOREGROUND_COLOR = "white"
INSERT_COLOR = "black"
SELECT_BACKGROUND_COLOR = "#007ACC"
BUTTON_COLOR = "#007ACC"
BUTTON_ACTIVATE_COLOR = "#008ADC"
BUTTON_PRESSED_COLOR = "#3A3A3A"
TEXT_BG_COLOR = "#3C3C3C"
INSERT_BACKGROUND_COLOR = "white"
PLACEHOLDER_FG_COLOR = "gray"

# --- Prompt Generation ---
CARD_USER_ROLE = "develop around Main Character personality (Main Character interest/Lover/Rival/NTR partecipant...)"
CARD_CHAR_TO_ANALYZE = "Main Character"
SD_CHAR_TO_ANALYZE = "Character from character card, Main Character"