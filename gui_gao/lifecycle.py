"""Release widget-owned Tcl variables while their owner is still on the UI thread."""
import tkinter as tk


class _OwnedVariable:
    def __init__(self, master, **kwargs):
        self._released = False
        super().__init__(master=master, **kwargs)
        master.bind("<Destroy>", self._owner_destroyed, add="+")

    def _owner_destroyed(self, event):
        if event.widget is self._root_owner:
            self._release()

    def _release(self):
        if not self._released:
            self._released = True
            super().__del__()

    def __del__(self):
        if not getattr(self, "_released", True):
            super().__del__()


class StringVar(_OwnedVariable, tk.StringVar):
    def __init__(self, master, **kwargs):
        self._root_owner = master
        super().__init__(master, **kwargs)


class BooleanVar(_OwnedVariable, tk.BooleanVar):
    def __init__(self, master, **kwargs):
        self._root_owner = master
        super().__init__(master, **kwargs)
