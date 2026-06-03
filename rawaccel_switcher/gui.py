"""The main settings window (Tkinter).

Lets the user point at their RawAccel directory and create / rename /
delete / apply profile slots. The window can be closed without quitting
the app; the tray icon keeps it running in the background.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from . import __app_name__, __version__
from .config import Config
from .profiles import ProfileError, ProfileManager, summarize_profile
from . import rawaccel


class MainWindow:
    """The application's main window.

    The window is created on demand and hidden (not destroyed) when closed
    so the tray icon and any in-memory state survive.
    """

    def __init__(self, config: Config, on_profile_applied=None):
        self.config = config
        self.manager = ProfileManager(config.profiles_dir())
        self.on_profile_applied = on_profile_applied

        self.root = tk.Tk()
        self.root.title(f"{__app_name__} v{__version__}")
        self.root.geometry("470x560")
        self.root.minsize(440, 500)

        # Closing the window hides it instead of exiting the program.
        self.root.protocol("WM_DELETE_WINDOW", self.hide)

        self._build_widgets()
        self.refresh()

    # ----- layout ----------------------------------------------------------
    def _build_widgets(self) -> None:
        pad = {"padx": 10, "pady": 6}

        # RawAccel directory selector
        dir_frame = ttk.LabelFrame(self.root, text="RawAccel directory")
        dir_frame.pack(fill="x", **pad)

        self.dir_var = tk.StringVar(value=self.config.rawaccel_dir)
        entry = ttk.Entry(dir_frame, textvariable=self.dir_var)
        entry.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=8)
        ttk.Button(dir_frame, text="Browse…", command=self.browse_dir).pack(
            side="left", padx=(0, 8), pady=8
        )

        # Profiles list
        list_frame = ttk.LabelFrame(self.root, text="Profiles")
        list_frame.pack(fill="both", expand=True, **pad)

        self.listbox = tk.Listbox(list_frame, activestyle="dotbox")
        self.listbox.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        self.listbox.bind("<Double-Button-1>", lambda _e: self.apply_selected())
        self.listbox.bind("<<ListboxSelect>>", lambda _e: self._show_details())

        scrollbar = ttk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side="left", fill="y", pady=8)
        self.listbox.config(yscrollcommand=scrollbar.set)

        btns = ttk.Frame(list_frame)
        btns.pack(side="left", fill="y", padx=8, pady=8)
        ttk.Button(btns, text="Save current…", command=self.save_current_profile).pack(fill="x", pady=2)
        ttk.Button(btns, text="Update", command=self.update_profile).pack(fill="x", pady=2)
        ttk.Button(btns, text="Rename", command=self.rename_profile).pack(fill="x", pady=2)
        ttk.Button(btns, text="Delete", command=self.delete_profile).pack(fill="x", pady=2)
        ttk.Separator(btns, orient="horizontal").pack(fill="x", pady=6)
        ttk.Button(btns, text="Set active", command=self.apply_selected).pack(fill="x", pady=2)

        # Selected-profile values
        details_frame = ttk.LabelFrame(self.root, text="Selected profile")
        details_frame.pack(fill="x", **pad)
        self.details_var = tk.StringVar(value="Select a profile to see its values.")
        ttk.Label(
            details_frame, textvariable=self.details_var, anchor="w", justify="left"
        ).pack(fill="x", padx=8, pady=8)

        # Status bar
        self.status_var = tk.StringVar()
        status = ttk.Label(self.root, textvariable=self.status_var, anchor="w", relief="sunken")
        status.pack(fill="x", side="bottom")

    # ----- helpers ---------------------------------------------------------
    def refresh(self) -> None:
        """Reload the profile list and status text from disk/config."""
        self.manager = ProfileManager(self.config.profiles_dir())
        self.listbox.delete(0, tk.END)
        for name in self.manager.list_profiles():
            label = f"● {name}" if name == self.config.active_profile else f"   {name}"
            self.listbox.insert(tk.END, label)
        self.details_var.set("Select a profile to see its values.")
        self._update_status()

    def _show_details(self) -> None:
        """Show the key RawAccel values for the selected profile."""
        name = self.selected_name()
        if not name:
            return
        try:
            values = summarize_profile(self.manager.read(name))
        except ProfileError as exc:
            self.details_var.set(str(exc))
            return
        if values:
            self.details_var.set(
                "\n".join(f"{label}:  {value}" for label, value in values)
            )
        else:
            self.details_var.set("(no recognisable RawAccel values in this file)")

    def _update_status(self) -> None:
        active = self.config.active_profile or "(none)"
        ok = rawaccel.is_valid_rawaccel_dir(self.config.rawaccel_dir)
        warn = "" if ok else "  —  set a valid RawAccel directory"
        self.status_var.set(f"Active profile: {active}{warn}")

    def selected_name(self) -> str | None:
        sel = self.listbox.curselection()
        if not sel:
            return None
        # Strip the active marker / leading whitespace added in refresh().
        return self.listbox.get(sel[0]).lstrip("● ").strip()

    # ----- actions ---------------------------------------------------------
    def browse_dir(self) -> None:
        chosen = filedialog.askdirectory(title="Select your RawAccel folder")
        if not chosen:
            return
        if not rawaccel.is_valid_rawaccel_dir(chosen):
            if not messagebox.askyesno(
                "writer.exe not found",
                f"'{rawaccel.WRITER_EXE}' was not found in that folder.\n\n"
                "Use it anyway?",
            ):
                return
        self.dir_var.set(chosen)
        self.config.rawaccel_dir = chosen
        self.config.save()
        self.refresh()

    def save_current_profile(self) -> None:
        """Snapshot RawAccel's current settings.json into a new profile."""
        name = simpledialog.askstring(
            "Save current settings",
            "Name this profile (captures your current RawAccel settings):",
            parent=self.root,
        )
        if name is None:
            return
        template = rawaccel.current_settings_file(self.config.rawaccel_dir)
        try:
            self.manager.create(name, template=template)
        except ProfileError as exc:
            messagebox.showerror("Cannot create profile", str(exc))
            return
        if template is None:
            messagebox.showinfo(
                "Saved with defaults",
                "RawAccel's settings.json was not found, so this profile was "
                "created with default values. Tune it in RawAccel, click Apply, "
                "then use Update to capture your settings.",
            )
        self.refresh()

    def update_profile(self) -> None:
        """Re-snapshot RawAccel's current settings into the selected profile."""
        name = self.selected_name()
        if not name:
            messagebox.showinfo("Update", "Select a profile first.")
            return
        if not messagebox.askyesno(
            "Update profile",
            f"Overwrite '{name}' with your current RawAccel settings?",
        ):
            return
        template = rawaccel.current_settings_file(self.config.rawaccel_dir)
        try:
            self.manager.overwrite(name, template)
        except ProfileError as exc:
            messagebox.showerror("Cannot update profile", str(exc))
            return
        self.refresh()

    def rename_profile(self) -> None:
        old = self.selected_name()
        if not old:
            messagebox.showinfo("Rename", "Select a profile first.")
            return
        new = simpledialog.askstring(
            "Rename profile", "New name:", initialvalue=old, parent=self.root
        )
        if new is None:
            return
        try:
            self.manager.rename(old, new)
        except ProfileError as exc:
            messagebox.showerror("Cannot rename profile", str(exc))
            return
        if self.config.active_profile == old:
            self.config.active_profile = new
            self.config.save()
        self.refresh()

    def delete_profile(self) -> None:
        name = self.selected_name()
        if not name:
            messagebox.showinfo("Delete", "Select a profile first.")
            return
        if not messagebox.askyesno("Delete profile", f"Delete profile '{name}'?"):
            return
        try:
            self.manager.delete(name)
        except ProfileError as exc:
            messagebox.showerror("Cannot delete profile", str(exc))
            return
        if self.config.active_profile == name:
            self.config.active_profile = ""
            self.config.save()
        self.refresh()

    def apply_selected(self) -> None:
        name = self.selected_name()
        if not name:
            messagebox.showinfo("Set active", "Select a profile first.")
            return
        self.apply_profile(name)

    def apply_profile(self, name: str) -> bool:
        """Apply ``name`` via writer.exe. Returns True on success."""
        try:
            path = self.manager.path_for(name)
            rawaccel.apply_profile(self.config.rawaccel_dir, path)
        except (ProfileError, rawaccel.RawAccelError) as exc:
            messagebox.showerror("Could not switch profile", str(exc))
            return False
        self.config.active_profile = name
        self.config.save()
        self.refresh()
        if self.on_profile_applied:
            self.on_profile_applied(name)
        return True

    # ----- window visibility ----------------------------------------------
    def show(self) -> None:
        self.refresh()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide(self) -> None:
        self.root.withdraw()
