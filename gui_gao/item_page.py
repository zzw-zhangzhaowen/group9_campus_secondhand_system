"""Item detail with real data and an explicit owner action boundary."""
from tkinter import ttk
from . import theme as t
from .widgets import ScrollPage, ItemImage, empty_state


class ItemPage(ScrollPage):
    def __init__(self, parent, app, item_id):
        super().__init__(parent)
        self.app, self.item_id = app, item_id
        t.button(self.body, "‹ 返回商品列表", lambda: app.show("home"), "nav").pack(anchor="w", pady=(0,20))
        self.area = ttk.Frame(self.body)
        self.area.pack(fill="both", expand=True)

    def start(self):
        def load():
            item = self.app.gateway.detail(self.item_id)
            return item, self.app.gateway.seller_names([item])
        self.app.run_task(load, self.render, self.failed)

    def failed(self, message):
        for child in self.area.winfo_children():
            child.destroy()
        empty_state(self.area, "暂时无法查看这件商品", message, self.start)

    def render(self, data):
        item, names = data
        for child in self.area.winfo_children():
            child.destroy()
        self.area.columnconfigure(0, weight=1)
        self.area.columnconfigure(1, weight=1)
        left = ttk.Frame(self.area)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,30))
        picture = ItemImage(left, item.get("image_path", ""), item["category"], width=460, height=370)
        picture.pack(fill="x")
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
            t.label(right, "当前可浏览商品；联系卖家功能暂未开放。", color=t.MUTED, size=10,
                    wraplength=440, justify="left").pack(anchor="w", pady=(28,0))
