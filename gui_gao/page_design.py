"""B's illustrated secondary-page components; no service or data ownership."""
import math
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from . import theme as t


class PageBanner(tk.Frame):
    def __init__(self, parent, app, eyebrow, title, description, artwork='book'):
        super().__init__(parent, bg=t.BLUE)
        self.app, self.job, self.offset = app, None, 0
        copy = tk.Frame(self, bg=t.BLUE)
        copy.pack(side='left', fill='both', expand=True, padx=26, pady=23)
        t.label(copy, eyebrow, size=9, bold=True, color=t.LIME, bg=t.BLUE).pack(anchor='w')
        self.heading = t.label(copy, title, size=25, bold=True, color=t.WHITE, bg=t.BLUE,
                               wraplength=560, justify='left')
        self.heading.pack(anchor='w', pady=(10, 7))
        t.label(copy, description, size=11, color='#DBE6FF', bg=t.BLUE,
                wraplength=550, justify='left').pack(anchor='w')
        self.art = tk.Canvas(self, width=235, height=182, bg=t.BLUE, highlightthickness=0)
        self.art.pack(side='right', padx=(0, 22), pady=10)
        self.art.create_oval(20, 5, 207, 183, outline='#517CF0')
        self.art.create_rectangle(65, 22, 204, 160, fill='#103BB6', outline='')
        self.art.create_rectangle(56, 14, 195, 152, fill=t.WHITE, outline='', tags='paper')
        self.photo = None
        if artwork == 'account':
            self.art.create_oval(94, 37, 155, 98, fill=t.LIME, outline=t.INK, width=2, tags='paper')
            self.art.create_text(124, 68, text=app.gateway.user['nickname'][0], font=(t.FAMILY, 25, 'bold'), fill=t.INK, tags='paper')
            self.art.create_text(124, 120, text='MY CAMPUS CARD', font=(t.FAMILY, 8, 'bold'), fill=t.INK, tags='paper')
        else:
            source = tk.PhotoImage(master=self, file=str(Path(__file__).parent/'assets'/f'{artwork}.png'))
            self.photo = source.subsample(max(1, math.ceil(max(source.width()/124, source.height()/98))))
            self.art.create_image(125, 76, image=self.photo, tags='paper')
            self.art.create_text(125, 132, text='A NEW CHAPTER.', font=(t.FAMILY, 8, 'bold'), fill=t.INK, tags='paper')
        self.art.create_oval(13, 110, 81, 178, fill=t.LIME, outline=t.BLUE, width=4)
        self.art.create_text(47, 144, text='GOOD\nAGAIN ↗', font=(t.FAMILY, 9, 'bold'), fill=t.INK)
        self.art.bind('<Enter>', lambda _: self.animate(-5))
        self.art.bind('<Leave>', lambda _: self.animate(0))

    def animate(self, target):
        if self.job:
            self.after_cancel(self.job)
            self.job = None
        if getattr(self.app, 'reduce_motion', False):
            self.art.move('paper', 0, -self.offset)
            self.offset = 0
            return
        def step():
            delta = target-self.offset
            move = delta if abs(delta)<.3 else delta*.4
            self.art.move('paper', 0, move)
            self.offset += move
            self.job = self.after(20, step) if abs(delta)>=.3 else None
        step()

    def destroy(self):
        if self.job:
            self.after_cancel(self.job)
        self.photo = None
        super().destroy()


class StatStrip(ttk.Frame):
    def __init__(self, parent, entries):
        super().__init__(parent)
        self.values = []
        for i, (title, caption, command) in enumerate(entries):
            self.columnconfigure(i, weight=1, uniform='stats')
            box = tk.Frame(self, bg=t.PALE, padx=18, pady=15)
            box.grid(row=0, column=i, sticky='nsew', padx=(0, 12 if i<len(entries)-1 else 0))
            t.label(box, title, size=10, color=t.MUTED, bg=t.PALE).pack(anchor='w')
            value = t.label(box, '—', size=27, bold=True, color=t.BLUE, bg=t.PALE)
            value.pack(anchor='w', pady=4)
            self.values.append(value)
            t.button(box, caption+'  ↗', command, 'nav').pack(anchor='w')

    def set_counts(self, counts):
        for widget, count in zip(self.values, counts):
            widget.configure(text=str(count).zfill(2))


def note_card(parent, title, text):
    box = tk.Frame(parent, bg=t.PALE, padx=18, pady=18)
    t.label(box, title, bold=True, bg=t.PALE, color=t.BLUE).pack(anchor='w')
    t.label(box, text, size=10, color=t.MUTED, bg=t.PALE, wraplength=350, justify='left').pack(anchor='w', pady=(8,0))
    return box


class AuthArtwork(tk.Canvas):
    """A small paper collage with a finite hover transition, never a running loop."""
    def __init__(self, parent, app):
        super().__init__(parent, width=320, height=245, bg=t.BLUE, highlightthickness=0)
        self.app, self.job, self.offset = app, None, 0
        self.photos = []
        self.create_oval(18, 3, 306, 236, outline='#6087ED')
        self.create_text(291, 30, text='✳', font=(t.FAMILY, 38), fill=t.LIME)
        for name, x, y, caption in [('book', 15, 22, 'A NEW CHAPTER.'), ('lamp', 163, 83, 'STILL SHINING.')]:
            self.create_rectangle(x+5, y+6, x+144, y+162, fill='#103BB6', outline='')
            self.create_rectangle(x, y, x+137, y+156, fill=t.WHITE, outline='', tags='paper')
            source = tk.PhotoImage(master=self, file=str(Path(__file__).parent/'assets'/f'{name}.png'))
            photo = source.subsample(max(1, math.ceil(max(source.width()/116, source.height()/110))))
            self.photos.append(photo)
            self.create_image(x+68, y+66, image=photo, tags='paper')
            self.create_text(x+68, y+138, text=caption, fill=t.INK, font=(t.FAMILY, 8, 'bold'), tags='paper')
        self.create_oval(75, 169, 144, 238, fill=t.LIME, outline=t.BLUE, width=4)
        self.create_text(110, 204, text='GOOD\nAGAIN ↗', fill=t.INK, font=(t.FAMILY, 9, 'bold'))
        self.bind('<Enter>', lambda _: self.animate(-5))
        self.bind('<Leave>', lambda _: self.animate(0))

    animate = PageBanner.animate

    @property
    def art(self):
        return self

    def destroy(self):
        if self.job:
            self.after_cancel(self.job)
        self.photos.clear()
        super().destroy()
