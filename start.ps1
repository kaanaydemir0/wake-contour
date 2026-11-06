param([switch]$CheckOnly)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$appPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

if (!(Test-Path -LiteralPath $appPython)) {
    $runtimePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $runtimePython) {
        & $runtimePython -m venv .venv
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv .venv
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv .venv
    } else {
        throw 'Python 3.10+ gerekli. Python kurun, sonra Baslat.cmd dosyasini yeniden acin.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Python sanal ortami olusturulamadi.' }
}

& $appPython -c "import importlib.util; raise SystemExit(0 if all(importlib.util.find_spec(name) is not None for name in ['numpy', 'matplotlib', 'tkinter']) else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Gerekli paketler proje ortamına kuruluyor...'
    & $appPython -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Paketler kurulamadi. Internet baglantisini kontrol edin.' }
}
if ($CheckOnly) {
    Write-Host 'Python ortami ve paketler hazir.'
    exit 0
}
& $appPython wake_app.py
if ($LASTEXITCODE -ne 0) { throw 'Uygulama baslatilamadi.' }

