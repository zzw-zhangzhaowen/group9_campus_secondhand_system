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
        self.banner = PageBanner(self.body, app, 'MY CAMPUS CARD / MY PROFILE',
            f"Hello, {app.gateway.user['nickname']}.", 'Manage your profile, listings and account security.', 'account')
        self.banner.pack(fill='x', pady=(0, 20))
        self.stats = StatStrip(self.body, [('My listings', 'Manage listings', lambda: app.show('mine')),
            ('Saved items', 'View saved items', lambda: app.show('interactions', kind='favorites')),
            ('Enquiries', 'View enquiries', lambda: app.show('interactions', kind='intentions'))])
        self.stats.pack(fill='x', pady=(0, 12))
        t.button(self.body, "View my activity  →", lambda: app.show("interactions", kind="logs"), "nav").pack(anchor="e")
        area = ttk.Frame(self.body)
        area.pack(fill="x", pady=15)
        area.columnconfigure(0, weight=1)
        area.columnconfigure(1, weight=1)
        left = ttk.Frame(area, padding=(20,20,35,20), relief="solid", borderwidth=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,25))
        t.label(left, "Profile", size=18, bold=True).pack(anchor="w", pady=(0,20))
        t.label(left, "Username", color=t.MUTED, size=10).pack(anchor="w")
        t.label(left, app.gateway.user["username"], bold=True).pack(anchor="w", pady=(5,25))
        self.name_preview = t.label(left, app.gateway.user['nickname'], size=24, bold=True, color=t.BLUE)
        self.name_preview.pack(anchor='w', pady=(0, 15))
        self.nickname = Field(left, "Display name", app.gateway.user["nickname"], hint="2–20 letters, Chinese characters, digits or underscores.")
        self.nickname.pack(fill="x")
        self.nickname.observe(lambda: self.name_preview.configure(text=self.nickname.get() or 'Your display name'))
        t.button(left, "Save display name", self.save_nickname, "primary").pack(anchor="e", pady=10)
        self.original_nickname = self.nickname.get()
        note_card(left, 'Help others recognise you', 'Your display name appears on listings and public comments. Your username stays the same.').pack(fill='x', pady=(16, 12))
        self.motion_button = t.button(left, 'Enable animations' if app.reduce_motion else 'Reduce motion', self.toggle_motion, 'nav')
        self.motion_button.pack(anchor='w')
        FoldNote(left, 'About your profile', 'Choose a recognisable display name for listings and comments. You can change it without changing your username.').pack(fill='x', pady=15)
        right = ttk.Frame(area, padding=20, relief="solid", borderwidth=1)
        right.grid(row=0, column=1, sticky="nsew")
        t.label(right, "Change password", size=18, bold=True).pack(anchor="w", pady=(0,20))
        self.fields = {
            "old": Field(right, "Current password", secret=True),
            "new": Field(right, "New password", secret=True, hint="8–32 characters, including a letter and a digit. No spaces."),
            "confirm": Field(right, "Confirm new password", secret=True),
        }
        for field in self.fields.values():
            field.pack(fill="x")
        self.error = t.label(right, "", color=t.RED, wraplength=430, justify="left")
        self.error.pack(anchor="w", pady=(0,10))
        t.button(right, "Update password", self.save_password, "primary").pack(anchor="e", pady=10)

    def start(self):
        def load():
            uid = self.app.gateway.user_id()
            return (len(self.app.gateway.mine()), len(self.app.gateway.features.favorite_ids()),
                    sum(r['user_id'] == uid for r in self.app.gateway.features.intentions()))
        self.app.run_task(load, self.stats.set_counts)

    def toggle_motion(self):
        self.app.reduce_motion = not self.app.reduce_motion
        self.motion_button.configure(text='Enable animations' if self.app.reduce_motion else 'Reduce motion')
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
            self.banner.heading.configure(text=f"Hello, {user['nickname']}.")
            self.app.render_header()
            self.app.notify("Display name saved")
        self.app.run_task(lambda: self.app.gateway.nickname(value), saved,
                          lambda message: self.nickname.show_error(message))

    def save_password(self):
        if self.app.busy:
            return
        values = {key: field.get() for key, field in self.fields.items()}
        errors = {}
        if not values["old"]:
            errors["old"] = "Enter your current password."
        error = password_error(values["new"])
        if error:
            errors["new"] = error
        if values["new"] != values["confirm"]:
            errors["confirm"] = "The new passwords do not match."
        if field_errors(self.fields, errors, self):
            return
        self.error.configure(text="")
        self.app.run_task(lambda: self.app.gateway.password(values["old"], values["new"]),
                          lambda _: self.app.notify("Password updated. Use the new password next time you sign in."),
                          lambda message: self.error.configure(text=message))
        for field in self.fields.values():
            field.set("")
