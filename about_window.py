import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
import webbrowser
from assets_utils import resource_path
from config import DARK_COLOR, FIELD_FOREGROUND_COLOR, BUTTON_ACTIVATE_COLOR
from config import APP_VERSION


class AboutWindow(tk.Toplevel):
    """
    Creates the 'About' window for the application.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.title(f"About PlotCaption v{APP_VERSION}")
        self.geometry("400x300")
        self.configure(bg=DARK_COLOR)
        self.resizable(False, False)

        # Make this window modal
        self.grab_set()
        self.transient(parent)

        try:
            img_path = resource_path('assets/plot_icon.ico')
            pil_image = Image.open(img_path).resize((96, 96), Image.Resampling.LANCZOS)
            self.app_icon = ImageTk.PhotoImage(pil_image)

            icon_label = tk.Label(self, image=self.app_icon, bg=DARK_COLOR)
            icon_label.pack(pady=(50, 10))

        except Exception as e:
            print(f"Could not load about window icon: {e}")
            fallback_label = tk.Label(self, text="PLOT", font=("Segoe UI", 24, "bold"), fg="white", bg=DARK_COLOR)
            fallback_label.pack(pady=(20, 10))

        # A frame to hold the profile pic and text
        author_frame = tk.Frame(self, bg=DARK_COLOR)
        author_frame.pack(pady=(10, 20))

        try:
            # Load image
            profile_path = resource_path('assets/profile.png')
            profile_pil = Image.open(profile_path).resize((48, 48), Image.Resampling.LANCZOS)
            self.profile_icon = ImageTk.PhotoImage(profile_pil)

            profile_label = tk.Label(author_frame, image=self.profile_icon, bg=DARK_COLOR)
            profile_label.pack(side=tk.LEFT, padx=(0, 10))
        except Exception as e:
            print(f"Could not load profile icon: {e}")  # It will just not show if it fails

        # Text and link, now inside the author_frame ---
        text_frame = tk.Frame(author_frame, bg=DARK_COLOR)
        text_frame.pack(side=tk.LEFT)

        created_by_label = tk.Label(text_frame, text="Created with ♡ by", fg="white", bg=DARK_COLOR,
                                    font=("Segoe UI", 10))
        created_by_label.pack(anchor="w")  # Anchor west = align left

        link_font = font.Font(family="Segoe UI", size=11, underline=True)
        github_link_label = tk.Label(
            text_frame,
            text="maocide",
            fg="#6495ED",
            bg=DARK_COLOR,
            font=link_font,
            cursor="hand2"
        )
        github_link_label.pack(anchor="w")  # Anchor west = align left

        github_link_label.bind("<Button-1>", self._open_github_link)
        github_link_label.bind("<Enter>", lambda e: github_link_label.config(fg=BUTTON_ACTIVATE_COLOR))
        github_link_label.bind("<Leave>", lambda e: github_link_label.config(fg="#6495ED"))

        # --- Center the window ---
        self.center_window(parent)

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

    def _open_github_link(self, event):
        """Opens the GitHub profile URL in a web browser."""
        webbrowser.open_new_tab("https://github.com/maocide")