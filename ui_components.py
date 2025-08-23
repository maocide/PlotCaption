import tkinter as tk
from tkinter import ttk
from config import FIELD_BACK_COLOR, FIELD_FOREGROUND_COLOR, SELECT_BACKGROUND_COLOR

class AutocompleteEntry(ttk.Frame):
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

        self.entry = ttk.Entry(self, textvariable=self.var, style='Dark.TEntry', **kwargs)
        self.entry.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(self.winfo_toplevel(),
                                 bg=FIELD_BACK_COLOR,
                                 fg=FIELD_FOREGROUND_COLOR,
                                 selectbackground=SELECT_BACKGROUND_COLOR,
                                 selectforeground=FIELD_FOREGROUND_COLOR,
                                 highlightthickness=0,
                                 borderwidth=0,
                                 relief=tk.FLAT)

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

            # Calculate position relative to the toplevel window
            x = self.winfo_rootx() - self.winfo_toplevel().winfo_rootx()
            y = self.winfo_rooty() - self.winfo_toplevel().winfo_rooty() + self.winfo_height()
            width = self.winfo_width()

            self.listbox.place(x=x, y=y, width=width)
            self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
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
            self.on_listbox_select()
            return "break"  # Prevents the default Enter behavior

    def on_listbox_select(self, event=None):
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
