# model_handler.py (Final, Simplified Version)

import torch


# No more specific transformers imports needed here!

class ModelHandler:
    def __init__(self):
        self.model = None
        self.processor = None

    def pick_device(self, loaded_profile):
        if torch.cuda.is_available():
            # Get total VRAM in bytes and convert to Gigabytes
            total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)

            # Set a threshold for what we consider a "high VRAM" GPU
            vram_threshold_gb = loaded_profile.required_vram_gb  # We can adjust this value if needed

            if total_vram_gb > vram_threshold_gb:
                # If the user has plenty of VRAM, force the model to the GPU for max speed.
                self.device = "cuda"
                print(f"Sufficient VRAM ({total_vram_gb:.2f}GB) detected. Using 'cuda' for maximum performance.")
            else:
                # If VRAM is limited, use "auto" to prevent crashes and allow offloading.
                self.device = "auto"
                print(f"Limited VRAM ({total_vram_gb:.2f}GB) detected. Using 'auto' to enable model offloading.")
        else:
            # If there's no GPU, we fall back to CPU.
            self.device = "cpu"
            print("No CUDA device found. Using CPU.")

    def load_model(self, loaded_profile):
        """
        Loads a VLM model and processor using the function from the profile.
        """

        if not loaded_profile:
            raise ValueError("A valid VLMProfile must be provided.")

        # Picks the correct device based on profile GB require VRAM
        self.pick_device(loaded_profile)

        # Call the specific loader function from the profile
        # Add a print statement for better logging
        print(f"Loading {loaded_profile.model_id} onto device: {self.device}")

        self.model, self.processor = loaded_profile.loader_function(
            loaded_profile.model_id,
            self.device  # Pass the device string here
        )

    def unload_model(self):
        """
        Unloads the model and processor, and clears GPU memory if applicable.
        """
        self.model = None
        self.processor = None
        self.is_toriigate_model = False
        if self.device == "cuda":
            torch.cuda.empty_cache()

    def generate_description(self, loaded_profile, prompt, image_raw):
        """
        Generates text by calling the specific function from the loaded profile.
        """
        # ... (error checking) ...

        # The ModelHandler calls the function from the profile and
        # passes its own tools as arguments.
        return loaded_profile.generation_function(
            self.model,  # Tool #1 from the Handler's toolkit
            self.processor,  # Tool #2 from the Handler's toolkit
            self.device,  # Tool #3 from the Handler's toolkit
            prompt,
            loaded_profile.system_prompt,
            image_raw
        )