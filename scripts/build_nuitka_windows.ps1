$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

if ($args.Count -gt 0 -and ($args[0] -eq "-h" -or $args[0] -eq "--help")) {
    Write-Output "Usage: scripts\build_nuitka_windows.ps1"
    Write-Output ""
    Write-Output "Builds Shardveil with Nuitka into build\nuitka\main.dist\."
    Write-Output "Requires .venv, project requirements, and Nuitka to be installed first."
    exit 0
}

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error "Missing .venv Python. Create it first: python -m venv .venv"
}

& $Python -c "import arcade, pyglet, tcod, numpy" *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Missing runtime dependencies. Install them first: .venv\Scripts\python.exe -m pip install -r requirements.txt"
}

& $Python -m nuitka --version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Missing Nuitka. Install it first: .venv\Scripts\python.exe -m pip install nuitka"
}

$env:NUITKA_CACHE_DIR = if ($env:NUITKA_CACHE_DIR) {
    $env:NUITKA_CACHE_DIR
} else {
    Join-Path $RepoRoot ".nuitka-cache"
}

& $Python -m nuitka src/main.py `
    --standalone `
    --enable-plugin=numpy `
    --include-data-dir=assets=assets `
    --output-dir=build/nuitka `
    --output-filename=shardveil
