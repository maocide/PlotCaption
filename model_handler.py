import torch
from transformers import AutoProcessor, LlavaForConditionalGeneration, AutoModelForVision2Seq
from qwen_vl_utils import process_vision_info

class ModelHandler:
    """
    Handles loading, unloading, and running Vision Language Models (VLMs).
    """
    def __init__(self):
        """
        Initializes the ModelHandler.
        """
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_toriigate_model = False

    def load_model(self, model_name):
        """
        Loads a VLM model and processor from Hugging Face.

        This method determines which specific loading function to call based on
        the model name.

        Args:
            model_name (str): The name of the model to load.

        Raises:
            Exception: If the model loading fails.
        """
        if model_name == "Minthy/ToriiGate-v0.4-7B":
            self._load_toriigate_model(model_name)
        else:
            self._load_llava_model(model_name)

    def _load_llava_model(self, model_name):
        """
        Loads a LLaVA-based VLM model and processor.

        Args:
            model_name (str): The name of the model to load from Hugging Face.
        """
        self.processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
        self.model = LlavaForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
        self.model.eval()
        self.is_toriigate_model = False

    def _load_toriigate_model(self, model_name):
        """
        Loads the Minthy/ToriiGate-v0.4-7B model and processor.

        Args:
            model_name (str): The name of the model to load.
        """
        from transformers import AutoConfig

        config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
        config.num_attention_heads = 28

        self.processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModelForVision2Seq.from_pretrained(
            model_name,
            config=config,
            trust_remote_code=True,
            device_map="auto",
            torch_dtype=torch.bfloat16
        )
        self.model.eval()
        self.is_toriigate_model = True

    def unload_model(self):
        """
        Unloads the model and processor, and clears GPU memory if applicable.
        """
        self.model = None
        self.processor = None
        self.is_toriigate_model = False
        if self.device == "cuda":
            torch.cuda.empty_cache()

    def generate_description(self, prompt, image_raw):
        """
        Generates a text description for an image using the loaded model.

        This method determines which specific generation function to call
        based on the model type.

        Args:
            prompt (str): The text prompt to use for generation.
            image_raw (PIL.Image.Image): The raw image to describe.

        Returns:
            str: The generated text description.

        Raises:
            Exception: If text generation fails.
        """
        if not image_raw or not self.model or not self.processor:
            raise ValueError("Model, processor, and image must be loaded before generation.")

        if self.is_toriigate_model:
            return self._generate_toriigate_description(prompt, image_raw)
        else:
            return self._generate_llava_description(prompt, image_raw)

    def _generate_llava_description(self, prompt, image_raw):
        """
        Generates a text description for a LLaVA model.
        """
        with torch.no_grad():
            convo = [
                {"role": "system", "content": "You are an expert at analyzing images."},
                {"role": "user", "content": f"<image>\n{prompt}"}
            ]
            convo_string = self.processor.apply_chat_template(convo, tokenize=False, add_generation_prompt=True)

            inputs = self.processor(
                text=[convo_string],
                images=[image_raw],
                return_tensors="pt"
            ).to(self.device)

            inputs['pixel_values'] = inputs['pixel_values'].to(torch.bfloat16)

            output = self.model.generate(**inputs, max_new_tokens=512, do_sample=False)
            decoded_output = self.processor.batch_decode(output, skip_special_tokens=True)[0]
            assistant_response = decoded_output.split("assistant\n")[-1].strip()
            return assistant_response

    def _generate_toriigate_description(self, prompt, image_raw):
        """
        Generates a text description for the Minthy/ToriiGate-v0.4-7B model.
        """
        with torch.no_grad():
            messages = [
                {"role": "system", "content": "You are an expert at analyzing images."},
                {"role": "user", "content": [
                    {"type": "image", "image": image_raw},
                    {"type": "text", "text": prompt}
                ]}
            ]

            text_input = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, _ = process_vision_info(messages)

            model_inputs = self.processor(
                text=[text_input],
                images=image_inputs,
                videos=None,
                padding=True,
                return_tensors="pt"
            ).to(self.device)

            generated_ids = self.model.generate(**model_inputs, max_new_tokens=512, do_sample=False)
            trimmed_generated_ids = [out_ids[len(in_ids):] for in_ids, out_ids in zip(model_inputs.input_ids, generated_ids)]
            assistant_response = self.processor.batch_decode(
                trimmed_generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0]
            return assistant_response
