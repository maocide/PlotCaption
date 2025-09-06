# download_model_script.py
# utility file to download models locally from huggingface, not in code, extra.
from huggingface_hub import snapshot_download
import os

# Define the model and the local directory
model_id = "Minthy/ToriiGate-v0.4-7B"
local_dir = os.path.join("models", model_id)

# Create the directory if it doesn't exist
os.makedirs(local_dir, exist_ok=True)

print(f"Downloading model {model_id} to {local_dir}...")

# Download the model files
snapshot_download(
    repo_id=model_id,
    local_dir=local_dir,
    local_dir_use_symlinks=False # Important for PyInstaller
)

print("Download complete!")