# RawAccel Profile Switcher

A tiny Windows tray app for managing your [RawAccel](https://github.com/a1xd/rawaccel)
mouse settings. Keep several profiles (e.g. **Gaming**, **Desktop**, **FPS**) and
switch between them in two clicks from the system tray.

A profile is simply a RawAccel settings `.json` file. Switching a profile applies
it to the driver by running RawAccel's `writer.exe` for you.

---

## Features

- 🗂️ **Profile slots** – create, rename and delete profiles (each is a `.json` file).
- ⚡ **One-click switching** – pick a profile from the tray menu to apply it instantly.
- 🖱️ **Tray app** – runs quietly in the background; closing the window doesn't quit it.
- 📁 **Point at your install** – tell it where your RawAccel folder is, once.

---

## Install (the easy way)

1. Download **`RawAccelProfileSwitcher.exe`** from the
   [latest release](../../releases/latest).
2. Double-click it to run. No installer needed.
3. The icon appears in your system tray (bottom-right, near the clock).

> You need a working [RawAccel](https://github.com/a1xd/rawaccel) install. This app
> only manages profiles and applies them — it does **not** include the driver.

---

## First-time setup

1. Click the tray icon and choose **Open settings**.
2. Click **Browse…** and select your **RawAccel folder** (the one that contains
   `writer.exe`).
3. Click **New** to create your first profile.
4. Select a profile and click **Set active** (or pick it from the tray menu).

That's it. New profiles start from your current RawAccel settings, so you can tweak
each one in the RawAccel app and re-save it as needed.

### Where are my profiles stored?

```
%APPDATA%\RawAccelProfileSwitcher\
├── config.json        # your settings (RawAccel folder, active profile)
└── profiles\          # one .json file per profile
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

---

## Build the .exe yourself

```bash
pip install -r requirements-dev.txt
build.bat
```

Or directly with PyInstaller:

```bash
pyinstaller --noconfirm RawAccelProfileSwitcher.spec
```

The finished app lands at `dist\RawAccelProfileSwitcher.exe`.

---

## How it works

| Action            | What happens                                                        |
| ----------------- | ------------------------------------------------------------------- |
| Create profile    | Writes a new `<name>.json` (copied from your current settings).     |
| Rename / Delete   | Renames or removes that `.json` file.                               |
| **Set active**    | Runs `writer.exe <profile>.json`, which applies it to the driver.   |

---

## Development

Run the test suite (covers the non-GUI logic):

```bash
pip install -r requirements-dev.txt
pytest
```

---

## License

[MIT](LICENSE) — version **0.1.2**.
