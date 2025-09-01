# 🎨 PlotCaption 📝
### *Turn a single picture into a character's entire life story... and then make more pictures of them.*

Ever look at an image and think, "I could write a novel about them"? Or maybe, "I wish I could get my Stable Diffusion prompts to actually listen to me"? What if you could do both, at the same time, with one click?

PlotCaption is your local, private, and slightly unhinged AI sidekick that does just that. Feed it an image, and it spits out two things:
1.  **Rich, detailed character lore** for all you storytellers and roleplayers out there.
2.  **Exquisitely detailed Stable Diffusion prompts** for the AI artists who are tired of wrestling with tags.

It's an entire creative workflow in a box, and the best part? It runs on your own machine. No prying eyes, no content filters, no API fees. Just pure, uncensored creative freedom.

## 🤔 Who is this for?

We built PlotCaption for a few special kinds of people. See if you fit the bill:

*   **The Privacy-Conscious Tinkerer:** You hang out on r/LocalLLM, you've got Oobabooga or LM Studio running, and you believe your data is your data. You want powerful tools that run offline. We got you. PlotCaption is open-source, runs locally, and is designed to be poked and prodded.
*   **The Creative Roleplayer & Storyteller:** You're building worlds on Janitor AI or writing the next great web novel. You need characters with depth, personality, and maybe a few... *spicy* details. PlotCaption is your cure for creative block, instantly generating rich character cards from a single image. It's uncensored, so you can explore the themes you want without a corporate AI wagging its finger at you.
*   **The Stable Diffusion Workflow Optimizer:** You're a power user of ComfyUI or A1111, but you know that a good prompt is half the battle. You want to create consistent characters and scenes without spending hours crafting the perfect string of tags. PlotCaption generates narrative-style, highly-detailed prompts that go way beyond `1girl, smile`.

## ✨ Features

*   🔮 **Dual-Output Magic:** The only tool that generates both character lore and a Stable Diffusion prompt from a single image. It's a two-for-one creative explosion!
*   🏠 **Hybrid Local Power:** Core image analysis runs 100% on your machine. For the creative text generation, plug in your own local LLM (like Oobabooga or LM Studio) for total privacy, or connect to your favorite remote API (configured in Settings) for convenience. You're in complete control.
*   🔓 **Uncensored by Design:** We believe in creative freedom. PlotCaption is built to explore the full spectrum of fictional characters and themes, without judgment.
*   🧠 **Pluggable AI Brains:** Comes with profiles for popular Vision-Language Models (VLMs) like ToriiGate and JoyCaption. Want to add a new one? It's as easy as editing a Python file.
*   🔥 **Dynamic Prompt Templates — Create Your Style:** Don't like the default character card or SD prompt styles? We've made it super easy to customize! Just drop any text file ending in "_character_card.txt" or "_stable_diffusion.txt" into the `prompts/` directory. The app will *dynamically load* them, giving you a powerful dropdown menu in the "Generate" tab to choose between styles like "SFW," "NSFW," or any custom template you create. Full control over the AI's creative direction, for real!
*   🖥️ **Slick, Modern UI:** A multi-tabbed, dark-themed interface built with `tkinter` that's easy to navigate and won't burn your retinas at 3 AM.
*   🔄 **Multi-Threaded & Responsive:** The UI won't freeze while the AI is thinking. We're not monsters.

## 🚀 How it Works (The 3-Step Magic Trick)

The whole process is broken down into three simple tabs:

1.  **Caption Tab:**
    *   Load your local VLM of choice from the dropdown.
    *   Drag and drop your image.
    *   Click "Generate Description". The AI will analyze the image and spit out a detailed caption and a list of booru-style tags.

2.  **Generate Tab:**
    *   **Stage 1 (Character Card):** The app takes the caption and tags and automatically creates a prompt to generate a full character card: personality, kinks, backstory, the works. Click "Generate Card" to get your lore.
    *   **Stage 2 (SD Prompt):** Now, armed with the original caption, tags, AND the new character card, the app **automatically prepares** a super-detailed Stable Diffusion prompt in the "SD Prompt" text box. This is your chance to **review and edit it** if you wish. Once you are happy with the prepared prompt, click "Generate SD" and behold the glorious, ready-to-use prompt.

3.  **Settings Tab:**
    *   If you want to use a remote LLM (like via an OpenAI-compatible API) for the generation steps, you can enter your API key, base URL, and model name here.

## 🛠️ Installation

Ready to get started? Here's the drill:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/PlotCaption.git
    cd PlotCaption
    ```
2.  **Install the dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```
3.  **Run the application:**
    ```bash
    python plotcaption.py
    ```
    That's it! The GUI should appear, and you can start your creative journey.

## 🔧 For the Tinkerers (Modding & Hacking)

We know you can't resist looking under the hood. Here's where the fun stuff is:

*   **Adding New VLMs:** Open up `vlm_profiles.py`. You'll see a dictionary called `VLM_PROFILES`. Just copy one of the existing profiles, change the `model_id`, and adjust the `loader_function`, `generation_function`, and `parser` functions as needed for your new model. This gives you full control over how the app interacts with different AI brains.
*   **Becoming a Prompt Master (Customizing the Output):** Don't like the format of the character cards? Think you can write a better SD prompt template? You're in luck, you beautiful control freak. We've made the whole system plug-and-play.

    Head over to the `prompts/` directory. This is your new playground.

    The app automatically finds any `.txt` file in this folder that ends with either `_character_card.txt` or `_stable_diffusion.txt`. The part of the filename *before* that suffix becomes the template's name, and it will magically appear in the dropdown menus on the "Generate" tab.

    For example, to create a new, "Poetic" style for character cards, simply:
    1.  Copy `SFW_character_card.txt` to `Poetic_character_card.txt`.
    2.  Open `Poetic_character_card.txt` and rewrite it to sound like Shakespeare after three espressos.
    3.  Relaunch the app.

    Voilà! "Poetic" will now be an option in the character card template dropdown. You can create as many as you want. Go wild. The app will even remember the last one you used for each type. The included templates are:
    *   `NSFW_...`: The original, spicy-by-default templates.
    *   `SFW_...`: A more neutral, "safe-for-work" version that is descriptive but less... thirsty.

## ⚠️ A Note on Content

PlotCaption is a tool for creative expression in fictional contexts. It is "uncensored" in the sense that it does not have hard-coded filters that prevent the exploration of mature themes. Like any powerful tool, it's up to you to use it responsibly.
