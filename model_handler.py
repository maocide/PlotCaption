import torch


class ModelHandler:
    def __init__(self):
        self.model = None
        self.processor = None

        # This is the device we will ALWAYS use for TENSOR computations.
        self.compute_device = "cuda" if torch.cuda.is_available() else "cpu"

        # This will be the STRATEGY for loading the model. It might be 'auto' or 'cuda'.
        self.device_map_config = self.compute_device

    def pick_device_map_strategy(self, loaded_profile):
        """Determines the best loading strategy based on available VRAM."""
        if self.compute_device == "cuda":
            total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            vram_threshold_gb = loaded_profile.required_vram_gb

            if total_vram_gb <= vram_threshold_gb:
                self.device_map_config = "auto"
                print(f"Limited VRAM ({total_vram_gb:.2f}GB) detected. Using 'auto' device map for loading.")
            else:
                self.device_map_config = "cuda"
                print(f"Sufficient VRAM ({total_vram_gb:.2f}GB) detected. Using 'cuda' for loading.")
        else:
            self.device_map_config = "cpu"
            print("No CUDA device found. Using CPU.")

    def load_model(self, loaded_profile):
        if not loaded_profile:
            raise ValueError("A valid VLMProfile must be provided.")

        # First, determine the best loading strategy for this specific profile
        self.pick_device_map_strategy(loaded_profile)

        print(f"Loading {loaded_profile.model_id} with strategy: '{self.device_map_config}'")
        self.model, self.processor = loaded_profile.loader_function(
            loaded_profile.model_id,
            self.device_map_config  # Pass the loading STRATEGY here
        )

    def unload_model(self):
        self.model = None
        self.processor = None
        if self.compute_device == "cuda":
            torch.cuda.empty_cache()

    def generate_description(self, loaded_profile, prompt, image_raw):
        # Always pass the actual COMPUTE device here ("cuda" or "cpu"), never "auto".
        return loaded_profile.generation_function(
            self.model,
            self.processor,
            self.compute_device,
            prompt,
            loaded_profile.system_prompt,
            image_raw
        )