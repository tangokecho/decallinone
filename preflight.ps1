<#
.SYNOPSIS
  Display the environment checklist and run optional validations for a local LLM setup.

.DESCRIPTION
  This script renders the assumptions, failure modes, and future enhancements you listed
  so they can be reviewed without triggering parser errors in an interactive PowerShell
  session. When -RunValidations is provided, the script performs lightweight checks for
  Python, CUDA/NVIDIA tooling, and an Ollama process. It also exposes helper functions
  that embody the failure modes you want to handle: retries with backoff, JSON
  validation, directory creation, non-empty response checks, and safe file writes.

.PARAMETER RunValidations
  Perform the validation routines after printing the checklist.

.PARAMETER OutputDirectory
  Target directory to exercise the directory creation and file-write helpers.

.EXAMPLE
  pwsh ./preflight.ps1

.EXAMPLE
  pwsh ./preflight.ps1 -RunValidations -OutputDirectory "$HOME/llm-output"
#>
param(
    [switch]$RunValidations,
    [string]$OutputDirectory = "$PSScriptRoot/output"
)

$assumptions = @(
    "Ubuntu 22.04 LTS with Python 3.10+",
    "NVIDIA RTX 4070 with CUDA",
    "Ollama installed and running locally",
    "Base model: llama3.2 (default, configurable)",
    "Internet not required after setup"
)

$failureModes = @(
    "LLM connection failures (retry with backoff)",
    "Malformed JSON input (validation)",
    "Missing directories (auto-create)",
    "Empty LLM responses (validation)",
    "File write permissions (graceful errors)"
)

$futureEnhancements = @(
    "Parallel processing with multiprocessing",
    "Web dashboard for monitoring",
    "REST API for remote triggering",
    "Template customization UI",
    "Batch prioritization and queuing"
)

function Show-Checklist {
    param(
        [string]$Title,
        [string[]]$Items
    )

    Write-Host "`n## $Title" -ForegroundColor Cyan
    for ($i = 0; $i -lt $Items.Count; $i++) {
        $index = $i + 1
        Write-Host " $index. $($Items[$i])"
    }
}

function Invoke-WithRetry {
    param(
        [scriptblock]$Action,
        [int]$MaxAttempts = 3,
        [int]$InitialDelaySeconds = 1
    )

    $attempt = 0
    $delay = [double]$InitialDelaySeconds
    while ($attempt -lt $MaxAttempts) {
        try {
            $attempt++
            return & $Action
        } catch {
            if ($attempt -ge $MaxAttempts) { throw }
            Start-Sleep -Seconds $delay
            $delay = [math]::Min($delay * 2, 30)
        }
    }
}

function Validate-Json {
    param([string]$Json)
    if ([string]::IsNullOrWhiteSpace($Json)) {
        throw "JSON payload is empty"
    }

    try {
        return $Json | ConvertFrom-Json -ErrorAction Stop
    } catch {
        throw "Malformed JSON input: $($_.Exception.Message)"
    }
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Assert-NonEmptyResponse {
    param([string]$Response)
    if ([string]::IsNullOrWhiteSpace($Response)) {
        throw "LLM response is empty"
    }
}

function Write-ContentSafe {
    param(
        [string]$Path,
        [string]$Content
    )

    try {
        Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8 -Force
    } catch {
        Write-Warning "Unable to write to '$Path': $($_.Exception.Message)"
    }
}

function Test-Python {
    Write-Host "`n[check] Python version" -ForegroundColor Yellow
    $python = Get-Command python, python3 -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $python) {
        Write-Warning "Python is not available on PATH"
        return
    }

    $version = & $python.Source --version 2>$null
    Write-Host "Found $($python.Name): $version"
}

function Test-Nvidia {
    Write-Host "`n[check] NVIDIA/CUDA" -ForegroundColor Yellow
    $nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($nvidiaSmi) {
        $output = & $nvidiaSmi.Source --query-gpu=name --format=csv,noheader 2>$null
        if ($LASTEXITCODE -eq 0 -and $output) {
            Write-Host "Detected GPU: $output"
            return
        }
    }

    $gpu = Get-CimInstance -ClassName Win32_VideoController -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'NVIDIA' }
    if ($gpu) {
        Write-Host "Detected GPU: $($gpu.Name)"
    } else {
        Write-Warning "NVIDIA GPU not detected; ensure CUDA drivers are installed"
    }
}

function Test-Ollama {
    Write-Host "`n[check] Ollama process" -ForegroundColor Yellow
    $process = Get-Process -Name ollama -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "Ollama is running (PID $($process.Id))"
    } else {
        Write-Warning "Ollama process not found; start ollama before invoking the LLM"
    }
}

function Show-FutureEnhancements {
    param([string[]]$Items)
    Write-Host "`nFuture enhancements to consider:" -ForegroundColor Magenta
    $Items | ForEach-Object { Write-Host " - $_" }
}

Show-Checklist -Title "Assumptions" -Items $assumptions
Show-Checklist -Title "Failure Modes Handled" -Items $failureModes
Show-Checklist -Title "Future Enhancements" -Items $futureEnhancements

if ($RunValidations) {
    Ensure-Directory -Path $OutputDirectory
    Test-Python
    Test-Nvidia
    Test-Ollama

    try {
        $json = Validate-Json '{"ok": true}'
        Assert-NonEmptyResponse "sample"
        Write-ContentSafe -Path (Join-Path $OutputDirectory "validation.txt") -Content "Checklist run on $(Get-Date -Format o)"
        Write-Host "`nValidation helpers executed successfully." -ForegroundColor Green
    } catch {
        Write-Warning $_
    }
}

Show-FutureEnhancements -Items $futureEnhancements
