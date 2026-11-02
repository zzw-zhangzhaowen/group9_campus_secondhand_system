"""GAO JINGYAN's Tkinter frontend. Importing this package opens no window."""


def main():
    """Entry point consumed by the team's unchanged ``main.py --gui``."""
    from .app import launch
    launch()


__all__ = ["main"]
