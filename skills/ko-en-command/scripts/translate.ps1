param(
    [string]$Text,
    [string]$InputFile,
    [string]$Context = '',
    [string]$Glossary,
    [string]$Output
)
$ErrorActionPreference = 'Stop'
$runtimeRoot = if ($env:KO_EN_RUNTIME) { $env:KO_EN_RUNTIME } else { (Join-Path $env:LOCALAPPDATA 'LayaCommand') }
$pythonExe = Join-Path $runtimeRoot '.venv/Scripts/python.exe'
$translateScript = Join-Path $PSScriptRoot 'translate.py'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw "Python runtime missing: $pythonExe" }
if (($Text -and $InputFile) -or (-not $Text -and -not $InputFile)) { throw 'Choose either -Text or -InputFile.' }
$translateArgs = @($translateScript)
if ($InputFile) { $translateArgs += @('--file', $InputFile) } else { $translateArgs += @('--text', $Text) }
if ($Context) { $translateArgs += @('--context', $Context) }
if ($Glossary) { $translateArgs += @('--glossary', $Glossary) }
if ($Output) { $translateArgs += @('--output', $Output) }
& $pythonExe @translateArgs
exit $LASTEXITCODE
