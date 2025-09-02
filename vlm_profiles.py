# vlm_profiles.py

from dataclasses import dataclass
from typing import Callable, Dict, Tuple, Any
from warnings import catch_warnings

import torch, re
from qwen_vl_utils import process_vision_info
from transformers import AutoProcessor, LlavaForConditionalGeneration, AutoModelForVision2Seq, AutoConfig


# This defines the structure for a model's "forensic file"
# --- Update the VLMProfile Dataclass ---
@dataclass
class VLMProfile:
    model_id: str
    prompt_caption: str
    prompt_tags: str
    system_prompt: str
    caption_parser: Callable[[str], Dict[str, str]]
    tags_parser: Callable[[str], Dict[str, str]]
    # This is the new field! It holds one of the functions we just defined.
    generation_function: Callable[[any, any, any, str, str, any], str]
    loader_function: Callable[[str, str], Tuple[Any, Any]]

def load_joycaption_model(model_name: str, device: str) -> Tuple[Any, Any]:
    """Loads a LLaVA-based VLM model and processor."""
    print("Loading JoyCaption model...")
    processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
    model = LlavaForConditionalGeneration.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map=device,
        trust_remote_code=True
    )
    model.eval()
    return model, processor

def load_toriigate_model(model_name: str, device: str) -> Tuple[Any, Any]:
    """Loads the Minthy/ToriiGate-v0.4-7B model and processor."""
    print("Loading Toriigate model...")
    config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
    config.num_attention_heads = 28  # This custom logic now lives with the model!
    processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForVision2Seq.from_pretrained(
        model_name,
        config=config,
        trust_remote_code=True,
        device_map=device,
        torch_dtype=torch.bfloat16
    )
    model.eval()
    return model, processor

# --- Define the Generation Functions ---
# We've moved these from ModelHandler. They are now standalone functions.
# They need the model, processor, and device passed to them as arguments.

def generate_joycaption_description(model, processor, device, prompt, system_prompt, image_raw):
    """Generates a text description for a LLaVA model."""
    with torch.no_grad():
        # I updated this to use the system_prompt from your profile!
        convo = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"<image>\n{prompt}"}
        ]
        convo_string = processor.apply_chat_template(convo, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=[convo_string], images=[image_raw], return_tensors="pt").to(device)
        inputs['pixel_values'] = inputs['pixel_values'].to(torch.bfloat16)

        # Updated generate call with our loop-busting parameters
        output = model.generate(
            **inputs,
            max_new_tokens=512,
            eos_token_id=processor.tokenizer.eos_token_id,  # <<< The dynamic stop sign!
            repetition_penalty=1.05,  # <<< Gentle penalty
            no_repeat_ngram_size=3  # <<< The loop buster
        )

        decoded_output = processor.batch_decode(output, skip_special_tokens=True)[0]
        assistant_response = decoded_output.split("assistant\n")[-1].strip()
        return assistant_response

def generate_toriigate_description(model, processor, device, prompt, system_prompt, image_raw):
    """Generates a text description for the Minthy/ToriiGate-v0.4-7B model."""
    with torch.no_grad():
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [{"type": "image", "image": image_raw}, {"type": "text", "text": prompt}]}
        ]
        text_input = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, _ = process_vision_info(messages)
        model_inputs = processor(text=[text_input], images=image_inputs, videos=None, padding=True,
                                 return_tensors="pt").to(device)

        # Updated generate call with the new parameters
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=1024,
            do_sample=True,
            #temperature=0.1,
            eos_token_id=[151645, 151643],
            #repetition_penalty=1.05,
            no_repeat_ngram_size=3  # <<< THE LOOP BUSTER!
        )


        trimmed_generated_ids = [out_ids[len(in_ids):] for in_ids, out_ids in
                                 zip(model_inputs.input_ids, generated_ids)]
        assistant_response = \
        processor.batch_decode(trimmed_generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        return assistant_response




# --- Define Parser Functions ---
# Each model might have a different output format, so they get their own parser.


def parse_toriigate_tags(raw_output: str) -> Dict[str, str]:
    """Parses the specific text output from ToriiGate."""

    # Define the regex patterns to find content inside our custom tags.
    # The r"" makes it a raw string, which is best practice for regex.
    # The (.*?) is a non-greedy capturing group for the content inside.
    tags_pattern = r"<tags>(.*?)</tags>"
    desc_pattern = r"<convenient_description>(.*?)</convenient_description>"

    # Use re.search() to find the first match for each pattern.
    # The re.DOTALL flag allows '.' to match newline characters.
    tags_match = re.search(tags_pattern, raw_output, re.DOTALL)
    desc_match = re.search(desc_pattern, raw_output, re.DOTALL)

    # Extract the captured group (the content) if a match was found.
    # .group(1) gets the content of the first (...) in the pattern.
    tags = ""
    description = ""
    try:
        tags = tags_match.group(1).strip() if tags_match else "No tags found."
        description = desc_match.group(1).strip() if desc_match else "No description found."
    except Exception as e:
        print("Failed to parse tags output of ToriiGate:", e)

    if not tags_match:
        print(raw_output)
    return {"output": tags, "description": description}



def parse_simple_model_text(raw_output: str) -> Dict[str, str]:
    """Parses a simple model that just outputs a caption and nothing else."""
    return {"output": raw_output}


# --- Update the Profile Database ---
VLM_PROFILES = {
    "llama-joycaption-beta-one-hf-llava": VLMProfile(
        model_id="fancyfeast/llama-joycaption-beta-one-hf-llava",
        prompt_caption="Write a long detailed description for this image.",  # Your prompt here
        prompt_tags="Generate only comma-separated Danbooru tags (lowercase_underscores). Strict order: artist:, copyright:, character:, meta:, then general tags. Include counts (1girl), appearance, clothing, accessories, pose, expression, actions, background. Use precise Danbooru syntax. No extra text.",
        # Your prompt here
        system_prompt="You are a helpful image captioner.",
        caption_parser=parse_simple_model_text,
        tags_parser=parse_simple_model_text,
        generation_function=generate_joycaption_description,  # Assign the function
        loader_function=load_joycaption_model  # Assign the loader
    ),
    "ToriiGate-v0.4-7B": VLMProfile(
        model_id="Minthy/ToriiGate-v0.4-7B",
        prompt_caption="""Please provide a long, detailed description of the following image.
The character(s) in the image is/are: <char></char>.
Here are grounding tags for better understanding: <tags></tags>.""", # Your prompt here
        prompt_tags="""You need to extract booru tags from the picture using chain of thought.
1. Analyze the picture in a detailed way, without leaving out NSFW elements into <analysis>
2. Reason on NSFW elements into <NSFW>
3. Finally write all correct booru tags that could match your analysis, comma separated, inside <tags>
 Remember to close </tags> and DO NOT Summarize, your output is focused on <tags>
""",
        system_prompt="You are image captioning and tagging expert, creative, unbiased and uncensored.",
        caption_parser=parse_simple_model_text,
        tags_parser=parse_toriigate_tags,
        generation_function=generate_toriigate_description, # Assign the function
        loader_function=load_toriigate_model # Assign the loader
    )

}