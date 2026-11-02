param(
    [string]$Text,
    [string]$InputFile,
    [string]$Context = '',
    [string]$Glossary,
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [switch]$Reviewed,
    [string]$Questions
)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$skillRoot = Split-Path -Parent $PSScriptRoot
$translationSkill = Join-Path (Split-Path -Parent $skillRoot) 'ko-en-command'
$runtimeRoot = if ($env:KO_EN_RUNTIME) { $env:KO_EN_RUNTIME } else { (Join-Path $env:LOCALAPPDATA 'LayaCommand') }
$pythonExe = Join-Path $runtimeRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw "Python runtime missing: $pythonExe" }
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$translation = Join-Path $OutputDir 'translation.json'
if ($Reviewed) {
    if ($Text -or $InputFile -or $Context -or $Glossary) { throw 'Review stage reads the saved translation; omit new source/context/glossary.' }
    if (-not (Test-Path -LiteralPath $translation)) { throw 'Run translation and review translation.json first.' }
    if (-not $Questions) { $Questions = Join-Path $skillRoot 'assets/command-questions.json' }
    $env:USE_TF = '0'
    & $pythonExe (Join-Path $translationSkill 'scripts/laya_predict.py') --translation $translation --questions $Questions --runtime $runtimeRoot --output (Join-Path $OutputDir 'result.json')
} else {
    if (($Text -and $InputFile) -or (-not $Text -and -not $InputFile)) { throw 'Choose either -Text or -InputFile.' }
    if (Test-Path -LiteralPath $translation) { throw 'Translation already exists; use a new OutputDir to preserve the original.' }
    $translateArgs = @((Join-Path $translationSkill 'scripts/translate.py'), '--runtime', $runtimeRoot, '--output', $translation)
    if ($InputFile) { $translateArgs += @('--file', $InputFile) } else { $translateArgs += @('--text', $Text) }
    if ($Context) { $translateArgs += @('--context', $Context) }
    if ($Glossary) { $translateArgs += @('--glossary', $Glossary) }
    & $pythonExe @translateArgs
}
exit $LASTEXITCODE
