# --- Configuration ---
# Use a quantized model for lower VRAM usage, or the full model for better quality.
# Quantized model: "John6666/llama-joycaption-beta-one-hf-llava-nf4"
# Full model: "fancyfeast/llama-joycaption-alpha-two-hf-llava"
DEFAULT_MODEL = "fancyfeast/llama-joycaption-alpha-two-hf-llava"
DEFAULT_PROMPT = "Write a detailed description of this image."
MAX_THUMBNAIL_SIZE = (400, 400)
MODEL_HISTORY_FILE = "model_history.json"
