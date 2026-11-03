"""Item detail with real data and an explicit owner action boundary."""
import tkinter as tk
from tkinter import ttk, messagebox
from .gateway import UserError
from .interaction_page import MessagePanel
from . import theme as t
from .page_design import note_card
from .widgets import ScrollPage, ItemImage, empty_state


class ItemPage(ScrollPage):
    def __init__(self, parent, app, item_id):
        super().__init__(parent)
        self.app, self.item_id = app, item_id
        self.messages_panel = None
        self.item = None
        self.favorited = False
        self.intended = False
        t.button(self.body, "‹ 返回商品列表", lambda: app.show("home"), "nav").pack(anchor="w", pady=(0,20))
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
        empty_state(self.area, "暂时无法查看这件商品", message, self.start)

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
        t.button(left, '放大查看图片  ↗', self.zoom_image, 'nav').pack(anchor='e', pady=8)
        note_card(left, '每件好物，都有继续的可能', '01  看清照片、描述与使用情况。\n02  在留言区确认配件和交收安排。\n03  线下见面检查，双方确认后交接。').pack(fill='x', pady=(12,20))
        if picture.reason:
            t.label(left, "卖家未上传可预览的图片，可参考右侧商品描述。", size=10, color=t.MUTED,
                    wraplength=420).pack(anchor="w", pady=10)
        right = ttk.Frame(self.area, padding=(5,0,5,20))
        right.grid(row=0, column=1, sticky="nsew")
        t.label(right, f"{item['category']}  /  {item['status']}", color=t.GREEN if item["status"] == "在售" else t.MUTED).pack(anchor="w")
        t.label(right, item["name"], size=26, bold=True, wraplength=460, justify="left").pack(anchor="w", pady=(15,20))
        t.label(right, f"¥ {item['price']:.2f}", size=34, bold=True, color=t.BLUE).pack(anchor="w", pady=(0,20))
        ttk.Separator(right).pack(fill="x", pady=12)
        t.label(right, "商品描述", bold=True).pack(anchor="w", pady=(8,10))
        t.label(right, item["description"], wraplength=440, justify="left").pack(anchor="w", pady=(0,20))
        t.label(right, "发布人", size=10, color=t.MUTED).pack(anchor="w", pady=(12,5))
        t.label(right, names.get(item["seller_id"], "校园同学"), bold=True).pack(anchor="w")
        t.label(right, f"发布时间  {item.get('created_at', '')}", size=10, color=t.MUTED).pack(anchor="w", pady=(12,5))
        t.label(right, f"更新时间  {item.get('updated_at', '')}", size=10, color=t.MUTED).pack(anchor="w")
        if item["seller_id"] == self.app.gateway.user_id():
            t.button(right, "编辑这件商品", lambda: self.app.show("publish", item_id=item["id"]), "primary").pack(fill="x", pady=(28,10))
            t.button(right, "前往我的商品管理", lambda: self.app.show("mine")).pack(fill="x")
        else:
            self.intention_button = t.button(right, "已提交意向 · 查看" if self.intended else "我想要  →", self.intention, "primary")
            self.intention_button.pack(fill="x", pady=(24, 10))
            t.label(right, "提交兴趣后，到商品留言区与卖家沟通。不会扣款或预订。", color=t.MUTED, size=10, wraplength=410, justify="left").pack(anchor="w")

        self.favorite_button = t.button(right, "♥ 已收藏" if self.favorited else "♡ 收藏这件好物", self.favorite)
        self.favorite_button.pack(fill="x", pady=12)
        self.feature_error = t.label(right, error, color=t.RED, size=10, wraplength=410, justify="left")
        self.feature_error.pack(anchor="w")
        self.messages_panel = MessagePanel(self.area, self.app, item)
        self.messages_panel.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(25, 0))
        self.messages_panel.start()

    def zoom_image(self):
        if not self.item:
            return
        window = tk.Toplevel(self.app.root)
        window.title(self.item['name']+' · 商品图片')
        window.transient(self.app.root)
        window.geometry('700x600')
        window.configure(bg=t.WHITE)
        ItemImage(window, self.item.get('image_path',''), width=660, height=470).pack(fill='both', expand=True, padx=20, pady=20)
        t.label(window, self.item['name'], bold=True).pack(pady=8)
        t.button(window, '关闭预览', window.destroy).pack(pady=(0,20))
        window.bind('<Escape>', lambda _: window.destroy())
        window.focus_set()

    def is_dirty(self):
        return bool(self.messages_panel and self.messages_panel.is_dirty())

    def favorite(self):
        def saved(value):
            self.favorited = value['favorited']
            self.favorite_button.configure(text="♥ 已收藏" if self.favorited else "♡ 收藏这件好物")
            self.feature_error.configure(text="")
            self.app.notify("已加入收藏" if self.favorited else "已取消收藏")
        self.app.run_task(lambda: self.app.gateway.features.toggle_favorite(self.item_id), saved,
                          lambda message: self.feature_error.configure(text=message))

    def intention(self):
        if self.app.busy:
            return
        if self.intended:
            self.app.show('interactions', kind='intentions')
            return
        if not messagebox.askyesno('提交购买意向？', f"向卖家表达对“{self.item['name']}”的兴趣？\n\n此操作不会扣款，也不会预订商品。", parent=self.app.root, default='no'):
            return
        def saved(_):
            self.intended = True
            self.intention_button.configure(text='已提交意向 · 查看')
            self.feature_error.configure(text='')
            self.app.notify('意向已提交，可在购买意向页查看。')
        self.app.run_task(lambda: self.app.gateway.features.create_intention(self.item_id), saved,
                          lambda message: self.feature_error.configure(text=message))
