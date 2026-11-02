"""Approved blue/white visual tokens, using native Tk/ttk only."""
import tkinter as tk
from tkinter import ttk, font

BLUE = "#2855C7"
INK = "#172C50"
MUTED = "#64728B"
BG = "#F4F7FC"
LINE = "#DBE2ED"
PALE = "#EAF0FF"
RED = "#B43838"
GREEN = "#19714E"
WHITE = "#FFFFFF"
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
    style.configure("TFrame", background=WHITE)
    style.configure("TLabel", background=WHITE, foreground=INK, font=(FAMILY, 12))
    style.configure("TButton", background=WHITE, foreground=INK, bordercolor=LINE,
                    lightcolor=LINE, darkcolor=LINE, padding=(14, 9), width=0, font=(FAMILY, 12))
    style.map("TButton", background=[("active", BG)], foreground=[("disabled", MUTED)])
    style.configure("Primary.TButton", background=BLUE, foreground=WHITE,
                    bordercolor=BLUE, lightcolor=BLUE, darkcolor=BLUE)
    style.map("Primary.TButton", background=[("disabled", "#A4B5E0"), ("active", "#2147AA")],
              foreground=[("disabled", WHITE), ("active", WHITE)])
    style.configure("Nav.TButton", borderwidth=0, bordercolor=WHITE, lightcolor=WHITE, darkcolor=WHITE)
    style.configure("Selected.TButton", background=PALE, foreground=BLUE, bordercolor=PALE)
    style.map("Selected.TButton", background=[("active", PALE)])
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
              "danger": "Danger.TButton", "default": "TButton"}
    return ttk.Button(parent, text=text, command=command, style=styles[kind], **kwargs)
