import queue
import sys, os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, scrolledtext
import threading
from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD

from about_window import AboutWindow
from assets_utils import resource_path

from config import MAX_THUMBNAIL_SIZE, INACTIVE_TAB_COLOR, DARK_COLOR, FIELD_BORDER_AREA_COLOR, \
    FIELD_BACK_COLOR, FIELD_FOREGROUND_COLOR, INSERT_COLOR, SELECT_BACKGROUND_COLOR, BUTTON_ACTIVATE_COLOR, \
    BUTTON_PRESSED_COLOR, BUTTON_COLOR, TEXT_BG_COLOR, INSERT_BACKGROUND_COLOR, PLACEHOLDER_FG_COLOR, COPY_IMAGE_FILE, \
    COPY_IMAGE_HOVER_FILE, CARD_USER_ROLE, CARD_CHAR_TO_ANALYZE, SD_CHAR_TO_ANALYZE, APP_VERSION, \
    ACCEPTED_IMAGE_EXTENSIONS
import ai_utils
from persistence_manager import PersistenceManager
from model_handler import ModelHandler
from prompts import generate_character_card_prompt, generate_stable_diffusion_prompt, discover_prompt_templates, _load_prompt_template
from ui_components import AutocompleteEntry
from ui_tabs import CaptionTab, GenerateTab, SettingsTab
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

        # Application title, icon, window size
        self.title(f"PlotCaption v{APP_VERSION}")
        #self.iconbitmap(resource_path('assets/plot_icon.ico')

        # Create a PhotoImage object from PNG file
        icon_image = tk.PhotoImage(file=resource_path('assets/plot-icon.png'))
        # Set it as the window icon for this window and future top-level windows
        self.iconphoto(True, icon_image)

        self.geometry("900x750")
        self.configure(bg=DARK_COLOR)

        # Handlers
        self.model_handler = ModelHandler()
        self.persistence = PersistenceManager()
        self.settings = self.persistence.load_settings()

        # State Variables
        self.loaded_profile: VLMProfile = None
        self.image_path = None
        self.image_raw = None
        self.image_tk = None

        # STYLE CONFIGURATION using config values
        # Create the Style object
        self.style = ttk.Style(self)

        # Switch to a configurable theme to escape Windows' native rendering
        self.style.theme_use('clam')

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
                             relief='flat')

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

        # Change color when the mouse hovers or clicks
        self.style.map('Dark.TButton',
                       background=[('active', BUTTON_ACTIVATE_COLOR), ('pressed', BUTTON_PRESSED_COLOR)])

        # Add 'focuscolor' to the map.
        self.style.map('TNotebook.Tab',
                       background=[('selected', DARK_COLOR)],
                       foreground=[('selected', FIELD_FOREGROUND_COLOR)],
                       focuscolor=[('selected', DARK_COLOR)])

        self.style.configure('Placeholder.TLabel', background=TEXT_BG_COLOR, foreground=PLACEHOLDER_FG_COLOR)

        # Add this new style for our text box frames
        self.style.configure('Border.TFrame', background=TEXT_BG_COLOR,
                             borderwidth=1, relief='solid', bordercolor=FIELD_BORDER_AREA_COLOR)

        # Load Icon Images
        self.copy_icon = tk.PhotoImage(file=resource_path(COPY_IMAGE_FILE))
        self.copy_icon_hover = tk.PhotoImage(file=resource_path(COPY_IMAGE_HOVER_FILE))

        # Prompt Template Discovery (to get custom ones)
        prompt_templates = discover_prompt_templates()
        self.card_prompt_templates = prompt_templates.get("card_prompts", ["NSFW"])
        self.sd_prompt_templates = prompt_templates.get("sd_prompts", ["NSFW"])

        # UI Setup
        # Create Tab Instances
        self.tab_control = ttk.Notebook(self)
        self.caption_tab = CaptionTab(self.tab_control, self)
        self.generate_tab = GenerateTab(self.tab_control, self,
            copy_icon=self.copy_icon,
            copy_icon_hover=self.copy_icon_hover)
        self.settings_tab = SettingsTab(self.tab_control, self)

        self.tab_control.add(self.caption_tab, text='Caption')
        self.tab_control.add(self.generate_tab, text='Generate')
        self.tab_control.add(self.settings_tab, text='Settings')

        # Create the status bar first and pack it to the bottom of the window
        self.style.configure('Dark.TLabel', background=DARK_COLOR, foreground="white")
        self.status_bar = ttk.Label(self, text="Ready. Please load a model.", relief=tk.FLAT, anchor=tk.W,
                                    background=DARK_COLOR, foreground="white")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Pack tabs
        self.tab_control.pack(expand=True, fill="both")

        # Now that all tabs exist, we can safely run setup methods.
        self.generate_tab.post_init_setup()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.current_state = None
        self.set_state(AppState.IDLE)  # Set the initial state

    def start_api_generation_task(self):
        """The controller's method for handling the start of an API task."""
        self.set_state(AppState.API_GENERATING)

    def end_api_generation_task(self):
        """The controller's method for handling the end of an API task."""
        self.set_state(AppState.READY_FOR_SD_GENERATION)

    def on_closing(self):  # Renamed to be a public method, good practice!
        """
        Handles the application window closing event.
        Saves the complete application state and closes the application.
        """
        try:
            # Update settings with the final state from the UI
            settings_data = self.persistence.load_settings()

            # Update settings with the final state from the UI
            self.settings['last_used_vlm'] = self.caption_tab.model_selection_combo.get()
            self.settings['last_card_template'] = self.generate_tab.card_template_combo.get()
            self.settings['last_sd_template'] = self.generate_tab.sd_template_combo.get()
            self.settings['temperature'] = self.settings_tab.temperature_slider.get()
            self.settings['frequency_penalty'] = self.settings_tab.frequency_penalty_slider.get()
            self.settings['presence_penalty'] = self.settings_tab.presence_penalty_slider.get()

            # Save all settings
            self.persistence.save_settings(settings_data)
            print("Settings saved.")

        except Exception as e:
            print(f"Error saving settings: {e}")
        finally:
            self.destroy()





    def process_dropped_image(self, filepath):
        # This is the new home for the image processing logic!
        if filepath.lower().endswith(ACCEPTED_IMAGE_EXTENSIONS):
            self.image_path = filepath
            try:
                self.image_raw = Image.open(self.image_path).convert("RGB")
                display_image = self.image_raw.copy()
                display_image.thumbnail(MAX_THUMBNAIL_SIZE)
                self.image_tk = ImageTk.PhotoImage(display_image)

                # The controller updates the widget on the specific tab
                self.caption_tab.image_label.config(image=self.image_tk, text="")

                if self.current_state == AppState.MODEL_LOADED:
                    self.set_state(AppState.READY_TO_GENERATE)
                elif self.current_state == AppState.MODEL_LOADING:
                    self.update_status("Image ready. Wait for model...")
                elif self.current_state == AppState.READY_TO_GENERATE:
                    self.update_status("Image ready. Ready to generate.")
                else:
                    # If the model isn't loaded yet, just update the status
                    self.update_status("Image ready. Now load a model.")

            except Exception as e:
                messagebox.showerror("Image Error", f"Failed to load image: {e}")
                self.image_path = None
        else:
            supported_extensions = ', '.join(ACCEPTED_IMAGE_EXTENSIONS)
            messagebox.showerror("Error", f"Invalid file type.\nAccepted: {supported_extensions}\n Please drop a valid image file.")



    def load_model_threaded(self):
        """
        Initiates model loading in a separate thread. The model to be loaded
        is determined by the current selection in the combobox.
        Transitions the UI to the MODEL_LOADING state.
        """
        model_name = self.caption_tab.model_selection_combo.get()
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

    def set_state(self, new_state: AppState):
        """
        Manages UI element states based on the application's current state.

        Args:
            new_state (AppState): The state to transition to.
        """
        self.current_state = new_state
        # Default states
        self.caption_tab.load_button.config(state='disabled')
        self.caption_tab.load_button.config(text="Load")
        self.caption_tab.unload_button.config(state='disabled')
        self.caption_tab.generate_button.config(state='disabled', text="Generate")
        self.caption_tab.copy_caption_button.config(state='enabled')
        self.caption_tab.copy_tags_button.config(state='enabled')
        self.caption_tab.model_selection_combo.config(state='disabled')
        self.generate_tab.card_text_box.config(state='disabled')
        self.generate_tab.sd_text_box.config(state='disabled')
        self.settings_tab.test_button.config(state='enabled')

        # Update default button state
        self._update_generate_buttons_state()

        # Configure UI based on the new state ---
        if self.current_state == AppState.IDLE:
            self.caption_tab.load_button.config(state='normal')
            self.caption_tab.model_selection_combo.config(state='readonly')
            self.update_status("Ready. Please load a model.")

        elif self.current_state == AppState.MODEL_LOADING:
            self.caption_tab.load_button.config(text="Loading...")
            self.update_status(f"Loading model: {self.caption_tab.model_selection_combo.get()}...")


        elif self.current_state == AppState.MODEL_LOADED:
            self.caption_tab.load_button.config(text="Loaded")
            self.caption_tab.unload_button.config(state='normal')
            self.caption_tab.model_selection_combo.config(state='disabled')
            self.settings_tab.test_button.config(state='enabled')
            if not self.image_raw:
                self.update_status("Model loaded. Please drop an image.")
            else:
                self.update_status("Model loaded.")

        elif self.current_state == AppState.READY_TO_GENERATE:
            self.caption_tab.load_button.config(text="Loaded")
            self.caption_tab.unload_button.config(state='normal')
            self.caption_tab.generate_button.config(state='normal')
            self.caption_tab.model_selection_combo.config(state='disabled')
            self.update_status("Ready to generate.")

        elif self.current_state == AppState.GENERATING:
            self.caption_tab.generate_button.config(text="Generating...")
            self.caption_tab.unload_button.config(state='disabled')
            self.caption_tab.model_selection_combo.config(state='disabled')
            self.settings_tab.test_button.config(state='disabled')
            self.update_status("Generating, please wait...")

        elif self.current_state == AppState.READY_FOR_CARD_GENERATION:
            self.caption_tab.generate_button.config(state='normal')
            self.generate_tab.card_text_box.config(state='normal')
            self.generate_tab.card_generate_button.config(state='normal')
            self.generate_tab.sd_text_box.config(state='disabled')
            self.generate_tab.sd_generate_button.config(state='normal')
            self.caption_tab.copy_caption_button.config(state='normal')
            self.caption_tab.copy_tags_button.config(state='normal')
            self.caption_tab.unload_button.config(state='normal')
            self.settings_tab.test_button.config(state='enabled')
            self.update_status("Character Card prompt ready. -> In Generate Tab, click 'Generate Card'.")

        elif self.current_state == AppState.READY_FOR_SD_GENERATION:
            self.caption_tab.generate_button.config(state='normal')
            self.generate_tab.card_text_box.config(state='normal')
            self.generate_tab.card_generate_button.config(state='normal')
            self.generate_tab.sd_text_box.config(state='normal')
            self.generate_tab.sd_generate_button.config(state='normal')
            self.caption_tab.copy_caption_button.config(state='normal')
            self.caption_tab.copy_tags_button.config(state='normal')
            self.caption_tab.unload_button.config(state='normal')
            self.settings_tab.test_button.config(state='enabled')
            self.update_status("Character Card generated. SD prompt is ready.")

        elif self.current_state == AppState.API_GENERATING:
            self.generate_tab.card_generate_button.config(state='disabled')
            self.generate_tab.sd_generate_button.config(state='disabled')
            self.caption_tab.unload_button.config(state='normal')
            self.settings_tab.test_button.config(state='disabled')
            self.update_status("Generating via API...")

    def _update_generate_buttons_state(self):
        """
        A specialist function to manage the state of the 'Generate' tab buttons
        based on whether their driving text boxes have content.
        """
        # Enable card generation if the main VLM output has text.
        if self.caption_tab.output_caption_text.get("1.0", tk.END).strip():
            self.generate_tab.card_generate_button.config(state='normal')
        else:
            self.generate_tab.card_generate_button.config(state='disabled')

        # Enable SD generation if the character card output has text.
        if self.generate_tab.card_output_text_box.get("1.0", tk.END).strip():
            self.generate_tab.sd_generate_button.config(state='normal')
        else:
            self.generate_tab.sd_generate_button.config(state='disabled')



    def generate_threaded(self):
        """
        Initiates a multi-step generation task in a separate thread.
        Transitions the UI to the GENERATING state.
        """
        prompt = self.caption_tab.caption_prompt.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Input Error", "Prompt cannot be empty.")
            return

        self.set_state(AppState.GENERATING)

        # Create a queue to communicate with the worker thread
        self.task_queue = queue.Queue()

        # Start the worker thread, passing it the queue
        threading.Thread(target=self._generate_task_chain, args=(prompt, self.task_queue), daemon=True).start()

        # Start a loop to check the queue for updates from the thread, this will be rescheduled until done
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
                self.caption_tab.update_caption_text(data)
            elif message_type == "update_tags":
                self.caption_tab.update_tags_text(data)
            elif message_type == "error":
                print(data)
                messagebox.showerror("Generation Error", data)
            elif message_type == "done":
                # The chain is finished, populate the next tab
                final_caption = self.caption_tab.output_caption_text.get("1.0", tk.END).strip()
                final_tags = self.caption_tab.output_tags_text.get("1.0", tk.END).strip()
                # Set the state first to enable the text boxes
                self.set_state(AppState.READY_FOR_CARD_GENERATION)
                # Now populate them
                self.generate_tab.populate_generate_card(final_caption, final_tags)
                return  # Stop the queue-checking loop

        except queue.Empty:
            # If the queue is empty, do nothing and check again later
            pass

        # Reschedule execution to go over queue again
        self.after(100, self._process_queue)

    def update_status(self, text):
        """Updates the status bar text."""
        self.status_bar.config(text=text)

    def copy_to_clipboard(self, source_control, subject):
        """Copies from a textbox to the clipboard."""
        self.clipboard_clear()
        self.clipboard_append(source_control.get("1.0", tk.END))
        self.update_status(f"{subject} copied to clipboard.")

    def open_about_window(self):
        """Creates and shows the About window."""
        about = AboutWindow(self)

if __name__ == "__main__":

    app = VLM_GUI()
    app.mainloop()
