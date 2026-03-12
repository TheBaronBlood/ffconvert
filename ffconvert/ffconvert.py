#!/usr/bin/env python3
"""
FFConvert v1.0 — Terminal UI for FFmpeg
Cross-platform audio/video converter
"""

from __future__ import annotations
import json, os, re, subprocess, sys, asyncio
from pathlib import Path
from typing import Optional

try:
    from textual import on, work
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.screen import ModalScreen
    from textual.widgets import (
        Button, DataTable, Footer, Header, Input,
        Label, ProgressBar, RadioButton, RadioSet,
        Static, DirectoryTree, Select, Switch, Digits,
    )
    from textual.message import Message
    from rich.text import Text
except ImportError:
    print("⚙ Installiere Textual...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "textual", "--quiet"])
    print("✅ Fertig! Bitte Programm neu starten.")
    sys.exit(0)

# ─── Konfiguration ────────────────────────────────────────────────────────────

CONFIG_DIR  = Path.home() / ".ffconvert"
CONFIG_FILE = CONFIG_DIR  / "config.json"

DEFAULT_CONFIG = {
    "output_dir":    str(Path.home() / "Downloads"),
    "audio_quality": "192k",
    "video_quality": "23",
    "overwrite":     False,
    "same_dir":      False,
}

def load_config() -> dict:
    CONFIG_DIR.mkdir(exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text())}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg: dict):
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

# ─── Formate ─────────────────────────────────────────────────────────────────

SUPPORTED_EXT = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv",
    ".m4a", ".mp3", ".wav", ".flac", ".ogg", ".aac", ".wma", ".opus",
}

FORMAT_OPTIONS = [
    ("mp3",  "MP3   Audio · Universal"),
    ("wav",  "WAV   Audio · Lossless"),
    ("flac", "FLAC  Audio · Lossless"),
    ("aac",  "AAC   Audio · Modern"),
    ("ogg",  "OGG   Audio · Open"),
    ("opus", "OPUS  Audio · Compressed"),
    ("mp4",  "MP4   Video · Universal"),
    ("mkv",  "MKV   Video · Container"),
    ("webm", "WebM  Video · Web"),
    ("avi",  "AVI   Video · Legacy"),
    ("gif",  "GIF   Animation"),
]

def human_size(path: Path) -> str:
    try:
        s = path.stat().st_size
        for u in ["B", "KB", "MB", "GB"]:
            if s < 1024: return f"{s:.1f} {u}"
            s /= 1024
        return f"{s:.1f} TB"
    except Exception:
        return "?"

def build_cmd(inp: Path, out: Path, fmt: str, cfg: dict) -> list[str]:
    ow = ["-y"] if cfg["overwrite"] else ["-n"]
    cmd = ["ffmpeg", *ow, "-i", str(inp), "-progress", "pipe:1", "-nostats"]
    audio = {"mp3","wav","flac","aac","ogg","opus","m4a"}
    aq = cfg["audio_quality"]
    vq = cfg["video_quality"]
    if fmt in audio:
        cmd += ["-vn"]
        if   fmt == "mp3":  cmd += ["-c:a","libmp3lame","-b:a",aq]
        elif fmt == "wav":  cmd += ["-c:a","pcm_s16le"]
        elif fmt == "flac": cmd += ["-c:a","flac"]
        elif fmt == "aac":  cmd += ["-c:a","aac","-b:a",aq]
        elif fmt == "ogg":  cmd += ["-c:a","libvorbis","-b:a",aq]
        elif fmt == "opus": cmd += ["-c:a","libopus","-b:a",aq]
    else:
        if   fmt == "mp4":  cmd += ["-c:v","libx264","-crf",vq,"-c:a","aac","-b:a",aq]
        elif fmt == "mkv":  cmd += ["-c:v","libx264","-crf",vq,"-c:a","aac"]
        elif fmt == "webm": cmd += ["-c:v","libvpx-vp9","-crf",vq,"-c:a","libopus"]
        elif fmt == "avi":  cmd += ["-c:v","mpeg4","-c:a","mp3"]
        elif fmt == "gif":  cmd += ["-vf","fps=12,scale=480:-1:flags=lanczos","-loop","0"]
    cmd.append(str(out))
    return cmd

def get_duration(path: Path) -> Optional[float]:
    try:
        r = subprocess.run(
            ["ffprobe","-v","quiet","-print_format","json","-show_format",str(path)],
            capture_output=True, text=True
        )
        return float(json.loads(r.stdout)["format"].get("duration", 0))
    except Exception:
        return None

# ─── Daten-Klasse ─────────────────────────────────────────────────────────────

STATUS_ICON = {
    "ready":      "⏳",
    "converting": "⚙",
    "done":       "✅",
    "error":      "❌",
    "skipped":    "⏭",
}

class FileEntry:
    def __init__(self, path: Path):
        self.path     = path
        self.status   = "ready"
        self.progress = 0.0
        self.msg      = ""
        self.duration = get_duration(path)

# ─── Einstellungen-Modal ──────────────────────────────────────────────────────

class SettingsScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Schließen")]

    CSS = """
    SettingsScreen {
        align: center middle;
    }
    #dlg {
        width: 62;
        height: auto;
        border: double $primary;
        background: $surface;
        padding: 1 2;
    }
    .s-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    .row {
        height: 3;
        margin-bottom: 1;
        align: left middle;
    }
    .lbl {
        width: 22;
        content-align: left middle;
    }
    .val { width: 1fr; }
    #btn-row {
        align: right middle;
        height: 3;
        margin-top: 1;
    }
    """

    def __init__(self, config: dict):
        super().__init__()
        self.cfg = config.copy()

    def compose(self) -> ComposeResult:
        c = self.cfg
        with Container(id="dlg"):
            yield Label("⚙  Einstellungen", classes="s-title")
            with Horizontal(classes="row"):
                yield Label("Ausgabe-Ordner:", classes="lbl")
                yield Input(value=c["output_dir"], id="out-dir", classes="val")
            with Horizontal(classes="row"):
                yield Label("Audio-Qualität:", classes="lbl")
                yield Select(
                    [("96k – Klein","96k"),("128k – Standard","128k"),
                     ("192k – Gut","192k"),("320k – Optimal","320k")],
                    value=c["audio_quality"], id="aq", classes="val"
                )
            with Horizontal(classes="row"):
                yield Label("Video-Qualität (CRF):", classes="lbl")
                yield Select(
                    [("18 – Sehr gut","18"),("23 – Standard","23"),
                     ("28 – Kompakt","28"),("35 – Sehr klein","35")],
                    value=c["video_quality"], id="vq", classes="val"
                )
            with Horizontal(classes="row"):
                yield Label("In gleichem Ordner:", classes="lbl")
                yield Switch(value=c["same_dir"], id="same-dir")
            with Horizontal(classes="row"):
                yield Label("Dateien überschreiben:", classes="lbl")
                yield Switch(value=c["overwrite"], id="ow")
            with Horizontal(id="btn-row"):
                yield Button("Abbrechen", variant="default", id="cancel")
                yield Button("💾 Speichern", variant="primary", id="save")

    @on(Button.Pressed, "#cancel")
    def do_cancel(self): self.dismiss(None)

    @on(Button.Pressed, "#save")
    def do_save(self):
        self.cfg["output_dir"]    = self.query_one("#out-dir", Input).value
        self.cfg["audio_quality"] = self.query_one("#aq", Select).value
        self.cfg["video_quality"] = self.query_one("#vq", Select).value
        self.cfg["same_dir"]      = self.query_one("#same-dir", Switch).value
        self.cfg["overwrite"]     = self.query_one("#ow", Switch).value
        self.dismiss(self.cfg)

# ─── Datei-Browser Modal ──────────────────────────────────────────────────────

class BrowserScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Schließen")]

    CSS = """
    BrowserScreen { align: center middle; }
    #bdlg {
        width: 70; height: 28;
        border: double $primary;
        background: $surface;
        padding: 1;
    }
    .b-title { text-style: bold; color: $primary; margin-bottom: 1; }
    DirectoryTree { height: 1fr; border: solid $panel; }
    #sel-path { color: $text-muted; margin-top: 1; height: 2; }
    #bbtns { align: right middle; height: 3; }
    """

    def __init__(self):
        super().__init__()
        self.selected: Optional[Path] = None

    def compose(self) -> ComposeResult:
        with Container(id="bdlg"):
            yield Label("📁  Datei auswählen", classes="b-title")
            yield DirectoryTree(str(Path.home()), id="tree")
            yield Static("Keine Datei ausgewählt", id="sel-path")
            with Horizontal(id="bbtns"):
                yield Button("Abbrechen", variant="default",  id="bcancel")
                yield Button("Hinzufügen ▶", variant="primary", id="badd")

    @on(DirectoryTree.FileSelected)
    def on_file(self, ev: DirectoryTree.FileSelected):
        p = Path(str(ev.path))
        self.selected = p
        self.query_one("#sel-path", Static).update(f"📄 {p.name}")

    @on(Button.Pressed, "#bcancel")
    def do_cancel(self): self.dismiss(None)

    @on(Button.Pressed, "#badd")
    def do_add(self): self.dismiss(self.selected)

# ─── Hilfe Modal ──────────────────────────────────────────────────────────────

class HelpScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Schließen"),
                Binding("?", "dismiss", "Schließen")]
    CSS = """
    HelpScreen { align: center middle; }
    #hdlg {
        width: 50; height: auto;
        border: double $primary;
        background: $surface;
        padding: 1 2;
    }
    .h-title { text-style: bold; color: $primary; margin-bottom: 1; }
    .h-key   { color: $accent; width: 16; }
    .h-row   { height: 2; }
    """

    KEYS = [
        ("a",       "Datei hinzufügen"),
        ("s",       "Einstellungen"),
        ("?",       "Diese Hilfe"),
        ("Enter",   "Konvertierung starten"),
        ("Delete",  "Ausgewählte entfernen"),
        ("Ctrl+A",  "Alle entfernen"),
        ("q",       "Beenden"),
        ("Tab",     "Panel wechseln"),
        ("↑ ↓",     "Navigieren"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="hdlg"):
            yield Label("❓  Tastenkürzel", classes="h-title")
            for key, desc in self.KEYS:
                with Horizontal(classes="h-row"):
                    yield Label(f"  {key}", classes="h-key")
                    yield Label(desc)
            yield Button("Schließen", variant="primary", id="hclose")

    @on(Button.Pressed, "#hclose")
    def close(self): self.dismiss(None)

# ─── Haupt-App ────────────────────────────────────────────────────────────────

class FFConvertApp(App):
    TITLE    = "FFConvert"
    SUB_TITLE = "FFmpeg Terminal Converter"
    CSS_PATH = None

    CSS = """
    /* ── Layout ── */
    #main {
        height: 1fr;
        min-height: 14;
    }
    #file-panel {
        width: 1.7fr;
        border: solid $panel;
        padding: 0 1;
    }
    #ctrl-panel {
        width: 37;
        border: solid $panel;
        padding: 0 1;
    }
    #prog-panel {
        height: 6;
        border: solid $panel;
        padding: 0 1;
    }

    /* ── Dateiliste ── */
    .panel-title {
        text-style: bold;
        color: $primary;
        margin: 1 0 0 0;
    }
    DataTable { height: 1fr; }
    #drop-input {
        margin-top: 1;
        border: dashed $panel;
    }
    #drop-input:focus { border: dashed $accent; }

    /* ── Kontrollbereich ── */
    RadioSet { height: auto; border: none; }
    RadioButton { margin: 0; padding: 0 1; }

    .sep {
        color: $panel-lighten-2;
        margin: 1 0;
    }
    .out-label { color: $text-muted; text-style: italic; }

    #btn-convert {
        width: 100%;
        margin-top: 1;
    }
    #btn-browse, #btn-remove, #btn-settings, #btn-help {
        width: 100%;
        margin-top: 1;
    }

    /* ── Fortschritt ── */
    #prog-bar  { margin: 0 0 0 0; }
    #prog-text { color: $text-muted; margin-bottom: 1; }
    #status    { color: $success; }
    """

    BINDINGS = [
        Binding("q",      "quit",        "Beenden"),
        Binding("s",      "settings",    "Einstellungen"),
        Binding("a",      "add_file",    "Hinzufügen"),
        Binding("?",      "help",        "Hilfe"),
        Binding("enter",  "convert",     "Konvertieren"),
        Binding("delete", "remove_sel",  "Entfernen"),
        Binding("ctrl+a", "clear_all",   "Alle löschen"),
    ]

    def __init__(self):
        super().__init__()
        self.config    = load_config()
        self.files:  list[FileEntry] = []
        self.busy        = False
        self.selected_fmt = "mp3"

    # ── Aufbau ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="main"):
            # Linkes Panel – Dateiliste
            with Vertical(id="file-panel"):
                yield Label("📂  Datei-Warteschlange", classes="panel-title")
                tbl = DataTable(id="file-table", cursor_type="row", zebra_stripes=True)
                yield tbl
                yield Input(
                    id="drop-input",
                    placeholder="📥  Datei-Pfad einfügen oder hierhin ziehen …"
                )

            # Rechtes Panel – Format & Aktionen
            with Vertical(id="ctrl-panel"):
                yield Label("🎯  Zielformat", classes="panel-title")
                with RadioSet(id="fmt-set"):
                    for val, label in FORMAT_OPTIONS:
                        yield RadioButton(label, value=(val == "mp3"), id=f"fmt-{val}")

                yield Static("─" * 22, classes="sep")
                yield Label("📁  Ausgabe:", classes="panel-title")
                yield Static(self._short_path(self.config["output_dir"]), id="out-lbl", classes="out-label")

                yield Button("▶ Konvertieren",   variant="success", id="btn-convert")
                yield Button("📁 Durchsuchen",   variant="default", id="btn-browse")
                yield Button("🗑 Entfernen",     variant="warning", id="btn-remove")
                yield Button("⚙ Einstellungen",  variant="default", id="btn-settings")
                yield Button("❓ Hilfe",          variant="default", id="btn-help")

        # Fortschritts-Panel
        with Vertical(id="prog-panel"):
            yield Static("Bereit – Dateien hinzufügen und Format wählen", id="status")
            yield ProgressBar(id="prog-bar", total=100, show_eta=False)
            yield Static("", id="prog-text")

        yield Footer()

    def on_mount(self):
        tbl = self.query_one("#file-table", DataTable)
        tbl.add_columns("", "Dateiname", "Größe", "Format", "Status")
        tbl.cursor_type = "row"

    # ── Hilfsfunktionen ───────────────────────────────────────────────────────

    def _short_path(self, p: str) -> str:
        try:
            return str(Path(p).relative_to(Path.home().parent))
        except Exception:
            return p[:22] + "…" if len(p) > 24 else p

    def _refresh_table(self):
        tbl = self.query_one("#file-table", DataTable)
        tbl.clear()
        for entry in self.files:
            pct  = f"{entry.progress:.0f}%" if entry.status == "converting" else ""
            icon = STATUS_ICON.get(entry.status, "")
            row  = (icon, entry.path.name, human_size(entry.path),
                    entry.path.suffix.lstrip(".").upper(), pct or entry.msg or entry.status)
            tbl.add_row(*row, key=str(entry.path))

    def _add_path(self, p: Path):
        if not p.exists():
            self.notify(f"Datei nicht gefunden: {p.name}", severity="error"); return
        if p.suffix.lower() not in SUPPORTED_EXT:
            self.notify(f"Format nicht unterstützt: {p.suffix}", severity="warning"); return
        if any(e.path == p for e in self.files):
            self.notify("Datei bereits in der Liste", severity="warning"); return
        self.files.append(FileEntry(p))
        self._refresh_table()
        self.notify(f"Hinzugefügt: {p.name}", severity="information")

    # ── Events ────────────────────────────────────────────────────────────────

    @on(Input.Submitted, "#drop-input")
    def on_drop_input(self, ev: Input.Submitted):
        raw = ev.value.strip().strip('"').strip("'")
        if raw:
            self._add_path(Path(raw))
        self.query_one("#drop-input", Input).clear()

    @on(RadioSet.Changed, "#fmt-set")
    def on_format(self, ev: RadioSet.Changed):
        self.selected_fmt = FORMAT_OPTIONS[ev.index][0]

    @on(Button.Pressed, "#btn-convert")
    def on_btn_convert(self): self.action_convert()

    @on(Button.Pressed, "#btn-browse")
    def on_btn_browse(self): self.action_add_file()

    @on(Button.Pressed, "#btn-remove")
    def on_btn_remove(self): self.action_remove_sel()

    @on(Button.Pressed, "#btn-settings")
    def on_btn_settings(self): self.action_settings()

    @on(Button.Pressed, "#btn-help")
    def on_btn_help(self): self.action_help()

    # ── Aktionen ──────────────────────────────────────────────────────────────

    def action_help(self):
        self.push_screen(HelpScreen())

    def action_settings(self):
        def on_close(new_cfg):
            if new_cfg:
                self.config = new_cfg
                save_config(new_cfg)
                self.query_one("#out-lbl", Static).update(
                    self._short_path(new_cfg["output_dir"])
                )
                self.notify("Einstellungen gespeichert ✅")
        self.push_screen(SettingsScreen(self.config), on_close)

    def action_add_file(self):
        def on_close(path: Optional[Path]):
            if path:
                self._add_path(path)
        self.push_screen(BrowserScreen(), on_close)

    def action_remove_sel(self):
        tbl = self.query_one("#file-table", DataTable)
        if tbl.cursor_row is not None and self.files:
            try:
                removed = self.files.pop(tbl.cursor_row)
                self._refresh_table()
                self.notify(f"Entfernt: {removed.path.name}")
            except IndexError:
                pass

    def action_clear_all(self):
        self.files.clear()
        self._refresh_table()

    def action_convert(self):
        if self.busy:
            self.notify("Konvertierung läuft bereits …", severity="warning"); return
        ready = [f for f in self.files if f.status == "ready"]
        if not ready:
            self.notify("Keine bereiten Dateien in der Liste", severity="warning"); return
        self._run_conversion(ready)

    # ── Konvertierung ─────────────────────────────────────────────────────────

    @work(thread=True)
    def _run_conversion(self, entries: list[FileEntry]):
        self.busy = True
        total = len(entries)
        out_base = Path(self.config["output_dir"])
        out_base.mkdir(parents=True, exist_ok=True)

        for i, entry in enumerate(entries):
            entry.status   = "converting"
            entry.progress = 0.0
            self.call_from_thread(self._refresh_table)
            self.call_from_thread(
                self.query_one("#status", Static).update,
                f"⚙  Konvertiere {i+1}/{total}: {entry.path.name}"
            )

            if self.config["same_dir"]:
                out_dir = entry.path.parent
            else:
                out_dir = out_base

            out_path = out_dir / f"{entry.path.stem}.{self.selected_fmt}"

            cmd = build_cmd(entry.path, out_path, self.selected_fmt, self.config)
            duration = entry.duration or 0.0

            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, bufsize=1
                )
                for line in proc.stdout:
                    line = line.strip()
                    m = re.match(r"out_time_ms=(\d+)", line)
                    if m and duration > 0:
                        t = int(m.group(1)) / 1_000_000
                        entry.progress = min(100.0, t / duration * 100)
                        self.call_from_thread(self._update_progress, entry, i, total)
                proc.wait()
                if proc.returncode == 0:
                    entry.status   = "done"
                    entry.progress = 100.0
                    entry.msg      = out_path.name
                else:
                    entry.status = "error"
                    entry.msg    = proc.stderr.read()[-60:] if proc.stderr else "Fehler"
            except FileNotFoundError:
                entry.status = "error"
                entry.msg    = "ffmpeg nicht gefunden!"
                self.call_from_thread(
                    self.notify, "❌ ffmpeg nicht gefunden! Bitte installieren.", severity="error"
                )
                break
            except Exception as e:
                entry.status = "error"
                entry.msg    = str(e)[:60]

            self.call_from_thread(self._refresh_table)

        self.busy = False
        done  = sum(1 for f in entries if f.status == "done")
        errs  = sum(1 for f in entries if f.status == "error")
        self.call_from_thread(
            self.query_one("#status", Static).update,
            f"✅ Fertig: {done} konvertiert, {errs} Fehler"
        )
        self.call_from_thread(
            self.query_one("#prog-bar", ProgressBar).update, progress=100
        )

    def _update_progress(self, entry: FileEntry, idx: int, total: int):
        overall = (idx * 100 + entry.progress) / total
        self.query_one("#prog-bar",  ProgressBar).update(progress=overall)
        self.query_one("#prog-text", Static).update(
            f"{entry.path.name}  {entry.progress:.0f}%"
        )
        self._refresh_table()

# ─── Einstiegspunkt ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    FFConvertApp().run()