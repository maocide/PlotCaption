# prompts.py (Refactored Version)
import os
import sys


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def _load_prompt_template(filename: str) -> str:
    """
    Loads a prompt template from a file in the 'prompts' directory.
    """
    template_path = resource_path(os.path.join("prompts", filename))

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: Prompt template file not found at {template_path}")
        return "" # Return empty string or raise an error
    except Exception as e:
        print(f"ERROR: Could not read prompt template file {filename}: {e}")
        return ""


def discover_prompt_templates() -> dict:
    """
    Scans the 'prompts' directory for prompt templates and returns their names.
    """
    prompts_dir = resource_path("prompts")

    card_prompts = []
    sd_prompts = []

    try:
        for filename in os.listdir(prompts_dir):
            if filename.endswith("_character_card.txt"):
                prefix = filename.replace("_character_card.txt", "")
                card_prompts.append(prefix)
            elif filename.endswith("_stable_diffusion.txt"):
                prefix = filename.replace("_stable_diffusion.txt", "")
                sd_prompts.append(prefix)
    except FileNotFoundError:
        print(f"ERROR: Prompts directory not found at {prompts_dir}")

    return {"card_prompts": sorted(card_prompts), "sd_prompts": sorted(sd_prompts)}

def generate_character_card_prompt(
        template_name: str,
        character_to_analyze: str,
        user_role: str,
        user_placeholder: str,
        caption: str,
        tags: str
) -> str:
    """
    Generates a prompt for creating a character card by loading a template
    and replacing placeholders.
    """
    filename = f"{template_name}_character_card.txt"
    template = _load_prompt_template(filename)

    prompt = template.replace("[[[character_to_analyze]]]", character_to_analyze)
    prompt = prompt.replace("[[[user_role]]]", user_role)
    prompt = prompt.replace("[[[user_placeholder]]]", user_placeholder)
    prompt = prompt.replace("[[[caption]]]", caption)
    prompt = prompt.replace("[[[tags]]]", tags)

    return prompt


def generate_stable_diffusion_prompt(
        template_name: str,
        character_to_analyze: str,
        caption: str,
        tags: str,
        character_card: str
) -> str:
    """
    Generates a Stable Diffusion prompt by loading a template and
    replacing placeholders.
    """
    filename = f"{template_name}_stable_diffusion.txt"
    template = _load_prompt_template(filename)

    prompt = template.replace("[[[character_to_analyze]]]", character_to_analyze)
    prompt = prompt.replace("[[[caption]]]", caption)
    prompt = prompt.replace("[[[tags]]]", tags)
    prompt = prompt.replace("[[[character_card]]]", character_card)

    return prompt