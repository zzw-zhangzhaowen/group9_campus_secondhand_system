"""Nickname and password forms, isolated from other people's account data."""
from tkinter import ttk
from . import theme as t
from .validation import nickname_error, password_error
from .widgets import ScrollPage, Field, field_errors, page_title


class AccountPage(ScrollPage):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        page_title(self.body, "账号设置", "让同学认出你，也照顾好账号安全。")
        area = ttk.Frame(self.body)
        area.pack(fill="x", pady=15)
        area.columnconfigure(0, weight=1)
        area.columnconfigure(1, weight=1)
        left = ttk.Frame(area, padding=(20,20,35,20), relief="solid", borderwidth=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,25))
        t.label(left, "个人资料", size=18, bold=True).pack(anchor="w", pady=(0,20))
        t.label(left, "用户名", color=t.MUTED, size=10).pack(anchor="w")
        t.label(left, app.gateway.user["username"], bold=True).pack(anchor="w", pady=(5,25))
        self.nickname = Field(left, "昵称", app.gateway.user["nickname"], hint="2–20 个中文、字母、数字或下划线。")
        self.nickname.pack(fill="x")
        t.button(left, "保存昵称", self.save_nickname, "primary").pack(anchor="e", pady=10)
        self.original_nickname = self.nickname.get()
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
        pass

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
