import tkinter as tk


class CreateToolTip(object):
    """
    Creates a tooltip for a given widget.
    """

    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        # Schedule the tooltip to appear after a short delay
        self.schedule()

    def leave(self, event=None):
        # Cancel the scheduled tooltip and hide it if it's visible
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip)  # 500ms delay

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        # Get the position of the widget
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        # Creates a toplevel window
        self.tw = tk.Toplevel(self.widget)

        # Removes the window frame
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")

        # Style the label to match your dark theme
        label = tk.Label(self.tw, text=self.text, justify='left',
                         background="#3C3C3C", relief='solid', borderwidth=1,
                         foreground="white", wraplength=250, padding=(5, 3))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()