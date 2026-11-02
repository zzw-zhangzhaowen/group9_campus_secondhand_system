"""Login and registration forms; passwords are cleared after submission."""
from tkinter import ttk
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
        left = ttk.Frame(self.body, padding=(25, 70, 35, 40))
        left.grid(row=0, column=0, sticky="nsew", padx=(0,35))
        t.label(left, "你的闲置，\n同学的新发现。", size=31, bold=True, justify="left").pack(anchor="w", pady=(0,25))
        t.label(left, "从一本书、一盏灯开始，\n让校园里的好物继续被使用。", color=t.MUTED,
                justify="left", size=14).pack(anchor="w", pady=(0,55))
        for line in ["01   发现校园好物", "02   轻松发布闲置", "03   管理自己的商品"]:
            t.label(left, line, size=14, color=t.BLUE).pack(anchor="w", pady=10)
        if app.demo:
            t.label(left, "独立演示账号\ngao_demo / Campus123\n\n可自由试用，演示数据会在关闭后清空。", color=t.MUTED,
                    wraplength=320, justify="left").pack(anchor="w", pady=30)
        right = ttk.Frame(self.body, padding=(5,30,10,15))
        right.grid(row=0, column=1, sticky="nsew")
        tabs = ttk.Frame(right)
        tabs.pack(fill="x", pady=(0,20))
        for route, title in [("login", "登录"), ("register", "注册账号")]:
            t.button(tabs, title, lambda r=route: app.show(r),
                     "selected" if app.route == route else "nav").pack(side="left", padx=(0,8))
        t.label(right, "加入校园二手" if self.registering else "欢迎回来", size=24, bold=True).pack(anchor="w", pady=(0,20))
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
        self.error = t.label(right, "", color=t.RED, wraplength=450, justify="left")
        self.error.pack(anchor="w", pady=(0,10))
        t.button(right, "创建账号" if self.registering else "登录", self.submit, "primary").pack(fill="x")

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

        self.app.run_task(work, completed, lambda m: self.error.configure(text=m))
        for key in ("password", "confirm"):
            if key in self.fields:
                self.fields[key].set("")
