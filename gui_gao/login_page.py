"""Login and registration forms; passwords are cleared after submission."""
import tkinter as tk
from tkinter import ttk
from .page_design import AuthArtwork
from . import theme as t
from .widgets import ScrollPage, Field, field_errors
from .validation import registration_errors


class LoginPage(ScrollPage):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.registering = app.route == "register"
        self.body.columnconfigure(0, weight=1)
        self.body.columnconfigure(1, weight=1)
        left = tk.Frame(self.body, bg=t.BLUE, padx=26, pady=28)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 28))
        t.label(left, "RE:CAMPUS / 好物循环计划", size=10, bold=True, color=t.LIME, bg=t.BLUE).pack(anchor="w")
        t.label(left, "你的闲置，\n同学的新发现。", size=29, bold=True, justify="left",
                color=t.WHITE, bg=t.BLUE).pack(anchor="w", pady=(18, 12))
        t.label(left, "从一本书、一盏灯开始，\n让校园里的好物继续被使用。", color='#DBE6FF',
                bg=t.BLUE, justify="left", size=12).pack(anchor="w")
        self.artwork = AuthArtwork(left, app)
        self.artwork.pack(anchor="center", pady=(20, 12))
        self.light_button = t.button(left, '点亮书桌 ✦', self.toggle_light, 'accent')
        self.light_button.pack(anchor='center')
        t.label(left, "发现好物   /   轻松发布   /   校园相遇", size=10,
                color=t.LIME, bg=t.BLUE).pack(anchor="w", pady=(12, 0))
        t.label(left, "LESS WASTE.  MORE STORIES.", size=9, color='#DBE6FF', bg=t.BLUE).pack(anchor="w", pady=(10, 0))
        right = ttk.Frame(self.body, padding=(0, 15, 8, 15))
        right.grid(row=0, column=1, sticky="nsew")
        tabs = ttk.Frame(right)
        tabs.pack(fill="x", pady=(0, 25))
        for route, title in [("login", "登录"), ("register", "注册账号")]:
            t.button(tabs, title, lambda r=route: app.show(r),
                     "selected" if app.route == route else "nav").pack(side="left", padx=(0, 8))
        t.label(right, "START YOUR CAMPUS STORY" if self.registering else "GOOD TO SEE YOU AGAIN", size=9,
                bold=True, color=t.BLUE).pack(anchor="w")
        t.label(right, "加入校园二手" if self.registering else "欢迎回来。", size=27, bold=True).pack(anchor="w", pady=(9, 8))
        t.label(right, "给闲置一个新的开始。" if self.registering else "登录，接着发现你的下一件好物。",
                color=t.MUTED, size=11).pack(anchor="w", pady=(0, 23))
        self.fields = {}
        self.fields["username"] = Field(right, "用户名", hint="3–20 个字符，以英文字母开头。" if self.registering else "")
        if self.registering:
            self.fields["nickname"] = Field(right, "昵称", hint="2–20 个中文、字母、数字或下划线。")
        self.fields["password"] = Field(right, "密码", secret=True,
            hint="8–32 个字符，至少一个英文字母和一个数字，无空格。" if self.registering else "")
        if self.registering:
            self.fields["confirm"] = Field(right, "确认密码", secret=True)
        for field in self.fields.values():
            field.pack(fill="x")
            field.input.bind("<Return>", lambda e: self.submit())
        self.password_visible = False
        self.visibility_button = t.button(right, "显示密码", self.toggle_password, "nav")
        self.visibility_button.pack(anchor="e", pady=(0, 5))
        self.error = t.label(right, "", color=t.RED, wraplength=450, justify="left")
        self.error.pack(anchor="w", pady=(0,10))
        t.button(right, "创建账号  →" if self.registering else "登录，去逛校园  →", self.submit, "primary").pack(fill="x")
        t.label(right, "账号用于管理商品和公开互动。平台不提供线上支付。",
                size=10, color=t.MUTED, wraplength=380, justify="left").pack(anchor="w", pady=(16, 0))
        if app.demo and not self.registering:
            demo = tk.Frame(right, bg=t.PALE, padx=16, pady=14)
            demo.pack(fill="x", pady=(20, 0))
            t.label(demo, "先体验一下校园生活", bold=True, size=11, bg=t.PALE, color=t.BLUE).pack(anchor="w")
            t.label(demo, "虚构演示账号 · 关闭后清空演示数据", size=10, bg=t.PALE, color=t.MUTED).pack(anchor="w", pady=5)
            t.button(demo, "填入演示账号  ↗", self.fill_demo, "nav").pack(anchor="w")

    def toggle_light(self):
        lit = self.artwork.toggle_light()
        self.light_button.configure(text='关掉灯光 ☾' if lit else '点亮书桌 ✦')

    def toggle_password(self):
        self.password_visible = not self.password_visible
        for key in ("password", "confirm"):
            if key in self.fields:
                self.fields[key].input.configure(show="" if self.password_visible else "•")
        self.visibility_button.configure(text="隐藏密码" if self.password_visible else "显示密码")

    def fill_demo(self):
        if self.app.demo:
            from .demo import DEMO_USERNAME, DEMO_PASSWORD
            self.fields["username"].set(DEMO_USERNAME)
            self.fields["password"].set(DEMO_PASSWORD)
            self.fields["username"].input.focus_set()

    def start(self):
        self.fields["username"].input.focus_set()

    def submit(self):
        if self.app.busy:
            return
        values = {key: field.get() for key, field in self.fields.items()}
        errors = registration_errors(values) if self.registering else {
            k: "请填写此项。" for k, v in values.items() if not v.strip()}
        if field_errors(self.fields, errors, self):
            return
        self.error.configure(text="")
        if self.registering:
            work = lambda: self.app.gateway.register(values["username"], values["password"], values["nickname"])
        else:
            work = lambda: self.app.gateway.login(values["username"], values["password"])

        def completed(user):
            if self.registering:
                self.app.show("login", force=True)
                self.app.page.fields["username"].set(user["username"])
                self.app.notify("注册成功，请使用新账号登录。")
            else:
                self.app.show("home", force=True)

        if self.password_visible:
            self.toggle_password()
        self.app.run_task(work, completed, lambda m: self.error.configure(text=m))
        for key in ("password", "confirm"):
            if key in self.fields:
                self.fields[key].set("")
