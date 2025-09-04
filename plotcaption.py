import queue
import sys, os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, scrolledtext
import threading
from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD

from config import DEFAULT_PROMPT, MAX_THUMBNAIL_SIZE, INACTIVE_TAB_COLOR, DARK_COLOR, FIELD_BORDER_AREA_COLOR, \
    FIELD_BACK_COLOR, FIELD_FOREGROUND_COLOR, INSERT_COLOR, SELECT_BACKGROUND_COLOR, BUTTON_ACTIVATE_COLOR, \
    BUTTON_PRESSED_COLOR, BUTTON_COLOR, TEXT_BG_COLOR, INSERT_BACKGROUND_COLOR, PLACEHOLDER_FG_COLOR, COPY_IMAGE_FILE, \
    COPY_IMAGE_HOVER_FILE, CARD_USER_ROLE, CARD_CHAR_TO_ANALYZE, SD_CHAR_TO_ANALYZE, APP_VERSION
import ai_utils
from persistence_manager import PersistenceManager
from model_handler import ModelHandler
from prompts import generate_character_card_prompt, generate_stable_diffusion_prompt, discover_prompt_templates, _load_prompt_template
from ui_components import AutocompleteEntry
from vlm_profiles import VLMProfile, VLM_PROFILES

from enum import Enum, auto


class AppState(Enum):
    IDLE = auto()  # App just started, no model
    MODEL_LOADING = auto()  # A model is being downloaded/loaded
    MODEL_LOADED = auto()  # Model is loaded, but no image is present
    READY_TO_GENERATE = auto()  # Model and image are both loaded and ready
    GENERATING = auto()  # A generation task is running in the background
    READY_FOR_CARD_GENERATION = auto()
    READY_FOR_SD_GENERATION = auto()
    API_GENERATING = auto()

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class VLM_GUI(TkinterDnD.Tk):
    """
    A simple GUI for interacting with a Vision Language Model (VLM).

    Allows users to load a model from Hugging Face, provide an image via
    drag-and-drop, ask a question or give a prompt, and get a text-based
    response from the model.
    """



    def __init__(self):
        """
        Initializes the main application window and its components.
        """
        super().__init__()



        self.title(f"PLOT Captioning in detail v{APP_VERSION}")
        self.iconbitmap(resource_path('assets/plot_icon.ico'))
        self.geometry("900x750")
        self.configure(bg=DARK_COLOR)



        # --- Handlers ---
        self.model_handler = ModelHandler()
        self.persistence = PersistenceManager()
        self.settings = self.persistence.load_settings()

        # --- State Variables ---
        self.loaded_profile: VLMProfile = None
        self.image_path = None
        self.image_raw = None
        self.image_tk = None

        # --- STYLE CONFIGURATION (Based on your research doc) ---
        # 1. Create the Style object
        self.style = ttk.Style(self)

        # 2. MANDATORY: Switch to a configurable theme to escape Windows' native rendering
        self.style.theme_use('clam')

        # 4. Configure the colors for the different widget parts

        # Style for the container frame
        self.style.configure('Dark.TFrame', background=DARK_COLOR)
        # Style for the scrollbar
        self.style.configure('Dark.Vertical.TScrollbar', background=FIELD_BORDER_AREA_COLOR, troughcolor=DARK_COLOR)
        # This tells the scrollbar to keep its color even when disabled
        self.style.map('Dark.Vertical.TScrollbar',
                       background=[('disabled', FIELD_BORDER_AREA_COLOR)],
                       troughcolor=[('disabled', DARK_COLOR)])

        # Configure the main Notebook body
        self.style.configure('TNotebook',
                             background=DARK_COLOR,
                             bordercolor=DARK_COLOR,
                             borderwidth=0,
                             highlightthickness=0)  # <--- KILLS THE LINE ON THE RIGHT

        # Configure the Frames inside the tabs
        self.style.configure('Dark.TFrame', background=DARK_COLOR)

        # Configure the Entry
        self.style.configure('Dark.TEntry',
                             background=FIELD_BORDER_AREA_COLOR,  # Color of the border area (optional)
                             fieldbackground=FIELD_BACK_COLOR,  # The main background color of the text area
                             foreground=FIELD_FOREGROUND_COLOR,  # The text color
                             insertcolor=INSERT_COLOR,  # The blinking cursor color
                             borderwidth=0,  # To achieve the FLAT relief
                             selectbackground=SELECT_BACKGROUND_COLOR  # Color of selected text (optional but good)
                             )

        # Configure the Combobox
        self.style.configure('Dark.TCombobox',
                             fieldbackground=FIELD_BACK_COLOR,
                             background=FIELD_BORDER_AREA_COLOR,
                             foreground=FIELD_FOREGROUND_COLOR,
                             arrowcolor='white',
                             bordercolor=FIELD_BORDER_AREA_COLOR,
                             selectbackground=SELECT_BACKGROUND_COLOR,
                             padding=5)
        self.style.map('Dark.TCombobox',
                       fieldbackground=[('readonly', FIELD_BACK_COLOR)],
                       foreground=[('readonly', FIELD_FOREGROUND_COLOR)],
                       selectbackground=[('readonly', SELECT_BACKGROUND_COLOR)],
                       selectforeground=[('readonly', FIELD_FOREGROUND_COLOR)])

        # Configure the Tab buttons themselves
        self.style.configure('TNotebook.Tab',
                             foreground=FIELD_FOREGROUND_COLOR,
                             padding=[10, 5],
                             background=INACTIVE_TAB_COLOR,
                             borderwidth=0)

        # Buttons Styles
        self.style.configure('Dark.TButton',
                             background=BUTTON_COLOR,
                             foreground='white',
                             padding=6,
                             relief='flat')  # Makes the button flat

        # This is the style we are updating!
        self.style.configure('Icon.TButton',
                             background=DARK_COLOR,
                             foreground=FIELD_FOREGROUND_COLOR,
                             relief='flat',
                             font=('Segoe UI Emoji', 10), # emoji fontgit
                             padding=[5, 2, 5, 4])

        self.style.map('Icon.TButton',
                       background=[('active', FIELD_BORDER_AREA_COLOR),
                                   ('pressed', BUTTON_PRESSED_COLOR)])

        # Optional: Change color when the mouse hovers or clicks
        self.style.map('Dark.TButton',
                       background=[('active', BUTTON_ACTIVATE_COLOR), ('pressed', BUTTON_PRESSED_COLOR)])

        # Add 'focuscolor' to the map.
        self.style.map('TNotebook.Tab',
                       background=[('selected', DARK_COLOR)],
                       foreground=[('selected', FIELD_FOREGROUND_COLOR)],
                       focuscolor=[('selected', DARK_COLOR)])  # <--- ADD THIS LINE

        self.style.configure('Placeholder.TLabel', background=TEXT_BG_COLOR, foreground=PLACEHOLDER_FG_COLOR)

        # Add this new style for our text box frames
        self.style.configure('Border.TFrame', background=TEXT_BG_COLOR,
                             borderwidth=1, relief='solid', bordercolor=FIELD_BORDER_AREA_COLOR)

        # --- WIDGET CREATION ---
        # (Your existing code for creating the notebook and frames is correct)
        # Just make sure to apply the 'Dark.TFrame' style to your frames:
        # 1. Create the Notebook as an instance variable
        self.tab_control = ttk.Notebook(self)

        # 2. Create the Frames and APPLY THE NEW STYLE
        self.tab1_frame = ttk.Frame(self.tab_control, style='Dark.TFrame')
        self.tab2_frame = ttk.Frame(self.tab_control, style='Dark.TFrame')
        self.tab3_frame = ttk.Frame(self.tab_control, style='Dark.TFrame')

        # 3. Add the Frames to the Notebook as tabs
        self.tab_control.add(self.tab1_frame, text='Caption')
        self.tab_control.add(self.tab2_frame, text='Generate')
        self.tab_control.add(self.tab3_frame, text='Settings')


        # --- Status Bar ---
        # Create the status bar first and pack it to the bottom of the window
        self.style.configure('Dark.TLabel', background=DARK_COLOR, foreground="white")
        self.status_bar = ttk.Label(self, text="Ready. Please load a model.", relief=tk.FLAT, anchor=tk.W, background=DARK_COLOR, foreground="white")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Tab Control ---
        # NOW, pack the tab control last, letting it fill the remaining space
        self.tab_control.pack(expand=True, fill="both", padx=0, pady=0)

        # --- Load Icon Images ---
        self.copy_icon = tk.PhotoImage(file=resource_path(COPY_IMAGE_FILE))
        self.copy_icon_hover = tk.PhotoImage(file=resource_path(COPY_IMAGE_HOVER_FILE))

        # --- Prompt Template Discovery ---
        prompt_templates = discover_prompt_templates()
        self.card_prompt_templates = prompt_templates.get("card_prompts", ["NSFW"])
        self.sd_prompt_templates = prompt_templates.get("sd_prompts", ["NSFW"])

        # --- Create Frame for LLM Tab ---
        self.main_llm_frame = ttk.Frame(self.tab2_frame, style='Dark.TFrame', padding=10)
        self.main_llm_frame.pack(expand=True, fill="both")

        # --- Create Comboboxes ---
        self.card_template_combo = ttk.Combobox(
            self.main_llm_frame,
            values=self.card_prompt_templates,
            state='readonly',
            style='Dark.TCombobox'
        )
        self.card_template_combo.bind("<<ComboboxSelected>>", lambda event: self._on_prompt_template_selected(event, 'card'))

        self.sd_template_combo = ttk.Combobox(
            self.main_llm_frame,
            values=self.sd_prompt_templates,
            state='readonly',
            style='Dark.TCombobox'
        )
        self.sd_template_combo.bind("<<ComboboxSelected>>", lambda event: self._on_prompt_template_selected(event, 'sd'))

        # --- UI Setup ---
        self._setup_widgets_vlm(self.tab1_frame)
        self._setup_widgets_llm(self.tab2_frame)
        self._setup_widgets_settings(self.tab3_frame)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # --- Load Last Used Templates ---
        last_card_template = self.settings.get("last_card_template", "NSFW")
        last_sd_template = self.settings.get("last_sd_template", "NSFW")

        if last_card_template in self.card_prompt_templates:
            self.card_template_combo.set(last_card_template)
        else:
            self.card_template_combo.set("NSFW")

        if last_sd_template in self.sd_prompt_templates:
            self.sd_template_combo.set(last_sd_template)
        else:
            self.sd_template_combo.set("NSFW")

        # Manually trigger the loading of the content for the default/saved templates
        self._on_prompt_template_selected(None, 'card')
        self._on_prompt_template_selected(None, 'sd')

        # Set initial slider values from loaded settings
        temp_val = self.settings.get("temperature", 0.7)
        freq_pen_val = self.settings.get("frequency_penalty", 0.0)
        pres_pen_val = self.settings.get("presence_penalty", 0.0)

        self.temperature_slider.set(temp_val)
        self.temperature_value_label.config(text=f"{temp_val:.2f}")
        self.frequency_penalty_slider.set(freq_pen_val)
        self.freq_pen_value_label.config(text=f"{freq_pen_val:.2f}")
        self.presence_penalty_slider.set(pres_pen_val)
        self.pres_pen_value_label.config(text=f"{pres_pen_val:.2f}")

        self.current_state = None
        self.set_state(AppState.IDLE)

        self.current_state = None  # Initialize it
        self.set_state(AppState.IDLE)  # Set the initial state

    def _on_prompt_template_selected(self, event, prompt_type):
        """
        Handles the event when a new prompt template is selected.
        Triggers the repopulation of the corresponding prompt text box,
        ensuring all updates go through the placeholder replacement logic.
        """
        # Get the current data from the UI.
        # These will be empty strings if no data is present.
        final_caption = self.output_caption_text.get("1.0", tk.END).strip()
        final_tags = self.output_tags_text.get("1.0", tk.END).strip()

        if prompt_type == 'card':
            # Always call _populate_generate_card. It will handle generating
            # the prompt with or without data to fill the placeholders.
            self._populate_generate_card(final_caption, final_tags)
        elif prompt_type == 'sd':
            # Always call _populate_generate_SD, which also needs the card text.
            final_card = self.card_output_text_box.get("1.0", tk.END).strip()
            self._populate_generate_SD(final_caption, final_tags, final_card)

    def _on_closing(self):
        """
        Handles the application window closing event.
        Saves the complete application state and closes the application.
        """
        # Update settings with the final state from the UI
        self.settings['last_used_vlm'] = self.model_selection_combo.get()
        self.settings['last_card_template'] = self.card_template_combo.get()
        self.settings['last_sd_template'] = self.sd_template_combo.get()

        # Save all settings
        self.persistence.save_settings(self.settings)

        self.destroy()

    def _on_copy_enter(self, event):
        """Changes the button image when the mouse enters."""
        event.widget.config(image=self.copy_icon_hover)

    def _on_copy_leave(self, event):
        """Changes the button image back when the mouse leaves."""
        event.widget.config(image=self.copy_icon)

    def _create_labeled_textbox(self, parent, label_text, grid_row, grid_column, copy_command=None):
        """
        Creates and grids a labeled Text widget with an optional, right-aligned copy button.
        """
        # --- Create the Label Frame (this will hold the label and optional button) ---
        label_frame = ttk.Frame(parent, style='Dark.TFrame')
        label_frame.grid(row=grid_row, column=grid_column, padx=5, pady=(5, 0), sticky="ew")

        label = ttk.Label(label_frame, text=label_text, style='Dark.TLabel')
        label.pack(side=tk.LEFT)

        # --- If a copy command is provided, create the button! ---
        if copy_command:
            copy_button = ttk.Button(label_frame, image=self.copy_icon, command=copy_command, style='Icon.TButton')
            copy_button.pack(side=tk.RIGHT)
            copy_button.bind("<Enter>", self._on_copy_enter)
            copy_button.bind("<Leave>", self._on_copy_leave)

        # --- Create the Text Box Frame (no changes here) ---
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

    def _setup_widgets_llm(self, parent_frame):
        # The main_frame is now self.main_llm_frame, created in __init__
        self.main_llm_frame.columnconfigure(0, weight=1)
        self.main_llm_frame.columnconfigure(1, weight=1)
        self.main_llm_frame.rowconfigure(2, weight=1) # Adjusted row for text box
        self.main_llm_frame.rowconfigure(5, weight=1) # Adjusted row for text box

        # --- Place Comboboxes ---
        self.card_template_combo.grid(row=0, column=0, padx=5, pady=(0, 5), sticky="ew")
        self.sd_template_combo.grid(row=0, column=1, padx=5, pady=(0, 5), sticky="ew")

        # --- Input boxes don't get a copy button ---
        self.card_text_box = self._create_labeled_textbox(
            parent=self.main_llm_frame,
            label_text="Character card Prompt:",
            grid_row=1, # Adjusted row
            grid_column=0
        )

        self.sd_text_box = self._create_labeled_textbox(
            parent=self.main_llm_frame,
            label_text="SD Prompt:",
            grid_row=1, # Adjusted row
            grid_column=1
        )

        # --- Output boxes DO get a copy button! ---
        self.card_output_text_box = self._create_labeled_textbox(
            parent=self.main_llm_frame,
            label_text="Output Character Card:",
            grid_row=4, # Adjusted row
            grid_column=0,
            copy_command=self._copy_card_output_to_clipboard
        )

        self.sd_output_text_box = self._create_labeled_textbox(
            parent=self.main_llm_frame,
            label_text="Output SD Prompt:",
            grid_row=4, # Adjusted row
            grid_column=1,
            copy_command=self._copy_sd_output_to_clipboard
        )

        # ... (the rest of the function with the generate buttons is the same) ...
        self.card_generate_button = ttk.Button(self.main_llm_frame, text="Generate Card", command=self._generate_card_threaded,
                                               style='Dark.TButton')
        self.card_generate_button.grid(row=3, column=0, sticky="ns", pady=5) # Adjusted row
        self.sd_generate_button = ttk.Button(self.main_llm_frame, text="Generate SD", command=self._generate_sd_prompt_threaded,
                                             style='Dark.TButton')
        self.sd_generate_button.grid(row=3, column=1, sticky="ns", pady=5) # Adjusted row


    def _generate_card_threaded(self):
        """
        Handles the 'Generate Card' button click event in a separate thread.
        """
        self.set_state(AppState.API_GENERATING)
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
        self.set_state(AppState.API_GENERATING)
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
            # 1. Get credentials and prompt
            api_key = self.llm_key_entry.get().strip()
            base_url = self.llm_url_entry.get().strip()
            model_name = self.llm_model_entry.get().strip()
            prompt = input_widget.get("1.0", tk.END).strip()
            temperature = round(self.temperature_slider.get(), 2)
            frequency_penalty = round(self.frequency_penalty_slider.get(), 2)
            presence_penalty = round(self.presence_penalty_slider.get(), 2)

            if not all([api_key, base_url, model_name, prompt]):
                q.put(("error", "API credentials, model, and prompt cannot be empty."))
                q.put(("done", task_type))
                return

            # 2. Make the API call
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

            # 3. Update the UI with the result
            if response:
                q.put(("update_output", (output_widget, response)))
                q.put(("status", "API call successful."))
            else:
                q.put(("error", "API call failed. No response received."))

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

            if message_type == "status":
                self.update_status(data)
            elif message_type == "update_output":
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
                    final_caption = self.output_caption_text.get("1.0", tk.END).strip()
                    final_tags = self.output_tags_text.get("1.0", tk.END).strip()
                    final_card = self.card_output_text_box.get("1.0", tk.END).strip()
                    self._populate_generate_SD(final_caption, final_tags, final_card)
                    self.set_state(AppState.READY_FOR_SD_GENERATION)
                else:  # The SD prompt finished
                    self.set_state(AppState.READY_FOR_SD_GENERATION)
                return  # Stop the queue-checking loop

        except queue.Empty:
            pass

        self.after(100, self._process_api_queue)

    def _setup_widgets_settings(self, parent_element):
        """Creates and arranges all settings tab widgets."""
        parent_element.config(padding=15)
        top_frame = ttk.Frame(parent_element, style='Dark.TFrame')
        top_frame.pack(fill=tk.X, pady=(0, 10))
        top_frame.columnconfigure(1, weight=1)
        top_frame.columnconfigure(3, weight=1)

        # API URL
        url_label = ttk.Label(top_frame, text="API Url:", style='Dark.TLabel')
        url_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.llm_url_entry = ttk.Entry(top_frame, style='Dark.TEntry')
        self.llm_url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # API Key
        llm_key_label = ttk.Label(top_frame, text="API Key:", style='Dark.TLabel')
        llm_key_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.llm_key_entry = ttk.Entry(top_frame, style='Dark.TEntry', show='*')
        self.llm_key_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # Model Name
        llm_model_label = ttk.Label(top_frame, text="Model:", style='Dark.TLabel')
        llm_model_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.llm_model_entry = ttk.Entry(top_frame, style='Dark.TEntry')
        self.llm_model_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # --- Temperature Slider ---
        temp_label = ttk.Label(top_frame, text="Temperature:", style='Dark.TLabel')
        temp_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.temperature_value_label = ttk.Label(top_frame, text="0.7", style='Dark.TLabel')
        self.temperature_value_label.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        self.temperature_slider = ttk.Scale(top_frame, from_=0.0, to=2.0, orient=tk.HORIZONTAL,
                                            command=lambda val: self.temperature_value_label.config(text=f"{float(val):.2f}"))
        self.temperature_slider.grid(row=2, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

        # --- Frequency Penalty Slider ---
        freq_pen_label = ttk.Label(top_frame, text="Frequency Penalty:", style='Dark.TLabel')
        freq_pen_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.freq_pen_value_label = ttk.Label(top_frame, text="0.0", style='Dark.TLabel')
        self.freq_pen_value_label.grid(row=3, column=3, padx=5, pady=5, sticky="w")
        self.frequency_penalty_slider = ttk.Scale(top_frame, from_=-2.0, to=2.0, orient=tk.HORIZONTAL,
                                                    command=lambda val: self.freq_pen_value_label.config(text=f"{float(val):.2f}"))
        self.frequency_penalty_slider.grid(row=3, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

        # --- Presence Penalty Slider ---
        pres_pen_label = ttk.Label(top_frame, text="Presence Penalty:", style='Dark.TLabel')
        pres_pen_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.pres_pen_value_label = ttk.Label(top_frame, text="0.0", style='Dark.TLabel')
        self.pres_pen_value_label.grid(row=4, column=3, padx=5, pady=5, sticky="w")
        self.presence_penalty_slider = ttk.Scale(top_frame, from_=-2.0, to=2.0, orient=tk.HORIZONTAL,
                                                     command=lambda val: self.pres_pen_value_label.config(text=f"{float(val):.2f}"))
        self.presence_penalty_slider.grid(row=4, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

        # Load existing settings
        self.llm_url_entry.insert(0, self.settings.get("base_url", ""))
        self.llm_model_entry.insert(0, self.settings.get("model_name", ""))
        self.llm_key_entry.insert(0, self.settings.get("api_key", ""))

        # --- Buttons ---
        button_frame = ttk.Frame(top_frame, style='Dark.TFrame')
        button_frame.grid(row=1, column=3, padx=5, pady=5, sticky="e")
        self.save_button = ttk.Button(button_frame, text="Save", command=self._save_api_settings, style='Dark.TButton')
        self.save_button.pack(side=tk.LEFT, padx=(0, 5))
        self.test_button = ttk.Button(button_frame, text="Test", command=self._test_api_connection_threaded, style='Dark.TButton')
        self.test_button.pack(side=tk.LEFT)

    def _save_api_settings(self, silent=False):
        """Handles the Save button click event in the Settings tab."""
        self.settings['api_key'] = self.llm_key_entry.get().strip()
        self.settings['model_name'] = self.llm_model_entry.get().strip()
        self.settings['base_url'] = self.llm_url_entry.get().strip()
        self.settings['temperature'] = self.temperature_slider.get()
        self.settings['frequency_penalty'] = self.frequency_penalty_slider.get()
        self.settings['presence_penalty'] = self.presence_penalty_slider.get()

        success = self.persistence.save_settings(self.settings)

        if success:
            if not silent:
                self.update_status("API settings saved successfully.")
                messagebox.showinfo("Settings Saved", "Your API settings have been saved.")
        else:
            if not silent:
                self.update_status("Error: Failed to save API settings.")
                messagebox.showerror("Error", "Could not save settings. Check console for details.")

    def _test_api_connection_threaded(self):
        """
        Tests the API connection in a separate thread.
        """
        threading.Thread(target=self._test_api_task, daemon=True).start()

    def _test_api_task(self):
        """
        The actual task of testing the API connection.
        """
        self.update_status("Testing API connection...")
        try:
            api_key = self.llm_key_entry.get().strip()
            base_url = self.llm_url_entry.get().strip()
            model_name = self.llm_model_entry.get().strip()

            if not all([api_key, base_url, model_name]):
                messagebox.showerror("Input Error", "Please fill in all API fields before testing.")
                self.update_status("Test failed: Missing credentials.")
                return

            response = ai_utils.call_text_model(
                api_key=api_key,
                base_url=base_url,
                model=model_name,
                user_request="hello!"
            )

            if response:
                messagebox.showinfo("Success", "API connection successful!")
                self.update_status("API connection test successful.")
            else:
                messagebox.showerror("Failure", "API call failed. Check console for details.")
                self.update_status("API connection test failed.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during the test: {e}")
            self.update_status("API connection test failed.")

    def _populate_generate_card(self, caption: str, tags: str):
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

    def _populate_generate_SD(self, caption: str, tags: str, character_card: str):
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

    def _on_model_selected(self, event=None):
        """
        Handles the event when a new model is selected from the Combobox.
        Loads the corresponding profile and updates the UI.
        """
        model_name = self.model_selection_combo.get()
        self.loaded_profile = VLM_PROFILES.get(model_name)

        if self.loaded_profile:
            # Update the prompt text box with the prompt from the selected profile
            self.caption_prompt.delete("1.0", tk.END)
            self.caption_prompt.insert(tk.END, self.loaded_profile.prompt_caption)
        else:
            # This case should ideally not happen with a readonly combobox
            messagebox.showerror("Profile Error", f"No VLM profile defined for '{model_name}'.")
            self.caption_prompt.delete("1.0", tk.END)

    def _setup_widgets_vlm(self, parent_element):
        """Creates and arranges all the VLM tab widgets."""

        main_frame = ttk.Frame(parent_element, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # --- Top Frame for Model Control ---
        top_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        top_frame.pack(fill=tk.X, pady=(0, 10))

        self.load_button = ttk.Button(top_frame, text="Load Model", command=self.load_model_threaded, style='Dark.TButton', width=15)
        self.load_button.pack(side=tk.LEFT, padx=(0, 10))

        self.unload_button = ttk.Button(top_frame, text="Unload Model", command=self.unload_model, style='Dark.TButton', width=15)
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
        last_vlm = self.settings.get('last_used_vlm')
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
        self.image_label = ttk.Label(content_frame, text="Drag & Drop an Image Here", style='Placeholder.TLabel', relief=tk.SOLID)
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
        self.caption_prompt = tk.Text(right_panel, height=4, bg=TEXT_BG_COLOR, fg=FIELD_FOREGROUND_COLOR, relief=tk.FLAT,
                                      insertbackground=INSERT_BACKGROUND_COLOR)
        self.caption_prompt.grid(row=1, column=0, sticky="ew", pady=(5, 10))
        # self.caption_prompt.insert(tk.END, DEFAULT_PROMPT) # This is now handled by _on_model_selected
        self._on_model_selected() # Call this now that caption_prompt exists

        # Row 2: Generate Button (fixed height)
        self.generate_button = ttk.Button(right_panel, text="Generate Description", command=self.generate_threaded,
                                          style='Dark.TButton')
        self.generate_button.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.generate_button.config(state=tk.DISABLED)


        # --- NEW: Output Caption Label with Copy Button ---
        caption_label_frame = ttk.Frame(right_panel, style='Dark.TFrame')
        caption_label_frame.grid(row=3, column=0, sticky="ew")

        output_caption_label = ttk.Label(caption_label_frame, text="Model Output:", style='Dark.TLabel')
        output_caption_label.pack(side=tk.LEFT)  # This stays on the left

        self.copy_caption_button = ttk.Button(caption_label_frame, image=self.copy_icon, command=self.copy_to_clipboard,
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

        # --- NEW: Output Tags Label with Copy Button ---
        tags_label_frame = ttk.Frame(right_panel, style='Dark.TFrame')
        tags_label_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0))

        output_tags_label = ttk.Label(tags_label_frame, text="Booru Tags Output:", style='Dark.TLabel')
        output_tags_label.pack(side=tk.LEFT)  # This stays on the left

        self.copy_tags_button = ttk.Button(tags_label_frame, image=self.copy_icon, command=self.copy_tags_to_clipboard,
                                           style='Icon.TButton')
        self.copy_tags_button.pack(side=tk.RIGHT)  # <-- CHANGE THIS to tk.RIGHT
        self.copy_tags_button.bind("<Enter>", self._on_copy_enter)
        self.copy_tags_button.bind("<Leave>", self._on_copy_leave)

        # Row 6: Output Tags Text
        # NEW CODE for the tags text box
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



    def handle_drop(self, event):
        """
        Handles the drag-and-drop file event.
        """
        filepath = event.data.strip('{}')
        if filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
            self.image_path = filepath
            self.load_and_display_image()
        else:
            messagebox.showerror("Error", "Invalid file type. Please drop a valid image file.")

    def load_and_display_image(self):
        """
        Loads an image from the given path, displays it as a thumbnail,
        and updates the application state. If a model is already loaded,
        it transitions to the READY_TO_GENERATE state.
        """
        try:
            self.image_raw = Image.open(self.image_path).convert("RGB")
            display_image = self.image_raw.copy()
            display_image.thumbnail(MAX_THUMBNAIL_SIZE)
            self.image_tk = ImageTk.PhotoImage(display_image)

            self.image_label.config(image=self.image_tk, text="")

            if self.current_state == AppState.MODEL_LOADED:
                self.set_state(AppState.READY_TO_GENERATE)
            else:
                # If the model isn't loaded yet, just update the status
                self.update_status("Image loaded. Now load a model.")

        except Exception as e:
            messagebox.showerror("Image Error", f"Failed to load image: {e}")
            self.image_path = None

    def load_model_threaded(self):
        """
        Initiates model loading in a separate thread. The model to be loaded
        is determined by the current selection in the combobox.
        Transitions the UI to the MODEL_LOADING state.
        """
        model_name = self.model_selection_combo.get()
        if not model_name:
            messagebox.showerror("Error", "No model selected.")
            return

        # The profile is already loaded by _on_model_selected, so we just use it.
        if not self.loaded_profile:
            messagebox.showerror("Profile Error", f"Could not find a loaded profile for '{model_name}'.")
            return

        self.set_state(AppState.MODEL_LOADING)
        threading.Thread(target=self._load_model_task, args=(self.loaded_profile.model_id,), daemon=True).start()

    def _load_model_task(self, model_id: str):
        """
        The actual task of loading the model, executed in a separate thread.
        Updates the state to MODEL_LOADED on success, or READY_TO_GENERATE
        if an image is already present. Updates to IDLE on failure.

        Args:
            model_id (str): The Hugging Face ID of the model to load.
        """
        try:
            print(model_id)
            print("Loading model thread...")
            self.model_handler.load_model(self.loaded_profile)
            # The history manager is no longer the source of truth for VLM models.
            # The VLM_PROFILES dictionary is. We leave the history logic for now
            # as it might be used by other parts of the application, but we don't
            # add VLM models to it anymore.
            # self.history_manager.add_model_to_history(model_id)
            # self.model_name_entry.set_completions(self.history_manager.get_history())

            if self.image_path:
                self.set_state(AppState.READY_TO_GENERATE)
            else:
                self.set_state(AppState.MODEL_LOADED)

        except Exception as e:
            print(e)
            messagebox.showerror("Model Loading Error",
                                 f"Failed to load model: {e}\n\nCheck the model name, your internet connection, and ensure you have enough VRAM/RAM.")
            self.set_state(AppState.IDLE)

    def unload_model(self):
        """
        Unloads the model and resets the GUI to the IDLE state.
        """
        self.model_handler.unload_model()
        self.set_state(AppState.IDLE)

    # def generate_threaded(self):
    #     """
    #     Initiates text generation in a separate thread.
    #     """
    #     prompt = self.llm_url_text.get("1.0", tk.END).strip()
    #     if not prompt:
    #         messagebox.showwarning("Input Error", "Prompt cannot be empty.")
    #         return
    #
    #     self.update_status("Generating text...")
    #     self.generate_button.config(state=tk.DISABLED, text="Generating...")
    #     self.copy_button.config(state=tk.DISABLED)
    #
    #     threading.Thread(target=self._generate_task, args=(prompt,), daemon=True).start()

    def set_state(self, new_state: AppState):
        """
        Manages all UI element states based on the application's current state.
        This is the single source of truth for the UI's appearance and interactivity.

        Args:
            new_state (AppState): The state to transition to.
        """
        self.current_state = new_state
        # Default states
        self.load_button.config(state='disabled')
        self.load_button.config(text="Load")
        self.unload_button.config(state='disabled')
        self.generate_button.config(state='disabled', text="Generate Description")
        self.copy_caption_button.config(state='enabled')
        self.copy_tags_button.config(state='enabled')
        self.model_selection_combo.config(state='disabled')
        self.card_generate_button.config(state='disabled')
        self.sd_generate_button.config(state='disabled')
        self.card_text_box.config(state='disabled')
        self.sd_text_box.config(state='disabled')
        self.test_button.config(state='enabled')

        # --- Configure UI based on the new state ---
        if self.current_state == AppState.IDLE:
            self.load_button.config(state='normal')
            self.model_selection_combo.config(state='readonly')
            self.update_status("Ready. Please load a model.")

        elif self.current_state == AppState.MODEL_LOADING:
            self.load_button.config(text="Loading...")
            self.update_status(f"Loading model: {self.model_selection_combo.get()}...")


        elif self.current_state == AppState.MODEL_LOADED:
            self.load_button.config(text="Loaded")
            self.unload_button.config(state='normal')
            self.model_selection_combo.config(state='disabled')
            self.test_button.config(state='enabled')
            self.update_status("Model loaded. Please drop an image.")

        elif self.current_state == AppState.READY_TO_GENERATE:
            self.load_button.config(text="Loaded")
            self.unload_button.config(state='normal')
            self.generate_button.config(state='normal')
            self.model_selection_combo.config(state='disabled')
            self.update_status("Ready to generate.")

        elif self.current_state == AppState.GENERATING:
            self.generate_button.config(text="Generating...")
            self.unload_button.config(state='disabled')
            self.model_selection_combo.config(state='disabled')
            self.test_button.config(state='disabled')
            self.update_status("Generating, please wait...")

        elif self.current_state == AppState.READY_FOR_CARD_GENERATION:
            self.generate_button.config(state='normal')
            self.card_text_box.config(state='normal')
            self.card_generate_button.config(state='normal')
            self.sd_text_box.config(state='disabled')
            self.sd_generate_button.config(state='normal')
            self.copy_caption_button.config(state='normal')
            self.copy_tags_button.config(state='normal')
            self.unload_button.config(state='normal')
            self.test_button.config(state='enabled')
            self.update_status("Character Card prompt ready. Click 'Generate Card'.")

        elif self.current_state == AppState.READY_FOR_SD_GENERATION:
            self.generate_button.config(state='normal')
            self.card_text_box.config(state='normal')
            self.card_generate_button.config(state='normal')
            self.sd_text_box.config(state='normal')
            self.sd_generate_button.config(state='normal')
            self.copy_caption_button.config(state='normal')
            self.copy_tags_button.config(state='normal')
            self.unload_button.config(state='normal')
            self.test_button.config(state='enabled')
            self.update_status("Character Card generated. SD prompt is ready.")

        elif self.current_state == AppState.API_GENERATING:
            self.card_generate_button.config(state='disabled')
            self.sd_generate_button.config(state='disabled')
            self.unload_button.config(state='normal')
            self.test_button.config(state='disabled')
            self.update_status("Generating via API...")



    def generate_threaded(self):
        """
        Initiates a multi-step generation task in a separate thread.
        Transitions the UI to the GENERATING state.
        """
        prompt = self.caption_prompt.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Input Error", "Prompt cannot be empty.")
            return

        self.set_state(AppState.GENERATING)

        # Create a queue to communicate with the worker thread
        self.task_queue = queue.Queue()

        # Start the worker thread, passing it the queue
        threading.Thread(target=self._generate_task_chain, args=(prompt, self.task_queue), daemon=True).start()

        # Start a loop to check the queue for updates from the thread
        self.after(100, self._process_queue)

    def _generate_task_chain(self, prompt, q):
        """
        The actual task of generating in a sequence. Runs in a worker thread.
        """
        if not self.loaded_profile:
            q.put(("error", "No model profile loaded. Cannot generate."))
            q.put(("status", "Generation failed."))
            q.put(("done", None))
            return
        try:

            # --- TASK 1: Generate and Parse Caption ---
            q.put(("status", "Generating description (step 1/2)..."))
            raw_caption_output = self.model_handler.generate_description(self.loaded_profile, prompt, self.image_raw)

            # Use the caption_parser here!
            parsed_caption_data = self.loaded_profile.caption_parser(raw_caption_output)
            q.put(("update_caption", parsed_caption_data.get("output", "")))

            q.put(("status", "Generating booru tags. (step 2/2)..."))

            # --- TASK 2: Generate and Parse Tags ---
            tags_prompt = self.loaded_profile.prompt_tags
            raw_tags_output = self.model_handler.generate_description(self.loaded_profile, tags_prompt, self.image_raw)


            # Use the tags_parser here!
            parsed_tags_data = self.loaded_profile.tags_parser(raw_tags_output)
            q.put(("update_tags",
                   parsed_tags_data.get("output", "")))

            q.put(("status", "Generation complete."))
        except Exception as e:
            # If anything fails, put an error message in the queue
            q.put(("error", f"An error occurred during generation: {e}"))
            q.put(("status", "Generation failed."))
        finally:
            # Put a special "DONE" signal in the queue so the UI knows to re-enable buttons
            q.put(("done", None))

    def _process_queue(self):
        """
        Checks the queue for messages from the worker thread and updates the UI.
        """
        try:
            # Check the queue for a new message without blocking
            message_type, data = self.task_queue.get_nowait()

            # Process the message based on its type
            if message_type == "status":
                self.update_status(data)
            elif message_type == "update_caption":
                self.update_caption_text(data)  # Update your first text box
            elif message_type == "update_tags":
                self.update_tags_text(data) # Update your second text box
                pass  # Replace with your actual UI update
            elif message_type == "error":
                print(data)
                messagebox.showerror("Generation Error", data)
            elif message_type == "done":
                # The chain is finished, populate the next tab
                # The chain is finished, populate the next tab
                final_caption = self.output_caption_text.get("1.0", tk.END).strip()
                final_tags = self.output_tags_text.get("1.0", tk.END).strip()
                # Set the state first to enable the text boxes
                self.set_state(AppState.READY_FOR_CARD_GENERATION)
                # Now populate them
                self._populate_generate_card(final_caption, final_tags)
                return  # Stop the queue-checking loop

        except queue.Empty:
            # If the queue is empty, do nothing and check again later
            pass

        # Schedule this method to run again after 100ms
        self.after(100, self._process_queue)

    def _generate_task(self, prompt):
        """
        The actual task of generating the description.
        """
        try:
            response = self.model_handler.generate_description(prompt, self.image_raw)
            self.update_caption_text(response)
            self.update_status("Generation complete.")
            self.copy_caption_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Generation Error", f"An error occurred during generation: {e}")
            self.update_status("Generation failed.")
        finally:
            self.generate_button.config(state=tk.NORMAL, text="Generate Description")

    def update_status(self, text):
        """Updates the status bar text."""
        self.status_bar.config(text=text)

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

    def copy_to_clipboard(self):
        """Copies the output text to the clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.output_caption_text.get("1.0", tk.END))
        self.update_status("Output copied to clipboard.")

    def copy_tags_to_clipboard(self):
        """Copies the tags output text to the clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.output_tags_text.get("1.0", tk.END))
        self.update_status("Tags copied to clipboard.")

    def _copy_card_output_to_clipboard(self):
        """Copies the character card output to the clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.card_output_text_box.get("1.0", tk.END))
        self.update_status("Character card output copied to clipboard.")

    def _copy_sd_output_to_clipboard(self):
        """Copies the SD prompt output to the clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.sd_output_text_box.get("1.0", tk.END))
        self.update_status("SD prompt output copied to clipboard.")


if __name__ == "__main__":

    app = VLM_GUI()
    app.mainloop()
