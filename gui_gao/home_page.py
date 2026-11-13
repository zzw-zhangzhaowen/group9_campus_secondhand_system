"""Searchable marketplace and owner-only listing management."""
from pathlib import Path
from tkinter import ttk, messagebox
from . import theme as t
from .page_design import PageBanner, StatStrip
from .widgets import ScrollPage, ItemImage, page_title, empty_state, MarketHero
from .validation import CATEGORIES, SORTS


class HomePage(ScrollPage):
    PAGE_SIZE = 12

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.items, self.names, self.page_number = [], {}, 0
        self.columns = 5
        if not app.keyword and not app.category:
            MarketHero(self.body, app).pack(fill="x", pady=(0, 24))
        if not app.keyword and not app.category:
            collections = ttk.Frame(self.body)
            collections.pack(fill='x', pady=(0, 25))
            for i, (category, image, title) in enumerate([
                    ('Books', 'book', 'Books for term'), ('Electronics', 'keyboard', 'Study essentials'),
                    ('Home & Living', 'bag', 'Room essentials')]):
                tile = ttk.Frame(collections, padding=12, relief='solid', borderwidth=1)
                tile.grid(row=0, column=i, sticky='nsew', padx=(0, 12))
                collections.columnconfigure(i, weight=1, uniform='collection')
                ItemImage(tile, str(Path(__file__).parent/'assets'/f'{image}.png'), width=70, height=65).pack(side='right')
                t.button(tile, title+' ↗', lambda c=category: self.filter(c), 'nav').pack(side='left')
        page_title(self.body, "Browse Campus Market", "Find what you need. Pass on what you no longer use.")
        filters = ttk.Frame(self.body)
        filters.pack(fill="x", pady=(8,16))
        for category in ("",) + CATEGORIES:
            t.button(filters, category or "All items", lambda c=category: self.filter(c),
                     "selected" if category == app.category else "nav").pack(side="left", padx=(0,6))
        self.sort = ttk.Combobox(filters, values=SORTS, state="readonly", width=16)
        self.sort.set(app.sort)
        self.sort.pack(side="right")
        self.sort.bind("<<ComboboxSelected>>", self.sort_changed)
        summary = ttk.Frame(self.body)
        summary.pack(fill="x", pady=(0,15))
        self.count = t.label(summary, "Loading items…", color=t.MUTED)
        self.count.pack(side="left")
        t.button(summary, "Refresh", self.start, "nav").pack(side="right")
        self.results = ttk.Frame(self.body)
        self.results.pack(fill="both", expand=True)
        self.pagination = ttk.Frame(self.body)
        self.pagination.pack(fill="x", pady=(15,0))
        self.resize_job = None
        self.results.bind("<Configure>", self.resized)

    def resized(self, event):
        columns = 5 if event.width >= 1180 else 4 if event.width >= 920 else 3
        if columns != self.columns and self.items:
            self.columns = columns
            if self.resize_job:
                self.after_cancel(self.resize_job)
            self.resize_job = self.after(120, self.render)

    def start(self):
        if self.app.busy:
            return
        def load():
            items = self.app.gateway.browse(self.app.keyword, self.app.category, self.app.sort)
            return items, self.app.gateway.seller_names(items)
        self.app.run_task(load, self.loaded, self.failed)

    def loaded(self, result):
        self.items, self.names = result
        self.page_number = 0
        self.render()

    def failed(self, message):
        self.items = []
        self.clear()
        self.count.configure(text="Could not load items")
        empty_state(self.results, "Could not load this page", message, self.start)

    def filter(self, category):
        self.app.category = category
        self.app.show("home")

    def sort_changed(self, event=None):
        if not self.app.busy:
            self.app.sort = self.sort.get()
            self.start()

    def clear(self):
        for container in (self.results, self.pagination):
            for child in container.winfo_children():
                child.destroy()

    def render(self):
        self.resize_job = None
        width = self.results.winfo_width()
        if width > 1:
            self.columns = 5 if width >= 1180 else 4 if width >= 920 else 3
        self.clear()
        count = len(self.items)
        label = f"{count} available items"
        if self.app.keyword:
            label = f"“{self.app.keyword}” · {label}"
        self.count.configure(text=label)
        if not count:
            empty_state(self.results, "No matching items", "Try another search or category, or list your first item.",
                        self.reset_filters, "Browse all items")
            return
        for column in range(5):
            self.results.columnconfigure(column, weight=1 if column < self.columns else 0, uniform="cards" if column < self.columns else "")
        start = self.page_number * self.PAGE_SIZE
        for index, item in enumerate(self.items[start:start+self.PAGE_SIZE]):
            card = ttk.Frame(self.results, padding=(12,12,12,18), style="Card.TFrame")
            card.grid(row=index//self.columns, column=index%self.columns, sticky="nsew", padx=8, pady=10)
            picture = ItemImage(card, item.get("image_path", ""), item["category"], width=190, height=170)
            picture.pack(fill="x")
            picture.bind("<Button-1>", lambda e, i=item["id"]: self.app.show("detail", item_id=i))
            picture.configure(cursor="hand2")
            content = ttk.Frame(card, padding=(4,14,4,0))
            content.pack(fill="x")
            t.label(content, item["category"], size=10, color=t.MUTED).pack(anchor="w")
            t.label(content, item["name"], size=13, bold=True, wraplength=200, justify="left").pack(anchor="w", pady=(5,8))
            t.label(content, f"¥ {item['price']:.2f}", size=22, bold=True, color=t.INK).pack(anchor="w")
            seller = self.names.get(item["seller_id"], "Student")
            t.label(content, seller, size=10, color=t.MUTED).pack(anchor="w", pady=(8,8))
            t.button(content, "View details", lambda i=item["id"]: self.app.show("detail", item_id=i)).pack(fill="x")
        total = (count + self.PAGE_SIZE - 1) // self.PAGE_SIZE
        previous = t.button(self.pagination, "Previous", lambda: self.turn(-1))
        previous.pack(side="left")
        if self.page_number == 0:
            previous.state(["disabled"])
        t.label(self.pagination, f"Page {self.page_number+1} / {total}", color=t.MUTED).pack(side="left", padx=20)
        following = t.button(self.pagination, "Next", lambda: self.turn(1))
        following.pack(side="left")
        if self.page_number + 1 >= total:
            following.state(["disabled"])

    def turn(self, direction):
        if self.app.busy:
            return
        self.page_number += direction
        self.render()
        self.canvas.yview_moveto(0)

    def reset_filters(self):
        self.app.keyword, self.app.category = "", ""
        self.app.show("home")

    def destroy(self):
        if self.resize_job:
            self.after_cancel(self.resize_job)
        super().destroy()


class MyItemsPage(ScrollPage):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.items = []
        self.filter_value = "All"
        PageBanner(self.body, app, 'MY LITTLE STORE / MY LISTINGS', 'Manage your listings.',
                   'Update details, take items off sale or list them again.', 'keyboard').pack(fill='x', pady=(0,20))
        self.stats = StatStrip(self.body, [('All items', 'View my listings', lambda: self.filter('All')),
            ('Available', 'Manage available items', lambda: self.filter('Available')),
            ('Off sale', 'View inactive items', lambda: self.filter('Off sale'))])
        self.stats.pack(fill='x', pady=(0,18))
        self.tabs = ttk.Frame(self.body)
        self.tabs.pack(fill="x", pady=(5,18))
        self.tab_buttons = {}
        for value in ["All", "Available", "Off sale"]:
            button = t.button(self.tabs, value, lambda v=value: self.filter(v), "selected" if value == "All" else "nav")
            button.pack(side="left", padx=(0,8))
            self.tab_buttons[value] = button
        t.button(self.tabs, "+ List an item", lambda: app.show("publish"), "primary").pack(side="right")
        t.button(self.tabs, "Refresh", self.start, "nav").pack(side="right", padx=10)
        self.list = ttk.Frame(self.body)
        self.list.pack(fill="both", expand=True)

    def start(self):
        self.app.run_task(self.app.gateway.mine, self.loaded, self.failed)

    def loaded(self, items):
        self.items = items
        self.render()

    def filter(self, value):
        self.filter_value = value
        self.render()

    def clear(self):
        for child in self.list.winfo_children():
            child.destroy()

    def failed(self, message):
        self.clear()
        empty_state(self.list, "Could not load your listings", message, self.start)

    def render(self):
        self.clear()
        self.stats.set_counts([len(self.items), sum(i['status']=='Available' for i in self.items), sum(i['status']=='Off sale' for i in self.items)])
        for value, button in self.tab_buttons.items():
            count = len([i for i in self.items if value == "All" or i["status"] == value])
            button.configure(text=f"{value}  {count}", style="Selected.TButton" if value == self.filter_value else "Nav.TButton")
        items = [i for i in self.items if self.filter_value == "All" or i["status"] == self.filter_value]
        if not items:
            empty_state(self.list, "No items here yet", "List an item you no longer need.",
                        lambda: self.app.show("publish"), "List an item")
            return
        for item in items:
            row = ttk.Frame(self.list, padding=(12,14), relief="solid", borderwidth=1)
            row.pack(fill="x", pady=(0,12))
            ItemImage(row, item.get("image_path", ""), width=95, height=80).pack(side="left", padx=(0,20))
            info = ttk.Frame(row)
            info.pack(side="left", fill="x", expand=True)
            t.label(info, item["name"], size=14, bold=True).pack(anchor="w")
            t.label(info, f"{item['category']}   ·   ¥ {item['price']:.2f}", color=t.MUTED).pack(anchor="w", pady=6)
            t.label(info, item["status"], color=t.GREEN if item["status"] == "Available" else t.MUTED, size=10).pack(anchor="w")
            actions = ttk.Frame(row)
            actions.pack(side="right")
            t.button(actions, "View", lambda i=item["id"]: self.app.show("detail", item_id=i), "nav").pack(side="left")
            t.button(actions, "Edit", lambda i=item["id"]: self.app.show("publish", item_id=i)).pack(side="left", padx=6)
            action = "remove" if item["status"] == "Available" else "restore"
            t.button(actions, "Take off sale" if action == "remove" else "Relist",
                     lambda i=item, a=action: self.change(i, a)).pack(side="left", padx=6)
            t.button(actions, "Delete", lambda i=item: self.change(i, "delete"), "danger").pack(side="left", padx=6)

    def change(self, item, action):
        if self.app.busy:
            return
        if action in ("delete", "remove"):
            verb = "Delete permanently" if action == "delete" else "Take off sale"
            consequence = "This action cannot be undone." if action == "delete" else "The item will be hidden from Browse. You can relist it later."
            if not messagebox.askyesno(f"{verb} item?", f"{verb} “{item['name']}”?\n\n{consequence}",
                                      parent=self.app.root, default="no"):
                return
        def complete(_):
            self.start()
        self.app.run_task(lambda: self.app.gateway.change_item(action, item["id"]), complete)
