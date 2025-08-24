import queue
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, scrolledtext
import threading
from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD

from config import DEFAULT_PROMPT, MAX_THUMBNAIL_SIZE, INACTIVE_TAB_COLOR, DARK_COLOR, FIELD_BORDER_AREA_COLOR, \
    FIELD_BACK_COLOR, FIELD_FOREGROUND_COLOR, INSERT_COLOR, SELECT_BACKGROUND_COLOR, BUTTON_ACTIVATE_COLOR, \
    BUTTON_PRESSED_COLOR, BUTTON_COLOR, TEXT_BG_COLOR, INSERT_BACKGROUND_COLOR, PLACEHOLDER_FG_COLOR, TAGS_PROMPT
from history_manager import HistoryManager
from model_handler import ModelHandler
from ui_components import AutocompleteEntry

from enum import Enum, auto


class AppState(Enum):
    IDLE = auto()  # App just started, no model
    MODEL_LOADING = auto()  # A model is being downloaded/loaded
    MODEL_LOADED = auto()  # Model is loaded, but no image is present
    READY_TO_GENERATE = auto()  # Model and image are both loaded and ready
    GENERATING = auto()  # A generation task is running in the background

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



        self.title("PLOT Captioning in detail")
        self.geometry("900x750")
        self.configure(bg=DARK_COLOR)



        # --- Handlers ---
        self.model_handler = ModelHandler()
        self.history_manager = HistoryManager()

        # --- State Variables ---
        self.image_path = None
        self.image_raw = None
        self.image_tk = None

        # --- STYLE CONFIGURATION (Based on your research doc) ---
        # 1. Create the Style object
        self.style = ttk.Style(self)

        # 2. MANDATORY: Switch to a configurable theme to escape Windows' native rendering
        self.style.theme_use('clam')

        # 3. DEFINITIVE BORDER REMOVAL: Redefine the TNotebook layout
        #    An empty layout tells ttk to draw no container elements (and thus no border).
        self.style.layout('TNotebook', [])

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

        # Optional: Change color when the mouse hovers or clicks
        self.style.map('Dark.TButton',
                       background=[('active', BUTTON_ACTIVATE_COLOR), ('pressed', BUTTON_PRESSED_COLOR)])

        # Add 'focuscolor' to the map.
        self.style.map('TNotebook.Tab',
                       background=[('selected', DARK_COLOR)],
                       foreground=[('selected', FIELD_FOREGROUND_COLOR)],
                       focuscolor=[('selected', DARK_COLOR)])  # <--- ADD THIS LINE

        self.style.configure('Placeholder.TLabel', background=TEXT_BG_COLOR, foreground=PLACEHOLDER_FG_COLOR)

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
        self.status_bar = ttk.Label(self, text="Ready. Please load a model.", style='Dark.TLabel', anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Tab Control ---
        # NOW, pack the tab control last, letting it fill the remaining space
        self.tab_control.pack(expand=True, fill="both", padx=0, pady=0)

        # --- UI Setup ---
        self._setup_widgets_vlm(self.tab1_frame)
        self._setup_widgets_llm(self.tab2_frame)
        self._setup_widgets_settings(self.tab3_frame)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.current_state = None  # Initialize it
        self.set_state(AppState.IDLE)  # Set the initial state

    def _on_closing(self):
        """
        Handles the application window closing event.
        Saves history and closes the application.
        """
        self.history_manager.save_on_exit()
        self.destroy()

    def _create_labeled_textbox(self, parent, label_text, grid_row, grid_column):
        """
        Creates and grids a labeled Text widget with a vertical scrollbar.
        (Corrected Version)
        """
        # --- Create the Label ---
        label = ttk.Label(parent, text=label_text, background=DARK_COLOR, foreground=FIELD_FOREGROUND_COLOR)
        label.grid(row=grid_row, column=grid_column, padx=5, pady=(5, 0), sticky="w")

        # --- Create the Container Frame for the Text and Scrollbar ---
        text_frame = ttk.Frame(parent, style='Dark.TFrame')
        text_frame.grid(row=grid_row + 1, column=grid_column, sticky="nsew", padx=5, pady=5)

        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        # --- Create the Text Widget and Scrollbar ---
        text_box = tk.Text(text_frame,
                           wrap="word",
                           bg=TEXT_BG_COLOR,
                           fg=FIELD_FOREGROUND_COLOR,
                           relief="flat",
                           insertbackground=INSERT_BACKGROUND_COLOR
                           )

        scrollbar = ttk.Scrollbar(text_frame,
                                  orient="vertical",
                                  style='Dark.Vertical.TScrollbar',  # <<< THE MISSING PIECE OF EVIDENCE!
                                  command=text_box.yview
                                  )
        text_box.config(yscrollcommand=scrollbar.set)


        # --- Grid the Text and Scrollbar inside their frame ---
        text_box.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        return text_box

    def _setup_widgets_llm(self, parent_frame):
        # --- WIDGET CREATION ---
        main_frame = ttk.Frame(parent_frame, style='Dark.TFrame', padding=10)
        main_frame.pack(expand=True, fill="both")

        # --- Configure the grid of the PARENT element to be resizable ---
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        # This next line is important so the text boxes can grow vertically!
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # --- Create Text Boxes using our shiny new helper function ---
        self.card_text_box = self._create_labeled_textbox(
            parent=main_frame,
            label_text="Character card Prompt:",
            grid_row=0,
            grid_column=0
        )

        self.sd_text_box = self._create_labeled_textbox(
            parent=main_frame,
            # I noticed both your labels were the same, so I fixed this one!
            label_text="SD Prompt:",
            grid_row=0,
            grid_column=1
        )

        self.card_output_text_box = self._create_labeled_textbox(
            parent=main_frame,
            # I noticed both your labels were the same, so I fixed this one!
            label_text="Output Charater Card:",
            grid_row=3,
            grid_column=0
        )

        self.sd_output_text_box = self._create_labeled_textbox(
            parent=main_frame,
            # I noticed both your labels were the same, so I fixed this one!
            label_text="Output Charater Card:",
            grid_row=3,
            grid_column=1
        )

        # --- Top Frame for Api data ---
        #button_frame = tk.Frame(top_frame, bg=DARK_COLOR)
        #button_frame.grid(row=1, column=3, padx=5, pady=5, sticky="e")

        self.card_generate_button = ttk.Button(main_frame, text="Generate Card", command=None, style='Dark.TButton')
        self.card_generate_button.grid(row=2, column=0, sticky="ns", pady= 5)

        self.sd_generate_button = ttk.Button(main_frame, text="Generate SD", command=None, style='Dark.TButton')
        self.sd_generate_button.grid(row=2, column=1, sticky="ns", pady=5)

        # Add some example text to show the scrollbar
        for i in range(50):
            self.card_text_box.insert(tk.END, f"This is line number {i + 1}\\n")
            self.sd_text_box.insert(tk.END, f"This is line number {i + 1}\\n")

    def _setup_widgets_settings(self, parent_element):
        """Creates and arranges all settings tab widgets."""

        # Let's add the padding directly to it.
        parent_element.config(padding=15)

        # --- Top Frame for Api data ---
        top_frame = ttk.Frame(parent_element, style='Dark.TFrame')
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # --- Configure the columns of the PARENT element to be resizable ---
        # Columns 1 and 3, which contain the entries, will get the extra space.
        top_frame.columnconfigure(1, weight=1)
        top_frame.columnconfigure(3, weight=1)

        # --- Url Text ---
        # --- Row 0 ---
        url_label = ttk.Label(top_frame, text="API Url:", background=DARK_COLOR, foreground=FIELD_FOREGROUND_COLOR)
        # sticky="w" aligns the text to the West (left) of its grid cell
        url_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.character_card_prompt_entry = ttk.Entry(top_frame, style='Dark.TEntry')
        self.character_card_prompt_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # --- Row 1 ---
        llm_model_label = ttk.Label(top_frame, text="Model:", background=DARK_COLOR, foreground=FIELD_FOREGROUND_COLOR)
        # sticky="w" aligns the text to the West (left) of its grid cell
        llm_model_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.llm_model_entry = ttk.Entry(top_frame,  style='Dark.TEntry')
        self.llm_model_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # ---Row 0 Col 1 ---
        llm_key_label = ttk.Label(top_frame, text="API Key:", background=DARK_COLOR, foreground=FIELD_FOREGROUND_COLOR)
        # sticky="w" aligns the text to the West (left) of its grid cell
        llm_key_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        self.llm_key_entry = ttk.Entry(top_frame,  style='Dark.TEntry')
        self.llm_key_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # --- Top Frame for Api data ---
        button_frame = ttk.Frame(top_frame, style='Dark.TFrame')
        button_frame.grid(row=1, column=3, padx=5, pady=5, sticky="e")

        self.save_button = ttk.Button(button_frame, text="Save", command=None, style='Dark.TButton')
        self.save_button.pack(side=tk.LEFT, padx=(0,5))

        self.test_button = ttk.Button(button_frame, text="Test", command=None, style='Dark.TButton')
        self.test_button.pack(side=tk.LEFT)



    def _setup_widgets_vlm(self, parent_element):
        """Creates and arranges all the VLM tab widgets."""
        # In your _setup_widgets method:
        # Add highlightthickness=0 and bd=0 (border) to this line.

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

        model_history = self.history_manager.get_history()
        self.model_name_entry = AutocompleteEntry(
            top_frame,
            completions=model_history,
            width=50
        )
        self.model_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.model_name_entry.insert(0, model_history[0] if model_history else "")

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
        # This is the new, important part!
        # Tell the grid that column 0 should expand to fill the horizontal space.
        right_panel.columnconfigure(0, weight=1)

        # Tell the grid how to distribute EXTRA vertical space.
        # We give more weight to the caption output (row 4) than the tags output (row 6).
        # A 2:1 ratio means the caption gets 2/3 and the tags get 1/3 of the extra space.
        right_panel.rowconfigure(4, weight=2)
        right_panel.rowconfigure(6, weight=1)
        # All other rows have a default weight of 0 and will not expand vertically.

        # --- Place widgets using .grid() instead of .pack() ---

        # Row 0: Input Prompt Label
        prompt_label = ttk.Label(right_panel, text="Your Question/Prompt:", style='Dark.TLabel')
        prompt_label.grid(row=0, column=0, sticky="w")

        # Row 1: Input Prompt Text (fixed height, doesn't expand)
        self.llm_url_text = tk.Text(right_panel, height=4, bg=TEXT_BG_COLOR, fg=FIELD_FOREGROUND_COLOR, relief=tk.FLAT,
                                    insertbackground=INSERT_BACKGROUND_COLOR)
        self.llm_url_text.grid(row=1, column=0, sticky="ew", pady=(5, 10))
        self.llm_url_text.insert(tk.END, DEFAULT_PROMPT)

        # Row 2: Generate Button (fixed height)
        self.generate_button = ttk.Button(right_panel, text="Generate Description", command=self.generate_threaded,
                                          style='Dark.TButton')
        self.generate_button.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.generate_button.config(state=tk.DISABLED)

        # Row 3: Output Caption Label
        output_caption_label = ttk.Label(right_panel, text="Model Output:", style='Dark.TLabel')
        output_caption_label.grid(row=3, column=0, sticky="w")

        # Row 4: Output Caption Text (EXPANDS with weight=2)
        self.output_caption_text = scrolledtext.ScrolledText(right_panel, wrap=tk.WORD, bg=TEXT_BG_COLOR,
                                                             fg=FIELD_FOREGROUND_COLOR,
                                                             relief=tk.FLAT, insertbackground=INSERT_BACKGROUND_COLOR,
                                                             state=tk.DISABLED,
                                                             height=1 )
        self.output_caption_text.grid(row=4, column=0, sticky="nsew")

        # Row 5: Output Tags Label
        output_tags_label = ttk.Label(right_panel, text="Booru Tags Output:", style='Dark.TLabel')
        output_tags_label.grid(row=5, column=0, sticky="w", pady=(10, 0))

        # Row 6: Output Tags Text (EXPANDS with weight=1)
        self.output_tags_text = scrolledtext.ScrolledText(right_panel, wrap=tk.WORD, bg=TEXT_BG_COLOR,
                                                          fg=FIELD_FOREGROUND_COLOR,
                                                          relief=tk.FLAT, insertbackground=INSERT_BACKGROUND_COLOR,
                                                          state=tk.DISABLED,
                                                          height=1 )
        self.output_tags_text.grid(row=6, column=0, sticky="nsew")

        # Row 7: Copy Button (fixed height)
        self.copy_button = ttk.Button(right_panel, text="Copy Output", command=self.copy_to_clipboard,
                                      style='Dark.TButton')
        self.copy_button.grid(row=7, column=0, sticky="ew", pady=(10, 0))
        self.copy_button.config(state=tk.DISABLED)


    def handle_drop(self, event):
        """
        Handles the drag-and-drop file event.
        """
        filepath = event.data.strip('{}')
        if filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
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
        Initiates model loading in a separate thread after validating the model name.
        Transitions the UI to the MODEL_LOADING state.
        """
        model_name = self.model_name_entry.get()
        if not model_name:
            messagebox.showerror("Error", "Model name cannot be empty.")
            return

        self.set_state(AppState.MODEL_LOADING)
        threading.Thread(target=self._load_model_task, args=(model_name,), daemon=True).start()

    def _load_model_task(self, model_name: str):
        """
        The actual task of loading the model, executed in a separate thread.
        Updates the state to MODEL_LOADED on success, or READY_TO_GENERATE
        if an image is already present. Updates to IDLE on failure.

        Args:
            model_name (str): The name of the model to load.
        """
        try:
            self.model_handler.load_model(model_name)
            self.history_manager.add_model_to_history(model_name)
            self.model_name_entry.set_completions(self.history_manager.get_history())

            if self.image_path:
                self.set_state(AppState.READY_TO_GENERATE)
            else:
                self.set_state(AppState.MODEL_LOADED)

        except Exception as e:
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
        self.unload_button.config(state='disabled')
        self.generate_button.config(state='disabled', text="Generate Description")
        self.copy_button.config(state='disabled')
        self.model_name_entry.config(state='disabled')
        self.set_buttons_status('disabled')

        # --- Configure UI based on the new state ---
        if self.current_state == AppState.IDLE:
            self.load_button.config(state='normal', text="Load Model")
            self.model_name_entry.config(state='normal')
            self.update_status("Ready. Please load a model.")
            self.set_buttons_status('normal',
                                    [self.generate_button, self.load_button, self.unload_button, self.copy_button])


        elif self.current_state == AppState.MODEL_LOADING:
            self.load_button.config(text="Loading...")
            self.update_status(f"Loading model: {self.model_name_entry.get()}...")


        elif self.current_state == AppState.MODEL_LOADED:
            self.load_button.config(text="Loaded")
            self.unload_button.config(state='normal')
            self.model_name_entry.config(state='disabled')
            self.update_status("Model loaded. Please drop an image.")
            self.set_buttons_status('normal',
                                    [self.generate_button, self.load_button, self.copy_button])


        elif self.current_state == AppState.READY_TO_GENERATE:
            self.load_button.config(text="Loaded")
            self.unload_button.config(state='normal')
            self.generate_button.config(state='normal')
            self.copy_button.config(state='normal')
            self.model_name_entry.config(state='disabled')
            self.update_status("Ready to generate.")
            self.set_buttons_status('normal', [self.load_button])


        elif self.current_state == AppState.GENERATING:
            self.generate_button.config(text="Generating...")
            self.update_status("Generating, please wait...")

    def set_buttons_status(self, status, exclude=None):
        """
        Sets the state of all major buttons, with an option to exclude some.

        Args:
            status (str): The state to set (e.g., 'disabled', 'normal').
            exclude (list, optional): A list of button widgets to ignore.
        """
        if exclude is None:
            exclude = []  # Default to an empty list if no exclusions are given

        # A list of all the buttons this function controls
        all_buttons = [
            self.sd_generate_button,
            self.card_generate_button,
            self.generate_button,
            self.load_button,
            self.unload_button,
            self.save_button,
            self.test_button,
            self.copy_button
            # buttons to manage here!
        ]

        for button in all_buttons:
            if button not in exclude:
                button.config(state=status)


    def generate_threaded(self):
        """
        Initiates a multi-step generation task in a separate thread.
        Transitions the UI to the GENERATING state.
        """
        prompt = self.llm_url_text.get("1.0", tk.END).strip()
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
        try:
            # --- TASK 1 ---
            q.put(("status", "Generating description (step 1/2)..."))
            response1 = self.model_handler.generate_description(prompt, self.image_raw)

            # If the first task is successful, update the UI via the queue
            q.put(("update_caption", response1))
            q.put(("status", "Generating booru tags. (step 2/2)..."))

            # --- TASK 2 ---
            # Replace this with your second long-running call
            response2 = self.model_handler.generate_description(TAGS_PROMPT, self.image_raw)

            # Put the final result in the queue
            q.put(("update_tags", response2))
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
                # The chain is finished, re-enable the UI
                self.set_state(AppState.READY_TO_GENERATE)
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
            self.copy_button.config(state=tk.NORMAL)
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


if __name__ == "__main__":

    app = VLM_GUI()
    app.mainloop()
