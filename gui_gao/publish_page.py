"""Create/edit form with photo preview, validation and unsaved-change guard."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog
from . import theme as t
from .page_design import PageBanner, note_card
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
        PageBanner(self.body, app, 'START A NEW CHAPTER / 闲置新生',
            '为好物补充一些细节。' if item_id else '下一段故事，从这里开始。',
            '边填写，边预览。清楚的照片和真实描述，让沟通更轻松。', 'bag').pack(fill='x', pady=(0, 20))
        self.area = ttk.Frame(self.body)
        self.area.pack(fill="both", expand=True, pady=(10,0))

    def start(self):
        if self.item_id is None:
            self.form({})
        else:
            def load():
                item = self.app.gateway.detail(self.item_id)
                if item["seller_id"] != self.app.gateway.user_id():
                    raise UserError("只能编辑自己发布的商品。")
                return item
            self.app.run_task(load, self.form, self.failed)

    def failed(self, message):
        for child in self.area.winfo_children():
            child.destroy()
        empty_state(self.area, "无法编辑这件商品", message, self.start)

    def form(self, item):
        for child in self.area.winfo_children():
            child.destroy()
        self.path = item.get("image_path", "")
        self.area.columnconfigure(0, weight=2)
        self.area.columnconfigure(1, weight=3)
        left = ttk.Frame(self.area, padding=(0,0,30,0))
        left.grid(row=0, column=0, sticky="nsew")
        t.label(left, "商品图片（选填）", bold=True).pack(anchor="w", pady=(0,12))
        self.preview = ttk.Frame(left)
        self.preview.pack(fill="x")
        self.refresh_image()
        self.filename = t.label(left, self.file_label(), color=t.MUTED, wraplength=350, justify="left", size=10)
        self.filename.pack(anchor="w", pady=10)
        controls = ttk.Frame(left)
        controls.pack(fill="x", pady=(8,15))
        t.button(controls, "选择图片", self.choose_image).pack(side="left", padx=(0,8))
        t.button(controls, "移除图片", self.remove_image, "nav").pack(side="left")
        t.label(left, "支持 PNG / GIF；图片可选，不上传也可发布。\n图片保存在你选择的本地位置，请勿移动原文件。",
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
        note_card(left, '给下一位主人多一点了解', '01  说明商品的新旧程度。\n02  列清楚一起附送的配件。\n03  如实描述磨损或需要留意的细节。').pack(fill='x', pady=20)
        right = ttk.Frame(self.area)
        right.grid(row=0, column=1, sticky="nsew")
        self.fields = {
            "name": Field(right, "商品名称 *", item.get("name", ""), hint="最多 20 个字符，例如：Python 入门教材。"),
            "category": Field(right, "分类 *", item.get("category", CATEGORIES[0]), choices=CATEGORIES),
            "price": Field(right, "价格（¥）*", f"{item['price']:.2f}" if "price" in item else "", hint="价格需大于 0，保存时保留两位小数。"),
            "description": Field(right, "商品描述 *", item.get("description", ""), multiline=True,
                                 hint="最多 200 个字符。建议说明新旧程度、使用情况和配件。"),
        }
        for field in self.fields.values():
            field.pack(fill="x")
        self.error = t.label(right, "", color=t.RED, wraplength=490, justify="left")
        self.error.pack(anchor="w", pady=(0,12))
        buttons = ttk.Frame(right)
        buttons.pack(fill="x", pady=10)
        t.button(buttons, "保存修改" if self.item_id else "发布商品", self.submit, "primary").pack(side="right")
        t.button(buttons, "取消", lambda: self.app.show("mine" if self.item_id else "home")).pack(side="right", padx=12)
        chips = ttk.Frame(right)
        chips.pack(fill='x', pady=(6, 12))
        for text in ['使用情况：', '附带配件：', '需要留意：']:
            t.button(chips, text[:-1]+' +', lambda v=text: self.add_prompt(v), 'nav').pack(side='left', padx=(0, 5))
        for field in self.fields.values():
            field.observe(self.update_preview)
        self.update_preview()
        self.original = self.values()

    def update_preview(self):
        if not self.fields:
            return
        values = self.values()
        errors = item_errors(values)
        count = sum(key not in errors for key in ('name', 'category', 'price', 'description'))
        self.progress['value'] = count
        self.readiness.configure(text=f'信息准备度  {count} / 4  ·  图片选填')
        self.live_name.configure(text=values['name'].strip() or '你的好物名称')
        self.live_price.configure(text='¥ '+(values['price'].strip() or '—'))

    def add_prompt(self, text):
        current = self.fields['description'].get()
        updated = current + ('\n' if current else '') + text
        if len(updated) > 200:
            self.fields['description'].show_error('描述最多 200 字，请先精简内容。')
            return
        self.fields['description'].set(updated)
        self.fields['description'].input.focus_set()
        self.update_preview()

    def values(self):
        return {**{key: field.get() for key, field in self.fields.items()}, "image_path": self.path}

    def is_dirty(self):
        return self.original is not None and self.values() != self.original

    def file_label(self):
        return Path(self.path).name if self.path else "尚未选择图片"

    def refresh_image(self):
        for child in self.preview.winfo_children():
            child.destroy()
        self.picture = ItemImage(self.preview, self.path, width=330, height=235)
        self.picture.pack(fill="x")

    def choose_image(self):
        if self.app.busy:
            return
        path = filedialog.askopenfilename(parent=self.app.root, title="选择商品图片",
            filetypes=[("PNG / GIF 图片", "*.png *.gif"), ("所有文件", "*")])
        if not path:
            return
        self.path = path
        self.image_changed = True
        self.refresh_image()
        self.filename.configure(text=self.file_label())
        self.image_error.configure(text="请选择可预览的 PNG / GIF 图片（不超过 20 MB）。" if self.picture.reason else "")

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
            self.image_error.configure(text="这张图片无法预览，请重新选择或移除图片。")
            return
        self.error.configure(text="")
        def saved(item):
            self.original = self.values()
            self.app.show("detail", force=True, item_id=item["id"])
        self.app.run_task(lambda: self.app.gateway.save_item(values, self.item_id), saved,
                          lambda message: self.error.configure(text=message))
