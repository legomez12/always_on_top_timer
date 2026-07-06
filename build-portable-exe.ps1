param(
    [ValidateSet('onedir', 'onefile', 'both')]
    [string]$Mode = 'both',
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'

function Run-Command {
    param([string]$Command)
    Write-Host "> $Command" -ForegroundColor Cyan
    Invoke-Expression $Command
}

if ($Clean) {
    if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
    if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
}

if ($Mode -eq 'onedir' -or $Mode -eq 'both') {
    Run-Command "uv run pyinstaller --noconfirm --clean always_on_top_timer.spec"
}

if ($Mode -eq 'onefile' -or $Mode -eq 'both') {
    Run-Command "uv run pyinstaller --noconfirm --clean --windowed --name AlwaysOnTopTimer --onefile always_on_top_timer.py"
}

Write-Host "Portable build complete." -ForegroundColor Green
Write-Host "Outputs:" -ForegroundColor Green
if (Test-Path "dist\\AlwaysOnTopTimer") {
    Write-Host "- dist\\AlwaysOnTopTimer\\AlwaysOnTopTimer.exe (one-folder)"
}
if (Test-Path "dist\\AlwaysOnTopTimer.exe") {
    Write-Host "- dist\\AlwaysOnTopTimer.exe (one-file)"
}
Write-Host "No installer is created. These are portable run-in-place artifacts." -ForegroundColor Yellow
