"""Application shell: navigation, safe async service calls and session lifecycle."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import gc
import tkinter as tk
from tkinter import ttk, messagebox
from . import theme as t
from .lifecycle import StringVar
from .gateway import Gateway, UserError
from .widgets import ScrollPage


class CampusApp:
    def __init__(self, root, gateway=None, *, demo=False):
        self.root = root
        self.gateway = gateway or Gateway()
        self.demo = demo
        self.reduce_motion = False
        self.busy = False
        self.closed = False
        self.page = None
        self.route = "login"
        self.keyword, self.category, self.sort = "", "", "Newest"
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="campus-service")
        self.status = StringVar(master=root)
        t.setup(root)
        root.title("Campus Market · Design B · Group 9" + (" · Demo" if demo else ""))
        root.geometry("1180x820")
        root.minsize(1000, 700)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.report_callback_exception = self.callback_error
        self.header = ttk.Frame(root, padding=(28, 18, 28, 0))
        self.header.pack(fill="x")
        ttk.Separator(root).pack(fill="x")
        self.content = ttk.Frame(root)
        self.content.pack(fill="both", expand=True)
        self.footer = ttk.Frame(root, padding=(28, 8))
        self.footer.pack(fill="x")
        self.status_label = t.label(self.footer, textvariable=self.status, size=10, color=t.MUTED)
        self.status_label.pack(side="left", fill="x", expand=True)
        t.label(self.footer, "Demo · Temporary data is cleared on exit" if demo else "Campus Market · No online payments",
                size=10, color=t.MUTED).pack(side="right")
        # Bind once to the toplevel; do not accumulate bind_all callbacks per page.
        root.bind("<MouseWheel>", self.wheel, add="+")
        root.bind("<Button-4>", self.wheel, add="+")
        root.bind("<Button-5>", self.wheel, add="+")
        modifier = "Command" if root.tk.call("tk", "windowingsystem") == "aqua" else "Control"
        for key, route in [("1", "home"), ("2", "mine"), ("3", "account"), ("4", "interactions"), ("n", "publish")]:
            root.bind(f"<{modifier}-Key-{key}>", lambda e, r=route: self.shortcut(r))
        self.show("home" if self.gateway.user else "login", force=True)

    def shortcut(self, route):
        if self.gateway.user:
            self.show(route)
        return "break"

    def callback_error(self, exc_type, exc, tb):
        # Never echo exception values that might contain a password or file data.
        self.notify("Something went wrong. Return to Browse and try again.", error=True)

    def notify(self, message, error=False):
        self.status.set(message)
        self.status_label.configure(fg=t.RED if error else t.GREEN)

    def wheel(self, event):
        if not isinstance(self.page, ScrollPage):
            return
        target = self.root.winfo_containing(event.x_root, event.y_root)
        if target is None or isinstance(target, (tk.Text, ttk.Combobox)):
            return
        # Do not scroll the page when using a native dialog or another window.
        if target.winfo_toplevel() != self.root:
            return
        canvas = self.page.canvas
        if canvas.yview() == (0.0, 1.0):
            return
        if getattr(event, "num", None) in (4, 5):
            steps = -3 if event.num == 4 else 3
        else:
            delta = getattr(event, "delta", 0)
            if not delta:
                return
            steps = -int(delta / 120) if abs(delta) >= 120 else -int(delta)
        canvas.yview_scroll(steps, "units")

    def run_task(self, work, success, failure=None):
        """All service I/O is serialized off the Tk thread; callbacks stay in Tk."""
        if self.busy or self.closed:
            return False
        self.busy = True
        self.notify("Working, please wait…")
        self.root.configure(cursor="watch")
        disabled = []

        def freeze(widget):
            for child in widget.winfo_children():
                if isinstance(child, (ttk.Button, ttk.Entry, ttk.Combobox, ttk.Checkbutton)):
                    if not child.instate(["disabled"]):
                        disabled.append(child)
                        child.state(["disabled"])
                elif isinstance(child, tk.Text) and child.cget("state") == "normal":
                    disabled.append(child)
                    child.configure(state="disabled")
                freeze(child)
        freeze(self.header)
        freeze(self.content)
        # Collect retired page cycles on the Tcl-owning thread before allocating
        # service objects in the worker. Automatic GC remains enabled.
        gc.collect()
        future = self.executor.submit(work)

        def poll():
            if self.closed:
                return
            if not future.done():
                self.root.after(35, poll)
                return
            self.busy = False
            self.root.configure(cursor="")
            for widget in disabled:
                if widget.winfo_exists():
                    if isinstance(widget, tk.Text):
                        widget.configure(state="normal")
                    else:
                        widget.state(["!disabled"])
            try:
                result = future.result()
            except Exception as exc:
                message = str(exc) if isinstance(exc, UserError) else "Could not complete the action. Try again or check file permissions."
                self.notify(message, error=True)
                if failure:
                    failure(message)
            else:
                self.notify("Updated")
                success(result)
                if self.gateway.warning:
                    self.notify(self.gateway.warning, error=True)
                    self.gateway.warning = ""
        self.root.after(35, poll)
        return True

    def can_leave(self):
        if self.busy:
            return False
        if self.page and hasattr(self.page, "is_dirty") and self.page.is_dirty():
            return messagebox.askyesno("Discard unsaved changes?", "Your changes have not been saved. Leave this page?",
                                       parent=self.root, default="no")
        return True

    def show(self, route, *, force=False, **kwargs):
        if not force and not self.can_leave():
            return
        if route not in ("login", "register") and not self.gateway.user:
            route = "login"
        if self.page:
            self.page.destroy()
        self.route = route
        self.render_header()
        from .login_page import LoginPage
        from .home_page import HomePage, MyItemsPage
        from .item_page import ItemPage
        from .publish_page import PublishPage
        from .account_page import AccountPage
        from .interaction_page import InteractionPage
        classes = {"login": LoginPage, "register": LoginPage, "home": HomePage,
                   "mine": MyItemsPage, "detail": ItemPage, "publish": PublishPage,
                   "account": AccountPage, "interactions": InteractionPage}
        self.page = classes[route](self.content, self, **kwargs)
        self.page.pack(fill="both", expand=True)
        self.root.after_idle(self.page.start)

    def render_header(self):
        for child in self.header.winfo_children():
            child.destroy()
        top = ttk.Frame(self.header)
        top.pack(fill="x", pady=(0, 15))
        t.button(top, "⇄  Campus Market", lambda: self.show("home"), "nav").pack(side="left")
        if not self.gateway.user or self.route in ("login", "register"):
            t.label(top, "Buy and sell within your campus", color=t.MUTED).pack(side="right")
            return
        t.button(top, "+ List an item", lambda: self.show("publish"), "accent").pack(side="right", padx=(18,0))
        t.label(top, self.gateway.user["nickname"], bold=True, color=t.BLUE).pack(side="right", padx=16)
        searchbox = ttk.Frame(top)
        searchbox.pack(side="left", fill="x", expand=True, padx=30)
        self.search = ttk.Entry(searchbox)
        self.search.insert(0, self.keyword)
        self.search.pack(side="left", fill="x", expand=True)
        self.search.bind("<Return>", lambda e: self.search_now())
        t.button(searchbox, "Search", self.search_now, "primary").pack(side="left", padx=(6,0))
        nav = ttk.Frame(self.header)
        nav.pack(fill="x", pady=(0,10))
        for route, name in [("home", "Browse"), ("interactions", "Community"), ("mine", "My listings"), ("account", "Account")]:
            selected = self.route == route or (route == "home" and self.route == "detail")
            t.button(nav, name, lambda r=route: self.show(r), "selected" if selected else "nav").pack(side="left", padx=(0,8))
        t.button(nav, "Sign out", self.logout, "nav").pack(side="right")

    def search_now(self):
        if self.can_leave():
            self.keyword = self.search.get().strip()
            self.show("home", force=True)

    def logout(self):
        if self.can_leave():
            self.gateway.logout()
            self.keyword, self.category, self.sort = "", "", "Newest"
            self.show("login", force=True)
            self.notify("You have signed out")

    def close(self):
        if self.busy:
            self.notify("Please wait for the current action to finish before closing.", error=True)
            return
        if not self.can_leave():
            return
        self.closed = True
        self.gateway.logout()
        # No service operation is in flight once busy is false. Join the idle
        # worker before tearing down the Tcl interpreter and its resources.
        self.executor.shutdown(wait=True, cancel_futures=True)
        self.status = None
        self.root.destroy()


def launch(gateway=None, *, demo=False):
    root = tk.Tk()
    app = CampusApp(root, gateway, demo=demo)
    root.mainloop()
    return app
