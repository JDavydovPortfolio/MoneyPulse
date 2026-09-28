$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Push-Location $Root

try {
    $Python = if ($env:PYTHON) { $env:PYTHON } else { "python" }
    & $Python "scripts/verify.py" @args
    $Code = $LASTEXITCODE
}
finally {
    Pop-Location
}

exit $Code
