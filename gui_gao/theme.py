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
FAMILY = "TkDefaultFont"


def setup(root):
    global FAMILY
    installed = set(font.families(root))
    FAMILY = next((f for f in ["PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC"]
                   if f in installed), "TkDefaultFont")
    for name in ["TkDefaultFont", "TkTextFont", "TkMenuFont"]:
        font.nametofont(name).configure(family=FAMILY, size=12)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background=WHITE, bordercolor=LINE, lightcolor=LINE, darkcolor=LINE)
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
    style.configure("TEntry", padding=8, fieldbackground=WHITE, bordercolor=LINE)
    style.map("TEntry", bordercolor=[("focus", BLUE), ("invalid", RED)])
    style.configure("TCombobox", padding=8, fieldbackground=WHITE, bordercolor=LINE,
                    arrowsize=14)
    style.map("TCombobox", fieldbackground=[("readonly", WHITE)],
              selectbackground=[("readonly", WHITE)], selectforeground=[("readonly", INK)])
    style.configure("TCheckbutton", background=WHITE, foreground=INK)
    style.configure("TSeparator", background=LINE)
    style.configure("Vertical.TScrollbar", background=LINE, troughcolor=WHITE,
                    borderwidth=0, arrowsize=12)
    root.configure(background=BG)


def label(parent, text="", *, size=12, bold=False, color=INK, bg=WHITE, **kwargs):
    kwargs.setdefault("anchor", "w")
    return tk.Label(parent, text=text, font=(FAMILY, size, "bold" if bold else "normal"),
                    fg=color, bg=bg, **kwargs)


def button(parent, text, command, kind="default", **kwargs):
    styles = {"primary": "Primary.TButton", "nav": "Nav.TButton", "selected": "Selected.TButton",
              "danger": "Danger.TButton", "accent": "Accent.TButton", "default": "TButton"}
    return ttk.Button(parent, text=text, command=command, style=styles[kind], cursor="hand2", **kwargs)
