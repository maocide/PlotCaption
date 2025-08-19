import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
from PIL import Image, ImageTk
import torch
from transformers import AutoProcessor, LlavaForConditionalGeneration, AutoModelForCausalLM, AutoTokenizer, \
    AutoModelForVision2Seq
from tkinterdnd2 import DND_FILES, TkinterDnD
from qwen_vl_utils import process_vision_info
import json
import os

# --- Configuration ---
# Use a quantized model for lower VRAM usage, or the full model for better quality.
# Quantized model: "John6666/llama-joycaption-beta-one-hf-llava-nf4"
# Full model: "fancyfeast/llama-joycaption-alpha-two-hf-llava"
DEFAULT_MODEL = "fancyfeast/llama-joycaption-alpha-two-hf-llava"
DEFAULT_PROMPT = "Write a detailed description of this image."
MAX_THUMBNAIL_SIZE = (400, 400)
MODEL_HISTORY_FILE = "model_history.json"


class AutocompleteEntry(tk.Frame):
    """
    A tkinter widget that features a text entry box with an autocomplete dropdown.

    The dropdown list appears as the user types and suggests completions from a
    provided list of options. The user can navigate the suggestions with arrow
    keys and select one with Enter or a mouse click.
    """

    def __init__(self, parent, completions=None, **kwargs):
        """
        Initializes the AutocompleteEntry widget.

        Args:
            parent: The parent tkinter widget.
            completions (list): A list of strings to be used as autocomplete suggestions.
            **kwargs: Keyword arguments to be passed to the underlying tk.Entry widget.
        """
        super().__init__(parent)

        self.completions = sorted(completions) if completions else []
        self.var = tk.StringVar()

        self.entry = tk.Entry(self, textvariable=self.var, **kwargs)
        self.entry.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(parent)

        self.var.trace("w", self.on_text_changed)
        self.entry.bind("<Up>", self.on_arrow_up)
        self.entry.bind("<Down>", self.on_arrow_down)
        self.entry.bind("<Return>", self.on_enter)
        self.entry.bind("<FocusOut>", self.on_focus_out)

    def on_text_changed(self, *args):
        """
        Handles the event when the text in the entry box changes.

        Filters the completion list based on the current text and updates the
        suggestion listbox.
        """
        text = self.var.get().lower()
        if not text:
            self.hide_listbox()
            return

        matches = [comp for comp in self.completions if text in comp.lower()]
        if matches:
            self.show_listbox(matches)
        else:
            self.hide_listbox()

    def show_listbox(self, completions):
        """
        Displays the listbox with the given completion suggestions.

        Args:
            completions (list): The list of strings to display.
        """
        if not hasattr(self, 'listbox_active') or not self.listbox_active:
            self.listbox_active = True
            self.listbox.delete(0, tk.END)
            for item in completions:
                self.listbox.insert(tk.END, item)

            # Calculate position relative to the parent of the AutocompleteEntry
            x = self.winfo_x() + self.entry.winfo_x()
            y = self.winfo_y() + self.entry.winfo_y() + self.entry.winfo_height()
            width = self.entry.winfo_width()

            self.listbox.place(x=x, y=y, width=width)
            self.listbox.lift() # Bring the listbox to the top of the stacking order
            self.listbox.bind("<Button-1>", self.on_listbox_select)
            self.listbox.bind("<Return>", self.on_enter)

    def hide_listbox(self, event=None):
        """Hides the autocomplete listbox."""
        if hasattr(self, 'listbox_active') and self.listbox_active:
            self.listbox.place_forget()
            self.listbox_active = False

    def on_arrow_up(self, event):
        """Handles the 'Up' arrow key press to navigate the suggestion list."""
        if self.listbox_active:
            current_selection = self.listbox.curselection()
            if not current_selection:
                idx = tk.END
            else:
                idx = current_selection[0] - 1

            if idx < 0:
                idx = tk.END

            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(idx)
            self.listbox.activate(idx)
            return "break"  # Prevents the cursor from moving in the entry

    def on_arrow_down(self, event):
        """Handles the 'Down' arrow key press to navigate the suggestion list."""
        if self.listbox_active:
            current_selection = self.listbox.curselection()
            if not current_selection:
                idx = 0
            else:
                idx = current_selection[0] + 1

            if idx >= self.listbox.size():
                idx = 0

            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(idx)
            self.listbox.activate(idx)
            return "break" # Prevents the cursor from moving in the entry

    def on_enter(self, event):
        """Handles the 'Enter' key press to select a suggestion."""
        if self.listbox_active and self.listbox.curselection():
            self.on_listbox_select(event)
            return "break"  # Prevents the default Enter behavior

    def on_listbox_select(self, event):
        """Handles a selection from the listbox, updating the entry."""
        if self.listbox.curselection():
            selection = self.listbox.get(self.listbox.curselection())
            self.var.set(selection)
            self.hide_listbox()
            self.entry.icursor(tk.END) # Move cursor to the end

    def on_focus_out(self, event):
        """Hides the listbox when the entry widget loses focus."""
        self.after(200, self.hide_listbox) # Delay to allow listbox click to register

    def configure(self, *args, **kwargs):
        """Configures the underlying Entry widget."""
        self.entry.configure(*args, **kwargs)

    config = configure

    def get(self):
        """Returns the current text from the entry widget."""
        return self.var.get()

    def insert(self, index, text):
        """Inserts text into the entry widget."""
        self.var.set(text)

    def set_completions(self, completions):
        """
        Updates the list of autocomplete suggestions.

        Args:
            completions (list): The new list of strings for suggestions.
        """
        self.completions = sorted(completions)


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

        # --- Model and Processor ---
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # --- State Variables ---
        self.image_path = None
        self.image_raw = None
        self.image_tk = None
        self.is_toriigate_model = False

        # --- Model History ---
        self.model_history = self._load_model_history()


        # --- UI Setup ---
        self._setup_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _load_model_history(self):
        """
        Loads the model history from the JSON file.

        If the file doesn't exist, it returns a list containing the default model.

        Returns:
            list: A list of previously used model names.
        """
        if os.path.exists(MODEL_HISTORY_FILE):
            try:
                with open(MODEL_HISTORY_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return [DEFAULT_MODEL] # Return default if file is corrupted
        else:
            return [DEFAULT_MODEL]

    def _save_model_history(self):
        """Saves the current model history list to the JSON file."""
        try:
            with open(MODEL_HISTORY_FILE, "w") as f:
                json.dump(self.model_history, f, indent=4)
        except IOError as e:
            print(f"Error saving model history: {e}") # Log to console

    def _add_model_to_history(self, model_name):
        """
        Adds a new model name to the history if it's not already present.

        Args:
            model_name (str): The name of the model to add.
        """
        if model_name not in self.model_history:
            self.model_history.append(model_name)
            # No need to save here, it's saved on closing
            if hasattr(self, 'model_name_entry'):
                self.model_name_entry.set_completions(self.model_history)

    def _on_closing(self):
        """Handles the application window closing event."""
        self._save_model_history()
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

        self.model_name_entry = AutocompleteEntry(
            top_frame,
            completions=self.model_history,
            bg="#3C3C3C", fg="white", relief=tk.FLAT, width=50
        )
        self.model_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.model_name_entry.insert(0, self.model_history[0] if self.model_history else DEFAULT_MODEL)

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

        Validates if the dropped file is an image and, if so, proceeds to
        load and display it.

        Args:
            event: The event object from TkinterDnD, containing the file path.
        """
        filepath = event.data.strip('{}')  # Clean up the path string from dnd
        if filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            self.image_path = filepath
            self.load_and_display_image()
        else:
            messagebox.showerror("Error", "Invalid file type. Please drop a valid image file.")

    def load_and_display_image(self):
        """
        Loads an image from the stored file path, converts it to RGB,
        and displays a thumbnail in the GUI.
        """
        try:
            self.image_raw = Image.open(self.image_path).convert("RGB")

            # Create a thumbnail for display
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
        Initiates model loading in a separate thread to keep the GUI responsive.

        Retrieves the model name from the entry field, validates it, and
        starts the appropriate model loading method in a new thread.
        """
        model_name = self.model_name_entry.get()
        if not model_name:
            messagebox.showerror("Error", "Model name cannot be empty.")
            return

        self.update_status(f"Loading model: {model_name}...")
        self.load_button.config(state=tk.DISABLED, text="Loading...")
        self.model_name_entry.config(state=tk.DISABLED)

        if model_name == "Minthy/ToriiGate-v0.4-7B":
            target_func = self._load_toriigate_model
        else:
            target_func = self._load_llava_model

        threading.Thread(target=target_func, args=(model_name,), daemon=True).start()

    def _load_llava_model(self, model_name):
        """
        Loads a LLaVA-based VLM model and processor from Hugging Face.

        Handles the actual model loading, updating the GUI on success or failure.
        This method is designed to be run in a separate thread.

        Args:
            model_name (str): The name of the model to load from Hugging Face.
        """
        try:
            self.processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
            self.model = LlavaForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True
            )
            self.model.eval()
            self.is_toriigate_model = False
            self.update_status(f"Model loaded successfully on {self.device.upper()}.")
            self.load_button.config(state=tk.DISABLED, text="Loaded")
            self.unload_button.config(state=tk.NORMAL)
            self.check_generate_button_state()
            self._add_model_to_history(model_name)
        except Exception as e:
            messagebox.showerror("Model Loading Error",
                                 f"Failed to load model: {e}\n\nCheck the model name, your internet connection, and ensure you have enough VRAM/RAM.")
            self.update_status("Model loading failed.")
            self.load_button.config(state=tk.NORMAL, text="Load Model")
            self.model_name_entry.config(state=tk.NORMAL)

    def _load_toriigate_model(self, model_name):
        """
        Loads the Minthy/ToriiGate-v0.4-7B model and processor.

        This is a Qwen-based model and requires specific classes for loading.
        Handles the actual model loading, updating the GUI on success or failure.
        This method is designed to be run in a separate thread.

        Args:
            model_name (str): The name of the model to load (should be "Minthy/ToriiGate-v0.4-7B").
        """
        try:
            self.processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)

            self.model = AutoModelForVision2Seq.from_pretrained( # CHANGE THIS LINE!
                model_name,
                trust_remote_code=True,
                device_map="auto",  # This helps distribute the model across your GPU's VRAM automatically
                torch_dtype=torch.bfloat16  # <--- ADD THIS LINE!
            )
            self.model.eval()
            self.is_toriigate_model = True
            self.update_status(f"Model loaded successfully on {self.device.upper()}.")
            self.load_button.config(state=tk.DISABLED, text="Loaded")
            self.unload_button.config(state=tk.NORMAL)
            self.check_generate_button_state()
        except Exception as e:
            messagebox.showerror("Model Loading Error",
                                 f"Failed to load model: {e}\n\nCheck the model name, your internet connection, and ensure you have enough VRAM/RAM.")
            self.update_status("Model loading failed.")
            self.load_button.config(state=tk.NORMAL, text="Load Model")
            self.model_name_entry.config(state=tk.NORMAL)


    def unload_model(self):
        """
        Unloads the model and processor, and clears GPU memory if applicable.
        Resets the GUI state to allow loading a new model.
        """
        self.model = None
        self.processor = None
        self.is_toriigate_model = False
        if self.device == "cuda":
            torch.cuda.empty_cache()
        self.update_status("Model unloaded.")
        self.load_button.config(state=tk.NORMAL, text="Load Model")
        self.unload_button.config(state=tk.DISABLED)
        self.model_name_entry.config(state=tk.NORMAL)
        self.check_generate_button_state()

    def generate_threaded(self):
        """
        Initiates text generation in a separate thread to keep the GUI responsive.
        """
        self.update_status("Generating text...")
        self.generate_button.config(state=tk.DISABLED, text="Generating...")

        if self.is_toriigate_model:
            target_func = self._generate_toriigate_description
        else:
            target_func = self._generate_llava_description

        threading.Thread(target=target_func, daemon=True).start()

    def _generate_llava_description(self):
        """
        Generates a text description for a LLaVA model.

        Formats the input for the model, runs inference, decodes the output,
        and displays it in the GUI. This method is designed to be run in a
        separate thread.
        """
        if not self.image_raw or not self.model or not self.processor:
            return

        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Input Error", "Prompt cannot be empty.")
            self.generate_button.config(state=tk.NORMAL, text="Generate Description")
            return

        try:
            with torch.no_grad():
                # Format the conversation using the model's chat template
                convo = [
                    {"role": "system", "content": "You are an expert at analyzing images."},
                    {"role": "user", "content": f"<image>\n{prompt}"}
                ]
                convo_string = self.processor.apply_chat_template(convo, tokenize=False, add_generation_prompt=True)

                # Process inputs
                inputs = self.processor(
                    text=[convo_string],
                    images=[self.image_raw],
                    return_tensors="pt"
                ).to(self.device)

                inputs['pixel_values'] = inputs['pixel_values'].to(torch.bfloat16)

                # Generate output
                output = self.model.generate(**inputs, max_new_tokens=512, do_sample=False)

                # Decode and clean the output
                decoded_output = self.processor.batch_decode(output, skip_special_tokens=True)[0]

                # The output often includes the full prompt, so we find the assistant's response
                assistant_response = decoded_output.split("assistant\n")[-1].strip()

            self.update_output_text(assistant_response)
            self.update_status("Generation complete.")

        except Exception as e:
            messagebox.showerror("Generation Error", f"An error occurred during generation: {e}")
            self.update_status("Generation failed.")
        finally:
            self.generate_button.config(state=tk.NORMAL, text="Generate Description")
            self.copy_button.config(state=tk.NORMAL)

    def _generate_toriigate_description(self):
        """
        Generates a text description for the Minthy/ToriiGate-v0.4-7B model.

        Formats the input for the Qwen-VL model, runs inference, decodes the output,
        and displays it in the GUI. This method is designed to be run in a
        separate thread.
        """
        if not self.image_raw or not self.model or not self.processor:
            return

        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Input Error", "Prompt cannot be empty.")
            self.generate_button.config(state=tk.NORMAL, text="Generate Description")
            return

        try:
            with torch.no_grad():
                messages = [
                    {"role": "system", "content": "You are an expert at analyzing images."},
                    {"role": "user", "content": [
                        {"type": "image", "image": self.image_raw},
                        {"type": "text", "text": prompt}
                    ]}
                ]

                text_input = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                image_inputs, _ = process_vision_info(messages)

                model_inputs = self.processor(
                    text=[text_input],
                    images=image_inputs,
                    videos=None,
                    padding=True,
                    return_tensors="pt"
                ).to(self.device)

                generated_ids = self.model.generate(**model_inputs, max_new_tokens=512, do_sample=False)

                trimmed_generated_ids = [out_ids[len(in_ids):] for in_ids, out_ids in zip(model_inputs.input_ids, generated_ids)]

                assistant_response = self.processor.batch_decode(
                    trimmed_generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
                )[0]

            self.update_output_text(assistant_response)
            self.update_status("Generation complete.")

        except Exception as e:
            messagebox.showerror("Generation Error", f"An error occurred during generation: {e}")
            self.update_status("Generation failed.")
        finally:
            self.generate_button.config(state=tk.NORMAL, text="Generate Description")
            self.copy_button.config(state=tk.NORMAL)

    def update_status(self, text):
        """
        Updates the status bar text in a thread-safe manner.

        Args:
            text (str): The text to display in the status bar.
        """
        self.status_bar.config(text=text)

    def update_output_text(self, text):
        """
        Updates the main output text box in a thread-safe manner.

        Args:
            text (str): The text to display in the output box.
        """
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, text)
        self.output_text.config(state=tk.DISABLED)

    def check_generate_button_state(self):
        """
        Enables or disables the 'Generate' button based on whether both a
        model and an image are loaded.
        """
        if self.model and self.image_path:
            self.generate_button.config(state=tk.NORMAL)
        else:
            self.generate_button.config(state=tk.DISABLED)

    def copy_to_clipboard(self):
        """
        Copies the entire content of the output text box to the system clipboard.
        """
        self.clipboard_clear()
        self.clipboard_append(self.output_text.get("1.0", tk.END))
        self.update_status("Output copied to clipboard.")


if __name__ == "__main__":
    # Note: tkdnd requires the mainloop to be called on the root window instance
    app = VLM_GUI()
    app.mainloop()