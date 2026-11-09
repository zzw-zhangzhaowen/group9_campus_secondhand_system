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
        t.label(left, "RE:CAMPUS / CAMPUS MARKET", size=10, bold=True, color=t.LIME, bg=t.BLUE).pack(anchor="w")
        t.label(left, "Your spare items.\nTheir next find.", size=29, bold=True, justify="left",
                color=t.WHITE, bg=t.BLUE).pack(anchor="w", pady=(18, 12))
        t.label(left, "Books, lamps and everyday items.\nGive them a second life on campus.", color='#DBE6FF',
                bg=t.BLUE, justify="left", size=12).pack(anchor="w")
        self.artwork = AuthArtwork(left, app)
        self.artwork.pack(anchor="center", pady=(20, 12))
        self.light_button = t.button(left, 'Turn on the lamp ✦', self.toggle_light, 'accent')
        self.light_button.pack(anchor='center')
        t.label(left, "Browse   /   List   /   Meet on campus", size=10,
                color=t.LIME, bg=t.BLUE).pack(anchor="w", pady=(12, 0))
        t.label(left, "LESS WASTE.  MORE STORIES.", size=9, color='#DBE6FF', bg=t.BLUE).pack(anchor="w", pady=(10, 0))
        right = ttk.Frame(self.body, padding=(0, 15, 8, 15))
        right.grid(row=0, column=1, sticky="nsew")
        tabs = ttk.Frame(right)
        tabs.pack(fill="x", pady=(0, 25))
        for route, title in [("login", "Sign in"), ("register", "Register")]:
            t.button(tabs, title, lambda r=route: app.show(r),
                     "selected" if app.route == route else "nav").pack(side="left", padx=(0, 8))
        t.label(right, "START YOUR CAMPUS STORY" if self.registering else "GOOD TO SEE YOU AGAIN", size=9,
                bold=True, color=t.BLUE).pack(anchor="w")
        t.label(right, "Join Campus Market" if self.registering else "Welcome back.", size=27, bold=True).pack(anchor="w", pady=(9, 8))
        t.label(right, "Find a new home for your spare items." if self.registering else "Sign in to browse and manage your items.",
                color=t.MUTED, size=11).pack(anchor="w", pady=(0, 23))
        self.fields = {}
        self.fields["username"] = Field(right, "Username", hint="3–20 characters, starting with a letter." if self.registering else "")
        if self.registering:
            self.fields["nickname"] = Field(right, "Display name", hint="2–20 letters, Chinese characters, digits or underscores.")
        self.fields["password"] = Field(right, "Password", secret=True,
            hint="8–32 characters, including a letter and a digit. No spaces." if self.registering else "")
        if self.registering:
            self.fields["confirm"] = Field(right, "Confirm password", secret=True)
        for field in self.fields.values():
            field.pack(fill="x")
            field.input.bind("<Return>", lambda e: self.submit())
        self.password_visible = False
        self.visibility_button = t.button(right, "Show password", self.toggle_password, "nav")
        self.visibility_button.pack(anchor="e", pady=(0, 5))
        self.error = t.label(right, "", color=t.RED, wraplength=450, justify="left")
        self.error.pack(anchor="w", pady=(0,10))
        t.button(right, "Create account  →" if self.registering else "Sign in and browse  →", self.submit, "primary").pack(fill="x")
        t.label(right, "Use your account to manage listings and public comments. No online payments.",
                size=10, color=t.MUTED, wraplength=380, justify="left").pack(anchor="w", pady=(16, 0))
        if app.demo and not self.registering:
            demo = tk.Frame(right, bg=t.PALE, padx=16, pady=14)
            demo.pack(fill="x", pady=(20, 0))
            t.label(demo, "Try the demo", bold=True, size=11, bg=t.PALE, color=t.BLUE).pack(anchor="w")
            t.label(demo, "Fictional demo account · Data is cleared on exit", size=10, bg=t.PALE, color=t.MUTED).pack(anchor="w", pady=5)
            t.button(demo, "Use demo account  ↗", self.fill_demo, "nav").pack(anchor="w")

    def toggle_light(self):
        lit = self.artwork.toggle_light()
        self.light_button.configure(text='Turn off the lamp ☾' if lit else 'Turn on the lamp ✦')

    def toggle_password(self):
        self.password_visible = not self.password_visible
        for key in ("password", "confirm"):
            if key in self.fields:
                self.fields[key].input.configure(show="" if self.password_visible else "•")
        self.visibility_button.configure(text="Hide password" if self.password_visible else "Show password")

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
            k: "This field is required." for k, v in values.items() if not v.strip()}
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
                self.app.notify("Account created. Sign in with your new account.")
            else:
                self.app.show("home", force=True)

        if self.password_visible:
            self.toggle_password()
        self.app.run_task(work, completed, lambda m: self.error.configure(text=m))
        for key in ("password", "confirm"):
            if key in self.fields:
                self.fields[key].set("")
