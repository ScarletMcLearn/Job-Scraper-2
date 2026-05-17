param(
    [string]$Config = "config/search.yml"
)

$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yy-MM-dd-hh-mm-ss-tt"
$timestamp = $timestamp.ToLowerInvariant()
$artifactDir = Join-Path "artifacts/jobs" $timestamp
$markdownPath = Join-Path $artifactDir "jobs.md"

uv --cache-dir .uv-cache sync
uv --cache-dir .uv-cache run job-finder scan --config $Config
uv --cache-dir .uv-cache run job-finder export-markdown --config $Config --output $markdownPath

Write-Host "Markdown report saved to $markdownPath"
