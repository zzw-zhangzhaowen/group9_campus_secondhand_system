"""Reusable fields, scrollable pages and bounded local image loading."""
from __future__ import annotations

import math
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from . import theme as t
from .lifecycle import StringVar

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
        self.var = StringVar(master=self, value=value)
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

    def observe(self, callback):
        """Notify for typing, paste and programmatic updates without timer polling."""
        self._observer = callback
        if self.multiline:
            def changed(event=None):
                if self.input.edit_modified():
                    self.input.edit_modified(False)
                    callback()
            self.input.edit_modified(False)
            self.input.bind("<<Modified>>", changed, add="+")
        else:
            self._trace = self.var.trace_add("write", lambda *_: callback())

    def show_error(self, message):
        self.error.configure(text=message)
        if not self.multiline:
            self.input.state(["invalid"] if message else ["!invalid"])

    def destroy(self):
        # Release Tcl resources on the UI thread, not a later worker GC cycle.
        if hasattr(self, "_trace"):
            self.var.trace_remove("write", self._trace)
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
        self.reason = "No image"
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
            self.reason = "Preview unavailable"
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


def empty_state(parent, title, message, command, button_text="Reload"):
    box = ttk.Frame(parent, padding=35)
    box.pack(fill="both", expand=True, pady=30)
    t.label(box, title, size=19, bold=True, anchor="center").pack(pady=12)
    t.label(box, message, color=t.MUTED, wraplength=650, justify="center").pack(pady=10)
    t.button(box, button_text, command).pack(pady=15)


class MarketHero(ttk.Frame):
    """B's blue/lime hero. A short pointer-driven accent replaces web animations."""
    def __init__(self, parent, app):
        super().__init__(parent, style="Hero.TFrame", padding=12)
        copy = tk.Frame(self, bg=t.BLUE)
        copy.pack(side='left', fill='both', expand=True, padx=28, pady=28)
        t.label(copy, 'THE CAMPUS MARKET IS OPEN.', size=10, bold=True,
                color=t.LIME, bg=t.BLUE).pack(anchor='w')
        t.label(copy, 'Browse campus.\nFind your next item.', size=25, bold=True,
                color=t.WHITE, bg=t.BLUE, justify='left').pack(anchor='w', pady=(8, 5))
        t.label(copy, 'Books, tech and everyday essentials, ready to use again.', size=11,
                color='#DFE8FF', bg=t.BLUE).pack(anchor='w')
        t.button(copy, 'List an item  →', lambda: app.show('publish'), 'accent').pack(anchor='w', pady=(12, 0))
        self.art = tk.Canvas(self, width=290, height=215, bg=t.BLUE, highlightthickness=0)
        self.art.pack(side='right', padx=(0, 22))
        self.photos = []
        # Decorative illustrations, with no fabricated price or product availability.
        for x, y, name, caption in [(12, 32, 'keyboard', 'Make room on your desk'), (139, 66, 'bag', 'Carry what you need')]:
            self.art.create_rectangle(x, y, x+137, y+137, fill=t.WHITE, outline=t.WHITE, tags='paper')
            pic = tk.PhotoImage(master=self, file=str(Path(__file__).parent / 'assets' / f'{name}.png'))
            scale = max(1, math.ceil(max(pic.width()/122, pic.height()/96)))
            pic = pic.subsample(scale, scale)
            self.photos.append(pic)
            self.art.create_image(x+68, y+55, image=pic, tags='paper')
            self.art.create_text(x+68, y+119, text=caption, fill=t.INK, font=(t.FAMILY, 8), tags='paper')
        self.art.create_oval(218, 10, 277, 69, fill=t.LIME, outline='', tags='sticker')
        self.art.create_text(248, 39, text='GOOD\nFINDS!', fill=t.INK, font=(t.FAMILY, 9, 'bold'), tags='sticker')
        self.app = app
        self.job = None
        self.offset = 0
        self.art.bind('<Enter>', lambda e: self.animate(-5))
        self.art.bind('<Leave>', lambda e: self.animate(0))

    def animate(self, target):
        if getattr(self.app, "reduce_motion", False):
            target = 0
        if self.job:
            self.after_cancel(self.job)
        def step():
            delta = target - self.offset
            if abs(delta) < .3:
                self.art.move('paper', 0, delta)
                self.offset = target
                self.job = None
                return
            movement = delta * .4
            self.art.move('paper', 0, movement)
            self.offset += movement
            self.job = self.after(20, step)
        step()

    def destroy(self):
        if self.job:
            self.after_cancel(self.job)
        self.photos.clear()
        super().destroy()
