# Windows (PowerShell 5.1+):  powershell -ExecutionPolicy Bypass -File install.ps1 [--demo C:\my-series | --starter C:\my-series] [--target both] [--yes]
$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python -ErrorAction SilentlyContinue }
if (-not $py) {
  Write-Host "Python 3 not found. Installing with winget (then reopen PowerShell and run this again)..."
  winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
  exit 1
}
& $py.Source "$PSScriptRoot\install.py" @args
