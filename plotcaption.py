import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, scrolledtext
import threading
from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD

from config import DEFAULT_PROMPT, MAX_THUMBNAIL_SIZE, INACTIVE_TAB_COLOR, DARK_COLOR, FIELD_BORDER_AREA_COLOR, \
    FIELD_BACK_COLOR, FIELD_FOREGROUND_COLOR, INSERT_COLOR, SELECT_BACKGROUND_COLOR, BUTTON_ACTIVATE_COLOR, \
    BUTTON_PRESSED_COLOR, BUTTON_COLOR, TEXT_BG_COLOR, INSERT_BACKGROUND_COLOR, PLACEHOLDER_FG_COLOR
from history_manager import HistoryManager
from model_handler import ModelHandler
from ui_components import AutocompleteEntry



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

    def _on_closing(self):
        """Handles the application window closing event."""
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

        # --- Input Prompt ---
        prompt_label = ttk.Label(right_panel, text="Your Question/Prompt:", style='Dark.TLabel')
        prompt_label.pack(anchor="w")
        self.llm_url_text = tk.Text(right_panel, height=4, bg=TEXT_BG_COLOR, fg=FIELD_FOREGROUND_COLOR, relief=tk.FLAT,
                                    insertbackground=INSERT_BACKGROUND_COLOR)
        self.llm_url_text.pack(fill=tk.X, pady=(5, 10))
        self.llm_url_text.insert(tk.END, DEFAULT_PROMPT)

        # --- Generate Button ---
        self.generate_button = ttk.Button(right_panel, text="Generate Description", command=self.generate_threaded, style='Dark.TButton')
        self.generate_button.pack(fill=tk.X, pady=(0, 10))
        self.generate_button.config(state=tk.DISABLED)

        # --- Output Text Area ---
        output_label = ttk.Label(right_panel, text="Model Output:", style='Dark.TLabel')
        output_label.pack(anchor="w")
        self.output_text = scrolledtext.ScrolledText(right_panel, wrap=tk.WORD, bg=TEXT_BG_COLOR, fg=FIELD_FOREGROUND_COLOR,
                                                     relief=tk.FLAT, insertbackground=INSERT_BACKGROUND_COLOR, state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # --- Copy Button ---
        self.copy_button = ttk.Button(right_panel, text="Copy Output", command=self.copy_to_clipboard, style='Dark.TButton')
        self.copy_button.pack(fill=tk.X, pady=(10, 0))
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
        Loads and displays an image thumbnail.
        """
        try:
            self.image_raw = Image.open(self.image_path).convert("RGB")
            display_image = self.image_raw.copy()
            display_image.thumbnail(MAX_THUMBNAIL_SIZE)
            self.image_tk = ImageTk.PhotoImage(display_image)

            self.image_label.config(image=self.image_tk, text="")
            self.update_status("Image loaded successfully.")
            self.check_generate_button_state()
        except Exception as e:
            messagebox.showerror("Image Error", f"Failed to load image: {e}")
            self.image_path = None

    def load_model_threaded(self):
        """
        Initiates model loading in a separate thread.
        """
        model_name = self.model_name_entry.get()
        if not model_name:
            messagebox.showerror("Error", "Model name cannot be empty.")
            return

        self.update_status(f"Loading model: {model_name}...")
        self.load_button.config(state=tk.DISABLED, text="Loading...")
        self.model_name_entry.config(state=tk.DISABLED)
        self.unload_button.config(state=tk.DISABLED)

        threading.Thread(target=self._load_model_task, args=(model_name,), daemon=True).start()

    def _load_model_task(self, model_name):
        """
        The actual task of loading the model.
        """
        try:
            self.model_handler.load_model(model_name)
            self.update_status(f"Model loaded successfully on {self.model_handler.device.upper()}.")
            self.load_button.config(text="Loaded")
            self.unload_button.config(state=tk.NORMAL)
            self.history_manager.add_model_to_history(model_name)
            self.model_name_entry.set_completions(self.history_manager.get_history())
        except Exception as e:
            messagebox.showerror("Model Loading Error",
                                 f"Failed to load model: {e}\n\nCheck the model name, your internet connection, and ensure you have enough VRAM/RAM.")
            self.update_status("Model loading failed.")
            print("Error message:", e)
            self.load_button.config(state=tk.NORMAL, text="Load Model")
            self.model_name_entry.config(state=tk.NORMAL)
        finally:
            self.check_generate_button_state()

    def unload_model(self):
        """
        Unloads the model and resets the GUI state.
        """
        self.model_handler.unload_model()
        self.update_status("Model unloaded.")
        self.load_button.config(state=tk.NORMAL, text="Load Model")
        self.unload_button.config(state=tk.DISABLED)
        self.model_name_entry.config(state=tk.NORMAL)
        self.check_generate_button_state()

    def generate_threaded(self):
        """
        Initiates text generation in a separate thread.
        """
        prompt = self.llm_url_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Input Error", "Prompt cannot be empty.")
            return

        self.update_status("Generating text...")
        self.generate_button.config(state=tk.DISABLED, text="Generating...")
        self.copy_button.config(state=tk.DISABLED)

        threading.Thread(target=self._generate_task, args=(prompt,), daemon=True).start()

    def _generate_task(self, prompt):
        """
        The actual task of generating the description.
        """
        try:
            response = self.model_handler.generate_description(prompt, self.image_raw)
            self.update_output_text(response)
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

    def update_output_text(self, text):
        """Updates the main output text box."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, text)
        self.output_text.config(state=tk.DISABLED)

    def check_generate_button_state(self):
        """Enables or disables the 'Generate' button."""
        if self.model_handler.model and self.image_path:
            self.generate_button.config(state=tk.NORMAL)
        else:
            self.generate_button.config(state=tk.DISABLED)

    def copy_to_clipboard(self):
        """Copies the output text to the clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.output_text.get("1.0", tk.END))
        self.update_status("Output copied to clipboard.")


if __name__ == "__main__":
    app = VLM_GUI()
    app.mainloop()
