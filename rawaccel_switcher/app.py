"""Application wiring.

Runs the Tkinter window on the main thread and the pystray tray icon on a
background thread. Tray callbacks are marshalled back onto the Tk thread
with ``root.after`` because Tkinter is not thread safe.
"""

from __future__ import annotations

import threading

from .config import Config
from .gui import MainWindow
from .tray import TrayIcon


class App:
    def __init__(self):
        self.config = Config.load()
        self.config.profiles_dir().mkdir(parents=True, exist_ok=True)

        self.window = MainWindow(self.config, on_profile_applied=self._profile_applied)
        # Start hidden: the app lives in the tray.
        self.window.hide()

        self.tray = TrayIcon(
            list_profiles=lambda: self.window.manager.list_profiles(),
            active_profile=lambda: self.config.active_profile,
            on_show=self._show_window,
            on_select=self._select_profile,
            on_quit=self._quit,
        )

    # ----- tray -> tk marshalling -----------------------------------------
    def _show_window(self) -> None:
        self.window.root.after(0, self.window.show)

    def _select_profile(self, name: str) -> None:
        self.window.root.after(0, lambda: self.window.apply_profile(name))

    def _profile_applied(self, _name: str) -> None:
        # Called on the Tk thread after a successful switch; refresh the tray
        # so the checkmark moves to the new active profile.
        self.tray.refresh()

    def _quit(self) -> None:
        self.window.root.after(0, self.window.root.quit)

    # ----- run -------------------------------------------------------------
    def run(self) -> None:
        tray_thread = threading.Thread(target=self.tray.run, daemon=True)
        tray_thread.start()
        try:
            self.window.root.mainloop()
        finally:
            self.tray.stop()


def main() -> None:
    App().run()
