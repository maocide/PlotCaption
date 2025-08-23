# --- Configuration ---
# Use a quantized model for lower VRAM usage, or the full model for better quality.
# Quantized model: "John6666/llama-joycaption-beta-one-hf-llava-nf4"
# Full model: "fancyfeast/llama-joycaption-alpha-two-hf-llava"

DEFAULT_MODELS = ["minthy/ToriiGate-v0.4-7B", "fancyfeast/llama-joycaption-alpha-two-hf-llava"]
DEFAULT_PROMPT = "Write a detailed description of this image."
MAX_THUMBNAIL_SIZE = (400, 400)
MODEL_HISTORY_FILE = "model_history.json"

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