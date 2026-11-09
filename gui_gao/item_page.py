"""Item detail with real data and an explicit owner action boundary."""
import tkinter as tk
from tkinter import ttk, messagebox
from .gateway import UserError
from .interaction_page import MessagePanel
from . import theme as t
from .page_design import note_card, FoldNote
from .widgets import ScrollPage, ItemImage, empty_state


class ItemPage(ScrollPage):
    def __init__(self, parent, app, item_id):
        super().__init__(parent)
        self.app, self.item_id = app, item_id
        self.messages_panel = None
        self.item = None
        self.favorited = False
        self.intended = False
        t.button(self.body, "‹ Back to items", lambda: app.show("home"), "nav").pack(anchor="w", pady=(0,20))
        self.area = ttk.Frame(self.body)
        self.area.pack(fill="both", expand=True)

    def start(self):
        def load():
            item = self.app.gateway.detail(self.item_id)
            error = ""
            try:
                self.favorited = self.item_id in self.app.gateway.features.favorite_ids()
                self.intended = any(r["user_id"] == self.app.gateway.user_id() and r["item_id"] == self.item_id for r in self.app.gateway.features.intentions())
            except UserError as exc:
                error = str(exc)
            return item, self.app.gateway.seller_names([item]), error
        self.app.run_task(load, self.render, self.failed)

    def failed(self, message):
        for child in self.area.winfo_children():
            child.destroy()
        empty_state(self.area, "Could not open this item", message, self.start)

    def render(self, data):
        item, names, error = data
        self.item = item
        for child in self.area.winfo_children():
            child.destroy()
        self.area.columnconfigure(0, weight=1)
        self.area.columnconfigure(1, weight=1)
        left = ttk.Frame(self.area)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,30))
        picture = ItemImage(left, item.get("image_path", ""), item["category"], width=460, height=370)
        picture.pack(fill="x")
        picture.configure(cursor='hand2')
        picture.bind('<Button-1>', lambda _: self.zoom_image())
        t.button(left, 'Enlarge image  ↗', self.zoom_image, 'nav').pack(anchor='e', pady=8)
        note_card(left, 'Before you arrange a handover', '01  Review the photo, description and condition.\n02  Ask about accessories and meeting arrangements.\n03  Inspect the item together before handing it over.').pack(fill='x', pady=(12,20))
        FoldNote(left, 'What should I check in the photo?', 'Look at edges, screens and connectors for wear. Each listing has one photo; ask in the comments if you need more detail.').pack(fill='x', pady=(0, 16))
        if picture.reason:
            t.label(left, "No image preview is available. Check the description on the right.", size=10, color=t.MUTED,
                    wraplength=420).pack(anchor="w", pady=10)
        right = ttk.Frame(self.area, padding=(5,0,5,20))
        right.grid(row=0, column=1, sticky="nsew")
        t.label(right, f"{item['category']}  /  {item['status']}", color=t.GREEN if item["status"] == "Available" else t.MUTED).pack(anchor="w")
        t.label(right, item["name"], size=26, bold=True, wraplength=460, justify="left").pack(anchor="w", pady=(15,20))
        t.label(right, f"¥ {item['price']:.2f}", size=34, bold=True, color=t.BLUE).pack(anchor="w", pady=(0,20))
        ttk.Separator(right).pack(fill="x", pady=12)
        t.label(right, "Description", bold=True).pack(anchor="w", pady=(8,10))
        t.label(right, item["description"], wraplength=440, justify="left").pack(anchor="w", pady=(0,20))
        t.label(right, "Seller", size=10, color=t.MUTED).pack(anchor="w", pady=(12,5))
        t.label(right, names.get(item["seller_id"], "Student"), bold=True).pack(anchor="w")
        t.label(right, f"Listed  {item.get('created_at', '')}", size=10, color=t.MUTED).pack(anchor="w", pady=(12,5))
        t.label(right, f"Updated  {item.get('updated_at', '')}", size=10, color=t.MUTED).pack(anchor="w")
        if item["seller_id"] == self.app.gateway.user_id():
            t.button(right, "Edit item", lambda: self.app.show("publish", item_id=item["id"]), "primary").pack(fill="x", pady=(28,10))
            t.button(right, "Manage my listings", lambda: self.app.show("mine")).pack(fill="x")
        else:
            self.intention_button = t.button(right, "Enquiry sent · View" if self.intended else "I am interested  →", self.intention, "primary")
            self.intention_button.pack(fill="x", pady=(24, 10))
            t.label(right, "Continue in the comments after sending an enquiry. No payment or reservation is made.", color=t.MUTED, size=10, wraplength=410, justify="left").pack(anchor="w")

        self.favorite_button = t.button(right, "♥ Saved" if self.favorited else "♡ Save item", self.favorite)
        self.favorite_button.pack(fill="x", pady=12)
        if item['status'] != 'Available':
            self.favorite_button.configure(state='disabled')
        self.feature_error = t.label(right, error, color=t.RED, size=10, wraplength=410, justify="left")
        self.feature_error.pack(anchor="w")
        self.messages_panel = MessagePanel(self.area, self.app, item)
        self.messages_panel.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(25, 0))
        self.messages_panel.start()

    def zoom_image(self):
        if not self.item:
            return
        window = tk.Toplevel(self.app.root)
        window.title(self.item['name']+' · Item image')
        window.transient(self.app.root)
        window.geometry('700x600')
        window.configure(bg=t.WHITE)
        viewport = tk.Canvas(window, bg=t.PALE, highlightthickness=0)
        viewport.pack(fill='both', expand=True, padx=20, pady=10)
        horizontal = ttk.Scrollbar(window, orient='horizontal', command=viewport.xview)
        horizontal.pack(fill='x', padx=20)
        vertical = ttk.Scrollbar(viewport, orient='vertical', command=viewport.yview)
        vertical.pack(side='right', fill='y')
        viewport.configure(xscrollcommand=horizontal.set, yscrollcommand=vertical.set)
        source = ItemImage(window, self.item.get('image_path',''), width=620, height=420)
        controls = ttk.Frame(window)
        controls.pack(pady=12)
        scale = [1]
        counter = t.label(controls, '100%', size=11)
        def zoom(delta=0):
            scale[0] = max(1, min(3, scale[0]+delta)) if delta else 1
            viewport.delete('picture')
            if source.photo:
                viewport.photo = source.photo.zoom(scale[0])
                viewport.create_image(0, 0, image=viewport.photo, anchor='nw', tags='picture')
                viewport.configure(scrollregion=viewport.bbox('picture'))
            else:
                viewport.create_text(310, 180, text=source.reason, fill=t.MUTED, tags='picture')
            counter.configure(text=f'{scale[0]*100}%')
            smaller.configure(state='disabled' if scale[0] == 1 else 'normal')
            larger.configure(state='disabled' if scale[0] == 3 else 'normal')
        smaller = t.button(controls, '− Zoom out', lambda: zoom(-1))
        smaller.pack(side='left', padx=8)
        counter.pack(side='left', padx=8)
        larger = t.button(controls, '＋ Zoom in', lambda: zoom(1))
        larger.pack(side='left', padx=8)
        t.button(controls, 'Reset', zoom, 'nav').pack(side='left', padx=8)
        zoom()
        t.label(window, 'Use the scrollbars to inspect the enlarged image · '+self.item['name'], size=10).pack(pady=8)
        t.button(window, 'Close preview', window.destroy).pack(pady=(0, 15))
        window.bind('<Escape>', lambda _: window.destroy())
        window.focus_set()

    def is_dirty(self):
        return bool(self.messages_panel and self.messages_panel.is_dirty())

    def favorite(self):
        def saved(value):
            self.favorited = value['favorited']
            self.favorite_button.configure(text="♥ Saved" if self.favorited else "♡ Save item")
            self.feature_error.configure(text="")
            self.app.notify("Item saved" if self.favorited else "Item removed from saved items")
        self.app.run_task(lambda: self.app.gateway.features.toggle_favorite(self.item_id), saved,
                          lambda message: self.feature_error.configure(text=message))

    def intention(self):
        if self.app.busy:
            return
        if self.intended:
            self.app.show('interactions', kind='intentions')
            return
        if not messagebox.askyesno('Send an enquiry?', f"Tell the seller you are interested in “{self.item['name']}”?\n\nThis does not charge or reserve the item.", parent=self.app.root, default='no'):
            return
        def saved(_):
            self.intended = True
            self.intention_button.configure(text='Enquiry sent · View')
            self.feature_error.configure(text='')
            self.app.notify('Enquiry sent. View it on the Enquiries page.')
        self.app.run_task(lambda: self.app.gateway.features.create_intention(self.item_id), saved,
                          lambda message: self.feature_error.configure(text=message))
