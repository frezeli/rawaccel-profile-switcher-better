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

## How profiles work

RawAccel is a **driver**. The RawAccel GUI (`rawaccel.exe`) is just where you
tune your curves — when you click **Apply** it saves them to `settings.json` and
loads them into the driver. The driver keeps running after you close the GUI.

This app saves snapshots of those settings as **profiles** and switches between
them with `writer.exe`, which talks straight to the driver. So **you don't need
RawAccel open to switch profiles** — set up your curves once, close RawAccel, and
flip profiles from the tray.

## First-time setup

1. Click the tray icon and choose **Open settings**.
2. Click **Browse…** and select your **RawAccel folder** (the one that contains
   `writer.exe`).
3. In RawAccel, tune your settings and click **Apply**. Then in this app click
   **Save current…** and name the profile (e.g. *Gaming*).
4. Repeat step 3 for each setup you want (e.g. *Desktop*, *FPS*).
5. Select a profile and click **Set active** (or pick it from the tray menu) to
   switch instantly.

Selecting a profile shows its key values (sensitivity, rotation, etc.) so you can
tell them apart. To change a profile later, re-tune in RawAccel, click Apply, then
select the profile and hit **Update**.

> **Note:** if RawAccel's own window is open when you switch, it won't visually
> refresh (it only reads `settings.json` on startup) — but your mouse feel changes
> immediately. The switch always affects the live driver.

### Where are my profiles stored?

Inside your RawAccel folder, so they live next to `writer.exe`:

```
<your RawAccel folder>\
├── writer.exe
├── settings.json       # RawAccel's current settings
└── profiles\           # one .json file per profile (created by this app)
```

Your app preferences (RawAccel folder, active profile) live in
`%APPDATA%\RawAccelProfileSwitcher\config.json`.

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

| Action            | What happens                                                              |
| ----------------- | ------------------------------------------------------------------------- |
| **Save current…** | Snapshots RawAccel's `settings.json` into a new `<name>.json` profile.    |
| **Update**        | Re-snapshots your current RawAccel settings over the selected profile.    |
| Rename / Delete   | Renames or removes that `.json` file.                                     |
| **Set active**    | Runs `writer.exe <profile>.json`, which applies it straight to the driver. |

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
