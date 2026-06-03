# RawAccel Profile Switcher

A small Windows tray app for managing [RawAccel](https://github.com/a1xd/rawaccel)
mouse settings. Keep several profiles (e.g. **Gaming**, **Desktop**, **FPS**) and
switch between them in one click from the system tray — no need to open RawAccel.

---

## How it works

RawAccel is a **kernel driver**. The RawAccel GUI (`rawaccel.exe`) is just where you
tune your curves — clicking **Apply** saves them to `settings.json` and loads them
into the driver. The driver keeps running after you close the GUI.

This app snapshots those settings as named **profiles** and switches between them by
calling `writer.exe` (bundled with RawAccel), which talks directly to the driver.
**You don't need RawAccel open to switch profiles.** Tune your curves once, save the
profile, close RawAccel, and flip between profiles from the tray.

Switching is **immediate** — the driver applies the new settings the moment
`writer.exe` runs. No relaunch, no reboot.

---

## Install

1. Download **`RawAccelProfileSwitcher.exe`** from the
   [latest release](../../releases/latest).
2. Double-click it — no installer needed. The icon appears in the system tray.

> You need a working [RawAccel](https://github.com/a1xd/rawaccel) install.
> This app only manages profiles; it does **not** include the driver.

---

## First-time setup

1. Click the tray icon and choose **Open settings** (or double-click it).
2. Click **Browse…** and select your **RawAccel folder** — the one that contains
   `writer.exe`.
3. In the RawAccel GUI, tune your settings and click **Apply**. Then, back in this
   app, click **Save current…** and give the profile a name (e.g. *Gaming*).
4. Repeat for each setup you want (e.g. *Desktop*, *FPS*).
5. Select a profile in the list and click **Set active** to switch to it, or pick it
   directly from the tray menu.

---

## The main window

![Main window](assets/main-window.png)

- **Profiles list** — all saved profiles. The active one is marked with a bullet (•).
  Clicking a profile shows its key values in the **Selected profile** panel below.
- **Save current…** — snapshots RawAccel's current `settings.json` into a new named
  profile.
- **Update** — re-snapshots your current RawAccel settings over the selected profile
  (use this after you tweak and Apply in RawAccel).
- **Rename / Delete** — rename or remove the selected profile file.
- **Set active** — applies the selected profile to the driver immediately via
  `writer.exe`.
- **Status bar** (bottom) — always shows which profile is currently active.

---

## The tray menu

![Tray menu](assets/tray-menu.png)

Right-clicking the tray icon shows:

- **Open settings** — opens the main window. Double-clicking the icon does the same.
- **Profile list** — every saved profile as a radio item. The active profile is
  checked. Click any profile to switch to it immediately.
- **Quit** — exits the app.

---

## Actions reference

| Action            | What happens                                                                |
| ----------------- | --------------------------------------------------------------------------- |
| **Save current…** | Copies RawAccel's `settings.json` into a new `<name>.json` profile file.   |
| **Update**        | Re-copies current RawAccel settings over an existing profile file.          |
| **Rename**        | Renames the profile's `.json` file.                                         |
| **Delete**        | Deletes the profile's `.json` file.                                         |
| **Set active**    | Runs `writer.exe <profile>.json` — applies the profile to the driver now.   |
| Tray profile item | Same as Set active — one click from anywhere.                               |

---

## Where files live

```
<your RawAccel folder>\
├── writer.exe
├── settings.json        ← RawAccel's current driver state
└── profiles\            ← one .json per profile (created by this app)
    ├── Gaming.json
    ├── Desktop.json
    └── ...
```

App preferences (RawAccel folder path, active profile name) are stored in:

```
%APPDATA%\RawAccelProfileSwitcher\config.json
```

---

## Run from source

Requires **Python 3.9+** on Windows.

```bash
git clone https://github.com/frezeli/rawaccel-profile-switcher-better.git
cd rawaccel-profile-switcher-better
pip install -r requirements.txt
python main.py
```

## Build the .exe

```bash
pip install -r requirements-dev.txt
build.bat
```

Or directly:

```bash
pyinstaller --noconfirm RawAccelProfileSwitcher.spec
```

Output: `dist\RawAccelProfileSwitcher.exe`

---

## Development

```bash
pip install -r requirements-dev.txt
pytest
```

Tests cover all non-GUI logic (profile management, RawAccel integration).

---

## License

[MIT](LICENSE) — version **0.1.2**
