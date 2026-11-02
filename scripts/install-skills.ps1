param(
    [string]$SkillsDir = $(if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $env:USERPROFILE '.codex/skills' }),
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
$source = Join-Path (Split-Path -Parent $PSScriptRoot) 'skills'
foreach ($name in @('ko-en-command','laya-command')) {
    if ((Test-Path -LiteralPath (Join-Path $SkillsDir $name)) -and -not $Force) {
        throw "Skill already exists: $name. Back it up and use -Force if replacement is intended."
    }
}
New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null
foreach ($name in @('ko-en-command','laya-command')) {
    $target = Join-Path $SkillsDir $name
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    Get-ChildItem -LiteralPath (Join-Path $source $name) | Copy-Item -Destination $target -Recurse -Force
}
Write-Output "Installed laya-command and ko-en-command in $SkillsDir"

