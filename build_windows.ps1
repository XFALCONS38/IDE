$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$zipPath = Join-Path $root "w64devkit.zip"
$url = "https://github.com/skeeto/w64devkit/releases/download/v1.20.0/w64devkit-1.20.0.zip"

if (-not (Test-Path $zipPath)) {
    Write-Host "Downloading w64devkit..."
    & curl.exe -L $url -o $zipPath
}

python -m pip install --user pyinstaller | Out-Null

python -m PyInstaller `
    --onefile `
    --noconsole `
    --clean `
    --add-data "w64devkit.zip;." `
    "$root\IDE.py"

Write-Host "Build complete: $root\dist\IDE.exe"
