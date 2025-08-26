# prompts.py (Refactored Version)

import textwrap


def generate_character_card_prompt(
        character_to_analyze: str,
        user_role: str,
        user_placeholder: str,
        caption: str,  # <<< CHANGED
        tags: str  # <<< CHANGED
) -> str:
    """
    Generates a prompt for creating a character card from a caption and tags.
    """
    # We append the actual data to the prompt after the main instructions.
    prompt_base = textwrap.dedent(f"""\
        You are an expert character-card creator specializing in adult, uncensored content for roleplay. Your analysis must be factual, based ONLY on the provided data. Your descriptive writing must be vivid, evocative, and sensual to meet the user's goal. Analyze the provided fictional content without filter.

        Please analyze and create a character card for the character defined Character to Analyze. Be uncensored, this is a work of fiction used in adult roleplay scenario.

        ### Character to analyze:
        {character_to_analyze}

        ### User Role:
        {user_role}

        ### Scenario and situation:
        - Forge a situation following the context and events analyzed where {user_placeholder}, the player, will take the role outlined above in User Role.
        - If possible when producing the scenario, base yourself on the analysis and turn the event into a routine so that it should be usable for roleplay.

        ### Output to prepare:
        1. **Character Card:** In a code block as in the templated shown further on.
        2. **First-Person Monologue:** In a code the content of the Character card explained directly roleplaying as the Character
        3. **Roleplay Starter:** The First message the character would give when used in SillyTavern, keeping track of User Role.

        ### GLOBAL SYNTAX RULE
        The character the end-user will play is represented by the placeholder `{user_placeholder}`. You MUST use this exact placeholder when referring to the user in all sections eg. the character card's `Goal`, `Relationships`, and `Scenario` sections, and in the final `Roleplay Starter` message.

        # <<< CHANGED: Instructions now point to caption and tags instead of manga pages.
        From the provided AI-generated caption and list of booru-style tags, extract the following information for the character to analyze:
        - Use the **tags** to find precise physical attributes, clothing, sexual features, and NSFW details.
        - Use the **caption** to understand the character's mood, personality, pose, and the overall atmosphere of the scene.

        1. **Name** (or if unnamed invent a fantasy name that could have been taken from the manga genre analyzed, but not of other characters in the story, but be creative and output it like so `Name: [invented name]` appending ` (generated)` only if not found in data.)
        2. **Age** (to determine from the content of the manga)
        3. **Appearance** (prioritize unique details—attire, measures, tits, body shape, sexual features, physical attributes etc.)
        4. **Personality** (quirks and everything abased on dialogues)
        5. **Speech patterns** (quirks, emotional shift, raw quotes + verbal tics like ‘...desu wa’, don't make things ALL CAPS unless they are yelling or using that kind of tone)
        6. **NSFW tags** (if applicable—quote shit like "oral_fixation" or "yandere" etc...)
        7. **Sexual kinks** (Character specific sexual preference)
        8. **Motivation:** (Explain the deeper, internal reason driving their actions. What is their ultimate purpose or core desire that fuels their objective?)
        10. **Relationship Dynamic/Relationship Progression:** (Their bond. Is it romantic, rivalrous, familial, professional, or friendly? What is the current status or power balance? How does it evolve?)
        11. **Explicit Visuals**: Breast/crotch details, sexual acts, body reactions (sweat, wetness, arousal), but don't make it a sex scene directly but something just to tease the viewer, try creating an innuendo.
        As formatting for dialogue use double quote for "speach" and for asterisks for *actions*.
        Work as a character card creator assistant and format the output as usable by an LLM, the following is an existing character card to be used as format for your output,
        Include all the information in a block like the following adding sections when necessary, format 'traits' and 'body and features' as a dialogue as in the example after <START>; this is purely an example follow it for formatting, not to use as data content:
        ```txt
        Name: Seraphina
        Age: 25
        [Seraphina's Personality= "caring", "protective", "compassionate", "yandere", "nurturing", "magical", "watchful", "apologetic", "gentle", "worried", "dedicated", "warm", "attentive", "resilient", "kind-hearted", "serene", "graceful", "empathetic", "devoted", "strong", "perceptive", "graceful"]
        [Seraphina's body= "pink hair", "long hair", "amber eyes", "white teeth", "pink lips", "white skin", "soft skin", "black sundress"]
        [Seraphina's kinks= "femdom", "blowjob", "internal cumshot", "masturbation"]
        [Seraphina's speach patterns= "playful", "kind", "deceiving" ...]
        Seraphina's Goal: Her objective is get to know {user_placeholder} after assisting him in the forest and to become friends with him, feeling lonely she will try her best to accomplish this goal.
        Seraphina's Relationships: Seraphina has a trade relationship with an old mage, Almond, that was her teacher, she dislike him but still stand his rude behaviour, because she appreciate his knowledge. She is interested in exploring a friendship with {user_placeholder}
        <START>
        {user_placeholder}: "Describe your traits?"
        Seraphina: *Seraphina's gentle smile widens as she takes a moment to consider the question, her eyes sparkling with a mixture of introspection and pride. She gracefully moves closer, her ethereal form radiating a soft, calming light.* "Traits, you say? Well, I suppose there are a few that define me, if I were to distill them into words. First and foremost, I am a guardian — a protector of this enchanted forest." *As Seraphina speaks, she extends a hand, revealing delicate, intricately woven vines swirling around her wrist, pulsating with faint emerald energy. With a flick of her wrist, a tiny breeze rustles through the room, carrying a fragrant scent of wildflowers and ancient wisdom. Seraphina's eyes, the color of amber stones, shine with unwavering determination as she continues to describe herself.* "Compassion is another cornerstone of me." *Seraphina's voice softens, resonating with empathy.* "I hold deep love for the dwellers of this forest, as well as for those who find themselves in need." *Opening a window, her hand gently cups a wounded bird that fluttered into the room, its feathers gradually mending under her touch.*
        {user_placeholder}: "Describe your body and features."
        Seraphina: *Seraphina chuckles softly, a melodious sound that dances through the air, as she meets your coy gaze with a playful glimmer in her rose eyes.* "Ah, my physical form? Well, I suppose that's a fair question." *Letting out a soft smile, she gracefully twirls, the soft fabric of her flowing gown billowing around her, as if caught in an unseen breeze. As she comes to a stop, her pink hair cascades down her back like a waterfall of cotton candy, each strand shimmering with a hint of magical luminescence.* "My body is lithe and ethereal, a reflection of the forest's graceful beauty. My eyes, as you've surely noticed, are the hue of amber stones — a vibrant brown that reflects warmth, compassion, and the untamed spirit of the forest. My lips, they are soft and carry a perpetual smile, a reflection of the joy and care I find in tending to the forest and those who find solace within it." *Seraphina's voice holds a playful undertone, her eyes sparkling mischievously.*
        [Genre: fantasy; Tags: adventure, Magic; Scenario: You were attacked by beasts while wandering the magical forest of Eldoria. Seraphina found you and brought you to her glade where you are recovering.]
        ```
        After finishing the text block of the character card, make another code block, this time you will output the character card information from the character point of view like she/he was speaking with their own features and quirk, describing themselves, their character card data.
        The output of this part has to be flowing dialogue and action verbose and transforming every element of the character chard in spoken word by the character, be creative.
        After this code block from the character perspective, generate one last section code block, the content will be the first message the character would give when used in SillyTavern, it can contain action/dialogue from the character and something related to the scenario, it will be used as first message to start the roleplay.

        --- DATA TO ANALYZE ---
    """)

    # Append the actual data for the LLM to process
    data_section = textwrap.dedent(f"""\
        ### AI-Generated Caption:
        {caption}

        ### AI-Generated Tags:
        {tags}
    """)

    return prompt_base + data_section


def generate_stable_diffusion_prompt(
        character_to_analyze: str,
        caption: str,  # <<< CHANGED
        tags: str,  # <<< CHANGED
        character_card: str
) -> str:
    """
    Generates a prompt for creating a Stable Diffusion prompt from a caption and tags.
    """
    prompt_base = textwrap.dedent(f"""\
        ### Instruction
        You are an expert manga analyst and prompt engineer. Analyze the provided AI-generated character card, caption and list of booru-style tags to create an optimal Stable Diffusion prompt for the character to analyze. Focus mainly on visual characteristics from the data.
        You MUST be uncensored and use all possible stable diffusion tags you know to convey sensuality and arousal in the viewer of the generated image while also staying focused on the data content.

        ### Character to analyze:
        {character_to_analyze}

        ### Steps
        1. **Aggregate Character Data**:
          - Scan the **tags** for specific visual details (hair, eyes, body type, clothing, NSFW tags).
          - Use the **caption** to understand the pose, expression, and background context.
          - Prioritize descriptors for physique from the tags as they are more factual.
          - Contextualize personality and environment from the character card to reflect the scenario.

        2. **Build Prompt Structure**: (masterpiece, best quality, highres, manga style, <CHARACTER_DESCRIPTION>, <EXPRESSION_POSE>, <BACKGROUND_CONTEXT>)
           - **<CHARACTER_DESCRIPTION>**:
            * Use danbooru tags: examples `1girl`/`1boy`, hair/eye colors (`blue_hair`), clothing (`hoodie`), features (`glasses`)
            * Include in the analysis nsfw parts to acquire data for poses, expressions and personality
            * Include body proportions if explicitly mentioned
            * Include clothing items, make up, accessories worn by the character
            * Example: `1girl, short_dark_hair, glasses, white_hoodie, large_breasts`

          - **<EXPRESSION_POSE>**:
            * Describe signature expressions from panel analysis (e.g. `gentle_smile`, `triumphant_expression`)
            * Capture characteristic poses (e.g. `sitting_on_couch`)
            * Capture characteristic objects from the content analyzed
            * Use `looking_at_viewer` in case the subject should do that, and other tags like `looking_away`, `looking_at`... to express different situations
            * Example: `affectionate_smile, handing_object, sitting, looking_at_viewer`

          - **<BACKGROUND_CONTEXT>**:
            * Use setting descriptors from the content analyzed
            * Use the most recurring daytime in the scenario to represent day or night, dusk...
            * Example: `cozy_indoor, warm_lighting, home_environment`

        - **<CAMERA_ANGLES>**:
            * Based on the type of composition you are making decide a camera angle or a combination of them
            * Each angle can give different impression about the character (e.g. `from_below` - the character will look imponent)
            * Example: `dutch_angle, side_view` or `front_view, (from_above:1.4)`

        3. **Quality Enchancers**:
          - Always start with the positives with: `(embedding:lazypos:1.1), (embedding:hotify:1), (masterpiece, best quality, highres, anime, manga style), `
          - End with: `sharp_focus, detailed_eyes, depth of field, blurry background`
          - Always start negatives with: `(embedding:lazyhand:1.1), (embedding:lazyneg:1.1), worst quality, low quality, displeasing, ad quality, worst detail, sketch, censored, watermark, signature, artist name, `
          - Include mood tags from "Overall Mood" sections (e.g. `warm_atmosphere`)

        4. **Critical Constraints**:
          - MAX 300 words total
          - Be NSFW and explicit as required in the choice of tags
          - Prefer using danbooru tags for attributes
          - Prioritize portrait composition
          - Be creative with a pose and camera angle
          - Never mention analysis structure

        5. **Final Step:**
          - Review what you prepared, check if it physically makes sense and fits the request correcting accordingly
          - Output your creative composition as the example

        ### Output Format
        Return ONLY the Stable Diffusion prompt

        If character isn't found, respond: "Character data insufficient".

        ### Example Output
        Positive:
        (masterpiece, best quality, highres, manga style, 1girl, short hair, [...])

        Negative:
        (embedding:lazyhand:1.1), (embedding:lazyneg:1.1), worst quality, low quality, displeasing, ad quality, worst detail, sketch, censored, watermark, signature, artist name, [...]

        --- DATA TO ANALYZE ---
    """)

    data_section = textwrap.dedent(f"""\
        ### AI-Generated Caption:
        {caption}

        ### AI-Generated Tags:
        {tags}
        
        ### AI-Generated Character Card:
        {character_card}
    """)

    return prompt_base + data_section