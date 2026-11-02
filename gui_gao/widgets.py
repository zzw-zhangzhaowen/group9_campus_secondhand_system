"""Reusable fields, scrollable pages and bounded local image loading."""
from __future__ import annotations

import math
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from . import theme as t

ROOT = Path(__file__).resolve().parent.parent


class ScrollPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg=t.WHITE, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = ttk.Frame(self.canvas, padding=(30, 24, 30, 24))
        self.window_id = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window_id, width=e.width))

    def scroll_to(self, widget):
        self.update_idletasks()
        y = widget.winfo_rooty() - self.body.winfo_rooty()
        height = max(self.body.winfo_height(), 1)
        self.canvas.yview_moveto(max(0, (y - 25) / height))


class Field(ttk.Frame):
    def __init__(self, parent, title, value="", *, hint="", secret=False, choices=None,
                 multiline=False, width=35):
        super().__init__(parent)
        self.multiline = multiline
        t.label(self, title, bold=True).pack(anchor="w", pady=(0, 6))
        self.var = tk.StringVar(master=self, value=value)
        if multiline:
            self.input = tk.Text(self, height=5, width=width, wrap="word", undo=True,
                                 font=(t.FAMILY, 12), bg=t.WHITE, fg=t.INK,
                                 relief="solid", bd=1, highlightthickness=1,
                                 highlightbackground=t.LINE, highlightcolor=t.BLUE,
                                 padx=8, pady=8)
            self.input.insert("1.0", value)
            self.input.bind("<Tab>", lambda e: (e.widget.tk_focusNext().focus_set(), "break")[1])
            self.input.bind("<Shift-Tab>", lambda e: (e.widget.tk_focusPrev().focus_set(), "break")[1])
        elif choices:
            self.input = ttk.Combobox(self, textvariable=self.var, values=choices,
                                      state="readonly", width=width)
        else:
            self.input = ttk.Entry(self, textvariable=self.var, show="•" if secret else "", width=width)
        self.input.pack(fill="x")
        if hint:
            t.label(self, hint, color=t.MUTED, size=10, wraplength=490, justify="left").pack(anchor="w", pady=(5, 0))
        self.error = t.label(self, "", color=t.RED, size=10, wraplength=490, justify="left")
        self.error.pack(anchor="w", pady=(2, 7))

    def get(self):
        return self.input.get("1.0", "end-1c") if self.multiline else self.var.get()

    def set(self, value):
        if self.multiline:
            self.input.delete("1.0", "end")
            self.input.insert("1.0", value)
        else:
            self.var.set(value)

    def show_error(self, message):
        self.error.configure(text=message)
        if not self.multiline:
            self.input.state(["invalid"] if message else ["!invalid"])

    def destroy(self):
        # Release Tcl resources on the UI thread, not a later worker GC cycle.
        self.var = None
        super().destroy()


def field_errors(fields, errors, page=None):
    for key, field in fields.items():
        field.show_error(errors.get(key, ""))
    if errors:
        first = next((fields[k] for k in fields if k in errors), None)
        if first:
            first.input.focus_set()
            if page:
                page.scroll_to(first)
    return bool(errors)


def image_path(value):
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


class ItemImage(tk.Canvas):
    """PNG/GIF with Tk. Optional Pillow adds JPEG/EXIF and high-quality scaling.

    Network images are never fetched. Missing/corrupt/oversized files show an
    explicit placeholder rather than crashing the page or erasing the path.
    """
    def __init__(self, parent, path="", category="", width=250, height=160):
        super().__init__(parent, width=width, height=height, bg=t.BG,
                         highlightthickness=0, bd=0)
        self.photo = None
        self.reason = "暂无图片"
        try:
            source = image_path(path)
            if source:
                if not source.is_file() or source.stat().st_size > 20 * 1024 * 1024:
                    raise ValueError("missing or too large")
                try:
                    from PIL import Image, ImageTk, ImageOps
                except ImportError:
                    original = tk.PhotoImage(master=self, file=str(source))
                    if original.width() * original.height() > 25_000_000:
                        raise ValueError("too many pixels")
                    scale = max(1, math.ceil(original.width() / width), math.ceil(original.height() / height))
                    self.photo = original.subsample(scale, scale)
                else:
                    with Image.open(source) as original:
                        if original.width * original.height > 25_000_000:
                            raise ValueError("too many pixels")
                        original = ImageOps.exif_transpose(original).convert("RGB")
                        original.thumbnail((width, height))
                        self.photo = ImageTk.PhotoImage(original, master=self)
                self.reason = ""
        except (OSError, ValueError, tk.TclError, RuntimeError):
            self.reason = "图片无法预览"
        self.bind("<Configure>", self.draw)
        self.draw()

    def draw(self, event=None):
        self.delete("all")
        width = event.width if event else int(self.cget("width"))
        height = event.height if event else int(self.cget("height"))
        if self.photo:
            self.create_image(width/2, height/2, image=self.photo)
        else:
            x, y = width/2, height/2-12
            self.create_rectangle(x-28,y-23,x+28,y+18,outline="#A8B7D0",width=2)
            self.create_oval(x+10,y-15,x+18,y-7,fill="#A8B7D0",outline="")
            self.create_line(x-24,y+14,x-8,y-3,x+4,y+9,x+12,y+1,x+24,y+14,fill="#A8B7D0",width=2)
            self.create_text(x,y+40,text=self.reason,fill=t.MUTED,font=(t.FAMILY,11))

    def destroy(self):
        self.photo = None
        super().destroy()


def page_title(parent, title, subtitle=""):
    t.label(parent, title, size=25, bold=True).pack(anchor="w")
    if subtitle:
        t.label(parent, subtitle, color=t.MUTED).pack(anchor="w", pady=(8, 20))


def empty_state(parent, title, message, command, button_text="重新加载"):
    box = ttk.Frame(parent, padding=35)
    box.pack(fill="both", expand=True, pady=30)
    t.label(box, title, size=19, bold=True, anchor="center").pack(pady=12)
    t.label(box, message, color=t.MUTED, wraplength=650, justify="center").pack(pady=10)
    t.button(box, button_text, command).pack(pady=15)
