param(
    [string]$Runtime = $(if ($env:KO_EN_RUNTIME) {$env:KO_EN_RUNTIME} else {Join-Path $env:LOCALAPPDATA 'LayaCommand'}),
    [string]$Python = 'python',
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $Runtime '.venv/Scripts/python.exe'
if ($CheckOnly) {
    if (-not (Test-Path -LiteralPath $venvPython)) {throw "Missing Python: $venvPython"}
    & $venvPython (Join-Path $PSScriptRoot 'setup_runtime.py') --runtime $Runtime --check
    exit $LASTEXITCODE
}
New-Item -ItemType Directory -Force -Path $Runtime | Out-Null
if (-not (Test-Path -LiteralPath $venvPython)) {
    & $Python -m venv (Join-Path $Runtime '.venv')
    if ($LASTEXITCODE -ne 0) {throw 'Creating Python virtual environment failed.'}
}
& $venvPython -m pip install --no-cache-dir 'torch==2.15.0+cpu' --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) {throw 'CPU PyTorch installation failed.'}
& $venvPython -m pip install --no-cache-dir -r (Join-Path $repoRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) {throw 'Laya dependencies installation failed.'}
& $venvPython (Join-Path $PSScriptRoot 'setup_runtime.py') --runtime $Runtime
exit $LASTEXITCODE
