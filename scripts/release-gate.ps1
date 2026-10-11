param(
    [switch]$SkipLiveModel
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Push-Location $Root

function Run-Step {
    param(
        [string]$Label,
        [scriptblock]$Command
    )
    Write-Host "`n=== $Label ===" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

function Get-PythonCommand {
    param([string]$Version)
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py "-$Version" -c "import sys; print(sys.executable)" *> $null
        if ($LASTEXITCODE -eq 0) {
            return @("py", "-$Version")
        }
    }
    $Candidates = @("python$Version", "python")
    foreach ($Candidate in $Candidates) {
        if (Get-Command $Candidate -ErrorAction SilentlyContinue) {
            $Actual = & $Candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            if ($LASTEXITCODE -eq 0 -and $Actual.Trim() -eq $Version) {
                return @($Candidate)
            }
        }
    }
    throw "Python $Version was not found. Install it before running the release gate."
}

function Invoke-Python {
    param(
        [string[]]$PythonCommand,
        [string[]]$Arguments
    )
    $Exe = $PythonCommand[0]
    $Prefix = @()
    if ($PythonCommand.Count -gt 1) {
        $Prefix = $PythonCommand[1..($PythonCommand.Count - 1)]
    }
    & $Exe @Prefix @Arguments
}

try {
    Write-Host "MoneyPulse release-candidate gate" -ForegroundColor Green

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw "Git is required for the release gate."
    }

    $Status = git status --porcelain
    if ($LASTEXITCODE -ne 0) { throw "Unable to read git status." }
    if ($Status) {
        throw "Working tree is not clean. Commit/stash changes before release verification."
    }

    $Commit = (git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Unable to resolve HEAD." }
    Write-Host "Commit: $Commit"

    foreach ($Tool in @("tesseract", "pdfinfo", "pdftoppm")) {
        if (-not (Get-Command $Tool -ErrorAction SilentlyContinue)) {
            throw "$Tool was not found on PATH. See docs/SETUP.md."
        }
    }

    $Python312 = Get-PythonCommand "3.12"
    $Python313 = Get-PythonCommand "3.13"

    Run-Step "Fresh verifier - Python 3.12" {
        Invoke-Python $Python312 @("scripts/verify.py", "--fresh")
    }

    Run-Step "Fresh verifier - Python 3.13" {
        Invoke-Python $Python313 @("scripts/verify.py", "--fresh")
    }

    if ($SkipLiveModel) {
        Write-Warning "Live-model smoke test was skipped. Because extraction/provider behavior changed in this release cycle, this run is NOT sufficient by itself for a release decision."
    }
    else {
        Run-Step "Live local-model smoke test" {
            Invoke-Python $Python312 @("scripts/verify.py", "--fresh", "--live-model", "auto")
        }
    }

    Write-Host "`nAUTOMATED GATES PASSED for $Commit" -ForegroundColor Green
    Write-Host "Before tagging/releasing, still complete the manual gates in docs/RELEASE.md:" -ForegroundColor Yellow
    Write-Host "  1. Native desktop launch + fictional-document workflow on the target OS."
    Write-Host "  2. Current-tree and newly reachable git-history privacy/secret audit."
    Write-Host "  3. Documentation/release-note review against actual behavior."
    Write-Host "A passing automated gate is evidence, not permission to skip those checks."
}
catch {
    Write-Host "`nRELEASE GATE FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    Pop-Location
}

exit 0
