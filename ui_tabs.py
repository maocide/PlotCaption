import queue
import threading
import tkinter as tk

from sympy.physics.units import temperature
from tkinterdnd2 import DND_FILES

import ai_utils
import config
from tkinter import ttk, messagebox

from config import *
from prompts import generate_stable_diffusion_prompt, generate_character_card_prompt
from vlm_profiles import VLM_PROFILES
from tkinter import messagebox



# This file will hold the classes for each tab in the notebook.

class CaptionTab(ttk.Frame):
    def __init__(self, parent, controller):
        """
        Initializes the Caption Tab.

        Args:
            parent: The parent widget (the ttk.Notebook).
            controller: The main VLM_GUI application instance.
        """
        super().__init__(parent, style='Dark.TFrame')
        self.controller = controller

        main_frame = ttk.Frame(self, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # --- Top Frame for Model Control ---
        top_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        top_frame.pack(fill=tk.X, pady=(0, 10))

        self.load_button = ttk.Button(top_frame, text="Load Model", command=self.controller.load_model_threaded,
                                      style='Dark.TButton', width=15)
        self.load_button.pack(side=tk.LEFT, padx=(0, 10))

        self.unload_button = ttk.Button(top_frame, text="Unload Model", command=self.controller.unload_model, style='Dark.TButton',
                                        width=15)
        self.unload_button.pack(side=tk.LEFT, padx=(0, 20))
        self.unload_button.config(state=tk.DISABLED)

        model_label = ttk.Label(top_frame, text="Model:", style='Dark.TLabel')
        model_label.pack(side=tk.LEFT)

        self.model_selection_combo = ttk.Combobox(
            top_frame,
            values=list(VLM_PROFILES.keys()),
            state='readonly',
            style='Dark.TCombobox',
            width=48
        )
        self.model_selection_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Set initial value from saved settings or default
        last_vlm = self.controller.settings.get('last_used_vlm')
        vlm_options = list(VLM_PROFILES.keys())
        if last_vlm in vlm_options:
            self.model_selection_combo.set(last_vlm)
        elif vlm_options:
            self.model_selection_combo.current(0)

        self.model_selection_combo.bind("<<ComboboxSelected>>", self._on_model_selected)

        # --- Main Content Frame (Image and Text) ---
        content_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)

        # --- Image Display Area ---
        self.image_label = ttk.Label(content_frame, text="Drag & Drop an Image Here", style='Placeholder.TLabel',
                                     relief=tk.SOLID)
        self.image_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        self.image_label.drop_target_register(DND_FILES)
        self.image_label.dnd_bind('<<Drop>>', self.handle_drop)

        # --- Right Panel for Inputs and Output ---
        right_panel = ttk.Frame(content_frame, style='Dark.TFrame')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- GRID CONFIGURATION FOR THE RIGHT PANEL ---
        # Tell the grid that column 0 should expand to fill the horizontal space.
        right_panel.columnconfigure(0, weight=1)

        # Tell the grid how to distribute EXTRA vertical space.
        # A 2:1 ratio means the caption gets 2/3 and the tags get 1/3 of the extra space.
        right_panel.rowconfigure(4, weight=2)
        right_panel.rowconfigure(6, weight=1)
        # All other rows have a default weight of 0 and will not expand vertically.

        # --- Place widgets using .grid() instead of .pack() ---

        # Row 0: Input Prompt Label
        prompt_label = ttk.Label(right_panel, text="Your Question/Prompt:", style='Dark.TLabel')
        prompt_label.grid(row=0, column=0, sticky="w")

        # Row 1: Input Prompt Text (fixed height, doesn't expand)
        self.caption_prompt = tk.Text(right_panel, height=4, bg=TEXT_BG_COLOR, fg=FIELD_FOREGROUND_COLOR,
                                      relief=tk.FLAT,
                                      insertbackground=INSERT_BACKGROUND_COLOR)
        self.caption_prompt.grid(row=1, column=0, sticky="ew", pady=(5, 10))
        # self.caption_prompt.insert(tk.END, DEFAULT_PROMPT) # This is now handled by _on_model_selected
        self._on_model_selected()  # Call this now that caption_prompt exists

        # Row 2: Generate Button (fixed height)
        self.generate_button = ttk.Button(right_panel, text="Generate Description", command=self.controller.generate_threaded,
                                          style='Dark.TButton')
        self.generate_button.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.generate_button.config(state=tk.DISABLED)

        # --- NEW: Output Caption Label with Copy Button ---
        caption_label_frame = ttk.Frame(right_panel, style='Dark.TFrame')
        caption_label_frame.grid(row=3, column=0, sticky="ew")

        output_caption_label = ttk.Label(caption_label_frame, text="Model Output:", style='Dark.TLabel')
        output_caption_label.pack(side=tk.LEFT)  # This stays on the left

        self.copy_caption_button = ttk.Button(caption_label_frame, image=self.controller.copy_icon,
                                              command=lambda: self.controller.copy_to_clipboard(self.output_caption_text,
                                                                                     "Caption"),
                                              style='Icon.TButton')
        self.copy_caption_button.pack(side=tk.RIGHT)  # <-- CHANGE THIS to tk.RIGHT
        self.copy_caption_button.bind("<Enter>", self._on_copy_enter)
        self.copy_caption_button.bind("<Leave>", self._on_copy_leave)

        # Row 4: Output Caption Text
        caption_text_frame = ttk.Frame(right_panel, style='Border.TFrame')
        caption_text_frame.grid(row=4, column=0, sticky="nsew")
        caption_text_frame.columnconfigure(0, weight=1)
        caption_text_frame.rowconfigure(0, weight=1)

        self.output_caption_text = tk.Text(caption_text_frame, wrap="word", bg=TEXT_BG_COLOR,
                                           fg=FIELD_FOREGROUND_COLOR, relief="flat",
                                           insertbackground=INSERT_BACKGROUND_COLOR,
                                           highlightthickness=0, borderwidth=0, state=tk.DISABLED)
        caption_scrollbar = ttk.Scrollbar(caption_text_frame, orient="vertical",
                                          style='Dark.Vertical.TScrollbar',  # <-- The magic style!
                                          command=self.output_caption_text.yview)
        self.output_caption_text.config(yscrollcommand=caption_scrollbar.set)

        self.output_caption_text.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        caption_scrollbar.grid(row=0, column=1, sticky="ns")

        # Output Tags Label with Copy Button
        tags_label_frame = ttk.Frame(right_panel, style='Dark.TFrame')
        tags_label_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0))

        output_tags_label = ttk.Label(tags_label_frame, text="Booru Tags Output:", style='Dark.TLabel')
        output_tags_label.pack(side=tk.LEFT)  # This stays on the left

        self.copy_tags_button = ttk.Button(tags_label_frame, image=self.controller.copy_icon,
                                           command=lambda: self.controller.copy_to_clipboard(self.output_tags_text, "Tags"),
                                           style='Icon.TButton')
        self.copy_tags_button.pack(side=tk.RIGHT)
        self.copy_tags_button.bind("<Enter>", self._on_copy_enter)
        self.copy_tags_button.bind("<Leave>", self._on_copy_leave)

        # Row 6: Output Tags Text
        tags_text_frame = ttk.Frame(right_panel, style='Border.TFrame')
        tags_text_frame.grid(row=6, column=0, sticky="nsew")
        tags_text_frame.columnconfigure(0, weight=1)
        tags_text_frame.rowconfigure(0, weight=1)

        self.output_tags_text = tk.Text(tags_text_frame, wrap="word", bg=TEXT_BG_COLOR,
                                        fg=FIELD_FOREGROUND_COLOR, relief="flat",
                                        insertbackground=INSERT_BACKGROUND_COLOR,
                                        highlightthickness=0, borderwidth=0, state=tk.DISABLED)
        tags_scrollbar = ttk.Scrollbar(tags_text_frame, orient="vertical",
                                       style='Dark.Vertical.TScrollbar',  # <-- The magic style again!
                                       command=self.output_tags_text.yview)
        self.output_tags_text.config(yscrollcommand=tags_scrollbar.set)

        self.output_tags_text.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        tags_scrollbar.grid(row=0, column=1, sticky="ns")

        # Row 7: Button Container
        button_container = ttk.Frame(right_panel, style='Dark.TFrame')
        button_container.grid(row=7, column=0, sticky="ew", pady=(10, 0))

        print("Caption Tab initialized!") # Placeholder

    def handle_drop(self, event):
        """
        Handles the drag-and-drop file event.
        """
        filepath = event.data.strip('{}')
        self.controller.process_dropped_image(filepath)
        # if filepath.lower().endswith(ACCEPTED_IMAGE_EXTENSIONS):
        #     #self.image_path = filepath
        #     #self.load_and_display_image()
        # else:
        #     supported_extensions = ', '.join(ACCEPTED_IMAGE_EXTENSIONS)
        #     messagebox.showerror("Error", f"Invalid file type.\nAccepted: {supported_extensions}\n Please drop a valid image file.")

    # def load_and_display_image(self):
    #     """
    #     Loads an image from the given path, displays it as a thumbnail,
    #     and updates the application state. If a model is already loaded,
    #     it transitions to the READY_TO_GENERATE state.
    #     """
    #     try:
    #         self.controller.image_raw = Image.open(self.image_path).convert("RGB")
    #         display_image = self.controller.image_raw.copy()
    #         display_image.thumbnail(MAX_THUMBNAIL_SIZE)
    #         self.image_tk = ImageTk.PhotoImage(display_image)
    #
    #         self.image_label.config(image=self.image_tk, text="")
    #
    #         if self.controller.current_state == AppState.MODEL_LOADED:
    #             self.controller.set_state(AppState.READY_TO_GENERATE)
    #         elif self.controller.current_state == AppState.MODEL_LOADING:
    #             self.controller.update_status("Image ready. Wait for model...")
    #         elif self.controller.current_state == AppState.READY_TO_GENERATE:
    #             self.controller.update_status("Image ready. Ready to generate.")
    #         else:
    #             # If the model isn't loaded yet, just update the status
    #             self.controller.update_status("Image ready. Now load a model.")
    #
    #     except Exception as e:
    #         messagebox.showerror("Image Error", f"Failed to load image: {e}")
    #         self.controller.image_path = None

    def update_caption_text(self, text):
        """Updates the cart text box."""
        self.output_caption_text.config(state=tk.NORMAL)
        self.output_caption_text.delete("1.0", tk.END)
        self.output_caption_text.insert(tk.END, text)
        self.output_caption_text.config(state=tk.DISABLED)

    def update_tags_text(self, text):
        """Updates the tags text box."""
        self.output_tags_text.config(state=tk.NORMAL)
        self.output_tags_text.delete("1.0", tk.END)
        self.output_tags_text.insert(tk.END, text)
        self.output_tags_text.config(state=tk.DISABLED)



    def _on_model_selected(self, event=None):
        """
        Handles the event when a new model is selected from the Combobox.
        Loads the corresponding profile and updates the UI.
        """
        model_name = self.model_selection_combo.get()
        self.controller.loaded_profile = VLM_PROFILES.get(model_name)

        if self.controller.loaded_profile:
            # Update the prompt text box with the prompt from the selected profile
            self.caption_prompt.delete("1.0", tk.END)
            self.caption_prompt.insert(tk.END, self.controller.loaded_profile.prompt_caption)
        else:
            # This case should ideally not happen with a readonly combobox
            messagebox.showerror("Profile Error", f"No VLM profile defined for '{model_name}'.")
            self.caption_prompt.delete("1.0", tk.END)

    def _on_copy_enter(self, event):
        """Changes the button image when the mouse enters."""
        event.widget.config(image=self.controller.copy_icon_hover)

    def _on_copy_leave(self, event):
        """Changes the button image back when the mouse leaves."""
        event.widget.config(image=self.controller.copy_icon)

    # --- METHODS ---
    # Move the functions from plotcaption.py that are specific to this tab
    # here to become methods of this class.
    #
    # def handle_drop(self, event):
    #     # ...
    #
    # def load_and_display_image(self):
    #     # ...


class GenerateTab(ttk.Frame):
    def __init__(self, parent, controller, copy_icon, copy_icon_hover):
        """
        LLM tab widget setup.
        """
        super().__init__(parent)
        self.controller = controller

        self.copy_icon = copy_icon  # <-- Store the icon
        self.copy_icon_hover = copy_icon_hover  # <-- Store the hover icon

        # The tab creates its OWN main frame.
        main_llm_frame = ttk.Frame(self, style='Dark.TFrame', padding=10)
        main_llm_frame.pack(expand=True, fill="both")

        main_llm_frame.columnconfigure(0, weight=1)
        main_llm_frame.columnconfigure(1, weight=1)
        main_llm_frame.rowconfigure(2, weight=1)  # Adjusted row for text box
        main_llm_frame.rowconfigure(5, weight=1)  # Adjusted row for text box


        self.card_template_combo = ttk.Combobox(
            main_llm_frame,
            values=self.controller.card_prompt_templates,
            state='readonly',
            style='Dark.TCombobox'
        )
        self.card_template_combo.bind("<<ComboboxSelected>>", lambda event: self._on_prompt_template_selected(event, 'card'))

        self.sd_template_combo = ttk.Combobox(
            main_llm_frame,
            values=self.controller.sd_prompt_templates,
            state='readonly',
            style='Dark.TCombobox'
        )
        self.sd_template_combo.bind("<<ComboboxSelected>>", lambda event: self._on_prompt_template_selected(event, 'sd'))

        # Place Comboboxes
        self.card_template_combo.grid(row=0, column=0, padx=5, pady=(0, 5), sticky="ew")
        self.sd_template_combo.grid(row=0, column=1, padx=5, pady=(0, 5), sticky="ew")

        # Input boxes don't get a copy button
        self.card_text_box = self.create_labeled_textbox(
            parent=main_llm_frame,
            label_text="Character card Prompt:",
            grid_row=1,  # Adjusted row
            grid_column=0
        )

        self.sd_text_box = self.create_labeled_textbox(
            parent=main_llm_frame,
            label_text="SD Prompt:",
            grid_row=1,  # Adjusted row
            grid_column=1
        )

        # Output boxes created with a copy button
        self.card_output_text_box = self.create_labeled_textbox(
            parent=main_llm_frame,
            label_text="Output Character Card:",
            grid_row=4,  # Adjusted row
            grid_column=0,
            copy_command=lambda: self.controller.copy_to_clipboard(self.card_output_text_box, "Character Card")
        )

        self.sd_output_text_box = self.create_labeled_textbox(
            parent=main_llm_frame,
            label_text="Output SD Prompt:",
            grid_row=4,  # Adjusted row
            grid_column=1,
            copy_command=lambda: self.controller.copy_to_clipboard(self.sd_output_text_box, "SD Prompt")
        )

        # Generate Buttons
        self.card_generate_button = ttk.Button(main_llm_frame, text="Generate Card",
                                               command=self._generate_card_threaded,
                                               style='Dark.TButton')
        self.card_generate_button.grid(row=3, column=0, sticky="ns", pady=5)  # Adjusted row
        self.sd_generate_button = ttk.Button(main_llm_frame, text="Generate SD",
                                             command=self._generate_sd_prompt_threaded,
                                             style='Dark.TButton')
        self.sd_generate_button.grid(row=3, column=1, sticky="ns", pady=5)  # Adjusted row

        # Load Last Used Templates
        last_card_template = self.controller.settings.get("last_card_template", DEFAULT_CARD_TEMPLATE)
        last_sd_template = self.controller.settings.get("last_sd_template", DEFAULT_SD_TEMPLATE)

        if last_card_template in self.controller.card_prompt_templates:
            self.card_template_combo.set(last_card_template)
        else:
            self.card_template_combo.set(DEFAULT_CARD_TEMPLATE)

        if last_sd_template in self.controller.sd_prompt_templates:
            self.sd_template_combo.set(last_sd_template)
        else:
            self.sd_template_combo.set(DEFAULT_SD_TEMPLATE)



        print("Generate Tab initialized!") # Placeholder

    def post_init_setup(self):
        """Run setup tasks that require the rest of the application to exist."""
        print("Running Generate Tab post-init setup...")
        # Put the moved lines here instead
        self._on_prompt_template_selected(None, 'card')
        self._on_prompt_template_selected(None, 'sd')

    def _generate_card_threaded(self):
        """
        Handles the 'Generate Card' button click event in a separate thread.
        """
        self.controller.start_api_generation_task()

        self.task_queue = queue.Queue()
        threading.Thread(
            target=self._api_call_task,
            args=(
                self.card_text_box,
                self.card_output_text_box,
                self.task_queue,
                'card'
            ),
            daemon=True
        ).start()
        self.after(100, self._process_api_queue)

    def _generate_sd_prompt_threaded(self):
        """
        Handles the 'Generate SD' button click event in a separate thread.
        """
        self.controller.start_api_generation_task()

        self.task_queue = queue.Queue()
        threading.Thread(
            target=self._api_call_task,
            args=(
                self.sd_text_box,
                self.sd_output_text_box,
                self.task_queue,
                'sd'
            ),
            daemon=True
        ).start()
        self.after(100, self._process_api_queue)



    def _api_call_task(self, input_widget, output_widget, q, task_type):
        """
        A generic worker thread for making API calls.
        """
        try:
            # Get credentials and prompt
            api_key = self.controller.settings_tab.llm_key_entry.get().strip()
            base_url = self.controller.settings_tab.llm_url_entry.get().strip()
            model_name = self.controller.settings_tab.llm_model_entry.get().strip()
            prompt = input_widget.get("1.0", tk.END).strip()
            # Values rounded to avoid long floats
            temperature = round(self.controller.settings_tab.temperature_slider.get(), 2)
            frequency_penalty = round(self.controller.settings_tab.frequency_penalty_slider.get(), 2)
            presence_penalty = round(self.controller.settings_tab.presence_penalty_slider.get(), 2)

            if not all([api_key, base_url, model_name, prompt]):
                q.put(("error", "API credentials, model, url and prompt cannot be empty."))
                q.put(("done", task_type))
                return

            # Make the API call using ai_utils module
            q.put(("status", f"Calling model {model_name}..."))
            response = ai_utils.call_text_model(
                api_key=api_key,
                base_url=base_url,
                model=model_name,
                user_request=prompt,
                temperature=temperature,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty
            )

            # Update the UI with the result of the task
            if response:
                q.put(("update_output", (output_widget, response)))
                q.put(("status", "API call successful."))
            else:
                q.put(("error", "API call failed!"))

        except Exception as e:
            q.put(("error", f"An error occurred during the API call: {e}"))
        finally:
            q.put(("done", task_type))

    def _process_api_queue(self):
        """
        Checks the queue for messages from the API worker thread and updates the UI.
        """
        try:
            message_type, data = self.task_queue.get_nowait()

            if message_type == "status": # status update, we display it
                self.controller.update_status(data)
            elif message_type == "update_output": # updates the control text
                widget, text = data
                widget.config(state=tk.NORMAL)
                widget.delete("1.0", tk.END)
                widget.insert(tk.END, text)
                widget.config(state=tk.DISABLED)
            elif message_type == "error":
                messagebox.showerror("API Error", data)
            elif message_type == "done":
                task_type = data  # This will be 'card' or 'sd'
                if task_type == 'card':
                    # The card is finished, NOW we populate the SD prompt
                    final_caption = self.controller.caption_tab.output_caption_text.get("1.0", tk.END).strip()
                    final_tags = self.controller.caption_tab.output_tags_text.get("1.0", tk.END).strip()
                    final_card = self.card_output_text_box.get("1.0", tk.END).strip()
                    self.populate_generate_sd(final_caption, final_card, final_tags)
                    self.controller.end_api_generation_task() # change controller state
                else:  # The SD prompt finished
                    self.controller.end_api_generation_task() # change controller state
                return  # Stop the queue-checking loop. We finished card or sd prompt

        except queue.Empty:
            pass

        self.after(100, self._process_api_queue) # Schedule again the queue process until done

    def populate_generate_card(self, caption: str, tags: str):
        """
        Generates prompts based on VLM output and populates the Generate tab.
        """
        template_name = self.card_template_combo.get()
        card_prompt = generate_character_card_prompt(
            template_name=template_name,
            caption=caption,
            tags=tags,
            character_to_analyze=CARD_CHAR_TO_ANALYZE,
            user_role=CARD_USER_ROLE,
            user_placeholder="{{user}}"
        )

        self.card_text_box.config(state=tk.NORMAL)
        self.card_text_box.delete("1.0", tk.END)
        self.card_text_box.insert(tk.END, card_prompt)

    def populate_generate_sd(self, caption: str, character_card: str, tags: str):
        """
        Populates the Stable Diffusion prompt by replacing placeholders in the
        currently selected template.
        """
        template_name = self.sd_template_combo.get()
        sd_prompt = generate_stable_diffusion_prompt(
            template_name=template_name,
            caption=caption,
            tags=tags,
            character_card=character_card,
            character_to_analyze=SD_CHAR_TO_ANALYZE
        )

        self.sd_text_box.config(state=tk.NORMAL)
        self.sd_text_box.delete("1.0", tk.END)
        self.sd_text_box.insert(tk.END, sd_prompt)



    def _on_prompt_template_selected(self, event, prompt_type):
        """
        Handles the event when a new prompt template is selected.
        Triggers the repopulation of the corresponding prompt text box,
        ensuring all updates go through the placeholder replacement logic.
        """
        # Get the current data from the UI.
        # These will be empty strings if no data is present.
        final_caption = self.controller.caption_tab.output_caption_text.get("1.0", tk.END).strip()
        final_tags = self.controller.caption_tab.output_tags_text.get("1.0", tk.END).strip()

        if prompt_type == 'card':
            # Always call _populate_generate_card. It will handle generating
            # the prompt with or without data to fill the placeholders.
            self.populate_generate_card(final_caption, final_tags)
        elif prompt_type == 'sd':
            # Always call _populate_generate_SD, which also needs the card text.
            final_card = self.card_output_text_box.get("1.0", tk.END).strip()
            self.populate_generate_sd(final_caption,  final_card, final_tags)

    def create_labeled_textbox(self, parent, label_text, grid_row, grid_column, copy_command=None):
        """
        Creates and grids a labeled Text widget with an optional, right-aligned copy button.
        """
        # Create the Label Frame (this will hold the label and optional button) ---
        label_frame = ttk.Frame(parent, style='Dark.TFrame')
        label_frame.grid(row=grid_row, column=grid_column, padx=5, pady=(5, 0), sticky="ew")

        label = ttk.Label(label_frame, text=label_text, style='Dark.TLabel')
        label.pack(side=tk.LEFT)

        # If a copy command is provided, create the button
        if copy_command:
            copy_button = ttk.Button(label_frame, image=self.copy_icon, command=copy_command, style='Icon.TButton')
            copy_button.pack(side=tk.RIGHT)
            copy_button.bind("<Enter>", self._on_copy_enter)
            copy_button.bind("<Leave>", self._on_copy_leave)

        # Create the Text Box Frame
        outer_frame = ttk.Frame(parent, style='Dark.TFrame')
        outer_frame.grid(row=grid_row + 1, column=grid_column, sticky="nsew", padx=5, pady=5)
        outer_frame.columnconfigure(0, weight=1)
        outer_frame.rowconfigure(0, weight=1)

        border_frame = ttk.Frame(outer_frame, style='Border.TFrame')
        border_frame.grid(row=0, column=0, sticky="nsew")
        border_frame.columnconfigure(0, weight=1)
        border_frame.rowconfigure(0, weight=1)

        text_box = tk.Text(border_frame, wrap="word", bg=TEXT_BG_COLOR, fg=FIELD_FOREGROUND_COLOR,
                           relief="flat", insertbackground=INSERT_BACKGROUND_COLOR,
                           highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(border_frame, orient="vertical", style='Dark.Vertical.TScrollbar',
                                  command=text_box.yview)
        text_box.config(yscrollcommand=scrollbar.set)
        text_box.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        scrollbar.grid(row=0, column=1, sticky="ns")

        return text_box

    def _on_copy_enter(self, event):
        """Changes the button image when the mouse enters."""
        event.widget.config(image=self.controller.copy_icon_hover)

    def _on_copy_leave(self, event):
        """Changes the button image back when the mouse leaves."""
        event.widget.config(image=self.controller.copy_icon)


class SettingsTab(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style='Dark.TFrame')
        self.controller = controller

        # The main container frame that holds everything
        main_frame = ttk.Frame(self, style='Dark.TFrame', padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # A dedicated frame for the button at the bottom
        bottom_frame = ttk.Frame(self, style='Dark.TFrame', padding=(15, 0, 15, 15))
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Configure the grid inside the main_frame ---
        # Make the second column (index 1) where the sliders/entries live, expand
        main_frame.columnconfigure(1, weight=1)

        # --- API and Model Entries ---
        # Row 0: API URL
        url_label = ttk.Label(main_frame, text="API Url:", style='Dark.TLabel')
        url_label.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        self.llm_url_entry = ttk.Entry(main_frame, style='Dark.TEntry')
        self.llm_url_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        # Row 1: API Key & Model
        llm_key_label = ttk.Label(main_frame, text="API Key:", style='Dark.TLabel')
        llm_key_label.grid(row=1, column=0, padx=(0, 5), pady=5, sticky="w")
        self.llm_key_entry = ttk.Entry(main_frame, style='Dark.TEntry', show='*')
        self.llm_key_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        llm_model_label = ttk.Label(main_frame, text="Model:", style='Dark.TLabel')
        llm_model_label.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.llm_model_entry = ttk.Entry(main_frame, style='Dark.TEntry')
        self.llm_model_entry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        # Row 2: Save/Test Buttons
        button_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        button_frame.grid(row=1, column=4, padx=5, pady=5, sticky="e")
        self.save_button = ttk.Button(button_frame, text="Save", command=self._save_api_settings, style='Dark.TButton')
        self.save_button.pack(side=tk.LEFT, padx=(0, 5))
        self.test_button = ttk.Button(button_frame, text="Test", command=self._test_api_connection_threaded,
                                      style='Dark.TButton')
        self.test_button.pack(side=tk.LEFT)

        # --- Temperature Slider Row ---
        temp_label = ttk.Label(main_frame, text="Temperature:", style='Dark.TLabel')
        temp_label.grid(row=3, column=0, padx=(0, 5), pady=5, sticky="w")

        temp_slider_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        temp_slider_frame.grid(row=3, column=1, columnspan=4, sticky="ew")

        self.temperature_slider = ttk.Scale(temp_slider_frame, from_=0.0, to=2.0, orient=tk.HORIZONTAL,
                                            command=lambda val: self.temperature_value_label.config(
                                                text=f"{float(val):.2f}"))
        self.temperature_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.temperature_value_label = ttk.Label(temp_slider_frame, text="0.70", style='Dark.TLabel', width=5)
        self.temperature_value_label.pack(side=tk.LEFT, padx=5)

        temperature_reset_button = ttk.Button(temp_slider_frame, text="Reset", style='Dark.TButton', width=6,
                                       command=lambda: self.temperature_slider.set(0.7))
        temperature_reset_button.pack(side=tk.LEFT, padx=5, pady=5)

        # --- Frequency Penalty Slider Row ---
        freq_pen_label = ttk.Label(main_frame, text="Frequency Penalty:", style='Dark.TLabel')
        freq_pen_label.grid(row=4, column=0, padx=(0, 5), pady=5, sticky="w")

        freq_slider_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        freq_slider_frame.grid(row=4, column=1, columnspan=4, sticky="ew")

        self.frequency_penalty_slider = ttk.Scale(freq_slider_frame, from_=-2.0, to=2.0, orient=tk.HORIZONTAL,
                                                  command=lambda val: self.freq_pen_value_label.config(
                                                      text=f"{float(val):.2f}"))
        self.frequency_penalty_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.freq_pen_value_label = ttk.Label(freq_slider_frame, text="0.00", style='Dark.TLabel', width=5)
        self.freq_pen_value_label.pack(side=tk.LEFT, padx=5)

        freq_reset_button = ttk.Button(freq_slider_frame, text="Reset", style='Dark.TButton', width=6,
                                       command=lambda: self.frequency_penalty_slider.set(0.0))
        freq_reset_button.pack(side=tk.LEFT, padx=5, pady=5)

        # --- Presence Penalty Slider Row ---
        pres_pen_label = ttk.Label(main_frame, text="Presence Penalty:", style='Dark.TLabel')
        pres_pen_label.grid(row=5, column=0, padx=(0, 5), pady=5, sticky="w")

        pres_slider_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        pres_slider_frame.grid(row=5, column=1, columnspan=4, sticky="ew")

        self.presence_penalty_slider = ttk.Scale(pres_slider_frame, from_=-2.0, to=2.0, orient=tk.HORIZONTAL,
                                                 command=lambda val: self.pres_pen_value_label.config(
                                                     text=f"{float(val):.2f}"))
        self.presence_penalty_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.pres_pen_value_label = ttk.Label(pres_slider_frame, text="0.00", style='Dark.TLabel', width=5)
        self.pres_pen_value_label.pack(side=tk.LEFT, padx=5)

        pres_reset_button = ttk.Button(pres_slider_frame, text="Reset", style='Dark.TButton', width=6,
                                       command=lambda: self.presence_penalty_slider.set(0.0))
        pres_reset_button.pack(side=tk.LEFT, padx=5, pady=5)

        # --- Load existing settings ---
        self.llm_url_entry.insert(0, self.controller.settings.get("base_url", ""))
        self.llm_model_entry.insert(0, self.controller.settings.get("model_name", ""))
        self.llm_key_entry.insert(0, self.controller.settings.get("api_key", ""))

        # --- Set initial slider values ---
        temp_val = self.controller.settings.get("temperature", 0.7)
        freq_pen_val = self.controller.settings.get("frequency_penalty", 0.0)
        pres_pen_val = self.controller.settings.get("presence_penalty", 0.0)
        self.temperature_slider.set(temp_val)
        self.temperature_value_label.config(text=f"{temp_val:.2f}")
        self.frequency_penalty_slider.set(freq_pen_val)
        self.freq_pen_value_label.config(text=f"{freq_pen_val:.2f}")
        self.presence_penalty_slider.set(pres_pen_val)
        self.pres_pen_value_label.config(text=f"{pres_pen_val:.2f}")

        # --- About Button in the bottom_frame ---
        about_button = ttk.Button(bottom_frame, text="About This App", command=self.controller.open_about_window,
                                  style='Dark.TButton')
        about_button.pack(side=tk.RIGHT)

        print("Settings Tab initialized!") # Placeholder

    def _save_api_settings(self, silent=False):
        """Handles the Save button click event in the Settings tab."""
        self.controller.settings['api_key'] = self.llm_key_entry.get().strip()
        self.controller.settings['model_name'] = self.llm_model_entry.get().strip()
        self.controller.settings['base_url'] = self.llm_url_entry.get().strip()
        self.controller.settings['temperature'] = self.temperature_slider.get()
        self.controller.settings['frequency_penalty'] = self.frequency_penalty_slider.get()
        self.controller.settings['presence_penalty'] = self.presence_penalty_slider.get()

        success = self.controller.persistence.save_settings(self.controller.settings)

        if success:
            if not silent:
                self.controller.update_status(f"""API settings saved successfully in \"{self.controller.persistence.get_settings_path()}\"""")
                messagebox.showinfo("Settings Saved", "Your API settings have been saved.")
        else:
            if not silent:
                self.controller.update_status("Error: Failed to save API settings.")
                messagebox.showerror("Error", "Could not save settings. Check console for details.")

    def _test_api_connection_threaded(self):
        """
        Tests the API connection in a separate thread.
        """
        threading.Thread(target=self._test_api_task, daemon=True).start()

    def center_window(self, parent):
        """Calculates the coordinates to center this window over its parent."""
        # Update idle tasks to make sure widgets have been drawn
        self.update_idletasks()

        # Get parent window's geometry
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # Get this window's requested size
        window_width = self.winfo_width()
        window_height = self.winfo_height()

        # Calculate the position
        pos_x = parent_x + (parent_width // 2) - (window_width // 2)
        pos_y = parent_y + (parent_height // 2) - (window_height // 2)

        # Set the geometry
        self.geometry(f"+{pos_x}+{pos_y}")

    def _test_api_task(self):
        """
        The actual task of testing the API connection.
        """
        self.controller.update_status("Testing API connection...")
        try:
            api_key = self.llm_key_entry.get().strip()
            base_url = self.llm_url_entry.get().strip()
            model_name = self.llm_model_entry.get().strip()

            if not all([api_key, base_url, model_name]):
                messagebox.showerror("Input Error", "Please fill in all API fields before testing.")
                self.controller.update_status("Test failed: Missing credentials.")
                return

            response = ai_utils.call_text_model(
                api_key=api_key,
                base_url=base_url,
                model=model_name,
                user_request="Hello!"
            )

            if response:
                messagebox.showinfo("Success", "API connection successful!")
                self.controller.update_status("API connection test successful.")
            else:
                messagebox.showerror("Failure", "API call failed. Check console for details.")
                self.controller.update_status("API connection test failed.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during the test: {e}")
            self.controller.update_status("API connection test failed.")
