"""System tray icon (pystray).

The tray menu lets the user open the settings window, switch directly to
any profile, and quit. The menu is built dynamically so newly created
profiles appear without restarting the app.
"""

from __future__ import annotations

from typing import Callable, List

import pystray

from . import __app_name__
from .icon import make_icon


class TrayIcon:
    """A thin wrapper around :class:`pystray.Icon`.

    Parameters
    ----------
    list_profiles:
        Callable returning the current list of profile names.
    active_profile:
        Callable returning the name of the active profile (or "").
    on_show:
        Called when the user asks to open the window.
    on_select:
        Called with a profile name when the user picks one from the menu.
    on_quit:
        Called when the user chooses Quit.
    """

    def __init__(
        self,
        list_profiles: Callable[[], List[str]],
        active_profile: Callable[[], str],
        on_show: Callable[[], None],
        on_select: Callable[[str], None],
        on_quit: Callable[[], None],
    ):
        self._list_profiles = list_profiles
        self._active_profile = active_profile
        self._on_show = on_show
        self._on_select = on_select
        self._on_quit = on_quit

        self.icon = pystray.Icon(
            "rawaccel_profile_switcher",
            icon=make_icon(),
            title=__app_name__,
            menu=pystray.Menu(self._build_menu),
        )

    def _build_menu(self):
        yield pystray.MenuItem("Open settings", lambda: self._on_show(), default=True)
        yield pystray.Menu.SEPARATOR

        profiles = self._list_profiles()
        if profiles:
            active = self._active_profile()
            for name in profiles:
                yield pystray.MenuItem(
                    name,
                    self._make_select(name),
                    checked=lambda item, n=name: n == active,
                    radio=True,
                )
        else:
            yield pystray.MenuItem("(no profiles yet)", None, enabled=False)

        yield pystray.Menu.SEPARATOR
        yield pystray.MenuItem("Quit", lambda: self._quit())

    def _make_select(self, name: str):
        return lambda: self._on_select(name)

    def _quit(self):
        self._on_quit()
        self.icon.stop()

    def refresh(self) -> None:
        """Redraw the menu (call after profiles change)."""
        try:
            self.icon.update_menu()
        except Exception:
            # update_menu may be a no-op before the icon is running.
            pass

    def run(self) -> None:
        """Run the tray icon loop (blocking)."""
        self.icon.run()

    def stop(self) -> None:
        self.icon.stop()
