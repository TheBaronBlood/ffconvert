# FFConvert Installer — Windows (PowerShell)
# Verwendung: irm https://DEINE-URL/install.ps1 | iex

$ErrorActionPreference = "Stop"

$INSTALL_DIR = "$env:LOCALAPPDATA\FFConvert"
$SCRIPT_URL  = "https://raw.githubusercontent.com/TheBaronBlood/ffconvert/refs/heads/main/ffconvert.py"   # ← hier deine URL

function Write-Step  { param($msg) Write-Host "[→] $msg" -ForegroundColor Cyan }
function Write-Ok    { param($msg) Write-Host "[✓] $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Err   { param($msg) Write-Host "[✗] $msg" -ForegroundColor Red; exit 1 }

Clear-Host
Write-Host @"
  ███████╗███████╗ ██████╗ ██████╗ ███╗   ██╗██╗   ██╗
  ██╔════╝██╔════╝██╔════╝██╔═══██╗████╗  ██║██║   ██║
  █████╗  █████╗  ██║     ██║   ██║██╔██╗ ██║██║   ██║
  ██╔══╝  ██╔══╝  ██║     ██║   ██║██║╚██╗██║╚██╗ ██╔╝
  ██║     ██║     ╚██████╗╚██████╔╝██║ ╚████║ ╚████╔╝
  ╚═╝     ╚═╝      ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝  ╚═══╝  v1.0

  FFmpeg Terminal Converter — Windows Installer
"@ -ForegroundColor Cyan

# ── Python prüfen ─────────────────────────────────────────────────────────────
Write-Step "Prüfe Python 3 ..."
try {
    $pyVer = python --version 2>&1
    if ($pyVer -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]; $minor = [int]$Matches[2]
        if ($major -ge 3 -and $minor -ge 8) {
            Write-Ok "Python $major.$minor gefunden"
        } else {
            Write-Err "Python 3.8+ erforderlich (gefunden: $major.$minor)"
        }
    }
} catch {
    Write-Warn "Python nicht gefunden — versuche winget ..."
    try {
        winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements
        Write-Ok "Python installiert – bitte PowerShell neu starten und Installer erneut ausführen"
        Read-Host "Enter drücken zum Beenden"
        exit 0
    } catch {
        Write-Err "Bitte Python manuell installieren: https://python.org"
    }
}

# ── ffmpeg prüfen ─────────────────────────────────────────────────────────────
Write-Step "Prüfe ffmpeg ..."
$ffmpegOk = $null -ne (Get-Command ffmpeg -ErrorAction SilentlyContinue)
if ($ffmpegOk) {
    Write-Ok "ffmpeg gefunden"
} else {
    Write-Warn "ffmpeg nicht gefunden — versuche winget ..."
    try {
        winget install Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
        Write-Ok "ffmpeg installiert"
        Write-Warn "Bitte PowerShell neu starten damit ffmpeg im PATH ist"
    } catch {
        Write-Warn "Konnte ffmpeg nicht automatisch installieren."
        Write-Warn "Bitte manuell: https://ffmpeg.org/download.html"
    }
}

# ── Textual installieren ───────────────────────────────────────────────────────
Write-Step "Installiere Textual ..."
python -m pip install textual --quiet --upgrade
Write-Ok "Textual installiert"

# ── Dateien kopieren ──────────────────────────────────────────────────────────
Write-Step "Installiere FFConvert nach $INSTALL_DIR ..."
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null

if (Test-Path ".\ffconvert.py") {
    Copy-Item ".\ffconvert.py" "$INSTALL_DIR\ffconvert.py" -Force
} else {
    Invoke-WebRequest -Uri $SCRIPT_URL -OutFile "$INSTALL_DIR\ffconvert.py"
}
Write-Ok "Programm installiert"

# ── Launcher-Batch erstellen ──────────────────────────────────────────────────
Write-Step "Erstelle Launcher ..."
$batchContent = "@echo off`r`npython `"$INSTALL_DIR\ffconvert.py`" %*"
Set-Content -Path "$INSTALL_DIR\ffconvert.bat" -Value $batchContent -Encoding ASCII

# ── PATH aktualisieren ────────────────────────────────────────────────────────
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$INSTALL_DIR*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$INSTALL_DIR", "User")
    Write-Ok "PATH aktualisiert (wird beim nächsten Terminal-Start aktiv)"
}

Write-Host ""
Write-Host "  ✅ Installation abgeschlossen!" -ForegroundColor Green
Write-Host ""
Write-Host "  Starten:    " -NoNewline
Write-Host "ffconvert" -ForegroundColor Yellow
Write-Host "  Oder:       " -NoNewline
Write-Host "python $INSTALL_DIR\ffconvert.py" -ForegroundColor Yellow
Write-Host ""
Write-Host ""
Write-Host "  Starte FFConvert ..." -ForegroundColor Cyan
Start-Sleep -Seconds 1
python "$INSTALL_DIR\ffconvert.py"
