"""B's illustrated secondary-page components; no service or data ownership."""
from pathlib import Path
import math
import time
import tkinter as tk
from tkinter import ttk
from . import theme as t


class PageBanner(tk.Frame):
    def __init__(self, parent, app, eyebrow, title, description, artwork='book'):
        super().__init__(parent, bg=t.BLUE)
        self.app = app
        copy = tk.Frame(self, bg=t.BLUE)
        copy.pack(side='left', fill='both', expand=True, padx=26, pady=23)
        t.label(copy, eyebrow, size=9, bold=True, color=t.LIME, bg=t.BLUE).pack(anchor='w')
        self.heading = t.label(copy, title, size=25, bold=True, color=t.WHITE, bg=t.BLUE,
                               wraplength=560, justify='left')
        self.heading.pack(anchor='w', pady=(10, 7))
        t.label(copy, description, size=11, color='#DBE6FF', bg=t.BLUE,
                wraplength=550, justify='left').pack(anchor='w')
        scene = {'book': 'home', 'bag': 'publish', 'keyboard': 'mine'}.get(artwork, artwork)
        artwork_box = tk.Frame(self, bg=t.BLUE)
        artwork_box.pack(side='right', padx=(0, 22), pady=10)
        self.art = SceneArtwork(artwork_box, app, scene)
        self.art.pack()
        if self.art.is_loop:
            self.motion_control = tk.Button(artwork_box, text='Ⅱ 暂停动画',
                                            command=self.toggle_animation, bg=t.BLUE,
                                            fg=t.WHITE, highlightbackground=t.BLUE,
                                            font=(t.FAMILY, 10))
            self.motion_control.pack(pady=(0, 4))
            if getattr(app, 'reduce_motion', False):
                self.motion_control.configure(text='已减少动态', state='disabled')

    def toggle_animation(self):
        paused = self.art.toggle_motion()
        self.motion_control.configure(text='▶ 播放动画' if paused else 'Ⅱ 暂停动画')

    def animate(self, target):
        self.art.animate(target)

    @property
    def job(self):
        return self.art.job if hasattr(self, 'art') else None

    @property
    def offset(self):
        return self.art.offset if hasattr(self, 'art') else 0



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


class SceneArtwork(tk.Canvas):
    """Decorative scenes; route/clock motion never modifies business state."""
    VECTORS = {'messages': (1, 0), 'account': (1, .3), 'publish': (0, 1),
               'mine': (.5, .5), 'favorites': (0, -1), 'intentions': (0, 1),
               'logs': (-1, .3), 'home': (0, 1), 'login': (0, 0)}

    def __init__(self, parent, app, kind='home', large=False):
        width, height, scale = (320, 245, 3) if large else (235, 182, 4)
        super().__init__(parent, width=width, height=height, bg=t.BLUE, highlightthickness=0)
        self.app, self.kind, self.job, self.offset = app, kind, None, 0
        self.photos, self.lit = [], False
        self.is_loop = kind in ('intentions', 'logs')
        self.motion_paused, self.elapsed, self._last_tick = False, 0.0, None
        self.factor = 2 / scale
        self.origin = ((width-420*self.factor)/2, (height-300*self.factor)/2)
        for part, tag in [('base', 'scene'), ('float', 'paper')]:
            if self.is_loop and part == 'float':
                continue
            source = tk.PhotoImage(master=self, file=str(Path(__file__).parent/'assets'/'scenes'/f'{kind}-{part}.png'))
            photo = source.subsample(scale)
            self.photos.append(photo)
            self.create_image(width/2, height/2, image=photo, tags=tag)
        if self.is_loop:
            self._create_motion_art()
            self._draw_motion(0)
            self.bind('<Map>', lambda _: self._start_motion())
            self.bind('<Unmap>', lambda _: self._stop_motion())
        elif kind == 'login':
            self.itemconfigure('paper', state='hidden')
        else:
            self.bind('<Enter>', lambda _: self.animate(-7))
            self.bind('<Leave>', lambda _: self.animate(0))

    def _points(self, *values):
        return [value*self.factor+self.origin[i%2] for i, value in enumerate(values)]

    def _create_motion_art(self):
        ink, peach = '#142244', '#ffb797'
        if self.kind == 'intentions':
            self.create_polygon(0, 0, 0, 0, 0, 0, fill=peach, outline=ink,
                                width=2*self.factor, smooth=True, tags='route-pin')
            self.create_oval(0, 0, 0, 0, fill='#fffdf4', outline='', tags='pin-hole')
        else:
            self.create_oval(*self._points(274,201,356,283), fill=peach,
                             outline=ink, width=2*self.factor)
            for i in range(12):
                angle = math.radians(i*30)
                inner = 30 if i%3 == 0 else 32
                self.create_line(*self._points(315+inner*math.sin(angle),242-inner*math.cos(angle),
                                               315+35*math.sin(angle),242-35*math.cos(angle)),
                                 fill='#b76c53', width=1)
            for tag, width in [('clock-hour',4), ('clock-minute',3)]:
                self.create_line(0,0,0,0, fill=ink, width=width*self.factor,
                                 capstyle=tk.ROUND, tags=tag)
            self.create_oval(*self._points(312,239,318,245),fill=ink,outline='')

    def _draw_motion(self, elapsed):
        if self.kind == 'intentions':
            phase = (elapsed % 6)/6
            x, y = 77, 177
            if .20 < phase < .33:
                progress = (phase-.20)/.13
                x, y = 77+113*progress, 177-103*progress-26*math.sin(math.pi*progress)
            elif .33 <= phase <= .53:
                x, y = 190, 74
            elif .53 < phase < .66:
                progress = (phase-.53)/.13
                x, y = 190+135*progress, 74+76*progress-44*math.sin(math.pi*progress)
            elif phase >= .66:
                x, y = 325, 150
            self.coords('route-pin', *self._points(x,y,x-7,y-13,x-18,y-25,x-18,y-35,
                                                 x-12,y-48,x+12,y-48,x+18,y-35,x+18,y-25,x+7,y-13))
            self.coords('pin-hole', *self._points(x-6,y-36,x+6,y-24))
            state = 'hidden' if phase >= .94 else 'normal'
            self.itemconfigure('route-pin', state=state)
            self.itemconfigure('pin-hole', state=state)
        else:
            for tag, length, degrees in [('clock-hour',20,120+30*int(elapsed/3)),
                                          ('clock-minute',28,30*int(elapsed/.5))]:
                angle = math.radians(degrees % 360)
                self.coords(tag, *self._points(315,242,315+length*math.sin(angle),242-length*math.cos(angle)))

    def _start_motion(self):
        if self.job or self.motion_paused or getattr(self.app, 'reduce_motion', False):
            return
        self._last_tick = time.monotonic()
        self.job = self.after(33, self._tick_motion)

    def _tick_motion(self):
        self.job = None
        if self.motion_paused or getattr(self.app, 'reduce_motion', False) or not self.winfo_viewable():
            self._last_tick = None
            return
        now = time.monotonic()
        self.elapsed += now-self._last_tick if self._last_tick is not None else 0
        self._last_tick = now
        self._draw_motion(self.elapsed)
        self.job = self.after(33 if self.kind == 'intentions' else 100, self._tick_motion)

    def _stop_motion(self):
        if self.job:
            self.after_cancel(self.job)
            self.job = None
        self._last_tick = None

    def toggle_motion(self):
        self.motion_paused = not self.motion_paused
        if self.motion_paused:
            self._stop_motion()
        else:
            self._start_motion()
        return self.motion_paused

    def toggle_light(self):
        self.lit = not self.lit
        self.itemconfigure('paper', state='normal' if self.lit else 'hidden')
        return self.lit

    def animate(self, target):
        if self.is_loop:
            if getattr(self.app, 'reduce_motion', False):
                self._stop_motion()
            return
        if self.job:
            self.after_cancel(self.job)
            self.job = None
        dx, dy = self.VECTORS[self.kind]
        if getattr(self.app, 'reduce_motion', False):
            self.move('paper', -self.offset*dx, -self.offset*dy)
            self.offset = 0
            return
        def step():
            delta = target-self.offset
            move = delta if abs(delta) < .3 else delta*.4
            self.move('paper', move*dx, move*dy)
            self.offset += move
            self.job = self.after(20, step) if abs(delta) >= .3 else None
        step()

    def destroy(self):
        self._stop_motion()
        self.photos.clear()
        super().destroy()


class AuthArtwork(SceneArtwork):
    def __init__(self, parent, app):
        super().__init__(parent, app, 'login', large=True)


class LocalChecklist(ttk.Frame):
    """Voluntary on-page reminders; never alters an item or intention status."""
    def __init__(self, parent, title, items):
        super().__init__(parent, padding=18, relief='solid', borderwidth=1)
        t.label(self, title, bold=True, color=t.BLUE, wraplength=360, justify='left').pack(anchor='w')
        t.label(self, '仅本页自检，不代表交易状态，不会发送给对方。', size=9,
                color=t.MUTED, wraplength=350, justify='left').pack(anchor='w', pady=(8, 12))
        self.values = []
        for item in items:
            value = tk.BooleanVar(master=self, value=False)
            self.values.append(value)
            ttk.Checkbutton(self, text=item, variable=value, command=self.update_count).pack(anchor='w', pady=5)
        self.summary = t.label(self, '', color=t.MUTED, size=10)
        self.summary.pack(anchor='w', pady=(12,0))
        self.update_count()

    def update_count(self):
        count = sum(v.get() for v in self.values)
        self.summary.configure(text=f'{count} / {len(self.values)} 已确认', fg=t.GREEN if count == len(self.values) else t.MUTED)


class FoldNote(ttk.Frame):
    def __init__(self, parent, title, text):
        super().__init__(parent, padding=12, relief='solid', borderwidth=1)
        self.open = False
        self.title = title
        self.control = t.button(self, '＋  '+title, self.toggle, 'nav')
        self.control.pack(fill='x')
        self.copy = t.label(self, text, size=11, color=t.MUTED, wraplength=410, justify='left')

    def toggle(self):
        self.open = not self.open
        self.control.configure(text=('−  ' if self.open else '＋  ')+self.title)
        if self.open:
            self.copy.pack(fill='x', pady=(10, 3))
        else:
            self.copy.pack_forget()
