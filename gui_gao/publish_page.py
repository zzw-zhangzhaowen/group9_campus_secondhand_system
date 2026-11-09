"""Create/edit form with photo preview, validation and unsaved-change guard."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog
from . import theme as t
from .page_design import PageBanner, note_card, LocalChecklist
from .gateway import UserError
from .validation import CATEGORIES, item_errors
from .widgets import ScrollPage, Field, ItemImage, field_errors, page_title, empty_state, image_path


class PublishPage(ScrollPage):
    def __init__(self, parent, app, item_id=None):
        super().__init__(parent)
        self.app, self.item_id = app, item_id
        self.fields = {}
        self.original = None
        self.path = ""
        self.image_changed = False
        PageBanner(self.body, app, 'START A NEW CHAPTER / LIST AN ITEM',
            'Update your item.' if item_id else 'List your item.',
            'Preview as you type. Add a clear photo and an accurate description.', 'bag').pack(fill='x', pady=(0, 20))
        self.area = ttk.Frame(self.body)
        self.area.pack(fill="both", expand=True, pady=(10,0))

    def start(self):
        if self.item_id is None:
            self.form({})
        else:
            def load():
                item = self.app.gateway.detail(self.item_id)
                if item["seller_id"] != self.app.gateway.user_id():
                    raise UserError("You can only edit your own listings.")
                return item
            self.app.run_task(load, self.form, self.failed)

    def failed(self, message):
        for child in self.area.winfo_children():
            child.destroy()
        empty_state(self.area, "Could not edit this item", message, self.start)

    def form(self, item):
        for child in self.area.winfo_children():
            child.destroy()
        self.path = item.get("image_path", "")
        self.area.columnconfigure(0, weight=2)
        self.area.columnconfigure(1, weight=3)
        left = ttk.Frame(self.area, padding=(0,0,30,0))
        left.grid(row=0, column=0, sticky="nsew")
        t.label(left, "Item photo (optional)", bold=True).pack(anchor="w", pady=(0,12))
        self.preview = ttk.Frame(left)
        self.preview.pack(fill="x")
        self.refresh_image()
        self.filename = t.label(left, self.file_label(), color=t.MUTED, wraplength=350, justify="left", size=10)
        self.filename.pack(anchor="w", pady=10)
        controls = ttk.Frame(left)
        controls.pack(fill="x", pady=(8,15))
        t.button(controls, "Choose image", self.choose_image).pack(side="left", padx=(0,8))
        t.button(controls, "Remove image", self.remove_image, "nav").pack(side="left")
        t.label(left, "PNG / GIF supported. A photo is optional.\nKeep the original file in its current location.",
                color=t.MUTED, size=10, wraplength=350, justify="left").pack(anchor="w")
        self.image_error = t.label(left, "", color=t.RED, size=10, wraplength=350, justify="left")
        self.image_error.pack(anchor="w", pady=10)
        self.live_name = t.label(left, '', bold=True, size=17, wraplength=340, justify='left')
        self.live_name.pack(anchor='w', pady=(8, 6))
        self.live_price = t.label(left, '', size=25, color=t.BLUE, bold=True)
        self.live_price.pack(anchor='w')
        self.readiness = t.label(left, '', color=t.MUTED, size=11)
        self.readiness.pack(anchor='w', pady=(20, 8))
        self.progress = ttk.Progressbar(left, maximum=4)
        self.progress.pack(fill='x')
        note_card(left, 'Help the buyer understand your item', '01  Describe the condition.\n02  List any included accessories.\n03  Mention wear, damage or other details.').pack(fill='x', pady=20)
        right = ttk.Frame(self.area)
        right.grid(row=0, column=1, sticky="nsew")
        self.fields = {
            "name": Field(right, "Item name *", item.get("name", ""), hint="Up to 20 characters, e.g. Python textbook."),
            "category": Field(right, "Category *", item.get("category", CATEGORIES[0]), choices=CATEGORIES),
            "price": Field(right, "Price (¥) *", f"{item['price']:.2f}" if "price" in item else "", hint="Price must be positive and is saved to two decimal places."),
            "description": Field(right, "Description *", item.get("description", ""), multiline=True,
                                 hint="Up to 200 characters. Include condition, use and accessories."),
        }
        for field in self.fields.values():
            field.pack(fill="x")
        self.error = t.label(right, "", color=t.RED, wraplength=490, justify="left")
        self.error.pack(anchor="w", pady=(0,12))
        buttons = ttk.Frame(right)
        buttons.pack(fill="x", pady=10)
        t.button(buttons, "Save changes" if self.item_id else "List item", self.submit, "primary").pack(side="right")
        t.button(buttons, "Cancel", lambda: self.app.show("mine" if self.item_id else "home")).pack(side="right", padx=12)
        chips = ttk.Frame(right)
        chips.pack(fill='x', pady=(6, 12))
        for text in ['Condition: ', 'Accessories: ', 'Please note: ']:
            t.button(chips, text[:-1]+' +', lambda v=text: self.add_prompt(v), 'nav').pack(side='left', padx=(0, 5))
        for field in self.fields.values():
            field.observe(self.update_preview)
        self.update_preview()
        self.photo_check = LocalChecklist(left, 'Photo checklist', [
            'Show the whole item against a plain background', 'Describe any wear and included accessories', 'Make sure the photo shows the actual item'])
        self.photo_check.pack(fill='x', pady=16)
        self.original = self.values()

    def update_preview(self):
        if not self.fields:
            return
        values = self.values()
        errors = item_errors(values)
        count = sum(key not in errors for key in ('name', 'category', 'price', 'description'))
        self.progress['value'] = count
        self.readiness.configure(text=f'Ready: {count} / 4 fields · Photo optional')
        self.live_name.configure(text=values['name'].strip() or 'Your item name')
        self.live_price.configure(text='¥ '+(values['price'].strip() or '—'))

    def add_prompt(self, text):
        current = self.fields['description'].get()
        updated = current + ('\n' if current else '') + text
        if len(updated) > 200:
            self.fields['description'].show_error('Descriptions are limited to 200 characters. Please shorten the text.')
            return
        self.fields['description'].set(updated)
        self.fields['description'].input.focus_set()
        self.update_preview()

    def values(self):
        return {**{key: field.get() for key, field in self.fields.items()}, "image_path": self.path}

    def is_dirty(self):
        return self.original is not None and self.values() != self.original

    def file_label(self):
        return Path(self.path).name if self.path else "No image selected"

    def refresh_image(self):
        for child in self.preview.winfo_children():
            child.destroy()
        self.picture = ItemImage(self.preview, self.path, width=330, height=235)
        self.picture.pack(fill="x")

    def choose_image(self):
        if self.app.busy:
            return
        path = filedialog.askopenfilename(parent=self.app.root, title="Choose item image",
            filetypes=[("PNG / GIF images", "*.png *.gif"), ("All files", "*")])
        if not path:
            return
        self.path = path
        self.image_changed = True
        self.refresh_image()
        self.filename.configure(text=self.file_label())
        self.image_error.configure(text="Choose a valid PNG / GIF image up to 20 MB." if self.picture.reason else "")

    def remove_image(self):
        if not self.app.busy:
            self.path = ""
            self.image_changed = True
            self.refresh_image()
            self.filename.configure(text=self.file_label())
            self.image_error.configure(text="")

    def submit(self):
        if self.app.busy:
            return
        values = self.values()
        errors = item_errors(values)
        self.image_error.configure(text=errors.get("image_path", ""))
        if field_errors(self.fields, errors, self):
            return
        # Existing unavailable photos are preserved on edit. New invalid photos
        # are rejected with the explicit option to remove the image.
        if self.image_changed and self.path and self.picture.reason:
            self.image_error.configure(text="This image cannot be previewed. Choose another or remove it.")
            return
        self.error.configure(text="")
        def saved(item):
            self.original = self.values()
            self.app.show("detail", force=True, item_id=item["id"])
        self.app.run_task(lambda: self.app.gateway.save_item(values, self.item_id), saved,
                          lambda message: self.error.configure(text=message))
