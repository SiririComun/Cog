<#
==============================================================================
Cog: Context on Git - Windows PowerShell CLI Entry Point
Usage: .\Cog\Ctx.ps1 [COMMAND] [OPTIONS]
==============================================================================
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Locate Python binary
$PythonBin = $null
foreach ($cmd in @("python", "python3", "py")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $PythonBin = $cmd
        break
    }
}

if (-not $PythonBin) {
    Write-Error "[Cog ERROR] Python was not found on your PATH."
    exit 1
}

& $PythonBin "$ScriptDir/core/engine.py" @args
exit $LASTEXITCODE