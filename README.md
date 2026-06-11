# ⬇️ Ultimate Download MP4

A **Windows** desktop app that downloads **videos and audio** from **TikTok, YouTube, Instagram and X/Twitter**, always in the **best available quality**, with automatic platform detection and a modern dark-themed interface.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6)
![GUI](https://img.shields.io/badge/UI-CustomTkinter-25F4EE)
![Engine](https://img.shields.io/badge/Engine-yt--dlp-FF0033)

---

## 🌐 Supported platforms

| Platform | Content | Saved to |
|---|---|---|
| **TikTok** | Videos (without watermark) | `Downloads/TikTok` |
| **YouTube** | Videos, **Shorts**, **playlists**, recorded **lives** | `Downloads/YouTube` |
| **Instagram** | Posts, **Reels**, IGTV, public videos | `Downloads/Instagram` |
| **X / Twitter** | Videos posted in tweets | `Downloads/Twitter` |
| *Other sites* | Anything else yt-dlp supports (best effort) | `Downloads/Outros` |

> The app **detects the platform automatically** from the pasted link, shows the
> **platform name + icon**, the **thumbnail**, and the **content info**
> (title, author, resolution, duration and estimated size) **before** downloading.

---

## ✨ Features

- 🔍 **Automatic platform detection** from the link (with a "Paste" button).
- 🏷️ **Platform name and icon** shown for the detected link.
- 🖼️ **Thumbnail preview** before downloading.
- ⬇️ **Video (MP4)** download in the **best quality** (via `yt-dlp`).
- 🎵 **Audio-only (MP3, 192 kbps)** — choose video *or* audio when available.
- 🗂️ **Files organized per platform** in separate subfolders.
- 📺 **YouTube playlists**: downloads every item into its own folder.
- 🏷️ **Metadata kept** (title / author) embedded when FFmpeg is available.
- ℹ️ Shows **resolution, estimated size and duration** before the download.
- 🎨 **Modern, dark, responsive** interface (CustomTkinter).
- 🌐 **Bilingual UI (English / Portuguese)** with a flag switcher.
- 📊 **Real-time progress bar** + speed, size and ETA (and item X/N for playlists).
- 📝 **Activity log** with detailed status of each step.
- 📁 **Destination folder selector** (saved between sessions).
- ⏹️ **Cancel** a download at any time.
- 🧵 **Threaded**: the interface **never freezes** during downloads.
- 🕘 **History** of recent downloads (platform + MP4/MP3 badge + "Open folder").
- 🔔 Native **notifications** when finished.
- 🧩 **Modular platform system** — add new sites without touching the UI.
- 🔄 **Update check** (optional/configurable).
- 💾 **Settings stored in JSON** (theme, quality, notifications, etc.).
- 🛡️ **Friendly error handling** (private/login-required content, 404, timeouts…).

---

## 📥 Download (end users)

> **Requirements:** Windows 10/11 (64-bit). **No** Python installation needed.

- Build the installer yourself (see below) or grab `UltimateDownloadMP4-Setup-2.0.0.exe`.
- Run the Setup and follow the wizard (Next → Accept the license → Install → Finish).
- If **Windows SmartScreen** shows a warning, click **"More info" → "Run anyway"**
  (normal for apps without a paid code-signing certificate).

**About MP3:** Video (MP4) downloads work right away. For audio (MP3), the first
time you use it the app downloads FFmpeg automatically (once, then cached).

---

## 📂 Project structure

```
Ultimate Download MP4/
├── main.py                       # App entry point
├── requirements.txt              # Dependencies
├── build.bat                     # Builds the .exe with PyInstaller
├── build_installer.bat           # Builds the Setup.exe with Inno Setup
├── installer.iss                 # Inno Setup installer script
├── run.bat                       # Runs in development mode
├── LICENSE.txt                   # Terms shown by the installer
├── README.md
├── assets/
│   ├── create_icon.py            # Generates icon.ico automatically
│   └── create_installer_images.py# Generates the wizard images
└── src/
    ├── __init__.py               # Version, app name, repo
    ├── utils.py                  # Link helpers, formatting, paths
    ├── i18n.py                   # Translations (EN / PT-BR)
    ├── config.py                 # Settings (JSON)
    ├── history.py                # Download history (JSON)
    ├── downloader.py             # Download engine (yt-dlp, multi-platform)
    ├── updater.py                # Update check
    ├── notifications.py          # System notifications
    ├── platforms/                # 🧩 Modular platform system
    │   ├── __init__.py           # Registry + detect_platform()
    │   ├── base.py               # Platform dataclass + registry
    │   ├── tiktok.py             # TikTok definition
    │   ├── youtube.py            # YouTube definition
    │   ├── instagram.py          # Instagram definition
    │   └── twitter.py            # X / Twitter definition
    └── gui/
        ├── __init__.py
        ├── theme.py              # Color palette and fonts
        ├── flags.py              # Language flag images
        ├── platform_icons.py     # Platform brand icons (drawn with Pillow)
        └── app.py                # Main window and the whole UI
```

User settings and history live in:
`%APPDATA%\Ultimate Download MP4\` (`config.json` and `history.json`).

---

## 🧩 Adding a new platform (modular system)

The interface never needs to change. To support a new site, drop a file in
`src/platforms/` that registers a `Platform`, then add it to the imports list:

```python
# src/platforms/vimeo.py
from .base import Platform, register

register(Platform(
    id="vimeo",
    name="Vimeo",
    folder="Vimeo",
    color="#1AB7EA",
    glyph="V",
    patterns=(r"https?://(?:www\.)?vimeo\.com/\S+",),
))
```

```python
# src/platforms/__init__.py
from . import tiktok, youtube, instagram, twitter, vimeo  # add vimeo here
```

Detection, the destination subfolder, the displayed name and a generic icon all
work automatically. (Optionally add a custom drawing in `gui/platform_icons.py`.)

---

## 🚀 Run from source (development)

> Requires **Python 3.10 or newer** installed and on PATH.

### Quick option (Windows)
**Double-click** `run.bat`. It installs the dependencies the first time and opens the program.

### Manual option
```powershell
# 1) (Optional, recommended) create a virtual environment
python -m venv venv
venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) (Optional) generate the icon
python assets\create_icon.py

# 4) Run
python main.py
```

---

## 🏗️ Build the executable (.exe)

### Quick option
**Double-click** `build.bat`. When it finishes, the executable will be at:
```
dist\UltimateDownloadMP4.exe
```

### Manual option (PyInstaller)
```powershell
pip install -r requirements.txt
python assets\create_icon.py

pyinstaller --noconfirm --onefile --windowed ^
    --name "UltimateDownloadMP4" ^
    --icon "assets\icon.ico" ^
    --add-data "assets\icon.ico;assets" ^
    --collect-submodules src.platforms ^
    --collect-all customtkinter ^
    --collect-all yt_dlp ^
    --collect-all plyer ^
    --exclude-module imageio_ffmpeg ^
    --hidden-import plyer.platforms.win.notification ^
    main.py
```

- `--collect-submodules src.platforms` → makes sure every platform module is bundled.
- `--collect-all yt_dlp` → includes all yt-dlp extractors (so new sites keep working).
- `--exclude-module imageio_ffmpeg` → keeps the `.exe` small (FFmpeg is fetched on demand).

---

## 📦 Build an INSTALLER (Setup.exe)

Besides the standalone `.exe`, you can build a **professional installer** that
installs the program, creates shortcuts (Start Menu + Desktop) and adds an
uninstaller — a classic Node.js-style wizard.

**Prerequisites:**
1. The executable in `dist\` (run `build.bat` first).
2. Inno Setup 6 installed:
   ```powershell
   winget install JRSoftware.InnoSetup
   ```

**Build:** double-click `build_installer.bat`. The installer is produced as:
```
UltimateDownloadMP4-Setup-2.0.0.exe
```

---

## 🎬 FFmpeg (downloaded on demand — lightweight `.exe`!)

**FFmpeg is needed for MP3** (audio conversion), for **merging** high-quality
video+audio on some platforms, and to **embed metadata**. To keep the `.exe`
small, it is **not bundled**.

- **Video (MP4):** works without FFmpeg when the site serves a single file
  (e.g. TikTok). For separate video+audio streams (common on YouTube), FFmpeg is
  used to merge when available.
- **Audio (MP3):** the **first time** you click "Download Audio (MP3)", the app
  **downloads FFmpeg automatically** (once, ~80 MB) and caches it in
  `%APPDATA%\Ultimate Download MP4\ffmpeg\`. Next times it's instant.
- If you **already have** FFmpeg on the system PATH, the app uses it.
- In **development**, installing `imageio-ffmpeg` avoids that download.

---

## ❓ Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` when running | Run `pip install -r requirements.txt`. |
| "Content unavailable / private" | The content may be private or removed. |
| "Login required" (Instagram/X) | Only **public** content can be downloaded. |
| Notifications don't show | Check Windows notifications; the app has a sound fallback. |
| Connection failure | Check your internet; yt-dlp retries automatically. |
| A site stopped downloading | Update with `pip install -U yt-dlp`. |

---

## ⚖️ Disclaimer

This tool is intended for **personal use** and for downloading content you have
the right to access. Respect each platform's **Terms of Service** and the
**copyrights** of creators. The authors are not responsible for misuse.

---

Made with ❤️ using **Python**, **CustomTkinter** and **yt-dlp**.
