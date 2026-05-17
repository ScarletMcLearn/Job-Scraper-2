param(
    [string]$Config = "config/search.yml",
    [ValidateSet("strict", "evidence", "broad", "lenient", "discovery", "prompt")]
    [string]$Strictness = "prompt"
)

$ErrorActionPreference = "Stop"

function Select-Strictness {
    $modes = @(
        [pscustomobject]@{
            Mode = "strict"
            Description = "Only explicit visa, relocation, or eligible remote evidence"
        },
        [pscustomobject]@{
            Mode = "evidence"
            Description = "Default safe mode; uncertain remote roles go to review"
        },
        [pscustomobject]@{
            Mode = "broad"
            Description = "Includes uncertain remote roles"
        },
        [pscustomobject]@{
            Mode = "lenient"
            Description = "Accepts QA evidence from descriptions and reviews weak matches"
        },
        [pscustomobject]@{
            Mode = "discovery"
            Description = "Highest-volume mode; includes weak QA matches unless blocked"
        }
    )

    if (Get-Command Out-GridView -ErrorAction SilentlyContinue) {
        $selection = $modes | Out-GridView -Title "Select job search strictness" -PassThru
        if ($null -ne $selection) {
            return $selection.Mode
        }
    }

    Write-Host "Select job search strictness:"
    for ($index = 0; $index -lt $modes.Count; $index++) {
        Write-Host ("  {0}. {1} - {2}" -f ($index + 1), $modes[$index].Mode, $modes[$index].Description)
    }

    do {
        $choice = Read-Host "Enter 1-5"
        $parsed = 0
        $isNumber = [int]::TryParse($choice, [ref]$parsed)
    } while (-not $isNumber -or $parsed -lt 1 -or $parsed -gt $modes.Count)

    return $modes[$parsed - 1].Mode
}

if ($Strictness -eq "prompt") {
    $Strictness = Select-Strictness
}

$timestamp = Get-Date -Format "yy-MM-dd-hh-mm-ss-tt"
$timestamp = $timestamp.ToLowerInvariant()
$artifactDir = Join-Path "artifacts/jobs" $timestamp
$markdownPath = Join-Path $artifactDir "jobs.md"

uv --cache-dir .uv-cache sync
uv --cache-dir .uv-cache run job-finder scan --config $Config --strictness $Strictness
uv --cache-dir .uv-cache run job-finder export-markdown --config $Config --output $markdownPath

Write-Host "Search strictness: $Strictness"
Write-Host "Markdown report saved to $markdownPath"
