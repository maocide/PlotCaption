import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD

from config import DEFAULT_PROMPT, MAX_THUMBNAIL_SIZE
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
        self.title("VLM Interface")
        self.geometry("900x750")
        self.configure(bg="#2E2E2E")

        # --- Handlers ---
        self.model_handler = ModelHandler()
        self.history_manager = HistoryManager()

        # --- State Variables ---
        self.image_path = None
        self.image_raw = None
        self.image_tk = None

        # --- UI Setup ---
        self._setup_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        """Handles the application window closing event."""
        self.history_manager.save_on_exit()
        self.destroy()

    def _setup_widgets(self):
        """Creates and arranges all the GUI widgets."""
        main_frame = tk.Frame(self, bg="#2E2E2E")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # --- Top Frame for Model Control ---
        top_frame = tk.Frame(main_frame, bg="#2E2E2E")
        top_frame.pack(fill=tk.X, pady=(0, 10))

        self.load_button = tk.Button(top_frame, text="Load Model", command=self.load_model_threaded, bg="#4A4A4A",
                                     fg="white", relief=tk.FLAT, width=15)
        self.load_button.pack(side=tk.LEFT, padx=(0, 10))

        self.unload_button = tk.Button(top_frame, text="Unload Model", command=self.unload_model, state=tk.DISABLED,
                                       bg="#4A4A4A", fg="white", relief=tk.FLAT, width=15)
        self.unload_button.pack(side=tk.LEFT, padx=(0, 20))

        model_label = tk.Label(top_frame, text="Model:", bg="#2E2E2E", fg="white")
        model_label.pack(side=tk.LEFT)

        model_history = self.history_manager.get_history()
        self.model_name_entry = AutocompleteEntry(
            top_frame,
            completions=model_history,
            bg="#3C3C3C", fg="white", relief=tk.FLAT, width=50
        )
        self.model_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.model_name_entry.insert(0, model_history[0] if model_history else "")

        # --- Main Content Frame (Image and Text) ---
        content_frame = tk.Frame(main_frame, bg="#2E2E2E")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # --- Image Display Area ---
        self.image_label = tk.Label(content_frame, text="Drag & Drop an Image Here", bg="#3C3C3C", fg="gray",
                                    relief=tk.SOLID, bd=1)
        self.image_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        self.image_label.drop_target_register(DND_FILES)
        self.image_label.dnd_bind('<<Drop>>', self.handle_drop)

        # --- Right Panel for Inputs and Output ---
        right_panel = tk.Frame(content_frame, bg="#2E2E2E")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Input Prompt ---
        prompt_label = tk.Label(right_panel, text="Your Question/Prompt:", bg="#2E2E2E", fg="white")
        prompt_label.pack(anchor="w")
        self.prompt_text = tk.Text(right_panel, height=4, bg="#3C3C3C", fg="white", relief=tk.FLAT,
                                   insertbackground="white")
        self.prompt_text.pack(fill=tk.X, pady=(5, 10))
        self.prompt_text.insert(tk.END, DEFAULT_PROMPT)

        # --- Generate Button ---
        self.generate_button = tk.Button(right_panel, text="Generate Description", command=self.generate_threaded,
                                         state=tk.DISABLED, bg="#007ACC", fg="white", relief=tk.FLAT, height=2)
        self.generate_button.pack(fill=tk.X, pady=(0, 10))

        # --- Output Text Area ---
        output_label = tk.Label(right_panel, text="Model Output:", bg="#2E2E2E", fg="white")
        output_label.pack(anchor="w")
        self.output_text = scrolledtext.ScrolledText(right_panel, wrap=tk.WORD, bg="#3C3C3C", fg="white",
                                                     relief=tk.FLAT, insertbackground="white", state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # --- Copy Button ---
        self.copy_button = tk.Button(right_panel, text="Copy Output", command=self.copy_to_clipboard, state=tk.DISABLED,
                                     bg="#4A4A4A", fg="white", relief=tk.FLAT)
        self.copy_button.pack(fill=tk.X, pady=(10, 0))

        # --- Status Bar ---
        self.status_bar = tk.Label(self, text="Ready. Please load a model.", bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                   bg="#2E2E2E", fg="white")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

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
        prompt = self.prompt_text.get("1.0", tk.END).strip()
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
