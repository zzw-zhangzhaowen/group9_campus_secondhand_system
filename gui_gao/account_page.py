"""Nickname and password forms, isolated from other people's account data."""
from tkinter import ttk
from . import theme as t
from .page_design import PageBanner, StatStrip, note_card, FoldNote
from .validation import nickname_error, password_error
from .widgets import ScrollPage, Field, field_errors, page_title


class AccountPage(ScrollPage):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.banner = PageBanner(self.body, app, 'MY CAMPUS CARD / 我的校园名片',
            f"你好，{app.gateway.user['nickname']}。", '好物与日常，都在这里。让同学认出你，也照顾好账号安全。', 'account')
        self.banner.pack(fill='x', pady=(0, 20))
        self.stats = StatStrip(self.body, [('我的商品', '管理闲置', lambda: app.show('mine')),
            ('我的收藏', '接着逛逛', lambda: app.show('interactions', kind='favorites')),
            ('购买意向', '继续沟通', lambda: app.show('interactions', kind='intentions'))])
        self.stats.pack(fill='x', pady=(0, 12))
        t.button(self.body, "查看我的操作记录  →", lambda: app.show("interactions", kind="logs"), "nav").pack(anchor="e")
        area = ttk.Frame(self.body)
        area.pack(fill="x", pady=15)
        area.columnconfigure(0, weight=1)
        area.columnconfigure(1, weight=1)
        left = ttk.Frame(area, padding=(20,20,35,20), relief="solid", borderwidth=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,25))
        t.label(left, "个人资料", size=18, bold=True).pack(anchor="w", pady=(0,20))
        t.label(left, "用户名", color=t.MUTED, size=10).pack(anchor="w")
        t.label(left, app.gateway.user["username"], bold=True).pack(anchor="w", pady=(5,25))
        self.name_preview = t.label(left, app.gateway.user['nickname'], size=24, bold=True, color=t.BLUE)
        self.name_preview.pack(anchor='w', pady=(0, 15))
        self.nickname = Field(left, "昵称", app.gateway.user["nickname"], hint="2–20 个中文、字母、数字或下划线。")
        self.nickname.pack(fill="x")
        self.nickname.observe(lambda: self.name_preview.configure(text=self.nickname.get() or '你的昵称'))
        t.button(left, "保存昵称", self.save_nickname, "primary").pack(anchor="e", pady=10)
        self.original_nickname = self.nickname.get()
        note_card(left, '一张容易被记住的校园名片', '昵称会出现在商品和公开留言中。修改昵称不会改变登录用户名。').pack(fill='x', pady=(16, 12))
        self.motion_button = t.button(left, '恢复轻动效' if app.reduce_motion else '减少动态效果', self.toggle_motion, 'nav')
        self.motion_button.pack(anchor='w')
        FoldNote(left, '校园名片怎么用？', '取一个容易辨认的昵称，让同学在商品和公开留言里认出你。昵称可更新，登录用户名保持不变。').pack(fill='x', pady=15)
        right = ttk.Frame(area, padding=20, relief="solid", borderwidth=1)
        right.grid(row=0, column=1, sticky="nsew")
        t.label(right, "修改密码", size=18, bold=True).pack(anchor="w", pady=(0,20))
        self.fields = {
            "old": Field(right, "当前密码", secret=True),
            "new": Field(right, "新密码", secret=True, hint="8–32 个字符，至少一个英文字母和一个数字，无空格。"),
            "confirm": Field(right, "确认新密码", secret=True),
        }
        for field in self.fields.values():
            field.pack(fill="x")
        self.error = t.label(right, "", color=t.RED, wraplength=430, justify="left")
        self.error.pack(anchor="w", pady=(0,10))
        t.button(right, "更新密码", self.save_password, "primary").pack(anchor="e", pady=10)

    def start(self):
        def load():
            uid = self.app.gateway.user_id()
            return (len(self.app.gateway.mine()), len(self.app.gateway.features.favorite_ids()),
                    sum(r['user_id'] == uid for r in self.app.gateway.features.intentions()))
        self.app.run_task(load, self.stats.set_counts)

    def toggle_motion(self):
        self.app.reduce_motion = not self.app.reduce_motion
        self.motion_button.configure(text='恢复轻动效' if self.app.reduce_motion else '减少动态效果')
        self.banner.animate(0)

    def is_dirty(self):
        return self.nickname.get() != self.original_nickname or any(f.get() for f in self.fields.values())

    def save_nickname(self):
        value = self.nickname.get()
        error = nickname_error(value)
        if field_errors({"nickname": self.nickname}, {"nickname": error} if error else {}, self):
            return
        def saved(user):
            self.nickname.set(user["nickname"])
            self.original_nickname = user["nickname"]
            self.banner.heading.configure(text=f"你好，{user['nickname']}。")
            self.app.render_header()
            self.app.notify("昵称已保存")
        self.app.run_task(lambda: self.app.gateway.nickname(value), saved,
                          lambda message: self.nickname.show_error(message))

    def save_password(self):
        if self.app.busy:
            return
        values = {key: field.get() for key, field in self.fields.items()}
        errors = {}
        if not values["old"]:
            errors["old"] = "请输入当前密码。"
        error = password_error(values["new"])
        if error:
            errors["new"] = error
        if values["new"] != values["confirm"]:
            errors["confirm"] = "两次输入的新密码不一致。"
        if field_errors(self.fields, errors, self):
            return
        self.error.configure(text="")
        self.app.run_task(lambda: self.app.gateway.password(values["old"], values["new"]),
                          lambda _: self.app.notify("密码已更新，下次登录请使用新密码。"),
                          lambda message: self.error.configure(text=message))
        for field in self.fields.values():
            field.set("")
