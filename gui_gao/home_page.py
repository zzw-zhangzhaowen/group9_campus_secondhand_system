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
                    ('书籍', 'book', '新学期书桌'), ('电子产品', 'keyboard', '学习好搭档'),
                    ('生活用品', 'bag', '宿舍小日子')]):
                tile = ttk.Frame(collections, padding=12, relief='solid', borderwidth=1)
                tile.grid(row=0, column=i, sticky='nsew', padx=(0, 12))
                collections.columnconfigure(i, weight=1, uniform='collection')
                ItemImage(tile, str(Path(__file__).parent/'assets'/f'{image}.png'), width=70, height=65).pack(side='right')
                t.button(tile, title+' ↗', lambda c=category: self.filter(c), 'nav').pack(side='left')
        page_title(self.body, "发现校园好物", "找到需要的，也让喜欢的继续。")
        filters = ttk.Frame(self.body)
        filters.pack(fill="x", pady=(8,16))
        for category in ("",) + CATEGORIES:
            t.button(filters, category or "全部商品", lambda c=category: self.filter(c),
                     "selected" if category == app.category else "nav").pack(side="left", padx=(0,6))
        self.sort = ttk.Combobox(filters, values=SORTS, state="readonly", width=16)
        self.sort.set(app.sort)
        self.sort.pack(side="right")
        self.sort.bind("<<ComboboxSelected>>", self.sort_changed)
        summary = ttk.Frame(self.body)
        summary.pack(fill="x", pady=(0,15))
        self.count = t.label(summary, "正在加载商品…", color=t.MUTED)
        self.count.pack(side="left")
        t.button(summary, "刷新", self.start, "nav").pack(side="right")
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
        self.count.configure(text="商品加载失败")
        empty_state(self.results, "暂时无法加载", message, self.start)

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
        label = f"共 {count} 件在售商品"
        if self.app.keyword:
            label = f"“{self.app.keyword}” · {label}"
        self.count.configure(text=label)
        if not count:
            empty_state(self.results, "还没有找到合适的好物", "换个关键词或分类试试，也可以发布你的第一件闲置。",
                        self.reset_filters, "查看全部商品")
            return
        for column in range(5):
            self.results.columnconfigure(column, weight=1 if column < self.columns else 0, uniform="cards" if column < self.columns else "")
        start = self.page_number * self.PAGE_SIZE
        for index, item in enumerate(self.items[start:start+self.PAGE_SIZE]):
            card = ttk.Frame(self.results, padding=(0,0,0,18))
            card.grid(row=index//self.columns, column=index%self.columns, sticky="nsew", padx=8, pady=10)
            picture = ItemImage(card, item.get("image_path", ""), item["category"], width=190, height=170)
            picture.pack(fill="x")
            picture.bind("<Button-1>", lambda e, i=item["id"]: self.app.show("detail", item_id=i))
            picture.configure(cursor="hand2")
            content = ttk.Frame(card, padding=(1,12,1,0))
            content.pack(fill="x")
            t.label(content, item["category"], size=10, color=t.MUTED).pack(anchor="w")
            t.label(content, item["name"], size=13, bold=True, wraplength=200, justify="left").pack(anchor="w", pady=(5,8))
            t.label(content, f"¥ {item['price']:.2f}", size=22, bold=True, color=t.INK).pack(anchor="w")
            seller = self.names.get(item["seller_id"], "校园同学")
            t.label(content, seller, size=10, color=t.MUTED).pack(anchor="w", pady=(8,8))
            t.button(content, "查看详情", lambda i=item["id"]: self.app.show("detail", item_id=i)).pack(fill="x")
        total = (count + self.PAGE_SIZE - 1) // self.PAGE_SIZE
        previous = t.button(self.pagination, "上一页", lambda: self.turn(-1))
        previous.pack(side="left")
        if self.page_number == 0:
            previous.state(["disabled"])
        t.label(self.pagination, f"第 {self.page_number+1} / {total} 页", color=t.MUTED).pack(side="left", padx=20)
        following = t.button(self.pagination, "下一页", lambda: self.turn(1))
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
        self.filter_value = "全部"
        PageBanner(self.body, app, 'MY LITTLE STORE / 我的闲置架', '让闲置继续发光。',
                   '整理、更新、再出发。每件好物都有下一位主人。', 'keyboard').pack(fill='x', pady=(0,20))
        self.stats = StatStrip(self.body, [('全部商品', '看看我的闲置', lambda: self.filter('全部')),
            ('正在出售', '管理在售商品', lambda: self.filter('在售')),
            ('暂时收起', '查看下架商品', lambda: self.filter('已下架'))])
        self.stats.pack(fill='x', pady=(0,18))
        self.tabs = ttk.Frame(self.body)
        self.tabs.pack(fill="x", pady=(5,18))
        self.tab_buttons = {}
        for value in ["全部", "在售", "已下架"]:
            button = t.button(self.tabs, value, lambda v=value: self.filter(v), "selected" if value == "全部" else "nav")
            button.pack(side="left", padx=(0,8))
            self.tab_buttons[value] = button
        t.button(self.tabs, "+ 发布闲置", lambda: app.show("publish"), "primary").pack(side="right")
        t.button(self.tabs, "刷新", self.start, "nav").pack(side="right", padx=10)
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
        empty_state(self.list, "暂时无法加载你的商品", message, self.start)

    def render(self):
        self.clear()
        self.stats.set_counts([len(self.items), sum(i['status']=='在售' for i in self.items), sum(i['status']=='已下架' for i in self.items)])
        for value, button in self.tab_buttons.items():
            count = len([i for i in self.items if value == "全部" or i["status"] == value])
            button.configure(text=f"{value}  {count}", style="Selected.TButton" if value == self.filter_value else "Nav.TButton")
        items = [i for i in self.items if self.filter_value == "全部" or i["status"] == self.filter_value]
        if not items:
            empty_state(self.list, "这里还没有商品", "发布一件闲置，让它遇见新的主人。",
                        lambda: self.app.show("publish"), "发布闲置")
            return
        for item in items:
            row = ttk.Frame(self.list, padding=(12,14), relief="solid", borderwidth=1)
            row.pack(fill="x", pady=(0,12))
            ItemImage(row, item.get("image_path", ""), width=95, height=80).pack(side="left", padx=(0,20))
            info = ttk.Frame(row)
            info.pack(side="left", fill="x", expand=True)
            t.label(info, item["name"], size=14, bold=True).pack(anchor="w")
            t.label(info, f"{item['category']}   ·   ¥ {item['price']:.2f}", color=t.MUTED).pack(anchor="w", pady=6)
            t.label(info, item["status"], color=t.GREEN if item["status"] == "在售" else t.MUTED, size=10).pack(anchor="w")
            actions = ttk.Frame(row)
            actions.pack(side="right")
            t.button(actions, "查看", lambda i=item["id"]: self.app.show("detail", item_id=i), "nav").pack(side="left")
            t.button(actions, "编辑", lambda i=item["id"]: self.app.show("publish", item_id=i)).pack(side="left", padx=6)
            action = "remove" if item["status"] == "在售" else "restore"
            t.button(actions, "下架" if action == "remove" else "重新上架",
                     lambda i=item, a=action: self.change(i, a)).pack(side="left", padx=6)
            t.button(actions, "删除", lambda i=item: self.change(i, "delete"), "danger").pack(side="left", padx=6)

    def change(self, item, action):
        if self.app.busy:
            return
        if action in ("delete", "remove"):
            verb = "永久删除" if action == "delete" else "下架"
            consequence = "此操作无法通过前端恢复。" if action == "delete" else "下架后将从公开列表隐藏，你可以重新上架。"
            if not messagebox.askyesno(f"{verb}商品？", f"{verb}“{item['name']}”？\n\n{consequence}",
                                      parent=self.app.root, default="no"):
                return
        def complete(_):
            self.start()
        self.app.run_task(lambda: self.app.gateway.change_item(action, item["id"]), complete)
