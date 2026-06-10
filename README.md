# 🎵 TikTok Ultimate Downloader

A **Windows** desktop app that downloads **TikTok videos without watermark**, always in the **highest available quality**, with a modern dark-themed interface.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6)
![GUI](https://img.shields.io/badge/UI-CustomTkinter-25F4EE)

---

## 📥 Download

> **Requirements:** Windows 10/11 (64-bit). **No** Python installation needed.

- Download the installer for Windows via the link below:
  - ➡️ **[Main Download Link](https://github.com/Overocai/tiktok-ultimate-downloader/releases/download/v1.2.0/TikTokUltimateDownloader-Setup-1.2.0.exe)** (direct download)
  - ➡️ **[Main Download Link mirror](https://github.com/Overocai/tiktok-ultimate-downloader/releases/latest)** (Releases page)

- How to install:
  - Run **`TikTokUltimateDownloader-Setup-1.2.0.exe`** and follow the wizard (Next → Accept the license → Install → Finish).
  - If **Windows SmartScreen** shows a warning, click **"More info" → "Run anyway"** (normal for apps without a paid code-signing certificate).

- Note about MP3:
  - **Video (MP4)** downloads work right away, no extras. For **audio (MP3)**, the **first time** you use it the app downloads FFmpeg automatically (just once, then cached).

---

## ✨ Features

- ⬇️ **Watermark-free video (MP4) download** in the **highest quality** (via `yt-dlp`).
- 🎵 **Audio-only download as MP3** (192 kbps) — FFmpeg fetched automatically on first use (nothing to install by hand).
- 🖼️ **Video thumbnail** shown in the info card.
- 🎨 **Modern, dark, responsive** interface (CustomTkinter).
- 🌐 **Bilingual UI (English / Portuguese)** with flag switcher.
- 🔗 **Automatic detection** of valid TikTok links (with a "Paste" button).
- 📊 **Real-time progress bar** + speed, size and ETA.
- 📝 **Activity log** with detailed status of each step.
- 📁 **Destination folder selector** (saved between sessions).
- ℹ️ Shows **title, author, duration, resolution and size**.
- ⏹️ **Cancel** a download at any time.
- 🧵 **Threaded**: the interface **never freezes** during downloads.
- 🕘 **History** of recent downloads (with MP4/MP3 badge and "Open folder").
- 🔔 Native **notifications** when finished.
- 🔄 **Update check** (optional/configurable).
- 💾 **Settings stored in JSON** (theme, quality, notifications, etc.).
- 🛡️ **Full error handling** with friendly messages.

---

## 📂 Project structure

```
TikTok Ultimate Downloader/
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
    ├── utils.py                  # Link validation, formatting, paths
    ├── i18n.py                   # Translations (EN / PT-BR)
    ├── config.py                 # Settings (JSON)
    ├── history.py                # Download history (JSON)
    ├── downloader.py             # Download engine (yt-dlp)
    ├── updater.py                # Update check
    ├── notifications.py          # System notifications
    └── gui/
        ├── __init__.py
        ├── theme.py              # Color palette and fonts
        ├── flags.py              # Language flag images
        └── app.py                # Main window and the whole UI
```

User settings and history live in:
`%APPDATA%\TikTokUltimateDownloader\` (`config.json` and `history.json`).

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
dist\TikTokUltimateDownloader.exe
```

### Manual option (PyInstaller)
```powershell
pip install -r requirements.txt
python assets\create_icon.py

pyinstaller --noconfirm --onefile --windowed ^
    --name "TikTokUltimateDownloader" ^
    --icon "assets\icon.ico" ^
    --add-data "assets\icon.ico;assets" ^
    --collect-all customtkinter ^
    --collect-all yt_dlp ^
    --collect-all plyer ^
    --exclude-module imageio_ffmpeg ^
    --hidden-import plyer.platforms.win.notification ^
    main.py
```

**What each option does:**
- `--onefile` → bundles everything into a single `.exe`.
- `--windowed` → no console window (GUI app).
- `--icon` → sets the executable icon.
- `--add-data` → embeds the icon inside the `.exe` (for the window and notifications).
- `--collect-all customtkinter` → includes CustomTkinter themes/resources.
- `--collect-all yt_dlp` → includes all yt-dlp extractors.
- `--collect-all plyer` + `--hidden-import ...` → ensures notifications work on Windows.
- `--exclude-module imageio_ffmpeg` → keeps the `.exe` small (FFmpeg is downloaded on demand).

---

## 📦 Build an INSTALLER (Setup.exe)

Besides the standalone `.exe`, you can build a **professional installer** that installs the program, creates shortcuts (Start Menu + Desktop) and adds an uninstaller — a classic Node.js-style wizard.

**Prerequisites:**
1. The executable in `dist\` (run `build.bat` first).
2. Inno Setup 6 installed:
   ```powershell
   winget install JRSoftware.InnoSetup
   ```

**Build:** double-click `build_installer.bat` (or open `installer.iss` in Inno Setup and click *Compile*).

The installer is produced as:
```
TikTokUltimateDownloader-Setup-1.2.0.exe
```

The end user only needs to run that `Setup.exe` — no Python, nothing else.

---

## 🎬 FFmpeg (downloaded on demand — lightweight `.exe`!)

**FFmpeg is only needed for MP3** (audio conversion). To **keep the `.exe` small (~31 MB instead of ~61 MB)**, it is **not bundled** inside the executable.

How it works:
- **Video (MP4):** works **without FFmpeg** (TikTok videos already come as a single MP4).
- **Audio (MP3):** the **first time** you click "Download Audio (MP3)", the app **downloads FFmpeg automatically** (once, ~80 MB) and caches it in `%APPDATA%\TikTokUltimateDownloader\ffmpeg\`. Next times it's instant.
- If you **already have** FFmpeg on the system PATH, the app uses it and downloads nothing.
- In **development**, installing `imageio-ffmpeg` (`pip install imageio-ffmpeg`) avoids that download — the app reuses its binary.

---

## ❓ Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` when running | Run `pip install -r requirements.txt`. |
| "Video unavailable / private" | The video may have been removed or be private. |
| Notifications don't show | Check Windows notifications; the app has a sound fallback. |
| Connection failure | Check your internet; yt-dlp retries automatically. |
| Outdated `yt-dlp` stopped downloading | Update with `pip install -U yt-dlp`. |

---

## ⚖️ Disclaimer

This tool is intended for **personal use** and for downloading content you have the right to access.
Respect **TikTok's Terms of Service** and the **copyrights** of creators.
The authors are not responsible for misuse.

---

Made with ❤️ using **Python**, **CustomTkinter** and **yt-dlp**.
