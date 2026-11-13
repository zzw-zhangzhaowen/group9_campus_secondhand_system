"""Approved B market visual tokens, using native Tk/ttk only."""
import tkinter as tk
from tkinter import ttk, font

BLUE = "#1549DF"
INK = "#142244"
MUTED = "#6E7689"
BG = "#F5F7FC"
LINE = "#E0E5EF"
PALE = "#EDF2FF"
RED = "#B43838"
GREEN = "#19714E"
WHITE = "#FFFFFF"
LIME = "#DFFA75"
FAMILY = "Arial"


def setup(root):
    global FAMILY
    installed = set(font.families(root))
    candidates = ["SF Pro Text", "Helvetica Neue", "Segoe UI", "Arial",
                  "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", "DejaVu Sans"]
    FAMILY = next((family for family in candidates if family in installed),
                  font.nametofont("TkDefaultFont", root=root).actual("family"))
    for name in ["TkDefaultFont", "TkTextFont", "TkMenuFont"]:
        font.nametofont(name, root=root).configure(family=FAMILY, size=12)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background=WHITE, bordercolor=LINE, lightcolor=LINE, darkcolor=LINE)
    style.configure("Card.TFrame", background=WHITE, relief="solid", borderwidth=1)
    style.configure("TLabel", background=WHITE, foreground=INK, font=(FAMILY, 12))
    style.configure("TButton", background=WHITE, foreground=INK, bordercolor=LINE,
                    lightcolor=LINE, darkcolor=LINE, padding=(14, 9), width=0, font=(FAMILY, 12))
    style.map("TButton", background=[("active", BG)], foreground=[("disabled", MUTED)])
    style.configure("Primary.TButton", background=BLUE, foreground=WHITE,
                    bordercolor=BLUE, lightcolor=BLUE, darkcolor=BLUE)
    style.map("Primary.TButton", background=[("disabled", "#A4B5E0"), ("active", "#2147AA")],
              foreground=[("disabled", WHITE), ("active", WHITE)])
    style.configure("Nav.TButton", borderwidth=0, bordercolor=WHITE, lightcolor=WHITE, darkcolor=WHITE)
    style.configure("Selected.TButton", background=PALE, foreground=BLUE, bordercolor=PALE,
                    lightcolor=PALE, darkcolor=PALE)
    style.map("Selected.TButton", background=[("active", PALE)])
    style.configure("Accent.TButton", background=LIME, foreground=INK, bordercolor=LIME, lightcolor=LIME, darkcolor=LIME)
    style.map("Accent.TButton", background=[("pressed", "#C3E35D"), ("active", "#D2F268")])
    style.map("Primary.TButton", background=[("disabled", "#A4B5E0"), ("pressed", "#1037A7"), ("active", "#245CEB")], foreground=[("disabled", WHITE)])
    style.configure("Danger.TButton", foreground=RED)
    style.configure("TEntry", padding=(12, 11), fieldbackground=WHITE, bordercolor=LINE,
                    foreground=INK, font=(FAMILY, 12))
    style.map("TEntry", bordercolor=[("focus", BLUE), ("invalid", RED)])
    style.configure("TCombobox", padding=8, fieldbackground=WHITE, bordercolor=LINE,
                    arrowsize=14)
    style.map("TCombobox", fieldbackground=[("readonly", WHITE)],
              selectbackground=[("readonly", WHITE)], selectforeground=[("readonly", INK)])
    style.configure("TCheckbutton", background=WHITE, foreground=INK)
    style.configure("TSeparator", background=LINE)
    style.configure("Vertical.TScrollbar", background=LINE, troughcolor=WHITE,
                    borderwidth=0, arrowsize=12)
    # Image-backed ttk elements keep native focus, keyboard and disabled behavior.
    root._market_button_images = []
    for prefix, normal, hover, pressed, disabled in [
            ("Primary", BLUE, "#245CEB", "#1037A7", "#A4B5E0"),
            ("Accent", LIME, "#D2F268", "#C3E35D", LINE),
            ("Selected", PALE, "#E0E9FF", "#D5E0FC", BG),
            ("Nav", WHITE, BG, PALE, WHITE),
            ("", BG, PALE, LINE, BG),
            ("Danger", WHITE, "#FFF0F0", "#FFE0E0", WHITE)]:
        images = []
        for color in (normal, hover, pressed, disabled):
            image = tk.PhotoImage(master=root, width=32, height=32)
            radius = 10
            for y in range(32):
                dy = max(radius-y, y-(31-radius), 0)
                inset = round(radius-(radius*radius-dy*dy)**0.5) if dy else 0
                image.put(color, to=(inset, y, 32-inset, y+1))
            images.append(image)
        root._market_button_images.extend(images)
        element = f"Market{prefix}.border"
        style.element_create(element, "image", images[0],
                             ("disabled", images[3]), ("pressed", images[2]),
                             ("active", images[1]), border=11, sticky="nsew")
        name = f"{prefix}.TButton" if prefix else "TButton"
        style.layout(name, [(element, {"sticky": "nsew", "children": [
            ("Button.focus", {"sticky": "nsew", "children": [
                ("Button.padding", {"sticky": "nsew", "children": [
                    ("Button.label", {"sticky": "nsew"})]})]})]})])
        style.configure(name, padding=(18, 11), font=(FAMILY, 12, "bold"))
    for name, color in [("Hero", BLUE), ("Soft", PALE)]:
        image = tk.PhotoImage(master=root, width=64, height=64)
        radius = 20
        for y in range(64):
            dy = max(radius-y, y-(63-radius), 0)
            inset = round(radius-(radius*radius-dy*dy)**0.5) if dy else 0
            image.put(color, to=(inset, y, 64-inset, y+1))
        root._market_button_images.append(image)
        element = f"Market{name}.panel"
        style.element_create(element, "image", image, border=22, sticky="nsew")
        style.layout(f"{name}.TFrame", [(element, {"sticky": "nsew"})])
        style.configure(f"{name}.TFrame", background=WHITE)
    style.configure("Horizontal.TProgressbar", background=BLUE, troughcolor=PALE,
                    borderwidth=0, thickness=6)
    root.configure(background=BG)


def label(parent, text="", *, size=12, bold=False, color=INK, bg=WHITE, **kwargs):
    kwargs.setdefault("anchor", "w")
    return tk.Label(parent, text=text, font=(FAMILY, size, "bold" if bold else "normal"),
                    fg=color, bg=bg, **kwargs)


def button(parent, text, command, kind="default", **kwargs):
    styles = {"primary": "Primary.TButton", "nav": "Nav.TButton", "selected": "Selected.TButton",
              "danger": "Danger.TButton", "accent": "Accent.TButton", "default": "TButton"}
    return ttk.Button(parent, text=text, command=command, style=styles[kind], cursor="hand2", **kwargs)
