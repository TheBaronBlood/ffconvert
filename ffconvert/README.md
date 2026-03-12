# FFConvert 🎬

**Terminal UI für FFmpeg** — Cross-platform, keine GUI nötig.

```
┌─ FFConvert ──────────────────────────────────────────────────────────────────┐
│ FFConvert                                       Terminal FFmpeg Converter     │
├──────────────────────────────────────┬───────────────────────────────────────┤
│ 📂  Datei-Warteschlange              │ 🎯  Zielformat                        │
│                                      │                                       │
│  ✅  video.mp4         4.2 MB  MP4   │  ● MP3   Audio · Universal            │
│  ⚙   audio.m4a         1.1 MB  M4A   │  ○ WAV   Audio · Lossless             │
│  ⏳  podcast.wav       22 MB   WAV   │  ○ FLAC  Audio · Lossless             │
│                                      │  ○ AAC   Audio · Modern               │
│                                      │  ○ OGG   Audio · Open                 │
│  📥 Datei-Pfad einfügen …           │  ○ OPUS  Audio · Compressed           │
│                                      │  ○ MP4   Video · Universal            │
│                                      │  ────────────────────────────         │
│                                      │  📁 Ausgabe: ~/Downloads              │
│                                      │                                       │
│                                      │  ▶ Konvertieren                       │
│                                      │  📁 Durchsuchen                       │
│                                      │  🗑 Entfernen                         │
│                                      │  ⚙ Einstellungen                     │
├──────────────────────────────────────┴───────────────────────────────────────┤
│ ⚙  Konvertiere 1/3: video.mp4                                                │
│ ████████████████████████░░░░░░░░░░░░░░░  63%                                │
│ video.mp4  63%                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
 q Beenden  s Einstellungen  a Hinzufügen  ? Hilfe  Enter Konvertieren
```

## Installation

### Linux / macOS
```bash
curl -sSL https://DEINE-URL/install.sh | bash
```

### Windows (PowerShell)
```powershell
irm https://DEINE-URL/install.ps1 | iex
```

### Manuell
```bash
pip install textual
python ffconvert.py
```

## Features

- 🎯 **11 Formate**: MP3, WAV, FLAC, AAC, OGG, OPUS, MP4, MKV, WebM, AVI, GIF
- ⌨️ **Vollständige Tastatursteuerung** (Pfeiltasten, Tab, Shortcuts)
- 🖱️ **Klickbare Oberfläche** (Buttons, Radio-Buttons, Switches)
- 📁 **Datei-Browser** mit Verzeichnis-Navigation
- 📥 **Drag & Drop** (Datei in Terminal ziehen → Pfad wird eingefügt)
- ⚙️ **Einstellungen-Fenster** (Qualität, Ausgabe-Ordner, etc.)
- 📊 **Live-Fortschrittsbalken** pro Datei und gesamt
- 🔄 **Batch-Konvertierung** (mehrere Dateien gleichzeitig in die Queue)
- 💾 **Einstellungen** werden gespeichert (`~/.ffconvert/config.json`)

## Unterstützte Eingabe-Formate

| Video | Audio |
|-------|-------|
| MP4, MKV, AVI, MOV, WebM, FLV, WMV | MP3, WAV, FLAC, OGG, AAC, M4A, WMA, OPUS |

## Tastenkürzel

| Taste | Aktion |
|-------|--------|
| `a` | Datei hinzufügen (Browser) |
| `Enter` | Konvertierung starten |
| `Delete` | Ausgewählte Datei entfernen |
| `Ctrl+A` | Alle Dateien entfernen |
| `s` | Einstellungen öffnen |
| `?` | Hilfe |
| `q` | Beenden |
| `Tab` | Zwischen Panels wechseln |

## Voraussetzungen

- Python 3.8+
- [ffmpeg](https://ffmpeg.org/download.html) im PATH
- `pip install textual`

## Eigenen Server hosten

Dateien (`ffconvert.py`, `install.sh`, `install.ps1`) auf einen Webserver laden
und die `SCRIPT_URL`-Variable in den Installer-Scripts anpassen.

Einfachste Option: **GitHub Releases** oder **GitHub Raw**:
```
https://raw.githubusercontent.com/DEIN_USER/ffconvert/main/ffconvert.py
```
